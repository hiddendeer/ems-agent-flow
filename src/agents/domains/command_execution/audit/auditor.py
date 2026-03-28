"""
操作审计追踪器。

提供完整的操作审计追踪能力。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .logger import OperationLogger, OperationLog, OperationStatus, get_logger

logger = logging.getLogger(__name__)


class OperationAuditor:
    """
    操作审计追踪器。

    功能：
    - 完整的操作轨迹追踪
    - 审计报告生成
    - 异常操作检测
    - 合规性检查
    """

    def __init__(self, operation_logger: OperationLogger = None):
        """
        初始化审计追踪器。

        Args:
            operation_logger: 操作日志记录器
        """
        self.logger = operation_logger or get_logger()

    def audit_operation(
        self,
        operation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        审计单个操作。

        Args:
            operation_id: 操作ID

        Returns:
            审计报告字典
        """
        log = self.logger.get_log(operation_id)
        if not log:
            logger.warning(f"审计失败：操作不存在: {operation_id}")
            return None

        # 生成审计报告
        report = {
            "operation_id": operation_id,
            "audit_time": datetime.now().isoformat(),
            "operation_details": log.to_dict(),
            "compliance_check": self._check_compliance(log),
            "risk_assessment": self._assess_risk(log),
            "recommendations": self._generate_recommendations(log)
        }

        return report

    def audit_device(
        self,
        device_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        审计设备操作。

        Args:
            device_id: 设备ID
            days: 审计天数

        Returns:
            设备审计报告
        """
        logs = self.logger.get_logs_by_device(device_id, limit=1000)

        # 过滤指定天数内的日志
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        recent_logs = [
            log for log in logs
            if datetime.fromisoformat(log.timestamp).timestamp() > cutoff_time
        ]

        # 统计分析
        total = len(recent_logs)
        if total == 0:
            return {
                "device_id": device_id,
                "audit_period_days": days,
                "total_operations": 0,
                "message": "该时段内无操作记录"
            }

        success_count = sum(1 for log in recent_logs if log.status == OperationStatus.SUCCESS)
        failed_count = sum(1 for log in recent_logs if log.status == OperationStatus.FAILED)
        rejected_count = sum(1 for log in recent_logs if log.status == OperationStatus.REJECTED)

        # 指令类型分布
        command_distribution = {}
        for log in recent_logs:
            cmd = log.command_type
            command_distribution[cmd] = command_distribution.get(cmd, 0) + 1

        # 操作者分布
        operator_distribution = {}
        for log in recent_logs:
            op = log.operator
            operator_distribution[op] = operator_distribution.get(op, 0) + 1

        return {
            "device_id": device_id,
            "audit_period_days": days,
            "total_operations": total,
            "success_rate": f"{success_count / total * 100:.1f}%",
            "statistics": {
                "success": success_count,
                "failed": failed_count,
                "rejected": rejected_count
            },
            "command_distribution": command_distribution,
            "operator_distribution": operator_distribution,
            "recent_logs": [log.to_dict() for log in recent_logs[-10:]]
        }

    def audit_operator(
        self,
        operator: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        审计操作者行为。

        Args:
            operator: 操作者标识
            days: 审计天数

        Returns:
            操作者审计报告
        """
        logs = self.logger.get_logs_by_operator(operator, limit=1000)

        # 过滤指定天数内的日志
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        recent_logs = [
            log for log in logs
            if datetime.fromisoformat(log.timestamp).timestamp() > cutoff_time
        ]

        total = len(recent_logs)
        if total == 0:
            return {
                "operator": operator,
                "audit_period_days": days,
                "total_operations": 0,
                "message": "该时段内无操作记录"
            }

        # 统计分析
        success_count = sum(1 for log in recent_logs if log.status == OperationStatus.SUCCESS)
        failed_count = sum(1 for log in recent_logs if log.status == OperationStatus.FAILED)

        # 设备操作分布
        device_distribution = {}
        for log in recent_logs:
            device = log.device_id
            device_distribution[device] = device_distribution.get(device, 0) + 1

        # 高风险操作检测
        high_risk_operations = [
            log.to_dict() for log in recent_logs
            if log.risk_level in ["高", "严重"]
        ]

        return {
            "operator": operator,
            "audit_period_days": days,
            "total_operations": total,
            "success_rate": f"{success_count / total * 100:.1f}%",
            "statistics": {
                "success": success_count,
                "failed": failed_count
            },
            "device_distribution": device_distribution,
            "high_risk_operations": high_risk_operations,
            "compliance_score": self._calculate_compliance_score(recent_logs)
        }

    def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        检测异常操作。

        Args:
            hours: 检测时间范围（小时）

        Returns:
            异常操作列表
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_logs = [
            log for log in self.logger.get_recent_logs(limit=1000)
            if datetime.fromisoformat(log.timestamp).timestamp() > cutoff_time
        ]

        anomalies = []

        # 1. 检测频繁失败的操作
        failed_operations = [log for log in recent_logs if log.status == OperationStatus.FAILED]
        if len(failed_operations) > 5:
            anomalies.append({
                "type": "频繁失败",
                "severity": "中",
                "description": f"过去{hours}小时内发现{len(failed_operations)}次失败操作",
                "affected_devices": list(set(log.device_id for log in failed_operations))
            })

        # 2. 检测被拒绝的操作
        rejected_operations = [log for log in recent_logs if log.status == OperationStatus.REJECTED]
        if len(rejected_operations) > 3:
            anomalies.append({
                "type": "审查拒绝",
                "severity": "低",
                "description": f"过去{hours}小时内发现{len(rejected_operations)}次被拒绝的操作",
                "details": [log.to_dict() for log in rejected_operations[-5:]]
            })

        # 3. 检测高风险操作
        high_risk_operations = [
            log for log in recent_logs
            if log.risk_level in ["高", "严重"]
        ]
        if len(high_risk_operations) > 2:
            anomalies.append({
                "type": "高风险操作",
                "severity": "高",
                "description": f"过去{hours}小时内发现{len(high_risk_operations)}次高风险操作",
                "details": [log.to_dict() for log in high_risk_operations[-5:]]
            })

        return anomalies

    def _check_compliance(self, log: OperationLog) -> Dict[str, Any]:
        """检查合规性"""
        issues = []

        # 检查1: 是否有完整的审查记录
        if not log.review_result:
            issues.append("缺少审查记录")

        # 检查2: 风险评估是否完整
        if not log.risk_level:
            issues.append("缺少风险评估")

        # 检查3: 高风险操作是否有特殊授权
        if log.risk_level in ["高", "严重"]:
            if log.metadata.get("special_authorization") is True:
                issues.append("高风险操作需要特殊授权")

        return {
            "is_compliant": len(issues) == 0,
            "issues": issues
        }

    def _assess_risk(self, log: OperationLog) -> Dict[str, Any]:
        """评估操作风险"""
        risk_score = 0

        # 基于指令类型的风险评分
        if log.command_type in ["reset", "emergency_stop"]:
            risk_score += 30
        elif log.command_type in ["charge", "discharge"]:
            risk_score += 20

        # 基于参数的风险评分
        power = log.parameters.get("power", 0)
        if power > 1000:
            risk_score += 20

        # 基于设备状态的风险评分
        if log.status == OperationStatus.FAILED:
            risk_score += 20

        return {
            "risk_score": min(risk_score, 100),
            "risk_level": "低" if risk_score < 40 else "中" if risk_score < 70 else "高"
        }

    def _generate_recommendations(self, log: OperationLog) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if log.status == OperationStatus.FAILED:
            recommendations.append("检查失败原因并优化操作流程")

        if log.risk_level in ["高", "严重"]:
            recommendations.append("高风险操作建议增加审批环节")

        if not log.review_result:
            recommendations.append("确保所有操作都经过审查")

        return recommendations

    def _calculate_compliance_score(self, logs: List[OperationLog]) -> float:
        """计算合规性评分"""
        if not logs:
            return 100.0

        total = len(logs)
        compliant = 0

        for log in logs:
            compliance = self._check_compliance(log)
            if compliance["is_compliant"]:
                compliant += 1

        return round(compliant / total * 100, 1)
