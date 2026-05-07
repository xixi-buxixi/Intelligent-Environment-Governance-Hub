package com.environment.controller;

import com.environment.pojo.Result;
import com.environment.pojo.User;
import com.environment.pojo.UserContext;
import com.environment.service.UserService;
import com.environment.service.VectorStoreService;
import com.environment.util.CaptchaUtil;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import org.yaml.snakeyaml.Yaml;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * 系统控制器
 * 处理系统相关请求
 */
@RestController
@RequestMapping("/system")
public class SystemController {
    private static final Set<String> EDITABLE_EXTENSIONS = Set.of("md", "txt", "markdown", "json", "csv", "log", "yaml", "yml");

    private final UserService userService;
    private final VectorStoreService vectorStoreService;
    private final WebClient.Builder webClientBuilder;

    @Value("${knowledge.base-path}")
    private String knowledgeBasePath;

    @Value("${python.api.url:http://localhost:5001}")
    private String pythonApiUrl;

    public SystemController(UserService userService,
                            VectorStoreService vectorStoreService,
                            WebClient.Builder webClientBuilder) {
        this.userService = userService;
        this.vectorStoreService = vectorStoreService;
        this.webClientBuilder = webClientBuilder;
    }

    /**
     * 健康检查
     * @return 系统状态
     */
    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        Map<String, Object> data = new HashMap<>();
        data.put("status", "UP");
        data.put("timestamp", System.currentTimeMillis());
        data.put("message", "智能环境治理中枢平台运行正常");
        return Result.success(data);
    }

    /**
     * 获取系统信息
     * @return 系统信息
     */
    @GetMapping("/info")
    public Result<Map<String, Object>> getSystemInfo() {
        Map<String, Object> data = new HashMap<>();
        data.put("name", "智能环境治理中枢平台");
        data.put("version", "1.0.0");
        data.put("description", "Intelligent Environment Governance Hub");
        data.put("author", "Environment Team");
        return Result.success(data);
    }

    /**
     * 获取验证码（简化版，返回数字验证码）
     * @param request HTTP请求
     * @return 验证码
     */
    @GetMapping("/captcha")
    public Result<Map<String, String>> getCaptcha(HttpServletRequest request) {
        String captcha = CaptchaUtil.generateCaptcha();
        HttpSession session = request.getSession();
        session.setAttribute("captcha", captcha);
        // 设置验证码有效期（5分钟）
        session.setMaxInactiveInterval(300);

        Map<String, String> data = new HashMap<>();
        data.put("captcha", captcha);

        return Result.success(data);
    }

    @PostMapping("/user/updateRole")
    public Result<String> updateUserRole(@RequestBody Map<String, Object> params) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可操作");
        }
        Long userId = Long.valueOf(params.get("userId").toString());
        String newRole = params.get("newRole").toString();
        String password = params.get("password").toString();

        String s = userService.updateUserRole(userId, newRole, password);
        if ("权限修改成功".equals(s)) {
            return Result.success(s);
        } else {
            return Result.badRequest(s);
        }
    }

    @GetMapping("/config/agent")
    public Result<Map<String, Object>> getAgentConfig() {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可查看配置");
        }
        try {
            Map<String, String> env = readEnvFile(getPythonEnvPath());
            Map<String, Object> data = new HashMap<>();
            data.put("llmModel", env.getOrDefault("LLM_MODEL", "qwen3.5-35b-a3b"));
            data.put("temperature", parseDouble(env.getOrDefault("LLM_TEMPERATURE", "0.7"), 0.7));
            data.put("maxIterations", parseInt(env.getOrDefault("AGENT_MAX_ITERATIONS", "6"), 6));
            data.put("maxRetries", parseInt(env.getOrDefault("AGENT_MAX_RETRIES", "3"), 3));
            data.put("maxHistory", parseInt(env.getOrDefault("AGENT_MAX_HISTORY", "10"), 10));
            data.put("enableReflection", Boolean.parseBoolean(env.getOrDefault("AGENT_ENABLE_REFLECTION", "true")));
            return Result.success(data);
        } catch (Exception e) {
            return Result.error("读取Agent配置失败: " + e.getMessage());
        }
    }

    @PutMapping("/config/agent")
    public Result<String> updateAgentConfig(@RequestBody Map<String, Object> body) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可修改配置");
        }
        try {
            Map<String, String> updates = new LinkedHashMap<>();
            updates.put("LLM_MODEL", String.valueOf(body.getOrDefault("llmModel", "qwen3.5-35b-a3b")));
            updates.put("LLM_TEMPERATURE", String.valueOf(body.getOrDefault("temperature", "0.7")));
            updates.put("AGENT_MAX_ITERATIONS", String.valueOf(body.getOrDefault("maxIterations", "6")));
            updates.put("AGENT_MAX_RETRIES", String.valueOf(body.getOrDefault("maxRetries", "3")));
            updates.put("AGENT_MAX_HISTORY", String.valueOf(body.getOrDefault("maxHistory", "10")));
            updates.put("AGENT_ENABLE_REFLECTION", String.valueOf(body.getOrDefault("enableReflection", "true")));
            updateEnvFile(getPythonEnvPath(), updates);
            return Result.success("Agent配置已保存（Python服务重启后生效）", null);
        } catch (Exception e) {
            return Result.error("保存Agent配置失败: " + e.getMessage());
        }
    }

    @GetMapping("/config/rag")
    public Result<Map<String, Object>> getRagConfig() {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可查看配置");
        }
        try {
            Path appYaml = getBackendAppYamlPath();
            Map<String, Object> yamlMap = readYaml(appYaml);
            Map<String, String> env = readEnvFile(getPythonEnvPath());

            Map<String, Object> langchain = new HashMap<>();
            langchain.put("retrieveTopK", parseInt(env.getOrDefault("RETRIEVE_TOP_K", "3"), 3));
            langchain.put("chunkSize", parseInt(env.getOrDefault("CHUNK_SIZE", "500"), 500));
            langchain.put("chunkOverlap", parseInt(env.getOrDefault("CHUNK_OVERLAP", "100"), 100));
            Path langchainKnowledgePath = resolvePythonKnowledgePath(env.getOrDefault("KNOWLEDGE_PATH", "./data/knowledge"));
            langchain.put("knowledgePath", langchainKnowledgePath.toString());
            langchain.put("files", listKnowledgeFiles(langchainKnowledgePath));

            Map<String, Object> langchain4j = new HashMap<>();
            langchain4j.put("chunkSize", readYamlInt(yamlMap, "knowledge.chunk-size", 500));
            langchain4j.put("chunkOverlap", readYamlInt(yamlMap, "knowledge.chunk-overlap", 100));
            langchain4j.put("maxResults", readYamlInt(yamlMap, "assistant.retriever.max-results", 3));
            langchain4j.put("minScore", readYamlDouble(yamlMap, "assistant.retriever.min-score", 0.6));
            langchain4j.put("memoryMaxMessages", readYamlInt(yamlMap, "assistant.memory.max-messages", 20));
            Path langchain4jKnowledgePath = Paths.get(knowledgeBasePath);
            langchain4j.put("knowledgePath", langchain4jKnowledgePath.toString());
            langchain4j.put("files", listKnowledgeFiles(langchain4jKnowledgePath));

            Map<String, Object> data = new HashMap<>();
            data.put("langchain", langchain);
            data.put("langchain4j", langchain4j);
            return Result.success(data);
        } catch (Exception e) {
            return Result.error("读取RAG配置失败: " + e.getMessage());
        }
    }

    @PutMapping("/config/rag/langchain")
    public Result<String> updateLangchainRagConfig(@RequestBody Map<String, Object> body) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可修改配置");
        }
        try {
            Map<String, String> updates = new LinkedHashMap<>();
            updates.put("RETRIEVE_TOP_K", String.valueOf(body.getOrDefault("retrieveTopK", "3")));
            updates.put("CHUNK_SIZE", String.valueOf(body.getOrDefault("chunkSize", "500")));
            updates.put("CHUNK_OVERLAP", String.valueOf(body.getOrDefault("chunkOverlap", "100")));
            updateEnvFile(getPythonEnvPath(), updates);
            return Result.success("LangChain RAG配置已保存（Python服务重启后生效）", null);
        } catch (Exception e) {
            return Result.error("保存LangChain RAG配置失败: " + e.getMessage());
        }
    }

    @PutMapping("/config/rag/langchain4j")
    public Result<String> updateLangchain4jRagConfig(@RequestBody Map<String, Object> body) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可修改配置");
        }
        try {
            Path appYaml = getBackendAppYamlPath();
            Map<String, Object> yaml = readYaml(appYaml);
            writeYamlPath(yaml, "knowledge.chunk-size", body.getOrDefault("chunkSize", 500));
            writeYamlPath(yaml, "knowledge.chunk-overlap", body.getOrDefault("chunkOverlap", 100));
            writeYamlPath(yaml, "assistant.retriever.max-results", body.getOrDefault("maxResults", 3));
            writeYamlPath(yaml, "assistant.retriever.min-score", body.getOrDefault("minScore", 0.6));
            writeYamlPath(yaml, "assistant.memory.max-messages", body.getOrDefault("memoryMaxMessages", 20));
            saveYaml(appYaml, yaml);
            return Result.success("LangChain4j RAG配置已保存（Java服务重启后生效）", null);
        } catch (Exception e) {
            return Result.error("保存LangChain4j RAG配置失败: " + e.getMessage());
        }
    }

    @GetMapping("/config/rag/knowledge-files")
    public Result<List<Map<String, Object>>> listKnowledgeFile(@RequestParam("engine") String engine) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可查看知识库");
        }
        try {
            return Result.success(listKnowledgeFiles(resolveKnowledgePath(engine)));
        } catch (Exception e) {
            return Result.error("读取知识库文件失败: " + e.getMessage());
        }
    }

    @PostMapping(value = "/config/rag/knowledge-files", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Result<String> uploadKnowledgeFile(@RequestParam("engine") String engine,
                                              @RequestPart("file") MultipartFile file) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可上传知识库");
        }
        if (file == null || file.isEmpty() || !StringUtils.hasText(file.getOriginalFilename())) {
            return Result.badRequest("文件不能为空");
        }
        try {
            String safeName = safeFileName(file.getOriginalFilename());
            Path targetDir = resolveKnowledgePath(engine);
            Files.createDirectories(targetDir);
            Path target = targetDir.resolve(safeName);
            Files.write(target, file.getBytes(), StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);

            if ("langchain4j".equalsIgnoreCase(engine)) {
                vectorStoreService.processDocument(target);
            } else {
                triggerPythonRebuild();
            }
            return Result.success("文件上传成功", null);
        } catch (Exception e) {
            return Result.error("上传文件失败: " + e.getMessage());
        }
    }

    @DeleteMapping("/config/rag/knowledge-files")
    public Result<String> deleteKnowledgeFile(@RequestParam("engine") String engine,
                                              @RequestParam("fileName") String fileName) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可删除知识库");
        }
        if (!StringUtils.hasText(fileName)) {
            return Result.badRequest("文件名不能为空");
        }
        try {
            Path dir = resolveKnowledgePath(engine);
            Path file = dir.resolve(safeFileName(fileName)).normalize();
            if (!file.startsWith(dir.normalize())) {
                return Result.badRequest("非法文件路径");
            }
            if (!Files.exists(file)) {
                return Result.badRequest("文件不存在");
            }
            if ("langchain4j".equalsIgnoreCase(engine)) {
                vectorStoreService.removeDocument(file);
            }
            Files.delete(file);
            if ("langchain".equalsIgnoreCase(engine)) {
                triggerPythonRebuild();
            }
            return Result.success("文件删除成功", null);
        } catch (Exception e) {
            return Result.error("删除文件失败: " + e.getMessage());
        }
    }

    @GetMapping({"/config/rag/knowledge-files/content", "/config/rag/knowledge-files/content/"})
    public Result<Map<String, Object>> getKnowledgeFileContent(@RequestParam("engine") String engine,
                                                               @RequestParam("fileName") String fileName) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可查看知识库");
        }
        if (!StringUtils.hasText(fileName)) {
            return Result.badRequest("文件名不能为空");
        }
        try {
            Path dir = resolveKnowledgePath(engine);
            Path file = dir.resolve(safeFileName(fileName)).normalize();
            if (!file.startsWith(dir.normalize())) {
                return Result.badRequest("非法文件路径");
            }
            if (!Files.exists(file)) {
                return Result.badRequest("文件不存在");
            }
            if (!isEditableTextFile(file)) {
                return Result.badRequest("该文件类型不支持在线编辑");
            }
            String content = Files.readString(file, StandardCharsets.UTF_8);
            Map<String, Object> data = new HashMap<>();
            data.put("fileName", file.getFileName().toString());
            data.put("content", content);
            return Result.success(data);
        } catch (Exception e) {
            return Result.error("读取文件内容失败: " + e.getMessage());
        }
    }

    @PutMapping({"/config/rag/knowledge-files/content", "/config/rag/knowledge-files/content/"})
    public Result<String> updateKnowledgeFileContent(@RequestParam("engine") String engine,
                                                     @RequestParam("fileName") String fileName,
                                                     @RequestBody Map<String, Object> body) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可修改知识库");
        }
        if (!StringUtils.hasText(fileName)) {
            return Result.badRequest("文件名不能为空");
        }
        try {
            Path dir = resolveKnowledgePath(engine);
            Path file = dir.resolve(safeFileName(fileName)).normalize();
            if (!file.startsWith(dir.normalize())) {
                return Result.badRequest("非法文件路径");
            }
            if (!Files.exists(file)) {
                return Result.badRequest("文件不存在");
            }
            if (!isEditableTextFile(file)) {
                return Result.badRequest("该文件类型不支持在线编辑");
            }
            String content = String.valueOf(body.getOrDefault("content", ""));
            Files.writeString(file, content, StandardCharsets.UTF_8, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.CREATE);
            if ("langchain4j".equalsIgnoreCase(engine)) {
                vectorStoreService.processDocument(file);
            } else {
                triggerPythonRebuild();
            }
            return Result.success("文件内容已保存", null);
        } catch (Exception e) {
            return Result.error("保存文件内容失败: " + e.getMessage());
        }
    }

    private boolean isAdmin() {
        User user = UserContext.getUser();
        return user != null && "ADMIN".equalsIgnoreCase(user.getRole());
    }

    private Path getProjectRoot() {
        Path backendRoot = Paths.get(System.getProperty("user.dir")).toAbsolutePath();
        return backendRoot.getParent() == null ? backendRoot : backendRoot.getParent();
    }

    private Path getBackendAppYamlPath() {
        return Paths.get(System.getProperty("user.dir"), "src", "main", "resources", "application.yml");
    }

    private Path getPythonRoot() {
        return getProjectRoot().resolve("back-end-python");
    }

    private Path getPythonEnvPath() {
        return getPythonRoot().resolve(".env");
    }

    private Path resolvePythonKnowledgePath(String rawPath) {
        Path p = Paths.get(rawPath);
        return p.isAbsolute() ? p : getPythonRoot().resolve(p).normalize();
    }

    private Path resolveKnowledgePath(String engine) throws IOException {
        if ("langchain4j".equalsIgnoreCase(engine)) {
            Path p = Paths.get(knowledgeBasePath).normalize();
            Files.createDirectories(p);
            return p;
        }
        if ("langchain".equalsIgnoreCase(engine)) {
            Map<String, String> env = readEnvFile(getPythonEnvPath());
            Path p = resolvePythonKnowledgePath(env.getOrDefault("KNOWLEDGE_PATH", "./data/knowledge"));
            Files.createDirectories(p);
            return p;
        }
        throw new IllegalArgumentException("engine仅支持 langchain 或 langchain4j");
    }

    private List<Map<String, Object>> listKnowledgeFiles(Path dir) throws IOException {
        if (!Files.exists(dir)) {
            return List.of();
        }
        List<Map<String, Object>> files = new ArrayList<>();
        try (var stream = Files.list(dir)) {
            stream.filter(Files::isRegularFile)
                    .sorted(Comparator.comparing(Path::getFileName))
                    .forEach(path -> {
                        try {
                            Map<String, Object> one = new HashMap<>();
                            one.put("name", path.getFileName().toString());
                            one.put("size", Files.size(path));
                            one.put("modifiedAt", Files.getLastModifiedTime(path).toMillis());
                            files.add(one);
                        } catch (IOException ignored) {
                        }
                    });
        }
        return files;
    }

    private String safeFileName(String originalName) {
        String name = Paths.get(Objects.requireNonNull(originalName)).getFileName().toString();
        if (!Pattern.matches("[\\w\\-.\\u4e00-\\u9fa5 ]+", name)) {
            throw new IllegalArgumentException("文件名包含非法字符");
        }
        return name;
    }

    private boolean isEditableTextFile(Path file) {
        String name = file.getFileName().toString();
        int dot = name.lastIndexOf('.');
        if (dot < 0 || dot == name.length() - 1) {
            return true;
        }
        String ext = name.substring(dot + 1).toLowerCase();
        return EDITABLE_EXTENSIONS.contains(ext);
    }

    private Map<String, String> readEnvFile(Path envPath) throws IOException {
        Map<String, String> map = new LinkedHashMap<>();
        if (!Files.exists(envPath)) {
            return map;
        }
        for (String line : Files.readAllLines(envPath, StandardCharsets.UTF_8)) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("#") || !trimmed.contains("=")) {
                continue;
            }
            int idx = trimmed.indexOf('=');
            map.put(trimmed.substring(0, idx).trim(), trimmed.substring(idx + 1).trim());
        }
        return map;
    }

    private void updateEnvFile(Path envPath, Map<String, String> updates) throws IOException {
        List<String> lines = Files.exists(envPath)
                ? new ArrayList<>(Files.readAllLines(envPath, StandardCharsets.UTF_8))
                : new ArrayList<>();

        Map<String, Boolean> found = new HashMap<>();
        for (String k : updates.keySet()) {
            found.put(k, false);
        }

        for (int i = 0; i < lines.size(); i++) {
            String line = lines.get(i);
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("#") || !trimmed.contains("=")) {
                continue;
            }
            int idx = trimmed.indexOf('=');
            String key = trimmed.substring(0, idx).trim();
            if (updates.containsKey(key)) {
                lines.set(i, key + "=" + updates.get(key));
                found.put(key, true);
            }
        }

        for (Map.Entry<String, String> e : updates.entrySet()) {
            if (!Boolean.TRUE.equals(found.get(e.getKey()))) {
                lines.add(e.getKey() + "=" + e.getValue());
            }
        }

        Files.write(envPath, lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> readYaml(Path yamlPath) throws IOException {
        Yaml yaml = new Yaml();
        if (!Files.exists(yamlPath)) {
            return new LinkedHashMap<>();
        }
        Object loaded = yaml.load(Files.newInputStream(yamlPath));
        if (loaded instanceof Map<?, ?> loadedMap) {
            return (Map<String, Object>) loadedMap;
        }
        return new LinkedHashMap<>();
    }

    private void saveYaml(Path yamlPath, Map<String, Object> yamlData) throws IOException {
        Yaml yaml = new Yaml();
        String dumped = yaml.dump(yamlData);
        Files.writeString(yamlPath, dumped, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    }

    @SuppressWarnings("unchecked")
    private void writeYamlPath(Map<String, Object> root, String path, Object value) {
        String[] segments = path.split("\\.");
        Map<String, Object> cur = root;
        for (int i = 0; i < segments.length - 1; i++) {
            Object next = cur.get(segments[i]);
            if (!(next instanceof Map<?, ?>)) {
                next = new LinkedHashMap<String, Object>();
                cur.put(segments[i], next);
            }
            cur = (Map<String, Object>) next;
        }
        cur.put(segments[segments.length - 1], value);
    }

    @SuppressWarnings("unchecked")
    private Object readYamlPath(Map<String, Object> root, String path) {
        String[] segments = path.split("\\.");
        Object cur = root;
        for (String seg : segments) {
            if (!(cur instanceof Map<?, ?> map)) {
                return null;
            }
            cur = map.get(seg);
            if (cur == null) {
                return null;
            }
        }
        return cur;
    }

    private int readYamlInt(Map<String, Object> root, String path, int defaultValue) {
        Object v = readYamlPath(root, path);
        return parseInt(v, defaultValue);
    }

    private double readYamlDouble(Map<String, Object> root, String path, double defaultValue) {
        Object v = readYamlPath(root, path);
        return parseDouble(v, defaultValue);
    }

    private int parseInt(Object val, int defaultValue) {
        if (val == null) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(String.valueOf(val));
        } catch (Exception e) {
            return defaultValue;
        }
    }

    private double parseDouble(Object val, double defaultValue) {
        if (val == null) {
            return defaultValue;
        }
        try {
            return Double.parseDouble(String.valueOf(val));
        } catch (Exception e) {
            return defaultValue;
        }
    }

    private void triggerPythonRebuild() {
        try {
            WebClient client = webClientBuilder.baseUrl(pythonApiUrl).build();
            client.post()
                    .uri("/api/rebuild")
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
        } catch (Exception ignored) {
            // 知识库重建失败不阻塞文件操作，前端提示重启/手动重建
        }
    }
}
