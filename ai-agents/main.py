"""
Auto-Researcher Multi-Agent System
基于 LangGraph 的多智能体学术研究自动化系统
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入各个 Agent
from agents.orchestrator import OrchestratorAgent
from agents.search import SearchAgent
from agents.rag import RAGAgent
from agents.code import CodeAgent


class AgentType(str, Enum):
    """Agent 类型枚举"""
    ORCHESTRATOR = "orchestrator"
    SEARCH = "search"
    RAG = "rag"
    CODE = "code"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SubTask(TypedDict):
    """子任务定义"""
    id: str
    type: str  # 改为字符串类型
    description: str
    status: str  # 改为字符串类型
    result: Optional[Dict[str, Any]]  # 结果改为字典类型


class AgentState(TypedDict):
    """Agent 系统状态"""
    task_id: str
    original_task: str
    sub_tasks: List[SubTask]
    current_task_index: int
    results: Dict[str, Any]
    messages: List[str]
    error: Optional[str]
    files: List[Dict[str, Any]]  # 新增：存储生成的文件信息


class MultiAgentSystem:
    """多智能体系统主类"""
    
    def __init__(self):
        """初始化多智能体系统"""
        # 初始化各个 Agent
        self.orchestrator = OrchestratorAgent()
        self.search_agent = SearchAgent()
        self.rag_agent = RAGAgent()
        self.code_agent = CodeAgent()
        
        # 构建 LangGraph 工作流
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("rag", self._rag_node)
        workflow.add_node("code", self._code_node)
        
        # 设置入口节点
        workflow.set_entry_point("orchestrator")
        
        # 添加条件边（由 Orchestrator 决定下一个 Agent）
        # LangGraph 新版本使用 path 参数，不需要 mapping
        workflow.add_conditional_edges(
            "orchestrator",
            self._route_to_agent,
            {
                "search": "search",
                "rag": "rag",
                "code": "code",
                None: END  # None 表示结束
            }
        )
        
        # 各个 Agent 完成后回到 Orchestrator
        workflow.add_edge("search", "orchestrator")
        workflow.add_edge("rag", "orchestrator")
        workflow.add_edge("code", "orchestrator")
        
        return workflow.compile()
    
    def _orchestrator_node(self, state: AgentState) -> AgentState:
        """Orchestrator 节点"""
        print("\n=== Orchestrator 正在规划任务 ===")
        
        # 如果是第一个节点，拆解任务
        if not state.get("sub_tasks") or len(state.get("sub_tasks", [])) == 0:
            sub_tasks = self.orchestrator.plan_tasks(state["original_task"])
            state["sub_tasks"] = sub_tasks
            state["current_task_index"] = 0
            print(f"任务已拆解为 {len(sub_tasks)} 个子任务")
            for i, task in enumerate(sub_tasks):
                print(f"  {i+1}. [{task['type']}] {task['description']}")
        
        # 检查是否所有任务都已完成
        if state["current_task_index"] >= len(state["sub_tasks"]):
            print("所有子任务已完成")
            # 添加总结信息到 results
            if "summary" not in state["results"]:
                state["results"]["summary"] = self._generate_summary(state)
            return state
        
        # 获取当前任务
        current_task = state["sub_tasks"][state["current_task_index"]]
        print(f"\n当前执行任务：{current_task['description']}")
        
        return state
    
    def _search_node(self, state: AgentState) -> AgentState:
        """Search Agent 节点"""
        print("\n=== Search Agent 正在搜索文献 ===")
        
        current_task = state["sub_tasks"][state["current_task_index"]]
        
        # 执行搜索
        result = self.search_agent.search(current_task["description"])
        
        # 保存结果
        state["results"][current_task["id"]] = result
        state["sub_tasks"][state["current_task_index"]]["status"] = TaskStatus.COMPLETED
        state["sub_tasks"][state["current_task_index"]]["result"] = result
        
        # 收集文件
        print(f"Search Agent 返回的文件数量：{len(result.get('files', []))}")
        if "files" in result and result["files"]:
            if "files" not in state:
                state["files"] = []
            print(f"收集到 {len(result['files'])} 个文件")
            for f in result["files"]:
                print(f"  - {f.get('name', 'unknown')}")
            state["files"].extend(result["files"])
        
        # 更新消息历史
        state["messages"].append(f"Search Agent: {result}")
        
        # 移动到下一个任务
        state["current_task_index"] += 1
        
        return state
    
    def _rag_node(self, state: AgentState) -> AgentState:
        """RAG Agent 节点"""
        print("\n=== RAG Agent 正在解析论文 ===")
        
        current_task = state["sub_tasks"][state["current_task_index"]]
        
        # 执行 RAG
        result = self.rag_agent.analyze(current_task["description"])
        
        # 保存结果
        state["results"][current_task["id"]] = result
        state["sub_tasks"][state["current_task_index"]]["status"] = TaskStatus.COMPLETED
        state["sub_tasks"][state["current_task_index"]]["result"] = result
        
        # 收集文件
        print(f"RAG Agent 返回的文件数量：{len(result.get('files', []))}")
        if "files" in result and result["files"]:
            if "files" not in state:
                state["files"] = []
            print(f"收集到 {len(result['files'])} 个文件")
            for f in result["files"]:
                print(f"  - {f.get('name', 'unknown')}")
            state["files"].extend(result["files"])
        
        # 更新消息历史
        state["messages"].append(f"RAG Agent: {result}")
        
        # 移动到下一个任务
        state["current_task_index"] += 1
        
        return state
    
    def _code_node(self, state: AgentState) -> AgentState:
        """Code Agent 节点"""
        print("\n=== Code Agent 正在编写代码 ===")
        
        current_task = state["sub_tasks"][state["current_task_index"]]
        
        # 执行代码生成
        result = self.code_agent.generate_code(current_task["description"])
        
        # 保存结果
        state["results"][current_task["id"]] = result
        state["sub_tasks"][state["current_task_index"]]["status"] = TaskStatus.COMPLETED
        state["sub_tasks"][state["current_task_index"]]["result"] = result
        
        # 收集文件
        print(f"Code Agent 返回的文件数量：{len(result.get('files', []))}")
        if "files" in result and result["files"]:
            if "files" not in state:
                state["files"] = []
            print(f"收集到 {len(result['files'])} 个文件")
            for f in result["files"]:
                print(f"  - {f.get('name', 'unknown')}")
            state["files"].extend(result["files"])
        
        # 更新消息历史
        state["messages"].append(f"Code Agent: {result}")
        
        # 移动到下一个任务
        state["current_task_index"] += 1
        
        return state
    
    def _route_to_agent(self, state: AgentState) -> str:
        """路由到下一个 Agent"""
        # 检查是否所有任务都已完成
        if state["current_task_index"] >= len(state["sub_tasks"]):
            print("所有任务已完成，返回 None 结束工作流")
            return None  # 返回 None 表示结束
        
        # 获取当前任务的类型
        current_task = state["sub_tasks"][state["current_task_index"]]
        task_type = current_task["type"]
        print(f"路由到 Agent: {task_type}, 任务描述：{current_task['description']}")
        return task_type
    
    async def execute_task_stream(self, task_id: str, task_description: str):
        """
        流式执行任务，yield 每个阶段的事件
        
        Args:
            task_id: 任务 ID
            task_description: 任务描述
            
        Yields:
            事件字典，包含 type 和 data 字段
        """
        # 初始化状态
        initial_state: AgentState = {
            "task_id": task_id,
            "original_task": task_description,
            "sub_tasks": [],
            "current_task_index": 0,
            "results": {},
            "messages": [],
            "error": None,
            "files": []
        }
        
        print(f"\n{'='*60}")
        print(f"开始执行任务：{task_description}")
        print(f"{'='*60}")
        
        # 发送开始事件
        yield {
            "type": "start",
            "data": {"task_id": task_id, "description": task_description}
        }
        
        try:
            # 手动执行工作流的每个节点，以便流式输出
            state = initial_state
            
            # 执行 Orchestrator 节点
            print("\n=== Orchestrator 正在规划任务 ===")
            yield {
                "type": "thinking",
                "data": {"agent": "orchestrator", "message": "正在规划任务..."}
            }
            
            state = self._orchestrator_node(state)
            
            # 发送任务规划结果
            sub_tasks_info = []
            for task in state.get("sub_tasks", []):
                sub_tasks_info.append({
                    "id": task["id"],
                    "type": task["type"],
                    "description": task["description"]
                })
            
            yield {
                "type": "plan",
                "data": {
                    "sub_tasks": sub_tasks_info,
                    "count": len(sub_tasks_info)
                }
            }
            
            # 逐个执行子任务
            while state["current_task_index"] < len(state["sub_tasks"]):
                current_task = state["sub_tasks"][state["current_task_index"]]
                task_type = current_task["type"]
                
                # 发送当前任务开始事件
                yield {
                    "type": "thinking",
                    "data": {
                        "agent": task_type,
                        "message": f"正在执行：{current_task['description']}"
                    }
                }
                
                # 执行对应的 Agent
                if task_type == "search":
                    state = self._search_node(state)
                elif task_type == "rag":
                    state = self._rag_node(state)
                elif task_type == "code":
                    state = self._code_node(state)
                
                # 发送任务完成事件
                yield {
                    "type": "task_complete",
                    "data": {
                        "agent": task_type,
                        "task_id": current_task["id"],
                        "description": current_task["description"]
                    }
                }
            
            # 所有任务完成
            files_list = state.get("files", [])
            
            yield {
                "type": "complete",
                "data": {
                    "status": "completed",
                    "results": state["results"],
                    "summary": self._generate_summary(state),
                    "files": files_list
                }
            }
            
        except Exception as e:
            print(f"\n任务执行失败：{str(e)}")
            yield {
                "type": "error",
                "data": {"error": str(e)}
            }
    
    async def execute_task(self, task_id: str, task_description: str) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_id: 任务 ID
            task_description: 任务描述
            
        Returns:
            执行结果
        """
        # 初始化状态
        initial_state: AgentState = {
            "task_id": task_id,
            "original_task": task_description,
            "sub_tasks": [],
            "current_task_index": 0,
            "results": {},
            "messages": [],
            "error": None,
            "files": []  # 新增：收集所有生成的文件
        }
        
        print(f"\n{'='*60}")
        print(f"开始执行任务：{task_description}")
        print(f"{'='*60}")
        
        try:
            # 执行工作流
            final_state = await self.workflow.ainvoke(initial_state)
            
            # 收集所有结果和文件
            files_list = final_state.get("files", []) if isinstance(final_state, dict) else []
            
            print(f"\n{'='*60}")
            print("任务执行完成！")
            print(f"收集到的文件数量：{len(files_list)}")
            if files_list:
                print("文件列表:")
                for f in files_list:
                    print(f"  - {f.get('name', 'unknown')} ({f.get('path', 'unknown')})")
            else:
                print("警告：没有收集到任何文件！")
            print(f"{'='*60}")
            
            results = {
                "task_id": task_id,
                "status": "completed",
                "sub_tasks": final_state["sub_tasks"],
                "results": final_state["results"],
                "summary": self._generate_summary(final_state),
                "files": files_list  # 收集所有文件
            }
            
            return results
            
        except Exception as e:
            print(f"\n任务执行失败：{str(e)}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "files": []
            }
    
    def _generate_summary(self, state: AgentState) -> str:
        """生成任务总结"""
        summary = []
        summary.append(f"任务：{state['original_task']}")
        summary.append(f"子任务数量：{len(state['sub_tasks'])}")
        summary.append(f"完成数量：{sum(1 for t in state['sub_tasks'] if t['status'] == 'completed')}")
        
        return "\n".join(summary)


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # 创建多智能体系统
        agent_system = MultiAgentSystem()
        
        # 执行任务
        task_description = "研究大模型机器遗忘的最新方法，找到相关论文，解析核心算法，并实现示例代码"
        
        results = await agent_system.execute_task(
            task_id="task_001",
            task_description=task_description
        )
        
        print("\n最终结果：")
        print(results["summary"])
    
    # 运行
    asyncio.run(main())
