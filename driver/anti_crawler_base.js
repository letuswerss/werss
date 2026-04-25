// === 基础反检测脚本 ===
// 隐藏webdriver属性
delete navigator.__proto__.webdriver;

// === 浏览器指纹伪装 ===

// 伪装mimeTypes
Object.defineProperty(navigator, 'mimeTypes', {
    get: function() {
        return {
            "application/pdf": {
                description: "Portable Document Format",
                suffixes: "pdf",
                type: "application/pdf",
                enabledPlugin: {
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }
            }
        };
    }
});

// 伪装硬件信息
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: function() {
        return Math.floor(Math.random() * 8) + 4; // 4-12核心
    }
});

Object.defineProperty(navigator, 'deviceMemory', {
    get: function() {
        return Math.random() > 0.5 ? 8 : 4; // 4GB或8GB
    }
});

// 伪装屏幕信息
Object.defineProperty(screen, 'colorDepth', {
    get: function() {
        return 24;
    }
});

Object.defineProperty(screen, 'pixelDepth', {
    get: function() {
        return 24;
    }
});

// 伪装canvas指纹
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(...args) {
    // 添加随机噪声
    const ctx = this.getContext('2d');
    if (ctx) {
        const imageData = ctx.getImageData(0, 0, this.width, this.height);
        for (let i = 0; i < imageData.data.length; i += 4) {
            if (Math.random() > 0.98) {
                imageData.data[i] = Math.floor(Math.random() * 256);
                imageData.data[i + 1] = Math.floor(Math.random() * 256);
                imageData.data[i + 2] = Math.floor(Math.random() * 256);
            }
        }
        ctx.putImageData(imageData, 0, 0);
    }
    return originalToDataURL.apply(this, args);
};

// 伪装WebGL指纹
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
        return 'Intel Inc.';
    }
    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.call(this, parameter);
};

// === Chrome扩展API伪装 ===
// 伪装chrome.runtime API以通过CHR_MEMORY检测
if (typeof chrome === 'undefined') {
    window.chrome = {};
}

if (!chrome.runtime) {
    chrome.runtime = {
        onConnect: {
            addListener: function() {},
            removeListener: function() {}
        },
        onMessage: {
            addListener: function() {},
            removeListener: function() {}
        },
        connect: function() {
            return {
                onMessage: { addListener: function() {} },
                onDisconnect: { addListener: function() {} },
                postMessage: function() {}
            };
        },
        sendMessage: function() {},
        getURL: function(path) { return path; },
        id: 'fake_extension_id',
        getManifest: function() {
            return {
                name: 'Chrome',
                version: '120.0.0.0',
                manifest_version: 3
            };
        }
    };
}

// 伪装chrome.permissions API
if (!chrome.permissions) {
    chrome.permissions = {
        request: function(permissions) {
            return Promise.resolve(false);
        },
        contains: function(permissions) {
            return Promise.resolve(false);
        },
        getAll: function() {
            return Promise.resolve({
                permissions: ['notifications', 'geolocation']
            });
        },
        remove: function(permissions) {
            return Promise.resolve(false);
        }
    };
}

// === 内存API伪装 ===
// 伪装performance.memory以通过内存检测
if (performance && !performance.memory) {
    Object.defineProperty(performance, 'memory', {
        get: function() {
            return {
                usedJSHeapSize: Math.floor(Math.random() * 50000000) + 10000000,
                totalJSHeapSize: Math.floor(Math.random() * 100000000) + 50000000,
                jsHeapSizeLimit: Math.floor(Math.random() * 2000000000) + 1000000000
            };
        }
    });
}

// === 语言和时区伪装 ===
// 伪装navigator.languages
Object.defineProperty(navigator, 'languages', {
    get: function() {
        return ['zh-CN', 'zh', 'en'];
    }
});

// 伪装时区
const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
Date.prototype.getTimezoneOffset = function() {
    return -480; // UTC+8 (北京时间)
};

// === 反自动化检测 ===
// 隐藏自动化相关属性
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

// 伪装toString方法
const originalFunctionToString = Function.prototype.toString;
Function.prototype.toString = function() {
    if (this === navigator.webdriver) {
        return 'function webdriver() { [native code] }';
    }
    return originalFunctionToString.call(this);
};

// === 网络检测绕过 ===
// 伪装网络连接类型
Object.defineProperty(navigator, 'connection', {
    get: function() {
        return {
            effectiveType: '4g',
            rtt: 100,
            downlink: 10,
            saveData: false
        };
    }
});

// === 电池API伪装 ===
Object.defineProperty(navigator, 'getBattery', {
    get: function() {
        return function() {
            return Promise.resolve({
                charging: Math.random() > 0.5,
                chargingTime: Math.random() * 3600,
                dischargingTime: Math.random() * 7200,
                level: Math.random() * 0.5 + 0.5
            });
        };
    }
});

// === 传感器伪装 ===
if (window.DeviceOrientationEvent) {
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
        if (type === 'deviceorientation') {
            // 模拟设备方向数据
            setTimeout(() => {
                const event = new DeviceOrientationEvent('deviceorientation', {
                    alpha: Math.random() * 360,
                    beta: Math.random() * 180 - 90,
                    gamma: Math.random() * 90 - 45
                });
                listener.call(this, event);
            }, Math.random() * 1000);
        }
        return originalAddEventListener.call(this, type, listener, options);
    };
}