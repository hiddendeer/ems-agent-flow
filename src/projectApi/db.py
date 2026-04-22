"""
MySQL 学习模块 - 异步数据库引擎
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .mysql_config import mysql_settings

# 创建异步引擎
# pool_size: 连接池大小
# max_overflow: 超过 pool_size 后最多可以创建的连接数
# echo: 是否在终端打印 SQL 语句 (学习时建议开启 True)
engine = create_async_engine(
    mysql_settings.ASYNC_DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=10,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明式基类
class Base(DeclarativeBase):
    pass

# 获取数据库会话的依赖函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
