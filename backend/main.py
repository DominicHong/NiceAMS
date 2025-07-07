from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
import pandas as pd
import json
from contextlib import asynccontextmanager

from models import (
    Currency, ExchangeRate, Asset, AssetMetadata, Transaction, Price, 
    Portfolio, PortfolioStatistics, Holding, get_session, create_db_and_tables
)

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
def get_transactions(session: Session = Depends(get_session)):
    """Get all transactions"""
    transactions = session.exec(select(Transaction)).all()
    return transactions

@app.post("/transactions/", response_model=Transaction)
def create_transaction(transaction: Transaction, session: Session = Depends(get_session)):
    """Create a new transaction"""
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

# CSV Import endpoints
@app.post("/import/transactions/")
async def import_transactions(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Import transactions from CSV file"""
    try:
        contents = await file.read()
        df = pd.read_csv(contents.decode('utf-8'))
        
        # Validate required columns
        required_columns = ['trade_date', 'action', 'amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_columns}")
        
        transactions = []
        for _, row in df.iterrows():
            # Create asset if not exists
            asset = None
            if 'symbol' in row and pd.notna(row['symbol']):
                asset = session.exec(select(Asset).where(Asset.symbol == row['symbol'])).first()
                if not asset:
                    # Create new asset
                    asset = Asset(
                        symbol=row['symbol'],
                        name=row.get('name', row['symbol']),
                        isin=row.get('isin'),
                        asset_type='stock',  # Default
                        currency_id=1  # Default to first currency
                    )
                    session.add(asset)
                    session.commit()
                    session.refresh(asset)
            
            # Create transaction
            transaction = Transaction(
                trade_date=pd.to_datetime(row['trade_date']).date(),
                action=row['action'],
                asset_id=asset.id if asset else None,
                quantity=Decimal(str(row['quantity'])) if 'quantity' in row and pd.notna(row['quantity']) else None,
                price=Decimal(str(row['price'])) if 'price' in row and pd.notna(row['price']) else None,
                amount=Decimal(str(row['amount'])),
                fees=Decimal(str(row['fees'])) if 'fees' in row and pd.notna(row['fees']) else Decimal('0'),
                currency_id=1,  # Default to first currency
                notes=row.get('notes')
            )
            transactions.append(transaction)
        
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
        df = pd.read_csv(contents.decode('utf-8'))
        
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

@app.get("/portfolios/{portfolio_id}/holdings")
def get_portfolio_holdings(portfolio_id: int, session: Session = Depends(get_session)):
    """Get portfolio holdings"""
    holdings = session.exec(select(Holding).where(Holding.portfolio_id == portfolio_id)).all()
    return holdings

@app.get("/portfolios/{portfolio_id}/statistics")
def get_portfolio_statistics(portfolio_id: int, session: Session = Depends(get_session)):
    """Get portfolio statistics"""
    stats = session.exec(select(PortfolioStatistics).where(PortfolioStatistics.portfolio_id == portfolio_id)).all()
    return stats

# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 