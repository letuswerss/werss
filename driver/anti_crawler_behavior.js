// === 用户行为模拟脚本 ===

// === 全局行为管理器 ===
class BehaviorSimulator {
    constructor() {
        this.mouseMovements = 0;
        this.scrollCount = 0;
        this.keyPresses = 0;
        this.clicks = 0;
        this.lastActivity = Date.now();
        this.isActive = true;
        this.init();
    }

    init() {
        this.simulateMouseActivity();
        this.simulateScrolling();
        this.simulateKeyboardActivity();
        this.simulateFocusBehavior();
        this.simulateHumanDelays();
        this.simulatePageInteraction();
    }

    // === 鼠标行为模拟 ===
    simulateMouseActivity() {
        document.addEventListener('mousemove', (e) => {
            this.mouseMovements++;
            this.lastActivity = Date.now();
            
            // 随机暂停，模拟真实用户思考
            if (Math.random() > 0.95 && this.mouseMovements > 10) {
                e.stopImmediatePropagation();
                setTimeout(() => {
                    this.mouseMovements = 0;
                }, Math.random() * 2000 + 500);
            }

            // 模拟不规则的鼠标轨迹
            if (Math.random() > 0.98) {
                const randomX = e.clientX + (Math.random() - 0.5) * 10;
                const randomY = e.clientY + (Math.random() - 0.5) * 10;
                setTimeout(() => {
                    const event = new MouseEvent('mousemove', {
                        clientX: randomX,
                        clientY: randomY
                    });
                    document.dispatchEvent(event);
                }, Math.random() * 100);
            }
        }, true);

        // 模拟随机点击
        document.addEventListener('click', (e) => {
            this.clicks++;
            this.lastActivity = Date.now();
            
            // 偶尔模拟双击
            if (Math.random() > 0.9 && this.clicks % 3 === 0) {
                setTimeout(() => {
                    const doubleClickEvent = new MouseEvent('dblclick', {
                        clientX: e.clientX,
                        clientY: e.clientY,
                        bubbles: true
                    });
                    e.target.dispatchEvent(doubleClickEvent);
                }, Math.random() * 300 + 100);
            }
        }, true);
    }

    // === 滚动行为模拟 ===
    simulateScrolling() {
        document.addEventListener('scroll', () => {
            this.scrollCount++;
            this.lastActivity = Date.now();
            
            // 模拟不规则的滚动行为
            if (this.scrollCount % 5 === 0) {
                const randomScroll = Math.random() * 20 - 10;
                setTimeout(() => {
                    window.scrollTo(window.scrollX, window.scrollY + randomScroll);
                }, Math.random() * 200);
            }

            // 模拟滚动到页面底部附近时的回弹
            if (window.scrollY + window.innerHeight > document.body.scrollHeight - 100) {
                if (Math.random() > 0.7) {
                    setTimeout(() => {
                        window.scrollTo(window.scrollX, window.scrollY - Math.random() * 50);
                    }, Math.random() * 500);
                }
            }
        }, true);

        // 自动滚动模拟
        this.startAutoScroll();
    }

    startAutoScroll() {
        setInterval(() => {
            if (!this.isActive) return;
            
            const timeSinceLastActivity = Date.now() - this.lastActivity;
            if (timeSinceLastActivity > 10000 && Math.random() > 0.8) {
                const scrollDistance = Math.random() * 200 + 50;
                const scrollDirection = Math.random() > 0.5 ? 1 : -1;
                
                window.scrollBy({
                    top: scrollDistance * scrollDirection,
                    behavior: 'smooth'
                });
            }
        }, 5000);
    }

    // === 键盘行为模拟 ===
    simulateKeyboardActivity() {
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (type === 'click') {
                const wrappedListener = function(...args) {
                    // 随机延迟点击，模拟人类反应时间
                    const delay = Math.random() * 150 + 30;
                    setTimeout(() => listener.apply(this, args), delay);
                };
                return originalAddEventListener.call(this, type, wrappedListener, options);
            }
            if (type === 'keydown') {
                const wrappedListener = function(...args) {
                    // 随机延迟键盘输入
                    const delay = Math.random() * 100 + 20;
                    setTimeout(() => listener.apply(this, args), delay);
                };
                return originalAddEventListener.call(this, type, wrappedListener, options);
            }
            return originalAddEventListener.call(this, type, listener, options);
        };

        // 模拟随机按键
        setInterval(() => {
            if (!this.isActive || Math.random() > 0.95) return;
            
            const keys = ['Tab', 'Shift', 'Control', 'Alt'];
            const randomKey = keys[Math.floor(Math.random() * keys.length)];
            const event = new KeyboardEvent('keydown', {
                key: randomKey,
                code: randomKey,
                bubbles: true
            });
            document.dispatchEvent(event);
        }, 8000);
    }

    // === 焦点行为模拟 ===
    simulateFocusBehavior() {
        document.addEventListener('focusin', (e) => {
            if (Math.random() > 0.8) {
                // 模拟用户分心，暂时失去焦点
                setTimeout(() => {
                    e.target.blur();
                    setTimeout(() => e.target.focus(), Math.random() * 200);
                }, Math.random() * 100);
            }
        }, true);

        // 模拟标签页切换
        setInterval(() => {
            if (Math.random() > 0.95) {
                document.dispatchEvent(new Event('visibilitychange'));
                setTimeout(() => {
                    document.dispatchEvent(new Event('visibilitychange'));
                }, Math.random() * 1000 + 500);
            }
        }, 15000);
    }

    // === 人性化延迟模拟 ===
    simulateHumanDelays() {
        // 覆盖一些常见的自动化检测方法
        const originalQuerySelector = document.querySelector;
        document.querySelector = function(selector) {
            // 添加随机延迟
            if (Math.random() > 0.9) {
                const delay = Math.random() * 50 + 10;
                const startTime = Date.now();
                while (Date.now() - startTime < delay) {
                    // 忙等待模拟人类思考
                }
            }
            return originalQuerySelector.call(this, selector);
        };
    }

    // === 页面交互模拟 ===
    simulatePageInteraction() {
        // 模拟鼠标悬停
        setInterval(() => {
            if (!this.isActive || Math.random() > 0.9) return;
            
            const links = document.querySelectorAll('a, button, [onclick]');
            if (links.length > 0) {
                const randomElement = links[Math.floor(Math.random() * links.length)];
                const rect = randomElement.getBoundingClientRect();
                
                const mouseEnterEvent = new MouseEvent('mouseenter', {
                    clientX: rect.left + rect.width / 2,
                    clientY: rect.top + rect.height / 2,
                    bubbles: true
                });
                
                randomElement.dispatchEvent(mouseEnterEvent);
                
                // 偶尔触发悬停离开
                if (Math.random() > 0.5) {
                    setTimeout(() => {
                        const mouseLeaveEvent = new MouseEvent('mouseleave', {
                            clientX: rect.left + rect.width / 2,
                            clientY: rect.top + rect.height / 2,
                            bubbles: true
                        });
                        randomElement.dispatchEvent(mouseLeaveEvent);
                    }, Math.random() * 1000 + 200);
                }
            }
        }, 3000);

        // 模拟文本选择
        setInterval(() => {
            if (!this.isActive || Math.random() > 0.95) return;
            
            const texts = document.querySelectorAll('p, span, div');
            if (texts.length > 0) {
                const randomText = texts[Math.floor(Math.random() * texts.length)];
                if (randomText.textContent && randomText.textContent.length > 10) {
                    const selection = window.getSelection();
                    const range = document.createRange();
                    
                    try {
                        range.setStart(randomText.firstChild, 0);
                        range.setEnd(randomText.firstChild, Math.min(randomText.textContent.length, 20));
                        selection.removeAllRanges();
                        selection.addRange(range);
                        
                        // 清除选择
                        setTimeout(() => {
                            selection.removeAllRanges();
                        }, Math.random() * 2000 + 500);
                    } catch (e) {
                        // 忽略选择错误
                    }
                }
            }
        }, 8000);
    }

    // 活动状态控制
    pause() {
        this.isActive = false;
    }

    resume() {
        this.isActive = true;
        this.lastActivity = Date.now();
    }
}

// 启动行为模拟器
const behaviorSimulator = new BehaviorSimulator();

// 导出供外部使用
window.behaviorSimulator = behaviorSimulator;