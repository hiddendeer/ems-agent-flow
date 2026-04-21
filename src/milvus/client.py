import logging
from typing import Optional

from pymilvus import connections, utility

from src.common.config import settings

logger = logging.getLogger(__name__)

class MilvusManager:
    """
    Milvus 客户端管理器
    负责统一管理与 Milvus 数据库的连接
    """
    def __init__(
        self,
        host: str = settings.MILVUS_HOST,
        port: int = settings.MILVUS_PORT,
        user: str = settings.MILVUS_USER,
        password: str = settings.MILVUS_PASSWORD,
        db_name: str = settings.MILVUS_DB_NAME,
        alias: str = "default"
    ):
        # 兼容处理：如果填写了 http:// 或 https://，自动去除，只保留域名/IP
        if host.startswith("http://"):
            self.host = host[7:]
        elif host.startswith("https://"):
            self.host = host[8:]
        else:
            self.host = host
            
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.alias = alias
        
    def connect(self) -> None:
        """建立并验证与 Milvus 的连接"""
        if not self.host:
            logger.warning("Milvus host not configured. Please check .env or config.")
            return
            
        try:
            params = {
                "alias": self.alias,
                "host": self.host,
                "port": str(self.port),
                "db_name": self.db_name
            }
            
            # 只有设置了密码且可能启用了鉴权才传递 user/pwd
            if self.user and self.password:
                params["user"] = self.user
                params["password"] = self.password
                
            connections.connect(**params)
            
            logger.info(f"Successfully connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
            
    def disconnect(self) -> None:
        """断开连接"""
        if connections.has_connection(self.alias):
            connections.disconnect(self.alias)
            logger.info(f"Disconnected from Milvus [{self.alias}]")
            
    def is_connected(self) -> bool:
        """检查是否已连接"""
        try:
            # 简单调用 utility.has_collection 来确认连接池是否生效且通畅
            utility.has_collection("dummy_check_collection", using=self.alias)
            return True
        except Exception:
            return False

# 全局单例
milvus_manager = MilvusManager()
