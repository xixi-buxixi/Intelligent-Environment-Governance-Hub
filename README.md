# 智能环境治理中枢平台

## 项目简介
智能环境治理中枢平台是一个环境保护相关的管理系统，提供环境数据监测、分析、预警等功能。

## 项目结构

```
Intelligent-Environment-Governance-Hub/
├── front-end/                    # 前端项目
│   ├── login.html               # 登录页面
│   ├── index.html               # 首页
│   ├── css/
│   │   └── login.css            # 登录页面样式
│   ├── js/
│   │   └── login.js             # 登录页面逻辑
│   └── images/
│       └── login-bg.jpg         # 登录背景图片
│
└── back-end/                     # 后端项目
    ├── pom.xml                   # Maven配置
    └── src/main/
        ├── java/com/environment/
        │   ├── controller/       # 控制器层
        │   │   ├── AuthController.java
        │   │   └── SystemController.java
        │   ├── service/          # 服务层
        │   │   └── UserService.java
        │   ├── pojo/             # 实体类
        │   │   ├── User.java
        │   │   ├── Result.java
        │   │   ├── LoginRequest.java
        │   │   └── LoginResponse.java
        │   ├── util/             # 工具类
        │   │   ├── JwtUtil.java
        │   │   └── CaptchaUtil.java
        │   └── config/           # 配置类
        │       ├── CorsFilter.java
        │       ├── JwtAuthFilter.java
        │       └── WebMvcConfig.java
        ├── resources/
        │   ├── applicationContext.xml
        │   ├── spring-mvc.xml
        │   ├── logback.xml
        │   └── jdbc.properties
        └── webapp/WEB-INF/
            └── web.xml
```

## 技术栈

### 前端
- HTML5 + CSS3 + JavaScript
- Vue.js 2.x
- Axios（HTTP请求）

### 后端
- Java 8+
- Spring MVC 5.x
- JWT（JSON Web Token）
- Maven

## 功能特性

### 登录功能
- 用户名密码登录
- 4位数字验证码校验
- JWT Token认证
- 记住用户名功能
- 环保主题UI设计

### 测试账号
| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| user | user123 | 普通用户 |
| monitor | monitor123 | 监测专员 |

## 运行说明

### 前端运行
直接在浏览器中打开 `front-end/login.html` 文件，或使用本地服务器运行。

### 后端运行
1. 确保安装了JDK 8+和Maven
2. 进入 `back-end` 目录
3. 执行 `mvn clean package` 打包
4. 将war包部署到Tomcat服务器

## API接口

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/captcha` - 获取验证码
- `GET /api/auth/userinfo` - 获取用户信息

### 系统接口
- `GET /api/system/health` - 健康检查
- `GET /api/system/info` - 系统信息

## 开发说明

1. 后端使用Spring MVC框架，未集成Spring Boot
2. JWT Token有效期为24小时
3. 验证码为4位数字，存储在Session中
4. 支持跨域请求（CORS）

## 后续规划

- [ ] 数据库集成（MySQL）
- [ ] 环境数据监测模块
- [ ] 数据可视化大屏
- [ ] 预警通知功能
- [ ] 用户权限管理
- [ ] 操作日志记录