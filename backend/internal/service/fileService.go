package service

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
	"fmt"
	"strings"
	"time"
)

// CreateFile 创建文件记录
func CreateFile(file *models.File) error {
	return db.GormDB.Create(file).Error
}

// GetFilesBySession 获取会话的所有文件
func GetFilesBySession(sessionID uint) ([]*models.File, error) {
	var files []*models.File
	err := db.GormDB.Where("session_id = ?", sessionID).Order("created_at ASC").Find(&files).Error
	return files, err
}

// GetFileByID 根据 ID 获取文件
func GetFileByID(fileID uint) (*models.File, error) {
	var file models.File
	err := db.GormDB.First(&file, fileID).Error
	if err != nil {
		return nil, err
	}
	return &file, nil
}

// DeleteFile 删除文件
func DeleteFile(fileID uint) error {
	return db.GormDB.Delete(&models.File{}, fileID).Error
}

// BuildFileTree 构建文件树
func BuildFileTree(files []*models.File) []*models.FileTree {
	root := make([]*models.FileTree, 0)
	folderMap := make(map[string]*models.FileTree)

	// 首先创建所有文件夹
	for _, file := range files {
		path := file.Path
		if path == "" {
			path = file.Name
		}

		// 分割路径
		parts := splitPath(path)
		currentPath := ""

		// 创建路径中的所有文件夹
		for i, part := range parts[:len(parts)-1] {
			if currentPath == "" {
				currentPath = part
			} else {
				currentPath = currentPath + "/" + part
			}

			if _, exists := folderMap[currentPath]; !exists {
				folderMap[currentPath] = &models.FileTree{
					Name:     part,
					Type:     "folder",
					Children: make([]*models.FileTree, 0),
				}

				// 添加到根节点或父文件夹
				if i == 0 {
					root = append(root, folderMap[currentPath])
				} else {
					parentPath := ""
					if i > 1 {
						for j := 0; j < i-1; j++ {
							if parentPath == "" {
								parentPath = parts[j]
							} else {
								parentPath = parentPath + "/" + parts[j]
							}
						}
					}
					if parentFolder, exists := folderMap[parentPath]; exists {
						parentFolder.Children = append(parentFolder.Children, folderMap[currentPath])
					}
				}
			}
		}
	}

	// 添加文件到对应的文件夹
	for _, file := range files {
		path := file.Path
		if path == "" {
			path = file.Name
		}

		parts := splitPath(path)
		fileName := parts[len(parts)-1]

		fileNode := &models.FileTree{
			Name: fileName,
			Type: "file",
			File: file,
		}

		// 如果有父文件夹，添加到父文件夹
		if len(parts) > 1 {
			parentPath := ""
			for i := 0; i < len(parts)-1; i++ {
				if parentPath == "" {
					parentPath = parts[i]
				} else {
					parentPath = parentPath + "/" + parts[i]
				}
			}
			if parentFolder, exists := folderMap[parentPath]; exists {
				parentFolder.Children = append(parentFolder.Children, fileNode)
			}
		} else {
			// 直接添加到根节点
			root = append(root, fileNode)
		}
	}

	return root
}

// splitPath 分割文件路径
func splitPath(path string) []string {
	// 支持 Windows 和 Unix 路径分隔符
	result := make([]string, 0)
	current := ""

	for _, c := range path {
		if c == '/' || c == '\\' {
			if current != "" {
				result = append(result, current)
				current = ""
			}
		} else {
			current += string(c)
		}
	}

	if current != "" {
		result = append(result, current)
	}

	return result
}

// SaveAgentFiles 保存 Agent 生成的文件
func SaveAgentFiles(sessionID uint, agentResponse map[string]interface{}) error {
	fmt.Printf("开始保存 Agent 生成的文件到会话 %d\n", sessionID)

	// 打印接收到的数据结构，方便调试
	fmt.Printf("Agent 响应数据结构:\n")
	for key, value := range agentResponse {
		if files, ok := value.([]interface{}); ok {
			fmt.Printf("  - %s: %d 个元素\n", key, len(files))
		} else if m, ok := value.(map[string]interface{}); ok {
			fmt.Printf("  - %s: map (keys: %v)\n", key, getMapKeys(m))
		} else {
			fmt.Printf("  - %s: %T\n", key, value)
		}
	}

	// 优先从顶层 files 字段读取（新的响应格式）
	if files, ok := agentResponse["files"].([]interface{}); ok && len(files) > 0 {
		fmt.Printf("发现 %d 个文件需要保存（从顶层 files 字段）\n", len(files))
		for _, fileData := range files {
			if f, ok := fileData.(map[string]interface{}); ok {
				name, _ := f["name"].(string)
				path, _ := f["path"].(string)
				content, _ := f["content"].(string)
				language, _ := f["language"].(string)

				if name != "" && content != "" {
					// 如果没有指定路径，使用默认路径
					if path == "" {
						path = name
					}

					// 如果没有指定语言，根据路径判断
					if language == "" {
						language = getLanguageFromPath(path)
					}

					// 确定文件类型
					fileType := "code"
					if strings.Contains(path, "analysis/") {
						fileType = "paper"
					} else if strings.Contains(path, "search/") {
						fileType = "paper"
					} else if strings.Contains(path, "summary/") {
						fileType = "summary"
					}

					file := &models.File{
						SessionID: sessionID,
						Name:      name,
						Path:      path,
						Content:   content,
						Size:      formatFileSize(len(content)),
						Type:      fileType,
						Language:  language,
						CreatedAt: time.Now(),
					}
					if err := CreateFile(file); err != nil {
						fmt.Printf("保存文件失败：%v\n", err)
					} else {
						fmt.Printf("成功保存文件：%s (%s)\n", file.Path, fileType)
					}
				}
			}
		}
	}

	// 兼容旧格式：从 results 中读取 files
	if results, ok := agentResponse["results"].(map[string]interface{}); ok {
		if files, ok := results["files"].([]interface{}); ok && len(files) > 0 {
			fmt.Printf("发现 %d 个文件需要保存（从 results.files 字段）\n", len(files))
			for _, fileData := range files {
				if f, ok := fileData.(map[string]interface{}); ok {
					name, _ := f["name"].(string)
					path, _ := f["path"].(string)
					content, _ := f["content"].(string)
					language, _ := f["language"].(string)

					if name != "" && content != "" {
						if path == "" {
							path = name
						}

						if language == "" {
							language = getLanguageFromPath(path)
						}

						fileType := "code"
						if strings.Contains(path, "analysis/") {
							fileType = "paper"
						} else if strings.Contains(path, "search/") {
							fileType = "paper"
						} else if strings.Contains(path, "summary/") {
							fileType = "summary"
						}

						file := &models.File{
							SessionID: sessionID,
							Name:      name,
							Path:      path,
							Content:   content,
							Size:      formatFileSize(len(content)),
							Type:      fileType,
							Language:  language,
							CreatedAt: time.Now(),
						}
						if err := CreateFile(file); err != nil {
							fmt.Printf("保存文件失败：%v\n", err)
						} else {
							fmt.Printf("成功保存文件：%s (%s)\n", file.Path, fileType)
						}
					}
				}
			}
		}
	}

	// 兼容旧格式：保存代码文件（支持多个文件）
	if codeResult, ok := agentResponse["code_1"].(map[string]interface{}); ok {
		// 如果有文件列表，保存所有文件
		if files, ok := codeResult["files"].([]interface{}); ok && len(files) > 0 {
			for _, fileData := range files {
				if f, ok := fileData.(map[string]interface{}); ok {
					name, _ := f["name"].(string)
					path, _ := f["path"].(string)
					content, _ := f["content"].(string)

					if name != "" && content != "" {
						file := &models.File{
							SessionID: sessionID,
							Name:      name,
							Path:      path,
							Content:   content,
							Size:      formatFileSize(len(content)),
							Type:      "code",
							Language:  getLanguageFromPath(path),
							CreatedAt: time.Now(),
						}
						if err := CreateFile(file); err != nil {
							fmt.Printf("保存代码文件失败：%v\n", err)
						} else {
							fmt.Printf("成功保存代码文件：%s\n", file.Path)
						}
					}
				}
			}
		}

		// 保存主要代码文件
		if code, ok := codeResult["code"].(string); ok && code != "" {
			file := &models.File{
				SessionID: sessionID,
				Name:      "main.py",
				Path:      "code/main.py",
				Content:   code,
				Size:      formatFileSize(len(code)),
				Type:      "code",
				Language:  "python",
				CreatedAt: time.Now(),
			}
			if err := CreateFile(file); err != nil {
				fmt.Printf("保存代码文件失败：%v\n", err)
			} else {
				fmt.Printf("成功保存代码文件：%s\n", file.Path)
			}
		}

		// 保存完整响应
		if fullResponse, ok := codeResult["full_response"].(string); ok && fullResponse != "" {
			file := &models.File{
				SessionID: sessionID,
				Name:      "code_explanation.md",
				Path:      "code/code_explanation.md",
				Content:   fullResponse,
				Size:      formatFileSize(len(fullResponse)),
				Type:      "summary",
				Language:  "markdown",
				CreatedAt: time.Now(),
			}
			if err := CreateFile(file); err != nil {
				fmt.Printf("保存代码说明文件失败：%v\n", err)
			} else {
				fmt.Printf("成功保存代码说明文件：%s\n", file.Path)
			}
		}

		// 保存目录结构信息
		if dirStructure, ok := codeResult["directory_structure"].(string); ok && dirStructure != "" {
			file := &models.File{
				SessionID: sessionID,
				Name:      "directory_structure.txt",
				Path:      "code/directory_structure.txt",
				Content:   dirStructure,
				Size:      formatFileSize(len(dirStructure)),
				Type:      "summary",
				Language:  "text",
				CreatedAt: time.Now(),
			}
			if err := CreateFile(file); err != nil {
				fmt.Printf("保存目录结构文件失败：%v\n", err)
			} else {
				fmt.Printf("成功保存目录结构文件：%s\n", file.Path)
			}
		}
	}

	// 兼容旧格式：保存论文解析结果
	if ragResult, ok := agentResponse["rag_1"].(map[string]interface{}); ok {
		if content, ok := ragResult["content"].(string); ok && content != "" {
			file := &models.File{
				SessionID: sessionID,
				Name:      "paper_analysis.md",
				Path:      "analysis/paper_analysis.md",
				Content:   content,
				Size:      formatFileSize(len(content)),
				Type:      "paper",
				Language:  "markdown",
				CreatedAt: time.Now(),
			}
			if err := CreateFile(file); err != nil {
				fmt.Printf("保存论文解析文件失败：%v\n", err)
			} else {
				fmt.Printf("成功保存论文解析文件：%s\n", file.Path)
			}
		}

		if analysis, ok := ragResult["analysis"].(string); ok && analysis != "" {
			file := &models.File{
				SessionID: sessionID,
				Name:      "detailed_analysis.md",
				Path:      "analysis/detailed_analysis.md",
				Content:   analysis,
				Size:      formatFileSize(len(analysis)),
				Type:      "paper",
				Language:  "markdown",
				CreatedAt: time.Now(),
			}
			if err := CreateFile(file); err != nil {
				fmt.Printf("保存详细分析文件失败：%v\n", err)
			} else {
				fmt.Printf("成功保存详细分析文件：%s\n", file.Path)
			}
		}
	}

	// 兼容旧格式：保存搜索结果
	if searchResult, ok := agentResponse["search_1"].(map[string]interface{}); ok {
		if summary, ok := searchResult["summary"].(string); ok && summary != "" {
			file := &models.File{
				SessionID: sessionID,
				Name:      "search_summary.md",
				Path:      "search/search_summary.md",
				Content:   summary,
				Size:      formatFileSize(len(summary)),
				Type:      "paper",
				Language:  "markdown",
				CreatedAt: time.Now(),
			}
			if err := CreateFile(file); err != nil {
				fmt.Printf("保存搜索总结文件失败：%v\n", err)
			} else {
				fmt.Printf("成功保存搜索总结文件：%s\n", file.Path)
			}
		}
	}

	// 保存总结
	if summary, ok := agentResponse["summary"].(string); ok && summary != "" {
		file := &models.File{
			SessionID: sessionID,
			Name:      "task_summary.md",
			Path:      "summary/task_summary.md",
			Content:   summary,
			Size:      formatFileSize(len(summary)),
			Type:      "summary",
			Language:  "markdown",
			CreatedAt: time.Now(),
		}
		if err := CreateFile(file); err != nil {
			fmt.Printf("保存任务总结文件失败：%v\n", err)
		} else {
			fmt.Printf("成功保存任务总结文件：%s\n", file.Path)
		}
	}

	return nil
}

// getLanguageFromPath 根据文件路径判断编程语言
func getLanguageFromPath(path string) string {
	if strings.HasSuffix(path, ".py") {
		return "python"
	} else if strings.HasSuffix(path, ".js") || strings.HasSuffix(path, ".jsx") {
		return "javascript"
	} else if strings.HasSuffix(path, ".ts") || strings.HasSuffix(path, ".tsx") {
		return "typescript"
	} else if strings.HasSuffix(path, ".java") {
		return "java"
	} else if strings.HasSuffix(path, ".cpp") || strings.HasSuffix(path, ".cc") {
		return "cpp"
	} else if strings.HasSuffix(path, ".c") {
		return "c"
	} else if strings.HasSuffix(path, ".go") {
		return "go"
	} else if strings.HasSuffix(path, ".rs") {
		return "rust"
	} else if strings.HasSuffix(path, ".rb") {
		return "ruby"
	} else if strings.HasSuffix(path, ".php") {
		return "php"
	} else if strings.HasSuffix(path, ".md") {
		return "markdown"
	} else if strings.HasSuffix(path, ".json") {
		return "json"
	} else if strings.HasSuffix(path, ".yaml") || strings.HasSuffix(path, ".yml") {
		return "yaml"
	} else if strings.HasSuffix(path, ".xml") {
		return "xml"
	} else if strings.HasSuffix(path, ".html") {
		return "html"
	} else if strings.HasSuffix(path, ".css") {
		return "css"
	}
	return "text"
}

// formatFileSize 格式化文件大小
func formatFileSize(size int) string {
	if size < 1024 {
		return fmt.Sprintf("%d B", size)
	} else if size < 1024*1024 {
		return fmt.Sprintf("%.2f KB", float64(size)/1024)
	} else {
		return fmt.Sprintf("%.2f MB", float64(size)/(1024*1024))
	}
}

// getMapKeys 获取 map 的所有键
func getMapKeys(m map[string]interface{}) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}
