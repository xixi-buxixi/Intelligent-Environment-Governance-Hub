package com.environment.mapper;

import com.environment.pojo.PermissionApplication;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 权限申请Mapper
 */
@Mapper
public interface PermissionApplicationMapper {
    int insert(PermissionApplication application);

    PermissionApplication selectById(@Param("id") Long id);

    PermissionApplication selectPendingByUserId(@Param("userId") Long userId);

    List<PermissionApplication> selectByUserId(@Param("userId") Long userId);

    List<PermissionApplication> selectList(@Param("status") String status);

    int updateReviewResult(PermissionApplication application);
}
