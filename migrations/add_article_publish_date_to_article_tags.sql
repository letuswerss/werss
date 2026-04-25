-- 添加 article_publish_date 字段到 article_tags 表
-- 用于记录文章的发布日期，用于趋势统计

-- PostgreSQL 语法
ALTER TABLE article_tags ADD COLUMN IF NOT EXISTS article_publish_date TIMESTAMP;

-- 从 articles 表的 publish_time 更新 article_publish_date
-- 将时间戳转换为 datetime
UPDATE article_tags 
SET article_publish_date = (
    SELECT 
        CASE 
            WHEN articles.publish_time < 10000000000 THEN 
                to_timestamp(articles.publish_time)
            ELSE 
                to_timestamp(articles.publish_time / 1000.0)
        END
    FROM articles 
    WHERE articles.id = article_tags.article_id
)
WHERE article_publish_date IS NULL 
  AND EXISTS (
      SELECT 1 FROM articles 
      WHERE articles.id = article_tags.article_id 
        AND articles.publish_time IS NOT NULL
  );

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_article_tags_publish_date ON article_tags(article_publish_date);

-- 添加注释（PostgreSQL）
COMMENT ON COLUMN article_tags.article_publish_date IS '文章的发布日期（用于趋势统计）';
