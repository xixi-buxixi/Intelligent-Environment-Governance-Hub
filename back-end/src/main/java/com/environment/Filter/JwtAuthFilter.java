package com.environment.Filter;

import com.environment.util.JwtUtil;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * JWT认证过滤器
 * 验证请求中的JWT Token
 */
@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    // 不需要验证Token的路径
    private static final String[] EXCLUDE_PATHS = {
            "/auth/login",
            "/auth/register",
            "/auth/captcha",
            "/system/health",
            "/system/info",
            "/system/captcha",
            "/data/crawl/notify"
    };

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        String requestURI = request.getRequestURI();

        // 检查是否是排除路径
        for (String excludePath : EXCLUDE_PATHS) {
            if (requestURI.endsWith(excludePath)) {
                filterChain.doFilter(request, response);
                return;
            }
        }

        // 获取Token
        String authHeader = request.getHeader(JwtUtil.HEADER_NAME);

        if (authHeader != null && authHeader.startsWith(JwtUtil.TOKEN_PREFIX)) {
            String token = authHeader.substring(JwtUtil.TOKEN_PREFIX.length());

            // 验证Token
            if (JwtUtil.validateToken(token)) {
                // Token有效，将用户信息存入request
                String username = JwtUtil.getUsernameFromToken(token);
                Long userId = JwtUtil.getUserIdFromToken(token);

                request.setAttribute("username", username);
                request.setAttribute("userId", userId);
                request.setAttribute("token", token);

                filterChain.doFilter(request, response);
                return;
            }
        }

        // OPTIONS请求直接放行
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            filterChain.doFilter(request, response);
            return;
        }

        // Token无效，返回错误
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":401,\"message\":\"未授权，请先登录\",\"data\":null}");
    }
}
