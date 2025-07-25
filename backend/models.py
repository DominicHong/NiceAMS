from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import UniqueConstraint
import json
import os

# Database setup
ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(ROOT_PATH, "backend", "portfolio.db")}"
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


def utcnow() -> datetime:
    """Returns the current datetime in UTC."""
    return datetime.now(timezone.utc)


class Currency(SQLModel, table=True):
    """Currency model for multi-currency support"""
    id: int = Field(unique=True, primary_key=True)
    code: str = Field(unique=True, index=True)  # CNY, USD, HKD, etc.
    name: str
    symbol: str  # ¥, $, HK$, etc.
    is_primary: bool = Field(default=False)
    
    # Relationships
    exchange_rates: list["ExchangeRate"] = Relationship(back_populates="currency")
    transactions: list["Transaction"] = Relationship(back_populates="currency")


class ExchangeRate(SQLModel, table=True):
    """Exchange rate model for currency conversion"""
    id: int = Field(unique=True, primary_key=True)
    currency_id: int = Field(foreign_key="currency.id")
    rate_date: date
    rate_to_primary: Decimal  # Exchange rate to primary currency
    created_at: datetime = Field(default_factory=utcnow)
    
    # Relationships
    currency: Currency = Relationship(back_populates="exchange_rates")


class Asset(SQLModel, table=True):
    """Asset model for stocks, bonds, funds, etc."""
    id: int = Field(unique=True, primary_key=True)
    symbol: str = Field(unique=True, index=True)  # Ticker symbol
    name: str
    isin: str | None = None
    type: str  # stock, bond, fund, etf, cash.
    currency_id: int = Field(foreign_key="currency.id")
    created_at: datetime = Field(default_factory=utcnow)
    
    @staticmethod
    def validate_type(value: str) -> None:
        """Validate that type is one of the allowed values."""
        allowed_types = {"stock", "bond", "fund", "etf", "cash"}
        if value not in allowed_types:
            raise ValueError(f"type must be one of {allowed_types}, got '{value}'")
            
    def __setattr__(self, name: str, value) -> None:
        """Override to validate type when it's set."""
        if name == "type":
            self.validate_type(value)
        super().__setattr__(name, value)

    # Relationships
    currency: Currency = Relationship()
    transactions: list["Transaction"] = Relationship(back_populates="asset")
    prices: list["Price"] = Relationship(back_populates="asset")
    asset_metadata: list["AssetMetadata"] = Relationship(back_populates="asset")
    positions: list["Position"] = Relationship(back_populates="asset")


class AssetMetadata(SQLModel, table=True):
    """Metadata model for asset attributes"""
    id: int = Field(unique=True, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id")
    attribute_name: str
    attribute_value: str  # JSON string for complex values
    created_at: datetime = Field(default_factory=utcnow)
    
    # Relationships
    asset: Asset = Relationship(back_populates="asset_metadata")


class Transaction(SQLModel, table=True):
    """Transaction model for all portfolio transactions"""
    id: int = Field(unique=True, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    trade_date: date
    action: str  # buy, sell, cash_in, cash_out, tax, dividends, split, interest
    asset_id: int = Field(foreign_key="asset.id")  # Required for all transactions
    quantity: Decimal | None = None
    price: Decimal | None = None
    amount: Decimal
    fees: Decimal | None = Field(default=0)
    currency_id: int = Field(foreign_key="currency.id")
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    
    # Relationships
    portfolio: "Portfolio" = Relationship()
    asset: Asset = Relationship(back_populates="transactions")  
    currency: Currency = Relationship(back_populates="transactions")


class Price(SQLModel, table=True):
    """Price model for historical and real-time prices"""
    id: int = Field(unique=True, primary_key=True)
    asset_id: int = Field(foreign_key="asset.id")
    price_date: date
    price: Decimal
    price_type: str  # real_time, historical, manual
    source: str | None = None  # akshare, manual, etc.
    created_at: datetime = Field(default_factory=utcnow)
    
    # Add unique constraint for asset_id and price_date
    __table_args__ = (UniqueConstraint('asset_id', 'price_date', name='uq_price_asset_date'),)
    
    # Relationships
    asset: Asset = Relationship(back_populates="prices")


class Portfolio(SQLModel, table=True):
    """Portfolio model for portfolio statistics"""
    id: int = Field(primary_key=True)
    name: str
    description: str | None = None
    base_currency_id: int = Field(foreign_key="currency.id")
    created_at: datetime = Field(default_factory=utcnow)
    
    # Relationships
    base_currency: Currency = Relationship()
    transactions: list["Transaction"] = Relationship(back_populates="portfolio")
    statistics: list["PortfolioStatistics"] = Relationship(back_populates="portfolio")
    positions: list["Position"] = Relationship(back_populates="portfolio")


class PortfolioStatistics(SQLModel, table=True):
    """Portfolio statistics model"""
    id: int = Field(unique=True, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    stat_date: date
    total_value: Decimal
    cash_balance: Decimal
    invested_amount: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_return: Decimal
    time_weighted_return: Decimal
    max_drawdown: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    created_at: datetime = Field(default_factory=utcnow)
    
    # Relationships
    portfolio: Portfolio = Relationship(back_populates="statistics")


class Position(SQLModel, table=True):
    """Asset Position model for a portfolio on a specific date"""
    id: int = Field(unique=True, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    asset_id: int = Field(foreign_key="asset.id")
    position_date: date  # The specific date this position is for
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal | None = None
    market_value: Decimal | None = None
    total_pnl: Decimal | None = None  # market_value + cash_received_on_sale + dividends_received - cash_paid_on_bought
    
    # Relationships
    portfolio: Portfolio = Relationship(back_populates="positions")
    asset: Asset = Relationship(back_populates="positions")
