-- 热点发现功能相关表
-- 用于基于最近 N 天文章的 LLM 事件级聚类

-- 1. 热点发现任务运行记录表
CREATE TABLE IF NOT EXISTS hot_topic_runs (
    id VARCHAR(255) PRIMARY KEY,
    window_days INTEGER DEFAULT 3,
    article_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    model_name VARCHAR(255),
    prompt_version VARCHAR(100),
    raw_request TEXT,
    raw_response TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 热点主题表
CREATE TABLE IF NOT EXISTS hot_topics (
    id VARCHAR(255) PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL,
    topic_name VARCHAR(500),
    summary TEXT,
    signals_json JSON,
    article_count INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id)
);

-- 3. 热点主题-文章关联表
CREATE TABLE IF NOT EXISTS hot_topic_articles (
    id VARCHAR(255) PRIMARY KEY,
    topic_id VARCHAR(255) NOT NULL,
    article_id VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_topic_id (topic_id),
    INDEX idx_article_id (article_id)
);
