"""
Embedding聚类可视化模块
提供降维算法和2D布局计算功能
"""

import os
from typing import Any, Dict, List, Tuple
import numpy as np
from sqlalchemy.orm import Session

from core.models.tag_cluster_members import TagClusterMember
from core.models.tag_embeddings import TagEmbedding
from core.models.tags import Tags as TagsModel


def _get_int(name: str, default: int) -> int:
    """获取整数环境变量"""
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    """获取浮点数环境变量"""
    try:
        return float(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def reduce_dimensions(
    vectors: List[List[float]],
    method: str = 'pca',
    n_components: int = 2,
    **kwargs
) -> List[List[float]]:
    """
    对高维向量进行降维

    Args:
        vectors: 高维向量列表
        method: 降维方法 ('pca', 'tsne', 'umap')
        n_components: 降维后的维度 (默认为2)
        **kwargs: 其他参数传递给降维算法

    Returns:
        降维后的向量列表
    """
    if not vectors or len(vectors) == 0:
        return []

    # 转换为numpy数组
    vectors_array = np.array(vectors)

    # 处理维度不足的情况
    if vectors_array.shape[1] <= n_components:
        # 如果原始维度小于等于目标维度，直接填充0
        result = vectors_array.copy()
        while result.shape[1] < n_components:
            result = np.hstack([result, np.zeros((result.shape[0], 1))])
        return result.tolist()

    # 根据方法选择降维算法
    if method == 'pca':
        return _pca_reduce(vectors_array, n_components, **kwargs)
    elif method == 'tsne':
        return _tsne_reduce(vectors_array, n_components, **kwargs)
    elif method == 'umap':
        return _umap_reduce(vectors_array, n_components, **kwargs)
    else:
        raise ValueError(f"Unsupported dimensionality reduction method: {method}")


def _pca_reduce(
    vectors: np.ndarray,
    n_components: int,
    random_state: int = 42,
    **kwargs
) -> List[List[float]]:
    """
    使用PCA进行降维

    PCA特点：
    - 速度快，适合大数据集
    - 保持全局结构
    - 线性变换，结果可重现
    """
    try:
        from sklearn.decomposition import PCA
    except ImportError:
        raise ImportError("scikit-learn is required for PCA reduction. Please install it: pip install scikit-learn")

    pca = PCA(
        n_components=n_components,
        random_state=random_state
    )
    reduced = pca.fit_transform(vectors)
    return reduced.tolist()


def _tsne_reduce(
    vectors: np.ndarray,
    n_components: int = 2,
    perplexity: int = 30,
    n_iter: int = 1000,
    random_state: int = 42,
    **kwargs
) -> List[List[float]]:
    """
    使用t-SNE进行降维

    t-SNE特点：
    - 高质量可视化效果
    - 保持局部结构
    - 计算速度较慢
    - 结果可能不完全可重现
    """
    try:
        from sklearn.manifold import TSNE
    except ImportError:
        raise ImportError("scikit-learn is required for t-SNE reduction. Please install it: pip install scikit-learn")

    # 对于大数据集，减少迭代次数以提高速度
    n_samples = vectors.shape[0]
    if n_samples > 1000:
        n_iter = min(n_iter, 500)
        perplexity = min(perplexity, n_samples // 4)

    tsne = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        n_iter=n_iter,
        random_state=random_state,
        method='barnes_hut' if n_components == 2 else 'exact'
    )
    reduced = tsne.fit_transform(vectors)
    return reduced.tolist()


def _umap_reduce(
    vectors: np.ndarray,
    n_components: int = 2,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    random_state: int = 42,
    **kwargs
) -> List[List[float]]:
    """
    使用UMAP进行降维

    UMAP特点：
    - 平衡性能和质量
    - 保持局部和全局结构
    - 速度较快
    - 结果相对稳定
    """
    try:
        import umap
    except ImportError:
        raise ImportError("umap-learn is required for UMAP reduction. Please install it: pip install umap-learn")

    # 根据数据规模调整参数
    n_samples = vectors.shape[0]
    if n_samples > 1000:
        n_neighbors = min(n_neighbors, n_samples // 10)

    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state,
        transform_seed=random_state
    )
    reduced = reducer.fit_transform(vectors)
    return reduced.tolist()


def compute_2d_layout(
    cluster_id: str,
    db: Session,
    method: str = 'pca',
    include_edges: bool = True,
    min_edge_weight: float = 0.5
) -> Dict[str, Any]:
    """
    计算聚类的2D可视化布局

    Args:
        cluster_id: 聚类ID
        db: 数据库会话
        method: 降维方法 ('pca', 'tsne', 'umap')
        include_edges: 是否包含边信息
        min_edge_weight: 最小边权重阈值

    Returns:
        包含节点和边的可视化数据字典
    """
    # 获取聚类成员
    member_rows = (
        db.query(TagClusterMember, TagsModel)
        .join(TagsModel, TagsModel.id == TagClusterMember.tag_id)
        .filter(TagClusterMember.cluster_id == cluster_id)
        .all()
    )

    if not member_rows:
        return {
            "nodes": [],
            "edges": [],
            "metadata": {
                "cluster_id": cluster_id,
                "method": method,
                "node_count": 0,
                "edge_count": 0
            }
        }

    # 获取标签ID和名称
    tag_ids = []
    tag_names = {}
    for member, tag in member_rows:
        tag_ids.append(member.tag_id)
        tag_names[member.tag_id] = tag.name or member.tag_id

    # 获取embedding向量
    embedding_rows = (
        db.query(TagEmbedding)
        .filter(TagEmbedding.tag_id.in_(tag_ids))
        .all()
    )

    if not embedding_rows:
        # 如果没有embedding数据，使用随机布局
        nodes = [
            {
                "id": tag_id,
                "name": tag_names.get(tag_id, tag_id),
                "x": np.random.randn(),
                "y": np.random.randn(),
                "cluster": cluster_id
            }
            for tag_id in tag_ids
        ]
        return {
            "nodes": nodes,
            "edges": [],
            "metadata": {
                "cluster_id": cluster_id,
                "method": method,
                "node_count": len(nodes),
                "edge_count": 0,
                "warning": "No embedding data found, using random layout"
            }
        }

    # 提取向量数据（按tag_ids顺序）
    vector_map = {row.tag_id: row.vector for row in embedding_rows}
    vectors = []
    valid_tag_ids = []
    for tag_id in tag_ids:
        if tag_id in vector_map and vector_map[tag_id]:
            vectors.append(vector_map[tag_id])
            valid_tag_ids.append(tag_id)

    if not vectors:
        return {
            "nodes": [],
            "edges": [],
            "metadata": {
                "cluster_id": cluster_id,
                "method": method,
                "node_count": 0,
                "edge_count": 0,
                "warning": "No valid embedding vectors found"
            }
        }

    # 应用降维算法
    try:
        reduced_coords = reduce_dimensions(vectors, method=method, n_components=2)
    except Exception as e:
        # 如果降维失败，使用PCA作为后备
        if method != 'pca':
            reduced_coords = reduce_dimensions(vectors, method='pca', n_components=2)
        else:
            # 如果PCA也失败，使用随机坐标
            reduced_coords = [[np.random.randn(), np.random.randn()] for _ in range(len(vectors))]

    # 创建节点数据
    nodes = []
    for i, tag_id in enumerate(valid_tag_ids):
        if i < len(reduced_coords):
            nodes.append({
                "id": tag_id,
                "name": tag_names.get(tag_id, tag_id),
                "x": float(reduced_coords[i][0]),
                "y": float(reduced_coords[i][1]),
                "cluster": cluster_id
            })

    # 创建边数据（基于共现关系）
    edges = []
    if include_edges:
        # 从相似度数据获取边信息
        try:
            from core.models.tag_similarities import TagSimilarity

            # 获取聚类内标签的相似度关系
            similarity_rows = (
                db.query(TagSimilarity)
                .filter(
                    TagSimilarity.tag_id.in_(valid_tag_ids),
                    TagSimilarity.similar_tag_id.in_(valid_tag_ids)
                )
                .all()
            )

            for row in similarity_rows:
                # 将得分转换为0-1范围
                weight = row.score / 10000.0 if row.score else 0
                if weight >= min_edge_weight:
                    edges.append({
                        "source": row.tag_id,
                        "target": row.similar_tag_id,
                        "weight": float(weight),
                        "embedding_score": float(row.embedding_score / 10000.0) if row.embedding_score else 0,
                        "cooccurrence_score": float(row.cooccurrence_score / 10000.0) if row.cooccurrence_score else 0,
                        "lexical_score": float(row.lexical_score / 10000.0) if row.lexical_score else 0
                    })
        except Exception:
            # 如果相似度表不存在或查询失败，忽略边数据
            pass

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "cluster_id": cluster_id,
            "method": method,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "dimensions": len(vectors[0]) if vectors else 0
        }
    }


def normalize_coordinates(
    nodes: List[Dict[str, Any]],
    padding: float = 0.1
) -> List[Dict[str, Any]]:
    """
    归一化节点坐标到指定范围

    Args:
        nodes: 节点列表，每个节点包含x和y坐标
        padding: 边距比例

    Returns:
        坐标归一化后的节点列表
    """
    if not nodes:
        return nodes

    # 提取x和y坐标
    x_coords = [node.get('x', 0) for node in nodes]
    y_coords = [node.get('y', 0) for node in nodes]

    if not x_coords or not y_coords:
        return nodes

    # 计算最小最大值
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)

    # 避免除零
    x_range = x_max - x_min if x_max != x_min else 1.0
    y_range = y_max - y_min if y_max != y_min else 1.0

    # 归一化到[padding, 1-padding]范围
    normalized_nodes = []
    for node in nodes:
        normalized_node = node.copy()
        if 'x' in node:
            normalized_node['x'] = padding + (node['x'] - x_min) / x_range * (1 - 2 * padding)
        if 'y' in node:
            normalized_node['y'] = padding + (node['y'] - y_min) / y_range * (1 - 2 * padding)
        normalized_nodes.append(normalized_node)

    return normalized_nodes


def compute_cluster_overview(
    cluster_ids: List[str],
    db: Session,
    method: str = 'pca'
) -> Dict[str, Any]:
    """
    计算多个聚类的概览可视化

    Args:
        cluster_ids: 聚类ID列表
        db: 数据库会话
        method: 降维方法

    Returns:
        包含所有聚类节点的可视化数据
    """
    all_nodes = []
    all_edges = []

    for cluster_id in cluster_ids:
        try:
            layout_data = compute_2d_layout(
                cluster_id=cluster_id,
                db=db,
                method=method,
                include_edges=False,  # 概览不包含边，避免过于复杂
                min_edge_weight=0.7
            )
            all_nodes.extend(layout_data.get("nodes", []))
            all_edges.extend(layout_data.get("edges", []))
        except Exception:
            # 如果某个聚类处理失败，继续处理其他聚类
            continue

    # 如果有多个聚类的节点，重新进行全局降维以获得更好的布局
    if len(cluster_ids) > 1 and all_nodes:
        # 提取所有节点的原始向量
        tag_ids = [node["id"] for node in all_nodes]
        embedding_rows = (
            db.query(TagEmbedding)
            .filter(TagEmbedding.tag_id.in_(tag_ids))
            .all()
        )

        if embedding_rows:
            vector_map = {row.tag_id: row.vector for row in embedding_rows}
            vectors = []
            valid_nodes = []

            for node in all_nodes:
                if node["id"] in vector_map and vector_map[node["id"]]:
                    vectors.append(vector_map[node["id"]])
                    valid_nodes.append(node)

            if vectors:
                try:
                    reduced_coords = reduce_dimensions(vectors, method=method, n_components=2)
                    for i, node in enumerate(valid_nodes):
                        if i < len(reduced_coords):
                            node["x"] = float(reduced_coords[i][0])
                            node["y"] = float(reduced_coords[i][1])
                except Exception:
                    # 如果降维失败，保持原有坐标
                    pass

    return {
        "nodes": all_nodes,
        "edges": all_edges,
        "metadata": {
            "method": method,
            "cluster_count": len(cluster_ids),
            "node_count": len(all_nodes),
            "edge_count": len(all_edges)
        }
    }