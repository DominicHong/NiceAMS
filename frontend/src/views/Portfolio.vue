<template>
  <div class="portfolio">
    <div class="page-header">
      <h2>Portfolio Positions</h2>
      <div class="position-controls">
        <el-tooltip content="Select the date for viewing or recalculating positions" placement="top">
          <el-date-picker
            v-model="recalculateDate"
            type="date"
            placeholder="Select date (default: today)"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            size="default"
            style="margin-right: 10px; width: 200px;"
          />
        </el-tooltip>
        <el-button 
          type="success" 
          @click="handleShowPositions"
          :loading="loading"
          size="default"
          style="margin-right: 10px;"
        >
          Show Positions
        </el-button>
        <el-button 
          type="primary" 
          @click="handleRecalculate"
          :loading="loading"
          size="default"
        >
          Recalculate Positions
        </el-button>
      </div>
    </div>
    
    <el-card>
      <div v-if="positions.length === 0 && !loading" class="empty-state">
        <p>No positions found. Your portfolio appears to be empty.</p>
        <p>If you have transactions, click "Recalculate Positions" to generate positions from your transactions.</p>
      </div>
      
      <SharedDataTable 
        v-else
        :data="positions" 
        :columns="tableColumns" 
        :loading="loading"
        empty-text="No positions found. Your portfolio appears to be empty."
      />
    </el-card>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import { ElMessage } from 'element-plus'
import SharedDataTable from '../components/SharedDataTable.vue'
import formatMixin from '../mixins/formatMixin'

export default {
  name: 'Portfolio',
  
  components: {
    SharedDataTable
  },
  
  mixins: [formatMixin],
  
  data() {
    return {
      recalculateDate: this.formatDate(new Date())
    }
  },
  
  computed: {
    ...mapState(['positions', 'loading', 'currentPortfolio', 'portfolios']),
    
    tableColumns() {
      return [
        { prop: 'symbol', label: 'Symbol', width: '100' },
        { prop: 'name', label: 'Name' },
        { prop: 'quantity', label: 'Quantity', align: 'right', type: 'quantity' },
        { prop: 'current_price', label: 'Current Price', align: 'right', type: 'currency' },
        { prop: 'market_value', label: 'Market Value', align: 'right', type: 'currency' },
        { prop: 'total_pnl', label: 'Total P&L', align: 'right', type: 'pnl' }
      ]
    }
  },
  
  async created() {
    await this.initializePortfolio()
  },
  
  methods: {
    ...mapActions(['fetchPositions', 'recalculatePositions', 'fetchPortfolios', 'fetchPositionsForDate']),
    
    formatDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    
    disabledDate(time) {
      // Disable future dates
      return time.getTime() > Date.now()
    },
    
    async initializePortfolio() {
      try {
        // If no current portfolio, fetch portfolios first
        if (!this.currentPortfolio) {
          await this.fetchPortfolios()
        }
        
        // Now fetch positions if we have a current portfolio
        if (this.currentPortfolio) {
          await this.fetchPositions(this.currentPortfolio.id)
        }
      } catch (error) {
        console.error('Failed to initialize portfolio:', error)
        ElMessage.error('Failed to load portfolio data')
      }
    },
    
    async handleRecalculate() {
      if (!this.currentPortfolio) {
        ElMessage.error('No portfolio selected')
        return
      }
      
      if (!this.recalculateDate) {
        ElMessage.error('Please select a date for recalculation')
        return
      }
      
      try {
        const result = await this.recalculatePositions({
          portfolioId: this.currentPortfolio.id,
          asOfDate: this.recalculateDate
        })
        ElMessage.success(result.message || 'Positions recalculated successfully')
        
        // Ensure positions are refreshed after recalculation
        await this.fetchPositions(this.currentPortfolio.id)
      } catch (error) {
        ElMessage.error('Failed to recalculate positions: ' + error.message)
      }
    },
    
    async handleShowPositions() {
      if (!this.currentPortfolio) {
        ElMessage.error('No portfolio selected')
        return
      }
      
      if (!this.recalculateDate) {
        ElMessage.error('Please select a date to view positions')
        return
      }
      
      try {
        // First, try to fetch positions for the selected date
        const positions = await this.fetchPositionsForDate({
          portfolioId: this.currentPortfolio.id,
          asOfDate: this.recalculateDate
        })
        
        // If no positions found, recalculate positions for that date
        if (!positions || positions.length === 0) {
          ElMessage.info('No positions found for the selected date. Recalculating positions...')
          
          const result = await this.recalculatePositions({
            portfolioId: this.currentPortfolio.id,
            asOfDate: this.recalculateDate
          })
          
          ElMessage.success(result.message || 'Positions recalculated successfully')
          
          // Fetch the recalculated positions
          await this.fetchPositionsForDate({
            portfolioId: this.currentPortfolio.id,
            asOfDate: this.recalculateDate
          })
        } else {
          ElMessage.success(`Found ${positions.length} positions for ${this.recalculateDate}`)
        }
      } catch (error) {
        ElMessage.error('Failed to show positions: ' + error.message)
      }
    }
  }
}
</script>

<style scoped>
.portfolio {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.position-controls {
  display: flex;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state p {
  margin: 10px 0;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style> 