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

// GetSessions 获取当前用户的所有会话
func GetSessions(c *gin.Context) {
	userId, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.Response{
			Code:    http.StatusUnauthorized,
			Message: "未授权",
			Data:    nil,
		})
		return
	}

	session := &models.Session{UserID: userId.(uint)}
	sessions, err := service.GetUserSessions(session)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}
	c.JSON(http.StatusOK, models.Response{
		Code:    http.StatusOK,
		Message: utils.MSGSuccess,
		Data:    sessions,
	})
}

// CreateSession 创建会话
func CreateSession(c *gin.Context) {
	var req struct {
		Title string `json:"title"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}

	userId, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.Response{
			Code:    http.StatusUnauthorized,
			Message: "未授权",
			Data:    nil,
		})
		return
	}

	session := &models.Session{
		UserID: userId.(uint),
		Title:  req.Title,
	}

	if err := service.CreateSession(session); err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}
	c.JSON(http.StatusOK, models.Response{
		Code:    http.StatusOK,
		Message: utils.MSGSuccess,
		Data:    session,
	})
}

// DeleteSession 删除会话
func DeleteSession(c *gin.Context) {
	id := c.Param("sessionId")
	sessionId, err := strconv.ParseUint(id, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: "无效的会话 ID",
			Data:    nil,
		})
		return
	}

	if err := service.DeleteSession(uint(sessionId)); err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}
	c.JSON(http.StatusOK, models.Response{
		Code:    http.StatusOK,
		Message: utils.MSGSuccess,
		Data:    nil,
	})
}

// GetMessages 获取关于会话的所有消息
func GetMessages(c *gin.Context) {
	id := c.Param("sessionId")
	sessionId, err := strconv.ParseUint(id, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: "无效的会话 ID",
			Data:    nil,
		})
		return
	}

	messages, err := service.GetMessagesBySessionId(uint(sessionId))
	if err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}
	c.JSON(http.StatusOK, models.Response{
		Code:    http.StatusOK,
		Message: utils.MSGSuccess,
		Data:    messages,
	})
}

// SendMessage 发送消息
func SendMessage(c *gin.Context) {
	var req struct {
		SessionId uint   `json:"session_id"`
		Content   string `json:"content"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}

	if req.Content == "" {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: "消息内容不能为空",
			Data:    nil,
		})
		return
	}

	userId, exists := c.Get("userId")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.Response{
			Code:    http.StatusUnauthorized,
			Message: "未授权",
			Data:    nil,
		})
		return
	}

	// 设置 SSE 响应头
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("X-Accel-Buffering", "no")

	// 使用流式处理
	err := service.ProcessMessageStream(userId.(uint), req.SessionId, req.Content, func(eventType string, data map[string]interface{}) {
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
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: "无效的会话 ID",
			Data:    nil,
		})
		return
	}

	files, err := service.GetFilesBySession(uint(id))
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.Response{
			Code:    http.StatusInternalServerError,
			Message: err.Error(),
			Data:    nil,
		})
		return
	}

	fmt.Printf("[GetFiles] 会话 %d 查询到 %d 个文件\n", id, len(files))
	for _, f := range files {
		fmt.Printf("  - %s (%s)\n", f.Name, f.Path)
	}

	// 构建文件树
	fileTree := service.BuildFileTree(files)
	fmt.Printf("[GetFiles] 构建文件树，根节点数量：%d\n", len(fileTree))

	c.JSON(http.StatusOK, models.Response{
		Code:    http.StatusOK,
		Message: utils.MSGSuccess,
		Data:    fileTree,
	})
}

// GetFileContent 获取文件内容
func GetFileContent(c *gin.Context) {
	fileId := c.Param("fileId")
	id, err := strconv.ParseUint(fileId, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: "无效的文件 ID",
			Data:    nil,
		})
		return
	}

	file, err := service.GetFileByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, models.Response{
			Code:    http.StatusNotFound,
			Message: "文件不存在",
			Data:    nil,
		})
		return
	}

	c.JSON(http.StatusOK, models.Response{
		Code:    http.StatusOK,
		Message: utils.MSGSuccess,
		Data:    file,
	})
}

// DownloadFile 下载文件
func DownloadFile(c *gin.Context) {
	fileId := c.Param("fileId")
	id, err := strconv.ParseUint(fileId, 10, 32)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.Response{
			Code:    http.StatusBadRequest,
			Message: "无效的文件 ID",
			Data:    nil,
		})
		return
	}

	file, err := service.GetFileByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, models.Response{
			Code:    http.StatusNotFound,
			Message: "文件不存在",
			Data:    nil,
		})
		return
	}

	// 设置响应头
	c.Header("Content-Type", "text/plain; charset=utf-8")
	c.Header("Content-Disposition", "attachment; filename=\""+file.Name+"\"")
	c.String(http.StatusOK, file.Content)
}
