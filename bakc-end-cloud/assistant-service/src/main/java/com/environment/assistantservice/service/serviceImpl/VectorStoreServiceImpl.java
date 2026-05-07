package com.environment.assistantservice.service.serviceImpl;




import com.environment.assistantservice.service.VectorStoreService;
import dev.langchain4j.community.store.embedding.redis.RedisEmbeddingStore;
import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.DocumentParser;
import dev.langchain4j.data.document.DocumentSplitter;
import dev.langchain4j.data.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.data.document.parser.TextDocumentParser;
import dev.langchain4j.data.document.parser.apache.pdfbox.ApachePdfBoxDocumentParser;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStoreIngestor;
import dev.langchain4j.store.embedding.filter.Filter;


import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;

/**
 * 向量存储服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class VectorStoreServiceImpl implements VectorStoreService {

    private final EmbeddingModel embeddingModel;
    private final RedisEmbeddingStore redisEmbeddingStore;
    private final StringRedisTemplate redisTemplate;

    private static final String FILE_META_KEY = "knowledge:file:meta";
    private static final String FILE_SEGMENT_KEY = "knowledge:file:segments";

    @Value("${knowledge.chunk-size:500}")
    private int chunkSize;

    @Value("${knowledge.chunk-overlap:100}")
    private int chunkOverlap;

    @Override
    public void processDocument(Path filePath) {
        log.info("开始处理文档: {}", filePath.getFileName());

        try {
            // 1. 加载文档
            Document document = loadDocument(filePath);
            if (document == null) {
                log.warn("无法加载文档: {}", filePath);
                return;
            }

            // 2. 如果是修改，先删除旧的向量数据
            removeDocument(filePath);

            // 3. 切割
            DocumentSplitter splitter = DocumentSplitters.recursive(chunkSize, chunkOverlap);
            List<TextSegment> segments = splitter.split(document);

            // 4. 为每个片段添加文件路径元数据
            String filePathStr = filePath.toString();
            for (int i = 0; i < segments.size(); i++) {
                TextSegment segment = segments.get(i);
                segment.metadata().put("file_path", filePathStr);
                segment.metadata().put("file_name", filePath.getFileName().toString());
                segment.metadata().put("segment_index", String.valueOf(i));
            }

            // 5. 向量化并存储
            EmbeddingStoreIngestor ingestor = EmbeddingStoreIngestor.builder()
                    .embeddingStore(redisEmbeddingStore)
                    .documentSplitter(splitter)
                    .embeddingModel(embeddingModel)
                    .build();

            ingestor.ingest(document);

            // 6. 记录处理状态
            recordProcessed(filePath, segments.size());

            log.info("文档处理完成: {}，生成 {} 个片段", filePath.getFileName(), segments.size());

        } catch (Exception e) {
            log.error("处理文档失败: {}", filePath, e);
            throw new RuntimeException("处理文档失败", e);
        }
    }

    @Override
    public void removeDocument(Path filePath) {
        log.info("开始删除文档向量: {}", filePath.getFileName());

        String filePathStr = filePath.toString();
        String fileName = filePath.getFileName().toString();

        try {
            // 直接通过 Redis 删除
            String pattern = "doc:*" + fileName + "*";
            Set<String> keys = redisTemplate.keys(pattern);

            if (keys != null && !keys.isEmpty()) {
                redisTemplate.delete(keys);
                log.info("删除 {} 个向量 key", keys.size());
            }

            // 清除处理记录
            redisTemplate.opsForHash().delete(FILE_META_KEY, filePathStr);
            redisTemplate.opsForHash().delete(FILE_SEGMENT_KEY, filePathStr);

            log.info("文档向量删除完成: {}", fileName);

        } catch (Exception e) {
            log.error("删除文档向量失败: {}", filePath, e);
        }
    }

    @Override
    public void processDocuments(List<Document> documents) {
        if (documents == null || documents.isEmpty()) {
            return;
        }

        DocumentSplitter splitter = DocumentSplitters.recursive(chunkSize, chunkOverlap);

        EmbeddingStoreIngestor ingestor = EmbeddingStoreIngestor.builder()
                .embeddingStore(redisEmbeddingStore)
                .documentSplitter(splitter)
                .embeddingModel(embeddingModel)
                .build();

        ingestor.ingest(documents);
        log.info("批量处理完成，共 {} 个文档", documents.size());
    }

    @Override
    public boolean needsProcessing(Path filePath) {
        try {
            if (!Files.exists(filePath)) {
                return false;
            }
            long lastModified = Files.getLastModifiedTime(filePath).toMillis();
            String storedTime = getStoredModifiedTime(filePath);
            return lastModified > Long.parseLong(storedTime);
        } catch (IOException e) {
            return false;
        }
    }

    /**
     * 删除文档 - 备用方案（直接删除 Redis key）
     */
    private void removeDocumentFallback(Path filePath) {
        String filePathStr = filePath.toString();
        String fileName = filePath.getFileName().toString();

        try {
            // 根据 Redis key 模式匹配删除
            String pattern = "doc:*" + fileName + "*";
            Set<String> keys = redisTemplate.keys(pattern);

            if (keys != null && !keys.isEmpty()) {
                redisTemplate.delete(keys);
                log.info("删除 {} 个向量 key", keys.size());
            }

            // 清除记录
            redisTemplate.opsForHash().delete(FILE_META_KEY, filePathStr);
            redisTemplate.opsForHash().delete(FILE_SEGMENT_KEY, filePathStr);

            log.info("文档向量删除完成(备用方案): {}", fileName);

        } catch (Exception e) {
            log.error("删除文档向量失败: {}", filePath, e);
        }
    }

    /**
     * 加载文档（根据文件类型选择解析器）
     */
    private Document loadDocument(Path filePath) {
        String fileName = filePath.getFileName().toString().toLowerCase();

        try {
            DocumentParser parser;
            if (fileName.endsWith(".pdf")) {
                parser = new ApachePdfBoxDocumentParser();
            } else if (fileName.endsWith(".txt") || fileName.endsWith(".md")) {
                parser = new TextDocumentParser();
            } else {
                log.warn("不支持的文件类型: {}", fileName);
                return null;
            }

            return FileSystemDocumentLoader.loadDocument(filePath, parser);

        } catch (Exception e) {
            log.error("加载文档失败: {}", filePath, e);
            return null;
        }
    }

    /**
     * 记录文件已处理
     */
    private void recordProcessed(Path filePath, int segmentCount) {
        try {
            long lastModified = Files.getLastModifiedTime(filePath).toMillis();
            String filePathStr = filePath.toString();

            // 记录修改时间
            redisTemplate.opsForHash().put(FILE_META_KEY, filePathStr, String.valueOf(lastModified));

            // 记录片段数量
            redisTemplate.opsForHash().put(FILE_SEGMENT_KEY, filePathStr, "count:" + segmentCount);

        } catch (IOException e) {
            log.error("记录文件状态失败", e);
        }
    }

    /**
     * 获取已存储的修改时间
     */
    private String getStoredModifiedTime(Path filePath) {
        Object value = redisTemplate.opsForHash().get(FILE_META_KEY, filePath.toString());
        return value != null ? value.toString() : "0";
    }
}