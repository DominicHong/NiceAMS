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

<script>
import { Chart, registerables } from 'chart.js'
import dayjs from 'dayjs'

Chart.register(...registerables)

export default {
  name: 'PerformanceChart',
  
  props: {
    performanceHistory: {
      type: Array,
      required: true,
      default: () => []
    },
    currencySymbol: {
      type: String,
      default: '¥'
    }
  },
  
  data() {
    return {
      performanceChart: null
    }
  },
  
  computed: {
    hasPerformanceData() {
      return this.performanceHistory && this.performanceHistory.length > 0
    }
  },
  
  mounted() {
    this.$nextTick(() => {
      this.createPerformanceChart()
    })
  },
  
  beforeUnmount() {
    if (this.performanceChart) {
      this.performanceChart.destroy()
    }
  },
  
  watch: {
    performanceHistory: {
      handler() {
        this.$nextTick(() => {
          this.createPerformanceChart()
        })
      },
      deep: true
    }
  },
  
  methods: {
    createPerformanceChart() {
      const canvas = this.$refs.performanceChart
      if (!canvas) {
        console.warn('Performance chart canvas not found')
        return
      }
      
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        console.warn('Could not get 2D context from performance chart canvas')
        return
      }

      // Real data from performance history
      const { labels, data } = this.preparePerformanceData()
      
      // Don't create chart if no data
      if (labels.length === 0 || data.length === 0) {
        console.warn('No performance data available for chart')
        return
      }

      try {
        // Safely destroy existing chart
        if (this.performanceChart) {
          try {
            this.performanceChart.destroy()
          } catch (e) {
            console.warn('Error destroying previous chart:', e)
          }
          this.performanceChart = null
        }
        
        this.performanceChart = new Chart(ctx, {
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
              pointRadius: 0, // Disable points for better performance
              pointHoverRadius: 0 // Disable hover points for better performance
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // Disable animations for better performance
            scales: {
              y: {
                beginAtZero: false,
                ticks: {
                  callback: (value) => {
                    return this.currencySymbol + value.toLocaleString()
                  }
                }
              },
              x: {
                ticks: {
                  maxRotation: 0, // Prevent label rotation for better performance
                  autoSkip: true, // Automatically skip labels for better performance
                  maxTicksLimit: 10 // Limit number of x-axis labels
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
        this.performanceChart = null
      }
    },

    preparePerformanceData() {
      // Prepare data for the chart based on performance history
      if (!this.performanceHistory || this.performanceHistory.length === 0) {
        return { labels: [], data: [] }
      }

      // Extract labels and values
      const labels = this.performanceHistory.map(item => 
        dayjs(item.date).format('MM/DD')
      )
      const data = this.performanceHistory.map(item => item.value)

      return { labels, data }
    }
  }
}
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