package com.environment.service.risk;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RiskScoreCalculatorTest {

    @Test
    void calculatePicksHighestDailyRiskAndRiskDates() {
        RiskScoreCalculator calculator = new RiskScoreCalculator();

        RiskScoreCalculator.ScoreResult result = calculator.calculate(
                List.of("AQI", "PM25", "O3"),
                List.of(
                        Map.of("date", "2026-05-07", "AQI", 68, "PM25", 45, "O3", 110),
                        Map.of("date", "2026-05-08", "AQI", 98, "PM25", 84, "O3", 150)
                )
        );

        assertEquals("HIGH", result.getRiskLevel());
        assertEquals("PM25", result.getKeyFactor());
        assertEquals(List.of("2026-05-08"), result.getRiskDates());
        assertTrue(result.getRiskScore() >= 70 && result.getRiskScore() < 90);
        assertEquals(2, result.getPredictionDays().size());
        assertEquals("LOW", result.getPredictionDays().get(0).getDailyRiskLevel());
        assertEquals("HIGH", result.getPredictionDays().get(1).getDailyRiskLevel());
    }

    @Test
    void calculateReturnsLowRiskWhenValuesStayBelowMediumThresholds() {
        RiskScoreCalculator calculator = new RiskScoreCalculator();

        RiskScoreCalculator.ScoreResult result = calculator.calculate(
                List.of("AQI", "PM25"),
                List.of(
                        Map.of("date", "2026-05-07", "AQI", 42, "PM25", 22),
                        Map.of("date", "2026-05-08", "AQI", 50, "PM25", 30)
                )
        );

        assertEquals("LOW", result.getRiskLevel());
        assertEquals("AQI", result.getKeyFactor());
        assertTrue(result.getRiskScore() < 40);
        assertTrue(result.getRiskDates().isEmpty());
        assertFalse(result.getPredictionDays().get(0).getExceedThreshold());
    }
}
