"""Shared test configuration for all test modules"""

import pytest
import tempfile
import os
from sqlmodel import create_engine, SQLModel, Session
from backend.models import Currency, Portfolio, Asset


@pytest.fixture
def test_db():
    """Create a fresh test database for each test"""
    # Create a temporary file-based SQLite database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        
        with Session(engine) as session:
            # Initialize basic test data for each test
            currency = Currency(code="USD", name="US Dollar", symbol="$", is_primary=True)
            session.add(currency)
            session.flush()  # Get the ID without committing
            
            portfolio = Portfolio(name="Test Portfolio", base_currency_id=currency.id)
            session.add(portfolio)
            session.flush()
            
            asset = Asset(symbol="AAPL", name="Apple Inc.", type="stock", currency_id=currency.id)
            session.add(asset)
            session.flush()
            
            session.commit()
            
            # Store references for tests to use
            session._test_currency = currency
            session._test_portfolio = portfolio
            session._test_asset = asset
            
            yield session
            
    finally:
        # Clean up - close the engine and remove the temporary file
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)