package com.environment.mapper;

import com.environment.pojo.RiskAnalysisRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface RiskAnalysisRecordMapper {
    int insert(RiskAnalysisRecord record);

    RiskAnalysisRecord selectById(@Param("id") Long id);

    int countByCondition(@Param("userId") Long userId,
                         @Param("city") String city,
                         @Param("riskLevel") String riskLevel);

    List<RiskAnalysisRecord> selectByCondition(@Param("userId") Long userId,
                                               @Param("city") String city,
                                               @Param("riskLevel") String riskLevel,
                                               @Param("offset") Integer offset,
                                               @Param("size") Integer size);
}
