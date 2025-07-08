from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import json


class Currency(SQLModel, table=True):
    """Currency model for multi-currency support"""
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)  # CNY, USD, HKD, etc.
    name: str
    symbol: str  # ¥, $, HK$, etc.
    is_primary: bool = Field(default=False)
    
    # Relationships
    exchange_rates: List["ExchangeRate"] = Relationship(back_populates="currency")
    transactions: List["Transaction"] = Relationship(back_populates="currency")


class ExchangeRate(SQLModel, table=True):
    """Exchange rate model for currency conversion"""
    id: Optional[int] = Field(default=None, primary_key=True)
    currency_id: int = Field(foreign_key="currency.id")
    rate_date: date
    rate_to_primary: Decimal  # Exchange rate to primary currency
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    currency: Currency = Relationship(back_populates="exchange_rates")


class Asset(SQLModel, table=True):
    """Asset model for stocks, bonds, funds, etc."""
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(unique=True, index=True)  # Ticker symbol
    name: str
    isin: Optional[str] = None
    asset_type: str  # stock, bond, fund, cash, etc.
    currency_id: int = Field(foreign_key="currency.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    currency: Currency = Relationship()
    transactions: List["Transaction"] = Relationship(back_populates="asset")
    prices: List["Price"] = Relationship(back_populates="asset")
    asset_metadata: List["AssetMetadata"] = Relationship(back_populates="asset")


class AssetMetadata(SQLModel, table=True):
    """Metadata model for asset attributes"""
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id")
    attribute_name: str
    attribute_value: str  # JSON string for complex values
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    asset: Asset = Relationship(back_populates="asset_metadata")


class Transaction(SQLModel, table=True):
    """Transaction model for all portfolio transactions"""
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    trade_date: date
    action: str  # buy, sell, cash_in, cash_out, tax, dividends, split, interest
    asset_id: Optional[int] = Field(default=None, foreign_key="asset.id")
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Decimal
    fees: Optional[Decimal] = Field(default=0)
    currency_id: int = Field(foreign_key="currency.id")
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    portfolio: "Portfolio" = Relationship()
    asset: Optional[Asset] = Relationship(back_populates="transactions")
    currency: Currency = Relationship(back_populates="transactions")


class Price(SQLModel, table=True):
    """Price model for historical and real-time prices"""
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id")
    price_date: date
    price: Decimal
    price_type: str  # real_time, historical, manual
    source: Optional[str] = None  # akshare, manual, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    asset: Asset = Relationship(back_populates="prices")


class Portfolio(SQLModel, table=True):
    """Portfolio model for portfolio statistics"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    base_currency_id: int = Field(foreign_key="currency.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    base_currency: Currency = Relationship()
    transactions: List["Transaction"] = Relationship(back_populates="portfolio")
    statistics: List["PortfolioStatistics"] = Relationship(back_populates="portfolio")


class PortfolioStatistics(SQLModel, table=True):
    """Portfolio statistics model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    stat_date: date
    total_value: Decimal
    cash_balance: Decimal
    invested_amount: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_return: Decimal
    time_weighted_return: Decimal
    max_drawdown: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    portfolio: Portfolio = Relationship(back_populates="statistics")


class Holding(SQLModel, table=True):
    """Current holdings model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    asset_id: int = Field(foreign_key="asset.id")
    quantity: Decimal
    average_cost: Decimal
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    portfolio: Portfolio = Relationship()
    asset: Asset = Relationship()


# Database setup
DATABASE_URL = "sqlite:///./portfolio.db"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)

def drop_db_and_tables():
    """Drop database and tables"""
    SQLModel.metadata.drop_all(engine)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session 