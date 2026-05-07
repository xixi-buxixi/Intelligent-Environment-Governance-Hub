package com.environment.Initializer;

import com.environment.service.VectorStoreService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.stream.Stream;

/**
 * 知识库初始化器
 * 项目启动时自动加载知识库文件并构建向量索引
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KnowledgeInitializer implements CommandLineRunner {

    private final VectorStoreService vectorStoreService;
    private final StringRedisTemplate redisTemplate;

    @Value("${knowledge.base-path}")
    private String knowledgeBasePath;

    private static final String FILE_META_KEY = "knowledge:file:meta";

    @Override
    public void run(String... args) throws Exception {
        log.info("开始初始化知识库...");

        Path knowledgePath = Paths.get(knowledgeBasePath);

        // 检查知识库目录是否存在
        if (!Files.exists(knowledgePath)) {
            log.warn("知识库目录不存在，正在创建: {}", knowledgeBasePath);
            try {
                Files.createDirectories(knowledgePath);
                log.info("知识库目录创建成功");
            } catch (IOException e) {
                log.error("创建知识库目录失败", e);
                return;
            }
            return; // 新建目录，没有文件需要处理
        }

        // 遍历知识库目录，处理所有文件
        int processedCount = 0;
        int skippedCount = 0;

        try (Stream<Path> files = Files.walk(knowledgePath)) {
            for (Path file : files.toList()) {
                if (Files.isRegularFile(file) && isSupportedFile(file)) {
                    if (vectorStoreService.needsProcessing(file)) {
                        try {
                            log.info("正在处理文件: {}", file.getFileName());
                            vectorStoreService.processDocument(file);
                            processedCount++;
                        } catch (Exception e) {
                            log.error("处理文件失败: {}", file, e);
                        }
                    } else {
                        skippedCount++;
                    }
                }
            }
        } catch (IOException e) {
            log.error("遍历知识库目录失败", e);
        }

        log.info("知识库初始化完成！已处理: {} 个文件，跳过: {} 个文件", processedCount, skippedCount);
    }

    /**
     * 判断文件是否为支持的类型
     */
    private boolean isSupportedFile(Path file) {
        String fileName = file.getFileName().toString().toLowerCase();
        return fileName.endsWith(".pdf")
            || fileName.endsWith(".txt")
            || fileName.endsWith(".md");
    }
}