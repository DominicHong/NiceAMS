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
                <el-radio value="primary">Primary Currency</el-radio>
                <el-radio value="original">Original Currency</el-radio>
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

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useMainStore } from '../stores'

// Pinia store
const store = useMainStore()

// Reactive data
const showAddRateDialog = ref(false)
const currencySettings = ref({
  primary_currency: 1,
  display_format: 'primary'
})
const portfolioSettings = ref({
  tax_rate: 0.2,
  benchmark: 'CSI 300',
  risk_free_rate: 2.5
})
const rateForm = ref({
  currency_id: null,
  rate: null,
  rate_date: null
})
const exchangeRates = ref([
  { currency_code: 'USD', rate: 7.2, rate_date: '2024-01-15' },
  { currency_code: 'HKD', rate: 0.92, rate_date: '2024-01-15' },
  { currency_code: 'EUR', rate: 7.8, rate_date: '2024-01-15' }
])

// Computed properties
const currencies = computed(() => store.currencies)
const loading = computed(() => store.loading)

// Methods
const saveRate = () => {
  showAddRateDialog.value = false
  ElMessage.success('Exchange rate saved')
}

const editRate = (rate) => {
  ElMessage.info('Edit rate functionality to be implemented')
}

const importRates = () => {
  ElMessage.info('Import rates functionality to be implemented')
}

// Methods
const saveCurrencySettings = async () => {
  try {
    await store.saveSetting('primary_currency', currencySettings.value.primary_currency, 'Primary currency for display')
    await store.saveSetting('display_format', currencySettings.value.display_format, 'Currency display format')
    ElMessage.success('Currency settings saved')
  } catch (error) {
    ElMessage.error('Failed to save currency settings')
  }
}

const savePortfolioSettings = async () => {
  try {
    // Convert tax rate from percentage to decimal before saving
    const taxRateDecimal = portfolioSettings.value.tax_rate / 100
    await store.saveSetting('tax_rate', taxRateDecimal, 'Tax rate percentage')
    await store.saveSetting('benchmark', portfolioSettings.value.benchmark, 'Portfolio benchmark')
    // Convert risk-free rate from percentage to decimal before saving
    const riskFreeRateDecimal = portfolioSettings.value.risk_free_rate / 100
    await store.saveSetting('risk_free_rate', riskFreeRateDecimal, 'Risk-free rate for calculations')
    ElMessage.success('Portfolio settings saved')
  } catch (error) {
    ElMessage.error('Failed to save portfolio settings')
  }
}

const loadSettings = async () => {
  try {
    await store.fetchSettings()
    
    // Load currency settings
    if (store.settings.primary_currency) {
      currencySettings.value.primary_currency = parseInt(store.settings.primary_currency.value)
    }
    if (store.settings.display_format) {
      currencySettings.value.display_format = store.settings.display_format.value
    }
    
    // Load portfolio settings
    if (store.settings.tax_rate) {
      // Convert tax rate from decimal to percentage for display
      portfolioSettings.value.tax_rate = parseFloat(store.settings.tax_rate.value) * 100
    }
    if (store.settings.benchmark) {
      portfolioSettings.value.benchmark = store.settings.benchmark.value
    }
    if (store.settings.risk_free_rate) {
      // Convert risk-free rate from decimal to percentage for display
      portfolioSettings.value.risk_free_rate = parseFloat(store.settings.risk_free_rate.value) * 100
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

// Lifecycle
onMounted(async () => {
  await store.fetchCurrencies()
  await loadSettings()
})
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