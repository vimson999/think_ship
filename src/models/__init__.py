"""
文件名: __init__.py
描述: 数据模型模块包初始化文件

本模块包含系统的所有数据模型定义：
1. 基础模型类
2. 用户相关模型
3. 内容相关模型
4. 账号相关模型
5. 系统管理模型

依赖模块:
   - sqlalchemy: ORM框架

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

# 基础模型
from src.models.base import Base

# 用户相关模型
from src.models.user import (
    User, Role, UserSession, UserStatus, RoleType, user_roles
)

# 账号管理模型
from src.models.account import (
    Account, AccountHealth, PlatformType, AccountStatus, 
    AccountCategory, RiskLevel
)

# 内容相关模型
from src.models.content import (
    HotTopic, Content, PublishRecord, ContentMetrics, 
    ContentTemplate, ContentStateTransition,
    ContentSource, ContentCategory, ContentStatus, 
    PublishStatus, TemplateType
)

# 系统管理模型
from src.models.system import (
    TaskQueue, SystemConfig, OperationLog, CrawlerRule,
    TaskType, TaskStatus, LogLevel, ConfigType
)

# 导出所有模型类
__all__ = [
    # 基础
    "Base",
    
    # 用户模型
    "User", "Role", "UserSession", "UserStatus", "RoleType", "user_roles",
    
    # 账号模型
    "Account", "AccountHealth", "PlatformType", "AccountStatus", 
    "AccountCategory", "RiskLevel",
    
    # 内容模型
    "HotTopic", "Content", "PublishRecord", "ContentMetrics", 
    "ContentTemplate", "ContentStateTransition",
    "ContentSource", "ContentCategory", "ContentStatus", 
    "PublishStatus", "TemplateType",
    
    # 系统模型
    "TaskQueue", "SystemConfig", "OperationLog", "CrawlerRule",
    "TaskType", "TaskStatus", "LogLevel", "ConfigType",
]