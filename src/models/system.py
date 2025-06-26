"""
文件名: system.py
描述: 系统管理数据模型

本模块定义系统管理相关的数据模型：
1. TaskQueue - 任务队列模型
2. SystemConfig - 系统配置模型
3. OperationLog - 操作日志模型
4. CrawlerRule - 爬虫规则模型

依赖模块:
   - sqlalchemy: ORM框架
   - ipaddress: IP地址处理

使用示例:
   >>> task = TaskQueue(
   ...     task_type=TaskType.COLLECT,
   ...     payload={"source": "weibo", "url": "https://..."},
   ...     priority=5
   ... )
   >>> config = SystemConfig(
   ...     config_key="daily_collect_limit",
   ...     config_value={"value": 1000}
   ... )

注意事项:
   - 任务队列支持优先级调度
   - 敏感配置需要加密存储
   - 操作日志使用分区表提升性能

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from ipaddress import IPv4Address, IPv6Address

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import Base


class TaskType(str, Enum):
    """任务类型枚举"""
    COLLECT = "collect"
    ANALYZE = "analyze"
    GENERATE = "generate"
    PUBLISH = "publish"
    METRIC = "metric"
    CLEANUP = "cleanup"
    HEALTH_CHECK = "health_check"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConfigType(str, Enum):
    """配置类型枚举"""
    GLOBAL = "global"
    ACCOUNT = "account"
    CATEGORY = "category"
    PLATFORM = "platform"


class TaskQueue(Base):
    """
    任务队列模型
    
    管理系统中的异步任务
    """
    __tablename__ = "task_queue"
    __table_args__ = (
        CheckConstraint('priority BETWEEN 1 AND 10', name='check_priority_range'),
        Index('idx_task_queue_status_scheduled', 'status', 'scheduled_at'),
        Index('idx_task_queue_type', 'task_type'),
        Index('idx_task_queue_priority', 'priority'),
        {'comment': '任务队列表'}
    )
    
    # 任务基本信息
    task_type = Column(
        String(50),
        nullable=False,
        comment="任务类型"
    )
    task_name = Column(
        String(100),
        nullable=True,
        comment="任务名称"
    )
    description = Column(
        Text,
        nullable=True,
        comment="任务描述"
    )
    
    # 优先级和负载
    priority = Column(
        Integer,
        default=5,
        nullable=False,
        comment="优先级 (1-10, 10最高)"
    )
    payload = Column(
        JSONB,
        nullable=False,
        comment="任务参数"
    )
    
    # 状态管理
    status = Column(
        String(20),
        default=TaskStatus.PENDING,
        nullable=False,
        comment="任务状态"
    )
    
    # 重试机制
    retry_count = Column(
        Integer,
        default=0,
        comment="重试次数"
    )
    max_retries = Column(
        Integer,
        default=3,
        comment="最大重试次数"
    )
    
    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    error_details = Column(
        JSONB,
        default=dict,
        comment="错误详情"
    )
    
    # 执行结果
    result = Column(
        JSONB,
        nullable=True,
        comment="任务结果"
    )
    
    # 时间管理
    scheduled_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="计划执行时间"
    )
    started_at = Column(
        DateTime,
        nullable=True,
        comment="开始执行时间"
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="完成时间"
    )
    
    # 执行者信息
    worker_id = Column(
        String(100),
        nullable=True,
        comment="执行者ID"
    )
    
    # 依赖关系
    parent_task_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="父任务ID"
    )
    dependency_ids = Column(
        JSONB,
        default=list,
        comment="依赖任务ID列表"
    )
    
    # 超时设置
    timeout_seconds = Column(
        Integer,
        nullable=True,
        comment="超时时间(秒)"
    )
    
    @hybrid_property
    def execution_time(self) -> Optional[float]:
        """
        计算执行时间
        
        Returns:
            Optional[float]: 执行时间(秒)
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def start_execution(self, worker_id: str) -> None:
        """
        开始执行任务
        
        Args:
            worker_id: 执行者ID
        """
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now()
        self.worker_id = worker_id
    
    def complete_task(self, result: Dict[str, Any] = None) -> None:
        """
        完成任务
        
        Args:
            result: 执行结果
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if result:
            self.result = result
    
    def fail_task(self, error_message: str, error_details: Dict[str, Any] = None) -> None:
        """
        任务失败
        
        Args:
            error_message: 错误信息
            error_details: 错误详情
        """
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        
        self.retry_count += 1
        
        if self.retry_count >= self.max_retries:
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.now()
        else:
            self.status = TaskStatus.RETRY
            # 重新调度执行
            self.scheduled_at = datetime.now()
    
    def cancel_task(self, reason: str = None) -> None:
        """
        取消任务
        
        Args:
            reason: 取消原因
        """
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        if reason:
            self.error_message = f"任务被取消: {reason}"
    
    def can_execute(self) -> bool:
        """
        检查任务是否可以执行
        
        Returns:
            bool: 是否可以执行
        """
        return (
            self.status in [TaskStatus.PENDING, TaskStatus.RETRY] and
            self.scheduled_at <= datetime.now()
        )
    
    def is_overdue(self) -> bool:
        """
        检查任务是否超时
        
        Returns:
            bool: 是否超时
        """
        if not self.timeout_seconds or not self.started_at:
            return False
        
        if self.status != TaskStatus.PROCESSING:
            return False
        
        elapsed = (datetime.now() - self.started_at).total_seconds()
        return elapsed > self.timeout_seconds
    
    def __repr__(self):
        return f"<TaskQueue(type='{self.task_type}', status='{self.status}', priority={self.priority})>"


class SystemConfig(Base):
    """
    系统配置模型
    
    存储系统的各种配置参数
    """
    __tablename__ = "system_configs"
    __table_args__ = (
        Index('idx_system_configs_key', 'config_key', unique=True),
        Index('idx_system_configs_type', 'config_type'),
        {'comment': '系统配置表'}
    )
    
    # 配置标识
    config_key = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="配置键"
    )
    config_name = Column(
        String(100),
        nullable=True,
        comment="配置名称"
    )
    
    # 配置值
    config_value = Column(
        JSONB,
        nullable=False,
        comment="配置值"
    )
    default_value = Column(
        JSONB,
        nullable=True,
        comment="默认值"
    )
    
    # 配置类型
    config_type = Column(
        String(50),
        default=ConfigType.GLOBAL,
        comment="配置类型"
    )
    
    # 描述信息
    description = Column(
        Text,
        nullable=True,
        comment="配置描述"
    )
    
    # 验证规则
    validation_rules = Column(
        JSONB,
        default=dict,
        comment="验证规则"
    )
    
    # 安全标记
    is_encrypted = Column(
        Boolean,
        default=False,
        comment="是否加密"
    )
    is_sensitive = Column(
        Boolean,
        default=False,
        comment="是否敏感"
    )
    
    # 状态管理
    is_active = Column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    
    # 变更记录
    updated_by = Column(
        String(100),
        nullable=True,
        comment="更新者"
    )
    change_reason = Column(
        Text,
        nullable=True,
        comment="变更原因"
    )
    
    def get_value(self, default=None):
        """
        获取配置值
        
        Args:
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        if self.is_active and self.config_value is not None:
            if isinstance(self.config_value, dict) and 'value' in self.config_value:
                return self.config_value['value']
            return self.config_value
        
        if self.default_value is not None:
            if isinstance(self.default_value, dict) and 'value' in self.default_value:
                return self.default_value['value']
            return self.default_value
        
        return default
    
    def set_value(self, value: Any, updated_by: str = None, reason: str = None) -> None:
        """
        设置配置值
        
        Args:
            value: 新值
            updated_by: 更新者
            reason: 变更原因
        """
        if isinstance(value, dict):
            self.config_value = value
        else:
            self.config_value = {"value": value}
        
        if updated_by:
            self.updated_by = updated_by
        if reason:
            self.change_reason = reason
    
    def validate_value(self, value: Any) -> bool:
        """
        验证配置值
        
        Args:
            value: 要验证的值
            
        Returns:
            bool: 是否有效
        """
        if not self.validation_rules:
            return True
        
        # TODO: 实现具体的验证逻辑
        # 可以根据validation_rules中的规则进行验证
        return True
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}', type='{self.config_type}', active={self.is_active})>"


class OperationLog(Base):
    """
    操作日志模型
    
    记录系统操作日志（使用分区表）
    """
    __tablename__ = "operation_logs"
    __table_args__ = (
        Index('idx_operation_logs_created', 'created_at'),
        Index('idx_operation_logs_module_level', 'module', 'level'),
        Index('idx_operation_logs_user', 'user_id'),
        Index('idx_operation_logs_request', 'request_id'),
        {'comment': '操作日志表（分区表）'}
    )
    
    # 操作信息
    module = Column(
        String(50),
        nullable=False,
        comment="模块名称"
    )
    action = Column(
        String(100),
        nullable=False,
        comment="操作动作"
    )
    level = Column(
        String(20),
        default=LogLevel.INFO,
        nullable=False,
        comment="日志级别"
    )
    
    # 日志内容
    message = Column(
        Text,
        nullable=True,
        comment="日志消息"
    )
    details = Column(
        JSONB,
        default=dict,
        comment="详细信息"
    )
    
    # 用户信息
    user_id = Column(
        String(100),
        nullable=True,
        comment="用户ID"
    )
    username = Column(
        String(100),
        nullable=True,
        comment="用户名"
    )
    
    # 请求信息
    request_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="请求ID"
    )
    ip_address = Column(
        INET,
        nullable=True,
        comment="IP地址"
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment="用户代理"
    )
    
    # 性能信息
    duration_ms = Column(
        Integer,
        nullable=True,
        comment="操作耗时(毫秒)"
    )
    
    # 错误信息
    error_code = Column(
        String(50),
        nullable=True,
        comment="错误代码"
    )
    stack_trace = Column(
        Text,
        nullable=True,
        comment="堆栈跟踪"
    )
    
    # 扩展信息
    extra_data = Column(
        JSONB,
        default=dict,
        comment="扩展元数据"
    )
    
    @classmethod
    def log_operation(
        cls,
        module: str,
        action: str,
        message: str = None,
        level: LogLevel = LogLevel.INFO,
        user_id: str = None,
        username: str = None,
        request_id: uuid.UUID = None,
        ip_address: str = None,
        user_agent: str = None,
        duration_ms: int = None,
        details: Dict[str, Any] = None,
        **kwargs
    ) -> 'OperationLog':
        """
        记录操作日志
        
        Args:
            module: 模块名称
            action: 操作动作
            message: 日志消息
            level: 日志级别
            user_id: 用户ID
            username: 用户名
            request_id: 请求ID
            ip_address: IP地址
            user_agent: 用户代理
            duration_ms: 耗时
            details: 详细信息
            **kwargs: 其他参数
            
        Returns:
            OperationLog: 日志实例
        """
        return cls(
            module=module,
            action=action,
            message=message,
            level=level,
            user_id=user_id,
            username=username,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            details=details or {},
            extra_data=kwargs.get('extra_data', {}),
            **{k: v for k, v in kwargs.items() if k != 'extra_data'}
        )
    
    def is_error(self) -> bool:
        """
        检查是否为错误日志
        
        Returns:
            bool: 是否为错误
        """
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]
    
    def get_ip_version(self) -> Optional[int]:
        """
        获取IP版本
        
        Returns:
            Optional[int]: IP版本 (4 或 6)
        """
        if not self.ip_address:
            return None
        
        try:
            if '.' in str(self.ip_address):
                IPv4Address(str(self.ip_address))
                return 4
            elif ':' in str(self.ip_address):
                IPv6Address(str(self.ip_address))
                return 6
        except:
            pass
        
        return None
    
    def __repr__(self):
        return f"<OperationLog(module='{self.module}', action='{self.action}', level='{self.level}')>"


class CrawlerRule(Base):
    """
    爬虫规则模型
    
    定义各平台的爬虫规则和配置
    """
    __tablename__ = "crawler_rules"
    __table_args__ = (
        Index('idx_crawler_rules_source', 'source'),
        Index('idx_crawler_rules_active', 'is_active'),
        {'comment': '爬虫规则配置表'}
    )
    
    # 基本信息
    source = Column(
        String(50),
        nullable=False,
        comment="数据源"
    )
    rule_name = Column(
        String(100),
        nullable=False,
        comment="规则名称"
    )
    description = Column(
        Text,
        nullable=True,
        comment="规则描述"
    )
    
    # URL配置
    url_pattern = Column(
        Text,
        nullable=True,
        comment="URL模式"
    )
    base_url = Column(
        Text,
        nullable=True,
        comment="基础URL"
    )
    
    # 选择器配置
    selectors = Column(
        JSONB,
        nullable=False,
        comment="CSS选择器配置"
    )
    
    # 请求配置
    headers = Column(
        JSONB,
        default=dict,
        comment="请求头配置"
    )
    cookies = Column(
        JSONB,
        default=dict,
        comment="Cookie配置"
    )
    
    # 限流配置
    rate_limit = Column(
        Integer,
        default=10,
        comment="每分钟请求数"
    )
    delay_seconds = Column(
        Float,
        default=1.0,
        comment="请求间隔(秒)"
    )
    
    # 重试配置
    max_retries = Column(
        Integer,
        default=3,
        comment="最大重试次数"
    )
    retry_delay = Column(
        Float,
        default=5.0,
        comment="重试延迟(秒)"
    )
    
    # 状态管理
    is_active = Column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    
    # 统计信息
    success_count = Column(
        Integer,
        default=0,
        comment="成功次数"
    )
    fail_count = Column(
        Integer,
        default=0,
        comment="失败次数"
    )
    last_success_at = Column(
        DateTime,
        nullable=True,
        comment="最后成功时间"
    )
    last_fail_at = Column(
        DateTime,
        nullable=True,
        comment="最后失败时间"
    )
    
    # 扩展配置
    extra_config = Column(
        JSONB,
        default=dict,
        comment="扩展配置"
    )
    
    @hybrid_property
    def success_rate(self) -> float:
        """
        计算成功率
        
        Returns:
            float: 成功率
        """
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def record_success(self) -> None:
        """记录成功"""
        self.success_count += 1
        self.last_success_at = datetime.now()
    
    def record_failure(self) -> None:
        """记录失败"""
        self.fail_count += 1
        self.last_fail_at = datetime.now()
    
    def is_healthy(self) -> bool:
        """
        检查规则是否健康
        
        Returns:
            bool: 是否健康
        """
        if not self.is_active:
            return False
        
        # 成功率低于50%认为不健康
        if self.success_rate < 0.5 and (self.success_count + self.fail_count) >= 10:
            return False
        
        return True
    
    def get_selector(self, key: str, default: str = None) -> Optional[str]:
        """
        获取选择器
        
        Args:
            key: 选择器键
            default: 默认值
            
        Returns:
            Optional[str]: 选择器值
        """
        if not self.selectors:
            return default
        
        return self.selectors.get(key, default)
    
    def update_selector(self, key: str, value: str) -> None:
        """
        更新选择器
        
        Args:
            key: 选择器键
            value: 选择器值
        """
        if not self.selectors:
            self.selectors = {}
        
        selectors_dict = dict(self.selectors)
        selectors_dict[key] = value
        self.selectors = selectors_dict
    
    def __repr__(self):
        return f"<CrawlerRule(source='{self.source}', name='{self.rule_name}', active={self.is_active})>"


# 导出所有模型
__all__ = [
    "TaskQueue",
    "SystemConfig", 
    "OperationLog",
    "CrawlerRule",
    "TaskType",
    "TaskStatus",
    "LogLevel",
    "ConfigType"
]