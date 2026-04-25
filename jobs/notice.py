from core.config import cfg
import time
def sys_notice(text:str="",title:str="",tag:str='系统通知',type=""):
    from core.notice import notice
    markdown_text = f"### {title} {type} {tag}\n{text}"
    webhook = cfg.get('notice')['dingding']
    if len(webhook)>0:
        notice(webhook, title, markdown_text)
    feishu_webhook = cfg.get('notice')['feishu']
    if len(feishu_webhook)>0:
        notice(feishu_webhook, title, markdown_text)
    wechat_webhook = cfg.get('notice')['wechat']
    if len(wechat_webhook)>0:
        notice(wechat_webhook, title, markdown_text)
    custom_webhook = cfg.get('notice')['custom']
    if len(custom_webhook)>0:
        notice(custom_webhook, title, markdown_text)

