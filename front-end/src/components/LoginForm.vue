<template>
  <div class="login-container">
    <!-- 左侧功能卡片 -->
    <div class="cards-container">
      <div class="func-card" v-for="(item, index) in funcCards" :key="index"
           :class="{ 'active': item.active, 'disabled': !item.active }">
        <i :class="item.icon"></i>
        <span>{{ item.name }}</span>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-section">
      <div class="login-card">
        <!-- Logo -->
        <div class="logo-area">
          <div class="logo-icon">
            <i class="fas fa-leaf"></i>
          </div>
          <h1 class="logo-title">智能环境治理中枢平台</h1>
          <p class="logo-subtitle">Environment Governance Hub</p>
        </div>

        <!-- 登录表单 -->
        <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>

          <el-form-item prop="captcha">
            <div class="captcha-row">
              <el-input
                v-model="loginForm.captcha"
                placeholder="请输入验证码"
                size="large"
                maxlength="4"
                :prefix-icon="Key"
              />
              <div class="captcha-box" @click="refreshCaptcha" title="点击刷新验证码">
                {{ captchaCode }}
              </div>
            </div>
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
            <el-link type="success" :underline="false">忘记密码？</el-link>
          </div>

          <el-form-item>
            <el-button
              type="success"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          还没有账号？<a href="#">立即注册</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Key } from '@element-plus/icons-vue'
import request from '@/utils/request'

const emit = defineEmits(['login-success'])

const loginFormRef = ref(null)
const loading = ref(false)
const captchaCode = ref('')

const funcCards = ref([
  { name: '环保数据获取', icon: 'fas fa-database', active: true },
  { name: '系统管理', icon: 'fas fa-cog', active: true },
  { name: '待开发', icon: 'fas fa-lock', active: false },
  { name: '待开发', icon: 'fas fa-lock', active: false },
  { name: '待开发', icon: 'fas fa-lock', active: false },
  { name: '待开发', icon: 'fas fa-lock', active: false }
])

const loginForm = reactive({
  username: '',
  password: '',
  captcha: '',
  remember: false
})

const loginRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
})

const refreshCaptcha = () => {
  const chars = '0123456789'
  let code = ''
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  captchaCode.value = code
}

const loadRememberedUser = () => {
  const remembered = localStorage.getItem('rememberedUser')
  if (remembered) {
    loginForm.username = remembered
    loginForm.remember = true
  }
}

const handleLogin = async () => {
  // 验证码校验
  if (loginForm.captcha !== captchaCode.value) {
    ElMessage.error('验证码错误')
    refreshCaptcha()
    return
  }

  // 表单验证
  try {
    await loginFormRef.value.validate()
  } catch (error) {
    return
  }

  loading.value = true

  try {
    const response = await request.post('/auth/login', {
      username: loginForm.username,
      password: loginForm.password,
      captcha: loginForm.captcha
    })

    if (response.code === 200) {
      // 保存token和用户信息
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('userInfo', JSON.stringify(response.data.user))

      // 记住用户
      if (loginForm.remember) {
        localStorage.setItem('rememberedUser', loginForm.username)
      } else {
        localStorage.removeItem('rememberedUser')
      }

      ElMessage.success('登录成功！')

      // 通知父组件登录成功
      emit('login-success', response.data.user)
    } else {
      ElMessage.error(response.message || '登录失败')
      refreshCaptcha()
    }
  } catch (error) {
    console.error('登录请求失败:', error)
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshCaptcha()
  loadRememberedUser()
})
</script>

<style scoped>
.login-container {
  display: flex;
  width: 100%;
  height: 100vh;
  background: url('/images/login-bg.jpg') center center / cover no-repeat fixed;
  position: relative;
}

.cards-container {
  width: 55%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  padding: 40px;
  justify-items: center;
  align-content: center;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.3);
}

.func-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 12px;
  width: 85%;
  padding: 20px 15px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 2px solid transparent;
}

.func-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
  border-color: #67c23a;
  background: rgba(255, 255, 255, 0.95);
}

.func-card i {
  font-size: 32px;
  margin-bottom: 12px;
}

.func-card span {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.func-card.active i {
  color: #67c23a;
}

.func-card.disabled {
  opacity: 0.6;
  cursor: default;
}

.func-card.disabled i {
  color: #999;
}

.func-card.disabled:hover {
  transform: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  border-color: transparent;
}

.login-section {
  width: 45%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.3);
}

.login-card {
  width: 80%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 40px 35px;
}

.logo-area {
  text-align: center;
  margin-bottom: 30px;
}

.logo-icon {
  width: 70px;
  height: 70px;
  background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  box-shadow: 0 6px 20px rgba(46, 125, 50, 0.3);
}

.logo-icon i {
  font-size: 32px;
  color: white;
}

.logo-title {
  font-size: 20px;
  font-weight: 700;
  color: #1b5e20;
  margin-bottom: 5px;
}

.logo-subtitle {
  font-size: 12px;
  color: #81c784;
  letter-spacing: 1px;
}

.login-form .el-input {
  height: 45px;
}

.login-form .el-input__wrapper {
  border-radius: 8px;
}

.login-form .el-form-item {
  margin-bottom: 22px;
}

.captcha-row {
  display: flex;
  gap: 12px;
}

.captcha-row .el-input {
  flex: 1;
}

.captcha-box {
  width: 110px;
  height: 45px;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  font-weight: bold;
  font-family: 'Courier New', monospace;
  letter-spacing: 4px;
  color: #2e7d32;
  user-select: none;
  border: 2px solid #a5d6a7;
  transition: all 0.3s ease;
}

.captcha-box:hover {
  border-color: #4caf50;
  transform: scale(1.02);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  border-radius: 8px;
  background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
  border: none;
}

.login-btn:hover {
  background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #999;
}

.form-footer a {
  color: #67c23a;
  text-decoration: none;
}

.form-footer a:hover {
  color: #2e7d32;
}

@media (max-width: 1024px) {
  .login-container {
    flex-direction: column;
  }

  .cards-container {
    width: 100%;
    height: auto;
    padding: 20px;
    grid-template-columns: repeat(3, 1fr);
  }

  .login-section {
    width: 100%;
    padding: 20px;
  }

  .login-card {
    width: 100%;
    max-width: 450px;
  }
}

@media (max-width: 768px) {
  .cards-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 15px;
  }

  .func-card {
    padding: 15px 10px;
  }

  .func-card i {
    font-size: 24px;
    margin-bottom: 8px;
  }

  .func-card span {
    font-size: 12px;
  }
}
</style>