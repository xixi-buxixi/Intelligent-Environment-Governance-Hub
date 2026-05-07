package com.environment.userservice.service.serviceImpl;


import com.environment.common.pojo.PageResult;
import com.environment.common.pojo.User;
import com.environment.common.pojo.UserContext;
import com.environment.common.utils.JwtUtil;
import com.environment.userservice.mapper.UserMapper;
import com.environment.userservice.pojo.LoginRequest;
import com.environment.userservice.pojo.LoginResponse;
import com.environment.userservice.service.UserService;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 用户服务实现类
 */
@Service
public class UserServiceImpl implements UserService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public LoginResponse login(LoginRequest request) {
        // 1. 查询用户
        User user = userMapper.selectByUsername(request.getUsername());
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }

        // 2. 验证密码
        if (!user.getPassword().equals(request.getPassword())) {
            throw new RuntimeException("密码错误");
        }

        // 3. 检查状态
        if (user.getStatus() != 1) {
            throw new RuntimeException("账号已被禁用");
        }

        // 4. 生成JWT Token
        String token = JwtUtil.generateToken(user.getId(), user.getUsername());

        // 5. 返回登录响应
        return new LoginResponse(token, user);
    }

    @Override
    public User getUserByUsername(String username) {
        return userMapper.selectByUsername(username);
    }

    @Override
    public User getUserById(Long userId) {
        return userMapper.selectById(userId);
    }

    @Override
    public void saveCaptcha(String sessionId, String captcha) {
        // 后续可使用Redis存储
    }

    @Override
    public String getCaptcha(String sessionId) {
        // 后续可使用Redis存储
        return null;
    }

    @Override
    public void removeCaptcha(String sessionId) {
        // 后续可使用Redis存储
    }

    @Override
    public PageResult<User> getUserList(Integer page, Integer size, String role) {
        // 设置分页参数
        PageHelper.startPage(page, size);
        // 查询列表
        List<User> list = userMapper.selectListByRole(role);
        // 获取分页信息
        PageInfo<User> pageInfo = new PageInfo<>(list);
        // 封装返回结果
        return new PageResult<>(
                pageInfo.getList(),
                pageInfo.getTotal(),
                (long) pageInfo.getPageNum(),
                (long) pageInfo.getPageSize()
        );
    }

    @Override
    public Integer addUser(User user) {
        return userMapper.insert(user);
    }

    @Override
    public Integer updateUser(User user) {
        return userMapper.update(user);
    }

    @Override
    public Integer deleteUser(Long id) {
        return userMapper.deleteById(id);
    }

    @Override
    public String updateUserRole(Long currentUserId, String newRole, String password) {
        // 验证当前管理员的密码
        User CurrentUser = UserContext.getUser();
        String userPassword = CurrentUser.getPassword();
        if(!userPassword.equals(password)){
            return "密码错误";
        }
        User targetUser = userMapper.selectById(currentUserId);
        targetUser.setRole(newRole);
        return userMapper.update(targetUser) > 0 ? "权限修改成功" : "权限修改失败";
    }
}