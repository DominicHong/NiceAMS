import { defineStore } from 'pinia'
import axios from 'axios'
import dayjs from 'dayjs'

const API_BASE_URL = 'http://localhost:8000'

// Configure axios
axios.defaults.baseURL = API_BASE_URL
axios.defaults.timeout = 10000

export const useMainStore = defineStore('main', {
  state: () => ({
    // Portfolio data
    portfolios: [],
    currentPortfolio: null,
    positions: [],
    portfolioSummary: null,
    
    // Transaction data
    transactions: [],
    
    // Asset data
    assets: [],
    prices: [],
    
    // Currency data
    currencies: [],
    exchangeRates: [],
    primaryCurrency: null,
    
    // UI state
    loading: false,
    error: null,
    
    // Statistics
    portfolioStats: {},
    assetAllocation: {},
    performanceHistory: [],
    
    // Settings
    settings: {}
  }),

  getters: {
    // Portfolio getters
    currentPortfolioId: (state) => state.currentPortfolio?.id,
    
    totalPortfolioValue: (state) => {
      return state.positions.reduce((total, position) => {
        return total + (position.market_value || 0)
      }, 0)
    },
    
    totalPnL: (state) => {
      return state.positions.reduce((total, position) => {
        return total + (position.total_pnl || 0)
      }, 0)
    },
    
    // Asset getters
    assetsByType: (state) => {
      const grouped = {}
      state.assets.forEach(asset => {
        if (!grouped[asset.type]) {
          grouped[asset.type] = []
        }
        grouped[asset.type].push(asset)
      })
      return grouped
    },
    
    // Transaction getters
    transactionsByType: (state) => {
      const grouped = {}
      state.transactions.forEach(transaction => {
        if (!grouped[transaction.action]) {
          grouped[transaction.action] = []
        }
        grouped[transaction.action].push(transaction)
      })
      return grouped
    },
    
    recentTransactions: (state) => {
      return state.transactions
        .sort((a, b) => new Date(b.trade_date) - new Date(a.trade_date))
        .slice(0, 10)
    }
  },

  actions: {
    setLoading(loading) {
      this.loading = loading
    },
    
    setError(error) {
      this.error = error
    },
    
    setPortfolios(portfolios) {
      this.portfolios = portfolios
    },
    
    setCurrentPortfolio(portfolio) {
      this.currentPortfolio = portfolio
    },
    
    setPositions(positions) {
      this.positions = positions
    },
    
    setPortfolioSummary(summary) {
      this.portfolioSummary = summary
    },
    
    setTransactions(transactions) {
      this.transactions = transactions
    },
    
    addTransaction(transaction) {
      this.transactions.push(transaction)
    },
    
    setAssets(assets) {
      this.assets = assets
    },
    
    addAsset(asset) {
      this.assets.push(asset)
    },
    
    setCurrencies(currencies) {
      this.currencies = currencies
      this.primaryCurrency = currencies.find(c => c.is_primary)
    },
    
    setExchangeRates(rates) {
      this.exchangeRates = rates
    },
    
    setPortfolioStats(stats) {
      this.portfolioStats = stats
    },
    
    setAssetAllocation(allocation) {
      this.assetAllocation = allocation
    },
    
    setPerformanceHistory(history) {
      this.performanceHistory = history
    },
    
    setSettings(settings) {
      this.settings = settings
    },
    
    setSetting(key, value) {
      this.settings[key] = value
    },

    // Portfolio actions
    async fetchPortfolios() {
      try {
        this.setLoading(true)
        const response = await axios.get('/portfolios/')
        this.setPortfolios(response.data)
        
        // Set first portfolio as current if none selected
        if (response.data.length > 0 && !this.currentPortfolio) {
          this.setCurrentPortfolio(response.data[0])
        }
      } catch (error) {
        this.setError(error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    async createPortfolio(portfolioData) {
      try {
        const response = await axios.post('/portfolios/', portfolioData)
        this.setCurrentPortfolio(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },
    
    async fetchPositions(portfolioId, asOfDate = null) {
      try {
        this.setLoading(true)
        const params = asOfDate ? { as_of_date: asOfDate } : {}
        const response = await axios.get(`/portfolios/${portfolioId}/positions`, { params })
        this.setPositions(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async recalculatePositions({ portfolioId, asOfDate }) {
      try {
        this.setLoading(true)
        const params = asOfDate ? { as_of_date: asOfDate } : {}
        const response = await axios.post(`/portfolios/${portfolioId}/recalculate-positions`, null, { params })
        // Refresh positions after recalculation for the specific date
        const positionsParams = asOfDate ? { as_of_date: asOfDate } : {}
        const positionsResponse = await axios.get(`/portfolios/${portfolioId}/positions`, { params: positionsParams })
        this.setPositions(positionsResponse.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    async fetchPortfolioSummary({ portfolioId, asOfDate }) {
      try {
        this.setLoading(true)
        const params = asOfDate ? { as_of_date: asOfDate } : {}
        const response = await axios.get(`/portfolios/${portfolioId}/summary`, { params })
        this.setPortfolioSummary(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // Transaction actions
    async fetchTransactions(portfolioId = null) {
      try {
        this.setLoading(true)
        const params = portfolioId ? { portfolio_id: portfolioId } : {}
        const response = await axios.get('/transactions/', { params })
        this.setTransactions(response.data)
      } catch (error) {
        this.setError(error.message)
      } finally {
        this.setLoading(false)
      }
    },
    
    async createTransaction(transactionData) {
      try {
        const response = await axios.post('/transactions/', transactionData)
        this.addTransaction(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },
    
    async importTransactions(file) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await axios.post('/import/transactions/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },
    
    // Asset actions
    async fetchAssets() {
      try {
        const response = await axios.get('/assets/')
        this.setAssets(response.data)
      } catch (error) {
        this.setError(error.message)
      }
    },
    
    async createAsset(assetData) {
      try {
        const response = await axios.post('/assets/', assetData)
        this.addAsset(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },

    async updateAsset(assetId, assetData) {
      try {
        const response = await axios.put(`/assets/${assetId}`, assetData)
        // Update the asset in the local state
        const index = this.assets.findIndex(asset => asset.id === assetId)
        if (index !== -1) {
          this.assets[index] = response.data
        }
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },

    async deleteAsset(assetId) {
      try {
        await axios.delete(`/assets/${assetId}`)
        // Remove the asset from local state
        this.assets = this.assets.filter(asset => asset.id !== assetId)
        return true
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },
    
    // Currency actions
    async fetchCurrencies() {
      try {
        const response = await axios.get('/currencies/')
        this.setCurrencies(response.data)
      } catch (error) {
        this.setError(error.message)
      }
    },
    
    async fetchExchangeRates() {
      try {
        const response = await axios.get('/exchange-rates/')
        this.setExchangeRates(response.data)
      } catch (error) {
        this.setError(error.message)
      }
    },
    
    // Statistics actions

    async fetchPerformanceMetrics(portfolioId) {
      try {
        this.setLoading(true)
        const response = await axios.get(`/portfolios/${portfolioId}/performance-metrics`)
        this.setPortfolioStats(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchPerformanceHistory(portfolioId, options = {}) {
      try {
        this.setLoading(true)
        const { startDate, endDate } = options
        
        // Ensure both start_date and end_date are always provided
        let params = {}
        if (startDate && endDate) {
          params = { start_date: startDate, end_date: endDate }
        } else {
          // Default to 1-year range if dates are not provided
          const endDate = new Date()
          const startDate = new Date(endDate)
          startDate.setDate(startDate.getDate() - 365)
          
          // Format dates as YYYY-MM-DD using dayjs
          params = { 
            start_date: dayjs(startDate).format('YYYY-MM-DD'), 
            end_date: dayjs(endDate).format('YYYY-MM-DD') 
          }
        }
        
        const response = await axios.get(`/portfolios/${portfolioId}/performance-history`, { params })
        this.setPerformanceHistory(response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchMonthlyReturns(portfolioId) {
      try {
        this.setLoading(true)
        const response = await axios.get(`/portfolios/${portfolioId}/monthly-returns`)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchAssetAllocation(portfolioId, asOfDate) {
      try {
        this.setLoading(true)
        const params = { by: 'type' }
        if (asOfDate) {
          params.as_of_date = asOfDate
        }
        const response = await axios.get(`/portfolios/${portfolioId}/allocation`, {
          params
        })
        this.setAssetAllocation(response.data.asset_allocation || {})
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // Settings actions
    async fetchSettings() {
      try {
        const response = await axios.get('/settings/')
        // Convert array to object for easier access
        const settingsObj = {}
        response.data.forEach(setting => {
          settingsObj[setting.key] = setting
        })
        this.setSettings(settingsObj)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },
    
    async fetchSetting(key) {
      try {
        const response = await axios.get(`/settings/${key}`)
        this.setSetting(key, response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    },
    
    async saveSetting(key, value, description = null) {
      try {
        const settingData = {
          key: key,
          value: value.toString(),
          description: description
        }
        const response = await axios.post('/settings/', settingData)
        this.setSetting(key, response.data)
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      }
    }
  }
})