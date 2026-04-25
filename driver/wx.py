from asyncio import wait_for
from socket import timeout
import sys

from sqlalchemy import False_

import driver
from .playwright_driver import PlaywrightController,ControlDriver
from PIL import Image
from .success import Success
import time
import os
from driver.success import getStatus
from driver.store import Store
import re
from threading import Timer, Lock
from .cookies import expire
import json
from core.print import print_error,print_warning,print_info,print_success
class Wx:
    _haslogin=False
    SESSION=None
    HasCode=False
    isLOCK=False
    WX_LOGIN="https://mp.weixin.qq.com/"
    WX_HOME="https://mp.weixin.qq.com/cgi-bin/home"
    wx_login_url="static/wx_qrcode.png"
    lock_file_path="data/.lock"
    CallBack=None
    Notice=None
    ext_data = None
    # 添加线程锁保护共享变量
    _login_lock = Lock()
    def __init__(self):
        self.lock_path=os.path.dirname(self.lock_file_path)
        self.refresh_interval=3660*24
        self.controller=PlaywrightController()
        os.makedirs(self.lock_path, exist_ok=True)
        self.Clean()
        self.release_lock()
        pass

    def GetHasCode(self):
        if os.path.exists(self.wx_login_url):
            return True
        return False
    def extract_token_from_requests(self):
        """从页面中提取token"""
        try:
            # 优先使用临时控制器，其次使用默认控制器
            controller = getattr(self, '_temp_controller', None) or self.controller
            
            if not controller or not controller.page:
                return None
                
            page = controller.page
            # 尝试从当前URL获取token
            current_url = page.url
            token_match = re.search(r'token=([^&]+)', current_url)
            if token_match:
                return token_match.group(1)
            
            # 尝试从localStorage获取
            token = page.evaluate("() => localStorage.getItem('token')")
            if token:
                return token
                
            # 尝试从sessionStorage获取
            token = page.evaluate("() => sessionStorage.getItem('token')")
            if token:
                return token
                
            # 尝试从cookie获取
            cookies = page.context.cookies()
            for cookie in cookies:
                if 'token' in cookie['name'].lower():
                    return cookie['value']
                    
            return None
        except Exception as e:
            print(f"提取token时出错: {str(e)}")
            return None
    def switch_account(self, username: str = ""):
        """切换账号功能
        Args:
            username: 目标账号的用户名，如果为空则切换到其他可用账号
        """
        print("开始切换账号...")
        try:
            self.Token(isClose=False)
            if self._haslogin is False:
                self.Close()
                self.GetCode(Success)
                time.sleep(60)
                return False
            time.sleep(1)
            if not hasattr(self, 'controller') or not self.controller.page:
                print_error("浏览器未启动，无法切换账号")
                return False
                
            page = self.controller.page
            
            # 等待页面加载完成
            page.wait_for_load_state("networkidle")
            
            # 点击账号信息区域打开账号面板
            account_info = page.locator(".weui-desktop-account__info")
            if account_info.count() > 0:
                account_info.click()
                time.sleep(1)
                
                # 等待账号面板显示
                account_panel = page.locator(".account_box-panel")
                if account_panel.count() > 0:
                    # 查找切换账号按钮（更精确的选择器）
                    switch_account_link = account_panel.locator("li.account_box-panel-item:has-text('切换账号') a")
                    if switch_account_link.count() > 0:
                        print_info("找到切换账号按钮，点击切换...")
                        switch_account_link.click()
                        time.sleep(3)
                        
                        try:
                            # 查找可切换的账号（排除当前登录账号）
                            accounts = page.locator(
                                                ".switch-account-dialog .switch-account-dialog_section:has-text('公众号') .section-item:not(:has-text('当前登录')),"
                                                ".switch-account-dialog .switch-account-dialog_section:has-text('服务号') .section-item:not(:has-text('当前登录'))"
                                            )
                            account_count = accounts.count()
                            print(f"当前一共有{account_count}个可切换账号")
                            import random
                            if account_count > 0:
                                # 点击第一个可切换的账号
                                random_index = random.randint(0, account_count - 1)
                                time.sleep(1)
                                p=accounts.nth(random_index).locator("p")
                                nick_name=accounts.nth(random_index).locator(".section-item__nickname")
                                account_id=p.text_content()
                                account_name=nick_name.text_content()
                                print(f"账号: {account_name} ID:{account_id}")
                                p.click()
                                # 等待页面加载并验证切换成功
                                page.wait_for_load_state("networkidle", timeout=10000)
                                time.sleep(5)
                                self.Call_Success()
                                self.Close()
                                self.Token()
                                print_success("账号切换成功")
                                from jobs.notice import sys_notice
                                from core.config import cfg
                                sys_notice(f"账号切换成功\n- 账号名称: {account_name} \n- 账号ID: {account_id} \n- 过期时间: {self.SESSION.get('expire_time')}", str(cfg.get("server.code_title","WeRss账号切换成功")))
                                return True
                            else:
                                print_warning("没有找到可切换的账号")
                        except Exception as e:
                            print_error(f"切换账号时发生错误: {str(e)}")
                            return False
                    else:
                        print_warning("未找到切换账号按钮")
                else:
                    print_warning("账号面板未打开")
            else:
                print_warning("未找到账号信息区域")
                
        except Exception as e:
            print_error(f"切换账号时发生错误: {str(e)}")
            return False 
    def GetCode(self,CallBack=None,Notice=None):
        self.Notice=Notice
        if  self.check_lock():
            print_warning("微信公众平台登录脚本正在运行，请勿重复运行")
            return {
                "code":f"{self.wx_login_url}?t={(time.time())}",
                "msg":"微信公众平台登录脚本正在运行，请勿重复运行！"}
       
        self.Clean()
        print("子线程执行中")
        from core.thread import ThreadManager
        self.thread = ThreadManager(target=self.wxLogin,args=(CallBack,False))  # 传入函数名
        self.thread.start()  # 启动线程
        from core.ver import VERSION
        print(f"微信公众平台登录 v{VERSION}")
        return WX_API.QRcode()
    
    wait_time=1
    def QRcode(self):
        return {
            "code":f"/{self.wx_login_url}?t={(time.time())}",
            "is_exists":self.GetHasCode(),
        }
    def refresh_task(self):
        try:
            self.controller.driver.refresh()
            self.Call_Success()
            # 检查登录状态
            if "home" not in self.controller.driver.current_url:
                print("检测到登录已过期，请重新登录")
                raise Exception(f"登录已经失效，请重新登录")
        except Exception as e:
            raise Exception(f"浏览器关闭")  # 重新抛出异常以便外部捕获处理
    def HasLogin(self):
        with self._login_lock:
            return self._haslogin
    def schedule_refresh(self):
        if self.refresh_interval <= 0:
            return
            
        with self._login_lock:
            if not self._haslogin or not hasattr(self, 'controller') or self.controller is None:
                return
                
        try:
            self.refresh_task()
            # 使用守护线程避免资源泄露
            timer = Timer(self.refresh_interval, self.schedule_refresh)
            timer.daemon = True
            timer.start()
        except Exception as e:
            print_error(f"定时刷新任务失败: {str(e)}")
            # 不再抛出异常，避免无限循环
    def Token(self, callback=None,isClose=True):
        try:
            self.CallBack = callback
            if not getStatus():
                print_warning("登录状态检查失败")
                return None
                
                
            from driver.token import wx_cfg
            token = str(wx_cfg.get("token", ""))
            if not token:
                print_warning("未找到有效的token")
                return None
            
            # 创建新的控制器实例避免线程冲突
            controller=self.controller
            controller.start_browser()    
            controller.open_url(f"{self.WX_HOME}?t=home/index&lang=zh_CN&token={token}")
            
            cookie = Store.load()
            if cookie:
                # 为每个cookie添加必要的domain字段
                for c in cookie:
                    if 'domain' not in c:
                        c['domain'] = '.weixin.qq.com'
                    if 'path' not in c:
                        c['path'] = '/'
                controller.add_cookies(cookie)
            # 为单个token cookie添加必要的字段
            token_cookie = {
                "name": "token", 
                "value": token,
                "domain": ".weixin.qq.com",
                "path": "/"
            }
            controller.add_cookie(token_cookie)
            page=controller.page
            qrcode = page.locator("#jumpUrl")
            qrcode.wait_for(state="visible", timeout=self.wait_time * 1000)
            qrcode.click()
            time.sleep(2)
            hasLogin=page.locator("body:has-text('使用账号登录')")
            if hasLogin.count()>0:
                self._haslogin=False
                return False
            return self.Call_Success()
        except ImportError as e:
            print_error(f"导入模块失败: {str(e)}")
            return None
        except Exception as e:
            print_error(f"Token操作失败: {str(e)}")
            return None
        finally:
            # 不在这里清理，让Call_Success处理清理
            if isClose:
                self.controller.cleanup()
            pass
    def isLock(self):             
        if self.isLock:
            if os.path.exists(self.wx_login_url):
                try:
                    size=os.path.getsize(self.wx_login_url)
                    return size>364
                except Exception as e:
                    print(f"二维码图片获取失败: {str(e)}")
        return self.isLock
    def wxLogin(self, CallBack=None, NeedExit=False):
        """
        微信公众平台登录流程：
        1. 检查依赖和环境
        2. 打开微信公众平台
        3. 全屏截图保存二维码
        4. 等待用户扫码登录
        5. 获取登录后的cookie和token
        6. 启动定时刷新线程(默认30分钟刷新一次)
        """
            
        # 使用上下文管理器确保资源清理
        try:
            if self.check_lock():
                print_warning("微信公众平台登录脚本正在运行，请勿重复运行")
                return None
                
            self.set_lock()
            
            with self._login_lock:
                self._haslogin = False
                
            # 清理现有资源
            self.cleanup_resources()
            
            self.controller=PlaywrightController()
            # 初始化浏览器控制器
            driver=self.controller
            # 启动浏览器并打开微信公众平台
            print_info("正在启动浏览器...")
            driver.start_browser()
            driver.open_url(self.WX_LOGIN)
            page=driver.page

            # from playwright.sync_api import sync_playwright
            # playwright=sync_playwright().start()
            # browser = playwright.chromium.launch()
            # context = browser.new_context()
            # page = context.new_page()
            # page.goto(self.WX_LOGIN)
            # 等待页面完全加载
            print_info("正在加载登录页面...")
            page.wait_for_load_state("networkidle")
            
            # 定位二维码区域
            qr_tag=".login__type__container__scan__qrcode"
            # 获取二维码图片URL
            qrcode = page.query_selector(qr_tag)
            code_src=qrcode.get_attribute("src")
            print("正在生成二维码图片...")
            print(f"code_src:{code_src}")
            # qrcode = page.query_selector(qr_tag)
           
            # 使用Playwright截图功能（添加异常处理）
            qrcode.screenshot(path=self.wx_login_url)

            print("二维码已保存为 wx_qrcode.png，请扫码登录...")
            self.HasCode=True
            if os.path.getsize(self.wx_login_url)<=364:
                raise Exception("二维码图片获取失败，请重新扫码")
            # 等待登录成功（检测二维码图片加载完成）
            print("等待扫码登录...")
            if self.Notice is not None:
                self.Notice()
           
            # # 监听页面导航事件
            def handle_frame_navigated(frame):
                current_url = frame.url
                if self.WX_HOME in current_url:
                    print(f"登录成功，正在获取cookie和token...")
            page.on('framenavigated', handle_frame_navigated)
            page.wait_for_event("framenavigated", timeout=60 * 1000)
           
            from .success import setStatus
            with self._login_lock:
                self._haslogin=True
            setStatus(True)
            self.CallBack=CallBack
            self.Call_Success()
        except Exception as e:
            if "Timeout" in str(e):
                print_warning("\n扫码登录超时，请重新运行程序进行扫码登录")
            else:
                print_error(f"\n错误发生: {str(e)}")
            self.SESSION=None
            return self.SESSION
        finally:
            self.release_lock()
            # 只有在NeedExit为True且未登录成功时才清理资源
            if NeedExit and 'controller' in locals() and not self._haslogin:
                self.controller.cleanup()
                self.Clean()
        return self.SESSION
    def format_token(self, cookies: list, token: str = ""):
        cookies_str=""
        for cookie in cookies:
            # print(f"{cookie['name']}={cookie['value']}")
            cookies_str+=f"{cookie['name']}={cookie['value']}; "
            if 'token' in cookie['name'].lower():
                token= token or cookie['value']
        # 计算 slave_sid cookie 有效时间
        cookie_expiry = expire(cookies)
        return{
                'cookies': cookies,
                'cookies_str': cookies_str,
                'token': token,
                'wx_login_url': self.wx_login_url,
                'expiry': cookie_expiry
            }
    def Call_Success(self):
        """处理登录成功后的回调逻辑"""
        if not hasattr(self, 'controller') or self.controller is None:
            print_error("浏览器控制器未初始化")
            return None
            
        # 获取token
        token = self.extract_token_from_requests()

        # 获取当前所有cookie
        cookies = self.controller.get_cookies()
        # print("\n获取到的Cookie:")
        self.SESSION=self.format_token(cookies,str(token))
        with self._login_lock:
            self._haslogin=False if self.SESSION["expiry"] is None else True
        # 登录成功后不立即清理二维码，保持浏览器运行
        if  self._haslogin:
            try:
            # 使用更健壮的选择器定位元素
                self.ext_data = self._extract_wechat_data()
            except Exception as e:
                print_error(f"获取公众号信息失败: {str(e)}")
                self.ext_data = None
            Store.save(cookies)
            print_success("登录成功！")
        else:
            print_warning("未登录！")
        
        # print(cookie_expiry)
        if self.CallBack is not None:
            self.CallBack(self.SESSION,self.ext_data)

        return self.SESSION 

    def _extract_wechat_data(self):
        """提取微信公众号数据，使用更健壮的选择器"""
        # 优先使用临时控制器，其次使用默认控制器
        controller = getattr(self, '_temp_controller', None) or self.controller
        
        if not controller or not controller.page:
            return {}
            
        page = controller.page
        data = {}
        
        # 使用更健壮的选择器，增加备选方案
        selectors = {
            "wx_app_name": [".weui-desktop_name", ".acount_box-nickname", ".account_box-panel-head__nickname"],
            "wx_logo": [".weui-desktop-account__img", ".weui-desktop-account__thumb", ".account_box-panel-head__thumb"],
            "wx_read_yesterday": [".weui-desktop-data-overview:nth-child(1) .weui-desktop-data-overview__desc span", ".weui-desktop-data-overview:first-child .weui-desktop-data-overview__desc span"],
            "wx_share_yesterday": [".weui-desktop-data-overview:nth-child(2) .weui-desktop-data-overview__desc span", ".weui-desktop-data-overview:nth-child(1) + .weui-desktop-data-overview .weui-desktop-data-overview__desc span"], 
            "wx_watch_yesterday": [".weui-desktop-data-overview:nth-child(3) .weui-desktop-data-overview__desc span", ".weui-desktop-data-overview:last-child .weui-desktop-data-overview__desc span"],
            "wx_yuan_count": [".original_cnt .weui-desktop-user_sum span", ".weui-desktop-user_sum.original_cnt span"],
            "wx_user_count": [".weui-desktop-user_sum:not(.original_cnt) span", ".weui-desktop-user_num .weui-desktop-user_sum span"]
        }
        
        for key, selector_list in selectors.items():
            data[key] = ""
            selector_found = False
            
            # 遍历备选选择器
            for selector in selector_list:
                try:
                    element = page.locator(selector)
                    # 先检查元素是否存在，再等待可见
                    if element.count() > 0:
                        element.wait_for(state="visible", timeout=2000)
                        if key == "wx_logo":
                            data[key] = element.get_attribute("src")
                        else:
                            data[key] = element.text_content()
                        selector_found = True
                        print_info(f"成功获取{key}，使用选择器: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not selector_found:
                print_warning(f"获取{key}失败: 所有选择器都无法定位到元素")
                # 对于特定字段，尝试更通用的方法
                if key == "wx_watch_yesterday":
                    try:
                        # 尝试获取所有.data-item .number元素
                        all_numbers = page.locator(".data-item .number")
                        count = all_numbers.count()
                        if count >= 3:
                            data[key] = all_numbers.nth(2).text_content()
                            print_info(f"使用通用方法获取{key}成功")
                        elif count > 0:
                            # 如果只有1-2个，取最后一个
                            data[key] = all_numbers.nth(count-1).text_content()
                            print_info(f"使用备用方法获取{key}成功")
                    except Exception as fallback_e:
                        print_error(f"备用方法也失败: {str(fallback_e)}")
                
        return data
    
    def cleanup_resources(self):
        """清理所有相关资源"""
        try:
            # 清理临时文件
            self.Clean()
                
            # 重置状态
            with self._login_lock:
                self._haslogin = False
                self.HasCode = False
                
            print_info("资源清理完成")
            return True
        except Exception as e:
            return False
            
    def Close(self):
        rel=False
        try:
            if hasattr(self, 'controller') and self.controller is not None:
                self.controller.cleanup()
                rel=True
        except Exception as e:
            print_warning("浏览器未启动或已关闭")
            pass
        return rel
    def Clean(self):
        try:
            os.remove(self.wx_login_url)
        except:
            pass
        finally:
           pass
           
    def expire_all_cookies(self):
        """设置所有cookie为过期状态"""
        try:
            if hasattr(self, 'controller') and hasattr(self.controller, 'context'):
                self.controller.context.clear_cookies()
                return True
            else:
                print("浏览器未启动，无法操作cookie")
                return False
        except Exception as e:
            print(f"设置cookie过期时出错: {str(e)}")
            return False
            
    def check_lock(self):
        """检查锁定状态"""
        time.sleep(1)
        return os.path.exists(self.lock_file_path)
        
    def set_lock(self):
        """创建锁定文件"""
        with open(self.lock_file_path, 'w') as f:
            f.write(str(time.time()))
        self.isLOCK = True
        
    def release_lock(self):
        """删除锁定文件"""
        try:
            os.remove(self.lock_file_path)
            self.isLOCK = False
            return True
        except:
            return False


WX_API = Wx()
def GetCode(CallBack:any=None,NeedExit=True):
    WX_API.GetCode(CallBack,NeedExit=NeedExit)