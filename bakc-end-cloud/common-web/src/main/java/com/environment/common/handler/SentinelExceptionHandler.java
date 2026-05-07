package com.environment.common.handler;

import com.alibaba.csp.sentinel.adapter.spring.webmvc.callback.BlockExceptionHandler;
import com.alibaba.csp.sentinel.slots.block.BlockException;
import com.alibaba.csp.sentinel.slots.block.degrade.DegradeException;
import com.alibaba.csp.sentinel.slots.block.flow.FlowException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Component
public class SentinelExceptionHandler implements BlockExceptionHandler {

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       BlockException e) throws Exception {
        response.setContentType("application/json;charset=utf-8");

        String message;
        int code = 429;

        if (e instanceof FlowException) {
            message = "访问频率过快，请稍后再试";
        } else if (e instanceof DegradeException) {
            message = "服务已降级，请稍后再试";
            code = 503;
        } else {
            message = "未知限制";
        }

        Map<String, Object> result = new HashMap<>();
        result.put("code", code);
        result.put("message", message);
        result.put("data", null);

        response.getWriter().write(new ObjectMapper().writeValueAsString(result));
    }
}