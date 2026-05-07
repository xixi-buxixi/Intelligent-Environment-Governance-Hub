package com.environment.pojo.DTO;

import lombok.Data;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.util.LinkedHashMap;
import java.util.Map;

@Data
public class RiskPredictionDay {
    private String date;
    private Map<String, Object> values;
    private String dailyRiskLevel;
    private Integer dailyRiskScore;
    private String mainFactor;
    private Boolean exceedThreshold;

    @JsonIgnore
    public Map<String, Object> getValuesWithDate() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("date", date);
        if (values != null) {
            row.putAll(values);
        }
        return row;
    }
}
