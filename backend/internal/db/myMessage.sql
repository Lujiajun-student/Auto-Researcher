use auto_researcher;
CREATE TABLE `messages` (
                           `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
                           `session_id` INT NOT NULL COMMENT '会话 ID (外键)',
                           `role` ENUM('user', 'assistant') NOT NULL COMMENT '角色 (user/assistant)',
                           `content` TEXT NOT NULL COMMENT '消息内容',
                           `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    -- 约束：会话删除时，关联的消息也一并删除
                           CONSTRAINT `fk_message_session` FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;