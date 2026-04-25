from fastapi import APIRouter, Depends, HTTPException, status as fast_status
from core.auth import get_current_user
from core.db import DB
from core.models.base import DATA_STATUS
from core.models.article import Article, ArticleBase
from core.models.feed import Feed
from sqlalchemy import func, and_, case, or_
from datetime import datetime, timedelta
from .base import success_response, error_response
from typing import Dict, Any, List

router = APIRouter(prefix="/dashboard", tags=["Dashboard统计"])


@router.get("/stats", summary="获取Dashboard统计数据")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取Dashboard统计数据，包括：
    - 总文章数、来源数量、今日新增、本周新增
    - 来源分布统计
    - 热门关键词统计
    - 关键词趋势数据
    - 抓取趋势数据
    """
    session = DB.get_session()
    try:
        # 检测数据库类型
        db_config = DB.connection_str if hasattr(DB, 'connection_str') else ""
        is_postgresql = 'postgresql' in db_config.lower() or 'postgres' in db_config.lower()
        
        # 使用本地时间（不带时区），在比较时统一处理时区问题
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        week_start = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        # 辅助函数：将带时区的 datetime 转换为不带时区的本地时间
        def normalize_datetime(dt):
            """将 datetime 对象标准化为不带时区的本地时间"""
            if dt is None:
                return None
            try:
                # 如果不是 datetime 对象，直接返回
                if not isinstance(dt, datetime):
                    return dt
                
                # 如果是带时区的，先转换为本地时间（UTC），再移除时区信息
                if dt.tzinfo is not None:
                    # 转换为 UTC 时间（不带时区）
                    dt_utc = dt.astimezone(datetime.now().astimezone().tzinfo).replace(tzinfo=None)
                    # 或者直接移除时区信息（使用本地时间）
                    return dt.replace(tzinfo=None)
                
                # 如果已经是不带时区的，直接返回
                return dt
            except (AttributeError, TypeError, ValueError) as e:
                # 如果转换失败，尝试直接移除时区信息
                try:
                    if hasattr(dt, 'replace'):
                        return dt.replace(tzinfo=None)
                except:
                    pass
                # 如果都失败了，返回原值（可能是其他类型）
                return dt

        # 1. 基础统计
        # 总文章数（排除已删除）
        total_articles = session.query(ArticleBase).filter(
            ArticleBase.status != DATA_STATUS.DELETED
        ).count()

        # 总来源数
        total_sources = session.query(Feed).count()

        # 今日新增文章
        # 使用 func.date() 或直接比较，但需要处理时区问题
        # 先查询所有符合条件的记录，然后在 Python 层面过滤
        all_recent_articles = session.query(ArticleBase).filter(
            ArticleBase.status != DATA_STATUS.DELETED
        ).all()
        
        today_articles = 0
        week_articles = 0
        for article in all_recent_articles:
            if article.created_at:
                created_at = normalize_datetime(article.created_at)
                today_start_normalized = normalize_datetime(today_start)
                week_start_normalized = normalize_datetime(week_start)
                if created_at and today_start_normalized and created_at >= today_start_normalized:
                    today_articles += 1
                if created_at and week_start_normalized and created_at >= week_start_normalized:
                    week_articles += 1

        # 2. 来源分布统计
        source_stats_query = session.query(
            Feed.id,
            Feed.mp_name,
            func.count(
                case((Article.status != DATA_STATUS.DELETED, Article.id), else_=None)
            ).label('article_count')
        ).outerjoin(
            Article, Feed.id == Article.mp_id
        ).group_by(
            Feed.id, Feed.mp_name
        ).order_by(
            func.count(
                case((Article.status != DATA_STATUS.DELETED, Article.id), else_=None)
            ).desc()
        ).limit(10).all()

        source_stats = [
            {
                "mp_id": str(item.id),
                "mp_name": item.mp_name or "未知来源",
                "article_count": item.article_count or 0,
                "percentage": round((item.article_count or 0) / total_articles * 100, 2) if total_articles > 0 else 0
            }
            for item in source_stats_query
        ]

        # 3. 热门关键词统计（从文章的 tags 中获取，而不是从标题拆分）
        from core.models.article_tags import ArticleTag
        from core.models.tags import Tags as TagsModel
        
        # 获取最近30天的文章及其标签
        # 使用 ArticleTag.article_publish_date 来统计趋势（文章的发布日期）
        # 如果 article_publish_date 为 NULL，则使用 Article.publish_time 转换
        # 计算30天前的时间戳（秒级）
        thirty_days_ago_timestamp = int(thirty_days_ago.timestamp())
        
        # 根据数据库类型构建时间戳转换表达式
        # 优先使用 article_publish_date，如果为 NULL 则从 Article.publish_time 转换
        if is_postgresql:
            # PostgreSQL 使用 to_timestamp
            timestamp_expr = func.to_timestamp(
                case(
                    (Article.publish_time < 10000000000, Article.publish_time),
                    else_=Article.publish_time / 1000.0
                )
            )
        elif 'mysql' in db_config.lower():
            # MySQL 使用 FROM_UNIXTIME
            timestamp_expr = func.from_unixtime(
                case(
                    (Article.publish_time < 10000000000, Article.publish_time),
                    else_=Article.publish_time / 1000.0
                )
            )
        else:
            # SQLite 使用 datetime
            timestamp_expr = func.datetime(
                case(
                    (Article.publish_time < 10000000000, Article.publish_time),
                    else_=Article.publish_time / 1000.0
                ),
                'unixepoch'
            )
        
        recent_articles_with_tags = session.query(
            Article.id,
            # 优先使用 article_publish_date，如果为 NULL 则从 Article.publish_time 转换
            case(
                (ArticleTag.article_publish_date.isnot(None), ArticleTag.article_publish_date),
                else_=timestamp_expr
            ).label('tag_date'),  # 使用文章的发布日期
            TagsModel.name.label('tag_name')
        ).join(
            ArticleTag, Article.id == ArticleTag.article_id
        ).join(
            TagsModel, ArticleTag.tag_id == TagsModel.id
        ).filter(
            and_(
                Article.status != DATA_STATUS.DELETED,
                TagsModel.status == 1  # 只统计启用的标签
            )
        ).all()
        
        # 在 Python 层面过滤最近30天的文章，避免时区比较问题
        filtered_articles = []
        thirty_days_ago_normalized = normalize_datetime(thirty_days_ago)
        for row in recent_articles_with_tags:
            tag_date = row.tag_date
            if tag_date:
                tag_date = normalize_datetime(tag_date)
                if tag_date and thirty_days_ago_normalized and tag_date >= thirty_days_ago_normalized:
                    filtered_articles.append(row)
            else:
                # 如果没有 tag_date，尝试从 publish_time 转换
                article = session.query(Article).filter(Article.id == row.id).first()
                if article and article.publish_time:
                    publish_timestamp = article.publish_time
                    if publish_timestamp < 10000000000:
                        publish_dt = datetime.fromtimestamp(publish_timestamp)
                    else:
                        publish_dt = datetime.fromtimestamp(publish_timestamp / 1000.0)
                    publish_dt = normalize_datetime(publish_dt)
                    if publish_dt and thirty_days_ago_normalized and publish_dt >= thirty_days_ago_normalized:
                        filtered_articles.append(row)
        
        recent_articles_with_tags = filtered_articles

        keyword_map = {}
        keyword_trend_map = {}  # keyword -> date -> count

        # 过滤无效关键词的正则表达式
        import re
        invalid_keyword_pattern = re.compile(r'^[a-z]{1,2}$|^[0-9]+$|^[^\u4e00-\u9fa5a-zA-Z0-9]+$|^\.+$')

        for row in recent_articles_with_tags:
            tag_name = row.tag_name
            if not tag_name or not tag_name.strip():
                continue
            
            keyword = tag_name.strip()
            # 过滤无效关键词：
            # 1. 长度至少2个字符
            # 2. 不是单个或两个小写字母（如 "pe", "en"）
            # 3. 不是纯数字
            # 4. 不是纯标点符号
            # 5. 不是只有点号
            # 6. 长度不超过20个字符
            if (
                len(keyword) < 2 or 
                len(keyword) > 20 or
                invalid_keyword_pattern.match(keyword)
            ):
                continue
            
            # 使用 ArticleTag.article_publish_date（文章的发布日期）
            tag_date = row.tag_date
            date_key = None
            tag_datetime = None
            if tag_date is not None:
                try:
                    # 统一处理：先确保转为 datetime 对象，再提取日期字符串
                    # 关键：带时区的 datetime 需要转换为本地时间后再去除时区
                    if isinstance(tag_date, datetime):
                        if tag_date.tzinfo is not None:
                            tag_datetime = tag_date.astimezone().replace(tzinfo=None)
                        else:
                            tag_datetime = tag_date
                    elif isinstance(tag_date, str):
                        tag_str = tag_date.replace('Z', '+00:00')
                        parsed = datetime.fromisoformat(tag_str)
                        if parsed.tzinfo is not None:
                            tag_datetime = parsed.astimezone().replace(tzinfo=None)
                        else:
                            tag_datetime = parsed
                    elif hasattr(tag_date, 'isoformat') and not isinstance(tag_date, datetime):
                        # date 对象
                        date_key = tag_date.isoformat()
                    else:
                        tag_datetime = normalize_datetime(tag_date)

                    if tag_datetime and isinstance(tag_datetime, datetime):
                        date_key = tag_datetime.date().isoformat()
                    elif date_key is None and tag_date is not None:
                        # 兜底：直接取前10个字符作为日期
                        date_key = str(tag_date)[:10]
                except Exception:
                    date_key = None
                    tag_datetime = None

            # 只统计最近30天的关键词（使用文章的发布日期）
            # 确保比较时两个 datetime 都不带时区
            if tag_datetime:
                try:
                    tag_datetime = normalize_datetime(tag_datetime)
                    compare_date = normalize_datetime(thirty_days_ago)
                    # 确保两个都是 datetime 对象且都不带时区
                    if (isinstance(tag_datetime, datetime) and 
                        isinstance(compare_date, datetime) and
                        tag_datetime.tzinfo is None and 
                        compare_date.tzinfo is None and
                        tag_datetime >= compare_date):
                        keyword_map[keyword] = keyword_map.get(keyword, 0) + 1
                except (TypeError, AttributeError) as e:
                    # 如果比较失败，跳过这条记录
                    pass

            # 记录关键词趋势（按日期统计，使用文章的发布日期）
            if keyword not in keyword_trend_map:
                keyword_trend_map[keyword] = {}
            if date_key and tag_datetime:
                try:
                    tag_datetime = normalize_datetime(tag_datetime)
                    compare_date = normalize_datetime(thirty_days_ago)
                    # 确保两个都是 datetime 对象且都不带时区
                    if (isinstance(tag_datetime, datetime) and 
                        isinstance(compare_date, datetime) and
                        tag_datetime.tzinfo is None and 
                        compare_date.tzinfo is None and
                        tag_datetime >= compare_date):
                        keyword_trend_map[keyword][date_key] = keyword_trend_map[keyword].get(date_key, 0) + 1
                except (TypeError, AttributeError) as e:
                    # 如果比较失败，跳过这条记录
                    pass

        # 排序并取前20个
        keyword_stats = sorted(
            [{"keyword": k, "count": v} for k, v in keyword_map.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:20]

        # 4. 关键词趋势数据（前10个关键词，最近30天）
        top_keywords = [item["keyword"] for item in keyword_stats[:10]]
        
        # 生成日期范围
        date_range = []
        for i in range(30):
            date = (now - timedelta(days=29 - i)).date()
            date_range.append(date.isoformat())

        keyword_trend_data = []
        for date in date_range:
            keywords = {}
            for keyword in top_keywords:
                keywords[keyword] = keyword_trend_map.get(keyword, {}).get(date, 0)
            keyword_trend_data.append({
                "date": date,
                "keywords": keywords
            })

        # 5. 抓取趋势数据（最近30天，按公众号分组，使用文章发布时间）
        # 计算30天前的时间戳（秒级）
        thirty_days_ago_timestamp = int((now - timedelta(days=30)).timestamp())
        
        # 查询所有符合条件的文章（使用发布时间）
        trend_query = session.query(
            Article.publish_time,
            Feed.mp_name,
            Article.id
        ).outerjoin(
            Feed, Article.mp_id == Feed.id
        ).filter(
            and_(
                Article.status != DATA_STATUS.DELETED,
                Article.publish_time >= thirty_days_ago_timestamp
            )
        ).all()

        # 在 Python 层面按日期和公众号分组统计
        trend_map: Dict[str, Dict[str, int]] = {}
        for item in trend_query:
            # 将时间戳转换为日期
            try:
                # publish_time 是秒级时间戳
                publish_timestamp = item.publish_time
                if publish_timestamp and publish_timestamp > 0:
                    publish_date = datetime.fromtimestamp(publish_timestamp)
                    date_key = publish_date.date().isoformat()
                    mp_name = item.mp_name or "未知来源"
                    
                    if date_key not in trend_map:
                        trend_map[date_key] = {}
                    if mp_name not in trend_map[date_key]:
                        trend_map[date_key][mp_name] = 0
                    trend_map[date_key][mp_name] += 1
            except (ValueError, TypeError, OSError) as e:
                # 时间戳转换失败，跳过这条记录
                continue

        # 获取所有出现过的公众号名称
        all_mp_names = set()
        for sources in trend_map.values():
            all_mp_names.update(sources.keys())

        # 生成趋势数据，每个日期包含所有公众号的统计
        trend_data = []
        for date in date_range:
            sources = trend_map.get(date, {})
            # 确保所有公众号都在数据中，即使某天没有文章也显示为0
            sources_dict = {mp_name: sources.get(mp_name, 0) for mp_name in all_mp_names}
            trend_data.append({
                "date": date,
                "sources": sources_dict
            })

        # 调试日志：检查趋势数据是否为空
        from core.print import print_info, print_warning
        trend_has_data = any(
            v > 0
            for item in keyword_trend_data
            for v in item.get("keywords", {}).values()
        )
        if not trend_has_data and keyword_stats:
            print_warning(f"Dashboard: keywordStats 有 {len(keyword_stats)} 个关键词，但 keywordTrendData 全为 0")
            print_warning(f"keyword_trend_map keys: {list(keyword_trend_map.keys())[:5]}")
            if keyword_trend_map:
                sample_kw = list(keyword_trend_map.keys())[0]
                print_warning(f"sample trend data for '{sample_kw}': {dict(list(keyword_trend_map[sample_kw].items())[:3])}")
            print_warning(f"date_range sample: {date_range[:3]}")

        return success_response({
            "stats": {
                "totalArticles": total_articles,
                "totalSources": total_sources,
                "todayArticles": today_articles,
                "weekArticles": week_articles
            },
            "sourceStats": source_stats,
            "keywordStats": keyword_stats,
            "keywordTrendData": keyword_trend_data,
            "trendData": trend_data,
            "_meta": {
                "topKeywords": top_keywords,
                "usingFallback": False
            }
        })

    except Exception as e:
        session.rollback()
        import traceback
        error_detail = traceback.format_exc()
        from core.print import print_error
        print_error(f"获取 Dashboard 统计数据失败: {str(e)}")
        print_error(f"错误详情:\n{error_detail}")
        raise HTTPException(
            status_code=fast_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"获取统计数据失败: {str(e)}"
            )
        )
    finally:
        session.close()

