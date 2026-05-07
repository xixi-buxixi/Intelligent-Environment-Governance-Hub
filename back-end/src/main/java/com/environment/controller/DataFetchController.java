package com.environment.controller;

import com.environment.pojo.DataFetchRecord;
import com.environment.pojo.DataSource;
import com.environment.pojo.DTO.DataFetchRequestDTO;
import com.environment.pojo.DTO.UserFetchLimitDTO;
import com.environment.pojo.Result;
import com.environment.pojo.User;
import com.environment.service.DataFetchService;
import com.environment.service.DataSourceService;
import com.environment.service.UserService;
import com.environment.util.JwtUtil;
import io.jsonwebtoken.Claims;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/data")
public class DataFetchController {

    @Autowired
    private DataFetchService dataFetchService;

    @Autowired
    private DataSourceService dataSourceService;

    @Autowired
    private UserService userService;

    @GetMapping("/sources")
    public Result<List<DataSource>> getDataSources() {
        return Result.success(dataSourceService.getAllActiveDataSources());
    }

    @GetMapping("/fetch-limit")
    public Result<UserFetchLimitDTO> getFetchLimit(HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        return Result.success(dataFetchService.getUserFetchLimit(user.getId(), user.getRole()));
    }

    @PostMapping("/fetch/preview")
    public Result<Map<String, Object>> fetchPreview(@RequestBody DataFetchRequestDTO requestDTO,
                                                    HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        try {
            Map<String, Object> data = dataFetchService.fetchDataPreview(requestDTO, user.getId(), user.getRole());
            if (Boolean.TRUE.equals(data.get("needConfirm"))) {
                return new Result<>(409, String.valueOf(data.get("message")), data);
            }
            return Result.success(data);
        } catch (IllegalArgumentException e) {
            return Result.badRequest(e.getMessage());
        } catch (RuntimeException e) {
            return Result.error(500, e.getMessage());
        }
    }

    @PostMapping("/fetch/export")
    public void exportCsv(@RequestBody DataFetchRequestDTO requestDTO,
                          HttpServletRequest request,
                          HttpServletResponse response) throws IOException {
        User user = getCurrentUser(request);
        if (user == null) {
            response.setStatus(401);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":401,\"message\":\"未登录或登录已过期\"}");
            return;
        }
        try {
            dataFetchService.exportCsv(requestDTO, response);
        } catch (Exception e) {
            response.setStatus(500);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":500,\"message\":\"导出失败: " + e.getMessage() + "\"}");
        }
    }

    // 兼容旧接口：直接导出
    @PostMapping("/fetch")
    public void fetchData(@RequestBody DataFetchRequestDTO requestDTO,
                          HttpServletRequest request,
                          HttpServletResponse response) throws IOException {
        exportCsv(requestDTO, request, response);
    }

    @PostMapping("/crawl/notify")
    public Result<Void> crawlNotify(@RequestBody Map<String, Object> body) {
        String status = String.valueOf(body.getOrDefault("status", ""));
        String message = String.valueOf(body.getOrDefault("message", ""));
        String finishedAt = String.valueOf(body.getOrDefault("finishedAt", ""));
        dataFetchService.handleCrawlNotify(status, message, finishedAt);
        return Result.success();
    }

    @GetMapping("/records")
    public Result<List<DataFetchRecord>> getUserRecords(HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        return Result.success(dataFetchService.getUserFetchRecords(user.getId()));
    }

    @GetMapping("/all-records")
    public Result<List<DataFetchRecord>> getAllRecords(HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        if (!"ADMIN".equals(user.getRole())) {
            return Result.error(403, "权限不足");
        }
        return Result.success(dataFetchService.getAllFetchRecords());
    }

    @GetMapping("/init-info")
    public Result<Map<String, Object>> getInitInfo(HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }

        Map<String, Object> result = new HashMap<>();
        result.put("sources", dataSourceService.getAllActiveDataSources());
        result.put("fetchLimit", dataFetchService.getUserFetchLimit(user.getId(), user.getRole()));
        result.put("cities", Arrays.asList("宜春", "南昌", "九江", "赣州", "吉安", "上饶", "抚州", "景德镇", "萍乡", "新余", "鹰潭"));
        return Result.success(result);
    }

    private User getCurrentUser(HttpServletRequest request) {
        String token = request.getHeader("Authorization");
        if (token == null || !token.startsWith("Bearer ")) {
            return null;
        }
        token = token.substring(7);
        try {
            Claims claims = JwtUtil.parseToken(token);
            if (claims == null) {
                return null;
            }

            User user = new User();
            Long userId = claims.get("userId", Long.class);
            if (userId == null) {
                Integer idInt = claims.get("userId", Integer.class);
                if (idInt != null) {
                    userId = idInt.longValue();
                }
            }
            user.setId(userId);
            user.setUsername(claims.get("username", String.class));
            String role = claims.get("role", String.class);
            if (role == null || role.isBlank()) {
                User dbUser = userService.getUserById(userId);
                if (dbUser != null) {
                    role = dbUser.getRole();
                }
            }
            user.setRole(role);
            return user;
        } catch (Exception e) {
            return null;
        }
    }
}
