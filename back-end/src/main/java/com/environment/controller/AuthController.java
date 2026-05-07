package com.environment.controller;

import com.environment.pojo.LoginRequest;
import com.environment.pojo.LoginResponse;
import com.environment.pojo.Result;
import com.environment.pojo.User;
import com.environment.pojo.UserContext;
import com.environment.service.UserService;
import com.environment.util.CaptchaUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import java.util.HashMap;
import java.util.Map;

/**
 * 认证控制器
 * 处理登录、登出等认证相关请求
 */
@RestController
@RequestMapping("/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    /**
     * 用户登录
     * @param request 登录请求
     * @param httpRequest HTTP请求
     * @return 登录结果
     */
    @PostMapping("/login")
    public Result<LoginResponse> login(@RequestBody LoginRequest request, HttpServletRequest httpRequest) {
        try {
            // 验证用户名密码
            LoginResponse response = userService.login(request);

            // 登录成功，清除验证码
            HttpSession session = httpRequest.getSession(false);
            if (session != null) {
                session.removeAttribute("captcha");
            }

            return Result.success("登录成功", response);
        } catch (RuntimeException e) {
            return Result.error(e.getMessage());
        } catch (Exception e) {
            return Result.error("登录失败：" + e.getMessage());
        }
    }

    /**
     * 生成验证码
     * @param request HTTP请求
     * @return 验证码
     */
    @GetMapping("/captcha")
    public Result<Map<String, String>> generateCaptcha(HttpServletRequest request) {
        String captcha = CaptchaUtil.generateCaptcha();
        HttpSession session = request.getSession();
        session.setAttribute("captcha", captcha);

        Map<String, String> data = new HashMap<>();
        data.put("captcha", captcha);
        data.put("sessionId", session.getId());

        return Result.success(data);
    }

    /**
     * 用户登出
     * @return 操作结果
     */
    @PostMapping("/logout")
    public Result<String> logout() {
        // JWT是无状态的，客户端删除token即可
        return Result.success("登出成功");
    }

    /**
     * 获取当前用户信息
     * @return 用户信息
     */
    @GetMapping("/userinfo")
    public Result<User> getUserInfo() {
        // 从拦截器设置的UserContext获取当前用户
        User user = UserContext.getUser();
        if (user == null) {
            return Result.unauthorized("未登录");
        }

        // 清除敏感信息
        user.setPassword(null);
        return Result.success(user);
    }

    /**
     * 验证Token有效性
     * @return 验证结果
     */
    @GetMapping("/validate")
    public Result<User> validateToken() {
        // 从拦截器设置的UserContext获取当前用户
        User user = UserContext.getUser();
        if (user == null) {
            return Result.unauthorized("Token无效或已过期");
        }

        // 清除敏感信息
        user.setPassword(null);
        return Result.success("Token有效", user);
    }
}