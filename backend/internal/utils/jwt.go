package utils

import (
	"fmt"
	"os"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var jwtSecret = []byte(os.Getenv("JWT_SECRET"))

type CustomClaims struct {
	UserID uint `json:"user_id"`
	jwt.RegisteredClaims
}

// GenerateJWT 根据用户 ID 生成 JWT
func GenerateJWT(userId uint) (string, error) {

	claims := &CustomClaims{
		userId,
		jwt.RegisteredClaims{
			// 设置过期时间
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
			// 签发人
			Issuer: "auto_researcher",
			// 签发时间
			IssuedAt: jwt.NewNumericDate(time.Now()),
		},
	}
	// 创建 token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(jwtSecret)
	if err != nil {
		return "", err
	}
	return tokenString, nil
}

// ParseToken 解析 JWT
func ParseToken(tokenString string) (*CustomClaims, error) {
	// 1. 解析 Token
	token, err := jwt.ParseWithClaims(tokenString, &CustomClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf(MSGUnauthorized)
		}
		return jwtSecret, nil
	})

	if err != nil {
		return nil, err
	}

	// 2. 校验 Claims 并提取数据
	if claims, ok := token.Claims.(*CustomClaims); ok && token.Valid {
		return claims, nil
	}
	return nil, fmt.Errorf(MSGUnauthorized)
}
