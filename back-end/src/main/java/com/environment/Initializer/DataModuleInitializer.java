package com.environment.Initializer;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

@Component
public class DataModuleInitializer {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @PostConstruct
    public void init() {
        createDataSourceTable();
        cleanupDuplicateDataSource();
        createFetchRecordTable();
        createAqiDataTable();
        createSpiderRawDataTable();
        seedDataSource();
    }

    private void createDataSourceTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS data_source (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    source_name VARCHAR(100) NOT NULL,
                    source_code VARCHAR(100) NOT NULL,
                    source_url VARCHAR(255),
                    description VARCHAR(500),
                    data_types VARCHAR(1000),
                    status TINYINT DEFAULT 1,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """);
        if (!indexExists("data_source", "uk_data_source_code")) {
            jdbcTemplate.execute("CREATE UNIQUE INDEX uk_data_source_code ON data_source(source_code)");
        }
    }

    private void cleanupDuplicateDataSource() {
        // 先按 source_code 去重（保留较早创建的一条）
        jdbcTemplate.update("""
                DELETE t1 FROM data_source t1
                INNER JOIN data_source t2
                    ON t1.source_code = t2.source_code
                   AND t1.id > t2.id
                """);
        // 再按 source_name + source_url 去重，兜底清理历史重复数据
        jdbcTemplate.update("""
                DELETE t1 FROM data_source t1
                INNER JOIN data_source t2
                    ON t1.source_name = t2.source_name
                   AND IFNULL(t1.source_url,'') = IFNULL(t2.source_url,'')
                   AND t1.id > t2.id
                """);
    }

    private void createFetchRecordTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS data_fetch_record (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    source_id BIGINT,
                    city VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    data_type VARCHAR(100),
                    file_name VARCHAR(255),
                    file_path VARCHAR(255),
                    record_count INT DEFAULT 0,
                    fetch_date DATE NOT NULL,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """);
    }

    private void createAqiDataTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS aqi_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    province VARCHAR(50),
                    city VARCHAR(50),
                    date DATE,
                    Quality VARCHAR(255),
                    AQI INT,
                    AQI_Rank INT,
                    PM25 INT,
                    PM10 INT,
                    SO2 INT,
                    NO2 INT,
                    CO FLOAT,
                    O3 INT,
                    UNIQUE KEY unique_record(province, city, date)
                )
                """);
    }

    private void createSpiderRawDataTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS spider_raw_data (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    source_code VARCHAR(100) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    data_date DATE,
                    data_json JSON NOT NULL,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_spider_raw_source_city_date(source_code, city, data_date)
                )
                """);
    }

    private boolean indexExists(String tableName, String indexName) {
        Integer count = jdbcTemplate.queryForObject(
                """
                SELECT COUNT(1)
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = ?
                  AND index_name = ?
                """,
                Integer.class,
                tableName,
                indexName
        );
        return count != null && count > 0;
    }

    private void seedDataSource() {
        String allTypes = "[\"AQI\",\"AQI_RANK\",\"QUALITY\",\"PM25\",\"PM10\",\"SO2\",\"NO2\",\"CO\",\"O3\"]";
        String weatherTypes = "[\"TEMP_HIGH\",\"TEMP_LOW\",\"WEATHER\",\"WIND\",\"HUMIDITY\"]";
        String newsTypes = "[\"TITLE\",\"PUBLISH_TIME\",\"SOURCE\",\"URL\"]";

        upsertDataSource(
                "空气质量历史数据（天气后报）",
                "aqi_history",
                "https://www.tianqihoubao.com",
                "来源：天气后报历史空气质量公开数据，覆盖城市日级空气质量指标。",
                allTypes
        );

        upsertDataSource(
                "历史气象数据",
                "weather_history",
                "https://www.tianqihoubao.com",
                "来源：天气后报历史天气页面，覆盖温度、天气、风力等。",
                weatherTypes
        );

        upsertDataSource(
                "生态环境新闻",
                "env_news",
                "http://sthjj.yichun.gov.cn/ycssthjj/",
                "来源：宜春生态环境局公开新闻栏目。",
                newsTypes
        );

        // 清理重复/过渡/不再保留来源，避免页面出现不合规站点
        jdbcTemplate.update("""
                DELETE FROM data_source
                WHERE source_code IN (
                    'aqi_history_ext','aqi_city_rank','aqi_realtime','aqi_aggregated',
                    'aqi_search','aqi_live','city_aqi','company_monitor','water_quality'
                )
                """);
    }

    private void upsertDataSource(String sourceName, String sourceCode, String sourceUrl, String description, String dataTypes) {
        jdbcTemplate.update("""
                UPDATE data_source
                SET source_name = ?,
                    source_url = ?,
                    description = ?,
                    data_types = ?,
                    status = 1
                WHERE source_code = ?
                """,
                sourceName,
                sourceUrl,
                description,
                dataTypes,
                sourceCode
        );

        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM data_source WHERE source_code = ?",
                Integer.class,
                sourceCode
        );
        if (count == null || count == 0) {
            jdbcTemplate.update("""
                    INSERT INTO data_source(source_name, source_code, source_url, description, data_types, status)
                    VALUES (?,?,?,?,?,?)
                    """,
                    sourceName,
                    sourceCode,
                    sourceUrl,
                    description,
                    dataTypes,
                    1
            );
        }
    }
}
