"""
认证模块异常类
"""

from typing import Optional, Dict, Any
from ..core.exceptions import MCPError


class AuthError(MCPError):
    """认证基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTH_ERROR", details)


class LoginError(AuthError):
    """登录异常"""
    
    def __init__(self, message: str, login_type: str = "", details: Optional[Dict[str, Any]] = None):
        self.login_type = login_type
        details = details or {}
        details["login_type"] = login_type
        super().__init__(message, details)
        self.error_code = "LOGIN_ERROR"


class SessionError(AuthError):
    """会话异常"""
    
    def __init__(self, message: str, session_token: str = "", details: Optional[Dict[str, Any]] = None):
        self.session_token = session_token
        details = details or {}
        details["session_token"] = session_token
        super().__init__(message, details)
        self.error_code = "SESSION_ERROR"


class AccountNotFoundError(AuthError):
    """账号不存在异常"""
    
    def __init__(self, username: str):
        message = f"账号 {username} 不存在"
        details = {"username": username}
        super().__init__(message, details)
        self.error_code = "ACCOUNT_NOT_FOUND"


class AccountExistsError(AuthError):
    """账号已存在异常"""
    
    def __init__(self, username: str):
        message = f"账号 {username} 已存在"
        details = {"username": username}
        super().__init__(message, details)
        self.error_code = "ACCOUNT_EXISTS"


class AccountSuspendedError(AuthError):
    """账号被暂停异常"""
    
    def __init__(self, username: str, reason: str = ""):
        message = f"账号 {username} 已被暂停"
        if reason:
            message += f": {reason}"
        details = {"username": username, "reason": reason}
        super().__init__(message, details)
        self.error_code = "ACCOUNT_SUSPENDED"


class LoginFailedError(LoginError):
    """登录失败异常"""
    
    def __init__(self, reason: str, login_type: str = "", attempts: int = 0):
        message = f"登录失败: {reason}"
        details = {"reason": reason, "attempts": attempts}
        super().__init__(message, login_type, details)
        self.error_code = "LOGIN_FAILED"


class QRCodeExpiredError(LoginError):
    """二维码过期异常"""
    
    def __init__(self, qr_uuid: str = ""):
        message = "二维码已过期，请重新获取"
        details = {"qr_uuid": qr_uuid}
        super().__init__(message, "qrcode", details)
        self.error_code = "QR_CODE_EXPIRED"


class SMSCodeInvalidError(LoginError):
    """短信验证码无效异常"""
    
    def __init__(self, phone_number: str = ""):
        message = "短信验证码无效或已过期"
        details = {"phone_number": phone_number}
        super().__init__(message, "sms", details)
        self.error_code = "SMS_CODE_INVALID"


class PasswordIncorrectError(LoginError):
    """密码错误异常"""
    
    def __init__(self, username: str = ""):
        message = "用户名或密码错误"
        details = {"username": username}
        super().__init__(message, "password", details)
        self.error_code = "PASSWORD_INCORRECT"


class CaptchaRequiredError(LoginError):
    """需要验证码异常"""
    
    def __init__(self, captcha_url: str = "", login_type: str = ""):
        message = "需要验证码验证"
        details = {"captcha_url": captcha_url}
        super().__init__(message, login_type, details)
        self.error_code = "CAPTCHA_REQUIRED"


class RiskControlError(LoginError):
    """风控异常"""
    
    def __init__(self, message: str = "触发平台风控，请稍后重试", login_type: str = ""):
        details = {"risk_control": True}
        super().__init__(message, login_type, details)
        self.error_code = "RISK_CONTROL"


class BrowserError(AuthError):
    """浏览器异常"""
    
    def __init__(self, message: str, browser_type: str = ""):
        details = {"browser_type": browser_type}
        super().__init__(message, details)
        self.error_code = "BROWSER_ERROR"


class CookieInvalidError(AuthError):
    """Cookie无效异常"""
    
    def __init__(self, username: str = ""):
        message = "Cookie已失效，请重新登录"
        details = {"username": username}
        super().__init__(message, details)
        self.error_code = "COOKIE_INVALID"
