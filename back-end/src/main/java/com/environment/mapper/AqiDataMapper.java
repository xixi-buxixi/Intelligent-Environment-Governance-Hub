package com.environment.mapper;

import com.environment.pojo.AqiDataRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface AqiDataMapper {

    int countDistinctDatesInRange(@Param("city") String city,
                                  @Param("startDate") LocalDate startDate,
                                  @Param("endDate") LocalDate endDate);

    int countRowsInRange(@Param("city") String city,
                         @Param("startDate") LocalDate startDate,
                         @Param("endDate") LocalDate endDate);

    List<AqiDataRecord> selectPreviewByRange(@Param("city") String city,
                                             @Param("startDate") LocalDate startDate,
                                             @Param("endDate") LocalDate endDate,
                                             @Param("limit") Integer limit);

    List<AqiDataRecord> selectAllByRange(@Param("city") String city,
                                         @Param("startDate") LocalDate startDate,
                                         @Param("endDate") LocalDate endDate);
}

