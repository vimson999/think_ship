toutiao-matrix/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── contents.py
│   │   │   ├── accounts.py
│   │   │   └── analytics.py
│   │   └── dependencies.py
│   │
│   ├── core/                   # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全相关
│   │   └── exceptions.py       # 自定义异常
│   │
│   ├── domain/                 # 业务领域
│   │   ├── __init__.py
│   │   ├── content/
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # 领域模型
│   │   │   ├── services.py     # 业务逻辑
│   │   │   └── repositories.py # 数据访问
│   │   ├── account/
│   │   └── analytics/
│   │
│   ├── infrastructure/         # 基础设施
│   │   ├── __init__.py
│   │   ├── database.py         # 数据库连接
│   │   ├── cache.py            # Redis连接
│   │   ├── ai_client.py        # AI服务客户端
│   │   └── storage.py          # 文件存储
│   │
│   ├── tasks/                  # 异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py       # Celery配置
│   │   ├── collectors.py       # 采集任务
│   │   ├── generators.py       # 生成任务
│   │   └── publishers.py       # 发布任务
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── hash.py             # 内容去重
│       ├── rate_limiter.py     # 速率限制
│       └── validators.py       # 数据验证
│
├── migrations/                 # 数据库迁移
├── tests/                      # 测试
├── scripts/                    # 运维脚本
├── docker/                     # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
├── requirements.txt
├── Makefile                    # 常用命令
└── README.md


┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                       │
│  ├── API Server (FastAPI)                                    │
│  ├── Task Worker (Celery)                                    │
│  └── Admin Dashboard                                         │
├─────────────────────────────────────────────────────────────┤
│                    业务领域层 (Domain)                        │
│  ├── 内容流水线 (Content Pipeline)                            │
│  │   ├── 采集器 (Collector)                                  │
│  │   ├── 处理器 (Processor)                                  │
│  │   └── 发布器 (Publisher)                                  │
│  ├── 账号管理 (Account Management)                           │
│  └── 分析引擎 (Analytics Engine)                             │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)                 │
│  ├── 数据存储 (PostgreSQL + Redis)                           │
│  ├── 消息队列 (RabbitMQ/Redis)                               │
│  └── 对象存储 (MinIO/S3)                                     │
└─────────────────────────────────────────────────────────────┘