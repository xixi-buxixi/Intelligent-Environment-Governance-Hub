package com.environment.pojo.DTO;

import lombok.Data;

import java.util.List;

@Data
public class RiskAnalyzeRequest {
    private String city;
    private List<String> factors;
    private Integer horizonDays;
    private String analysisMode;
    private Boolean generateReport;
    private Boolean saveRecord;
}
