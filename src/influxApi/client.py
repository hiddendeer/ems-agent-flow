import logging
from typing import Any, Dict, List, Optional, Union

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from src.common.config import settings

logger = logging.getLogger(__name__)

class InfluxDBManager:
    """
    InfluxDB 客户端管理器
    负责初始化连接并提供写入接口
    """
    def __init__(
        self,
        url: str = settings.INFLUXDB_URL,
        token: str = settings.INFLUXDB_TOKEN,
        org: str = settings.INFLUXDB_ORG,
        bucket: str = settings.INFLUXDB_BUCKET,
        username: str = settings.INFLUXDB_USER,
        password: str = settings.INFLUXDB_PASSWORD
    ):
        self.url = url
        self.org = org
        self.bucket = bucket
        
        # 兼容性处理：如果没有提供 token 但提供了账号密码，则组合为 "user:pass" (InfluxDB 1.8 兼容格式)
        if not token and username and password:
            self.token = f"{username}:{password}"
        else:
            self.token = token

        self._client: Optional[InfluxDBClient] = None
        self._async_client: Optional[InfluxDBClientAsync] = None

    def get_client(self) -> InfluxDBClient:
        """获取同步客户端"""
        if self._client is None:
            self._client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        return self._client

    async def get_async_client(self) -> InfluxDBClientAsync:
        """获取异步客户端"""
        if self._async_client is None:
            self._async_client = InfluxDBClientAsync(url=self.url, token=self.token, org=self.org)
        return self._async_client

    def write_point(self, point: Point, bucket: str = None):
        """
        同步写入个数据点
        """
        target_bucket = bucket or self.bucket
        client = self.get_client()
        write_api = client.write_api(write_options=SYNCHRONOUS)
        try:
            write_api.write(bucket=target_bucket, org=self.org, record=point)
            logger.info(f"Successfully wrote point to InfluxDB bucket: {target_bucket}")
        except Exception as e:
            logger.error(f"Failed to write point to InfluxDB: {e}")
            raise

    def write_data(self, measurement: str, tags: Dict[str, str], fields: Dict[str, Any], bucket: str = None):
        """
        便捷写入接口
        """
        point = Point(measurement)
        for key, value in tags.items():
            point.tag(key, value)
        for key, value in fields.items():
            point.field(key, value)
        
        self.write_point(point, bucket)

    async def write_point_async(self, point: Point, bucket: str = None):
        """
        异步写入一个数据点
        """
        target_bucket = bucket or self.bucket
        client = await self.get_async_client()
        write_api = client.write_api()
        try:
            await write_api.write(bucket=target_bucket, org=self.org, record=point)
            logger.info(f"Successfully wrote point (async) to InfluxDB bucket: {target_bucket}")
        except Exception as e:
            logger.error(f"Failed to write point (async) to InfluxDB: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
        if self._async_client:
            await self._async_client.close()

# 全局单例
influx_manager = InfluxDBManager()
