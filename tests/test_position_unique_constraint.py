"""Tests for Position unique constraint"""

import pytest
from sqlmodel import Session, create_engine, select
from sqlalchemy.exc import IntegrityError
from datetime import date
from decimal import Decimal
from backend.models import Position, Portfolio, Asset, Currency, create_db_and_tables, drop_db_and_tables


@pytest.fixture
def test_db():
    """Create a test database and drop it after the test"""
    # Create a test database
    test_engine = create_engine("sqlite:///:memory:")
    
    # Bind the engine to the models
    from backend.models import SQLModel
    SQLModel.metadata.create_all(test_engine)
    
    # Create a session
    with Session(test_engine) as session:
        # Create test data
        currency = Currency(id=1, code="USD", name="US Dollar", symbol="$", is_primary=True)
        session.add(currency)
        session.commit()
        
        portfolio = Portfolio(id=1, name="Test Portfolio", base_currency_id=1)
        session.add(portfolio)
        session.commit()
        
        asset = Asset(id=1, symbol="AAPL", name="Apple Inc.", type="stock", currency_id=1)
        session.add(asset)
        session.commit()
        
        yield session
        
    # Drop the test database
    SQLModel.metadata.drop_all(test_engine)


def test_position_unique_constraint(test_db: Session):
    """Test that Position unique constraint prevents duplicate entries"""
    # Create a position
    position_date = date(2023, 1, 1)
    position1 = Position(
        portfolio_id=1,
        asset_id=1,
        position_date=position_date,
        quantity=Decimal("100"),
        average_cost=Decimal("150.00"),
        current_price=Decimal("160.00"),
        market_value=Decimal("16000.00"),
        total_pnl=Decimal("1000.00")
    )
    
    test_db.add(position1)
    test_db.commit()
    
    # Try to create another position with the same portfolio_id, asset_id, and position_date
    position2 = Position(
        portfolio_id=1,
        asset_id=1,
        position_date=position_date,
        quantity=Decimal("200"),
        average_cost=Decimal("155.00"),
        current_price=Decimal("165.00"),
        market_value=Decimal("33000.00"),
        total_pnl=Decimal("2000.00")
    )
    
    test_db.add(position2)
    
    # This should raise an IntegrityError due to the unique constraint
    with pytest.raises(IntegrityError):
        test_db.commit()


def test_position_different_dates_allowed(test_db: Session):
    """Test that positions with different dates are allowed"""
    # Create a position
    position_date1 = date(2023, 1, 1)
    position1 = Position(
        portfolio_id=1,
        asset_id=1,
        position_date=position_date1,
        quantity=Decimal("100"),
        average_cost=Decimal("150.00"),
        current_price=Decimal("160.00"),
        market_value=Decimal("16000.00"),
        total_pnl=Decimal("1000.00")
    )
    
    test_db.add(position1)
    test_db.commit()
    
    # Create another position with a different date
    position_date2 = date(2023, 1, 2)
    position2 = Position(
        portfolio_id=1,
        asset_id=1,
        position_date=position_date2,
        quantity=Decimal("200"),
        average_cost=Decimal("155.00"),
        current_price=Decimal("165.00"),
        market_value=Decimal("33000.00"),
        total_pnl=Decimal("2000.00")
    )
    
    test_db.add(position2)
    # This should not raise an exception
    test_db.commit()
    
    # Verify both positions exist
    positions = test_db.exec(select(Position)).all()
    assert len(positions) == 2


def test_position_different_assets_allowed(test_db: Session):
    """Test that positions with different assets on the same date are allowed"""
    # Create a position
    position_date = date(2023, 1, 1)
    position1 = Position(
        portfolio_id=1,
        asset_id=1,
        position_date=position_date,
        quantity=Decimal("100"),
        average_cost=Decimal("150.00"),
        current_price=Decimal("160.00"),
        market_value=Decimal("16000.00"),
        total_pnl=Decimal("1000.00")
    )
    
    test_db.add(position1)
    test_db.commit()
    
    # Create another asset
    asset2 = Asset(id=2, symbol="GOOGL", name="Alphabet Inc.", type="stock", currency_id=1)
    test_db.add(asset2)
    test_db.commit()
    
    # Create another position with a different asset
    position2 = Position(
        portfolio_id=1,
        asset_id=2,
        position_date=position_date,
        quantity=Decimal("50"),
        average_cost=Decimal("2500.00"),
        current_price=Decimal("2600.00"),
        market_value=Decimal("130000.00"),
        total_pnl=Decimal("5000.00")
    )
    
    test_db.add(position2)
    # This should not raise an exception
    test_db.commit()
    
    # Verify both positions exist
    positions = test_db.exec(select(Position)).all()
    assert len(positions) == 2


def test_position_different_portfolios_allowed(test_db: Session):
    """Test that positions with different portfolios on the same date are allowed"""
    # Create a position
    position_date = date(2023, 1, 1)
    position1 = Position(
        portfolio_id=1,
        asset_id=1,
        position_date=position_date,
        quantity=Decimal("100"),
        average_cost=Decimal("150.00"),
        current_price=Decimal("160.00"),
        market_value=Decimal("16000.00"),
        total_pnl=Decimal("1000.00")
    )
    
    test_db.add(position1)
    test_db.commit()
    
    # Create another portfolio
    portfolio2 = Portfolio(id=2, name="Test Portfolio 2", base_currency_id=1)
    test_db.add(portfolio2)
    test_db.commit()
    
    # Create another position with a different portfolio
    position2 = Position(
        portfolio_id=2,
        asset_id=1,
        position_date=position_date,
        quantity=Decimal("200"),
        average_cost=Decimal("155.00"),
        current_price=Decimal("165.00"),
        market_value=Decimal("33000.00"),
        total_pnl=Decimal("2000.00")
    )
    
    test_db.add(position2)
    # This should not raise an exception
    test_db.commit()
    
    # Verify both positions exist
    positions = test_db.exec(select(Position)).all()
    assert len(positions) == 2