package com.environment.controller;

import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.RiskAnalyzeRequest;
import com.environment.pojo.DTO.RiskAnalyzeResponse;
import com.environment.pojo.DTO.RiskOverviewResponse;
import com.environment.pojo.Result;
import com.environment.pojo.RiskAnalysisRecord;
import com.environment.pojo.User;
import com.environment.service.RiskAnalysisService;
import com.environment.service.UserService;
import com.environment.util.JwtUtil;
import io.jsonwebtoken.Claims;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/risk")
public class RiskController {

    @Autowired
    private RiskAnalysisService riskAnalysisService;

    @Autowired
    private UserService userService;

    @GetMapping("/overview")
    public Result<RiskOverviewResponse> overview(@RequestParam(required = false) String city,
                                                 @RequestParam(required = false) String factors,
                                                 @RequestParam(required = false) Integer horizonDays,
                                                 HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        try {
            return Result.success(riskAnalysisService.overview(city, factors, horizonDays, user));
        } catch (IllegalArgumentException e) {
            return Result.badRequest(e.getMessage());
        } catch (Exception e) {
            return Result.error("风险概览获取失败: " + e.getMessage());
        }
    }

    @PostMapping("/analyze")
    public Result<RiskAnalyzeResponse> analyze(@RequestBody RiskAnalyzeRequest analyzeRequest,
                                               HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        try {
            return Result.success("研判完成", riskAnalysisService.analyze(analyzeRequest, user));
        } catch (IllegalArgumentException e) {
            return Result.badRequest(e.getMessage());
        } catch (Exception e) {
            return Result.error("智能研判失败: " + e.getMessage());
        }
    }

    @GetMapping("/records")
    public Result<PageResult<RiskAnalysisRecord>> records(@RequestParam(required = false) Integer page,
                                                          @RequestParam(required = false) Integer size,
                                                          @RequestParam(required = false) String city,
                                                          @RequestParam(required = false) String riskLevel,
                                                          HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        return Result.success(riskAnalysisService.getRecords(page, size, city, riskLevel, user));
    }

    @GetMapping("/records/{id}")
    public Result<RiskAnalysisRecord> recordDetail(@PathVariable Long id, HttpServletRequest request) {
        User user = getCurrentUser(request);
        if (user == null) {
            return Result.error(401, "未登录或登录已过期");
        }
        RiskAnalysisRecord record = riskAnalysisService.getRecordById(id, user);
        if (record == null) {
            return Result.error(404, "研判记录不存在或无权查看");
        }
        return Result.success(record);
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
            if (userId == null) {
                return null;
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
