"""
数据库配置
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from loguru import logger

from .settings import settings


# 数据库元数据
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# 数据库基类
Base = declarative_base(metadata=metadata)


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    def initialize(self) -> None:
        """初始化数据库连接"""
        if self._initialized:
            logger.warning("数据库已经初始化")
            return
        
        try:
            # 创建异步数据库引擎
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True,
                echo=settings.DEBUG,
                future=True
            )
            
            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            self._initialized = True
            logger.info("数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def create_tables(self) -> None:
        """创建数据库表"""
        if not self._initialized:
            self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """删除数据库表"""
        if not self._initialized:
            self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self._initialized:
            self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")


# 全局数据库配置实例
db_config = DatabaseConfig()


# 依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    async for session in db_config.get_session():
        yield session
