package com.environment.assistantservice.config;


import com.environment.assistantservice.repository.RedisChatMemoryStore;
import dev.langchain4j.community.store.embedding.redis.RedisEmbeddingStore;
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.ChatMemoryProvider;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.rag.content.retriever.ContentRetriever;
import dev.langchain4j.rag.content.retriever.EmbeddingStoreContentRetriever;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AssistantConfig {
    @Autowired
    private RedisChatMemoryStore redisChatMemoryStore;
    @Autowired
    private EmbeddingModel embeddingModel;
    @Autowired
    private RedisEmbeddingStore redisEmbeddingStore;

    //构建聊天内存对象：保存对话历史
    @Bean
    public ChatMemory chatMemory(){
        MessageWindowChatMemory memory=MessageWindowChatMemory.builder()
                .maxMessages(20)
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
                        .maxMessages(20)
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
                .minScore(0.6)
                .maxResults(3)
                .embeddingModel(embeddingModel)
                .build();
    }

}
