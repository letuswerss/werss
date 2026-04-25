from fastapi import APIRouter, Depends, HTTPException, status as fast_status, Query, Body
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timedelta, timezone
from core.auth import get_current_user
from core.db import DB
from core.models.base import DATA_STATUS
from core.models.article import Article,ArticleBase
from sqlalchemy import and_, or_, desc, func, distinct
from .base import success_response, error_response
from core.config import cfg
from apis.base import format_search_kw
from core.print import print_warning, print_info, print_error, print_success
from core.log import logger
from core.cache import get_cache, set_cache, get_cache_key, clear_cache_pattern
from typing import Optional, List, Tuple, Dict, Any
from core.article_filter import get_article_filter_engine
from core.storage.avatar_mirror import mirror_feed_avatar_to_minio, mirror_feeds_avatars_batch

router = APIRouter(prefix=f"/articles", tags=["文章管理"])


def _normalize_publish_ts(ts: Optional[int]) -> Optional[int]:
    """将查询参数中的时间统一为与库表一致的毫秒时间戳。"""
    if ts is None:
        return None
    try:
        v = int(ts)
    except (TypeError, ValueError):
        return None
    # 与项目内其它逻辑一致：小于 10^10 视为秒
    if v < 10_000_000_000:
        return v * 1000
    return v


def _parse_tag_id_list(tag_id: Optional[str], tag_ids: Optional[str]) -> List[str]:
    out: List[str] = []
    if tag_id and str(tag_id).strip():
        out.append(str(tag_id).strip())
    if tag_ids and str(tag_ids).strip():
        for part in str(tag_ids).split(","):
            p = part.strip()
            if p:
                out.append(p)
    # 去重且保序
    return list(dict.fromkeys(out))


def _merge_time_bounds(
    publish_from: Optional[int],
    publish_to: Optional[int],
    date_from: Optional[str],
    date_to: Optional[str],
) -> Tuple[Optional[int], Optional[int]]:
    """
    合并时间戳参数与 YYYY-MM-DD 日期参数，取更严格的区间。
    返回 (下界毫秒含, 上界毫秒含)。
    """
    pf = _normalize_publish_ts(publish_from)
    pt = _normalize_publish_ts(publish_to)

    df_ms: Optional[int] = None
    dt_ms: Optional[int] = None
    if date_from and str(date_from).strip():
        try:
            d = datetime.strptime(str(date_from).strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            df_ms = int(d.timestamp() * 1000)
        except ValueError:
            pass
    if date_to and str(date_to).strip():
        try:
            d = datetime.strptime(str(date_to).strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end = d + timedelta(days=1) - timedelta(milliseconds=1)
            dt_ms = int(end.timestamp() * 1000)
        except ValueError:
            pass

    low = pf
    if df_ms is not None:
        low = df_ms if low is None else max(low, df_ms)

    high = pt
    if dt_ms is not None:
        high = dt_ms if high is None else min(high, dt_ms)

    return low, high


class TagMatchMode(str, Enum):
    """标签匹配：任一 / 全部"""

    any = "any"
    all = "all"


class ArticleAiFilterAnalyzeRequest(BaseModel):
    article_ids: List[str] = Field(..., min_length=1, description="需要分析的文章 ID 列表，支持 __all__（全部文章）和 __unfiltered__（仅未过滤过的文章）")


class ArticleAiFilterRestoreRequest(BaseModel):
    article_ids: List[str] = Field(..., min_length=1, description="需要恢复的文章 ID 列表")


    
@router.delete("/clean", summary="清理无效文章(MP_ID不存在于Feeds表中的文章)")
async def clean_orphan_articles(
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.feed import Feed
        from core.models.article import Article
        
        # 找出Articles表中mp_id不在Feeds表中的记录
        subquery = session.query(Feed.id).subquery()
        deleted_count = session.query(Article)\
            .filter(~Article.mp_id.in_(subquery))\
            .delete(synchronize_session=False)
        
        session.commit()
        
        return success_response({
            "message": "清理无效文章成功",
            "deleted_count": deleted_count
        })
    except Exception as e:
        session.rollback()
        print(f"清理无效文章错误: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="清理无效文章失败"
            )
        )
    finally:
        session.close()
    
@router.delete("/clean_duplicate_articles", summary="清理重复文章")
async def clean_duplicate(
    current_user: dict = Depends(get_current_user)
):
    try:
        from tools.clean import clean_duplicate_articles
        (msg, deleted_count) =clean_duplicate_articles()
        return success_response({
            "message": msg,
            "deleted_count": deleted_count
        })
    except Exception as e:
        print(f"清理重复文章: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_201_CREATED,
            detail=error_response(
                code=50001,
                message="清理重复文章"
            )
        )


def _serialize_ai_filter_row(row: Any) -> Dict[str, Any]:
    if not row:
        return {}
    return {
        "article_id": row.article_id,
        "decision": row.decision,
        "category": row.category,
        "confidence": row.confidence,
        "reason": row.reason,
        "model_name": row.model_name,
        "updated_at": row.updated_at,
    }


@router.post("/ai-filter-analyze", summary="AI 过滤文章")
@router.post("/ai-filter/analyze", summary="AI 过滤文章")
async def analyze_ai_filter(
    payload: ArticleAiFilterAnalyzeRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    from core.article_filter import get_article_filter_engine
    from core.models.article_ai_filter import ArticleAiFilter
    from core.models.article_tags import ArticleTag
    from core.models.tags import Tags as TagsModel
    from core.models.feed import Feed

    raw_ids = list(dict.fromkeys([str(item).strip() for item in payload.article_ids if str(item).strip()]))
    if not raw_ids:
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40001, message="文章 ID 不能为空"),
        )

    from sqlalchemy import exists

    session = DB.get_session()
    try:
        # 支持特殊标记：__all__ 全量，__unfiltered__ 仅未过滤过的文章
        if raw_ids == ["__all__"]:
            all_rows = session.query(Article.id).filter(
                Article.status != DATA_STATUS.DELETED
            ).all()
            article_ids = [str(r.id) for r in all_rows]
        elif raw_ids == ["__unfiltered__"]:
            no_filter_row = ~exists().where(ArticleAiFilter.article_id == Article.id)
            all_rows = session.query(Article.id).filter(
                no_filter_row,
                Article.status != DATA_STATUS.DELETED,
            ).all()
            article_ids = [str(r.id) for r in all_rows]
        else:
            article_ids = raw_ids

        if not article_ids:
            return success_response({"items": [], "summary": {"hidden": 0, "keep": 0, "maybe": 0}, "total": 0})

        articles = session.query(Article).filter(Article.id.in_(article_ids)).all()
        article_map = {article.id: article for article in articles}
        ordered_articles = [article_map[aid] for aid in article_ids if aid in article_map]

        if not ordered_articles:
            return success_response({"items": [], "summary": {"hidden": 0, "keep": 0, "maybe": 0}, "total": 0})

        article_tags = session.query(ArticleTag).filter(
            ArticleTag.article_id.in_([a.id for a in ordered_articles])
        ).all()
        tags_by_article: Dict[str, List[str]] = {}
        all_tag_ids = set()
        for at in article_tags:
            tags_by_article.setdefault(at.article_id, []).append(at.tag_id)
            all_tag_ids.add(at.tag_id)

        tags_dict = {}
        if all_tag_ids:
            tags = session.query(TagsModel).filter(
                TagsModel.id.in_(list(all_tag_ids)),
                TagsModel.status == 1
            ).all()
            tags_dict = {t.id: t for t in tags}

        mp_ids = list(set([a.mp_id for a in ordered_articles if a.mp_id]))
        mp_info = {}
        if mp_ids:
            feeds = session.query(Feed).filter(Feed.id.in_(mp_ids)).all()
            mirror_feeds_avatars_batch(session, feeds)
            mp_info = {feed.id: {"mp_name": feed.mp_name, "mp_cover": feed.mp_cover} for feed in feeds}

        engine = get_article_filter_engine()
        items: List[Dict[str, Any]] = []
        summary = {"hidden": 0, "keep": 0, "maybe": 0}

        for article in ordered_articles:
            tag_ids = tags_by_article.get(article.id, [])
            tag_names = [
                tags_dict[tag_id].name
                for tag_id in tag_ids
                if tag_id in tags_dict and tags_dict[tag_id].name
            ]
            mp_name = mp_info.get(article.mp_id, {}).get("mp_name", "未知公众号")
            result = await engine.classify(
                title=article.title or "",
                tags=tag_names,
                source=mp_name,
                description=article.description or "",
            )

            row = session.query(ArticleAiFilter).filter(ArticleAiFilter.article_id == article.id).first()
            if not row:
                row = ArticleAiFilter(article_id=article.id)
                session.add(row)

            row.decision = result.decision
            row.category = result.category
            row.confidence = result.confidence
            row.reason = result.reason
            row.model_name = result.model_name or engine.model
            row.source_title = article.title
            row.source_tags = ",".join(tag_names)
            row.updated_at = datetime.now()
            if not row.created_at:
                row.created_at = datetime.now()

            if result.decision == "hide":
                article.status = DATA_STATUS.INACTIVE

            summary_key = result.decision if result.decision in summary else "keep"
            summary[summary_key] += 1
            items.append(
                {
                    "article_id": article.id,
                    "title": article.title,
                    "decision": result.decision,
                    "category": result.category,
                    "confidence": result.confidence,
                    "reason": result.reason,
                    "model_name": result.model_name,
                    "mp_name": mp_name,
                    "tags": tag_names,
                }
            )

        session.commit()
        clear_cache_pattern("articles:")

        return success_response({"items": items, "summary": summary, "total": len(ordered_articles)})
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        print_error(f"AI 过滤文章失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"AI 过滤文章失败: {str(e)}"),
        )
    finally:
        session.close()


@router.get("/ai-filter/unfiltered-ids", summary="获取未过滤文章ID列表")
async def get_unfiltered_article_ids(
    current_user: dict = Depends(get_current_user),
):
    """返回所有未删除且未被 AI 过滤过的文章 ID 列表（轻量查询，仅返回 ID）。"""
    from core.models.article_ai_filter import ArticleAiFilter
    from sqlalchemy import exists

    session = DB.get_session()
    try:
        no_filter_row = ~exists().where(ArticleAiFilter.article_id == Article.id)
        rows = session.query(Article.id).filter(
            no_filter_row,
            Article.status != DATA_STATUS.DELETED,
        ).all()
        ids = [str(r.id) for r in rows]
        return success_response({"ids": ids, "total": len(ids)})
    except Exception as e:
        print_error(f"获取未过滤文章ID失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"获取未过滤文章ID失败: {str(e)}"),
        )
    finally:
        session.close()


@router.get("/ai-filter/all-ids", summary="获取全部未删除文章ID（供前端分批AI过滤）")
async def get_all_article_ids_for_ai_filter(
    current_user: dict = Depends(get_current_user),
):
    """与 analyze 中 __all__ 解析一致：仅 ID 列表，便于前端逐批请求并展示进度。"""
    session = DB.get_session()
    try:
        rows = session.query(Article.id).filter(Article.status != DATA_STATUS.DELETED).all()
        ids = [str(r.id) for r in rows]
        return success_response({"ids": ids, "total": len(ids)})
    except Exception as e:
        print_error(f"获取全库文章ID失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"获取全库文章ID失败: {str(e)}"),
        )
    finally:
        session.close()


@router.post("/ai-filter-restore", summary="恢复 AI 过滤文章")
@router.post("/ai-filter/restore", summary="恢复 AI 过滤文章")
async def restore_ai_filter(
    payload: ArticleAiFilterRestoreRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    from core.models.article_ai_filter import ArticleAiFilter

    article_ids = list(dict.fromkeys([str(item).strip() for item in payload.article_ids if str(item).strip()]))
    if not article_ids:
        raise HTTPException(
            status_code=fast_status.HTTP_400_BAD_REQUEST,
            detail=error_response(code=40001, message="文章 ID 不能为空"),
        )

    session = DB.get_session()
    try:
        rows = session.query(ArticleAiFilter).filter(ArticleAiFilter.article_id.in_(article_ids)).all()
        if not rows:
            return success_response({"restored": 0})

        for row in rows:
            row.decision = "keep"
            row.category = "manual_restore"
            row.confidence = 1.0
            row.reason = "用户手动恢复"
            row.model_name = "manual"
            row.updated_at = datetime.now()

        articles = session.query(Article).filter(Article.id.in_(article_ids)).all()
        for article in articles:
            article.status = DATA_STATUS.ACTIVE

        session.commit()
        clear_cache_pattern("articles:")
        return success_response({"restored": len(rows)})
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        print_error(f"恢复 AI 过滤失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(code=50001, message=f"恢复 AI 过滤失败: {str(e)}"),
        )
    finally:
        session.close()


@router.api_route(
    "",
    summary="获取文章列表",
    methods=["GET", "POST"],
    operation_id="get_articles_list",
    openapi_extra={
        "description": (
            "支持分页、标题搜索、公众号、状态、是否含正文；"
            "可选 **发布时间范围**（时间戳或 UTC 日期）、**标签筛选**（任一/全部）。"
            "认证：JWT 或 `X-API-Key`。"
        )
    },
)
async def get_articles(
    offset: int = Query(0, ge=0, description="分页偏移，从 0 开始"),
    limit: int = Query(5, ge=1, le=100, description="每页条数，最大 100"),
    status: Optional[str] = Query(None, description="按状态精确筛选；不传则排除已删除文章"),
    search: Optional[str] = Query(None, description="标题关键词，空格/|/- 拆成多词，满足任一词即匹配"),
    mp_id: Optional[str] = Query(None, description="仅返回指定公众号 mp_id 的文章"),
    has_content: bool = Query(False, description="true 时只查含正文 content 的记录"),
    publish_from: Optional[int] = Query(
        None,
        description="发布时间下界（含）。数值 < 10^12 视为秒，否则为毫秒",
    ),
    publish_to: Optional[int] = Query(
        None,
        description="发布时间上界（含）。数值 < 10^12 视为秒，否则为毫秒",
    ),
    publish_date_from: Optional[str] = Query(
        None,
        description="发布日期起始 YYYY-MM-DD（UTC 日界线，含当日 0 点）",
        examples=["2026-01-01"],
    ),
    publish_date_to: Optional[str] = Query(
        None,
        description="发布日期结束 YYYY-MM-DD（UTC，含当日结束）",
        examples=["2026-03-20"],
    ),
    tag_id: Optional[str] = Query(None, description="单个标签 ID（与 tags 接口返回的 id 一致）"),
    tag_ids: Optional[str] = Query(
        None,
        description="多个标签 ID，逗号分隔；可与 tag_id 同时使用，会去重合并",
    ),
    tag_match: TagMatchMode = Query(
        TagMatchMode.any,
        description="any=命中任一标签；all=必须同时包含所列全部标签",
    ),
    current_user: dict = Depends(get_current_user),
):
    resolved_tags = _parse_tag_id_list(tag_id, tag_ids)
    time_low, time_high = _merge_time_bounds(
        publish_from, publish_to, publish_date_from, publish_date_to
    )
    if time_low is not None and time_high is not None and time_low > time_high:
        from .base import success_response
        return success_response({"list": [], "total": 0})

    # 生成缓存键（含新增筛选条件）
    cache_key = f"articles:{get_cache_key(offset, limit, status, mp_id, search, has_content, time_low, time_high, resolved_tags, tag_match.value)}"

    # 尝试从缓存获取
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        return cached_result

    session = DB.get_session()
    try:
        from core.models.article_tags import ArticleTag

        # 构建查询条件
        # 统一使用 ArticleBase 进行查询（包含 status 字段）
        query = session.query(ArticleBase)
        if has_content:
            query = session.query(Article)

        # 默认过滤已删除的文章（除非明确指定 status 参数）
        if status:
            # 如果指定了 status，按指定状态过滤（包括已删除状态）
            query = query.filter(ArticleBase.status == int(status))
        else:
            # 默认不显示已删除的文章
            query = query.filter(ArticleBase.status != DATA_STATUS.DELETED)
        if mp_id:
            query = query.filter(ArticleBase.mp_id == mp_id)
        if search:
            # format_search_kw 使用 Article 模型，但 Article 继承自 ArticleBase，共享同一张表
            # 所以可以直接使用
            query = query.filter(
               format_search_kw(search)
            )

        if time_low is not None:
            query = query.filter(ArticleBase.publish_time >= time_low)
        if time_high is not None:
            query = query.filter(ArticleBase.publish_time <= time_high)

        if resolved_tags:
            if tag_match == TagMatchMode.all:
                n = len(resolved_tags)
                subq = (
                    session.query(ArticleTag.article_id)
                    .filter(ArticleTag.tag_id.in_(resolved_tags))
                    .group_by(ArticleTag.article_id)
                    .having(func.count(distinct(ArticleTag.tag_id)) == n)
                )
                query = query.filter(ArticleBase.id.in_(subq))
            else:
                subq = (
                    session.query(ArticleTag.article_id)
                    .filter(ArticleTag.tag_id.in_(resolved_tags))
                    .distinct()
                )
                query = query.filter(ArticleBase.id.in_(subq))

        # 获取总数
        total = query.count()
        query = query.order_by(ArticleBase.publish_time.desc()).offset(offset).limit(limit)
        # 分页查询（按发布时间降序）
        articles = query.all()

        try:
            logger.debug(
                "articles list SQL: %s",
                str(query.statement.compile(compile_kwargs={"literal_binds": True})),
            )
        except Exception:
            pass
        
        if not articles:
            # 如果没有文章，直接返回空列表
            from .base import success_response
            empty_result = success_response({
                "list": [],
                "total": total
            })
            set_cache(cache_key, empty_result, ttl=300)
            return empty_result
                       
        # 批量查询优化：一次性获取所有需要的数据
        from core.models.feed import Feed
        from core.models.tags import Tags as TagsModel
        from core.models.article_ai_filter import ArticleAiFilter
        
        # 1. 批量查询公众号信息
        article_ids = [a.id for a in articles]
        mp_ids = list(set([a.mp_id for a in articles if a.mp_id]))
        mp_info = {}
        if mp_ids:
            feeds = session.query(Feed).filter(Feed.id.in_(mp_ids)).all()
            mirror_feeds_avatars_batch(session, feeds)
            # 批量记录名称和头像
            mp_info = {feed.id: {"mp_name": feed.mp_name, "mp_cover": feed.mp_cover} for feed in feeds}
        
        # 2. 批量查询所有文章的标签关联
        all_article_tags = session.query(ArticleTag).filter(
            ArticleTag.article_id.in_(article_ids)
        ).all()
        
        # 3. 按文章 ID 分组标签 ID
        tags_by_article = {}
        all_tag_ids = set()
        for at in all_article_tags:
            if at.article_id not in tags_by_article:
                tags_by_article[at.article_id] = []
            tags_by_article[at.article_id].append(at.tag_id)
            all_tag_ids.add(at.tag_id)
        
        # 4. 批量查询所有标签信息
        tags_dict = {}
        if all_tag_ids:
            tags = session.query(TagsModel).filter(
                TagsModel.id.in_(list(all_tag_ids)),
                TagsModel.status == 1
            ).all()
            tags_dict = {t.id: t for t in tags}
        
        # 5. 批量查询 AI 过滤结果
        ai_filter_rows = session.query(ArticleAiFilter).filter(
            ArticleAiFilter.article_id.in_(article_ids)
        ).all()
        ai_filter_map = {row.article_id: row for row in ai_filter_rows}

        # 6. 在内存中组装数据
        article_list = []
        for article in articles:
            article_dict = article.__dict__.copy()
            
            # 填充公众号信息
            info = mp_info.get(article.mp_id, {})
            article_dict["mp_name"] = info.get("mp_name", "未知公众号")
            article_dict["mp_cover"] = info.get("mp_cover", "")
            
            # 从预加载的数据中获取标签
            article_tag_ids = tags_by_article.get(article.id, [])
            article_tags = [tags_dict[tag_id] for tag_id in article_tag_ids if tag_id in tags_dict]
            article_dict["tags"] = [{"id": t.id, "name": t.name} for t in article_tags]
            article_dict["tag_names"] = [t.name for t in article_tags]  # 用于显示
            # topics 应该独立于 tags，不应该被 tag 覆盖
            article_dict["topics"] = []
            article_dict["topic_names"] = []
            ai_row = ai_filter_map.get(article.id)
            if ai_row:
                article_dict["ai_filter_status"] = ai_row.decision
                article_dict["ai_filter_category"] = ai_row.category
                article_dict["ai_filter_confidence"] = ai_row.confidence
                article_dict["ai_filter_reason"] = ai_row.reason
                article_dict["ai_filter_model"] = ai_row.model_name
                article_dict["ai_filter_updated_at"] = ai_row.updated_at
            else:
                article_dict["ai_filter_status"] = None
                article_dict["ai_filter_category"] = None
                article_dict["ai_filter_confidence"] = None
                article_dict["ai_filter_reason"] = None
                article_dict["ai_filter_model"] = None
                article_dict["ai_filter_updated_at"] = None
            
            article_list.append(article_dict)
        
        from .base import success_response
        result = success_response({
            "list": article_list,
            "total": total
        })
        
        # 存入缓存（缓存5分钟）
        set_cache(cache_key, result, ttl=300)
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章列表失败: {str(e)}"
            )
        )
    finally:
        session.close()

@router.get("/{article_id}", summary="获取文章详情")
async def get_article_detail(
    article_id: str,
    content: bool = False,
    # current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        article = session.query(Article).filter(Article.id==article_id).filter(Article.status != DATA_STATUS.DELETED).first()
        if not article:
            from .base import error_response
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        
        # 转换为字典并添加额外信息
        article_dict = article.__dict__.copy()
        
        # 查询公众号名称
        from core.models.feed import Feed
        if article.mp_id:
            feed = session.query(Feed).filter(Feed.id == article.mp_id).first()
            if feed:
                mirror_feed_avatar_to_minio(session, feed)
            article_dict["mp_name"] = feed.mp_name if feed else "未知公众号"
            article_dict["mp_cover"] = feed.mp_cover if feed else ""
        
        # 获取文章的标签
        from core.models.article_tags import ArticleTag
        from core.models.tags import Tags as TagsModel
        article_tags = session.query(ArticleTag).filter(
            ArticleTag.article_id == article.id
        ).all()
        tag_ids = [at.tag_id for at in article_tags]
        tags = session.query(TagsModel).filter(
            TagsModel.id.in_(tag_ids),
            TagsModel.status == 1
        ).all() if tag_ids else []
        article_dict["tags"] = [{"id": t.id, "name": t.name} for t in tags]
        article_dict["tag_names"] = [t.name for t in tags]
        # topics 应该独立于 tags，不应该被 tag 覆盖
        article_dict["topics"] = []
        article_dict["topic_names"] = []
        
        return success_response(article_dict)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取文章详情失败: {str(e)}"
            )
        )
    finally:
        session.close()

# 更新文章请求模型
class ArticleUpdateRequest(BaseModel):
    """更新文章请求模型"""
    title: Optional[str] = Field(None, description="文章标题")
    description: Optional[str] = Field(None, description="文章描述")
    url: Optional[str] = Field(None, description="文章链接")
    pic_url: Optional[str] = Field(None, description="文章封面图链接")
    status: Optional[int] = Field(None, description="文章状态：1=启用，2=禁用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "文章标题",
                "description": "文章描述",
                "url": "https://mp.weixin.qq.com/s/xxx",
                "pic_url": "https://example.com/image.jpg",
                "status": 1
            }
        }

@router.put("/{article_id}", summary="更新文章")
async def update_article(
    article_id: str,
    article_data: ArticleUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    更新文章信息
    可以更新标题、描述、链接、封面图等字段
    """
    session = DB.get_session()
    try:
        from core.models.article import Article
        from datetime import datetime
        
        # 检查文章是否存在
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        
        # 更新允许修改的字段
        update_data = article_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None and hasattr(article, field):
                setattr(article, field, value)
        
        # 更新 updated_at 时间戳
        article.updated_at = datetime.now()
        
        session.commit()
        print_success(f"成功更新文章 {article.title}")
        
        # 清除文章列表缓存（因为文章信息已更新）
        clear_cache_pattern("articles:")
        
        return success_response(None, message="文章更新成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        print_error(f"更新文章失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"更新文章失败: {str(e)}"
            )
        )
    finally:
        session.close()

@router.delete("/{article_id}", summary="删除文章")
async def delete_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        from core.models.article import Article
        
        # 检查文章是否存在
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        # 根据配置决定是逻辑删除还是物理删除
        # 默认使用物理删除（真正从数据库删除），如果需要逻辑删除，可在配置文件中设置 article.true_delete: False
        true_delete = cfg.get("article.true_delete", True)
        if true_delete:
            # 物理删除（真正从数据库删除）
            session.delete(article)
            message = "文章已删除"
        else:
            # 逻辑删除（更新状态为deleted，保留数据）
            article.status = DATA_STATUS.DELETED
            message = "文章已标记为删除"
        
        session.commit()
        
        # 清除文章列表缓存（因为文章已删除）
        clear_cache_pattern("articles:")
        
        return success_response(None, message=message)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"删除文章失败: {str(e)}"
            )
        )
    finally:
        session.close()

@router.get("/{article_id}/next", summary="获取下一篇文章")
async def get_next_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 获取当前文章的发布时间
        current_article = session.query(Article).filter(Article.id == article_id).first()
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="当前文章不存在"
                )
            )
        
        # 查询发布时间更晚的第一篇文章
        next_article = session.query(Article)\
            .filter(Article.publish_time > current_article.publish_time)\
            .filter(Article.status != DATA_STATUS.DELETED)\
            .filter(Article.mp_id == current_article.mp_id)\
            .order_by(Article.publish_time.asc())\
            .first()
        
        if not next_article:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=40402,
                    message="没有下一篇文章"
                )
            )
        
        return success_response(next_article)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取下一篇文章失败: {str(e)}"
            )
        )
    finally:
        session.close()

@router.get("/{article_id}/prev", summary="获取上一篇文章")
async def get_prev_article(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = DB.get_session()
    try:
        # 获取当前文章的发布时间
        current_article = session.query(Article).filter(Article.id == article_id).first()
        if not current_article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="当前文章不存在"
                )
            )
        
        # 查询发布时间更早的第一篇文章
        prev_article = session.query(Article)\
            .filter(Article.publish_time < current_article.publish_time)\
            .filter(Article.status != DATA_STATUS.DELETED)\
            .filter(Article.mp_id == current_article.mp_id)\
            .order_by(Article.publish_time.desc())\
            .first()
        
        if not prev_article:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=40403,
                    message="没有上一篇文章"
                )
            )
        
        return success_response(prev_article)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"获取上一篇文章失败: {str(e)}"
            )
        )
    finally:
        session.close()

@router.post("/{article_id}/fetch_content", summary="重新获取文章内容")
async def fetch_article_content(
    article_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    重新获取文章内容
    如果文章内容为空或需要更新，可以调用此接口重新获取
    """
    session = DB.get_session()
    try:
        # 查询文章
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=fast_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="文章不存在"
                )
            )
        
        # 构建URL
        if article.url:
            url = article.url
        else:
            url = f"https://mp.weixin.qq.com/s/{article.id}"
        
        print_info(f"正在重新获取文章内容: {article.title}, URL: {url}")
        
        # 根据配置选择获取方式
        from core.wx.base import WxGather
        from driver.wxarticle import Web
        import random
        import time
        import asyncio

        content = None
        fetched_metrics = {}
        if cfg.get("gather.content_mode", "web") == "web":
            # 使用 Web 模式（Playwright）
            try:
                result = await asyncio.to_thread(Web.get_article_content, url)
                content = result.get("content") if result else None
                fetched_metrics = {
                    "read_count": result.get("read_count") if result else None,
                    "like_count": result.get("like_count") if result else None,
                    "looking_count": result.get("looking_count") if result else None,
                    "comment_count": result.get("comment_count") if result else None,
                    "share_count": result.get("share_count") if result else None,
                }
            except Exception as e:
                print_error(f"Web模式获取内容失败: {e}")
        else:
            # 使用 API 模式
            try:
                ga = WxGather().Model()
                content = ga.content_extract(url)
            except Exception as e:
                print_error(f"API模式获取内容失败: {e}")
        
        if content:
            # 检查内容是否被删除
            if content == "DELETED":
                article.status = DATA_STATUS.DELETED
                session.commit()
                # 清除文章列表缓存（因为文章状态已更新）
                clear_cache_pattern("articles:")
                raise HTTPException(
                    status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                    detail=error_response(
                        code=40404,
                        message="文章内容已被发布者删除"
                    )
                )
            
            # 更新内容
            article.content = content
            for field, value in fetched_metrics.items():
                if hasattr(article, field):
                    setattr(article, field, value)
            session.commit()
            print_success(f"成功更新文章 {article.title} 的内容")
            
            # 清除文章列表缓存（因为文章内容已更新）
            clear_cache_pattern("articles:")
            
            return success_response({
                "message": "内容获取成功",
                "content_length": len(content)
            })
        else:
            raise HTTPException(
                status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
                detail=error_response(
                    code=50002,
                    message="获取文章内容失败，请稍后重试"
                )
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        print_error(f"重新获取文章内容失败: {str(e)}")
        raise HTTPException(
            status_code=fast_status.HTTP_406_NOT_ACCEPTABLE,
            detail=error_response(
                code=50001,
                message=f"重新获取文章内容失败: {str(e)}"
            )
        )
    finally:
        session.close()
