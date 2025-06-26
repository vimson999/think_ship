# Think Ship

## 简介

一个基于FastAPI的后端应用系统。

## 环境要求

- Python 3.12+
- PostgreSQL
- Redis

## 安装

```bash
# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

## 运行

```bash
# 启动应用
uvicorn src.main:app --reload
```

## 许可证

MIT License