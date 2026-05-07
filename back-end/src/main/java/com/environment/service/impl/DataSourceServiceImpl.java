package com.environment.service.impl;

import com.environment.mapper.DataSourceMapper;
import com.environment.pojo.DataSource;
import com.environment.service.DataSourceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 数据源服务实现类
 */
@Service
public class DataSourceServiceImpl implements DataSourceService {

    @Autowired
    private DataSourceMapper dataSourceMapper;

    @Override
    public List<DataSource> getAllActiveDataSources() {
        return dataSourceMapper.selectAllActive();
    }

    @Override
    public DataSource getDataSourceById(Long id) {
        return dataSourceMapper.selectById(id);
    }

    @Override
    public DataSource getDataSourceByCode(String sourceCode) {
        return dataSourceMapper.selectByCode(sourceCode);
    }

    @Override
    public List<DataSource> getAllDataSources() {
        return dataSourceMapper.selectAll();
    }

    @Override
    public boolean addDataSource(DataSource dataSource) {
        return dataSourceMapper.insert(dataSource) > 0;
    }

    @Override
    public boolean updateDataSource(DataSource dataSource) {
        return dataSourceMapper.update(dataSource) > 0;
    }

    @Override
    public boolean deleteDataSource(Long id) {
        return dataSourceMapper.deleteById(id) > 0;
    }
}
