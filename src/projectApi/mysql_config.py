"""
MySQL 学习模块 - 数据库配置
"""
from pydantic_settings import BaseSettings

class MySQLSettings(BaseSettings):
    # 数据库连接配置
    DB_HOST: str = "180.112.195.106"
    DB_PORT: int = 13306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Chen#1994!"
    DB_NAME: str = "project_api_test"  # 建议先在 MySQL 中创建此数据库: CREATE DATABASE project_api_test CHARACTER SET utf8mb4;

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """异步连接 URL"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """同步连接 URL (可选)"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

mysql_settings = MySQLSettings()
