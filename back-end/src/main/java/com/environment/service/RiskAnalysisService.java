package com.environment.service;

import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.RiskAnalyzeRequest;
import com.environment.pojo.DTO.RiskAnalyzeResponse;
import com.environment.pojo.DTO.RiskOverviewResponse;
import com.environment.pojo.RiskAnalysisRecord;
import com.environment.pojo.User;

public interface RiskAnalysisService {
    RiskAnalyzeResponse analyze(RiskAnalyzeRequest request, User user);

    RiskOverviewResponse overview(String city, String factors, Integer horizonDays, User user);

    PageResult<RiskAnalysisRecord> getRecords(Integer page, Integer size, String city, String riskLevel, User user);

    RiskAnalysisRecord getRecordById(Long id, User user);
}
