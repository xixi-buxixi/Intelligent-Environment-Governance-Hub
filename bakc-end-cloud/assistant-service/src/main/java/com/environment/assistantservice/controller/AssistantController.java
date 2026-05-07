package com.environment.assistantservice.controller;


import com.environment.assistantservice.service.ConsultantService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

@Tag(name = "环境小助手管理", description = "环境小助手相关接口")
@RestController
@RequestMapping("/assistant")
public class AssistantController {

    @Autowired
    private ConsultantService consultantService;

    /**
     * 支持 JSON 格式请求（前端使用）
     */
    @PostMapping(value = "/chat", produces = "text/html;charset=utf-8")
    public Flux<String> chat(@RequestBody ChatRequest request) {
        String memoryId = request.getSessionId() != null ? request.getSessionId() : "default";
        return consultantService.streamChat(memoryId, request.getMessage());
    }

    /**
     * 聊天请求 DTO
     */
    public static class ChatRequest {
        private String sessionId;  // 前端传的是 sessionId
        private String message;

        public String getSessionId() {
            return sessionId;
        }

        public void setSessionId(String sessionId) {
            this.sessionId = sessionId;
        }

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }
    }
}
