package middleware

import (
	"auto-researcher/internal/models"
	"auto-researcher/internal/service"
	"auto-researcher/internal/utils"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

// AuthMiddleware 鉴权中间件
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.GetHeader("Authorization")
		tokenString = strings.TrimPrefix(tokenString, "Bearer ")
		// 没有登录用户 token，返回登录页
		if tokenString == "" {
			c.JSON(http.StatusUnauthorized, models.Response{
				Code:    http.StatusUnauthorized,
				Message: utils.MSGUnauthorized,
				Data:    nil,
			})
			c.Abort()
			return
		}

		// 检查 Token 是否在黑名单中
		isBlacklisted, err := service.IsTokenBlacklisted(tokenString)
		if err != nil {
			c.JSON(http.StatusInternalServerError, models.Response{
				Code:    http.StatusInternalServerError,
				Message: "Token 验证失败",
				Data:    nil,
			})
			c.Abort()
			return
		}
		if isBlacklisted {
			c.JSON(http.StatusUnauthorized, models.Response{
				Code:    http.StatusUnauthorized,
				Message: "Token 已失效，请重新登录",
				Data:    nil,
			})
			c.Abort()
			return
		}

		// 验证 token
		claims, err := utils.ParseToken(tokenString)
		// token 不符，清空 Cookie 返回登录页
		if err != nil {
			c.JSON(http.StatusUnauthorized, models.Response{
				Code:    http.StatusUnauthorized,
				Message: utils.MSGTokenExpired,
				Data:    nil,
			})
			c.Abort()
			return
		}
		// 验证通过
		c.Set("userId", claims.UserID)
		c.Next()
	}
}
