"""
文件名: base.py
描述: 数据模型基类定义

本模块定义数据库模型的基础类和公共字段：
1. 基础模型类Base
2. 公共字段定义（id、创建时间、更新时间等）
3. 数据库会话管理
4. 模型基础方法

依赖模块:
   - sqlalchemy: ORM框架
   - uuid: 唯一标识符生成
   - datetime: 时间处理

使用示例:
   >>> from src.models.base import Base
   >>> class User(Base):
   ...     __tablename__ = "users"
   ...     name = Column(String(100))

注意事项:
   - 所有模型都应该继承Base类
   - 主键使用UUID类型
   - 自动管理创建和更新时间

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session


@as_declarative()
class Base:
    """
    数据库模型基类
    
    为所有数据库模型提供公共字段和方法
    """
    
    # 主键：使用UUID作为主键，提供更好的分布式支持
    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="主键ID"
    )
    
    # 创建时间：记录创建时间，使用数据库时间
    created_at: datetime = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        comment="创建时间"
    )
    
    # 更新时间：记录最后更新时间，自动更新
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间"
    )
    
    # 创建者ID：记录创建该记录的用户ID
    created_by: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    # 更新者ID：记录最后更新该记录的用户ID
    updated_by: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID"
    )
    
    # 备注字段：用于存储额外信息
    remark: str = Column(
        String(500),
        nullable=True,
        comment="备注信息"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        自动生成表名
        
        将类名转换为下划线格式作为表名
        例如：UserAccount -> user_account
        """
        import re
        # 将驼峰命名转换为下划线命名
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def to_dict(self, exclude_fields: list = None) -> dict:
        """
        将模型实例转换为字典
        
        Args:
            exclude_fields: 需要排除的字段列表
            
        Returns:
            dict: 模型数据字典
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        for column in self.__table__.columns:
            field_name = column.name
            if field_name not in exclude_fields:
                value = getattr(self, field_name)
                
                # 处理特殊类型的值
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[field_name] = str(value)
                else:
                    result[field_name] = value
                    
        return result
    
    def update_from_dict(self, data: dict, exclude_fields: list = None) -> None:
        """
        从字典更新模型实例
        
        Args:
            data: 要更新的数据字典
            exclude_fields: 需要排除的字段列表
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'created_by']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
    
    def save(self, db: Session, commit: bool = True) -> None:
        """
        保存模型实例到数据库
        
        Args:
            db: 数据库会话
            commit: 是否立即提交事务
        """
        db.add(self)
        if commit:
            db.commit()
            db.refresh(self)
    
    def delete(self, db: Session, commit: bool = True) -> None:
        """
        从数据库删除模型实例
        
        Args:
            db: 数据库会话
            commit: 是否立即提交事务
        """
        db.delete(self)
        if commit:
            db.commit()
    
    @classmethod
    def get_by_id(cls, db: Session, record_id: uuid.UUID):
        """
        根据ID获取记录
        
        Args:
            db: 数据库会话
            record_id: 记录ID
            
        Returns:
            模型实例或None
        """
        return db.query(cls).filter(cls.id == record_id).first()
    
    @classmethod
    def get_all(cls, db: Session, skip: int = 0, limit: int = 100):
        """
        获取所有记录（分页）
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数限制
            
        Returns:
            记录列表
        """
        return db.query(cls).offset(skip).limit(limit).all()
    
    @classmethod
    def count(cls, db: Session) -> int:
        """
        获取记录总数
        
        Args:
            db: 数据库会话
            
        Returns:
            记录总数
        """
        return db.query(cls).count()
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"