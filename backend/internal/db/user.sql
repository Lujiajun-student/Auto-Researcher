-- 如果数据库不存在则创建
CREATE DATABASE IF NOT EXISTS `auto_researcher`;
USE `auto_researcher`;

-- 创建用户表
CREATE TABLE `user` (
                        `id`         INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                        `username`   VARCHAR(50) NOT NULL UNIQUE     COMMENT '唯一用户名',
                        `password`   VARCHAR(255) NOT NULL           COMMENT '加密后的密码',
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;