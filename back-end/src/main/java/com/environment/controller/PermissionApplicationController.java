package com.environment.controller;

import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.PermissionApplicationRequest;
import com.environment.pojo.DTO.PermissionApplicationReviewRequest;
import com.environment.pojo.PermissionApplication;
import com.environment.pojo.Result;
import com.environment.pojo.User;
import com.environment.pojo.UserContext;
import com.environment.service.PermissionApplicationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 权限申请控制器
 */
@RestController
public class PermissionApplicationController {
    private final PermissionApplicationService permissionApplicationService;

    public PermissionApplicationController(PermissionApplicationService permissionApplicationService) {
        this.permissionApplicationService = permissionApplicationService;
    }

    @PostMapping("/permission-applications")
    public Result<Long> submit(@RequestBody PermissionApplicationRequest request) {
        User user = UserContext.getUser();
        if (user == null) {
            return Result.unauthorized("未登录");
        }
        try {
            Long id = permissionApplicationService.submit(user.getId(), request);
            return Result.success("申请已提交", id);
        } catch (RuntimeException e) {
            return Result.badRequest(e.getMessage());
        }
    }

    @GetMapping("/permission-applications/my")
    public Result<PageResult<PermissionApplication>> myApplications(@RequestParam(defaultValue = "1") Integer page,
                                                                    @RequestParam(defaultValue = "10") Integer size) {
        User user = UserContext.getUser();
        if (user == null) {
            return Result.unauthorized("未登录");
        }
        return Result.success(permissionApplicationService.getMyApplications(user.getId(), page, size));
    }

    @GetMapping("/system/permission-applications")
    public Result<PageResult<PermissionApplication>> list(@RequestParam(defaultValue = "1") Integer page,
                                                          @RequestParam(defaultValue = "10") Integer size,
                                                          @RequestParam(required = false) String status) {
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可查看注册中心");
        }
        try {
            return Result.success(permissionApplicationService.getAllApplications(page, size, status));
        } catch (RuntimeException e) {
            return Result.badRequest(e.getMessage());
        }
    }

    @PostMapping("/system/permission-applications/{id}/approve")
    public Result<String> approve(@PathVariable Long id,
                                  @RequestBody(required = false) PermissionApplicationReviewRequest request) {
        User user = UserContext.getUser();
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可审批申请");
        }
        try {
            String message = permissionApplicationService.approve(id, user.getId(), request == null ? null : request.getComment());
            return Result.success(message, null);
        } catch (RuntimeException e) {
            return Result.badRequest(e.getMessage());
        }
    }

    @PostMapping("/system/permission-applications/{id}/reject")
    public Result<String> reject(@PathVariable Long id,
                                 @RequestBody PermissionApplicationReviewRequest request) {
        User user = UserContext.getUser();
        if (!isAdmin()) {
            return Result.error(403, "仅管理员可审批申请");
        }
        try {
            String message = permissionApplicationService.reject(id, user.getId(), request == null ? null : request.getComment());
            return Result.success(message, null);
        } catch (RuntimeException e) {
            return Result.badRequest(e.getMessage());
        }
    }

    private boolean isAdmin() {
        User user = UserContext.getUser();
        return user != null && "ADMIN".equalsIgnoreCase(user.getRole());
    }
}
