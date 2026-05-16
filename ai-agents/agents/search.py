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
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paper_store import get_paper_store


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

    def _extract_arxiv_keywords(self, query: str) -> str:
        """
        将用户查询转换为适合 arXiv 搜索的英文关键词
        
        Args:
            query: 用户原始查询（可能是中文或冗长描述）
            
        Returns:
            简洁的英文关键词
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""你是一个 arXiv 搜索专家。你的任务是将用户的搜索查询转换为简洁的英文关键词，用于在 arXiv 上搜索学术论文。

规则：
1. 仅输出英文关键词，不要有其他解释性文字
2. 使用学术领域常用的术语
3. 关键词用空格分隔
4. 不要添加标点符号
5. 3-5个关键词最佳，不要超过10个
6. 如果查询是中文，先翻译成英文再提取关键词

示例：
输入: "研究大模型机器遗忘的最新方法"
输出: large language model machine forgetting unlearning

输入: "transformer 改进相关论文"
输出: transformer improvement attention mechanism
"""),
            HumanMessage(content=f"请将以下查询转换为 arXiv 搜索关键词：\n{query}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        # 清理结果：去除多余空格和换行
        keywords = response.content.strip()
        keywords = ' '.join(keywords.split())
        
        return keywords

    def search(self, query: str) -> Dict[str, Any]:
        """
        执行搜索（带重试机制）
        
        Args:
            query: 搜索查询
            
        Returns:
            搜索结果
        """
        print(f"原始查询：{query}")
        
        # 先用 LLM 将查询转换为简洁的英文关键词
        arxiv_query = self._extract_arxiv_keywords(query)
        print(f"ArXiv 搜索关键词：{arxiv_query}")
        
        # 先尝试从本地向量数据库搜索
        try:
            paper_store = get_paper_store()
            cached_papers = paper_store.search_papers(arxiv_query, n_results=3)
            
            if cached_papers and len(cached_papers) >= 2:
                print(f"从本地向量库找到 {len(cached_papers)} 篇相关论文，直接使用缓存")
                papers = self._convert_cached_papers(cached_papers)
                
                # 使用 LLM 总结搜索结果
                summary = self._summarize_results(query, papers)
                
                result = {
                    "query": query,
                    "papers": papers,
                    "summary": summary,
                    "count": len(papers),
                    "from_cache": True
                }
                
                # 添加文件信息
                result["files"] = [{
                    "name": "search_results.md",
                    "path": "search/search_results.md",
                    "content": self._format_search_results(papers, summary),
                    "language": "markdown",
                    "description": "搜索结果汇总"
                }]
                
                return result
            else:
                print("本地缓存不足，调用 arXiv API 搜索")
        except Exception as e:
            print(f"搜索本地向量库失败: {e}，将调用 arXiv API")
        
        # 调用 arXiv API 搜索
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
                    query=arxiv_query,
                    max_results=3,
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
                
                # 将论文保存到向量数据库
                try:
                    paper_store = get_paper_store()
                    paper_store.add_papers(papers, query)
                except Exception as e:
                    print(f"保存论文到向量数据库失败: {e}")
                
                result = {
                    "query": query,
                    "papers": papers,
                    "summary": summary,
                    "count": len(papers),
                    "from_cache": False
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
        for i, paper in enumerate(papers, 1):
            papers_info += f"{i}. {paper['title']}\n"
            papers_info += f"   作者：{', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}\n"
            papers_info += f"   时间：{paper['published']}\n"
            papers_info += f"   摘要：{paper['summary']}\n\n"
        
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
    
    def _convert_cached_papers(self, cached_papers: List[Dict]) -> List[Dict]:
        """
        将缓存的论文转换为标准格式
        
        Args:
            cached_papers: 从向量库检索的论文
            
        Returns:
            标准格式的论文列表
        """
        papers = []
        for cached in cached_papers:
            paper = {
                "title": cached.get("title", ""),
                "authors": cached.get("authors", "").split(", ") if cached.get("authors") else [],
                "summary": cached.get("document", "").replace("标题: ", "").replace("\n摘要: ", "\n") if cached.get("document") else "",
                "published": cached.get("published", ""),
                "link": cached.get("link", ""),
                "pdf_link": cached.get("pdf_link", ""),
                "distance": cached.get("distance")
            }
            papers.append(paper)
        return papers
    
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
            result += f"**摘要**: {paper['summary']}\n\n"
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
