package com.environment.service;

import com.environment.mapper.PermissionApplicationMapper;
import com.environment.mapper.UserMapper;
import com.environment.pojo.PermissionApplication;
import com.environment.pojo.User;
import com.environment.service.impl.PermissionApplicationServiceImpl;
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
class PermissionApplicationServiceImplTest {

    @Mock
    private PermissionApplicationMapper applicationMapper;

    @Mock
    private UserMapper userMapper;

    @InjectMocks
    private PermissionApplicationServiceImpl service;

    @Test
    void approvePendingApplicationPromotesUserToMonitor() {
        PermissionApplication application = new PermissionApplication();
        application.setId(1L);
        application.setUserId(20L);
        application.setTargetRole("MONITOR");
        application.setStatus("PENDING");

        User user = new User();
        user.setId(20L);
        user.setUsername("normal_user");
        user.setRole("USER");

        when(applicationMapper.selectById(1L)).thenReturn(application);
        when(userMapper.selectById(20L)).thenReturn(user);
        when(applicationMapper.updateReviewResult(any(PermissionApplication.class))).thenReturn(1);
        when(userMapper.update(any(User.class))).thenReturn(1);

        String result = service.approve(1L, 99L, "符合监测员职责");

        assertEquals("申请已同意", result);
        ArgumentCaptor<User> userCaptor = ArgumentCaptor.forClass(User.class);
        verify(userMapper).update(userCaptor.capture());
        assertEquals("MONITOR", userCaptor.getValue().getRole());

        ArgumentCaptor<PermissionApplication> applicationCaptor = ArgumentCaptor.forClass(PermissionApplication.class);
        verify(applicationMapper).updateReviewResult(applicationCaptor.capture());
        assertEquals("APPROVED", applicationCaptor.getValue().getStatus());
        assertEquals(99L, applicationCaptor.getValue().getReviewerId());
    }

    @Test
    void approveRejectsAlreadyReviewedApplication() {
        PermissionApplication application = new PermissionApplication();
        application.setId(2L);
        application.setUserId(20L);
        application.setTargetRole("MONITOR");
        application.setStatus("REJECTED");
        when(applicationMapper.selectById(2L)).thenReturn(application);

        RuntimeException ex = assertThrows(RuntimeException.class, () -> service.approve(2L, 99L, "重新同意"));

        assertEquals("申请已处理，不能重复操作", ex.getMessage());
    }
}
