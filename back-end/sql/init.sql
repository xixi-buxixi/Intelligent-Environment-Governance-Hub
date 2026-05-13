-- =============================================
-- 智能环境治理中枢平台 - 数据库初始化脚本
-- 创建时间：2024-03-10
-- =============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS environment_hub DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE environment_hub;

-- =============================================
-- 用户表
-- =============================================
DROP TABLE IF EXISTS `sys_user`;

CREATE TABLE `sys_user` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `password` VARCHAR(100) NOT NULL COMMENT '密码',
    `real_name` VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
    `department` VARCHAR(100) DEFAULT NULL COMMENT '部门',
    `role` VARCHAR(20) DEFAULT 'USER' COMMENT '角色：ADMIN-管理员，USER-普通用户，MONITOR-监测专员',
    `status` TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted` TINYINT(1) DEFAULT 0 COMMENT '删除标志：0-未删除，1-已删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_status` (`status`),
    KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- =============================================
-- 角色表
-- =============================================
DROP TABLE IF EXISTS `sys_role`;

CREATE TABLE `sys_role` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    `role_name` VARCHAR(50) NOT NULL COMMENT '角色名称',
    `role_code` VARCHAR(50) NOT NULL COMMENT '角色编码',
    `description` VARCHAR(200) DEFAULT NULL COMMENT '角色描述',
    `status` TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_role_code` (`role_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- =============================================
-- 初始化数据
-- =============================================

-- 插入默认管理员
INSERT INTO `sys_user` (`username`, `password`, `real_name`, `email`, `phone`, `department`, `role`, `status`) VALUES
('admin', 'admin123', '系统管理员', 'admin@example.com', '13800138000', '信息技术部', 'ADMIN', 1);

-- 插入测试用户
INSERT INTO `sys_user` (`username`, `password`, `real_name`, `email`, `phone`, `department`, `role`, `status`) VALUES
('user01', '123456', '张三', 'zhangsan@example.com', '13800138001', '运维部', 'USER', 1),
('user02', '123456', '李四', 'lisi@example.com', '13800138002', '监测部', 'MONITOR', 1),
('user03', '123456', '王五', 'wangwu@example.com', '13800138003', '运维部', 'USER', 0),
('user04', '123456', '赵六', 'zhaoliu@example.com', '13800138004', '管理部', 'USER', 1),
('monitor01', '123456', '孙七', 'sunqi@example.com', '13800138005', '监测部', 'MONITOR', 1);

-- 插入默认角色
INSERT INTO `sys_role` (`role_name`, `role_code`, `description`, `status`) VALUES
('管理员', 'ADMIN', '系统管理员，拥有所有权限', 1),
('普通用户', 'USER', '普通用户，拥有基本权限', 1),
('监测员', 'MONITOR', '监测专员，拥有数据查看权限', 1);

-- =============================================
-- 用户权限申请表
-- =============================================
DROP TABLE IF EXISTS `permission_application`;

CREATE TABLE `permission_application` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '申请ID',
    `user_id` BIGINT(20) NOT NULL COMMENT '申请用户ID',
    `current_role` VARCHAR(20) NOT NULL COMMENT '申请时角色',
    `target_role` VARCHAR(20) NOT NULL COMMENT '申请目标角色',
    `reason` VARCHAR(500) NOT NULL COMMENT '申请原因',
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING-待处理，APPROVED-已同意，REJECTED-已拒绝',
    `reviewer_id` BIGINT(20) DEFAULT NULL COMMENT '审批管理员ID',
    `review_comment` VARCHAR(500) DEFAULT NULL COMMENT '审批意见',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `review_time` DATETIME DEFAULT NULL COMMENT '审批时间',
    PRIMARY KEY (`id`),
    KEY `idx_permission_application_user` (`user_id`),
    KEY `idx_permission_application_status` (`status`),
    KEY `idx_permission_application_reviewer` (`reviewer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户权限申请表';

-- =============================================
-- 数据源配置表
-- =============================================
DROP TABLE IF EXISTS `data_source`;

CREATE TABLE `data_source` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '数据源ID',
    `source_name` VARCHAR(100) NOT NULL COMMENT '数据源名称',
    `source_code` VARCHAR(50) NOT NULL COMMENT '数据源编码',
    `source_url` VARCHAR(500) DEFAULT NULL COMMENT '数据源URL',
    `description` VARCHAR(500) DEFAULT NULL COMMENT '数据源描述',
    `data_types` VARCHAR(500) DEFAULT NULL COMMENT '可获取数据类型，JSON格式',
    `status` TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_source_code` (`source_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据源配置表';

-- =============================================
-- 用户数据获取记录表
-- =============================================
DROP TABLE IF EXISTS `data_fetch_record`;

CREATE TABLE `data_fetch_record` (
    `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    `user_id` BIGINT(20) NOT NULL COMMENT '用户ID',
    `source_id` BIGINT(20) NOT NULL COMMENT '数据源ID',
    `city` VARCHAR(50) NOT NULL COMMENT '城市',
    `start_date` DATE NOT NULL COMMENT '起始日期',
    `end_date` DATE NOT NULL COMMENT '终止日期',
    `data_type` VARCHAR(50) DEFAULT NULL COMMENT '数据类型',
    `file_name` VARCHAR(200) DEFAULT NULL COMMENT '导出文件名',
    `file_path` VARCHAR(500) DEFAULT NULL COMMENT '文件路径',
    `record_count` INT DEFAULT 0 COMMENT '记录数',
    `fetch_date` DATE NOT NULL COMMENT '获取日期',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_fetch_date` (`fetch_date`),
    KEY `idx_source_id` (`source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户数据获取记录表';

-- =============================================
-- 初始化数据源数据
-- =============================================
INSERT INTO `data_source` (`source_name`, `source_code`, `source_url`, `description`, `data_types`, `status`) VALUES
('中国环境监测总站', 'CNEMC', 'https://air.cnemc.cn/', '全国城市空气质量实时发布平台', '["AQI", "PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]', 1),
('天气后', 'TIANQI', 'https://www.tianqihou.com/', '历史天气数据查询网站', '["温度", "湿度", "风速", "风向", "天气状况"]', 1),
('水环境监测数据', 'WATER_API', 'https://moonapi.com/', '水质监测数据API', '["水质等级", "pH值", "溶解氧", "高锰酸盐指数", "氨氮"]', 1);
