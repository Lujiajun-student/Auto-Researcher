package main

import (
	"auto-researcher/internal/db"
	"auto-researcher/internal/handlers"
	"auto-researcher/internal/middleware"
	"auto-researcher/internal/redis"

	"github.com/gin-gonic/gin"
)

func main() {
	// 数据库
	db.InitDB()
	defer db.DB.Close()

	// Redis
	if err := redis.InitRedis(); err != nil {
		panic(err)
	}
	defer redis.Close()

	r := gin.Default()
	apiGroup := r.Group("/api")
	authGroup := apiGroup.Group("/auth")
	{
		authGroup.POST("/register", handlers.Register)
		authGroup.POST("/login", handlers.Login)
		authGroup.POST("/logout", handlers.Logout)
		authGroup.GET("/:userId", handlers.GetUserInfo, middleware.AuthMiddleware())
		authGroup.DELETE("/:userId", handlers.DeleteUser, middleware.AuthMiddleware())

	}

	chatGroup := apiGroup.Group("/chat")
	chatGroup.Use(middleware.AuthMiddleware())
	{
		chatGroup.GET("/sessions", handlers.GetSessions)
		chatGroup.POST("/sessions", handlers.CreateSession)
		chatGroup.DELETE("/sessions/:sessionId", handlers.DeleteSession)
		chatGroup.GET("/sessions/:sessionId/messages", handlers.GetMessages)
		chatGroup.POST("/send", handlers.SendMessage)
		chatGroup.GET("/sessions/:sessionId/files", handlers.GetFiles)
		chatGroup.GET("/files/:fileId", handlers.GetFileContent)
		chatGroup.GET("/files/:fileId/download", handlers.DownloadFile)
	}

	r.Run(":8080")
}
