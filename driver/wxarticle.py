import random
from socket import timeout
from .playwright_driver import PlaywrightController
from typing import Any, Dict, Optional
from core.print import print_error,print_info,print_success,print_warning
import time
import base64
import re
import os
from datetime import datetime
from core.config import cfg

class WXArticleFetcher:
    """微信公众号文章获取器
    
    基于WX_API登录状态获取文章内容
    
    Attributes:
        wait_timeout: 显式等待超时时间(秒)
    """
    
    def __init__(self, wait_timeout: int = 10000):
        """初始化文章获取器"""
        self.wait_timeout = wait_timeout
        self.controller = PlaywrightController()
        if not self.controller:
            raise Exception("WebDriver未初始化或未登录")
    
    def convert_publish_time_to_timestamp(self, publish_time_str: str) -> int:
        """将发布时间字符串转换为时间戳
        
        Args:
            publish_time_str: 发布时间字符串，如 "2024-01-01" 或 "2024-01-01 12:30"
            
        Returns:
            时间戳（秒）
        """
        try:
            # 尝试解析不同的时间格式
            formats = [
                "%Y-%m-%d %H:%M:%S",  # 2024-01-01 12:30:45
                "%Y年%m月%d日 %H:%M",        # 2024年03月24日 17:14
                "%Y-%m-%d %H:%M",     # 2024-01-01 12:30
                "%Y-%m-%d",           # 2024-01-01
                "%Y年%m月%d日",        # 2024年01月01日
                "%m月%d日",            # 01月01日 (当年)
            ]
            
            for fmt in formats:
                try:
                    if fmt == "%m月%d日":
                        # 对于只有月日的格式，智能判断年份
                        current_date = datetime.now()
                        current_year = current_date.year
                        full_time_str = f"{current_year}年{publish_time_str}"
                        dt = datetime.strptime(full_time_str, "%Y年%m月%d日")
                        
                        # 如果解析出的日期在未来，使用上一年
                        if dt > current_date:
                            dt = dt.replace(year=current_year - 1)
                    else:
                        dt = datetime.strptime(publish_time_str, fmt)
                    return int(dt.timestamp())
                except ValueError:
                    continue
            
            # 如果所有格式都失败，返回当前时间戳
            print_warning(f"无法解析时间格式: {publish_time_str}，使用当前时间")
            return int(datetime.now().timestamp())
            
        except Exception as e:
            print_error(f"时间转换失败: {e}")
            return int(datetime.now().timestamp())
       
        
    def extract_biz_from_source(self, url: str, page=None) -> str:
        """从URL或页面源码中提取biz参数
        
        Args:
            url: 文章URL
            page: Playwright Page实例，可选
            
        Returns:
            biz参数值
        """
        # 尝试从URL中提取
        match = re.search(r'[?&]__biz=([^&]+)', url)
        if match:
            return match.group(1)
            
        # 从页面源码中提取（需要page参数）
        if page is None:
            if not hasattr(self, 'page') or self.page is None:
                return ""
            page = self.page
            
        try:
            # 从页面源码中查找biz信息
            page_source = page.content()
            print_info(f'开始解析Biz')
            biz_match = re.search(r'var biz = "([^"]+)"', page_source)
            if biz_match:
                return biz_match.group(1)
                
            # 尝试其他可能的biz存储位置
            biz_match = re.search(r'window\.__biz=([^&]+)', page_source)
            if biz_match:
                return biz_match.group(1)
            # biz_match=page.evaluate('() =>window.biz')
            return ""
            
        except Exception as e:
            print_error(f"从页面源码中提取biz参数失败: {e}")
            return ""
    def extract_id_from_url(self, url: str) -> str:
        """从微信文章URL中提取ID
        
        Args:
            url: 文章URL
            
        Returns:
            文章ID字符串，如果提取失败返回None
        """
        try:
            # 从URL中提取ID部分
            match = re.search(r'/s/([A-Za-z0-9_-]+)', url)
            if not match:
                return ""
                
            id_str = match.group(1)
            
            # 添加必要的填充
            padding = 4 - len(id_str) % 4
            if padding != 4:
                id_str += '=' * padding
                
            # 尝试解码base64
            try:
                id_number = base64.b64decode(id_str).decode("utf-8")
                return id_number
            except Exception as e:
                # 如果base64解码失败，返回原始ID字符串
                return id_str
                
        except Exception as e:
            print_error(f"提取文章ID失败: {e}")
            return ""

    def normalize_metric_count(self, value: Any) -> Optional[int]:
        """将页面或接口返回的数量文本规范化为整数。"""
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)

        text = str(value).strip()
        if not text:
            return None

        text = text.replace(",", "").replace("+", "").replace("次", "").strip()
        text = re.sub(r"^[^\d]+", "", text)
        if not text:
            return None

        unit = 1
        if text.endswith(("万", "w", "W")):
            unit = 10000
            text = text[:-1]
        elif text.endswith(("千", "k", "K")):
            unit = 1000
            text = text[:-1]

        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            return None

        try:
            return int(float(match.group(0)) * unit)
        except (TypeError, ValueError):
            return None

    def merge_metric_counts(self, target: Dict[str, Optional[int]], source: Dict[str, Any]) -> Dict[str, Optional[int]]:
        """用 source 中的有效数量补齐 target。"""
        for key, value in source.items():
            normalized = self.normalize_metric_count(value)
            if normalized is not None:
                target[key] = normalized
        return target

    def extract_metrics_from_json(self, payload: Any) -> Dict[str, Optional[int]]:
        """从接口返回 JSON 中递归提取热度数量。"""
        alias_map = {
            "read_count": {"read_count", "read_num", "readNum"},
            "like_count": {"like_count", "like_num", "likeNum", "up_num", "digg_count"},
            "looking_count": {"looking_count", "old_like_num", "oldLikeNum", "looking_count_num", "friend_like_num"},
            "comment_count": {"comment_count", "comment_num", "commentNum", "comments_count"},
            "share_count": {"share_count", "share_num", "shareNum", "forward_num", "repost_num"},
        }
        result: Dict[str, Optional[int]] = {
            "read_count": None,
            "like_count": None,
            "looking_count": None,
            "comment_count": None,
            "share_count": None,
        }

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    lowered = str(key).strip().lower()
                    for target_key, aliases in alias_map.items():
                        if lowered in {alias.lower() for alias in aliases}:
                            normalized = self.normalize_metric_count(value)
                            if normalized is not None:
                                result[target_key] = normalized
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(payload)
        return result

    def extract_article_metrics(self, page, response_metrics: Optional[Dict[str, Optional[int]]] = None) -> Dict[str, Optional[int]]:
        """从微信文章页提取阅读/点赞/在看/评论/分享数量。"""
        metrics: Dict[str, Optional[int]] = {
            "read_count": None,
            "like_count": None,
            "looking_count": None,
            "comment_count": None,
            "share_count": None,
        }
        if response_metrics:
            self.merge_metric_counts(metrics, response_metrics)

        selector_metrics = page.evaluate(
            """
            () => {
              const metricKeys = ['read_count', 'like_count', 'looking_count', 'comment_count', 'share_count'];
              const result = { read_count: null, like_count: null, looking_count: null, comment_count: null, share_count: null };
              const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
              };
              const pickText = (el) => {
                if (!el || !isVisible(el)) return '';
                const candidates = [
                  el.textContent || '',
                  el.getAttribute('data-num') || '',
                  el.getAttribute('data-count') || '',
                  el.getAttribute('aria-label') || '',
                  el.getAttribute('title') || '',
                ];
                return candidates.map((item) => String(item || '').trim()).find(Boolean) || '';
              };
              const selectorMap = {
                read_count: [
                  '#js_read_area3',
                  '#js_read_num3',
                  '#readNum3',
                  '[id*="readNum"]',
                  '[id*="read_num"]',
                  '[class*="read_num"]',
                ],
                like_count: [
                  '#js_like_btn .like_comment_primary_num',
                  '#js_like_area3 .like_comment_primary_num',
                  '#js_like_btn',
                  '[id*="like_btn"] .like_comment_primary_num',
                  '[id*="like"] [class*="num"]',
                  '[class*="like_comment_primary_num"]',
                ],
                looking_count: [
                  '#js_old_like_btn .like_comment_primary_num',
                  '#js_read_like_btn .like_comment_primary_num',
                  '#js_old_like_btn',
                  '[id*="old_like"] .like_comment_primary_num',
                  '[id*="old_like"]',
                  '[class*="old_like"] [class*="num"]',
                ],
                comment_count: [
                  '#js_cmt_btn .like_comment_primary_num',
                  '#js_comment_btn .like_comment_primary_num',
                  '#js_cmt_btn',
                  '#js_comment_btn',
                  '[id*="comment"] [class*="num"]',
                  '[id*="cmt"] [class*="num"]',
                ],
                share_count: [
                  '#js_share_btn .like_comment_primary_num',
                  '#js_share_appmsg .like_comment_primary_num',
                  '#js_share_btn',
                  '#js_share_appmsg',
                  '[id*="share"] [class*="num"]',
                  '[class*="share"] [class*="num"]',
                ],
              };

              for (const key of metricKeys) {
                for (const selector of selectorMap[key]) {
                  const el = document.querySelector(selector);
                  const text = pickText(el);
                  if (text) {
                    result[key] = text;
                    break;
                  }
                }
              }

              const bodyText = document.body?.innerText || '';
              const labelRegexMap = {
                read_count: [/阅读\\s*([0-9.,万wWkK+]+)/],
                like_count: [/(?:点赞|推荐)\\s*([0-9.,万wWkK+]+)/],
                looking_count: [/在看\\s*([0-9.,万wWkK+]+)/],
                comment_count: [/评论\\s*([0-9.,万wWkK+]+)/],
                share_count: [/(?:分享|转发)\\s*([0-9.,万wWkK+]+)/],
              };

              for (const key of metricKeys) {
                if (result[key]) continue;
                for (const pattern of labelRegexMap[key]) {
                  const match = bodyText.match(pattern);
                  if (match && match[1]) {
                    result[key] = match[1];
                    break;
                  }
                }
              }

              const attrHintMap = {
                like_count: ['like'],
                looking_count: ['old_like', 'read_like', 'watch', 'kan'],
                comment_count: ['comment', 'cmt'],
                share_count: ['share', 'forward', 'repost'],
              };

              const numericText = (text) => /^\\d+(?:[.,]\\d+)?(?:万|[wWkK])?$/.test((text || '').trim());
              const nodes = Array.from(document.querySelectorAll('button, a, div, span')).slice(-300);

              for (const [key, hints] of Object.entries(attrHintMap)) {
                if (result[key]) continue;
                for (const node of nodes) {
                  const attrs = [
                    node.id || '',
                    node.className || '',
                    node.getAttribute?.('aria-label') || '',
                    node.getAttribute?.('data-type') || '',
                    node.getAttribute?.('title') || '',
                  ].join(' ').toLowerCase();
                  if (!hints.some((hint) => attrs.includes(hint))) continue;

                  const text = pickText(node);
                  if (numericText(text)) {
                    result[key] = text;
                    break;
                  }

                  const child = Array.from(node.querySelectorAll('span, strong, em, i'))
                    .map((el) => pickText(el))
                    .find((value) => numericText(value));
                  if (child) {
                    result[key] = child;
                    break;
                  }
                }
              }

              return result;
            }
            """
        )
        if isinstance(selector_metrics, dict):
            self.merge_metric_counts(metrics, selector_metrics)

        return metrics

    def FixArticle(self, urls: list = [], mp_id: str = "") -> bool:
        """批量修复文章内容
        
        Args:
            urls: 文章URL列表，默认为示例URL
            mp_id: 公众号ID，可选
            
        Returns:
            操作是否成功
        """
        try:
            from jobs.article import UpdateArticle
            import core.db as db
            from core.models.article import Article
            
            # 设置默认URL列表
            if urls is []:
                urls = ["https://mp.weixin.qq.com/s/YTHUfxzWCjSRnfElEkL2Xg"]
                
            success_count = 0
            total_count = len(urls)
            DB = db.Db(tag="文章修复")
            
            for i, url in enumerate(urls, 1):
                if url=="":
                    continue
                print_info(f"正在处理第 {i}/{total_count} 篇文章: {url}")
                
                try:
                    # 先提取文章ID，检查文章是否已存在
                    article_id_from_url = self.extract_id_from_url(url)
                    article_exists = False
                    existing_article = None
                    
                    if article_id_from_url and mp_id:
                        # 构建完整的文章ID（与 add_article 中的逻辑一致）
                        full_article_id = f"{str(mp_id)}-{article_id_from_url}".replace("MP_WXS_","")
                        session = DB.get_session()
                        existing_article = session.query(Article).filter(Article.id == full_article_id).first()
                        if existing_article:
                            article_exists = True
                            # 检查文章是否已有完整内容
                            if existing_article.content and len(existing_article.content.strip()) > 0:
                                print_info(f"文章已存在且内容完整，跳过处理: {full_article_id}")
                                continue
                            else:
                                print_info(f"文章已存在但内容不完整，继续处理: {full_article_id}")
                    
                    # 如果文章已存在且内容完整，跳过处理（避免重复上传图片）
                    if article_exists and existing_article and existing_article.content and len(existing_article.content.strip()) > 0:
                        print_info(f"文章已存在且内容完整，跳过处理: {full_article_id}")
                        continue
                    
                    article_data = self.get_article_content(url)
                    
                    # 构建文章数据
                    article = {
                        "id": article_data.get('id'), 
                        "title": article_data.get('title'),
                        "mp_id": article_data.get('mp_id') if mp_id is None else mp_id, 
                        "publish_time": article_data.get('publish_time'),
                        "pic_url": article_data.get('pic_url'),
                        "content": article_data.get('content'),
                        "read_count": article_data.get('read_count'),
                        "like_count": article_data.get('like_count'),
                        "looking_count": article_data.get('looking_count'),
                        "comment_count": article_data.get('comment_count'),
                        "share_count": article_data.get('share_count'),
                        "url": url,
                    }
                    
                    # 删除content字段避免重复存储
                    content_backup = article_data.get('content', '')
                    del article_data['content']
                    
                    print_success(f"获取成功: {article_data}")
                    
                    # 更新文章
                    ok = UpdateArticle(article, check_exist=True)
                    if ok:
                        success_count += 1
                        print_info(f"已更新文章: {article_data.get('title', '未知标题')}")
                    else:
                        print_warning(f"更新失败（文章可能已存在）: {article_data.get('title', '未知标题')}")
                        
                    # 恢复content字段
                    article_data['content'] = content_backup
                    
                    # 避免请求过快，但只在非最后一个请求时等待
                    if i < total_count:
                        time.sleep(3)
                        
                except Exception as e:
                    print_error(f"处理文章失败 {url}: {e}")
                    continue
                    
            print_success(f"批量处理完成: 成功 {success_count}/{total_count}")
            return success_count > 0
            
        except Exception as e:
            print_error(f"批量修复文章失败: {e}")
            return False
        finally:
            self.Close() 
    async def async_get_article_content(self,url:str)->Dict:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            future = loop.run_in_executor(pool, self.get_article_content, url)
        return await future
    def get_article_content(self, url: str) -> Dict:
        """获取单篇文章详细内容
        
        Args:
            url: 文章URL (如: https://mp.weixin.qq.com/s/qfe2F6Dcw-uPXW_XW7UAIg)
            
        Returns:
            文章内容数据字典，包含:
            - title: 文章标题
            - author: 作者
            - publish_time: 发布时间
            - content: 正文HTML
            - images: 图片URL列表
            
        Raises:
            Exception: 如果未登录或获取内容失败
        """
        info={
                "id": self.extract_id_from_url(url),
                "title": "",
                "publish_time": "",
                "content": "",
                "images": "",
                "read_count": None,
                "like_count": None,
                "looking_count": None,
                "comment_count": None,
                "share_count": None,
                "mp_info":{
                "mp_name":"",   
                "logo":"",
                "biz": "",
                }
            }
        self.controller.start_browser()
       
        self.page = self.controller.page
        response_metrics: Dict[str, Optional[int]] = {
            "read_count": None,
            "like_count": None,
            "looking_count": None,
            "comment_count": None,
            "share_count": None,
        }

        def handle_response(response):
            try:
                if "mp.weixin.qq.com" not in response.url:
                    return
                if not any(token in response.url for token in ("appmsg", "comment", "like", "read")):
                    return
                headers = response.headers or {}
                content_type = str(headers.get("content-type", "")).lower()
                if "json" not in content_type and "javascript" not in content_type and "text/plain" not in content_type:
                    return
                payload = response.json()
                self.merge_metric_counts(response_metrics, self.extract_metrics_from_json(payload))
            except Exception:
                pass

        self.page.on("response", handle_response)
        print_warning(f"Get:{url} Wait:{self.wait_timeout}")
        self.controller.open_url(url)
        page = self.page
        content=""
        
        try:
            # 等待页面加载
            # page.wait_for_load_state("networkidle")
            # body = page.evaluate('() => document.body.innerText')
            body= page.locator("body").text_content().strip()
            
            info["content"]=body
            if "当前环境异常，完成验证后即可继续访问" in body:
                info["content"]=""
                # try:
                #     page.locator("#js_verify").click()
                # except:
                self.controller.cleanup()
                time.sleep(5)
                raise Exception("当前环境异常，完成验证后即可继续访问")
            if "该内容已被发布者删除" in body or "The content has been deleted by the author." in body:
                info["content"]="DELETED"
                raise Exception("该内容已被发布者删除")
            if  "内容审核中" in body:
                info['content']="DELETED"
                raise Exception("内容审核中")
            if "该内容暂时无法查看" in body:
                info["content"]="DELETED"
                raise Exception("该内容暂时无法查看")
            if "违规无法查看" in body:
                info["content"]="DELETED"
                raise Exception("违规无法查看")
            if "发送失败无法查看" in body:
                info["content"]="DELETED"
                raise Exception("发送失败无法查看")
            if "Unable to view this content because it violates regulation" in body:     
                info["content"]="DELETED"
                raise Exception("违规无法查看")
            try:
                page.wait_for_timeout(1500)
            except Exception:
                pass

            # 获取标题
            title = page.locator('meta[property="og:title"]').get_attribute("content")
            #获取作者
            author = page.locator('meta[property="og:article:author"]').get_attribute("content")
            #获取描述
            description = page.locator('meta[property="og:description"]').get_attribute("content")
            #获取题图
            topic_image = page.locator('meta[property="twitter:image"]').get_attribute("content")

            self.export_to_pdf(f"./data/{title}.pdf")
            if title=="":
                title = page.evaluate('() => document.title')
            
          
         
            # 获取正文内容和图片
            content_element = page.locator("#js_content")
            content = content_element.inner_html()

            #获取图集内容 
            if content=="":
                content_element = page.locator("#js_article")
                content = content_element.inner_html()

            content=self.clean_article_content(str(content))
            #获取图像资源
            images = [
                img.get_attribute("data-src") or img.get_attribute("src")
                for img in content_element.locator("img").all()
                if img.get_attribute("data-src") or img.get_attribute("src")
            ]
            
            # 处理图片上传到MinIO并替换URL
            article_id = self.extract_id_from_url(url) or "unknown"
            # 处理正文中的图片，上传到MinIO并替换为MinIO地址
            content = self.process_images_for_minio(content, article_id)
            if not content:
                # 如果处理失败，使用原始内容
                content = content_element.inner_html()
            
            # 处理封面图片上传到MinIO
            try:
                from core.storage.minio_client import MinIOClient, should_mirror_article_images
                minio_client = MinIOClient()
                
                # 优先使用 topic_image，如果没有则使用正文第一张图片
                cover_image_url = topic_image if topic_image else (images[0] if images and len(images) > 0 else None)
                
                if cover_image_url and should_mirror_article_images():
                    minio_cover_url = minio_client.upload_image(cover_image_url, article_id)
                    if minio_cover_url:
                        info["pic_url"] = minio_cover_url
                        if topic_image:
                            info["topic_image"] = minio_cover_url
                        print_info(f"封面图片已上传到MinIO: {cover_image_url} -> {minio_cover_url}")
                    else:
                        # 上传失败，使用原始URL
                        info["pic_url"] = cover_image_url
                        if topic_image:
                            info["topic_image"] = topic_image
                else:
                    # MinIO不可用或没有封面图，使用原始URL
                    if images and len(images)>0:
                        info["pic_url"]=images[0]
            except Exception as e:
                from core.print import print_warning
                print_warning(f"处理封面图片失败: {e}")
                # 失败时使用原始图片
                if images and len(images)>0:
                    info["pic_url"]=images[0]


            try:
                #获取发布时间
                publish_time_str = page.locator("#publish_time").text_content().strip()
                # 将发布时间转换为时间戳
                publish_time = self.convert_publish_time_to_timestamp(publish_time_str)
            except Exception as e:
                print_warning(f"获取作者和发布时间失败: {e}")
                publish_time=""
            info["title"]=title
            info["publish_time"]=publish_time
            info["content"]=content
            info["images"]=images
            info["author"]=author
            info["description"]=description
            # topic_image 已在封面图片处理中设置（如果上传成功）
            if "topic_image" not in info:
                info["topic_image"]=topic_image
            info.update(self.extract_article_metrics(page, response_metrics))

        except Exception as e:
            print_error(f"文章内容获取失败: {str(e)}")
            print_warning(f"页面内容预览: {body[:50]}...")
            # raise e
            # 记录详细错误信息但继续执行
            try:
                info.update(self.extract_article_metrics(page, response_metrics))
            except Exception:
                pass

        try:
            # 等待关键元素加载
            # 使用更精确的选择器避免匹配多个元素
            ele_logo = page.locator('#js_like_profile_bar .wx_follow_avatar img')
            # 获取<img>标签的src属性
            logo_src = ele_logo.get_attribute('src')

            # 获取公众号名称
            title = page.evaluate('() => $("#js_wx_follow_nickname").text()')
            biz = page.evaluate('() => window.biz')
            info["mp_info"]={
                "mp_name":title,
                "logo":logo_src,
                "biz": biz or self.extract_biz_from_source(url, page), 
            }
            info["mp_id"]= "MP_WXS_"+base64.b64decode(info["mp_info"]["biz"]).decode("utf-8")
        except Exception as e:
            print_error(f"获取公众号信息失败: {str(e)}")   
            pass
        self.Close()
        return info
    def Close(self):
        """关闭浏览器"""
        if hasattr(self, 'controller'):
            self.controller.Close()
        else:
            print("WXArticleFetcher未初始化或已销毁")
    def __del__(self):
        """销毁文章获取器"""
        try:
            if hasattr(self, 'controller') and self.controller is not None:
                self.controller.Close()
        except Exception as e:
            # 析构函数中避免抛出异常
            pass

    def export_to_pdf(self, title=None):
        """将文章内容导出为 PDF 文件
        
        Args:
            output_path: 输出 PDF 文件的路径（可选）
        """
        output_path=""
        try:
            if cfg.get("export.pdf.enable",False)==False:
                return
            # 使用浏览器打印功能生成 PDF
            if output_path:
                import os
                pdf_path=cfg.get("export.pdf.dir","./data/pdf")
                output_path=os.path.abspath(f"{pdf_path}/{title}.pdf")
            print_success(f"PDF 文件已生成{output_path}")
        except Exception as e:
            print_error(f"生成 PDF 失败: {str(e)}")

   
    def process_images_for_minio(self, html_content: str, article_id: str) -> str:
        """处理HTML内容中的图片，上传到MinIO并替换URL
        
        Args:
            html_content: HTML内容
            article_id: 文章ID
            
        Returns:
            处理后的HTML内容
        """
        try:
            from bs4 import BeautifulSoup
            from core.storage.minio_client import MinIOClient, should_mirror_article_images
            from core.log import logger
            import re
            
            # 未开启转存或 MinIO 不可用，直接返回原内容
            if not should_mirror_article_images():
                return html_content
            
            minio_client = MinIOClient()
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            img_tags = soup.find_all('img')
            
            # 处理每个图片
            uploaded_count = 0
            failed_count = 0
            for img_tag in img_tags:
                # 获取图片URL（优先使用data-src，因为微信图片通常使用懒加载）
                img_url = str(img_tag.get('data-src') or img_tag.get('src') or '')
                if not img_url or img_url.strip() == '':
                    continue
                
                # 跳过已经是MinIO URL的图片（避免重复上传）
                if 'minio' in img_url.lower() or (minio_client.public_url and minio_client.public_url in img_url):
                    continue
                
                # 尝试上传到MinIO
                minio_url = minio_client.upload_image(img_url, article_id)
                
                if minio_url:
                    # 替换为MinIO URL
                    img_tag['src'] = minio_url
                    # 删除data-src属性，因为已经替换为MinIO地址
                    if 'data-src' in img_tag.attrs:
                        del img_tag['data-src']
                    logger.info(f"图片已上传到MinIO并替换URL: {img_url[:80]}... -> {minio_url[:80]}...")
                    uploaded_count += 1
                else:
                    # 如果上传失败，至少确保src可用（将data-src移到src）
                    if 'data-src' in img_tag.attrs and not img_tag.get('src'):
                        img_tag['src'] = img_tag['data-src']
                        del img_tag['data-src']
                    failed_count += 1
            
            if uploaded_count > 0:
                from core.print import print_info
                print_info(f"正文图片处理完成: 成功上传 {uploaded_count} 张，失败 {failed_count} 张")
            
            return str(soup)
        except Exception as e:
            logger.error(f"处理图片上传到MinIO失败: {e}")
            return html_content
    
    def clean_article_content(self,html_content: str):
        from tools.html import htmltools
        if not cfg.get("gather.clean_html",False):
            return html_content
        return htmltools.clean_html(str(html_content).strip(),
                                 remove_selectors=[
                                     "link",
                                     "head",
                                     "script"
                                 ],
                                 remove_attributes=[
                                     {"name":"style","value":"display: none;"},
                                     {"name":"style","value":"display:none;"},
                                     {"name":"aria-hidden","value":"true"},
                                 ],
                                 remove_normal_tag=True
                                 )
   


Web=WXArticleFetcher()
