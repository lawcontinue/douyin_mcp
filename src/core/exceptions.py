"""
自定义异常类
"""

from typing import Any, Dict, Optional


class MCPError(Exception):
    """MCP服务基础异常"""
    
    def __init__(self, message: str, error_code: str = "MCP_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class AuthError(MCPError):
    """认证相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTH_ERROR", details)


class MonitorError(MCPError):
    """监测相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "MONITOR_ERROR", details)


class ReplyError(MCPError):
    """回复相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "REPLY_ERROR", details)


class AnalyticsError(MCPError):
    """分析相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ANALYTICS_ERROR", details)


class ContentError(MCPError):
    """内容分析相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONTENT_ERROR", details)


class ConfigError(MCPError):
    """配置相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class RateLimitError(MCPError):
    """频率限制异常"""
    
    def __init__(self, message: str, retry_after: int = 60, details: Optional[Dict[str, Any]] = None):
        self.retry_after = retry_after
        details = details or {}
        details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class ValidationError(MCPError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str, value: Any = None, details: Optional[Dict[str, Any]] = None):
        self.field = field
        self.value = value
        details = details or {}
        details.update({"field": field, "value": value})
        super().__init__(message, "VALIDATION_ERROR", details)
