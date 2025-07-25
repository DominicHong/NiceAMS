"""
Test cases for PriceService
"""

import pytest
from datetime import date
from decimal import Decimal
from sqlmodel import Session, select

# Add backend directory to path to enable relative imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import Asset, Price
from sqlmodel import SQLModel, create_engine
from services import PriceService

ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(ROOT_PATH, "tests", "test_portfolio.db")}"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)

def drop_db_and_tables():
    """Drop database and tables"""
    SQLModel.metadata.drop_all(engine)


class TestPriceService:
    """Test cases for PriceService"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and sample data"""
        # Drop and recreate database tables to ensure schema matches
        drop_db_and_tables()
        create_db_and_tables()
        
        # Add test data
        with Session(engine) as session:
            # Create asset
            asset = Asset(
                symbol="600036.SH",
                name="China Merchants Bank",
                isin=None,
                type="stock",
                currency_id=1
            )
            session.add(asset)
            session.commit()
            session.refresh(asset)
            
            # Add test price for 2025-6-30
            price = Price(
                asset_id=asset.id,
                price_date=date(2025, 6, 30),
                price=Decimal("45.95"),
                price_type="historical",
                source="test"
            )
            session.add(price)
            session.commit()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database"""
        drop_db_and_tables()
    
    def test_get_latest_price(self):
        """Test get_latest_price method returns correct price"""
        with Session(engine) as session:
            # Get the asset
            asset = session.exec(
                select(Asset).where(Asset.symbol == "600036.SH")
            ).first()
            
            # Create PriceService instance
            price_service = PriceService(session)
            
            # Get latest price for 2025-6-30
            price = price_service.get_latest_price(asset.id, date(2025, 6, 30))
            
            # Verify the price
            assert price is not None, "Price should not be None"
            assert price.price == Decimal("45.95"), f"Expected price 45.95, got {price.price}"
            assert price.price_date == date(2025, 6, 30), f"Expected date 2025-06-30, got {price.price_date}"
    
    def test_unique_constraint(self):
        """Test that unique constraint prevents duplicate prices for same asset and date"""
        with Session(engine) as session:
            # Get the asset
            asset = session.exec(
                select(Asset).where(Asset.symbol == "600036.SH")
            ).first()
            
            # Try to insert a duplicate price
            duplicate_price = Price(
                asset_id=asset.id,
                price_date=date(2025, 6, 30),  # Same date as existing price
                price=Decimal("50.00"),
                price_type="historical",
                source="test_duplicate"
            )
            
            # Add the duplicate price
            session.add(duplicate_price)
            
            # Check that committing raises an IntegrityError
            with pytest.raises(Exception) as exc_info:
                session.commit()
            
            # Rollback the session
            session.rollback()
            
            # Verify that the duplicate price was not added
            prices = session.exec(
                select(Price).where(
                    Price.asset_id == asset.id,
                    Price.price_date == date(2025, 6, 30)
                )
            ).all()
            
            # Should only have one price
            assert len(prices) == 1, f"Expected 1 price, got {len(prices)}"
            assert prices[0].price == Decimal("45.95"), f"Expected price 45.95, got {prices[0].price}"