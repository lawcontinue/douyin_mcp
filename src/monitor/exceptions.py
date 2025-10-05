"""
监测模块异常类
"""

from typing import Optional, Dict, Any
from ..core.exceptions import MCPError


class MonitorError(MCPError):
    """监测基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "MONITOR_ERROR", details)


class TaskNotFoundError(MonitorError):
    """监测任务不存在异常"""
    
    def __init__(self, task_id: int):
        message = f"监测任务 {task_id} 不存在"
        details = {"task_id": task_id}
        super().__init__(message, details)
        self.error_code = "TASK_NOT_FOUND"


class TaskAlreadyRunningError(MonitorError):
    """任务已在运行异常"""
    
    def __init__(self, task_id: int):
        message = f"监测任务 {task_id} 已在运行中"
        details = {"task_id": task_id}
        super().__init__(message, details)
        self.error_code = "TASK_ALREADY_RUNNING"


class VideoNotFoundError(MonitorError):
    """视频不存在异常"""
    
    def __init__(self, video_id: str):
        message = f"视频 {video_id} 不存在"
        details = {"video_id": video_id}
        super().__init__(message, details)
        self.error_code = "VIDEO_NOT_FOUND"


class CommentNotFoundError(MonitorError):
    """评论不存在异常"""
    
    def __init__(self, comment_id: str):
        message = f"评论 {comment_id} 不存在"
        details = {"comment_id": comment_id}
        super().__init__(message, details)
        self.error_code = "COMMENT_NOT_FOUND"


class ScrapingError(MonitorError):
    """数据抓取异常"""
    
    def __init__(self, message: str, url: str = "", details: Optional[Dict[str, Any]] = None):
        self.url = url
        details = details or {}
        details["url"] = url
        super().__init__(message, details)
        self.error_code = "SCRAPING_ERROR"


class RateLimitExceededError(MonitorError):
    """频率限制超出异常"""
    
    def __init__(self, message: str = "请求频率过高，请稍后重试", retry_after: int = 300):
        self.retry_after = retry_after
        details = {"retry_after": retry_after}
        super().__init__(message, details)
        self.error_code = "RATE_LIMIT_EXCEEDED"


class ContentFilterError(MonitorError):
    """内容过滤异常"""
    
    def __init__(self, message: str, content: str = "", filter_type: str = ""):
        details = {"content": content[:100], "filter_type": filter_type}
        super().__init__(message, details)
        self.error_code = "CONTENT_FILTER_ERROR"


class BrowserConnectionError(MonitorError):
    """浏览器连接异常"""
    
    def __init__(self, message: str = "浏览器连接失败"):
        super().__init__(message)
        self.error_code = "BROWSER_CONNECTION_ERROR"


class LoginRequiredError(MonitorError):
    """需要登录异常"""
    
    def __init__(self, account_id: int):
        message = f"账号 {account_id} 需要重新登录"
        details = {"account_id": account_id}
        super().__init__(message, details)
        self.error_code = "LOGIN_REQUIRED"
