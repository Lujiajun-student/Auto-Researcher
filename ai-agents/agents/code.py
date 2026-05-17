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
import json
import re
import ast


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
        files = []
        directory_structure = ""
        code = ""
        
        print(f"[Code Agent] 尝试从响应中提取文件...")
        print(f"响应长度：{len(text)}")
        
        # 首先尝试直接解析 JSON（不要求在代码块内）
        try:
            # 尝试找到文本中的 JSON 对象
            # 寻找第一个 { 和对应的 }
            start_idx = text.find('{')
            if start_idx >= 0:
                # 找到匹配的结束 }
                brace_count = 0
                end_idx = -1
                for i, char in enumerate(text[start_idx:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = start_idx + i + 1
                            break
                
                if end_idx > start_idx:
                    json_text = text[start_idx:end_idx]
                    
                    # 尝试修复 JSON 中的换行符问题
                    # 在解析之前先替换可能的未转义换行符
                    try:
                        data = json.loads(json_text)
                    except json.JSONDecodeError as e:
                        print(f"标准解析失败，尝试修复 JSON: {e}")
                        try:
                            # 尝试将其作为 Python 字典字面量解析
                            data = ast.literal_eval(json_text)
                        except:
                            # 更智能地修复 JSON 中的换行符
                            # 我们需要找出所有的字符串字面量并替换其中的换行符
                            fixed_json = self._fix_json_newlines(json_text)
                            data = json.loads(fixed_json)
                    
                    if "files" in data:
                        files = data["files"]
                        print(f"从文本中直接提取到 {len(files)} 个文件")
                    if "directory_structure" in data:
                        directory_structure = data["directory_structure"]
                    if "main_code" in data:
                        code = data["main_code"]
                    elif "code" in data:
                        code = data["code"]
        except Exception as e:
            print(f"直接解析 JSON 失败：{e}")
        
        # 如果没有提取到文件，尝试从代码块中解析 JSON
        if not files:
            json_pattern = r"```(?:json)?\n(\{[\s\S]*?\})\n```"
            json_matches = re.findall(json_pattern, text, re.DOTALL)
            
            print(f"JSON 匹配结果：{len(json_matches)} 个")
            
            if json_matches:
                try:
                    data = json.loads(json_matches[0])
                    if "files" in data:
                        files = data["files"]
                        print(f"从 JSON 代码块中提取到 {len(files)} 个文件")
                    if "directory_structure" in data:
                        directory_structure = data["directory_structure"]
                    if "main_code" in data:
                        code = data["main_code"]
                    elif "code" in data:
                        code = data["code"]
                except Exception as e:
                    print(f"解析 JSON 代码块失败：{e}")
                    pass
        
        # 如果没有提取到文件，尝试提取代码块
        if not files:
            print("未从 JSON 中提取到文件，尝试提取代码块...")
            code_pattern = r"```(?:python)?\n(.*?)```"
            code_matches = re.findall(code_pattern, text, re.DOTALL)
            print(f"代码块匹配结果：{len(code_matches)} 个")
            
            if code_matches:
                # 找到所有代码块，分别保存
                for i, code_block in enumerate(code_matches):
                    if i == 0:
                        code = code_block.strip()
                    
                    # 尝试从代码块前的文本提取文件名
                    file_name = f"main_{i+1}.py" if i > 0 else "main.py"
                    file_desc = f"代码文件 {i+1}"
                    
                    files.append({
                        "name": file_name,
                        "path": file_name,
                        "content": code_block.strip(),
                        "language": "python",
                        "description": file_desc
                    })
                
                print(f"从代码块创建了 {len(files)} 个文件")
        
        # 如果仍然没有文件，尝试清理响应并创建合理的文件
        if not files:
            print("未提取到代码块，尝试清理响应...")
            
            # 尝试从响应中提取合理的代码
            # 移除 JSON 标记和多余的文本
            cleaned_text = self._clean_response(text)
            
            if cleaned_text and len(cleaned_text) > 0:
                code = cleaned_text
                files = [{
                    "name": "main.py",
                    "path": "main.py",
                    "content": code,
                    "language": "python",
                    "description": "生成的代码"
                }]
                print(f"创建了清理后的代码文件")
            else:
                # 如果无法清理，保存完整响应但重命名文件为说明文件
                files = [{
                    "name": "response.md",
                    "path": "response.md",
                    "content": "# AI 响应\n\n" + text,
                    "language": "markdown",
                    "description": "AI 的完整响应"
                }]
                print(f"创建了响应说明文件")
        
        # 如果没有目录结构，创建一个简单的
        if not directory_structure and files:
            directory_structure = "\n".join([f["path"] for f in files])
        
        print(f"最终提取结果：{len(files)} 个文件")
        return code, files, directory_structure
    
    def _fix_json_newlines(self, json_str: str) -> str:
        """
        修复 JSON 字符串中未转义的换行符
        
        Args:
            json_str: 原始 JSON 字符串
            
        Returns:
            修复后的 JSON 字符串
        """
        result = []
        in_string = False
        escape_next = False
        
        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
            elif char == '\\':
                result.append(char)
                escape_next = True
            elif char == '"':
                result.append(char)
                in_string = not in_string
            elif char == '\n' and in_string:
                # 在字符串中的换行符替换为 \n
                result.append('\\n')
            elif char == '\r' and in_string:
                # 在字符串中的回车符替换为 \r
                result.append('\\r')
            elif char == '\t' and in_string:
                # 在字符串中的制表符替换为 \t
                result.append('\\t')
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _clean_response(self, text: str) -> str:
        """
        清理响应文本，移除 JSON 标记等非代码内容
        
        Args:
            text: 原始响应文本
            
        Returns:
            清理后的代码
        """
        # 1. 移除 JSON 标记
        cleaned = re.sub(r'^```json\n', '', text)
        cleaned = re.sub(r'\n```$', '', cleaned)
        
        # 2. 尝试从 JSON 中提取 content/code/files 字段
        try:
            data = json.loads(cleaned)
            if "content" in data:
                return data["content"]
            if "code" in data:
                return data["code"]
            if "files" in data and isinstance(data["files"], list) and len(data["files"]) > 0:
                if "content" in data["files"][0]:
                    return data["files"][0]["content"]
        except:
            pass
        
        # 3. 如果还是 JSON，尝试提取 main_code 或 files[0].content
        # 简单的字符串匹配
        patterns = [
            r'"main_code"\s*:\s*"([^"]*(?:\\"[^"]*)*)"',
            r'"code"\s*:\s*"([^"]*(?:\\"[^"]*)*)"',
            r'"content"\s*:\s*"([^"]*(?:\\"[^"]*)*)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                content = match.group(1)
                # 恢复转义字符
                content = content.replace('\\"', '"')
                content = content.replace('\\n', '\n')
                content = content.replace('\\t', '\t')
                return content
        
        # 4. 如果都失败，尝试移除 JSON 结构，保留看起来像代码的部分
        # 查找第一个可能是 Python 代码的部分
        lines = text.split('\n')
        code_lines = []
        
        for line in lines:
            # 跳过明显的 JSON 标记行
            stripped = line.strip()
            if stripped.startswith('{') or stripped.startswith('}') or stripped.startswith('"files"') or stripped.startswith('"main_code"'):
                continue
            
            # 如果看起来像代码（有缩进、关键字等）
            code_lines.append(line)
        
        result = '\n'.join(code_lines).strip()
        
        # 如果结果太短，尝试另一种方法
        if len(result) < 50:
            # 直接查找第一个代码块
            code_pattern = r"```(?:python)?\n(.*?)```"
            match = re.search(code_pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return result
    
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
