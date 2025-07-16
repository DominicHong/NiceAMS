<template>
  <div class="settings">
    <div class="page-header">
      <h2>Settings</h2>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Currency Settings</span>
          </template>
          
          <el-form :model="currencySettings" label-width="120px">
            <el-form-item label="Primary Currency">
              <el-select v-model="currencySettings.primary_currency" style="width: 100%">
                <el-option v-for="currency in currencies" :key="currency.id" :label="currency.code" :value="currency.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="Display Format">
              <el-radio-group v-model="currencySettings.display_format">
                <el-radio label="primary">Primary Currency</el-radio>
                <el-radio label="original">Original Currency</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveCurrencySettings">Save</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Exchange Rates</span>
          </template>
          
          <el-table :data="exchangeRates" style="width: 100%">
            <el-table-column prop="currency_code" label="Currency" width="100" />
            <el-table-column prop="rate" label="Rate" align="right" />
            <el-table-column prop="rate_date" label="Date" width="120" />
            <el-table-column label="Actions" width="100">
              <template #default="scope">
                <el-button size="small" @click="editRate(scope.row)">Edit</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div style="margin-top: 20px;">
            <el-button type="primary" @click="showAddRateDialog = true">Add Rate</el-button>
            <el-button @click="importRates">Import from CSV</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>Portfolio Settings</span>
          </template>
          
          <el-form :model="portfolioSettings" label-width="120px">
            <el-form-item label="Tax Rate">
              <el-input-number v-model="portfolioSettings.tax_rate" :precision="2" :min="0" :max="100" />
              <span style="margin-left: 10px;">%</span>
            </el-form-item>
            <el-form-item label="Benchmark">
              <el-input v-model="portfolioSettings.benchmark" placeholder="e.g., S&P 500" />
            </el-form-item>
            <el-form-item label="Risk-Free Rate">
              <el-input-number v-model="portfolioSettings.risk_free_rate" :precision="2" :min="0" :max="100" />
              <span style="margin-left: 10px;">%</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="savePortfolioSettings">Save</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- Add Exchange Rate Dialog -->
    <el-dialog v-model="showAddRateDialog" title="Add Exchange Rate" width="400px">
      <el-form :model="rateForm" ref="rateFormRef">
        <el-form-item label="Currency" prop="currency_id">
          <el-select v-model="rateForm.currency_id" style="width: 100%">
            <el-option v-for="currency in currencies" :key="currency.id" :label="currency.code" :value="currency.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Rate" prop="rate">
          <el-input-number v-model="rateForm.rate" :precision="4" style="width: 100%" />
        </el-form-item>
        <el-form-item label="Date" prop="rate_date">
          <el-date-picker v-model="rateForm.rate_date" type="date" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveRate">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { useMainStore } from '../stores'

export default {
  name: 'Settings',
  
  data() {
    return {
      showAddRateDialog: false,
      currencySettings: {
        primary_currency: 1,
        display_format: 'primary'
      },
      portfolioSettings: {
        tax_rate: 10,
        benchmark: 'CSI 300',
        risk_free_rate: 2.5
      },
      rateForm: {
        currency_id: null,
        rate: null,
        rate_date: null
      },
      exchangeRates: [
        { currency_code: 'USD', rate: 7.2, rate_date: '2024-01-15' },
        { currency_code: 'HKD', rate: 0.92, rate_date: '2024-01-15' },
        { currency_code: 'EUR', rate: 7.8, rate_date: '2024-01-15' }
      ]
    }
  },
  
  computed: {
    // Pinia store
    store() {
      return useMainStore()
    },
    
    // State from store
    currencies() {
      return this.store.currencies
    },
    
    loading() {
      return this.store.loading
    }
  },
  
  async created() {
    await this.store.fetchCurrencies()
  },
  
  methods: {
    
    saveCurrencySettings() {
      this.$message.success('Currency settings saved')
    },
    
    savePortfolioSettings() {
      this.$message.success('Portfolio settings saved')
    },
    
    saveRate() {
      this.showAddRateDialog = false
      this.$message.success('Exchange rate saved')
    },
    
    editRate(rate) {
      this.$message.info('Edit rate functionality to be implemented')
    },
    
    importRates() {
      this.$message.info('Import rates functionality to be implemented')
    }
  }
}
</script>

<style scoped>
.settings {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style> 