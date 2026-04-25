"""
环境变量加载工具
- 开发环境：从 .env 文件加载
- 生产环境（Docker）：使用 Docker Compose 注入的环境变量
"""
import os


def load_dev_env_if_needed():
    """
    在开发环境中加载 .env 文件
    只在非 Docker 环境中加载，避免覆盖生产环境配置
    """
    # 检测是否在 Docker 容器中
    is_docker = False
    if os.path.exists('/.dockerenv'):
        is_docker = True
    elif os.path.exists('/proc/self/cgroup'):
        try:
            with open('/proc/self/cgroup', 'r') as f:
                if any('docker' in line for line in f):
                    is_docker = True
        except:
            pass
    
    if is_docker:
        # Docker 环境中，环境变量由 docker-compose.yml 注入，不需要加载 .env
        return
    
    # 开发环境：尝试加载 .env
    try:
        from dotenv import load_dotenv
        # 获取当前文件所在目录，然后找到 .env
        # core/env_loader.py -> werss/core -> werss -> .env
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)  # werss 目录
        env_path = os.path.join(os.path.dirname(parent_dir), '.env')  # .env
        
        # 调试：记录路径信息
        try:
            from core.log import logger
            logger.debug(f"尝试加载 .env 文件: {env_path}, 存在: {os.path.exists(env_path)}")
        except:
            pass
        
        if os.path.exists(env_path):
            # 先检查环境变量是否已存在且非空
            api_key_before = os.getenv("OPENAI_API_KEY", "")
            # 如果环境变量不存在或为空，则从 .env 文件加载（override=True）
            # 如果环境变量已存在且非空，则不覆盖（override=False）
            override = not bool(api_key_before)
            load_dotenv(env_path, override=override)
            api_key_after = os.getenv("OPENAI_API_KEY", "")
            
            # 如果加载成功，尝试记录日志（避免循环导入）
            if api_key_after and not api_key_before:
                try:
                    from core.log import logger
                    logger.info(f"已从 {env_path} 加载 OPENAI_API_KEY")
                except:
                    pass  # 如果 logger 还未初始化，忽略
            elif api_key_after:
                try:
                    from core.log import logger
                    logger.debug(f"使用已存在的 OPENAI_API_KEY（来自环境变量）")
                except:
                    pass
    except ImportError:
        # python-dotenv 未安装时忽略
        pass
    except Exception as e:
        # 加载失败时尝试记录日志
        try:
            from core.log import logger
            logger.debug(f"加载 .env 文件失败: {e}")
        except:
            pass  # 如果 logger 还未初始化，忽略

