"""
Test cases for PriceService
"""

import pytest
from datetime import date
from decimal import Decimal
from sqlmodel import Session, select

from backend.models import create_db_and_tables, drop_db_and_tables, engine, Asset, Price
from backend.services import PriceService


class TestPriceService:
    """Test cases for PriceService"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and sample data"""
        # Create database and tables
        create_db_and_tables()
        
        # Add test data
        with Session(engine) as session:
            # Check if asset already exists
            asset = session.exec(
                select(Asset).where(Asset.symbol == "600036.SH")
            ).first()
            
            # If not, create it
            if not asset:
                asset = Asset(
                    symbol="600036.SH",
                    name="China Merchants Bank",
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