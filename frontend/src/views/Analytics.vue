<template>
  <div class="analytics">
    <div class="page-header">
      <h2>Portfolio Analytics</h2>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Performance Metrics</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Total Return">{{ formatPercentage(15.2) }}</el-descriptions-item>
            <el-descriptions-item label="Annualized Return">{{ formatPercentage(12.8) }}</el-descriptions-item>
            <el-descriptions-item label="Volatility">{{ formatPercentage(18.5) }}</el-descriptions-item>
            <el-descriptions-item label="Sharpe Ratio">0.85</el-descriptions-item>
            <el-descriptions-item label="Max Drawdown">{{ formatPercentage(-8.2) }}</el-descriptions-item>
            <el-descriptions-item label="Beta">1.12</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Asset Allocation</span>
          </template>
          <div class="allocation-chart">
            <el-progress type="dashboard" :percentage="45" status="success">
              <span>Stocks<br/>45%</span>
            </el-progress>
            <el-progress type="dashboard" :percentage="25" status="warning">
              <span>Bonds<br/>25%</span>
            </el-progress>
            <el-progress type="dashboard" :percentage="20" status="info">
              <span>Funds<br/>20%</span>
            </el-progress>
            <el-progress type="dashboard" :percentage="10" status="danger">
              <span>Cash<br/>10%</span>
            </el-progress>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>Monthly Returns</span>
      </template>
      <el-table :data="monthlyReturns" style="width: 100%">
        <el-table-column prop="month" label="Month" width="120" />
        <el-table-column prop="portfolio_return" label="Portfolio Return" align="right">
          <template #default="scope">
            <span :class="scope.row.portfolio_return >= 0 ? 'positive' : 'negative'">
              {{ formatPercentage(scope.row.portfolio_return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="benchmark_return" label="Benchmark Return" align="right">
          <template #default="scope">
            <span :class="scope.row.benchmark_return >= 0 ? 'positive' : 'negative'">
              {{ formatPercentage(scope.row.benchmark_return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="alpha" label="Alpha" align="right">
          <template #default="scope">
            <span :class="scope.row.alpha >= 0 ? 'positive' : 'negative'">
              {{ formatPercentage(scope.row.alpha) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'Analytics',
  
  data() {
    return {
      monthlyReturns: [
        { month: '2024-01', portfolio_return: 2.5, benchmark_return: 1.8, alpha: 0.7 },
        { month: '2024-02', portfolio_return: -1.2, benchmark_return: -0.8, alpha: -0.4 },
        { month: '2024-03', portfolio_return: 3.1, benchmark_return: 2.5, alpha: 0.6 },
        { month: '2024-04', portfolio_return: 1.8, benchmark_return: 2.2, alpha: -0.4 },
        { month: '2024-05', portfolio_return: 0.9, benchmark_return: 1.1, alpha: -0.2 },
        { month: '2024-06', portfolio_return: 2.7, benchmark_return: 2.0, alpha: 0.7 }
      ]
    }
  },
  
  methods: {
    formatPercentage(value) {
      if (value == null) return '0.00%'
      return Number(value).toFixed(2) + '%'
    }
  }
}
</script>

<style scoped>
.analytics {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.allocation-chart {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
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