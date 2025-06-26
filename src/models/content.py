"""
文件名: content.py
描述: 内容管理数据模型

本模块定义内容相关的数据模型：
1. HotTopic - 热点内容模型
2. Content - 生成内容模型
3. PublishRecord - 发布记录模型
4. ContentMetrics - 内容表现模型
5. ContentTemplate - 内容模板模型
6. ContentStateTransition - 内容状态转换模型

依赖模块:
   - sqlalchemy: ORM框架
   - hashlib: 内容哈希计算

使用示例:
   >>> topic = HotTopic(
   ...     source="weibo",
   ...     title="热点新闻标题",
   ...     content="新闻内容...",
   ...     category="tech"
   ... )
   >>> content = Content.from_topic(topic, template_id="article_template")

注意事项:
   - 内容表使用分区存储提升性能
   - 内容去重基于SHA256哈希
   - 发布状态使用状态机管理

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import hashlib
import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Float, ForeignKey, Text, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import Base


class ContentSource(str, Enum):
    """内容来源枚举"""
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    DOUYIN = "douyin"
    NEWS = "news"
    MANUAL = "manual"
    API = "api"


class ContentCategory(str, Enum):
    """内容分类枚举"""
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


class ContentStatus(str, Enum):
    """内容状态枚举"""
    DRAFT = "draft"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class PublishStatus(str, Enum):
    """发布状态枚举"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TemplateType(str, Enum):
    """模板类型枚举"""
    ARTICLE = "article"
    SHORT_ARTICLE = "short_article"
    VIDEO_SCRIPT = "video_script"
    SOCIAL_POST = "social_post"


class HotTopic(Base):
    """
    热点内容模型
    
    存储从各平台采集的热点内容和话题
    """
    __tablename__ = "hot_topics"
    __table_args__ = (
        Index('idx_hot_topics_source_id', 'source', 'source_id', unique=True),
        Index('idx_hot_topics_processed', 'processed'),
        Index('idx_hot_topics_category_score', 'category', 'score'),
        Index('idx_hot_topics_collected_at', 'collected_at'),
        {'comment': '热点内容表'}
    )
    
    # 来源信息
    source = Column(
        String(50),
        nullable=False,
        comment="内容来源"
    )
    source_id = Column(
        String(200),
        nullable=True,
        comment="原始来源ID"
    )
    source_url = Column(
        Text,
        nullable=True,
        comment="原始链接"
    )
    
    # 内容信息
    title = Column(
        Text,
        nullable=False,
        comment="标题"
    )
    content = Column(
        Text,
        nullable=True,
        comment="内容正文"
    )
    summary = Column(
        Text,
        nullable=True,
        comment="内容摘要"
    )
    
    # 分类和标签
    category = Column(
        String(50),
        nullable=True,
        comment="内容分类"
    )
    keywords = Column(
        ARRAY(String),
        default=list,
        comment="关键词"
    )
    tags = Column(
        ARRAY(String),
        default=list,
        comment="标签"
    )
    
    # 热度评分
    score = Column(
        Float,
        default=0.0,
        comment="热度分数"
    )
    views_count = Column(
        Integer,
        default=0,
        comment="浏览量"
    )
    comments_count = Column(
        Integer,
        default=0,
        comment="评论数"
    )
    shares_count = Column(
        Integer,
        default=0,
        comment="分享数"
    )
    
    # 原始数据
    extra_data = Column(
        JSONB,
        default=dict,
        comment="原始数据"
    )
    
    # 处理状态
    processed = Column(
        Boolean,
        default=False,
        comment="是否已处理"
    )
    processed_at = Column(
        DateTime,
        nullable=True,
        comment="处理时间"
    )
    collected_at = Column(
        DateTime,
        default=datetime.now,
        comment="采集时间"
    )
    
    # 关系定义
    generated_contents = relationship(
        "Content",
        back_populates="hot_topic",
        cascade="all, delete-orphan"
    )
    
    def calculate_score(self) -> float:
        """
        计算热度分数
        
        Returns:
            float: 热度分数
        """
        # 基于浏览量、评论数、分享数计算热度
        base_score = 0.0
        
        if self.views_count > 0:
            base_score += min(self.views_count / 1000, 50)  # 最多50分
        
        if self.comments_count > 0:
            base_score += min(self.comments_count * 2, 30)  # 最多30分
        
        if self.shares_count > 0:
            base_score += min(self.shares_count * 5, 20)   # 最多20分
        
        # 时间衰减
        hours_passed = (datetime.now() - self.collected_at).total_seconds() / 3600
        time_decay = max(0.1, 1 - (hours_passed / 24))  # 24小时内线性衰减
        
        self.score = base_score * time_decay
        return self.score
    
    def mark_processed(self) -> None:
        """标记为已处理"""
        self.processed = True
        self.processed_at = datetime.now()
    
    def add_keyword(self, keyword: str) -> None:
        """
        添加关键词
        
        Args:
            keyword: 关键词
        """
        if not self.keywords:
            self.keywords = []
        
        if keyword not in self.keywords:
            keywords_list = list(self.keywords)
            keywords_list.append(keyword)
            self.keywords = keywords_list
    
    def get_engagement_rate(self) -> float:
        """
        计算互动率
        
        Returns:
            float: 互动率
        """
        if self.views_count <= 0:
            return 0.0
        
        total_engagement = self.comments_count + self.shares_count
        return total_engagement / self.views_count
    
    def __repr__(self):
        return f"<HotTopic(source='{self.source}', title='{self.title[:50]}...', score={self.score})>"


class Content(Base):
    """
    生成内容模型
    
    存储AI生成的内容（使用分区表）
    """
    __tablename__ = "contents"
    __table_args__ = (
        Index('idx_contents_hash', 'content_hash', unique=True),
        Index('idx_contents_status', 'status'),
        Index('idx_contents_category', 'category'),
        Index('idx_contents_topic', 'topic_id'),
        {'comment': '生成内容表（分区表）'}
    )
    
    # 关联信息
    topic_id = Column(
        UUID(as_uuid=True),
        ForeignKey('hot_topics.id'),
        nullable=True,
        comment="热点话题ID"
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey('content_templates.id'),
        nullable=True,
        comment="模板ID"
    )
    
    # 内容信息
    title = Column(
        String(200),
        nullable=False,
        comment="标题"
    )
    content = Column(
        Text,
        nullable=False,
        comment="内容正文"
    )
    content_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="内容哈希(SHA256)"
    )
    summary = Column(
        Text,
        nullable=True,
        comment="摘要"
    )
    
    # 分类和标签
    category = Column(
        String(50),
        nullable=False,
        comment="内容分类"
    )
    keywords = Column(
        ARRAY(String),
        default=list,
        comment="关键词"
    )
    tags = Column(
        ARRAY(String),
        default=list,
        comment="标签"
    )
    
    # 媒体文件
    images = Column(
        JSONB,
        default=list,
        comment="图片URL列表"
    )
    videos = Column(
        JSONB,
        default=list,
        comment="视频URL列表"
    )
    
    # AI生成信息
    ai_model = Column(
        String(50),
        nullable=True,
        comment="AI模型"
    )
    generation_params = Column(
        JSONB,
        default=dict,
        comment="生成参数"
    )
    
    # 质量评分
    quality_score = Column(
        Float,
        nullable=True,
        comment="质量分数"
    )
    
    # 状态管理
    status = Column(
        String(20),
        default=ContentStatus.DRAFT,
        nullable=False,
        comment="内容状态"
    )
    
    # 统计信息
    word_count = Column(
        Integer,
        default=0,
        comment="字数"
    )
    
    # 关系定义
    hot_topic = relationship("HotTopic", back_populates="generated_contents")
    template = relationship("ContentTemplate", back_populates="generated_contents")
    publish_records = relationship(
        "PublishRecord",
        back_populates="content",
        cascade="all, delete-orphan"
    )
    state_transitions = relationship(
        "ContentStateTransition",
        back_populates="content",
        cascade="all, delete-orphan"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.content and not self.content_hash:
            self.content_hash = self.generate_content_hash()
        if self.content and not self.word_count:
            self.word_count = len(self.content)
    
    def generate_content_hash(self) -> str:
        """
        生成内容哈希
        
        Returns:
            str: SHA256哈希值
        """
        content_str = f"{self.title}{self.content}"
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
    
    @classmethod
    def from_topic(
        cls,
        topic: HotTopic,
        template_id: Optional[uuid.UUID] = None,
        ai_model: str = "gpt-3.5-turbo",
        **kwargs
    ) -> 'Content':
        """
        从热点话题创建内容
        
        Args:
            topic: 热点话题
            template_id: 模板ID
            ai_model: AI模型
            **kwargs: 其他参数
            
        Returns:
            Content: 内容实例
        """
        return cls(
            topic_id=topic.id,
            template_id=template_id,
            category=topic.category or ContentCategory.NEWS,
            keywords=topic.keywords,
            tags=topic.tags,
            ai_model=ai_model,
            **kwargs
        )
    
    def calculate_quality_score(self) -> float:
        """
        计算质量分数
        
        Returns:
            float: 质量分数 (0-100)
        """
        score = 0.0
        
        # 内容长度评分 (30分)
        if self.word_count:
            if 500 <= self.word_count <= 2000:  # 理想长度
                score += 30
            elif 200 <= self.word_count < 500 or 2000 < self.word_count <= 3000:
                score += 20
            elif self.word_count >= 100:
                score += 10
        
        # 标题质量评分 (20分)
        if self.title:
            title_len = len(self.title)
            if 10 <= title_len <= 50:  # 理想标题长度
                score += 20
            elif 5 <= title_len < 10 or 50 < title_len <= 80:
                score += 15
            elif title_len >= 3:
                score += 10
        
        # 关键词覆盖评分 (20分)
        if self.keywords:
            keyword_count = len(self.keywords)
            if 3 <= keyword_count <= 8:
                score += 20
            elif 1 <= keyword_count < 3 or 8 < keyword_count <= 15:
                score += 15
            elif keyword_count > 0:
                score += 10
        
        # 内容结构评分 (15分)
        if self.content:
            # 简单检查段落结构
            paragraphs = self.content.split('\n\n')
            if len(paragraphs) >= 3:
                score += 15
            elif len(paragraphs) >= 2:
                score += 10
            else:
                score += 5
        
        # 媒体文件评分 (15分)
        image_count = len(self.images) if self.images else 0
        if image_count >= 1:
            score += min(image_count * 5, 15)
        
        self.quality_score = min(score, 100.0)
        return self.quality_score
    
    def change_status(self, new_status: ContentStatus, reason: str = None) -> None:
        """
        改变内容状态
        
        Args:
            new_status: 新状态
            reason: 变更原因
        """
        old_status = self.status
        self.status = new_status
        
        # 记录状态转换
        transition = ContentStateTransition(
            content_id=self.id,
            from_state=old_status,
            to_state=new_status,
            reason=reason
        )
        self.state_transitions.append(transition)
    
    def add_image(self, image_url: str, caption: str = None) -> None:
        """
        添加图片
        
        Args:
            image_url: 图片URL
            caption: 图片说明
        """
        if not self.images:
            self.images = []
        
        image_info = {"url": image_url}
        if caption:
            image_info["caption"] = caption
        
        images_list = list(self.images)
        images_list.append(image_info)
        self.images = images_list
    
    def is_duplicate(self, other_content: str) -> bool:
        """
        检查是否与其他内容重复
        
        Args:
            other_content: 其他内容
            
        Returns:
            bool: 是否重复
        """
        other_hash = hashlib.sha256(other_content.encode('utf-8')).hexdigest()
        return self.content_hash == other_hash
    
    def __repr__(self):
        return f"<Content(title='{self.title[:50]}...', status='{self.status}', score={self.quality_score})>"


class PublishRecord(Base):
    """
    发布记录模型
    
    记录内容的发布状态和结果
    """
    __tablename__ = "publish_records"
    __table_args__ = (
        Index('idx_publish_records_content_account', 'content_id', 'account_id', unique=True),
        Index('idx_publish_records_account', 'account_id'),
        Index('idx_publish_records_status', 'status'),
        Index('idx_publish_records_scheduled', 'scheduled_time'),
        {'comment': '发布记录表'}
    )
    
    # 关联信息
    content_id = Column(
        UUID(as_uuid=True),
        ForeignKey('contents.id'),
        nullable=False,
        comment="内容ID"
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey('accounts.id'),
        nullable=False,
        comment="账号ID"
    )
    
    # 平台信息
    platform = Column(
        String(50),
        nullable=False,
        comment="发布平台"
    )
    platform_post_id = Column(
        String(200),
        nullable=True,
        comment="平台文章ID"
    )
    platform_url = Column(
        Text,
        nullable=True,
        comment="发布后的URL"
    )
    
    # 发布时间
    scheduled_time = Column(
        DateTime,
        nullable=True,
        comment="计划发布时间"
    )
    published_time = Column(
        DateTime,
        nullable=True,
        comment="实际发布时间"
    )
    
    # 状态信息
    status = Column(
        String(20),
        default=PublishStatus.PENDING,
        nullable=False,
        comment="发布状态"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    retry_count = Column(
        Integer,
        default=0,
        comment="重试次数"
    )
    
    # 扩展信息
    extra_data = Column(
        JSONB,
        default=dict,
        comment="平台返回的其他信息"
    )
    
    # 关系定义
    content = relationship("Content", back_populates="publish_records")
    account = relationship("Account", back_populates="publish_records")
    metrics = relationship(
        "ContentMetrics",
        back_populates="publish_record",
        cascade="all, delete-orphan"
    )
    
    def mark_published(self, platform_post_id: str = None, platform_url: str = None) -> None:
        """
        标记为已发布
        
        Args:
            platform_post_id: 平台文章ID
            platform_url: 发布URL
        """
        self.status = PublishStatus.PUBLISHED
        self.published_time = datetime.now()
        
        if platform_post_id:
            self.platform_post_id = platform_post_id
        if platform_url:
            self.platform_url = platform_url
    
    def mark_failed(self, error_message: str) -> None:
        """
        标记为发布失败
        
        Args:
            error_message: 错误信息
        """
        self.status = PublishStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """
        检查是否可以重试
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否可以重试
        """
        return self.status == PublishStatus.FAILED and self.retry_count < max_retries
    
    def is_published(self) -> bool:
        """
        检查是否已发布
        
        Returns:
            bool: 是否已发布
        """
        return self.status == PublishStatus.PUBLISHED
    
    def get_latest_metrics(self) -> Optional['ContentMetrics']:
        """
        获取最新指标
        
        Returns:
            Optional[ContentMetrics]: 最新指标
        """
        if self.metrics:
            return max(self.metrics, key=lambda m: m.collected_at)
        return None
    
    def __repr__(self):
        return f"<PublishRecord(content_id='{self.content_id}', platform='{self.platform}', status='{self.status}')>"


class ContentMetrics(Base):
    """
    内容表现模型
    
    记录内容的表现数据（使用分区表）
    """
    __tablename__ = "content_metrics"
    __table_args__ = (
        Index('idx_content_metrics_publish', 'publish_id'),
        Index('idx_content_metrics_time', 'collected_at'),
        {'comment': '内容表现表（分区表）'}
    )
    
    # 关联信息
    publish_id = Column(
        UUID(as_uuid=True),
        ForeignKey('publish_records.id'),
        nullable=False,
        comment="发布记录ID"
    )
    
    # 基础指标
    views = Column(
        Integer,
        default=0,
        comment="浏览量"
    )
    likes = Column(
        Integer,
        default=0,
        comment="点赞数"
    )
    comments = Column(
        Integer,
        default=0,
        comment="评论数"
    )
    shares = Column(
        Integer,
        default=0,
        comment="分享数"
    )
    
    # 高级指标
    read_completion_rate = Column(
        Float,
        nullable=True,
        comment="阅读完成率"
    )
    avg_read_time = Column(
        Integer,
        nullable=True,
        comment="平均阅读时间(秒)"
    )
    bounce_rate = Column(
        Float,
        nullable=True,
        comment="跳出率"
    )
    
    # 收益信息
    revenue = Column(
        DECIMAL(10, 2),
        default=0,
        comment="广告收入"
    )
    
    # 采集时间
    collected_at = Column(
        DateTime,
        default=datetime.now,
        comment="采集时间"
    )
    
    # 关系定义
    publish_record = relationship("PublishRecord", back_populates="metrics")
    
    @hybrid_property
    def engagement_rate(self) -> float:
        """
        计算互动率
        
        Returns:
            float: 互动率
        """
        if self.views <= 0:
            return 0.0
        
        total_engagement = self.likes + self.comments + self.shares
        return total_engagement / self.views
    
    def calculate_performance_score(self) -> float:
        """
        计算表现分数
        
        Returns:
            float: 表现分数 (0-100)
        """
        score = 0.0
        
        # 浏览量评分 (30分)
        if self.views >= 10000:
            score += 30
        elif self.views >= 5000:
            score += 25
        elif self.views >= 1000:
            score += 20
        elif self.views >= 100:
            score += 15
        elif self.views > 0:
            score += 10
        
        # 互动率评分 (40分)
        engagement = self.engagement_rate
        if engagement >= 0.1:  # 10%以上
            score += 40
        elif engagement >= 0.05:  # 5-10%
            score += 30
        elif engagement >= 0.02:  # 2-5%
            score += 20
        elif engagement >= 0.01:  # 1-2%
            score += 15
        elif engagement > 0:
            score += 10
        
        # 阅读完成率评分 (20分)
        if self.read_completion_rate:
            if self.read_completion_rate >= 0.8:
                score += 20
            elif self.read_completion_rate >= 0.6:
                score += 15
            elif self.read_completion_rate >= 0.4:
                score += 10
            elif self.read_completion_rate > 0:
                score += 5
        
        # 收益评分 (10分)
        if self.revenue:
            if self.revenue >= 100:
                score += 10
            elif self.revenue >= 50:
                score += 8
            elif self.revenue >= 10:
                score += 5
            elif self.revenue > 0:
                score += 3
        
        return min(score, 100.0)
    
    def __repr__(self):
        return f"<ContentMetrics(publish_id='{self.publish_id}', views={self.views}, engagement={self.engagement_rate:.3f})>"


class ContentTemplate(Base):
    """
    内容模板模型
    
    定义不同类型的内容生成模板
    """
    __tablename__ = "content_templates"
    __table_args__ = {'comment': '内容模板表'}
    
    # 基本信息
    name = Column(
        String(100),
        nullable=False,
        comment="模板名称"
    )
    display_name = Column(
        String(100),
        nullable=False,
        comment="显示名称"
    )
    description = Column(
        Text,
        nullable=True,
        comment="模板描述"
    )
    
    # 分类信息
    category = Column(
        String(50),
        nullable=False,
        comment="模板分类"
    )
    template_type = Column(
        String(50),
        nullable=False,
        comment="模板类型"
    )
    
    # 模板配置
    structure = Column(
        JSONB,
        nullable=False,
        comment="模板结构"
    )
    variables = Column(
        JSONB,
        default=dict,
        comment="可替换变量"
    )
    prompt_template = Column(
        Text,
        nullable=True,
        comment="AI提示词模板"
    )
    
    # 状态和统计
    is_active = Column(
        Boolean,
        default=True,
        comment="是否启用"
    )
    usage_count = Column(
        Integer,
        default=0,
        comment="使用次数"
    )
    success_rate = Column(
        Float,
        default=0.0,
        comment="成功率"
    )
    avg_quality_score = Column(
        Float,
        default=0.0,
        comment="平均质量分数"
    )
    
    # 关系定义
    generated_contents = relationship("Content", back_populates="template")
    
    def increment_usage(self) -> None:
        """增加使用次数"""
        self.usage_count += 1
    
    def update_success_rate(self, successful_count: int) -> None:
        """
        更新成功率
        
        Args:
            successful_count: 成功次数
        """
        if self.usage_count > 0:
            self.success_rate = successful_count / self.usage_count
    
    def update_avg_quality_score(self, total_score: float, content_count: int) -> None:
        """
        更新平均质量分数
        
        Args:
            total_score: 总分数
            content_count: 内容数量
        """
        if content_count > 0:
            self.avg_quality_score = total_score / content_count
    
    def __repr__(self):
        return f"<ContentTemplate(name='{self.name}', type='{self.template_type}', active={self.is_active})>"


class ContentStateTransition(Base):
    """
    内容状态转换模型
    
    记录内容状态变化的审计日志
    """
    __tablename__ = "content_state_transitions"
    __table_args__ = {'comment': '内容状态转换表'}
    
    # 关联信息
    content_id = Column(
        UUID(as_uuid=True),
        ForeignKey('contents.id'),
        nullable=False,
        comment="内容ID"
    )
    
    # 状态信息
    from_state = Column(
        String(20),
        nullable=True,
        comment="原状态"
    )
    to_state = Column(
        String(20),
        nullable=False,
        comment="新状态"
    )
    
    # 变更信息
    reason = Column(
        Text,
        nullable=True,
        comment="变更原因"
    )
    operator = Column(
        String(50),
        default='system',
        comment="操作者"
    )
    
    # 扩展信息
    extra_data = Column(
        JSONB,
        default=dict,
        comment="扩展信息"
    )
    
    # 关系定义
    content = relationship("Content", back_populates="state_transitions")
    
    def __repr__(self):
        return f"<ContentStateTransition(content_id='{self.content_id}', {self.from_state}->{self.to_state})>"


# 导出所有模型
__all__ = [
    "HotTopic",
    "Content", 
    "PublishRecord",
    "ContentMetrics",
    "ContentTemplate",
    "ContentStateTransition",
    "ContentSource",
    "ContentCategory",
    "ContentStatus",
    "PublishStatus",
    "TemplateType"
]