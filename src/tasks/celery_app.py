"""
文件名: celery_app.py
描述: Celery异步任务应用配置

本模块配置和初始化Celery异步任务系统：
1. Celery应用实例创建
2. 任务路由配置
3. 任务监控配置
4. 错误处理配置
5. 定时任务配置

依赖模块:
   - celery: 异步任务框架
   - kombu: 消息序列化
   - loguru: 日志记录

使用示例:
   >>> from src.tasks.celery_app import celery_app
   >>> # 启动Worker
   >>> celery -A src.tasks.celery_app worker --loglevel=info
   
   >>> # 启动定时任务
   >>> celery -A src.tasks.celery_app beat --loglevel=info

注意事项:
   - 确保Redis服务正常运行
   - 生产环境需要配置监控
   - 任务失败会自动重试

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

try:
    from celery import Celery
    from celery.signals import task_failure, task_success, worker_ready
    from kombu import Queue
except ImportError:
    logger.error("Celery模块未安装，请运行：pip install celery[redis]")
    raise

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings


def create_celery_app() -> Celery:
    """
    创建和配置Celery应用
    
    Returns:
        Celery: 配置好的Celery应用实例
    """
    
    # 创建Celery应用实例
    app = Celery(
        "think_ship",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    
    # 基础配置
    app.conf.update(
        # 任务序列化
        task_serializer=settings.CELERY_TASK_SERIALIZER,
        result_serializer=settings.CELERY_RESULT_SERIALIZER,
        accept_content=settings.CELERY_ACCEPT_CONTENT,
        
        # 时区设置
        timezone=settings.CELERY_TIMEZONE,
        enable_utc=settings.CELERY_ENABLE_UTC,
        
        # 任务路由
        task_routes={
            "src.tasks.collectors.*": {"queue": "collectors"},
            "src.tasks.generators.*": {"queue": "generators"},
            "src.tasks.publishers.*": {"queue": "publishers"},
            "src.tasks.analytics.*": {"queue": "analytics"},
        },
        
        # 队列定义
        task_queues=(
            Queue("default", routing_key="default"),
            Queue("collectors", routing_key="collectors"),
            Queue("generators", routing_key="generators"),
            Queue("publishers", routing_key="publishers"),
            Queue("analytics", routing_key="analytics"),
        ),
        
        # 默认队列
        task_default_queue="default",
        task_default_exchange="default",
        task_default_routing_key="default",
        
        # 任务执行配置
        task_acks_late=True,  # 任务完成后确认
        worker_prefetch_multiplier=1,  # 每次只取一个任务
        task_reject_on_worker_lost=True,  # Worker丢失时拒绝任务
        
        # 任务结果配置
        result_expires=3600,  # 结果1小时后过期
        result_persistent=True,  # 持久化结果
        
        # 任务重试配置
        task_annotations={
            "*": {
                "rate_limit": "100/m",  # 限制每分钟100个任务
                "max_retries": 3,
                "default_retry_delay": 60,  # 60秒后重试
            },
            "src.tasks.collectors.*": {
                "rate_limit": "30/m",  # 采集任务限制更严格
                "max_retries": 5,
                "default_retry_delay": 120,
            },
            "src.tasks.generators.*": {
                "rate_limit": "20/m",  # AI生成任务限制
                "max_retries": 3,
                "default_retry_delay": 180,
            },
        },
        
        # 监控配置
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Beat定时任务配置
        beat_schedule={
            # 热点采集任务 - 每5分钟执行一次
            "collect-hot-topics": {
                "task": "src.tasks.collectors.collect_hot_topics",
                "schedule": settings.HOT_TOPIC_FETCH_INTERVAL,
                "options": {"queue": "collectors"},
            },
            
            # 账号健康检查 - 每小时执行一次
            "check-account-health": {
                "task": "src.tasks.analytics.check_account_health",
                "schedule": 3600.0,  # 1小时
                "options": {"queue": "analytics"},
            },
            
            # 清理过期数据 - 每天凌晨2点执行
            "cleanup-expired-data": {
                "task": "src.tasks.analytics.cleanup_expired_data",
                "schedule": {
                    "hour": 2,
                    "minute": 0,
                },
                "options": {"queue": "analytics"},
            },
            
            # 生成日报 - 每天早上8点执行
            "generate-daily-report": {
                "task": "src.tasks.analytics.generate_daily_report",
                "schedule": {
                    "hour": 8,
                    "minute": 0,
                },
                "options": {"queue": "analytics"},
            },
        },
        
        # 安全配置
        worker_hijack_root_logger=False,  # 不劫持root logger
        worker_log_color=settings.DEBUG,  # 开发环境启用颜色日志
    )
    
    # 自动发现任务
    app.autodiscover_tasks([
        "src.tasks.collectors",
        "src.tasks.generators", 
        "src.tasks.publishers",
        "src.tasks.analytics",
    ])
    
    return app


# 创建全局Celery应用实例
celery_app = create_celery_app()


# 信号处理器
@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """任务成功完成时的处理"""
    task_id = kwargs.get("task_id")
    task_name = sender.__name__ if sender else "unknown"
    logger.info(f"✅ 任务成功完成: {task_name} (ID: {task_id})")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """任务失败时的处理"""
    task_name = sender.__name__ if sender else "unknown"
    logger.error(f"❌ 任务执行失败: {task_name} (ID: {task_id})")
    logger.error(f"异常信息: {exception}")
    if traceback:
        logger.error(f"堆栈跟踪: {traceback}")


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker准备就绪时的处理"""
    logger.info(f"🚀 Celery Worker已就绪: {sender.hostname}")


# 自定义任务基类
class BaseTask(celery_app.Task):
    """
    自定义任务基类
    
    提供统一的错误处理和日志记录
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"任务失败: {self.name} (ID: {task_id})")
        logger.error(f"参数: args={args}, kwargs={kwargs}")
        logger.error(f"异常: {exc}")
        
        # 这里可以添加失败通知逻辑
        # 比如发送邮件、推送通知等
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        logger.info(f"任务成功: {self.name} (ID: {task_id})")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试时的回调"""
        logger.warning(f"任务重试: {self.name} (ID: {task_id})")
        logger.warning(f"重试原因: {exc}")


# 设置默认任务基类
celery_app.Task = BaseTask


# 健康检查任务
@celery_app.task(bind=True)
def health_check(self):
    """
    Celery健康检查任务
    
    用于监控系统检查Celery是否正常工作
    """
    import time
    start_time = time.time()
    
    # 执行一些基础操作
    result = {
        "status": "healthy",
        "timestamp": time.time(),
        "worker_id": self.request.hostname,
        "task_id": self.request.id,
        "execution_time": time.time() - start_time,
    }
    
    logger.info(f"Celery健康检查完成: {result}")
    return result


# 测试任务
@celery_app.task(bind=True)
def test_task(self, message: str = "Hello Celery!"):
    """
    测试任务
    
    用于验证Celery配置是否正确
    """
    import time
    
    logger.info(f"开始执行测试任务: {message}")
    
    # 模拟一些工作
    time.sleep(2)
    
    result = {
        "message": message,
        "timestamp": time.time(),
        "worker_id": self.request.hostname,
        "task_id": self.request.id,
    }
    
    logger.info(f"测试任务完成: {result}")
    return result


# 导出
__all__ = ["celery_app", "BaseTask", "health_check", "test_task"]