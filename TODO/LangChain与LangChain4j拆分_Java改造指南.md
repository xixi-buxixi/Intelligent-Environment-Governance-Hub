# 环保小助手 Java 端改造指南（LangChain 与 LangChain4j 分离）

## 一、改造目标
1. `LangChain4j` 与 `LangChain` 路由、请求参数、响应处理彻底分开。
2. 前端默认进入 `LangChain`（Python Agent）模式。
3. Java 后端作为统一网关：前端只请求 Java，Java 再转发 Python Agent。
4. 保留原有 `LangChain4j` 能力，不影响你后续做管理员参数配置。

## 二、任务清单（建议执行顺序）
1. 增加 Python Agent 专属配置项（URL、path、默认 mode）。
2. 重构 `AssistantController`：拆分 LangChain4j 与 LangChain 两组接口。
3. 新增/重构请求响应 DTO，统一接收 `question/message/sessionId/mode`。
4. 实现 Python 同步接口与流式接口两套转发逻辑（按你 Python 实际暴露接口选择一套或两套）。
5. 增加异常处理与日志，避免前端收到空流。
6. 本地联调：前端 LangChain 默认、LangChain4j 可切换。

---

## 三、详细改造步骤

### 步骤 1：扩展 Python 配置
**文件位置：** `back-end/src/main/resources/application.yml`

```yaml
python:
  api:
    url: http://localhost:5001
    chat-path: /api/chat
    stream-path: /api/chat/stream
    default-mode: agent
```

说明：
- `chat-path` 对应你 Python 的普通问答接口。
- `stream-path` 对应你 Python 的 SSE 流式接口。
- 如果你 Python 只有一个接口，保留一个即可。

---

### 步骤 2：拆分 Controller 路由（核心）
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
@PostMapping(value = "/langchain4j/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chatLangChain4j(@RequestBody ChatRequest request) {
    String memoryId = request.getSessionId() != null ? request.getSessionId() : "default";
    String question = normalizeQuestion(request);

    return consultantService.streamChat(memoryId, question)
            .map(content -> ServerSentEvent.<String>builder().data(content).build());
}
```

**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
@PostMapping(value = "/langchain/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chatLangChain(@RequestBody ChatRequest request) {
    String question = normalizeQuestion(request);
    String mode = resolveMode(request);

    PythonChatRequest body = new PythonChatRequest();
    body.setQuestion(question);
    body.setMode(mode);
    body.setSessionId(request.getSessionId());

    return webClient.post()
            .uri(pythonChatPath)
            .bodyValue(body)
            .retrieve()
            .bodyToMono(String.class)
            .flatMapMany(resp -> Flux.just(
                    ServerSentEvent.<String>builder().data(extractAnswer(resp)).build()
            ));
}
```

说明：
- 上面是“Python 普通接口转 SSE 单条消息”的写法，稳定、易调试。
- 如果你 Python Agent 已经是 SSE，使用“步骤 3 的流式版本”。

---

### 步骤 3：如果 Python Agent 是 SSE，使用流式转发
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
@PostMapping(value = "/langchain/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chatLangChainStream(@RequestBody ChatRequest request) {
    String question = normalizeQuestion(request);
    String mode = resolveMode(request);

    PythonChatRequest body = new PythonChatRequest();
    body.setQuestion(question);
    body.setMode(mode);
    body.setSessionId(request.getSessionId());

    return webClient.post()
            .uri(pythonStreamPath)
            .bodyValue(body)
            .retrieve()
            .bodyToFlux(String.class)
            .map(this::extractContentFromSseChunk)
            .filter(content -> content != null && !content.isBlank())
            .map(content -> ServerSentEvent.<String>builder().data(content).build());
}
```

---

### 步骤 4：补齐字段兼容（message/question 双兼容）
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
private String normalizeQuestion(ChatRequest request) {
    if (request.getQuestion() != null && !request.getQuestion().isBlank()) {
        return request.getQuestion();
    }
    if (request.getMessage() != null && !request.getMessage().isBlank()) {
        return request.getMessage();
    }
    throw new IllegalArgumentException("问题不能为空");
}

private String resolveMode(ChatRequest request) {
    if (request.getMode() == null || request.getMode().isBlank()) {
        return pythonDefaultMode;
    }
    return request.getMode();
}
```

---

### 步骤 5：扩展请求 DTO
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
public static class ChatRequest {
    private String sessionId;
    private String message;
    private String question;
    private String mode;

    // getter / setter
}
```

**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
@Data
public static class PythonChatRequest {
    private String question;
    private String mode;
    private String sessionId;
}
```

---

### 步骤 6：加入配置注入与初始化
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
@Value("${python.api.url:http://localhost:5001}")
private String pythonApiUrl;

@Value("${python.api.chat-path:/api/chat}")
private String pythonChatPath;

@Value("${python.api.stream-path:/api/chat/stream}")
private String pythonStreamPath;

@Value("${python.api.default-mode:agent}")
private String pythonDefaultMode;

private WebClient webClient;

@Autowired
public void setWebClient(WebClient.Builder webClientBuilder) {
    this.webClient = webClientBuilder.baseUrl(pythonApiUrl).build();
}
```

---

### 步骤 7：增加 JSON 解析辅助方法
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
private final ObjectMapper mapper = new ObjectMapper();

private String extractAnswer(String json) {
    try {
        JsonNode node = mapper.readTree(json);
        if (node.has("answer")) {
            return node.get("answer").asText("");
        }
        if (node.has("content")) {
            return node.get("content").asText("");
        }
        return json;
    } catch (Exception e) {
        return json;
    }
}

private String extractContentFromSseChunk(String chunk) {
    if (chunk == null || chunk.contains("[DONE]")) {
        return "";
    }
    String text = chunk.trim();
    if (text.startsWith("data:")) {
        text = text.substring(5).trim();
    }
    try {
        JsonNode node = mapper.readTree(text);
        if (node.has("content")) {
            return node.get("content").asText("");
        }
        if (node.has("answer")) {
            return node.get("answer").asText("");
        }
        return "";
    } catch (Exception e) {
        return text;
    }
}
```

---

### 步骤 8：兼容旧路由（迁移期建议）
**文件位置：** `back-end/src/main/java/com/environment/controller/AssistantController.java`

```java
@PostMapping(value = "/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chatLegacy(@RequestBody ChatRequest request) {
    return chatLangChain4j(request);
}

@PostMapping(value = "/chat-python", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> chatPythonLegacy(@RequestBody ChatRequest request) {
    return chatLangChain(request);
}
```

说明：
- 这样可以先让旧前端继续跑，逐步迁移到新路由。

---

## 四、联调检查清单
1. Java 启动后，确认日志打印的 Python `baseUrl` 正确。
2. Postman 测 `/api/assistant/langchain/chat`：传 `question + mode + sessionId`，应返回 SSE 文本。
3. Postman 测 `/api/assistant/langchain4j/chat`：应返回 LangChain4j 的 SSE 文本。
4. 前端默认打开应命中 LangChain（Python）接口。
5. 切换到 LangChain4j 后，再发送消息应命中 Java LangChain4j 接口。

---

## 五、和你当前前端改造的接口对齐
你当前前端已按如下参数发送：
- `question`
- `message`
- `mode`
- `sessionId`

因此 Java 端只要按本指南第 4、5 步做字段兼容即可直接接上。

---

## 六、后续你要做管理员参数配置时的接口预留（本次不做）
建议后续新增：
- `GET /assistant/config`
- `PUT /assistant/config`

参数可先预留：
- `knowledgeBasePath`
- `temperature`
- `topP`
- `maxTokens`
- `defaultMode`

这样就能无缝承接你提到的“管理员设置环保小助手参数”。
