<template>
  <div class="system-view">
    <!-- 头部导航 -->
    <AppHeader title="系统管理" show-back />

    <!-- 主体 -->
    <div class="main-container">
      <!-- 左侧菜单 -->
      <aside class="sidebar">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="user">
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="permission">
            <el-icon><Lock /></el-icon>
            <span>权限配置</span>
          </el-menu-item>
          <el-menu-item index="registerCenter">
            <el-icon><UserFilled /></el-icon>
            <span>注册中心</span>
          </el-menu-item>
          <el-menu-item index="agent">
            <el-icon><Tools /></el-icon>
            <span>Agent配置</span>
          </el-menu-item>
          <el-menu-item index="rag">
            <el-icon><Setting /></el-icon>
            <span>RAG配置</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 右侧内容 -->
      <main class="content-wrapper">
        <!-- 用户管理 -->
        <div v-show="activeMenu === 'user'">
          <h2 class="page-title">用户管理</h2>

          <!-- 搜索区域 -->
          <div class="search-area">
            <div class="search-item">
              <span class="label">角色</span>
              <el-select v-model="searchForm.role" placeholder="全部" clearable>
                <el-option label="管理员" value="ADMIN" />
                <el-option label="普通用户" value="USER" />
                <el-option label="监测员" value="MONITOR" />
              </el-select>
            </div>
            <div class="search-btns">
              <el-button @click="resetSearch">重置</el-button>
              <el-button type="primary" @click="handleSearch">搜索</el-button>
            </div>
          </div>

          <!-- 工具栏 -->
          <div class="toolbar">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增用户
            </el-button>
          </div>

          <!-- 数据表格 -->
          <div class="table-wrapper" v-loading="loading">
            <el-table :data="tableData" stripe style="width: 100%">
              <el-table-column prop="username" label="用户名" min-width="100" />
              <el-table-column prop="realName" label="真实姓名" min-width="100" />
              <el-table-column prop="department" label="部门" min-width="100" />
              <el-table-column label="角色" min-width="100">
                <template #default="scope">
                  <span v-if="scope.row.role === 'ADMIN'">管理员</span>
                  <span v-else-if="scope.row.role === 'USER'">普通用户</span>
                  <span v-else-if="scope.row.role === 'MONITOR'">监测员</span>
                  <span v-else>{{ scope.row.role }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="email" label="邮箱" min-width="150" />
              <el-table-column prop="phone" label="手机号" min-width="120" />
              <el-table-column label="状态" width="80">
                <template #default="scope">
                  <el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">
                    {{ scope.row.status === 1 ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                  <el-button type="primary" link size="small" @click="handleEdit(scope.row)">编辑</el-button>
                  <el-button type="danger" link size="small" @click="handleDelete(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 分页 -->
          <div class="pagination-area">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.size"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>

        <!-- 权限配置 -->
        <div v-show="activeMenu === 'permission'">
          <h2 class="page-title">权限配置</h2>
          <div class="permission-cards" v-loading="loading">
            <div class="user-card" v-for="user in tableData" :key="user.id">
              <div class="user-card-header">
                <span class="user-card-name">{{ user.username }}</span>
                <el-tag :type="getRoleTagType(user.role)" size="small">
                  {{ getRoleName(user.role) }}
                </el-tag>
              </div>
              <div class="user-card-info">
                <div class="info-item">
                  <span class="info-label">部门：</span>
                  <span class="info-value">{{ user.department }}</span>
                </div>
              </div>
              <div class="user-card-permissions">
                <div class="permissions-title">权限说明：</div>
                <ul class="permissions-list">
                  <li v-for="perm in getRolePermissions(user.role)" :key="perm">{{ perm }}</li>
                </ul>
              </div>
              <div class="user-card-actions" v-if="currentUserRole === 'ADMIN'">
                <el-button type="primary" size="small" @click="handlePermissionEdit(user)">
                  修改权限
                </el-button>
              </div>
            </div>
            <div v-if="tableData.length === 0" class="empty-permission">
              暂无用户数据
            </div>
          </div>
        </div>

        <div v-show="activeMenu === 'registerCenter'">
          <h2 class="page-title">注册中心</h2>
          <div class="search-area">
            <div class="search-item">
              <span class="label">处理状态</span>
              <el-select v-model="applicationSearch.status" placeholder="全部" clearable>
                <el-option label="待处理" value="PENDING" />
                <el-option label="已同意" value="APPROVED" />
                <el-option label="已拒绝" value="REJECTED" />
              </el-select>
            </div>
            <div class="search-btns">
              <el-button @click="resetApplicationSearch">重置</el-button>
              <el-button type="primary" @click="searchApplications">搜索</el-button>
            </div>
          </div>

          <div class="table-wrapper" v-loading="applicationLoading">
            <el-table :data="applicationData" stripe style="width: 100%">
              <el-table-column prop="username" label="用户名" min-width="110" />
              <el-table-column prop="realName" label="真实姓名" min-width="110" />
              <el-table-column label="申请权限" width="120">
                <template #default="scope">{{ getRoleName(scope.row.targetRole) }}</template>
              </el-table-column>
              <el-table-column prop="reason" label="申请原因" min-width="220" />
              <el-table-column label="状态" width="110">
                <template #default="scope">
                  <el-tag :type="getApplicationStatusType(scope.row.status)">
                    {{ getApplicationStatusName(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="reviewComment" label="处理意见" min-width="160">
                <template #default="scope">{{ scope.row.reviewComment || '-' }}</template>
              </el-table-column>
              <el-table-column label="提交时间" width="180">
                <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="170" fixed="right">
                <template #default="scope">
                  <template v-if="scope.row.status === 'PENDING'">
                    <el-button type="success" link size="small" @click="openApplicationReview(scope.row, 'approve')">
                      同意
                    </el-button>
                    <el-button type="danger" link size="small" @click="openApplicationReview(scope.row, 'reject')">
                      拒绝
                    </el-button>
                  </template>
                  <span v-else class="muted-text">已处理</span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="pagination-area">
            <el-pagination
              v-model:current-page="applicationPagination.page"
              v-model:page-size="applicationPagination.size"
              :page-sizes="[10, 20, 50, 100]"
              :total="applicationPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleApplicationSizeChange"
              @current-change="loadApplications"
            />
          </div>
        </div>

        <div v-show="activeMenu === 'agent'">
          <h2 class="page-title">Agent配置（仅管理员）</h2>
          <el-card>
            <el-form :model="agentConfig" label-width="140px">
              <el-form-item label="模型名称">
                <el-input v-model="agentConfig.llmModel" />
              </el-form-item>
              <el-form-item label="Temperature">
                <el-input-number v-model="agentConfig.temperature" :step="0.1" :min="0" :max="2" />
              </el-form-item>
              <el-form-item label="最大思考轮数">
                <el-input-number v-model="agentConfig.maxIterations" :min="1" :max="30" />
              </el-form-item>
              <el-form-item label="最大重试次数">
                <el-input-number v-model="agentConfig.maxRetries" :min="0" :max="10" />
              </el-form-item>
              <el-form-item label="最大历史轮数">
                <el-input-number v-model="agentConfig.maxHistory" :min="1" :max="100" />
              </el-form-item>
              <el-form-item label="启用反思">
                <el-switch v-model="agentConfig.enableReflection" />
              </el-form-item>
            </el-form>
            <div class="form-actions">
              <el-button type="primary" @click="saveAgentConfig">保存Agent配置</el-button>
              <el-button @click="loadAgentConfig">刷新</el-button>
            </div>
            <p class="hint-text">保存后需重启 Python 服务生效。</p>
          </el-card>
        </div>

        <div v-show="activeMenu === 'rag'">
          <h2 class="page-title">RAG配置（仅管理员）</h2>

          <el-card class="rag-card">
            <template #header>
              <div class="card-header">LangChain（Python）</div>
            </template>
            <el-form :model="ragLangchain" label-width="140px">
              <el-form-item label="检索 top_k">
                <el-input-number v-model="ragLangchain.retrieveTopK" :min="1" :max="20" />
              </el-form-item>
              <el-form-item label="chunk_size">
                <el-input-number v-model="ragLangchain.chunkSize" :min="100" :max="4000" :step="50" />
              </el-form-item>
              <el-form-item label="chunk_overlap">
                <el-input-number v-model="ragLangchain.chunkOverlap" :min="0" :max="1000" :step="10" />
              </el-form-item>
              <el-form-item label="知识库目录">
                <el-input v-model="ragLangchain.knowledgePath" disabled />
              </el-form-item>
            </el-form>
            <div class="form-actions">
              <el-button type="primary" @click="saveLangchainRagConfig">保存LangChain配置</el-button>
              <el-button @click="openUpload('langchain')">新增知识文件</el-button>
            </div>
            <el-table :data="ragLangchain.files" stripe style="width: 100%; margin-top: 12px">
              <el-table-column prop="name" label="文件名" min-width="220" />
              <el-table-column label="大小(KB)" width="120">
                <template #default="scope">{{ formatKB(scope.row.size) }}</template>
              </el-table-column>
              <el-table-column label="更新时间" min-width="180">
                <template #default="scope">{{ formatTime(scope.row.modifiedAt) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="160">
                <template #default="scope">
                  <el-button type="primary" link @click="editKnowledgeFile('langchain', scope.row.name)">编辑</el-button>
                  <el-button type="danger" link @click="deleteKnowledgeFile('langchain', scope.row.name)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-card class="rag-card">
            <template #header>
              <div class="card-header">LangChain4j（Java）</div>
            </template>
            <el-form :model="ragLangchain4j" label-width="140px">
              <el-form-item label="检索 maxResults">
                <el-input-number v-model="ragLangchain4j.maxResults" :min="1" :max="20" />
              </el-form-item>
              <el-form-item label="检索 minScore">
                <el-input-number v-model="ragLangchain4j.minScore" :step="0.05" :min="0" :max="1" />
              </el-form-item>
              <el-form-item label="记忆 maxMessages">
                <el-input-number v-model="ragLangchain4j.memoryMaxMessages" :min="1" :max="200" />
              </el-form-item>
              <el-form-item label="chunk_size">
                <el-input-number v-model="ragLangchain4j.chunkSize" :min="100" :max="4000" :step="50" />
              </el-form-item>
              <el-form-item label="chunk_overlap">
                <el-input-number v-model="ragLangchain4j.chunkOverlap" :min="0" :max="1000" :step="10" />
              </el-form-item>
              <el-form-item label="知识库目录">
                <el-input v-model="ragLangchain4j.knowledgePath" disabled />
              </el-form-item>
            </el-form>
            <div class="form-actions">
              <el-button type="primary" @click="saveLangchain4jRagConfig">保存LangChain4j配置</el-button>
              <el-button @click="openUpload('langchain4j')">新增知识文件</el-button>
            </div>
            <el-table :data="ragLangchain4j.files" stripe style="width: 100%; margin-top: 12px">
              <el-table-column prop="name" label="文件名" min-width="220" />
              <el-table-column label="大小(KB)" width="120">
                <template #default="scope">{{ formatKB(scope.row.size) }}</template>
              </el-table-column>
              <el-table-column label="更新时间" min-width="180">
                <template #default="scope">{{ formatTime(scope.row.modifiedAt) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="160">
                <template #default="scope">
                  <el-button type="primary" link @click="editKnowledgeFile('langchain4j', scope.row.name)">编辑</el-button>
                  <el-button type="danger" link @click="deleteKnowledgeFile('langchain4j', scope.row.name)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <p class="hint-text">LangChain配置保存后需重启Python；LangChain4j配置保存后需重启Java。</p>
        </div>
      </main>
    </div>

    <!-- 用户编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="userForm.realName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-select v-model="userForm.department" placeholder="请选择部门" style="width: 100%;">
            <el-option label="信息技术部" value="信息技术部" />
            <el-option label="环境监测部" value="环境监测部" />
            <el-option label="生态保护部" value="生态保护部" />
            <el-option label="污染防治部" value="污染防治部" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" :disabled="isEdit" style="width: 100%;">
            <el-option label="管理员" value="ADMIN" />
            <el-option label="普通用户" value="USER" />
            <el-option label="监测员" value="MONITOR" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="userForm.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 权限修改对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="修改用户权限"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="permissionForm" ref="permissionFormRef" label-width="80px">
        <el-form-item label="用户名">
          <el-input :value="permissionForm.username" disabled />
        </el-form-item>
        <el-form-item label="当前角色">
          <el-tag :type="getRoleTagType(permissionForm.oldRole)" size="small">
            {{ getRoleName(permissionForm.oldRole) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="新角色" prop="newRole">
          <el-select v-model="permissionForm.newRole" placeholder="请选择角色" style="width: 100%;">
            <el-option label="管理员" value="ADMIN" />
            <el-option label="普通用户" value="USER" />
            <el-option label="监测员" value="MONITOR" />
          </el-select>
        </el-form-item>
        <el-form-item label="确认密码" prop="password">
          <el-input v-model="permissionForm.password" type="password" placeholder="请输入您的密码确认" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPermissionChange">确认修改</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="applicationReviewDialogVisible"
      :title="applicationReviewMode === 'approve' ? '同意权限申请' : '拒绝权限申请'"
      width="460px"
      :close-on-click-modal="false"
    >
      <el-form :model="applicationReviewForm" label-width="90px">
        <el-form-item label="申请用户">
          <el-input :value="applicationReviewForm.username" disabled />
        </el-form-item>
        <el-form-item label="申请权限">
          <el-input :value="getRoleName(applicationReviewForm.targetRole)" disabled />
        </el-form-item>
        <el-form-item label="处理意见">
          <el-input
            v-model="applicationReviewForm.comment"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            :placeholder="applicationReviewMode === 'approve' ? '可填写同意说明' : '请填写拒绝原因'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applicationReviewDialogVisible = false">取消</el-button>
        <el-button
          :type="applicationReviewMode === 'approve' ? 'success' : 'danger'"
          :loading="applicationReviewLoading"
          @click="submitApplicationReview"
        >
          确认
        </el-button>
      </template>
    </el-dialog>

    <input
      ref="uploadInputRef"
      type="file"
      style="display: none"
      @change="handleFileSelected"
    />

    <el-dialog
      v-model="knowledgeEditorVisible"
      :title="`编辑知识文件：${knowledgeEditor.fileName || ''}`"
      width="70%"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="knowledgeEditor.content"
        type="textarea"
        :rows="20"
        placeholder="请输入文件内容"
      />
      <template #footer>
        <el-button @click="knowledgeEditorVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKnowledgeFileContent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import request from '@/utils/request'

const router = useRouter()

const activeMenu = ref('user')
const loading = ref(false)
const userFormRef = ref(null)
const permissionFormRef = ref(null)

const currentUserRole = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    const user = JSON.parse(userInfo)
    return user.role || ''
  }
  return ''
})

const searchForm = reactive({
  role: ''
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const tableData = ref([])
const applicationLoading = ref(false)
const applicationData = ref([])

const applicationSearch = reactive({
  status: ''
})

const applicationPagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

const userForm = reactive({
  id: null,
  username: '',
  password: '',
  realName: '',
  email: '',
  phone: '',
  department: '',
  role: '',
  status: 1
})

const userRules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
})

const permissionDialogVisible = ref(false)
const permissionForm = reactive({
  userId: null,
  username: '',
  oldRole: '',
  newRole: '',
  password: ''
})

const applicationReviewDialogVisible = ref(false)
const applicationReviewLoading = ref(false)
const applicationReviewMode = ref('approve')
const applicationReviewForm = reactive({
  id: null,
  username: '',
  targetRole: 'MONITOR',
  comment: ''
})

const uploadInputRef = ref(null)
const uploadEngine = ref('langchain')
const knowledgeEditorVisible = ref(false)
const knowledgeEditor = reactive({
  engine: 'langchain',
  fileName: '',
  content: ''
})

const agentConfig = reactive({
  llmModel: '',
  temperature: 0.7,
  maxIterations: 6,
  maxRetries: 3,
  maxHistory: 10,
  enableReflection: true
})

const ragLangchain = reactive({
  retrieveTopK: 3,
  chunkSize: 500,
  chunkOverlap: 100,
  knowledgePath: '',
  files: []
})

const ragLangchain4j = reactive({
  maxResults: 3,
  minScore: 0.6,
  memoryMaxMessages: 20,
  chunkSize: 500,
  chunkOverlap: 100,
  knowledgePath: '',
  files: []
})

// 检查权限
const checkPermission = () => {
  if (currentUserRole.value !== 'ADMIN') {
    ElMessage.error('权限不足')
    router.push('/')
  }
}

// 获取用户列表
const fetchUserList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (searchForm.role) {
      params.role = searchForm.role
    }

    const response = await request.get('/system/user/list', { params })
    if (response.code === 200) {
      tableData.value = response.data.records || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

const resetSearch = () => {
  searchForm.role = ''
  pagination.page = 1
  fetchUserList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchUserList()
}

const handlePageChange = () => {
  fetchUserList()
}

const handleMenuSelect = (index) => {
  activeMenu.value = index
  if (index === 'agent') {
    loadAgentConfig()
  } else if (index === 'rag') {
    loadRagConfig()
  } else if (index === 'registerCenter') {
    loadApplications()
  }
}

const handleAdd = () => {
  isEdit.value = false
  resetUserForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(userForm, {
    id: row.id,
    username: row.username,
    realName: row.realName,
    email: row.email,
    phone: row.phone,
    department: row.department,
    role: row.role,
    status: row.status
  })
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const response = await request.delete(`/system/user/${row.id}`)
      if (response.code === 200) {
        ElMessage.success('删除成功')
        fetchUserList()
      }
    } catch (error) {
      console.error('删除用户失败:', error)
    }
  }).catch(() => {})
}

const resetUserForm = () => {
  Object.assign(userForm, {
    id: null,
    username: '',
    password: '',
    realName: '',
    email: '',
    phone: '',
    department: '',
    role: '',
    status: 1
  })
}

const submitForm = async () => {
  try {
    await userFormRef.value.validate()
  } catch (error) {
    return
  }

  try {
    const url = isEdit.value ? '/system/user/update' : '/system/user/add'
    const response = await request.post(url, userForm)
    if (response.code === 200) {
      ElMessage.success(isEdit.value ? '修改成功' : '新增成功')
      dialogVisible.value = false
      fetchUserList()
    }
  } catch (error) {
    console.error('提交失败:', error)
  }
}

const getRoleName = (role) => {
  const roleMap = {
    'ADMIN': '管理员',
    'USER': '普通用户',
    'MONITOR': '监测员'
  }
  return roleMap[role] || role
}

const getRoleTagType = (role) => {
  const typeMap = {
    'ADMIN': 'danger',
    'USER': 'success',
    'MONITOR': 'warning'
  }
  return typeMap[role] || 'info'
}

const getRolePermissions = (role) => {
  const permissionsMap = {
    'ADMIN': ['可进行用户管理', '可进行权限配置', '可查看所有数据', '可进行系统设置'],
    'USER': ['可查看个人数据', '可提交环保数据', '可查看数据报表'],
    'MONITOR': ['可查看监测数据', '可进行数据采集', '可生成监测报告']
  }
  return permissionsMap[role] || ['暂无权限说明']
}

const handlePermissionEdit = (user) => {
  Object.assign(permissionForm, {
    userId: user.id,
    username: user.username,
    oldRole: user.role,
    newRole: user.role,
    password: ''
  })
  permissionDialogVisible.value = true
}

const submitPermissionChange = async () => {
  if (!permissionForm.newRole) {
    ElMessage.warning('请选择新角色')
    return
  }
  if (!permissionForm.password) {
    ElMessage.warning('请输入密码确认')
    return
  }
  if (permissionForm.newRole === permissionForm.oldRole) {
    ElMessage.warning('新角色与当前角色相同')
    return
  }

  try {
    const response = await request.post('/system/user/updateRole', {
      userId: permissionForm.userId,
      newRole: permissionForm.newRole,
      password: permissionForm.password
    })
    if (response.code === 200) {
      ElMessage.success('权限修改成功')
      permissionDialogVisible.value = false
      fetchUserList()
    }
  } catch (error) {
    console.error('权限修改失败:', error)
  }
}

const loadApplications = async () => {
  applicationLoading.value = true
  try {
    const params = {
      page: applicationPagination.page,
      size: applicationPagination.size
    }
    if (applicationSearch.status) {
      params.status = applicationSearch.status
    }
    const response = await request.get('/system/permission-applications', { params })
    if (response.code === 200 && response.data) {
      applicationData.value = response.data.records || []
      applicationPagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('读取注册中心申请失败:', error)
  } finally {
    applicationLoading.value = false
  }
}

const searchApplications = () => {
  applicationPagination.page = 1
  loadApplications()
}

const resetApplicationSearch = () => {
  applicationSearch.status = ''
  applicationPagination.page = 1
  loadApplications()
}

const handleApplicationSizeChange = () => {
  applicationPagination.page = 1
  loadApplications()
}

const openApplicationReview = (row, mode) => {
  applicationReviewMode.value = mode
  Object.assign(applicationReviewForm, {
    id: row.id,
    username: row.realName || row.username,
    targetRole: row.targetRole,
    comment: mode === 'approve' ? '同意申请' : ''
  })
  applicationReviewDialogVisible.value = true
}

const submitApplicationReview = async () => {
  if (applicationReviewMode.value === 'reject' && !applicationReviewForm.comment.trim()) {
    ElMessage.warning('请填写拒绝原因')
    return
  }

  applicationReviewLoading.value = true
  try {
    const action = applicationReviewMode.value === 'approve' ? 'approve' : 'reject'
    const response = await request.post(`/system/permission-applications/${applicationReviewForm.id}/${action}`, {
      comment: applicationReviewForm.comment
    })
    if (response.code === 200) {
      ElMessage.success(response.message || '处理成功')
      applicationReviewDialogVisible.value = false
      await loadApplications()
      await fetchUserList()
    } else {
      ElMessage.error(response.message || '处理失败')
    }
  } catch (error) {
    console.error('处理权限申请失败:', error)
  } finally {
    applicationReviewLoading.value = false
  }
}

const getApplicationStatusName = (status) => {
  const map = {
    PENDING: '待处理',
    APPROVED: '已同意',
    REJECTED: '已拒绝'
  }
  return map[status] || status
}

const getApplicationStatusType = (status) => {
  const map = {
    PENDING: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger'
  }
  return map[status] || 'info'
}

const loadAgentConfig = async () => {
  try {
    const response = await request.get('/system/config/agent')
    if (response.code === 200 && response.data) {
      Object.assign(agentConfig, response.data)
    }
  } catch (error) {
    console.error('读取Agent配置失败:', error)
  }
}

const saveAgentConfig = async () => {
  try {
    const response = await request.put('/system/config/agent', { ...agentConfig })
    if (response.code === 200) {
      ElMessage.success(response.message || 'Agent配置保存成功')
    }
  } catch (error) {
    console.error('保存Agent配置失败:', error)
  }
}

const loadRagConfig = async () => {
  try {
    const response = await request.get('/system/config/rag')
    if (response.code === 200 && response.data) {
      Object.assign(ragLangchain, response.data.langchain || {})
      Object.assign(ragLangchain4j, response.data.langchain4j || {})
    }
  } catch (error) {
    console.error('读取RAG配置失败:', error)
  }
}

const saveLangchainRagConfig = async () => {
  try {
    const payload = {
      retrieveTopK: ragLangchain.retrieveTopK,
      chunkSize: ragLangchain.chunkSize,
      chunkOverlap: ragLangchain.chunkOverlap
    }
    const response = await request.put('/system/config/rag/langchain', payload)
    if (response.code === 200) {
      ElMessage.success(response.message || 'LangChain配置保存成功')
    }
  } catch (error) {
    console.error('保存LangChain配置失败:', error)
  }
}

const saveLangchain4jRagConfig = async () => {
  try {
    const payload = {
      maxResults: ragLangchain4j.maxResults,
      minScore: ragLangchain4j.minScore,
      memoryMaxMessages: ragLangchain4j.memoryMaxMessages,
      chunkSize: ragLangchain4j.chunkSize,
      chunkOverlap: ragLangchain4j.chunkOverlap
    }
    const response = await request.put('/system/config/rag/langchain4j', payload)
    if (response.code === 200) {
      ElMessage.success(response.message || 'LangChain4j配置保存成功')
    }
  } catch (error) {
    console.error('保存LangChain4j配置失败:', error)
  }
}

const openUpload = (engine) => {
  uploadEngine.value = engine
  if (uploadInputRef.value) {
    uploadInputRef.value.value = ''
    uploadInputRef.value.click()
  }
}

const handleFileSelected = async (event) => {
  const file = event?.target?.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await request.post(`/system/config/rag/knowledge-files?engine=${uploadEngine.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (response.code === 200) {
      ElMessage.success('知识文件上传成功')
      await loadRagConfig()
    }
  } catch (error) {
    console.error('上传知识文件失败:', error)
  }
}

const deleteKnowledgeFile = async (engine, name) => {
  ElMessageBox.confirm(`确定删除知识文件 "${name}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const response = await request.delete('/system/config/rag/knowledge-files', {
      params: { engine, fileName: name }
    })
    if (response.code === 200) {
      ElMessage.success('删除成功')
      await loadRagConfig()
    }
  }).catch(() => {})
}

const editKnowledgeFile = async (engine, name) => {
  try {
    const response = await request.get('/system/config/rag/knowledge-files/content', {
      params: { engine, fileName: name }
    })
    if (response.code === 200 && response.data) {
      knowledgeEditor.engine = engine
      knowledgeEditor.fileName = response.data.fileName || name
      knowledgeEditor.content = response.data.content || ''
      knowledgeEditorVisible.value = true
    } else {
      ElMessage.error(response.message || '读取文件失败')
    }
  } catch (error) {
    console.error('读取知识文件失败:', error)
    ElMessage.error(error?.response?.data?.message || '读取文件失败')
  }
}

const saveKnowledgeFileContent = async () => {
  try {
    const response = await request.put(
      '/system/config/rag/knowledge-files/content',
      { content: knowledgeEditor.content },
      { params: { engine: knowledgeEditor.engine, fileName: knowledgeEditor.fileName } }
    )
    if (response.code === 200) {
      ElMessage.success('文件保存成功')
      knowledgeEditorVisible.value = false
      await loadRagConfig()
    }
  } catch (error) {
    console.error('保存知识文件失败:', error)
    ElMessage.error(error?.response?.data?.message || '保存文件失败')
  }
}

const formatKB = (size) => {
  const val = Number(size || 0) / 1024
  return val.toFixed(2)
}

const formatTime = (ts) => {
  if (!ts) return '-'
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleString('zh-CN')
}

onMounted(() => {
  checkPermission()
  fetchUserList()
  loadAgentConfig()
  loadRagConfig()
})
</script>

<style scoped>
.system-view {
  min-height: 100vh;
}

.main-container {
  display: flex;
  padding-top: 60px;
  min-height: 100vh;
}

.sidebar {
  width: 200px;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  position: fixed;
  top: 60px;
  bottom: 0;
  left: 0;
  overflow-y: auto;
}

.sidebar-menu {
  border-right: none;
}

.content-wrapper {
  flex: 1;
  margin-left: 200px;
  padding: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

.search-area {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}

.search-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-item .label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.search-item .el-select {
  width: 140px;
}

.search-btns {
  display: flex;
  gap: 8px;
}

.toolbar {
  margin-bottom: 16px;
}

.table-wrapper {
  background-color: #fff;
  border-radius: 8px;
}

.pagination-area {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.permission-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.user-card {
  background-color: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  padding: 20px;
  transition: box-shadow 0.2s;
}

.user-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.user-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.user-card-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.user-card-info {
  margin-bottom: 12px;
}

.info-item {
  font-size: 14px;
  color: #606266;
  margin-bottom: 6px;
}

.info-label {
  color: #909399;
}

.info-value {
  color: #606266;
}

.user-card-permissions {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
}

.permissions-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.permissions-list {
  margin: 0;
  padding-left: 16px;
  font-size: 13px;
  color: #606266;
}

.permissions-list li {
  margin-bottom: 4px;
}

.user-card-actions {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  text-align: right;
}

.empty-permission {
  grid-column: 1 / -1;
  text-align: center;
  color: #909399;
  padding: 60px;
}

.rag-card {
  margin-bottom: 16px;
}

.card-header {
  font-weight: 600;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.hint-text {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

.muted-text {
  color: #909399;
  font-size: 13px;
}

@media (max-width: 768px) {
  .sidebar {
    width: 160px;
  }

  .content-wrapper {
    margin-left: 160px;
    padding: 16px;
  }
}
</style>
