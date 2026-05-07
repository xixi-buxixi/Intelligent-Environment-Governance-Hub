package com.environment.pojo.DTO;

import lombok.Data;

import java.util.List;

@Data
public class RiskAnalyzeResponse {
    private Long analysisId;
    private String city;
    private List<String> factors;
    private Integer horizonDays;
    private String riskLevel;
    private Integer riskScore;
    private String keyFactor;
    private List<String> riskDates;
    private Double confidence;
    private String trendSummary;
    private String causeExplanation;
    private List<String> governanceSuggestions;
    private String publicAdvice;
    private List<RiskPredictionDay> predictions;
    private List<RiskTrendItem> trendItems;
    private Boolean alertCreated = false;
    private Long alertId;
    private String reportContent;
}
