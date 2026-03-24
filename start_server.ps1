# EMS Agent Flow - 服务启动脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EMS Agent Flow - FastAPI 服务启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "[错误] 虚拟环境不存在！" -ForegroundColor Red
    Write-Host "请先运行: uv sync" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "[1/2] 激活虚拟环境..." -ForegroundColor Green
. .venv\Scripts\Activate.ps1

Write-Host "[2/2] 启动 FastAPI 服务..." -ForegroundColor Green
Write-Host ""
Write-Host "服务地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
