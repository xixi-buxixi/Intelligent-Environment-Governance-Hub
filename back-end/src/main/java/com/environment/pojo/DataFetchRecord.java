package com.environment.pojo;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 数据获取记录实体类
 */
public class DataFetchRecord {

    /**
     * 记录ID
     */
    private Long id;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 数据源ID
     */
    private Long sourceId;

    /**
     * 城市
     */
    private String city;

    /**
     * 起始日期
     */
    private LocalDate startDate;

    /**
     * 终止日期
     */
    private LocalDate endDate;

    /**
     * 数据类型
     */
    private String dataType;

    /**
     * 导出文件名
     */
    private String fileName;

    /**
     * 文件路径
     */
    private String filePath;

    /**
     * 记录数
     */
    private Integer recordCount;

    /**
     * 获取日期
     */
    private LocalDate fetchDate;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    // 关联信息
    private String sourceName;
    private String sourceUrl;
    private String username;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public Long getSourceId() {
        return sourceId;
    }

    public void setSourceId(Long sourceId) {
        this.sourceId = sourceId;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public LocalDate getStartDate() {
        return startDate;
    }

    public void setStartDate(LocalDate startDate) {
        this.startDate = startDate;
    }

    public LocalDate getEndDate() {
        return endDate;
    }

    public void setEndDate(LocalDate endDate) {
        this.endDate = endDate;
    }

    public String getDataType() {
        return dataType;
    }

    public void setDataType(String dataType) {
        this.dataType = dataType;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public Integer getRecordCount() {
        return recordCount;
    }

    public void setRecordCount(Integer recordCount) {
        this.recordCount = recordCount;
    }

    public LocalDate getFetchDate() {
        return fetchDate;
    }

    public void setFetchDate(LocalDate fetchDate) {
        this.fetchDate = fetchDate;
    }

    public LocalDateTime getCreateTime() {
        return createTime;
    }

    public void setCreateTime(LocalDateTime createTime) {
        this.createTime = createTime;
    }

    public String getSourceName() {
        return sourceName;
    }

    public void setSourceName(String sourceName) {
        this.sourceName = sourceName;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public void setSourceUrl(String sourceUrl) {
        this.sourceUrl = sourceUrl;
    }

    @Override
    public String toString() {
        return "DataFetchRecord{" +
                "id=" + id +
                ", userId=" + userId +
                ", city='" + city + '\'' +
                ", fetchDate=" + fetchDate +
                '}';
    }
}
