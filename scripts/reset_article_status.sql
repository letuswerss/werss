-- 重置文章状态 SQL 脚本
-- 功能：
-- 1. 查看前100篇文章
-- 2. 将所有文章的 status 置为 0

-- ============================================
-- 1. 查看前100篇文章
-- ============================================
SELECT * FROM articles LIMIT 100;

-- ============================================
-- 2. 查看当前状态分布
-- ============================================
SELECT status, COUNT(*) as count 
FROM articles 
GROUP BY status 
ORDER BY status;

-- ============================================
-- 3. 将所有文章的 status 置为 0
-- ============================================
-- 注意：执行前请确认，这是不可逆操作！

-- PostgreSQL 语法：
UPDATE articles SET status = 0;

-- MySQL 语法（相同）：
-- UPDATE articles SET status = 0;

-- SQLite 语法（相同）：
-- UPDATE articles SET status = 0;

-- ============================================
-- 4. 只更新前 N 篇文章（如果需要）
-- ============================================
-- PostgreSQL 语法：
-- UPDATE articles 
-- SET status = 0 
-- WHERE id IN (
--     SELECT id FROM articles LIMIT 100
-- );

-- MySQL 语法：
-- UPDATE articles SET status = 0 LIMIT 100;

-- SQLite 语法（不支持 LIMIT，使用子查询）：
-- UPDATE articles 
-- SET status = 0 
-- WHERE id IN (
--     SELECT id FROM articles LIMIT 100
-- );

-- ============================================
-- 5. 验证更新结果
-- ============================================
SELECT status, COUNT(*) as count 
FROM articles 
GROUP BY status 
ORDER BY status;
