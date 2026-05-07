package com.environment.Filter;

import org.springframework.stereotype.Component;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * CORS跨域过滤器
 * 允许前端跨域访问后端API
 */
@Component
public class CorsFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletResponse httpResponse = (HttpServletResponse) response;
        HttpServletRequest httpRequest = (HttpServletRequest) request;

        // 与 allow-credentials=true 配套：不能返回 *
        String origin = httpRequest.getHeader("Origin");
        if (origin == null || origin.isBlank()) {
            origin = "http://localhost:3000";
        }
        httpResponse.setHeader("Access-Control-Allow-Origin", origin);
        httpResponse.setHeader("Vary", "Origin");

        // 允许的请求方法
        httpResponse.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");

        // 允许的请求头
        httpResponse.setHeader("Access-Control-Allow-Headers",
                "Content-Type, Authorization, X-Requested-With, Accept, Origin");

        // 允许携带凭证
        httpResponse.setHeader("Access-Control-Allow-Credentials", "true");

        // 预检请求的缓存时间（秒）
        httpResponse.setHeader("Access-Control-Max-Age", "3600");

        // 对于OPTIONS预检请求，直接返回200
        if ("OPTIONS".equalsIgnoreCase(httpRequest.getMethod())) {
            httpResponse.setStatus(HttpServletResponse.SC_OK);
            return;
        }

        chain.doFilter(request, response);
    }
}
