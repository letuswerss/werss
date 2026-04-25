
import os
from core.config import cfg
print(bool(cfg.get("server.auth_web", False)) )
if bool(cfg.get("server.auth_web", False)) == True:
    from driver.wx import WX_API 
    from driver.wx import Wx as WX_InterFace
else:
    from driver.wx_api import WeChat_api as WX_API
    from driver.wx_api import WeChatAPI as WX_InterFace
