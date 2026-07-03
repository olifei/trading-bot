import time
import uuid
from datetime import datetime
from typing import Optional
from trading_assistant.services.portfolio.portfolio_api import update_user_balance
from trading_assistant.services.market.market_api import get_market_price, get_conversion_rate
from trading_assistant.services.database.firestore_client import get_firestore_client

def create_spot_order(user_id: str, symbol: str, side: str, order_type: str, 
                     quantity: Optional[str] = None, price: Optional[str] = None, amount: Optional[str] = None) -> dict:
    """
    Create a spot trading order and store in Firestore
    
    Args:
        user_id: The ID of the user
        symbol: The trading pair symbol (e.g., "BTCUSDT")
        side: "BUY" or "SELL"
        order_type: "LIMIT" or "MARKET"
        quantity: Quantity of the base asset to trade
        price: Limit price (required for LIMIT orders)
        amount: Total value in quote currency (alternative to quantity)
        
    Returns:
        Dict containing order information
    """
    # print(f"[Trading API] Creating spot order for user {user_id}")
    
    try:
        # Get Firestore client
        db = get_firestore_client()
        
        # Generate order ID and transaction ID
        order_id = f"ord-{uuid.uuid4().hex[:8]}"
        transaction_id = f"tx-{uuid.uuid4().hex[:8]}"
    
        # Standardize inputs
        symbol = symbol.upper()
        side = side.upper()
        order_type = order_type.upper()
        
        # Add USDT suffix if not present
        if not symbol.endswith("USDT"):
            symbol = f"{symbol}USDT"
        
        # Get current market price
        market_data = get_market_price(symbol)
        market_price = float(market_data.get("price", "0.00"))
        
        # Calculate quantity if amount is provided
        base_asset = symbol[:-4]  # Remove USDT
        quote_asset = "USDT"
        
        if quantity is None and amount is not None:
            # Convert amount to quantity
            amount_float = float(amount)
            quantity = str(round(amount_float / market_price, 8)) if market_price > 0 else "0.00"
        elif quantity is None and amount is None:
            # Default to a small amount
            quantity = "0.0"
        
        # Calculate amount if not provided
        quantity_float = float(quantity)
        if amount is None:
            amount = str(round(quantity_float * market_price, 2))
    
        # Create transactions for portfolio update
        transactions = []
        if side == "BUY":
            transactions.append({"asset": base_asset, "amount": quantity})
            transactions.append({"asset": quote_asset, "amount": f"-{amount}"})
        else:  # SELL
            transactions.append({"asset": base_asset, "amount": f"-{quantity}"})
            transactions.append({"asset": quote_asset, "amount": amount})
        
        # Update user portfolio
        updated_portfolio = update_user_balance(user_id, transactions)
        
        # Create timestamps
        now = datetime.now().isoformat()
        now_ms = int(time.time() * 1000)
        
        # Create order object
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price if order_type == "LIMIT" else str(market_price),
            "amount": amount,
            "status": "FILLED",  # Always fills immediately
            "create_time": now_ms,
            "update_time": now_ms
        }
        
        # Create transaction document
        transaction_data = {
            "user_id": user_id,
            "type": "spot",
            "status": "completed",
            "created_at": now,
            "updated_at": now,
            "order": order
        }
        
        # Store in Firestore
        db.collection("transactions").document(transaction_id).set(transaction_data)
        
        return order
        
    except Exception as e:
        print(f"[Trading API Error] {str(e)}")
        return {
            "order_id": f"error-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "symbol": symbol,
            "status": "ERROR",
            "error": str(e)
        }

def convert_currency(user_id: str, from_asset: str, to_asset: str, amount: str) -> dict:
    """
    Convert one cryptocurrency to another and store in Firestore
    
    Args:
        user_id: The ID of the user
        from_asset: Source asset
        to_asset: Target asset
        amount: Amount of source asset to convert
        
    Returns:
        Dict containing conversion information
    """
    # print(f"[Trading API] Converting currency for user {user_id}")
    
    try:
        # Get Firestore client
        db = get_firestore_client()
        
        # Generate conversion ID and transaction ID
        conversion_id = f"cnv-{uuid.uuid4().hex[:8]}"
        transaction_id = f"tx-{uuid.uuid4().hex[:8]}"
        
        # Standardize inputs
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        # Get conversion rate
        rate_data = get_conversion_rate(from_asset, to_asset)
        rate = float(rate_data.get("rate", "0.00"))
        
        # Calculate output amount
        from_amount = float(amount)
        to_amount = from_amount * rate
        
        # Create transactions for portfolio update
        transactions = [
            {"asset": from_asset, "amount": f"-{amount}"},
            {"asset": to_asset, "amount": str(round(to_amount, 8))}
        ]
        
        # Update user portfolio
        updated_portfolio = update_user_balance(user_id, transactions)
        
        # Create timestamps
        now = datetime.now().isoformat()
        now_ms = int(time.time() * 1000)
        
        # Create conversion object
        conversion = {
            "conversion_id": conversion_id,
            "from_asset": from_asset,
            "to_asset": to_asset,
            "from_amount": amount,
            "to_amount": str(round(to_amount, 8)),
            "rate": str(rate),
            "status": "COMPLETED",  # Always completes immediately
            "create_time": now_ms,
            "update_time": now_ms
        }
        
        # Create transaction document
        transaction_data = {
            "user_id": user_id,
            "type": "convert",
            "status": "completed",
            "created_at": now,
            "updated_at": now,
            "conversion": conversion
        }
        
        # Store in Firestore
        db.collection("transactions").document(transaction_id).set(transaction_data)
        
        return conversion
        
    except Exception as e:
        print(f"[Trading API Error] {str(e)}")
        return {
            "conversion_id": f"error-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "status": "ERROR",
            "error": str(e)
        }

def get_order_status(user_id: str, order_id: str) -> dict:
    """
    Get the status of an order from Firestore
    
    Args:
        user_id: The ID of the user
        order_id: The ID of the order
        
    Returns:
        Dict containing order information
    """
    # print(f"[Trading API] Getting order status for user {user_id}, order {order_id}")
    
    try:
        # Get Firestore client
        db = get_firestore_client()
        
        # Query for the order in transactions collection
        query = db.collection("transactions").where("user_id", "==", user_id).where("type", "==", "spot").where("order.order_id", "==", order_id)
        results = query.get()
        
        # Check if order was found
        for doc in results:
            transaction_data = doc.to_dict()
            # Return the order data if found
            if "order" in transaction_data:
                return transaction_data["order"]
        
        # Order not found
        return {"error": "Order not found", "status": "ERROR"}
        
    except Exception as e:
        print(f"[Trading API Error] {str(e)}")
        return {"error": str(e), "status": "ERROR"}

def get_conversion_status(user_id: str, conversion_id: str) -> dict:
    """
    Get the status of a conversion from Firestore
    
    Args:
        user_id: The ID of the user
        conversion_id: The ID of the conversion
        
    Returns:
        Dict containing conversion information
    """
    # print(f"[Trading API] Getting conversion status for user {user_id}, conversion {conversion_id}")
    
    try:
        # Get Firestore client
        db = get_firestore_client()
        
        # Query for the conversion in transactions collection
        query = db.collection("transactions").where("user_id", "==", user_id).where("type", "==", "convert").where("conversion.conversion_id", "==", conversion_id)
        results = query.get()
        
        # Check if conversion was found
        for doc in results:
            transaction_data = doc.to_dict()
            # Return the conversion data if found
            if "conversion" in transaction_data:
                return transaction_data["conversion"]
        
        # Conversion not found
        return {"error": "Conversion not found", "status": "ERROR"}
        
    except Exception as e:
        print(f"[Trading API Error] {str(e)}")
        return {"error": str(e), "status": "ERROR"}
