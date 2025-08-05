<template>
  <div class="performance-chart-wrapper">
    <!-- Portfolio Performance Chart -->
    <div class="chart-container">
      <canvas ref="performanceChart" v-show="hasPerformanceData"></canvas>
      <div v-show="!hasPerformanceData" class="no-data-message">
        <el-empty description="No Performance Data" :image-size="100"></el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Chart, registerables } from 'chart.js'
import dayjs from 'dayjs'
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

Chart.register(...registerables)

// Props definition
const props = defineProps({
  performanceHistory: {
    type: Array,
    required: true,
    default: () => []
  },
  currencySymbol: {
    type: String,
    default: '¥'
  }
})

// Template ref for canvas
const performanceChart = ref(null)

// Chart instance
let chartInstance = null

// Computed property to check if performance data exists
const hasPerformanceData = computed(() => {
  return props.performanceHistory && props.performanceHistory.length > 0
})

// Prepare performance data for chart
const preparePerformanceData = () => {
  if (!props.performanceHistory || props.performanceHistory.length === 0) {
    return { labels: [], data: [] }
  }

  const labels = props.performanceHistory.map(item => 
    dayjs(item.date).format('MM/DD')
  )
  const data = props.performanceHistory.map(item => item.value)

  return { labels, data }
}

// Create performance chart
const createPerformanceChart = () => {
  const canvas = performanceChart.value
  if (!canvas) {
    console.warn('Performance chart canvas not found')
    return
  }
  
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    console.warn('Could not get 2D context from performance chart canvas')
    return
  }

  const { labels, data } = preparePerformanceData()
  
  if (labels.length === 0 || data.length === 0) {
    console.warn('No performance data available for chart')
    return
  }

  try {
    // Safely destroy existing chart
    if (chartInstance) {
      try {
        chartInstance.destroy()
      } catch (e) {
        console.warn('Error destroying previous chart:', e)
      }
      chartInstance = null
    }
    
    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Portfolio Value',
          data: data,
          borderColor: '#409EFF',
          backgroundColor: 'rgba(64, 158, 255, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: (value) => {
                return props.currencySymbol + value.toLocaleString()
              }
            }
          },
          x: {
            ticks: {
              maxRotation: 0,
              autoSkip: true,
              maxTicksLimit: 10
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        }
      }
    })
  } catch (error) {
    console.error('Error creating performance chart:', error)
    chartInstance = null
  }
}

// Lifecycle hooks
onMounted(() => {
  nextTick(() => {
    createPerformanceChart()
  })
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})

// Watch for performance history changes
watch(
  () => props.performanceHistory,
  () => {
    nextTick(() => {
      createPerformanceChart()
    })
  },
  { deep: true }
)
</script>

<style scoped>
.chart-container {
  height: 300px;
  position: relative;
}

.no-data-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>