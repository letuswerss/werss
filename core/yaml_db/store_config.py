import yaml
from core.db import DB as db
from core.models.config_management import ConfigManagement
import logging
from typing import Dict, Any

class ConfigManager:
    """配置管理器，负责YAML配置与数据库之间的双向转换"""
    
    def __init__(self, config_path='config.yaml'):
        """
        初始化配置管理器
        :param config_path: 配置文件路径，默认为config.yaml
        """
        self.config_path = config_path
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger('ConfigManager')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
        
    def _load_config(self):
        """加载YAML配置文件"""
        from core.config import cfg
        return cfg.get_config()

    def yaml_to_list(self):
        """将配置文件转换为嵌套字典结构"""
        config = self._load_config()
        return self._convert_to_nested_dict(config)
        
    def _store_single_config(self, key, value, description=""):
        """存储单个配置项到数据库
        
        Args:
            key: 配置项键名
            value: 配置项值
            description: 配置项描述，会自动处理：
                - 去除前后空格
                - 空描述时使用默认值
                - 转义特殊字符
                - 限制长度(255字符)
        """
        try:
            # 处理description
            if not description or not description.strip():
                description = "系统配置项" if "." not in key else f"{key.split('.')[0]}配置的子项"
            
            # 清理description
            description = description.strip()
            
            # 转义特殊字符
            description = description.replace("'", "''").replace('"', '""')
            
            # 限制长度
            description = description[:255]
            
            db.get_session().merge(ConfigManagement(
                config_key=key,
                config_value=str(value) if value is not None else '',
                description=description
            ))
            self.logger.debug(f"成功存储配置项: {key}")
        except Exception as e:
            self.logger.error(f"存储配置项 {key} 失败: {str(e)}")
            raise
            
    def store_config_to_db(self):
        """将配置文件中的所有配置项存储到数据库"""
        self.logger.info("开始存储配置到数据库...")
        config = self._load_config()
        session=db.get_session()
        try:
            for key, value in config.items():
                if isinstance(value, dict):
                    # 处理嵌套配置
                    for sub_key, sub_value in value.items():
                        config_key = f"{key}.{sub_key}"
                        self._store_single_config(
                            config_key, 
                            sub_value,
                            f"{key}配置的子项"
                        )
                else:
                    self._store_single_config(
                        key, 
                        value,
                        "系统配置项"
                    )
            
            session.commit()
            self.logger.info("配置已成功存储到ConfigManagement表")
            return True
        except Exception as e:
            session.rollback()
            self.logger.error(f"存储配置失败: {str(e)}")
            return False
            
    def store_config_to_list(self,config=None) -> list:
        """
        将配置文件转换为ConfigManagement对象列表
        :return: 包含所有配置项的ConfigManagement对象列表
        """
        self.logger.info("开始转换配置到列表...")
        if config is None:
            config = self._load_config()
        config_list = []
        from core.config import cfg
        keys = [k.strip() for k in cfg.get("safe.hide_config", "db").split(",") if k.strip()]
        try:
            for key, value in config.items():
                if key in keys:
                    value = "***"
                if isinstance(value, dict):
                    # 处理嵌套配置
                    for sub_key, sub_value in value.items():
                        config_key = f"{key}.{sub_key}"
                        if config_key in keys:
                            sub_value = "***"
                        config_list.append(ConfigManagement(
                            config_key=config_key,
                            config_value=str(sub_value) if sub_value is not None else '',
                            description=f"{key}配置的子项"
                        ))
                else:
                    config_list.append(ConfigManagement(
                        config_key=key,
                        config_value=str(value) if value is not None else '',
                        description="系统配置项"
                    ))

            # 用 config_management 表中的值覆盖展示（与运行时 cfg.get 一致）
            try:
                from core.config_overrides import env_overrides_db_mode, get_all_overrides

                if not env_overrides_db_mode():
                    overrides = get_all_overrides()
                    seen = {item.config_key for item in config_list}
                    for item in config_list:
                        if item.config_key in overrides:
                            v = overrides[item.config_key]
                            item.config_value = (
                                "***" if item.config_key in keys else str(v if v is not None else "")
                            )
                    for k, v in overrides.items():
                        if k not in seen:
                            config_list.append(
                                ConfigManagement(
                                    config_key=k,
                                    config_value=(
                                        "***" if k in keys else str(v if v is not None else "")
                                    ),
                                    description="数据库配置项",
                                )
                            )
            except Exception as e:
                self.logger.debug("合并数据库配置覆盖失败（可忽略）: %s", e)
            
            self.logger.info("配置已成功转换为列表")
            return config_list
        except Exception as e:
            self.logger.error(f"配置转换失败: {str(e)}")
            return []

    def _convert_to_nested_dict(self, flat_config: Dict[str, str]) -> Dict[str, Any]:
        """将扁平化的配置字典转换为嵌套字典结构"""
        nested_config = {}
        for key, value in flat_config.items():
            parts = key.split('.')
            current_level = nested_config
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level[parts[-1]] = self._convert_value_type(value)
        return nested_config

    def _convert_value_type(self, value: str) -> Any:
        """尝试将字符串值转换为适当的数据类型"""
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.lower() == 'null' or value == '':
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def generate_config_from_db(self, output_path: str = None) -> bool:
        """
        从数据库生成YAML配置文件
        :param output_path: 输出文件路径，默认为初始化时的config_path
        :return: 是否成功
        """
        output_path = output_path or self.config_path
        self.logger.info(f"开始从数据库生成配置文件: {output_path}")
        
        try:
            # 从数据库获取所有配置项
            config_items = ConfigManagement.query.all()
            flat_config = {item.config_key: item.config_value for item in config_items}
            
            # 转换为嵌套结构
            nested_config = self._convert_to_nested_dict(flat_config)
            
            # 写入YAML文件
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(nested_config, f, allow_unicode=True, sort_keys=False)
            
            self.logger.info(f"成功生成配置文件: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"从数据库生成配置文件失败: {str(e)}")
            return False
if __name__ == '__main__':
    manager = ConfigManager()
    # 示例用法
    print("1. 将config.yaml存储到数据库")
    success = manager.store_config_to_db()
    if not success:
        exit(1)
        
    print("\n2. 从数据库生成config.yaml.backup")
    success = manager.generate_config_from_db("config.yaml.backup")
    if not success:
        exit(1)