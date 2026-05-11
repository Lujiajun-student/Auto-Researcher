"""
Code Agent - 代码智能体
负责根据论文方法编写实现代码和示例
"""

from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
import os
import subprocess
import tempfile
import docker


class CodeAgent:
    """Code Agent 类"""
    
    def __init__(self):
        """初始化 Code Agent"""
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE_CODE", "0.7"))
        )
        
        # 系统提示词
        self.system_prompt = """你是一个专业的编程专家和代码实现工程师。你的职责是：

1. 根据论文描述的方法实现代码
2. 提供完整的、可运行的示例代码
3. 包含详细的注释和文档字符串
4. 提供使用示例和测试代码
5. 确保代码符合最佳实践
6. 考虑边界情况和错误处理

请提供高质量、生产级别的代码实现。"""

    def generate_code(self, description: str) -> Dict[str, Any]:
        """
        生成代码
        
        Args:
            description: 代码需求描述
            
        Returns:
            生成的代码
        """
        print(f"开始生成代码：{description}")
        
        try:
            # 调用 LLM 生成代码
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
请根据以下描述实现完整的代码：

{description}

请提供：
1. 完整的代码实现（可以包含多个文件）
2. 详细的注释
3. 使用示例
4. 必要的依赖说明
5. 测试代码

请使用 Python 语言，并确保代码可以运行。

请按照以下 JSON 格式返回：
{{
  "files": [
    {{
      "name": "文件名.py",
      "path": "目录/文件名.py",
      "content": "完整的代码内容",
      "language": "python",
      "description": "文件描述"
    }}
  ],
  "main_code": "主要代码内容（如果有多个文件，这里是主文件）",
  "directory_structure": "目录结构文本描述",
  "explanation": "代码说明"
}}

如果没有多个文件，至少返回一个文件在 files 数组中。
""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({})
            
            # 提取代码和文件信息
            code, files, dir_structure = self._extract_code_and_files(response.content)
            
            return {
                "description": description,
                "code": code,
                "files": files,  # 新增：文件列表
                "directory_structure": dir_structure,  # 新增：目录结构
                "full_response": response.content,
                "language": "python"
            }
            
        except Exception as e:
            print(f"代码生成失败：{e}")
            return {
                "description": description,
                "error": str(e),
                "code": None,
                "files": []
            }
    
    def _extract_code(self, text: str) -> str:
        """
        从响应中提取代码
        
        Args:
            text: LLM 响应文本
            
        Returns:
            提取的代码
        """
        # 查找代码块
        import re
        
        # 匹配 ```python ... ``` 或 ``` ... ```
        pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            # 返回第一个代码块
            return matches[0].strip()
        else:
            # 如果没有代码块，返回原文
            return text
    
    def _extract_code_and_files(self, text: str) -> tuple:
        """
        从响应中提取代码和文件信息
        
        Args:
            text: LLM 响应文本
            
        Returns:
            (code, files, directory_structure) 元组
        """
        import re
        import json
        
        files = []
        directory_structure = ""
        code = ""
        
        print(f"[Code Agent] 尝试从响应中提取文件...")
        print(f"响应长度：{len(text)}")
        
        # 尝试提取 JSON 格式的文件列表
        json_pattern = r"```(?:json)?\n(\{[\s\S]*?\})\n```"
        json_matches = re.findall(json_pattern, text, re.DOTALL)
        
        print(f"JSON 匹配结果：{len(json_matches)} 个")
        
        if json_matches:
            try:
                data = json.loads(json_matches[0])
                if "files" in data:
                    files = data["files"]
                    print(f"从 JSON 中提取到 {len(files)} 个文件")
                if "directory_structure" in data:
                    directory_structure = data["directory_structure"]
                if "main_code" in data:
                    code = data["main_code"]
            except Exception as e:
                print(f"解析 JSON 失败：{e}")
                pass
        
        # 如果没有提取到文件，尝试提取代码块
        if not files:
            print("未从 JSON 中提取到文件，尝试提取代码块...")
            code_pattern = r"```(?:python)?\n(.*?)```"
            code_matches = re.findall(code_pattern, text, re.DOTALL)
            print(f"代码块匹配结果：{len(code_matches)} 个")
            
            if code_matches:
                code = code_matches[0].strip()
                # 创建一个默认文件
                files = [{
                    "name": "main.py",
                    "path": "main.py",
                    "content": code,
                    "language": "python",
                    "description": "主要代码文件"
                }]
                print(f"从代码块创建了 1 个默认文件")
        
        # 如果仍然没有文件，使用整个响应作为代码
        if not files:
            print("未提取到代码块，使用整个响应作为代码...")
            code = text.strip()
            files = [{
                "name": "code.txt",
                "path": "code.txt",
                "content": text,
                "language": "text",
                "description": "生成的代码"
            }]
            print(f"创建了 1 个文本文件")
        
        # 如果没有目录结构，创建一个简单的
        if not directory_structure and files:
            directory_structure = "\n".join([f["path"] for f in files])
        
        print(f"最终提取结果：{len(files)} 个文件")
        return code, files, directory_structure
    
    def run_code_in_sandbox(self, code: str, test_input: str = None) -> Dict[str, Any]:
        """
        在 Docker 沙箱中运行代码
        
        Args:
            code: 要运行的代码
            test_input: 测试输入
            
        Returns:
            运行结果
        """
        print("在 Docker 沙箱中运行代码...")
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            # 启动 Docker 容器
            client = docker.from_env()
            
            # 运行容器
            result = client.containers.run(
                "python:3.10-slim",
                command=f"python /code/{os.path.basename(code_file)}",
                volumes={code_file: {'bind': f"/code/{os.path.basename(code_file)}", 'mode': 'ro'}},
                remove=True,
                timeout=30,
                mem_limit="512m",
                network_disabled=True  # 禁用网络，增强安全性
            )
            
            return {
                "success": True,
                "output": result.decode('utf-8'),
                "exit_code": 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None
            }
    
    def explain_code(self, code: str) -> Dict[str, Any]:
        """
        解释代码
        
        Args:
            code: 代码
            
        Returns:
            代码解释
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是一个代码解释专家。请用清晰的语言解释代码的功能和实现细节。"),
            HumanMessage(content=f"""
请详细解释以下代码：

```python
{code}
```

请包括：
1. 代码的整体功能
2. 关键函数和类的作用
3. 实现逻辑和算法
4. 时间和空间复杂度
5. 使用示例
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return {
            "code": code,
            "explanation": response.content
        }
    
    def debug_code(self, code: str, error_message: str) -> Dict[str, Any]:
        """
        调试代码
        
        Args:
            code: 有问题的代码
            error_message: 错误信息
            
        Returns:
            修复建议
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="你是一个调试专家。请分析代码错误并提供修复方案。"),
            HumanMessage(content=f"""
以下代码运行时出现错误：

```python
{code}
```

错误信息：
{error_message}

请：
1. 分析错误原因
2. 提供修复方案
3. 给出修复后的完整代码
""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        return {
            "code": code,
            "error": error_message,
            "analysis": response.content
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "type": "code",
            "status": "ready",
            "llm_model": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            "capabilities": ["code_generation", "code_explanation", "debugging", "sandbox_execution"]
        }


# 使用示例
if __name__ == "__main__":
    agent = CodeAgent()
    
    # 生成代码示例
    description = "实现一个快速排序算法，包含详细的注释和测试代码"
    result = agent.generate_code(description)
    
    print("\n生成的代码：")
    print(result["code"])
    
    # 解释代码
    explanation = agent.explain_code(result["code"])
    print("\n代码解释：")
    print(explanation["explanation"])
