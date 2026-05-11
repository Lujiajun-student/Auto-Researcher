package handlers

import (
	"auto-researcher/internal/models"
	"auto-researcher/internal/service"
	"auto-researcher/internal/utils"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

// getUserIdFromContext 从上下文中获取用户 ID
func getUserIdFromContext(c *gin.Context) (uint, error) {
	userId, exists := c.Get("userId")
	if !exists {
		return 0, fmt.Errorf("未授权")
	}
	return userId.(uint), nil
}

// GetSessions 获取当前用户的所有会话
func GetSessions(c *gin.Context) {
	userId, err := getUserIdFromContext(c)
	if err != nil {
		utils.SendUnauthorized(c, err.Error())
		return
	}

	session := &models.Session{UserID: userId}
	sessions, err := service.GetUserSessions(session)
	if err != nil {
		utils.SendBadRequest(c, err.Error())
		return
	}
	utils.SendSuccess(c, sessions)
}

// CreateSession 创建会话
func CreateSession(c *gin.Context) {
	var req struct {
		Title string `json:"title"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.SendBadRequest(c, err.Error())
		return
	}

	userId, err := getUserIdFromContext(c)
	if err != nil {
		utils.SendUnauthorized(c, err.Error())
		return
	}

	session := &models.Session{
		UserID: userId,
		Title:  req.Title,
	}

	if err := service.CreateSession(session); err != nil {
		utils.SendBadRequest(c, err.Error())
		return
	}
	utils.SendSuccess(c, session)
}

// DeleteSession 删除会话
func DeleteSession(c *gin.Context) {
	id := c.Param("sessionId")
	sessionId, err := strconv.ParseUint(id, 10, 32)
	if err != nil {
		utils.SendBadRequest(c, "无效的会话 ID")
		return
	}

	if err := service.DeleteSession(uint(sessionId)); err != nil {
		utils.SendBadRequest(c, err.Error())
		return
	}
	utils.SendSuccess(c, nil)
}

// GetMessages 获取关于会话的所有消息
func GetMessages(c *gin.Context) {
	id := c.Param("sessionId")
	sessionId, err := strconv.ParseUint(id, 10, 32)
	if err != nil {
		utils.SendBadRequest(c, "无效的会话 ID")
		return
	}

	messages, err := service.GetMessagesBySessionId(uint(sessionId))
	if err != nil {
		utils.SendBadRequest(c, err.Error())
		return
	}
	utils.SendSuccess(c, messages)
}

// SendMessage 发送消息
func SendMessage(c *gin.Context) {
	var req struct {
		SessionId uint   `json:"session_id"`
		Content   string `json:"content"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.SendBadRequest(c, err.Error())
		return
	}

	if req.Content == "" {
		utils.SendBadRequest(c, "消息内容不能为空")
		return
	}

	userId, err := getUserIdFromContext(c)
	if err != nil {
		utils.SendUnauthorized(c, err.Error())
		return
	}

	// 设置 SSE 响应头
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("X-Accel-Buffering", "no")

	// 使用流式处理
	err = service.ProcessMessageStream(userId, req.SessionId, req.Content, func(eventType string, data map[string]interface{}) {
		// 将事件写入 SSE 响应
		eventJSON, _ := json.Marshal(map[string]interface{}{
			"type": eventType,
			"data": data,
		})
		c.Writer.WriteString(fmt.Sprintf("data: %s\n\n", string(eventJSON)))
		c.Writer.Flush()
	})

	if err != nil {
		errorJSON, _ := json.Marshal(map[string]interface{}{
			"type": "error",
			"data": map[string]interface{}{"error": err.Error()},
		})
		c.Writer.WriteString(fmt.Sprintf("data: %s\n\n", string(errorJSON)))
		c.Writer.Flush()
	}
}

// GetFiles 获取会话的所有文件
func GetFiles(c *gin.Context) {
	sessionId := c.Param("sessionId")
	id, err := strconv.ParseUint(sessionId, 10, 32)
	if err != nil {
		utils.SendBadRequest(c, "无效的会话 ID")
		return
	}

	files, err := service.GetFilesBySession(uint(id))
	if err != nil {
		utils.SendInternalServerError(c, err.Error())
		return
	}

	fmt.Printf("[GetFiles] 会话 %d 查询到 %d 个文件\n", id, len(files))
	for _, f := range files {
		fmt.Printf("  - %s (%s)\n", f.Name, f.Path)
	}

	// 构建文件树
	fileTree := service.BuildFileTree(files)
	fmt.Printf("[GetFiles] 构建文件树，根节点数量：%d\n", len(fileTree))

	utils.SendSuccess(c, fileTree)
}

// GetFileContent 获取文件内容
func GetFileContent(c *gin.Context) {
	fileId := c.Param("fileId")
	id, err := strconv.ParseUint(fileId, 10, 32)
	if err != nil {
		utils.SendBadRequest(c, "无效的文件 ID")
		return
	}

	file, err := service.GetFileByID(uint(id))
	if err != nil {
		utils.SendNotFound(c, "文件不存在")
		return
	}

	utils.SendSuccess(c, file)
}

// DownloadFile 下载文件
func DownloadFile(c *gin.Context) {
	fileId := c.Param("fileId")
	id, err := strconv.ParseUint(fileId, 10, 32)
	if err != nil {
		utils.SendBadRequest(c, "无效的文件 ID")
		return
	}

	file, err := service.GetFileByID(uint(id))
	if err != nil {
		utils.SendNotFound(c, "文件不存在")
		return
	}

	// 设置响应头
	c.Header("Content-Type", "text/plain; charset=utf-8")
	c.Header("Content-Disposition", "attachment; filename=\""+file.Name+"\"")
	c.String(http.StatusOK, file.Content)
}
