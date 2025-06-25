# 核心框架
fastapi==0.109.0
uvicorn[standard]==0.25.0
pydantic==2.5.3
pydantic-settings==2.1.0

# 异步任务
celery[redis]==5.3.4
flower==2.0.1  # Celery监控

# 数据库
asyncpg==0.29.0  # 异步PostgreSQL
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
redis[hiredis]==5.0.1  # 使用hiredis提升性能

# AI服务
openai==1.6.1
anthropic==0.8.1
langchain==0.0.352
langchain-community==0.0.10

# 爬虫
httpx==0.26.0  # 支持HTTP/2
selectolite==0.5.0  # 轻量级浏览器自动化
beautifulsoup4==4.12.3

# 图像处理
pillow==10.2.0
aiofiles==23.2.1

# 数据处理
pandas==2.1.4
numpy==1.26.3
jieba==0.42.1

# 监控和日志
loguru==0.7.2
sentry-sdk[fastapi]==1.39.2
prometheus-fastapi-instrumentator==6.1.0

# 安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 开发和测试
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==23.12.1
ruff==0.1.11  # 更快的linter
pre-commit==3.6.0

# 部署
gunicorn==21.2.0
python-dotenv==1.0.0

# 工具
tenacity==8.2.3
python-dateutil==2.8.2
orjson==3.9.10  # 更快的JSON