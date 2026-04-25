import json
import inspect
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Body, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func

from apis.tag_clusters import _get_tag_cluster_payload
from core.db import DB
from core.models.article import Article, ArticleBase
from core.models.article_ai_filter import ArticleAiFilter
from core.models.article_tags import ArticleTag
from core.models.base import DATA_STATUS
from core.models.feed import Feed
from core.models.tags import Tags as TagsModel
from core.models.tag_clusters import TagCluster
from core.models.tag_cluster_members import TagClusterMember
from core.print import print_warning
from core.visualization import compute_2d_layout, normalize_coordinates

router = APIRouter(prefix="/mcp", tags=["MCP"])

MCP_SERVER_NAME = "WeRSS MCP"
MCP_SERVER_VERSION = "1.0.0"
MCP_PROTOCOL_VERSION = "2025-03-26"


class MCPError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class ArticlesListParams(BaseModel):
    page: int = Field(1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")
    search: Optional[str] = Field(None, description="标题关键词")
    mp_id: Optional[str] = Field(None, description="公众号 ID")
    status: Optional[int] = Field(None, description="文章状态")
    has_content: bool = Field(False, description="仅含正文")


class ArticleGetParams(BaseModel):
    article_id: str = Field(..., description="文章 ID")


class ArticleStatusUpdateParams(BaseModel):
    article_id: str = Field(..., description="文章 ID")
    status: int = Field(..., description="文章状态")


class ArticleAiFilterParams(BaseModel):
    article_ids: list[str] = Field(..., min_length=1, description="文章 ID 列表")


class ArticleAiFilterRestoreParams(BaseModel):
    article_ids: list[str] = Field(..., min_length=1, description="文章 ID 列表")


class TagsListParams(BaseModel):
    offset: int = Field(0, ge=0, description="偏移")
    limit: int = Field(20, ge=1, le=100, description="条数")
    search: Optional[str] = Field(None, description="标签名称关键词")


class TagGetParams(BaseModel):
    tag_id: str = Field(..., description="标签 ID")


class TagStatusUpdateParams(BaseModel):
    tag_id: str = Field(..., description="标签 ID")
    status: int = Field(..., description="标签状态")


class TagClusterListParams(BaseModel):
    offset: int = Field(0, ge=0, description="偏移")
    limit: int = Field(20, ge=1, le=100, description="条数")


class TagClusterGetParams(BaseModel):
    cluster_id: str = Field(..., description="聚类 ID")


class TagClusterVizParams(BaseModel):
    cluster_id: str = Field(..., description="聚类 ID")
    method: str = Field("pca", description="降维方法")
    include_edges: bool = Field(True, description="是否包含边")
    min_edge_weight: float = Field(0.5, ge=0.0, le=1.0, description="最小边权重")
    normalize: bool = Field(True, description="是否归一化坐标")


class TagClusterNetworkParams(BaseModel):
    cluster_id: str = Field(..., description="聚类 ID")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="最小相似度")
    layout_type: str = Field("force", description="布局类型")
    max_nodes: int = Field(100, ge=10, le=500, description="最大节点数")


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=_json_default, indent=2)


def _rpc_result(request_id: Any, result: Any):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _rpc_error(request_id: Any, code: int, message: str, data: Any = None):
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if data is not None:
        error["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error,
    }


def _success_content(payload: Any):
    return {
        "content": [
            {
                "type": "text",
                "text": _json_text(payload),
            }
        ],
        "isError": False,
    }


def _error_content(message: str, payload: Any = None):
    body = {"message": message}
    if payload is not None:
        body["data"] = payload
    return {
        "content": [
            {
                "type": "text",
                "text": _json_text(body),
            }
        ],
        "isError": True,
    }


def _check_origin(request: Request):
    allowed = [item.strip() for item in os.getenv("MCP_ALLOWED_ORIGINS", "").split(",") if item.strip()]
    if not allowed:
        return
    origin = request.headers.get("origin")
    if origin and origin not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden origin")


def _get_expected_token() -> Optional[str]:
    return (os.getenv("WERSS_MCP_TOKEN") or os.getenv("MCP_TOKEN") or "").strip() or None


def _check_auth(authorization: Optional[str], x_mcp_token: Optional[str]):
    expected = _get_expected_token()
    if not expected:
        return

    token = (x_mcp_token or "").strip()
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()

    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _get_session():
    return DB.get_session()


def _parse_request_body(body: Any):
    if isinstance(body, dict):
        return [body]
    if isinstance(body, list):
        return body
    raise MCPError(-32600, "Invalid Request")


def _article_public_payload(article: ArticleBase, tags_by_article: dict[str, list[str]], tags_lookup: dict[str, TagsModel], ai_map: dict[str, ArticleAiFilter]):
    article_dict = article.__dict__.copy()
    article_tags = [tags_lookup[tag_id] for tag_id in tags_by_article.get(article.id, []) if tag_id in tags_lookup]
    article_dict["tags"] = [{"id": item.id, "name": item.name} for item in article_tags]
    article_dict["tag_names"] = [item.name for item in article_tags]
    article_dict["topics"] = []
    article_dict["topic_names"] = []
    ai_row = ai_map.get(article.id)
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
    article_dict.pop("_sa_instance_state", None)
    return article_dict


def _list_articles(args: dict[str, Any]):
    session = _get_session()
    try:
        page = max(1, int(args.get("page", 1)))
        page_size = max(1, min(100, int(args.get("page_size", 20))))
        search = (args.get("search") or "").strip() or None
        mp_id = (args.get("mp_id") or "").strip() or None
        status = args.get("status")
        has_content = bool(args.get("has_content", False))
        offset = (page - 1) * page_size

        query = session.query(ArticleBase)
        if has_content:
            query = session.query(Article)
        if status is not None:
            query = query.filter(ArticleBase.status == int(status))
        else:
            query = query.filter(ArticleBase.status != DATA_STATUS.DELETED)
        if mp_id:
            query = query.filter(ArticleBase.mp_id == mp_id)
        if search:
            from apis.base import format_search_kw
            query = query.filter(format_search_kw(search))

        total = query.count()
        articles = query.order_by(ArticleBase.publish_time.desc()).offset(offset).limit(page_size).all()
        if not articles:
            return {"items": [], "total": total, "page": page, "page_size": page_size}

        article_ids = [item.id for item in articles]
        mp_ids = list({item.mp_id for item in articles if item.mp_id})

        mp_lookup = {}
        if mp_ids:
            feeds = session.query(Feed).filter(Feed.id.in_(mp_ids)).all()
            mp_lookup = {feed.id: {"mp_name": feed.mp_name, "mp_cover": feed.mp_cover} for feed in feeds}

        article_tags = session.query(ArticleTag).filter(ArticleTag.article_id.in_(article_ids)).all()
        tags_by_article: dict[str, list[str]] = {}
        tag_ids = set()
        for item in article_tags:
            tags_by_article.setdefault(item.article_id, []).append(item.tag_id)
            tag_ids.add(item.tag_id)

        tags_lookup = {}
        if tag_ids:
            tag_rows = session.query(TagsModel).filter(TagsModel.id.in_(list(tag_ids)), TagsModel.status == 1).all()
            tags_lookup = {item.id: item for item in tag_rows}

        ai_rows = session.query(ArticleAiFilter).filter(ArticleAiFilter.article_id.in_(article_ids)).all()
        ai_map = {item.article_id: item for item in ai_rows}

        items = []
        for article in articles:
            item = _article_public_payload(article, tags_by_article, tags_lookup, ai_map)
            item["mp_name"] = mp_lookup.get(article.mp_id, {}).get("mp_name", "未知公众号")
            item["mp_cover"] = mp_lookup.get(article.mp_id, {}).get("mp_cover", "")
            items.append(item)

        return {"items": items, "total": total, "page": page, "page_size": page_size}
    finally:
        session.close()


def _get_article(article_id: str):
    session = _get_session()
    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise MCPError(-32004, "Article not found")

        article_tags = session.query(ArticleTag).filter(ArticleTag.article_id == article_id).all()
        tag_ids = [item.tag_id for item in article_tags]
        tags_lookup = {}
        if tag_ids:
            tag_rows = session.query(TagsModel).filter(TagsModel.id.in_(tag_ids)).all()
            tags_lookup = {item.id: item for item in tag_rows}
        ai_row = session.query(ArticleAiFilter).filter(ArticleAiFilter.article_id == article_id).first()
        ai_map = {article_id: ai_row} if ai_row else {}
        return _article_public_payload(article, {article_id: tag_ids}, tags_lookup, ai_map)
    finally:
        session.close()


def _update_article_status(article_id: str, status: int):
    session = _get_session()
    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise MCPError(-32004, "Article not found")
        article.status = status
        session.commit()
        session.refresh(article)
        return {"article_id": article_id, "status": article.status}
    finally:
        session.close()


def _list_tags(args: dict[str, Any]):
    session = _get_session()
    try:
        offset = max(0, int(args.get("offset", 0)))
        limit = max(1, min(100, int(args.get("limit", 20))))
        search = (args.get("search") or "").strip().lower() or None

        three_days_ago = datetime.now() - timedelta(days=3)
        query = session.query(
            TagsModel,
            func.count(
                case(
                    (
                        and_(
                            Article.id.isnot(None),
                            Article.status != DATA_STATUS.DELETED,
                            Article.created_at >= three_days_ago,
                        ),
                        ArticleTag.id,
                    ),
                    else_=None,
                )
            ).label("article_count")
        ).outerjoin(ArticleTag, TagsModel.id == ArticleTag.tag_id).outerjoin(
            Article, Article.id == ArticleTag.article_id
        ).group_by(TagsModel.id)
        if search:
            query = query.filter(TagsModel.name.ilike(f"%{search}%"))

        total = query.count()
        rows = query.offset(offset).limit(limit).all()
        items = []
        for tag, article_count in rows:
            items.append({
                "id": tag.id,
                "name": tag.name,
                "cover": tag.cover,
                "intro": tag.intro,
                "status": tag.status,
                "mps_id": tag.mps_id,
                "is_custom": tag.is_custom,
                "sync_time": tag.sync_time,
                "update_time": tag.update_time,
                "created_at": tag.created_at.isoformat() if tag.created_at else None,
                "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
                "article_count": int(article_count or 0),
            })
        return {"items": items, "total": total, "offset": offset, "limit": limit}
    finally:
        session.close()


def _get_tag(tag_id: str):
    session = _get_session()
    try:
        tag = session.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            raise MCPError(-32004, "Tag not found")
        return {
            "id": tag.id,
            "name": tag.name,
            "cover": tag.cover,
            "intro": tag.intro,
            "status": tag.status,
            "mps_id": tag.mps_id,
            "is_custom": tag.is_custom,
            "sync_time": tag.sync_time,
            "update_time": tag.update_time,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
        }
    finally:
        session.close()


def _update_tag_status(tag_id: str, status: int):
    session = _get_session()
    try:
        tag = session.query(TagsModel).filter(TagsModel.id == tag_id).first()
        if not tag:
            raise MCPError(-32004, "Tag not found")
        tag.status = status
        tag.updated_at = datetime.now()
        session.commit()
        session.refresh(tag)
        return {"tag_id": tag_id, "status": tag.status}
    finally:
        session.close()


def _list_tag_clusters(args: dict[str, Any]):
    session = _get_session()
    try:
        offset = max(0, int(args.get("offset", 0)))
        limit = max(1, min(100, int(args.get("limit", 20))))
        total = session.query(TagCluster).count()
        rows = (
            session.query(TagCluster)
            .order_by(TagCluster.size.desc(), TagCluster.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "centroid_tag_id": row.centroid_tag_id,
                "size": row.size,
                "cluster_version": row.cluster_version,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in rows
        ]
        return {"items": items, "total": total, "offset": offset, "limit": limit}
    finally:
        session.close()


def _get_tag_cluster(cluster_id: str):
    session = _get_session()
    try:
        payload = _get_tag_cluster_payload(session, cluster_id)
        if not payload:
            raise MCPError(-32004, "Tag cluster not found")
        return payload
    finally:
        session.close()


def _get_tag_cluster_visualization(params: dict[str, Any]):
    session = _get_session()
    try:
        cluster_id = params["cluster_id"]
        cluster = session.query(TagCluster).filter(TagCluster.id == cluster_id).first()
        if not cluster:
            raise MCPError(-32004, "Tag cluster not found")

        layout_data = compute_2d_layout(
            cluster_id=cluster_id,
            db=session,
            method=params.get("method", "pca"),
            include_edges=bool(params.get("include_edges", True)),
            min_edge_weight=float(params.get("min_edge_weight", 0.5)),
        )
        if params.get("normalize", True) and layout_data.get("nodes"):
            layout_data["nodes"] = normalize_coordinates(layout_data["nodes"])
        layout_data["metadata"]["cluster_name"] = cluster.name
        layout_data["metadata"]["cluster_description"] = cluster.description
        layout_data["metadata"]["centroid_tag_id"] = cluster.centroid_tag_id
        layout_data["metadata"]["cluster_size"] = cluster.size
        return layout_data
    finally:
        session.close()


def _get_tag_cluster_network(params: dict[str, Any]):
    session = _get_session()
    try:
        cluster_id = params["cluster_id"]
        cluster = session.query(TagCluster).filter(TagCluster.id == cluster_id).first()
        if not cluster:
            raise MCPError(-32004, "Tag cluster not found")

        member_rows = (
            session.query(TagClusterMember, TagsModel)
            .join(TagsModel, TagsModel.id == TagClusterMember.tag_id)
            .filter(TagClusterMember.cluster_id == cluster_id)
            .order_by(TagClusterMember.member_score.desc())
            .limit(int(params.get("max_nodes", 100)))
            .all()
        )

        if not member_rows:
            return {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "cluster_id": cluster_id,
                    "layout_type": params.get("layout_type", "force"),
                    "node_count": 0,
                    "edge_count": 0,
                },
            }

        nodes = []
        tag_ids = []
        article_count_by_tag: dict[str, int] = {}
        for member, tag in member_rows:
            tag_ids.append(member.tag_id)
            nodes.append({
                "id": member.tag_id,
                "name": tag.name or member.tag_id,
                "score": member.member_score / 10000.0,
                "cluster": cluster_id,
                "size": max(5, min(20, 5 + (member.member_score / 10000.0) * 15)),
            })

        article_rows = session.query(ArticleTag.article_id, ArticleTag.tag_id).filter(ArticleTag.tag_id.in_(tag_ids)).all()
        article_to_tags: dict[str, set[str]] = {}
        for article_id, tag_id in article_rows:
            if article_id and tag_id:
                article_to_tags.setdefault(article_id, set()).add(tag_id)
                article_count_by_tag[tag_id] = article_count_by_tag.get(tag_id, 0) + 1

        pair_counts: dict[tuple[str, str], int] = {}
        from itertools import combinations
        for article_tag_ids in article_to_tags.values():
            related_tags = sorted(article_tag_ids)
            if len(related_tags) < 2:
                continue
            for source_id, target_id in combinations(related_tags, 2):
                pair_counts[(source_id, target_id)] = pair_counts.get((source_id, target_id), 0) + 1

        edges = []
        for (source_id, target_id), pair_count in pair_counts.items():
            denominator = min(article_count_by_tag.get(source_id, 0), article_count_by_tag.get(target_id, 0))
            if denominator <= 0:
                continue
            weight = pair_count / denominator
            if weight >= float(params.get("min_similarity", 0.3)):
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "weight": float(weight),
                    "cooccurrence_score": float(weight),
                    "cooccurrence_count": pair_count,
                    "source_article_count": article_count_by_tag.get(source_id, 0),
                    "target_article_count": article_count_by_tag.get(target_id, 0),
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "cluster_id": cluster_id,
                "cluster_name": cluster.name,
                "layout_type": params.get("layout_type", "force"),
                "node_count": len(nodes),
                "edge_count": len(edges),
                "min_similarity": float(params.get("min_similarity", 0.3)),
                "relation_source": "article_cooccurrence",
            },
        }
    finally:
        session.close()


async def _analyze_articles_ai_filter(arguments: dict[str, Any]):
    from core.article_filter import get_article_filter_engine
    from core.models.article_ai_filter import ArticleAiFilter

    raw_ids = arguments.get("article_ids") or []
    article_ids = list(dict.fromkeys([str(item).strip() for item in raw_ids if str(item).strip()]))
    if not article_ids:
        raise MCPError(-32602, "article_ids is required")

    session = _get_session()
    try:
        articles = session.query(Article).filter(Article.id.in_(article_ids)).all()
        article_map = {article.id: article for article in articles}
        ordered_articles = [article_map[article_id] for article_id in article_ids if article_id in article_map]
        if not ordered_articles:
            return {"items": [], "summary": {"hidden": 0, "keep": 0, "maybe": 0}}

        article_tags = session.query(ArticleTag).filter(ArticleTag.article_id.in_([a.id for a in ordered_articles])).all()
        tags_by_article: dict[str, list[str]] = {}
        all_tag_ids = set()
        for at in article_tags:
            tags_by_article.setdefault(at.article_id, []).append(at.tag_id)
            all_tag_ids.add(at.tag_id)

        tags_dict = {}
        if all_tag_ids:
            tags = session.query(TagsModel).filter(TagsModel.id.in_(list(all_tag_ids)), TagsModel.status == 1).all()
            tags_dict = {t.id: t for t in tags}

        mp_ids = list({a.mp_id for a in ordered_articles if a.mp_id})
        mp_info = {}
        if mp_ids:
            feeds = session.query(Feed).filter(Feed.id.in_(mp_ids)).all()
            mp_info = {feed.id: {"mp_name": feed.mp_name, "mp_cover": feed.mp_cover} for feed in feeds}

        engine = get_article_filter_engine()
        items: list[dict[str, Any]] = []
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
            items.append({
                "article_id": article.id,
                "title": article.title,
                "decision": result.decision,
                "category": result.category,
                "confidence": result.confidence,
                "reason": result.reason,
                "model_name": result.model_name,
                "mp_name": mp_name,
                "tags": tag_names,
            })

        session.commit()
        return {"items": items, "summary": summary}
    except Exception as exc:
        session.rollback()
        raise MCPError(-32603, "Internal error", str(exc))
    finally:
        session.close()


def _restore_articles_ai_filter(arguments: dict[str, Any]):
    from core.models.article_ai_filter import ArticleAiFilter

    raw_ids = arguments.get("article_ids") or []
    article_ids = list(dict.fromkeys([str(item).strip() for item in raw_ids if str(item).strip()]))
    if not article_ids:
        raise MCPError(-32602, "article_ids is required")

    session = _get_session()
    try:
        rows = session.query(ArticleAiFilter).filter(ArticleAiFilter.article_id.in_(article_ids)).all()
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
        return {"restored": len(rows)}
    except Exception as exc:
        session.rollback()
        raise MCPError(-32603, "Internal error", str(exc))
    finally:
        session.close()


def _list_tools():
    return [
        {
            "name": "articles.list",
            "description": "分页获取文章列表",
            "inputSchema": ArticlesListParams.model_json_schema(),
        },
        {
            "name": "articles.get",
            "description": "获取单篇文章详情",
            "inputSchema": ArticleGetParams.model_json_schema(),
        },
        {
            "name": "articles.toggle_status",
            "description": "切换文章启用/禁用状态",
            "inputSchema": ArticleStatusUpdateParams.model_json_schema(),
        },
        {
            "name": "articles.ai_filter",
            "description": "按文章 ID 执行 AI 过滤",
            "inputSchema": ArticleAiFilterParams.model_json_schema(),
        },
        {
            "name": "articles.ai_filter_restore",
            "description": "恢复 AI 过滤结果",
            "inputSchema": ArticleAiFilterRestoreParams.model_json_schema(),
        },
        {
            "name": "tags.list",
            "description": "分页获取标签列表",
            "inputSchema": TagsListParams.model_json_schema(),
        },
        {
            "name": "tags.get",
            "description": "获取单个标签详情",
            "inputSchema": TagGetParams.model_json_schema(),
        },
        {
            "name": "tags.toggle_status",
            "description": "切换标签启用/禁用状态",
            "inputSchema": TagStatusUpdateParams.model_json_schema(),
        },
        {
            "name": "tag_clusters.list",
            "description": "分页获取标签聚类列表",
            "inputSchema": TagClusterListParams.model_json_schema(),
        },
        {
            "name": "tag_clusters.get",
            "description": "获取标签聚类详情",
            "inputSchema": TagClusterGetParams.model_json_schema(),
        },
        {
            "name": "tag_clusters.visualization",
            "description": "获取标签聚类可视化数据",
            "inputSchema": TagClusterVizParams.model_json_schema(),
        },
        {
            "name": "tag_clusters.network",
            "description": "获取标签聚类网络图数据",
            "inputSchema": TagClusterNetworkParams.model_json_schema(),
        },
    ]


def _dispatch_tool(name: str, arguments: dict[str, Any]):
    if name == "articles.list":
        return _list_articles(arguments)
    if name == "articles.get":
        return _get_article(arguments["article_id"])
    if name == "articles.toggle_status":
        return _update_article_status(arguments["article_id"], int(arguments["status"]))
    if name == "articles.ai_filter":
        return _analyze_articles_ai_filter(arguments)
    if name == "articles.ai_filter_restore":
        return _restore_articles_ai_filter(arguments)
    if name == "tags.list":
        return _list_tags(arguments)
    if name == "tags.get":
        return _get_tag(arguments["tag_id"])
    if name == "tags.toggle_status":
        return _update_tag_status(arguments["tag_id"], int(arguments["status"]))
    if name == "tag_clusters.list":
        return _list_tag_clusters(arguments)
    if name == "tag_clusters.get":
        return _get_tag_cluster(arguments["cluster_id"])
    if name == "tag_clusters.visualization":
        return _get_tag_cluster_visualization(arguments)
    if name == "tag_clusters.network":
        return _get_tag_cluster_network(arguments)
    raise MCPError(-32601, f"Unknown tool: {name}")


@router.get("")
async def mcp_get(request: Request):
    _check_origin(request)
    return JSONResponse(status_code=405, content={"detail": "MCP streamable HTTP GET is not enabled"})


@router.post("")
async def mcp_post(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_mcp_token: Optional[str] = Header(None, alias="X-MCP-Token"),
):
    _check_origin(request)
    _check_auth(authorization, x_mcp_token)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        requests = _parse_request_body(payload)
        responses = []
        for item in requests:
            if not isinstance(item, dict):
                responses.append(_rpc_error(None, -32600, "Invalid Request"))
                continue

            jsonrpc = item.get("jsonrpc")
            method = item.get("method")
            request_id = item.get("id")
            params = item.get("params") or {}

            if jsonrpc != "2.0" or not method:
                if request_id is not None:
                    responses.append(_rpc_error(request_id, -32600, "Invalid Request"))
                continue

            if request_id is None:
                # notification
                if method in {"notifications/initialized"}:
                    continue
                # ignore unsupported notifications silently
                continue

            try:
                if method == "initialize":
                    protocol_version = params.get("protocolVersion") or MCP_PROTOCOL_VERSION
                    responses.append(_rpc_result(request_id, {
                        "protocolVersion": protocol_version,
                        "serverInfo": {
                            "name": MCP_SERVER_NAME,
                            "version": MCP_SERVER_VERSION,
                        },
                        "capabilities": {
                            "tools": {"listChanged": False},
                            "resources": {"listChanged": False},
                            "prompts": {"listChanged": False},
                        },
                    }))
                elif method == "tools/list":
                    responses.append(_rpc_result(request_id, {"tools": _list_tools()}))
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments") or {}
                    if not tool_name:
                        raise MCPError(-32602, "Missing tool name")
                    result = _dispatch_tool(tool_name, arguments)
                    if inspect.isawaitable(result):
                        result = await result
                    responses.append(_rpc_result(request_id, _success_content(result)))
                elif method == "resources/list":
                    responses.append(_rpc_result(request_id, {"resources": []}))
                elif method == "prompts/list":
                    responses.append(_rpc_result(request_id, {"prompts": []}))
                elif method == "ping":
                    responses.append(_rpc_result(request_id, {}))
                else:
                    raise MCPError(-32601, f"Method not found: {method}")
            except MCPError as exc:
                responses.append(_rpc_error(request_id, exc.code, exc.message, exc.data))
            except Exception as exc:
                print_warning(f"MCP method error in {method}: {exc}")
                responses.append(_rpc_error(request_id, -32603, "Internal error", str(exc)))

        if not responses:
            return Response(status_code=204)
        if len(responses) == 1:
            return JSONResponse(content=responses[0])
        return JSONResponse(content=responses)
    except HTTPException:
        raise
    except Exception as exc:
        print_warning(f"MCP request failed: {exc}")
        return JSONResponse(
            status_code=500,
            content=_rpc_error(None, -32603, "Internal error", str(exc)),
        )
