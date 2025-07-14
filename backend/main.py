from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import pandas as pd
import io
from contextlib import asynccontextmanager
import numpy as np

from models import (
    Currency, ExchangeRate, Asset, AssetMetadata, Transaction, Price, 
    Portfolio, PortfolioStatistics, Position, get_session, create_db_and_tables
)
from services import PortfolioService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for the FastAPI application."""
    create_db_and_tables()
    yield

app = FastAPI(title="Portfolio Tracker API", version="1.0.0", lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Currency endpoints
@app.get("/currencies/", response_model=List[Currency])
def get_currencies(session: Session = Depends(get_session)):
    """Get all currencies"""
    currencies = session.exec(select(Currency)).all()
    return currencies

@app.post("/currencies/", response_model=Currency)
def create_currency(currency: Currency, session: Session = Depends(get_session)):
    """Create a new currency"""
    session.add(currency)
    session.commit()
    session.refresh(currency)
    return currency

@app.get("/currencies/{currency_id}", response_model=Currency)
def get_currency(currency_id: int, session: Session = Depends(get_session)):
    """Get a specific currency"""
    currency = session.get(Currency, currency_id)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return currency

# Exchange Rate endpoints
@app.get("/exchange-rates/", response_model=List[ExchangeRate])
def get_exchange_rates(session: Session = Depends(get_session)):
    """Get all exchange rates"""
    rates = session.exec(select(ExchangeRate)).all()
    return rates

@app.post("/exchange-rates/", response_model=ExchangeRate)
def create_exchange_rate(rate: ExchangeRate, session: Session = Depends(get_session)):
    """Create a new exchange rate"""
    session.add(rate)
    session.commit()
    session.refresh(rate)
    return rate

# Asset endpoints
@app.get("/assets/", response_model=List[Asset])
def get_assets(session: Session = Depends(get_session)):
    """Get all assets"""
    assets = session.exec(select(Asset)).all()
    return assets

@app.post("/assets/", response_model=Asset)
def create_asset(asset: Asset, session: Session = Depends(get_session)):
    """Create a new asset"""
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset

@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: int, session: Session = Depends(get_session)):
    """Get a specific asset"""
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

# Transaction endpoints
@app.get("/transactions/", response_model=List[Transaction])
def get_transactions(portfolio_id: int | None = None, session: Session = Depends(get_session)):
    """Get all transactions, optionally filtered by portfolio"""
    query = select(Transaction).order_by(Transaction.trade_date.desc())  
    
    if portfolio_id:
        query = query.where(Transaction.portfolio_id == portfolio_id)
    
    transactions = session.exec(query).all()
    return transactions

@app.post("/transactions/", response_model=Transaction)
def create_transaction(transaction: Transaction, session: Session = Depends(get_session)):
    """Create a new transaction"""
    # Ensure portfolio_id is set
    if not transaction.portfolio_id:
        # Use the first portfolio as default if not specified
        portfolio = session.exec(select(Portfolio)).first()
        if portfolio:
            transaction.portfolio_id = portfolio.id
        else:
            raise HTTPException(status_code=400, detail="No portfolio available. Please create a portfolio first.")
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
        
    return transaction

@app.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: int, session: Session = Depends(get_session)):
    """Get a specific transaction"""
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

def _import_transactions_from_dataframe(df: pd.DataFrame, session: Session) -> List[Transaction]:
    """Core logic for importing transactions from a pandas DataFrame"""
    # Validate required columns
    required_columns = ['trade_date', 'action', 'amount']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    transactions = []
    
    # Get all currencies for mapping
    currencies = session.exec(select(Currency)).all()
    currency_map = {curr.code: curr.id for curr in currencies}
    
    for _, row in df.iterrows():
        asset = None
        currency_id = 1  # Default to CNY
        
        # Handle symbol and asset lookup
        if 'symbol' in row and pd.notna(row['symbol']):
            symbol = str(row['symbol']).strip()
            
            # Check if this is a cash transaction with currency code
            if row['action'] in ['cash_in', 'cash_out', 'interest', 'tax'] and symbol in currency_map:
                # Convert currency code to cash asset symbol
                symbol = f"{symbol}_CASH"
                currency_id = currency_map[str(row['symbol']).strip()]
            
            # Look up asset by symbol
            asset = session.exec(select(Asset).where(Asset.symbol == symbol)).first()
            
            if not asset:
                # Determine asset type and currency
                if symbol.endswith('_CASH'):
                    asset_type = 'cash'
                    curr_code = symbol.replace('_CASH', '')
                    currency_id = currency_map.get(curr_code, 1)
                elif symbol.endswith('.SH') or symbol.endswith('.SZ'):
                    asset_type = 'stock'
                    currency_id = currency_map.get('CNY', 1)
                elif symbol in ['AAPL', 'GOOGL', 'MSFT', 'TSLA']:  # US stocks
                    asset_type = 'stock'
                    currency_id = currency_map.get('USD', 1)
                elif 'ETF' in str(row.get('name', '')).upper():
                    asset_type = 'etf'
                    currency_id = currency_map.get('CNY', 1)
                else:
                    asset_type = 'stock'  # Default
                    currency_id = currency_map.get('CNY', 1)
                
                # Create new asset
                asset = Asset(
                    symbol=symbol,
                    name=row.get('name', symbol),
                    isin=row.get('isin'),
                    asset_type=asset_type,
                    currency_id=currency_id
                )
                session.add(asset)
                session.commit()
                session.refresh(asset)
            else:
                # Use the asset's currency
                currency_id = asset.currency_id
        
        # Handle quantity for cash transactions
        quantity = None
        if 'quantity' in row and pd.notna(row['quantity']):
            quantity = Decimal(str(row['quantity']))
        elif row['action'] in ['cash_in', 'cash_out'] and asset and asset.asset_type == 'cash':
            # For cash transactions without explicit quantity, use amount as quantity
            quantity = Decimal(str(row['amount']))
        
        # Handle price for cash transactions
        price = None
        if 'price' in row and pd.notna(row['price']):
            price = Decimal(str(row['price']))
        elif asset and asset.asset_type == 'cash':
            # Cash assets always have a price of 1.0
            price = Decimal('1.0')
        
        # Get the first portfolio (or create logic to determine which portfolio)
        portfolio = session.exec(select(Portfolio)).first()
        if not portfolio:
            raise ValueError("No portfolio available. Please create a portfolio first.")
        
        # Create transaction
        transaction = Transaction(
            portfolio_id=portfolio.id,
            trade_date=pd.to_datetime(row['trade_date']).date(),
            action=row['action'],
            asset_id=asset.id if asset else None,
            quantity=quantity,
            price=price,
            amount=Decimal(str(row['amount'])),
            fees=Decimal(str(row['fees'])) if 'fees' in row and pd.notna(row['fees']) else Decimal('0'),
            currency_id=currency_id,
            notes=row.get('notes')
        )
        transactions.append(transaction)
    
    return transactions

# CSV Import endpoints
@app.post("/import/transactions/")
async def import_transactions(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Import transactions from CSV file"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        transactions = _import_transactions_from_dataframe(df, session)
        
        session.add_all(transactions)
        session.commit()
                
        return {"message": f"Successfully imported {len(transactions)} transactions"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importing CSV: {str(e)}")

@app.post("/import/prices/")
async def import_prices(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Import prices from CSV file"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['symbol', 'price_date', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_columns}")
        
        prices = []
        for _, row in df.iterrows():
            # Find asset
            asset = session.exec(select(Asset).where(Asset.symbol == row['symbol'])).first()
            if not asset:
                continue  # Skip if asset not found
            
            # Create price
            price = Price(
                asset_id=asset.id,
                price_date=pd.to_datetime(row['price_date']).date(),
                price=Decimal(str(row['price'])),
                price_type='historical',
                source='csv_import'
            )
            prices.append(price)
        
        session.add_all(prices)
        session.commit()
        
        return {"message": f"Successfully imported {len(prices)} prices"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importing CSV: {str(e)}")

# Portfolio endpoints
@app.get("/portfolios/", response_model=List[Portfolio])
def get_portfolios(session: Session = Depends(get_session)):
    """Get all portfolios"""
    portfolios = session.exec(select(Portfolio)).all()
    return portfolios

@app.post("/portfolios/", response_model=Portfolio)
def create_portfolio(portfolio: Portfolio, session: Session = Depends(get_session)):
    """Create a new portfolio"""
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    return portfolio

@app.get("/portfolios/{portfolio_id}/positions")
def get_portfolio_positions(portfolio_id: int, as_of_date: Optional[str] = None, session: Session = Depends(get_session)):
    """Get portfolio positions for a specific date or latest positions"""
    try:
        from services import PositionService
        
        position_service = PositionService(session)
        
        if as_of_date:
            # Parse the date string
            target_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
            positions = session.exec(
                select(Position)
                .where(Position.portfolio_id == portfolio_id)
                .where(Position.position_date == target_date)
            ).all()
        else:
            # Get latest positions
            positions = position_service.get_latest_positions(portfolio_id)
        
        # Return positions with asset information
        positions_data = []
        for position in positions:
            asset = session.get(Asset, position.asset_id)
            if asset:
                positions_data.append({
                    "id": position.id,
                    "portfolio_id": position.portfolio_id,
                    "asset_id": position.asset_id,
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "quantity": position.quantity,
                    "average_cost": position.average_cost,
                    "current_price": position.current_price,
                    "market_value": position.market_value,
                    "total_pnl": position.total_pnl,
                    "position_date": position.position_date
                })
        
        return positions_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving positions: {str(e)}")

@app.get("/portfolios/{portfolio_id}/statistics")
def get_portfolio_statistics(portfolio_id: int, session: Session = Depends(get_session)):
    """Get portfolio statistics"""
    stats = session.exec(select(PortfolioStatistics).where(PortfolioStatistics.portfolio_id == portfolio_id)).all()
    return stats

@app.get("/portfolios/{portfolio_id}/monthly-returns")
def get_monthly_returns(portfolio_id: int, session: Session = Depends(get_session)):
    """Get monthly returns for a portfolio"""
    try:
        portfolio_service = PortfolioService(session)
        
        # Get all transactions for the portfolio
        transactions = session.exec(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.trade_date)  
        ).all()
        
        if not transactions:
            return []
        
        # Get date range from first to last transaction
        start_date = transactions[0].trade_date
        end_date = transactions[-1].trade_date
        
        # Calculate monthly returns
        monthly_returns = []
        current_date = start_date.replace(day=1)  # Start from first day of month
        
        while current_date <= end_date:
            # Calculate returns for this month
            month_start = current_date
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            # Get portfolio value at start and end of month
            try:
                start_value = portfolio_service.calculate_portfolio_value(portfolio_id, month_start)
                end_value = portfolio_service.calculate_portfolio_value(portfolio_id, month_end)
                
                # Calculate returns
                start_total = start_value.get('total_value', 0)
                end_total = end_value.get('total_value', 0)
                
                if start_total > 0:
                    portfolio_return = ((end_total - start_total) / start_total) * 100
                else:
                    portfolio_return = 0
                
                # Mock benchmark return (in real implementation, you'd get this from external data)
                benchmark_return = portfolio_return * 0.8  # Simplified benchmark
                alpha = portfolio_return - benchmark_return
                
                monthly_returns.append({
                    'month': current_date.strftime('%Y-%m'),
                    'portfolio_return': round(portfolio_return, 2),
                    'benchmark_return': round(benchmark_return, 2),
                    'alpha': round(alpha, 2)
                })
                
            except Exception as e:
                # If calculation fails, add zeros
                monthly_returns.append({
                    'month': current_date.strftime('%Y-%m'),
                    'portfolio_return': 0,
                    'benchmark_return': 0,
                    'alpha': 0
                })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return monthly_returns
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error calculating monthly returns: {str(e)}")

@app.get("/portfolios/{portfolio_id}/performance-metrics")
def get_performance_metrics(portfolio_id: int, session: Session = Depends(get_session)):
    """Get portfolio performance metrics"""
    try:
        portfolio_service = PortfolioService(session)
        
        # Get all transactions to determine date range
        transactions = session.exec(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.trade_date)
        ).all()
        
        if not transactions:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "beta": 1.0,
                "message": "No transactions found"
            }
        
        # Use date range from first transaction to today
        start_date = transactions[0].trade_date
        end_date = date.today()
        
        # Calculate portfolio statistics
        stats = portfolio_service.calculate_portfolio_statistics(portfolio_id, start_date, end_date)
        
        # Get asset allocation for additional context
        allocation = portfolio_service.get_asset_allocation(portfolio_id, end_date)
        
        # Safe function to convert and round values
        def safe_round(value, decimals=2):
            try:
                if value is None:
                    return 0.0
                # Convert to float and ensure it's real
                val = float(value)
                if np.iscomplex(val) or np.isnan(val) or np.isinf(val):
                    return 0.0
                return round(float(np.real(val)), decimals)
            except (TypeError, ValueError, AttributeError):
                return 0.0
        
        return {
            "total_return": safe_round(stats.get("time_weighted_return", 0)),
            "annualized_return": safe_round(stats.get("annualized_return", 0)),
            "volatility": safe_round(stats.get("volatility", 0)),
            "sharpe_ratio": safe_round(stats.get("sharpe_ratio", 0)),
            "max_drawdown": safe_round(stats.get("max_drawdown", 0)),
            "beta": 1.0,  # Mock beta - would need market data to calculate properly
            "beginning_value": safe_round(stats.get("beginning_value", 0)),
            "ending_value": safe_round(stats.get("ending_value", 0)),
            "period_days": int(stats.get("period_days", 0)),
            "asset_allocation": allocation.get("by_type", {}),
            "calculation_date": end_date.isoformat()
        }
        
    except Exception as e:
        print(f"Error in performance metrics endpoint: {e}")
        # Return safe default values
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "beta": 1.0,
            "beginning_value": 0.0,
            "ending_value": 0.0,
            "period_days": 0,
            "asset_allocation": {},
            "calculation_date": date.today().isoformat(),
            "message": f"Error calculating performance metrics: {str(e)}"
        }

@app.post("/portfolios/{portfolio_id}/recalculate-positions")
def recalculate_positions(portfolio_id: int, as_of_date: Optional[str] = None, session: Session = Depends(get_session)):
    """Recalculate positions from existing transactions up to a specific date"""
    try:
        from services import PositionService
        
        # Parse the date if provided, otherwise use today
        if as_of_date:
            target_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Get all transactions for this portfolio up to the target date
        transactions = session.exec(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .where(Transaction.trade_date <= target_date)
            .order_by(Transaction.trade_date, Transaction.id)  
        ).all()
        
        if not transactions:
            return {"message": f"No transactions found up to {target_date.strftime('%Y-%m-%d')}"}
        
        # Use PositionService to calculate positions up to the target date
        position_service = PositionService(session)
        
        # Get the date range from transactions
        start_date = min(t.trade_date for t in transactions)
        end_date = target_date
        
        # Calculate positions for the period up to the target date
        positions = position_service.update_positions_for_period(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            save_to_db=True
        )
        
        # Update positions with current market values and prices
        portfolio_service = PortfolioService(session)
        portfolio_service.calculate_portfolio_value(portfolio_id, end_date)
        
        return {"message": f"Successfully recalculated positions up to {target_date.strftime('%Y-%m-%d')} from {len(transactions)} transactions"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error recalculating positions: {str(e)}")

# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 