"""
账号管理器 - 负责抖音账号的认证和管理
"""

import asyncio
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from loguru import logger
from cryptography.fernet import Fernet

from .models import DouyinAccount, LoginSession, LoginType, AccountStatus
from .models import AccountCreate, AccountUpdate, LoginRequest, LoginResponse, QRCodeStatus
from .exceptions import (
    AuthError, LoginError, AccountNotFoundError, AccountExistsError,
    AccountSuspendedError, SessionError, CookieInvalidError
)
from .browser_manager import BrowserManager
from ..config.database import get_db
from ..config.redis_config import get_redis
from ..config.settings import settings


class AuthManager:
    """账号认证管理器"""
    
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("账号认证管理器初始化完成")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        try:
            # 尝试从环境变量或配置文件读取密钥
            key = settings.SECRET_KEY.encode()
            if len(key) < 32:
                key = key.ljust(32, b'0')[:32]
            return Fernet.generate_key()
        except Exception:
            return Fernet.generate_key()
    
    def _encrypt_password(self, password: str) -> str:
        """加密密码"""
        try:
            return self.cipher.encrypt(password.encode()).decode()
        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise AuthError("密码加密失败")
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """解密密码"""
        try:
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error(f"密码解密失败: {e}")
            raise AuthError("密码解密失败")
    
    def _generate_session_token(self) -> str:
        """生成会话令牌"""
        return secrets.token_urlsafe(32)
    
    async def create_account(self, account_data: AccountCreate, db: AsyncSession) -> DouyinAccount:
        """创建新账号"""
        try:
            # 检查账号是否已存在
            existing_account = await self.get_account_by_username(account_data.username, db)
            if existing_account:
                raise AccountExistsError(account_data.username)
            
            # 创建新账号
            account = DouyinAccount(
                username=account_data.username,
                login_type=account_data.login_type.value,
                phone_number=account_data.phone_number,
                enable_monitoring=account_data.enable_monitoring,
                enable_auto_reply=account_data.enable_auto_reply,
                max_replies_per_hour=account_data.max_replies_per_hour,
                status=AccountStatus.INACTIVE.value
            )
            
            # 加密保存密码
            if account_data.password:
                account.encrypted_password = self._encrypt_password(account_data.password)
            
            db.add(account)
            await db.commit()
            await db.refresh(account)
            
            logger.info(f"创建账号成功: {account_data.username}")
            return account
            
        except Exception as e:
            await db.rollback()
            if isinstance(e, AuthError):
                raise
            logger.error(f"创建账号失败: {e}")
            raise AuthError(f"创建账号失败: {e}")
    
    async def get_account_by_username(self, username: str, db: AsyncSession) -> Optional[DouyinAccount]:
        """根据用户名获取账号"""
        try:
            result = await db.execute(
                select(DouyinAccount).where(DouyinAccount.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取账号失败 {username}: {e}")
            return None
    
    async def get_account_by_id(self, account_id: int, db: AsyncSession) -> Optional[DouyinAccount]:
        """根据ID获取账号"""
        try:
            result = await db.execute(
                select(DouyinAccount).where(DouyinAccount.id == account_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取账号失败 {account_id}: {e}")
            return None
    
    async def update_account(self, account_id: int, update_data: AccountUpdate, db: AsyncSession) -> DouyinAccount:
        """更新账号信息"""
        try:
            account = await self.get_account_by_id(account_id, db)
            if not account:
                raise AccountNotFoundError(str(account_id))
            
            # 更新字段
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(account, field):
                    setattr(account, field, value)
            
            account.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(account)
            
            logger.info(f"更新账号成功: {account.username}")
            return account
            
        except Exception as e:
            await db.rollback()
            if isinstance(e, AuthError):
                raise
            logger.error(f"更新账号失败: {e}")
            raise AuthError(f"更新账号失败: {e}")
    
    async def delete_account(self, account_id: int, db: AsyncSession) -> bool:
        """删除账号"""
        try:
            account = await self.get_account_by_id(account_id, db)
            if not account:
                raise AccountNotFoundError(str(account_id))
            
            # 删除相关会话
            await db.execute(
                delete(LoginSession).where(LoginSession.account_id == account_id)
            )
            
            # 删除账号
            await db.delete(account)
            await db.commit()
            
            logger.info(f"删除账号成功: {account.username}")
            return True
            
        except Exception as e:
            await db.rollback()
            if isinstance(e, AuthError):
                raise
            logger.error(f"删除账号失败: {e}")
            raise AuthError(f"删除账号失败: {e}")
    
    async def list_accounts(self, db: AsyncSession, limit: int = 100, offset: int = 0) -> List[DouyinAccount]:
        """列出所有账号"""
        try:
            result = await db.execute(
                select(DouyinAccount)
                .order_by(DouyinAccount.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取账号列表失败: {e}")
            return []
    
    async def login_with_qrcode(self, username: str, db: AsyncSession) -> LoginResponse:
        """二维码登录"""
        try:
            account = await self.get_account_by_username(username, db)
            if not account:
                raise AccountNotFoundError(username)
            
            if account.status == AccountStatus.SUSPENDED.value:
                raise AccountSuspendedError(username)
            
            # 使用浏览器管理器获取二维码
            qr_result = await self.browser_manager.get_qrcode()
            
            if not qr_result.get("success"):
                raise LoginError(qr_result.get("message", "获取二维码失败"))
            
            # 缓存二维码状态
            redis = await get_redis()
            qr_uuid = qr_result["qr_uuid"]
            await redis.set(
                f"qr_code:{qr_uuid}",
                {
                    "account_id": account.id,
                    "username": username,
                    "status": "waiting",
                    "created_at": datetime.utcnow().isoformat()
                },
                ttl=300  # 5分钟过期
            )
            
            return LoginResponse(
                success=True,
                message="请使用抖音APP扫描二维码登录",
                qr_code_url=qr_result["qr_code_url"],
                qr_uuid=qr_uuid
            )
            
        except Exception as e:
            if isinstance(e, (AuthError, LoginError)):
                raise
            logger.error(f"二维码登录失败: {e}")
            raise LoginError(f"二维码登录失败: {e}")
    
    async def check_qrcode_status(self, qr_uuid: str, db: AsyncSession) -> QRCodeStatus:
        """检查二维码状态"""
        try:
            redis = await get_redis()
            qr_data = await redis.get(f"qr_code:{qr_uuid}")
            
            if not qr_data:
                return QRCodeStatus(
                    status="expired",
                    message="二维码已过期"
                )
            
            # 检查浏览器中的二维码状态
            browser_status = await self.browser_manager.check_qrcode_status(qr_uuid)
            
            if browser_status["status"] == "confirmed":
                # 登录成功，创建会话
                account_id = qr_data["account_id"]
                session_token = await self._create_login_session(
                    account_id, "qrcode", db
                )
                
                # 更新账号状态
                await self._update_account_login_status(account_id, db)
                
                # 清理二维码缓存
                await redis.delete(f"qr_code:{qr_uuid}")
                
                return QRCodeStatus(
                    status="confirmed",
                    message="登录成功",
                    account_info={
                        "account_id": account_id,
                        "session_token": session_token
                    }
                )
            
            return QRCodeStatus(
                status=browser_status["status"],
                message=browser_status["message"]
            )
            
        except Exception as e:
            logger.error(f"检查二维码状态失败: {e}")
            return QRCodeStatus(
                status="error",
                message=f"检查状态失败: {e}"
            )
    
    async def login_with_password(self, login_data: LoginRequest, db: AsyncSession) -> LoginResponse:
        """密码登录"""
        try:
            account = await self.get_account_by_username(login_data.username, db)
            if not account:
                raise AccountNotFoundError(login_data.username)
            
            if account.status == AccountStatus.SUSPENDED.value:
                raise AccountSuspendedError(login_data.username)
            
            if not account.encrypted_password or not login_data.password:
                raise LoginError("密码登录需要密码")
            
            # 验证密码
            stored_password = self._decrypt_password(account.encrypted_password)
            if stored_password != login_data.password:
                raise LoginError("用户名或密码错误")
            
            # 使用浏览器登录
            login_result = await self.browser_manager.login_with_password(
                login_data.username,
                login_data.password
            )
            
            if not login_result.get("success"):
                raise LoginError(login_result.get("message", "登录失败"))
            
            # 创建会话
            session_token = await self._create_login_session(
                account.id, "password", db
            )
            
            # 更新账号状态
            await self._update_account_login_status(account.id, db)
            
            return LoginResponse(
                success=True,
                message="登录成功",
                account_id=account.id,
                session_token=session_token
            )
            
        except Exception as e:
            if isinstance(e, (AuthError, LoginError)):
                raise
            logger.error(f"密码登录失败: {e}")
            raise LoginError(f"密码登录失败: {e}")
    
    async def _create_login_session(self, account_id: int, login_type: str, db: AsyncSession) -> str:
        """创建登录会话"""
        try:
            session_token = self._generate_session_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            session = LoginSession(
                account_id=account_id,
                session_token=session_token,
                expires_at=expires_at,
                is_active=True
            )
            
            db.add(session)
            await db.commit()
            
            # 缓存会话信息
            self._active_sessions[session_token] = {
                "account_id": account_id,
                "login_type": login_type,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at
            }
            
            return session_token
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建会话失败: {e}")
            raise SessionError(f"创建会话失败: {e}")
    
    async def _update_account_login_status(self, account_id: int, db: AsyncSession) -> None:
        """更新账号登录状态"""
        try:
            now = datetime.utcnow()
            await db.execute(
                update(DouyinAccount)
                .where(DouyinAccount.id == account_id)
                .values(
                    status=AccountStatus.ACTIVE.value,
                    last_login_at=now,
                    last_active_at=now,
                    updated_at=now
                )
            )
            await db.commit()
            
        except Exception as e:
            logger.error(f"更新账号登录状态失败: {e}")
    
    async def validate_session(self, session_token: str, db: AsyncSession) -> Optional[DouyinAccount]:
        """验证会话"""
        try:
            # 先从内存缓存检查
            if session_token in self._active_sessions:
                session_info = self._active_sessions[session_token]
                if session_info["expires_at"] > datetime.utcnow():
                    account = await self.get_account_by_id(session_info["account_id"], db)
                    if account and account.status == AccountStatus.ACTIVE.value:
                        return account
                else:
                    # 会话已过期，从缓存中移除
                    del self._active_sessions[session_token]
            
            # 从数据库检查
            result = await db.execute(
                select(LoginSession, DouyinAccount)
                .join(DouyinAccount, LoginSession.account_id == DouyinAccount.id)
                .where(
                    LoginSession.session_token == session_token,
                    LoginSession.is_active == True,
                    LoginSession.expires_at > datetime.utcnow()
                )
            )
            
            session_data = result.first()
            if session_data:
                session, account = session_data
                
                # 更新最后使用时间
                session.last_used_at = datetime.utcnow()
                await db.commit()
                
                return account
            
            return None
            
        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return None
    
    async def logout(self, session_token: str, db: AsyncSession) -> bool:
        """登出"""
        try:
            # 从内存缓存移除
            if session_token in self._active_sessions:
                del self._active_sessions[session_token]
            
            # 数据库中禁用会话
            await db.execute(
                update(LoginSession)
                .where(LoginSession.session_token == session_token)
                .values(is_active=False)
            )
            await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return False
    
    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """清理过期会话"""
        try:
            # 清理内存缓存
            now = datetime.utcnow()
            expired_tokens = [
                token for token, info in self._active_sessions.items()
                if info["expires_at"] <= now
            ]
            
            for token in expired_tokens:
                del self._active_sessions[token]
            
            # 清理数据库
            result = await db.execute(
                delete(LoginSession)
                .where(LoginSession.expires_at <= now)
            )
            await db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"清理过期会话: {deleted_count} 个")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
    
    async def get_account_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """获取账号统计信息"""
        try:
            # 总账号数
            total_result = await db.execute(select(DouyinAccount.id).count())
            total_accounts = total_result.scalar()
            
            # 活跃账号数
            active_result = await db.execute(
                select(DouyinAccount.id)
                .where(DouyinAccount.status == AccountStatus.ACTIVE.value)
                .count()
            )
            active_accounts = active_result.scalar()
            
            # 监控账号数
            monitoring_result = await db.execute(
                select(DouyinAccount.id)
                .where(DouyinAccount.enable_monitoring == True)
                .count()
            )
            monitoring_accounts = monitoring_result.scalar()
            
            # 自动回复账号数
            auto_reply_result = await db.execute(
                select(DouyinAccount.id)
                .where(DouyinAccount.enable_auto_reply == True)
                .count()
            )
            auto_reply_accounts = auto_reply_result.scalar()
            
            return {
                "total_accounts": total_accounts or 0,
                "active_accounts": active_accounts or 0,
                "monitoring_accounts": monitoring_accounts or 0,
                "auto_reply_accounts": auto_reply_accounts or 0,
                "cached_sessions": len(self._active_sessions),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取账号统计失败: {e}")
            return {}
