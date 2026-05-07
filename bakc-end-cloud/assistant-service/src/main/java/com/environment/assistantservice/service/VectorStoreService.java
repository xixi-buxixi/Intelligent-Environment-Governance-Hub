package com.environment.assistantservice.service;


import dev.langchain4j.data.document.Document;


import java.nio.file.Path;
import java.util.List;

/**
 * 向量存储服务接口
 * 支持文档的新增、修改、删除的增量更新
 */
public interface VectorStoreService {

    /**
     * 处理单个文件（新增/修改时调用）
     * @param filePath 文件路径
     */
    void processDocument(Path filePath);

    /**
     * 删除文档的向量数据（文件删除时调用）
     * @param filePath 文件路径
     */
    void removeDocument(Path filePath);

    /**
     * 批量处理文档
     * @param documents 文档列表
     */
    void processDocuments(List<Document> documents);

    /**
     * 判断文件是否需要处理
     * @param filePath 文件路径
     * @return true-需要处理，false-不需要处理
     */
    boolean needsProcessing(Path filePath);
}