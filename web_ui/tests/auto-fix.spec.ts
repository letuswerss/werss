import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// 存储所有错误和修复建议
interface ErrorInfo {
  type: string;
  message: string;
  file?: string;
  line?: number;
  fix?: string;
  severity: 'error' | 'warning';
}

const errors: ErrorInfo[] = [];
const fixes: Array<{ file: string; fix: string; description: string }> = [];

// 常见错误模式和修复方案
const errorPatterns = [
  {
    pattern: /does not provide an export named ['"](.*?)['"]/,
    fix: (match: RegExpMatchArray) => ({
      description: `修复导入错误: ${match[1]}`,
      type: 'import-error'
    })
  },
  {
    pattern: /Failed to resolve import ['"](.*?)['"]/,
    fix: (match: RegExpMatchArray) => ({
      description: `修复模块解析错误: ${match[1]}`,
      type: 'module-resolution'
    })
  },
  {
    pattern: /Cannot read property ['"](.*?)['"] of undefined/,
    fix: (match: RegExpMatchArray) => ({
      description: `添加空值检查: ${match[1]}`,
      type: 'null-check'
    })
  },
  {
    pattern: /Each child in a list should have a unique ["']key["'] prop/,
    fix: () => ({
      description: '添加缺失的 key 属性',
      type: 'missing-key'
    })
  },
  {
    pattern: /Received `true` for a non-boolean attribute ['"](.*?)['"]/,
    fix: (match: RegExpMatchArray) => ({
      description: `修复属性类型错误: ${match[1]}`,
      type: 'attribute-type'
    })
  }
];

test.beforeEach(async ({ page }) => {
  // 监听控制台错误
  page.on('console', (msg) => {
    const text = msg.text();
    const location = msg.location();
    
    // 检查错误模式
    for (const pattern of errorPatterns) {
      const match = text.match(pattern.pattern);
      if (match) {
        const fixInfo = pattern.fix(match);
        errors.push({
          type: fixInfo.type,
          message: text,
          file: location.url,
          line: location.lineNumber,
          fix: fixInfo.description,
          severity: msg.type() === 'error' ? 'error' : 'warning'
        });
      }
    }
  });

  // 监听页面错误
  page.on('pageerror', (error) => {
    const message = error.message;
    for (const pattern of errorPatterns) {
      const match = message.match(pattern.pattern);
      if (match) {
        const fixInfo = pattern.fix(match);
        errors.push({
          type: fixInfo.type,
          message: message,
          fix: fixInfo.description,
          severity: 'error'
        });
      }
    }
  });
});

test.afterAll(async () => {
  // 生成修复报告
  const report = {
    timestamp: new Date().toISOString(),
    errors: errors,
    fixes: fixes,
    summary: {
      total: errors.length,
      errors: errors.filter(e => e.severity === 'error').length,
      warnings: errors.filter(e => e.severity === 'warning').length
    }
  };

  // 保存报告
  const reportPath = path.join(process.cwd(), 'test-results', 'auto-fix-report.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log('\n\n=== 自动修复报告 ===');
  console.log(`总计: ${report.summary.total} 个问题`);
  console.log(`错误: ${report.summary.errors} 个`);
  console.log(`警告: ${report.summary.warnings} 个`);
  
  if (fixes.length > 0) {
    console.log('\n=== 建议的修复 ===');
    fixes.forEach((fix, index) => {
      console.log(`\n${index + 1}. ${fix.description}`);
      console.log(`   文件: ${fix.file}`);
      console.log(`   修复: ${fix.fix}`);
    });
  }
});

test('检测并记录所有错误', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  // 检查页面是否正常
  await expect(page.locator('body')).toBeVisible();
});

test('检查常见错误模式', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  // 执行一些交互来触发可能的错误
  const inputs = page.locator('input');
  const inputCount = await inputs.count();
  if (inputCount > 0) {
    await inputs.first().click();
  }
  
  await page.waitForTimeout(1000);
});

