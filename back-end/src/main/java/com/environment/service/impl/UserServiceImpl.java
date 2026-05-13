package com.environment.service.impl;

import com.environment.mapper.UserMapper;
import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.DTO.UserRegisterRequest;
import com.environment.pojo.LoginRequest;
import com.environment.pojo.LoginResponse;
import com.environment.pojo.User;
import com.environment.pojo.UserContext;
import com.environment.service.UserService;
import com.environment.util.JwtUtil;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

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
    public Integer register(UserRegisterRequest request) {
        if (request == null) {
            throw new RuntimeException("注册信息不能为空");
        }
        if (!StringUtils.hasText(request.getUsername())) {
            throw new RuntimeException("用户名不能为空");
        }
        if (!StringUtils.hasText(request.getPassword())) {
            throw new RuntimeException("密码不能为空");
        }
        if (!StringUtils.hasText(request.getRealName())) {
            throw new RuntimeException("真实姓名不能为空");
        }
        String username = request.getUsername().trim();
        if (userMapper.selectByUsername(username) != null) {
            throw new RuntimeException("用户名已存在");
        }

        User user = new User();
        user.setUsername(username);
        user.setPassword(request.getPassword());
        user.setRealName(request.getRealName().trim());
        user.setEmail(trimToNull(request.getEmail()));
        user.setPhone(trimToNull(request.getPhone()));
        user.setDepartment(trimToNull(request.getDepartment()));
        user.setRole("USER");
        user.setStatus(1);
        return userMapper.insert(user);
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

    private String trimToNull(String value) {
        return StringUtils.hasText(value) ? value.trim() : null;
    }
}
