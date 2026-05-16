"""
RAG Agent - 检索增强生成智能体
负责解析论文内容、提取关键方法和技术细节
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
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
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE_RAG", "0.5"))
        )
        
        # 初始化文本分块器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      # 每个 chunk 约 1000 tokens
            chunk_overlap=200,    # 重叠 200 tokens，避免信息丢失
            separators=["\n\n", "\n", "。", ".", " "]
        )
        
        # 系统提示词
        self.system_prompt = """你是一个专业的学术论文解析专家。你的职责是：

1. 下载并解析学术论文 PDF
2. 提取论文的核心方法、算法和技术细节
3. 总结论文的主要贡献和创新点
4. 提取关键公式、图表和实验结果
5. 用清晰的结构化方式呈现解析结果

请提供详细、准确的技术分析。"""

    def analyze(self, query: str, search_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析论文
        
        Args:
            query: 论文查询或任务描述
            search_results: Search Agent 返回的搜索结果（包含论文列表）
            
        Returns:
            分析结果
        """
        print(f"开始解析论文：{query}")
        
        try:
            # 如果有搜索结果，使用搜索结果中的论文信息
            if search_results and search_results.get("papers"):
                papers = search_results["papers"]
                print(f"使用搜索结果中的 {len(papers)} 篇论文进行分析")
                analysis = self._analyze_papers_from_search(papers, query)
                
                # 添加文件信息
                analysis["files"] = [{
                    "name": "paper_analysis.md",
                    "path": "analysis/paper_analysis.md",
                    "content": analysis.get("content", ""),
                    "language": "markdown",
                    "description": "论文解析报告"
                }]
                
                return analysis
            
            # 如果查询是 URL，下载并解析 PDF
            if query.startswith("http"):
                # 保存 PDF 到本地
                pdf_filename = query.split("/")[-1] if "/" in query else "paper.pdf"
                pdf_path = f"data/papers/{pdf_filename}"
                
                pdf_content = self._download_pdf(query, save_path=pdf_path)
                if pdf_content:
                    # 提取文本
                    text = self._extract_text_from_pdf(pdf_content)
                    
                    # 分块
                    metadata = {"source_url": query, "paper_type": "pdf"}
                    chunks = self._chunk_text(text, metadata)
                    
                    # 生成向量嵌入
                    chunks = self._embed_chunks(chunks)
                    
                    # 存储到向量数据库
                    self._store_chunks_to_chroma(chunks, metadata)
                    
                    # 分析论文
                    analysis = self._analyze_paper_text(text)
                    
                    analysis["files"] = [{
                        "name": "paper_analysis.md",
                        "path": "analysis/paper_analysis.md",
                        "content": analysis.get("content", ""),
                        "language": "markdown",
                        "description": "论文解析报告"
                    }]
                    
                    return analysis
            
            # 否则，使用 LLM 生成分析
            result = self._mock_analysis(query)
            
            # 添加文件信息
            result["files"] = [{
                "name": "paper_analysis.md",
                "path": "analysis/paper_analysis.md",
                "content": result.get("content", ""),
                "language": "markdown",
                "description": "论文解析报告"
            }]
            
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
    
    def _download_pdf(self, url: str, save_path: str = None) -> bytes:
        """
        下载 PDF 文件
        
        Args:
            url: PDF 链接
            save_path: 保存路径（可选）
            
        Returns:
            PDF 二进制内容
        """
        try:
            print(f"正在下载 PDF: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # 保存到本地（如果指定了路径）
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"PDF 已保存到: {save_path}")
            
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
            
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {i+1} ---\n{page_text}"
            
            print(f"成功提取 {len(pdf_reader.pages)} 页文本，共 {len(text)} 字符")
            return text
        except Exception as e:
            print(f"提取 PDF 文本失败：{e}")
            return ""
    
    def _chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        将文本分块
        
        Args:
            text: 完整文本
            metadata: 元数据（论文信息）
            
        Returns:
            分块列表，每个块包含内容和元数据
        """
        # 使用分块器切分文本
        chunks = self.text_splitter.split_text(text)
        
        print(f"文本分块完成，共 {len(chunks)} 个块")
        
        # 为每个块添加元数据
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_length": len(chunk),
            }
            if metadata:
                chunk_metadata.update(metadata)
            
            chunked_docs.append({
                "content": chunk,
                "metadata": chunk_metadata
            })
        
        return chunked_docs
    
    def _embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        将文本块转换为向量嵌入
        
        Args:
            chunks: 分块列表
            
        Returns:
            包含向量嵌入的分块列表
        """
        try:
            # 使用 ChromaDB 的嵌入函数
            from paper_store import get_paper_store
            paper_store = get_paper_store()
            
            # 提取所有文本内容
            texts = [chunk["content"] for chunk in chunks]
            
            # 批量生成嵌入向量
            embeddings = paper_store.embedding_function(texts)
            
            # 将向量添加到分块中
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i]
            
            print(f"成功生成 {len(embeddings)} 个向量嵌入")
            return chunks
            
        except Exception as e:
            print(f"生成向量嵌入失败：{e}")
            # 返回没有嵌入向量的分块
            return chunks
    
    def _store_chunks_to_chroma(self, chunks: List[Dict], metadata: Dict):
        """
        将分块存储到 ChromaDB 向量数据库
        
        Args:
            chunks: 分块列表
            metadata: 元数据
        """
        try:
            from paper_store import get_paper_store
            paper_store = get_paper_store()
            
            # 准备存储数据
            texts = [chunk["content"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            ids = [f"chunk_{metadata.get('source_url', 'unknown')}_{i}" for i in range(len(chunks))]
            
            # 存储到 ChromaDB
            paper_store.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"成功将 {len(chunks)} 个分块存储到向量数据库")
            
        except Exception as e:
            print(f"存储到向量数据库失败：{e}")
    
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
    
    def _analyze_papers_from_search(self, papers: List[Dict], query: str) -> Dict[str, Any]:
        """
        基于搜索结果中的论文信息进行分析
        
        Args:
            papers: 论文列表（包含标题、作者、摘要等）
            query: 原始查询
            
        Returns:
            分析结果
        """
        # 构建论文信息文本
        papers_info = ""
        for i, paper in enumerate(papers, 1):
            papers_info += f"论文 {i}:\n"
            papers_info += f"标题: {paper.get('title', '')}\n"
            papers_info += f"作者: {', '.join(paper.get('authors', []))}\n"
            papers_info += f"发表时间: {paper.get('published', '')}\n"
            papers_info += f"摘要: {paper.get('summary', '')}\n"
            papers_info += f"链接: {paper.get('link', '')}\n\n"
        
        # 调用 LLM 分析
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
请基于以下搜索到的论文信息，为用户查询'{query}'提供一个详细的论文解析报告：

{papers_info}

请提供：
1. 最相关的论文推荐（1-2篇）及推荐理由
2. 主要研究方向总结
3. 各论文的核心方法和技术要点
4. 论文列表详细信息
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return {
            "content": response.content,
            "source": "search_results_analysis",
            "papers_count": len(papers)
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
