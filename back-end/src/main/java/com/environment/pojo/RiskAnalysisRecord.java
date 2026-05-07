package com.environment.pojo;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;

@Data
public class RiskAnalysisRecord {
    private Long id;
    private Long userId;
    private String createUserName;
    private String city;
    private String factors;
    private Integer horizonDays;
    private String riskLevel;
    private Integer riskScore;
    private String keyFactor;
    private Double confidence;
    private String predictionJson;
    private String trendSummary;
    private String explanation;
    private String suggestions;
    private String publicAdvice;
    private String reportContent;
    private LocalDateTime createTime;

    public List<String> getFactorList() {
        if (factors == null || factors.isBlank()) {
            return Collections.emptyList();
        }
        try {
            return new ObjectMapper().readValue(factors, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return List.of(factors.split(","));
        }
    }
}
