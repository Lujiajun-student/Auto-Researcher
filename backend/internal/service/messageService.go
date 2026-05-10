package service

import (
	"auto-researcher/internal/dao"
	"auto-researcher/internal/models"
	"time"
)

// SendMessage 发送消息
func SendMessage(message *models.Message) error {
	message.CreatedAt = time.Now()
	return dao.CreateMessage(message)
}

// GetMessagesBySessionId 根据会话id查询会话所有消息
func GetMessagesBySessionId(sessionId uint) ([]*models.Message, error) {
	return dao.GetMessagesBySessionId(sessionId)
}

// DeleteMessageBySessionId 根据会话id删除会话所有消息
func DeleteMessageBySessionId(sessionId uint) error {
	return dao.DeleteMessageBySessionId(sessionId)
}
