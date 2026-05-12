"""
Orchestrator Agent - 协调者智能体
负责接收任务、拆解任务、分配给子 Agent 并监控执行状态
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import os
import json


class OrchestratorAgent:
    """Orchestrator Agent 类"""
    
    def __init__(self):
        """初始化 Orchestrator Agent"""
        # 初始化 LLM（使用 DeepSeek）
        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE_ORCHESTRATOR", "0.7"))
        )
        
        # 系统提示词
        self.system_prompt = """你是一个学术研究任务的协调者（Orchestrator）。你的职责是：

1. 接收复杂的学术研究任务
2. 将任务拆解为多个子任务，每个子任务由专门的 Agent 执行：
   - Search Agent: 搜索学术文献、查找相关资料
   - RAG Agent: 解析论文内容、提取关键方法和技术细节
   - Code Agent: 根据论文方法编写实现代码和示例

3. 为每个子任务指定合适的 Agent 类型
4. 监控执行进度，确保所有子任务完成

请按照以下 JSON 格式返回任务拆解结果：
{
  "sub_tasks": [
    {
      "id": "task_1",
      "type": "search|rag|code",
      "description": "任务描述",
      "priority": 1
    }
  ]
}

确保任务拆解合理，Agent 类型选择正确。"""

    def plan_tasks(self, task_description: str, retrieved_memories: str = None) -> List[Dict[str, Any]]:
        """
        规划子任务
        
        Args:
            task_description: 原始任务描述
            retrieved_memories: 检索到的相关长期记忆（可选）
            
        Returns:
            子任务列表
        """
        # 构建记忆上下文
        memory_context = ""
        if retrieved_memories:
            memory_context = f"""

以下是相关的历史记忆，请参考这些信息来优化任务拆解：
{retrieved_memories}
"""
        
        # 构建提示词
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"请拆解以下任务：{task_description}{memory_context}")
        ])
        
        # 调用 LLM
        chain = prompt | self.llm
        response = chain.invoke({})
        
        # 解析响应
        try:
            # 提取 JSON 内容
            content = response.content
            # 查找 JSON 块
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
                
                # 转换为需要的格式
                sub_tasks = []
                for task in result.get("sub_tasks", []):
                    sub_tasks.append({
                        "id": task["id"],
                        "type": task["type"],
                        "description": task["description"],
                        "status": "pending",
                        "result": None
                    })
                
                return sub_tasks
            else:
                # 如果解析失败，返回默认任务拆解
                return self._default_plan(task_description)
                
        except Exception as e:
            print(f"解析任务规划失败：{e}")
            return self._default_plan(task_description)
    
    def _default_plan(self, task_description: str) -> List[Dict[str, Any]]:
        """默认任务拆解策略"""
        # 基于关键词的简单规则
        sub_tasks = []
        
        task_lower = task_description.lower()
        
        # 检查是否需要搜索
        if any(word in task_lower for word in ["研究", "查找", "搜索", "文献", "论文", "最新"]):
            sub_tasks.append({
                "id": "search_1",
                "type": "search",
                "description": f"搜索与'{task_description}'相关的学术文献",
                "status": "pending",
                "result": None
            })
        
        # 检查是否需要解析
        if any(word in task_lower for word in ["解析", "分析", "理解", "方法", "算法", "技术"]):
            sub_tasks.append({
                "id": "rag_1",
                "type": "rag",
                "description": f"解析相关论文的核心方法和技术细节",
                "status": "pending",
                "result": None
            })
        
        # 检查是否需要代码
        if any(word in task_lower for word in ["实现", "代码", "示例", "编程", "编写"]):
            sub_tasks.append({
                "id": "code_1",
                "type": "code",
                "description": f"根据论文方法编写实现代码和示例",
                "status": "pending",
                "result": None
            })
        
        # 如果没有匹配任何规则，至少创建一个搜索任务
        if not sub_tasks:
            sub_tasks.append({
                "id": "search_1",
                "type": "search",
                "description": f"搜索与'{task_description}'相关的资料",
                "status": "pending",
                "result": None
            })
        
        return sub_tasks
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "type": "orchestrator",
            "status": "ready",
            "llm_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        }
