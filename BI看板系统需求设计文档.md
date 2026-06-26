# 影刀社区 · 企业级运营数据看板 — 需求设计文档

> **版本**: v1.0  
> **日期**: 2026-06-25  
> **技术栈**: Vue 3 (前端) + Python FastAPI (后端) + PostgreSQL (数据库) + Redis (缓存)  
> **参考原型**: step5.html

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [数据模型设计](#3-数据模型设计)
4. [API 接口设计](#4-api-接口设计)
5. [前端页面布局与组件树](#5-前端页面布局与组件树)
6. [功能模块详细设计](#6-功能模块详细设计)
7. [按钮与交互行为详述](#7-按钮与交互行为详述)
8. [图表配置详述](#8-图表配置详述)
9. [后端实现步骤](#9-后端实现步骤)
10. [前端实现步骤](#10-前端实现步骤)
11. [部署与运维](#11-部署与运维)

---

## 1. 项目概述

### 1.1 项目背景

基于影刀社区运营数据，构建一个企业级 BI 数据看板系统。该系统用于监控社区帖子趋势、异常检测、情绪分析、问题归因与风险预警，为产品与运营决策提供数据支撑。

### 1.2 核心目标

| 目标 | 描述 |
|------|------|
| 数据可视化 | 将社区运营数据以图表形式直观呈现 |
| 异常检测 | 自动识别 Bug 突增、情绪恶化等异常信号 |
| 风险预警 | 对 P0/P1 级别问题进行实时告警 |
| 根因分析 | 通过语义聚类识别问题根因 |
| 决策支持 | 输出可执行的业务洞察建议 |

### 1.3 用户角色

| 角色 | 权限描述 |
|------|----------|
| 管理员 | 全部数据查看、系统配置、用户管理 |
| 运营人员 | 数据查看、筛选、导出 |
| 产研人员 | 查看 Bug/异常相关数据、风险预警 |
| 只读用户 | 仅查看汇总数据，不可导出 |

---

## 2. 技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 看板首页  │ │ 趋势分析  │ │ 问题分析  │ │ 风险中心 │ │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │         组件库 (ECharts / Tailwind CSS)          │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │      状态管理 (Pinia) + 路由 (Vue Router)        │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────┴──────────────────────────────┐
│                  后端 (Python FastAPI)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 数据接口层 │ │ 分析服务层 │ │ 告警服务  │ │ 认证服务 │ │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │     数据采集 (定时任务 / 消息队列 / 爬虫)         │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│              数据层 (PostgreSQL + Redis)              │
│  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │   PostgreSQL     │  │   Redis (缓存 / 会话)     │  │
│  │   (业务数据)      │  │                          │  │
│  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 2.2 前端技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 前端框架，使用 Composition API |
| Vite | 5.x | 构建工具 |
| Vue Router | 4.x | 路由管理 |
| Pinia | 2.x | 状态管理 |
| ECharts | 5.5+ | 数据可视化图表 |
| Tailwind CSS | 3.4+ | 原子化 CSS 样式 |
| Axios | 1.x | HTTP 请求 |
| dayjs | 1.x | 日期处理 |
| VueUse | 10.x | 组合式工具函数 |

### 2.3 后端技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 后端语言 |
| FastAPI | 0.110+ | Web 框架 |
| SQLAlchemy | 2.x | ORM |
| Alembic | 1.x | 数据库迁移 |
| Pydantic | 2.x | 数据校验 |
| APScheduler | 3.x | 定时任务调度 |
| Redis | 7.x | 缓存与会话 |
| PostgreSQL | 16.x | 主数据库 |
| Pandas | 2.x | 数据分析 |
| scikit-learn | 1.x | 语义聚类 (可选) |
| JWT (PyJWT) | 2.x | 身份认证 |

---

## 3. 数据模型设计

### 3.1 数据库表结构 (PostgreSQL)

#### 3.1.1 帖子表 `posts`

```sql
CREATE TABLE posts (
    id              BIGSERIAL PRIMARY KEY,
    title           VARCHAR(500) NOT NULL,              -- 帖子标题
    content         TEXT,                                -- 帖子正文
    category        VARCHAR(100) NOT NULL,               -- 问题分类
    priority        VARCHAR(10) NOT NULL DEFAULT 'P2',  -- 优先级: P0/P1/P2
    sentiment       VARCHAR(20) NOT NULL,                -- 情绪: negative/neutral/positive
    view_count      INTEGER DEFAULT 0,                   -- 浏览量
    reply_count     INTEGER DEFAULT 0,                   -- 回复数
    author_name     VARCHAR(100),                        -- 发帖人
    source          VARCHAR(100),                        -- 来源渠道
    tags            JSONB DEFAULT '[]',                  -- 标签
    is_anomaly      BOOLEAN DEFAULT FALSE,               -- 是否异常
    risk_level      VARCHAR(20),                         -- 风险等级: high/medium/low
    root_cause_cluster VARCHAR(200),                     -- 根因聚类标签
    keywords        JSONB DEFAULT '[]',                  -- 关键词
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),   -- 发帖时间
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),   -- 更新时间
    data_date       DATE NOT NULL                        -- 数据日期 (分区键)
);

CREATE INDEX idx_posts_category ON posts(category);
CREATE INDEX idx_posts_priority ON posts(priority);
CREATE INDEX idx_posts_sentiment ON posts(sentiment);
CREATE INDEX idx_posts_data_date ON posts(data_date);
CREATE INDEX idx_posts_created_at ON posts(created_at);
```

#### 3.1.2 每日汇总表 `daily_summary`

```sql
CREATE TABLE daily_summary (
    id                  BIGSERIAL PRIMARY KEY,
    data_date           DATE NOT NULL UNIQUE,            -- 数据日期
    total_posts         INTEGER DEFAULT 0,               -- 总帖子量
    bug_posts           INTEGER DEFAULT 0,               -- Bug类帖子量
    consultation_posts  INTEGER DEFAULT 0,               -- 咨询类帖子量
    rpa_posts           INTEGER DEFAULT 0,               -- RPA执行类帖子量
    excel_posts         INTEGER DEFAULT 0,               -- Excel类帖子量
    third_party_posts   INTEGER DEFAULT 0,               -- 第三方系统类帖子量
    emergency_posts     INTEGER DEFAULT 0,               -- 紧急求助帖子量
    negative_count      INTEGER DEFAULT 0,               -- 消极情绪数
    neutral_count       INTEGER DEFAULT 0,               -- 中性情绪数
    positive_count      INTEGER DEFAULT 0,               -- 积极情绪数
    p0_count            INTEGER DEFAULT 0,               -- P0数量
    p1_count            INTEGER DEFAULT 0,               -- P1数量
    p2_count            INTEGER DEFAULT 0,               -- P2数量
    health_score        INTEGER DEFAULT 100,             -- 健康度评分 0-100
    anomaly_flag        BOOLEAN DEFAULT FALSE,           -- 异常标记
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
```

#### 3.1.3 根因分析表 `root_cause_analysis`

```sql
CREATE TABLE root_cause_analysis (
    id              BIGSERIAL PRIMARY KEY,
    data_date       DATE NOT NULL,                       -- 分析日期
    cluster_name    VARCHAR(200) NOT NULL,               -- 聚类名称
    cluster_index   INTEGER NOT NULL,                    -- 聚类序号
    post_count      INTEGER DEFAULT 0,                   -- 涉及帖子数
    percentage      DECIMAL(5,2) DEFAULT 0,              -- 占比
    keywords        JSONB DEFAULT '[]',                  -- 关键词
    possible_cause  TEXT,                                -- 可能原因
    suggestion      TEXT,                                -- 建议措施
    priority_level  VARCHAR(10) DEFAULT 'P1',            -- 优先级
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### 3.1.4 业务洞察表 `business_insights`

```sql
CREATE TABLE business_insights (
    id              BIGSERIAL PRIMARY KEY,
    data_date       DATE NOT NULL,
    insight_index   INTEGER NOT NULL,                    -- 洞察序号 1-5
    title           VARCHAR(300) NOT NULL,               -- 洞察标题
    impact          TEXT,                                -- 影响描述
    suggestion      TEXT,                                -- 建议措施
    severity        VARCHAR(20) DEFAULT 'medium',        -- 严重程度
    category        VARCHAR(50),                         -- 分类
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### 3.1.5 风险告警表 `risk_alerts`

```sql
CREATE TABLE risk_alerts (
    id              BIGSERIAL PRIMARY KEY,
    data_date       DATE NOT NULL,
    title           VARCHAR(300) NOT NULL,
    priority        VARCHAR(10) NOT NULL,                -- P0/P1/P2
    description     TEXT,
    view_count      INTEGER DEFAULT 0,
    is_systemic     BOOLEAN DEFAULT FALSE,               -- 是否系统性风险
    status          VARCHAR(20) DEFAULT 'active',        -- active/resolved/ignored
    resolved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### 3.1.6 用户表 `users`

```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'viewer', -- admin/operator/developer/viewer
    display_name    VARCHAR(100),
    email           VARCHAR(200),
    is_active       BOOLEAN DEFAULT TRUE,
    last_login_at   TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### 3.1.7 系统配置表 `system_config`

```sql
CREATE TABLE system_config (
    id              BIGSERIAL PRIMARY KEY,
    config_key      VARCHAR(100) NOT NULL UNIQUE,
    config_value    JSONB NOT NULL,
    description     TEXT,
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 |
|----------|------|-----|------|
| `dashboard:summary:{date}` | String (JSON) | 300s | 每日汇总数据 |
| `dashboard:trend:{start}:{end}` | String (JSON) | 600s | 趋势数据 |
| `dashboard:sentiment:{date}` | String (JSON) | 300s | 情绪数据 |
| `dashboard:categories:{date}` | String (JSON) | 300s | 分类数据 |
| `dashboard:hot_posts:{date}` | String (JSON) | 120s | 热门帖子 |
| `dashboard:insights:{date}` | String (JSON) | 600s | 业务洞察 |
| `dashboard:risk:{date}` | String (JSON) | 300s | 风险告警 |
| `user:session:{token}` | String (JSON) | 86400s | 用户会话 |

---

## 4. API 接口设计

### 4.1 接口总览

```
Base URL: /api/v1

认证相关:
  POST   /auth/login              用户登录
  POST   /auth/logout             用户登出
  GET    /auth/me                 获取当前用户信息

看板数据:
  GET    /dashboard/summary       看板总览数据
  GET    /dashboard/trend         趋势数据 (折线图)
  GET    /dashboard/sentiment     情绪分布 (饼图)
  GET    /dashboard/categories    问题分类 (柱状图)
  GET    /dashboard/priority      优先级分布
  GET    /dashboard/hot-posts     热门帖子 TOP N
  GET    /dashboard/root-cause    根因分析
  GET    /dashboard/insights      业务洞察
  GET    /dashboard/risk-alerts   风险告警
  GET    /dashboard/health-score  健康度评分

数据管理:
  GET    /posts                   帖子列表 (分页、筛选)
  GET    /posts/{id}              帖子详情
  POST   /posts                   新增帖子
  PUT    /posts/{id}              更新帖子
  DELETE /posts/{id}              删除帖子

数据导出:
  GET    /export/posts            导出帖子数据 (CSV/Excel)
  GET    /export/dashboard        导出看板数据 (PDF)

系统管理:
  GET    /admin/users             用户列表
  POST   /admin/users             创建用户
  PUT    /admin/users/{id}        更新用户
  DELETE /admin/users/{id}        删除用户
  GET    /admin/config            系统配置
  PUT    /admin/config            更新系统配置
  POST   /admin/data/refresh      手动触发数据刷新

WebSocket:
  WS     /ws/dashboard            看板实时数据推送
```

### 4.2 核心接口详细定义

#### 4.2.1 看板总览数据

```
GET /api/v1/dashboard/summary?date=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "date": "2026-06-25",
    "health_score": 45,
    "health_status": "high_risk",          // healthy/warning/high_risk
    "health_description": "Bug占比与消极情绪占比双高...",
    "total_posts": 314,
    "daily_avg_posts": 52.3,
    "bug_ratio": 34.7,
    "negative_ratio": 51.0,
    "today_vs_yesterday": {
      "change_type": "surge",              // surge/increase/stable/decrease
      "change_percent": 17.9,
      "description": "Bug类问题（6/23→6/24）",
      "bar_percent": 72
    },
    "p0_risk": {
      "level": "need_attention",
      "emergency_count": 1,
      "systemic_bug_count": 5,
      "p0_count": 6,
      "p1_count": 181,
      "p2_count": 127
    },
    "data_period": {
      "start": "2026-06-20",
      "end": "2026-06-25"
    },
    "sample_count": 314
  }
}
```

#### 4.2.2 趋势数据

```
GET /api/v1/dashboard/trend?start=2026-06-20&end=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "dates": ["6/20", "6/21", "6/22", "6/23", "6/24", "6/25*"],
    "series": [
      {
        "name": "Bug / 系统异常",
        "data": [4, 8, 28, 28, 33, 8],
        "color": "#ef4444",
        "anomaly": {
          "type": "surge",
          "percent": 17.9,
          "peak_date": "6/24",
          "peak_value": 33
        }
      },
      {
        "name": "功能咨询",
        "data": [2, 12, 26, 29, 22, 12],
        "color": "#8b5cf6"
      },
      {
        "name": "RPA执行",
        "data": [1, 6, 5, 12, 11, 9],
        "color": "#3b82f6"
      },
      {
        "name": "Excel数据",
        "data": [3, 2, 5, 6, 8, 4],
        "color": "#f59e0b",
        "anomaly": {
          "type": "surge",
          "percent": 33.3
        }
      },
      {
        "name": "第三方系统",
        "data": [0, 1, 7, 9, 7, 4],
        "color": "#10b981"
      }
    ],
    "anomaly_tags": [
      {"label": "Bug 突增 +17.9%", "type": "danger"},
      {"label": "Excel 突增 +33.3%", "type": "warn"}
    ],
    "description": "6/22 起整体帖量进入高位（>70/日）..."
  }
}
```

#### 4.2.3 情绪数据

```
GET /api/v1/dashboard/sentiment?date=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "items": [
      {"name": "消极", "value": 160, "percent": 51.0, "color": "#ef4444"},
      {"name": "中性", "value": 150, "percent": 47.8, "color": "#8b5cf6"},
      {"name": "积极", "value": 3,   "percent": 1.0,  "color": "#10b981"}
    ],
    "dominant": "negative",
    "description": "消极情绪连续4日≥40条，主要驱动来自Bug/系统异常（占消极53%）..."
  }
}
```

#### 4.2.4 问题分类数据

```
GET /api/v1/dashboard/categories?date=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "categories": [
      {"name": "Bug / 系统异常",   "count": 109, "percent": 34.7, "color": "#ef4444"},
      {"name": "功能咨询",         "count": 103, "percent": 32.8, "color": "#8b5cf6"},
      {"name": "RPA执行问题",      "count": 44,  "percent": 14.0, "color": "#3b82f6"},
      {"name": "Excel数据问题",    "count": 28,  "percent": 8.9,  "color": "#f59e0b"},
      {"name": "第三方系统问题",    "count": 28,  "percent": 8.9,  "color": "#10b981"},
      {"name": "紧急求助",         "count": 1,   "percent": 0.3,  "color": "#f97316"}
    ],
    "total": 314
  }
}
```

#### 4.2.5 热门帖子

```
GET /api/v1/dashboard/hot-posts?date=2026-06-25&limit=8

Response 200:
{
  "code": 0,
  "data": {
    "posts": [
      {
        "id": 1,
        "title": "多台电脑反复出现元素错位",
        "category": "Bug / 系统异常",
        "sentiment": "消极",
        "view_count": 337,
        "priority": "P0"
      }
      // ... 共8条
    ]
  }
}
```

#### 4.2.6 根因分析

```
GET /api/v1/dashboard/root-cause?date=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "clusters": [
      {
        "index": 1,
        "name": "元素定位 / 元素错位",
        "count": 42,
        "percent": 13.4,
        "priority": "danger",
        "keywords": ["元素错位", "多账号偏移", "xpath", "iframe", "懒加载"],
        "possible_cause": "近期发版引入DOM兼容性回归...",
        "suggestion": "回归覆盖：多账号、Chrome新版、iframe、懒加载四类场景"
      }
      // ... 共4个聚类
    ],
    "total_clusters": 4
  }
}
```

#### 4.2.7 业务洞察

```
GET /api/v1/dashboard/insights?date=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "insights": [
      {
        "index": 1,
        "title": "Bug类问题进入爆发期，需立刻冻结非必要发版",
        "impact": "消极情绪51%，已显著超过预警线（35%）",
        "suggestion": "组织RPA引擎+浏览器适配专项hotfix，48小时内合入",
        "severity": "critical",
        "color": "#ef4444"
      }
      // ... 共5条
    ]
  }
}
```

#### 4.2.8 风险告警

```
GET /api/v1/dashboard/risk-alerts?date=2026-06-25

Response 200:
{
  "code": 0,
  "data": {
    "is_systemic_risk": true,
    "urgent_action_required": true,
    "suggestion": "建议立刻拉起跨研发-产品-客服三方应急例会...",
    "alerts": [
      {
        "id": 1,
        "title": "多电脑反复出现元素错位",
        "priority": "P0",
        "description": "浏览量337（周期最高），跨账号复现",
        "is_systemic": true
      }
      // ...
    ]
  }
}
```

#### 4.2.9 数据导出

```
GET /api/v1/export/posts?start=2026-06-20&end=2026-06-25&format=csv
Response: application/octet-stream (文件下载)

GET /api/v1/export/dashboard?date=2026-06-25&format=pdf
Response: application/pdf (文件下载)
```

#### 4.2.10 WebSocket 实时推送

```
WS /api/v1/ws/dashboard?token=xxx

服务端推送消息格式:
{
  "type": "health_update",           // 消息类型
  "data": {
    "health_score": 42,
    "health_status": "high_risk"
  }
}

{
  "type": "new_alert",
  "data": {
    "id": 10,
    "title": "新P0告警: ...",
    "priority": "P0"
  }
}

{
  "type": "data_refresh",
  "data": {
    "message": "数据已刷新",
    "timestamp": "2026-06-25T14:30:00"
  }
}
```

### 4.3 通用响应格式

```json
// 成功
{
  "code": 0,
  "data": { ... },
  "message": "ok"
}

// 失败
{
  "code": 40001,
  "data": null,
  "message": "参数错误: date 格式不正确"
}

// 错误码定义
// 0:     成功
// 40001: 参数错误
// 40100: 未认证
// 40300: 无权限
// 40400: 资源不存在
// 50000: 服务器内部错误
```

---

## 5. 前端页面布局与组件树

### 5.1 路由设计

```javascript
const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true, title: '运营数据看板' }
  },
  {
    path: '/trend',
    name: 'TrendAnalysis',
    component: () => import('@/views/TrendAnalysisView.vue'),
    meta: { requiresAuth: true, title: '趋势分析' }
  },
  {
    path: '/issues',
    name: 'IssueAnalysis',
    component: () => import('@/views/IssueAnalysisView.vue'),
    meta: { requiresAuth: true, title: '问题分析' }
  },
  {
    path: '/risk',
    name: 'RiskCenter',
    component: () => import('@/views/RiskCenterView.vue'),
    meta: { requiresAuth: true, title: '风险中心' }
  },
  {
    path: '/posts',
    name: 'PostList',
    component: () => import('@/views/PostListView.vue'),
    meta: { requiresAuth: true, title: '帖子管理' }
  },
  {
    path: '/posts/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetailView.vue'),
    meta: { requiresAuth: true, title: '帖子详情' }
  },
  {
    path: '/admin',
    name: 'AdminPanel',
    component: () => import('@/views/AdminPanelView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '系统管理' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue')
  }
]
```

### 5.2 看板首页组件树

```
DashboardView.vue
├── TopNavBar.vue                          // 顶部导航栏
│   ├── Logo.vue                           //   Logo + 标题
│   ├── StatusChips.vue                    //   状态标签组
│   │   ├── LiveIndicator.vue              //     实时指示灯 (脉冲动画)
│   │   ├── DateRangeChip.vue              //     数据周期
│   │   └── SampleCountChip.vue            //     样本数量
│   ├── UserMenu.vue                       //   用户菜单
│   │   ├── UserAvatar.vue                 //     头像
│   │   └── DropdownMenu.vue               //     下拉菜单 (个人信息/退出)
│   └── NavLinks.vue                       //   导航链接
│
├── PageHeader.vue                         // 页面标题区
│   ├── DailyInsightTitle.vue              //   每日洞察标题
│   └── DescriptionText.vue                //   描述文字
│
├── SectionHealthScore.vue                 // 区域1: 健康度 + 快速统计
│   ├── HealthScoreCard.vue                //   健康度卡片
│   │   ├── ScoreRing.vue                  //     SVG 圆环进度 (0-100)
│   │   ├── MiniStatCards.vue              //     迷你统计卡片 x4
│   │   │   └── MiniCard.vue (x4)
│   │   └── AssessmentText.vue             //     健康评估文字
│   ├── TodayVsYesterdayCard.vue           //   日环比卡片
│   │   ├── ChangePercent.vue              //     变化百分比
│   │   ├── ProgressBar.vue                //     进度条
│   │   └── DescriptionText.vue            //     描述文字
│   └── P0RiskCard.vue                     //   P0风险卡片
│       ├── RiskSummary.vue                //     风险摘要
│       └── PriorityGrid.vue               //     优先级分布网格 P0/P1/P2
│           └── PriorityCell.vue (x3)
│
├── SectionTrendSentiment.vue              // 区域2: 趋势 + 情绪
│   ├── TrendChartCard.vue                 //   趋势图卡片
│   │   ├── ChartHeader.vue                //     图表标题栏
│   │   │   ├── SectionLabel.vue           //       区域标签 (TREND & ANOMALY)
│   │   │   ├── SectionTitle.vue           //       区域标题
│   │   │   └── AnomalyTags.vue            //       异常标签
│   │   │       └── Chip.vue (x2)
│   │   ├── LineChart.vue                  //     ECharts 折线图
│   │   └── ChartDescription.vue           //     图表说明文字
│   └── SentimentChartCard.vue             //   情绪图卡片
│       ├── ChartHeader.vue                //     图表标题栏
│       ├── DonutChart.vue                 //     ECharts 环形饼图
│       ├── SentimentBarList.vue           //     情绪柱状列表
│       │   └── SentimentBarItem.vue (x3)  //       单条情绪 (标签/百分比/进度条)
│       └── ChartDescription.vue           //     图表说明文字
│
├── SectionIssueBreakdown.vue              // 区域3: 问题拆解 + 优先级
│   ├── CategoryChartCard.vue              //   分类图表卡片
│   │   ├── ChartHeader.vue
│   │   └── HorizontalBarChart.vue         //     ECharts 横向柱状图
│   └── PriorityDistributionCard.vue       //   优先级分布卡片
│       ├── ChartHeader.vue
│       └── PriorityDetailList.vue         //     优先级详情列表
│           └── PriorityDetailItem.vue (x3)//       单条优先级详情 (P0/P1/P2)
│               ├── Badge.vue              //         优先级徽章
│               ├── DetailText.vue         //         详情文字
│               ├── CountNumber.vue        //         数量
│               └── ProgressBar.vue        //         进度条
│
├── SectionRootCauseInsight.vue            // 区域4: 根因 + 洞察
│   ├── RootCauseCard.vue                  //   根因分析卡片
│   │   ├── ChartHeader.vue
│   │   └── ClusterList.vue                //     聚类列表
│   │       └── ClusterItem.vue (x4)       //       单条聚类
│   │           ├── ClusterTitle.vue       //         聚类标题
│   │           ├── ClusterStats.vue       //         统计 (条数/占比)
│   │           ├── KeywordsList.vue       //         关键词
│   │           └── CauseAnalysis.vue      //         原因分析
│   └── BusinessInsightCard.vue            //   业务洞察卡片
│       ├── ChartHeader.vue
│       └── InsightList.vue                //     洞察列表
│           └── InsightItem.vue (x5)       //       单条洞察
│               ├── IndexBadge.vue         //         序号徽章 (1-5 带颜色)
│               ├── InsightTitle.vue       //         标题
│               ├── ImpactText.vue         //         影响描述
│               └── SuggestionText.vue     //         建议
│
├── SectionRiskHotPosts.vue                // 区域5: 风险 + 热门帖子
│   ├── RiskAlertCard.vue                  //   风险告警卡片
│   │   ├── ChartHeader.vue                //     标题栏 (含脉冲指示灯)
│   │   ├── AlertGrid.vue                  //     告警网格
│   │   │   └── AlertItem.vue (x4)         //       单条告警
│   │   │       ├── PriorityBadge.vue      //         优先级徽章
│   │   │       ├── AlertTitle.vue         //         告警标题
│   │   │       └── AlertDescription.vue   //         告警描述
│   │   └── RiskSummaryFooter.vue          //     风险总结
│   └── HotPostsCard.vue                   //   热门帖子卡片
│       ├── ChartHeader.vue
│       └── HotPostList.vue                //     热帖列表
│           └── HotPostItem.vue (x8)       //       单条热帖
│               ├── PostTitle.vue          //         帖子标题 (截断)
│               ├── PostMeta.vue           //         分类/情绪
│               └── ViewCount.vue          //         浏览量
│
└── PageFooter.vue                         // 页脚
    └── CopyrightText.vue
```

---

## 6. 功能模块详细设计

### 6.1 模块一：顶部导航栏 (TopNavBar)

#### 6.1.1 功能描述
- 固定在页面顶部 (`position: sticky`)
- 毛玻璃半透明效果 (`backdrop-filter: blur`)
- 包含 Logo、系统标题、实时状态指示、数据周期、样本量、用户菜单

#### 6.1.2 子组件行为

**Logo.vue**
- 显示影刀 Logo 图标 (SVG 趋势图图标)
- 蓝紫渐变背景圆角方块
- 无交互行为（纯展示）

**LiveIndicator.vue**
- 显示红色脉冲圆点 + "实时" 文字
- 脉冲动画：红色阴影呼吸效果，2s 循环
- 点击：无交互（纯状态展示）
- 当系统离线时变为灰色静态圆点 + "离线" 文字

**DateRangeChip.vue**
- 显示当前数据周期，如 "数据周期 2026/06/20 — 2026/06/25"
- 点击：弹出日期范围选择器 (DateRangePicker)，可自定义查询周期
- 选择后触发全局数据刷新

**SampleCountChip.vue**
- 显示样本量，如 "样本 314 条"
- 纯展示

**UserMenu.vue**
- 显示用户头像（首字母头像）和用户名
- 点击展开下拉菜单：
  - "个人信息" → 跳转个人信息页
  - "系统设置" → 跳转管理页（仅管理员可见）
  - "退出登录" → 清除 token，跳转登录页

**NavLinks.vue**
- 导航链接列表：看板总览 | 趋势分析 | 问题分析 | 风险中心 | 帖子管理
- 当前激活路由高亮显示
- 点击切换路由

#### 6.1.3 响应式行为
- 移动端 (<768px): 导航链接折叠为汉堡菜单
- 状态标签组在移动端仅显示"实时"指示器，其余隐藏

---

### 6.2 模块二：健康度评分区 (SectionHealthScore)

#### 6.2.1 HealthScoreCard — 健康度卡片

**ScoreRing (SVG 圆环)**
- 圆形进度环，表示健康评分 (0-100)
- 轨道颜色：半透明灰色
- 进度颜色：红→橙→黄渐变 (低分偏红，高分偏绿)
- 中心大字显示当前评分，下方小字 "/ 100"
- 动画：`stroke-dashoffset` 过渡 1.2s 弹性曲线
- 悬停效果：卡片上浮 2px，阴影加深

**MiniStatCards (4个迷你卡片)**
| 卡片 | 指标 | 数据来源字段 |
|------|------|-------------|
| 总帖子量 | 314 | `total_posts` |
| 日均帖子量 | 52.3 | `daily_avg_posts` |
| Bug 占比 | 34.7% | `bug_ratio` |
| 消极情绪占比 | 51.0% | `negative_ratio` |

- 每个卡片：灰色小标题 + 大号数字
- "Bug 占比"和"消极情绪占比"数字使用红色 (`t-danger`)
- 悬停效果：背景变亮，轻微上浮

**AssessmentText**
- 显示健康度评估说明
- 关键短语使用彩色字体（红/橙色高亮）
- 内容由后端 `health_description` 字段提供

#### 6.2.2 TodayVsYesterdayCard — 日环比卡片

- 显示日环比变化数据
- 顶部：标签 "今日 vs 昨日" + 状态标签 (突增/下降/持平)
- 主体：大号百分比数字 (如 +17.9%)
- 描述文字说明变化类型
- 底部进度条：可视化变化幅度

**状态标签颜色规则**
| 变化幅度 | 类型 | 标签颜色 |
|----------|------|----------|
| > +15% | 突增 | danger (红) |
| +5% ~ +15% | 上升 | warn (橙) |
| -5% ~ +5% | 持平 | info (蓝) |
| < -5% | 下降 | ok (绿) |

#### 6.2.3 P0RiskCard — P0 风险卡片

- 顶部标签 "P0 风险" + 状态标签
- 紧急求助数量 + 系统性 Bug 数量
- P0/P1/P2 三格分布网格
  - P0: 红色数字 (紧急)
  - P1: 橙色数字 (警告)
  - P2: 蓝色数字 (信息)

**状态判定规则**
| 条件 | 标签 | 颜色 |
|------|------|------|
| P0 ≥ 5 或紧急求助 ≥ 3 | 紧急处理 | danger |
| P0 ≥ 2 或 P1 > 150 | 需关注 | warn |
| 其他 | 正常 | ok |

---

### 6.3 模块三：趋势与情绪区 (SectionTrendSentiment)

#### 6.3.1 TrendChartCard — 趋势图卡片

**功能**
- 展示 5 个分类的每日帖子量折线图
- 支持异常点标记 (峰值 pin 标记)
- 异常标签 (如 "Bug 突增 +17.9%")

**ECharts 折线图配置**
- 5 条平滑折线 (`smooth: true`)
- X 轴：日期 (6/20 ~ 6/25*)
- Y 轴：帖子数量
- 图例：右上角，圆形图标
- Tooltip：毛玻璃效果弹出层
- Bug 系列带面积渐变 (红→透明)
- Bug 系列峰值标记点 (pin 图标)
- 最新一天 (6/25*) 数据虚线样式表示不完整

**AnomalyTags**
- 显示异常标签组
- 每个标签可点击，点击后：
  - 对应系列高亮，其他系列半透明
  - 弹出该异常的详细说明 tooltip
- 再次点击取消高亮

**交互行为**
| 交互 | 行为 |
|------|------|
| 鼠标悬停数据点 | 显示 tooltip (日期 + 分类名 + 数值) |
| 点击图例项 | 切换该系列的显示/隐藏 |
| 双击图表空白 | 重置所有交互状态 |
| 刷选区域 | 放大选定时间范围 (dataZoom) |
| 点击异常标签 | 高亮对应系列 |

#### 6.3.2 SentimentChartCard — 情绪图表卡片

**DonutChart (环形饼图)**
- 3 个扇区：消极(红)、中性(紫)、积极(绿)
- 内半径 62%，外半径 88%
- 中心文字：主情绪标签 + 百分比
- 圆角扇区 (`borderRadius: 6`)
- 白色间隔线

**SentimentBarList**
- 3 条情绪柱状列表
- 每条：圆点颜色指示 + 情绪名称 + 数量 + 百分比 + 进度条
- 进度条颜色与情绪颜色对应

**交互行为**
| 交互 | 行为 |
|------|------|
| 鼠标悬停扇区 | 显示 tooltip (情绪名 + 数量 + 百分比) |
| 点击扇区 | 高亮该扇区 (其他扇区半透明)，下方柱状列表对应项高亮 |
| 再次点击 | 取消高亮 |

---

### 6.4 模块四：问题拆解区 (SectionIssueBreakdown)

#### 6.4.1 CategoryChartCard — 分类图卡片

**HorizontalBarChart (横向柱状图)**
- 6 个分类的横向柱状图
- Y 轴：分类名称
- X 轴：数量
- 每个柱子：从左到右渐变 (浅色→深色)
- 右端圆角 (`borderRadius: [0, 10, 10, 0]`)
- 每根柱子右侧标签：数量 · 百分比
- 降序排列（数量多的在上）

**交互行为**
| 交互 | 行为 |
|------|------|
| 鼠标悬停柱子 | 显示 tooltip (分类名 + 数量 + 百分比) |
| 点击柱子 | 跳转到帖子列表页，自动筛选该分类 |

#### 6.4.2 PriorityDistributionCard — 优先级分布卡片

**PriorityDetailList**
- P0/P1/P2 三个优先级详情卡片
- 每个卡片包含：
  - 优先级徽章（彩色渐变圆角标签）
  - 标题描述（如 "系统不可用 / 大面积 / 紧急求助"）
  - 子分类标签（如 "登录失败、批量数据抓取BUG"）
  - 数量数字
  - 进度条（相对于总数的百分比宽度）

**交互行为**
| 交互 | 行为 |
|------|------|
| 点击 P0 卡片 | 跳转到帖子列表，筛选 P0 |
| 点击 P1 卡片 | 跳转到帖子列表，筛选 P1 |
| 点击 P2 卡片 | 跳转到帖子列表，筛选 P2 |

---

### 6.5 模块五：根因与洞察区 (SectionRootCauseInsight)

#### 6.5.1 RootCauseCard — 根因分析卡片

**ClusterList**
- 4 个语义聚类条目
- 每条包含：
  - 聚类序号 + 名称 (如 "① 元素定位 / 元素错位")
  - 统计标签：条数 + 占比
  - 关键词列表
  - 可能原因分析
  - 建议措施

**关键词颜色规则**
| 优先级 | 标签颜色 |
|--------|----------|
| 高 (>10%) | danger (红) |
| 中 (5%-10%) | warn (橙) |
| 低 (<5%) | info (蓝) |

**交互行为**
| 交互 | 行为 |
|------|------|
| 点击聚类条目 | 展开/收起详细分析 |
| 点击关键词 | 跳转帖子列表，按关键字搜索 |
| 悬停条目 | 高亮背景 |

#### 6.5.2 BusinessInsightCard — 业务洞察卡片

**InsightList**
- 5 条可执行洞察
- 每条包含：
  - 序号徽章 (1-5，各有不同渐变色：红/橙/紫/蓝/绿)
  - 洞察标题
  - 影响描述
  - 建议措施

**交互行为**
- 纯展示，无可点击交互
- 支持一键复制整条洞察内容

---

### 6.6 模块六：风险与热门区 (SectionRiskHotPosts)

#### 6.6.1 RiskAlertCard — 风险告警卡片

**视觉特征**
- 浅红色渐变背景 (`risk-card`)
- 标题旁脉冲红点 (持续动画)
- 红色主题标签

**AlertGrid (2x2 网格)**
- P0 告警：红色调迷你卡片 (`risk-mini`)
- P1 告警：琥珀色调迷你卡片 (`risk-mini-amber`)

**RiskSummaryFooter**
- 系统性风险判定结果
- 紧急处理建议
- 红色加粗关键词

**交互行为**
| 交互 | 行为 |
|------|------|
| 点击告警卡片 | 跳转到对应帖子详情 |
| 点击"标记已处理" | 调用 API 更新告警状态 |

#### 6.6.2 HotPostsCard — 热门帖子卡片

**HotPostList**
- TOP 8 热门帖子列表
- 每条：标题 (截断) + 分类/情绪 + 浏览量
- 浏览量 > 300 的条目浏览量数字显示红色

**交互行为**
| 交互 | 行为 |
|------|------|
| 点击帖子条目 | 跳转到帖子详情页 (`/posts/:id`) |

---

### 6.7 模块七：全局交互功能

#### 6.7.1 数据刷新机制

| 触发方式 | 行为 |
|----------|------|
| 页面加载 | 自动请求全量数据 |
| 手动刷新按钮 (F5) | 重新请求所有数据 |
| WebSocket 推送 | 收到 `data_refresh` 消息后静默更新图表 |
| 定时刷新 (可配置) | 默认每 5 分钟自动刷新 (通过 `setInterval`) |
| 日期选择变更 | 按新日期范围重新请求 |

#### 6.7.2 日期范围选择器

- 顶部导航栏 DateRangeChip 点击触发
- 弹出 DatePicker 组件
- 支持快捷选项：
  - 最近 7 天
  - 最近 30 天
  - 本月
  - 上个月
  - 自定义范围
- 选择后触发全部图表数据刷新

#### 6.7.3 数据导出功能

**导出帖子 (CSV/Excel)**
- 在帖子列表页提供"导出"按钮
- 点击弹出格式选择下拉菜单
- 导出当前筛选条件下的帖子数据
- CSV 格式：UTF-8 BOM 编码，逗号分隔
- Excel 格式：`.xlsx` 文件，包含格式化表头

**导出看板报告 (PDF)**
- 看板首页提供"导出报告"按钮
- 点击后调用后端生成 PDF
- PDF 包含当前页面所有图表和文字的静态快照
- 显示生成进度条，完成后自动下载

#### 6.7.4 响应式布局

| 断点 | 列数变化 |
|------|----------|
| ≥1280px (xl) | 12 列网格，完整布局 |
| 1024-1279px (lg) | 部分区域改为全宽 |
| 768-1023px (md) | 大部分区域全宽，导航折叠 |
| <768px (sm) | 单列布局，简化图表 |

#### 6.7.5 暗色模式

- 系统设置中可切换暗色模式
- 暗色模式变量覆盖：
  - 背景渐变：深色系
  - 玻璃效果：深色半透明
  - 文字颜色：浅色系
  - 图表配色自动切换
- 偏好存储在 localStorage

---

## 7. 按钮与交互行为详述

### 7.1 全局按钮清单

| 编号 | 按钮名称 | 位置 | 触发条件 | 行为描述 | API 调用 |
|------|----------|------|----------|----------|----------|
| B01 | 实时状态指示器 | 顶部导航 | 始终显示 | 纯展示，显示系统在线/离线状态 | 无 |
| B02 | 数据周期选择 | 顶部导航 | 点击 | 弹出日期范围选择器，选择后刷新全部数据 | 批量调用所有 dashboard API |
| B03 | 用户头像 | 顶部导航 | 点击 | 展开下拉菜单 (个人信息/管理/退出) | 无 |
| B04 | 退出登录 | 用户下拉菜单 | 点击 | 清除 token，跳转登录页 | POST /auth/logout |
| B05 | 导航链接 | 顶部导航 | 点击 | 切换路由到对应页面 | 无 |
| B06 | 移动端菜单 | 顶部导航 (sm) | 点击 | 展开/收起移动端导航菜单 | 无 |
| B07 | 手动刷新 | 页面右上角 | 点击 | 显示加载动画，重新请求当前页面全量数据 | 批量调用当前页面所需 API |
| B08 | 导出报告 | 看板首页 | 点击 | 生成 PDF 报告并下载 | GET /export/dashboard |
| B09 | 导出数据 | 帖子列表页 | 点击 | 弹出格式选择，下载 CSV/Excel | GET /export/posts |
| B10 | 暗色模式切换 | 用户下拉/设置 | 点击 | 切换亮色/暗色主题 | 无 (localStorage) |
| B11 | 图例项 | 折线图 | 点击 | 切换对应系列显示/隐藏 | 无 (ECharts 内置) |
| B12 | 异常标签 | 趋势图区域 | 点击 | 高亮对应系列，弹出详情 | 无 |
| B13 | 情绪扇区 | 环形图 | 点击 | 高亮选中扇区 | 无 (ECharts 内置) |
| B14 | 分类柱子 | 柱状图 | 点击 | 跳转帖子列表，预设分类筛选 | 路由跳转 |
| B15 | 优先级卡片 | 优先级区域 | 点击 | 跳转帖子列表，预设优先级筛选 | 路由跳转 |
| B16 | 根因聚类条目 | 根因分析区 | 点击 | 展开/收起详细分析 | 无 |
| B17 | 关键词标签 | 根因分析区 | 点击 | 跳转帖子列表，按关键词搜索 | 路由跳转 |
| B18 | 风险告警卡片 | 风险告警区 | 点击 | 跳转对应帖子详情 | 路由跳转 |
| B19 | 标记已处理 | 风险告警区 | 点击 | 调用 API 更新告警状态为 resolved | PUT /api/v1/admin/alerts/:id |
| B20 | 热门帖子条目 | 热门帖子区 | 点击 | 跳转帖子详情页 | 路由跳转 |
| B21 | 复制洞察 | 业务洞察区 | 点击 | 复制洞察内容到剪贴板，显示 toast 提示 | 无 |
| B22 | 登录按钮 | 登录页 | 点击 | 验证用户名密码，获取 token，跳转看板 | POST /auth/login |
| B23 | 帖子搜索 | 帖子列表页 | 输入+回车 | 按关键词搜索帖子 | GET /posts?keyword=xxx |
| B24 | 分类筛选 | 帖子列表页 | 点击下拉 | 按分类筛选帖子 | GET /posts?category=xxx |
| B25 | 优先级筛选 | 帖子列表页 | 点击下拉 | 按优先级筛选帖子 | GET /posts?priority=xxx |
| B26 | 情绪筛选 | 帖子列表页 | 点击下拉 | 按情绪筛选帖子 | GET /posts?sentiment=xxx |
| B27 | 时间排序 | 帖子列表页 | 点击表头 | 切换升序/降序排列 | GET /posts?sort=created_at&order=asc/desc |
| B28 | 分页控制 | 帖子列表页 | 点击页码 | 翻页加载数据 | GET /posts?page=N&page_size=M |

### 7.2 页面加载流程

```
1. 用户访问 /dashboard
2. 路由守卫检查 token
   ├── 无 token → 跳转 /login
   └── 有 token → 继续
3. DashboardView.vue mounted()
4. 并行请求所有 API:
   ├── GET /dashboard/summary
   ├── GET /dashboard/trend
   ├── GET /dashboard/sentiment
   ├── GET /dashboard/categories
   ├── GET /dashboard/hot-posts
   ├── GET /dashboard/root-cause
   ├── GET /dashboard/insights
   └── GET /dashboard/risk-alerts
5. 建立 WebSocket 连接
6. 渲染所有组件 + 初始化 ECharts 实例
7. 监听窗口 resize → 图表 resize
8. 组件卸载时销毁 ECharts 实例 + 断开 WebSocket
```

### 7.3 数据刷新流程

```
触发条件（任一）:
  - 手动点击刷新按钮
  - 定时器到期 (默认5分钟)
  - WebSocket 收到 data_refresh
  - 日期范围变更

流程:
1. 显示骨架屏/加载动画 (仅手动刷新时)
2. 重新请求当前视图所需 API
3. 更新 Pinia store 数据
4. 响应式更新 UI (图表通过 watch 自动 setOption)
5. 隐藏加载动画
6. 更新"最后刷新时间"显示
```

---

## 8. 图表配置详述

### 8.1 趋势折线图 (Line Chart)

```javascript
// 完整 ECharts 配置参考
{
  grid: {
    left: 36, right: 24, top: 36, bottom: 36
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.92)',
    borderColor: 'rgba(226,232,240,1)',
    borderWidth: 1,
    textStyle: { color: '#0f172a', fontSize: 12 },
    // 毛玻璃效果通过 extraCssText 实现
  },
  legend: {
    data: ['Bug / 系统异常', '功能咨询', 'RPA执行', 'Excel数据', '第三方系统'],
    textStyle: { color: '#475569', fontSize: 11 },
    top: 0, right: 0,
    itemGap: 14,
    icon: 'circle',
    itemWidth: 8, itemHeight: 8
  },
  xAxis: {
    type: 'category',
    data: [],  // 从 API 获取
    axisLine: { lineStyle: { color: 'rgba(148,163,184,0.25)' } },
    axisTick: { show: false },
    axisLabel: { color: '#94a3b8', fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)', type: 'dashed' } },
    axisLabel: { color: '#94a3b8', fontSize: 11 }
  },
  dataZoom: [
    {
      type: 'inside',     // 鼠标滚轮/双指缩放
      start: 0, end: 100
    },
    {
      type: 'slider',     // 底部滑块
      start: 0, end: 100,
      height: 20,
      bottom: 0
    }
  ],
  series: []  // 从 API 动态构建
}
```

### 8.2 情绪环形图 (Donut Chart)

```javascript
{
  tooltip: {
    trigger: 'item',
    formatter: '{b}<br/>{c} 条 ({d}%)'
  },
  series: [{
    type: 'pie',
    radius: ['62%', '88%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderColor: '#fff',
      borderWidth: 2,
      borderRadius: 6
    },
    label: { show: false },
    labelLine: { show: false },
    emphasis: {
      scale: true,
      scaleSize: 10,
      focus: 'self'
    },
    data: []  // 从 API 获取
  }],
  graphic: [
    // 中心主文字
    { type: 'text', left: 'center', top: '42%',
      style: { text: '', fill: '#0f172a', fontSize: 14, fontWeight: 600 } },
    // 中心百分比
    { type: 'text', left: 'center', top: '56%',
      style: { text: '', fill: '#dc2626', fontSize: 18, fontWeight: 700 } }
  ]
}
```

### 8.3 分类横向柱状图 (Horizontal Bar Chart)

```javascript
{
  grid: { left: 130, right: 60, top: 16, bottom: 16 },
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    formatter: (p) => {
      const o = p[0];
      return `${o.name}<br/>${o.value} 条 · ${(o.value/total*100).toFixed(1)}%`;
    }
  },
  xAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: 'rgba(148,163,184,0.25)', type: 'dashed' } }
  },
  yAxis: {
    type: 'category',
    data: [],  // 从 API 获取 (已排序)
    axisLine: { show: false },
    axisTick: { show: false }
  },
  series: [{
    type: 'bar',
    data: [],
    barWidth: 16,
    label: {
      show: true,
      position: 'right',
      formatter: (p) => `${p.value} · ${(p.value/total*100).toFixed(1)}%`
    }
  }]
}
```

### 8.4 图表通用特性

| 特性 | 说明 |
|------|------|
| 自适应 resize | 监听 `window.resize`，调用 `chart.resize()` |
| 毛玻璃 tooltip | `backdrop-filter: blur(20px)` |
| 动画 | 默认开启动画，`animationDuration: 800` |
| 无障碍 | 支持 `prefers-reduced-motion` 媒体查询关闭动画 |
| 暗色模式 | 通过 CSS 变量切换图表配色 |
| 响应式 | 不同屏幕尺寸下调整 grid 间距和字体大小 |

---

## 9. 后端实现步骤

### 9.1 项目初始化

```bash
# 步骤 1: 创建项目目录结构
mkdir bi-dashboard-backend
cd bi-dashboard-backend
mkdir -p app/{api,models,schemas,services,core,utils}
mkdir -p alembic/versions
mkdir -p tests

# 步骤 2: 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 步骤 3: 安装依赖
pip install fastapi uvicorn[standard] sqlalchemy asyncpg psycopg2
pip install alembic pydantic python-jose[cryptography] passlib[bcrypt]
pip install redis pandas openpyxl reportlab python-multipart
pip install apscheduler jinja2 aiofiles websockets
pip install scikit-learn jieba  # 用于语义聚类
```

### 9.2 项目文件结构

```
bi-dashboard-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理
│   ├── database.py                # 数据库连接与会话
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入 (认证/DB会话)
│   │   ├── auth.py                # 认证接口
│   │   ├── dashboard.py           # 看板数据接口
│   │   ├── posts.py               # 帖子 CRUD 接口
│   │   ├── export.py              # 数据导出接口
│   │   ├── admin.py               # 管理接口
│   │   └── websocket.py           # WebSocket 接口
│   ├── models/
│   │   ├── __init__.py
│   │   ├── post.py                # 帖子模型
│   │   ├── daily_summary.py       # 每日汇总模型
│   │   ├── root_cause.py          # 根因分析模型
│   │   ├── insight.py             # 业务洞察模型
│   │   ├── risk_alert.py          # 风险告警模型
│   │   └── user.py                # 用户模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── dashboard.py           # 看板响应 Schema
│   │   ├── post.py                # 帖子 Schema
│   │   ├── user.py                # 用户 Schema
│   │   └── common.py              # 通用 Schema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── dashboard_service.py   # 看板数据计算服务
│   │   ├── post_service.py        # 帖子服务
│   │   ├── analysis_service.py    # 分析服务 (聚类/情绪/异常)
│   │   ├── export_service.py      # 导出服务
│   │   ├── alert_service.py       # 告警服务
│   │   └── user_service.py        # 用户服务
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py            # JWT/密码处理
│   │   └── middleware.py           # 中间件 (CORS/日志)
│   └── utils/
│       ├── __init__.py
│       ├── cache.py               # Redis 缓存工具
│       └── date_utils.py          # 日期工具函数
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── tests/
│   ├── test_dashboard.py
│   ├── test_posts.py
│   └── test_auth.py
├── scripts/
│   ├── seed_data.py               # 种子数据脚本
│   └── run_scheduler.py           # 定时任务调度
├── requirements.txt
└── .env                           # 环境变量
```

### 9.3 实现步骤明细

#### 步骤 1: 项目骨架搭建
1. 初始化 FastAPI 应用 (`main.py`)
2. 配置 CORS 中间件
3. 配置数据库连接 (SQLAlchemy async)
4. 配置 Redis 连接
5. 配置环境变量 (.env)
6. 创建基础目录结构

#### 步骤 2: 数据模型定义
1. 定义所有 SQLAlchemy 模型 (7 张表)
2. 编写 Alembic 初始迁移脚本
3. 执行 `alembic upgrade head` 创建表
4. 编写 Pydantic Schema 类

#### 步骤 3: 认证系统
1. 实现密码哈希 (bcrypt)
2. 实现 JWT token 生成与验证
3. 实现登录/登出接口
4. 实现 `get_current_user` 依赖注入
5. 实现角色权限装饰器

#### 步骤 4: 看板数据 API
1. 实现 `GET /dashboard/summary` — 查询 daily_summary 表，计算健康度评分
2. 实现 `GET /dashboard/trend` — 查询 posts 表按日期和分类聚合
3. 实现 `GET /dashboard/sentiment` — 查询 posts 表按情绪聚合
4. 实现 `GET /dashboard/categories` — 查询 posts 表按分类聚合
5. 实现 `GET /dashboard/priority` — 查询 posts 表按优先级聚合
6. 实现 `GET /dashboard/hot-posts` — 按浏览量排序取 TOP N
7. 实现 `GET /dashboard/root-cause` — 查询 root_cause_analysis 表
8. 实现 `GET /dashboard/insights` — 查询 business_insights 表
9. 实现 `GET /dashboard/risk-alerts` — 查询 risk_alerts 表
10. 为以上接口添加 Redis 缓存

#### 步骤 5: 帖子管理 API
1. 实现 `GET /posts` — 分页、筛选、排序
2. 实现 `GET /posts/{id}` — 帖子详情
3. 实现 `POST /posts` — 新增帖子 (管理员/运营)
4. 实现 `PUT /posts/{id}` — 更新帖子
5. 实现 `DELETE /posts/{id}` — 删除帖子 (管理员)

#### 步骤 6: 数据分析服务
1. 实现健康度评分算法：
   ```
   健康度 = 100
   - (bug_ratio * 100) * 0.4        // Bug占比扣分权重 40%
   - (negative_ratio * 100) * 0.35  // 消极情绪扣分权重 35%
   - (p0_count * 5) * 0.15          // P0风险扣分权重 15%
   - (anomaly_count * 3) * 0.10     // 异常扣分权重 10%
   最低 0 分，最高 100 分
   ```
2. 实现异常检测算法：
   - 日环比变化 > 15% 标记为异常
   - Bug 类帖子 > 25/日 标记为异常
   - 消极情绪 > 40/日 标记为异常
3. 实现语义聚类分析：
   - 使用 jieba 分词
   - TF-IDF 特征提取
   - K-Means 聚类 (k=4)
   - 提取每类 TOP 关键词
4. 实现日汇总数据计算：
   - 每日凌晨 2:00 通过 APScheduler 自动执行
   - 从 posts 表聚合前一日数据写入 daily_summary

#### 步骤 7: 数据导出服务
1. 实现 CSV 导出：
   - 查询符合条件的帖子
   - 使用 Python `csv` 模块写入
   - StreamingResponse 返回文件流
2. 实现 Excel 导出：
   - 使用 openpyxl 生成 .xlsx
   - 格式化表头行
3. 实现 PDF 报告生成：
   - 使用 reportlab 或 Jinja2 + WeasyPrint
   - 包含图表静态快照和所有分析文字

#### 步骤 8: WebSocket 实时推送
1. 实现 WebSocket 连接管理
2. 实现心跳检测 (每 30s)
3. 定时检查新告警 → 推送给所有连接的客户端
4. 数据刷新通知广播

#### 步骤 9: 管理接口
1. 用户 CRUD
2. 系统配置 CRUD
3. 手动触发数据刷新
4. 告警状态更新

#### 步骤 10: 种子数据
1. 编写 `seed_data.py` 脚本
2. 生成 demo 中的 314 条模拟数据
3. 生成 6 天的每日汇总数据
4. 生成根因分析数据
5. 生成业务洞察数据
6. 生成风险告警数据
7. 创建默认管理员账号 (admin/admin123)

#### 步骤 11: 测试
1. 编写 API 单元测试 (pytest + httpx)
2. 编写服务层单元测试
3. 编写集成测试
4. 测试覆盖率 > 80%

---

## 10. 前端实现步骤

### 10.1 项目初始化

```bash
# 步骤 1: 创建 Vue 3 项目
npm create vite@latest bi-dashboard-frontend -- --template vue
cd bi-dashboard-frontend

# 步骤 2: 安装依赖
npm install vue-router@4 pinia axios echarts dayjs
npm install -D tailwindcss @tailwindcss/vite @vueuse/core
npm install -D @types/node sass

# 步骤 3: 初始化 Tailwind CSS
npx tailwindcss init
```

### 10.2 项目文件结构

```
bi-dashboard-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.js                     # 应用入口
│   ├── App.vue                     # 根组件
│   ├── style.css                   # 全局样式 + Tailwind
│   ├── router/
│   │   └── index.js                # 路由配置
│   ├── stores/
│   │   ├── index.js                # Pinia 实例
│   │   ├── dashboard.js            # 看板数据 Store
│   │   ├── auth.js                 # 认证 Store
│   │   └── app.js                  # 应用全局 Store (主题等)
│   ├── api/
│   │   ├── index.js                # Axios 实例配置
│   │   ├── dashboard.js            # 看板 API 封装
│   │   ├── posts.js                # 帖子 API 封装
│   │   ├── auth.js                 # 认证 API 封装
│   │   └── admin.js                # 管理 API 封装
│   ├── composables/
│   │   ├── useChart.js             # ECharts 组合式函数
│   │   ├── useWebSocket.js         # WebSocket 组合式函数
│   │   ├── usePolling.js           # 轮询组合式函数
│   │   └── useExport.js            # 导出组合式函数
│   ├── components/
│   │   ├── layout/
│   │   │   ├── TopNavBar.vue
│   │   │   ├── PageHeader.vue
│   │   │   └── PageFooter.vue
│   │   ├── dashboard/
│   │   │   ├── HealthScoreCard.vue
│   │   │   ├── ScoreRing.vue
│   │   │   ├── MiniStatCards.vue
│   │   │   ├── TodayVsYesterdayCard.vue
│   │   │   ├── P0RiskCard.vue
│   │   │   ├── TrendChartCard.vue
│   │   │   ├── SentimentChartCard.vue
│   │   │   ├── CategoryChartCard.vue
│   │   │   ├── PriorityDistributionCard.vue
│   │   │   ├── RootCauseCard.vue
│   │   │   ├── BusinessInsightCard.vue
│   │   │   ├── RiskAlertCard.vue
│   │   │   └── HotPostsCard.vue
│   │   ├── charts/
│   │   │   ├── LineChart.vue
│   │   │   ├── DonutChart.vue
│   │   │   └── HorizontalBarChart.vue
│   │   └── common/
│   │       ├── Chip.vue
│   │       ├── Badge.vue
│   │       ├── ProgressBar.vue
│   │       ├── MiniCard.vue
│   │       ├── SkeletonLoader.vue
│   │       ├── DateRangePicker.vue
│   │       ├── DropdownMenu.vue
│   │       ├── Toast.vue
│   │       └── EmptyState.vue
│   └── views/
│       ├── LoginView.vue
│       ├── DashboardView.vue
│       ├── TrendAnalysisView.vue
│       ├── IssueAnalysisView.vue
│       ├── RiskCenterView.vue
│       ├── PostListView.vue
│       ├── PostDetailView.vue
│       ├── AdminPanelView.vue
│       └── NotFoundView.vue
├── index.html
├── vite.config.js
├── tailwind.config.js
├── package.json
└── .env
```

### 10.3 实现步骤明细

#### 步骤 1: 项目骨架搭建
1. 初始化 Vite + Vue 3 项目
2. 配置 Tailwind CSS
3. 创建目录结构
4. 配置路径别名 (`@` → `src/`)
5. 配置代理 (开发环境 API 代理到后端)
6. 创建基础布局组件

#### 步骤 2: 全局样式实现
1. 定义 CSS 变量 (`:root` 亮色 / `.dark` 暗色)
2. 实现毛玻璃效果类 (`.glass`)
3. 实现环境光球动画 (`.ambient-orb`)
4. 实现脉冲动画 (`.pulse-dot`)
5. 实现镜面高光效果 (`.specular`)
6. 实现进度条样式 (`.bar-track` / `.bar-fill`)
7. 实现徽章样式 (`.badge-p0/p1/p2`)
8. 实现标签样式 (`.chip` / `.chip-danger/warn/ok/info`)
9. 实现迷你卡片样式 (`.mini-card`)
10. 实现自定义滚动条样式
11. 实现响应式网格布局
12. 添加 `prefers-reduced-motion` 媒体查询

#### 步骤 3: 路由与状态管理
1. 配置 Vue Router (8 个路由 + 404)
2. 实现路由守卫 (认证检查 + 角色检查)
3. 创建 Pinia stores：
   - `authStore`: 用户登录状态、token、角色
   - `dashboardStore`: 看板所有数据
   - `appStore`: 主题、加载状态、全局配置

#### 步骤 4: API 层封装
1. 创建 Axios 实例：
   - baseURL 配置
   - 请求拦截器 (添加 token)
   - 响应拦截器 (处理 401 跳转登录)
   - 错误统一处理
2. 封装所有 API 函数 (对应后端 15+ 个接口)
3. 添加请求取消功能 (重复请求自动取消上一次)

#### 步骤 5: 通用组件开发
1. **Chip.vue** — 标签组件
   - Props: `type` (danger/warn/ok/info/default), `label`
   - 颜色自动映射
2. **Badge.vue** — 徽章组件
   - Props: `priority` (P0/P1/P2), `label`
   - P0 红橙渐变、P1 橙黄渐变、P2 蓝紫渐变
3. **ProgressBar.vue** — 进度条组件
   - Props: `percent`, `color`
   - 宽度动画过渡
4. **MiniCard.vue** — 迷你卡片组件
   - 悬停效果、插槽支持
5. **SkeletonLoader.vue** — 骨架屏
   - 模拟卡片布局的灰色占位块
   - 闪光动画
6. **DateRangePicker.vue** — 日期范围选择器
   - 快捷选项
   - 自定义日期范围
7. **DropdownMenu.vue** — 下拉菜单
8. **Toast.vue** — 消息提示
   - 成功/错误/警告/信息四种类型
9. **EmptyState.vue** — 空状态占位

#### 步骤 6: 图表组件开发

**useChart.js (组合式函数)**
```javascript
// 核心逻辑
export function useChart(options = {}) {
  const chartRef = ref(null)
  let chartInstance = null

  const initChart = () => {
    if (chartRef.value) {
      chartInstance = echarts.init(chartRef.value)
    }
  }

  const setOption = (option) => {
    chartInstance?.setOption(option, { notMerge: true })
  }

  const resize = () => {
    chartInstance?.resize()
  }

  // 自动管理生命周期
  onMounted(() => {
    initChart()
    window.addEventListener('resize', resize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    chartInstance?.dispose()
  })

  return { chartRef, setOption, resize, getInstance: () => chartInstance }
}
```

**LineChart.vue** — 折线图
- Props: `seriesData`, `xAxisData`, `anomalyTags`
- 从 props 构建 ECharts option
- watch props 变化自动更新

**DonutChart.vue** — 环形图
- Props: `data`, `centerText`
- 支持扇区点击事件 emit

**HorizontalBarChart.vue** — 横向柱状图
- Props: `categories`, `total`
- 支持柱子点击事件 emit (用于路由跳转)

#### 步骤 7: 看板卡片组件开发

按组件树从上到下实现每个卡片组件。每个卡片组件：
1. 定义 Props 接口
2. 定义 Emits 接口
3. 实现模板 (复用通用组件)
4. 实现样式 (glass/mini-card 等)
5. 处理加载/空/错误状态

#### 步骤 8: 页面视图开发

**DashboardView.vue** — 看板首页
1. 引入 14 个卡片组件
2. 使用 12 列网格布局
3. `onMounted` 时 dispatch dashboardStore 加载数据
4. 响应式网格 (5 个 section，每个含 2-3 卡片)
5. 建立 WebSocket 连接接收实时更新

**LoginView.vue** — 登录页
- 用户名/密码表单
- 登录按钮 + 回车提交
- 错误提示

**PostListView.vue** — 帖子列表页
- 搜索栏 + 筛选器 (分类/优先级/情绪/日期)
- 数据表格 (排序/分页)
- 导出按钮
- 点击行跳转详情

**PostDetailView.vue** — 帖子详情页
- 帖子完整信息展示
- 返回按钮
- 编辑/删除按钮 (管理员)

**AdminPanelView.vue** — 管理页
- Tab 切换：用户管理 / 系统配置 / 数据管理
- 用户 CRUD 表格
- 配置表单
- 手动刷新数据按钮

**TrendAnalysisView.vue** — 趋势分析独立页
- 大尺寸折线图
- 更多筛选维度
- 对比分析功能

**IssueAnalysisView.vue** — 问题分析独立页
- 分类详细分析
- 根因深入探索

**RiskCenterView.vue** — 风险中心独立页
- 全量告警列表
- 告警处理工作流

#### 步骤 9: 响应式适配
1. 使用 Tailwind 响应式前缀 (`md:` / `lg:` / `xl:`)
2. 移动端导航折叠为汉堡菜单
3. 小屏图表简化 (隐藏图例、调整 grid)
4. 小屏卡片全宽显示

#### 步骤 10: 暗色模式
1. CSS 变量系统
2. `appStore` 管理主题状态
3. 切换时在 `<html>` 上添加/移除 `.dark` 类
4. localStorage 持久化主题偏好
5. ECharts 配色随主题切换

#### 步骤 11: WebSocket 集成
```javascript
// useWebSocket.js
export function useWebSocket() {
  const ws = ref(null)
  const isConnected = ref(false)

  const connect = (token) => {
    ws.value = new WebSocket(`ws://localhost:8000/api/v1/ws/dashboard?token=${token}`)
    ws.value.onopen = () => { isConnected.value = true }
    ws.value.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      handleMessage(msg)  // 根据 type 更新对应 store
    }
    ws.value.onclose = () => { isConnected.value = false; /* 自动重连 */ }
  }

  const disconnect = () => { ws.value?.close() }

  return { isConnected, connect, disconnect }
}
```

#### 步骤 12: 性能优化
1. 路由懒加载 (`() => import(...)`)
2. 图表组件使用 `v-memo` 避免不必要重渲染
3. 大数据列表使用虚拟滚动
4. 图表按需初始化 (进入视口才渲染)
5. API 请求去重与缓存

---

## 11. 部署与运维

### 11.1 开发环境

```bash
# 后端
cd bi-dashboard-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd bi-dashboard-frontend
npm run dev  # 默认 http://localhost:5173
```

### 11.2 生产环境

```bash
# 后端 — 使用 Gunicorn + Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 前端 — 构建 + Nginx
npm run build
# 将 dist/ 部署到 Nginx
```

### 11.3 Docker 部署

```dockerfile
# 后端 Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 前端 Dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

### 11.4 docker-compose.yml

```yaml
version: '3.8'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: bi_dashboard
      POSTGRES_USER: bi_user
      POSTGRES_PASSWORD: bi_password
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./bi-dashboard-backend
    environment:
      DATABASE_URL: postgresql+asyncpg://bi_user:bi_password@db:5432/bi_dashboard
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your-secret-key-here
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"

  frontend:
    build: ./bi-dashboard-frontend
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  pgdata:
```

### 11.5 监控与告警

| 监控项 | 工具 | 阈值 |
|--------|------|------|
| API 响应时间 | Prometheus + Grafana | P95 > 2s 告警 |
| 数据库连接池 | SQLAlchemy 事件 | 使用率 > 80% 告警 |
| Redis 内存 | Redis INFO | 使用率 > 80% 告警 |
| 错误率 | Sentry | 5xx > 1% 告警 |
| WebSocket 断连 | 客户端心跳 | 断连 > 30s 告警 |

---

## 附录 A: 健康度评分算法详细说明

```
输入参数:
  - bug_ratio: Bug类帖子占比 (0-1)
  - negative_ratio: 消极情绪占比 (0-1)
  - p0_count: P0 级别问题数量
  - anomaly_count: 异常信号数量

计算过程:
  score = 100
  score -= min(bug_ratio * 100, 40) * (bug_ratio > 0.15 ? 1.0 : 0.5)
  score -= min(negative_ratio * 100, 35) * (negative_ratio > 0.3 ? 1.0 : 0.5)
  score -= min(p0_count, 10) * 1.5
  score -= min(anomaly_count, 10) * 1.0
  score = max(0, min(100, round(score)))

健康状态判定:
  score >= 80: "healthy"     (健康 - 绿色)
  score >= 60: "warning"     (警告 - 橙色)
  score < 60:  "high_risk"   (高风险 - 红色)
```

## 附录 B: 异常检测规则

| 规则 ID | 条件 | 严重级别 | 标签 |
|---------|------|----------|------|
| A01 | 日环比变化 > 15% | warning | "突增/骤降" |
| A02 | Bug 类 > 25条/日 | danger | "Bug 爆发" |
| A03 | 消极情绪 > 40条/日 | danger | "情绪恶化" |
| A04 | P0 数量 > 3 | danger | "P0 堆积" |
| A05 | 连续3天趋势上升 | warning | "持续恶化" |
| A06 | 单日帖子量 > 100 | warning | "流量异常" |

## 附录 C: 颜色系统

| 变量名 | 色值 | 用途 |
|--------|------|------|
| `--c-danger` | #ef4444 | 危险/错误/消极 |
| `--c-danger-soft` | #fee2e2 | 危险浅色背景 |
| `--c-warn` | #f59e0b | 警告/注意 |
| `--c-warn-soft` | #fef3c7 | 警告浅色背景 |
| `--c-ok` | #10b981 | 成功/积极 |
| `--c-ok-soft` | #d1fae5 | 成功浅色背景 |
| `--c-info` | #3b82f6 | 信息/中性 |
| `--c-info-soft` | #dbeafe | 信息浅色背景 |
| `--c-purple` | #8b5cf6 | 紫色强调 |
| `--t-primary` | #0f172a | 主文字色 |
| `--t-secondary` | #475569 | 次要文字色 |
| `--t-tertiary` | #94a3b8 | 辅助文字色 |

---

> **文档结束** — 本文档涵盖 BI 看板系统的全部功能模块、按钮交互、数据结构、API 接口、图表配置以及前后端实现步骤。开发时可按照第 9 节和第 10 节的步骤顺序依次实施。
