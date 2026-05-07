package com.environment.config;

import com.environment.Interceptor.LoginInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Web MVC 配置类
 * 配置跨域等
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Autowired
    private LoginInterceptor loginInterceptor;

    /**
     * 配置拦截器
     */
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(loginInterceptor)
                .addPathPatterns("/**")  // 拦截所有请求
                .excludePathPatterns(
                        "/auth/login",      // 登录接口
                        "/auth/captcha",    // 验证码接口
                        "/system/captcha",  // 系统验证码接口
                        "/data/crawl/notify", // 爬虫回调
                        "/register",        // 注册接口
                        "/css/**",          // 静态资源
                        "/js/**",           // 静态资源
                        "/images/**",       // 图片资源（可选）
                        "/error"            // 错误页面（可选）
                );
    }

    /**
     * 配置跨域访问
     */
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")              // 所有接口
                .allowedOriginPatterns("*")      // 允许所有来源
                .allowedMethods(                  // 允许的请求方法
                        "GET", "POST", "PUT", "DELETE", "OPTIONS"
                )
                .allowedHeaders("*")              // 允许所有请求头
                .allowCredentials(true)           // 允许携带凭证（如Cookie）
                .maxAge(3600);                     // 预检请求缓存时间（秒）
    }
}
