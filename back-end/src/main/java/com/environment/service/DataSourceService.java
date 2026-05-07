package com.environment.service;

import com.environment.pojo.DataSource;

import java.util.List;

/**
 * 数据源服务接口
 */
public interface DataSourceService {

    /**
     * 获取所有启用的数据源
     */
    List<DataSource> getAllActiveDataSources();

    /**
     * 根据ID获取数据源
     */
    DataSource getDataSourceById(Long id);

    /**
     * 根据编码获取数据源
     */
    DataSource getDataSourceByCode(String sourceCode);

    /**
     * 获取所有数据源（包含禁用）
     */
    List<DataSource> getAllDataSources();

    /**
     * 添加数据源
     */
    boolean addDataSource(DataSource dataSource);

    /**
     * 更新数据源
     */
    boolean updateDataSource(DataSource dataSource);

    /**
     * 删除数据源
     */
    boolean deleteDataSource(Long id);
}
