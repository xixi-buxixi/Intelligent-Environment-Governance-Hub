package com.environment.pojo.DTO;

/**
 * 权限申请请求
 */
public class PermissionApplicationRequest {
    private String targetRole;
    private String reason;

    public String getTargetRole() {
        return targetRole;
    }

    public void setTargetRole(String targetRole) {
        this.targetRole = targetRole;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
