from typing import Optional, List
from fastapi import FastAPI, Path, Query, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="FastAPI Common Syntax Demo",
    description="A reference file for frequently used FastAPI features.",
    version="1.0.0"
)

# --- Models (Pydantic) ---

class Item(BaseModel):
    """商品项模型。

    用于表示单个商品项的数据结构，包含商品的基本信息和价格。

    Attributes:
        name (str): 商品名称，必填项，不能为空。
        description (Optional[str]): 商品描述，可选，最大长度为 300 字符。
        price (float): 商品价格，必填项，必须大于 0。
        tax (Optional[float]): 税费，可选字段，默认为 None。

    Example:
        >>> item = Item(name="Smartphone", description="Latest model", price=999.99)
        >>> item.name
        'Smartphone'
    """
    name: str = Field(..., title="Item Name", example="Smartphone")
    description: Optional[str] = Field(None, max_length=300, description="Optional description of the item")
    price: float = Field(..., gt=0, description="Price must be greater than zero")
    tax: Optional[float] = None

class User(BaseModel):
    """用户模型。

    用于表示用户的基本信息数据结构。

    Attributes:
        username (str): 用户名，必填项。
        email (str): 用户邮箱地址，必填项。
        full_name (Optional[str]): 用户全名，可选字段，默认为 None。

    Example:
        >>> user = User(username="alice", email="alice@example.com", full_name="Alice Smith")
        >>> user.username
        'alice'
    """
    username: str
    email: str
    full_name: Optional[str] = None

# --- Dependencies ---

async def common_parameters(
    q: Optional[str] = Query(None, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    """可重用的依赖函数，用于提取常见的查询参数。

    此函数作为 FastAPI 依赖注入使用，自动从请求查询参数中提取并验证参数。
    可以在任何路由函数中通过 Depends(common_parameters) 注入使用。

    Args:
        q (Optional[str]): 搜索查询字符串，可选参数，最大长度为 50 字符。
        skip (int): 跳过记录数，用于分页，默认为 0，最小值为 0。
        limit (int): 返回记录数限制，默认为 10，最大值为 100。

    Returns:
        dict: 包含查询参数的字典，格式为 {"q": q, "skip": skip, "limit": limit}。

    Example:
        在路由中使用：
        >>> @app.get("/items/")
        >>> async def read_items(commons: dict = Depends(common_parameters)):
        >>>     return commons

        请求示例：GET /items/?q=test&skip=10&limit=20
        返回：{"q": "test", "skip": 10, "limit": 20}
    """
    return {"q": q, "skip": skip, "limit": limit}

# --- Custom Exceptions ---

class UnicornException(Exception):
    """自定义异常类，用于演示 FastAPI 异常处理。

    这是一个示例异常类，展示如何创建自定义异常并将其与全局异常处理器结合使用。
    当抛出此异常时，会被 unicorn_exception_handler 捕获并返回自定义的错误响应。

    Usage:
        在路由函数中可以抛出此异常：
        >>> raise UnicornException(name="yolo")

        系统会返回 HTTP 418 状态码和自定义错误消息：
        {"message": "Oops! yolo did something funny. "}

    Attributes:
        name (str): 异常名称，用于生成自定义错误消息。

    Example:
        >>> raise UnicornException(name="test")
        # 将触发异常处理器，返回 HTTP 418 响应
    """

    def __init__(self, name: str):
        """初始化 UnicornException 异常。

        Args:
            name (str): 异常名称，将被存储在实例属性中，用于生成错误消息。

        Raises:
            无主动抛出的异常。

        Example:
            >>> exc = UnicornException(name="yolo")
            >>> exc.name
            'yolo'
        """
        self.name = name

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request, exc: UnicornException):
    """UnicornException 的全局异常处理器。

    此函数被注册为全局异常处理器，当任何路由抛出 UnicornException 时，
    都会被此函数捕获并返回自定义的 HTTP 响应。

    Args:
        request: FastAPI/Starlette 的请求对象，包含请求的详细信息。
            虽然此处理器未使用此参数，但它是 FastAPI 异常处理器签名的必需部分。
        exc (UnicornException): 被捕获的 UnicornException 异常实例。
            exc.name 属性用于生成自定义错误消息。

    Returns:
        JSONResponse: 返回一个 HTTP 418 (I'm a teapot) 状态码的 JSON 响应。
        响应体格式：{"message": "Oops! {exc.name} did something funny. "}

    Example:
        当路由抛出异常时：
        >>> raise UnicornException(name="yolo")

        此处理器将返回：
        - 状态码：418
        - 响应体：{"message": "Oops! yolo did something funny. "}

    Note:
        HTTP 418 状态码是 RFC 2324 定义的非标准状态码，常用于幽默场景。
        在生产环境中，建议使用更合适的错误状态码（如 400、500 等）。
    """
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something funny. "},
    )

# --- Routes ---

@app.get("/items/{item_id}", tags=["Basic"], response_model=dict)
async def read_item_path(
    item_id: int = Path(..., title="The ID of the item to get", gt=0),
    q: Optional[str] = Query(None, max_length=50, description="Search query")
):
    """获取指定 ID 的商品信息（演示路径参数和查询参数）。

    此路由函数演示了 FastAPI 中路径参数和查询参数的使用。
    路径参数 {item_id} 是必填的，查询参数 q 是可选的。

    Args:
        item_id (int): 商品 ID，从 URL 路径中提取。
            必填参数，必须大于 0（通过 Path(gt=0) 验证）。
            例如：URL /items/123 中，item_id 为 123。
        q (Optional[str]): 搜索查询字符串，从 URL 查询参数中提取。
            可选参数，最大长度为 50 字符。
            例如：URL /items/123?q=test 中，q 为 "test"。

    Returns:
        dict: 包含商品 ID 和查询参数的字典。
            格式：{"item_id": <item_id>, "q": <q> 或 None}

    Example:
        请求示例 1（无查询参数）：
        GET /items/123
        返回：{"item_id": 123, "q": null}

        请求示例 2（带查询参数）：
        GET /items/456?q=smartphone
        返回：{"item_id": 456, "q": "smartphone"}

    Note:
        此函数主要演示参数验证：
        - Path(gt=0): 确保 item_id 大于 0
        - Query(max_length=50): 限制 q 的最大长度
    """
    return {"item_id": item_id, "q": q}

@app.get("/users/", tags=["Basic"], response_model=List[dict])
async def read_users_query(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    """获取用户列表（演示查询参数的默认值和验证）。

    此路由函数演示了 FastAPI 查询参数的默认值设置和数值范围验证。
    主要用于实现分页功能。

    Args:
        skip (int): 跳过的记录数，用于分页的起始位置。
            默认值为 0，最小值为 0（通过 Query(0, ge=0) 设置）。
            例如：GET /users/?skip=10 表示跳过前 10 条记录。
        limit (int): 返回的记录数限制。
            默认值为 10，最大值为 100（通过 Query(10, le=100) 设置）。
            例如：GET /users/?limit=20 表示返回 20 条记录。

    Returns:
        List[dict]: 用户列表，每个用户是一个字典，包含 user_id 和 username。
            返回的列表长度不受 skip 和 limit 参数限制（演示用）。

    Example:
        请求示例 1（使用默认值）：
        GET /users/
        返回：[
            {"user_id": 1, "username": "alice"},
            {"user_id": 2, "username": "bob"}
        ]

        请求示例 2（自定义分页参数）：
        GET /users/?skip=5&limit=50
        返回：[
            {"user_id": 1, "username": "alice"},
            {"user_id": 2, "username": "bob"}
        ]

    Note:
        在实际应用中，应该根据 skip 和 limit 参数对数据库查询进行分页处理。
        此函数仅演示参数验证和默认值，未实现实际分页逻辑。
    """
    return [{"user_id": 1, "username": "alice"}, {"user_id": 2, "username": "bob"}]

@app.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["Models"])
async def create_item(item: Item):
    """创建新商品（演示请求体、响应模型和状态码）。

    此路由函数演示了 FastAPI 中 POST 请求的完整处理流程：
    1. 自动解析请求体为 Pydantic 模型
    2. 返回自定义 HTTP 状态码
    3. 使用响应模型验证和过滤输出数据

    Args:
        item (Item): 商品数据对象，从请求体中自动解析。
            Item 模型包含以下字段：
            - name (str): 商品名称，必填
            - description (Optional[str]): 商品描述，可选
            - price (float): 商品价格，必填，必须大于 0
            - tax (Optional[float]): 税费，可选

    Returns:
        Item: 创建成功的商品对象。
            返回的数据会经过 response_model=Item 的验证，确保符合模型定义。

    Example:
        请求示例：
        POST /items/
        Content-Type: application/json

        {
            "name": "Smartphone",
            "description": "Latest model with 5G",
            "price": 999.99,
            "tax": 99.99
        }

        返回示例（状态码：201 Created）：
        {
            "name": "Smartphone",
            "description": "Latest model with 5G",
            "price": 999.99,
            "tax": 99.99
        }

    Note:
        - HTTP 201 Created 状态码表示资源创建成功
        - response_model 会自动过滤响应数据，确保不泄露敏感信息
        - Pydantic 自动验证输入数据，不符合验证规则会返回 422 错误
    """
    return item

@app.get("/items-di/", tags=["Advanced"])
async def read_items_with_di(commons: dict = Depends(common_parameters)):
    """获取商品列表（演示依赖注入）。

    此路由函数演示了 FastAPI 的依赖注入（Dependency Injection）功能。
    通过 Depends(common_parameters) 注入公共参数处理逻辑，
    实现了代码复用和参数验证的集中管理。

    Args:
        commons (dict): 通过依赖注入获取的公共参数字典。
            由 common_parameters 函数提供，包含以下字段：
            - q (Optional[str]): 搜索查询字符串
            - skip (int): 跳过记录数，默认 0
            - limit (int): 返回记录数限制，默认 10

    Returns:
        dict: 原样返回传入的 commons 字典。
            格式：{"q": <q>, "skip": <skip>, "limit": <limit>}

    Example:
        请求示例 1（无参数）：
        GET /items-di/
        返回：{"q": null, "skip": 0, "limit": 10}

        请求示例 2（带查询参数）：
        GET /items-di/?q=test&skip=20&limit=50
        返回：{"q": "test", "skip": 20, "limit": 50}

    Note:
        依赖注入的优势：
        1. 代码复用：多个路由可以共享同一套参数处理逻辑
        2. 参数验证：在依赖函数中集中处理参数验证
        3. 职责分离：将参数提取逻辑与业务逻辑分离
        4. 自动文档生成：依赖会自动反映在 OpenAPI 文档中

        在实际应用中，通常会用依赖注入来：
        - 验证用户认证和授权
        - 提取和验证公共查询参数
        - 管理数据库连接
        - 实现缓存逻辑
    """
    return commons

@app.get("/unicorns/{name}", tags=["Advanced"])
async def trigger_custom_exception(name: str):
    """触发自定义异常（演示自定义异常和全局异常处理）。

    此路由函数演示了 FastAPI 中自定义异常的使用和全局异常处理器的功能。
    当传入特定参数时抛出 UnicornException，该异常会被全局异常处理器捕获。

    Args:
        name (str): 独角兽名称，从 URL 路径参数中提取。
            当 name 为 "yolo" 时，会抛出 UnicornException。
            其他值则正常返回。

    Returns:
        dict: 正常情况下返回包含独角兽名称的字典。
            格式：{"unicorn_name": <name>}
            当抛出异常时，由异常处理器返回响应。

    Raises:
        UnicornException: 当 name 等于 "yolo" 时抛出。
            此异常会被全局异常处理器捕获，返回 HTTP 418 响应。

    Example:
        请求示例 1（正常情况）：
        GET /unicorns/rainbow
        返回：{"unicorn_name": "rainbow"}

        请求示例 2（触发异常）：
        GET /unicorns/yolo
        返回（状态码：418 I'm a teapot）：
        {
            "message": "Oops! yolo did something funny. "
        }

    Note:
        自定义异常的使用场景：
        1. 业务逻辑错误：如资源不存在、权限不足等
        2. 特殊情况处理：如支付失败、库存不足等
        3. 提供友好的错误消息：将技术错误转换为用户友好的消息

        全局异常处理器的优势：
        1. 集中错误处理：统一管理异常响应格式
        2. 避免重复代码：多个路由可共享同一异常处理逻辑
        3. 保持代码整洁：路由函数专注于业务逻辑，不混入错误处理代码
    """
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}

@app.get("/items-error/{item_id}", tags=["Advanced"])
async def trigger_http_exception(item_id: int):
    """获取商品状态（演示标准 HTTP 异常）。

    此路由函数演示了 FastAPI 中 HTTPException 的使用。
    HTTPException 是 FastAPI 提供的标准异常类，用于返回 HTTP 错误响应。
    相比自定义异常，HTTPException 更适用于常见的 HTTP 错误场景。

    Args:
        item_id (int): 商品 ID，从 URL 路径参数中提取。
            当 item_id 等于 404 时，抛出 HTTPException。
            其他值则正常返回。

    Returns:
        dict: 正常情况下返回包含商品 ID 和状态的字典。
            格式：{"item_id": <item_id>, "status": "exists"}

    Raises:
        HTTPException: 当 item_id 等于 404 时抛出。
            状态码：404 Not Found
            详情：{"detail": "Item not found"}

    Example:
        请求示例 1（正常情况）：
        GET /items-error/123
        返回：{"item_id": 123, "status": "exists"}

        请求示例 2（触发 404 错误）：
        GET /items-error/404
        返回（状态码：404 Not Found）：
        {
            "detail": "Item not found"
        }

    Note:
        HTTPException 的常用场景：
        - 400 Bad Request：请求参数错误
        - 401 Unauthorized：未认证
        - 403 Forbidden：无权限
        - 404 Not Found：资源不存在
        - 422 Unprocessable Entity：数据验证失败
        - 500 Internal Server Error：服务器内部错误

        HTTPException 参数说明：
        - status_code: HTTP 状态码（必填）
        - detail: 错误详情（可选，默认为空）
        - headers: 自定义响应头（可选）

        与自定义异常的比较：
        - HTTPException: 适用于标准 HTTP 错误，快速实现
        - 自定义异常: 适用于业务特定错误，可携带更多信息
    """
    if item_id == 404:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "status": "exists"}

# --- 主程序入口 ---
# 当直接运行此文件时，启动 Uvicorn 服务器
# 使用命令：python fastapi_syntax_demo.py
# 或者使用 uvicorn 命令：uvicorn fastapi_syntax_demo:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
