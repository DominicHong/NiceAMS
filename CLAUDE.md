# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NiceAMS** is a comprehensive portfolio tracking and asset management system built with a modern tech stack:
- **Frontend**: Vue.js 3 + Element Plus UI + Chart.js for visualizations
- **Backend**: FastAPI + SQLModel + SQLite for robust data management
- **Architecture**: Clean separation of frontend/backend with RESTful APIs
- **Database**: SQLite for local deployment with comprehensive data models

## Quick Start Commands

### Environment Setup
```bash
# Backend setup
cd backend
pip install -r requirements.txt
python init_data.py  # Initialize database with sample data

# Frontend setup
cd frontend
npm install
```

### Development Server Commands
```bash
# Backend (FastAPI)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Vue.js)
npm run dev  # Development server on port 3000
npm run build  # Production build
npm run preview  # Preview production build

# Quick start both servers (Windows)
start.bat

# Quick start both servers (Unix)
./start.sh
```

### Database Management
```bash
# Reset and reinitialize database with sample data
cd backend
python init_data.py

# Manual database operations
python -c "from models import *; create_db_and_tables()"
```

## Architecture Details

### Backend Structure (`backend/`)
- **`main.py`**: FastAPI application with REST endpoints
- **`models.py`**: SQLModel database models and schema definitions
- **`services.py`**: Business logic for portfolio calculations, currency conversion, and position management
- **`init_data.py`**: Database initialization with sample portfolio data

### Frontend Structure (`frontend/`)
- **`src/main.js`**: Vue.js application entry point
- **`src/App.vue`**: Root component with navigation
- **`src/stores/index.js`**: Pinia store for state management
- **`src/router/index.js`**: Vue Router configuration
- **`src/views/`**: Main application views (Dashboard, Portfolio, Transactions, Assets, Analytics, Settings)
- **`src/components/`**: Reusable UI components

## Key API Endpoints

### Core Endpoints
- `GET /portfolios/` - List all portfolios
- `GET /portfolios/{id}/positions` - Get portfolio positions
- `GET /portfolios/{id}/summary` - Portfolio summary with totals
- `GET /portfolios/{id}/performance-metrics` - Performance calculations
- `GET /transactions/` - List transactions
- `POST /transactions/` - Create new transaction
- `POST /import/transactions/` - Import transactions from CSV
- `POST /import/prices/` - Import prices from CSV

### Data Models
- **Currency**: Multi-currency support (CNY, USD, HKD, EUR)
- **Asset**: Stocks, bonds, funds, ETFs, cash instruments
- **Transaction**: Buy/sell/dividends/cash flows with flexible action types
- **Position**: Portfolio positions with P&L calculations
- **Price**: Historical and real-time price data
- **PortfolioStatistics**: Calculated performance metrics

## Development Workflows

### Adding New Transaction Types
1. Add action type to `Transaction.action` enum in `models.py`
2. Update transaction processing logic in `services.py`
3. Add UI support in frontend transaction forms
4. Update CSV import validation in `main.py`

### Currency Management
- Primary currency is set via `Currency.is_primary` flag
- Exchange rates managed through `/exchange-rates/` endpoints
- Automatic currency conversion for P&L calculations
- Cash assets follow `{CURRENCY_CODE}_CASH` naming convention

### Position Calculation
- Positions calculated from transaction history using FIFO methodology
- `PositionService.update_positions_for_period()` handles historical recalculation
- Positions cached in database for performance
- Use `/portfolios/{id}/recalculate-positions` to refresh from transactions

### Performance Metrics
- **TWR (Time-Weighted Return)**: Calculated using Modified Dietz method
- **Volatility**: Annualized standard deviation of daily returns
- **Sharpe Ratio**: Risk-adjusted return calculation
- **Max Drawdown**: Largest peak-to-trough decline
- Metrics calculated in `PortfolioService.calculate_portfolio_statistics()`

## CSV Import Formats

### Transactions CSV
```csv
trade_date,action,symbol,name,quantity,price,fees,amount,notes
2024-01-15,buy,AAPL,Apple Inc.,10,150.00,5.00,1500.00,Initial purchase
2024-01-20,dividends,AAPL,Apple Inc.,0,0,0,15.00,Dividend payment
```

### Prices CSV
```csv
symbol,price_date,price
AAPL,2024-01-15,150.00
GOOGL,2024-01-15,2800.00
```

## Common Development Tasks

### Testing New Features
1. Start backend: `uvicorn main:app --reload`
2. Access API docs: `http://localhost:8000/docs`
3. Start frontend: `npm run dev` (port 3000)
4. Test with sample data from `init_data.py`

### Database Schema Changes
1. Update models in `models.py`
2. Drop existing database: `rm backend/portfolio.db`
3. Reinitialize: `python init_data.py`

### Adding New Asset Types
1. Extend `Asset.asset_type` enum in `models.py`
2. Update asset creation logic in transaction import
3. Add UI components for new asset type selection
4. Update validation rules in services

### Debugging Position Calculations
- Use `/portfolios/{id}/recalculate-positions` endpoint for manual recalculation
- Check transaction data integrity with `/transactions/` endpoint
- Verify price data with `/assets/{id}/prices` (implement if needed)
- Monitor console logs for calculation errors

## Environment Configuration

### Backend Configuration
- Database: SQLite file `backend/portfolio.db`
- API: CORS enabled for all origins (development)
- Port: 8000 (configurable)

### Frontend Configuration
- API Base URL: `http://localhost:8000` (configured in `src/stores/index.js`)
- Development port: 3000 (in `vite.config.js`)
- Build output: `frontend/dist`

## Performance Considerations

- Position calculations are computationally intensive for large datasets
- Consider implementing caching strategies for frequently accessed calculations
- Database queries optimized for common portfolio operations
- CSV import processes large files efficiently using pandas DataFrames