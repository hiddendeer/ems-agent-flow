"""
MCP 客户端配置管理。
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class MCPTransportType(str, Enum):
    """MCP 传输类型"""
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


class MCPServerConfig(BaseModel):
    """
    MCP 服务器配置模型。

    支持多种传输方式：
    - stdio: 标准输入输出通信
    - sse: Server-Sent Events
    - websocket: WebSocket 通信
    """
    transport_type: MCPTransportType = Field(
        default=MCPTransportType.STDIO,
        description="传输类型"
    )

    # STDIO 配置
    command: Optional[str] = Field(
        default=None,
        description="STDIO 模式下的启动命令"
    )
    args: Optional[List[str]] = Field(
        default=None,
        description="STDIO 模式下的命令参数"
    )
    env: Optional[Dict[str, str]] = Field(
        default=None,
        description="STDIO 模式下的环境变量"
    )

    # SSE/WebSocket 配置
    url: Optional[str] = Field(
        default=None,
        description="SSE/WebSocket 模式下的服务 URL"
    )

    # 通用配置
    timeout: int = Field(
        default=30,
        description="连接超时时间（秒）"
    )
    max_retries: int = Field(
        default=3,
        description="最大重试次数"
    )
    retry_delay: float = Field(
        default=1.0,
        description="重试延迟（秒）"
    )

    # 可选配置
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="HTTP 请求头（SSE/WebSocket）"
    )

    class Config:
        arbitrary_types_allowed = True

    def get_stdio_params(self) -> Optional[tuple]:
        """获取 STDIO 服务器参数"""
        if self.transport_type != MCPTransportType.STDIO or not self.command:
            return None
        return (self.command, self.args or [], self.env or {})

    def validate_config(self) -> bool:
        """验证配置的有效性"""
        if self.transport_type == MCPTransportType.STDIO:
            if not self.command:
                raise ValueError("STDIO 模式需要提供 command 参数")
        elif self.transport_type in [MCPTransportType.SSE, MCPTransportType.WEBSOCKET]:
            if not self.url:
                raise ValueError(f"{self.transport_type.value} 模式需要提供 url 参数")
        return True


class MCPClientConfig(BaseModel):
    """
    MCP 客户端总配置。

    可以配置多个 MCP 服务器连接。
    """
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="MCP 服务器配置字典，key 为服务器名称"
    )
    default_server: Optional[str] = Field(
        default=None,
        description="默认使用的服务器名称"
    )
    enable_caching: bool = Field(
        default=True,
        description="是否启用工具列表缓存"
    )
    cache_ttl: int = Field(
        default=300,
        description="缓存有效期（秒）"
    )
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )

    def get_server_config(self, server_name: str) -> MCPServerConfig:
        """获取指定服务器的配置"""
        if server_name not in self.servers:
            available = list(self.servers.keys())
            raise KeyError(
                f"未找到服务器配置: {server_name}. "
                f"可用的服务器: {available}"
            )
        return self.servers[server_name]

    def add_server(self, name: str, config: MCPServerConfig) -> None:
        """添加服务器配置"""
        self.servers[name] = config

    def remove_server(self, name: str) -> None:
        """移除服务器配置"""
        if name in self.servers:
            del self.servers[name]

    def validate_config(self) -> bool:
        """验证配置的有效性"""
        if not self.servers:
            raise ValueError("至少需要配置一个 MCP 服务器")

        if self.default_server and self.default_server not in self.servers:
            raise ValueError(
                f"默认服务器 '{self.default_server}' 不在服务器列表中"
            )

        for name, config in self.servers.items():
            config.validate_config()

        return True


# 预定义配置
def create_stdio_config(
    command: str,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> MCPServerConfig:
    """创建 STDIO 类型的服务器配置"""
    return MCPServerConfig(
        transport_type=MCPTransportType.STDIO,
        command=command,
        args=args,
        env=env,
        timeout=timeout
    )


def create_sse_config(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> MCPServerConfig:
    """创建 SSE 类型的服务器配置"""
    return MCPServerConfig(
        transport_type=MCPTransportType.SSE,
        url=url,
        headers=headers,
        timeout=timeout
    )
