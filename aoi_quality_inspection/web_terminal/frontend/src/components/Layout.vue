<template>
  <el-container class="layout-container">
    <el-header>
      <div class="header-content">
        <h1>工业AI质检系统</h1>
        <div class="user-info">
          <span>{{ user?.username }}</span>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </div>
    </el-header>

    <el-container>
      <el-aside width="200px">
        <el-menu
          :default-active="activeMenu"
          router
        >
          <el-menu-item index="/annotation">
            <el-icon><Edit /></el-icon>
            <span>标注</span>
          </el-menu-item>
          <el-menu-item index="/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计</span>
          </el-menu-item>
          <el-menu-item index="/model">
            <el-icon><Setting /></el-icon>
            <span>模型管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authAPI } from '../api'

const router = useRouter()
const route = useRoute()

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))

const activeMenu = computed(() => route.path)

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出吗?', '提示', {
      type: 'warning'
    })
    await authAPI.logout()
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    ElMessage.success('已退出')
    router.push('/login')
  } catch (error) {
    console.log(error)
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-header {
  background: #409EFF;
  color: white;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.el-aside {
  background: #f5f5f5;
}

.el-menu {
  border-right: none;
}
</style>
