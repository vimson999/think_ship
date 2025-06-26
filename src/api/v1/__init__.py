"""
文件名: __init__.py
描述: API v1版本路由总入口

本模块负责注册和管理API v1版本的所有路由：
1. 热点内容相关API
2. 内容生成相关API
3. 账号管理相关API
4. 发布管理相关API
5. 数据分析相关API
6. 系统管理相关API

依赖模块:
   - fastapi: API路由框架

使用示例:
   >>> from src.api.v1 import api_router
   >>> app.include_router(api_router, prefix="/api/v1")

注意事项:
   - 所有API都应该包含适当的错误处理
   - 接口应该遵循RESTful设计原则
   - 需要添加适当的权限验证

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

from fastapi import APIRouter

from src.api.v1.endpoints import (
    health,
    contents,
    accounts,
    analytics,
    auth,
)

# 创建API v1路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(auth.router, prefix="/auth", tags=["认证授权"])
api_router.include_router(contents.router, prefix="/contents", tags=["内容管理"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["账号管理"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])

# 导出路由器
__all__ = ["api_router"]