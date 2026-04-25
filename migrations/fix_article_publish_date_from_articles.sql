-- 修复 article_tags 表的 article_publish_date 字段
-- 从 articles 表的 publish_time 更新 article_publish_date
-- 修复错误：article_publish_date 被设置为 created_at 的值

-- PostgreSQL 语法
-- 从 articles 表的 publish_time 更新 article_publish_date
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
WHERE (article_publish_date IS NULL 
   OR article_publish_date = article_tags.created_at)  -- 修复错误设置的数据（等于 created_at 的）
  AND EXISTS (
      SELECT 1 FROM articles 
      WHERE articles.id = article_tags.article_id 
        AND articles.publish_time IS NOT NULL
        AND articles.publish_time > 0
  );

-- 验证：检查还有多少条记录 article_publish_date 等于 created_at
-- SELECT COUNT(*) FROM article_tags WHERE article_publish_date = created_at;
