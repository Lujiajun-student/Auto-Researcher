package dao

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/models"
	"auto-researcher/internal/utils"
	"errors"
)

func CreateUser(user *models.User) error {
	hash, err := utils.HashPassword(user.Password)
	if err != nil {
		return err
	}
	result, err := db.DB.Exec("INSERT INTO user (username, password) VALUES (?, ?)", user.Username, hash)
	if err != nil {
		return err
	}
	id, err := result.LastInsertId()
	if err != nil {
		return err
	}
	user.ID = uint(id)
	return nil
}

func GetUserById(id uint) (*models.User, error) {
	user := models.User{}
	err := db.DB.QueryRow("SELECT id, username, password, created_at, updated_at FROM user WHERE id = ?", id).Scan(&user.ID, &user.Username, &user.Password, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// GetUserByUsername 登录时查看是否重名
func GetUserByUsername(username string) (*models.User, error) {
	user := models.User{}
	err := db.DB.QueryRow("SELECT id, username, password, created_at, updated_at FROM user WHERE username = ?", username).Scan(&user.ID, &user.Username, &user.Password, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func DeleteUser(user *models.User) error {
	_, err := db.DB.Exec("DELETE FROM user WHERE id = ?", user.ID)
	return err
}

func Login(username string, password string) (*models.User, error) {
	user := models.User{}
	err := db.DB.QueryRow("SELECT id, username, password FROM user WHERE username = ?", username).Scan(&user.ID, &user.Username, &user.Password)
	if err != nil {
		return nil, err
	}
	if !utils.CheckPassword(password, user.Password) {
		return nil, errors.New("wrong password")
	}
	return &user, nil
}
