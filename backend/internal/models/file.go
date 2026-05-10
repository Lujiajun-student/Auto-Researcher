package models

import "time"

// File AI 生成的文件
type File struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	SessionID uint      `json:"session_id" gorm:"index"`
	Name      string    `json:"name" gorm:"size:255;not null"`
	Path      string    `json:"path" gorm:"size:512;not null"` // 文件路径（目录结构）
	Content   string    `json:"content" gorm:"type:text"`       // 文件内容
	Size      string    `json:"size" gorm:"size:50"`           // 文件大小（格式化后的字符串）
	Type      string    `json:"type" gorm:"size:50"`           // 文件类型：code, paper, summary
	Language  string    `json:"language" gorm:"size:50"`       // 编程语言（如果是代码）
	CreatedAt time.Time `json:"created_at" gorm:"autoCreateTime"`
}

// FileTree 文件树节点
type FileTree struct {
	Name     string     `json:"name"`
	Type     string     `json:"type"` // folder 或 file
	Children []*FileTree `json:"children,omitempty"`
	File     *File      `json:"file,omitempty"`
}
