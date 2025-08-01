# NiceAMS - Nice Asset Management System

NiceAMS is a comprehensive Asset Management System built with a Python FastAPI backend and Vue.js frontend. It provides portfolio tracking, transaction management, performance analytics, and risk metrics for individual investors.

## Table of Contents
- [NiceAMS - Nice Asset Management System](#niceams---nice-asset-management-system)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
    - [Core Features](#core-features)
    - [Technical Features](#technical-features)
  - [Project Structure](#project-structure)
  - [Installation \& Setup](#installation--setup)
    - [Prerequisites](#prerequisites)
    - [Backend Setup](#backend-setup)
    - [Frontend Setup](#frontend-setup)
  - [Usage](#usage)
    - [Dashboard](#dashboard)
    - [Transaction Management](#transaction-management)
    - [Portfolio Positions](#portfolio-positions)
    - [Asset Management](#asset-management)
    - [Analytics \& Reporting](#analytics--reporting)
    - [Settings](#settings)
  - [API Documentation](#api-documentation)
  - [Database Schema](#database-schema)
    - [Core Tables](#core-tables)
    - [Transaction Types](#transaction-types)
  - [CSV Import Format](#csv-import-format)
    - [Transactions CSV](#transactions-csv)
    - [Prices CSV](#prices-csv)
  - [Performance Calculations](#performance-calculations)
    - [Time-Weighted Return (TWR)](#time-weighted-return-twr)
    - [Risk Metrics](#risk-metrics)
  - [Customization](#customization)
    - [Adding New Asset Types](#adding-new-asset-types)
    - [Adding New Currencies](#adding-new-currencies)
    - [Custom Metadata](#custom-metadata)
  - [Contributing](#contributing)
  - [License](#license)
  - [Architecture Notes](#architecture-notes)
    - [Design Principles](#design-principles)
    - [Technology Choices](#technology-choices)

## Features

### Core Features
- **Multi-currency Support**: Track assets in CNY, USD, HKD, EUR with automatic currency conversion
- **Portfolio Management**: Comprehensive portfolio tracking with positions, transactions, and performance metrics
- **Transaction Processing**: Support for buy/sell/dividends/splits/cash flows with CSV import
- **Real-time Pricing**: Integration with price APIs and manual price updates
- **Advanced Analytics**: Time-Weighted Return (TWR), Sharpe ratio, max drawdown, volatility calculations
- **Asset Allocation**: Visual breakdown by asset type and sector
- **Multi-asset Support**: Stocks, bonds, funds, ETFs, cash. See [Adding New Asset Types] for more details.

### Technical Features
- **Frontend**: Vue.js 3 + Element Plus UI + Chart.js for visualizations
- **State Management**: Pinia for application state management
- **Language**: TypeScript for type-safe development
- **Build Tool**: Vite for development and production builds
- **Component Architecture**: Composition API with `<script setup>` syntax
- **Backend**: FastAPI + SQLModel + SQLite for robust data management
- **Architecture**: Clean separation of frontend/backend with RESTful APIs
- **Database**: SQLite for local deployment with comprehensive data models
- **CSV Import/Export**: Batch transaction and price data management

## Project Structure

```
NiceAMS/
├── .gitignore
├── .vscode/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLModel database models
│   ├── services.py          # Business logic and calculations
│   ├── init_data.py         # Database initialization with sample data
│   ├── requirements.txt     # Python dependencies
│   ├── sample_portfolio.csv
│   └── sample_transactions.csv
├── frontend/
│   ├── src/
│   │   ├── main.js          # Vue.js application entry
│   │   ├── App.vue          # Main application component
│   │   ├── router/          # Vue Router configuration
│   │   ├── stores/          # Pinia state management
│   │   ├── components/       # Reusable Vue components
│   │   ├── mixins/           # Reusable composition logic
│   │   └── views/           # Page components
│   ├── package.json         # Node.js dependencies
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.js
├── tests/
├── start.bat                # Windows startup script
├── start.sh                 # Unix startup script
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- npm

### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Initialize database with sample data**:
```bash
python init_data.py
```

3. **Start the FastAPI server**:
```bash
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install Node.js dependencies**:
```bash
cd frontend
npm install
```

2. **Start the development server**:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

### Dashboard
- **Portfolio Overview**: Total value, unrealized P&L, asset count, and performance metrics
- **Performance Chart**: Interactive time-series chart with 1M/3M/6M/1Y/All time ranges
- **Asset Allocation**: Pie chart showing distribution by asset type
- **Top Positions**: List of largest positions with current values and P&L
- **Recent Transactions**: Latest portfolio activity

### Transaction Management
- **Add Transactions**: Manual entry of buy/sell/dividend/cash transactions
- **CSV Import**: Batch import of transaction data
- **Transaction History**: Filterable and sortable transaction list
- **Supported Actions**: buy, sell, cash_in, cash_out, dividends, interest, split, tax

### Portfolio Positions
- **Current Positions**: Real-time portfolio positions with market values
- **Unrealized P&L**: Gain/loss calculations for each position
- **Asset Details**: Symbol, name, quantity, current price, market value

### Asset Management
- **Asset Registry**: Maintain database of stocks, bonds, funds, ETFs
- **Multi-currency Assets**: Support for assets in different currencies
- **Metadata Support**: Sector classification and custom attributes

### Analytics & Reporting
- **Performance Metrics**: TWR, annualized returns, volatility, Sharpe ratio
- **Risk Analysis**: Maximum drawdown, beta, alpha calculations
- **Benchmark Comparison**: Compare portfolio performance against market indices
- **Monthly Returns**: Detailed month-by-month performance breakdown

### Settings
- **Currency Management**: Set primary currency and exchange rates
- **Portfolio Configuration**: Tax rates, benchmark indices, risk-free rates
- **Exchange Rate Updates**: Manual rate updates and CSV import

## API Documentation

The FastAPI backend provides comprehensive REST APIs:

- **Currencies**: `/currencies/` - Currency management
- **Assets**: `/assets/` - Asset registry and metadata
- **Transactions**: `/transactions/` - Transaction CRUD operations
- **Portfolios**: `/portfolios/` - Portfolio management and statistics
- **Import**: `/import/transactions/`, `/import/prices/` - CSV data import
- **Positions**: `/portfolios/{id}/positions` - Portfolio positions
- **Statistics**: `/portfolios/{id}/statistics` - Performance metrics

Visit `http://localhost:8000/docs` for interactive API documentation.

## Database Schema

### Core Tables
- **Currency**: Multi-currency support with exchange rates
- **Asset**: Security master with symbols, names, and metadata
- **Transaction**: All portfolio transactions with flexible action types
- **Price**: Historical and real-time price data
- **Portfolio**: Portfolio definitions and configurations
- **Position**: Current portfolio positions
- **PortfolioStatistics**: Calculated performance metrics

### Transaction Types
- `buy`: Purchase of securities
- `sell`: Sale of securities
- `cash_in`: Cash deposits
- `cash_out`: Cash withdrawals
- `dividends`: Dividend payments
- `interest`: Interest income
- `split`: Stock splits and bonus shares
- `tax`: Tax payments

## CSV Import Format

### Transactions CSV
Required columns:
- `trade_date`: Transaction date (YYYY-MM-DD)
- `action`: Transaction type (buy, sell, cash_in, cash_out, etc.)
- `symbol`: Asset symbol (for buy/sell transactions)
- `name`: Asset name
- `quantity`: Number of shares/units
- `price`: Price per share/unit
- `fees`: Transaction fees
- `amount`: Total transaction amount
- `notes`: Transaction notes

### Prices CSV
```csv
symbol,price_date,price
AAPL,2024-01-15,150.00
GOOGL,2024-01-15,2800.00
```

## Performance Calculations

### Time-Weighted Return (TWR)
The system implements proper TWR calculations using the Modified Dietz method, accounting for:
- Cash flows timing
- Portfolio value changes
- Fee adjustments
- Currency conversions

### Risk Metrics
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return calculation
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Beta**: Systematic risk relative to benchmark

## Customization

### Adding New Asset Types
1. Update the `Asset` model in `models.py`
2. Add asset type options in the frontend components
3. Implement specific logic in `services.py` if needed

### Adding New Currencies
1. Use the Currency management interface in Settings
2. Add exchange rate data via CSV import or manual entry
3. The system automatically handles currency conversions

### Custom Metadata
Assets support flexible metadata through the `AssetMetadata` model:
```python
# Example: Add sector classification
{
    "match": {"symbol": "AAPL"},
    "apply": {"sector": "Technology"}
}
```

## Contributing

This is a personal portfolio management system. For modifications:

1. **Backend Changes**: Modify models, services, or API endpoints
2. **Frontend Changes**: Update Vue components or add new features
3. **Database Changes**: Create migration scripts for schema updates
4. **Testing**: Add test cases for new functionality

## License

This project is for personal use. Please respect the licenses of third-party dependencies.

## Architecture Notes

### Design Principles
- **Separation of Concerns**: Clean frontend/backend architecture
- **Data Integrity**: Comprehensive validation and error handling
- **Scalability**: Modular design for easy extension
- **Performance**: Efficient database queries and caching strategies
- **Security**: Input validation and SQL injection prevention

### Technology Choices
- **SQLModel**: Type-safe database operations with Pydantic integration
- **FastAPI**: Modern, fast API framework with automatic documentation
- **Vue.js 3**: Reactive frontend framework with composition API
- **Element Plus**: Professional UI component library
- **Chart.js**: Flexible charting library for financial visualizations
