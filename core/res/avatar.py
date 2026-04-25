
from core.config import cfg
import os
import uuid
import requests
from urllib.parse import urlparse

# 使用绝对路径，确保在 Docker 容器中也能正确工作
files_dir = os.path.abspath("data/files")
avatar_dir = os.path.join(files_dir, "avatars")
os.makedirs(avatar_dir, exist_ok=True)
def save_avatar_locally(avatar_url):
    if not cfg.get("local_avatar",False):
        return avatar_url
    if not avatar_url:
        return None
    
    # 确保存储目录存在
    save_dir = avatar_dir
    os.makedirs(save_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(urlparse(avatar_url).path)[1]
    if not file_ext:
        file_ext = ".jpg"
    file_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(save_dir, file_name)
    
    # 下载并保存文件
    try:
        response = requests.get(avatar_url)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except Exception as e:
        print(f"保存头像失败: {str(e)}")
        return None

