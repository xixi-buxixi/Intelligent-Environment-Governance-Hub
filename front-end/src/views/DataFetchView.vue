<template>
  <div class="data-fetch-view">
    <AppHeader title="环保数据获取" show-back />

    <main class="main-content">
      <div class="section-card">
        <div class="section-title">📊 数据来源</div>
        <div class="source-list">
          <div class="source-card" v-for="source in topDataSources" :key="source.id">
            <div class="source-head">
              <h4>{{ source.sourceName }}</h4>
              <el-tag size="small" type="success" effect="dark">官方公开数据</el-tag>
            </div>
            <p class="source-desc">{{ source.description }}</p>
            <p class="source-capability">能力：{{ getSourceCapability(source.sourceCode) }}</p>
            <a class="source-link" :href="source.sourceUrl" target="_blank" rel="noopener noreferrer">
              数据站点：{{ source.sourceUrl }}
            </a>
            <div class="data-types">
              <el-tag v-for="type in normalizeDataTypes(parseDataTypes(source.dataTypes))" :key="type" size="small" type="success" effect="light">
                {{ formatDataTypeLabel(type) }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="source-more" v-if="remainingDataSources.length > 0">
          <el-button link type="primary" @click="showMoreSources = !showMoreSources">
            {{ showMoreSources ? '收起其余数据源' : `查看其余 ${remainingDataSources.length} 个数据源` }}
          </el-button>
          <el-scrollbar v-if="showMoreSources" max-height="240px">
            <div class="source-list source-list-more">
              <div class="source-card" v-for="source in remainingDataSources" :key="`more-${source.id}`">
                <div class="source-head">
                  <h4>{{ source.sourceName }}</h4>
                  <el-tag size="small" type="info" effect="light">扩展数据源</el-tag>
                </div>
                <p class="source-desc">{{ source.description }}</p>
                <a class="source-link" :href="source.sourceUrl" target="_blank" rel="noopener noreferrer">
                  数据站点：{{ source.sourceUrl }}
                </a>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <div class="fetch-limit-card" :class="{ unlimited: !fetchLimit.hasLimit }">
        <div>
          <template v-if="fetchLimit.hasLimit">
            <div class="limit-text">今日剩余获取次数</div>
            <div class="limit-desc">普通用户每日限制3次</div>
          </template>
          <template v-else>
            <div class="limit-text">当前身份为{{ roleText }}，获取次数不受限制</div>
            <div class="limit-desc">{{ roleText }}享有无限次获取权限</div>
          </template>
        </div>
        <div class="limit-count" v-if="fetchLimit.hasLimit">{{ fetchLimit.remainingCount }} / {{ fetchLimit.dailyLimit }}</div>
        <div class="limit-count" v-else>∞</div>
      </div>

      <div class="section-card form-section">
        <div class="section-title">🔍 数据获取</div>
        <el-form :model="form" label-width="100px">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="数据源" required>
                <el-select v-model="form.sourceId" placeholder="请选择数据源" @change="onSourceChange" style="width: 100%">
                  <el-option v-for="source in dataSources" :key="source.id" :label="source.sourceName" :value="source.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="城市" required>
                <el-select v-model="form.city" placeholder="请选择城市" style="width: 100%">
                  <el-option v-for="city in cities" :key="city" :label="city" :value="city" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="起始日期" required>
                <el-date-picker v-model="form.startDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="终止日期" required>
                <el-date-picker v-model="form.endDate" type="date" value-format="YYYY-MM-DD" :max-date="today" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="数据类型" required>
                <div class="type-select-wrap">
                  <div class="type-actions">
                    <el-button link type="primary" @click="selectAllTypes" :disabled="availableDataTypes.length === 0 || allTypesSelected">全选</el-button>
                    <el-button link @click="clearAllTypes" :disabled="form.dataTypes.length === 0">清空</el-button>
                  </div>
                  <el-select v-model="form.dataTypes" multiple collapse-tags collapse-tags-tooltip placeholder="请选择数据类型（可多选）" style="width: 100%">
                    <el-option v-for="type in availableDataTypes" :key="type" :label="formatDataTypeLabel(type)" :value="type" />
                  </el-select>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
          <div class="form-actions">
            <el-button type="success" size="large" :loading="isLoading" :disabled="!canFetch || isLoading" @click="fetchPreview(false)">
              {{ isLoading ? '获取中...' : '获取数据' }}
            </el-button>
            <el-button size="large" @click="resetForm">重置</el-button>
          </div>
        </el-form>
      </div>

      <div class="section-card" v-if="previewRows.length > 0">
        <div class="section-title">🧾 数据获取预览</div>
        <div class="preview-meta">
          <span>总记录数：{{ previewRecordCount }}</span>
          <span>预览上限：100</span>
          <span>当前显示：{{ visiblePreviewRows.length }}</span>
          <span v-if="lastCrawlTime">最近爬取：{{ formatDateTime(lastCrawlTime) }}</span>
        </div>
        <div class="preview-scroll-box" @scroll="onPreviewScroll">
          <el-table :data="visiblePreviewRows" stripe style="width: 100%">
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column prop="city" label="城市" width="90" />
            <el-table-column v-for="col in selectedMetricColumns" :key="col.prop" :prop="col.prop" :label="col.label" width="110" />
          </el-table>
        </div>
        <div class="preview-load-tip" v-if="visiblePreviewRows.length < filteredPreviewRows.length">
          向下滚动可继续加载，每次20条
        </div>
        <div class="form-actions" style="margin-top: 12px">
          <el-button type="primary" @click="exportCsv">导出CSV</el-button>
        </div>
      </div>

      <div class="section-card history-section">
        <div class="section-title">📋 获取历史</div>
        <el-table :data="historyRecords" stripe style="width: 100%" v-if="historyRecords.length">
          <el-table-column prop="city" label="城市" width="100" />
          <el-table-column label="日期范围" min-width="180">
            <template #default="scope">{{ scope.row.startDate }} 至 {{ scope.row.endDate }}</template>
          </el-table-column>
          <el-table-column prop="dataType" label="数据类型" min-width="180" />
          <el-table-column label="数据站点" min-width="220">
            <template #default="scope">
              <a v-if="scope.row.sourceUrl" class="history-link" :href="scope.row.sourceUrl" target="_blank" rel="noopener noreferrer">
                {{ scope.row.sourceName || scope.row.sourceUrl }}
              </a>
              <span v-else>{{ scope.row.sourceName || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="点击获取时间" min-width="170">
            <template #default="scope">{{ formatDateTime(scope.row.createTime) }}</template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-text">暂无获取记录</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import request from '@/utils/request'

const DATA_TYPE_DEFS = [
  { key: 'AQI', label: 'AQI', prop: 'aqi' },
  { key: 'AQI_RANK', label: 'AQI排名', prop: 'aqiRank' },
  { key: 'QUALITY', label: '质量等级', prop: 'quality' },
  { key: 'PM25', label: 'PM2.5', prop: 'pm25' },
  { key: 'PM10', label: 'PM10', prop: 'pm10' },
  { key: 'SO2', label: 'SO2', prop: 'so2' },
  { key: 'NO2', label: 'NO2', prop: 'no2' },
  { key: 'CO', label: 'CO', prop: 'co' },
  { key: 'O3', label: 'O3', prop: 'o3' },
  { key: 'TEMP_HIGH', label: '最高温', prop: 'tempHigh' },
  { key: 'TEMP_LOW', label: '最低温', prop: 'tempLow' },
  { key: 'WEATHER', label: '天气', prop: 'weather' },
  { key: 'WIND', label: '风力', prop: 'wind' },
  { key: 'HUMIDITY', label: '湿度', prop: 'humidity' },
  { key: 'TITLE', label: '标题', prop: 'title' },
  { key: 'PUBLISH_TIME', label: '发布时间', prop: 'publishTime' },
  { key: 'SOURCE', label: '来源', prop: 'source' },
  { key: 'URL', label: '链接', prop: 'url' },
  { key: 'COMPANY', label: '企业', prop: 'company' },
  { key: 'INDICATOR', label: '指标', prop: 'indicator' },
  { key: 'VALUE', label: '数值', prop: 'value' },
  { key: 'MEASURE_TIME', label: '监测时间', prop: 'measureTime' },
  { key: 'PH', label: 'pH', prop: 'ph' },
  { key: 'DO', label: '溶解氧', prop: 'doValue' },
  { key: 'NH3N', label: '氨氮', prop: 'nh3n' },
  { key: 'CODMN', label: '高锰酸盐指数', prop: 'codmn' },
  { key: 'TP', label: '总磷', prop: 'tp' },
  { key: 'WQI', label: '水质指数', prop: 'wqi' }
]
const DATA_TYPE_LABEL_MAP = DATA_TYPE_DEFS.reduce((acc, item) => {
  acc[item.key] = item.label
  return acc
}, {})
const ALL_DATA_TYPES = DATA_TYPE_DEFS.map(item => item.key)
const SOURCE_CAPABILITY_MAP = {
  aqi_history: '天气后报历史空气质量抓取，稳定覆盖日级数据',
  weather_history: '天气后报历史气象数据抓取（温度/天气/风力）',
  env_news: '宜春生态环境局新闻数据抓取'
}

const userRole = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (!userInfo) return 'USER'
  return JSON.parse(userInfo).role || 'USER'
})

const serverRole = ref('')

const roleText = computed(() => {
  const currentRole = serverRole.value || userRole.value
  const roleMap = { ADMIN: '管理员', USER: '普通用户', MONITOR: '监测员' }
  return roleMap[currentRole] || currentRole
})

const dataSources = ref([])
const cities = ref([])
const availableDataTypes = ref([])
const historyRecords = ref([])
const previewRows = ref([])
const previewRecordCount = ref(0)
const lastCrawlTime = ref('')
const isLoading = ref(false)
const previewDisplayCount = ref(20)
const showMoreSources = ref(false)

const fetchLimit = ref({ hasLimit: true, remainingCount: 0, dailyLimit: 3 })

const form = ref({
  sourceId: '',
  city: '',
  startDate: '',
  endDate: '',
  dataTypes: [],
  forceUpdate: false
})

const today = computed(() => new Date().toISOString().split('T')[0])
const canFetch = computed(() => !!(form.value.sourceId && form.value.city && form.value.startDate && form.value.endDate && form.value.dataTypes.length > 0))
const allTypesSelected = computed(() => availableDataTypes.value.length > 0 && form.value.dataTypes.length === availableDataTypes.value.length)

const parseDataTypes = (raw) => {
  if (!raw) return []
  try {
    return JSON.parse(raw)
  } catch (_) {
    return String(raw).split(',').map(s => s.trim())
  }
}

const topDataSources = computed(() => dataSources.value.slice(0, 3))
const remainingDataSources = computed(() => dataSources.value.slice(3))

const normalizeDataTypes = (types) => {
  const normalized = (types || []).map(v => String(v || '').trim().toUpperCase()).filter(Boolean)
  return Array.from(new Set(normalized.length ? normalized : ALL_DATA_TYPES))
}

const formatDataTypeLabel = (type) => DATA_TYPE_LABEL_MAP[type] || type.replaceAll('_', ' ')
const getSourceCapability = (sourceCode) => SOURCE_CAPABILITY_MAP[sourceCode] || '标准空气质量抓取能力'

const onSourceChange = () => {
  const source = dataSources.value.find(s => s.id === form.value.sourceId)
  availableDataTypes.value = source ? normalizeDataTypes(parseDataTypes(source.dataTypes)) : [...ALL_DATA_TYPES]
  form.value.dataTypes = form.value.dataTypes.filter(type => availableDataTypes.value.includes(type))
}

const selectAllTypes = () => {
  form.value.dataTypes = [...availableDataTypes.value]
}

const clearAllTypes = () => {
  form.value.dataTypes = []
}

const initData = async () => {
  const response = await request.get('/data/init-info')
  if (response.code === 200) {
    dataSources.value = response.data.sources || []
    cities.value = response.data.cities || []
    if (response.data.fetchLimit) {
      fetchLimit.value = response.data.fetchLimit
      serverRole.value = response.data.fetchLimit.role || ''
    }
  }
  await loadHistory()
}

const loadHistory = async () => {
  const response = await request.get('/data/records')
  if (response.code === 200) historyRecords.value = response.data || []
}

const typeToProp = (type) => {
  const found = DATA_TYPE_DEFS.find(item => item.key === type)
  if (found) return found.prop
  const parts = String(type || '').toLowerCase().split('_').filter(Boolean)
  if (parts.length === 0) return ''
  return parts
    .map((p, idx) => (idx === 0 ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join('')
}

const selectedMetricColumns = computed(() => {
  return (form.value.dataTypes || []).map(type => ({
    key: type,
    label: formatDataTypeLabel(type),
    prop: typeToProp(type)
  }))
})

const filteredPreviewRows = computed(() => {
  const cols = selectedMetricColumns.value
  return (previewRows.value || []).map(row => {
    const mapped = { date: row.date, city: row.city }
    cols.forEach(col => {
      mapped[col.prop] = row[col.prop] ?? row[col.key] ?? row[String(col.key || '').toLowerCase()]
    })
    return mapped
  })
})

const visiblePreviewRows = computed(() => filteredPreviewRows.value.slice(0, previewDisplayCount.value))

const onPreviewScroll = (event) => {
  const el = event?.target
  if (!el) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 24) {
    previewDisplayCount.value = Math.min(previewDisplayCount.value + 20, filteredPreviewRows.value.length)
  }
}

const fetchPreview = async (forceUpdate) => {
  if (!canFetch.value) {
    ElMessage.warning('请填写完整信息')
    return
  }
  isLoading.value = true
  try {
    const payload = {
      ...form.value,
      dataType: form.value.dataTypes.join(','),
      forceUpdate,
      previewLimit: 100
    }
    const response = await request.post('/data/fetch/preview', payload, { timeout: 300000 })
    if (response.code === 200) {
      previewRows.value = (response.data.previewRows || []).slice(0, 100)
      previewRecordCount.value = response.data.recordCount || 0
      lastCrawlTime.value = response.data.lastCrawlTime || ''
      previewDisplayCount.value = 20
      ElMessage.success('数据获取成功')
      await initData()
      return
    }
    if (response.code === 409 && response.data?.needConfirm) {
      await ElMessageBox.confirm(
        response.message || '距离最近一次爬虫超过7天，继续可能等待较长时间，是否继续？',
        '数据可能较旧',
        { confirmButtonText: '继续获取', cancelButtonText: '取消', type: 'warning' }
      )
      await fetchPreview(true)
      return
    }
    ElMessage.error(response.message || '获取失败')
  } catch (error) {
    const server = error?.response?.data
    if (server?.code === 409 && server?.data?.needConfirm) {
      try {
        await ElMessageBox.confirm(
          server.message || '距离最近一次爬虫超过7天，继续可能等待较长时间，是否继续？',
          '数据可能较旧',
          { confirmButtonText: '继续获取', cancelButtonText: '取消', type: 'warning' }
        )
        await fetchPreview(true)
      } catch (_) {}
      return
    }
    ElMessage.error(server?.message || '获取失败，请重试')
  } finally {
    isLoading.value = false
  }
}

const exportCsv = async () => {
  try {
    const response = await fetch('/environment/api/data/fetch/export', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ...form.value, dataType: form.value.dataTypes.join(',') })
    })
    if (!response.ok) throw new Error('导出失败')
    const blob = await response.blob()
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.href = url
    link.download = `${form.value.city}_${form.value.dataTypes.join('-')}_${form.value.startDate}_${form.value.endDate}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('CSV导出成功')
  } catch (_) {
    ElMessage.error('导出失败')
  }
}

const resetForm = () => {
  form.value = { sourceId: '', city: '', startDate: '', endDate: '', dataTypes: [], forceUpdate: false }
  previewRows.value = []
  previewRecordCount.value = 0
  previewDisplayCount.value = 20
}

const formatDateTime = (val) => {
  if (!val) return '-'
  const d = new Date(val)
  return Number.isNaN(d.getTime()) ? val : d.toLocaleString('zh-CN')
}

onMounted(() => {
  if (userRole.value === 'ADMIN') fetchLimit.value = { hasLimit: false, remainingCount: 999, dailyLimit: 999 }
  availableDataTypes.value = [...ALL_DATA_TYPES]
  initData()
})
</script>

<style scoped>
.data-fetch-view { min-height: 100vh; }
.source-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.source-list-more { margin-top: 8px; }
.source-more { margin-top: 8px; }
.source-card { background: linear-gradient(135deg, #f7fbf8, #eef8f1); border-radius: 12px; padding: 16px; border: 1px solid #d7eadb; box-shadow: 0 2px 10px rgba(28, 94, 51, 0.05); }
.source-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 10px; }
.source-head h4 { margin: 0; color: #1f5c35; font-size: 16px; }
.source-desc { margin: 0 0 10px; color: #3d4b43; font-size: 13px; line-height: 1.55; }
.source-capability { margin: 0 0 8px; color: #4f6b5a; font-size: 12px; }
.source-link { color: #0b7a43; font-size: 12px; text-decoration: none; word-break: break-all; }
.source-link:hover { text-decoration: underline; }
.data-types { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.fetch-limit-card { background: linear-gradient(135deg, #fff3e0, #ffe0b2); border-radius: 8px; padding: 20px 24px; border: 1px solid #ffd8bf; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.fetch-limit-card.unlimited { background: linear-gradient(135deg, #e3f2fd, #bbdefb); border: 1px solid #b3d8ff; }
.limit-text { font-size: 15px; font-weight: 500; color: #e65100; }
.fetch-limit-card.unlimited .limit-text { color: #1565c0; }
.limit-desc { font-size: 12px; color: #999; margin-top: 4px; }
.limit-count { font-size: 28px; font-weight: bold; color: #e65100; }
.fetch-limit-card.unlimited .limit-count { color: #1565c0; }
.form-section .el-form { max-width: 900px; }
.form-actions { margin-top: 10px; display: flex; gap: 12px; }
.type-select-wrap { width: 100%; }
.type-actions { display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 6px; }
.preview-meta { display: flex; gap: 24px; margin-bottom: 12px; color: #606266; font-size: 13px; }
.preview-scroll-box { max-height: 560px; overflow: auto; border: 1px solid #ebeef5; border-radius: 8px; }
.preview-load-tip { margin-top: 8px; color: #909399; font-size: 12px; }
.history-link { color: #0b7a43; text-decoration: none; }
.history-link:hover { text-decoration: underline; }
.empty-text { color: #909399; padding: 24px 0; text-align: center; }
</style>
