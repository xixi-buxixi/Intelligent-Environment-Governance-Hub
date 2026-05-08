<template>
  <header class="header">
    <div class="header-left">
      <div class="logo">
        <el-icon><Sunny /></el-icon>
      </div>
      <span class="system-name">{{ title }}</span>
      <el-button v-if="showBack" type="success" plain size="small" @click="handleBack" style="margin-left: 12px;">
        <el-icon><ArrowLeft /></el-icon>
        返回首页
      </el-button>
    </div>
    <div class="header-right">
      <div class="user-info">
        <el-icon><User /></el-icon>
        <span>{{ userName }}</span>
        <span class="user-role" v-if="userRole === 'ADMIN'">管理员</span>
        <span class="user-role" v-else-if="userRole === 'MONITOR'">监测员</span>
      </div>
      <el-button type="danger" plain size="small" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出
      </el-button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  title: {
    type: String,
    default: '智能环境治理中枢平台'
  },
  showBack: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()

const userName = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    const user = JSON.parse(userInfo)
    return user.realName || user.username || '用户'
  }
  return '用户'
})

const userRole = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    const user = JSON.parse(userInfo)
    return user.role || ''
  }
  return ''
})

const handleBack = () => {
  router.push('/')
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('chatSessionId')
    ElMessage.success('退出成功')
    router.push('/')
  }).catch(() => {})
}
</script>

<style scoped>
</style>