// Package dao 会话DAO模型
package dao

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
)

// CreateSession 创建会话
func CreateSession(session *models.Session) error {
	_, err := db.DB.Exec("INSERT INTO session (user_id, title) VALUES (?, ?)", session.UserID, session.Title)
	return err
}

// GetSessionById 根据 ID 查询会话
func GetSessionById(id uint) (*models.Session, error) {
	session := models.Session{}
	err := db.DB.QueryRow("SELECT id, user_id, title, created_at, updated_at FROM session WHERE id = ?", id).Scan(&session.ID, &session.UserID, &session.Title, &session.CreatedAt, &session.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return &session, nil
}

// GetSessionsByUserId 根据用户 id 查询所有会话
func GetSessionsByUserId(session *models.Session) ([]*models.Session, error) {
	rows, err := db.DB.Query("SELECT id, user_id, title, created_at, updated_at FROM session WHERE user_id = ?", int(session.UserID))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var sessions []*models.Session
	for rows.Next() {
		s := &models.Session{}
		err := rows.Scan(&s.ID, &s.UserID, &s.Title, &s.CreatedAt, &s.UpdatedAt)
		if err != nil {
			return nil, err
		}
		sessions = append(sessions, s)
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	return sessions, nil
}

// DeleteSession 删除会话
func DeleteSession(id uint) error {
	_, err := db.DB.Exec("DELETE FROM session WHERE id = ?", id)
	return err
}
