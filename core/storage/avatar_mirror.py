"""公众号头像：识别微信 CDN、在读写 API 中补转存到 MinIO。"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 微信侧头像/图片常见域名（仍指向微信 CDN 时需下载并转存到 MinIO）
_WECHAT_IMG_HOST_MARKERS = (
    "mmbiz.qpic.cn",
    "mmbiz.qlogo.cn",
    "mmecoa.qpic.cn",
    "wx.qlogo.cn",
)


def is_wechat_image_cdn_url(url: str) -> bool:
    if not url or not str(url).strip():
        return False
    u = str(url).lower().strip()
    return any(m in u for m in _WECHAT_IMG_HOST_MARKERS)


def feed_cover_is_self_hosted(cover: str | None) -> bool:
    """非微信 CDN 则视为已落在本系统或其它可长期使用的地址，无需再抓取微信。"""
    c = (cover or "").strip()
    if not c:
        return False
    return not is_wechat_image_cdn_url(c)


def mirror_feed_avatar_to_minio(session: Any, feed: Any) -> bool:
    """
    若 mp_cover 仍为微信 CDN URL，且已开启 MinIO 转存，则下载并写入 MinIO，更新 feed.mp_cover。
    返回是否成功替换为自建 URL。
    """
    cover = (feed.mp_cover or "").strip()
    if not cover or not is_wechat_image_cdn_url(cover):
        return False

    from core.storage.minio_client import MinIOClient, should_mirror_article_images

    if not should_mirror_article_images():
        return False

    client = MinIOClient()
    if not client.is_available():
        return False

    try:
        new_url = client.upload_avatar(cover, feed.id)
        if not new_url:
            return False
        feed.mp_cover = new_url
        session.add(feed)
        session.commit()
        logger.info("公众号头像已补转存 MinIO: feed=%s", feed.id)
        return True
    except Exception as e:
        logger.warning("补转存公众号头像失败 feed=%s: %s", getattr(feed, "id", ""), e)
        try:
            session.rollback()
        except Exception:
            pass
        return False


def mirror_feeds_avatars_batch(session: Any, feeds: list) -> None:
    for feed in feeds:
        try:
            mirror_feed_avatar_to_minio(session, feed)
        except Exception as e:
            logger.debug("mirror_feed_avatar skip feed=%s: %s", getattr(feed, "id", ""), e)
