<template>
  <div class="home-view">
    <!-- 头部导航 -->
    <AppHeader title="智能环境治理中枢平台" />

    <!-- 主内容 -->
    <main class="main-content">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <h1 class="welcome-title">欢迎使用智能环境治理中枢平台</h1>
        <p class="welcome-desc">Intelligent Environment Governance Hub</p>
      </div>

      <!-- 功能模块 -->
      <div class="module-grid">
        <!-- 环保数据获取 -->
        <div class="module-card" @click="enterModule('data')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><DataCollection /></el-icon>
            </div>
            <span class="card-title">环保数据获取</span>
          </div>
          <div class="card-desc">
            实时数据采集<br>
            多源数据整合
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 模型预测与获取 -->
        <div class="module-card" @click="enterModule('predict')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <span class="card-title">模型预测与获取</span>
          </div>
          <div class="card-desc">
            未来7天空气因子预测<br>
            支持多因子联合查看
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 环保小助手（RAG,Tool） -->
        <div class="module-card" @click="enterModule('assistant')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><Service /></el-icon>
            </div>
            <span class="card-title">环保小助手（RAG,Tool）</span>
          </div>
          <div class="card-desc">
            RAG知识检索<br>
            智能问答服务
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 环境风险智能研判中心 -->
        <div class="module-card" @click="enterModule('risk')">
          <div class="card-header">
            <div class="card-icon blue">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <span class="card-title">环境风险智能研判中心</span>
          </div>
          <div class="card-desc">
            趋势预测与风险评分<br>
            AI成因解释与治理建议
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 权限申请 - 普通用户可见 -->
        <div class="module-card" v-if="userRole === 'USER'" @click="enterModule('permission')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><Lock /></el-icon>
            </div>
            <span class="card-title">权限申请</span>
          </div>
          <div class="card-desc">
            申请监测员权限<br>
            查看申请处理情况
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 待开发模块 -->
        <div class="module-card disabled" v-if="userRole !== 'USER'">
          <div class="card-header">
            <div class="card-icon gray">
              <el-icon><Lock /></el-icon>
            </div>
            <span class="card-title">待开发</span>
          </div>
          <div class="card-desc">
            功能开发中<br>
            敬请期待
          </div>
          <div class="card-status">
            <span class="status-dot pending"></span>
            <span class="status-text">暂未开放</span>
          </div>
        </div>

        <!-- 系统管理 - 仅管理员可见 -->
        <div class="module-card" v-if="userRole === 'ADMIN'" @click="enterModule('system')">
          <div class="card-header">
            <div class="card-icon blue">
              <el-icon><Setting /></el-icon>
            </div>
            <span class="card-title">系统管理</span>
          </div>
          <div class="card-desc">
            用户管理<br>
            权限配置
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'

const router = useRouter()

const userRole = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    const user = JSON.parse(userInfo)
    return user.role || ''
  }
  return ''
})

const enterModule = (module) => {
  if (module === 'data') {
    router.push('/data-fetch')
  } else if (module === 'predict') {
    router.push('/model-predict')
  } else if (module === 'assistant') {
    router.push('/assistant')
  } else if (module === 'risk') {
    router.push('/risk-center')
  } else if (module === 'permission') {
    router.push('/permission-application')
  } else if (module === 'system') {
    if (userRole.value !== 'ADMIN') {
      ElMessage.error('权限不足')
      return
    }
    router.push('/system')
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  background-color: var(--bg-color);
}

.welcome-section {
  background: var(--bg-gradient-light);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 32px;
  border: 1px solid var(--primary-light);
  box-shadow: var(--shadow-sm);
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-dark);
  margin-bottom: 4px;
  letter-spacing: -0.025em;
}

.welcome-desc {
  font-size: 14px;
  color: var(--text-regular);
  font-weight: 500;
}
</style>
