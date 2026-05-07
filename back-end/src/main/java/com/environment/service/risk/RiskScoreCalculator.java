package com.environment.service.risk;

import com.environment.pojo.DTO.RiskPredictionDay;
import com.environment.pojo.DTO.RiskTrendItem;
import lombok.Data;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Component
public class RiskScoreCalculator {

    private static final Map<String, Threshold> THRESHOLDS = Map.of(
            "AQI", new Threshold(75, 115, 150),
            "PM25", new Threshold(55, 75, 115),
            "PM10", new Threshold(100, 150, 250),
            "SO2", new Threshold(75, 150, 500),
            "NO2", new Threshold(80, 120, 200),
            "CO", new Threshold(4, 10, 20),
            "O3", new Threshold(120, 160, 200)
    );

    public ScoreResult calculate(List<String> factors, List<Map<String, Object>> rawPredictions) {
        List<String> normalizedFactors = normalizeFactors(factors);
        if (normalizedFactors.isEmpty()) {
            throw new IllegalArgumentException("至少选择一个有效空气因子");
        }

        List<RiskPredictionDay> predictionDays = new ArrayList<>();
        List<RiskTrendItem> trendItems = new ArrayList<>();
        List<String> riskDates = new ArrayList<>();
        int overallScore = 0;
        String overallLevel = "LOW";
        String keyFactor = normalizedFactors.get(0);

        for (Map<String, Object> rawDay : rawPredictions) {
            String date = String.valueOf(rawDay.getOrDefault("date", ""));
            Map<String, Object> values = new LinkedHashMap<>();
            int dayScore = 0;
            String dayLevel = "LOW";
            String mainFactor = normalizedFactors.get(0);
            boolean dayExceed = false;

            for (String factor : normalizedFactors) {
                double value = asDouble(rawDay.get(factor));
                values.put(factor, formatValue(factor, value));

                int factorScore = scoreFor(factor, value);
                String factorLevel = levelForScore(factorScore);
                boolean exceedThreshold = factorScore >= 70;

                RiskTrendItem trendItem = new RiskTrendItem();
                trendItem.setDate(date);
                trendItem.setFactor(factor);
                trendItem.setPredictedValue(formatValue(factor, value));
                trendItem.setRiskLevel(factorLevel);
                trendItem.setRiskScore(factorScore);
                trendItem.setExceedThreshold(exceedThreshold);
                trendItems.add(trendItem);

                if (factorScore > dayScore) {
                    dayScore = factorScore;
                    dayLevel = factorLevel;
                    mainFactor = factor;
                }
                if (exceedThreshold) {
                    dayExceed = true;
                }
            }

            RiskPredictionDay predictionDay = new RiskPredictionDay();
            predictionDay.setDate(date);
            predictionDay.setValues(values);
            predictionDay.setDailyRiskLevel(dayLevel);
            predictionDay.setDailyRiskScore(dayScore);
            predictionDay.setMainFactor(mainFactor);
            predictionDay.setExceedThreshold(dayExceed);
            predictionDays.add(predictionDay);

            if (dayScore >= 70 && !riskDates.contains(date)) {
                riskDates.add(date);
            }
            if (dayScore > overallScore) {
                overallScore = dayScore;
                overallLevel = dayLevel;
                keyFactor = mainFactor;
            }
        }

        ScoreResult result = new ScoreResult();
        result.setRiskLevel(overallLevel);
        result.setRiskScore(overallScore);
        result.setKeyFactor(keyFactor);
        result.setRiskDates(riskDates);
        result.setPredictionDays(predictionDays);
        result.setTrendItems(trendItems);
        return result;
    }

    public List<String> normalizeFactors(List<String> factors) {
        List<String> normalized = new ArrayList<>();
        if (factors == null) {
            return normalized;
        }
        for (String raw : factors) {
            if (raw == null) {
                continue;
            }
            String factor = raw.trim().toUpperCase(Locale.ROOT).replace("PM2.5", "PM25");
            if (THRESHOLDS.containsKey(factor) && !normalized.contains(factor)) {
                normalized.add(factor);
            }
        }
        return normalized;
    }

    public String levelForScore(int score) {
        if (score >= 90) {
            return "SEVERE";
        }
        if (score >= 70) {
            return "HIGH";
        }
        if (score >= 40) {
            return "MEDIUM";
        }
        return "LOW";
    }

    private int scoreFor(String factor, double value) {
        Threshold threshold = THRESHOLDS.get(factor);
        if (threshold == null || value <= 0) {
            return 0;
        }
        if (value < threshold.medium()) {
            return clamp((int) Math.round(value / threshold.medium() * 39), 0, 39);
        }
        if (value < threshold.high()) {
            double ratio = (value - threshold.medium()) / (threshold.high() - threshold.medium());
            return clamp(40 + (int) Math.round(ratio * 29), 40, 69);
        }
        if (value < threshold.severe()) {
            double ratio = (value - threshold.high()) / (threshold.severe() - threshold.high());
            return clamp(70 + (int) Math.round(ratio * 19), 70, 89);
        }
        double ratio = Math.min(1.0, (value - threshold.severe()) / Math.max(threshold.severe(), 1));
        return clamp(90 + (int) Math.round(ratio * 10), 90, 100);
    }

    private Number formatValue(String factor, double value) {
        if ("CO".equals(factor)) {
            return Math.round(value * 100.0) / 100.0;
        }
        return (int) Math.round(value);
    }

    private double asDouble(Object raw) {
        if (raw instanceof Number number) {
            return number.doubleValue();
        }
        if (raw == null) {
            return 0;
        }
        try {
            return Double.parseDouble(String.valueOf(raw));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private record Threshold(double medium, double high, double severe) {
    }

    @Data
    public static class ScoreResult {
        private String riskLevel;
        private Integer riskScore;
        private String keyFactor;
        private List<String> riskDates;
        private List<RiskPredictionDay> predictionDays;
        private List<RiskTrendItem> trendItems;
    }
}
