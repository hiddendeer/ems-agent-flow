"""
权限检查器。

验证操作者的权限级别。
"""

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class PermissionLevel(Enum):
    """权限级别"""
    READ_ONLY = "只读"        # 只能查看，不能操作
    OPERATOR = "操作员"       # 基本操作权限
    SUPERVISOR = "主管"       # 高级操作权限
    ADMIN = "管理员"          # 所有权限


class CommandCategory(Enum):
    """指令类别"""
    READ = "read"              # 读取操作
    BASIC = "basic"            # 基本操作（启停、待机）
    CONTROL = "control"        # 控制操作（充放电、调节功率）
    RISKY = "risky"            # 风险操作（复位、清零）
    CRITICAL = "critical"      # 关键操作（紧急停止、熔断）


@dataclass
class PermissionCheckResult:
    """权限检查结果"""
    is_allowed: bool
    required_level: str = ""
    reason: str = ""
    current_level: str = ""


class PermissionChecker:
    """
    权限检查器。

    权限级别要求：
    - READ_ONLY: 只读操作
    - OPERATOR: 基本操作 + READ_ONLY
    - SUPERVISOR: 控制操作 + OPERATOR
    - ADMIN: 所有权限
    """

    # 指令权限映射
    COMMAND_PERMISSIONS: Dict[str, CommandCategory] = {
        "charge": CommandCategory.CONTROL,
        "discharge": CommandCategory.CONTROL,
        "stop": CommandCategory.BASIC,
        "standby": CommandCategory.BASIC,
        "reset": CommandCategory.RISKY,
        "emergency_stop": CommandCategory.CRITICAL,
    }

    # 权限级别映射
    PERMISSION_LEVELS: Dict[str, PermissionLevel] = {
        "read_only": PermissionLevel.READ_ONLY,
        "operator": PermissionLevel.OPERATOR,
        "supervisor": PermissionLevel.SUPERVISOR,
        "admin": PermissionLevel.ADMIN,
    }

    # 类别所需最低权限
    CATEGORY_MIN_PERMISSIONS: Dict[CommandCategory, PermissionLevel] = {
        CommandCategory.READ: PermissionLevel.READ_ONLY,
        CommandCategory.BASIC: PermissionLevel.OPERATOR,
        CommandCategory.CONTROL: PermissionLevel.SUPERVISOR,
        CommandCategory.RISKY: PermissionLevel.ADMIN,
        CommandCategory.CRITICAL: PermissionLevel.ADMIN,
    }

    # 模拟用户权限存储（实际应从用户系统获取）
    _user_permissions: Dict[str, PermissionLevel] = {
        "system": PermissionLevel.ADMIN,           # 系统默认最高权限
        "user_001": PermissionLevel.SUPERVISOR,
        "user_002": PermissionLevel.OPERATOR,
        "user_003": PermissionLevel.READ_ONLY,
    }

    def check(
        self,
        operator: str,
        command_type: str
    ) -> PermissionCheckResult:
        """
        检查操作者权限。

        Args:
            operator: 操作者标识
            command_type: 指令类型

        Returns:
            PermissionCheckResult: 权限检查结果
        """
        # 1. 获取操作者权限级别
        user_level = self._user_permissions.get(operator, PermissionLevel.READ_ONLY)

        # 2. 获取指令所需权限级别
        command_category = self.COMMAND_PERMISSIONS.get(
            command_type.lower(),
            CommandCategory.CONTROL  # 默认为控制操作
        )
        required_level = self.CATEGORY_MIN_PERMISSIONS[command_category]

        # 3. 比较权限级别
        permission_order = [
            PermissionLevel.READ_ONLY,
            PermissionLevel.OPERATOR,
            PermissionLevel.SUPERVISOR,
            PermissionLevel.ADMIN,
        ]

        user_level_index = permission_order.index(user_level)
        required_level_index = permission_order.index(required_level)

        if user_level_index >= required_level_index:
            return PermissionCheckResult(
                is_allowed=True,
                current_level=user_level.value,
                required_level=required_level.value
            )
        else:
            return PermissionCheckResult(
                is_allowed=False,
                current_level=user_level.value,
                required_level=required_level.value,
                reason=f"操作者权限({user_level.value})不足，"
                       f"该操作需要{required_level.value}权限"
            )

    def grant_permission(self, user: str, level: str):
        """授予用户权限（用于模拟）"""
        permission_level = self.PERMISSION_LEVELS.get(level)
        if permission_level:
            self._user_permissions[user] = permission_level

    def revoke_permission(self, user: str):
        """撤销用户权限"""
        if user in self._user_permissions:
            del self._user_permissions[user]

    def get_user_level(self, user: str) -> PermissionLevel:
        """获取用户权限级别"""
        return self._user_permissions.get(user, PermissionLevel.READ_ONLY)
