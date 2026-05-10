package utils

import "auto-researcher/internal/models"

/*
 * 构建响应数据
 */

func GetResponse(code int, msg string, data any) models.Response {
	return models.Response{
		Code:    code,
		Message: msg,
		Data:    data,
	}
}
