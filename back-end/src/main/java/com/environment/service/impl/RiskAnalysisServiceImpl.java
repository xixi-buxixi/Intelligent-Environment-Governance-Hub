package com.environment.service.impl;

import com.environment.mapper.RiskAnalysisRecordMapper;
import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.RiskAnalyzeRequest;
import com.environment.pojo.DTO.RiskAnalyzeResponse;
import com.environment.pojo.DTO.RiskOverviewResponse;
import com.environment.pojo.DTO.RiskPredictionDay;
import com.environment.pojo.RiskAnalysisRecord;
import com.environment.pojo.User;
import com.environment.service.RiskAnalysisService;
import com.environment.service.risk.RiskScoreCalculator;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class RiskAnalysisServiceImpl implements RiskAnalysisService {

    private static final List<String> DEFAULT_FACTORS = List.of("AQI", "PM25", "PM10", "O3");
    private static final List<String> GOVERNANCE_SUGGESTIONS = List.of(
            "建议加强重点道路扬尘管控和施工工地巡查。",
            "建议关注工业企业废气治理设施运行状态。",
            "建议提前发布空气质量提醒，提示敏感人群做好防护。"
    );
    private static final String PUBLIC_ADVICE = "敏感人群应减少长时间户外活动，外出时可佩戴防护口罩，并持续关注空气质量变化。";

    @Autowired
    private RiskAnalysisRecordMapper riskAnalysisRecordMapper;

    @Autowired
    private RiskScoreCalculator riskScoreCalculator;

    @Autowired
    private WebClient.Builder webClientBuilder;

    @Value("${python.api.url:http://localhost:5001}")
    private String pythonApiUrl;

    @Value("${python.api.predict-path:/api/predict/air-quality}")
    private String pythonPredictPath;

    @Value("${python.api.chat-path:/api/chat}")
    private String pythonChatPath;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public RiskAnalyzeResponse analyze(RiskAnalyzeRequest request, User user) {
        if (user == null) {
            throw new IllegalArgumentException("未登录或登录已过期");
        }
        RiskAnalyzeRequest normalized = normalizeRequest(request);
        List<Map<String, Object>> rawPredictions;
        boolean predictionDegraded = false;
        try {
            rawPredictions = callPredictService(normalized.getCity(), normalized.getFactors());
        } catch (Exception e) {
            rawPredictions = fallbackPredictions(normalized.getFactors());
            predictionDegraded = true;
        }

        RiskScoreCalculator.ScoreResult scoreResult = riskScoreCalculator.calculate(normalized.getFactors(), rawPredictions);

        RiskAnalyzeResponse response = new RiskAnalyzeResponse();
        response.setCity(normalized.getCity());
        response.setFactors(normalized.getFactors());
        response.setHorizonDays(7);
        response.setRiskLevel(scoreResult.getRiskLevel());
        response.setRiskScore(scoreResult.getRiskScore());
        response.setKeyFactor(scoreResult.getKeyFactor());
        response.setRiskDates(scoreResult.getRiskDates());
        response.setConfidence(predictionDegraded ? 0.65 : 0.85);
        response.setPredictions(scoreResult.getPredictionDays());
        response.setTrendItems(scoreResult.getTrendItems());
        response.setTrendSummary(buildTrendSummary(normalized.getCity(), scoreResult, predictionDegraded));
        response.setAlertCreated(false);

        String mode = resolveMode(normalized.getAnalysisMode());
        String fallbackExplanation = buildFallbackExplanation(response);
        if ("FAST".equals(mode)) {
            response.setCauseExplanation(fallbackExplanation);
        } else {
            response.setCauseExplanation(callAiExplanation(response, fallbackExplanation));
        }
        response.setGovernanceSuggestions(GOVERNANCE_SUGGESTIONS);
        response.setPublicAdvice(PUBLIC_ADVICE);
        if (Boolean.TRUE.equals(normalized.getGenerateReport())) {
            response.setReportContent(buildReport(response));
        }

        if (Boolean.TRUE.equals(normalized.getSaveRecord())) {
            RiskAnalysisRecord record = toRecord(response, user.getId());
            riskAnalysisRecordMapper.insert(record);
            response.setAnalysisId(record.getId());
        }
        return response;
    }

    @Override
    public RiskOverviewResponse overview(String city, String factors, Integer horizonDays, User user) {
        RiskAnalyzeRequest request = new RiskAnalyzeRequest();
        request.setCity(city == null || city.isBlank() ? "宜春" : city);
        request.setFactors(parseFactors(factors));
        request.setHorizonDays(horizonDays);
        request.setAnalysisMode("FAST");
        request.setGenerateReport(false);
        request.setSaveRecord(false);

        RiskAnalyzeResponse analysis = analyze(request, user);
        RiskScoreCalculator.ScoreResult scoreResult = riskScoreCalculator.calculate(
                analysis.getFactors(),
                analysis.getPredictions().stream().map(RiskPredictionDay::getValuesWithDate).toList()
        );

        RiskOverviewResponse overview = new RiskOverviewResponse();
        overview.setCity(analysis.getCity());
        overview.setHighestRiskLevel(analysis.getRiskLevel());
        overview.setRiskScore(analysis.getRiskScore());
        overview.setKeyFactor(analysis.getKeyFactor());
        overview.setConfidence(analysis.getConfidence());
        overview.setTrendSummary(analysis.getTrendSummary());
        overview.setTrendItems(scoreResult.getTrendItems());
        return overview;
    }

    @Override
    public PageResult<RiskAnalysisRecord> getRecords(Integer page, Integer size, String city, String riskLevel, User user) {
        int currentPage = page == null || page < 1 ? 1 : page;
        int pageSize = size == null || size < 1 ? 10 : Math.min(size, 50);
        Long visibleUserId = canViewAll(user) ? null : user.getId();
        String normalizedRiskLevel = normalizeRiskLevel(riskLevel);
        int total = riskAnalysisRecordMapper.countByCondition(visibleUserId, city, normalizedRiskLevel);
        List<RiskAnalysisRecord> records = riskAnalysisRecordMapper.selectByCondition(
                visibleUserId,
                city,
                normalizedRiskLevel,
                (currentPage - 1) * pageSize,
                pageSize
        );
        return new PageResult<>(records, (long) total, (long) currentPage, (long) pageSize);
    }

    @Override
    public RiskAnalysisRecord getRecordById(Long id, User user) {
        RiskAnalysisRecord record = riskAnalysisRecordMapper.selectById(id);
        if (record == null) {
            return null;
        }
        if (!canViewAll(user) && !record.getUserId().equals(user.getId())) {
            return null;
        }
        return record;
    }

    private RiskAnalyzeRequest normalizeRequest(RiskAnalyzeRequest request) {
        RiskAnalyzeRequest normalized = request == null ? new RiskAnalyzeRequest() : request;
        if (normalized.getCity() == null || normalized.getCity().isBlank()) {
            normalized.setCity("宜春");
        } else {
            normalized.setCity(normalized.getCity().trim());
        }

        List<String> factors = riskScoreCalculator.normalizeFactors(normalized.getFactors());
        if (factors.isEmpty()) {
            factors = DEFAULT_FACTORS;
        }
        normalized.setFactors(factors);
        normalized.setHorizonDays(7);
        normalized.setAnalysisMode(resolveMode(normalized.getAnalysisMode()));
        if (normalized.getGenerateReport() == null) {
            normalized.setGenerateReport(false);
        }
        if (normalized.getSaveRecord() == null) {
            normalized.setSaveRecord(true);
        }
        return normalized;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> callPredictService(String city, List<String> factors) {
        WebClient client = webClientBuilder.baseUrl(pythonApiUrl).build();
        Map<String, Object> payload = Map.of("city", city, "factors", factors);
        Map<String, Object> response = client.post()
                .uri(pythonPredictPath)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(Map.class)
                .block(Duration.ofMinutes(3));
        if (response == null || response.get("error") != null) {
            throw new IllegalStateException(response == null ? "预测服务未返回结果" : String.valueOf(response.get("error")));
        }
        Object data = response.getOrDefault("data", response);
        Map<String, Object> dataMap = objectMapper.convertValue(data, new TypeReference<Map<String, Object>>() {});
        Object predictions = dataMap.get("predictions");
        if (predictions == null) {
            throw new IllegalStateException("预测服务未返回 predictions");
        }
        return objectMapper.convertValue(predictions, new TypeReference<List<Map<String, Object>>>() {});
    }

    private List<Map<String, Object>> fallbackPredictions(List<String> factors) {
        List<Map<String, Object>> predictions = new ArrayList<>();
        LocalDate start = LocalDate.now().plusDays(1);
        for (int i = 0; i < 7; i++) {
            Map<String, Object> day = new LinkedHashMap<>();
            day.put("date", start.plusDays(i).toString());
            for (String factor : factors) {
                day.put(factor, fallbackValue(factor, i));
            }
            predictions.add(day);
        }
        return predictions;
    }

    private Number fallbackValue(String factor, int dayIndex) {
        return switch (factor) {
            case "AQI" -> 62 + dayIndex * 3;
            case "PM25" -> 38 + dayIndex * 2;
            case "PM10" -> 76 + dayIndex * 4;
            case "SO2" -> 28 + dayIndex;
            case "NO2" -> 44 + dayIndex * 2;
            case "CO" -> Math.round((1.2 + dayIndex * 0.08) * 100.0) / 100.0;
            case "O3" -> 105 + dayIndex * 5;
            default -> 0;
        };
    }

    private String callAiExplanation(RiskAnalyzeResponse response, String fallback) {
        try {
            WebClient client = webClientBuilder.baseUrl(pythonApiUrl).build();
            Map<String, Object> payload = Map.of(
                    "question", buildAiPrompt(response),
                    "mode", "agent"
            );
            @SuppressWarnings("unchecked")
            Map<String, Object> raw = client.post()
                    .uri(pythonChatPath)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block(Duration.ofSeconds(45));
            if (raw == null) {
                return fallback;
            }
            Object answer = raw.get("answer");
            if (answer == null || String.valueOf(answer).isBlank()) {
                return fallback;
            }
            return String.valueOf(answer).trim();
        } catch (Exception e) {
            return fallback;
        }
    }

    private String buildAiPrompt(RiskAnalyzeResponse response) {
        return """
                请作为环境风险研判助手，基于以下空气质量预测结果生成中文研判结论。
                要求：说明成因解释、治理建议、公众提示；表达简洁，适合放在系统页面展示。

                城市：%s
                因子：%s
                综合风险等级：%s
                风险评分：%s
                重点风险因子：%s
                风险日期：%s
                预测明细：%s
                """.formatted(
                response.getCity(),
                response.getFactors(),
                response.getRiskLevel(),
                response.getRiskScore(),
                response.getKeyFactor(),
                response.getRiskDates(),
                toJson(response.getPredictions())
        );
    }

    private String buildFallbackExplanation(RiskAnalyzeResponse response) {
        if ("HIGH".equals(response.getRiskLevel()) || "SEVERE".equals(response.getRiskLevel())) {
            return "预测结果显示 " + response.getKeyFactor() + " 是本次主要风险因子，风险日期集中在 "
                    + response.getRiskDates() + "。建议重点关注颗粒物、臭氧或综合 AQI 的连续升高趋势，并结合气象条件和重点排放源开展复核。";
        }
        if ("MEDIUM".equals(response.getRiskLevel())) {
            return "未来 7 天空气质量存在一定波动，" + response.getKeyFactor() + " 对综合风险贡献较高。建议保持常规监测并关注后续变化。";
        }
        return "未来 7 天预测指标整体处于低风险范围，空气质量趋势相对平稳，可继续保持日常监测。";
    }

    private String buildTrendSummary(String city, RiskScoreCalculator.ScoreResult scoreResult, boolean degraded) {
        String prefix = degraded ? "预测服务暂不可用，系统已使用降级预测数据完成研判。" : "";
        if ("HIGH".equals(scoreResult.getRiskLevel()) || "SEVERE".equals(scoreResult.getRiskLevel())) {
            return prefix + city + "未来 7 天存在较高空气质量风险，重点风险因子为 "
                    + scoreResult.getKeyFactor() + "，风险日期：" + scoreResult.getRiskDates() + "。";
        }
        if ("MEDIUM".equals(scoreResult.getRiskLevel())) {
            return prefix + city + "未来 7 天空气质量存在轻度波动，重点关注因子为 " + scoreResult.getKeyFactor() + "。";
        }
        return prefix + city + "未来 7 天空气质量整体稳定，暂未发现明显高风险日期。";
    }

    private String buildReport(RiskAnalyzeResponse response) {
        return """
                # %s空气质量风险研判报告

                ## 一、风险摘要

                综合风险等级：%s

                风险评分：%s

                重点风险因子：%s

                风险日期：%s

                ## 二、趋势分析

                %s

                ## 三、AI 研判结论

                %s

                ## 四、治理建议

                %s

                ## 五、公众提示

                %s
                """.formatted(
                response.getCity(),
                response.getRiskLevel(),
                response.getRiskScore(),
                response.getKeyFactor(),
                response.getRiskDates(),
                response.getTrendSummary(),
                response.getCauseExplanation(),
                String.join("\n\n", response.getGovernanceSuggestions()),
                response.getPublicAdvice()
        );
    }

    private RiskAnalysisRecord toRecord(RiskAnalyzeResponse response, Long userId) {
        RiskAnalysisRecord record = new RiskAnalysisRecord();
        record.setUserId(userId);
        record.setCity(response.getCity());
        record.setFactors(toJson(response.getFactors()));
        record.setHorizonDays(response.getHorizonDays());
        record.setRiskLevel(response.getRiskLevel());
        record.setRiskScore(response.getRiskScore());
        record.setKeyFactor(response.getKeyFactor());
        record.setConfidence(response.getConfidence());
        record.setPredictionJson(toJson(response.getPredictions()));
        record.setTrendSummary(response.getTrendSummary());
        record.setExplanation(response.getCauseExplanation());
        record.setSuggestions(toJson(response.getGovernanceSuggestions()));
        record.setPublicAdvice(response.getPublicAdvice());
        record.setReportContent(response.getReportContent());
        return record;
    }

    private List<String> parseFactors(String raw) {
        if (raw == null || raw.isBlank()) {
            return DEFAULT_FACTORS;
        }
        return Arrays.stream(raw.split(","))
                .map(String::trim)
                .filter(item -> !item.isBlank())
                .toList();
    }

    private String resolveMode(String raw) {
        if (raw == null || raw.isBlank()) {
            return "STANDARD";
        }
        String mode = raw.trim().toUpperCase(Locale.ROOT);
        if (!List.of("FAST", "STANDARD", "DEEP").contains(mode)) {
            return "STANDARD";
        }
        return mode;
    }

    private String normalizeRiskLevel(String riskLevel) {
        if (riskLevel == null || riskLevel.isBlank()) {
            return null;
        }
        return riskLevel.trim().toUpperCase(Locale.ROOT);
    }

    private boolean canViewAll(User user) {
        return user != null && ("ADMIN".equals(user.getRole()) || "MONITOR".equals(user.getRole()));
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception e) {
            return String.valueOf(value);
        }
    }
}
