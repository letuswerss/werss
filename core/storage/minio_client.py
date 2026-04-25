"""
MinIO客户端工具类
用于上传文章中的图片到MinIO对象存储
"""
from typing import Optional
import requests
from urllib.parse import urlparse
import hashlib
import os
from io import BytesIO
from core.config import cfg
from core.print import print_info, print_error, print_success, print_warning

try:
    from minio import Minio
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    print_warning("MinIO库未安装，图片上传功能将不可用。请运行: pip install minio")


def build_image_fetch_headers(image_url: str) -> dict:
    """微信 CDN 常校验 Referer，否则返回 403，导致头像/图片无法拉取转存。"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    u = (image_url or "").lower()
    if any(
        h in u
        for h in (
            "mmbiz.qpic.cn",
            "mmbiz.qlogo.cn",
            "mmecoa.qpic.cn",
            "wx.qlogo.cn",
        )
    ):
        headers["Referer"] = "https://mp.weixin.qq.com/"
    return headers


class MinIOClient:
    """MinIO客户端单例类"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        if not MINIO_AVAILABLE:
            self.client = None
            self._initialized = True
            return
        
        # 从配置读取MinIO设置
        self.endpoint = cfg.get("minio.endpoint", "")
        self.access_key = cfg.get("minio.access_key", "")
        self.secret_key = cfg.get("minio.secret_key", "")
        self.bucket_name = cfg.get("minio.bucket", "articles")
        self.secure = cfg.get("minio.secure", False)
        self.public_url = cfg.get("minio.public_url", "")
        self.enabled = cfg.get("minio.enabled", False)
        # 是否使用 presigned URL（如果 bucket 不是公开的，设置为 True）
        self.use_presigned_url = cfg.get("minio.use_presigned_url", False)
        
        # 清理 endpoint：移除协议前缀和路径（MinIO 客户端只接受 host:port 格式）
        if self.endpoint:
            # 移除 http:// 或 https:// 前缀
            self.endpoint = self.endpoint.replace('http://', '').replace('https://', '')
            # 移除路径部分（如果有）
            if '/' in self.endpoint:
                self.endpoint = self.endpoint.split('/')[0]
        
        # 如果未启用或配置不完整，则不初始化客户端
        if not self.enabled or not self.endpoint or not self.access_key or not self.secret_key:
            self.client = None
            self._initialized = True
            if self.enabled:
                print_warning("MinIO已启用但配置不完整，图片上传功能将不可用")
            return
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            # 确保bucket存在
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print_success(f"创建MinIO bucket: {self.bucket_name}")
            
            if not self.use_presigned_url:
                self._ensure_public_read_policy()
            
            self._initialized = True
            print_success(f"MinIO客户端初始化成功: {self.endpoint}/{self.bucket_name}")
        except Exception as e:
            print_error(f"MinIO客户端初始化失败: {str(e)}")
            self.client = None
            self._initialized = True
    
    def _ensure_public_read_policy(self):
        """确保 bucket 有公开读取策略，避免头像和图片无法外部访问"""
        import json
        try:
            self.client.get_bucket_policy(self.bucket_name)
        except Exception:
            try:
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                    }]
                }
                self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
                print_success(f"已自动设置 {self.bucket_name} bucket 为公开读取")
            except Exception as e:
                print_warning(f"设置 bucket 公开读取策略失败: {e}，请手动在MinIO管理界面设置")

    def is_available(self) -> bool:
        """检查MinIO是否可用"""
        return self.client is not None and MINIO_AVAILABLE
    
    def upload_image(self, image_url: str, article_id: str) -> Optional[str]:
        """
        下载图片并上传到MinIO
        
        Args:
            image_url: 原始图片URL
            article_id: 文章ID，用于组织存储路径
            
        Returns:
            MinIO中的图片URL，失败返回None
        """
        if not should_mirror_article_images():
            return None
        
        try:
            response = requests.get(
                image_url, stream=True, timeout=20, headers=build_image_fetch_headers(image_url)
            )
            response.raise_for_status()
            
            # 生成文件名
            parsed_url = urlparse(image_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            if not file_ext.startswith('.'):
                file_ext = '.' + file_ext
            
            # 使用URL的hash作为文件名，避免重复
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            filename = f"{url_hash}{file_ext}"
            
            # MinIO中的路径：articles/{article_id}/{filename}
            object_name = f"articles/{article_id}/{filename}"
            
            # 上传到MinIO
            image_data = BytesIO(response.content)
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                image_data,
                length=len(response.content),
                content_type=content_type
            )
            
            # 返回MinIO的访问URL
            minio_url = None
            
            # 如果配置了使用 presigned URL，生成临时访问链接（7天有效期）
            if self.use_presigned_url:
                try:
                    from datetime import timedelta
                    # 生成 presigned URL（7天有效期）
                    minio_url = self.client.presigned_get_object(
                        self.bucket_name,
                        object_name,
                        expires=timedelta(days=7)
                    )
                except Exception as presigned_error:
                    print_warning(f"生成presigned URL失败，使用直接URL: {presigned_error}")
                    # 回退到直接URL
                    minio_url = None
            
            # 如果未使用 presigned URL 或生成失败，使用直接访问URL
            if not minio_url:
                # 优先使用 public_url，如果没有配置则使用 endpoint
                if self.public_url:
                    # 清理 public_url：移除末尾的斜杠
                    public_url_clean = str(self.public_url).rstrip('/')
                    # 如果 public_url 以 bucket 名称结尾，说明已经包含 bucket
                    if public_url_clean.endswith(f'/{self.bucket_name}') or public_url_clean.endswith(self.bucket_name):
                        # public_url 已经包含 bucket，直接拼接 object_name
                        minio_url = f"{public_url_clean}/{object_name}"
                    else:
                        # public_url 不包含 bucket，需要拼接
                        minio_url = f"{public_url_clean}/{self.bucket_name}/{object_name}"
                else:
                    # 如果没有配置public_url，使用endpoint构建
                    protocol = "https" if self.secure else "http"
                    minio_url = f"{protocol}://{self.endpoint}/{self.bucket_name}/{object_name}"
            
            print_info(f"图片上传成功: {image_url} -> {minio_url}")
            return minio_url
            
        except Exception as e:
            print_error(f"图片上传失败 {image_url}: {str(e)}")
            return None
    
    def upload_avatar(self, avatar_url: str, mp_id: str) -> Optional[str]:
        """
        下载公众号头像并上传到MinIO
        
        Args:
            avatar_url: 原始头像URL
            mp_id: 公众号ID，用于组织存储路径
            
        Returns:
            MinIO中的头像URL，失败返回None
        """
        if not should_mirror_article_images():
            return None
        
        try:
            response = requests.get(
                avatar_url, stream=True, timeout=20, headers=build_image_fetch_headers(avatar_url)
            )
            response.raise_for_status()
            
            # 生成文件名
            parsed_url = urlparse(avatar_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            if not file_ext.startswith('.'):
                file_ext = '.' + file_ext
            
            # 使用URL的hash作为文件名，避免重复
            url_hash = hashlib.md5(avatar_url.encode()).hexdigest()
            filename = f"{url_hash}{file_ext}"
            
            # MinIO中的路径：avatars/{mp_id}/{filename}
            # 清理mp_id，移除MP_WXS_前缀（如果有）
            clean_mp_id = str(mp_id).replace("MP_WXS_", "") if mp_id else "unknown"
            object_name = f"avatars/{clean_mp_id}/{filename}"
            
            # 上传到MinIO
            avatar_data = BytesIO(response.content)
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                avatar_data,
                length=len(response.content),
                content_type=content_type
            )
            
            # 返回MinIO的访问URL
            minio_url = None
            
            # 如果配置了使用 presigned URL，生成临时访问链接（7天有效期）
            if self.use_presigned_url:
                try:
                    from datetime import timedelta
                    # 生成 presigned URL（7天有效期）
                    minio_url = self.client.presigned_get_object(
                        self.bucket_name,
                        object_name,
                        expires=timedelta(days=7)
                    )
                except Exception as presigned_error:
                    print_warning(f"生成presigned URL失败，使用直接URL: {presigned_error}")
                    # 回退到直接URL
                    minio_url = None
            
            # 如果未使用 presigned URL 或生成失败，使用直接访问URL
            if not minio_url:
                # 优先使用 public_url，如果没有配置则使用 endpoint
                if self.public_url:
                    # 清理 public_url：移除末尾的斜杠
                    public_url_clean = str(self.public_url).rstrip('/')
                    # 如果 public_url 以 bucket 名称结尾，说明已经包含 bucket
                    if public_url_clean.endswith(f'/{self.bucket_name}') or public_url_clean.endswith(self.bucket_name):
                        # public_url 已经包含 bucket，直接拼接 object_name
                        minio_url = f"{public_url_clean}/{object_name}"
                    else:
                        # public_url 不包含 bucket，需要拼接
                        minio_url = f"{public_url_clean}/{self.bucket_name}/{object_name}"
                else:
                    # 如果没有配置public_url，使用endpoint构建
                    protocol = "https" if self.secure else "http"
                    minio_url = f"{protocol}://{self.endpoint}/{self.bucket_name}/{object_name}"
            
            print_info(f"头像上传成功: {avatar_url} -> {minio_url}")
            return minio_url
            
        except Exception as e:
            print_error(f"头像上传失败 {avatar_url}: {str(e)}")
            return None
    
    def upload_file(self, file_path: str, object_name: str) -> Optional[str]:
        """上传本地文件到MinIO"""
        if not self.is_available():
            return None
        
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )
            if self.public_url:
                return f"{self.public_url.rstrip('/')}/{self.bucket_name}/{object_name}"
            else:
                protocol = "https" if self.secure else "http"
                return f"{protocol}://{self.endpoint}/{self.bucket_name}/{object_name}"
        except Exception as e:
            print_error(f"文件上传失败 {file_path}: {str(e)}")
            return None


def should_mirror_article_images() -> bool:
    """
    业务开关：是否将微信侧图片转存到 MinIO（正文、封面、公众号头像等）。
    需 minio.store_article_images 为真且客户端已连接成功。
    """
    if not cfg.get("minio.store_article_images", True):
        return False
    return MinIOClient().is_available()

