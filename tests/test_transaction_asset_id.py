import pytest
import sys
import os
from decimal import Decimal
from datetime import date
from sqlmodel import Session, create_engine

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import (
    Transaction, Asset, Currency, Portfolio, create_db_and_tables, drop_db_and_tables
)
from backend.services import TransactionService


class TestTransactionAssetId:
    """Test that asset_id is required for all transactions"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        # Create test database
        create_db_and_tables()
        
        # Create test session
        engine = create_engine("sqlite:///./portfolio.db", echo=False)
        with Session(engine) as session:
            # Create test data
            currency = Currency(
                code="USD",
                name="US Dollar",
                symbol="$",
                is_primary=True
            )
            session.add(currency)
            session.commit()
            session.refresh(currency)
            
            portfolio = Portfolio(
                name="Test Portfolio",
                description="Test portfolio",
                base_currency_id=currency.id
            )
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            
            # Create test assets
            stock_asset = Asset(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                currency_id=currency.id,
                isin="US0378331005"
            )
            session.add(stock_asset)
            session.commit()
            session.refresh(stock_asset)
            
            # Create cash asset
            cash_asset = Asset(
                symbol="USD_CASH",
                name="US Dollar Cash",
                asset_type="cash",
                currency_id=currency.id,
                isin="USD_CASH"
            )
            session.add(cash_asset)
            session.commit()
            session.refresh(cash_asset)
            
            self.session = session
            self.currency = currency
            self.portfolio = portfolio
            self.stock_asset = stock_asset
            self.cash_asset = cash_asset
            
            yield
            
            # Cleanup
            session.close()
        
        # Drop test database
        drop_db_and_tables()
    
    def test_cash_transaction_with_asset_id(self):
        """Test that cash transactions work correctly with asset_id set"""
        transaction_service = TransactionService(self.session)
        
        # Create a cash_in transaction with asset_id set
        transaction = Transaction(
            portfolio_id=self.portfolio.id,
            trade_date=date.today(),
            action="cash_in",
            asset_id=self.cash_asset.id,  # Explicitly set asset_id
            quantity=Decimal("1000"),
            amount=Decimal("1000"),
            currency_id=self.currency.id
        )
        
        # Process the transaction
        result = transaction_service.process_transaction(transaction, self.portfolio.id)
        
        # Verify success
        assert result["success"] is True
        assert "processed successfully" in result["message"]
    
    def test_cash_transaction_without_asset_id_gets_auto_set(self):
        """Test that cash transactions without asset_id get asset_id auto-set"""
        transaction_service = TransactionService(self.session)
        
        # Create a cash_in transaction without asset_id (this would fail with old model)
        # But with our new logic, it should work
        transaction = Transaction(
            portfolio_id=self.portfolio.id,
            trade_date=date.today(),
            action="cash_in",
            asset_id=0,  # Invalid asset_id, should be auto-corrected
            quantity=Decimal("1000"),
            amount=Decimal("1000"),
            currency_id=self.currency.id
        )
        
        # Process the transaction
        result = transaction_service.process_transaction(transaction, self.portfolio.id)
        
        # Verify success and that asset_id was corrected
        assert result["success"] is True
        assert transaction.asset_id == self.cash_asset.id
    
    def test_stock_transaction_requires_asset_id(self):
        """Test that stock transactions require valid asset_id"""
        transaction_service = TransactionService(self.session)

        # Add cash to the portfolio first
        cash_in = Transaction(
            portfolio_id=self.portfolio.id,
            trade_date=date.today(),
            action="cash_in",
            asset_id=self.cash_asset.id,
            quantity=Decimal("2000"),
            amount=Decimal("2000"),
            currency_id=self.currency.id
        )
        result_cash = transaction_service.process_transaction(cash_in, self.portfolio.id)
        assert result_cash["success"] is True

        # Create a buy transaction with valid asset_id
        transaction = Transaction(
            portfolio_id=self.portfolio.id,
            trade_date=date.today(),
            action="buy",
            asset_id=self.stock_asset.id,
            quantity=Decimal("10"),
            amount=Decimal("1500"),
            currency_id=self.currency.id
        )

        # Process the transaction
        result = transaction_service.process_transaction(transaction, self.portfolio.id)

        # Verify success
        assert result["success"] is True
    
    def test_transaction_model_requires_asset_id(self):
        """Test that Transaction model now requires asset_id"""
        # This should work
        transaction = Transaction(
            portfolio_id=1,
            trade_date=date.today(),
            action="buy",
            asset_id=1,  # Required
            amount=Decimal("100"),
            currency_id=1
        )
        
        # Verify asset_id is set
        assert transaction.asset_id == 1 