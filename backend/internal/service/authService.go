package service

import (
	"auto-researcher/internal/dao"
	"auto-researcher/internal/models"
	"auto-researcher/internal/utils"
	"errors"
	"time"
)

func Register(u models.User) (userId uint, err error) {
	// 校验用户名和密码是否为空
	if u.Username == "" || u.Password == "" {
		return 0, errors.New("username or password is empty")
	}

	// 校验用户是否重名
	existUser, _ := dao.GetUserByUsername(u.Username)
	if existUser != nil {
		return 0, errors.New("username already exists")
	}

	err = dao.CreateUser(&u)
	if err != nil {
		return 0, err
	}
	userId = u.ID
	return userId, nil
}

func Login(u models.User, oldToken string) (user *models.User, token string, err error) {
	// 校验用户名和密码是否为空
	if u.Username == "" || u.Password == "" {
		return nil, "", errors.New("user not found")
	}

	user, err = dao.Login(u.Username, u.Password)

	if err != nil {
		return nil, "", err
	}

	// 将旧 Token 加入黑名单（如果有的话）
	if oldToken != "" {
		// 获取 Token 的剩余有效期
		claims, err := utils.ParseToken(oldToken)
		if err == nil {
			// 计算 Token 剩余时间
			expiresAt := claims.ExpiresAt
			if expiresAt != nil {
				expireDuration := time.Until(expiresAt.Time)
				if expireDuration > 0 {
					// 将旧 Token 加入黑名单
					AddTokenToBlacklist(oldToken, expireDuration)
				}
			}
		}
		// 忽略解析错误，继续登录流程
	}

	token, err = utils.GenerateJWT(user.ID)

	if err != nil {
		return nil, "", err
	}

	return user, token, nil
}

func GetUserInfo(userId uint) (user *models.User, err error) {
	user = &models.User{}
	user, err = dao.GetUserById(userId)
	if err != nil {
		return nil, err
	}
	return user, nil
}

// DeleteUser 删除用户
func DeleteUser(userId uint) error {
	user, err := dao.GetUserById(userId)
	if err != nil {
		return err
	}
	err = dao.DeleteUser(user)
	if err != nil {
		return err
	}
	return nil
}
