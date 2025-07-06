<template>
  <div class="portfolio">
    <div class="page-header">
      <h2>Portfolio Holdings</h2>
    </div>
    
    <el-card>
      <el-table :data="holdings" style="width: 100%" v-loading="loading">
        <el-table-column prop="symbol" label="Symbol" width="100" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="quantity" label="Quantity" align="right" />
        <el-table-column prop="current_price" label="Current Price" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.current_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="market_value" label="Market Value" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.market_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="unrealized_pnl" label="Unrealized P&L" align="right">
          <template #default="scope">
            <span :class="scope.row.unrealized_pnl >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(scope.row.unrealized_pnl) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'Portfolio',
  
  computed: {
    ...mapState(['holdings', 'loading', 'currentPortfolio'])
  },
  
  async created() {
    if (this.currentPortfolio) {
      await this.fetchHoldings(this.currentPortfolio.id)
    }
  },
  
  methods: {
    ...mapActions(['fetchHoldings']),
    
    formatCurrency(value) {
      if (value == null) return '¥0.00'
      return '¥' + Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }
  }
}
</script>

<style scoped>
.portfolio {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style> 