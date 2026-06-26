-- ============================================================
-- 影刀社区 · BI 看板 — Supabase 数据库迁移脚本
-- 请在 Supabase Dashboard → SQL Editor 中执行此脚本
-- ============================================================

-- 1. 帖子表 (posts)
CREATE TABLE IF NOT EXISTS public.posts (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    category VARCHAR(100) NOT NULL DEFAULT '未分类',
    priority VARCHAR(10) NOT NULL DEFAULT 'P2',
    sentiment VARCHAR(20) NOT NULL DEFAULT 'neutral',
    view_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    author_name VARCHAR(100),
    source VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,
    is_anomaly BOOLEAN DEFAULT FALSE,
    risk_level VARCHAR(20),
    root_cause_cluster VARCHAR(200),
    keywords JSONB DEFAULT '[]'::jsonb,
    data_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 每日汇总表 (daily_summaries)
CREATE TABLE IF NOT EXISTS public.daily_summaries (
    id BIGSERIAL PRIMARY KEY,
    data_date DATE NOT NULL UNIQUE,
    total_posts INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_replies INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    p0_count INTEGER DEFAULT 0,
    p1_count INTEGER DEFAULT 0,
    p2_count INTEGER DEFAULT 0,
    anomaly_count INTEGER DEFAULT 0,
    category_breakdown JSONB DEFAULT '{}'::jsonb,
    sentiment_ratio JSONB DEFAULT '{}'::jsonb,
    trend_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 根因分析表 (root_cause_analyses)
CREATE TABLE IF NOT EXISTS public.root_cause_analyses (
    id BIGSERIAL PRIMARY KEY,
    data_date DATE NOT NULL,
    cluster_label VARCHAR(200) NOT NULL,
    post_count INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    keywords JSONB DEFAULT '[]'::jsonb,
    representative_posts JSONB DEFAULT '[]'::jsonb,
    severity VARCHAR(20) DEFAULT 'medium',
    trend VARCHAR(20) DEFAULT 'stable',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 业务洞察表 (business_insights)
CREATE TABLE IF NOT EXISTS public.business_insights (
    id BIGSERIAL PRIMARY KEY,
    data_date DATE NOT NULL,
    insight_type VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    metric_value FLOAT,
    change_pct FLOAT,
    severity VARCHAR(20) DEFAULT 'info',
    related_posts JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 风险告警表 (risk_alerts)
CREATE TABLE IF NOT EXISTS public.risk_alerts (
    id BIGSERIAL PRIMARY KEY,
    data_date DATE NOT NULL,
    title VARCHAR(300) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'P1',
    description TEXT,
    view_count INTEGER DEFAULT 0,
    is_systemic BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 6. 用户表 (users)
CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    display_name VARCHAR(100),
    email VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_posts_category ON public.posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_priority ON public.posts(priority);
CREATE INDEX IF NOT EXISTS idx_posts_sentiment ON public.posts(sentiment);
CREATE INDEX IF NOT EXISTS idx_posts_data_date ON public.posts(data_date);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at);
CREATE INDEX IF NOT EXISTS idx_daily_summaries_data_date ON public.daily_summaries(data_date);
CREATE INDEX IF NOT EXISTS idx_root_cause_analyses_data_date ON public.root_cause_analyses(data_date);
CREATE INDEX IF NOT EXISTS idx_business_insights_data_date ON public.business_insights(data_date);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_data_date ON public.risk_alerts(data_date);

-- ============================================================
-- 启用 Row Level Security (可选)
-- ============================================================
-- 如果需要对帖子表启用 RLS，取消下面的注释：
-- ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "公开可读" ON public.posts FOR SELECT USING (true);
-- CREATE POLICY "认证用户可插入" ON public.posts FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- ============================================================
-- 插入默认管理员用户
-- 密码: admin123 (bcrypt hash)
-- ============================================================
INSERT INTO public.users (username, password_hash, role, display_name, email, is_active)
VALUES (
    'admin',
    '$2b$12$LJ3m4ys3LkBCVxJGqOjPweFpJMJHyKqMqVuMIKmPyFYHlqxG3qLGa',
    'admin',
    '系统管理员',
    'admin@yingdao.com',
    TRUE
) ON CONFLICT (username) DO NOTHING;
