"""
AI Agents FastAPI Service
提供多智能体系统的 HTTP API 接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
import uuid

from main import MultiAgentSystem

# 创建 FastAPI 应用
app = FastAPI(
    title="Auto-Researcher AI Agents",
    description="多智能体学术研究自动化系统 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化多智能体系统
agent_system = MultiAgentSystem()


class TaskRequest(BaseModel):
    """任务请求模型"""
    task_id: Optional[str] = None
    description: str


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    files: Optional[list] = None  # 新增：生成的文件列表


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Auto-Researcher AI Agents Service",
        "version": "1.0.0",
        "endpoints": {
            "execute_task": "POST /api/v1/task/execute",
            "get_status": "GET /api/v1/status"
        }
    }


@app.post("/api/v1/task/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    执行任务
    
    Args:
        request: 任务请求
        
    Returns:
        任务执行结果
    """
    # 生成任务 ID（如果没有提供）
    task_id = request.task_id or str(uuid.uuid4())
    
    try:
        # 异步执行任务
        result = await agent_system.execute_task(
            task_id=task_id,
            task_description=request.description
        )
        
        print(f"\n[API] 返回结果:")
        print(f"  - task_id: {task_id}")
        print(f"  - status: {result.get('status')}")
        print(f"  - files 数量：{len(result.get('files', []))}")
        
        return TaskResponse(
            task_id=task_id,
            status=result.get("status", "completed"),
            results=result.get("results"),
            error=result.get("error"),
            files=result.get("files", [])  # 新增：包含文件列表
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"任务执行失败：{str(e)}"
        )


@app.post("/api/v1/task/stream")
async def execute_task_stream(request: TaskRequest):
    """
    流式执行任务，返回 SSE 事件流
    
    Args:
        request: 任务请求
        
    Returns:
        SSE 事件流
    """
    task_id = request.task_id or str(uuid.uuid4())
    
    async def event_generator():
        async for event in agent_system.execute_task_stream(
            task_id=task_id,
            task_description=request.description
        ):
            # 将事件格式化为 SSE 格式
            data = json.dumps(event, ensure_ascii=False)
            yield f"data: {data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/v1/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "running",
        "agents": {
            "orchestrator": agent_system.orchestrator.get_status(),
            "search": agent_system.search_agent.get_status(),
            "rag": agent_system.rag_agent.get_status(),
            "code": agent_system.code_agent.get_status()
        }
    }


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
