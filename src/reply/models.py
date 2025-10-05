"""
智能回复模块数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from ..config.database import Base


class ReplyStatus(str, Enum):
    """回复状态枚举"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ReplyType(str, Enum):
    """回复类型枚举"""
    AUTO = "auto"
    TEMPLATE = "template"
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"


class ReplyTemplate(Base):
    """回复模板数据库模型"""
    
    __tablename__ = "reply_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("douyin_accounts.id"), nullable=False, index=True)
    
    # 模板信息
    template_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # 法律咨询、感谢赞扬等
    subcategory = Column(String(100), nullable=True)  # 细分类别
    
    # 模板内容
    content = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # 可替换变量
    
    # 触发条件
    keywords = Column(JSON, nullable=True)  # 关键词列表
    sentiment = Column(String(50), nullable=True)  # 情感倾向
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # 成功率
    
    # 配置
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高
    
    # 时间限制
    time_restrictions = Column(JSON, nullable=True)  # 时间限制配置
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class ReplyRecord(Base):
    """回复记录数据库模型"""
    
    __tablename__ = "reply_records"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("douyin_accounts.id"), nullable=False, index=True)
    comment_id = Column(Integer, ForeignKey("comment_data.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("reply_templates.id"), nullable=True, index=True)
    
    # 回复信息
    reply_content = Column(Text, nullable=False)
    reply_type = Column(String(20), nullable=False, default=ReplyType.AUTO.value)
    status = Column(String(20), nullable=False, default=ReplyStatus.PENDING.value)
    
    # 原始评论信息（冗余存储便于分析）
    original_comment = Column(Text, nullable=True)
    original_author = Column(String(100), nullable=True)
    comment_category = Column(String(100), nullable=True)
    
    # AI生成信息
    ai_model = Column(String(50), nullable=True)  # 使用的AI模型
    ai_prompt = Column(Text, nullable=True)  # AI提示词
    confidence_score = Column(Float, nullable=True)  # 置信度评分
    
    # 执行信息
    platform_reply_id = Column(String(100), nullable=True)  # 平台返回的回复ID
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # 效果评估
    engagement_score = Column(Float, nullable=True)  # 互动效果评分
    follow_up_comments = Column(Integer, default=0)  # 后续评论数
    conversion_result = Column(String(50), nullable=True)  # 转化结果
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    
    # 关系
    template = relationship("ReplyTemplate")


class ReplyRule(Base):
    """回复规则数据库模型"""
    
    __tablename__ = "reply_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("douyin_accounts.id"), nullable=False, index=True)
    
    # 规则信息
    rule_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # 触发条件
    conditions = Column(JSON, nullable=False)  # 触发条件配置
    
    # 动作配置
    actions = Column(JSON, nullable=False)  # 动作配置
    
    # 限制条件
    rate_limit = Column(JSON, nullable=True)  # 频率限制
    time_restrictions = Column(JSON, nullable=True)  # 时间限制
    
    # 统计信息
    trigger_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)


# Pydantic模型用于API交互

class ReplyTemplateCreate(BaseModel):
    """创建回复模板请求模型"""
    account_id: int = Field(..., description="账号ID")
    template_name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    category: str = Field(..., min_length=1, max_length=100, description="分类")
    subcategory: Optional[str] = Field(None, max_length=100, description="子分类")
    content: str = Field(..., min_length=1, description="模板内容")
    variables: Optional[List[str]] = Field(None, description="可替换变量")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    sentiment: Optional[str] = Field(None, description="情感倾向")
    priority: int = Field(default=0, description="优先级")
    is_active: bool = Field(default=True, description="是否启用")


class ReplyTemplateUpdate(BaseModel):
    """更新回复模板请求模型"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=200, description="模板名称")
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="分类")
    subcategory: Optional[str] = Field(None, max_length=100, description="子分类")
    content: Optional[str] = Field(None, min_length=1, description="模板内容")
    variables: Optional[List[str]] = Field(None, description="可替换变量")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    sentiment: Optional[str] = Field(None, description="情感倾向")
    priority: Optional[int] = Field(None, description="优先级")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ReplyTemplateResponse(BaseModel):
    """回复模板响应模型"""
    id: int
    account_id: int
    template_name: str
    category: str
    subcategory: Optional[str]
    content: str
    variables: Optional[List[str]]
    keywords: Optional[List[str]]
    sentiment: Optional[str]
    usage_count: int
    success_rate: float
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]


class ReplyRequest(BaseModel):
    """回复请求模型"""
    comment_id: int = Field(..., description="评论ID")
    account_id: int = Field(..., description="账号ID")
    reply_type: ReplyType = Field(default=ReplyType.AUTO, description="回复类型")
    template_id: Optional[int] = Field(None, description="指定模板ID")
    custom_content: Optional[str] = Field(None, description="自定义内容")
    scheduled_at: Optional[datetime] = Field(None, description="定时发送时间")
    variables: Optional[Dict[str, str]] = Field(None, description="模板变量值")


class AIReplyRequest(BaseModel):
    """AI回复请求模型"""
    comment_content: str = Field(..., description="评论内容")
    comment_author: Optional[str] = Field(None, description="评论作者")
    video_title: Optional[str] = Field(None, description="视频标题")
    context: Optional[str] = Field(None, description="上下文信息")
    reply_style: str = Field(default="professional", description="回复风格")
    max_length: int = Field(default=200, ge=10, le=500, description="最大长度")
    include_call_to_action: bool = Field(default=True, description="包含行动召唤")


class AIReplyResponse(BaseModel):
    """AI回复响应模型"""
    success: bool
    reply_content: Optional[str]
    confidence_score: Optional[float]
    category: Optional[str]
    sentiment: Optional[str]
    call_to_action: Optional[str]
    error_message: Optional[str]


class ReplyRecordResponse(BaseModel):
    """回复记录响应模型"""
    id: int
    account_id: int
    comment_id: int
    template_id: Optional[int]
    reply_content: str
    reply_type: ReplyType
    status: ReplyStatus
    original_comment: Optional[str]
    original_author: Optional[str]
    ai_model: Optional[str]
    confidence_score: Optional[float]
    platform_reply_id: Optional[str]
    engagement_score: Optional[float]
    conversion_result: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]


class ReplyStats(BaseModel):
    """回复统计模型"""
    total_replies: int
    successful_replies: int
    failed_replies: int
    pending_replies: int
    average_response_time: float
    conversion_rate: float
    top_templates: List[Dict[str, Any]]
    reply_distribution: Dict[str, int]
    engagement_metrics: Dict[str, float]


class BatchReplyRequest(BaseModel):
    """批量回复请求模型"""
    comment_ids: List[int] = Field(..., min_items=1, max_items=50, description="评论ID列表")
    account_id: int = Field(..., description="账号ID")
    reply_type: ReplyType = Field(default=ReplyType.AUTO, description="回复类型")
    template_id: Optional[int] = Field(None, description="指定模板ID")
    delay_between_replies: int = Field(default=30, ge=10, le=300, description="回复间隔（秒）")


class TemplateTestRequest(BaseModel):
    """模板测试请求模型"""
    template_id: int = Field(..., description="模板ID")
    test_comments: List[str] = Field(..., min_items=1, max_items=10, description="测试评论列表")
    variables: Optional[Dict[str, str]] = Field(None, description="测试变量值")
