import numpy as np
import csv
from sqlmodel import Session, select
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from collections import defaultdict

from backend.models import (
    Currency,
    ExchangeRate,
    Asset,
    AssetMetadata,
    Transaction,
    Price,
    Position,
)
from backend import logger, f_logger



class CurrencyService:
    """Service for currency conversion and management"""

    def __init__(self, session: Session):
        self.session = session

    def get_primary_currency(self) -> Currency:
        """Get the primary currency"""
        primary = self.session.exec(
            select(Currency).where(Currency.is_primary == True)
        ).first()
        if not primary:
            # Create CNY as default primary currency
            primary = Currency(
                code="CNY", name="Chinese Yuan", symbol="¥", is_primary=True
            )
            self.session.add(primary)
            self.session.commit()
            self.session.refresh(primary)
        return primary

    def get_exchange_rate(self, currency_id: int, rate_date: date) -> Decimal:
        """Get exchange rate for a currency on a specific date"""
        if currency_id == self.get_primary_currency().id:
            return Decimal("1.0")

        # Get the most recent exchange rate before or on the date
        rate = self.session.exec(
            select(ExchangeRate)
            .where(ExchangeRate.currency_id == currency_id)
            .where(ExchangeRate.rate_date <= rate_date)
            .order_by(ExchangeRate.rate_date.desc())
        ).first()

        return rate.rate_to_primary if rate else Decimal("1.0")

    def convert_to_primary_currency(
        self, amount: Decimal, currency_id: int, rate_date: date
    ) -> Decimal:
        """Convert amount to primary currency"""
        rate = self.get_exchange_rate(currency_id, rate_date)
        return amount * rate


class PriceService:
    """Service for price management"""

    def __init__(self, session: Session):
        self.session = session

    def get_latest_price(
        self, asset_id: int, as_of_date: date = None
    ) -> Price | None:
        """Get the latest price for an asset"""
        if as_of_date is None:
            as_of_date = date.today()

        # Check if this is a cash asset
        asset = self.session.get(Asset, asset_id)
        if asset and asset.type == "cash":
            # Cash assets always have a price of 1.0
            return Price(
                asset_id=asset_id,
                price_date=as_of_date,
                price=Decimal("1.0"),
                price_type="real_time",
                source="system",
            )

        price = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date <= as_of_date)
            .order_by(Price.price_date.desc())
        ).first()

        return price

    def get_price_history(
        self, asset_id: int, start_date: date, end_date: date
    ) -> list[Price]:
        """Get price history for an asset"""
        prices = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date >= start_date)
            .where(Price.price_date <= end_date)
            .order_by(Price.price_date)
        ).all()

        return prices


class PortfolioService:
    """Service for portfolio calculations and statistics"""

    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
        self.price_service = PriceService(session)

    def calculate_portfolio_value(
        self, portfolio_id: int, as_of_date: date = None
    ) -> dict:
        """Calculate total portfolio value and store positions on the as_of_date"""
        if as_of_date is None:
            as_of_date = date.today()

        # Try to get positions for the exact date
        positions = self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == as_of_date)
        ).all()

        # If no positions found for the exact date, calculate positions up to the date
        if not positions:
            position_service = PositionService(self.session)
            positions_dict = position_service.update_positions_for_period(
                portfolio_id=portfolio_id,
                start_date=date(1982, 1, 1),
                end_date=as_of_date,
                save_to_db=True,
            )
            positions = list(positions_dict.values())

        if not positions:
            return {
                "total_value": Decimal("0"),
                "positions": [],
                "calculation_date": as_of_date,
            }

        total_value = Decimal("0")
        positions_value = []

        for position in positions:
            # Convert to primary currency
            asset = self.session.get(Asset, position.asset_id)
            if asset:
                market_value_primary = (
                    self.currency_service.convert_to_primary_currency(
                        position.market_value, asset.currency_id, as_of_date
                    )
                )
                total_pnl_primary = (
                    self.currency_service.convert_to_primary_currency(
                        position.total_pnl, asset.currency_id, as_of_date
                    )
                )
            else:
                raise ValueError(f"Asset {position.asset_id} not found")

            total_value += market_value_primary

            positions_value.append(
                {
                    "asset_id": position.asset_id,
                    "symbol": asset.symbol if asset else "Unknown",
                    "name": asset.name if asset else "Unknown",
                    "quantity": position.quantity,
                    "current_price": position.current_price,
                    "market_value": position.market_value,
                    "market_value_primary": market_value_primary,
                    "total_pnl": position.total_pnl,
                    "total_pnl_primary": total_pnl_primary,
                }
            )

        return {
            "total_value": total_value,
            "positions": positions_value,
            "calculation_date": as_of_date,
        }

    def _write_twr_debug_csv(self, data_rows: list[list[str]], overwrite: bool = True):
        """Write TWR calculation data to CSV file"""
        debug_csv_path = Path(__file__).parent.parent / "tests" / "output" / "debug_log.csv"
        mode = 'w' if overwrite else 'a'
        with open(debug_csv_path, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data_rows)

    def twr(
        self, portfolio_id: int, start_date: date, end_date: date
    ) -> dict:
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

            # Initialize variables for TWR calculation
            daily_returns = [] 
            nav_history = []  
            shares_history = []  
            dates_history = []  

            # External cash flows are added to the portfolio at the end of each day.
            # The first day is only for initialization of navs and shares.
            v_prev = self.calculate_portfolio_value(portfolio_id, start_date)["total_value"] 
            nav_prev = Decimal("1.0")  # 初始为1
            shares_prev = v_prev / nav_prev  # 初始化份额
            nav_history.append(float(nav_prev))
            shares_history.append(float(shares_prev))
            dates_history.append(start_date)
            # Start calculation from the second day
            current_date = start_date + timedelta(days=1)
            
            # Print to CSV for debugging (Overriding existing debug csv file)
            self._write_twr_debug_csv([
                ["date", "nav_today", "nav_prev", "shares_today", "shares_prev", "v_today", "v_prev", "r"],
                [start_date, f"{nav_prev:.6f}", f"{nav_prev:.6f}", f"{shares_prev:.2f}", f"{shares_prev:.2f}", f"{v_prev:.2f}", f"{v_prev:.2f}", "0"]
            ], overwrite=True)

            while current_date <= end_date:
                # Step 1. Prepare data for today
                v_today = self.calculate_portfolio_value(portfolio_id, current_date)["total_value"]

                # Step 2. Calculate external net cash flow in primary currency
                delta_cf = Decimal("0")
                for transaction in daily_transactions.get(current_date, []):
                    if transaction.action in ["cash_in"]:
                        amount = self.currency_service.convert_to_primary_currency(
                            transaction.amount, transaction.currency_id, current_date
                        )
                        delta_cf += amount
                    elif transaction.action in ["cash_out"]:
                        amount = self.currency_service.convert_to_primary_currency(
                            transaction.amount, transaction.currency_id, current_date
                        )
                        delta_cf -= amount
                
                # Step 3. Calculate the nav for current day by 2 methods

                # The first method: nav_today = (v_today - delta_cf) / shares_prev
                if shares_prev > 0:   # Handle division by zero for shares calculation
                    nav_today = (v_today - delta_cf) / shares_prev
                else:
                    nav_today = nav_prev

                # The second method: nav_today = nav_prev * (1 + r)
                if v_prev > 0:  # Handle division by zero for shares calculation
                    r = (v_today - delta_cf) / v_prev - 1
                else:
                    r = Decimal("0")
                nav_ref_today = nav_prev * (1 + r)
                
                # Nav calculated by 2 methods should be the same
                nav_diff = nav_today - nav_ref_today
                if abs(nav_diff) > 0.0001:
                    raise ValueError(f"NAV calculation error on {current_date}. nav_ref:{nav_ref_today}, nav:{nav_today}, diff:{nav_diff}")

                # Step 4. Modify shares for today
                delta_shares = delta_cf / nav_today
                shares_today = shares_prev + delta_shares
                
                # Store daily data
                daily_returns.append(float(r))
                shares_history.append(float(shares_today))
                nav_history.append(float(nav_today))
                dates_history.append(current_date)
                
                # Append debug data to existing CSV file
                self._write_twr_debug_csv([
                    [current_date, f"{nav_today:.6f}", f"{nav_prev:.6f}", f"{shares_today:.2f}", f"{shares_prev:.2f}", f"{v_today:.2f}", f"{v_prev:.2f}", f"{r:.4f}"]
                ], overwrite=False)
                
                # Step 5. Update data for next day
                v_prev = v_today
                shares_prev = shares_today
                nav_prev = nav_today
                current_date += timedelta(days=1)
            
            # Calculate cumulative TWR
            if len(daily_returns) > 0:
                # TWR = (1 + r1) * (1 + r2) * ... * (1 + rn) - 1
                cumulative_return = 1.0
                for r in daily_returns:
                    cumulative_return *= (1 + r)
                
                twr = cumulative_return - 1
                period_return = twr
            else:
                twr = 0.0
                period_return = 0.0
            
            # Annualize return
            days = (end_date - start_date).days
            if days > 0 and len(daily_returns) > 0:
                annualized_return = (1 + twr) ** (365 / days) - 1
            else:
                annualized_return = 0.0
            
            # Calculate beginning and ending values
            beginning_value = float(nav_history[0]) if nav_history else 0.0
            ending_value = float(nav_history[-1]) if nav_history else 0.0
            result = {
                "twr": float(twr),
                "period_return": float(period_return),
                "annualized_return": annualized_return,
                "beginning_value": beginning_value,
                "ending_value": ending_value,
                "daily_returns": daily_returns,
                "nav_history": nav_history,
                "shares_history": shares_history,
                "dates": [dates_history],
            }
            
            return result
            
        except Exception as e:
            logger.exception("Error in PortfolioService.twr()")

            return {
                "twr": 0.0,
                "period_return": 0.0,
                "annualized_return": 0.0,
                "beginning_value": 0.0,
                "ending_value": 0.0,
                "daily_returns": [],
                "nav_history": [],
                "shares_history": [],
                "dates": [],
            }

    def calculate_portfolio_statistics(
        self, portfolio_id: int, start_date: date, end_date: date
    ) -> dict:
        """Calculate comprehensive portfolio statistics"""
        try:
            twr_data = self.twr(
                portfolio_id, start_date, end_date
            )

            # Get daily returns for volatility calculation
            daily_returns = []
            current_date = start_date
            prev_value = None

            while current_date <= end_date:
                try:
                    value = self.calculate_portfolio_value(portfolio_id, current_date)[
                        "total_value"
                    ]
                    if prev_value is not None and prev_value > 0:
                        daily_return = (float(value) - float(prev_value)) / float(
                            prev_value
                        )
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
                    volatility = np.std(returns_array, ddof=1) * np.sqrt(
                        252
                    )  # Annualized volatility
                    # Ensure volatility is real and positive
                    if (
                        np.iscomplex(volatility)
                        or np.isnan(volatility)
                        or np.isinf(volatility)
                    ):
                        volatility = 0.0
                    else:
                        volatility = float(np.real(volatility))
                except Exception as e:
                    print(f"Error calculating volatility: {e}")
                    volatility = 0.0

                # Calculate max drawdown safely
                try:
                    max_drawdown = self._calculate_max_drawdown(daily_returns)
                    if (
                        np.iscomplex(max_drawdown)
                        or np.isnan(max_drawdown)
                        or np.isinf(max_drawdown)
                    ):
                        max_drawdown = 0.0
                    else:
                        max_drawdown = float(np.real(max_drawdown))
                except Exception as e:
                    print(f"Error calculating max drawdown: {e}")
                    max_drawdown = 0.0

                # Calculate Sharpe ratio safely
                try:
                    annualized_return = twr_data.get("annualized_return", 0)
                    if (
                        volatility > 0
                        and not np.isnan(annualized_return)
                        and not np.isinf(annualized_return)
                    ):
                        sharpe_ratio = (annualized_return / 100) / volatility
                        if (
                            np.iscomplex(sharpe_ratio)
                            or np.isnan(sharpe_ratio)
                            or np.isinf(sharpe_ratio)
                        ):
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
                "period_days": (end_date - start_date).days,
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
                "period_days": (end_date - start_date).days,
            }

    def _calculate_max_drawdown(self, returns: list[float]) -> float:
        """Calculate maximum drawdown"""
        if not returns or len(returns) < 2:
            return 0.0

        try:
            # Convert to numpy array and ensure it's real
            returns_array = np.array(returns, dtype=float)

            # Remove any NaN or infinite values
            returns_array = returns_array[
                ~(np.isnan(returns_array) | np.isinf(returns_array))
            ]

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

    def get_asset_allocation(self, portfolio_id: int, as_of_date: date = None, by: str = 'type') -> dict:
        """Get asset allocation by type or sector based on 'by' parameter"""
        if as_of_date is None:
            as_of_date = date.today()

        # Validate 'by' parameter
        if by not in ['type', 'sector']:
            raise ValueError('Invalid "by" parameter. Must be "type" or "sector".')

        try:
            positions = self.session.exec(
                select(Position)
                .where(Position.portfolio_id == portfolio_id)
                .where(Position.position_date == as_of_date)
            ).all()

            if not positions:
                return {by: {}, "total_value": 0}

            allocation = defaultdict(Decimal)
            total_value = Decimal("0")

            for position in positions:
                if position.market_value and position.market_value > 0:
                    asset = self.session.get(Asset, position.asset_id)
                    if asset:
                        # Convert market value to primary currency
                        market_value_primary = (
                            self.currency_service.convert_to_primary_currency(
                                position.market_value, asset.currency_id, as_of_date
                            )
                        )
                        total_value += market_value_primary
                        
                        if by == 'type':
                            allocation[asset.type] += market_value_primary
                        else:  # by 'sector'
                            # Get sector from asset metadata
                            sector_meta = self.session.exec(
                                select(AssetMetadata)
                                .where(AssetMetadata.asset_id == asset.id)
                                .where(AssetMetadata.attribute_name == "sector")
                            ).first()

                            if sector_meta:
                                allocation[sector_meta.attribute_value] += market_value_primary
                            else:
                                allocation["Unknown"] += market_value_primary
            # Convert to percentages
            percentages = {}
            if total_value > 0:
                percentages = {
                    key: float(value / total_value)
                    for key, value in allocation.items()
                }
            return {
                "allocation_pct": percentages,
                "total_value": float(total_value)
            }

        except Exception as e:
            print(f"Error calculating asset allocation: {e}")
            return {"allocation_pct": {}, "total_value": 0}


class PositionService:
    """Service for position calculations and management"""

    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
        self.price_service = PriceService(session)

    def get_initial_positions(
        self, portfolio_id: int, on_date: date
    ) -> list[Position]:
        """Get initial positions from database for a portfolio on a specific date"""
        positions = self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == on_date)
        ).all()

        return positions



    def _get_cash_asset(self, currency_id: int) -> Asset | None:
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
            .where(Asset.type == "cash")
        ).first()

        return cash_asset

    def save_positions(self, positions: dict[int, Position]):
        """Save calculated positions to database"""
        for position in positions.values():
            # Check if position already exists for this date
            existing_position = self.session.exec(
                select(Position)
                .where(Position.portfolio_id == position.portfolio_id)
                .where(Position.asset_id == position.asset_id)
                .where(Position.position_date == position.position_date)
            ).first()

            if existing_position:
                # Update existing position
                existing_position.quantity = position.quantity
                existing_position.average_cost = position.average_cost
                existing_position.current_price = position.current_price
                existing_position.market_value = position.market_value
                existing_position.total_pnl = position.total_pnl
            else:
                # Add new position
                self.session.add(position)

        self.session.commit()

    def get_latest_positions(self, portfolio_id: int) -> list[Position]:
        """Get the latest positions for a portfolio"""
        # Get all positions for the portfolio
        positions = self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .order_by(Position.position_date.desc())
        ).all()

        # Get the latest position for each asset
        latest_positions = {}
        for position in positions:
            if position.asset_id not in latest_positions:
                latest_positions[position.asset_id] = position

        return list(latest_positions.values())

    def update_positions_for_period(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        save_to_db: bool = True,
    ) -> dict[int, Position]:
        """
        Calculate positions generated by transactions during a given period.
        1. It gets the initial positions from the day before start_date and then 
        processes all transactions from start_date to end_date.
           If the initial positions don't exist, it starts with empty positions.
        2. Only the final positions at the end_date are saved and returned.

        Args:
            portfolio_id: the portfolio ID
            start_date: including transactions on start_date
            end_date: including transactions on end_date
            save_to_db: whether to save the calculated positions to the database
        Returns:
            A dictionary of asset_id to Position objects, representing the final positions at the end_date.
        """
        # Get all transactions between start_date and end_date for the portfolio
        transactions = self.session.exec(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .where(Transaction.trade_date >= start_date)
            .where(Transaction.trade_date <= end_date)
            .order_by(Transaction.trade_date)
        ).all()

        # Calculate positions for the period based on initial positions and transactions
        # The returned positions are the final positions at the end_date.
        
        # Get initial positions the day before start_date
        initial_positions = self.get_initial_positions(portfolio_id, start_date - timedelta(days=1))
        # Initially start with empty positions if no initial positions
        final_positions = {}
        init_positions_dict = {}
        if initial_positions: 
            for position in initial_positions:
                final_positions[position.asset_id] = Position(
                    portfolio_id=portfolio_id,
                    asset_id=position.asset_id,
                    position_date=end_date,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    current_price=position.current_price,
                    market_value=position.market_value or Decimal("0"),
                    total_pnl=position.total_pnl or Decimal("0"),
                )
                init_positions_dict[position.asset_id] = position

        # Track cash flows for total P&L calculation
        cash_flows = defaultdict(
            lambda: {
                "cash_paid_on_bought": Decimal("0"),
                "cash_received_on_sale": Decimal("0"),
                "dividends_received": Decimal("0"),
            }
        )

        # Process transactions
        for transaction in transactions:
            asset_id = transaction.asset_id

            # Initialize position if it doesn't exist
            if asset_id not in final_positions:
                final_positions[asset_id] = Position(
                    portfolio_id=portfolio_id,
                    asset_id=asset_id,
                    position_date=end_date,
                    quantity=Decimal("0"),
                    average_cost=Decimal("0"),
                    current_price=Decimal("0"),
                    market_value=Decimal("0"),
                    total_pnl=Decimal("0"),
                )

            position = final_positions[asset_id]

            # Get cash asset for the transaction currency
            cash_asset = self._get_cash_asset(transaction.currency_id)
            if not cash_asset:
                raise ValueError(
                    f"Cash asset not found for currency {transaction.currency_id}"
                )

            # Initialize cash position if it doesn't exist
            if cash_asset.id not in final_positions:
                final_positions[cash_asset.id] = Position(
                    portfolio_id=portfolio_id,
                    asset_id=cash_asset.id,
                    position_date=end_date,
                    quantity=Decimal("0"),
                    average_cost=Decimal("1.0"),  # Cash always has cost of 1.0
                    current_price=Decimal("1.0"),
                    market_value=Decimal("0"),
                    total_pnl=Decimal("0"),
                )
            
            cash_position = final_positions[cash_asset.id]

            if transaction.action == "buy":
                # Update average cost and quantity for the asset
                total_cost = position.average_cost * position.quantity
                position.quantity += transaction.quantity
                position.average_cost = (
                    total_cost + transaction.amount + (transaction.fees or Decimal("0"))
                ) / position.quantity

                # Track cash paid for P&L calculation
                cash_flows[asset_id]["cash_paid_on_bought"] += transaction.amount + (
                    transaction.fees or Decimal("0")
                )

                # Reduce cash position
                cash_position.quantity -= transaction.amount + (
                    transaction.fees or Decimal("0")
                )

            elif transaction.action == "sell":
                # Reduce quantity for the asset
                position.quantity -= transaction.quantity
                if position.quantity < 0:
                    position.quantity = Decimal("0")

                # Track cash received for P&L calculation
                cash_flows[asset_id]["cash_received_on_sale"] += transaction.amount - (
                    transaction.fees or Decimal("0")
                )
                # Increase cash position
                cash_position.quantity += transaction.amount - (
                    transaction.fees or Decimal("0")
                )

            elif transaction.action == "dividends":
                # Track dividends received for P&L calculation
                cash_flows[asset_id]["dividends_received"] += transaction.amount - (
                    transaction.fees or Decimal("0")
                )

                # Add dividends to cash position
                cash_position.quantity += transaction.amount - (
                    transaction.fees or Decimal("0")
                )

            elif transaction.action == "split":
                # Handle stock splits
                split_ratio = transaction.quantity
                position.quantity *= split_ratio
                if position.average_cost > 0:
                    position.average_cost /= split_ratio

            elif transaction.action == "cash_in":
                # Add cash to position
                cash_position.quantity += transaction.quantity
                cash_position.average_cost = Decimal("1.0")  # Cash always has cost of 1.0

            elif transaction.action == "cash_out":
                # Remove cash from position
                cash_position.quantity -= transaction.quantity
                cash_position.average_cost = Decimal("1.0")  # Cash always has cost of 1.0

        # Calculate current prices and market values
        for asset_id, position in final_positions.items():
            # Get current price
            latest_price = self.price_service.get_latest_price(asset_id, end_date)
            if latest_price:
                position.current_price = latest_price.price
            elif position.current_price is None:
                position.current_price = position.average_cost

            # Calculate market value
            position.market_value = position.quantity * position.current_price

            # Calculate total P&L
            asset = self.session.get(Asset, asset_id)
            # If the asset is cash, set total_pnl to 0
            if asset.type == "cash":  
                position.total_pnl = Decimal("0")
            else:
            # Profit_1 = Profit_0 + MarketValue_1 - MarketValue_0 + change of cashflow
                if asset_id in init_positions_dict:
                    profit_0 = init_positions_dict[asset_id].total_pnl
                    market_value_0 = init_positions_dict[asset_id].market_value
                else:
                    profit_0 = Decimal("0")
                    market_value_0 = Decimal("0")
                position.total_pnl = (
                    profit_0
                    + position.market_value
                    - market_value_0
                    + cash_flows[asset_id]["cash_received_on_sale"]
                    + cash_flows[asset_id]["dividends_received"]
                    - cash_flows[asset_id]["cash_paid_on_bought"]
                )

        # Save to database if requested
        if save_to_db:
            self.save_positions(final_positions)

        return final_positions
