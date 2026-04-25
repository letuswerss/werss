"""
微信公众平台API登录模块
基于 https://github.com/wechat-article/wechat-article-exporter 项目实现
提供二维码登录、token管理、cookie管理等功能
"""
from ast import Call
import os
# import traceback
import re
import time
import json
import base64
from urllib import response
from attr import s
import requests
from typing import Optional, Dict, Any, Callable
from threading import Lock, Timer
from PIL import Image
import qrcode
from io import BytesIO

from sqlalchemy import true

from core.print import print_warning
from .token import get as get_token,set_token
import logging
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeChatAPI:
    """微信公众平台API登录类"""
    
    def __init__(self):
        self.base_url = "https://mp.weixin.qq.com"
        self.login_url = f"{self.base_url}/"
        self.home_url = f"{self.base_url}/cgi-bin/home"
        # 状态管理
        self._islogin=False
        self.is_logged_in = False
        self.fingerprint = self._generate_uuid()
        self.session = requests.Session()
        self.token = None
        self.cookies_dict=[]
        self.cookies:Optional[Dict[str,str]] = {}
        self.qr_code_path = "static/wx_qrcode.png"
        self.wx_login_url=f"{self.qr_code_path}"
        # 线程安全
        self._lock = Lock()
        self._login_in_progress = False
        self._heartbeat_timer = None
        
        # 回调函数
        self.login_callback :Optional[Callable] = None
        self.notice_callback = None
        
        # 确保静态目录存在
        self.qr_code_path = os.path.abspath("static/wx_qrcode.png")
        os.makedirs(os.path.dirname(self.qr_code_path), exist_ok=True)
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://mp.weixin.qq.com/'
        })
     
    def get_qr_code(self, callback: Optional[Callable] = None, notice: Optional[Callable] = None) -> Dict[str, Any]:
        """
        获取登录二维码
        
        Args:
            callback: 登录成功后的回调函数
            notice: 通知回调函数
            
        Returns:
            包含二维码信息的字典
        """
        if self._login_in_progress:
            logger.info("登录流程已在进行中，跳过重复发起")
            return {
                'code': f"{self.qr_code_path}?t={int(time.time())}" if os.path.exists(self.qr_code_path) else None,
                'is_exists': os.path.exists(self.qr_code_path),
                'msg': '登录流程已在进行中，请等待扫码'
            }
        self.__init__()
        self._login_in_progress = True
        with self._lock:
            self.login_callback = callback
            self.notice_callback = notice
            
            try:
                # 获取登录页面
                response = self.session.get(self.login_url)
                response.raise_for_status()
                
                # 解析页面获取二维码相关信息
                qr_info = self._extract_qr_info(response.text)
                
                if qr_info:
                    # 生成二维码图片
                    self._generate_qr_image(qr_info['qr_url'])
                    
                    # 启动登录状态检查
                    self._start_login_check(qr_info['uuid'])
                    
                    return {
                        'code': f"{self.qr_code_path}?t={int(time.time())}",
                        'is_exists': os.path.exists(self.qr_code_path),
                        'uuid': qr_info['uuid'],
                        'msg': '请使用微信扫描二维码登录'
                    }
                else:
                    self._login_in_progress = False
                    return {
                        'code': None,
                        'is_exists': False,
                        'msg': '获取二维码失败'
                    }
                    
            except Exception as e:
                self._login_in_progress = False
                logger.error(f"获取二维码失败: {str(e)}")
                return {
                    'code': None,
                    'is_exists': False,
                    'msg': f'获取二维码失败: {str(e)}'
                }

    def _extract_qr_info(self, html_content: str) -> Optional[Dict[str, str]]:
        """
        从HTML内容中提取二维码信息
        
        Args:
            html_content: 登录页面HTML内容
            
        Returns:
            包含二维码URL和UUID的字典
        """
        try:
            # 使用更灵活的正则表达式匹配二维码URL和UUID
            import re
            
            # 查找二维码URL
            qr_pattern = r'(https?:\/\/mp\.weixin\.qq\.com\/cgi-bin\/loginqrcode\?action=getqrcode&param=\d+)'
            qr_match = re.search(qr_pattern, html_content)
            
            # 查找UUID
            uuid_pattern = r'(?:"|\')uuid(?:"|\')\s*:\s*(?:"|\')([^"\']+)(?:"|\')'
            uuid_match = re.search(uuid_pattern, html_content)
            
            if qr_match and uuid_match:
                return {
                    'qr_url': qr_match.group(1),
                    'uuid': uuid_match.group(1)
                }
            
            # 如果没有找到，尝试其他方式获取
            return self._get_qr_info_api()
            
        except Exception as e:
            logger.error(f"解析二维码信息失败: {str(e)}")
            return None

    def _get_qr_info_api(self) -> Optional[Dict[str, str]]:
        """
        通过API获取二维码信息
        
        Returns:
            包含二维码URL和UUID的字典
        """
        try:
            # 首先访问登录页面，模拟浏览器打开行为
            logger.info("模拟浏览器访问登录页面...")
            login_response = self.session.get(self.login_url)
            login_response.raise_for_status()
            session = self.session
            # 设置更完整的浏览器请求头
            browser_headers = {
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin',
                "Sec-Fetch-Mode": "navigate",
                "Upgrade-Insecure-Requests": "1",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.login_url
            }
            
            # 更新session请求头
            session.headers.update(browser_headers)
            
            # 启动登录流程获取UUID
            uuid = self.start_login()
            if not uuid:
                uuid = self._generate_uuid()
            
            # 构建二维码请求URL，模拟浏览器请求
            timestamp = int(time.time() * 1000)  # 使用毫秒时间戳
            qr_api_url = f"{self.base_url}/cgi-bin/scanloginqrcode?action=getqrcode&uuid={uuid}&random={timestamp}"
            

          
            
            logger.info(f"请求二维码: {qr_api_url}")
            logger.info(f"使用UUID: {uuid}")
            # 发送请求获取二维码
            response = session.get(qr_api_url,  allow_redirects=False)
            
            # 检查响应状态
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                # 检查是否返回图片
                if 'image/' in content_type:
                    # 验证图片数据有效性
                    try:
                        from PIL import Image
                        Image.open(BytesIO(response.content))
                        
                        # 保存二维码图片
                        with open(self.qr_code_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"二维码获取成功，已保存到: {self.qr_code_path}")
                        
                        return {
                            'qr_url': f"{qr_api_url}?",
                            'uuid': uuid
                        }
                        
                    except Exception as e:
                        logger.error(f"二维码图片数据无效: {str(e)}")
                        
                else:
                    logger.warning(f"响应不是图片格式: {content_type}")
                    logger.debug(f"响应内容: {response.text[:200]}...")
            
            elif response.status_code == 302:
                # 处理重定向
                redirect_url = response.headers.get('Location')
                logger.info(f"收到重定向: {redirect_url}")
                
                if redirect_url:
                    redirect_response = self.session.get(redirect_url)
                    if redirect_response.status_code == 200 and 'image/' in redirect_response.headers.get('Content-Type', ''):
                        with open(self.qr_code_path, 'wb') as f:
                            f.write(redirect_response.content)
                        
                        return {
                            'qr_url': redirect_url,
                            'uuid': uuid
                        }
            
            else:
                logger.error(f"请求失败: 状态码={response.status_code}")
                logger.debug(f"响应头: {dict(response.headers)}")
                logger.debug(f"响应内容: {response.text[:500]}...")
            
            
        except Exception as e:
            logger.error(f"API获取二维码失败: {str(e)}")
    #开始登录 
    def start_login(self):
        """
        启动登录流程
        """
        uuid=self._generate_uuid()
        self.session.cookies.set("uuid",uuid)
        token=self.session.cookies.get("token","")
        url=f"{self.base_url}/cgi-bin/bizlogin?action=startlogin"
        fingerprint=self._generate_uuid()
        data={
            "fingerprint": fingerprint,
            "token": token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "redirect_url": f"/cgi-bin/settingpage?t=setting/index&amp;action=index&amp;token={token}&amp;lang=zh_CN",
            "login_type": "3",
        }
        response=self.session.post(url,data=data)
          # 从响应头或Cookie中获取UUID
        uuid = response.cookies.get('uuid') or response.headers.get('X-UUID') 
        return uuid
    
    def pre_login(self):
        """
        启动登录流程
        """
        uuid=self._generate_uuid()
        self.session.cookies.set("uuid",uuid)
        url=f"{self.base_url}/cgi-bin/bizlogin"
        params={
            "action": "prelogin",
            "fingerprint": self._generate_uuid(),
            "token": "",
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }
        response=self.session.get(url,params=params)
          # 从响应头或Cookie中获取UUID
        uuid = response.cookies.get('uuid') or response.headers.get('X-UUID') 
        return uuid
        

    def _generate_uuid(self) -> str:
        """
        生成UUID
        
        Returns:
            UUID字符串
        """
        import uuid
        return str(uuid.uuid4()).replace('-', '')
    
    def _generate_qr_image(self, qr_url: str):
        """
        生成二维码图片
        
        Args:
            qr_url: 二维码URL
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.qr_code_path), exist_ok=True)
            
            # 如果是完整的URL，直接下载
            if qr_url.startswith('http'):
                response = self.session.get(qr_url)
                response.raise_for_status()
                
                with open(self.qr_code_path, 'wb') as f:
                    f.write(response.content)
            else:
                # 如果是数据，生成二维码
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # 确保图片格式正确
                if not self.qr_code_path.lower().endswith('.png'):
                    self.qr_code_path = os.path.splitext(self.qr_code_path)[0] + '.png'
                
                # 使用BytesIO临时保存图片，确保编码正确
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                
                # 写入文件
                with open(self.qr_code_path, 'wb') as f:
                    f.write(buffer.getvalue())
                
            logger.info(f"二维码已保存到: {self.qr_code_path}")
            
        except Exception as e:
            logger.error(f"生成二维码图片失败: {str(e)}")

    def _start_login_check(self, uuid: str):
        """
        启动登录状态检查，最多轮询5分钟（150次 x 2秒）
        
        Args:
            uuid: 二维码UUID
        """
        max_attempts = 150
        attempt_count = [0]
        error_count = [0]
        max_consecutive_errors = 3
        last_status = [None]

        def check_login():
            attempt_count[0] += 1

            if attempt_count[0] > max_attempts:
                logger.warning(f"二维码轮询超时（已等待 {max_attempts * 2} 秒），停止检查")
                self._clean_qr_code()
                self._login_in_progress = False
                if self.notice_callback:
                    self.notice_callback('二维码已超时，请重新获取')
                return

            try:
                status = self._check_login_status(uuid)

                if status != last_status[0]:
                    logger.info(f"登录状态变化: {last_status[0]} -> {status} (第{attempt_count[0]}次)")
                    last_status[0] = status

                if status == 'success':
                    self._islogin = True
                    self._login_in_progress = False
                    error_count[0] = 0
                    self._handle_login_success()
                elif status == 'scanned':
                    error_count[0] = 0
                    if self.notice_callback:
                        self.notice_callback('已扫描，请在手机上确认登录')
                    Timer(2.0, check_login).start()
                elif status == 'not_exists':
                    logger.info("二维码文件不存在，停止轮询")
                    self._login_in_progress = False
                    return
                elif status == 'expired':
                    logger.info("二维码已过期")
                    self._clean_qr_code()
                    self._login_in_progress = False
                    if self.notice_callback:
                        self.notice_callback('二维码已过期，请重新获取')
                    return
                elif status in ('invalid session', 'error'):
                    error_count[0] += 1
                    if error_count[0] >= max_consecutive_errors:
                        logger.error(f"连续 {error_count[0]} 次错误（{status}），停止轮询")
                        self._clean_qr_code()
                        self._login_in_progress = False
                        if self.notice_callback:
                            self.notice_callback('登录检查失败，请重新获取二维码')
                        return
                    Timer(3.0, check_login).start()
                else:
                    error_count[0] = 0
                    Timer(2.0, check_login).start()

            except Exception as e:
                logger.error(f"检查登录状态异常: {str(e)}")
                error_count[0] += 1
                if error_count[0] >= max_consecutive_errors:
                    logger.error("连续异常过多，停止轮询")
                    self._login_in_progress = False
                    if self.notice_callback:
                        self.notice_callback('检查登录状态失败,请重试')
                    return
                Timer(3.0, check_login).start()

        Timer(2.0, check_login).start()

    def _check_login_status(self, uuid: str) -> str:
        """
        检查登录状态
        
        Args:
            uuid: 二维码UUID
            
        Returns:
            登录状态: 'wait', 'scanned', 'success', 'expired', 'not_exists',
                      'invalid session', 'error'
        """
        try:
            if not os.path.exists(self.qr_code_path):
                return "not_exists"
            check_url = f"{self.base_url}/cgi-bin/scanloginqrcode"
            self.fingerprint = self.cookies.get("fingerprint") or self._generate_uuid()
            params = {
                "action": "ask",
                "fingerprint": self.fingerprint,
                "lang": "zh_CN",
                "f": "json",
                "ajax": 1
            }
            
            response = self.session.get(check_url, params=params)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                status = data.get('status', 0)
                if "invalid session" in str(data).lower():
                    return 'invalid session'
                if status == 1:
                    with self._lock:
                        self.cookies = requests.utils.dict_from_cookiejar(self.session.cookies) if self.session.cookies else {}
                    return 'success'
                elif status == 2:
                    return 'scanned'
                elif status == 3:
                    return 'success'
                elif status == 4:
                    return 'scanned'
                else:
                    return 'wait'
                    
        except Exception as e:
            logger.error(f"检查登录状态失败: {str(e)}")
            return 'error'

    def _handle_login_success(self):
        """
        处理登录成功
        """
        try:
            self.is_logged_in = True
            
            # 获取token和cookies
            self._extract_login_info()
            
            # 清理二维码文件
            self._clean_qr_code()
            from driver.cookies import expire
            # 调用成功回调
            if self._get_account_info() is not None:
                logger.info("登录成功！")
                self._start_heartbeat()
                return True
        except Exception as e:
            logger.error(f"处理登录失败: {str(e)}")
        return False

    def _start_heartbeat(self):
        """登录成功后启动心跳保活，每15分钟请求一次非敏感接口"""
        self._stop_heartbeat()
        heartbeat_interval = 900  # 15分钟

        def heartbeat():
            if not self.is_logged_in:
                logger.info("已登出，心跳停止")
                return
            try:
                result = self._get_account_list()
                if result and result.get('base_resp', {}).get('ret') == 0:
                    logger.debug("心跳保活成功")
                    timer = Timer(heartbeat_interval, heartbeat)
                    timer.daemon = True
                    timer.start()
                    self._heartbeat_timer = timer
                else:
                    ret = result.get('base_resp', {}).get('ret') if result else 'None'
                    logger.warning(f"心跳检测到 Session 失效 (ret={ret})")
                    self._on_session_expired()
            except Exception as e:
                logger.error(f"心跳请求失败: {e}")
                self._on_session_expired()

        logger.info(f"启动心跳保活（间隔 {heartbeat_interval}s）")
        timer = Timer(heartbeat_interval, heartbeat)
        timer.daemon = True
        timer.start()
        self._heartbeat_timer = timer

    def _stop_heartbeat(self):
        """停止心跳定时器"""
        if self._heartbeat_timer:
            try:
                self._heartbeat_timer.cancel()
            except Exception:
                pass
            self._heartbeat_timer = None

    def _on_session_expired(self):
        """Session 过期时的统一处理"""
        self._stop_heartbeat()
        self.is_logged_in = False
        self._islogin = False
        from driver.success import setStatus
        setStatus(False)
        logger.warning("Session 已过期，标记为未登录状态")
        from jobs.failauth import send_wx_code
        import threading
        threading.Thread(target=send_wx_code, args=("心跳检测到Session过期，请重新扫码登录",)).start()
    def _extract_login_info(self):
        """
        提取登录信息（token和cookies）
        """
        try:
            # 访问首页获取token
            # https://mp.weixin.qq.com/cgi-bin/loginpage?url=%2Fcgi-bin%2Fhome
            # https://mp.weixin.qq.com/cgi-bin/bizlogin?action=login
            
            # 执行登录POST请求
            login_data = {
                "userlang": "zh_CN",
                "redirect_url": "",
                "cookie_forbidden": "0",
                "cookie_cleaned": "0", 
                "plugin_used": "0",
                "login_type": "3",
                "fingerprint": self.fingerprint,
                "token": "",
                "lang": "zh_CN",
                "f": "json",
                "ajax": "1"
            }
            
            # 发送登录请求
            response = self.session.post(
                "https://mp.weixin.qq.com/cgi-bin/bizlogin?action=login",
                data=login_data
            )
            

            response.raise_for_status()
            self.cookies = requests.utils.dict_from_cookiejar(self.session.cookies) if self.session.cookies else {}
            print(self.cookies)
            # 从URL或页面内容中提取token
            import re
            token_match = re.search(r'token=([^&\s"\']+)', response.text)
            if token_match:
                self.token = token_match.group(1)
            
            
        except Exception as e:
            logger.error(f"提取登录信息失败: {str(e)}")

    def _cookie_string_to_dict(self,cookie_string: str) -> Dict[str, str]:
        """
        将cookie字符串转换为字典格式
        """
        cookie_dict = {}
        
        if not cookie_string or not isinstance(cookie_string, str):
            return cookie_dict
        
        # 按分号分割cookie字符串
        cookie_pairs = cookie_string.split(';')
        
        for pair in cookie_pairs:
            # 去除首尾空格
            pair = pair.strip()
            if not pair:
                continue
                
            # 按等号分割键值对
            if '=' in pair:
                key, value = pair.split('=', 1)  # 只分割第一个等号
                cookie_dict[key.strip()] = value.strip()
            else:
                # 如果没有等号，将整个字符串作为key，值为空字符串
                cookie_dict[pair] = ""
        
        return cookie_dict
    def _format_cookies_string(self) -> str:
        """
        格式化cookies为字符串
        
        Returns:
            cookies字符串
        """
        return '; '.join([f"{k}={v}" for k, v in self.cookies.items()])

    def _calculate_expiry(self) -> Optional[float]:
        """
        计算cookies过期时间
        
        Returns:
            过期时间戳
        """
        try:
            # 查找有过期时间的cookie
            for cookie in self.session.cookies:
                if cookie.expires:
                    return cookie.expires
            
            # 如果没有找到，返回默认过期时间（24小时后）
            return time.time() + 24 * 3600
            
        except Exception as e:
            logger.error(f"计算过期时间失败: {str(e)}")
            return None
    def get_cookie_expires(self,cookies):
        try:
            # 将cookie转换为字典
            cookies_dict =[]
            for cookie in cookies:
                if cookie.expires:
                    expiry_time = cookie.expires
                    cookies_dict.append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'expires': expiry_time
                    })
        except requests.exceptions.RequestException as e:
            logger.error(f"获取cookie过期时间失败: {str(e)}")   
        return cookies_dict
        
    def _get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        获取账号信息
        
        Returns:
            账号信息字典
        """
        try:
            # 这里需要根据实际页面结构获取账号信息
            response = self.session.get(self.home_url)
            response.raise_for_status()
            account_list=self._get_account_list()

            if account_list is None:
                logger.error("获取账号列表失败")
                return None
            # 提取 biz_list 的第一项数据
            biz_list=account_list['biz_list']['list']
            first_biz_item = biz_list[0] if len(biz_list) > 0 else None

            print(first_biz_item)
            # 解析账号信息（需要根据实际页面结构调整）
            account_info = {
                'wx_app_name': first_biz_item.get('username',''),
                'wx_logo': first_biz_item.get('headimgurl',''),
                'wx_read_yesterday': 0,
                'wx_share_yesterday': 0,
                'wx_watch_yesterday': 0,
                'wx_yuan_count': 0,
                'wx_user_count': 0
            }
            from driver.cookies import expire
            # 将cookie转换为字典
            login_data = {
                            'cookies': self.cookies,
                            'cookies_str': self._format_cookies_string(),
                            'token': self.token,
                            'fingerprint': self.fingerprint,
                            'wx_login_url': self.qr_code_path,
                            'expiry': expire(self.cookies_dict)
            }
            set_token(login_data,account_info)
            if self.login_callback:
                self.login_callback(login_data, account_info)
            return account_info
            
        except Exception as e:
            logger.error(f"获取账号信息失败: {str(e)}")
            return None

    def switch_account(self,username:str=""):
        """切换微信公众号账号"""
        self.login_with_token()
        url = f"{self.base_url}/cgi-bin/switchacct?action=switch"
        
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"130\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest",
        }
        headers["Referer"]=f"{self.base_url}/cgi-bin/home?t=home/index&lang=zh_CN&token={self.token}"
        params = {
            "f": "json",
            "username": username,
            "fingerprint": self.fingerprint,
            "token": self.token,
            "lang": "zh_CN",
            "ajax": "1"
        }
        
        try:
            response =  self.session.post(
                url, 
                headers=headers, 
                data=params,
                cookies={},
                allow_redirects=True
            )
            
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析JSON响应
            data = response.json()
            print("切换账号响应:", data)
            if data.get("base_resp").get("ret") == 0:
                self._redirect()
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析出错: {e}")
        return None
    def _redirect(self):
        url=f"https://mp.weixin.qq.com/cgi-bin/loginpage?url=/cgi-bin/home?t=home/index&lang=zh_CN&token={self.token}"
        response=self.session.get(url)
        response.raise_for_status()
        self.cookies = requests.utils.dict_from_cookiejar(response.cookies) if response.cookies else {}
        self.session.cookies.update(self.cookies)
        self.token=self.cookies.get("token")
        self._handle_login_success()

    def _get_account_list(self) -> Optional[Dict[str, Any]]:
        """
        获取账号列表
        
        Args:
            fingerprint: 指纹参数
            
        Returns:
            账号列表信息字典
        """
        try:
            if not self.token:
                logger.error("未获取到token，无法获取账号列表")
                return None
                
            # 构建请求URL
            url = f"{self.base_url}/cgi-bin/switchacct"
            self.fingerprint=self.cookies.get("fingerprint") or self._generate_uuid()
            # 设置请求参数
            params = {
                'action': 'get_acct_list',
                'fingerprint': self.fingerprint,
                'token': self.token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1'
            }
            # 设置请求头
            headers = {
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'sec-ch-ua': '"Not?A_Brand";v="99", "Chromium";v="130"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-requested-with': 'XMLHttpRequest'
            }
            
            # 设置referrer
            referrer = f"{self.base_url}/cgi-bin/home?t=home/index&lang=zh_CN&token={self.token}"
            headers['Referer'] = referrer
            
            # 发送GET请求
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            self.cookies_dict=self.get_cookie_expires(response.cookies)
            # 解析JSON响应
            result = response.json()
            if 'base_resp' in result and result['base_resp']['ret'] == 0:
                # logger.info(f"获取账号列表成功: {result}")
                return result
            else:
                logger.warning(f"获取账号列表失败: {result['base_resp']}")
            return None
            
        except Exception as e:
            logger.error(f"获取账号列表失败: {str(e)}")
            return None

    def _clean_qr_code(self):
        """
        清理二维码文件
        """
        try:
            if os.path.exists(self.qr_code_path):
                os.remove(self.qr_code_path)
        except Exception as e:
            logger.error(f"清理二维码文件失败: {str(e)}")

    def login_with_token(self, token: str="", cookies:Any = None) -> bool:
        """
        使用token登录
        
        Args:
            token: 登录token
            cookies: cookies字典
            
        Returns:
            是否登录成功
        """
        try:
            with self._lock:

                token=token or get_token("token")
                cookies=cookies or self._cookie_string_to_dict(get_token("cookie"))
                logger.info(f"尝试 Token 登录 (token={token[:8]}...)" if token else "Token 为空")
                self.token = token
                
                if cookies:
                    self.session.cookies.update(cookies)
                    self.cookies = cookies
                
                # 验证登录状态
                response = self.session.get(f"{self.home_url}?token={token}")
                response.raise_for_status()
                if token=="" or token is None:
                    print_warning("未登录，请扫码")
                    return False
               
                if 'home'  in response.url:
                    self.is_logged_in = True
                    logger.info("Token登录成功")
                    return self._handle_login_success()
                else:
                    logger.warning("Token登录失败")
                    return False
                    
        except Exception as e:
            logger.error(f"Token登录失败: {str(e)}")
            raise e
            return False

    def logout(self):
        """
        登出
        """
        self._stop_heartbeat()
        with self._lock:
            self.is_logged_in = False
            self._islogin = False
            self.token = None
            self.cookies = {}
            self.session.cookies.clear()
            self._clean_qr_code()
            logger.info("已登出")

    def is_login_valid(self) -> bool:
        """
        检查登录是否有效
        
        Returns:
            登录是否有效
        """
        if not self.is_logged_in or not self.token:
            return False
        
        try:
            response = self.session.get(f"{self.home_url}?token={self.token}")
            return 'home' in response.url
        except:
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话信息
        
        Returns:
            会话信息字典
        """
        return {
            'is_logged_in': self.is_logged_in,
            'token': self.token,
            'cookies': self.cookies,
            'cookies_str': self._format_cookies_string(),
            'expiry': self._calculate_expiry()
        }


    def Token(self,callback:Optional[Callable] = None):
        self.login_callback=callback
        rel= self.login_with_token()
        if rel==False:
            print_warning("未登录，Token登录失败")
        return rel
    def QRcode(self):
        return {
            "code":f"/{self.wx_login_url}?t={(time.time())}",
            "is_exists":self.GetHasCode(),
        }      
    def GetCode(self,CallBack=None,Notice=None):
        if self.GetHasCode():
            return {
                "code":f"/{self.wx_login_url}?t={(time.time())}",
                "is_exists":self.GetHasCode(),
            }
        from core.print import print_warning
        from core.thread import ThreadManager
        self.thread = ThreadManager(target=self.get_qr_code,args=(CallBack,Notice))  # 传入函数名
        self.thread.start()  # 启动线程
        from core.ver import VERSION
        print(f"微信公众平台登录 v{VERSION}")
        return {
            "code":f"/{self.wx_login_url}?t={(time.time())}",
            "is_exists":self.GetHasCode(),
        }
    def GetHasCode(self):
        if os.path.exists(self.wx_login_url):
            return True
        return False
    
    def HasLogin(self):
        return self._islogin and not self.GetHasCode()
    def Close(self):
        pass
# 创建全局实例
WeChat_api = WeChatAPI()


def get_qr_code(callback: Optional[Callable] = None, notice: Optional[Callable] = None) -> Dict[str, Any]:
    """
    获取登录二维码（全局函数）
    
    Args:
        callback: 登录成功回调函数
        notice: 通知回调函数
        
    Returns:
        二维码信息字典
    """
    return WeChat_api.get_qr_code(callback, notice)



def login_with_token(token:str="",cookies:Optional[Dict[str, str]]=None,login_callback: Optional[Callable] = None) -> bool:
    """
    使用token登录（全局函数）
    
    Args:
        token: 登录token
        cookies: cookies字典
        
    Returns:
        是否登录成功
    """
   
    
    WeChat_api.login_callback=login_callback
    return WeChat_api.login_with_token(token, cookies)


def get_session_info() -> Dict[str, Any]:
    """
    获取会话信息（全局函数）
    
    Returns:
        会话信息字典
    """
    return WeChat_api.get_session_info()


def logout():
    """
    登出（全局函数）
    """
    WeChat_api.logout()



if __name__ == "__main__":
    # 测试代码
    def login_success_callback(session_data, account_info):
        print("登录成功！")
        print(f"Token: {session_data.get('token')}")
        print(f"账号信息: {account_info}")
    
    def notice_callback(message):
        print(f"通知: {message}")
    
   
    
    # 保持程序运行以等待登录
    try:
         # 获取二维码
        result = WeChat_api.get_qr_code(login_success_callback, notice_callback)
        print(f"二维码结果: {result}")
        # while True:
        #     time.sleep(1)
    except KeyboardInterrupt:
        print("程序退出")
        logout()