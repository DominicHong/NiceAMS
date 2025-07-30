<template>
  <div class="allocation-chart-wrapper">
    <!-- Asset Allocation Chart -->
    <div class="chart-container">
      <canvas ref="allocationChart" v-show="hasAllocationData"></canvas>
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

<script>
import { Chart, registerables } from 'chart.js'
import { useMainStore } from '../stores'

Chart.register(...registerables)

export default {
  name: 'AllocationChart',
  
  props: {
    assetAllocation: {
      type: Object,
      required: true
    }
  },
  
  data() {
    return {
      allocationChart: null
    }
  },
  
  computed: {
    store() {
      return useMainStore()
    },
    
    hasAllocationData() {
      const allocation = this.assetAllocation || {}
      const hasData = Object.values(allocation).some(percentage => percentage > 0)
      return hasData
    },
    
    sortedAllocation() {
      const allocation = this.assetAllocation || {}
      return Object.entries(allocation)
        .filter(([_, percentage]) => percentage > 0)
        .sort(([, a], [, b]) => b - a)
        .reduce((obj, [type, percentage]) => {
          obj[type] = percentage
          return obj
        }, {})
    }
  },
  
  mounted() {
    this.$nextTick(() => {
      this.createAllocationChart()
    })
  },
  
  beforeUnmount() {
    if (this.allocationChart) {
      this.allocationChart.destroy()
    }
  },
  
  watch: {
    assetAllocation: {
      handler() {
        this.$nextTick(() => {
          this.createAllocationChart()
        })
      },
      deep: true
    }
  },
  
  methods: {
    createAllocationChart() {
      const ctx = this.$refs.allocationChart?.getContext('2d')
      if (!ctx) return

      // Destroy existing chart if it exists
      if (this.allocationChart) {
        this.allocationChart.destroy()
      }

      const allocationData = this.getAllocationData()

      // Check if we have valid data
      if (!allocationData.data || allocationData.data.length === 0 ||
        allocationData.data.every(val => val === 0)) {
        return
      }

      try {
        this.allocationChart = new Chart(ctx, {
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
        this.allocationChart = null
      }
    },
    
    getAllocationData() {
      const allocation = this.assetAllocation || {}

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
    },
    
    formatPercentage(value) {
      if (value == null) return '0.00%'
      return Number(value).toFixed(2) + '%'
    },
    
    formatAllocationType(type) {
      if (!type) return 'Unknown'
      return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
    }
  }
}
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