import os
import json
import logging
from typing import Dict, Any
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """每个用户独立的工作区和长期记忆管理器。"""
    
    def __init__(self, base_dir: str, user_id: str):
        self.base_dir = base_dir
        self.user_id = user_id
        # 用户物理沙箱路径：根目录/workspaces/user_id
        self.workspace_dir = os.path.join(base_dir, "workspaces", user_id)
        self.profile_path = os.path.join(self.workspace_dir, "user_profile.json")
        self._ensure_workspace()
        
    def _ensure_workspace(self):
        """确保工作区目录和初始记忆档案存在"""
        os.makedirs(os.path.join(self.workspace_dir, "reports"), exist_ok=True)
        if not os.path.exists(self.profile_path):
            initial_profile = {
                "user_id": self.user_id,
                "preferences": {},         # 用户的排版喜好、阅读偏好等
                "business_context": {},    # 业务参数，如所在省份、储能容量、企业类型
                "notes": []                # 其他补充信息
            }
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(initial_profile, f, ensure_ascii=False, indent=2)

    def get_workspace_dir(self) -> str:
        """获取沙箱工作区绝对路径"""
        return self.workspace_dir

    def get_profile_summary(self) -> str:
        """获取供大模型阅读的档案摘要"""
        if not os.path.exists(self.profile_path):
            return "当前用户暂无历史偏好档案。"
            
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"读取用户记忆档案失败: {str(e)}")
            return "记忆档案读取失败或已损坏。"
            
    def update_profile(self, category: str, key: str, value: str) -> str:
        """更新特定分类的档案值 (供智能体底层工具调用)"""
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if category not in data:
                data[category] = {}
            
            # 1. 如果是字典类型 (preferences, business_context)
            if isinstance(data[category], dict):
                data[category][key] = value
            
            # 2. 如果是列表类型 (notes) - 增强这里逻辑，防止只存时间
            elif isinstance(data[category], list):
                category_list = data[category]
                # 将 key 和 value 组合成更完整的描述，或者存为对象
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 构造综合描述：[分类/时间] 键: 值
                composite_entry = f"[{timestamp}] {key}: {value}"
                
                # 简单排重处理
                if composite_entry not in category_list:
                    # 如果列表太长，保留最近的 100 条
                    category_list.append(composite_entry)
                    if len(category_list) > 100:
                        data[category] = category_list[-100:]
                
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 记忆更新 [{self.user_id}] - {category}/{key}: {value}")
            return f"成功记录到持久化记忆库 [{category}] -> {key}: {value}。已完成自我进化。"
        except Exception as e:
            logger.error(f"记忆更新失败: {str(e)}")
            return f"档案更新失败: {str(e)}"

def create_memory_expert_tool(manager: WorkspaceManager) -> StructuredTool:
    """生成能让 LLM 主动调用以自我记录的长期记忆工具"""
    
    def update_user_memory(category: str, key: str, value: str) -> str:
        """
        当你察觉到用户在对话中透露了关键的业务背景、环境参数（如所在的省份、控制的储能容量）
        或者是表达了明确的报告偏好特性时（如“我喜欢看纯表格”、“下次加上分析”），
        你 MUST 立即使用本工具将这些信息写入记忆库固化，实现系统自进化，以免以后重复询问。
        """
        # 强制限定分类
        valid_categories = ["preferences", "business_context", "notes"]
        if category not in valid_categories:
            category = "notes"
        return manager.update_profile(category, key, value)
        
    return StructuredTool.from_function(
        func=update_user_memory,
        name="update_user_memory",
        description=(
            "极为重要的“自我进化/长期记忆”工具。当用户提供长效背景参数（如自身省份、企业资产属性）、"
            "或者对报告产出偏好提出约束、或者是需要记录重要的业务操作结果时，立即使用此工具将其固化。"
            "category参数必须是: 'preferences' (排版喜好), 'business_context' (业务参数属性), 'notes' (备忘录/操作日志)。"
            "如果是notes分类，key应该是摘要提示，value应该是详细的内容描述。"
        ),
    )
