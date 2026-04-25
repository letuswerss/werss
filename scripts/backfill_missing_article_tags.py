#!/usr/bin/env python3
"""
为「没有任何标签关联」的文章自动补充标签。

与 scripts/re_extract_all_tags.py 的区别：
- 只处理 article_tags 表中尚无任何记录的文章；
- 不会删除已有标签，仅在空白文章上调用与线上一致的提取逻辑（AI 由配置决定）。

用法：
    python scripts/backfill_missing_article_tags.py --dry-run
    python scripts/backfill_missing_article_tags.py --limit 50 --yes
    python scripts/backfill_missing_article_tags.py --mp-id <公众号id>
    python scripts/backfill_missing_article_tags.py --db-url postgresql://user:pass@host:5432/werss_db

积压很多篇时建议：
- 默认按发布时间「从旧到新」处理（--order asc），避免长期只加 --limit 时永远只打到最新稿、老文章永远无标签。
- AI 限流可加 --sleep 0.3；大批量可配合 --offset 分批续跑。
- 仍连不上库时检查 DB / POSTGRES_*，勿落到 sqlite。

在项目根目录的 `.env` 里配置 `DB`（推荐）或 `POSTGRES_*`（与 docker-compose 一致）；
**无 config.yaml 时务必传 `--db-url` 或导出 `DB`，**否则旧逻辑会误连 SQLite。
建议：`cp config.example.yaml config.yaml` 后再按需改 `db` 占位符。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
try:
    os.chdir(project_root)
except OSError:
    pass
_werss_env = os.path.join(project_root, ".env")


def _parse_db_url_argv() -> None:
    """在 import core 之前解析 --db-url，写入环境变量 DB。"""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--db-url" and i + 1 < len(argv):
            os.environ["DB"] = argv[i + 1]
            return
        if a.startswith("--db-url="):
            os.environ["DB"] = a.split("=", 1)[1]
            return


def _bootstrap_db_env() -> None:
    """加载 .env 并在未设置 DB 时用 POSTGRES_* 拼 PostgreSQL URL（必须在 import cfg/db 之前调用）。"""
    _parse_db_url_argv()
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore
    if load_dotenv:
        if os.path.isfile(_werss_env):
            load_dotenv(_werss_env, override=False)
    if os.getenv("DB"):
        return
    postgres_user = os.getenv("POSTGRES_USER", "admin")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db = os.getenv("POSTGRES_WERSS_DB") or os.getenv("POSTGRES_DB", "werss_db")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    if postgres_password:
        os.environ["DB"] = (
            f"postgresql://{postgres_user}:{postgres_password}"
            f"@{postgres_host}:{postgres_port}/{postgres_db}"
        )


_bootstrap_db_env()

from sqlalchemy import exists, or_
from sqlalchemy.orm import Session

from core.config import cfg
from core.db import DB
from core.models.article import Article
from core.models.article_tags import ArticleTag
from core.models.base import DATA_STATUS
from core.models.tags import Tags
from core.print import print_error, print_info, print_success, print_warning


def _reinit_db_if_config_yaml_forced_sqlite() -> None:
    """config.yaml 若写死 sqlite，cfg.get('db') 会忽略环境变量 DB，此处强制切到 PostgreSQL。"""
    url = os.getenv("DB") or ""
    if not url.startswith("postgresql"):
        return
    cur = getattr(DB, "connection_str", None) or ""
    if cur.startswith("sqlite") or cur != url:
        DB.init(url)


_reinit_db_if_config_yaml_forced_sqlite()


def _base_article_query(session: Session):
    """未删除且有标题的文章，且不存在任何 article_tags 行（NOT EXISTS，大表上通常比 outerjoin 更稳）。"""
    no_tag_row = ~exists().where(ArticleTag.article_id == Article.id)
    return (
        session.query(Article)
        .filter(no_tag_row)
        .filter(
            or_(
                Article.status != DATA_STATUS.DELETED,
                Article.status.is_(None),
                Article.status == 0,
            ),
            Article.title.isnot(None),
            Article.title != "",
        )
    )


def backfill_one(
    session: Session,
    article: Article,
    *,
    dry_run: bool,
) -> dict:
    out = {
        "article_id": article.id,
        "title": (article.title or "")[:80],
        "new_tags": [],
        "errors": [],
    }
    if not article.title:
        out["errors"].append("无标题")
        return out

    description = article.description or ""
    content = article.content if getattr(article, "content", None) else ""

    if dry_run:
        nested = session.begin_nested()
        try:
            DB._assign_tags_by_extraction(
                session=session,
                article_id=article.id,
                title=article.title,
                description=description,
                content=content,
            )
            session.flush()
            rows = (
                session.query(ArticleTag)
                .filter(ArticleTag.article_id == article.id)
                .all()
            )
            if rows:
                tag_ids = [r.tag_id for r in rows]
                names = [t.name for t in session.query(Tags).filter(Tags.id.in_(tag_ids)).all()]
                out["new_tags"] = names
        except Exception as e:
            out["errors"].append(str(e))
            print_error(f"试运行提取失败 {article.id}: {e}")
        finally:
            nested.rollback()
        return out

    try:
        DB._assign_tags_by_extraction(
            session=session,
            article_id=article.id,
            title=article.title,
            description=description,
            content=content,
        )
        session.flush()
        rows = session.query(ArticleTag).filter(ArticleTag.article_id == article.id).all()
        if rows:
            tag_ids = [r.tag_id for r in rows]
            out["new_tags"] = [
                t.name for t in session.query(Tags).filter(Tags.id.in_(tag_ids)).all()
            ]
    except Exception as e:
        out["errors"].append(str(e))
        print_error(f"处理失败 {article.id}: {e}")
        raise

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="为无标签文章自动补充标签")
    parser.add_argument("--limit", type=int, default=None, help="最多处理篇数（默认全部）")
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="跳过前 N 篇（与排序一致，便于分批续跑）",
    )
    parser.add_argument(
        "--order",
        choices=("asc", "desc"),
        default="asc",
        help="按 publish_time 排序：asc=最旧优先（默认，适合清积压）；desc=最新优先",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="每篇处理后休眠秒数（缓解 OpenAI 等 API 限流，如 0.2～0.5）",
    )
    parser.add_argument("--mp-id", type=str, default=None, help="仅指定公众号 mp_id")
    parser.add_argument("--dry-run", action="store_true", help="不写库；用 savepoint 试跑提取并回滚")
    parser.add_argument("--batch-size", type=int, default=20, help="每处理多少篇提交一次")
    parser.add_argument(
        "--fail-log",
        type=str,
        default=None,
        help="将失败文章的 id 追加写入该文件（便于对账与重试）",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="不询问确认（适合 cron / 流水线）",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="覆盖数据库连接串（与启动前环境变量 DB 等价，用于指向 PostgreSQL）",
    )
    args = parser.parse_args()
    if args.db_url:
        DB.init(args.db_url)

    db_raw = getattr(DB, "connection_str", None) or cfg.get("db", "") or ""
    db_disp = re.sub(r":([^:@]+)@", ":***@", db_raw) if "@" in db_raw else db_raw
    print_info("=" * 72)
    print_info("补充缺失标签（仅无 article_tags 的文章）")
    print_info(f"数据库: {db_disp}")
    print_info(f"提取方式: {cfg.get('article_tag.extract_method', 'ai')}")
    print_info(f"max_tags: {cfg.get('article_tag.max_tags', 5)}")
    print_info(f"排序: publish_time {args.order}（最旧优先可清历史积压）")
    if args.offset:
        print_info(f"offset: 跳过前 {args.offset} 篇")
    if args.sleep > 0:
        print_info(f"sleep: 每篇 {args.sleep}s")
    if args.dry_run:
        print_warning("dry-run：数据库不会被持久化修改")
    print_info("=" * 72)

    session_factory = DB.get_session_factory()

    # 用独立 session 查询待处理 ID 列表
    id_session = session_factory()
    try:
        q = _base_article_query(id_session)
        if args.mp_id:
            q = q.filter(Article.mp_id == args.mp_id)
        total = q.count()
        print_info(f"待补充（当前条件下无标签）: {total} 篇")

        order_col = Article.publish_time.desc() if args.order == "desc" else Article.publish_time.asc()
        q = q.order_by(order_col)
        if args.offset:
            q = q.offset(args.offset)
        if args.limit is not None:
            q = q.limit(args.limit)
        article_ids = [row[0] for row in q.with_entities(Article.id).all()]
    finally:
        id_session.close()

    n = len(article_ids)
    if n == 0:
        print_warning("没有符合条件的文章，退出。")
        return

    if not args.yes and not args.dry_run:
        r = input(f"将处理 {n} 篇，是否继续？(y/n): ")
        if r.lower() != "y":
            print_info("已取消")
            return

    tagged = 0
    empty = 0
    fail = 0
    for i, aid in enumerate(article_ids, 1):
        session = session_factory()
        try:
            article = session.get(Article, aid)
            if article is None:
                fail += 1
                continue
            title_short = (article.title or "")[:56]
            print_info(f"[{i}/{n}] {title_short}")
            result = backfill_one(session, article, dry_run=args.dry_run)
            if result["errors"]:
                fail += 1
                print_error(f"  跳过: {result['errors']}")
                if args.fail_log:
                    try:
                        with open(args.fail_log, "a", encoding="utf-8") as fl:
                            fl.write(f"{aid}\t{result['errors']}\n")
                    except OSError as e:
                        print_warning(f"  写入 fail-log 失败: {e}")
            elif result["new_tags"]:
                tagged += 1
                print_success(f"  标签: {', '.join(result['new_tags'][:8])}")
            else:
                empty += 1
                print_warning("  未得到标签（正文过短、抽取失败或未命中关键词等，可改 extract_method 或检查 API）")
                if args.fail_log:
                    try:
                        with open(args.fail_log, "a", encoding="utf-8") as fl:
                            fl.write(f"{aid}\tno_tags_extracted\n")
                    except OSError as e:
                        print_warning(f"  写入 fail-log 失败: {e}")
            if not args.dry_run:
                session.commit()
        except Exception:
            fail += 1
            if not args.dry_run:
                session.rollback()
            if args.fail_log:
                try:
                    with open(args.fail_log, "a", encoding="utf-8") as fl:
                        fl.write(f"{aid}\texception\n")
                except OSError:
                    pass
        finally:
            session.close()
        if args.sleep > 0 and i < n:
            time.sleep(args.sleep)

    print_info("-" * 72)
    print_info(
        f"完成: 已打标 {tagged} 篇, 无标签 {empty} 篇, 失败 {fail} 篇, 本轮共 {n} 篇"
    )


if __name__ == "__main__":
    main()
