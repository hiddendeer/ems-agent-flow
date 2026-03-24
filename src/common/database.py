"""
数据库连接管理
支持多数据库连接和异步操作
"""
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.common.config import settings


# MySQL 索引命名约定
MYSQL_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    metadata = MetaData(naming_convention=MYSQL_INDEXES_NAMING_CONVENTION)


class DatabaseManager:
    """
    数据库管理器
    支持多数据库连接管理
    """

    def __init__(self):
        self._engines: dict = {}
        self._session_factories: dict = {}

    def get_engine(self, db_name: str | None = None):
        """
        获取数据库引擎

        Args:
            db_name: 数据库名称，None 表示使用默认数据库
        """
        key = db_name or "default"

        if key not in self._engines:
            if db_name:
                url = settings.get_database_url(db_name)
            else:
                url = settings.DATABASE_URL

            # SQLite 不需要连接池配置
            if settings.DB_TYPE == "sqlite":
                self._engines[key] = create_async_engine(
                    url,
                    echo=settings.DB_ECHO,
                )
            else:
                # MySQL 需要连接池配置
                self._engines[key] = create_async_engine(
                    url,
                    echo=settings.DB_ECHO,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_recycle=settings.DB_POOL_RECYCLE,
                    pool_pre_ping=True,           # 使用前检查连接（防止使用断开的连接）
                    pool_use_lifo=True,           # 后进先出（优先使用最近的连接）
                )

        return self._engines[key]

    def get_session_factory(self, db_name: str | None = None) -> async_sessionmaker[AsyncSession]:
        """
        获取会话工厂
        
        Args:
            db_name: 数据库名称，None 表示使用默认数据库
        """
        key = db_name or settings.DB_NAME

        if key not in self._session_factories:
            engine = self.get_engine(db_name)
            self._session_factories[key] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

        return self._session_factories[key]

    async def get_session(self, db_name: str | None = None) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（异步生成器）
        
        Args:
            db_name: 数据库名称，None 表示使用默认数据库
        """
        session_factory = self.get_session_factory(db_name)
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close_all(self):
        """关闭所有数据库连接"""
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_factories.clear()


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 默认数据库会话依赖
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取默认数据库会话（用于 FastAPI 依赖注入）"""
    async for session in db_manager.get_session():
        yield session


# 多数据库会话依赖工厂
def get_db_dependency(db_name: str):
    """
    创建指定数据库的会话依赖
    
    使用示例:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_dependency("myems_user_db"))):
            ...
    """
    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async for session in db_manager.get_session(db_name):
            yield session
    return _get_db


# 预定义的数据库会话依赖（仅 MySQL 模式下使用）
# if settings.DB_TYPE == "mysql":
#     get_user_db = get_db_dependency(settings.DB_USER_NAME)
#     get_system_db = get_db_dependency(settings.DB_SYSTEM_NAME)
#     get_reporting_db = get_db_dependency(settings.DB_REPORTING_NAME)

