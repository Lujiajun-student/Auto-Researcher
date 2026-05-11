package utils

import (
	"auto-researcher/internal/models"
	"net/http"

	"github.com/gin-gonic/gin"
)

/*
 * 构建响应数据
 */

func GetResponse(code int, msg string, data any) models.Response {
	return models.Response{
		Code:    code,
		Message: msg,
		Data:    data,
	}
}

// SendSuccess 发送成功响应
func SendSuccess(c *gin.Context, data any) {
	c.JSON(http.StatusOK, GetResponse(http.StatusOK, MSGSuccess, data))
}

// SendError 发送错误响应
func SendError(c *gin.Context, code int, message string) {
	c.JSON(code, GetResponse(code, message, nil))
}

// SendBadRequest 发送 400 错误响应
func SendBadRequest(c *gin.Context, message string) {
	SendError(c, http.StatusBadRequest, message)
}

// SendUnauthorized 发送 401 错误响应
func SendUnauthorized(c *gin.Context, message string) {
	SendError(c, http.StatusUnauthorized, message)
}

// SendNotFound 发送 404 错误响应
func SendNotFound(c *gin.Context, message string) {
	SendError(c, http.StatusNotFound, message)
}

// SendInternalServerError 发送 500 错误响应
func SendInternalServerError(c *gin.Context, message string) {
	SendError(c, http.StatusInternalServerError, message)
}
