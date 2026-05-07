package com.environment.mapper;

import com.environment.pojo.DataFetchRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDate;
import java.util.List;

/**
 * 数据获取记录Mapper
 */
@Mapper
public interface DataFetchRecordMapper {

    /**
     * 插入记录
     */
    int insert(DataFetchRecord record);

    /**
     * 根据ID查询
     */
    DataFetchRecord selectById(Long id);

    /**
     * 查询用户的获取记录
     */
    List<DataFetchRecord> selectByUserId(Long userId);

    /**
     * 查询用户某日的获取次数
     */
    int countByUserIdAndDate(@Param("userId") Long userId, @Param("fetchDate") LocalDate fetchDate);

    /**
     * 查询所有记录（带用户信息）
     */
    List<DataFetchRecord> selectAllWithUserInfo();

    /**
     * 根据条件查询记录
     */
    List<DataFetchRecord> selectByCondition(@Param("userId") Long userId,
                                             @Param("sourceId") Long sourceId,
                                             @Param("city") String city);
}
