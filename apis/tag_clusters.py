from collections import defaultdict
from itertools import combinations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.auth import get_current_user
from core.database import get_db
from core.models.article_tags import ArticleTag
from core.models.tag_cluster_aliases import TagClusterAlias
from core.models.tag_cluster_members import TagClusterMember
from core.models.tag_clusters import TagCluster
from core.models.tag_similarities import TagSimilarity
from core.models.tags import Tags as TagsModel
from core.tag_cluster import rebuild_tag_clusters
from core.visualization import compute_2d_layout, normalize_coordinates, compute_cluster_overview
from .base import success_response, error_response

router = APIRouter(prefix="/tag-clusters", tags=["标签聚类"])


def _resolve_cluster(db: Session, cluster_identifier: str, max_depth: int = 8):
    current_id = cluster_identifier
    visited: set[str] = set()

    for _ in range(max_depth):
        cluster = db.query(TagCluster).filter(TagCluster.id == current_id).first()
        if cluster:
            return cluster

        centroid_cluster = db.query(TagCluster).filter(TagCluster.centroid_tag_id == current_id).first()
        if centroid_cluster:
            return centroid_cluster

        member_cluster = (
            db.query(TagCluster)
            .join(TagClusterMember, TagClusterMember.cluster_id == TagCluster.id)
            .filter(TagClusterMember.tag_id == current_id)
            .order_by(TagCluster.updated_at.desc())
            .first()
        )
        if member_cluster:
            return member_cluster

        if current_id in visited:
            break
        visited.add(current_id)

        alias = (
            db.query(TagClusterAlias)
            .filter(TagClusterAlias.alias_cluster_id == current_id)
            .order_by(TagClusterAlias.created_at.desc())
            .first()
        )
        if not alias:
            break
        current_id = alias.cluster_id

    return None


def _build_merge_suggestions(
    db: Session,
    centroid_tag_id: Optional[str],
    cluster_member_ids: Optional[set[str]] = None,
):
    if not centroid_tag_id:
        return []
    cluster_member_ids = cluster_member_ids or set()
    centroid_tag = db.query(TagsModel).filter(TagsModel.id == centroid_tag_id).first()
    source_tag_name = centroid_tag.name if centroid_tag and centroid_tag.name else centroid_tag_id
    rows = (
        db.query(TagSimilarity, TagsModel)
        .join(TagsModel, TagsModel.id == TagSimilarity.similar_tag_id)
        .filter(TagSimilarity.tag_id == centroid_tag_id)
        .order_by(TagSimilarity.score.desc())
        .limit(10)
        .all()
    )
    suggestions = []
    for row, tag in rows:
        if row.score < 7500:
            continue
        if row.similar_tag_id in cluster_member_ids:
            continue
        suggestions.append({
            "source_tag_id": row.tag_id,
            "source_tag_name": source_tag_name,
            "target_tag_id": row.similar_tag_id,
            "target_tag_name": tag.name,
            "score": row.score,
            "reason": "与中心标签字面或语义高度相近，疑似同一实体的别名或变体，可考虑标准化合并",
        })
    return suggestions


def _get_tag_cluster_payload(db: Session, cluster_id: str):
    cluster = _resolve_cluster(db, cluster_id)
    if not cluster:
        return None

    member_rows = (
        db.query(TagClusterMember, TagsModel)
        .join(TagsModel, TagsModel.id == TagClusterMember.tag_id)
        .filter(TagClusterMember.cluster_id == cluster.id)
        .order_by(TagClusterMember.member_score.desc())
        .all()
    )
    members = [
        {
            "tag_id": member.tag_id,
            "tag_name": tag.name,
            "member_score": member.member_score,
        }
        for member, tag in member_rows
    ]
    member_tag_ids = {member["tag_id"] for member in members}
    centroid_tag_name = next(
        (member["tag_name"] for member in members if member["tag_id"] == cluster.centroid_tag_id),
        None,
    )
    merge_suggestions = _build_merge_suggestions(db, cluster.centroid_tag_id, member_tag_ids)
    return {
        "id": cluster.id,
        "name": cluster.name,
        "description": cluster.description,
        "centroid_tag_id": cluster.centroid_tag_id,
        "centroid_tag_name": centroid_tag_name,
        "size": cluster.size,
        "cluster_version": cluster.cluster_version,
        "members": members,
        "merge_suggestions": merge_suggestions,
        "updated_at": cluster.updated_at.isoformat() if cluster.updated_at else None,
    }


@router.get("")
async def list_tag_clusters(
    offset: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    total = db.query(TagCluster).count()
    rows = (
        db.query(TagCluster)
        .order_by(TagCluster.size.desc(), TagCluster.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    data = [
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
    return success_response(data={
        "list": data,
        "page": {
            "offset": offset,
            "limit": limit,
            "total": total,
        },
    })


@router.get("/similar/{tag_id}")
async def get_similar_tags(
    tag_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    rows = (
        db.query(TagSimilarity, TagsModel)
        .join(TagsModel, TagsModel.id == TagSimilarity.similar_tag_id)
        .filter(TagSimilarity.tag_id == tag_id)
        .order_by(TagSimilarity.score.desc())
        .limit(limit)
        .all()
    )
    data = [
        {
            "tag_id": row.tag_id,
            "similar_tag_id": row.similar_tag_id,
            "similar_tag_name": tag.name,
            "score": row.score,
            "embedding_score": row.embedding_score,
            "cooccurrence_score": row.cooccurrence_score,
            "lexical_score": row.lexical_score,
        }
        for row, tag in rows
    ]
    return success_response(data=data)


@router.get("/{cluster_id}")
async def get_tag_cluster_detail(
    cluster_id: str,
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    payload = _get_tag_cluster_payload(db, cluster_id)
    if not payload:
        return error_response(404, "Tag cluster not found")
    return success_response(data=payload)


@router.get("/{cluster_id}/export")
async def export_tag_cluster(
    cluster_id: str,
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    payload = _get_tag_cluster_payload(db, cluster_id)
    if not payload:
        return error_response(404, "Tag cluster not found")
    return JSONResponse(content={
        "code": 0,
        "message": "success",
        "data": payload,
    })


@router.post("/rebuild")
async def rebuild_clusters(
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    try:
        result = rebuild_tag_clusters(db)
        return success_response(data=result, message="标签聚类重建完成")
    except ValueError as e:
        # 处理embedding provider配置错误
        error_msg = str(e)
        if "API_KEY 未配置" in error_msg or "未配置" in error_msg:
            return error_response(400, f"Embedding API密钥未配置，无法重建标签聚类。"
                            f"请在环境变量中配置 {error_msg.split()[0]}，"
                            f"或者在.env文件中设置相应的API密钥。")
        return error_response(500, f"重建聚类失败: {error_msg}")
    except Exception as e:
        return error_response(500, f"重建聚类失败: {str(e)}")


@router.get("/overview/visualization")
async def get_clusters_overview(
    method: str = Query('pca', description="降维方法: pca, tsne, umap"),
    limit: int = Query(10, ge=1, le=50, description="包含的聚类数量"),
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    """
    获取多个聚类的概览可视化

    用于在全局视图中展示所有聚类的关系。
    """
    try:
        # 获取最大的几个聚类
        clusters = (
            db.query(TagCluster)
            .order_by(TagCluster.size.desc())
            .limit(limit)
            .all()
        )

        if not clusters:
            return success_response(data={
                "nodes": [],
                "edges": [],
                "metadata": {
                    "method": method,
                    "cluster_count": 0,
                    "node_count": 0,
                    "edge_count": 0
                }
            })

        cluster_ids = [cluster.id for cluster in clusters]

        # 计算概览可视化
        overview_data = compute_cluster_overview(
            cluster_ids=cluster_ids,
            db=db,
            method=method
        )

        # 添加聚类名称到元数据
        overview_data["metadata"]["clusters"] = [
            {
                "id": cluster.id,
                "name": cluster.name,
                "size": cluster.size,
                "centroid_tag_id": cluster.centroid_tag_id
            }
            for cluster in clusters
        ]

        return success_response(data=overview_data)

    except Exception as e:
        return error_response(500, f"生成概览可视化失败: {str(e)}")


@router.get("/{cluster_id}/visualization")
async def get_cluster_visualization(
    cluster_id: str,
    method: str = Query('pca', description="降维方法: pca, tsne, umap"),
    include_edges: bool = Query(True, description="是否包含边信息"),
    min_edge_weight: float = Query(0.5, ge=0.0, le=1.0, description="最小边权重阈值"),
    normalize: bool = Query(True, description="是否归一化坐标"),
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    """
    获取聚类的2D可视化数据

    返回降维后的节点坐标和可选的边信息，用于前端渲染散点图或网络图。
    支持多种降维方法：
    - pca: 主成分分析，快速稳定
    - tsne: t-SNE，高质量但较慢
    - umap: UMAP，平衡性能和质量
    """
    try:
        # 验证聚类是否存在
        cluster = _resolve_cluster(db, cluster_id)
        if not cluster:
            return error_response(404, "聚类不存在")

        # 计算可视化布局
        layout_data = compute_2d_layout(
            cluster_id=cluster.id,
            db=db,
            method=method,
            include_edges=include_edges,
            min_edge_weight=min_edge_weight
        )

        # 归一化坐标（可选）
        if normalize and layout_data.get("nodes"):
            layout_data["nodes"] = normalize_coordinates(layout_data["nodes"])

        # 添加聚类元数据
        layout_data["metadata"]["cluster_name"] = cluster.name
        layout_data["metadata"]["cluster_description"] = cluster.description
        layout_data["metadata"]["centroid_tag_id"] = cluster.centroid_tag_id
        layout_data["metadata"]["cluster_size"] = cluster.size

        return success_response(data=layout_data)

    except ValueError as e:
        return error_response(400, f"不支持的降维方法: {str(e)}")
    except ImportError as e:
        return error_response(500, f"缺少必要的依赖库: {str(e)}")
    except Exception as e:
        return error_response(500, f"生成可视化数据失败: {str(e)}")


@router.get("/{cluster_id}/network")
async def get_cluster_network(
    cluster_id: str,
    min_similarity: float = Query(0.3, ge=0.0, le=1.0, description="最小共现强度阈值"),
    layout_type: str = Query('force', description="布局类型: force, circular, hierarchical"),
    max_nodes: int = Query(100, ge=10, le=500, description="最大节点数量"),
    db: Session = Depends(get_db),
    cur_user: dict = Depends(get_current_user),
):
    """
    获取聚类的网络图数据。

    这里的边只表示“文章共现关系”，不表示“语义相似”。
    聚类负责标准化同一实体；网络负责展示实体在文章中的共同出现。
    """
    try:
        # 验证聚类是否存在
        cluster = _resolve_cluster(db, cluster_id)
        if not cluster:
            return error_response(404, "聚类不存在")

        # 获取聚类成员（限制数量以避免前端性能问题）
        member_rows = (
            db.query(TagClusterMember, TagsModel)
            .join(TagsModel, TagsModel.id == TagClusterMember.tag_id)
            .filter(TagClusterMember.cluster_id == cluster.id)
            .order_by(TagClusterMember.member_score.desc())
            .limit(max_nodes)
            .all()
        )

        if not member_rows:
            return success_response(data={
                "nodes": [],
                "edges": [],
                "metadata": {
                    "cluster_id": cluster.id,
                    "layout_type": layout_type,
                    "node_count": 0,
                    "edge_count": 0
                }
            })

        # 创建节点数据
        nodes = []
        tag_ids = []
        article_count_by_tag = defaultdict(int)
        for member, tag in member_rows:
            tag_ids.append(member.tag_id)
            nodes.append({
                "id": member.tag_id,
                "name": tag.name or member.tag_id,
                "score": member.member_score / 10000.0,  # 归一化到0-1
                "cluster": cluster.id,
                "size": max(5, min(20, 5 + (member.member_score / 10000.0) * 15))  # 节点大小5-20
            })

        # 仅根据文章共现生成边，而不是语义相似度。
        article_rows = (
            db.query(ArticleTag.article_id, ArticleTag.tag_id)
            .filter(ArticleTag.tag_id.in_(tag_ids))
            .all()
        )

        article_to_tags: dict[str, set[str]] = defaultdict(set)
        for article_id, tag_id in article_rows:
            if article_id and tag_id:
                article_to_tags[article_id].add(tag_id)
                article_count_by_tag[tag_id] += 1

        pair_counts: dict[tuple[str, str], int] = defaultdict(int)
        for article_tag_ids in article_to_tags.values():
            related_tags = sorted(article_tag_ids)
            if len(related_tags) < 2:
                continue
            for source_id, target_id in combinations(related_tags, 2):
                pair_counts[(source_id, target_id)] += 1

        edges = []
        for (source_id, target_id), pair_count in pair_counts.items():
            source_articles = article_count_by_tag.get(source_id, 0)
            target_articles = article_count_by_tag.get(target_id, 0)
            denominator = min(source_articles, target_articles)
            if denominator <= 0:
                continue

            # 共现强度：共同出现次数 / 两者较小文章数
            weight = pair_count / denominator
            if weight >= min_similarity:
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "weight": float(weight),
                    "cooccurrence_score": float(weight),
                    "cooccurrence_count": pair_count,
                    "source_article_count": source_articles,
                    "target_article_count": target_articles
                })

        return success_response(data={
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "cluster_id": cluster.id,
                "cluster_name": cluster.name,
                "layout_type": layout_type,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "min_similarity": min_similarity,
                "min_cooccurrence_strength": min_similarity,
                "relation_source": "article_cooccurrence"
            }
        })

    except Exception as e:
        return error_response(500, f"生成网络图数据失败: {str(e)}")
