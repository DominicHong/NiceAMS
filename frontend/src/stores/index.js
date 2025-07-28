import { defineStore } from 'pinia'
import axios from 'axios'

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
    assetAllocation: {}
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
    // State setters (replacing mutations)
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
    
    async fetchPositions(portfolioId) {
      try {
        const response = await axios.get(`/portfolios/${portfolioId}/positions`)
        this.setPositions(response.data)
      } catch (error) {
        this.setError(error.message)
      }
    },

    async fetchPositionsForDate({ portfolioId, asOfDate }) {
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
    async fetchPortfolioStats({ portfolioId, startDate, endDate }) {
      try {
        const response = await axios.get(`/portfolios/${portfolioId}/statistics`, {
          params: { start_date: startDate, end_date: endDate }
        })
        this.setPortfolioStats(response.data)
      } catch (error) {
        this.setError(error.message)
      }
    },

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

    async fetchPerformanceHistory(portfolioId, days = 365) {
      try {
        this.setLoading(true)
        const response = await axios.get(`/portfolios/${portfolioId}/performance-history`, {
          params: { days }
        })
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchAssetAllocation(portfolioId) {
      try {
        this.setLoading(true)
        const response = await axios.get(`/portfolios/${portfolioId}/allocation`, {
          params: { by: 'type' }
        })
        this.setAssetAllocation(response.data.asset_allocation || {})
        return response.data
      } catch (error) {
        this.setError(error.message)
        throw error
      } finally {
        this.setLoading(false)
      }
    }
  }
})