"""
Search Agent - 搜索智能体
负责搜索学术文献、查找相关资料
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import os
import arxiv
import json
import time
import random


class SearchAgent:
    """Search Agent 类"""
    
    def __init__(self):
        """初始化 Search Agent"""
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE_SEARCH", "0.3"))
        )
        
        # 系统提示词
        self.system_prompt = """你是一个学术研究搜索专家。你的职责是：

1. 理解用户的搜索需求
2. 从 arXiv 等学术数据库中搜索相关论文
3. 提取论文的关键信息（标题、作者、摘要、链接）
4. 整理搜索结果，返回最相关的文献列表

请返回结构化的搜索结果。"""

    def search(self, query: str) -> Dict[str, Any]:
        """
        执行搜索（带重试机制）
        
        Args:
            query: 搜索查询
            
        Returns:
            搜索结果
        """
        print(f"搜索查询：{query}")
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                # 添加随机延迟避免并发请求
                if attempt > 0:
                    delay = retry_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
                    print(f"第 {attempt + 1} 次重试，延迟 {delay:.2f} 秒...")
                    time.sleep(delay)
                
                # 使用 arxiv API 搜索
                search = arxiv.Search(
                    query=query,
                    max_results=10,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                papers = []
                for result in search.results():
                    papers.append({
                        "title": result.title,
                        "authors": [str(author) for author in result.authors],
                        "summary": result.summary,
                        "published": result.published.strftime("%Y-%m-%d"),
                        "link": result.entry_id,
                        "pdf_link": result.pdf_url
                    })
                
                # 使用 LLM 总结搜索结果
                summary = self._summarize_results(query, papers)
                
                result = {
                    "query": query,
                    "papers": papers,
                    "summary": summary,
                    "count": len(papers)
                }
                
                # 添加文件信息
                result["files"] = [{
                    "name": "search_results.md",
                    "path": "search/search_results.md",
                    "content": self._format_search_results(papers, summary),
                    "language": "markdown",
                    "description": "搜索结果汇总"
                }]
                
                if attempt > 0:
                    print(f"第 {attempt + 1} 次重试成功！")
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                print(f"第 {attempt + 1} 次搜索失败：{error_msg}")
                
                # 如果是 429 错误，继续重试
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return {
                            "query": query,
                            "papers": [],
                            "summary": f"搜索失败：arXiv API 请求过于频繁，请稍后再试（{error_msg}）",
                            "count": 0,
                            "files": []
                        }
                else:
                    # 其他错误直接返回
                    return {
                        "query": query,
                        "papers": [],
                        "summary": f"搜索失败：{error_msg}",
                        "count": 0,
                        "files": []
                    }
        
        # 所有重试都失败
        return {
            "query": query,
            "papers": [],
            "summary": "搜索失败：多次重试后仍然无法访问 arXiv API",
            "count": 0,
            "files": []
        }
    
    def _summarize_results(self, query: str, papers: List[Dict]) -> str:
        """
        使用 LLM 总结搜索结果
        
        Args:
            query: 搜索查询
            papers: 论文列表
            
        Returns:
            总结文本
        """
        if not papers:
            return "未找到相关论文"
        
        # 构建论文信息
        papers_info = ""
        for i, paper in enumerate(papers[:5], 1):  # 只取前 5 篇
            papers_info += f"{i}. {paper['title']}\n"
            papers_info += f"   作者：{', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}\n"
            papers_info += f"   时间：{paper['published']}\n"
            papers_info += f"   摘要：{paper['summary'][:200]}...\n\n"
        
        # 调用 LLM 总结
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
请根据以下搜索结果，为用户查询'{query}'提供一个简洁的总结：

{papers_info}

请总结：
1. 找到了多少篇相关论文
2. 最相关的几篇论文是什么
3. 这些论文的主要研究方向
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return response.content
    
    def _format_search_results(self, papers: List[Dict], summary: str) -> str:
        """
        格式化搜索结果
        
        Args:
            papers: 论文列表
            summary: 总结
            
        Returns:
            格式化的搜索结果文本
        """
        result = "# 搜索结果汇总\n\n"
        result += f"## 搜索查询\n\n{papers[0].get('title', '') if papers else ''}\n\n"
        result += f"## 总结\n\n{summary}\n\n"
        result += "## 论文列表\n\n"
        
        for i, paper in enumerate(papers, 1):
            result += f"### {i}. {paper['title']}\n\n"
            result += f"**作者**: {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}\n\n"
            result += f"**发表时间**: {paper['published']}\n\n"
            result += f"**摘要**: {paper['summary'][:300]}...\n\n"
            result += f"[🔗 查看论文]({paper['link']})\n\n"
            result += f"[📄 PDF 下载]({paper['pdf_link']})\n\n"
            result += "---\n\n"
        
        return result
    
    def search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        直接在 arXiv 上搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            论文列表
        """
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for result in search.results():
            results.append({
                "title": result.title,
                "authors": [str(author) for author in result.authors],
                "summary": result.summary,
                "published": result.published.strftime("%Y-%m-%d"),
                "link": result.entry_id,
                "pdf_link": result.pdf_url,
                "categories": result.categories
            })
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "type": "search",
            "status": "ready",
            "llm_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            "search_engine": "arxiv"
        }
