// Package dao 会话 DAO 模型
package dao

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
)

// CreateSession 创建会话
func CreateSession(session *models.Session) error {
	return db.GormDB.Create(session).Error
}

// GetSessionById 根据 ID 查询会话
func GetSessionById(id uint) (*models.Session, error) {
	session := &models.Session{}
	err := db.GormDB.First(session, id).Error
	if err != nil {
		return nil, err
	}
	return session, nil
}

// GetSessionsByUserId 根据用户 id 查询所有会话
func GetSessionsByUserId(session *models.Session) ([]*models.Session, error) {
	var sessions []*models.Session
	err := db.GormDB.Where("user_id = ?", session.UserID).Find(&sessions).Error
	return sessions, err
}

// DeleteSession 删除会话
func DeleteSession(id uint) error {
	return db.GormDB.Delete(&models.Session{}, id).Error
}
