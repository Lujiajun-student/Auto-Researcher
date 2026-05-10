package models

import "time"

// Session 会话模型
type Session struct {
	ID        uint      `gorm:"primary_key;auto_increment" json:"id"`
	UserID    uint      `json:"user_id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}
