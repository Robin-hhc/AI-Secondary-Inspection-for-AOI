<template>
  <div class="statistics-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card>
          <el-statistic title="总样本数" :value="overview.total_samples" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="已标注" :value="overview.total_annotations" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="正常样本" :value="overview.normal_count" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="缺陷样本" :value="overview.defect_count" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>标注分布</span>
          </template>
          <div ref="pieChart" style="height: 300px"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>标注趋势</span>
          </template>
          <div ref="lineChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import { statisticsAPI } from '../api'

const overview = ref({
  total_samples: 0,
  total_annotations: 0,
  normal_count: 0,
  defect_count: 0
})

const pieChart = ref(null)
const lineChart = ref(null)

// 加载统计数据
const loadStatistics = async () => {
  try {
    const res = await statisticsAPI.getOverview()
    overview.value = res.data

    // 更新饼图
    updatePieChart()
  } catch (error) {
    console.error(error)
  }
}

// 更新饼图
const updatePieChart = () => {
  const chart = echarts.init(pieChart.value)
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '标注分布',
        type: 'pie',
        radius: '50%',
        data: [
          { value: overview.value.normal_count, name: '正常' },
          { value: overview.value.defect_count, name: '缺陷' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  chart.setOption(option)
}

// 初始化折线图
const initLineChart = () => {
  const chart = echarts.init(lineChart.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '标注数量',
        type: 'line',
        data: [120, 200, 150, 80, 70, 110, 130],
        smooth: true
      }
    ]
  }
  chart.setOption(option)
}

onMounted(() => {
  loadStatistics()
  initLineChart()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
}
</style>
