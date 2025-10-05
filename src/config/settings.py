"""
应用配置设置
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # 基础配置
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8002, env="API_PORT")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # 数据库配置
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/douyin_mcp.db", env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # 抖音配置
    DOUYIN_USERNAME: Optional[str] = Field(default=None, env="DOUYIN_USERNAME")
    DOUYIN_PASSWORD: Optional[str] = Field(default=None, env="DOUYIN_PASSWORD")
    DOUYIN_LOGIN_TYPE: str = Field(default="qrcode", env="DOUYIN_LOGIN_TYPE")
    DOUYIN_USER_AGENT: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="DOUYIN_USER_AGENT"
    )
    
    # AI配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-haiku-20240307", env="ANTHROPIC_MODEL")
    
    # 监控配置
    MONITOR_INTERVAL: int = Field(default=300, env="MONITOR_INTERVAL")  # 秒
    MAX_REPLIES_PER_HOUR: int = Field(default=10, env="MAX_REPLIES_PER_HOUR")
    ENABLE_AUTO_REPLY: bool = Field(default=True, env="ENABLE_AUTO_REPLY")
    MONITOR_MAX_VIDEOS: int = Field(default=50, env="MONITOR_MAX_VIDEOS")
    
    # 代理配置
    PROXY_ENABLED: bool = Field(default=False, env="PROXY_ENABLED")
    PROXY_URL: Optional[str] = Field(default=None, env="PROXY_URL")
    PROXY_USERNAME: Optional[str] = Field(default=None, env="PROXY_USERNAME")
    PROXY_PASSWORD: Optional[str] = Field(default=None, env="PROXY_PASSWORD")
    
    # 缓存配置
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 秒
    ENABLE_REDIS_CACHE: bool = Field(default=True, env="ENABLE_REDIS_CACHE")
    
    # 安全配置
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # 通知配置
    WEBHOOK_URL: Optional[str] = Field(default=None, env="WEBHOOK_URL")
    EMAIL_ENABLED: bool = Field(default=False, env="EMAIL_ENABLED")
    EMAIL_SMTP_HOST: Optional[str] = Field(default=None, env="EMAIL_SMTP_HOST")
    EMAIL_SMTP_PORT: int = Field(default=587, env="EMAIL_SMTP_PORT")
    EMAIL_USERNAME: Optional[str] = Field(default=None, env="EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = Field(default=None, env="EMAIL_PASSWORD")
    
    # 文件上传配置
    UPLOAD_MAX_SIZE: int = Field(default=10485760, env="UPLOAD_MAX_SIZE")  # 10MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".mp4", ".avi"],
        env="ALLOWED_EXTENSIONS"
    )
    UPLOAD_DIR: str = Field(default="data/uploads", env="UPLOAD_DIR")
    
    # 风险控制
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    MAX_REQUESTS_PER_MINUTE: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    ENABLE_CONTENT_FILTER: bool = Field(default=True, env="ENABLE_CONTENT_FILTER")
    
    # 浏览器配置
    BROWSER_HEADLESS: bool = Field(default=True, env="BROWSER_HEADLESS")
    BROWSER_TIMEOUT: int = Field(default=30000, env="BROWSER_TIMEOUT")  # 毫秒
    BROWSER_USER_DATA_DIR: Optional[str] = Field(default=None, env="BROWSER_USER_DATA_DIR")
    
    # 数据导出配置
    EXPORT_MAX_RECORDS: int = Field(default=10000, env="EXPORT_MAX_RECORDS")
    EXPORT_FORMATS: List[str] = Field(default=["csv", "json", "xlsx"], env="EXPORT_FORMATS")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @validator("EXPORT_FORMATS", pre=True)
    def parse_export_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("DOUYIN_LOGIN_TYPE")
    def validate_login_type(cls, v):
        valid_types = ["qrcode", "sms", "password"]
        if v not in valid_types:
            raise ValueError(f"DOUYIN_LOGIN_TYPE must be one of {valid_types}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()
