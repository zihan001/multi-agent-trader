"""
Binance Paper Trading service using Binance Spot Testnet API.

This service provides:
- Real Binance Testnet API integration (https://testnet.binance.vision)
- Authenticated order placement (Market, Limit, Stop-Loss, etc.)
- Real order execution and fills from Binance's paper trading system
- Account balance and position tracking via Binance API
- Fallback to local simulation if testnet disabled

Get testnet API keys: https://testnet.binance.vision/
- Sign in with GitHub
- Generate API Key & Secret
- Configure in .env file

Note: Binance Testnet uses fake money but real API behavior.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Literal
from sqlalchemy.orm import Session
from sqlalchemy import desc
from enum import Enum
import logging
import httpx
import hmac
import hashlib
import time

from app.models.database import PaperOrder, Trade, Position, PortfolioSnapshot
from app.services.binance import BinanceService
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class BinanceTestnetClient:
    """
    Client for Binance Spot Testnet API with authenticated requests.
    
    Handles signed API requests for trading operations.
    """
    
    def __init__(self):
        """Initialize Binance testnet client."""
        self.base_url = settings.binance_testnet_base_url
        self.api_key = settings.binance_testnet_api_key
        self.api_secret = settings.binance_testnet_api_secret
        
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Binance Testnet API credentials not configured. "
                "Get keys from https://testnet.binance.vision/ and set "
                "BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET"
            )
        
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a signed API request."""
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = 5000
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = self._generate_signature(query_string)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}{endpoint}"
        
        if method == 'GET':
            response = await self.client.get(url, params=params, headers=headers)
        elif method == 'POST':
            response = await self.client.post(url, params=params, headers=headers)
        elif method == 'DELETE':
            response = await self.client.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    async def get_account(self) -> Dict[str, Any]:
        """Get account information (balances, permissions)."""
        return await self._signed_request('GET', '/api/v3/account')
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new order on Binance Testnet.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            order_type: 'MARKET', 'LIMIT', 'STOP_LOSS_LIMIT', etc.
            **kwargs: Additional order parameters (quantity, price, etc.)
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            **kwargs
        }
        return await self._signed_request('POST', '/api/v3/order', params)
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an active order."""
        params = {'symbol': symbol, 'orderId': order_id}
        return await self._signed_request('DELETE', '/api/v3/order', params)
    
    async def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order details."""
        params = {'symbol': symbol, 'orderId': order_id}
        return await self._signed_request('GET', '/api/v3/order', params)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        params = {'symbol': symbol} if symbol else {}
        return await self._signed_request('GET', '/api/v3/openOrders', params)
    
    async def get_all_orders(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get all orders (filled, cancelled, etc.)."""
        params = {'symbol': symbol, 'limit': limit}
        return await self._signed_request('GET', '/api/v3/allOrders', params)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class PaperTradingService:
    """
    Binance Paper Trading service using Testnet API or local simulation.
    
    Modes:
    1. Testnet Mode (settings.paper_trading_mode == "testnet"):
       - Uses real Binance Testnet API
       - Actual order placement and fills
       - Real account balances and positions
       - Requires testnet API credentials
    
    2. Simulation Mode (settings.paper_trading_mode == "simulation"):
       - Local order simulation
       - Fills based on real market prices
       - Managed in PostgreSQL database
       - No API credentials required
    """
    
    def __init__(self, db: Session, run_id: str = "paper_live"):
        """
        Initialize paper trading service.
        
        Args:
            db: Database session
            run_id: Identifier for this trading session
        """
        self.db = db
        self.run_id = run_id
        self.mode = settings.paper_trading_mode
        
        # Initialize appropriate client (lazy initialization for testnet)
        self.testnet_client = None
        
        if self.mode == "testnet":
            try:
                self.testnet_client = BinanceTestnetClient()
                logger.info("Paper trading using Binance Testnet API")
            except ValueError as e:
                logger.error(f"Failed to initialize testnet client: {e}")
                raise
        else:
            logger.info("Paper trading using local simulation")
        
        self.binance = BinanceService()  # For market data
        
        # Simulation parameters (only used in simulation mode)
        self.slippage_pct = 0.001  # 0.1% slippage for market orders
        self.fee_rate = 0.001  # 0.1% trading fee
    
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC"  # Good Till Cancel
    ) -> PaperOrder:
        """
        Create a new paper trading order.
        
        Testnet Mode: Places real order on Binance Testnet
        Simulation Mode: Creates order in database and simulates fills
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: BUY or SELL
            order_type: MARKET, LIMIT, STOP_LOSS, or TAKE_PROFIT
            quantity: Order quantity
            price: Limit price (required for LIMIT orders)
            stop_price: Stop price (required for STOP_LOSS/TAKE_PROFIT)
            time_in_force: Order time in force (GTC, IOC, FOK)
            
        Returns:
            Created PaperOrder object
            
        Raises:
            ValueError: If order validation fails
        """
        # Validate order parameters
        self._validate_order(order_type, price, stop_price, quantity)
        
        symbol = symbol.upper()
        
        if self.mode == "testnet":
            # Use Binance Testnet API
            return await self._create_testnet_order(
                symbol, side, order_type, quantity, price, stop_price, time_in_force
            )
        else:
            # Use local simulation
            return await self._create_simulated_order(
                symbol, side, order_type, quantity, price, stop_price, time_in_force
            )
    
    async def _create_testnet_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float],
        stop_price: Optional[float],
        time_in_force: str
    ) -> PaperOrder:
        """Create order using Binance Testnet API."""
        # Map our order types to Binance API types
        binance_order_type = order_type.value
        
        order_params = {
            'quantity': quantity,
        }
        
        if order_type == OrderType.LIMIT:
            order_params['price'] = price
            order_params['timeInForce'] = time_in_force
        elif order_type == OrderType.STOP_LOSS:
            binance_order_type = 'STOP_LOSS_LIMIT'
            order_params['price'] = stop_price
            order_params['stopPrice'] = stop_price
            order_params['timeInForce'] = time_in_force
        elif order_type == OrderType.TAKE_PROFIT:
            binance_order_type = 'TAKE_PROFIT_LIMIT'
            order_params['price'] = stop_price
            order_params['stopPrice'] = stop_price
            order_params['timeInForce'] = time_in_force
        
        # Place order on Binance Testnet
        testnet_order = await self.testnet_client.create_order(
            symbol=symbol,
            side=side.value,
            order_type=binance_order_type,
            **order_params
        )
        
        # Store order in database
        order = PaperOrder(
            symbol=symbol,
            side=side.value,
            order_type=order_type.value,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            filled_quantity=float(testnet_order.get('executedQty', 0)),
            avg_fill_price=float(testnet_order.get('price', 0)) if testnet_order.get('price') else None,
            status=self._map_binance_status(testnet_order['status']),
            time_in_force=time_in_force,
            run_id=self.run_id,
            created_at=datetime.utcnow(),
            binance_order_id=testnet_order['orderId']  # Store Binance order ID
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(
            f"Created Testnet {order_type.value} {side.value} order for {quantity} {symbol} "
            f"(Binance Order ID: {testnet_order['orderId']})"
        )
        
        return order
    
    async def _create_simulated_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float],
        stop_price: Optional[float],
        time_in_force: str
    ) -> PaperOrder:
        """Create order using local simulation."""
        # Get current market price
        current_price = await self._get_current_price(symbol)
        
        # Validate sufficient balance
        self._validate_balance(symbol, side, quantity, current_price, price)
        
        # Create order
        order = PaperOrder(
            symbol=symbol,
            side=side.value,
            order_type=order_type.value,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            filled_quantity=0.0,
            status=OrderStatus.PENDING.value,
            time_in_force=time_in_force,
            run_id=self.run_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"Created simulated {order_type.value} {side.value} order for {quantity} {symbol}")
        
        # Try to fill market orders immediately
        if order_type == OrderType.MARKET:
            await self._fill_market_order(order, current_price)
        
        return order
    
    async def cancel_order(self, order_id: int) -> PaperOrder:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Updated PaperOrder object
            
        Raises:
            ValueError: If order not found or cannot be cancelled
        """
        order = self.db.query(PaperOrder).filter(
            PaperOrder.id == order_id,
            PaperOrder.run_id == self.run_id
        ).first()
        
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.status not in [OrderStatus.PENDING.value, OrderStatus.PARTIALLY_FILLED.value]:
            raise ValueError(f"Order {order_id} cannot be cancelled (status: {order.status})")
        
        order.status = OrderStatus.CANCELLED.value
        order.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Cancelled order {order_id}")
        return order
    
    async def create_stop_loss_and_take_profit(
        self,
        symbol: str,
        quantity: float,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create stop loss and/or take profit orders for a position.
        
        This should be called after opening a position to automatically
        protect against losses and lock in profits.
        
        Args:
            symbol: Trading pair
            quantity: Position quantity to protect
            stop_loss_price: Stop loss price (sell if price drops to this level)
            take_profit_price: Take profit price (sell if price rises to this level)
        
        Returns:
            Dictionary with created order IDs
        """
        created_orders = {}
        
        if stop_loss_price:
            try:
                stop_order = await self.create_order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.STOP_LOSS,
                    quantity=quantity,
                    stop_price=stop_loss_price
                )
                created_orders['stop_loss'] = stop_order.id
                logger.info(f"Created stop loss order for {symbol} at {stop_loss_price}")
            except Exception as e:
                logger.error(f"Error creating stop loss order: {e}")
        
        if take_profit_price:
            try:
                tp_order = await self.create_order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.TAKE_PROFIT,
                    quantity=quantity,
                    stop_price=take_profit_price
                )
                created_orders['take_profit'] = tp_order.id
                logger.info(f"Created take profit order for {symbol} at {take_profit_price}")
            except Exception as e:
                logger.error(f"Error creating take profit order: {e}")
        
        return created_orders
    
    async def process_pending_orders(self, symbol: Optional[str] = None):
        """
        Process all pending orders and check for fills.
        
        This should be called periodically to check if limit/stop orders
        should be filled based on current market prices.
        
        Args:
            symbol: Optional symbol filter (process only this symbol)
        """
        query = self.db.query(PaperOrder).filter(
            PaperOrder.run_id == self.run_id,
            PaperOrder.status.in_([OrderStatus.PENDING.value, OrderStatus.PARTIALLY_FILLED.value])
        )
        
        if symbol:
            query = query.filter(PaperOrder.symbol == symbol.upper())
        
        pending_orders = query.all()
        
        for order in pending_orders:
            try:
                current_price = await self._get_current_price(order.symbol)
                await self._check_and_fill_order(order, current_price)
            except Exception as e:
                logger.error(f"Error processing order {order.id}: {e}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[PaperOrder]:
        """
        Get all open (pending or partially filled) orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        query = self.db.query(PaperOrder).filter(
            PaperOrder.run_id == self.run_id,
            PaperOrder.status.in_([OrderStatus.PENDING.value, OrderStatus.PARTIALLY_FILLED.value])
        )
        
        if symbol:
            query = query.filter(PaperOrder.symbol == symbol.upper())
        
        return query.order_by(desc(PaperOrder.created_at)).all()
    
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[PaperOrder]:
        """
        Get order history.
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum number of orders to return
            
        Returns:
            List of orders
        """
        query = self.db.query(PaperOrder).filter(
            PaperOrder.run_id == self.run_id
        )
        
        if symbol:
            query = query.filter(PaperOrder.symbol == symbol.upper())
        
        return query.order_by(desc(PaperOrder.created_at)).limit(limit).all()
    
    async def sync_testnet_orders(self, symbol: Optional[str] = None):
        """
        Sync order status from Binance Testnet API.
        
        Updates database with latest order status from testnet.
        Only works in testnet mode.
        
        Args:
            symbol: Optional symbol filter
        """
        if self.mode != "testnet":
            logger.warning("sync_testnet_orders only works in testnet mode")
            return
        
        # Get orders from database that have binance_order_id
        query = self.db.query(PaperOrder).filter(
            PaperOrder.run_id == self.run_id,
            PaperOrder.binance_order_id.isnot(None),
            PaperOrder.status.in_([OrderStatus.PENDING.value, OrderStatus.PARTIALLY_FILLED.value])
        )
        
        if symbol:
            query = query.filter(PaperOrder.symbol == symbol.upper())
        
        orders = query.all()
        
        for order in orders:
            try:
                # Query Binance for order status
                testnet_order = await self.testnet_client.get_order(
                    symbol=order.symbol,
                    order_id=order.binance_order_id
                )
                
                # Update order status
                order.status = self._map_binance_status(testnet_order['status'])
                order.filled_quantity = float(testnet_order.get('executedQty', 0))
                
                if testnet_order.get('avgPrice'):
                    order.avg_fill_price = float(testnet_order['avgPrice'])
                
                order.updated_at = datetime.utcnow()
                
                logger.info(
                    f"Synced order {order.id}: status={order.status}, "
                    f"filled={order.filled_quantity}/{order.quantity}"
                )
            except Exception as e:
                logger.error(f"Error syncing order {order.id}: {e}")
        
        self.db.commit()
    
    async def get_testnet_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information from Binance Testnet.
        
        Returns balances and account status.
        Only works in testnet mode.
        
        Returns:
            Account info dict or None if not in testnet mode
        """
        if self.mode != "testnet":
            return None
        
        return await self.testnet_client.get_account()
    
    # Private helper methods
    
    def _map_binance_status(self, binance_status: str) -> str:
        """Map Binance order status to our status enum."""
        status_map = {
            'NEW': OrderStatus.PENDING.value,
            'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED.value,
            'FILLED': OrderStatus.FILLED.value,
            'CANCELED': OrderStatus.CANCELLED.value,
            'PENDING_CANCEL': OrderStatus.PENDING.value,
            'REJECTED': OrderStatus.REJECTED.value,
            'EXPIRED': OrderStatus.CANCELLED.value,
        }
        return status_map.get(binance_status, OrderStatus.PENDING.value)
    
    def _validate_order(
        self,
        order_type: OrderType,
        price: Optional[float],
        stop_price: Optional[float],
        quantity: float
    ):
        """Validate order parameters."""
        if quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}")
        
        if order_type == OrderType.LIMIT and not price:
            raise ValueError("Limit orders require a price")
        
        if order_type in [OrderType.STOP_LOSS, OrderType.TAKE_PROFIT] and not stop_price:
            raise ValueError(f"{order_type.value} orders require a stop price")
        
        if price and price <= 0:
            raise ValueError(f"Invalid price: {price}")
        
        if stop_price and stop_price <= 0:
            raise ValueError(f"Invalid stop price: {stop_price}")
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        ticker = await self.binance.fetch_ticker(symbol)
        return float(ticker['lastPrice'])
    
    def _validate_balance(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        current_price: float,
        limit_price: Optional[float]
    ):
        """Validate sufficient balance for order."""
        # Use limit price if specified, otherwise use current price
        price = limit_price if limit_price else current_price
        
        if side == OrderSide.BUY:
            # Check cash balance
            required_cash = quantity * price * (1 + self.fee_rate)
            cash = self._get_cash_balance()
            
            if required_cash > cash:
                raise ValueError(
                    f"Insufficient cash: need ${required_cash:.2f}, have ${cash:.2f}"
                )
        else:  # SELL
            # Check position
            position = self._get_position(symbol)
            current_qty = position.quantity if position else 0.0
            
            if quantity > current_qty:
                raise ValueError(
                    f"Insufficient position: need {quantity}, have {current_qty}"
                )
    
    async def _fill_market_order(self, order: PaperOrder, market_price: float):
        """Fill a market order immediately with slippage."""
        # Apply slippage
        if order.side == OrderSide.BUY.value:
            fill_price = market_price * (1 + self.slippage_pct)
        else:
            fill_price = market_price * (1 - self.slippage_pct)
        
        # Execute the fill
        await self._execute_fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            reason="Market order filled immediately"
        )
    
    async def _check_and_fill_order(self, order: PaperOrder, current_price: float):
        """Check if an order should be filled based on current price."""
        should_fill = False
        fill_price = None
        
        if order.order_type == OrderType.LIMIT.value:
            # Limit BUY fills when market price <= limit price
            # Limit SELL fills when market price >= limit price
            if order.side == OrderSide.BUY.value and current_price <= order.price:
                should_fill = True
                fill_price = order.price
            elif order.side == OrderSide.SELL.value and current_price >= order.price:
                should_fill = True
                fill_price = order.price
        
        elif order.order_type == OrderType.STOP_LOSS.value:
            # Stop loss triggers when price crosses stop price
            if order.side == OrderSide.SELL.value and current_price <= order.stop_price:
                should_fill = True
                fill_price = current_price  # Market fill at current price
            elif order.side == OrderSide.BUY.value and current_price >= order.stop_price:
                should_fill = True
                fill_price = current_price
        
        elif order.order_type == OrderType.TAKE_PROFIT.value:
            # Take profit triggers when price crosses take profit price
            if order.side == OrderSide.SELL.value and current_price >= order.stop_price:
                should_fill = True
                fill_price = order.stop_price
            elif order.side == OrderSide.BUY.value and current_price <= order.stop_price:
                should_fill = True
                fill_price = order.stop_price
        
        if should_fill and fill_price:
            remaining_qty = order.quantity - order.filled_quantity
            await self._execute_fill(
                order=order,
                fill_price=fill_price,
                fill_quantity=remaining_qty,
                reason=f"{order.order_type} triggered at {current_price}"
            )
    
    async def _execute_fill(
        self,
        order: PaperOrder,
        fill_price: float,
        fill_quantity: float,
        reason: str
    ):
        """Execute an order fill and update positions."""
        # Calculate fee
        fee = fill_quantity * fill_price * self.fee_rate
        
        # Update order
        order.filled_quantity += fill_quantity
        order.avg_fill_price = (
            (order.avg_fill_price or 0) * (order.filled_quantity - fill_quantity) +
            fill_price * fill_quantity
        ) / order.filled_quantity if order.filled_quantity > 0 else fill_price
        
        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED.value
        else:
            order.status = OrderStatus.PARTIALLY_FILLED.value
        
        order.updated_at = datetime.utcnow()
        
        # Create trade record
        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=fill_quantity,
            price=fill_price,
            timestamp=datetime.utcnow(),
            run_id=self.run_id,
            pnl=0.0  # Will be calculated when position is closed
        )
        self.db.add(trade)
        
        # Update position
        position = self._get_position(order.symbol)
        
        if order.side == OrderSide.BUY.value:
            if position:
                # Update existing position
                total_cost = (position.quantity * position.avg_entry_price) + (fill_quantity * fill_price)
                position.quantity += fill_quantity
                position.avg_entry_price = total_cost / position.quantity
            else:
                # Create new position
                position = Position(
                    symbol=order.symbol,
                    quantity=fill_quantity,
                    avg_entry_price=fill_price,
                    unrealized_pnl=0.0
                )
                self.db.add(position)
            
            # Deduct cash
            self._update_cash_balance(-1 * (fill_quantity * fill_price + fee))
        
        else:  # SELL
            if position:
                # Calculate realized PnL
                entry_value = fill_quantity * position.avg_entry_price
                exit_value = fill_quantity * fill_price
                pnl = exit_value - entry_value - fee
                trade.pnl = pnl
                
                # Update position
                position.quantity -= fill_quantity
                if position.quantity <= 0.0001:  # Close position (handle floating point)
                    self.db.delete(position)
                
                # Add cash
                self._update_cash_balance(fill_quantity * fill_price - fee)
            else:
                logger.warning(f"No position found for {order.symbol} during SELL fill")
        
        self.db.commit()
        
        logger.info(
            f"Filled {fill_quantity} {order.symbol} at ${fill_price:.2f} "
            f"(Fee: ${fee:.2f}, Reason: {reason})"
        )
    
    def _get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        return self.db.query(Position).filter(
            Position.symbol == symbol.upper()
        ).first()
    
    def _get_cash_balance(self) -> float:
        """Get current cash balance."""
        snapshot = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.run_id == self.run_id
        ).order_by(desc(PortfolioSnapshot.timestamp)).first()
        
        if snapshot:
            return snapshot.cash_balance
        return settings.initial_cash
    
    def _update_cash_balance(self, delta: float):
        """Update cash balance by delta amount."""
        current_cash = self._get_cash_balance()
        new_cash = current_cash + delta
        
        # Create snapshot
        snapshot = PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            cash_balance=new_cash,
            total_equity=self._calculate_total_equity(new_cash),
            run_id=self.run_id
        )
        self.db.add(snapshot)
    
    def _calculate_total_equity(self, cash: float) -> float:
        """Calculate total equity (cash + position values)."""
        positions = self.db.query(Position).all()
        # Note: This is approximate since we'd need current prices for each position
        # In production, you'd fetch current prices for all positions
        position_value = sum(p.quantity * p.avg_entry_price for p in positions)
        return cash + position_value
    
    async def close(self):
        """Close the Binance service connection."""
        await self.binance.close()
