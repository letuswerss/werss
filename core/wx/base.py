import requests
import json
import re
from core.models import Feed
from core.db import DB
from core.models.feed import Feed
from .cfg import cfg,wx_cfg
from core.print import print_error,print_info
from core.rss import RSS
from driver.success import setStatus
from driver.wxarticle import Web
from core.log import logger
import random
# 定义一些常见的 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 11; Mobile; rv:89.0) Gecko/89.0 Firefox/89.0",
    # Chrome 桌面端
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    # Firefox 桌面端
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.4; rv:109.0) Gecko/20100101 Firefox/114.0",
    # Safari 桌面端
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    # Edge 桌面端
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67",
    # Android 移动端 Chrome
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    # Android 移动端 Firefox
    "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/114.0",
    # iOS 移动端 Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]
# 定义基类
class WxGather:
    articles=[]
    aids=[]
    def all_count(self):
        if getattr(self, 'articles', None) is not None:
            return len(self.articles)
        return 0
    def RecordAid(self,aid:str):
        self.aids.append(aid)
        pass
    def HasGathered(self,aid:str):
        if aid in self.aids:
            return True
        self.RecordAid(aid)
        return False
    def get_collect_start_date(self):
        """获取采集起始日期，用于在抓取时判断是否应该停止"""
        from datetime import datetime, date
        try:
            from core.models.config_management import ConfigManagement
            session = DB.get_session()
            try:
                config = session.query(ConfigManagement).filter(
                    ConfigManagement.config_key == 'collect_start_date'
                ).first()
                if config and config.config_value:
                    try:
                        start_date = datetime.strptime(config.config_value, '%Y-%m-%d').date()
                        return start_date
                    except (ValueError, TypeError):
                        pass
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"读取采集起始时间配置失败: {e}")
        # 默认值：2025-12-01
        return date(2025, 12, 1)
    def Model(self,type=None):
        type=type or cfg.get("gather.model","web")
        print(f"采集模式:{type}")
        if type=="app":
            from core.wx.model.app import MpsAppMsg
            wx=MpsAppMsg()
        elif type=="web":
            from core.wx.model.web import MpsWeb
            wx=MpsWeb()
        else:
            from core.wx.model.api import MpsApi
            wx=MpsApi()
        return wx
    def __init__(self,is_add:bool=False):
        self.articles=[]
        self.is_add=is_add
        self._cookies={}
        session=  requests.Session()
        timeout = (5, 10)  
        session.timeout = timeout
        self.session=session
        self.get_token()
    def get_token(self):
        cfg.reload()
        wx_cfg.reload()
        self.Gather_Content=cfg.get('gather.content',False)
        self.cookies = wx_cfg.get('cookie', '')
        self.token=wx_cfg.get('token','')
        # 随机选择一个 User-Agent
        self.user_agent = cfg.get('user_agent', '')
        user_agent = random.choice(USER_AGENTS)
        self.user_agent=user_agent
        self.headers = {
            "Cookie":self.cookies,
            "User-Agent": user_agent
        }
    def fix_header(self,url):
         user_agent = random.choice(USER_AGENTS)
          # 更新请求头
         headers = self.headers.copy()
         headers.update({
                "User-Agent": user_agent,
                "Refer": url,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            })
         return headers
    def content_extract(self,  url):
        text=""
        try:
            # 确保使用 requests.Session，而不是 SQLAlchemy Session
            requests_session = self.session
            # 更新请求头
            headers = self.fix_header(url)
            r = requests_session.get(url, headers=headers)
            if r.status_code == 200:
                text = r.text
                text=self.remove_common_html_elements(text)
                if "当前环境异常，完成验证后即可继续访问" in text:
                    print_error("当前环境异常，完成验证后即可继续访问")
                    text=""
        except:
            pass
        return text
    def FillBack(self,CallBack=None,data=None,Ext_Data=None):
        if CallBack is not None:
            if data is not  None:
                setStatus(True)
                from core.models import Article
                from datetime import datetime
                
                # 先构建文章ID，用于检查文章是否已存在
                article_id = str(data.get('id', ''))
                mp_id = data.get('mp_id', '')
                if article_id and mp_id:
                    # 构建完整的文章ID（与 add_article 中的逻辑一致）
                    full_article_id = f"{str(mp_id)}-{article_id}".replace("MP_WXS_","")
                else:
                    full_article_id = None
                
                # 先检查文章是否已存在，避免重复上传图片
                article_exists = False
                if full_article_id:
                    try:
                        import core.db as db
                        DB = db.Db(tag="文章检查")
                        session = DB.get_session()
                        existing_article = session.query(Article).filter(Article.id == full_article_id).first()
                        if existing_article is not None:
                            article_exists = True
                            logger.info(f"文章已存在，跳过图片上传: {full_article_id}")
                    except Exception as e:
                        logger.warning(f"检查文章是否存在时出错: {e}")
                        # 检查失败时继续处理，避免影响正常流程
                
                # 只有在文章不存在时才上传封面图片
                pic_url = data.get('cover', '')
                if pic_url and not article_exists:
                    try:
                        from core.storage.minio_client import MinIOClient, should_mirror_article_images
                        import re
                        minio_client = MinIOClient()
                        
                        # 从URL中提取文章ID（用于MinIO路径）
                        article_id_for_minio = article_id or "unknown"
                        if not article_id_for_minio or article_id_for_minio == "unknown":
                            # 尝试从link中提取
                            link = data.get('link', '')
                            if link:
                                match = re.search(r'/s/([^/?]+)', str(link))
                                if match:
                                    article_id_for_minio = match.group(1)
                        
                        # 若开启转存且 MinIO 可用，且封面图不是 MinIO URL，则上传
                        if should_mirror_article_images() and pic_url:
                            # 跳过已经是MinIO URL的图片
                            if 'minio' not in pic_url.lower() and (not minio_client.public_url or minio_client.public_url not in pic_url):
                                minio_cover_url = minio_client.upload_image(pic_url, article_id_for_minio)
                                if minio_cover_url:
                                    pic_url = minio_cover_url
                                    print_info(f"封面图片已上传到MinIO: {data.get('cover', '')[:80]}... -> {minio_cover_url[:80]}...")
                    except Exception as e:
                        logger.warning(f"处理封面图片失败: {e}")
                        # 失败时使用原始URL
                        pass
                elif article_exists:
                    # 如果文章已存在，尝试从现有文章中获取已上传的封面图URL
                    try:
                        import core.db as db
                        from core.storage.minio_client import MinIOClient
                        DB = db.Db(tag="文章检查")
                        session = DB.get_session()
                        existing_article = session.query(Article).filter(Article.id == full_article_id).first()
                        if existing_article and existing_article.pic_url:
                            # 如果现有文章已有MinIO URL，使用它
                            minio_client = MinIOClient()
                            if 'minio' in existing_article.pic_url.lower() or (minio_client.public_url and minio_client.public_url in existing_article.pic_url):
                                pic_url = existing_article.pic_url
                                logger.info(f"使用已存在的封面图URL: {pic_url[:80]}...")
                    except Exception as e:
                        logger.warning(f"获取已存在文章封面图失败: {e}")
                
                # 处理公众号头像上传到MinIO
                if mp_id:
                    try:
                        from core.storage.minio_client import MinIOClient, should_mirror_article_images
                        from core.models.feed import Feed
                        import core.db as db
                        minio_client = MinIOClient()
                        
                        # 检查data中是否有mp_info和logo
                        mp_info = data.get('mp_info', {})
                        logo_url = mp_info.get('logo') if isinstance(mp_info, dict) else None
                        
                        # 如果没有从data中获取到logo，检查Ext_Data中是否有
                        if not logo_url and Ext_Data:
                            mp_info_from_ext = Ext_Data.get('mp_info', {})
                            if isinstance(mp_info_from_ext, dict):
                                logo_url = mp_info_from_ext.get('logo')
                        
                        # 若开启转存且 MinIO 可用，尝试上传头像
                        if logo_url and should_mirror_article_images():
                            from core.storage.avatar_mirror import (
                                feed_cover_is_self_hosted,
                                is_wechat_image_cdn_url,
                            )

                            # 检查Feed表中是否已有自建/非微信 CDN 头像
                            DB = db.Db(tag="头像处理")
                            session = DB.get_session()
                            try:
                                feed = session.query(Feed).filter(Feed.id == mp_id).first()
                                if feed:
                                    existing_cover = feed.mp_cover or ""
                                    if feed_cover_is_self_hosted(existing_cover):
                                        logger.info(f"公众号 {mp_id} 已有非微信 CDN 头像，跳过上传")
                                    elif is_wechat_image_cdn_url(logo_url):
                                        minio_avatar_url = minio_client.upload_avatar(logo_url, mp_id)
                                        if minio_avatar_url:
                                            feed.mp_cover = minio_avatar_url
                                            session.commit()
                                            print_info(
                                                f"公众号头像已上传到MinIO: {logo_url[:80]}... -> {minio_avatar_url[:80]}..."
                                            )
                                        else:
                                            logger.warning(f"公众号头像上传到MinIO失败: {logo_url[:80]}...")
                                else:
                                    if is_wechat_image_cdn_url(logo_url):
                                        minio_avatar_url = minio_client.upload_avatar(logo_url, mp_id)
                                        if minio_avatar_url:
                                            print_info(
                                                f"公众号头像已上传到MinIO（Feed尚未创建）: {logo_url[:80]}... -> {minio_avatar_url[:80]}..."
                                            )
                            except Exception as e:
                                logger.warning(f"处理公众号头像失败: {e}")
                            finally:
                                session.close()
                    except Exception as e:
                        logger.warning(f"处理公众号头像时出错: {e}")
                        # 失败时继续处理，不影响文章处理流程
                
                art={
                    "id":str(data['id']),
                    "mp_id":data['mp_id'],
                    "title":data['title'],
                    "url":data['link'],
                    "pic_url":pic_url,
                    "content":data.get("content",""),
                    "publish_time":data['update_time'],
                }
                if 'digest' in data:
                    art['description']=data['digest']
                if CallBack(art):
                    art["ext"]=Ext_Data
                    # art.pop("content")
                    self.articles.append(art)


    #通过公众号码平台接口查询公众号
    def search_Biz(self,kw:str="",limit=10,offset=0):

        self.get_token()
        url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        params = {
            "action": "search_biz",
            "begin":offset,
            "count": limit,
            "query": kw,
            "token":  self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }
        headers=self.fix_header(url)
        if self.token is None or self.token == "":
            self.Error("请先扫码登录公众号平台")
            return
        data={}
        try:
            response = requests.get(
            url,
            params=params,
            headers=headers,
            )
            response.raise_for_status()  # 检查状态码是否为200
            data = response.text  # 解析JSON数据
            msg = json.loads(data)  # 手动解析
            if msg['base_resp']['ret'] == 200013:
                self.Error("frequencey control, stop at {}".format(str(kw)))
                return
            if msg['base_resp']['ret'] != 0:
                self.Error("错误原因:{}:代码:{}".format(msg['base_resp']['err_msg'],msg['base_resp']['ret']),code="Invalid Session")
                return 
            if 'publish_page' in msg:
                msg['publish_page']=json.loads(msg['publish_page'])
        except Exception as e:
            print_error(f"请求失败: {e}")
            raise e
        return msg
    
    
    
    def Start(self,mp_id=None):
        self.articles=[]
        self.get_token()
        if self.token=="" or self.token is None:
             self.Error("请先扫码登录公众号平台")
             return
        import time
        self.update_mps(mp_id,Feed(
          sync_time=int(time.time()),
          update_time=int(time.time()),
        ))

    def Item_Over(self,item=None,CallBack=None):
        print(f"item end")
        _cookies=[{'name': c.name, 'value': c.value, 'domain': c.domain,'expiry':c.expires,'expires':c.expires} for c in self._cookies]
        _cookies.append({'name':'token','value':self.token})
        if CallBack is not None:
            CallBack(item)
        pass
    def Error(self,error:str,code=None):
        self.Over()
        if code=="Invalid Session":
            from driver.success import getStatus
            from core.queue import TaskQueue
            already_handling = not getStatus()
            setStatus(False)
            TaskQueue.clear_queue()
            if not already_handling:
                import threading
                from jobs.failauth import send_wx_code
                logger.warning(f"Session 失效，触发重新登录: {error}")
                threading.Thread(target=send_wx_code,args=(f"公众号平台登录失效,请重新登录",)).start()
            else:
                logger.info(f"Session 已标记失效，跳过重复触发登录: {error}")
            raise Exception(error)

    def Over(self,CallBack=None):
        if getattr(self, 'articles', None) is not None:
            print(f"成功{len(self.articles)}条")
            rss=RSS()
            mp_id=""
            try:
                mp_id=self.articles[0]['mp_id']
            except:
                pass
            rss.clear_cache(mp_id=mp_id)  
        if CallBack is not None:
            CallBack(self.articles)

    def dateformat(self,timestamp:any):
        from datetime import datetime, timezone
        # UTC时间对象
        utc_dt = datetime.fromtimestamp(int(timestamp), timezone.utc)
        t=(utc_dt.strftime("%Y-%m-%d %H:%M:%S")) 

        # UTC转本地时区
        local_dt = utc_dt.astimezone()
        t=(local_dt.strftime("%Y-%m-%d %H:%M:%S"))
        return t


    def remove_common_html_elements(self, html_content: str) -> str:
        html_content=Web.clean_article_content(html_content)
        return html_content

    # 更新公众号更新状态
    def update_mps(self,mp_id:str, mp:Feed):
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
                    print_error(f"未找到ID为{mp_id}的公众号记录")
            finally:
                pass
                
        except Exception as e:
            print_error(f"更新公众号状态失败: {e}")
            raise NotImplementedError(f"更新公众号状态失败:{str(e)}")