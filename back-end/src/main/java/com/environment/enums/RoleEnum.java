package com.environment.enums;

/**
 * 角色枚举
 */
public enum RoleEnum {

    ADMIN("ADMIN", "管理员"),
    USER("USER", "普通用户"),
    MONITOR("MONITOR", "监测员");

    private final String code;
    private final String desc;

    RoleEnum(String code, String desc) {
        this.code = code;
        this.desc = desc;
    }

    public String getCode() {
        return code;
    }

    public String getDesc() {
        return desc;
    }

    /**
     * 根据code获取枚举
     */
    public static RoleEnum getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (RoleEnum role : values()) {
            if (role.getCode().equals(code)) {
                return role;
            }
        }
        return null;
    }

    /**
     * 判断是否有效的角色
     */
    public static boolean isValid(String code) {
        return getByCode(code) != null;
    }
}