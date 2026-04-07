"""
MCP 客户端自定义异常类。
"""


class MCPClientError(Exception):
    """MCP 客户端基础异常类"""
    pass


class MCPConnectionError(MCPClientError):
    """MCP 连接异常"""
    pass


class MCPToolCallError(MCPClientError):
    """MCP 工具调用异常"""
    pass


class MCPInitializationError(MCPClientError):
    """MCP 初始化异常"""
    pass


class MCPTimeoutError(MCPClientError):
    """MCP 超时异常"""
    pass
