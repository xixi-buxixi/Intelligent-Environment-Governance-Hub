package com.environment.userservice.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.environment.common.pojo.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 用户Mapper接口
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {

    /**
     * 根据用户名查询用户
     * @param username 用户名
     * @return 用户对象
     */
    User selectByUsername(@Param("username") String username);

    /**
     * 根据ID查询用户
     * @param id 用户ID
     * @return 用户对象
     */
    User selectById(@Param("id") Long id);

    /**
     * 插入用户
     * @param user 用户对象
     * @return 影响行数
     */
    int insert(User user);

    /**
     * 更新用户
     * @param user 用户对象
     * @return 影响行数
     */
    int update(User user);

    /**
     * 删除用户
     * @param id 用户ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);

    /**
     * 查询所有用户列表
     * @return 用户列表
     */
    List<User> selectList();

    /**
     * 根据角色查询用户列表
     * @param role 角色（可选）
     * @return 用户列表
     */
    List<User> selectListByRole(@Param("role") String role);

}