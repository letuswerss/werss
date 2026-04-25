import hashlib
import math
import os
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from core.embedding import get_embedding_provider
from core.models.tag_cluster_aliases import TagClusterAlias
from core.models.tag_cluster_members import TagClusterMember
from core.models.tag_clusters import TagCluster
from core.models.tag_embeddings import TagEmbedding
from core.models.tag_similarities import TagSimilarity
from core.models.tags import Tags
from core.log import logger

PUNCTUATION_TO_REMOVE = " ·-_/()（）[]【】,，.。:："


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean_name(name: str) -> str:
    cleaned = (name or "").strip().lower()
    for char in PUNCTUATION_TO_REMOVE:
        cleaned = cleaned.replace(char, "")
    return cleaned


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _build_char_ngram_vector(text: str, min_n: int = 2, max_n: int = 4) -> Dict[str, float]:
    cleaned = _clean_name(text)
    if not cleaned:
        return {}

    grams: Dict[str, float] = defaultdict(float)
    for n in range(min_n, max_n + 1):
        if len(cleaned) < n:
            continue
        for idx in range(len(cleaned) - n + 1):
            grams[cleaned[idx: idx + n]] += 1.0

    if not grams:
        grams[cleaned] = 1.0
    return dict(grams)


def _sparse_cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    if not v1 or not v2:
        return 0.0

    common_keys = set(v1.keys()) & set(v2.keys())
    if not common_keys:
        return 0.0

    dot = sum(v1[key] * v2[key] for key in common_keys)
    norm1 = math.sqrt(sum(value * value for value in v1.values()))
    norm2 = math.sqrt(sum(value * value for value in v2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _combined_similarity(
    embedding_score: float,
    ngram_score: float,
    embedding_weight: float,
    ngram_weight: float,
) -> float:
    total_weight = embedding_weight + ngram_weight
    if total_weight <= 0:
        return 0.0
    return (embedding_score * embedding_weight + ngram_score * ngram_weight) / total_weight


def _score_to_int(value: float) -> int:
    return max(0, min(10000, int(round(value * 10000))))


def _build_cluster_aliases(
    db: Session,
    old_members: dict[str, set[str]],
    new_members: dict[str, set[str]],
    version: str,
) -> int:
    if not old_members or not new_members:
        return 0

    alias_rows = 0
    now = datetime.now()
    for old_cluster_id, old_tag_ids in old_members.items():
        if not old_tag_ids:
            continue

        best_cluster_id = None
        best_overlap = 0
        best_score = 0.0

        for new_cluster_id, new_tag_ids in new_members.items():
            if not new_tag_ids:
                continue

            overlap = len(old_tag_ids & new_tag_ids)
            if overlap <= 0:
                continue

            score = overlap / max(len(old_tag_ids), 1)
            if score > best_score:
                best_cluster_id = new_cluster_id
                best_overlap = overlap
                best_score = score

        if not best_cluster_id:
            continue

        db.add(
            TagClusterAlias(
                id=str(uuid.uuid4()),
                alias_cluster_id=old_cluster_id,
                cluster_id=best_cluster_id,
                overlap_score=_score_to_int(best_score),
                cluster_version=version,
                created_at=now,
            )
        )
        alias_rows += 1

    return alias_rows


def build_tag_embeddings_for_names(db: Session, tags: List[Tags]) -> Dict[str, TagEmbedding]:
    """
    仅对标签名称本身进行 Embedding 向量化，抛弃文章上下文。
    这才是真正的 Semantic Similarity。
    """
    if not tags:
        return {}

    provider = get_embedding_provider()
    now = datetime.now()

    # 获取已有的 Embeddings
    tag_ids = [t.id for t in tags]
    existing_rows = db.query(TagEmbedding).filter(TagEmbedding.tag_id.in_(tag_ids)).all()
    existing_map = {
        row.tag_id: row
        for row in existing_rows
        if row.embedding_provider == provider.provider_name
        and row.embedding_model == provider.model_name
        and row.embedding_dimensions == provider.dimensions
    }

    result_map: Dict[str, TagEmbedding] = {}
    pending: List[Tuple[str, str, str]] = [] # tag_id, tag_name, text_hash
    
    for tag in tags:
        if not tag.name:
            continue
        text_hash = _text_hash(tag.name)
        existing = existing_map.get(tag.id)
        
        # 借用 profile_hash 字段存储 tag.name 的 hash
        if existing and existing.profile_hash == text_hash:
            result_map[tag.id] = existing
        else:
            pending.append((tag.id, tag.name, text_hash))

    batch_size = _get_int("TAG_CLUSTER_REBUILD_BATCH_SIZE", 100)
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset: offset + batch_size]
        vectors = provider.embed_texts([item[1] for item in batch])
        if len(vectors) != len(batch):
            raise ValueError(f"embedding 返回数量异常: expected={len(batch)}, actual={len(vectors)}")
            
        for (tag_id, tag_name, text_hash), vector in zip(batch, vectors):
            existing = existing_map.get(tag_id)
            if existing:
                existing.profile_hash = text_hash
                existing.vector = vector
                existing.updated_at = now
                result_map[tag_id] = existing
            else:
                row = TagEmbedding(
                    id=str(uuid.uuid4()),
                    tag_id=tag_id,
                    embedding_provider=provider.provider_name,
                    embedding_model=provider.model_name,
                    embedding_dimensions=provider.dimensions,
                    profile_hash=text_hash,
                    vector=vector,
                    updated_at=now,
                )
                db.add(row)
                result_map[tag_id] = row

    db.commit()
    return result_map


def rebuild_tag_clusters(db: Session) -> Dict[str, Any]:
    """
    基于标签名相似图的标准化聚类逻辑。
    仅使用标签名本身的 embedding 相似度与字符 n-gram 相似度建图，
    再用 top-k 稀疏化后的连通分量生成标准化簇。
    """
    # 提取所有有效的标签
    tags = db.query(Tags).filter(Tags.name.isnot(None), Tags.name != "").all()
    if not tags:
        return {
            "tag_count": 0,
            "cluster_count": 0,
            "similarity_count": 0,
            "message": "没有满足条件的标签",
        }

    tag_ids = [t.id for t in tags]
    tag_names = {t.id: t.name for t in tags}

    old_cluster_rows = db.query(TagCluster).all()
    old_member_rows = db.query(TagClusterMember).all()
    old_members: dict[str, set[str]] = defaultdict(set)
    for row in old_member_rows:
        if row.cluster_id and row.tag_id:
            old_members[row.cluster_id].add(row.tag_id)

    # 1. 向量化标签名称
    provider = get_embedding_provider()
    embedding_rows = build_tag_embeddings_for_names(db, tags)
    vectors = {tag_id: (embedding_rows[tag_id].vector if tag_id in embedding_rows else []) for tag_id in tag_ids}
    ngram_vectors = {tag_id: _build_char_ngram_vector(tag_names[tag_id]) for tag_id in tag_ids}

    max_similar_tags = _get_int("TAG_CLUSTER_MAX_SIMILAR_TAGS", 10)
    top_k = _get_int("TAG_CLUSTER_GRAPH_TOP_K", 8)
    threshold = _get_float("TAG_CLUSTER_SIMILARITY_THRESHOLD", 0.78)
    embedding_weight = _get_float("TAG_CLUSTER_EMBEDDING_WEIGHT", 0.6)
    ngram_weight = _get_float("TAG_CLUSTER_NGRAM_WEIGHT", 0.4)
    version = datetime.now().strftime("%Y%m%d%H%M%S")

    similarities_by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pair_candidates: list[dict[str, Any]] = []

    logger.info(f"开始计算 {len(tag_ids)} 个标签的标准化相似图...")

    for i, tag_id in enumerate(tag_ids):
        for j in range(i + 1, len(tag_ids)):
            other_id = tag_ids[j]
            semantic_score = _cosine_similarity(vectors.get(tag_id, []), vectors.get(other_id, []))
            ngram_score = _sparse_cosine_similarity(ngram_vectors.get(tag_id, {}), ngram_vectors.get(other_id, {}))
            final_score = _combined_similarity(
                semantic_score,
                ngram_score,
                embedding_weight=embedding_weight,
                ngram_weight=ngram_weight,
            )
            if final_score < threshold:
                continue

            pair_candidates.append({
                "source_id": tag_id,
                "target_id": other_id,
                "score": final_score,
                "embedding_score": semantic_score,
                "cooccurrence_score": 0,
                "lexical_score": ngram_score,
            })

    # 图稀疏化：每个节点只保留 top-k 高权边
    candidate_map_by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pair_candidates:
        candidate_map_by_tag[pair["source_id"]].append(pair)
        candidate_map_by_tag[pair["target_id"]].append(pair)

    selected_edges: dict[tuple[str, str], dict[str, Any]] = {}
    for tag_id, items in candidate_map_by_tag.items():
        items.sort(key=lambda item: item["score"], reverse=True)
        for item in items[:top_k]:
            source_id, target_id = sorted((item["source_id"], item["target_id"]))
            selected_edges[(source_id, target_id)] = item

    for item in selected_edges.values():
        tag_id = item["source_id"]
        other_id = item["target_id"]
        similarities_by_tag[tag_id].append({
            "tag_id": tag_id,
            "similar_tag_id": other_id,
            "score": item["score"],
            "embedding_score": item["embedding_score"],
            "cooccurrence_score": item["cooccurrence_score"],
            "lexical_score": item["lexical_score"],
        })
        similarities_by_tag[other_id].append({
            "tag_id": other_id,
            "similar_tag_id": tag_id,
            "score": item["score"],
            "embedding_score": item["embedding_score"],
            "cooccurrence_score": item["cooccurrence_score"],
            "lexical_score": item["lexical_score"],
        })

    # 清空旧数据
    db.query(TagSimilarity).delete()
    db.query(TagClusterMember).delete()
    db.query(TagCluster).delete()
    db.commit()

    similarity_rows = 0
    for tag_id, items in similarities_by_tag.items():
        items.sort(key=lambda item: item["score"], reverse=True)
        for item in items[: min(max_similar_tags, top_k)]:
            db.add(
                TagSimilarity(
                    id=str(uuid.uuid4()),
                    tag_id=item["tag_id"],
                    similar_tag_id=item["similar_tag_id"],
                    score=_score_to_int(item["score"]),
                    embedding_score=_score_to_int(item["embedding_score"]),
                    cooccurrence_score=0,
                    lexical_score=_score_to_int(item["lexical_score"]),
                    cluster_version=version,
                    updated_at=datetime.now(),
                )
            )
            similarity_rows += 1

    adjacency: dict[str, set[str]] = {tag_id: set() for tag_id in tag_ids}
    for tag_id, items in similarities_by_tag.items():
        for item in items:
            adjacency[tag_id].add(item["similar_tag_id"])

    visited: set[str] = set()
    cluster_count = 0
    for tag_id in tag_ids:
        if tag_id in visited:
            continue
        stack = [tag_id]
        component = []
        visited.add(tag_id)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)

        # 既然是归一化，如果一个词没有同义词（孤立节点），就没必要建一个单成员的 Cluster
        if not component or len(component) < 2:
            continue

        component_scores: dict[str, float] = {}
        for member in component:
            scores = [item["score"] for item in similarities_by_tag.get(member, []) if item["similar_tag_id"] in component]
            component_scores[member] = sum(scores) / len(scores) if scores else 0.0

        centroid_tag_id = max(component_scores, key=lambda key: component_scores[key])
        cluster_id = str(uuid.uuid4())
        cluster_name = tag_names.get(centroid_tag_id) or f"Cluster {cluster_count + 1}"

        db.add(
            TagCluster(
                id=cluster_id,
                name=cluster_name,
                description=f"实体标准化簇：基于标签名相似图收敛了 {cluster_name} 及其 {len(component)-1} 个近似实体标签",
                centroid_tag_id=centroid_tag_id,
                size=len(component),
                cluster_version=version,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        cluster_count += 1

        for member in sorted(component, key=lambda member_id: component_scores[member_id], reverse=True):
            db.add(
                TagClusterMember(
                    id=str(uuid.uuid4()),
                    cluster_id=cluster_id,
                    tag_id=member,
                    member_score=_score_to_int(component_scores[member]),
                    cluster_version=version,
                    created_at=datetime.now(),
                )
            )

    db.commit()
    db.commit()

    new_member_rows = db.query(TagClusterMember).filter(TagClusterMember.cluster_version == version).all()
    new_members: dict[str, set[str]] = defaultdict(set)
    for row in new_member_rows:
        if row.cluster_id and row.tag_id:
            new_members[row.cluster_id].add(row.tag_id)

    alias_rows = _build_cluster_aliases(db, old_members, new_members, version)
    db.commit()

    return {
        "tag_count": len(tag_ids),
        "cluster_count": cluster_count,
        "similarity_count": similarity_rows,
        "alias_count": alias_rows,
        "cluster_version": version,
        "provider": provider.provider_name,
    }
