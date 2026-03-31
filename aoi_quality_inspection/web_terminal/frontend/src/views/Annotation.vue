<template>
  <div class="annotation-container">
    <el-row :gutter="20">
      <!-- 待标注样本列表 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>待标注样本 ({{ samples.length }})</span>
              <el-button size="small" @click="loadSamples">刷新</el-button>
            </div>
          </template>

          <div class="sample-list">
            <div
              v-for="sample in samples"
              :key="sample.id"
              class="sample-item"
              :class="{ active: currentSample?.id === sample.id }"
              @click="selectSample(sample)"
            >
              <div class="sample-info">
                <div>ID: {{ sample.id }}</div>
                <div>分数: {{ sample.ai_score?.toFixed(3) }}</div>
                <div>{{ sample.timestamp }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 标注区域 -->
      <el-col :span="16">
        <el-card v-if="currentSample">
          <template #header>
            <span>样本标注</span>
          </template>

          <!-- 图像显示 -->
          <div class="image-container">
            <el-image
              :src="getImageUrl(currentSample.image_path)"
              fit="contain"
              style="width: 100%; height: 400px"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                  <span>图像加载失败</span>
                </div>
              </template>
            </el-image>
          </div>

          <!-- 样本信息 -->
          <el-descriptions :column="2" border style="margin-top: 20px">
            <el-descriptions-item label="样本ID">{{ currentSample.id }}</el-descriptions-item>
            <el-descriptions-item label="产品型号">{{ currentSample.product_code }}</el-descriptions-item>
            <el-descriptions-item label="AI分数">{{ currentSample.ai_score?.toFixed(3) }}</el-descriptions-item>
            <el-descriptions-item label="AI判定">{{ getAiLabel(currentSample.ai_label) }}</el-descriptions-item>
            <el-descriptions-item label="采集时间">{{ currentSample.timestamp }}</el-descriptions-item>
          </el-descriptions>

          <!-- 标注表单 -->
          <el-form :model="annotationForm" style="margin-top: 20px">
            <el-form-item label="标注结果">
              <el-radio-group v-model="annotationForm.label">
                <el-radio :label="0">正常</el-radio>
                <el-radio :label="1">缺陷</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item v-if="annotationForm.label === 1" label="缺陷类型">
              <el-select v-model="annotationForm.defect_type" placeholder="选择缺陷类型">
                <el-option label="划痕" value="划痕" />
                <el-option label="污渍" value="污渍" />
                <el-option label="变形" value="变形" />
                <el-option label="缺件" value="缺件" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>

            <el-form-item label="备注">
              <el-input
                v-model="annotationForm.notes"
                type="textarea"
                :rows="2"
                placeholder="输入备注信息"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="submitAnnotation" :loading="loading">
                提交标注
              </el-button>
              <el-button @click="nextSample">下一个</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-empty v-else description="请选择待标注样本" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { annotationAPI } from '../api'

const samples = ref([])
const currentSample = ref(null)
const loading = ref(false)

const annotationForm = reactive({
  label: 0,
  defect_type: '',
  notes: ''
})

// 加载待标注样本
const loadSamples = async () => {
  try {
    const res = await annotationAPI.getPending({ limit: 100 })
    samples.value = res.data.samples
  } catch (error) {
    console.error(error)
  }
}

// 选择样本
const selectSample = (sample) => {
  currentSample.value = sample
  annotationForm.label = 0
  annotationForm.defect_type = ''
  annotationForm.notes = ''
}

// 提交标注
const submitAnnotation = async () => {
  if (!currentSample.value) return

  loading.value = true
  try {
    await annotationAPI.submit({
      sample_id: currentSample.value.id,
      label: annotationForm.label,
      defect_type: annotationForm.defect_type,
      notes: annotationForm.notes
    })
    ElMessage.success('标注成功')
    // 移除已标注样本
    samples.value = samples.value.filter(s => s.id !== currentSample.value.id)
    nextSample()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 下一个样本
const nextSample = () => {
  if (samples.value.length > 0) {
    selectSample(samples.value[0])
  } else {
    currentSample.value = null
  }
}

// 获取图像URL
const getImageUrl = (path) => {
  return `/data${path}`
}

// 获取AI判定文本
const getAiLabel = (label) => {
  if (label === 0) return '正常'
  if (label === 1) return '缺陷'
  return '不确定'
}

// 快捷键处理
const handleKeydown = (e) => {
  if (!currentSample.value) return

  if (e.key === 'n' || e.key === 'N') {
    annotationForm.label = 0
  } else if (e.key === 'd' || e.key === 'D') {
    annotationForm.label = 1
  } else if (e.key === 'Enter') {
    submitAnnotation()
  }
}

onMounted(() => {
  loadSamples()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.annotation-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sample-list {
  max-height: 600px;
  overflow-y: auto;
}

.sample-item {
  padding: 10px;
  border: 1px solid #ebeef5;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.sample-item:hover {
  background: #f5f7fa;
}

.sample-item.active {
  background: #ecf5ff;
  border-color: #409EFF;
}

.sample-info {
  font-size: 14px;
  color: #606266;
}

.image-container {
  text-align: center;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}
</style>
