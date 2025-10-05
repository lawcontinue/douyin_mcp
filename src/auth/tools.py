"""
认证模块MCP工具注册
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from loguru import logger

from ..core.tool_registry import tool_registry, ToolDefinition, ToolParameter
from ..config.database import get_db
from .auth_manager import AuthManager
from .models import AccountCreate, AccountUpdate, LoginRequest, AccountResponse, LoginResponse, QRCodeStatus


# 创建认证管理器实例
auth_manager = AuthManager()


async def login_douyin_account(
    username: str,
    login_type: str = "qrcode",
    password: Optional[str] = None,
    sms_code: Optional[str] = None,
    qr_uuid: Optional[str] = None,
    cookie_file: Optional[str] = None
) -> Dict[str, Any]:
    """登录抖音账号"""
    try:
        async for db in get_db():
            if login_type == "qrcode":
                if qr_uuid:
                    # 检查二维码状态
                    result = await auth_manager.check_qrcode_status(qr_uuid, db)
                    return {
                        "success": True,
                        "status": result.status,
                        "message": result.message,
                        "account_info": result.account_info
                    }
                else:
                    # 获取新的二维码
                    result = await auth_manager.login_with_qrcode(username, db)
                    return {
                        "success": result.success,
                        "message": result.message,
                        "qr_code_url": result.qr_code_url,
                        "qr_uuid": result.qr_uuid
                    }
            
            elif login_type == "password":
                if not password:
                    return {
                        "success": False,
                        "message": "密码登录需要提供密码"
                    }
                
                login_request = LoginRequest(
                    username=username,
                    login_type=login_type,
                    password=password
                )
                
                result = await auth_manager.login_with_password(login_request, db)
                return {
                    "success": result.success,
                    "message": result.message,
                    "account_id": result.account_id,
                    "session_token": result.session_token
                }
            
            elif login_type == "cookie":
                # Cookie登录
                from .browser_manager import BrowserManager
                browser_manager = BrowserManager()
                try:
                    result = await browser_manager.login_with_cookies(cookie_file)
                    return result
                finally:
                    await browser_manager.cleanup()
            
            else:
                return {
                    "success": False,
                    "message": f"不支持的登录类型: {login_type}"
                }
                
    except Exception as e:
        logger.error(f"登录抖音账号失败: {e}")
        return {
            "success": False,
            "message": f"登录失败: {e}"
        }


async def create_douyin_account(
    username: str,
    login_type: str = "qrcode",
    password: Optional[str] = None,
    phone_number: Optional[str] = None,
    enable_monitoring: bool = True,
    enable_auto_reply: bool = True,
    max_replies_per_hour: int = 10
) -> Dict[str, Any]:
    """创建抖音账号"""
    try:
        async for db in get_db():
            account_data = AccountCreate(
                username=username,
                login_type=login_type,
                password=password,
                phone_number=phone_number,
                enable_monitoring=enable_monitoring,
                enable_auto_reply=enable_auto_reply,
                max_replies_per_hour=max_replies_per_hour
            )
            
            account = await auth_manager.create_account(account_data, db)
            
            return {
                "success": True,
                "message": "账号创建成功",
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "login_type": account.login_type,
                    "status": account.status,
                    "created_at": account.created_at.isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"创建抖音账号失败: {e}")
        return {
            "success": False,
            "message": f"创建账号失败: {e}"
        }


async def get_douyin_accounts(
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """获取抖音账号列表"""
    try:
        async for db in get_db():
            accounts = await auth_manager.list_accounts(db, limit, offset)
            
            account_list = []
            for account in accounts:
                account_list.append({
                    "id": account.id,
                    "username": account.username,
                    "nickname": account.nickname,
                    "status": account.status,
                    "login_type": account.login_type,
                    "enable_monitoring": account.enable_monitoring,
                    "enable_auto_reply": account.enable_auto_reply,
                    "follower_count": account.follower_count,
                    "last_login_at": account.last_login_at.isoformat() if account.last_login_at else None,
                    "created_at": account.created_at.isoformat()
                })
            
            return {
                "success": True,
                "accounts": account_list,
                "total": len(account_list)
            }
            
    except Exception as e:
        logger.error(f"获取账号列表失败: {e}")
        return {
            "success": False,
            "message": f"获取账号列表失败: {e}",
            "accounts": []
        }


async def update_douyin_account(
    account_id: int,
    nickname: Optional[str] = None,
    enable_monitoring: Optional[bool] = None,
    enable_auto_reply: Optional[bool] = None,
    max_replies_per_hour: Optional[int] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """更新抖音账号信息"""
    try:
        async for db in get_db():
            # 构建更新数据
            update_data = AccountUpdate()
            if nickname is not None:
                update_data.nickname = nickname
            if enable_monitoring is not None:
                update_data.enable_monitoring = enable_monitoring
            if enable_auto_reply is not None:
                update_data.enable_auto_reply = enable_auto_reply
            if max_replies_per_hour is not None:
                update_data.max_replies_per_hour = max_replies_per_hour
            if status is not None:
                update_data.status = status
            
            account = await auth_manager.update_account(account_id, update_data, db)
            
            return {
                "success": True,
                "message": "账号更新成功",
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "nickname": account.nickname,
                    "status": account.status,
                    "enable_monitoring": account.enable_monitoring,
                    "enable_auto_reply": account.enable_auto_reply,
                    "max_replies_per_hour": account.max_replies_per_hour,
                    "updated_at": account.updated_at.isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"更新账号失败: {e}")
        return {
            "success": False,
            "message": f"更新账号失败: {e}"
        }


async def delete_douyin_account(account_id: int) -> Dict[str, Any]:
    """删除抖音账号"""
    try:
        async for db in get_db():
            success = await auth_manager.delete_account(account_id, db)
            
            if success:
                return {
                    "success": True,
                    "message": "账号删除成功"
                }
            else:
                return {
                    "success": False,
                    "message": "账号删除失败"
                }
                
    except Exception as e:
        logger.error(f"删除账号失败: {e}")
        return {
            "success": False,
            "message": f"删除账号失败: {e}"
        }


async def logout_douyin_account(session_token: str) -> Dict[str, Any]:
    """登出抖音账号"""
    try:
        async for db in get_db():
            success = await auth_manager.logout(session_token, db)
            
            return {
                "success": success,
                "message": "登出成功" if success else "登出失败"
            }
            
    except Exception as e:
        logger.error(f"登出失败: {e}")
        return {
            "success": False,
            "message": f"登出失败: {e}"
        }


async def validate_session(session_token: str) -> Dict[str, Any]:
    """验证会话状态"""
    try:
        async for db in get_db():
            account = await auth_manager.validate_session(session_token, db)
            
            if account:
                return {
                    "success": True,
                    "valid": True,
                    "account": {
                        "id": account.id,
                        "username": account.username,
                        "nickname": account.nickname,
                        "status": account.status
                    }
                }
            else:
                return {
                    "success": True,
                    "valid": False,
                    "message": "会话无效或已过期"
                }
                
    except Exception as e:
        logger.error(f"验证会话失败: {e}")
        return {
            "success": False,
            "message": f"验证会话失败: {e}"
        }


async def get_account_statistics() -> Dict[str, Any]:
    """获取账号统计信息"""
    try:
        async for db in get_db():
            stats = await auth_manager.get_account_statistics(db)
            return {
                "success": True,
                "statistics": stats
            }
            
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {
            "success": False,
            "message": f"获取统计信息失败: {e}",
            "statistics": {}
        }


async def register_auth_tools() -> None:
    """注册认证相关的MCP工具"""
    try:
        # 登录抖音账号
        login_tool = ToolDefinition(
            name="douyin_login",
            description="登录抖音账号，支持二维码和密码登录",
            parameters=[
                ToolParameter(
                    name="username",
                    type="string",
                    description="用户名或手机号",
                    required=True
                ),
                ToolParameter(
                    name="login_type",
                    type="string",
                    description="登录类型",
                    required=False,
                    default="qrcode",
                    enum=["qrcode", "password", "sms", "cookie"]
                ),
                ToolParameter(
                    name="password",
                    type="string",
                    description="密码（密码登录时需要）",
                    required=False
                ),
                ToolParameter(
                    name="sms_code",
                    type="string",
                    description="短信验证码（短信登录时需要）",
                    required=False
                ),
        ToolParameter(
            name="qr_uuid",
            type="string",
            description="二维码UUID（检查二维码状态时需要）",
            required=False
        ),
        ToolParameter(
            name="cookie_file",
            type="string",
            description="Cookie文件路径（Cookie登录时需要）",
            required=False
        )
            ],
            category="auth",
            handler=login_douyin_account
        )
        
        # 创建抖音账号
        create_account_tool = ToolDefinition(
            name="douyin_create_account",
            description="创建新的抖音账号记录",
            parameters=[
                ToolParameter(
                    name="username",
                    type="string",
                    description="用户名或手机号",
                    required=True
                ),
                ToolParameter(
                    name="login_type",
                    type="string",
                    description="登录类型",
                    required=False,
                    default="qrcode",
                    enum=["qrcode", "password", "sms", "cookie"]
                ),
                ToolParameter(
                    name="password",
                    type="string",
                    description="密码（可选）",
                    required=False
                ),
                ToolParameter(
                    name="phone_number",
                    type="string",
                    description="手机号（可选）",
                    required=False
                ),
                ToolParameter(
                    name="enable_monitoring",
                    type="boolean",
                    description="启用监控",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="enable_auto_reply",
                    type="boolean",
                    description="启用自动回复",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="max_replies_per_hour",
                    type="integer",
                    description="每小时最大回复数",
                    required=False,
                    default=10
                )
            ],
            category="auth",
            handler=create_douyin_account
        )
        
        # 获取账号列表
        list_accounts_tool = ToolDefinition(
            name="douyin_list_accounts",
            description="获取抖音账号列表",
            parameters=[
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="返回数量限制",
                    required=False,
                    default=50
                ),
                ToolParameter(
                    name="offset",
                    type="integer",
                    description="偏移量",
                    required=False,
                    default=0
                )
            ],
            category="auth",
            handler=get_douyin_accounts
        )
        
        # 更新账号
        update_account_tool = ToolDefinition(
            name="douyin_update_account",
            description="更新抖音账号信息",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                ),
                ToolParameter(
                    name="nickname",
                    type="string",
                    description="昵称",
                    required=False
                ),
                ToolParameter(
                    name="enable_monitoring",
                    type="boolean",
                    description="启用监控",
                    required=False
                ),
                ToolParameter(
                    name="enable_auto_reply",
                    type="boolean",
                    description="启用自动回复",
                    required=False
                ),
                ToolParameter(
                    name="max_replies_per_hour",
                    type="integer",
                    description="每小时最大回复数",
                    required=False
                ),
                ToolParameter(
                    name="status",
                    type="string",
                    description="账号状态",
                    required=False,
                    enum=["active", "inactive", "suspended", "banned"]
                )
            ],
            category="auth",
            handler=update_douyin_account
        )
        
        # 删除账号
        delete_account_tool = ToolDefinition(
            name="douyin_delete_account",
            description="删除抖音账号",
            parameters=[
                ToolParameter(
                    name="account_id",
                    type="integer",
                    description="账号ID",
                    required=True
                )
            ],
            category="auth",
            handler=delete_douyin_account
        )
        
        # 登出账号
        logout_tool = ToolDefinition(
            name="douyin_logout",
            description="登出抖音账号",
            parameters=[
                ToolParameter(
                    name="session_token",
                    type="string",
                    description="会话令牌",
                    required=True
                )
            ],
            category="auth",
            handler=logout_douyin_account
        )
        
        # 验证会话
        validate_session_tool = ToolDefinition(
            name="douyin_validate_session",
            description="验证会话状态",
            parameters=[
                ToolParameter(
                    name="session_token",
                    type="string",
                    description="会话令牌",
                    required=True
                )
            ],
            category="auth",
            handler=validate_session
        )
        
        # 获取统计信息
        stats_tool = ToolDefinition(
            name="douyin_account_stats",
            description="获取账号统计信息",
            parameters=[],
            category="auth",
            handler=get_account_statistics
        )
        
        # 注册所有工具
        tools = [
            login_tool,
            create_account_tool,
            list_accounts_tool,
            update_account_tool,
            delete_account_tool,
            logout_tool,
            validate_session_tool,
            stats_tool
        ]
        
        for tool in tools:
            tool_registry.register_tool(tool)
        
        logger.info(f"认证模块工具注册完成，共注册 {len(tools)} 个工具")
        
    except Exception as e:
        logger.error(f"注册认证工具失败: {e}")
        raise
