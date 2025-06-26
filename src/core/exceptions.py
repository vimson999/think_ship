"""
文件名: exceptions.py
描述: 头条矩阵系统自定义异常处理模块

本模块定义了系统中使用的各种自定义异常类，包括：
1. 基础业务异常类
2. 数据库相关异常
3. AI服务异常
4. 爬虫相关异常
5. 认证授权异常
6. 文件处理异常

依赖模块:
   - datetime: 时间戳生成
   - enum: 异常代码枚举

使用示例:
   >>> from src.core.exceptions import BusinessException, ErrorCode
   >>> raise BusinessException(
   ...     message="用户不存在",
   ...     code=ErrorCode.USER_NOT_FOUND,
   ...     status_code=404
   ... )

注意事项:
   - 所有业务异常都应该继承自BusinessException
   - 异常信息应该对用户友好
   - 敏感信息不应该暴露在异常消息中

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """
    错误代码枚举
    
    定义系统中所有可能的错误代码，便于前端处理和日志追踪
    """
    
    # ===== 通用错误 =====
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # ===== 认证授权错误 =====
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # ===== 数据库错误 =====
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    FOREIGN_KEY_VIOLATION = "FOREIGN_KEY_VIOLATION"
    
    # ===== AI服务错误 =====
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_REQUEST_TIMEOUT = "AI_REQUEST_TIMEOUT"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    AI_CONTENT_FILTERED = "AI_CONTENT_FILTERED"
    AI_RESPONSE_INVALID = "AI_RESPONSE_INVALID"
    
    # ===== 爬虫相关错误 =====
    CRAWL_TARGET_UNREACHABLE = "CRAWL_TARGET_UNREACHABLE"
    CRAWL_RATE_LIMITED = "CRAWL_RATE_LIMITED"
    CRAWL_BLOCKED = "CRAWL_BLOCKED"
    CRAWL_PARSE_ERROR = "CRAWL_PARSE_ERROR"
    
    # ===== 内容相关错误 =====
    CONTENT_NOT_FOUND = "CONTENT_NOT_FOUND"
    CONTENT_GENERATION_FAILED = "CONTENT_GENERATION_FAILED"
    CONTENT_AUDIT_FAILED = "CONTENT_AUDIT_FAILED"
    CONTENT_DUPLICATE = "CONTENT_DUPLICATE"
    CONTENT_LENGTH_INVALID = "CONTENT_LENGTH_INVALID"
    
    # ===== 账号管理错误 =====
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    ACCOUNT_QUOTA_EXCEEDED = "ACCOUNT_QUOTA_EXCEEDED"
    ACCOUNT_HEALTH_LOW = "ACCOUNT_HEALTH_LOW"
    
    # ===== 发布相关错误 =====
    PUBLISH_FAILED = "PUBLISH_FAILED"
    PUBLISH_QUOTA_EXCEEDED = "PUBLISH_QUOTA_EXCEEDED"
    PUBLISH_SCHEDULE_CONFLICT = "PUBLISH_SCHEDULE_CONFLICT"
    PLATFORM_API_ERROR = "PLATFORM_API_ERROR"
    
    # ===== 文件处理错误 =====
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_TYPE_NOT_SUPPORTED = "FILE_TYPE_NOT_SUPPORTED"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    
    # ===== 任务相关错误 =====
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_EXECUTION_FAILED = "TASK_EXECUTION_FAILED"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    TASK_CANCELLED = "TASK_CANCELLED"


class BusinessException(Exception):
    """
    业务异常基类
    
    所有业务逻辑相关的异常都应该继承此类
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化业务异常
        
        Args:
            message: 错误消息，对用户友好的描述
            code: 错误代码，用于程序化处理
            status_code: HTTP状态码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": True,
            "message": self.message,
            "code": self.code,
            "status_code": self.status_code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
    
    def __repr__(self) -> str:
        return f"BusinessException(code={self.code}, message='{self.message}')"


class ValidationException(BusinessException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_PARAMETER,
            status_code=400,
            **kwargs
        )
        if field:
            self.details["field"] = field


class AuthenticationException(BusinessException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            **kwargs
        )


class AuthorizationException(BusinessException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足", **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
            status_code=403,
            **kwargs
        )


class ResourceNotFoundException(BusinessException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "请求的资源不存在", resource_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            **kwargs
        )
        if resource_type:
            self.details["resource_type"] = resource_type


class DatabaseException(BusinessException):
    """数据库异常"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.DATABASE_QUERY_ERROR,
            status_code=500,
            **kwargs
        )
        if original_error:
            self.details["original_error"] = str(original_error)


class AIServiceException(BusinessException):
    """AI服务异常"""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            status_code=503,
            **kwargs
        )
        if service_name:
            self.details["service_name"] = service_name
        if request_id:
            self.details["request_id"] = request_id


class CrawlerException(BusinessException):
    """爬虫异常"""
    
    def __init__(
        self,
        message: str,
        target_url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.CRAWL_TARGET_UNREACHABLE,
            status_code=503,
            **kwargs
        )
        if target_url:
            self.details["target_url"] = target_url
        if status_code:
            self.details["response_status"] = status_code


class ContentException(BusinessException):
    """内容处理异常"""
    
    def __init__(self, message: str, content_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code=ErrorCode.CONTENT_GENERATION_FAILED,
            status_code=422,
            **kwargs
        )
        if content_id:
            self.details["content_id"] = content_id


class AccountException(BusinessException):
    """账号管理异常"""
    
    def __init__(
        self,
        message: str,
        account_id: Optional[str] = None,
        platform: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.ACCOUNT_NOT_FOUND,
            status_code=404,
            **kwargs
        )
        if account_id:
            self.details["account_id"] = account_id
        if platform:
            self.details["platform"] = platform


class PublishException(BusinessException):
    """发布异常"""
    
    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        account_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.PUBLISH_FAILED,
            status_code=422,
            **kwargs
        )
        if platform:
            self.details["platform"] = platform
        if account_id:
            self.details["account_id"] = account_id


class RateLimitException(BusinessException):
    """限流异常"""
    
    def __init__(
        self,
        message: str = "请求频率过高，请稍后再试",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            **kwargs
        )
        if retry_after:
            self.details["retry_after"] = retry_after


class FileException(BusinessException):
    """文件处理异常"""
    
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.FILE_UPLOAD_FAILED,
            status_code=422,
            **kwargs
        )
        if filename:
            self.details["filename"] = filename
        if file_size:
            self.details["file_size"] = file_size


class TaskException(BusinessException):
    """任务处理异常"""
    
    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=ErrorCode.TASK_EXECUTION_FAILED,
            status_code=500,
            **kwargs
        )
        if task_id:
            self.details["task_id"] = task_id
        if task_type:
            self.details["task_type"] = task_type


# 导出所有异常类
__all__ = [
    "ErrorCode",
    "BusinessException",
    "ValidationException",
    "AuthenticationException", 
    "AuthorizationException",
    "ResourceNotFoundException",
    "DatabaseException",
    "AIServiceException",
    "CrawlerException",
    "ContentException",
    "AccountException",
    "PublishException",
    "RateLimitException",
    "FileException",
    "TaskException",
]