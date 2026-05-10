package handlers

import (
	"auto-researcher/internal/models"
	"auto-researcher/internal/service"
	"auto-researcher/internal/utils"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

// Register 注册用户
func Register(c *gin.Context) {
	var user models.User
	if err := c.ShouldBind(&user); err != nil {
		c.JSON(http.StatusBadRequest, utils.GetResponse(http.StatusBadRequest, utils.MSGParameterError, nil))
		return
	}
	userId, err := service.Register(user)
	if err != nil {
		c.JSON(http.StatusUnauthorized, utils.GetResponse(http.StatusUnauthorized, utils.MSGRegisterFailed, nil))
		return
	}
	c.JSON(http.StatusOK, utils.GetResponse(http.StatusOK, utils.MSGSuccess, gin.H{"user": gin.H{"user_id": userId, "username": user.Username}}))
}

// Login 登录用户
func Login(c *gin.Context) {
	var u models.User
	if err := c.ShouldBind(&u); err != nil {
		c.JSON(http.StatusBadRequest, utils.GetResponse(http.StatusBadRequest, utils.MSGParameterError, nil))
		return
	}

	// 获取旧的 Token（如果有的话）
	oldToken := c.GetHeader("Authorization")
	if oldToken != "" {
		oldToken = strings.TrimPrefix(oldToken, "Bearer ")
	}

	user, token, err := service.Login(u, oldToken)
	if err != nil {
		c.JSON(http.StatusUnauthorized, utils.GetResponse(http.StatusUnauthorized, utils.MSGLoginFailed, nil))
		return
	}

	c.JSON(http.StatusOK, utils.GetResponse(http.StatusOK, utils.MSGSuccess, gin.H{"token": token, "user": gin.H{"user_id": user.ID, "username": user.Username}}))
}

// Logout 退出登录
func Logout(c *gin.Context) {
	// 获取 Token
	tokenString := c.GetHeader("Authorization")
	if tokenString == "" {
		c.JSON(http.StatusBadRequest, utils.GetResponse(http.StatusBadRequest, "未提供 Token", nil))
		return
	}

	tokenString = strings.TrimPrefix(tokenString, "Bearer ")

	// 解析 Token 获取过期时间
	claims, err := utils.ParseToken(tokenString)
	if err != nil {
		c.JSON(http.StatusBadRequest, utils.GetResponse(http.StatusBadRequest, "Token 无效", nil))
		return
	}

	// 计算 Token 剩余时间
	expiresAt := claims.ExpiresAt
	if expiresAt != nil {
		expireDuration := time.Until(expiresAt.Time)
		if expireDuration > 0 {
			// 将 Token 加入黑名单
			service.AddTokenToBlacklist(tokenString, expireDuration)
		}
	}

	c.JSON(http.StatusOK, utils.GetResponse(http.StatusOK, "退出成功", nil))
}

// GetUserInfo 获取用户信息
func GetUserInfo(c *gin.Context) {
	userId, _ := strconv.ParseUint(c.Param("userId"), 10, 32)
	user, err := service.GetUserInfo(uint(userId))
	if err != nil {
		c.JSON(http.StatusNotFound, utils.GetResponse(http.StatusNotFound, utils.MsgNotfound, nil))
		return
	}
	c.JSON(http.StatusOK, utils.GetResponse(http.StatusOK, utils.MSGSuccess, user))
}

// DeleteUser 删除用户
func DeleteUser(c *gin.Context) {
	userId, _ := strconv.ParseUint(c.Param("userId"), 10, 32)
	err := service.DeleteUser(uint(userId))
	if err != nil {
		c.JSON(http.StatusUnauthorized, utils.GetResponse(http.StatusUnauthorized, utils.MSGDeleteFailed, nil))
		return
	}
	c.JSON(http.StatusOK, utils.GetResponse(http.StatusOK, utils.MSGSuccess, nil))
}
