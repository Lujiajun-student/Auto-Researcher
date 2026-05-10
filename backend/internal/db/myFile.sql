-- 创建 AI 生成的文件表
CREATE TABLE IF NOT EXISTS `files` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL COMMENT '会话 ID',
  `name` varchar(255) NOT NULL COMMENT '文件名',
  `path` varchar(512) NOT NULL COMMENT '文件路径（目录结构）',
  `content` text COMMENT '文件内容',
  `size` varchar(50) DEFAULT NULL COMMENT '文件大小（格式化后的字符串）',
  `type` varchar(50) DEFAULT NULL COMMENT '文件类型：code, paper, summary',
  `language` varchar(50) DEFAULT NULL COMMENT '编程语言（如果是代码）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 生成的文件表';
