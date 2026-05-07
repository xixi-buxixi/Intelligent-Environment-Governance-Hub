# 智能环境治理中枢平台 - 微服务规范化 TODO

> 创建时间：2026-03-25
> 最后更新：2026-03-27
> 项目目标：打造一个完美符合规范的 Spring Cloud Alibaba 微服务项目

---

## 一、项目现状分析

### 1.1 模块结构

| 模块 | 状态 | 说明 |
|------|------|------|
| common-core | ✅ 已创建 | 公共核心模块（无Web依赖），包含枚举、工具类、通用实体 |
| common-web | ✅ 已创建 | 公共Web模块，包含过滤器、拦截器 |
| gateway-service | ✅ 已创建 | API网关服务，已配置路由和跨域 |
| user-service | ✅ 已创建 | 用户服务，已依赖 common-web |
| assistant-service | ✅ 已创建 | AI 助手服务 |
| data-service | ✅ 已创建 | 数据服务 |

### 1.2 已集成组件

- [x] Spring Boot 3.2.5
- [x] Spring Cloud 2023.0.1
- [x] Spring Cloud Alibaba 2023.0.1.0
- [x] Nacos 服务注册发现
- [x] OpenFeign 服务调用
- [x] LoadBalancer 负载均衡
- [x] JWT 认证
- [x] Gateway 网关（路由、跨域、JWT过滤器）

### 1.3 待解决问题

| 问题 | 严重程度 | 状态 |
|------|----------|------|
| 根目录旧代码未清理 | 🔴 高 | ❌ 待处理 |
| ~~assistant-service/data-service 依赖未更新~~ | 🔴 高 | ✅ 已完成 |
| 缺少 Nacos 配置中心 | 🟡 中 | ⚠️ 部分完成 |
| 缺少 Sentinel 限流熔断 | 🟡 中 | ⚠️ 部分完成 |
| 缺少统一异常处理 | 🟡 中 | ❌ 待处理 |
| 缺少 API 文档（Knife4j） | 🟡 中 | ❌ 待处理 |
| 缺少参数校验 | 🟡 中 | ❌ 待处理 |
| 包名不规范（大写开头） | 🟡 中 | ❌ 待处理 |
| 缺少 MyBatis-Plus | 🟡 中 | ❌ 待处理 |
| 缺少 Docker 部署 | 🟢 低 | ❌ 待处理 |

---

## 二、阶段一：基础架构整改（优先级：🔴 高）

---

### 2.1 清理根目录旧代码 ✅

**状态：❌ 待处理**

#### 问题说明

根目录 `D:\My\Java\project\Intelligent-Environment-Governance-Hub\bakc-end-cloud\src\` 包含单体架构遗留代码，与微服务架构混乱，需要删除。

当前存在的旧文件：
```
src/main/java/com/environment/
├── EnvironmentHubApplication.java     # 旧启动类
├── controller/                        # 旧 Controller
├── service/                           # 旧 Service
├── mapper/                            # 旧 Mapper
├── pojo/                              # 旧实体类
├── enums/                             # 旧枚举
├── util/                              # 旧工具类
├── Filter/                            # 旧过滤器
├── Interceptor/                       # 旧拦截器
├── config/                            # 旧配置
├── Listener/                          # 旧监听器
├── Initializer/                       # 旧初始化器
├── Constants/                         # 旧常量
└── repository/                        # 旧仓库
```

#### 具体操作

**步骤 2.1.1：关闭 IDEA 或刷新 Maven**

确保没有进程占用文件。

**步骤 2.1.2：删除 src 文件夹**

在项目根目录执行：
```cmd
rmdir /s /q src
```

**步骤 2.1.3：删除 target 文件夹**

```cmd
rmdir /s /q target
```

#### 验证方式

- 根目录下只剩下模块文件夹（common-core、common-web、gateway-service 等）
- IDEA 中不再显示根目录下的 Java 源码

---

### 2.2 更新业务服务依赖 ✅

**状态：✅ 已完成**

#### 问题说明

- user-service：✅ 已依赖 common-web
- assistant-service：✅ 已更新（pom.xml 已修改为 common-web）
- data-service：✅ 已更新（pom.xml 已修改为 common-web）

#### 已完成的修改

**assistant-service/pom.xml**
```xml
<dependency>
    <groupId>com.environment</groupId>
    <artifactId>common-web</artifactId>
    <version>1.0.0</version>
</dependency>
```

**data-service/pom.xml**
```xml
<dependency>
    <groupId>com.environment</groupId>
    <artifactId>common-web</artifactId>
    <version>1.0.0</version>
</dependency>
```

---

### 2.3 Gateway 网关服务 ✅

**状态：✅ 已完成**

#### 已完成内容

| 组件 | 状态 | 文件路径 |
|------|------|----------|
| 启动类 | ✅ | `gateway-service/.../GatewayServiceApplication.java` |
| 路由配置 | ✅ | `gateway-service/.../application.yaml` |
| 跨域配置 | ✅ | `gateway-service/.../application.yaml` |
| JWT 过滤器 | ✅ | `gateway-service/.../filter/AuthGlobalFilter.java` |
| Nacos 注册 | ✅ | `gateway-service/.../application.yaml` |

#### 当前路由配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://userService
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=1

        - id: assistant-service
          uri: lb://assistant-service
          predicates:
            - Path=/api/assistant/**
          filters:
            - StripPrefix=1

        - id: data-service
          uri: lb://data-service
          predicates:
            - Path=/api/data/**
          filters:
            - StripPrefix=1
```

#### 请求转发示例

| 前端请求 | StripPrefix=1 后 | 转发到服务 |
|----------|-------------------|------------|
| `GET /api/user/login` | `/user/login` | userService |
| `POST /api/assistant/chat` | `/assistant/chat` | assistant-service |
| `GET /api/data/list` | `/data/list` | data-service |

---

### 2.4 Common 模块拆分 ✅

**状态：✅ 已完成**

#### 拆分方案

| 模块 | 内容 | 依赖 | 使用方 |
|------|------|------|--------|
| common-core | 纯工具类（JWT、枚举、Result） | 无 Web | Gateway |
| common-web | Web 相关（过滤器、拦截器） | common-core + web | 业务服务 |

#### common-core 目录结构

```
common-core/src/main/java/com/environment/common/
├── enums/
│   ├── RoleEnum.java
│   └── StatusEnum.java
├── pojo/
│   ├── PageDTO.java
│   ├── PageResult.java
│   ├── Result.java
│   ├── User.java
│   └── UserContext.java
└── utils/
    ├── CaptchaUtil.java
    └── JwtUtil.java
```

#### common-web 目录结构

```
common-web/src/main/java/com/environment/common/
├── Filter/
│   ├── CorsFilter.java
│   └── JwtAuthFilter.java
└── Interceptor/
    └── LoginInterceptor.java
```

#### 为什么这样拆分？

**问题**：Gateway 基于 WebFlux（响应式），不能引入 `spring-boot-starter-web`，否则会冲突。

**解决**：
- Gateway 只依赖 `common-core`（无 Web 依赖）
- 业务服务依赖 `common-web`（包含 Web 依赖）

---

### 2.5 启用 Nacos 配置中心

**状态：⚠️ 部分完成**

#### 已完成内容

| 步骤 | 状态 | 说明 |
|------|------|------|
| 添加 spring-cloud-starter-bootstrap | ✅ | common-core 已添加 |
| 创建 bootstrap.yaml | ✅ | user-service、assistant-service、data-service 已创建 |
| 添加 nacos-config 依赖 | ❌ | common-core 缺少此依赖 |
| 在 Nacos 创建配置 | ❌ | 需要手动创建 |

#### 已创建的 bootstrap.yaml

**user-service/src/main/resources/bootstrap.yaml**
```yaml
spring:
  application:
    name: userService
  profiles:
    active: dev
  cloud:
    nacos:
      config:
        server-addr: localhost:8848
        file-extension: yaml
        shared-configs:
          - data-id: common.yaml
            group: DEFAULT_GROUP
            refresh: true
```

**assistant-service/src/main/resources/bootstrap.yaml**
```yaml
spring:
  application:
    name: assistantService
  profiles:
    active: dev
  cloud:
    nacos:
      config:
        server-addr: localhost:8848
        file-extension: yaml
        shared-configs:
          - data-id: common.yaml
            group: DEFAULT_GROUP
            refresh: true
```

**data-service/src/main/resources/bootstrap.yaml**
```yaml
spring:
  application:
    name: dataService
  profiles:
    active: dev
  cloud:
    nacos:
      config:
        server-addr: localhost:8848
        file-extension: yaml
        shared-configs:
          - data-id: common.yaml
            group: DEFAULT_GROUP
            refresh: true
```

#### 待完成操作

**步骤 2.5.1：在 common-core 添加 Nacos Config 依赖**

```xml
<!-- common-core/pom.xml 添加 -->
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
</dependency>
```

**步骤 2.5.2：在 Nacos 控制台创建配置**

访问：http://localhost:8848/nacos

创建公共配置 `common.yaml`：
- Data ID：`common.yaml`
- Group：`DEFAULT_GROUP`
- 配置内容：

```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/${spring.application.name}?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
    username: root
    password: 200575
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
    sentinel:
      transport:
        dashboard: localhost:8858
        port: 8719
      eager: true
feign:
  sentinel:
    enabled: true
```

**步骤 2.5.3：验证配置加载**

启动服务后，检查日志中是否有：
```
Located property source: [BootstrapPropertySource {name='bootstrapProperties-common.yaml,DEFAULT_GROUP'}]
```

---

## 三、阶段二：核心组件集成（优先级：🟡 中）

---

### 3.1 集成 Sentinel 限流熔断

**状态：⚠️ 部分完成**

#### 已完成内容

| 步骤 | 状态 | 说明 |
|------|------|------|
| 添加 Sentinel 依赖 | ✅ | common-web 已添加 spring-cloud-starter-alibaba-sentinel |
| 配置 Dashboard 地址 | ⚠️ | 需要在 Nacos 配置中添加 |
| OpenFeign 整合 Sentinel | ⚠️ | 需要在 Nacos 配置中添加 feign.sentinel.enabled |
| 创建降级处理类 | ❌ | 待创建 |
| 自定义限流响应 | ❌ | 待创建 |

#### 已添加的依赖

**common-web/pom.xml**
```xml
<!-- Sentinel 核心依赖 -->
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

#### 待完成操作

**步骤 3.1.1：Gateway 添加 Sentinel Gateway 支持**

在 `gateway-service/pom.xml` 中添加：

```xml
<!-- Sentinel Gateway 支持 -->
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-alibaba-sentinel-gateway</artifactId>
</dependency>
```

**步骤 3.1.2：在 Nacos common.yaml 中已配置**

```yaml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8858
        port: 8719
      eager: true
feign:
  sentinel:
    enabled: true
```

**步骤 3.1.3：创建 Feign 客户端和降级处理类**

> **位置说明**：
> - Feign 客户端接口：各业务服务模块（如 `user-service`）
> - 降级处理类：与 Feign 客户端同模块

**示例：user-service 调用 data-service**

1. 在 `user-service` 中创建 Feign 客户端接口：

```java
// user-service/src/main/java/com/environment/user/client/DataServiceClient.java
package com.environment.user.client;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient(
    value = "data-service",           // 目标服务名
    fallback = DataServiceFallback.class  // 降级处理类
)
public interface DataServiceClient {

    @GetMapping("/data/{id}")
    String getData(@PathVariable("id") Long id);
}
```

2. 在 `user-service` 中创建降级处理类：

```java
// user-service/src/main/java/com/environment/user/fallback/DataServiceFallback.java
package com.environment.user.fallback;

import com.environment.user.client.DataServiceClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class DataServiceFallback implements DataServiceClient {

    @Override
    public String getData(Long id) {
        log.warn("调用 data-service 失败，触发降级，id={}", id);
        return "服务暂时不可用，请稍后重试";
    }
}
```

**步骤 3.1.4：自定义限流响应**

> **位置**：`common-web` 模块（所有服务共用）

```java
// common-web/src/main/java/com/environment/common/handler/SentinelExceptionHandler.java
package com.environment.common.handler;

import com.alibaba.csp.sentinel.adapter.spring.webmvc.callback.BlockExceptionHandler;
import com.alibaba.csp.sentinel.slots.block.BlockException;
import com.alibaba.csp.sentinel.slots.block.degrade.DegradeException;
import com.alibaba.csp.sentinel.slots.block.flow.FlowException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Component
public class SentinelExceptionHandler implements BlockExceptionHandler {

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       BlockException e) throws Exception {
        response.setContentType("application/json;charset=utf-8");

        String message;
        int code = 429;

        if (e instanceof FlowException) {
            message = "访问频率过快，请稍后再试";
        } else if (e instanceof DegradeException) {
            message = "服务已降级，请稍后再试";
            code = 503;
        } else {
            message = "未知限制";
        }

        Map<String, Object> result = new HashMap<>();
        result.put("code", code);
        result.put("message", message);
        result.put("data", null);

        response.getWriter().write(new ObjectMapper().writeValueAsString(result));
    }
}
```

---

### 3.2 统一异常处理

**状态：❌ 待处理**

#### 步骤 3.2.1：创建业务异常类

在 `common-core` 中创建 `exception/BusinessException.java`：

```java
package com.environment.common.exception;

import lombok.Getter;

@Getter
public class BusinessException extends RuntimeException {
    private final Integer code;
    private final String message;

    public BusinessException(String message) {
        super(message);
        this.code = 500;
        this.message = message;
    }

    public BusinessException(Integer code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }
}
```

#### 步骤 3.2.2：创建错误码枚举

在 `common-core` 中创建 `exception/ErrorCode.java`：

```java
package com.environment.common.exception;

import lombok.Getter;

@Getter
public enum ErrorCode {
    SUCCESS(200, "操作成功"),
    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未登录或登录已过期"),
    FORBIDDEN(403, "没有权限访问"),
    NOT_FOUND(404, "资源不存在"),
    INTERNAL_ERROR(500, "服务器内部错误"),
    USER_NOT_FOUND(1001, "用户不存在"),
    PASSWORD_ERROR(1002, "密码错误");

    private final Integer code;
    private final String message;

    ErrorCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}
```

#### 步骤 3.2.3：创建全局异常处理器

在 `common-web` 中创建 `handler/GlobalExceptionHandler.java`：

```java
package com.environment.common.handler;

import com.environment.common.exception.BusinessException;
import com.environment.common.exception.ErrorCode;
import com.environment.common.pojo.Result;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public Result<Void> handleBusinessException(BusinessException e) {
        log.warn("业务异常: code={}, message={}", e.getCode(), e.getMessage());
        return Result.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Void> handleValidationException(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.joining(", "));
        log.warn("参数校验失败: {}", message);
        return Result.error(400, message);
    }

    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return Result.error(ErrorCode.INTERNAL_ERROR);
    }
}
```

#### 步骤 3.2.4：完善 Result 类

更新 `common-core/pojo/Result.java`：

```java
package com.environment.common.pojo;

import com.environment.common.exception.ErrorCode;
import lombok.Data;
import java.io.Serializable;

@Data
public class Result<T> implements Serializable {
    private Integer code;
    private String message;
    private T data;

    public static <T> Result<T> success() {
        return success(null);
    }

    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode(200);
        result.setMessage("操作成功");
        result.setData(data);
        return result;
    }

    public static <T> Result<T> error(String message) {
        return error(500, message);
    }

    public static <T> Result<T> error(Integer code, String message) {
        Result<T> result = new Result<>();
        result.setCode(code);
        result.setMessage(message);
        return result;
    }

    public static <T> Result<T> error(ErrorCode errorCode) {
        return error(errorCode.getCode(), errorCode.getMessage());
    }
}
```

---

### 3.3 集成 API 文档（Knife4j）

**状态：❌ 待处理**

#### 步骤 3.3.1：添加 Knife4j 依赖

在 `common-web/pom.xml` 中添加：

```xml
<dependency>
    <groupId>com.github.xiaoymin</groupId>
    <artifactId>knife4j-openapi3-jakarta-spring-boot-starter</artifactId>
    <version>4.4.0</version>
</dependency>
```

#### 步骤 3.3.2：创建配置类

在 `common-web` 中创建 `config/Knife4jConfig.java`：

```java
package com.environment.common.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class Knife4jConfig {

    @Bean
    public OpenAPI openAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("智能环境治理中枢平台 API")
                        .description("API Documentation")
                        .version("v1.0.0"));
    }
}
```

#### 步骤 3.3.3：在 Controller 中使用注解

```java
@Tag(name = "用户管理", description = "用户相关接口")
@RestController
@RequestMapping("/user")
public class UserController {

    @Operation(summary = "用户登录")
    @PostMapping("/login")
    public Result<String> login(
            @Parameter(description = "用户名") @RequestParam String username,
            @Parameter(description = "密码") @RequestParam String password) {
        return Result.success("登录成功");
    }
}
```

#### 步骤 3.3.4：配置 Gateway 聚合文档

在 `gateway-service/pom.xml` 添加：

```xml
<dependency>
    <groupId>com.github.xiaoymin</groupId>
    <artifactId>knife4j-gateway-spring-boot-starter</artifactId>
    <version>4.4.0</version>
</dependency>
```

在 `application.yaml` 添加：

```yaml
knife4j:
  gateway:
    enabled: true
    strategy: discover
    discover:
      enabled: true
      version: openapi3
```

访问地址：http://localhost:8080/doc.html

---

### 3.4 集成参数校验

**状态：❌ 待处理**

#### 步骤 3.4.1：添加依赖

在 `common-web/pom.xml` 中添加：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

#### 步骤 3.4.2：在 DTO 中使用校验注解

```java
@Data
public class UserRegisterDTO {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 20, message = "用户名长度需在3-20个字符之间")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)[a-zA-Z\\d]{8,}$",
             message = "密码必须包含大小写字母和数字，至少8位")
    private String password;

    @Email(message = "邮箱格式不正确")
    private String email;
}
```

#### 步骤 3.4.3：在 Controller 中启用校验

```java
@PostMapping("/register")
public Result<Void> register(@Valid @RequestBody UserRegisterDTO dto) {
    return Result.success();
}
```

---

### 3.5 集成 MyBatis-Plus

**状态：❌ 待处理**

#### 步骤 3.5.1：添加依赖

在 `common-web/pom.xml` 中添加：

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>3.5.5</version>
</dependency>
```

**注意**：添加后可移除 PageHelper，MyBatis-Plus 自带分页功能。

#### 步骤 3.5.2：配置 MyBatis-Plus

```yaml
mybatis-plus:
  mapper-locations: classpath*:/mapper/**/*.xml
  type-aliases-package: com.environment.*.pojo
  configuration:
    map-underscore-to-camel-case: true
  global-config:
    db-config:
      id-type: auto
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0
```

#### 步骤 3.5.3：配置分页插件

```java
@Configuration
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

#### 步骤 3.5.4：使用示例

```java
// Mapper
@Mapper
public interface UserMapper extends BaseMapper<User> {}

// Service
public PageResult<User> listUsers(Integer pageNum, Integer pageSize, String keyword) {
    Page<User> page = new Page<>(pageNum, pageSize);
    LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
    if (StringUtils.hasText(keyword)) {
        wrapper.like(User::getUsername, keyword);
    }
    Page<User> result = userMapper.selectPage(page, wrapper);
    return new PageResult<>(result.getTotal(), result.getPages(), result.getRecords());
}
```

---

## 四、阶段三：规范化代码（优先级：🟡 中）

---

### 4.1 包名规范化

**状态：❌ 待处理**

#### 问题说明

Java 包名规范是小写字母开头，当前项目中存在大写开头的包名。

#### 需要修改的包名

| 原包名 | 新包名 | 位置 |
|--------|--------|------|
| `Interceptor` | `interceptor` | common-web |
| `Filter` | `filter` | common-web |
| `Constants` | `constants` | common-web（如有） |

#### 修改步骤

1. 在 IDEA 中右键包 → Refactor → Rename
2. 修改为小写名称
3. 检查 import 语句是否自动更新

---

### 4.2 日志规范

**状态：❌ 待处理**

#### 步骤 4.2.1：创建 logback-spring.xml

在 `common-web/src/main/resources/` 创建 `logback-spring.xml`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property name="LOG_PATH" value="./logs"/>
    <property name="APP_NAME" value="environment-hub"/>

    <!-- 控制台输出 -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %highlight(%-5level) %cyan(%logger{50}) - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- INFO 日志文件 -->
    <appender name="INFO_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_PATH}/${APP_NAME}-info.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_PATH}/${APP_NAME}-info.%d{yyyy-MM-dd}.%i.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
    </appender>

    <!-- ERROR 日志文件 -->
    <appender name="ERROR_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_PATH}/${APP_NAME}-error.log</file>
        <filter class="ch.qos.logback.classic.filter.LevelFilter">
            <level>ERROR</level>
            <onMatch>ACCEPT</onMatch>
            <onMismatch>DENY</onMismatch>
        </filter>
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="INFO_FILE"/>
        <appender-ref ref="ERROR_FILE"/>
    </root>

    <logger name="com.environment" level="DEBUG"/>
</configuration>
```

---

## 五、阶段四：部署与运维（优先级：🟢 低）

---

### 5.1 Docker 容器化

**状态：❌ 待处理**

#### docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: environment-mysql
    environment:
      MYSQL_ROOT_PASSWORD: 200575
      TZ: Asia/Shanghai
    ports:
      - "3306:3306"
    volumes:
      - ./mysql-data:/var/lib/mysql
      - ./sql:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    container_name: environment-redis
    ports:
      - "6379:6379"

  nacos:
    image: nacos/nacos-server:v2.2.3
    container_name: environment-nacos
    environment:
      MODE: standalone
    ports:
      - "8848:8848"
      - "9848:9848"

  sentinel:
    image: bladex/sentinel-dashboard:1.8.6
    container_name: environment-sentinel
    ports:
      - "8858:8858"

  gateway-service:
    build: ./gateway-service
    ports:
      - "8080:8080"
    depends_on:
      - nacos

  user-service:
    build: ./user-service
    ports:
      - "8081:8081"
    depends_on:
      - mysql
      - nacos

  assistant-service:
    build: ./assistant-service
    ports:
      - "8082:8082"
    depends_on:
      - mysql
      - redis
      - nacos

  data-service:
    build: ./data-service
    ports:
      - "8083:8083"
    depends_on:
      - mysql
      - nacos
```

---

## 六、执行优先级总览

| 优先级 | 任务 | 状态 | 预计工作量 |
|--------|------|------|------------|
| 🔴 P0 | 清理根目录旧代码 | ❌ | 0.5h |
| 🔴 P0 | 更新 assistant/data-service 依赖 | ✅ 已完成 | - |
| 🟡 P1 | 启用 Nacos 配置中心 | ⚠️ 部分完成 | 0.5h |
| 🟡 P1 | 集成 Sentinel | ⚠️ 部分完成 | 0.5h |
| 🟡 P1 | 统一异常处理 | ❌ | 1h |
| 🟡 P1 | 集成 Knife4j | ❌ | 0.5h |
| 🟡 P1 | 参数校验 | ❌ | 0.5h |
| 🟡 P1 | 集成 MyBatis-Plus | ❌ | 1h |
| 🟡 P2 | 包名规范化 | ❌ | 0.5h |
| 🟡 P2 | 日志规范 | ❌ | 0.5h |
| 🟢 P3 | Docker 容器化 | ❌ | 2h |

---

## 七、下一步行动

**建议立即执行：**

1. **清理根目录旧代码** - 删除 `src/` 和 `target/`
   ```cmd
   rmdir /s /q src
   rmdir /s /q target
   ```

2. **完成 Nacos 配置中心** - 在 common-core 添加 nacos-config 依赖，然后在 Nacos 控制台创建 common.yaml 配置

3. **完成 Sentinel 集成** - 在 gateway-service 添加 sentinel-gateway 依赖，创建降级处理类

4. **集成统一异常处理** - 规范响应格式

---

## 八、当前进展总结（2026-03-27）

### 已完成 ✅

1. **业务服务依赖更新**
   - assistant-service/pom.xml → common-web ✅
   - data-service/pom.xml → common-web ✅

2. **bootstrap.yaml 创建**
   - user-service/src/main/resources/bootstrap.yaml ✅
   - assistant-service/src/main/resources/bootstrap.yaml ✅
   - data-service/src/main/resources/bootstrap.yaml ✅

3. **Sentinel 依赖**
   - common-web/pom.xml 已添加 spring-cloud-starter-alibaba-sentinel ✅

### 部分完成 ⚠️

1. **Nacos 配置中心**
   - bootstrap.yaml 已创建 ⚠️
   - 缺少 nacos-config 依赖 ❌
   - 缺少 Nacos 控制台配置 ❌

2. **Sentinel 集成**
   - 依赖已添加 ⚠️
   - 缺少 gateway-sentinel 依赖 ❌
   - 缺少降级处理类 ❌

### 待处理 ❌

1. 根目录 src/target 清理
2. 统一异常处理
3. Knife4j API 文档
4. 参数校验
5. MyBatis-Plus
6. 包名规范化
7. 日志规范
8. Docker 容器化

---

*本文档将随项目进展持续更新*