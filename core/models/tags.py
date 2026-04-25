from  .base import Base,Column,String,Integer,DateTime,Text,Boolean
class Tags(Base):   
    #标签数据模型类，用于存储和管理标签信息
    __tablename__ = 'tags'
    # 标签唯一标识符，主键
    id = Column(String(255), primary_key=True)
    # 标签名称
    name =Column(String(255))
    # 标签封面图片URL
    cover = Column(String(255))
    # 标签简介
    intro = Column(String(255))
    # 标签状态（0-禁用，1-启用，2-屏蔽）
    status = Column(Integer)
    # 定义需要通知的微信公众号ID集合（JSON格式字符串）
    mps_id = Column(Text, nullable=False)
    # 是否为用户自定义标签（用于标签提取时优先识别）
    is_custom = Column(Boolean, default=False, nullable=False)
    # 最后一次同步时间（时间戳）
    sync_time = Column(Integer)
    # 最后一次更新时间（时间戳）
    update_time = Column(Integer)
    # 记录创建时间
    created_at = Column(DateTime) 
    # 记录最后更新时间
    updated_at = Column(DateTime)
    