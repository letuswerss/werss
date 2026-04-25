-- 添加 is_custom 字段到 tags 表
-- 用于标识用户自定义标签，在标签提取时优先识别

ALTER TABLE tags ADD COLUMN IF NOT EXISTS is_custom BOOLEAN NOT NULL DEFAULT FALSE;

-- 添加注释
COMMENT ON COLUMN tags.is_custom IS '是否为用户自定义标签（用于标签提取时优先识别）';
