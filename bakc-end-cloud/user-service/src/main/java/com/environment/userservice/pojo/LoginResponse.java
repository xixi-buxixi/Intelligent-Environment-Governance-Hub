package com.environment.userservice.pojo;

import com.environment.common.pojo.User;

import java.util.HashMap;
import java.util.Map;

/**
 * 登录响应数据
 */
public class LoginResponse {

    /**
     * JWT Token
     */
    private String token;

    /**
     * 用户信息
     */
    private Map<String, Object> user;

    public LoginResponse() {
        this.user = new HashMap<>();
    }

    public LoginResponse(String token, User user) {
        this.token = token;
        this.user = new HashMap<>();
        if (user != null) {
            this.user.put("id", user.getId());
            this.user.put("username", user.getUsername());
            this.user.put("realName", user.getRealName());
            this.user.put("email", user.getEmail());
            this.user.put("phone", user.getPhone());
            this.user.put("department", user.getDepartment());
            this.user.put("role", user.getRole());
        }
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public Map<String, Object> getUser() {
        return user;
    }

    public void setUser(Map<String, Object> user) {
        this.user = user;
    }

    @Override
    public String toString() {
        return "LoginResponse{" +
                "token='" + token + '\'' +
                ", user=" + user +
                '}';
    }
}