"""
监测引擎数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from ..config.database import Base


class MonitorStatus(str, Enum):
    """监测状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class ContentType(str, Enum):
    """内容类型枚举"""
    VIDEO = "video"
    LIVE = "live"
    POST = "post"


class CommentType(str, Enum):
    """评论类型枚举"""
    COMMENT = "comment"
    REPLY = "reply"
    MENTION = "mention"


class MonitorTask(Base):
    """监测任务数据库模型"""
    
    __tablename__ = "monitor_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("douyin_accounts.id"), nullable=False, index=True)
    
    # 任务信息
    task_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=MonitorStatus.ACTIVE.value)
    
    # 监测配置
    monitor_videos = Column(Boolean, default=True)
    monitor_comments = Column(Boolean, default=True)
    monitor_messages = Column(Boolean, default=True)
    monitor_mentions = Column(Boolean, default=True)
    
    # 关键词配置
    keywords = Column(JSON, nullable=True)  # 关键词列表
    exclude_keywords = Column(JSON, nullable=True)  # 排除关键词
    
    # 频率控制
    check_interval = Column(Integer, default=300)  # 检查间隔（秒）
    max_videos_per_check = Column(Integer, default=10)
    
    # 过滤配置
    min_comment_length = Column(Integer, default=5)
    max_comment_length = Column(Integer, default=500)
    filter_spam = Column(Boolean, default=True)
    
    # 统计信息
    total_videos_monitored = Column(Integer, default=0)
    total_comments_found = Column(Integer, default=0)
    total_replies_sent = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_check_at = Column(DateTime, nullable=True)
    next_check_at = Column(DateTime, nullable=True)
    
    # 关系
    videos = relationship("VideoData", back_populates="monitor_task")
    comments = relationship("CommentData", back_populates="monitor_task")


class VideoData(Base):
    """视频数据模型"""
    
    __tablename__ = "video_data"
    
    id = Column(Integer, primary_key=True, index=True)
    monitor_task_id = Column(Integer, ForeignKey("monitor_tasks.id"), nullable=False, index=True)
    
    # 视频信息
    video_id = Column(String(100), unique=True, index=True, nullable=False)
    video_url = Column(String(500), nullable=False)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # 创作者信息
    author_name = Column(String(100), nullable=True)
    author_id = Column(String(100), nullable=True)
    
    # 统计数据
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # 内容分类
    content_type = Column(String(20), default=ContentType.VIDEO.value)
    tags = Column(JSON, nullable=True)  # 标签列表
    
    # 监测状态
    is_monitored = Column(Boolean, default=True)
    last_monitored_at = Column(DateTime, nullable=True)
    
    # 时间戳
    publish_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    monitor_task = relationship("MonitorTask", back_populates="videos")
    comments = relationship("CommentData", back_populates="video")


class CommentData(Base):
    """评论数据模型"""
    
    __tablename__ = "comment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    monitor_task_id = Column(Integer, ForeignKey("monitor_tasks.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("video_data.id"), nullable=True, index=True)
    
    # 评论信息
    comment_id = Column(String(100), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    comment_type = Column(String(20), default=CommentType.COMMENT.value)
    
    # 评论者信息
    author_name = Column(String(100), nullable=True)
    author_id = Column(String(100), nullable=True, index=True)
    author_avatar = Column(String(500), nullable=True)
    
    # 父评论信息（用于回复）
    parent_comment_id = Column(String(100), nullable=True, index=True)
    
    # 互动数据
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # 分类和标签
    sentiment = Column(String(20), nullable=True)  # 情感分析结果
    category = Column(String(50), nullable=True)  # 内容分类
    keywords_matched = Column(JSON, nullable=True)  # 匹配的关键词
    
    # 处理状态
    is_processed = Column(Boolean, default=False)
    is_replied = Column(Boolean, default=False)
    reply_id = Column(String(100), nullable=True)
    reply_content = Column(Text, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    
    # 质量评分
    quality_score = Column(Float, nullable=True)  # 0-1分数
    is_spam = Column(Boolean, default=False)
    
    # 时间戳
    comment_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    monitor_task = relationship("MonitorTask", back_populates="comments")
    video = relationship("VideoData", back_populates="comments")


# Pydantic模型用于API交互

class MonitorTaskCreate(BaseModel):
    """创建监测任务请求模型"""
    account_id: int = Field(..., description="账号ID")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    
    # 监测配置
    monitor_videos: bool = Field(default=True, description="监测视频")
    monitor_comments: bool = Field(default=True, description="监测评论")
    monitor_messages: bool = Field(default=True, description="监测私信")
    monitor_mentions: bool = Field(default=True, description="监测@提及")
    
    # 关键词配置
    keywords: Optional[List[str]] = Field(default=None, description="监测关键词")
    exclude_keywords: Optional[List[str]] = Field(default=None, description="排除关键词")
    
    # 频率控制
    check_interval: int = Field(default=300, ge=60, le=3600, description="检查间隔（秒）")
    max_videos_per_check: int = Field(default=10, ge=1, le=50, description="每次检查最大视频数")
    
    # 过滤配置
    min_comment_length: int = Field(default=5, ge=1, description="最小评论长度")
    max_comment_length: int = Field(default=500, ge=10, description="最大评论长度")
    filter_spam: bool = Field(default=True, description="过滤垃圾评论")


class MonitorTaskUpdate(BaseModel):
    """更新监测任务请求模型"""
    task_name: Optional[str] = Field(None, min_length=1, max_length=200, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    status: Optional[MonitorStatus] = Field(None, description="任务状态")
    
    monitor_videos: Optional[bool] = Field(None, description="监测视频")
    monitor_comments: Optional[bool] = Field(None, description="监测评论")
    monitor_messages: Optional[bool] = Field(None, description="监测私信")
    monitor_mentions: Optional[bool] = Field(None, description="监测@提及")
    
    keywords: Optional[List[str]] = Field(None, description="监测关键词")
    exclude_keywords: Optional[List[str]] = Field(None, description="排除关键词")
    
    check_interval: Optional[int] = Field(None, ge=60, le=3600, description="检查间隔（秒）")
    max_videos_per_check: Optional[int] = Field(None, ge=1, le=50, description="每次检查最大视频数")
    
    min_comment_length: Optional[int] = Field(None, ge=1, description="最小评论长度")
    max_comment_length: Optional[int] = Field(None, ge=10, description="最大评论长度")
    filter_spam: Optional[bool] = Field(None, description="过滤垃圾评论")


class MonitorTaskResponse(BaseModel):
    """监测任务响应模型"""
    id: int
    account_id: int
    task_name: str
    description: Optional[str]
    status: MonitorStatus
    
    monitor_videos: bool
    monitor_comments: bool
    monitor_messages: bool
    monitor_mentions: bool
    
    keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    
    check_interval: int
    max_videos_per_check: int
    
    total_videos_monitored: int
    total_comments_found: int
    total_replies_sent: int
    
    created_at: datetime
    updated_at: datetime
    last_check_at: Optional[datetime]
    next_check_at: Optional[datetime]


class VideoDataResponse(BaseModel):
    """视频数据响应模型"""
    id: int
    video_id: str
    video_url: str
    title: Optional[str]
    author_name: Optional[str]
    
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    
    content_type: ContentType
    tags: Optional[List[str]]
    
    is_monitored: bool
    last_monitored_at: Optional[datetime]
    publish_time: Optional[datetime]
    created_at: datetime


class CommentDataResponse(BaseModel):
    """评论数据响应模型"""
    id: int
    comment_id: str
    content: str
    comment_type: CommentType
    
    author_name: Optional[str]
    author_id: Optional[str]
    
    like_count: int
    reply_count: int
    
    sentiment: Optional[str]
    category: Optional[str]
    keywords_matched: Optional[List[str]]
    
    is_processed: bool
    is_replied: bool
    reply_content: Optional[str]
    replied_at: Optional[datetime]
    
    quality_score: Optional[float]
    is_spam: bool
    
    comment_time: Optional[datetime]
    created_at: datetime


class MonitorStats(BaseModel):
    """监测统计模型"""
    total_tasks: int
    active_tasks: int
    total_videos: int
    total_comments: int
    total_replies: int
    avg_response_time: float
    success_rate: float
