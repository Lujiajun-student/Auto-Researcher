package service

import (
	"auto-researcher/internal/redis"
	"time"
)

const (
	// TokenBlacklistPrefix Redis 中 Token 黑名单的前缀
	TokenBlacklistPrefix = "token:blacklist:"
)

// AddTokenToBlacklist 将 Token 加入黑名单
// token: JWT Token 字符串
// expireDuration: Token 的剩余有效期（黑名单的过期时间）
func AddTokenToBlacklist(token string, expireDuration time.Duration) error {
	key := TokenBlacklistPrefix + token
	return redis.Client.Set(redis.Ctx, key, "1", expireDuration).Err()
}

// IsTokenBlacklisted 检查 Token 是否在黑名单中
func IsTokenBlacklisted(token string) (bool, error) {
	key := TokenBlacklistPrefix + token
	exists, err := redis.Client.Exists(redis.Ctx, key).Result()
	if err != nil {
		return false, err
	}
	return exists > 0, nil
}

// GetTokenTTL 获取 Token 在黑名单中的剩余时间
func GetTokenTTL(token string) (time.Duration, error) {
	key := TokenBlacklistPrefix + token
	return redis.Client.TTL(redis.Ctx, key).Result()
}

// RemoveTokenFromBlacklist 从黑名单中移除 Token（可选功能）
func RemoveTokenFromBlacklist(token string) error {
	key := TokenBlacklistPrefix + token
	return redis.Client.Del(redis.Ctx, key).Err()
}

// CleanExpiredBlacklist 清理过期的黑名单（Redis 会自动过期，此函数可选）
func CleanExpiredBlacklist() error {
	// Redis 会自动删除过期的 key，所以这个函数实际上不需要做任何事
	// 这里只是为了代码完整性
	return nil
}
