// Package dao 消息DAO模型
package dao

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
)

// CreateMessage 创建消息
func CreateMessage(message *models.Message) error {
	_, err := db.DB.Exec("INSERT INTO message (session_id, role, content) VALUES (?, ?, ?)", message.SessionID, message.Role, message.Content)
	return err
}

// GetMessagesBySessionId 根据会话id查询会话所有消息
func GetMessagesBySessionId(sessionId uint) ([]*models.Message, error) {

	rows, err := db.DB.Query("SELECT * FROM message WHERE session_id = ?", sessionId)

	if err != nil {
		return nil, err
	}

	defer rows.Close()

	var messages []*models.Message

	for rows.Next() {

		var message models.Message

		err := rows.Scan(&message.ID, &message.SessionID, &message.Role, &message.Content, &message.CreatedAt)
		if err != nil {
			return nil, err
		}

		messages = append(messages, &message)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return messages, nil
}

// DeleteMessageBySessionId 根据会话id删除会话所有消息
func DeleteMessageBySessionId(sessionId uint) error {
	_, err := db.DB.Exec("DELETE FROM message WHERE session_id = ?", sessionId)
	return err
}
