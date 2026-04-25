from driver.base import WX_API
from core.config import cfg
from jobs.notice import sys_notice
from driver.success import Success
import time
def send_wx_code(title:str="",url:str=""):
    if cfg.get("server.send_code",False):
        WX_API.GetCode(Notice=CallBackNotice,CallBack=Success)
    pass
def CallBackNotice(data=None,ext_data=None):
        url=WX_API.QRcode()['code']
        svg="""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
        <rect x="10" y="10" width="180" height="180" fill="#ffcc00" stroke="#000" stroke-width="2"/>
        </svg>
        """
        rss_domain=str(cfg.get("rss.base_url",""))
        url=rss_domain+str(url)
        text=f"- 服务名：{cfg.get('server.name','')}\n"
        text+=f"- 发送时间： {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))}"
        if WX_API.GetHasCode():
            text+=f"![二维码]({url})"
            text+=f"\n- 请使用微信扫描二维码进行授权"
        sys_notice(text, str(cfg.get("server.code_title","WeRss授权过期,扫码授权")))