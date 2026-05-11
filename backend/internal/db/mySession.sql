use auto_researcher;
CREATE TABLE `sessions` (
                           `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
                           `user_id` INT NOT NULL COMMENT '用户 ID (外键)',
                           `title` VARCHAR(255) DEFAULT '新会话' COMMENT '会话标题',
                           `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                           `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 约束：假设你已经有张 user 表
                           CONSTRAINT `fk_session_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;