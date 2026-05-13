package com.environment.service;

import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.UserRegisterRequest;
import com.environment.pojo.LoginRequest;
import com.environment.pojo.LoginResponse;
import com.environment.pojo.User;

import java.util.List;

/**
 * 用户服务接口
 */
public interface UserService {


    /**
     * 用户登录
     * @param request 登录请求
     * @return 登录响应
     */
    LoginResponse login(LoginRequest request);

    /**
     * 用户注册，默认注册为普通用户
     * @param request 注册请求
     * @return 影响行数
     */
    Integer register(UserRegisterRequest request);

    /**
     * 根据用户名查询用户
     * @param username 用户名
     * @return 用户对象
     */
    User getUserByUsername(String username);

    /**
     * 根据ID查询用户
     * @param userId 用户ID
     * @return 用户对象
     */
    User getUserById(Long userId) ;

    /**
     * 存储验证码
     * @param sessionId 会话ID
     * @param captcha 验证码
     */
    void saveCaptcha(String sessionId, String captcha) ;

    /**
     * 获取验证码
     * @param sessionId 会话ID
     * @return 验证码
     */
    String getCaptcha(String sessionId) ;

    /**
     * 删除验证码
     * @param sessionId 会话ID
     */
    void removeCaptcha(String sessionId) ;

    /**
     * 获取用户列表（分页）
     * @param page 页码
     * @param size 每页条数
     * @param role 角色筛选（可选）
     * @return 分页结果
     */
    PageResult<User> getUserList(Integer page, Integer size, String role);

    /**
     * 新增用户
     * @param user 用户对象
     * @return 影响行数
     */
    Integer addUser(User user);

    /**
     * 更新用户
     * @param user 用户对象
     * @return 影响行数
     */
    Integer updateUser(User user);

    /**
     * 删除用户
     * @param id 用户ID
     * @return 影响行数
     */
    Integer deleteUser(Long id);

    String updateUserRole(Long currentUserId,String newRole, String password);
}
