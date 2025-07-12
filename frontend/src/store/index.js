import { createStore } from 'vuex'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

// Configure axios
axios.defaults.baseURL = API_BASE_URL
axios.defaults.timeout = 10000

export default createStore({
  state: {
    // Portfolio data
    portfolios: [],
    currentPortfolio: null,
    positions: [],
    
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
  },
  
  mutations: {
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    
    SET_ERROR(state, error) {
      state.error = error
    },
    
    SET_PORTFOLIOS(state, portfolios) {
      state.portfolios = portfolios
    },
    
    SET_CURRENT_PORTFOLIO(state, portfolio) {
      state.currentPortfolio = portfolio
    },
    
    SET_POSITIONS(state, positions) {
      state.positions = positions
    },
    
    SET_TRANSACTIONS(state, transactions) {
      state.transactions = transactions
    },
    
    ADD_TRANSACTION(state, transaction) {
      state.transactions.push(transaction)
    },
    
    SET_ASSETS(state, assets) {
      state.assets = assets
    },
    
    ADD_ASSET(state, asset) {
      state.assets.push(asset)
    },
    
    SET_CURRENCIES(state, currencies) {
      state.currencies = currencies
      state.primaryCurrency = currencies.find(c => c.is_primary)
    },
    
    SET_EXCHANGE_RATES(state, rates) {
      state.exchangeRates = rates
    },
    
    SET_PORTFOLIO_STATS(state, stats) {
      state.portfolioStats = stats
    },
    
    SET_ASSET_ALLOCATION(state, allocation) {
      state.assetAllocation = allocation
    }
  },
  
  actions: {
    // Portfolio actions
    async fetchPortfolios({ commit }) {
      try {
        commit('SET_LOADING', true)
        const response = await axios.get('/portfolios/')
        commit('SET_PORTFOLIOS', response.data)
        
        // Set first portfolio as current if none selected
        if (response.data.length > 0 && !this.state.currentPortfolio) {
          commit('SET_CURRENT_PORTFOLIO', response.data[0])
        }
      } catch (error) {
        commit('SET_ERROR', error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async createPortfolio({ commit }, portfolioData) {
      try {
        const response = await axios.post('/portfolios/', portfolioData)
        commit('SET_CURRENT_PORTFOLIO', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    async fetchPositions({ commit }, portfolioId) {
      try {
        const response = await axios.get(`/portfolios/${portfolioId}/positions`)
        commit('SET_POSITIONS', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    },

    async fetchPositionsForDate({ commit }, { portfolioId, asOfDate }) {
      try {
        commit('SET_LOADING', true)
        const params = asOfDate ? { as_of_date: asOfDate } : {}
        const response = await axios.get(`/portfolios/${portfolioId}/positions`, { params })
        commit('SET_POSITIONS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async recalculatePositions({ commit }, { portfolioId, asOfDate }) {
      try {
        commit('SET_LOADING', true)
        const params = asOfDate ? { as_of_date: asOfDate } : {}
        const response = await axios.post(`/portfolios/${portfolioId}/recalculate-positions`, null, { params })
        // Refresh positions after recalculation
        const positionsResponse = await axios.get(`/portfolios/${portfolioId}/positions`)
        commit('SET_POSITIONS', positionsResponse.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // Transaction actions
    async fetchTransactions({ commit }, portfolioId = null) {
      try {
        commit('SET_LOADING', true)
        const params = portfolioId ? { portfolio_id: portfolioId } : {}
        const response = await axios.get('/transactions/', { params })
        commit('SET_TRANSACTIONS', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async createTransaction({ commit }, transactionData) {
      try {
        const response = await axios.post('/transactions/', transactionData)
        commit('ADD_TRANSACTION', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    async importTransactions({ commit }, file) {
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
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    // Asset actions
    async fetchAssets({ commit }) {
      try {
        const response = await axios.get('/assets/')
        commit('SET_ASSETS', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    },
    
    async createAsset({ commit }, assetData) {
      try {
        const response = await axios.post('/assets/', assetData)
        commit('ADD_ASSET', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      }
    },
    
    // Currency actions
    async fetchCurrencies({ commit }) {
      try {
        const response = await axios.get('/currencies/')
        commit('SET_CURRENCIES', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    },
    
    async fetchExchangeRates({ commit }) {
      try {
        const response = await axios.get('/exchange-rates/')
        commit('SET_EXCHANGE_RATES', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    },
    
    // Statistics actions
    async fetchPortfolioStats({ commit }, { portfolioId, startDate, endDate }) {
      try {
        const response = await axios.get(`/portfolios/${portfolioId}/statistics`, {
          params: { start_date: startDate, end_date: endDate }
        })
        commit('SET_PORTFOLIO_STATS', response.data)
      } catch (error) {
        commit('SET_ERROR', error.message)
      }
    }
  },
  
  getters: {
    // Portfolio getters
    currentPortfolioId: state => state.currentPortfolio?.id,
    
    totalPortfolioValue: state => {
      return state.positions.reduce((total, position) => {
        return total + (position.market_value || 0)
      }, 0)
    },
    
    totalPnL: state => {
      return state.positions.reduce((total, position) => {
        return total + (position.total_pnl || 0)
      }, 0)
    },
    
    // Asset getters
    assetsByType: state => {
      const grouped = {}
      state.assets.forEach(asset => {
        if (!grouped[asset.asset_type]) {
          grouped[asset.asset_type] = []
        }
        grouped[asset.asset_type].push(asset)
      })
      return grouped
    },
    
    // Transaction getters
    transactionsByType: state => {
      const grouped = {}
      state.transactions.forEach(transaction => {
        if (!grouped[transaction.action]) {
          grouped[transaction.action] = []
        }
        grouped[transaction.action].push(transaction)
      })
      return grouped
    },
    
    recentTransactions: state => {
      return state.transactions
        .sort((a, b) => new Date(b.trade_date) - new Date(a.trade_date))
        .slice(0, 10)
    }
  }
}) 