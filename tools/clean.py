from core.models.article import Article
from sqlalchemy import func
import core.db as db
DB=db.Db(tag="文章清理")
def clean_duplicate_articles():
    """
    清理重复的文章
    """
    try:
        session = DB.get_session()
        
        # 查询所有文章的标题，并统计重复的标题
        duplicate_titles = session.query(
            Article.title,
            func.count(Article.id).label('count')
        ).group_by(Article.title).having(func.count(Article.id) > 1).all()
        
        # 如果没有重复的标题，直接返回
        if not duplicate_titles:
            return "没有找到重复的文章"
        
        # 获取所有重复的标题列表
        titles = [item[0] for item in duplicate_titles]
        
        # 查询这些标题对应的所有文章
        articles = session.query(Article).filter(Article.title.in_(titles)).all()
        
        # 用于存储已检查的文章标题和mp_id组合
        seen_articles = set()
        duplicates = []
        
        # 检查重复文章
        for article in articles:
            article_key = (article.title, article.mp_id)
            if article_key in seen_articles:
                duplicates.append(article)
            else:
                seen_articles.add(article_key)
        
        # 删除重复文章
        for duplicate in duplicates:
            print(f"删除重复文章: {duplicate.title}")
            session.delete(duplicate)
        session.commit()
    except:
        session.rollback()
    return (f"已清理 {len(duplicates)} 篇重复文章", len(duplicates))

if __name__ == "__main__":
    result = clean_duplicate_articles()
    print(result)