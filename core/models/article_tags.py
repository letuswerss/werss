"""文章-标签关联表模型"""
from .base import Base, Column, String, DateTime, UniqueConstraint
from datetime import datetime


class ArticleTag(Base):
    """文章-标签关联表"""
    __tablename__ = 'article_tags'

    # 不设数据库级 FOREIGN KEY：主栈/Prisma 等库里 articles.id 常为 integer，WeRSS 使用字符串复合 id，
    # 类型不一致会导致建表失败；关联由应用层 join 维护（删除文章时不会级联删关联行，需业务侧处理）。
    id = Column(String(255), primary_key=True)
    article_id = Column(String(255), nullable=False, index=True)
    tag_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)  # 关联创建时间（标签被关联到文章的时间）
    article_publish_date = Column(DateTime, nullable=True, index=True)  # 文章的发布日期（用于趋势统计）
    
    # 唯一约束：同一篇文章不能重复添加同一标签
    __table_args__ = (
        UniqueConstraint('article_id', 'tag_id', name='uq_article_tag'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<ArticleTag(article_id={self.article_id}, tag_id={self.tag_id})>"
