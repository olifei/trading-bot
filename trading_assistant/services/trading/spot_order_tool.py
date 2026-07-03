from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.trading.trading_api import create_spot_order
from trading_assistant.services.compliance.compliance_checker import compliance_check
from typing import Optional, Dict, Any

def execute_spot_order(symbol: str, side: str, order_type: str = "LIMIT", 
                      quantity: Optional[str] = None, price: Optional[str] = None, 
                      tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Execute a spot trading order to buy or sell cryptocurrency.
    
    This tool enables executing market or limit orders for cryptocurrency trading on the 
    exchange. It handles validation, compliance checks, and provides detailed 
    execution results.
    
    Args:
        symbol (str, required): The trading pair symbol (e.g., "BTC", "ETH", "BNB").
                               This represents the cryptocurrency to trade.
        
        side (str, required): Order direction, must be either "BUY" or "SELL".
                             Determines if you're purchasing or selling the asset.
        
        order_type (str, optional): Type of order, either "LIMIT" or "MARKET".
                                   Defaults to "LIMIT".
                                   - "LIMIT": Order executed at specified price or better
                                   - "MARKET": Order executed at current market price
        
        quantity (str, optional): Amount of the base asset to trade.
                                For BUY orders: quantity of cryptocurrency to purchase
                                For SELL orders: quantity of cryptocurrency to sell
                                Must be a positive number with appropriate precision.
        
        price (str, optional): Limit price for the order.
                              Required for LIMIT orders, ignored for MARKET orders.
                              Must be a positive number representing price in USDT.
        
        tool_context (ToolContext): The ADK tool context
    
    Returns:
        Dict[str, Any]: A dictionary containing the order details and status with standardized fields:
            - status (str): "success", "error", or "REJECTED"
            - data (dict): The complete order data from the exchange (on success)
            - message (str): A human-readable summary of the transaction
            - summary (str): Alternative field for the summary (for backward compatibility)
            - order_id (str): Unique identifier for the order (on success)
            - order_status (str): Status of the order on the exchange (on success)
            - reason (str): Rejection reason (only when status is "REJECTED")
            - details (dict): Rejection details (only when status is "REJECTED")
            - suggestion (str): Rejection suggestion (only when status is "REJECTED")
    
    Notes:
        - User must have sufficient balance to execute the order
        - For BUY orders: User needs enough USDT
        - For SELL orders: User needs enough of the specified crypto
        - The tool performs compliance checks before execution
        - Prices are always in USDT
    """
    user_id = tool_context.state.get("user_id", "user1")
    
    print(f"[SpotOrder] Request parameters: symbol={symbol}, side={side}, order_type={order_type}, "
          f"quantity={quantity}, price={price}")
    
    if not symbol:
        return {
            "status": "error",
            "message": "Symbol is required"
        }
    
    if not side:
        return {
            "status": "error",
            "message": "Side (BUY/SELL) is required"
        }
        
    if order_type == "LIMIT" and not price:
        return {
            "status": "error",
            "message": "Price is required for LIMIT orders"
        }
        
    if not quantity:
        return {
            "status": "error",
            "message": "Quantity must be specified"
        }
    
    transaction_params = {
        "transaction_type": "SPOT",
        "symbol": symbol,
        "side": side.upper() if side else "",
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
    }
    
    context = {
        "user_id": user_id,
        "kyc_verified": tool_context.state.get("kyc_verified", False),
        "user_region": tool_context.state.get("user_region", None)
    }
    
    compliance_result = compliance_check(transaction_params, context)
    if not compliance_result["passed"]:
        return {
            "status": "REJECTED",
            "reason": compliance_result["message"],
            "details": compliance_result,
            "suggestion": compliance_result.get("suggestion")
        }
    
    order = create_spot_order(
        user_id=user_id,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )
    
    base_asset = order["symbol"][:-4] if order["symbol"].endswith("USDT") else order["symbol"]
    quote_asset = "USDT"
    
    # Create a readable summary
    if order["side"] == "BUY":
        summary = (f"Successfully bought {order['quantity']} {base_asset} at "
                  f"{order['price']} {quote_asset} per {base_asset} "
                  f"(Total: {order['amount']} {quote_asset})")
    else:  # SELL
        summary = (f"Successfully sold {order['quantity']} {base_asset} at "
                  f"{order['price']} {quote_asset} per {base_asset} "
                  f"(Total: {order['amount']} {quote_asset})")
    
    # Return standardized structure with the raw order data and a formatted summary
    return {
        "status": "success",
        "data": order,
        "message": summary,
        "summary": summary,  # Keeping for backward compatibility
        "order_id": order["order_id"],
        "order_status": order["status"]
    }


def create_spot_order_tool() -> FunctionTool:
    """
    Create an ADK FunctionTool for spot trading operations
    """
    return FunctionTool(
        func=execute_spot_order
    )
