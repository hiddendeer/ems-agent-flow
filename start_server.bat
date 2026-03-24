@echo off
REM EMS Agent Flow - 服务启动脚本

echo ========================================
echo EMS Agent Flow - FastAPI 服务启动
echo ========================================
echo.

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在！
    echo 请先运行: uv sync
    pause
    exit /b 1
)

echo [1/2] 激活虚拟环境...
call .venv\Scripts\activate.bat

echo [2/2] 启动 FastAPI 服务...
echo.
echo 服务地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
