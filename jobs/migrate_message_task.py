"""
一次性数据迁移：把旧的 MessageTask 拆成 FetchTask + NotifyTask

原 MessageTask 同时承担「按 cron 抓取选定公众号」+「渲染模板推 webhook」两件事。
拆分后：
- FetchTask  -> 继承 mps_id / cron_exp / status / name
- NotifyTask -> 继承 mps_id / cron_exp / status / message_type / message_template / web_hook_url / name

迁移完成后，旧 MessageTask 会被置为 status=0 以避免和新任务双重执行；
原表数据保留以便回溯。

通过 ConfigManagement 中的一行标记防止重复迁移。
"""
import uuid
from datetime import datetime

import core.db as db
from core.log import logger
from core.models import FetchTask, MessageTask, NotifyTask
from core.models.config_management import ConfigManagement
from core.print import print_info, print_success, print_warning

MIGRATION_FLAG_KEY = "__migration_message_task_split_v1__"


def _already_migrated(session) -> bool:
    try:
        flag = session.query(ConfigManagement).filter(
            ConfigManagement.config_key == MIGRATION_FLAG_KEY
        ).first()
        return flag is not None and (flag.config_value or "").strip() == "1"
    except Exception as e:
        logger.warning(f"读取迁移标记失败（视为未迁移）: {e}")
        return False


def _set_migrated(session):
    try:
        flag = session.query(ConfigManagement).filter(
            ConfigManagement.config_key == MIGRATION_FLAG_KEY
        ).first()
        if flag:
            flag.config_value = "1"
        else:
            flag = ConfigManagement(
                config_key=MIGRATION_FLAG_KEY,
                config_value="1",
                description="MessageTask 拆分为 FetchTask + NotifyTask 的迁移标记",
            )
            session.add(flag)
        session.commit()
    except Exception as e:
        logger.warning(f"写入迁移标记失败: {e}")
        session.rollback()


def migrate_message_tasks_if_needed() -> int:
    """如未迁移过，把旧 MessageTask 拆分入新表；返回迁移条数。"""
    session = db.DB.get_session()
    try:
        if _already_migrated(session):
            return 0

        old_tasks = session.query(MessageTask).all()
        if not old_tasks:
            _set_migrated(session)
            print_info("【消息任务拆分】无旧任务，标记为已迁移")
            return 0

        now = datetime.now()
        migrated = 0
        for old in old_tasks:
            try:
                fetch = FetchTask(
                    id=str(uuid.uuid4()),
                    name=f"{old.name or '抓取任务'}（自动迁移）",
                    mps_id=old.mps_id or "[]",
                    cron_exp=old.cron_exp or "0 * * * *",
                    max_page=None,
                    status=1 if old.status == 1 else 0,
                    created_at=old.created_at or now,
                    updated_at=now,
                )
                notify = NotifyTask(
                    id=str(uuid.uuid4()),
                    name=f"{old.name or '推送任务'}（自动迁移）",
                    message_type=old.message_type if old.message_type is not None else 0,
                    message_template=old.message_template or "",
                    web_hook_url=old.web_hook_url or "",
                    mps_id=old.mps_id or "[]",
                    cron_exp=old.cron_exp or "0 9 * * *",
                    status=1 if old.status == 1 else 0,
                    created_at=old.created_at or now,
                    updated_at=now,
                )
                session.add(fetch)
                session.add(notify)
                old.status = 0
                old.updated_at = now
                migrated += 1
            except Exception as e:
                print_warning(f"迁移旧任务[{getattr(old, 'id', '?')}]失败: {e}")

        session.commit()
        _set_migrated(session)
        print_success(f"【消息任务拆分】完成，迁移 {migrated} 条旧任务，已置为停用")
        return migrated
    except Exception as e:
        session.rollback()
        logger.error(f"消息任务拆分迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        try:
            session.close()
        except Exception:
            pass
