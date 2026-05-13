<template>
  <div class="login-container">
    <!-- 左侧功能卡片 -->
    <div class="cards-container">
      <div class="func-card" v-for="(item, index) in funcCards" :key="index"
           :class="{ 'active': item.active, 'disabled': !item.active }">
        <i :class="item.icon"></i>
        <span class="func-name">{{ item.name }}</span>
        <small>{{ item.desc }}</small>
        <em>{{ item.scope }}</em>
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
          还没有账号？<a href="#" @click.prevent="openRegisterDialog">立即注册</a>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="registerDialogVisible"
      title="普通用户注册"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-width="86px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="registerForm.realName" placeholder="请输入真实姓名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="registerForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-select v-model="registerForm.department" placeholder="请选择部门" clearable style="width: 100%;">
            <el-option label="环境监测部" value="环境监测部" />
            <el-option label="生态保护部" value="生态保护部" />
            <el-option label="污染防治部" value="污染防治部" />
            <el-option label="信息技术部" value="信息技术部" />
          </el-select>
        </el-form-item>
        <el-alert
          title="注册后默认为普通用户，如需监测员权限可登录后提交权限申请。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="success" :loading="registerLoading" @click="submitRegister">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Key } from '@element-plus/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loading = ref(false)
const registerLoading = ref(false)
const captchaCode = ref('')
const registerDialogVisible = ref(false)

const funcCards = ref([
  { name: '环保数据获取', desc: '多源采集与预览', scope: '登录用户可用', icon: 'fas fa-database', active: true },
  { name: '模型预测', desc: '未来7天空气因子预测', scope: '登录用户可用', icon: 'fas fa-chart-line', active: true },
  { name: '环保小助手', desc: 'RAG知识问答服务', scope: '登录用户可用', icon: 'fas fa-robot', active: true },
  { name: '风险智能研判', desc: '风险评分与治理建议', scope: '登录用户可用', icon: 'fas fa-shield-alt', active: true },
  { name: '权限申请', desc: '普通用户申请监测员', scope: '普通用户可用', icon: 'fas fa-user-shield', active: true },
  { name: '系统管理', desc: '用户管理与注册中心', scope: '管理员可用', icon: 'fas fa-cog', active: true }
])

const loginForm = reactive({
  username: '',
  password: '',
  captcha: '',
  remember: false
})

const registerForm = reactive({
  username: '',
  password: '',
  realName: '',
  email: '',
  phone: '',
  department: ''
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

const registerRules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
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
  if (loginForm.captcha !== captchaCode.value) {
    ElMessage.error('验证码错误')
    refreshCaptcha()
    return
  }

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
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('userInfo', JSON.stringify(response.data.user))

      if (loginForm.remember) {
        localStorage.setItem('rememberedUser', loginForm.username)
      } else {
        localStorage.removeItem('rememberedUser')
      }

      ElMessage.success('登录成功！')
      router.push('/home')
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

const openRegisterDialog = () => {
  Object.assign(registerForm, {
    username: '',
    password: '',
    realName: '',
    email: '',
    phone: '',
    department: ''
  })
  registerDialogVisible.value = true
}

const submitRegister = async () => {
  try {
    await registerFormRef.value.validate()
  } catch (error) {
    return
  }

  registerLoading.value = true
  try {
    const response = await request.post('/auth/register', { ...registerForm })
    if (response.code === 200) {
      ElMessage.success(response.message || '注册成功，请返回登录')
      registerDialogVisible.value = false
      loginForm.username = registerForm.username
      loginForm.password = ''
      refreshCaptcha()
    } else {
      ElMessage.error(response.message || '注册失败')
    }
  } catch (error) {
    console.error('注册请求失败:', error)
  } finally {
    registerLoading.value = false
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
  gap: 24px;
  padding: 40px;
  justify-items: center;
  align-content: center;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.func-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  border-radius: 16px;
  width: 85%;
  padding: 24px 16px;
  text-align: center;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.func-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-color);
  background: rgba(255, 255, 255, 0.95);
}

.func-card i {
  font-size: 32px;
  margin-bottom: 12px;
  transition: transform 0.3s ease;
}

.func-card:hover i {
  transform: scale(1.1);
}

.func-card .func-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.func-card small {
  display: block;
  min-height: 18px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-regular);
  line-height: 1.5;
}

.func-card em {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  margin-top: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #ecfdf5;
  color: var(--primary-dark);
  font-size: 12px;
  font-style: normal;
}

.func-card.active i {
  color: var(--primary-color);
}

.func-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.func-card.disabled i {
  color: var(--text-secondary);
}

.func-card.disabled:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
  border-color: rgba(255, 255, 255, 0.5);
}

.login-section {
  width: 45%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.login-card {
  width: 80%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: var(--shadow-lg);
  padding: 40px;
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.logo-area {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  background: var(--bg-gradient);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.logo-icon i {
  font-size: 28px;
  color: white;
}

.logo-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.025em;
}

.logo-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--primary-light) inset !important;
}

.captcha-row {
  display: flex;
  gap: 12px;
}

.captcha-box {
  width: 110px;
  height: 40px;
  background: var(--primary-light);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 18px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  letter-spacing: 4px;
  color: var(--primary-dark);
  user-select: none;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.captcha-box:hover {
  border-color: var(--primary-color);
  transform: translateY(-1px);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: var(--bg-gradient);
  border: none;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  opacity: 0.9;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}

.form-footer a {
  color: var(--primary-color);
  font-weight: 600;
  text-decoration: none;
}

.form-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 1024px) {
  .login-container {
    flex-direction: column;
  }

  .cards-container {
    width: 100%;
    height: auto;
    padding: 24px;
    grid-template-columns: repeat(3, 1fr);
  }

  .login-section {
    width: 100%;
    padding: 40px 24px;
  }

  .login-card {
    max-width: 450px;
  }
}

@media (max-width: 768px) {
  .cards-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 16px;
  }

  .func-card {
    width: 100%;
    padding: 16px;
  }

  .func-card i {
    font-size: 24px;
    margin-bottom: 8px;
  }
}
</style>
