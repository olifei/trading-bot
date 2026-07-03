from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.market.market_api import get_market_price, get_conversion_rate


def get_price(symbol: str, tool_context: ToolContext = None) -> dict:
    """
    Get the current market price for a cryptocurrency.
    
    This tool provides real-time market price information for the specified cryptocurrency,
    denominated in USDT.
    
    Args:
        symbol (str, required): The trading pair symbol (e.g., "BTC", "ETH", "BTCUSDT")
        tool_context (ToolContext): The ADK tool context
        
    Returns:
        dict: Price information dictionary, containing:
            - status (str): "success" or "error"
            - data (dict): The complete price data
            - message (str): Human-readable price summary
            - summary (str): Brief price description (for backward compatibility)
            - price (str): Current price value
    
    Notes:
        - All prices are denominated in USDT
        - If the requested trading pair is not found, an error status will be returned
        - Price field is always returned as a string to maintain precision
    """
    price_data = get_market_price(symbol)
    
    if "error" not in price_data:
        formatted_price = f"Current price of {price_data['symbol']}: {price_data['price']} USDT"        
        return {
            "status": "success",
            "data": price_data,
            "message": formatted_price,
            "summary": formatted_price,  # Keeping for backward compatibility
            "price": price_data.get("price", "0.00")
        }
    else:
        formatted_price = f"Could not find price for {symbol}"        
        return {
            "status": "error",
            "data": price_data,
            "message": formatted_price,
            "summary": formatted_price,  # Keeping for backward compatibility
            "price": "0.00"
        }


def create_market_price_tool() -> FunctionTool:
    return FunctionTool(
        func=get_price
    )


def get_exchange_rate(from_asset: str, to_asset: str, tool_context: ToolContext = None) -> dict:
    """
    Get the current exchange rate between two cryptocurrencies.
    
    This tool provides the current exchange rate information between specified cryptocurrency pairs.
    
    Args:
        from_asset (str, required): The source cryptocurrency (e.g., "BTC")
        to_asset (str, required): The target cryptocurrency (e.g., "ETH")
        tool_context (ToolContext): The ADK tool context
        
    Returns:
        dict: Exchange rate information dictionary, containing:
            - status (str): "success" or "error"
            - data (dict): The complete rate data
            - message (str): Human-readable rate summary
            - summary (str): Brief rate description (for backward compatibility)
            - rate (str): Current exchange rate value
    
    Notes:
        - Rate represents how many units of target asset equal 1 unit of source asset
        - Rate field is always returned as a string to maintain precision
        - If rate cannot be obtained, an error status will be returned
    """
    rate_data = get_conversion_rate(from_asset, to_asset)    
    rate = rate_data.get("rate", "0.00")
    formatted_rate = f"Exchange rate: 1 {from_asset} = {rate} {to_asset}"
    
    if "error" not in rate_data and float(rate) > 0:
        return {
            "status": "success",
            "data": rate_data,
            "message": formatted_rate,
            "summary": formatted_rate,  # Keeping for backward compatibility
            "rate": rate
        }
    else:
        error_msg = rate_data.get("error", "Rate could not be determined")
        return {
            "status": "error",
            "data": rate_data,
            "message": f"Error getting exchange rate: {error_msg}",
            "summary": f"Error getting exchange rate: {error_msg}",  # Keeping for backward compatibility
            "rate": "0.00"
        }


def create_exchange_rate_tool() -> FunctionTool:
    return FunctionTool(
        func=get_exchange_rate
    )
