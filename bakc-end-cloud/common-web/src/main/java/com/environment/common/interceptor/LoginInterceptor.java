package com.environment.common.interceptor;

import com.environment.common.utils.JwtUtil;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 登录拦截器
 * 只解析Token，将用户信息存入请求属性，供下游服务使用
 */
@Component
public class LoginInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws Exception {
        // 对于OPTIONS请求直接放行（CORS预检）
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        // 从请求头获取Token
        String token = extractToken(request);
        if (token == null) {
            return unauthorized(response, "未登录或Token失效");
        }

        // 验证Token
        Claims claims = JwtUtil.parseToken(token);
        if (claims == null) {
            return unauthorized(response, "Token无效或已过期");
        }

        // 将用户信息放入请求属性，供下游服务使用
        Long userId = claims.get("userId", Long.class);
        String username = claims.getSubject();
        request.setAttribute("userId", userId);
        request.setAttribute("username", username);
        return true;
    }

    /**
     * 从请求头提取Token
     */
    private String extractToken(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return null;
        }
        return authHeader.substring(7); // 去掉 "Bearer " 前缀
    }

    /**
     * 返回未授权响应
     */
    private boolean unauthorized(HttpServletResponse response, String message) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"" + message + "\"}");
        return false;
    }
}