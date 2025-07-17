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
      
      <template v-else>
        <!-- Portfolio Summary -->
        <div v-if="portfolioSummary && positions.length > 0" class="portfolio-summary">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="summary-card">
                <div class="summary-label">Total Market Value</div>
                <div class="summary-value">
                  {{ formatCurrency(portfolioSummary.total_market_value_primary, { symbol: portfolioSummary.primary_currency_symbol }) }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-card">
                <div class="summary-label">Total P&L</div>
                <div class="summary-value" :class="{ 'positive': portfolioSummary.total_pnl_primary > 0, 'negative': portfolioSummary.total_pnl_primary < 0 }">
                  {{ formatCurrency(portfolioSummary.total_pnl_primary, { symbol: portfolioSummary.primary_currency_symbol }) }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="summary-card">
                <div class="summary-label">Positions</div>
                <div class="summary-value">{{ portfolioSummary.position_count }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <SharedDataTable 
          :data="positions" 
          :columns="tableColumns" 
          :loading="loading"
          empty-text="No positions found. Your portfolio appears to be empty."
        />
      </template>
    </el-card>
  </div>
</template>

<script>
import { useMainStore } from '../stores'
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
    // Pinia store
    store() {
      return useMainStore()
    },
    
    // State from store
    positions() {
      return this.store.positions
    },
    
    loading() {
      return this.store.loading
    },
    
    currentPortfolio() {
      return this.store.currentPortfolio
    },
    
    portfolios() {
      return this.store.portfolios
    },
    
    portfolioSummary() {
      return this.store.portfolioSummary
    },
    
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
          await this.store.fetchPortfolios()
        }
        
        // Now fetch positions if we have a current portfolio
        if (this.currentPortfolio) {
          await this.store.fetchPositions(this.currentPortfolio.id)
          // Fetch portfolio summary
          await this.store.fetchPortfolioSummary({ portfolioId: this.currentPortfolio.id })
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
        const result = await this.store.recalculatePositions({
          portfolioId: this.currentPortfolio.id,
          asOfDate: this.recalculateDate
        })
        ElMessage.success(result.message || 'Positions recalculated successfully')
        
        // Ensure positions are refreshed after recalculation
        await this.store.fetchPositions(this.currentPortfolio.id)
        // Fetch updated portfolio summary
        await this.store.fetchPortfolioSummary({ 
          portfolioId: this.currentPortfolio.id,
          asOfDate: this.recalculateDate
        })
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
        const positions = await this.store.fetchPositionsForDate({
          portfolioId: this.currentPortfolio.id,
          asOfDate: this.recalculateDate
        })
        
        // Fetch portfolio summary for the selected date
        await this.store.fetchPortfolioSummary({
          portfolioId: this.currentPortfolio.id,
          asOfDate: this.recalculateDate
        })
        
        // If no positions found, recalculate positions for that date
        if (!positions || positions.length === 0) {
          ElMessage.info('No positions found for the selected date. Recalculating positions...')
          
          const result = await this.store.recalculatePositions({
            portfolioId: this.currentPortfolio.id,
            asOfDate: this.recalculateDate
          })
          
          ElMessage.success(result.message || 'Positions recalculated successfully')
          
          // Fetch the recalculated positions
          await this.store.fetchPositionsForDate({
            portfolioId: this.currentPortfolio.id,
            asOfDate: this.recalculateDate
          })
          
          // Fetch updated portfolio summary
          await this.store.fetchPortfolioSummary({
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

.portfolio-summary {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.summary-card {
  text-align: center;
  padding: 10px 0;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.summary-value.positive {
  color: #67c23a; /* Green for positive P&L */
}

.summary-value.negative {
  color: #f56c6c; /* Red for negative P&L */
}
</style> 