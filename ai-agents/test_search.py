"""
测试 Search Agent 的关键词提取和搜索功能
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from agents.search import SearchAgent

def test_keyword_extraction():
    """测试关键词提取"""
    print("=" * 60)
    print("测试关键词提取")
    print("=" * 60)
    
    agent = SearchAgent()
    
    test_queries = [
        "研究大模型机器遗忘的最新方法",
        "transformer 改进相关论文",
        "研究深度学习在计算机视觉中的应用",
        "查找关于强化学习的最新研究"
    ]
    
    for query in test_queries:
        print(f"\n原始查询: {query}")
        keywords = agent._extract_arxiv_keywords(query)
        print(f"提取的关键词: {keywords}")

def test_search():
    """测试实际搜索"""
    print("\n" + "=" * 60)
    print("测试实际搜索")
    print("=" * 60)
    
    agent = SearchAgent()
    
    query = "研究大模型机器遗忘的最新方法"
    result = agent.search(query)
    
    print(f"\n搜索结果:")
    print(f"  - 找到 {result['count']} 篇论文")
    print(f"  - 总结: {result['summary'][:100]}...")
    
    if result['papers']:
        print(f"\n前 3 篇论文:")
        for i, paper in enumerate(result['papers'][:3], 1):
            print(f"\n  {i}. {paper['title']}")
            print(f"     作者: {', '.join(paper['authors'][:2])}...")
            print(f"     时间: {paper['published']}")

if __name__ == "__main__":
    test_keyword_extraction()
    test_search()
