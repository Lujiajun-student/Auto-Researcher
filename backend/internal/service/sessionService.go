package service

import (
	"auto-researcher/internal/dao"
	"auto-researcher/internal/models"
	"time"
)

// CreateSession 创建会话
func CreateSession(session *models.Session) error {
	session.CreatedAt = time.Now()
	session.UpdatedAt = time.Now()
	return dao.CreateSession(session)
}

// GetUserSessions 获取用户所有回话
func GetUserSessions(session *models.Session) ([]*models.Session, error) {
	return dao.GetSessionsByUserId(session)
}

// DeleteSession 删除会话
func DeleteSession(id uint) error {
	return dao.DeleteSession(id)
}
