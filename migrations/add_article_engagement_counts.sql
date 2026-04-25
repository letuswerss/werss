-- 为 articles 表增加微信公众号热度数量字段
-- 仅保存当前采集到的数量，不保存评论内容或历史快照

ALTER TABLE articles ADD COLUMN IF NOT EXISTS read_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS like_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS looking_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS comment_count INTEGER;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS share_count INTEGER;
