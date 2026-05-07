package com.environment.Listener;


import com.environment.Constants.ConstantsInfo;
import com.environment.service.VectorStoreService;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.*;


@Slf4j
@Component
public class KnowledgeFileWatcher {

    @Autowired
    private StringRedisTemplate redisTemplate;
    @Autowired
    private VectorStoreService vectorStoreService;

    @Value("${knowledge.base-path}")
    private String knowledgeBasePath;


    @PostConstruct
    public void startWatching() throws IOException {
        Path watchPath = Paths.get(knowledgeBasePath);

        // 如果目录不存在，创建它
        if (!Files.exists(watchPath)) {
            Files.createDirectories(watchPath);
            log.info("知识库目录创建成功: {}", knowledgeBasePath);
        }

        WatchService watchService= FileSystems.getDefault().newWatchService();

        watchPath.register(watchService,
                StandardWatchEventKinds.ENTRY_CREATE,
                StandardWatchEventKinds.ENTRY_DELETE,
                StandardWatchEventKinds.ENTRY_MODIFY);

        new Thread(()->{
            while(true){
                try{
                    WatchKey watchKey = watchService.take();
                    for(WatchEvent<?> event: watchKey.pollEvents()){
                        Path filePath = watchPath.resolve((Path) event.context());
                        handleFileChange(filePath, event.kind());
                    }
                    watchKey.reset();
                }catch (Exception e) {
                    log.error("监听异常", e);
                }
            }
        }).start();
        log.info("监听启动成功");
    }

    private void handleFileChange(Path filePath, WatchEvent.Kind<?> kind){
        String fileName=filePath.toString();

        // 删除文件
        if(kind==StandardWatchEventKinds.ENTRY_DELETE){
            vectorStoreService.removeDocument(filePath);
            redisTemplate.opsForHash().delete(ConstantsInfo.FILE_META_KEY, fileName);
            log.info("文件删除: {}", fileName);
            return;
        }

        // 检查文件是否存在（避免处理临时文件）
        if(!Files.exists(filePath)){
            return;
        }

        // 检查文件类型是否支持
        String lowerName = fileName.toLowerCase();
        if(!lowerName.endsWith(".pdf") && !lowerName.endsWith(".txt") && !lowerName.endsWith(".md")){
            return;
        }

        try {
            long lastModified = Files.getLastModifiedTime(filePath).toMillis();

            //获取Redis中存储的文件最后修改时间
            String storedTime=redisTemplate.opsForHash()
                    .get(ConstantsInfo.FILE_META_KEY, fileName)!=null
                    ? redisTemplate.opsForHash().get(ConstantsInfo.FILE_META_KEY, fileName).toString()
                    : "0";

            // 判断是否需要处理（新文件或修改过的文件）
            if(lastModified>Long.parseLong(storedTime)){
                log.info("正在处理文件: {}", fileName);
                vectorStoreService.processDocument(filePath);
                redisTemplate.opsForHash().put(ConstantsInfo.FILE_META_KEY, fileName, String.valueOf(lastModified));
                log.info("文件处理完成: {}", fileName);
            }
        } catch (IOException e) {
            log.error("处理文件失败: {}", fileName, e);
        }
    }
}
