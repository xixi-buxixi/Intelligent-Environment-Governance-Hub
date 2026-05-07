package com.environment.config;

import com.environment.repository.RedisChatMemoryStore;
import dev.langchain4j.community.store.embedding.redis.RedisEmbeddingStore;
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.ChatMemoryProvider;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.rag.content.retriever.ContentRetriever;
import dev.langchain4j.rag.content.retriever.EmbeddingStoreContentRetriever;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class AssistantConfig {
    @Autowired
    private RedisChatMemoryStore redisChatMemoryStore;
    @Autowired
    private EmbeddingModel embeddingModel;
    @Autowired
    private RedisEmbeddingStore redisEmbeddingStore;

    @Value("${assistant.memory.max-messages:20}")
    private Integer maxMessages;

    @Value("${assistant.retriever.min-score:0.6}")
    private Double retrieverMinScore;

    @Value("${assistant.retriever.max-results:3}")
    private Integer retrieverMaxResults;

    //构建聊天内存对象：保存对话历史
    @Bean
    public ChatMemory chatMemory(){
        MessageWindowChatMemory memory=MessageWindowChatMemory.builder()
                .maxMessages(maxMessages)
                .build();
        return memory;
    }

    //提供聊天内存的工厂对象，支持多用户会话管理
    @Bean
    public ChatMemoryProvider chatMemoryProvider(){
        ChatMemoryProvider provider=new ChatMemoryProvider() {
            @Override
            public ChatMemory get(Object memoryId) {
                return MessageWindowChatMemory.builder()
                        .maxMessages(maxMessages)
                        .id(memoryId)
                        .chatMemoryStore(redisChatMemoryStore)
                        .build();
            }
        };
        return provider;
    }
    //构建向量数据库存储对象，并完成文档的加载、分割、向量化和存储

    //构建数据库检索器，用于从向量数据库中检索相关内容
    @Bean
    public ContentRetriever retriever(){
        return EmbeddingStoreContentRetriever.builder()
                .embeddingStore(redisEmbeddingStore)
                .minScore(retrieverMinScore)
                .maxResults(retrieverMaxResults)
                .embeddingModel(embeddingModel)
                .build();
    }

    // WebClient.Builder 用于调用Python API
    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder();
    }

}
