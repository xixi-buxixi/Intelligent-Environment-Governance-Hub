package com.environment.controller;


import com.environment.service.ConsultantService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/assistant")
public class AssistantController {


    @Autowired
    private ConsultantService consultantService;
    @Value("${python.api.url:http://localhost:5001}")
    private String pythonApiUrl;

    @Value("${python.api.chat-path:/api/chat}")
    private String pythonChatPath;

    @Value("${python.api.stream-path:/api/chat/stream}")
    private String pythonStreamPath;

    @Value("${python.api.default-mode:agent}")
    private String pythonDefaultMode;

    private final ObjectMapper mapper = new ObjectMapper();
    private WebClient webClient;

    @Autowired
    public void setWebClient(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.baseUrl(pythonApiUrl).build();
    }
    /**
     * 支持 JSON 格式请求（前端使用） - SSE流式输出
     */
    @PostMapping(value = "/langchain4j/chat",produces=MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> chatLangChain4j(@RequestBody ChatRequest request){
        String memoryId=request.getSessionId()!=null? request.getSessionId() : "default";
        String question=normalizeQuestion(request);
        return consultantService.streamChat(memoryId, question)
                .map(content -> ServerSentEvent.<String>builder()
                        .data(content)
                        .build());
    }

    @PostMapping(value = "/langchain/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> chatLangChainStream(@RequestBody ChatRequest request) {
        String question = normalizeQuestion(request);
        String mode = resolveMode(request);

        PythonChatRequest body = new PythonChatRequest();
        body.setQuestion(question);
        body.setMode(mode);
        body.setSessionId(request.getSessionId());

        return webClient.post()
                .uri(pythonChatPath)
                .bodyValue(body)
                .exchangeToMono(response -> response.bodyToMono(String.class)
                        .defaultIfEmpty("")
                        .map(raw -> response.statusCode().is2xxSuccessful()
                                ? extractAnswer(raw)
                                : extractError(raw)))
                .onErrorResume(ex -> Mono.just("Python 服务调用失败: " + ex.getMessage()))
                .map(answer -> answer == null ? "" : answer.trim())
                .filter(answer -> !answer.isBlank())
                .map(answer -> ServerSentEvent.<String>builder().data(answer).build())
                .flux();
    }


    private String normalizeQuestion(ChatRequest request){
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

    //增加 JSON 解析辅助方法
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

    private String extractError(String json) {
        try {
            JsonNode node = mapper.readTree(json);
            if (node.has("error")) {
                String error = node.get("error").asText("");
                return error.isBlank() ? "Python 服务返回错误" : ("Python 服务错误: " + error);
            }
            return "Python 服务错误: " + json;
        } catch (Exception e) {
            return "Python 服务错误: " + json;
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






    @Data
    public static class ChatRequest {
        private String sessionId;
        private String message;
        private String question;
        private String mode;
    }
    @Data
    public static class PythonChatRequest {
        private String question;
        private String mode;
        private String sessionId;
    }

}
