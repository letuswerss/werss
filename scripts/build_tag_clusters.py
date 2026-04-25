#!/usr/bin/env python3
from core.db import DB
from core.print import print_error, print_info, print_success
from core.tag_cluster import rebuild_tag_clusters


def main():
    print_info("开始重建标签语义聚类")
    session = DB.get_session()
    try:
        result = rebuild_tag_clusters(session)
        print_success(
            f"完成: tags={result.get('tag_count', 0)}, "
            f"clusters={result.get('cluster_count', 0)}, "
            f"similarities={result.get('similarity_count', 0)}, "
            f"version={result.get('cluster_version', '-')}, "
            f"provider={result.get('provider', '-')}"
        )
    except Exception as e:
        print_error(f"重建标签聚类失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

