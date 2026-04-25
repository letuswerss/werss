"""热点发现模块

基于最近 N 天的公众号文章，使用 LLM 进行事件级聚类，
识别科技领域的热点话题。
"""

from .service import run_discovery
from .repository import (
    create_run,
    update_run_status,
    get_latest_successful_run,
    get_run_with_topics,
)

__all__ = [
    'run_discovery',
    'create_run',
    'update_run_status',
    'get_latest_successful_run',
    'get_run_with_topics',
]
