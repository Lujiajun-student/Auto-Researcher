package models

import "time"

// Message 消息模型
type Message struct {
	ID        uint      `gorm:"primary_key;auto_increment" json:"id"`
	SessionID uint      `json:"session_id"`
	Role      string    `json:"role"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}
