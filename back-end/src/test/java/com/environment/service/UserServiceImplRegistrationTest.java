package com.environment.service;

import com.environment.mapper.UserMapper;
import com.environment.pojo.DTO.UserRegisterRequest;
import com.environment.pojo.User;
import com.environment.service.impl.UserServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class UserServiceImplRegistrationTest {

    @Mock
    private UserMapper userMapper;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void registerCreatesEnabledNormalUserEvenWhenPrivilegedRoleIsSubmitted() {
        UserRegisterRequest request = new UserRegisterRequest();
        request.setUsername("new_user");
        request.setPassword("123456");
        request.setRealName("新用户");
        request.setEmail("new@example.com");
        request.setPhone("13800138010");
        request.setDepartment("环境监测部");
        request.setRole("ADMIN");

        when(userMapper.selectByUsername("new_user")).thenReturn(null);
        when(userMapper.insert(any(User.class))).thenReturn(1);

        Integer result = userService.register(request);

        assertEquals(1, result);
        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(userMapper).insert(captor.capture());
        User saved = captor.getValue();
        assertEquals("new_user", saved.getUsername());
        assertEquals("USER", saved.getRole());
        assertEquals(1, saved.getStatus());
    }

    @Test
    void registerRejectsDuplicateUsername() {
        UserRegisterRequest request = new UserRegisterRequest();
        request.setUsername("existing");
        request.setPassword("123456");
        request.setRealName("重复用户");

        User existing = new User();
        existing.setId(10L);
        existing.setUsername("existing");
        when(userMapper.selectByUsername("existing")).thenReturn(existing);

        RuntimeException ex = assertThrows(RuntimeException.class, () -> userService.register(request));

        assertEquals("用户名已存在", ex.getMessage());
    }
}
