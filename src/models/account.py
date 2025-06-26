"""
文件名: account.py
描述: 账号管理数据模型

本模块定义账号管理相关的数据模型：
1. Account - 平台账号模型
2. AccountHealth - 账号健康度模型
3. AccountCategory - 账号分类枚举

依赖模块:
   - sqlalchemy: ORM框架
   - cryptography: 认证信息加密

使用示例:
   >>> account = Account(
   ...     platform="toutiao",
   ...     account_name="tech_writer",
   ...     account_id="12345",
   ...     category=AccountCategory.TECH
   ... )
   >>> account.set_credentials({"token": "secret_token"})

注意事项:
   - 认证信息使用加密存储
   - 账号健康度每日更新
   - 支持多平台账号管理

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Float, ForeignKey, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
# from cryptography.fernet import Fernet  # TODO: 安装cryptography后启用

from src.models.base import Base
from src.core.config import settings


class PlatformType(str, Enum):
    """平台类型枚举"""
    TOUTIAO = "toutiao"
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    DOUYIN = "douyin"
    WECHAT = "wechat"
    BAIDU = "baidu"


class AccountStatus(str, Enum):
    """账号状态枚举"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING = "pending"
    DISABLED = "disabled"


class AccountCategory(str, Enum):
    """账号分类枚举"""
    TECH = "tech"
    NEWS = "news"
    FINANCE = "finance"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    EDUCATION = "education"
    HEALTH = "health"
    TRAVEL = "travel"
    FOOD = "food"
    LIFESTYLE = "lifestyle"


class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 加密工具（实际应用中应该从环境变量获取密钥）
def get_encryption_key() -> bytes:
    """获取加密密钥"""
    # TODO: 从环境变量或配置文件获取真实的加密密钥
    return b'dummy_key_32_bytes_for_development'


class Account(Base):
    """
    平台账号模型
    
    存储各平台账号的基本信息和认证数据
    """
    __tablename__ = "accounts"
    __table_args__ = {'comment': '平台账号表'}
    
    # 基本信息
    platform = Column(
        String(50),
        nullable=False,
        default=PlatformType.TOUTIAO,
        comment="平台类型"
    )
    account_name = Column(
        String(100),
        nullable=False,
        comment="账号名称"
    )
    account_id = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="平台账号ID"
    )
    
    # 认证信息（加密存储）
    credentials = Column(
        JSONB,
        nullable=False,
        comment="加密的认证信息"
    )
    
    # 分类和状态
    category = Column(
        String(50),
        nullable=False,
        comment="账号分类"
    )
    status = Column(
        String(20),
        default=AccountStatus.ACTIVE,
        nullable=False,
        comment="账号状态"
    )
    
    # 发布限制
    daily_limit = Column(
        Integer,
        default=5,
        comment="每日发布限制"
    )
    daily_count = Column(
        Integer,
        default=0,
        comment="今日已发布数量"
    )
    last_post_at = Column(
        DateTime,
        nullable=True,
        comment="最后发布时间"
    )
    
    # 统计信息
    total_followers = Column(
        Integer,
        default=0,
        comment="粉丝总数"
    )
    total_posts = Column(
        Integer,
        default=0,
        comment="发布总数"
    )
    total_views = Column(
        Integer,
        default=0,
        comment="总浏览量"
    )
    total_revenue = Column(
        DECIMAL(12, 2),
        default=0,
        comment="总收益"
    )
    
    # 扩展信息
    extra_data = Column(
        JSONB,
        default=dict,
        comment="账号元数据"
    )
    tags = Column(
        ARRAY(String),
        default=list,
        comment="账号标签"
    )
    
    # 时间记录
    activated_at = Column(
        DateTime,
        nullable=True,
        comment="账号激活时间"
    )
    last_check_at = Column(
        DateTime,
        nullable=True,
        comment="最后检查时间"
    )
    
    # 关系定义
    health_records = relationship(
        "AccountHealth",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="AccountHealth.date.desc()"
    )
    publish_records = relationship(
        "PublishRecord",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    def set_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        设置认证信息（加密存储）
        
        Args:
            credentials: 认证信息字典
        """
        # TODO: 实现真实的加密逻辑
        # 这里简化处理，实际应该使用真正的加密
        self.credentials = credentials
    
    def get_credentials(self) -> Dict[str, Any]:
        """
        获取认证信息（解密）
        
        Returns:
            Dict[str, Any]: 解密后的认证信息
        """
        # TODO: 实现真实的解密逻辑
        return self.credentials or {}
    
    def can_post_today(self) -> bool:
        """
        检查今天是否还能发布
        
        Returns:
            bool: 是否可以发布
        """
        if self.status != AccountStatus.ACTIVE:
            return False
        
        if self.daily_limit <= 0:
            return True  # 无限制
        
        # 检查是否是新的一天
        today = date.today()
        last_post_date = self.last_post_at.date() if self.last_post_at else None
        
        if last_post_date != today:
            # 新的一天，重置计数
            self.daily_count = 0
        
        return self.daily_count < self.daily_limit
    
    def increment_post_count(self) -> None:
        """增加发布计数"""
        self.daily_count += 1
        self.total_posts += 1
        self.last_post_at = datetime.now()
    
    def update_followers(self, followers: int) -> None:
        """
        更新粉丝数
        
        Args:
            followers: 新的粉丝数
        """
        self.total_followers = followers
        self.last_check_at = datetime.now()
    
    def get_latest_health(self) -> Optional['AccountHealth']:
        """
        获取最新的健康度记录
        
        Returns:
            Optional[AccountHealth]: 最新健康度记录
        """
        if self.health_records:
            return self.health_records[0]
        return None
    
    def get_health_score(self) -> float:
        """
        获取当前健康度分数
        
        Returns:
            float: 健康度分数 (0-100)
        """
        latest_health = self.get_latest_health()
        return latest_health.health_score if latest_health else 100.0
    
    def get_risk_level(self) -> RiskLevel:
        """
        获取风险等级
        
        Returns:
            RiskLevel: 风险等级
        """
        score = self.get_health_score()
        
        if score >= 80:
            return RiskLevel.LOW
        elif score >= 60:
            return RiskLevel.MEDIUM
        elif score >= 40:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def is_healthy(self) -> bool:
        """
        检查账号是否健康
        
        Returns:
            bool: 是否健康
        """
        return self.get_health_score() >= 70 and self.status == AccountStatus.ACTIVE
    
    def suspend(self, reason: str = None) -> None:
        """
        暂停账号
        
        Args:
            reason: 暂停原因
        """
        self.status = AccountStatus.SUSPENDED
        if reason:
            extra_data = self.extra_data or {}
            extra_data['suspend_reason'] = reason
            extra_data['suspended_at'] = datetime.now().isoformat()
            self.extra_data = extra_data
    
    def activate(self) -> None:
        """激活账号"""
        self.status = AccountStatus.ACTIVE
        self.activated_at = datetime.now()
        
        # 清除暂停信息
        if self.extra_data:
            self.extra_data.pop('suspend_reason', None)
            self.extra_data.pop('suspended_at', None)
    
    def __repr__(self):
        return f"<Account(platform='{self.platform}', name='{self.account_name}', status='{self.status}')>"


class AccountHealth(Base):
    """
    账号健康度模型
    
    记录账号的每日健康状况和表现指标
    """
    __tablename__ = "account_health"
    __table_args__ = (
        {'comment': '账号健康度表'},
    )
    
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey('accounts.id'),
        nullable=False,
        comment="账号ID"
    )
    date = Column(
        Date,
        nullable=False,
        default=date.today,
        comment="记录日期"
    )
    
    # 发布统计
    posts_count = Column(
        Integer,
        default=0,
        comment="当日发布数量"
    )
    avg_views = Column(
        Integer,
        default=0,
        comment="平均浏览量"
    )
    avg_engagement_rate = Column(
        Float,
        default=0.0,
        comment="平均互动率"
    )
    
    # 违规统计
    violations_count = Column(
        Integer,
        default=0,
        comment="违规次数"
    )
    warnings_count = Column(
        Integer,
        default=0,
        comment="警告次数"
    )
    
    # 健康度评分
    health_score = Column(
        Float,
        default=100.0,
        comment="健康度分数 (0-100)"
    )
    
    # AI建议
    recommendations = Column(
        JSONB,
        default=list,
        comment="AI推荐建议"
    )
    
    # 详细指标
    metrics = Column(
        JSONB,
        default=dict,
        comment="详细健康指标"
    )
    
    # 关系定义
    account = relationship("Account", back_populates="health_records")
    
    def calculate_health_score(self) -> float:
        """
        计算健康度分数
        
        Returns:
            float: 计算后的健康度分数
        """
        base_score = 100.0
        
        # 违规扣分
        violation_penalty = self.violations_count * 20  # 每次违规扣20分
        warning_penalty = self.warnings_count * 5      # 每次警告扣5分
        
        # 互动率加分
        engagement_bonus = min(self.avg_engagement_rate * 10, 20)  # 最多加20分
        
        # 发布频率评分
        frequency_score = 0
        if 1 <= self.posts_count <= 3:  # 理想发布频率
            frequency_score = 10
        elif self.posts_count > 5:  # 发布过多可能降权
            frequency_score = -5
        
        final_score = base_score - violation_penalty - warning_penalty + engagement_bonus + frequency_score
        
        # 确保分数在0-100范围内
        self.health_score = max(0, min(100, final_score))
        
        return self.health_score
    
    def add_recommendation(self, recommendation: str, priority: str = "medium") -> None:
        """
        添加AI建议
        
        Args:
            recommendation: 建议内容
            priority: 优先级 (low/medium/high)
        """
        if not self.recommendations:
            self.recommendations = []
        
        new_recommendation = {
            "content": recommendation,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
        
        recommendations_list = list(self.recommendations)
        recommendations_list.append(new_recommendation)
        self.recommendations = recommendations_list
    
    def get_risk_level(self) -> RiskLevel:
        """
        获取风险等级
        
        Returns:
            RiskLevel: 风险等级
        """
        if self.health_score >= 80:
            return RiskLevel.LOW
        elif self.health_score >= 60:
            return RiskLevel.MEDIUM
        elif self.health_score >= 40:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def is_healthy(self) -> bool:
        """
        检查是否健康
        
        Returns:
            bool: 是否健康
        """
        return self.health_score >= 70
    
    def get_health_status(self) -> str:
        """
        获取健康状态描述
        
        Returns:
            str: 健康状态描述
        """
        score = self.health_score
        
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "一般"
        elif score >= 60:
            return "需要注意"
        elif score >= 40:
            return "风险较高"
        else:
            return "风险很高"
    
    def __repr__(self):
        return f"<AccountHealth(account_id='{self.account_id}', date='{self.date}', score={self.health_score})>"


# 导出所有模型
__all__ = [
    "Account", 
    "AccountHealth",
    "PlatformType",
    "AccountStatus", 
    "AccountCategory",
    "RiskLevel"
]