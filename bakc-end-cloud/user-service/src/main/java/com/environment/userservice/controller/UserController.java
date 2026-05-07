package com.environment.userservice.controller;



import com.environment.common.enums.RoleEnum;
import com.environment.common.pojo.PageDTO;
import com.environment.common.pojo.PageResult;
import com.environment.common.pojo.Result;
import com.environment.common.pojo.User;
import com.environment.userservice.pojo.UserRegisterDTO;
import com.environment.userservice.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
@Tag(name = "用户管理", description = "用户相关接口")
@RestController
@RequestMapping("/system/user")
public class UserController {

    @Autowired
    private UserService userService;




    @Operation(summary = "用户登录")
    @PostMapping("/login")
    public Result<String> login(
            @Parameter(description = "用户名") @RequestParam String username,
            @Parameter(description = "密码") @RequestParam String password) {
        return Result.success("登录成功");
    }

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
            return Result.error("用户名不能为空");
        }
        if (user.getPassword() == null || user.getPassword().trim().isEmpty()) {
            return Result.error("密码不能为空");
        }
        if (user.getRealName() == null || user.getRealName().trim().isEmpty()) {
            return Result.error("真实姓名不能为空");
        }
        if (!RoleEnum.isValid(user.getRole())) {
            return Result.error("角色参数错误");
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
            return Result.error("用户ID不能为空");
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
            return Result.error("用户ID不能为空");
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
            return Result.error("用户ID不能为空");
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
    /**
    *  用户注册
    * */
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody UserRegisterDTO dto) {
        return Result.success();
    }
}