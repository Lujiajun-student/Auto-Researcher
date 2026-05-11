// Package dao 消息 DAO 模型
package dao

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
)

// CreateMessage 创建消息
func CreateMessage(message *models.Message) error {
	return db.GormDB.Create(message).Error
}

// GetMessagesBySessionId 根据会话 id 查询会话所有消息
func GetMessagesBySessionId(sessionId uint) ([]*models.Message, error) {
	var messages []*models.Message
	err := db.GormDB.Where("session_id = ?", sessionId).Order("created_at ASC").Find(&messages).Error
	return messages, err
}

// DeleteMessageBySessionId 根据会话 id 删除会话所有消息
func DeleteMessageBySessionId(sessionId uint) error {
	return db.GormDB.Where("session_id = ?", sessionId).Delete(&models.Message{}).Error
}
