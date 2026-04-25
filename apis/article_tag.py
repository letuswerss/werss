from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from core.models.article import Article
from core.models.article_tags import ArticleTag
from core.models.tags import Tags as TagsModel
from .base import success_response, error_response

router = APIRouter(prefix="/article-tag", tags=["文章标签关联"])


@router.get("",
    summary="获取文章的所有标签",
    description="根据文章ID获取该文章关联的所有标签"
)
async def get_article_tags(
    article_id: str = Query(..., description="文章ID"),
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user)
):
    """
    获取文章的所有标签
    
    参数:
    - article_id: 文章ID
    
    返回:
    - 包含标签列表的成功响应
    """
    try:
        # 检查文章是否存在
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return error_response(code=404, message="Article not found")
        
        # 查询文章的所有标签
        article_tags = db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id
        ).all()
        
        # 获取标签详情
        tags = []
        for article_tag in article_tags:
            tag = db.query(TagsModel).filter(TagsModel.id == article_tag.tag_id).first()
            if tag and tag.status == 1:
                tags.append({
                    "id": tag.id,
                    "name": tag.name,
                    "cover": tag.cover,
                    "intro": tag.intro,
                    "status": tag.status,
                    "is_custom": getattr(tag, 'is_custom', False),
                    "created_at": article_tag.created_at.isoformat() if article_tag.created_at is not None else None,
                    "article_publish_date": article_tag.article_publish_date.isoformat() if article_tag.article_publish_date is not None else None
                })
        
        return success_response(data=tags)
    except Exception as e:
        from core.print import print_error
        print_error(f"获取文章标签失败: {e}")
        return error_response(code=500, message=f"获取文章标签失败: {str(e)}")


@router.post("",
    summary="为文章添加标签",
    description="为指定文章关联一个标签"
)
async def add_article_tag(
    article_id: str,
    tag_id: str = Query(..., description="标签ID"),
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user)
):
    """
    为文章添加标签
    
    参数:
    - article_id: 文章ID
    - tag_id: 标签ID（Tags 表的 ID）
    
    返回:
    - 成功响应
    """
    try:
        import uuid
        from datetime import datetime
        
        # 检查文章是否存在
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return error_response(code=404, message="Article not found")
        
        # 检查标签是否存在
        tag = db.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            return error_response(code=404, message="Tag not found")
        if tag.status != 1:
            return error_response(code=400, message="Tag is disabled")
        
        # 检查是否已存在关联
        existing = db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id,
            ArticleTag.tag_id == tag_id
        ).first()
        
        if existing:
            return error_response(code=400, message="Tag already assigned to this article")
        
        # 获取文章的发布时间，用于设置 article_publish_date
        article_publish_date = datetime.now()  # 默认值
        if article:
            # 获取 publish_time 值（可能是整数时间戳）
            publish_time = getattr(article, 'publish_time', None)
            if publish_time is not None:
                try:
                    publish_timestamp = int(publish_time)  # type: ignore
                    if publish_timestamp < 10000000000:  # 秒级时间戳
                        publish_timestamp *= 1000
                    article_publish_date = datetime.fromtimestamp(publish_timestamp / 1000)
                except (ValueError, TypeError, OSError):
                    article_publish_date = datetime.now()
        
        # 创建关联
        article_tag = ArticleTag(
            id=str(uuid.uuid4()),
            article_id=article_id,
            tag_id=tag_id,
            created_at=datetime.now(),  # 关联创建时间
            article_publish_date=article_publish_date  # 文章的发布日期（用于趋势统计）
        )
        db.add(article_tag)
        db.commit()
        db.refresh(article_tag)
        
        return success_response(data={
            "article_id": article_id,
            "tag_id": tag_id,
            "tag_name": tag.name
        }, message="标签添加成功")
    except Exception as e:
        db.rollback()
        from core.print import print_error
        print_error(f"添加文章标签失败: {e}")
        return error_response(code=500, message=f"添加文章标签失败: {str(e)}")


@router.delete("/{tag_id}",
    summary="删除文章的标签关联",
    description="删除指定文章与标签的关联"
)
async def delete_article_tag(
    article_id: str,
    tag_id: str,
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user)
):
    """
    删除文章的标签关联
    
    参数:
    - article_id: 文章ID
    - tag_id: 标签ID
    
    返回:
    - 成功响应
    """
    try:
        # 查找关联
        article_tag = db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id,
            ArticleTag.tag_id == tag_id
        ).first()
        
        if not article_tag:
            return error_response(code=404, message="Article tag association not found")
        
        # 删除关联
        db.delete(article_tag)
        db.commit()
        
        return success_response(message="标签关联删除成功")
    except Exception as e:
        db.rollback()
        from core.print import print_error
        print_error(f"删除文章标签失败: {e}")
        return error_response(code=500, message=f"删除文章标签失败: {str(e)}")
