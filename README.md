# 头条矩阵系统 (Think Ship)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目简介

头条矩阵系统是一个智能内容生产与发布平台，通过自动化技术实现热点内容的采集、分析、生成和多账号矩阵发布，最终达到内容变现的目标。

### 核心功能

- 🔍 **智能热点采集**：自动采集微博、知乎、抖音等平台热点内容
- 🤖 **AI内容生成**：基于大模型生成高质量原创内容
- 📝 **智能内容审核**：自动化内容审核与人工审核工作台
- 🎯 **矩阵账号管理**：智能管理多平台账号健康度与发布策略
- ⏰ **智能发布调度**：基于数据分析优化发布时间和频率
- 📊 **效果数据分析**：实时监控发布效果与收益分析

### 技术架构

- **后端框架**：FastAPI + Uvicorn
- **任务队列**：Celery + Redis
- **数据库**：PostgreSQL + Redis
- **AI服务**：OpenAI + Anthropic + 国产大模型
- **爬虫框架**：httpx + BeautifulSoup4
- **监控日志**：Loguru + Prometheus + Grafana

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 13+
- Redis 6+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/think_ship.git
cd think_ship
```

2. **创建虚拟环境**
```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
# 使用清华镜像加速
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

4. **环境配置**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和API密钥
```

5. **数据库初始化**
```bash
# 创建数据库
createdb think_ship

# 运行数据库迁移
alembic upgrade head
```

6. **启动服务**
```bash
# 启动API服务
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 启动Celery Worker
celery -A src.tasks.celery_app worker --loglevel=info

# 启动Celery Flower监控
celery -A src.tasks.celery_app flower --port=5555
```

### 访问地址

- **API文档**：http://localhost:8000/docs
- **管理后台**：http://localhost:8000/admin
- **Celery监控**：http://localhost:5555

## 项目结构

```
think_ship/
├── src/                    # 源代码目录
│   ├── api/               # API接口
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── tasks/             # 异步任务
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── deploy/                # 部署脚本
├── docs/                  # 项目文档
├── logs/                  # 日志文件
│   ├── app/              # 应用日志
│   ├── error/            # 错误日志
│   ├── access/           # 访问日志
│   └── task/             # 任务日志
├── rules/                 # 开发规则文档
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量模板
└── README.md             # 项目说明
```

## 开发指南

### 代码规范

- 使用 Python 3.12
- 遵循 PEP 8 代码风格
- 使用 Black 进行代码格式化
- 使用 Ruff 进行代码质量检查
- 使用 MyPy 进行类型检查

### 测试

```bash
# 运行单元测试
pytest tests/ -v

# 生成测试覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 代码质量检查

```bash
# 代码格式化
black .

# 代码质量检查
ruff check .

# 类型检查
mypy src/
```

### 提交规范

每次提交前请确保：

- [ ] 代码已经过本地测试，确保无bug
- [ ] 添加了必要的注释和文档
- [ ] 通过了所有代码质量检查
- [ ] 更新了相关文档
- [ ] 没有硬编码的敏感信息

## 部署说明

### Docker部署

```bash
# 构建镜像
docker build -t think_ship .

# 启动服务
docker-compose up -d
```

### 生产环境

详细部署说明请参考 [deploy/README.md](deploy/README.md)

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目使用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页：https://github.com/your-username/think_ship
- 问题反馈：https://github.com/your-username/think_ship/issues
- 邮箱：your-email@example.com

## 致谢

感谢所有为本项目做出贡献的开发者和以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Celery](https://docs.celeryq.dev/) - 分布式任务队列
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包
- [OpenAI](https://openai.com/) - AI服务提供商