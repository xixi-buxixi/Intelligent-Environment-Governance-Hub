package com.environment.service;

import com.environment.pojo.DataFetchRecord;
import com.environment.pojo.DTO.DataFetchRequestDTO;
import com.environment.pojo.DTO.UserFetchLimitDTO;

import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import java.util.Map;

/**
 * 数据获取服务接口
 */
public interface DataFetchService {

    /**
     * 获取用户今日获取次数信息
     */
    UserFetchLimitDTO getUserFetchLimit(Long userId, String role);

    /**
     * 检查用户是否可以获取数据
     */
    boolean canFetchData(Long userId, String role);

    /**
     * 获取数据预览（必要时触发爬虫）
     */
    Map<String, Object> fetchDataPreview(DataFetchRequestDTO requestDTO, Long userId, String role);

    /**
     * 导出CSV
     */
    void exportCsv(DataFetchRequestDTO requestDTO, HttpServletResponse response) throws IOException;

    /**
     * 接收爬虫完成通知并更新最近爬取时间
     */
    void handleCrawlNotify(String status, String message, String finishedAt);

    /**
     * 获取用户的历史获取记录
     */
    List<DataFetchRecord> getUserFetchRecords(Long userId);

    /**
     * 获取所有获取记录（管理员）
     */
    List<DataFetchRecord> getAllFetchRecords();
}
