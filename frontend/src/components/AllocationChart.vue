<template>
  <div class="allocation-chart-wrapper">
    <!-- Asset Allocation Chart -->
    <div class="chart-container">
      <canvas ref="allocationChartRef" v-show="hasAllocationData"></canvas>
      <div v-show="!hasAllocationData" class="no-data-message">
        <el-empty description="No Position" :image-size="100"></el-empty>
      </div>
    </div>

    <!-- Allocation Details -->
    <div class="allocation-details" v-if="Object.keys(assetAllocation).length > 0">
      <el-divider></el-divider>
      <div class="allocation-item" v-for="(percentage, type) in sortedAllocation" :key="type">
        <span class="allocation-label">{{ formatAllocationType(type) }}:</span>
        <span class="allocation-value">{{ formatPercentage(percentage) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { formatPercentage } from '../utils/formatters'

Chart.register(...registerables)

// Props
const props = defineProps({
  assetAllocation: {
    type: Object,
    required: true
  }
})

// Refs
const allocationChart = ref(null)
const allocationChartRef = ref(null)

// Computed properties
const hasAllocationData = computed(() => {
  const allocation = props.assetAllocation || {}
  return Object.values(allocation).some(percentage => percentage > 0)
})

const sortedAllocation = computed(() => {
  const allocation = props.assetAllocation || {}
  return Object.entries(allocation)
    .filter(([_, percentage]) => percentage > 0)
    .sort(([, a], [, b]) => b - a)
    .reduce((obj, [type, percentage]) => {
      obj[type] = percentage
      return obj
    }, {})
})

// Methods
const createAllocationChart = () => {
  const ctx = allocationChartRef.value?.getContext('2d')
  if (!ctx) return

  // Destroy existing chart if it exists
  if (allocationChart.value) {
    allocationChart.value.destroy()
  }

  const allocationData = getAllocationData()

  // Check if we have valid data
  if (!allocationData.data || allocationData.data.length === 0 ||
    allocationData.data.every(val => val === 0)) {
    return
  }

  try {
    allocationChart.value = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: allocationData.labels,
        datasets: [{
          data: allocationData.data,
          backgroundColor: [
            '#409EFF',
            '#67C23A',
            '#E6A23C',
            '#F56C6C',
            '#909399',
            '#00c0ef',
            '#ff851b',
            '#605ca8',
            '#d2d6de',
            '#001f3f'
          ],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const label = context.label || ''
                const value = context.parsed || 0
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = ((value / total) * 100).toFixed(1)
                return `${label}: ${percentage}%`
              }
            }
          }
        }
      }
    })
  } catch (error) {
    console.error('Error creating allocation chart:', error)
    // Ensure chart is null on creation failure
    allocationChart.value = null
  }
}

const getAllocationData = () => {
  const allocation = props.assetAllocation || {}

  // Filter out zero percentages and sort by value
  const filteredAllocation = Object.entries(allocation)
    .filter(([_, percentage]) => percentage > 0)
    .sort(([, a], [, b]) => b - a)

  if (filteredAllocation.length === 0) {
    // Return empty structure instead of placeholder data
    return {
      labels: [],
      data: []
    }
  }

  // Format labels for display
  const labels = filteredAllocation.map(([type]) => {
    return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
  })

  const data = filteredAllocation.map(([_, percentage]) => percentage)

  return { labels, data }
}

const formatAllocationType = (type) => {
  if (!type) return 'Unknown'
  return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
}

// Lifecycle hooks
onMounted(() => {
  nextTick(() => {
    createAllocationChart()
  })
})

onUnmounted(() => {
  if (allocationChart.value) {
    allocationChart.value.destroy()
  }
})

// Watchers
watch(
  () => props.assetAllocation,
  () => {
    nextTick(() => {
      createAllocationChart()
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

.allocation-details {
  margin-top: 15px;
}

.allocation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.allocation-label {
  color: #606266;
  font-weight: 500;
}

.allocation-value {
  color: #303133;
  font-weight: 600;
}

.no-data-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>