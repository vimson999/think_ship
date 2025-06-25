-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. 账号表
CREATE TABLE accounts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    platform VARCHAR(50) NOT NULL DEFAULT 'toutiao',
    account_name VARCHAR(100) NOT NULL,
    account_id VARCHAR(100) UNIQUE NOT NULL,
    credentials JSONB NOT NULL,  -- 加密存储的认证信息
    category VARCHAR(50) NOT NULL,  -- 账号定位：tech, news, finance等
    status VARCHAR(20) DEFAULT 'active',  -- active, suspended, banned
    daily_limit INT DEFAULT 5,  -- 每日发文限制
    total_followers INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',  -- 其他账号信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 热点内容表
CREATE TABLE hot_topics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- weibo, zhihu, news等
    source_id VARCHAR(200),  -- 原始来源ID
    source_url TEXT,  -- 原始链接
    title TEXT NOT NULL,
    content TEXT,
    category VARCHAR(50),
    keywords TEXT[],  -- PostgreSQL数组类型
    score FLOAT DEFAULT 0,  -- 热度分数
    metadata JSONB DEFAULT '{}',  -- 原始数据
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    UNIQUE(source, source_id)  -- 防止重复采集
);

-- 3. 生成内容表（分区表）
CREATE TABLE contents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    topic_id UUID REFERENCES hot_topics(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256防止重复
    summary TEXT,
    category VARCHAR(50) NOT NULL,
    keywords TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    images JSONB DEFAULT '[]',  -- 图片URL列表
    ai_model VARCHAR(50),
    generation_params JSONB DEFAULT '{}',  -- AI生成参数
    status VARCHAR(20) DEFAULT 'draft',  -- draft, ready, published, failed
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- 创建月度分区（示例）
CREATE TABLE contents_2024_01 PARTITION OF contents
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE contents_2024_02 PARTITION OF contents
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 4. 发布记录表
CREATE TABLE publish_records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    account_id UUID REFERENCES accounts(id),
    platform VARCHAR(50) DEFAULT 'toutiao',
    platform_post_id VARCHAR(200),  -- 平台返回的内容ID
    platform_url TEXT,  -- 发布后的URL
    publish_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, published, failed
    error_message TEXT,
    retry_count INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',  -- 平台返回的其他信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_id, account_id)  -- 防止重复发布
);

-- 5. 内容表现表（分区表）
CREATE TABLE content_metrics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    publish_id UUID REFERENCES publish_records(id),
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    read_completion_rate FLOAT,
    engagement_rate FLOAT GENERATED ALWAYS AS 
        (CASE WHEN views > 0 THEN (likes + comments + shares)::FLOAT / views ELSE 0 END) STORED,
    revenue DECIMAL(10, 2) DEFAULT 0,  -- 广告收入
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(publish_id, collected_at)  -- 防止重复
) PARTITION BY RANGE (collected_at);

-- 创建月度分区
CREATE TABLE content_metrics_2024_01 PARTITION OF content_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 6. 内容状态转换表（审计日志）
CREATE TABLE content_state_transitions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    operator VARCHAR(50) DEFAULT 'system',  -- system, manual, auto
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 账号健康度表
CREATE TABLE account_health (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    date DATE NOT NULL,
    posts_count INT DEFAULT 0,
    avg_views INT DEFAULT 0,
    avg_engagement_rate FLOAT DEFAULT 0,
    violations_count INT DEFAULT 0,
    warnings_count INT DEFAULT 0,
    health_score FLOAT DEFAULT 100,  -- 0-100分
    recommendations JSONB DEFAULT '[]',  -- AI建议
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, date)
);

-- 8. 内容模板表
CREATE TABLE content_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    template_type VARCHAR(50) NOT NULL,  -- article, short_article, video_script
    structure JSONB NOT NULL,  -- 模板结构
    variables JSONB DEFAULT '{}',  -- 可替换变量
    prompt_template TEXT,  -- AI提示词模板
    is_active BOOLEAN DEFAULT true,
    success_rate FLOAT DEFAULT 0,
    usage_count INT DEFAULT 0,
    avg_quality_score FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 任务队列表
CREATE TABLE task_queue (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,  -- collect, analyze, generate, publish, metric
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed, cancelled
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    error_message TEXT,
    result JSONB,  -- 任务结果
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- 9. 系统配置表
CREATE TABLE system_configs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    config_type VARCHAR(50),  -- global, account, category
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- 10. 操作日志表（分区表）
CREATE TABLE operation_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    level VARCHAR(20) DEFAULT 'info',  -- debug, info, warning, error, critical
    message TEXT,
    user_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    request_id UUID,  -- 追踪请求
    duration_ms INT,  -- 操作耗时
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- 创建日志分区（按月）
CREATE TABLE operation_logs_2024_01 PARTITION OF operation_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 11. 内容状态转换表（状态机记录）
CREATE TABLE content_state_transitions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content_id UUID REFERENCES generated_contents(id) ON DELETE CASCADE,
    from_state VARCHAR(20),
    to_state VARCHAR(20) NOT NULL,
    reason TEXT,
    changed_by VARCHAR(100) DEFAULT 'system',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. 爬虫规则配置表
CREATE TABLE crawler_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- weibo, zhihu, etc
    rule_name VARCHAR(100) NOT NULL,
    url_pattern TEXT,
    selectors JSONB NOT NULL,  -- CSS选择器配置
    headers JSONB DEFAULT '{}',  -- 请求头配置
    rate_limit INT DEFAULT 10,  -- 每分钟请求数
    is_active BOOLEAN DEFAULT true,
    last_success_at TIMESTAMP,
    fail_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_accounts_status_category ON accounts(status, category);
CREATE INDEX idx_accounts_last_post ON accounts(last_post_at);
CREATE INDEX idx_hot_topics_processed ON hot_topics(processed);
CREATE INDEX idx_hot_topics_category_score ON hot_topics(category, score DESC);
CREATE INDEX idx_hot_topics_collected_at ON hot_topics(collected_at DESC);
CREATE INDEX idx_generated_contents_status ON generated_contents(status);
CREATE INDEX idx_generated_contents_hash ON generated_contents(content_hash);
CREATE INDEX idx_generated_contents_category ON generated_contents(category);
CREATE INDEX idx_publish_records_account ON publish_records(account_id);
CREATE INDEX idx_publish_records_status ON publish_records(status);
CREATE INDEX idx_publish_records_scheduled ON publish_records(scheduled_time);
CREATE INDEX idx_content_metrics_publish ON content_metrics(publish_id);
CREATE INDEX idx_content_metrics_time ON content_metrics(metric_time DESC);
CREATE INDEX idx_account_health_score ON account_health(account_id, date DESC);
CREATE INDEX idx_task_queue_status ON task_queue(status, scheduled_at);
CREATE INDEX idx_task_queue_type ON task_queue(task_type);
CREATE INDEX idx_operation_logs_created ON operation_logs(created_at DESC);
CREATE INDEX idx_operation_logs_module ON operation_logs(module, level);


-- 创建触发器：自动更新updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_templates_updated_at BEFORE UPDATE ON content_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crawler_rules_updated_at BEFORE UPDATE ON crawler_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建视图：活跃账号概览
CREATE VIEW active_accounts_overview AS
SELECT 
    a.id,
    a.account_name,
    a.category,
    a.status,
    a.daily_post_count,
    a.total_followers,
    ah.health_score,
    ah.risk_level,
    ah.avg_views,
    ah.avg_engagement_rate
FROM accounts a
LEFT JOIN LATERAL (
    SELECT * FROM account_health 
    WHERE account_id = a.id 
    ORDER BY date DESC 
    LIMIT 1
) ah ON true
WHERE a.status = 'active';

-- 创建视图：内容表现排行
CREATE VIEW content_performance_ranking AS
SELECT 
    gc.id,
    gc.title,
    gc.category,
    pr.account_id,
    pr.platform_url,
    cm.views,
    cm.engagement_rate,
    cm.revenue
FROM generated_contents gc
JOIN publish_records pr ON gc.id = pr.content_id
LEFT JOIN LATERAL (
    SELECT * FROM content_metrics 
    WHERE publish_id = pr.id 
    ORDER BY metric_time DESC 
    LIMIT 1
) cm ON true
WHERE pr.status = 'published'
ORDER BY cm.views DESC NULLS LAST;

-- 初始化系统配置
INSERT INTO system_configs (config_key, config_value, config_type, description) VALUES
('daily_collect_limit', '{"value": 1000}', 'global', '每日采集上限'),
('min_quality_score', '{"value": 0.7}', 'global', '最低质量分数'),
('publish_interval_minutes', '{"value": 30}', 'global', '发布间隔（分钟）'),
('account_cooling_days', '{"value": 7}', 'global', '账号冷却期（天）');