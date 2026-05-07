package com.environment;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;

/**
 * Spring Boot 启动类
 * 智能环境治理中枢平台
 */
@SpringBootApplication
@MapperScan("com.environment.mapper")
public class EnvironmentHubApplication extends SpringBootServletInitializer {

    /**
     * 支持外部Tomcat部署
     */
    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(EnvironmentHubApplication.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(EnvironmentHubApplication.class, args);
        System.out.println("==========================================");
        System.out.println("   智能环境治理中枢平台启动成功！");
        System.out.println("   访问地址: http://localhost:3000");
        System.out.println("==========================================");
    }
}