package com.environment.Initializer;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

@Component
public class RiskModuleInitializer {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @PostConstruct
    public void init() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS risk_analysis_record (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    factors VARCHAR(500) NOT NULL,
                    horizon_days INT DEFAULT 7,
                    risk_level VARCHAR(20) NOT NULL,
                    risk_score INT NOT NULL,
                    key_factor VARCHAR(50),
                    confidence DOUBLE,
                    prediction_json LONGTEXT,
                    trend_summary VARCHAR(1000),
                    explanation LONGTEXT,
                    suggestions LONGTEXT,
                    public_advice VARCHAR(1000),
                    report_content LONGTEXT,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_risk_user_time(user_id, create_time),
                    INDEX idx_risk_city_level(city, risk_level)
                )
                """);
    }
}
