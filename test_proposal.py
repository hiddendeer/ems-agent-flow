"""
执行提案功能测试脚本

演示如何使用结构化的执行提案
"""

import sys
import json

# 添加项目路径
sys.path.insert(0, 'e:/EMS/ems-agent-flow')

from src.agents.domains.command_execution.schemas import (
    ExecutionProposal,
    ProposalResponse,
    CommandType,
    RiskLevel,
    ProposalStatus
)

# 测试 1: 创建提案
print("=" * 70)
print("Test 1: Create Execution Proposal")
print("=" * 70)

proposal = ExecutionProposal(
    proposal_id="PROP-20260403-TEST-001",
    status=ProposalStatus.PENDING_EXECUTION,
    target={
        "device_id": "dev_001",
        "device_type": "PCS",
        "command_type": CommandType.CHARGE,
        "api_endpoint": "/api/v1/devices/pcs/charge",
        "http_method": "POST",
        "parameters": [
            {
                "name": "power",
                "value": 100.0,
                "data_type": "float",
                "unit": "kW",
                "range": {"min": 0, "max": 500},
                "required": True
            },
            {
                "name": "target_soc",
                "value": 80,
                "data_type": "int",
                "unit": "%",
                "range": {"min": 0, "max": 100},
                "required": True
            }
        ],
        "timeout_seconds": 30,
        "retry_count": 3
    },
    validation={
        "passed": True,
        "parameter_validation": True,
        "safety_check": True,
        "permission_check": True
    },
    risk_assessment={
        "risk_level": RiskLevel.LOW,
        "risk_factors": [],
        "confidence_score": 0.95
    },
    audit={
        "proposal_id": "PROP-20260403-TEST-001",
        "operator": "system",
        "agent_name": "CommandExecutionExpert",
        "session_id": "test_session_001",
        "review_summary": "Test proposal for charging operation"
    },
    priority=5,
    tags=["test", "charge"]
)

print("Proposal created successfully!")
print(f"Proposal ID: {proposal.proposal_id}")
print(f"Status: {proposal.status}")
print(f"Device: {proposal.target.device_id}")
print(f"Command: {proposal.target.command_type}")
print(f"Risk Level: {proposal.risk_assessment.risk_level}")
print()

# 测试 2: 转换为执行请求
print("=" * 70)
print("Test 2: Convert to Execution Request")
print("=" * 70)

execution_request = proposal.to_execution_request()
print("Execution Request:")
print(json.dumps(execution_request, indent=2, ensure_ascii=False))
print()

# 测试 3: 检查安全性
print("=" * 70)
print("Test 3: Check Safety")
print("=" * 70)

is_safe = proposal.is_safe_to_execute()
print(f"Is safe to execute: {is_safe}")
print()

# 测试 4: JSON 序列化
print("=" * 70)
print("Test 4: JSON Serialization")
print("=" * 70)

proposal_dict = proposal.dict(by_alias=True, exclude_none=True)
proposal_json = json.dumps(proposal_dict, indent=2, ensure_ascii=False)
print("Proposal JSON (first 500 chars):")
print(proposal_json[:500] + "...")
print()

print("=" * 70)
print("All tests passed!")
print("=" * 70)
