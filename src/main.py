"""
FastAPI 应用主入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.config import settings
from src.common.database import Base, db_manager
from src.common.error_handlers import setup_exception_handlers
from src.common.middleware import RequestLoggingMiddleware, setup_sql_logging
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化资源，关闭时清理资源
    """
    # 启动时
    logger.info(f"正在启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"环境: {settings.ENVIRONMENT.value}")
    logger.info(f"调试模式: {settings.DEBUG}")

    # 设置 SQL 日志记录
    engine = db_manager.get_engine()
    setup_sql_logging(engine)
    logger.info("SQL 日志已启用，日志文件: logs/sql_YYYY-MM-DD.log")

    # 创建数据库表（开发环境）
    if settings.ENVIRONMENT.value == "development":
        async with engine.begin() as conn:
            # 导入所有模型以确保它们被注册
            from src.demo.models import Item  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表已创建/更新")

    logger.info("应用启动完成")

    yield

    # 关闭时
    logger.info("正在关闭应用...")
    await db_manager.close_all()
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例
    """
    # 应用配置
    app_config = {
        "title": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "lifespan": lifespan,
    }

    # 根据环境配置文档
    if not settings.SHOW_DOCS:
        app_config["openapi_url"] = None
        app_config["docs_url"] = None
        app_config["redoc_url"] = None

    # 创建应用
    app = FastAPI(**app_config)

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)

    # 设置全局异常处理器（必须在注册路由之前）
    setup_exception_handlers(app)

    # 注册路由
    register_routers(app)

    return app


def register_routers(app: FastAPI) -> None:
    """
    注册所有路由
    """
    from src.demo.router import router as demo_router
    from src.projectApi.router import router as project_api_router
    from src.projectApi.device_router import router as device_router

    # 健康检查路由
    @app.get("/health", tags=["Health"])
    async def health_check():
        """健康检查接口"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    # API 路由
    app.include_router(demo_router, prefix=settings.API_V1_PREFIX)
    app.include_router(project_api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(device_router, prefix=settings.API_V1_PREFIX)


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
    )

