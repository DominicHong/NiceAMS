from sqlmodel import Session, select
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict

from models import (
    Currency, ExchangeRate, Asset, AssetMetadata, Transaction, Price, Portfolio, 
    PortfolioStatistics, Holding, get_session
)


class CurrencyService:
    """Service for currency conversion and management"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_primary_currency(self) -> Currency:
        """Get the primary currency"""
        primary = self.session.exec(select(Currency).where(Currency.is_primary == True)).first()
        if not primary:
            # Create CNY as default primary currency
            primary = Currency(
                code="CNY",
                name="Chinese Yuan",
                symbol="¥",
                is_primary=True
            )
            self.session.add(primary)
            self.session.commit()
            self.session.refresh(primary)
        return primary
    
    def get_exchange_rate(self, currency_id: int, rate_date: date) -> Decimal:
        """Get exchange rate for a currency on a specific date"""
        if currency_id == self.get_primary_currency().id:
            return Decimal('1.0')
        
        # Get the most recent exchange rate before or on the date
        rate = self.session.exec(
            select(ExchangeRate)
            .where(ExchangeRate.currency_id == currency_id)
            .where(ExchangeRate.rate_date <= rate_date)
            .order_by(ExchangeRate.rate_date.desc())
        ).first()
        
        return rate.rate_to_primary if rate else Decimal('1.0')
    
    def convert_to_primary_currency(self, amount: Decimal, currency_id: int, rate_date: date) -> Decimal:
        """Convert amount to primary currency"""
        rate = self.get_exchange_rate(currency_id, rate_date)
        return amount * rate


class PriceService:
    """Service for price management"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_latest_price(self, asset_id: int, as_of_date: date = None) -> Optional[Price]:
        """Get the latest price for an asset"""
        if as_of_date is None:
            as_of_date = date.today()
        
        # Check if this is a cash asset
        asset = self.session.get(Asset, asset_id)
        if asset and asset.asset_type == "cash":
            # Cash assets always have a price of 1.0
            return Price(
                asset_id=asset_id,
                price_date=as_of_date,
                price=Decimal('1.0'),
                price_type='real_time',
                source='system'
            )
        
        price = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date <= as_of_date)
            .order_by(Price.price_date.desc())
        ).first()
        
        return price
    
    def get_price_history(self, asset_id: int, start_date: date, end_date: date) -> List[Price]:
        """Get price history for an asset"""
        prices = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date >= start_date)
            .where(Price.price_date <= end_date)
            .order_by(Price.price_date)
        ).all()
        
        return prices


class TransactionService:
    """Service for transaction processing"""
    
    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
    
    def get_cash_asset(self, currency_id: int) -> Optional[Asset]:
        """Get the cash asset for a given currency"""
        # Get currency code
        currency = self.session.get(Currency, currency_id)
        if not currency:
            return None
        
        # Find cash asset by symbol pattern
        cash_symbol = f"{currency.code}_CASH"
        cash_asset = self.session.exec(
            select(Asset)
            .where(Asset.symbol == cash_symbol)
            .where(Asset.asset_type == "cash")
        ).first()
        
        # Create cash asset if it doesn't exist
        if not cash_asset:
            cash_asset = Asset(
                symbol=cash_symbol,
                name=f"{currency.name} Cash",
                asset_type="cash",
                currency_id=currency_id,
                isin=f"CASH_{currency.code}"
            )
            self.session.add(cash_asset)
            
            # Add a price record for the cash asset (always 1.0)
            price = Price(
                asset_id=cash_asset.id,
                price_date=date.today(),
                price=Decimal('1.0'),
                price_type='real_time',
                source='system'
            )
            self.session.add(price)
            self.session.commit()
            self.session.refresh(cash_asset)
        
        return cash_asset
    
    def process_transaction(self, transaction: Transaction, portfolio_id: int = 1) -> Dict:
        """Process a transaction and update holdings"""
        result = {"success": False, "message": ""}
        
        try:
            if transaction.action in ['buy', 'sell']:
                self._process_trade_transaction(transaction, portfolio_id)
            elif transaction.action == 'dividends':
                self._process_dividend_transaction(transaction, portfolio_id)
            elif transaction.action == 'split':
                self._process_split_transaction(transaction, portfolio_id)
            elif transaction.action == 'interest':
                self._process_interest_transaction(transaction, portfolio_id)
            elif transaction.action in ['cash_in', 'cash_out']:
                self._process_cash_transaction(transaction, portfolio_id)
            
            result["success"] = True
            result["message"] = f"Transaction {transaction.action} processed successfully"
            
        except Exception as e:
            result["message"] = f"Error processing transaction: {str(e)}"
        
        return result
    
    def _process_trade_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process buy/sell transactions"""
        # Find or create holding for the asset
        holding = self.session.exec(
            select(Holding)
            .where(Holding.asset_id == transaction.asset_id)
            .where(Holding.portfolio_id == portfolio_id)
        ).first()
        
        if not holding:
            holding = Holding(
                portfolio_id=portfolio_id,
                asset_id=transaction.asset_id,
                quantity=Decimal('0'),
                average_cost=Decimal('0')
            )
            self.session.add(holding)
        
        # Get cash asset for the transaction currency
        cash_asset = self.get_cash_asset(transaction.currency_id)
        if not cash_asset:
            raise ValueError(f"Cash asset not found for currency {transaction.currency_id}")
        
        # Find or create cash holding
        cash_holding = self.session.exec(
            select(Holding)
            .where(Holding.asset_id == cash_asset.id)
            .where(Holding.portfolio_id == portfolio_id)
        ).first()
        
        if not cash_holding:
            cash_holding = Holding(
                portfolio_id=portfolio_id,
                asset_id=cash_asset.id,
                quantity=Decimal('0'),
                average_cost=Decimal('1.0')  # Cash always has a cost of 1.0
            )
            self.session.add(cash_holding)
        
        # Calculate total cost including fees
        total_cost = transaction.amount + (transaction.fees or Decimal('0'))
        
        if transaction.action == 'buy':
            # Check if we have enough cash
            if cash_holding.quantity < total_cost:
                raise ValueError("Insufficient cash balance for purchase")
            
            # Update asset holding
            existing_cost = holding.average_cost * holding.quantity
            holding.quantity += transaction.quantity
            holding.average_cost = (existing_cost + transaction.amount) / holding.quantity if holding.quantity > 0 else Decimal('0')
            
            # Reduce cash holding
            cash_holding.quantity -= total_cost
        
        elif transaction.action == 'sell':
            # Check if we have enough quantity to sell
            if holding.quantity < transaction.quantity:
                raise ValueError("Insufficient quantity to sell")
            
            # Reduce asset holding
            holding.quantity -= transaction.quantity
            if holding.quantity <= 0:
                self.session.delete(holding)
            
            # Calculate proceeds (amount - fees)
            proceeds = transaction.amount - (transaction.fees or Decimal('0'))
            
            # Increase cash holding
            cash_holding.quantity += proceeds
        
        self.session.commit()
    
    def _process_dividend_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process dividend transactions"""
        # Add to cash balance (implementation depends on cash management structure)
        pass
    
    def _process_split_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process stock split transactions"""
        holding = self.session.exec(
            select(Holding)
            .where(Holding.asset_id == transaction.asset_id)
            .where(Holding.portfolio_id == portfolio_id)
        ).first()
        
        if holding:
            split_ratio = transaction.quantity  # e.g., 2 for 2-for-1 split
            holding.quantity *= split_ratio
            holding.average_cost /= split_ratio
            self.session.commit()
    
    def _process_interest_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process interest transactions"""
        # Add to cash balance
        pass
    
    def _process_cash_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process cash in/out transactions"""
        # Get cash asset for the transaction currency
        cash_asset = self.get_cash_asset(transaction.currency_id)
        if not cash_asset:
            raise ValueError(f"Cash asset not found for currency {transaction.currency_id}")
        
        # Find or create holding for cash asset
        holding = self.session.exec(
            select(Holding)
            .where(Holding.asset_id == cash_asset.id)
            .where(Holding.portfolio_id == portfolio_id)
        ).first()
        
        if not holding:
            holding = Holding(
                portfolio_id=portfolio_id,
                asset_id=cash_asset.id,
                quantity=Decimal('0'),
                average_cost=Decimal('1.0')  # Cash always has a cost of 1.0
            )
            self.session.add(holding)
        
        # Update cash holding
        if transaction.action == 'cash_in':
            holding.quantity += transaction.quantity
        elif transaction.action == 'cash_out':
            holding.quantity -= transaction.quantity
            if holding.quantity < 0:
                raise ValueError("Insufficient cash balance")
        
        self.session.commit()


class PortfolioService:
    """Service for portfolio calculations and statistics"""
    
    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
        self.price_service = PriceService(session)
    
    def calculate_portfolio_value(self, portfolio_id: int, as_of_date: date = None) -> Dict:
        """Calculate total portfolio value"""
        if as_of_date is None:
            as_of_date = date.today()
        
        holdings = self.session.exec(
            select(Holding).where(Holding.portfolio_id == portfolio_id)
        ).all()
        
        if not holdings:
            return {
                "total_value": Decimal('0'),
                "holdings": [],
                "calculation_date": as_of_date
            }
        
        total_value = Decimal('0')
        holdings_value = []
        
        for holding in holdings:
            try:
                # Get latest price
                latest_price = self.price_service.get_latest_price(holding.asset_id, as_of_date)
                
                # If no price data available, use average cost as fallback
                if latest_price:
                    current_price = latest_price.price
                else:
                    current_price = holding.average_cost
                
                # Calculate market value
                market_value = holding.quantity * current_price
                
                # Convert to primary currency
                asset = self.session.get(Asset, holding.asset_id)
                if asset:
                    market_value_primary = self.currency_service.convert_to_primary_currency(
                        market_value, asset.currency_id, as_of_date
                    )
                else:
                    market_value_primary = market_value
                
                total_value += market_value_primary
                
                # Update holding
                holding.current_price = current_price
                holding.market_value = market_value_primary
                holding.unrealized_pnl = market_value_primary - (holding.average_cost * holding.quantity)
                holding.last_updated = datetime.now(timezone.utc)
                
                holdings_value.append({
                    "asset_id": holding.asset_id,
                    "symbol": asset.symbol if asset else "Unknown",
                    "name": asset.name if asset else "Unknown",
                    "quantity": holding.quantity,
                    "current_price": current_price,
                    "market_value": market_value_primary,
                    "unrealized_pnl": holding.unrealized_pnl
                })
                
            except Exception as e:
                print(f"Error calculating holding value for asset {holding.asset_id}: {e}")
                # Skip this holding if there's an error
                continue
        
        try:
            self.session.commit()
        except Exception as e:
            print(f"Error committing portfolio value updates: {e}")
            self.session.rollback()
        
        return {
            "total_value": total_value,
            "holdings": holdings_value,
            "calculation_date": as_of_date
        }
    
    def calculate_time_weighted_return(self, portfolio_id: int, start_date: date, end_date: date) -> Dict:
        """Calculate Time-Weighted Return (TWR) for portfolio"""
        try:
            transactions = self.session.exec(
                select(Transaction)
                .where(Transaction.trade_date >= start_date)
                .where(Transaction.trade_date <= end_date)
                .order_by(Transaction.trade_date)
            ).all()
            
            # Group transactions by date
            daily_transactions = defaultdict(list)
            for transaction in transactions:
                daily_transactions[transaction.trade_date].append(transaction)
            
            # Calculate daily returns
            portfolio_values = []
            cash_flows = []
            dates = []
            
            current_date = start_date
            while current_date <= end_date:
                try:
                    # Calculate portfolio value
                    portfolio_value = self.calculate_portfolio_value(portfolio_id, current_date)["total_value"]
                    
                    # Calculate cash flows for the day
                    daily_cash_flow = Decimal('0')
                    for transaction in daily_transactions.get(current_date, []):
                        if transaction.action in ['buy', 'cash_in']:
                            daily_cash_flow += transaction.amount
                        elif transaction.action in ['sell', 'cash_out']:
                            daily_cash_flow -= transaction.amount
                    
                    portfolio_values.append(float(portfolio_value))
                    cash_flows.append(float(daily_cash_flow))
                    dates.append(current_date)
                    
                except Exception as e:
                    print(f"Error calculating portfolio value for {current_date}: {e}")
                    # Skip this date if there's an error
                    pass
                
                current_date += timedelta(days=1)
            
            # Calculate TWR using Modified Dietz method
            if len(portfolio_values) < 2:
                return {
                    "twr": 0.0,
                    "period_return": 0.0,
                    "annualized_return": 0.0,
                    "beginning_value": 0.0,
                    "ending_value": 0.0,
                    "net_cash_flow": 0.0
                }
            
            beginning_value = portfolio_values[0]
            ending_value = portfolio_values[-1]
            net_cash_flow = sum(cash_flows)
            
            # Simplified TWR calculation
            if beginning_value > 0:
                period_return = ((ending_value - beginning_value - net_cash_flow) / beginning_value) * 100
            else:
                period_return = 0.0
            
            # Annualize return
            days = (end_date - start_date).days
            if days > 0 and period_return is not None:
                try:
                    annualized_return = (1 + period_return / 100) ** (365 / days) - 1
                    annualized_return *= 100
                    # Ensure it's a real number
                    if np.iscomplex(annualized_return) or np.isnan(annualized_return) or np.isinf(annualized_return):
                        annualized_return = 0.0
                    else:
                        annualized_return = float(np.real(annualized_return))
                except Exception as e:
                    print(f"Error calculating annualized return: {e}")
                    annualized_return = 0.0
            else:
                annualized_return = 0.0
            
            # Ensure all values are real numbers
            result = {
                "twr": float(period_return) if period_return is not None else 0.0,
                "period_return": float(period_return) if period_return is not None else 0.0,
                "annualized_return": annualized_return,
                "beginning_value": float(beginning_value),
                "ending_value": float(ending_value),
                "net_cash_flow": float(net_cash_flow)
            }
            
            # Final validation to ensure no complex numbers
            for key, value in result.items():
                if np.iscomplex(value) or np.isnan(value) or np.isinf(value):
                    result[key] = 0.0
                else:
                    result[key] = float(np.real(value))
            
            return result
            
        except Exception as e:
            print(f"Error calculating time-weighted return: {e}")
            return {
                "twr": 0.0,
                "period_return": 0.0,
                "annualized_return": 0.0,
                "beginning_value": 0.0,
                "ending_value": 0.0,
                "net_cash_flow": 0.0
            }
    
    def calculate_portfolio_statistics(self, portfolio_id: int, start_date: date, end_date: date) -> Dict:
        """Calculate comprehensive portfolio statistics"""
        try:
            twr_data = self.calculate_time_weighted_return(portfolio_id, start_date, end_date)
            
            # Get daily returns for volatility calculation
            daily_returns = []
            current_date = start_date
            prev_value = None
            
            while current_date <= end_date:
                try:
                    value = self.calculate_portfolio_value(portfolio_id, current_date)["total_value"]
                    if prev_value is not None and prev_value > 0:
                        daily_return = (float(value) - float(prev_value)) / float(prev_value)
                        # Only add valid returns (not NaN, not infinite)
                        if not (np.isnan(daily_return) or np.isinf(daily_return)):
                            daily_returns.append(daily_return)
                    prev_value = value
                except Exception as e:
                    print(f"Error calculating portfolio value for {current_date}: {e}")
                    # Skip this date if there's an error
                    pass
                
                current_date += timedelta(days=1)
            
            # Calculate statistics with proper validation
            if len(daily_returns) > 1:
                # Convert to numpy array and ensure it's real
                returns_array = np.array(daily_returns, dtype=float)
                
                # Calculate volatility safely
                try:
                    volatility = np.std(returns_array, ddof=1) * np.sqrt(252)  # Annualized volatility
                    # Ensure volatility is real and positive
                    if np.iscomplex(volatility) or np.isnan(volatility) or np.isinf(volatility):
                        volatility = 0.0
                    else:
                        volatility = float(np.real(volatility))
                except Exception as e:
                    print(f"Error calculating volatility: {e}")
                    volatility = 0.0
                
                # Calculate max drawdown safely
                try:
                    max_drawdown = self._calculate_max_drawdown(daily_returns)
                    if np.iscomplex(max_drawdown) or np.isnan(max_drawdown) or np.isinf(max_drawdown):
                        max_drawdown = 0.0
                    else:
                        max_drawdown = float(np.real(max_drawdown))
                except Exception as e:
                    print(f"Error calculating max drawdown: {e}")
                    max_drawdown = 0.0
                
                # Calculate Sharpe ratio safely
                try:
                    annualized_return = twr_data.get("annualized_return", 0)
                    if volatility > 0 and not np.isnan(annualized_return) and not np.isinf(annualized_return):
                        sharpe_ratio = (annualized_return / 100) / volatility
                        if np.iscomplex(sharpe_ratio) or np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
                            sharpe_ratio = 0.0
                        else:
                            sharpe_ratio = float(np.real(sharpe_ratio))
                    else:
                        sharpe_ratio = 0.0
                except Exception as e:
                    print(f"Error calculating Sharpe ratio: {e}")
                    sharpe_ratio = 0.0
            else:
                volatility = 0.0
                max_drawdown = 0.0
                sharpe_ratio = 0.0
            
            # Ensure all return values are real numbers
            result = {
                "time_weighted_return": float(twr_data.get("twr", 0)),
                "annualized_return": float(twr_data.get("annualized_return", 0)),
                "volatility": volatility * 100,
                "max_drawdown": max_drawdown * 100,
                "sharpe_ratio": sharpe_ratio,
                "beginning_value": float(twr_data.get("beginning_value", 0)),
                "ending_value": float(twr_data.get("ending_value", 0)),
                "period_days": (end_date - start_date).days
            }
            
            # Final validation to ensure no complex numbers
            for key, value in result.items():
                if np.iscomplex(value) or np.isnan(value) or np.isinf(value):
                    result[key] = 0.0
                else:
                    result[key] = float(np.real(value))
            
            return result
            
        except Exception as e:
            print(f"Error calculating portfolio statistics: {e}")
            # Return default values if calculation fails
            return {
                "time_weighted_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "beginning_value": 0.0,
                "ending_value": 0.0,
                "period_days": (end_date - start_date).days
            }
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not returns or len(returns) < 2:
            return 0.0
        
        try:
            # Convert to numpy array and ensure it's real
            returns_array = np.array(returns, dtype=float)
            
            # Remove any NaN or infinite values
            returns_array = returns_array[~(np.isnan(returns_array) | np.isinf(returns_array))]
            
            if len(returns_array) < 2:
                return 0.0
            
            # Calculate cumulative returns
            cumulative = np.cumprod(1 + returns_array)
            
            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative)
            
            # Calculate drawdown
            drawdown = (cumulative - running_max) / running_max
            
            # Get maximum drawdown
            max_dd = np.min(drawdown)
            
            # Ensure result is real and valid
            if np.iscomplex(max_dd) or np.isnan(max_dd) or np.isinf(max_dd):
                return 0.0
            else:
                return float(np.real(max_dd))
                
        except Exception as e:
            print(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def get_asset_allocation(self, portfolio_id: int) -> Dict:
        """Get asset allocation by type and sector"""
        try:
            holdings = self.session.exec(
                select(Holding).where(Holding.portfolio_id == portfolio_id)
            ).all()
            
            if not holdings:
                return {
                    "by_type": {},
                    "by_sector": {},
                    "total_value": 0
                }
            
            allocation_by_type = defaultdict(Decimal)
            allocation_by_sector = defaultdict(Decimal)
            total_value = Decimal('0')
            
            for holding in holdings:
                try:
                    if holding.market_value and holding.market_value > 0:
                        asset = self.session.get(Asset, holding.asset_id)
                        if asset:
                            allocation_by_type[asset.asset_type] += holding.market_value
                            total_value += holding.market_value
                            
                            # Get sector from asset metadata
                            sector_meta = self.session.exec(
                                select(AssetMetadata)
                                .where(AssetMetadata.asset_id == asset.id)
                                .where(AssetMetadata.attribute_name == "sector")
                            ).first()
                            
                            if sector_meta:
                                allocation_by_sector[sector_meta.attribute_value] += holding.market_value
                            else:
                                allocation_by_sector["Unknown"] += holding.market_value
                except Exception as e:
                    print(f"Error processing holding {holding.id}: {e}")
                    continue
            
            # Convert to percentages
            type_percentages = {}
            sector_percentages = {}
            
            if total_value > 0:
                type_percentages = {
                    asset_type: float(value / total_value * 100)
                    for asset_type, value in allocation_by_type.items()
                }
                
                sector_percentages = {
                    sector: float(value / total_value * 100)
                    for sector, value in allocation_by_sector.items()
                }
            
            return {
                "by_type": type_percentages,
                "by_sector": sector_percentages,
                "total_value": float(total_value)
            }
            
        except Exception as e:
            print(f"Error calculating asset allocation: {e}")
            return {
                "by_type": {},
                "by_sector": {},
                "total_value": 0
            } 