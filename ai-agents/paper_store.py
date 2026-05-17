"""
论文向量数据库模块
使用 ChromaDB 存储和检索论文
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class PaperVectorStore:
    """论文向量存储类"""
    
    def __init__(self, persist_directory: str = "./data/chroma_memory"):
        """
        初始化向量存储
        
        Args:
            persist_directory: 数据持久化目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        if not CHROMA_AVAILABLE:
            print("警告: chromadb 未安装，向量存储功能不可用")
            self.client = None
            self.collection = None
            return
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 使用 all-mpnet-base-v2 嵌入模型（更强的语义理解能力）
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-mpnet-base-v2"
        )
        
        # 获取或创建论文集合
        self.collection = self.client.get_or_create_collection(
            name="papers",
            embedding_function=embedding_fn,
            metadata={"description": "Academic papers from arXiv"}
        )
        
        print(f"论文向量存储已初始化: {persist_directory}")
    
    def add_papers(self, papers: List[Dict[str, Any]], query: str = "") -> int:
        """
        添加论文到向量存储
        
        Args:
            papers: 论文列表
            query: 搜索查询（用于记录来源）
            
        Returns:
            成功添加的论文数量
        """
        if not self.collection:
            print("向量存储未初始化，跳过保存")
            return 0
        
        if not papers:
            return 0
        
        ids = []
        documents = []
        metadatas = []
        
        for paper in papers:
            # 生成唯一 ID
            paper_id = paper.get('link', '').split('/')[-1] or f"paper_{datetime.now().timestamp()}"
            
            # 构建文档内容（标题 + 摘要，用于向量检索）
            document = f"标题: {paper['title']}\n摘要: {paper['summary']}"
            
            # 构建元数据
            metadata = {
                "title": paper['title'],
                "authors": ", ".join(paper.get('authors', [])),
                "published": paper.get('published', ''),
                "link": paper.get('link', ''),
                "pdf_link": paper.get('pdf_link', ''),
                "query": query,
                "added_at": datetime.now().isoformat()
            }
            
            ids.append(paper_id)
            documents.append(document)
            metadatas.append(metadata)
        
        try:
            # 添加到集合
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"成功添加 {len(papers)} 篇论文到向量存储")
            return len(papers)
        except Exception as e:
            print(f"添加论文到向量存储失败: {e}")
            return 0
    
    def search_papers(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关论文
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            
        Returns:
            相关论文列表
        """
        if not self.collection:
            print("向量存储未初始化")
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            papers = []
            if results['metadatas'] and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    paper = {
                        **metadata,
                        "distance": results['distances'][0][i] if results.get('distances') else None,
                        "document": results['documents'][0][i] if results.get('documents') else None
                    }
                    papers.append(paper)
            
            print(f"从向量存储中找到 {len(papers)} 篇相关论文")
            return papers
            
        except Exception as e:
            print(f"搜索论文失败: {e}")
            return []
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """
        获取所有存储的论文
        
        Returns:
            所有论文列表
        """
        if not self.collection:
            return []
        
        try:
            count = self.collection.count()
            if count == 0:
                return []
            
            results = self.collection.get(
                limit=count
            )
            
            papers = []
            if results['metadatas']:
                for i, metadata in enumerate(results['metadatas']):
                    paper = {
                        **metadata,
                        "document": results['documents'][i] if results.get('documents') else None
                    }
                    papers.append(paper)
            
            return papers
        except Exception as e:
            print(f"获取论文列表失败: {e}")
            return []
    
    def clear(self):
        """清空所有论文"""
        if not self.collection:
            return
        
        try:
            ids = self.collection.get()['ids']
            if ids:
                self.collection.delete(ids=ids)
                print("已清空论文向量存储")
        except Exception as e:
            print(f"清空向量存储失败: {e}")


# 全局单例
_paper_store = None

def get_paper_store() -> PaperVectorStore:
    """获取论文向量存储单例"""
    global _paper_store
    if _paper_store is None:
        _paper_store = PaperVectorStore()
    return _paper_store
