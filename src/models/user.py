"""
文件名: user.py
描述: 用户管理数据模型

本模块定义用户相关的数据模型：
1. User - 系统用户模型
2. UserRole - 用户角色模型  
3. UserSession - 用户会话模型

依赖模块:
   - sqlalchemy: ORM框架
   - passlib: 密码加密

使用示例:
   >>> user = User(username="admin", email="admin@example.com")
   >>> user.set_password("password123")
   >>> user.save(db)

注意事项:
   - 密码使用bcrypt加密存储
   - 支持多角色权限管理
   - 记录用户操作日志

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from src.models.base import Base

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class RoleType(str, Enum):
    """角色类型枚举"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now),
)


class User(Base):
    """
    用户模型
    
    系统用户基本信息和认证数据
    """
    __tablename__ = "users"
    __table_args__ = {'comment': '系统用户表'}
    
    # 基本信息
    username = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="用户名"
    )
    email = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="邮箱地址"
    )
    full_name = Column(
        String(100), 
        nullable=True,
        comment="真实姓名"
    )
    
    # 认证信息
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="密码哈希"
    )
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="是否激活"
    )
    status = Column(
        String(20), 
        default=UserStatus.ACTIVE,
        nullable=False,
        comment="用户状态"
    )
    
    # 权限控制
    is_superuser = Column(
        Boolean, 
        default=False,
        comment="是否超级用户"
    )
    
    # 时间记录
    last_login_at = Column(
        DateTime, 
        nullable=True,
        comment="最后登录时间"
    )
    password_changed_at = Column(
        DateTime, 
        default=datetime.now,
        comment="密码修改时间"
    )
    
    # 附加信息
    avatar_url = Column(
        String(500),
        nullable=True,
        comment="头像URL"
    )
    phone = Column(
        String(20),
        nullable=True,
        comment="手机号码"
    )
    department = Column(
        String(100),
        nullable=True,
        comment="部门"
    )
    
    # JSON字段
    preferences = Column(
        JSONB,
        default=dict,
        comment="用户偏好设置"
    )
    extra_data = Column(
        JSONB,
        default=dict,
        comment="扩展元数据"
    )
    
    # 关系定义
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="select"
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def set_password(self, password: str) -> None:
        """
        设置用户密码
        
        Args:
            password: 明文密码
        """
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = datetime.now()
    
    def verify_password(self, password: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            
        Returns:
            bool: 密码是否正确
        """
        return pwd_context.verify(password, self.password_hash)
    
    def need_password_change(self, days: int = 90) -> bool:
        """
        检查是否需要修改密码
        
        Args:
            days: 密码有效期天数
            
        Returns:
            bool: 是否需要修改密码
        """
        if not self.password_changed_at:
            return True
        
        expire_date = self.password_changed_at + timedelta(days=days)
        return datetime.now() > expire_date
    
    def has_role(self, role_name: str) -> bool:
        """
        检查用户是否有指定角色
        
        Args:
            role_name: 角色名称
            
        Returns:
            bool: 是否有该角色
        """
        return any(role.name == role_name for role in self.roles)
    
    def get_permissions(self) -> List[str]:
        """
        获取用户所有权限
        
        Returns:
            List[str]: 权限列表
        """
        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)
        return list(permissions)
    
    def update_last_login(self) -> None:
        """更新最后登录时间"""
        self.last_login_at = datetime.now()
    
    def to_dict(self, exclude_fields: list = None) -> dict:
        """
        转换为字典，排除敏感信息
        
        Args:
            exclude_fields: 要排除的字段
            
        Returns:
            dict: 用户信息字典
        """
        exclude_fields = exclude_fields or ['password_hash']
        exclude_fields.extend(['password_hash'])  # 确保密码不被导出
        
        result = super().to_dict(exclude_fields)
        
        # 添加角色信息
        result['roles'] = [role.name for role in self.roles]
        
        return result
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Role(Base):
    """
    角色模型
    
    定义系统中的用户角色和权限
    """
    __tablename__ = "roles"
    __table_args__ = {'comment': '用户角色表'}
    
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="角色名称"
    )
    display_name = Column(
        String(100),
        nullable=False,
        comment="显示名称"
    )
    description = Column(
        Text,
        nullable=True,
        comment="角色描述"
    )
    
    # 权限列表（JSON数组）
    permissions = Column(
        JSONB,
        default=list,
        comment="权限列表"
    )
    
    # 状态
    is_active = Column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # 关系定义
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )
    
    def add_permission(self, permission: str) -> None:
        """
        添加权限
        
        Args:
            permission: 权限名称
        """
        if self.permissions is None:
            self.permissions = []
        
        if permission not in self.permissions:
            self.permissions = list(self.permissions) + [permission]
    
    def remove_permission(self, permission: str) -> None:
        """
        移除权限
        
        Args:
            permission: 权限名称
        """
        if self.permissions and permission in self.permissions:
            permissions_list = list(self.permissions)
            permissions_list.remove(permission)
            self.permissions = permissions_list
    
    def has_permission(self, permission: str) -> bool:
        """
        检查是否有指定权限
        
        Args:
            permission: 权限名称
            
        Returns:
            bool: 是否有该权限
        """
        return self.permissions and permission in self.permissions
    
    def __repr__(self):
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"


class UserSession(Base):
    """
    用户会话模型
    
    记录用户登录会话信息
    """
    __tablename__ = "user_sessions"
    __table_args__ = {'comment': '用户会话表'}
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment="用户ID"
    )
    
    # 会话信息
    session_token = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="会话令牌"
    )
    refresh_token = Column(
        String(255),
        unique=True,
        nullable=True,
        comment="刷新令牌"
    )
    
    # 设备信息
    device_id = Column(
        String(255),
        nullable=True,
        comment="设备ID"
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="用户代理"
    )
    ip_address = Column(
        String(45),  # 支持IPv6
        nullable=True,
        comment="IP地址"
    )
    
    # 时间信息
    login_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="登录时间"
    )
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="过期时间"
    )
    last_activity_at = Column(
        DateTime,
        default=datetime.now,
        comment="最后活动时间"
    )
    
    # 状态
    is_active = Column(
        Boolean,
        default=True,
        comment="是否活跃"
    )
    
    # 关系定义
    user = relationship("User", back_populates="sessions")
    
    def is_expired(self) -> bool:
        """
        检查会话是否过期
        
        Returns:
            bool: 是否过期
        """
        return datetime.now() > self.expires_at
    
    def extend_session(self, hours: int = 24) -> None:
        """
        延长会话时间
        
        Args:
            hours: 延长的小时数
        """
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.last_activity_at = datetime.now()
    
    def revoke(self) -> None:
        """撤销会话"""
        self.is_active = False
    
    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', ip='{self.ip_address}')>"


# 导出所有模型
__all__ = ["User", "Role", "UserSession", "UserStatus", "RoleType", "user_roles"]