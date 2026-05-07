package com.environment.pojo.DTO;

import java.time.LocalDate;

/**
 * 用户获取次数信息DTO
 */
public class UserFetchLimitDTO {

    /**
     * 用户角色
     */
    private String role;

    /**
     * 今日已使用次数
     */
    private Integer usedCount;

    /**
     * 每日限制次数（普通用户3次，监测员/管理员无限制）
     */
    private Integer dailyLimit;

    /**
     * 剩余次数
     */
    private Integer remainingCount;

    /**
     * 是否有限制
     */
    private Boolean hasLimit;

    /**
     * 当前日期
     */
    private LocalDate currentDate;

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public Integer getUsedCount() {
        return usedCount;
    }

    public void setUsedCount(Integer usedCount) {
        this.usedCount = usedCount;
    }

    public Integer getDailyLimit() {
        return dailyLimit;
    }

    public void setDailyLimit(Integer dailyLimit) {
        this.dailyLimit = dailyLimit;
    }

    public Integer getRemainingCount() {
        return remainingCount;
    }

    public void setRemainingCount(Integer remainingCount) {
        this.remainingCount = remainingCount;
    }

    public Boolean getHasLimit() {
        return hasLimit;
    }

    public void setHasLimit(Boolean hasLimit) {
        this.hasLimit = hasLimit;
    }

    public LocalDate getCurrentDate() {
        return currentDate;
    }

    public void setCurrentDate(LocalDate currentDate) {
        this.currentDate = currentDate;
    }
}
