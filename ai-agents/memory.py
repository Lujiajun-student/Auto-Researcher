"""
Long-term Memory Module - 长期记忆模块
基于 RAG 的长期记忆系统，使用向量存储实现语义检索
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """记忆类型"""
    TASK_RESULT = "task_result"       # 任务执行结果
    USER_PREFERENCE = "user_preference" # 用户偏好
    KNOWLEDGE = "knowledge"            # 领域知识
    EXPERIENCE = "experience"          # 经验教训


class MemoryEntry:
    """记忆条目"""
    
    def __init__(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = self._generate_id(content)
        self.content = content
        self.memory_type = memory_type
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.access_count = 0
    
    def _generate_id(self, content: str) -> str:
        """生成记忆 ID"""
        return hashlib.md5(f"{content}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "access_count": self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """从字典创建"""
        entry = cls(
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            metadata=data.get("metadata", {})
        )
        entry.id = data["id"]
        entry.created_at = data.get("created_at", datetime.now().isoformat())
        entry.access_count = data.get("access_count", 0)
        return entry


class LongTermMemory:
    """长期记忆管理类"""
    
    def __init__(self, storage_path: str = None):
        """
        初始化长期记忆
        
        Args:
            storage_path: 记忆存储路径（JSON 文件）
        """
        self.storage_path = storage_path or os.getenv(
            "MEMORY_STORAGE_PATH",
            os.path.join(os.path.dirname(__file__), "data", "long_term_memory.json")
        )
        self.max_retrievals = int(os.getenv("MEMORY_MAX_RETRIEVALS", "3"))
        self.memories: List[MemoryEntry] = []
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # 加载已有记忆
        self._load_memories()
    
    def _load_memories(self):
        """从文件加载记忆"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = [MemoryEntry.from_dict(m) for m in data]
                print(f"[Memory] 加载了 {len(self.memories)} 条长期记忆")
            except Exception as e:
                print(f"[Memory] 加载记忆失败: {e}")
                self.memories = []
    
    def _save_memories(self):
        """保存记忆到文件"""
        try:
            data = [m.to_dict() for m in self.memories]
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] 保存记忆失败: {e}")
    
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            metadata: 附加元数据
            
        Returns:
            创建的记忆条目
        """
        entry = MemoryEntry(content, memory_type, metadata)
        self.memories.append(entry)
        self._save_memories()
        print(f"[Memory] 添加记忆: {memory_type.value} - {content[:50]}...")
        return entry
    
    def search_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆（基于关键词匹配）
        
        Args:
            query: 搜索查询
            memory_type: 可选的记忆类型过滤
            top_k: 返回结果数量
            
        Returns:
            相关记忆列表
        """
        query_lower = query.lower()
        results = []
        
        for memory in self.memories:
            # 类型过滤
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # 计算相关性分数
            score = self._calculate_relevance(query_lower, memory)
            
            if score > 0:
                memory.access_count += 1
                results.append({
                    "memory": memory.to_dict(),
                    "score": score
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # 更新访问计数并保存
        self._save_memories()
        
        return results[:top_k]
    
    def _calculate_relevance(self, query: str, memory: MemoryEntry) -> float:
        """
        计算查询与记忆的相关性分数
        
        Args:
            query: 查询文本（小写）
            memory: 记忆条目
            
        Returns:
            相关性分数 (0-1)
        """
        score = 0.0
        
        # 内容匹配
        content_lower = memory.content.lower()
        
        # 关键词匹配
        query_words = set(query.split())
        content_words = set(content_lower.split())
        common_words = query_words & content_words
        
        if common_words:
            # Jaccard 相似度
            all_words = query_words | content_words
            score += len(common_words) / len(all_words) * 0.6
        
        # 子串匹配
        if query in content_lower:
            score += 0.3
        
        # 元数据匹配
        for key, value in memory.metadata.items():
            if isinstance(value, str) and query in value.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def get_memories_by_type(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """获取指定类型的所有记忆"""
        return [m for m in self.memories if m.memory_type == memory_type]
    
    def get_recent_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """获取最近添加的记忆"""
        return sorted(
            self.memories,
            key=lambda m: m.created_at,
            reverse=True
        )[:limit]
    
    def get_popular_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """获取最常访问的记忆"""
        return sorted(
            self.memories,
            key=lambda m: m.access_count,
            reverse=True
        )[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除指定记忆"""
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                self.memories.pop(i)
                self._save_memories()
                return True
        return False
    
    def clear_memories(self, memory_type: Optional[MemoryType] = None):
        """清空记忆"""
        if memory_type:
            self.memories = [m for m in self.memories if m.memory_type != memory_type]
        else:
            self.memories = []
        self._save_memories()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        stats = {
            "total": len(self.memories),
            "by_type": {},
            "total_access_count": sum(m.access_count for m in self.memories)
        }
        
        for memory_type in MemoryType:
            count = len([m for m in self.memories if m.memory_type == memory_type])
            stats["by_type"][memory_type.value] = count
        
        return stats
    
    def format_memories_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """
        将记忆格式化为提示词文本
        
        Args:
            memories: 搜索结果列表
            
        Returns:
            格式化的记忆文本
        """
        if not memories:
            return "（无相关历史记忆）"
        
        lines = ["\n=== 相关历史记忆 ==="]
        
        for i, item in enumerate(memories, 1):
            memory = item["memory"]
            score = item["score"]
            
            lines.append(f"\n记忆 {i} (相关度: {score:.2f}):")
            lines.append(f"  类型: {memory['memory_type']}")
            lines.append(f"  内容: {memory['content']}")
            
            if memory.get("metadata"):
                lines.append(f"  元数据: {json.dumps(memory['metadata'], ensure_ascii=False)}")
        
        lines.append("\n===================\n")
        
        return "\n".join(lines)
