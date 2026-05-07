package com.environment.common.utils;

import java.util.Random;

/**
 * 验证码工具类
 * 用于生成随机验证码
 */
public class CaptchaUtil {

    private static final Random RANDOM = new Random();

    /**
     * 生成4位数字验证码
     * @return 4位数字验证码字符串
     */
    public static String generateCaptcha() {
        StringBuilder captcha = new StringBuilder();
        for (int i = 0; i < 4; i++) {
            captcha.append(RANDOM.nextInt(10));
        }
        return captcha.toString();
    }

    /**
     * 生成指定位数的数字验证码
     * @param length 验证码长度
     * @return 指定位数的数字验证码字符串
     */
    public static String generateCaptcha(int length) {
        if (length <= 0) {
            throw new IllegalArgumentException("验证码长度必须大于0");
        }
        StringBuilder captcha = new StringBuilder();
        for (int i = 0; i < length; i++) {
            captcha.append(RANDOM.nextInt(10));
        }
        return captcha.toString();
    }

    /**
     * 生成包含数字和字母的验证码
     * @param length 验证码长度
     * @return 混合验证码字符串
     */
    public static String generateMixedCaptcha(int length) {
        String chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
        StringBuilder captcha = new StringBuilder();
        Random random = new Random();
        for (int i = 0; i < length; i++) {
            captcha.append(chars.charAt(random.nextInt(chars.length())));
        }
        return captcha.toString();
    }

    /**
     * 验证码比对（忽略大小写）
     * @param input 用户输入的验证码
     * @param expected 正确的验证码
     * @return 是否匹配
     */
    public static boolean verifyCaptcha(String input, String expected) {
        if (input == null || expected == null) {
            return false;
        }
        return input.equalsIgnoreCase(expected.trim());
    }
}