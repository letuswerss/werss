from core.models import Article,Feed,DATA_STATUS
from core.db import DB
import json
class ArticleInfo():
    #没有内容的文章数量
    no_content_count:int=0
    #有内容的文章数量
    has_content_count:int=0
    #所有文章数量
    all_count:int=0
    #不正常的文章数量
    wrong_count:int=0
    #公众号总数
    mp_all_count:int=0
def laxArticle():
    info=ArticleInfo()
    session=DB.get_session()
    #获取没有内容的文章数量
    info.no_content_count=session.query(Article).filter(Article.content == None).count()
    #所有文章数量
    info.all_count=session.query(Article).count()
    #有内容的文章数量
    info.has_content_count=info.all_count-info.no_content_count

    #获取删除的文章
    info.wrong_count=session.query(Article).filter(Article.status !=DATA_STATUS.ACTIVE ).count()

    #公众号总数
    info.mp_all_count=session.query(Feed).distinct(Feed.id).count()
    # session.close()
    return info.__dict__
    pass
ARTICLE_INFO=laxArticle()
print(ARTICLE_INFO)