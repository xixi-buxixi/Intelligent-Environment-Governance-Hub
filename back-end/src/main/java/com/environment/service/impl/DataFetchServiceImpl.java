package com.environment.service.impl;

import com.environment.enums.RoleEnum;
import com.environment.mapper.AqiDataMapper;
import com.environment.mapper.DataFetchRecordMapper;
import com.environment.pojo.AqiDataRecord;
import com.environment.pojo.DataSource;
import com.environment.pojo.DataFetchRecord;
import com.environment.pojo.DTO.DataFetchRequestDTO;
import com.environment.pojo.DTO.UserFetchLimitDTO;
import com.environment.service.DataFetchService;
import com.environment.service.DataSourceService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class DataFetchServiceImpl implements DataFetchService {

    private static final int DAILY_LIMIT = 3;
    private static final String REDIS_LAST_CRAWL_TIME_KEY = "data:crawl:last_success_time";
    private static final DateTimeFormatter DATETIME_FMT = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

    @Autowired
    private DataFetchRecordMapper dataFetchRecordMapper;

    @Autowired
    private AqiDataMapper aqiDataMapper;

    @Autowired
    private DataSourceService dataSourceService;

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    @Autowired
    private WebClient.Builder webClientBuilder;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Value("${python.api.url:http://localhost:5001}")
    private String pythonApiUrl;

    @Value("${python.api.spider-fetch-path:/api/spider/fetch}")
    private String pythonSpiderFetchPath;

    @Value("${data.fetch.crawl.max-gap-days:7}")
    private int crawlMaxGapDays;

    @Value("${data.fetch.preview-limit:50}")
    private int defaultPreviewLimit;

    @Value("${data.fetch.crawl.notify-url:http://localhost:8080/api/data/crawl/notify}")
    private String crawlNotifyUrl;

    @Value("${spring.datasource.url:}")
    private String jdbcUrl;

    @Value("${spring.datasource.username:root}")
    private String dbUser;

    @Value("${spring.datasource.password:}")
    private String dbPassword;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public UserFetchLimitDTO getUserFetchLimit(Long userId, String role) {
        UserFetchLimitDTO limitDTO = new UserFetchLimitDTO();
        limitDTO.setRole(role);
        limitDTO.setCurrentDate(LocalDate.now());

        if (RoleEnum.ADMIN.getCode().equals(role) || RoleEnum.MONITOR.getCode().equals(role)) {
            limitDTO.setHasLimit(false);
            limitDTO.setDailyLimit(-1);
            limitDTO.setUsedCount(0);
            limitDTO.setRemainingCount(-1);
            return limitDTO;
        }

        limitDTO.setHasLimit(true);
        limitDTO.setDailyLimit(DAILY_LIMIT);
        int usedCount = dataFetchRecordMapper.countByUserIdAndDate(userId, LocalDate.now());
        limitDTO.setUsedCount(usedCount);
        limitDTO.setRemainingCount(Math.max(0, DAILY_LIMIT - usedCount));
        return limitDTO;
    }

    @Override
    public boolean canFetchData(Long userId, String role) {
        if (RoleEnum.ADMIN.getCode().equals(role) || RoleEnum.MONITOR.getCode().equals(role)) {
            return true;
        }
        int usedCount = dataFetchRecordMapper.countByUserIdAndDate(userId, LocalDate.now());
        return usedCount < DAILY_LIMIT;
    }

    @Override
    public Map<String, Object> fetchDataPreview(DataFetchRequestDTO requestDTO, Long userId, String role) {
        validateRequest(requestDTO);
        if (!canFetchData(userId, role)) {
            throw new RuntimeException("今日获取次数已用完，请明天再试");
        }

        DataSource source = requestDTO.getSourceId() == null ? null : dataSourceService.getDataSourceById(requestDTO.getSourceId());
        String sourceCode = source == null ? "aqi_history" : source.getSourceCode();
        if (!isAqiSource(sourceCode)) {
            return fetchNonAqiPreview(requestDTO, userId, sourceCode);
        }

        LocalDate startDate = requestDTO.getStartDate();
        LocalDate endDate = requestDTO.getEndDate();
        String city = requestDTO.getCity();
        int requiredDays = (int) ChronoUnit.DAYS.between(startDate, endDate) + 1;
        int coveredDays = aqiDataMapper.countDistinctDatesInRange(city, startDate, endDate);

        boolean crawled = false;
        LocalDateTime lastCrawlTime = getLastCrawlTime();

        if (coveredDays < requiredDays) {
            boolean tooOld = lastCrawlTime == null || Duration.between(lastCrawlTime, LocalDateTime.now()).toDays() > crawlMaxGapDays;
            if (tooOld && !Boolean.TRUE.equals(requestDTO.getForceUpdate())) {
                Map<String, Object> needConfirm = new HashMap<>();
                needConfirm.put("needConfirm", true);
                needConfirm.put("lastCrawlTime", lastCrawlTime == null ? null : lastCrawlTime.format(DATETIME_FMT));
                needConfirm.put("message", "距离最近一次爬虫已超过" + crawlMaxGapDays + "天，继续获取可能等待较长时间，是否继续？");
                return needConfirm;
            }

            triggerSpiderFetch(requestDTO);
            crawled = true;
            coveredDays = aqiDataMapper.countDistinctDatesInRange(city, startDate, endDate);
            lastCrawlTime = getLastCrawlTime();
        }

        int previewLimit = requestDTO.getPreviewLimit() != null && requestDTO.getPreviewLimit() > 0
                ? requestDTO.getPreviewLimit() : defaultPreviewLimit;
        List<AqiDataRecord> previewRows = aqiDataMapper.selectPreviewByRange(city, startDate, endDate, previewLimit);
        int totalRows = aqiDataMapper.countRowsInRange(city, startDate, endDate);

        if (previewRows == null || previewRows.isEmpty() || totalRows <= 0) {
            throw new RuntimeException("获取失败：未获取到可展示数据，请检查日期范围或稍后重试");
        }

        saveFetchRecord(requestDTO, userId, totalRows);

        Map<String, Object> result = new HashMap<>();
        result.put("needConfirm", false);
        result.put("crawled", crawled);
        result.put("recordCount", totalRows);
        result.put("coveredDays", coveredDays);
        result.put("requiredDays", requiredDays);
        result.put("lastCrawlTime", lastCrawlTime == null ? null : lastCrawlTime.format(DATETIME_FMT));
        result.put("previewRows", previewRows);
        return result;
    }

    private Map<String, Object> fetchNonAqiPreview(DataFetchRequestDTO requestDTO, Long userId, String sourceCode) {
        LocalDate startDate = requestDTO.getStartDate();
        LocalDate endDate = requestDTO.getEndDate();
        String city = requestDTO.getCity();

        LocalDateTime lastCrawlTime = getLastCrawlTime();
        boolean crawled = false;

        int beforeCount = countSpiderRawRows(sourceCode, city, startDate, endDate);
        if (beforeCount <= 0) {
            boolean tooOld = lastCrawlTime == null || Duration.between(lastCrawlTime, LocalDateTime.now()).toDays() > crawlMaxGapDays;
            if (tooOld && !Boolean.TRUE.equals(requestDTO.getForceUpdate())) {
                Map<String, Object> needConfirm = new HashMap<>();
                needConfirm.put("needConfirm", true);
                needConfirm.put("lastCrawlTime", lastCrawlTime == null ? null : lastCrawlTime.format(DATETIME_FMT));
                needConfirm.put("message", "当前来源暂无近期缓存，触发抓取可能等待较长时间，是否继续？");
                return needConfirm;
            }
            triggerSpiderFetch(requestDTO);
            crawled = true;
            lastCrawlTime = getLastCrawlTime();
        }

        int previewLimit = requestDTO.getPreviewLimit() != null && requestDTO.getPreviewLimit() > 0
                ? requestDTO.getPreviewLimit() : defaultPreviewLimit;
        List<Map<String, Object>> rows = selectSpiderRawPreview(sourceCode, city, startDate, endDate, previewLimit, requestDTO.getDataType());
        int totalRows = countSpiderRawRows(sourceCode, city, startDate, endDate);

        if (rows.isEmpty() || totalRows <= 0) {
            throw new RuntimeException("获取失败：该来源暂无可展示数据，请调整时间范围后重试");
        }

        saveFetchRecord(requestDTO, userId, totalRows);

        Map<String, Object> result = new HashMap<>();
        result.put("needConfirm", false);
        result.put("crawled", crawled);
        result.put("recordCount", totalRows);
        result.put("coveredDays", totalRows);
        result.put("requiredDays", (int) ChronoUnit.DAYS.between(startDate, endDate) + 1);
        result.put("lastCrawlTime", lastCrawlTime == null ? null : lastCrawlTime.format(DATETIME_FMT));
        result.put("previewRows", rows);
        return result;
    }

    @Override
    public void exportCsv(DataFetchRequestDTO requestDTO, HttpServletResponse response) throws IOException {
        validateRequest(requestDTO);
        List<AqiDataRecord> rows = aqiDataMapper.selectAllByRange(requestDTO.getCity(), requestDTO.getStartDate(), requestDTO.getEndDate());

        String fileName = String.format("%s_AQI_%s_%s.csv",
                requestDTO.getCity(),
                requestDTO.getStartDate(),
                requestDTO.getEndDate());

        response.setContentType("text/csv; charset=UTF-8");
        response.setHeader("Content-Disposition", "attachment; filename=" + fileName);
        response.setCharacterEncoding("UTF-8");

        OutputStream outputStream = response.getOutputStream();
        outputStream.write(0xEF);
        outputStream.write(0xBB);
        outputStream.write(0xBF);

        OutputStreamWriter writer = new OutputStreamWriter(outputStream, StandardCharsets.UTF_8);
        writer.write("省份,城市,日期,质量等级,AQI,排名,PM2.5,PM10,SO2,NO2,CO,O3\n");
        for (AqiDataRecord row : rows) {
            writer.write(String.format("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
                    safe(row.getProvince()),
                    safe(row.getCity()),
                    row.getDate() == null ? "" : row.getDate().toString(),
                    safe(row.getQuality()),
                    safe(row.getAqi()),
                    safe(row.getAqiRank()),
                    safe(row.getPm25()),
                    safe(row.getPm10()),
                    safe(row.getSo2()),
                    safe(row.getNo2()),
                    safe(row.getCo()),
                    safe(row.getO3())
            ));
        }
        writer.flush();
        writer.close();
    }

    @Override
    public void handleCrawlNotify(String status, String message, String finishedAt) {
        if (!"success".equalsIgnoreCase(status)) {
            return;
        }
        LocalDateTime doneAt;
        try {
            doneAt = (finishedAt == null || finishedAt.isBlank())
                    ? LocalDateTime.now()
                    : LocalDateTime.parse(finishedAt, DATETIME_FMT);
        } catch (Exception e) {
            doneAt = LocalDateTime.now();
        }
        stringRedisTemplate.opsForValue().set(REDIS_LAST_CRAWL_TIME_KEY, doneAt.format(DATETIME_FMT));
    }

    @Override
    public List<DataFetchRecord> getUserFetchRecords(Long userId) {
        return dataFetchRecordMapper.selectByUserId(userId);
    }

    @Override
    public List<DataFetchRecord> getAllFetchRecords() {
        return dataFetchRecordMapper.selectAllWithUserInfo();
    }

    private void triggerSpiderFetch(DataFetchRequestDTO requestDTO) {
        Map<String, Object> body = new HashMap<>();
        DataSource source = requestDTO.getSourceId() == null ? null : dataSourceService.getDataSourceById(requestDTO.getSourceId());
        body.put("city", requestDTO.getCity());
        body.put("startDate", requestDTO.getStartDate().toString());
        body.put("endDate", requestDTO.getEndDate().toString());
        body.put("dataType", requestDTO.getDataType());
        body.put("sourceCode", source == null ? "aqi_history" : source.getSourceCode());
        body.put("callbackUrl", crawlNotifyUrl);
        body.put("dbName", parseDbNameFromJdbcUrl(jdbcUrl));
        body.put("dbUser", dbUser);
        body.put("dbPassword", dbPassword);

        WebClient webClient = webClientBuilder.baseUrl(pythonApiUrl).build();
        try {
            webClient.post()
                    .uri(pythonSpiderFetchPath)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block(Duration.ofMinutes(20));
        } catch (WebClientResponseException e) {
            String responseBody = e.getResponseBodyAsString();
            String detail = (responseBody == null || responseBody.isBlank())
                    ? e.getMessage()
                    : responseBody;
            throw new RuntimeException("爬虫更新失败：" + detail);
        } catch (Exception e) {
            throw new RuntimeException("爬虫更新失败：" + e.getMessage());
        }
    }

    private boolean isAqiSource(String sourceCode) {
        if (sourceCode == null) {
            return true;
        }
        return switch (sourceCode) {
            case "aqi_history", "aqi_search", "aqi_live", "city_aqi",
                    "aqi_history_ext", "aqi_city_rank", "aqi_realtime", "aqi_aggregated" -> true;
            default -> false;
        };
    }

    private int countSpiderRawRows(String sourceCode, String city, LocalDate startDate, LocalDate endDate) {
        Integer cnt = jdbcTemplate.queryForObject(
                """
                SELECT COUNT(*)
                FROM spider_raw_data
                WHERE source_code = ?
                  AND city = ?
                  AND data_date BETWEEN ? AND ?
                """,
                Integer.class,
                sourceCode,
                city,
                startDate,
                endDate
        );
        return cnt == null ? 0 : cnt;
    }

    private List<Map<String, Object>> selectSpiderRawPreview(String sourceCode,
                                                             String city,
                                                             LocalDate startDate,
                                                             LocalDate endDate,
                                                             int limit,
                                                             String rawDataTypes) {
        List<String> selectedTypes = Arrays.stream(rawDataTypes == null ? new String[0] : rawDataTypes.split(","))
                .map(String::trim)
                .filter(s -> !s.isBlank())
                .collect(Collectors.toList());

        return jdbcTemplate.query(
                """
                SELECT data_date, data_json
                FROM spider_raw_data
                WHERE source_code = ?
                  AND city = ?
                  AND data_date BETWEEN ? AND ?
                ORDER BY data_date DESC, id DESC
                LIMIT ?
                """,
                (rs, rowNum) -> {
                    String dataDate = rs.getDate("data_date") == null ? "" : rs.getDate("data_date").toString();
                    String json = rs.getString("data_json");
                    Map<String, Object> parsed = parseJsonMap(json);
                    Map<String, Object> one = new LinkedHashMap<>();
                    one.put("date", dataDate);
                    one.put("city", city);
                    for (String type : selectedTypes) {
                        String prop = typeToProp(type);
                        Object val = parsed.get(prop);
                        if (val == null) {
                            val = parsed.get(type);
                        }
                        if (val == null) {
                            val = parsed.get(type.toLowerCase());
                        }
                        one.put(prop, val);
                    }
                    return one;
                },
                sourceCode, city, startDate, endDate, limit
        );
    }

    private Map<String, Object> parseJsonMap(String json) {
        if (json == null || json.isBlank()) {
            return new HashMap<>();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            return new HashMap<>();
        }
    }

    private String typeToProp(String type) {
        if (type == null || type.isBlank()) {
            return "";
        }
        String[] arr = type.toLowerCase().split("_");
        if (arr.length == 0) {
            return type.toLowerCase();
        }
        StringBuilder sb = new StringBuilder(arr[0]);
        for (int i = 1; i < arr.length; i++) {
            String part = arr[i];
            if (part.isEmpty()) {
                continue;
            }
            sb.append(Character.toUpperCase(part.charAt(0)));
            if (part.length() > 1) {
                sb.append(part.substring(1));
            }
        }
        return sb.toString();
    }

    private void saveFetchRecord(DataFetchRequestDTO requestDTO, Long userId, Integer count) {
        DataFetchRecord record = new DataFetchRecord();
        record.setUserId(userId);
        record.setSourceId(requestDTO.getSourceId() == null ? 1L : requestDTO.getSourceId());
        record.setCity(requestDTO.getCity());
        record.setStartDate(requestDTO.getStartDate());
        record.setEndDate(requestDTO.getEndDate());
        record.setDataType(requestDTO.getDataType());
        record.setFileName(null);
        record.setRecordCount(count);
        record.setFetchDate(LocalDate.now());
        dataFetchRecordMapper.insert(record);
    }

    private LocalDateTime getLastCrawlTime() {
        String value = stringRedisTemplate.opsForValue().get(REDIS_LAST_CRAWL_TIME_KEY);
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return LocalDateTime.parse(value, DATETIME_FMT);
        } catch (Exception e) {
            return null;
        }
    }

    private void validateRequest(DataFetchRequestDTO requestDTO) {
        if (requestDTO == null || requestDTO.getCity() == null || requestDTO.getCity().isBlank()) {
            throw new IllegalArgumentException("城市不能为空");
        }
        if (requestDTO.getStartDate() == null || requestDTO.getEndDate() == null) {
            throw new IllegalArgumentException("日期范围不能为空");
        }
        if (requestDTO.getStartDate().isAfter(requestDTO.getEndDate())) {
            throw new IllegalArgumentException("起始日期不能晚于终止日期");
        }
    }

    private String parseDbNameFromJdbcUrl(String url) {
        if (url == null || url.isBlank()) {
            return "environment_hub";
        }
        try {
            String raw = url;
            if (raw.startsWith("jdbc:")) {
                raw = raw.substring(5);
            }
            java.net.URI uri = java.net.URI.create(raw);
            String path = uri.getPath();
            if (path == null || path.isBlank() || "/".equals(path)) {
                return "environment_hub";
            }
            String db = path.startsWith("/") ? path.substring(1) : path;
            return db.isBlank() ? "environment_hub" : db;
        } catch (Exception e) {
            return "environment_hub";
        }
    }

    private String safe(Object value) {
        return value == null ? "" : String.valueOf(value).replace(",", "，");
    }
}
