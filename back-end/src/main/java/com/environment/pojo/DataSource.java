package com.environment.pojo;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 数据源配置实体类
 */
public class DataSource {

    /**
     * 数据源ID
     */
    private Long id;

    /**
     * 数据源名称
     */
    private String sourceName;

    /**
     * 数据源编码
     */
    private String sourceCode;

    /**
     * 数据源URL
     */
    private String sourceUrl;

    /**
     * 数据源描述
     */
    private String description;

    /**
     * 可获取数据类型，JSON格式
     */
    private String dataTypes;

    /**
     * 状态：0-禁用，1-启用
     */
    private Integer status;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getSourceName() {
        return sourceName;
    }

    public void setSourceName(String sourceName) {
        this.sourceName = sourceName;
    }

    public String getSourceCode() {
        return sourceCode;
    }

    public void setSourceCode(String sourceCode) {
        this.sourceCode = sourceCode;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public void setSourceUrl(String sourceUrl) {
        this.sourceUrl = sourceUrl;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getDataTypes() {
        return dataTypes;
    }

    public void setDataTypes(String dataTypes) {
        this.dataTypes = dataTypes;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }

    public LocalDateTime getCreateTime() {
        return createTime;
    }

    public void setCreateTime(LocalDateTime createTime) {
        this.createTime = createTime;
    }

    public LocalDateTime getUpdateTime() {
        return updateTime;
    }

    public void setUpdateTime(LocalDateTime updateTime) {
        this.updateTime = updateTime;
    }

    @Override
    public String toString() {
        return "DataSource{" +
                "id=" + id +
                ", sourceName='" + sourceName + '\'' +
                ", sourceCode='" + sourceCode + '\'' +
                ", status=" + status +
                '}';
    }
}
