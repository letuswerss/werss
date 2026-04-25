import yaml
import sys
import os
import argparse
from string import Template
from core.print import print_warning, print_error,print_info
from .file import FileCrypto

# 在配置初始化之前加载开发环境的 .env 文件（延迟导入避免循环）
def _load_env_before_config():
    """在配置初始化前加载环境变量"""
    try:
        # 检测是否在 Docker 容器中
        is_docker = False
        if os.path.exists('/.dockerenv'):
            is_docker = True
        elif os.path.exists('/proc/self/cgroup'):
            try:
                with open('/proc/self/cgroup', 'r') as f:
                    if any('docker' in line for line in f):
                        is_docker = True
            except Exception:
                pass
        
        if is_docker:
            # Docker 环境中，环境变量由 docker-compose.yml 注入，不需要加载 .env
            return
        
        # 开发环境：尝试加载 .env
        try:
            from dotenv import load_dotenv
            # 获取当前文件所在目录，然后找到 .env
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # .env 文件在项目根目录，不在 core 目录下
            env_path = os.path.join(os.path.dirname(current_dir), '.env')

            if os.path.exists(env_path):
                # 先检查环境变量是否已存在
                api_key_before = os.getenv("OPENAI_API_KEY")
                load_dotenv(env_path, override=False)  # override=False 表示不覆盖已存在的环境变量
                api_key_after = os.getenv("OPENAI_API_KEY")
                
                # 如果加载成功，尝试记录日志（避免循环导入）
                if api_key_after and not api_key_before:
                    try:
                        from core.log import logger
                        logger.debug(f"已从 {env_path} 加载环境变量")
                    except Exception:
                        pass  # 如果 logger 还未初始化，忽略
        except ImportError:
            # python-dotenv 未安装时忽略
            pass
        except Exception as e:
            # 加载失败时尝试记录日志
            try:
                from core.log import logger
                logger.debug(f"加载 .env 文件失败: {e}")
            except Exception:
                pass  # 如果 logger 还未初始化，忽略
    except Exception:
        # 外层异常处理，防止任何未预期的错误导致配置初始化失败
        pass

_load_env_before_config()

class Config: 
    config_path=""
    config={}
    _config_cache = None  # 添加缓存变量
    def __init__(self, config_path=None, encrypt=False):
        self.args = self.parse_args()
        self.config_path = config_path or self.args.config

        # 确保目录存在
        if os.path.dirname(self.config_path) != "":
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        # 加密相关配置
        self.encryption_enabled = encrypt
        self.get_config()
        # 初始化加密设置
        self._init_encryption()
        
    def _init_encryption(self):
        """初始化加密设置"""
        key = os.getenv('ENCRYPTION_KEY', 'store.csol.store.werss')  # 默认密钥
        if self.encryption_enabled:
            try:
                self.crypto = FileCrypto(key)
            except Exception as e:
                print(f"加密初始化失败: {e}")
                self.encryption_enabled = False
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-config', help='配置文件', default='config.yaml')
        parser.add_argument('-job', help='启动任务', default=False)
        parser.add_argument('-init', help='初始化数据库,初始化用户', default=False)
        args, _ = parser.parse_known_args()
        return args
    def _encrypt(self, data):
        """加密数据"""
        if not self.encryption_enabled or not hasattr(self, 'crypto'):
            return data
        try:
            if isinstance(data, str):
                return self.crypto.encrypt(data.encode('utf-8')).decode('utf-8')
            return self.crypto.encrypt(data).decode('utf-8')
        except Exception as e:
            print(f"加密失败: {e}")
            return data

    def _decrypt(self, data):
        """解密数据"""
        if not self.encryption_enabled or not hasattr(self, 'crypto'):
            return data
        try:
            if isinstance(data, str):
                return self.crypto.decrypt(data.encode('utf-8')).decode('utf-8')
            return self.crypto.decrypt(data).decode('utf-8')
        except Exception as e:
            print(f"解密失败: {e}")
            return data  # 解密失败返回原始数据

    def save_config(self):
        config_to_save = self.config.copy()
        try:
                # 生成YAML内容
                yaml_content = yaml.dump(config_to_save)
                # 验证YAML格式是否合法
                try:
                    yaml.safe_load(yaml_content)
                except yaml.YAMLError as ye:
                    print_error(f"YAML格式验证失败: {ye}")
                    raise
                # 加密整个YAML内容
                encrypted_content = self._encrypt(yaml_content)
                # 直接写入临时文件，然后重命名（Windows下更安全的替换方式）
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    f.write(encrypted_content)
                self.reload()
             
        except Exception as e:
            print_error(f"保存配置文件失败: {e}")
            raise
    def replace_env_vars(self,data):
            if isinstance(data, dict):
                return {k: self.replace_env_vars(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self.replace_env_vars(item) for item in data]
            elif isinstance(data, str):
                try:
                    import re
                    # 匹配 ${VAR:-default} 或 ${VAR} 格式
                    pattern = re.compile(r'\$\{([^}:]+)(?::-([^}]*))?\}')
                    def replace_match(match):
                        var_name = match.group(1)
                        default_value = match.group(2)
                        # 环境变量名不能包含点号，所以将点号转换为下划线
                        # 先尝试原始名称（支持直接使用下划线的环境变量）
                        env_value = os.getenv(var_name)
                        if env_value is None:
                            # 如果原始名称不存在，尝试将点号转换为下划线
                            env_var_name = var_name.replace('.', '_')
                            env_value = os.getenv(env_var_name)
                        # 如果环境变量存在，使用环境变量的值；否则使用默认值
                        if env_value is not None:
                            return env_value
                        elif default_value is not None:
                            return default_value
                        else:
                            return ''
                    return pattern.sub(replace_match, data)
                except:
                    return data
            return data
    def get_config(self):
        # 如果有缓存，直接返回缓存
        if self._config_cache is not None:
            return self._config_cache
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if self.encryption_enabled:
                    try:
                        # 尝试解密整个文件内容
                        decrypted_content = self._decrypt(content)
                        config = yaml.safe_load(decrypted_content)
                    except Exception as e:
                        print(f"解密配置文件失败: {e}")
                        sys.exit(1)
                else:
                    config = yaml.safe_load(content)
                
                if config is None:
                    config = {}
                
                self.config = config
                self._config = self.replace_env_vars(config)
               
                return self.config
        except Exception as e:
            print_error(f"加载配置文件 {self.config_path} 错误: {e}")
            # sys.exit(1)
    def reload(self):
        self.config=self.get_config()
         # 更新缓存
        self._config_cache = self.config
    def set(self,key,default:any=None):
        self.config[key] = default
        self.save_config()
    def __fix(self,v):
        if v in ("", "''", '""', None):
            return ""
        # 如果已经是布尔值，直接返回
        if isinstance(v, bool):
            return v
        # 如果已经是数字，直接返回
        if isinstance(v, (int, float)):
            return v
        try:
            # 尝试转换为布尔值
            if isinstance(v, str) and v.lower() in ('true', 'false'):
                return v.lower() == 'true'
            # 尝试转换为整数
            if isinstance(v, str) and v.isdigit():
                return int(v)
            # 尝试转换为浮点数
            if isinstance(v, str) and '.' in v and all(part.isdigit() for part in v.split('.') if part):
                return float(v)
            return v
        except:
            return v
    def get(self,key,default:any=None, silent:bool=False):
        from core.config_overrides import (
            env_overrides_db_mode,
            get_config_override,
        )

        def _yaml_resolved():
            _config = self.replace_env_vars(self.config)
            keys = key.split('.') if isinstance(key, str) else [key]
            value = _config
            try:
                for k in keys:
                    value = value[k]
                return True, self.__fix(value)
            except (KeyError, TypeError):
                return False, None

        def _db_override():
            if not isinstance(key, str):
                return None
            try:
                return get_config_override(key)
            except Exception:
                return None

        def _effective_empty(val) -> bool:
            if val is None:
                return True
            if isinstance(val, str) and val.strip() == '':
                return True
            return False

        env_first = isinstance(key, str) and env_overrides_db_mode()

        if not env_first and isinstance(key, str):
            try:
                ov = _db_override()
                if ov is not None:
                    return self.__fix(ov)
            except Exception:
                pass

        ok, val = _yaml_resolved()
        if not ok:
            if default is None and not silent:
                print_warning("Key {} not found in configuration".format(key))
            if env_first:
                ov = _db_override()
                if ov is not None:
                    return self.__fix(ov)
            return default

        if env_first:
            if not _effective_empty(val):
                return val
            ov = _db_override()
            if ov is not None:
                return self.__fix(ov)
            if val is None and default is not None:
                return default
            return val

        if val is None and default is not None:
            return default
        return val

cfg=Config()
def set_config(key:str,value:str):
    cfg.set(key,value)
def save_config():
    cfg.save_config()
    
DEBUG=cfg.get("debug",False)
APP_NAME=cfg.get("app_name","werss")
from core.base import *
print(f"名称:{APP_NAME}\n版本:{VERSION} API_BASE:{API_BASE}")