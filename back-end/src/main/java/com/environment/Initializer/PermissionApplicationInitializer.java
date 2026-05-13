package com.environment.Initializer;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

/**
 * 权限申请表初始化
 */
@Component
public class PermissionApplicationInitializer implements CommandLineRunner {
    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Override
    public void run(String... args) {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS permission_application (
                    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '申请ID',
                    user_id BIGINT NOT NULL COMMENT '申请用户ID',
                    current_role VARCHAR(20) NOT NULL COMMENT '申请时角色',
                    target_role VARCHAR(20) NOT NULL COMMENT '申请目标角色',
                    reason VARCHAR(500) NOT NULL COMMENT '申请原因',
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态：PENDING/APPROVED/REJECTED',
                    reviewer_id BIGINT DEFAULT NULL COMMENT '审批管理员ID',
                    review_comment VARCHAR(500) DEFAULT NULL COMMENT '审批意见',
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    review_time DATETIME DEFAULT NULL COMMENT '审批时间',
                    PRIMARY KEY (id),
                    KEY idx_permission_application_user (user_id),
                    KEY idx_permission_application_status (status),
                    KEY idx_permission_application_reviewer (reviewer_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户权限申请表'
                """);
    }
}
