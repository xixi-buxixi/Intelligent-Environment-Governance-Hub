package com.environment.service.impl;

import com.environment.mapper.PermissionApplicationMapper;
import com.environment.mapper.UserMapper;
import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.PermissionApplicationRequest;
import com.environment.pojo.PermissionApplication;
import com.environment.pojo.User;
import com.environment.service.PermissionApplicationService;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;

/**
 * 权限申请服务实现
 */
@Service
public class PermissionApplicationServiceImpl implements PermissionApplicationService {
    private static final String ROLE_USER = "USER";
    private static final String ROLE_MONITOR = "MONITOR";
    private static final String STATUS_PENDING = "PENDING";
    private static final String STATUS_APPROVED = "APPROVED";
    private static final String STATUS_REJECTED = "REJECTED";

    private final PermissionApplicationMapper applicationMapper;
    private final UserMapper userMapper;

    public PermissionApplicationServiceImpl(PermissionApplicationMapper applicationMapper, UserMapper userMapper) {
        this.applicationMapper = applicationMapper;
        this.userMapper = userMapper;
    }

    @Override
    public Long submit(Long userId, PermissionApplicationRequest request) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        if (!ROLE_USER.equals(user.getRole())) {
            throw new RuntimeException("仅普通用户可提交权限申请");
        }
        String targetRole = StringUtils.hasText(request.getTargetRole()) ? request.getTargetRole() : ROLE_MONITOR;
        if (!ROLE_MONITOR.equals(targetRole)) {
            throw new RuntimeException("仅支持申请监测员权限");
        }
        if (!StringUtils.hasText(request.getReason())) {
            throw new RuntimeException("申请原因不能为空");
        }
        if (applicationMapper.selectPendingByUserId(userId) != null) {
            throw new RuntimeException("已有待处理申请，请勿重复提交");
        }

        PermissionApplication application = new PermissionApplication();
        application.setUserId(userId);
        application.setCurrentRole(user.getRole());
        application.setTargetRole(ROLE_MONITOR);
        application.setReason(request.getReason().trim());
        application.setStatus(STATUS_PENDING);
        applicationMapper.insert(application);
        return application.getId();
    }

    @Override
    public PageResult<PermissionApplication> getMyApplications(Long userId, Integer page, Integer size) {
        PageHelper.startPage(normalizePage(page), normalizeSize(size));
        List<PermissionApplication> list = applicationMapper.selectByUserId(userId);
        PageInfo<PermissionApplication> pageInfo = new PageInfo<>(list);
        return toPageResult(pageInfo);
    }

    @Override
    public PageResult<PermissionApplication> getAllApplications(Integer page, Integer size, String status) {
        PageHelper.startPage(normalizePage(page), normalizeSize(size));
        List<PermissionApplication> list = applicationMapper.selectList(normalizeStatus(status));
        PageInfo<PermissionApplication> pageInfo = new PageInfo<>(list);
        return toPageResult(pageInfo);
    }

    @Override
    @Transactional
    public String approve(Long applicationId, Long reviewerId, String comment) {
        PermissionApplication application = getPendingApplication(applicationId);
        if (!ROLE_MONITOR.equals(application.getTargetRole())) {
            throw new RuntimeException("仅支持同意监测员权限申请");
        }

        User targetUser = userMapper.selectById(application.getUserId());
        if (targetUser == null) {
            throw new RuntimeException("申请用户不存在");
        }
        targetUser.setRole(ROLE_MONITOR);
        if (userMapper.update(targetUser) <= 0) {
            throw new RuntimeException("用户权限更新失败");
        }

        application.setStatus(STATUS_APPROVED);
        application.setReviewerId(reviewerId);
        application.setReviewComment(StringUtils.hasText(comment) ? comment.trim() : "同意申请");
        if (applicationMapper.updateReviewResult(application) <= 0) {
            throw new RuntimeException("申请状态更新失败");
        }
        return "申请已同意";
    }

    @Override
    public String reject(Long applicationId, Long reviewerId, String comment) {
        PermissionApplication application = getPendingApplication(applicationId);
        if (!StringUtils.hasText(comment)) {
            throw new RuntimeException("拒绝原因不能为空");
        }
        application.setStatus(STATUS_REJECTED);
        application.setReviewerId(reviewerId);
        application.setReviewComment(comment.trim());
        if (applicationMapper.updateReviewResult(application) <= 0) {
            throw new RuntimeException("申请状态更新失败");
        }
        return "申请已拒绝";
    }

    private PermissionApplication getPendingApplication(Long applicationId) {
        if (applicationId == null) {
            throw new RuntimeException("申请ID不能为空");
        }
        PermissionApplication application = applicationMapper.selectById(applicationId);
        if (application == null) {
            throw new RuntimeException("申请不存在");
        }
        if (!STATUS_PENDING.equals(application.getStatus())) {
            throw new RuntimeException("申请已处理，不能重复操作");
        }
        return application;
    }

    private int normalizePage(Integer page) {
        return page == null || page < 1 ? 1 : page;
    }

    private int normalizeSize(Integer size) {
        return size == null || size < 1 ? 10 : Math.min(size, 100);
    }

    private String normalizeStatus(String status) {
        if (!StringUtils.hasText(status)) {
            return null;
        }
        String normalized = status.trim().toUpperCase();
        if (!STATUS_PENDING.equals(normalized) && !STATUS_APPROVED.equals(normalized) && !STATUS_REJECTED.equals(normalized)) {
            throw new RuntimeException("申请状态参数错误");
        }
        return normalized;
    }

    private PageResult<PermissionApplication> toPageResult(PageInfo<PermissionApplication> pageInfo) {
        return new PageResult<>(
                pageInfo.getList(),
                pageInfo.getTotal(),
                (long) pageInfo.getPageNum(),
                (long) pageInfo.getPageSize()
        );
    }
}
