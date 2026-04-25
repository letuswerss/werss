import { test, expect } from '@playwright/test';

// 全局存储所有错误
const allErrors: Array<{ page: string; type: string; message: string }> = [];
const allWarnings: Array<{ page: string; type: string; message: string }> = [];

test.beforeEach(async ({ page }) => {
  // 监听控制台错误
  page.on('console', (msg) => {
    const text = msg.text();
    const location = msg.location();
    const pageUrl = page.url();
    
    if (msg.type() === 'error') {
      allErrors.push({
        page: pageUrl,
        type: 'console.error',
        message: `${text} (at ${location.url}:${location.lineNumber}:${location.columnNumber})`
      });
    } else if (msg.type() === 'warning') {
      allWarnings.push({
        page: pageUrl,
        type: 'console.warning',
        message: `${text} (at ${location.url}:${location.lineNumber}:${location.columnNumber})`
      });
    }
  });

  // 监听页面错误
  page.on('pageerror', (error) => {
    allErrors.push({
      page: page.url(),
      type: 'pageerror',
      message: `${error.name}: ${error.message}\n${error.stack || ''}`
    });
  });

  // 监听请求失败
  page.on('requestfailed', (request) => {
    const failure = request.failure();
    if (failure && !request.url().includes('logo.svg')) { // 忽略已知的 logo 错误
      allErrors.push({
        page: page.url(),
        type: 'requestfailed',
        message: `Request failed: ${request.url()} - ${failure.errorText}`
      });
    }
  });
});

test.afterAll(() => {
  // 过滤掉已知的警告和错误
  const filteredErrors = allErrors.filter(err => 
    !err.message.includes('findDOMNode') &&
    !err.message.includes('React Router Future Flag') &&
    !err.message.includes('proxy error') &&
    !err.message.includes('ECONNREFUSED') &&
    !err.message.includes('logo.svg')
  );
  
  const filteredWarnings = allWarnings.filter(warn => 
    !warn.message.includes('findDOMNode') &&
    !warn.message.includes('React Router Future Flag') &&
    !warn.message.includes('MODULE_TYPELESS_PACKAGE_JSON')
  );
  
  // 输出所有错误和警告
  if (filteredErrors.length > 0) {
    console.log('\n\n┌─────────────────────────────────────────┐');
    console.log('│  ✗ 错误报告 (Error Report)              │');
    console.log('└─────────────────────────────────────────┘');
    filteredErrors.forEach((err, index) => {
      console.log(`\n  [${index + 1}] 类型: ${err.type}`);
      console.log(`      页面: ${err.page}`);
      console.log(`      信息: ${err.message}`);
    });
  }
  
  if (filteredWarnings.length > 0) {
    console.log('\n\n┌─────────────────────────────────────────┐');
    console.log('│  ⚡ 警告信息 (Warning Messages)         │');
    console.log('└─────────────────────────────────────────┘');
    filteredWarnings.forEach((warn, index) => {
      console.log(`\n  [${index + 1}] 类型: ${warn.type}`);
      console.log(`      页面: ${warn.page}`);
      console.log(`      信息: ${warn.message}`);
    });
  }
  
  // 检查是否有严重的运行时错误
  const criticalErrors = filteredErrors.filter(err => 
    err.message.includes('TypeError') ||
    err.message.includes('ReferenceError') ||
    err.message.includes('Cannot read') ||
    err.message.includes('is not defined') ||
    err.message.includes('Failed to resolve') ||
    err.message.includes('does not provide an export')
  );
  
  if (criticalErrors.length > 0) {
    console.log('\n\n┌─────────────────────────────────────────┐');
    console.log('│  ⛔ 严重错误 (Critical Errors)          │');
    console.log('└─────────────────────────────────────────┘');
    criticalErrors.forEach((err, index) => {
      console.log(`\n  [${index + 1}] 类型: ${err.type}`);
      console.log(`      页面: ${err.page}`);
      console.log(`      信息: ${err.message}`);
    });
    throw new Error(`检测到 ${criticalErrors.length} 个严重错误，请检查上述输出`);
  }
  
  if (filteredErrors.length > 0 || filteredWarnings.length > 0) {
    console.log('\n\n┌─────────────────────────────────────────┐');
    console.log(`│  统计: ${filteredErrors.length} 个错误 | ${filteredWarnings.length} 个警告  │`);
    console.log('└─────────────────────────────────────────┘');
  } else {
    console.log('\n\n┌─────────────────────────────────────────┐');
    console.log('│  ✓ 测试通过 - 未发现错误或警告          │');
    console.log('└─────────────────────────────────────────┘');
  }
});

test('检查登录页面', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000); // 等待所有脚本执行
  
  // 检查页面是否正常渲染
  await expect(page.locator('body')).toBeVisible();
  
  // 检查是否有 React 挂载点
  const app = page.locator('#app');
  if (await app.count() > 0) {
    await expect(app).toBeVisible();
  }
});

test('检查主页（需要登录）', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 检查是否重定向到登录页或正常加载
  const currentUrl = page.url();
  if (currentUrl.includes('/login')) {
    console.log('  [路由] 主页需要登录，已重定向到登录页');
  } else {
    await expect(page.locator('body')).toBeVisible();
  }
});

test('检查所有路由页面', async ({ page }) => {
  const routes = [
    '/login',
    '/',
  ];
  
  for (const route of routes) {
    await page.goto(route);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // 检查页面是否加载
    await expect(page.locator('body')).toBeVisible();
  }
});

test('检查控制台错误和警告', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000); // 等待所有脚本执行
  
  // 检查页面是否正常
  await expect(page.locator('body')).toBeVisible();
});

test('检查页面元素渲染', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  
  // 检查关键元素是否存在
  const body = page.locator('body');
  await expect(body).toBeVisible();
  
  // 检查是否有 React 挂载点
  const app = page.locator('#app');
  if (await app.count() > 0) {
    await expect(app).toBeVisible();
  }
  
  // 检查是否有表单元素（登录页面）
  const inputs = page.locator('input');
  const inputCount = await inputs.count();
  if (inputCount > 0) {
    console.log(`  [元素检查] 找到 ${inputCount} 个输入框`);
  }
});
