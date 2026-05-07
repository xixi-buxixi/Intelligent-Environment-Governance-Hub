package com.environment.controller;


import com.environment.enums.RoleEnum;
import com.environment.pojo.DTO.PageDTO;
import com.environment.pojo.DTO.PageResult;
import com.environment.pojo.Result;
import com.environment.pojo.User;
import com.environment.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/system/user")
public class UserController {

    @Autowired
    private UserService userService;

    /**
     * 获取用户列表（分页）
     */
    @GetMapping("/list")
    public Result<PageResult<User>> getUserList(PageDTO pageDTO) {
        // 获取分页参数
        Integer page = pageDTO.getPage();
        Integer size = pageDTO.getSize();
        String role = pageDTO.getRole();

        // 查询用户列表
        PageResult<User> result = userService.getUserList(page, size, role);
        return Result.success(result);
    }

    /**
     * 新增用户
     */
    @PostMapping("/add")
    public Result<String> addUser(@RequestBody User user) {
        // 参数校验
        if (user.getUsername() == null || user.getUsername().trim().isEmpty()) {
            return Result.badRequest("用户名不能为空");
        }
        if (user.getPassword() == null || user.getPassword().trim().isEmpty()) {
            return Result.badRequest("密码不能为空");
        }
        if (user.getRealName() == null || user.getRealName().trim().isEmpty()) {
            return Result.badRequest("真实姓名不能为空");
        }
        if (!RoleEnum.isValid(user.getRole())) {
            return Result.badRequest("角色参数错误");
        }

        Integer num = userService.addUser(user);
        if (num > 0) {
            return Result.success("新增成功");
        } else {
            return Result.error("新增失败");
        }
    }

    /**
     * 更新用户
     */
    @PostMapping("/update")
    public Result<String> updateUser(@RequestBody User user) {
        if (user.getId() == null) {
            return Result.badRequest("用户ID不能为空");
        }

        Integer num = userService.updateUser(user);
        if (num > 0) {
            return Result.success("更新成功");
        } else {
            return Result.error("更新失败");
        }
    }

    /**
     * 删除用户
     */
    @DeleteMapping("/{id}")
    public Result<String> deleteUser(@PathVariable Long id) {
        if (id == null) {
            return Result.badRequest("用户ID不能为空");
        }

        Integer num = userService.deleteUser(id);
        if (num > 0) {
            return Result.success("删除成功");
        } else {
            return Result.error("删除失败");
        }
    }

    /**
     * 根据ID获取用户
     */
    @GetMapping("/{id}")
    public Result<User> getUserById(@PathVariable Long id) {
        if (id == null) {
            return Result.badRequest("用户ID不能为空");
        }

        User user = userService.getUserById(id);
        if (user != null) {
            // 清除密码，不返回给前端
            user.setPassword(null);
            return Result.success(user);
        } else {
            return Result.error("用户不存在");
        }
    }
}