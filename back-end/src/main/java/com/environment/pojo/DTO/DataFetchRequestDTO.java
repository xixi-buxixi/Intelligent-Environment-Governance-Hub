package com.environment.pojo.DTO;

import java.time.LocalDate;

/**
 * 数据获取请求DTO
 */
public class DataFetchRequestDTO {

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
     * 是否确认继续触发爬虫（当超7天时）
     */
    private Boolean forceUpdate;

    /**
     * 预览条数
     */
    private Integer previewLimit;

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

    public Boolean getForceUpdate() {
        return forceUpdate;
    }

    public void setForceUpdate(Boolean forceUpdate) {
        this.forceUpdate = forceUpdate;
    }

    public Integer getPreviewLimit() {
        return previewLimit;
    }

    public void setPreviewLimit(Integer previewLimit) {
        this.previewLimit = previewLimit;
    }

    @Override
    public String toString() {
        return "DataFetchRequestDTO{" +
                "sourceId=" + sourceId +
                ", city='" + city + '\'' +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", dataType='" + dataType + '\'' +
                ", forceUpdate=" + forceUpdate +
                '}';
    }
}
