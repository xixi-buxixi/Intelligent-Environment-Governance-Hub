package com.environment.service;

import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.PermissionApplicationRequest;
import com.environment.pojo.PermissionApplication;

/**
 * 权限申请服务
 */
public interface PermissionApplicationService {
    Long submit(Long userId, PermissionApplicationRequest request);

    PageResult<PermissionApplication> getMyApplications(Long userId, Integer page, Integer size);

    PageResult<PermissionApplication> getAllApplications(Integer page, Integer size, String status);

    String approve(Long applicationId, Long reviewerId, String comment);

    String reject(Long applicationId, Long reviewerId, String comment);
}
