package com.environment.pojo.DTO;

import lombok.Data;

@Data
public class RiskTrendItem {
    private String date;
    private String factor;
    private Number predictedValue;
    private String riskLevel;
    private Integer riskScore;
    private Boolean exceedThreshold;
}
