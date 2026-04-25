import requests
import json
import re
import datetime
from datetime import datetime, timezone
# from core.config import cfg
from .cfg import wx_cfg,cfg
import core.db as db

def dateformat(timestamp:any):
    # UTC时间对象
    utc_dt = datetime.fromtimestamp(int(timestamp), timezone.utc)
    t=(utc_dt.strftime("%Y-%m-%d %H:%M:%S")) 

    # UTC转本地时区
    local_dt = utc_dt.astimezone()
    t=(local_dt.strftime("%Y-%m-%d %H:%M:%S"))
    return t
def set_config(key:str,value:str):
    wx_cfg.set(key,value)
def save_config():
    wx_cfg.save_config()
#通过公众号码平台接口查询公众号
def search_Biz(kw:str="",limit=5,offset=0):
    url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
    params = {
        "action": "search_biz",
        "begin":offset,
        "count": limit,
        "query": kw,
        # "fingerprint": "023c1c8dd42b4d1b28655ddb475b78a8",
        "token":  cfg.get("token"),
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1"
    }
    headers = {
        "Cookie": cfg.get("cookie"),
        "User-Agent": cfg.get("user_agent")
    }
    data={}
    try:
        response = requests.get(
        url,
        params=params,
        headers=headers,
        )
        response.raise_for_status  # 检查状态码是否为200
        data = response.text  # 解析JSON数据
        data = json.loads(data)  # 手动解析
        
        data['publish_page']=json.loads(data['publish_page'])
    except Exception as e:
        print(f"请求失败: {e}")
    return data

from bs4 import BeautifulSoup
# 提取一篇文章的内容
def content_extract(url):
    headers = {
        "Cookie": cfg.get("cookie"),
        "User-Agent": cfg.get("user_agent")
    }
    r = requests.get(eval(url),headers=headers)
    if r.status_code == 200:
        text = r.text
        soup = BeautifulSoup(text, 'html.parser')
        # 找到内容
        js_content_div = soup.find('div', {'id': 'js_content'})
        # 移除style属性中的visibility: hidden;
        js_content_div.attrs.pop('style', None)
        # 找到所有的img标签
        img_tags = js_content_div.find_all('img')
        # 遍历每个img标签并修改属性，设置宽度为1080p
        for img_tag in img_tags:
            if 'data-src' in img_tag.attrs:
                img_tag['src'] = img_tag['data-src']
                del img_tag['data-src']
            if 'style' in img_tag.attrs:
                style = img_tag['style']
                # 使用正则表达式替换width属性
                style = re.sub(r'width\s*:\s*\d+\s*px', 'width: 1080px', style)
                img_tag['style'] = style
        return js_content_div.prettify()
    else:
        print("download error,status_code: ",r.status_code,"\n")
    return ""
#通过公众号接口获取公众号文章列表
def get_Articles(faker_id:str):
    headers = {
        "Cookie": wx_cfg.get("cookie"),
        "User-Agent": wx_cfg.get("user_agent")
    }
    params = {
        "sub": "list",
        "sub_action": "list_ex",
        "begin": 0,
        "count": cfg.get("count"),
        "fakeid": faker_id,
        "token": wx_cfg.get("token"),
        "lang": "zh_CN",
        "f": "json",
        "ajax": 1
    }
    url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
    headers = {
        "Cookie": wx_cfg.get("cookie"),
        "User-Agent": wx_cfg.get("user_agent")
    }
    data={}
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status  # 检查状态码是否为200
        data = response.text  # 解析JSON数据
        data = json.loads(data)  # 手动解析
        data['publish_page']=json.loads(data['publish_page'])
        data['publish_info']=json.loads(data['publish_info'])
    except Exception as e:
        print(f"请求失败: {e}",data)
    return data
#通过公众号文章链接获取公众号id
def get_id(url:str)->str:
    pattern = r"/([^/]+)$"  # 使用原始字符串避免转义问题
    match = re.search(pattern, url)
    if match:
        article_id = match.group(1)
        print(f"提取结果：{article_id}")  # 输出：5iq10fsH-5ZA9D1Uv4ciqQ
    else:
        print("未匹配到有效内容")
    return article_id


# 从公众号平台获取列表并更新数据库
def get_list(faker_id:str=None,mp_id:str=None,is_add:bool=False):
    articles=[]
    if is_add:
      import time
      update_mps(mp_id,Feed(
          sync_time=int(time.time()),
          update_time=int(time.time()),
          ))
    data=get_Articles(faker_id)
    try:
        data=data['publish_page']['publish_list']
        wx_db=db.Db(tag="获取公众号列表")
        wx_db.init(cfg.get('db'))
        for i in data:
            art=i['publish_info']
            art=json.loads(art)
            art=art['appmsgex']
            art=art[0]
            #    print(art,type(art),sep='\n\n')
            print(art['title'],art['cover'],art['link'],art['update_time'],art['create_time'],sep='\n',end='\n\n\n')
            article={           
            'id':get_id(art['link']),
            'mp_id':mp_id,
            'title':art['title'],
            'pic_url':art['cover'],
            'publish_time':art['update_time'],
            'created_at':dateformat(art['create_time']),
            'updated_at':dateformat(art['update_time']),
            'content': content_extract(art['link']),
            'is_export':0,
            }
            articles.append(article)
            if is_add:
                isOk=wx_db.add_article(article)
                print(f'添加成功{isOk}')
    except Exception as e:
        print(e,"出错了")
   
   
    return articles

from core.models import Feed
# 更新公众号更新状态
from core.db import DB
from core.models.feed import Feed

def update_mps(mp_id:str, mp:Feed):
    """更新公众号同步状态和时间信息
    
    Args:
        mp_id: 公众号ID
        mp: Feed对象，包含公众号信息
    """
    from datetime import datetime
    import time
    try:
        
        # 更新同步时间为当前时间
        current_time = int(time.time())
        update_data = {
            'sync_time': current_time,
            # 'updated_at': dateformat(current_time)
            'updated_at': datetime.now(),
        }
        
        # 如果有新文章时间，也更新update_time
        if hasattr(mp, 'update_time') and mp.update_time:
            update_data['update_time'] = mp.update_time
        if hasattr(mp,'status') and mp.status is not None:
            update_data['status']=mp.status

        # 获取数据库会话并执行更新
        session = DB.get_session()
        try:
            feed = session.query(Feed).filter(Feed.id == mp_id).first()
            if feed:
                for key, value in update_data.items():
                    print(f"更新公众号{mp_id}的{key}为{value}")
                    setattr(feed, key, value)
                session.commit()
            else:
                print(f"未找到ID为{mp_id}的公众号记录")
        finally:
           pass
            
    except Exception as e:
        print(f"更新公众号状态失败: {e}")
        raise
# if __name__ == "__main__":
#   data=get_list()