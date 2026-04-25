import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

interface ErrorInfo {
  type: string;
  message: string;
  file?: string;
  line?: number;
  fix?: string;
  severity: 'error' | 'warning';
}

interface FixReport {
  timestamp: string;
  errors: ErrorInfo[];
  fixes: Array<{ file: string; fix: string; description: string }>;
  summary: {
    total: number;
    errors: number;
    warnings: number;
  };
}

// 自动修复函数
const autoFixes: Record<string, (error: ErrorInfo) => Promise<boolean>> = {
  'missing-key': async (error) => {
    // 这个需要手动修复，因为需要知道具体的组件
    console.log('需要手动添加 key 属性到列表项');
    return false;
  },
  
  'attribute-type': async (error) => {
    // 检查是否是 strong 属性问题
    if (error.message.includes('strong')) {
      const srcPath = path.join(process.cwd(), 'src');
      const files = findFiles(srcPath, ['.tsx', '.ts']);
      
      for (const file of files) {
        const content = fs.readFileSync(file, 'utf-8');
        if (content.includes('<Text strong')) {
          const fixed = content.replace(/<Text\s+strong\b/g, '<Text style={{ fontWeight: \'bold\' }}');
          if (fixed !== content) {
            fs.writeFileSync(file, fixed, 'utf-8');
            console.log(`✅ 已修复: ${file}`);
            return true;
          }
        }
      }
    }
    return false;
  },
  
  'import-error': async (error) => {
    // 检查是否是组件导入问题
    if (error.message.includes('Cannot find module') || error.message.includes('Module not found')) {
      const srcPath = path.join(process.cwd(), 'src');
      const files = findFiles(srcPath, ['.tsx', '.ts']);
      
      for (const file of files) {
        const content = fs.readFileSync(file, 'utf-8');
        // 检查是否有遗留的 @arco-design 导入
        if (content.includes("@arco-design/web-react")) {
          console.log(`⚠️  发现遗留的 @arco-design 导入: ${file}`);
          console.log('   请手动迁移该文件到 shadcn/ui 组件');
        }
      }
    }
    return false;
  }
};

function findFiles(dir: string, extensions: string[]): string[] {
  const files: string[] = [];
  
  function walk(currentDir: string) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      
      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        walk(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (extensions.includes(ext)) {
          files.push(fullPath);
        }
      }
    }
  }
  
  walk(dir);
  return files;
}

async function applyFixes() {
  const reportPath = path.join(process.cwd(), 'test-results', 'auto-fix-report.json');
  
  if (!fs.existsSync(reportPath)) {
    console.log('❌ 未找到测试报告，请先运行测试');
    return;
  }
  
  const report: FixReport = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
  
  console.log('\n=== 开始自动修复 ===\n');
  console.log(`发现 ${report.summary.total} 个问题\n`);
  
  let fixedCount = 0;
  
  for (const error of report.errors) {
    if (error.type && autoFixes[error.type]) {
      console.log(`尝试修复: ${error.type} - ${error.message.substring(0, 50)}...`);
      const fixed = await autoFixes[error.type](error);
      if (fixed) {
        fixedCount++;
      }
    }
  }
  
  console.log(`\n✅ 已修复 ${fixedCount} 个问题`);
  console.log('请重新运行测试以验证修复');
}

// 运行修复
applyFixes().catch(console.error);

