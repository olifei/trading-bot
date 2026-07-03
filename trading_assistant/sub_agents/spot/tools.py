from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.trading.trading_api import create_spot_order
from trading_assistant.services.market.market_api import get_market_price
from typing import Optional, Dict, Any

def execute_spot_order(symbol: str, side: str, order_type: str = "LIMIT", 
                      quantity: Optional[str] = None, price: Optional[str] = None, 
                      tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Execute a spot trading order (buy or sell cryptocurrency)
    
    Args:
        symbol: Trading pair, e.g. "BTC", "ETH", "BNB"
        side: "BUY" or "SELL"
        order_type: "LIMIT" or "MARKET"
        quantity: Trading quantity
        price: Limit price (required for LIMIT orders)
    """
    user_id = tool_context.state.get("user_id", "user1")
    
    print(f"[Spot] Executing order: {symbol} {side} {quantity}@{price}")
    
    if not symbol:
        return {"status": "error", "message": "Trading pair not specified"}
    if not side:
        return {"status": "error", "message": "Trading side (BUY/SELL) not specified"}
    if not quantity:
        return {"status": "error", "message": "Trading quantity not specified"}
    if order_type == "LIMIT":
        if not price:
            return {"status": "error", "message": "Price must be specified for LIMIT orders"}
    else: # MARKET
        price = get_market_price(symbol)
    try:
        order = create_spot_order(
            user_id=user_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        base_asset = symbol.split("USDT")[0] if symbol.endswith("USDT") else symbol
        return {
            "status": "success",
            "data": order,
            "message": f"Successfully {'bought' if side=='BUY' else 'sold'} {quantity} {base_asset} at price: {price} USDT each",
            "order_id": order["order_id"],
            "order_status": order["status"]
        }
    except Exception as e:
        print(f"[Spot Error] Order execution failed: {str(e)}")
        return {"status": "error", "message": f"Order execution failed: {str(e)}"}

spot_order_tool = FunctionTool(func=execute_spot_order)
