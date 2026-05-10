package service

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// DeepSeekRequest DeepSeek API 请求体
type DeepSeekRequest struct {
	Model    string            `json:"model"`
	Messages []DeepSeekMessage `json:"messages"`
	Stream   bool              `json:"stream"`
}

// DeepSeekMessage DeepSeek 消息格式
type DeepSeekMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// DeepSeekResponse DeepSeek API 响应体
type DeepSeekResponse struct {
	Choices []struct {
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage"`
}

// AgentRequest AI Agent 系统请求体
type AgentRequest struct {
	Description string `json:"description"`
	TaskID      string `json:"task_id,omitempty"`
}

// AgentResponse AI Agent 系统响应体
type AgentResponse struct {
	TaskID  string                 `json:"task_id"`
	Status  string                 `json:"status"`
	Results map[string]interface{} `json:"results"`
	Error   string                 `json:"error"`
}

// ProcessMessage 处理消息（调用 DeepSeek AI 接口或 AI Agent 系统）
func ProcessMessage(userID uint, sessionID uint, content string) (string, error) {
	// 1. 保存用户消息
	userMessage := &models.Message{
		SessionID: sessionID,
		Role:      "user",
		Content:   content,
		CreatedAt: time.Now(),
	}
	if err := SendMessage(userMessage); err != nil {
		return "", err
	}

	// 2. 获取当前会话的所有历史消息
	historyMessages, err := GetSessionMessages(sessionID)
	if err != nil {
		return "", fmt.Errorf("获取历史消息失败：%v", err)
	}

	// 3. 判断是否需要调用 AI Agent 系统
	needsAgent, taskDescription := shouldUseAgent(content)

	var aiResponse string
	var results map[string]interface{}
	if needsAgent {
		// 调用 AI Agent 系统并获取原始结果
		fmt.Printf("检测到需要 Agent 协助的任务，开始调用 AI Agent 系统：%s\n", taskDescription)
		aiResponse, results, err = callAgentSystemWithResults(taskDescription)
		if err != nil {
			fmt.Printf("AI Agent 系统调用失败，降级为普通 AI 回复：%v\n", err)
			// Agent 调用失败，降级为普通 AI 回复
			aiResponse, err = callDeepSeekAPIWithHistory(historyMessages, content)
		} else {
			// 保存 Agent 生成的文件（同步保存，确保文件保存完成后再返回）
			if results != nil {
				fmt.Printf("开始同步保存 Agent 生成的文件到会话 %d\n", sessionID)
				if saveErr := SaveAgentFiles(sessionID, results); saveErr != nil {
					fmt.Printf("保存 Agent 文件失败：%v\n", saveErr)
				} else {
					fmt.Printf("Agent 文件保存完成\n")
				}
			}
		}
	} else {
		// 直接调用 DeepSeek AI 接口
		aiResponse, err = callDeepSeekAPIWithHistory(historyMessages, content)
	}

	if err != nil {
		return "", fmt.Errorf("AI 接口调用失败：%v", err)
	}

	// 4. 保存 AI 回复
	aiMessage := &models.Message{
		SessionID: sessionID,
		Role:      "assistant",
		Content:   aiResponse,
		CreatedAt: time.Now(),
	}
	if err := SendMessage(aiMessage); err != nil {
		return "", err
	}

	// 5. 如果是会话的第一条消息，自动总结生成标题
	if len(historyMessages) == 0 {
		go func() {
			title, err := generateSessionTitle(content, aiResponse)
			if err == nil && title != "" {
				err = UpdateSessionTitle(sessionID, title)
				if err != nil {
					fmt.Printf("更新会话标题失败：%v\n", err)
				}
			}
		}()
	}

	return aiResponse, nil
}

// shouldUseAgent 判断是否需要调用 AI Agent 系统
func shouldUseAgent(content string) (bool, string) {
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		return false, ""
	}

	prompt := `请判断以下用户请求是否需要调用多智能体系统（包括文献搜索、论文解析、代码生成等功能）。

用户请求：` + content + `

如果需要调用 Agent 系统，请返回 JSON 格式：
{"needs_agent": true, "task_description": "具体的任务描述"}

如果不需要，请返回：
{"needs_agent": false}

只需要返回 JSON，不需要其他内容。`

	requestBody := DeepSeekRequest{
		Model: "deepseek-v4-flash",
		Messages: []DeepSeekMessage{
			{
				Role:    "user",
				Content: prompt,
			},
		},
		Stream: false,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		fmt.Printf("判断 Agent 需求时 JSON 序列化失败：%v\n", err)
		return false, ""
	}

	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		fmt.Printf("判断 Agent 需求时创建请求失败：%v\n", err)
		return false, ""
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("判断 Agent 需求时 HTTP 请求失败：%v\n", err)
		return false, ""
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("判断 Agent 需求时 API 返回错误状态码：%d, 响应：%s\n", resp.StatusCode, string(body))
		return false, ""
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("判断 Agent 需求时读取响应失败：%v\n", err)
		return false, ""
	}

	var response DeepSeekResponse
	if err := json.Unmarshal(body, &response); err != nil {
		fmt.Printf("判断 Agent 需求时解析响应失败：%v\n", err)
		return false, ""
	}

	if len(response.Choices) == 0 {
		return false, ""
	}

	// 解析 AI 返回的 JSON
	aiContent := response.Choices[0].Message.Content
	fmt.Printf("AI 判断结果：%s\n", aiContent)

	// 提取 JSON 内容
	var result struct {
		NeedsAgent    bool   `json:"needs_agent"`
		TaskDesc      string `json:"task_description"`
		NeedsAgentAlt bool   `json:"needsAgent"`
		TaskDescAlt   string `json:"taskDescription"`
	}

	// 尝试解析 JSON
	if err := json.Unmarshal([]byte(aiContent), &result); err != nil {
		// 如果解析失败，尝试查找 JSON 块
		startIdx := strings.Index(aiContent, "{")
		endIdx := strings.LastIndex(aiContent, "}")
		if startIdx != -1 && endIdx > startIdx {
			jsonStr := aiContent[startIdx : endIdx+1]
			json.Unmarshal([]byte(jsonStr), &result)
		}
	}

	// 兼容不同的字段名
	needsAgent := result.NeedsAgent || result.NeedsAgentAlt
	taskDesc := result.TaskDesc
	if taskDesc == "" {
		taskDesc = result.TaskDescAlt
	}

	return needsAgent, taskDesc
}

// callAgentSystem 调用 AI Agent 系统
func callAgentSystem(taskDescription string) (string, error) {
	agentURL := os.Getenv("AGENT_SYSTEM_URL")
	if agentURL == "" {
		agentURL = "http://localhost:8000/api/v1/task/execute"
	}

	requestBody := AgentRequest{
		Description: taskDescription,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("Agent 系统 JSON 序列化失败：%v", err)
	}

	req, err := http.NewRequest("POST", agentURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("Agent 系统创建请求失败：%v", err)
	}

	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{
		Timeout: 120 * time.Second, // Agent 系统可能需要较长时间
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("Agent 系统 HTTP 请求失败：%v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("Agent 系统返回错误状态码：%d, 响应：%s", resp.StatusCode, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("Agent 系统读取响应失败：%v", err)
	}

	var response AgentResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("Agent 系统解析响应失败：%v", err)
	}

	if response.Status == "failed" {
		return "", fmt.Errorf("Agent 系统执行失败：%s", response.Error)
	}

	// 解析 Agent 系统的结果并生成回复
	return formatAgentResponse(response), nil
}

// AgentStreamEvent AI Agent 流式事件
type AgentStreamEvent struct {
	Type string                 `json:"type"`
	Data map[string]interface{} `json:"data"`
}

// ProcessMessageStream 流式处理消息（调用 AI Agent 系统）
func ProcessMessageStream(userID uint, sessionID uint, content string, callback func(eventType string, data map[string]interface{})) error {
	// 1. 保存用户消息
	userMessage := &models.Message{
		SessionID: sessionID,
		Role:      "user",
		Content:   content,
		CreatedAt: time.Now(),
	}
	if err := SendMessage(userMessage); err != nil {
		return err
	}

	// 2. 判断是否需要调用 AI Agent 系统
	needsAgent, taskDescription := shouldUseAgent(content)

	if !needsAgent {
		// 不需要 Agent，直接调用 DeepSeek
		aiResponse, err := callDeepSeekAPIWithHistory(nil, content)
		if err != nil {
			return err
		}
		callback("complete", map[string]interface{}{
			"content": aiResponse,
		})
		// 保存 AI 回复
		aiMessage := &models.Message{
			SessionID: sessionID,
			Role:      "assistant",
			Content:   aiResponse,
			CreatedAt: time.Now(),
		}
		SendMessage(aiMessage)
		return nil
	}

	// 3. 调用 AI Agent 流式接口
	return callAgentSystemStream(taskDescription, sessionID, callback)
}

// callAgentSystemStream 流式调用 AI Agent 系统
func callAgentSystemStream(taskDescription string, sessionID uint, callback func(eventType string, data map[string]interface{})) error {
	agentURL := os.Getenv("AGENT_SYSTEM_URL")
	if agentURL == "" {
		agentURL = "http://localhost:8000"
	}

	// 如果 URL 包含 /api/v1/task/execute，替换为 /api/v1/task/stream
	streamURL := agentURL
	if strings.Contains(agentURL, "/api/v1/task/execute") {
		streamURL = strings.Replace(agentURL, "/api/v1/task/execute", "/api/v1/task/stream", 1)
	} else if !strings.Contains(agentURL, "/api/v1/task/stream") {
		// 如果 URL 只是基础地址，追加流式端点
		streamURL = strings.TrimRight(agentURL, "/") + "/api/v1/task/stream"
	}

	fmt.Printf("=== 开始流式调用 AI Agent 系统 ===\n")
	fmt.Printf("任务描述：%s\n", taskDescription)
	fmt.Printf("Stream URL: %s\n", streamURL)

	requestBody := AgentRequest{
		Description: taskDescription,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("Agent 系统 JSON 序列化失败：%v", err)
	}

	req, err := http.NewRequest("POST", streamURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("Agent 系统创建请求失败：%v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "text/event-stream")

	client := &http.Client{
		Timeout: 300 * time.Second,
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("Agent 系统 HTTP 请求失败：%v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("Agent 系统返回错误状态码：%d, 响应：%s", resp.StatusCode, string(body))
	}

	// 读取 SSE 事件流
	reader := resp.Body
	buf := make([]byte, 4096)
	var lineBuffer bytes.Buffer

	for {
		n, err := reader.Read(buf)
		if n > 0 {
			lineBuffer.Write(buf[:n])

			// 处理完整的事件
			for {
				line, err := lineBuffer.ReadString('\n')
				if err != nil {
					// 没有完整的行了，把剩余的放回 buffer
					lineBuffer.WriteString(line)
					break
				}

				line = strings.TrimSpace(line)
				if strings.HasPrefix(line, "data: ") {
					dataStr := strings.TrimPrefix(line, "data: ")
					if dataStr == "" {
						continue
					}

					var event AgentStreamEvent
					if err := json.Unmarshal([]byte(dataStr), &event); err != nil {
						fmt.Printf("解析 SSE 事件失败：%v, 数据：%s\n", err, dataStr)
						continue
					}

					fmt.Printf("[SSE] 收到事件: type=%s\n", event.Type)

					// 回调处理事件
					callback(event.Type, event.Data)
				}
			}
		}

		if err != nil {
			if err == io.EOF {
				break
			}
			return fmt.Errorf("读取 SSE 流失败：%v", err)
		}
	}

	return nil
}

// callAgentSystemWithResults 调用 AI Agent 系统并返回原始结果（用于保存文件）
func callAgentSystemWithResults(taskDescription string) (string, map[string]interface{}, error) {
	agentURL := os.Getenv("AGENT_SYSTEM_URL")
	if agentURL == "" {
		agentURL = "http://localhost:8000/api/v1/task/execute"
	}

	fmt.Printf("=== 开始调用 AI Agent 系统 ===\n")
	fmt.Printf("任务描述：%s\n", taskDescription)
	fmt.Printf("Agent URL: %s\n", agentURL)

	requestBody := AgentRequest{
		Description: taskDescription,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return "", nil, fmt.Errorf("Agent 系统 JSON 序列化失败：%v", err)
	}

	req, err := http.NewRequest("POST", agentURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", nil, fmt.Errorf("Agent 系统创建请求失败：%v", err)
	}

	req.Header.Set("Content-Type", "application/json")

	fmt.Printf("开始调用 AI Agent 系统：%s\n", agentURL)
	client := &http.Client{
		Timeout: 300 * time.Second, // 增加到 5 分钟，AI Agent 可能需要更长时间
	}

	fmt.Printf("发送 HTTP 请求...\n")
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("AI Agent 系统 HTTP 请求失败（超时或连接错误）：%v\n", err)
		fmt.Printf("请确认 AI Agent 服务是否在 %s 运行\n", agentURL)
		return "", nil, fmt.Errorf("Agent 系统 HTTP 请求失败：%v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", nil, fmt.Errorf("Agent 系统返回错误状态码：%d, 响应：%s", resp.StatusCode, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", nil, fmt.Errorf("Agent 系统读取响应失败：%v", err)
	}

	// 直接解析为 map 以保留所有字段（包括 files）
	var fullResponse map[string]interface{}
	if err := json.Unmarshal(body, &fullResponse); err != nil {
		return "", nil, fmt.Errorf("Agent 系统解析响应失败：%v", err)
	}

	// 检查状态
	if status, ok := fullResponse["status"].(string); ok && status == "failed" {
		errorMsg := ""
		if err, ok := fullResponse["error"].(string); ok {
			errorMsg = err
		}
		return "", nil, fmt.Errorf("Agent 系统执行失败：%s", errorMsg)
	}

	formattedResponse := formatAgentResponseFromMap(fullResponse)
	return formattedResponse, fullResponse, nil
}

// formatAgentResponse 格式化 Agent 系统的响应
func formatAgentResponse(response AgentResponse) string {
	var result bytes.Buffer

	result.WriteString("✅ **多智能体系统已完成任务**\n\n")

	// 处理搜索结果（支持多种可能的字段名）
	var papers []interface{}
	if p, ok := response.Results["papers"].([]interface{}); ok {
		papers = p
	} else if searchResult, ok := response.Results["search_1"].(map[string]interface{}); ok {
		if p, ok := searchResult["papers"].([]interface{}); ok {
			papers = p
		}
	}

	if papers != nil && len(papers) > 0 {
		result.WriteString("## 📚 相关文献\n\n")
		result.WriteString(fmt.Sprintf("共找到 **%d** 篇相关论文，以下是其中最相关的几篇：\n\n", len(papers)))

		for i, paper := range papers {
			if i >= 5 {
				break // 只显示前 5 篇
			}
			if p, ok := paper.(map[string]interface{}); ok {
				result.WriteString(fmt.Sprintf("### %d. %s\n\n", i+1, p["title"]))

				if authors, ok := p["authors"].([]interface{}); ok && len(authors) > 0 {
					authorList := ""
					for j, author := range authors {
						if j > 0 {
							authorList += ", "
						}
						authorList += fmt.Sprintf("%v", author)
					}
					if len(authors) > 3 {
						authorList += " 等"
					}
					result.WriteString(fmt.Sprintf("**作者**: %s\n\n", authorList))
				}

				if published, ok := p["published"].(string); ok {
					result.WriteString(fmt.Sprintf("**发表时间**: %s\n\n", published))
				}

				if summary, ok := p["summary"].(string); ok {
					// 清理摘要中的多余换行和空格
					summary = strings.TrimSpace(summary)
					summary = strings.ReplaceAll(summary, "\n", " ")

					// 只取摘要的前 300 个字符
					if len(summary) > 300 {
						summary = summary[:300] + "..."
					}
					result.WriteString(fmt.Sprintf("**摘要**: %s\n\n", summary))
				}

				if link, ok := p["link"].(string); ok {
					result.WriteString(fmt.Sprintf("[🔗 查看论文](%s)\n\n", link))
				}

				result.WriteString("---\n\n")
			}
		}
	}

	// 处理 RAG 解析结果
	if ragResult, ok := response.Results["rag_1"].(map[string]interface{}); ok {
		result.WriteString("## 🔍 论文解析\n\n")
		if content, ok := ragResult["content"].(string); ok {
			result.WriteString(content)
			result.WriteString("\n\n")
		}
		if analysis, ok := ragResult["analysis"].(string); ok {
			result.WriteString("### 详细分析\n\n")
			result.WriteString(analysis)
			result.WriteString("\n\n")
		}
	}

	// 处理代码生成结果
	if codeResult, ok := response.Results["code_1"].(map[string]interface{}); ok {
		result.WriteString("## 💻 实现代码\n\n")

		// 如果有文件列表，显示文件结构
		if files, ok := codeResult["files"].([]interface{}); ok && len(files) > 0 {
			result.WriteString("###  生成的文件结构\n\n")
			result.WriteString("```\n")
			for _, file := range files {
				if f, ok := file.(map[string]interface{}); ok {
					if path, ok := f["path"].(string); ok {
						result.WriteString(fmt.Sprintf("├── %s\n", path))
					}
				}
			}
			result.WriteString("```\n\n")
		}

		// 显示主要代码
		if code, ok := codeResult["code"].(string); ok && code != "" {
			result.WriteString("### 核心代码实现\n\n")
			result.WriteString("```python\n")
			result.WriteString(code)
			result.WriteString("\n```\n\n")
		}

		// 显示完整响应
		if fullResponse, ok := codeResult["full_response"].(string); ok && fullResponse != "" {
			result.WriteString("### 代码说明\n\n")
			result.WriteString(fullResponse)
			result.WriteString("\n\n")
		}

		// 如果有目录结构信息
		if dirStructure, ok := codeResult["directory_structure"].(string); ok {
			result.WriteString("### 项目目录结构\n\n")
			result.WriteString("```\n")
			result.WriteString(dirStructure)
			result.WriteString("\n```\n\n")
		}
	}

	// 添加总结
	if summary, ok := response.Results["summary"].(string); ok && summary != "" {
		result.WriteString("\n\n## 📝 总结\n\n")
		result.WriteString(summary)
	}

	return result.String()
}

// formatAgentResponseFromMap 格式化 Agent 系统的响应（从 map 解析）
func formatAgentResponseFromMap(response map[string]interface{}) string {
	var result bytes.Buffer

	result.WriteString("✅ **多智能体系统已完成任务**\n\n")

	// 获取 results 字段
	results, _ := response["results"].(map[string]interface{})
	if results == nil {
		results = response
	}

	// 添加任务概述
	if summary, ok := response["summary"].(string); ok && summary != "" {
		result.WriteString("## 📋 任务概述\n\n")
		result.WriteString(summary)
		result.WriteString("\n\n")
	}

	// 详细介绍每个 Agent 的工作
	result.WriteString("## 🤖 各智能体执行情况\n\n")

	// 1. Search Agent 的工作
	var searchPapers []interface{}
	if p, ok := results["papers"].([]interface{}); ok {
		searchPapers = p
	} else if searchResult, ok := results["search_1"].(map[string]interface{}); ok {
		if p, ok := searchResult["papers"].([]interface{}); ok {
			searchPapers = p
		}
	}

	if searchPapers != nil && len(searchPapers) > 0 {
		result.WriteString("### 🔍 **Search Agent（文献搜索）**\n\n")
		result.WriteString(fmt.Sprintf("**工作内容**: 在 arXiv 数据库中搜索相关学术论文\n\n"))
		result.WriteString(fmt.Sprintf("**找到文献**: 共找到 **%d** 篇相关论文\n\n", len(searchPapers)))

		// 显示前 3 篇论文
		for i, paper := range searchPapers {
			if i >= 3 {
				break
			}
			if p, ok := paper.(map[string]interface{}); ok {
				result.WriteString(fmt.Sprintf("**%d. %s**\n\n", i+1, p["title"]))

				if authors, ok := p["authors"].([]interface{}); ok && len(authors) > 0 {
					authorList := ""
					for j, author := range authors {
						if j > 0 {
							authorList += ", "
						}
						authorList += fmt.Sprintf("%v", author)
					}
					if len(authors) > 3 {
						authorList += " 等"
					}
					result.WriteString(fmt.Sprintf("- **作者**: %s\n\n", authorList))
				}

				if published, ok := p["published"].(string); ok {
					result.WriteString(fmt.Sprintf("- **发表时间**: %s\n\n", published))
				}

				if summary, ok := p["summary"].(string); ok {
					summary = strings.TrimSpace(summary)
					summary = strings.ReplaceAll(summary, "\n", " ")
					if len(summary) > 200 {
						summary = summary[:200] + "..."
					}
					result.WriteString(fmt.Sprintf("- **摘要**: %s\n\n", summary))
				}
			}
		}
		result.WriteString("\n")
	}

	// 2. RAG Agent 的工作
	var ragContent, ragAnalysis string
	if ragResult, ok := results["rag_1"].(map[string]interface{}); ok {
		if content, ok := ragResult["content"].(string); ok {
			ragContent = content
		}
		if analysis, ok := ragResult["analysis"].(string); ok {
			ragAnalysis = analysis
		}
	}

	if ragContent != "" || ragAnalysis != "" {
		result.WriteString("###  **RAG Agent（论文解析）**\n\n")
		result.WriteString("**工作内容**: 深入分析选定的论文，提取核心方法和技术细节\n\n")

		if ragContent != "" {
			// 只取前 500 个字符作为简介
			contentPreview := ragContent
			if len(contentPreview) > 500 {
				contentPreview = contentPreview[:500] + "...（完整内容请查看文件）"
			}
			result.WriteString(fmt.Sprintf("**核心内容**: %s\n\n", contentPreview))
		}

		if ragAnalysis != "" {
			analysisPreview := ragAnalysis
			if len(analysisPreview) > 500 {
				analysisPreview = analysisPreview[:500] + "...（完整分析请查看文件）"
			}
			result.WriteString(fmt.Sprintf("**技术分析**: %s\n\n", analysisPreview))
		}
		result.WriteString("\n")
	}

	// 3. Code Agent 的工作
	var codeFiles []interface{}
	var codeContent, fullResponse string
	if codeResult, ok := results["code_1"].(map[string]interface{}); ok {
		if files, ok := codeResult["files"].([]interface{}); ok {
			codeFiles = files
		}
		if code, ok := codeResult["code"].(string); ok {
			codeContent = code
		}
		if resp, ok := codeResult["full_response"].(string); ok {
			fullResponse = resp
		}
	}

	if codeFiles != nil && len(codeFiles) > 0 || codeContent != "" || fullResponse != "" {
		result.WriteString("### 💻 **Code Agent（代码生成）**\n\n")
		result.WriteString("**工作内容**: 根据论文方法实现可运行的代码示例\n\n")

		// 显示生成的文件
		if codeFiles != nil && len(codeFiles) > 0 {
			result.WriteString("**生成的文件**:\n\n")
			result.WriteString("```\n")
			for _, file := range codeFiles {
				if f, ok := file.(map[string]interface{}); ok {
					if path, ok := f["path"].(string); ok {
						result.WriteString(fmt.Sprintf("├── %s\n", path))
					}
				}
			}
			result.WriteString("```\n\n")

			// 显示每个文件的简介
			for i, file := range codeFiles {
				if i >= 5 {
					break
				}
				if f, ok := file.(map[string]interface{}); ok {
					if name, ok := f["name"].(string); ok {
						if desc, ok := f["description"].(string); ok {
							result.WriteString(fmt.Sprintf("- **%s**: %s\n\n", name, desc))
						}
					}
				}
			}
		}

		if fullResponse != "" {
			// 提取代码说明的关键部分
			preview := fullResponse
			if len(preview) > 600 {
				preview = preview[:600] + "...（完整说明请查看文件）"
			}
			result.WriteString(fmt.Sprintf("\n**实现说明**: %s\n\n", preview))
		}
		result.WriteString("\n")
	}

	// 添加文件提示
	result.WriteString("##  生成的文件\n\n")
	result.WriteString("所有生成的文件已保存到系统，包括：\n\n")

	// 直接从顶层 files 字段统计文件数量（这是实际保存的文件）
	fmt.Printf("[formatAgentResponseFromMap] 检查 response[\"files\"] 字段\n")

	var actualFiles []interface{}
	if files, ok := response["files"].([]interface{}); ok {
		actualFiles = files
		fmt.Printf("[formatAgentResponseFromMap] 找到 %d 个文件\n", len(files))
	} else {
		fmt.Printf("[formatAgentResponseFromMap] response[\"files\"] 不存在或类型不匹配\n")
		fmt.Printf("[formatAgentResponseFromMap] response 的 keys: %v\n", getMapKeysDebug(response))
	}

	fileCount := len(actualFiles)

	if fileCount > 0 {
		result.WriteString(" **已生成的文件列表**：\n\n")
		for _, file := range actualFiles {
			if f, ok := file.(map[string]interface{}); ok {
				if name, ok := f["name"].(string); ok {
					if path, ok := f["path"].(string); ok {
						result.WriteString(fmt.Sprintf("- `%s` (%s)\n", name, path))
					} else {
						result.WriteString(fmt.Sprintf("- `%s`\n", name))
					}
				}
			}
		}
		result.WriteString("\n")
	} else {
		result.WriteString("⚠️ 本次任务未生成文件\n\n")
	}

	result.WriteString(fmt.Sprintf("\n**共计 %d 个文件**，请在右侧文件面板中查看和下载。\n\n", fileCount))

	return result.String()
}

// getMapKeysDebug 获取 map 的所有键（用于调试）
func getMapKeysDebug(m map[string]interface{}) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}

// callDeepSeekAPIWithHistory 调用 DeepSeek API（带历史消息）
func callDeepSeekAPIWithHistory(history []*models.Message, currentContent string) (string, error) {
	// 从环境变量获取 API Key
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		return "", fmt.Errorf("未配置 DEEPSEEK_API_KEY 环境变量")
	}

	// 构建消息列表（系统消息 + 历史消息 + 当前消息）
	messages := []DeepSeekMessage{
		{
			Role:    "system",
			Content: "你是一个有帮助的 AI 助手。",
		},
	}

	// 添加历史消息（只取最近 10 条，避免超出 token 限制）
	startIndex := 0
	if len(history) > 10 {
		startIndex = len(history) - 10
	}

	for _, msg := range history[startIndex:] {
		role := "user"
		if msg.Role == "assistant" {
			role = "assistant"
		}
		messages = append(messages, DeepSeekMessage{
			Role:    role,
			Content: msg.Content,
		})
	}

	// 添加当前用户消息
	messages = append(messages, DeepSeekMessage{
		Role:    "user",
		Content: currentContent,
	})

	// 构建请求
	requestBody := DeepSeekRequest{
		Model:    "deepseek-v4-flash",
		Messages: messages,
		Stream:   false,
	}

	// 序列化为 JSON
	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("JSON 序列化失败：%v", err)
	}

	// 创建 HTTP 请求
	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("创建请求失败：%v", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// 发送请求
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("HTTP 请求失败：%v", err)
	}
	defer resp.Body.Close()

	// 检查响应状态
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("API 返回错误状态码：%d, 响应：%s", resp.StatusCode, string(body))
	}

	// 读取响应体
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取响应失败：%v", err)
	}

	// 解析响应
	var response DeepSeekResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("解析响应失败：%v", err)
	}

	// 检查是否有有效的响应
	if len(response.Choices) == 0 {
		return "", fmt.Errorf("AI 未返回有效内容")
	}

	return response.Choices[0].Message.Content, nil
}

// callDeepSeekAPI 调用 DeepSeek API
func callDeepSeekAPI(userContent string) (string, error) {
	// 从环境变量获取 API Key
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		return "", fmt.Errorf("未配置 DEEPSEEK_API_KEY 环境变量")
	}

	// 构建请求
	requestBody := DeepSeekRequest{
		Model: "deepseek-v4-flash",
		Messages: []DeepSeekMessage{
			{
				Role:    "system",
				Content: "你是一个有帮助的 AI 助手。",
			},
			{
				Role:    "user",
				Content: userContent,
			},
		},
		Stream: false,
	}

	// 序列化为 JSON
	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("JSON 序列化失败：%v", err)
	}

	// 创建 HTTP 请求
	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("创建请求失败：%v", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// 发送请求
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("HTTP 请求失败：%v", err)
	}
	defer resp.Body.Close()

	// 检查响应状态
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("API 返回错误状态码：%d, 响应：%s", resp.StatusCode, string(body))
	}

	// 读取响应体
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取响应失败：%v", err)
	}

	// 解析响应
	var response DeepSeekResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("解析响应失败：%v", err)
	}

	// 检查是否有有效的响应
	if len(response.Choices) == 0 {
		return "", fmt.Errorf("AI 未返回有效内容")
	}

	return response.Choices[0].Message.Content, nil
}

// GetSessionMessages 获取会话的所有消息
func GetSessionMessages(sessionId uint) ([]*models.Message, error) {
	return GetMessagesBySessionId(sessionId)
}

// generateSessionTitle 调用 AI 生成会话标题
func generateSessionTitle(userMessage, aiResponse string) (string, error) {
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		return "", fmt.Errorf("未配置 DEEPSEEK_API_KEY 环境变量")
	}

	prompt := `请根据以下对话内容，为这个会话生成一个简洁的标题（不超过20个中文字符）。
只需要返回标题，不需要任何解释或标点符号。

对话内容：
用户：` + userMessage + `
AI：` + aiResponse + `

请直接返回标题：`

	requestBody := DeepSeekRequest{
		Model: "deepseek-v4-flash",
		Messages: []DeepSeekMessage{
			{
				Role:    "user",
				Content: prompt,
			},
		},
		Stream: false,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("JSON 序列化失败：%v", err)
	}

	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("创建请求失败：%v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("HTTP 请求失败：%v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("API 返回错误状态码：%d, 响应：%s", resp.StatusCode, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取响应失败：%v", err)
	}

	var response DeepSeekResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("解析响应失败：%v", err)
	}

	if len(response.Choices) == 0 {
		return "", fmt.Errorf("AI 未返回有效内容")
	}

	title := response.Choices[0].Message.Content
	title = removeTitlePunctuations(title)

	if len(title) > 20 {
		title = title[:20]
	}

	return title, nil
}

// removeTitlePunctuations 移除标题中的标点符号
func removeTitlePunctuations(title string) string {
	punctuations := []string{"。", "，", "！", "？", "：", "；", "\"", "\"", "'", "'", "【", "】", "（", "）", "()", "《", "》"}
	result := title
	for _, p := range punctuations {
		result = removeString(result, p)
	}
	return result
}

// removeString 移除字符串中的指定字符
func removeString(s, toRemove string) string {
	result := ""
	for _, c := range s {
		if string(c) != toRemove {
			result += string(c)
		}
	}
	return result
}

// UpdateSessionTitle 更新会话标题
func UpdateSessionTitle(sessionID uint, title string) error {
	return updateSessionTitleInDB(sessionID, title)
}

// updateSessionTitleInDB 在数据库中更新会话标题
func updateSessionTitleInDB(sessionID uint, title string) error {
	_, err := db.DB.Exec("UPDATE session SET title = ?, updated_at = ? WHERE id = ?", title, time.Now(), sessionID)
	return err
}
