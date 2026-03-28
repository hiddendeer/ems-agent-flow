"""
操作日志记录器。

记录所有指令操作的完整轨迹。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """操作状态"""
    PENDING = "待执行"
    REVIEWING = "审查中"
    APPROVED = "已批准"
    REJECTED = "已拒绝"
    EXECUTING = "执行中"
    SUCCESS = "成功"
    FAILED = "失败"
    CANCELLED = "已取消"


@dataclass
class OperationLog:
    """操作日志"""
    operation_id: str                    # 操作ID
    command_type: str                    # 指令类型
    device_id: str                       # 设备ID
    operator: str                        # 操作者
    parameters: Dict[str, Any]           # 指令参数
    status: OperationStatus              # 操作状态
    timestamp: str                       # 时间戳
    review_result: Optional[str] = None  # 审查结果
    risk_level: Optional[str] = None     # 风险等级
    execution_result: Optional[str] = None  # 执行结果
    error_message: Optional[str] = None  # 错误信息
    metadata: Dict[str, Any] = None      # 元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            **asdict(self),
            "status": self.status.value,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class OperationLogger:
    """
    操作日志记录器。

    功能：
    - 记录操作日志
    - 查询操作历史
    - 导出日志数据
    - 日志统计分析
    """

    def __init__(self, log_file: str = "operation_logs.jsonl"):
        """
        初始化日志记录器。

        Args:
            log_file: 日志文件路径
        """
        self.log_file = log_file
        self._logs: List[OperationLog] = []
        self._load_logs()

    def _load_logs(self):
        """加载历史日志"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        data['status'] = OperationStatus(data['status'])
                        log = OperationLog(**data)
                        self._logs.append(log)
            logger.info(f"已加载 {len(self._logs)} 条历史日志")
        except FileNotFoundError:
            logger.info("日志文件不存在，创建新文件")
            self._logs = []
        except Exception as e:
            logger.error(f"加载日志失败: {e}")
            self._logs = []

    def _save_log(self, log: OperationLog):
        """保存单条日志"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log.to_json() + '\n')
        except Exception as e:
            logger.error(f"保存日志失败: {e}")

    def create_log(
        self,
        command_type: str,
        device_id: str,
        operator: str,
        parameters: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> OperationLog:
        """
        创建新的操作日志。

        Args:
            command_type: 指令类型
            device_id: 设备ID
            operator: 操作者
            parameters: 指令参数
            metadata: 元数据

        Returns:
            OperationLog: 操作日志对象
        """
        operation_id = f"OP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{device_id}"

        log = OperationLog(
            operation_id=operation_id,
            command_type=command_type,
            device_id=device_id,
            operator=operator,
            parameters=parameters,
            status=OperationStatus.PENDING,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )

        self._logs.append(log)
        self._save_log(log)
        logger.info(f"创建操作日志: {operation_id}")

        return log

    def update_log(
        self,
        operation_id: str,
        status: OperationStatus = None,
        review_result: str = None,
        risk_level: str = None,
        execution_result: str = None,
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[OperationLog]:
        """
        更新操作日志。

        Args:
            operation_id: 操作ID
            status: 操作状态
            review_result: 审查结果
            risk_level: 风险等级
            execution_result: 执行结果
            error_message: 错误信息
            metadata: 元数据

        Returns:
            OperationLog: 更新后的日志对象，如果不存在返回None
        """
        log = self.get_log(operation_id)
        if not log:
            logger.warning(f"操作日志不存在: {operation_id}")
            return None

        if status:
            log.status = status
        if review_result:
            log.review_result = review_result
        if risk_level:
            log.risk_level = risk_level
        if execution_result:
            log.execution_result = execution_result
        if error_message:
            log.error_message = error_message
        if metadata:
            log.metadata.update(metadata)

        log.timestamp = datetime.now().isoformat()
        self._save_log(log)
        logger.info(f"更新操作日志: {operation_id} -> {status.value if status else ''}")

        return log

    def get_log(self, operation_id: str) -> Optional[OperationLog]:
        """获取操作日志"""
        for log in reversed(self._logs):  # 从最新的开始查找
            if log.operation_id == operation_id:
                return log
        return None

    def get_logs_by_device(self, device_id: str, limit: int = 100) -> List[OperationLog]:
        """获取设备的操作日志"""
        return [
            log for log in self._logs
            if log.device_id == device_id
        ][-limit:]

    def get_logs_by_operator(self, operator: str, limit: int = 100) -> List[OperationLog]:
        """获取操作者的操作日志"""
        return [
            log for log in self._logs
            if log.operator == operator
        ][-limit:]

    def get_logs_by_status(self, status: OperationStatus, limit: int = 100) -> List[OperationLog]:
        """获取指定状态的日志"""
        return [
            log for log in self._logs
            if log.status == status
        ][-limit:]

    def get_recent_logs(self, limit: int = 50) -> List[OperationLog]:
        """获取最近的日志"""
        return self._logs[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        total = len(self._logs)
        if total == 0:
            return {"total": 0}

        status_count = {}
        for log in self._logs:
            status = log.status.value
            status_count[status] = status_count.get(status, 0) + 1

        device_count = {}
        for log in self._logs:
            device = log.device_id
            device_count[device] = device_count.get(device, 0) + 1

        return {
            "total": total,
            "status_distribution": status_count,
            "device_usage": device_count,
            "success_rate": f"{status_count.get('成功', 0) / total * 100:.1f}%"
        }


# 全局日志记录器实例
_global_logger: Optional[OperationLogger] = None


def get_logger() -> OperationLogger:
    """获取全局日志记录器"""
    global _global_logger
    if _global_logger is None:
        _global_logger = OperationLogger()
    return _global_logger
