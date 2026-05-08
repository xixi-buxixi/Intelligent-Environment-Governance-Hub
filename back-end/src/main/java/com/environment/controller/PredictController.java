package com.environment.controller;

import com.environment.pojo.Result;
import com.environment.pojo.User;
import com.environment.service.UserService;
import com.environment.util.JwtUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@RestController
@RequestMapping("/predict")
public class PredictController {

    @Value("${python.api.url:http://localhost:5001}")
    private String pythonApiUrl;

    @Value("${python.api.predict-path:/api/predict/air-quality}")
    private String pythonPredictPath;

    @Autowired
    private WebClient.Builder webClientBuilder;

    @Autowired
    private UserService userService;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private static final Map<String, String> RESULT_FACTOR_LABELS = Map.of(
            "AQI", "AQI",
            "PM25", "PM2.5",
            "PM10", "PM10",
            "SO2", "SO2",
            "NO2", "NO2",
            "CO", "CO",
            "O3", "O3"
    );
    private static final DateTimeFormatter FILE_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
            .withZone(ZoneId.systemDefault());
    private static final DateTimeFormatter RESULT_TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final int REQUIRED_PREDICTION_DAYS = 7;

    @Value("${predict.model-valid-days:14}")
    private int modelValidDays;

    @PostMapping("/air-quality")
    public Result<Object> predictAirQuality(@RequestBody PredictRequest request, HttpServletRequest httpRequest) {
        User user = getCurrentUser(httpRequest);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }

        if (request == null || request.getCity() == null || request.getCity().isBlank()) {
            return Result.badRequest("城市不能为空");
        }
        if (request.getFactors() == null || request.getFactors().isEmpty()) {
            return Result.badRequest("至少选择一个空气因子");
        }

        try {
            List<String> requestedFactors = normalizeFactors(String.join(",", request.getFactors()));
            if (requestedFactors.isEmpty()) {
                return Result.badRequest("至少选择一个有效空气因子");
            }

            PredictionFileInspection inspection = inspectResultFiles(requestedFactors);
            if (inspection.missingFactors().isEmpty() && inspection.expiredFactors().isEmpty()) {
                return Result.success(buildResultPayload(
                        request.getCity().trim(),
                        requestedFactors,
                        inspection.factorResults(),
                        inspection.missingFactors(),
                        inspection.expiredFactors(),
                        "result-files",
                        "已存在完整 7 天预测结果，直接展示现有结果文件"
                ));
            }

            Map<String, Object> payload = Map.of(
                    "city", request.getCity().trim(),
                    "factors", requestedFactors,
                    "missingFactors", inspection.missingFactors(),
                    "expiredFactors", inspection.expiredFactors()
            );

            WebClient client = webClientBuilder.baseUrl(pythonApiUrl).build();
            @SuppressWarnings("unchecked")
            Map<String, Object> pythonResp = client.post()
                    .uri(pythonPredictPath)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (pythonResp == null) {
                return Result.error("Python 服务未返回预测结果");
            }
            if (pythonResp.get("error") != null) {
                return Result.error(String.valueOf(pythonResp.get("error")));
            }
            if (pythonResp.get("data") != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> pythonData = objectMapper.convertValue(pythonResp.get("data"), Map.class);
                PredictionFileInspection refreshedInspection = inspectResultFiles(requestedFactors);
                if (!refreshedInspection.factorResults().isEmpty()) {
                    Map<String, Object> resultPayload = buildResultPayload(
                            request.getCity().trim(),
                            requestedFactors,
                            refreshedInspection.factorResults(),
                            refreshedInspection.missingFactors(),
                            refreshedInspection.expiredFactors(),
                            "model-prediction",
                            String.valueOf(pythonData.getOrDefault("statusMessage", "模型预测完成，已读取最新结果文件"))
                    );
                    resultPayload.put("factorStatuses", pythonData.getOrDefault("factorStatuses", List.of()));
                    resultPayload.put("retrainedFactors", pythonData.getOrDefault("retrainedFactors", List.of()));
                    return Result.success(resultPayload);
                }
                return Result.success(pythonData);
            }
            return Result.success(pythonResp);
        } catch (WebClientResponseException e) {
            return Result.error("预测服务调用失败: " + extractPythonError(e));
        } catch (Exception e) {
            return Result.error("模型预测需要启动 Python API 服务（端口 5001）。请先启动 Python 后端后再点击“模型预测”。原始错误: " + e.getMessage());
        }
    }

    @GetMapping("/air-quality/results")
    public Result<Object> getAirQualityResults(
            @RequestParam String city,
            @RequestParam String factors,
            HttpServletRequest httpRequest
    ) {
        User user = getCurrentUser(httpRequest);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }

        if (city == null || city.isBlank()) {
            return Result.badRequest("城市不能为空");
        }
        if (factors == null || factors.isBlank()) {
            return Result.badRequest("至少选择一个空气因子");
        }

        try {
            List<String> requestedFactors = normalizeFactors(factors);
            if (requestedFactors.isEmpty()) {
                return Result.badRequest("至少选择一个有效空气因子");
            }

            PredictionFileInspection inspection = inspectResultFiles(requestedFactors);

            if (inspection.factorResults().isEmpty()) {
                return Result.error("未找到所选空气因子的预测结果文件，请先启动 Python API 后点击“模型预测”生成文件");
            }

            return Result.success(buildResultPayload(
                    city.trim(),
                    requestedFactors,
                    inspection.factorResults(),
                    inspection.missingFactors(),
                    inspection.expiredFactors(),
                    "result-files",
                    "已读取现有预测结果文件"
            ));
        } catch (Exception e) {
            return Result.error("读取预测结果文件失败: " + e.getMessage());
        }
    }

    private PredictionFileInspection inspectResultFiles(List<String> requestedFactors) throws IOException {
        Map<String, FactorResultFile> factorResults = new LinkedHashMap<>();
        List<String> missingFactors = new ArrayList<>();
        List<String> expiredFactors = new ArrayList<>();

        for (String factor : requestedFactors) {
            FactorResultFile resultFile = readFactorResultFile(factor);
            if (resultFile == null || !resultFile.complete()) {
                missingFactors.add(factor);
                continue;
            }
            if (resultFile.modelExpired()) {
                expiredFactors.add(factor);
                continue;
            }
            factorResults.put(factor, resultFile);
        }

        return new PredictionFileInspection(factorResults, missingFactors, expiredFactors);
    }

    private List<String> normalizeFactors(String rawFactors) {
        return Arrays.stream(rawFactors.split(","))
                .map(String::trim)
                .map(String::toUpperCase)
                .map(item -> "PM2.5".equals(item) ? "PM25" : item)
                .filter(RESULT_FACTOR_LABELS::containsKey)
                .distinct()
                .toList();
    }

    private Map<String, Object> buildResultPayload(
            String city,
            List<String> requestedFactors,
            Map<String, FactorResultFile> factorResults,
            List<String> missingFactors,
            List<String> expiredFactors,
            String source,
            String statusMessage
    ) {
        List<String> dates = factorResults.values().stream()
                .flatMap(result -> result.rows().stream().map(ResultRow::date))
                .distinct()
                .sorted()
                .toList();

        List<Map<String, Object>> predictions = new ArrayList<>();
        for (String date : dates) {
            Map<String, Object> oneDay = new LinkedHashMap<>();
            oneDay.put("date", date);
            for (Map.Entry<String, FactorResultFile> entry : factorResults.entrySet()) {
                entry.getValue().rows().stream()
                        .filter(row -> row.date().equals(date))
                        .findFirst()
                        .ifPresent(row -> oneDay.put(entry.getKey(), row.value()));
            }
            predictions.add(oneDay);
        }

        List<Map<String, Object>> resultFiles = factorResults.values().stream()
                .map(result -> {
                    Map<String, Object> file = new LinkedHashMap<>();
                    file.put("factor", result.factor());
                    file.put("fileName", result.fileName());
                    file.put("lastModified", result.lastModified());
                    file.put("accuracy", result.accuracy());
                    file.put("trainingTime", result.trainingTime());
                    file.put("predictionTime", result.predictionTime());
                    file.put("complete", result.complete());
                    file.put("modelExpired", result.modelExpired());
                    return file;
                })
                .toList();

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("city", city);
        payload.put("factors", new ArrayList<>(factorResults.keySet()));
        payload.put("requestedFactors", requestedFactors);
        payload.put("missingFactors", missingFactors);
        payload.put("expiredFactors", expiredFactors);
        payload.put("horizonDays", predictions.size());
        payload.put("startDate", predictions.isEmpty() ? "" : predictions.get(0).get("date"));
        payload.put("historyDaysUsed", 0);
        payload.put("source", source);
        payload.put("statusMessage", statusMessage);
        payload.put("resultFiles", resultFiles);
        payload.put("predictions", predictions);
        return payload;
    }

    private FactorResultFile readFactorResultFile(String factor) throws IOException {
        Path path = resolvePredictResultDir().resolve(factor + "_result.txt");
        if (!Files.exists(path)) {
            return null;
        }

        String content = Files.readString(path, StandardCharsets.UTF_8);
        String label = Pattern.quote(RESULT_FACTOR_LABELS.getOrDefault(factor, factor));
        Pattern rowPattern = Pattern.compile("(\\d{4}-\\d{2}-\\d{2})\\s*\\|\\s*" + label + "\\s*:\\s*([-+]?\\d+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);
        Matcher rowMatcher = rowPattern.matcher(content);
        List<ResultRow> rows = new ArrayList<>();
        while (rowMatcher.find()) {
            rows.add(new ResultRow(rowMatcher.group(1), Double.parseDouble(rowMatcher.group(2))));
        }
        if (rows.size() > 7) {
            rows = rows.subList(rows.size() - 7, rows.size());
        }

        Double accuracy = null;
        Matcher accuracyMatcher = Pattern.compile("Model Accuracy:\\s*([-+]?\\d+(?:\\.\\d+)?)%?").matcher(content);
        if (accuracyMatcher.find()) {
            accuracy = Double.parseDouble(accuracyMatcher.group(1));
        }

        String predictionTime = "";
        Matcher predictionTimeMatcher = Pattern.compile("Prediction Time:\\s*([^\\r\\n]+)").matcher(content);
        if (predictionTimeMatcher.find()) {
            predictionTime = predictionTimeMatcher.group(1).trim();
        }

        String trainingTime = "";
        boolean modelExpired = false;
        Matcher trainingTimeMatcher = Pattern.compile("Training Time:\\s*([^\\r\\n]+)").matcher(content);
        if (trainingTimeMatcher.find()) {
            trainingTime = trainingTimeMatcher.group(1).trim();
            try {
                LocalDateTime trainedAt = LocalDateTime.parse(trainingTime, RESULT_TIME_FORMATTER);
                modelExpired = trainedAt.plusDays(modelValidDays).isBefore(LocalDateTime.now());
            } catch (Exception ignored) {
                modelExpired = false;
            }
        }

        Instant lastModified = Files.getLastModifiedTime(path).toInstant();
        return new FactorResultFile(
                factor,
                path.getFileName().toString(),
                FILE_TIME_FORMATTER.format(lastModified),
                accuracy,
                trainingTime,
                predictionTime,
                rows.size() >= REQUIRED_PREDICTION_DAYS,
                modelExpired,
                rows
        );
    }

    private Path resolvePredictResultDir() {
        Path cwd = Paths.get("").toAbsolutePath().normalize();
        List<Path> candidates = List.of(
                cwd.resolve("back-end-python").resolve("runtime").resolve("predict_models").resolve("results"),
                cwd.resolve("..").resolve("back-end-python").resolve("runtime").resolve("predict_models").resolve("results").normalize()
        );
        return candidates.stream().filter(Files::isDirectory).findFirst().orElse(candidates.get(0));
    }

    private record FactorResultFile(
            String factor,
            String fileName,
            String lastModified,
            Double accuracy,
            String trainingTime,
            String predictionTime,
            Boolean complete,
            Boolean modelExpired,
            List<ResultRow> rows
    ) {
    }

    private record ResultRow(String date, Double value) {
    }

    private record PredictionFileInspection(
            Map<String, FactorResultFile> factorResults,
            List<String> missingFactors,
            List<String> expiredFactors
    ) {
    }

    @SuppressWarnings("unchecked")
    private String extractPythonError(WebClientResponseException e) {
        String body = e.getResponseBodyAsString();
        if (body == null || body.isBlank()) {
            return e.getMessage();
        }
        try {
            Map<String, Object> parsed = objectMapper.readValue(body, Map.class);
            Object error = parsed.get("error");
            if (error != null) {
                return String.valueOf(error);
            }
        } catch (Exception ignored) {
        }
        return body;
    }

    private User getCurrentUser(HttpServletRequest request) {
        String token = request.getHeader("Authorization");
        if (token == null || !token.startsWith("Bearer ")) {
            return null;
        }
        token = token.substring(7);
        try {
            Claims claims = JwtUtil.parseToken(token);
            if (claims == null) {
                return null;
            }

            User user = new User();
            Long userId = claims.get("userId", Long.class);
            if (userId == null) {
                Integer idInt = claims.get("userId", Integer.class);
                if (idInt != null) {
                    userId = idInt.longValue();
                }
            }
            user.setId(userId);
            user.setUsername(claims.get("username", String.class));
            String role = claims.get("role", String.class);
            if (role == null || role.isBlank()) {
                User dbUser = userService.getUserById(userId);
                if (dbUser != null) {
                    role = dbUser.getRole();
                }
            }
            user.setRole(role);
            return user;
        } catch (Exception e) {
            return null;
        }
    }

    public static class PredictRequest {
        private String city;
        private List<String> factors;

        public String getCity() {
            return city;
        }

        public void setCity(String city) {
            this.city = city;
        }

        public List<String> getFactors() {
            return factors;
        }

        public void setFactors(List<String> factors) {
            this.factors = factors;
        }
    }
}
