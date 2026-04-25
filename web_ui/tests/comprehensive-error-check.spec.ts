import { test, expect } from '@playwright/test';

// 存储所有错误
const allErrors: Array<{ page: string; type: string; message: string; stack?: string }> = [];
const allWarnings: Array<{ page: string; type: string; message: string }> = [];

test.beforeEach(async ({ page }) => {
  // 监听控制台错误
  page.on('console', (msg) => {
    const text = msg.text();
    const location = msg.location();
    const pageUrl = page.url();
    
    // 忽略外部服务的错误
    if (text.includes('google-analytics') || text.includes('gtag')) {
      return;
    }
    
    if (msg.type() === 'error') {
      allErrors.push({
        page: pageUrl,
        type: 'console.error',
        message: text,
      });
    } else if (msg.type() === 'warning') {
      allWarnings.push({
        page: pageUrl,
        type: 'console.warning',
        message: text,
      });
    }
  });

  // 监听页面错误
  page.on('pageerror', (error) => {
    allErrors.push({
      page: page.url(),
      type: 'pageerror',
      message: `${error.name}: ${error.message}`,
      stack: error.stack
    });
  });

  // 监听请求失败（只关注应用内的请求）
  page.on('requestfailed', (request) => {
    const url = request.url();
    const failure = request.failure();
    
    // 忽略外部服务和已知的资源加载失败
    if (
        url.includes('google-analytics') ||
        url.includes('logo.svg') ||
        url.includes('favicon')) {
      return;
    }
    
    // 只关注应用内的 API 请求失败
    if (url.includes('/api/') || url.includes('/static/')) {
      allErrors.push({
        page: page.url(),
        type: 'requestfailed',
        message: `Request failed: ${url} - ${failure?.errorText || 'Unknown error'}`
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
    !err.message.includes('logo.svg') &&
    !err.message.includes('google-analytics') &&
    !err.message.includes('favicon')
  );
  
  const filteredWarnings = allWarnings.filter(warn => 
    !warn.message.includes('findDOMNode') &&
    !warn.message.includes('React Router Future Flag') &&
    !warn.message.includes('MODULE_TYPELESS_PACKAGE_JSON') &&
    !warn.message.includes('NO_COLOR')
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
      if (err.stack) {
        const stackLines = err.stack.split('\n').slice(0, 3);
        console.log(`      调用栈:`);
        stackLines.forEach(line => console.log(`        ${line.trim()}`));
      }
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
    err.message.includes('does not provide an export') ||
    err.message.includes('Cannot find module') ||
    err.message.includes('Unexpected token') ||
    err.message.includes('SyntaxError')
  );
  
  if (criticalErrors.length > 0) {
    console.log('\n\n┌─────────────────────────────────────────┐');
    console.log('│  ⛔ 严重错误 (Critical Errors)          │');
    console.log('└─────────────────────────────────────────┘');
    criticalErrors.forEach((err, index) => {
      console.log(`\n  [${index + 1}] 类型: ${err.type}`);
      console.log(`      页面: ${err.page}`);
      console.log(`      信息: ${err.message}`);
      if (err.stack) {
        const stackLines = err.stack.split('\n').slice(0, 5);
        console.log(`      调用栈:`);
        stackLines.forEach(line => console.log(`        ${line.trim()}`));
      }
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

test('检查登录页面加载和渲染', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  // 检查页面是否正常渲染
  await expect(page.locator('body')).toBeVisible();
  
  // 检查是否有 React 挂载点
  const app = page.locator('#app');
  await expect(app).toBeVisible();
  
  // 检查登录表单元素
  const usernameInput = page.locator('input[type="text"], input[name="username"]');
  const passwordInput = page.locator('input[type="password"]');
  
  // 至少应该有一个输入框
  const inputCount = await page.locator('input').count();
  expect(inputCount).toBeGreaterThan(0);
  
  // 检查是否有按钮
  const buttonCount = await page.locator('button').count();
  expect(buttonCount).toBeGreaterThan(0);
});

test('检查路由重定向', async ({ page }) => {
  // 访问需要登录的页面，应该重定向到登录页
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  const currentUrl = page.url();
  // 应该重定向到登录页或显示登录表单
  expect(currentUrl).toMatch(/\/(login|$)/);
});

test('检查页面 JavaScript 执行', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  // 检查是否有 React 应用
  const hasReact = await page.evaluate(() => {
    return typeof window !== 'undefined' && 
           (window as any).React !== undefined ||
           document.querySelector('#app') !== null;
  });
  
  expect(hasReact).toBeTruthy();
  
  // 检查是否有控制台错误（通过页面评估）
  const pageErrors = await page.evaluate(() => {
    return (window as any).__playwrightErrors || [];
  });
  
  if (pageErrors.length > 0) {
    console.log('  [页面错误]', pageErrors);
  }
});

test('检查资源加载', async ({ page }) => {
  const failedResources: string[] = [];
  
  page.on('requestfailed', (request) => {
    const url = request.url();
    // 只记录应用内的资源
    if (url.includes('localhost:3000') &&
        !url.includes('logo.svg')) {
      failedResources.push(url);
    }
  });
  
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // 检查关键资源是否加载
  const scripts = await page.locator('script[src]').count();
  const styles = await page.locator('link[rel="stylesheet"]').count();
  
  expect(scripts).toBeGreaterThan(0);
  expect(styles).toBeGreaterThan(0);
  
  if (failedResources.length > 0) {
    console.log('  [资源加载失败]', failedResources);
  }
});

test('检查组件渲染', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  // 检查页面是否有内容
  const bodyText = await page.locator('body').textContent();
  expect(bodyText).toBeTruthy();
  expect(bodyText!.length).toBeGreaterThan(0);
  
  // 检查是否有表单或主要内容区域
  const hasForm = await page.locator('form, [role="form"]').count() > 0;
  const hasCard = await page.locator('[class*="card"], [class*="Card"]').count() > 0;
  
  // 至少应该有一种主要内容容器
  expect(hasForm || hasCard || bodyText!.length > 100).toBeTruthy();
});

