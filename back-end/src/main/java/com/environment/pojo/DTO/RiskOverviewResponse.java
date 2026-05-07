package com.environment.pojo.DTO;

import lombok.Data;

import java.util.List;

@Data
public class RiskOverviewResponse {
    private String city;
    private String highestRiskLevel;
    private Integer riskScore;
    private String keyFactor;
    private Double confidence;
    private String trendSummary;
    private Integer pendingAlertCount = 0;
    private Integer processingAlertCount = 0;
    private Integer resolvedAlertCount = 0;
    private List<RiskTrendItem> trendItems;
}
