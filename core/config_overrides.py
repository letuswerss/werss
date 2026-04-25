"""控制台写入的 config_management 表覆盖层：使 cfg.get() 与配置列表读到数据库中的值。"""
from __future__ import annotations

import os
from typing import Dict, Optional


def env_overrides_db_mode() -> bool:
    """
    WERSS_ENV_OVERRIDES_DB=true：先使用 config.yaml + 环境变量展开后的值；
    仅当该项未配置或字符串为空时，再回退到 config_management 表。
    未设置或为 false：默认行为，数据库覆盖优先于 yaml/环境变量。
    """
    return os.getenv("WERSS_ENV_OVERRIDES_DB", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

_cache: Optional[Dict[str, str]] = None


def invalidate_config_overrides_cache() -> None:
    global _cache
    _cache = None


def _load_cache() -> Dict[str, str]:
    global _cache
    if _cache is not None:
        return _cache
    try:
        from core.db import DB

        if DB.engine is None:
            _cache = {}
            return _cache
        from core.models.config_management import ConfigManagement

        session = DB.get_session()
        try:
            rows = session.query(ConfigManagement).all()
            _cache = {
                r.config_key: (r.config_value if r.config_value is not None else "")
                for r in rows
            }
        finally:
            session.close()
    except Exception:
        _cache = {}
    return _cache


def get_config_override(config_key: str) -> Optional[str]:
    """若 config_management 中存在该键，返回其值（含空字符串）；否则 None 表示沿用 yaml/环境变量。"""
    if not isinstance(config_key, str) or config_key == "db":
        return None
    d = _load_cache()
    if config_key not in d:
        return None
    return d[config_key]


def get_all_overrides() -> Dict[str, str]:
    return dict(_load_cache())
