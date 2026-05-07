package com.environment.service;


import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.spring.AiService;
import dev.langchain4j.service.spring.AiServiceWiringMode;
import reactor.core.publisher.Flux;

@AiService(
        wiringMode = AiServiceWiringMode.EXPLICIT,
        chatModel = "openAiChatModel",//指定模型
        streamingChatModel = "openAiStreamingChatModel",//指定流式模型
        chatMemoryProvider = "chatMemoryProvider",//指定记忆提供者
        contentRetriever = "retriever"//指定内容检索者
        //tools = "environmentTools"
)
public interface ConsultantService {

    Flux<String> streamChat(@MemoryId String memoryId, @UserMessage String userMessage);
}
