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
	user.Password = hash
	return db.GormDB.Create(user).Error
}

func GetUserById(id uint) (*models.User, error) {
	user := &models.User{}
	err := db.GormDB.First(user, id).Error
	if err != nil {
		return nil, err
	}
	return user, nil
}

// GetUserByUsername 登录时查看是否重名
func GetUserByUsername(username string) (*models.User, error) {
	user := &models.User{}
	err := db.GormDB.Where("username = ?", username).First(user).Error
	if err != nil {
		return nil, err
	}
	return user, nil
}

func DeleteUser(user *models.User) error {
	return db.GormDB.Delete(user).Error
}

func Login(username string, password string) (*models.User, error) {
	user := &models.User{}
	err := db.GormDB.Where("username = ?", username).First(user).Error
	if err != nil {
		return nil, err
	}
	if !utils.CheckPassword(password, user.Password) {
		return nil, errors.New("wrong password")
	}
	return user, nil
}
