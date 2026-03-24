"""
通用模块
提供全局配置、数据库、异常、中间件等通用功能
"""

# 配置管理
from src.common.config import Settings, get_settings, settings

# 常量定义
from src.common.constants import Environment, OrderDirection

# 数据库管理
from src.common.database import (
    Base,
    DatabaseManager,
    db_manager,
    get_db,
    get_db_dependency,
)

# 异常定义
from src.common.exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)

# 异常处理器
from src.common.error_handlers import setup_exception_handlers

# 中间件
from src.common.middleware import (
    CatchExceptionMiddleware,
    RequestLoggingMiddleware,
    setup_sql_logging,
)

# 基础模型
from src.common.models import BaseModel, TimestampMixin

# 分页工具
from src.common.pagination import (
    PaginationParams,
    calculate_page_info,
    get_offset,
    get_pagination,
)

# 全局 Schema
from src.common.schemas import (
    CustomModel,
    ErrorResponse,
    IdResponse,
    MessageResponse,
    PageInfo,
    PageResponse,
    ResponseModel,
)

__all__ = [
    # 配置
    "Settings",
    "get_settings",
    "settings",
    # 常量
    "Environment",
    "OrderDirection",
    # 数据库
    "Base",
    "DatabaseManager",
    "db_manager",
    "get_db",
    "get_db_dependency",
    # 异常
    "AppException",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "ValidationException",
    # 异常处理器
    "setup_exception_handlers",
    # 中间件
    "RequestLoggingMiddleware",
    "CatchExceptionMiddleware",
    "setup_sql_logging",
    # 模型
    "BaseModel",
    "TimestampMixin",
    # 分页
    "PaginationParams",
    "get_pagination",
    "calculate_page_info",
    "get_offset",
    # Schema
    "CustomModel",
    "ResponseModel",
    "PageResponse",
    "PageInfo",
    "IdResponse",
    "MessageResponse",
    "ErrorResponse",
]

