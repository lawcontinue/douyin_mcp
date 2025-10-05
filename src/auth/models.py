"""
认证模块数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

from ..config.database import Base


class LoginType(str, Enum):
    """登录类型枚举"""
    QRCODE = "qrcode"
    SMS = "sms"
    PASSWORD = "password"
    COOKIE = "cookie"


class AccountStatus(str, Enum):
    """账号状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"
    LOGIN_REQUIRED = "login_required"


class DouyinAccount(Base):
    """抖音账号数据库模型"""
    
    __tablename__ = "douyin_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    douyin_id = Column(String(50), nullable=True, index=True)
    
    # 认证信息
    login_type = Column(String(20), nullable=False, default=LoginType.QRCODE)
    encrypted_password = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # 状态信息
    status = Column(String(20), nullable=False, default=AccountStatus.INACTIVE)
    is_verified = Column(Boolean, default=False)
    
    # 会话信息
    session_data = Column(JSON, nullable=True)
    cookies = Column(Text, nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # 监控配置
    enable_monitoring = Column(Boolean, default=True)
    enable_auto_reply = Column(Boolean, default=True)
    max_replies_per_hour = Column(Integer, default=10)
    
    # 统计信息
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "douyin_id": self.douyin_id,
            "login_type": self.login_type,
            "status": self.status,
            "is_verified": self.is_verified,
            "enable_monitoring": self.enable_monitoring,
            "enable_auto_reply": self.enable_auto_reply,
            "max_replies_per_hour": self.max_replies_per_hour,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "video_count": self.video_count,
            "like_count": self.like_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }


class LoginSession(Base):
    """登录会话数据库模型"""
    
    __tablename__ = "login_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    session_token = Column(String(100), unique=True, index=True, nullable=False)
    
    # 会话信息
    browser_fingerprint = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow)


# Pydantic模型用于API交互

class AccountCreate(BaseModel):
    """创建账号请求模型"""
    username: str = Field(..., min_length=1, max_length=100, description="用户名")
    login_type: LoginType = Field(default=LoginType.QRCODE, description="登录类型")
    password: Optional[str] = Field(None, description="密码（仅密码登录时需要）")
    phone_number: Optional[str] = Field(None, description="手机号（仅短信登录时需要）")
    enable_monitoring: bool = Field(default=True, description="启用监控")
    enable_auto_reply: bool = Field(default=True, description="启用自动回复")
    max_replies_per_hour: int = Field(default=10, ge=1, le=100, description="每小时最大回复数")


class AccountUpdate(BaseModel):
    """更新账号请求模型"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    enable_monitoring: Optional[bool] = Field(None, description="启用监控")
    enable_auto_reply: Optional[bool] = Field(None, description="启用自动回复")
    max_replies_per_hour: Optional[int] = Field(None, ge=1, le=100, description="每小时最大回复数")
    status: Optional[AccountStatus] = Field(None, description="账号状态")


class AccountResponse(BaseModel):
    """账号响应模型"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    douyin_id: Optional[str] = None
    login_type: LoginType
    status: AccountStatus
    is_verified: bool
    enable_monitoring: bool
    enable_auto_reply: bool
    max_replies_per_hour: int
    follower_count: int
    following_count: int
    video_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    login_type: LoginType = Field(default=LoginType.QRCODE, description="登录类型")
    password: Optional[str] = Field(None, description="密码")
    sms_code: Optional[str] = Field(None, description="短信验证码")
    qr_uuid: Optional[str] = Field(None, description="二维码UUID")


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    message: str
    account_id: Optional[int] = None
    session_token: Optional[str] = None
    qr_code_url: Optional[str] = None
    qr_uuid: Optional[str] = None
    expires_at: Optional[datetime] = None


class QRCodeStatus(BaseModel):
    """二维码状态模型"""
    status: str  # waiting, scanned, confirmed, expired
    message: str
    account_info: Optional[Dict[str, Any]] = None


class AccountStats(BaseModel):
    """账号统计模型"""
    total_accounts: int
    active_accounts: int
    monitoring_accounts: int
    auto_reply_accounts: int
    total_followers: int
    total_videos: int
    login_success_rate: float
