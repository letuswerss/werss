# 从 sqlalchemy 模块导入所需的列类型和数据库相关功能
from .base import Base,Column, Integer, String, Text

# 定义 ConfigManagement 类，继承自 Base 类，用于映射数据库中的 config_management 表
class ConfigManagement(Base):
    from_attributes = True
    # 指定映射的数据库表名为 config_management
    __tablename__ = 'config_management'
    # 配置项的键，唯一且建立索引，不能为空
    config_key = Column(String(100), primary_key=True, unique=True, index=True, nullable=False)
    # 配置项的值，使用 Text 类型，不能为空
    config_value = Column(Text, nullable=False)
    # 配置项的描述信息
    description = Column(String(200))