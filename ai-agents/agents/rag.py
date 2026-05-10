"""
RAG Agent - 检索增强生成智能体
负责解析论文内容、提取关键方法和技术细节
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import os
import requests
import PyPDF2
from io import BytesIO


class RAGAgent:
    """RAG Agent 类"""
    
    def __init__(self):
        """初始化 RAG Agent"""
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0.5
        )
        
        # 系统提示词
        self.system_prompt = """你是一个专业的学术论文解析专家。你的职责是：

1. 下载并解析学术论文 PDF
2. 提取论文的核心方法、算法和技术细节
3. 总结论文的主要贡献和创新点
4. 提取关键公式、图表和实验结果
5. 用清晰的结构化方式呈现解析结果

请提供详细、准确的技术分析。"""

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        分析论文
        
        Args:
            query: 论文查询或 PDF 链接
            
        Returns:
            分析结果
        """
        print(f"开始解析论文：{query}")
        
        try:
            # 如果查询是 URL，下载并解析 PDF
            if query.startswith("http"):
                pdf_content = self._download_pdf(query)
                if pdf_content:
                    text = self._extract_text_from_pdf(pdf_content)
                    analysis = self._analyze_paper_text(text)
                    return analysis
            
            # 否则，先搜索论文再解析
            # 这里简化处理，直接返回模拟结果
            result = self._mock_analysis(query)
            
            # 添加文件信息
            result["files"] = [{
                "name": "paper_analysis.md",
                "path": "analysis/paper_analysis.md",
                "content": result.get("content", ""),
                "language": "markdown",
                "description": "论文解析报告"
            }]
            
            if "analysis" in result:
                result["files"].append({
                    "name": "detailed_analysis.md",
                    "path": "analysis/detailed_analysis.md",
                    "content": result["analysis"],
                    "language": "markdown",
                    "description": "详细技术分析"
                })
            
            return result
            
        except Exception as e:
            print(f"解析失败：{e}")
            return {
                "query": query,
                "error": str(e),
                "summary": "解析失败",
                "methods": [],
                "contributions": [],
                "files": []
            }
    
    def _download_pdf(self, url: str) -> bytes:
        """
        下载 PDF 文件
        
        Args:
            url: PDF 链接
            
        Returns:
            PDF 二进制内容
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"下载 PDF 失败：{e}")
            return None
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        从 PDF 提取文本
        
        Args:
            pdf_content: PDF 二进制内容
            
        Returns:
            提取的文本
        """
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"提取 PDF 文本失败：{e}")
            return ""
    
    def _analyze_paper_text(self, text: str) -> Dict[str, Any]:
        """
        分析论文文本
        
        Args:
            text: 论文文本
            
        Returns:
            分析结果
        """
        # 调用 LLM 分析
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
请分析以下论文内容：

{text[:5000]}...  # 只取前 5000 字符

请提供：
1. 论文标题和作者
2. 研究问题和动机
3. 核心方法和算法
4. 主要贡献和创新点
5. 实验结果和性能
6. 关键公式和技术细节
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return {
            "content": response.content,
            "source": "pdf_analysis"
        }
    
    def _mock_analysis(self, query: str) -> Dict[str, Any]:
        """
        模拟分析结果（用于演示）
        
        Args:
            query: 查询
            
        Returns:
            分析结果
        """
        # 使用 LLM 生成模拟分析
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
请为以下研究主题生成一个详细的论文解析报告：

{query}

请包括：
1. 研究背景和问题
2. 核心方法和算法
3. 技术细节和实现要点
4. 主要贡献
5. 实验结果
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return {
            "query": query,
            "content": response.content,
            "source": "llm_generated"
        }
    
    def extract_method(self, paper_text: str) -> Dict[str, Any]:
        """
        提取论文方法
        
        Args:
            paper_text: 论文文本
            
        Returns:
            方法描述
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是一个算法提取专家。请从论文中提取核心算法和方法。"),
            HumanMessage(content=f"""
请从以下论文内容中提取核心算法和方法：

{paper_text[:3000]}

请提供：
1. 算法名称
2. 算法步骤
3. 关键公式
4. 伪代码
5. 时间复杂度分析
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return {
            "method": response.content
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "type": "rag",
            "status": "ready",
            "llm_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            "capabilities": ["pdf_parsing", "method_extraction", "summarization"]
        }
