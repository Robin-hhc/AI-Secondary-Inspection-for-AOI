<template>
  <div class="model-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>产品型号管理</span>
          <el-button type="primary" size="small" @click="showAddDialog">
            添加型号
          </el-button>
        </div>
      </template>

      <el-table :data="models" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="threshold" label="阈值" width="100">
          <template #default="{ row }">
            {{ row.threshold?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success">活跃</el-tag>
            <el-tag v-else>未激活</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="primary"
              size="small"
              @click="switchModel(row.id)"
            >
              切换
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加型号对话框 -->
    <el-dialog v-model="addDialogVisible" title="添加产品型号" width="500px">
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="编码">
          <el-input v-model="addForm.code" placeholder="product_a" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="addForm.name" placeholder="产品A" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="addForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="阈值">
          <el-input-number v-model="addForm.threshold" :min="0" :max="1" :step="0.1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addModel">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { modelAPI } from '../api'

const models = ref([])
const addDialogVisible = ref(false)

const addForm = reactive({
  code: '',
  name: '',
  description: '',
  threshold: 0.5
})

// 加载产品型号列表
const loadModels = async () => {
  try {
    const res = await modelAPI.getList()
    models.value = res.data.models
  } catch (error) {
    console.error(error)
  }
}

// 切换产品型号
const switchModel = async (modelId) => {
  try {
    await modelAPI.switch({ model_id: modelId })
    ElMessage.success('切换成功')
    loadModels()
  } catch (error) {
    console.error(error)
  }
}

// 显示添加对话框
const showAddDialog = () => {
  addForm.code = ''
  addForm.name = ''
  addForm.description = ''
  addForm.threshold = 0.5
  addDialogVisible.value = true
}

// 添加产品型号
const addModel = async () => {
  try {
    await modelAPI.add(addForm)
    ElMessage.success('添加成功')
    addDialogVisible.value = false
    loadModels()
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.model-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
