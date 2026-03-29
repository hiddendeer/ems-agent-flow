"""
EMS 设备管理路由 (Simulated)
提供设备的 CRUD 接口，用于 MCP 协议测试和 AI 对话处理
"""

from fastapi import APIRouter, HTTPException
from typing import List

from src.common.schemas import ResponseModel
from src.projectApi.schemas import DeviceCreate, DeviceUpdate, DeviceResponse
from src.projectApi.service import device_service

# 初始化路由
router = APIRouter(prefix="/devices", tags=["设备管理"])


@router.get(
    "/",
    response_model=ResponseModel[List[DeviceResponse]],
    summary="获取所有设备列表",
    description="返回系统中所有模拟设备的列表。"
)
async def list_devices():
    """获取设备列表"""
    devices = await device_service.list_devices()
    return ResponseModel(
        code=200,
        message="success",
        data=[DeviceResponse(**d) for d in devices]
    )


@router.get(
    "/{device_id}",
    response_model=ResponseModel[DeviceResponse],
    summary="获取特定设备详情",
    description="通过设备 ID 查询详细信息。"
)
async def get_device(device_id: str):
    """获取设备详情"""
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    
    return ResponseModel(
        code=200,
        message="success",
        data=DeviceResponse(**device)
    )


@router.post(
    "/",
    response_model=ResponseModel[DeviceResponse],
    summary="添加新设备",
    description="在系统中创建一个新的模拟设备。"
)
async def create_device(device_data: DeviceCreate):
    """创建设备"""
    new_device = await device_service.create_device(device_data.model_dump())
    return ResponseModel(
        code=201,
        message="设备创建成功",
        data=DeviceResponse(**new_device)
    )


@router.patch(
    "/{device_id}",
    response_model=ResponseModel[DeviceResponse],
    summary="更新设备信息",
    description="修改指定设备的属性（如名称、状态、位置等）。"
)
async def update_device(device_id: str, device_data: DeviceUpdate):
    """更新设备"""
    updated_device = await device_service.update_device(
        device_id, 
        device_data.model_dump(exclude_unset=True)
    )
    if not updated_device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
    return ResponseModel(
        code=200,
        message="设备更新成功",
        data=DeviceResponse(**updated_device)
    )


@router.delete(
    "/{device_id}",
    response_model=ResponseModel,
    summary="删除设备",
    description="从系统中移除指定的模拟设备。"
)
async def delete_device(device_id: str):
    """删除设备"""
    success = await device_service.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
    return ResponseModel(
        code=200,
        message="设备已成功删除",
        data=None
    )
