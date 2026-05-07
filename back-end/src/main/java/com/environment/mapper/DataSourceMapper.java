package com.environment.mapper;

import com.environment.pojo.DataSource;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 数据源Mapper
 */
@Mapper
public interface DataSourceMapper {

    /**
     * 查询所有启用的数据源
     */
    List<DataSource> selectAllActive();

    /**
     * 根据ID查询
     */
    DataSource selectById(Long id);

    /**
     * 根据编码查询
     */
    DataSource selectByCode(@Param("sourceCode") String sourceCode);

    /**
     * 插入数据源
     */
    int insert(DataSource dataSource);

    /**
     * 更新数据源
     */
    int update(DataSource dataSource);

    /**
     * 删除数据源
     */
    int deleteById(Long id);

    /**
     * 查询所有数据源
     */
    List<DataSource> selectAll();
}
