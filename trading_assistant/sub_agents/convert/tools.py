from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.trading.trading_api import convert_currency
from typing import Optional, Dict, Any

def execute_convert_operation(from_asset: str, to_asset: str, amount: Optional[str] = None, 
                             tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Execute a cryptocurrency conversion operation between different cryptocurrencies.
    
    This tool provides direct conversion between cryptocurrencies without going through 
    USDT as an intermediate step.
    
    Args:
        from_asset (str, required): Source cryptocurrency (e.g., "BTC", "ETH", "BNB")
        to_asset (str, required): Target cryptocurrency (e.g., "ETH", "DOT", "ADA")
        amount (str, optional): Conversion amount (quantity of source cryptocurrency)
        tool_context (ToolContext): The ADK tool context
    
    Returns:
        Dict[str, Any]: Conversion operation result, containing:
            - status (str): "success" or "error"
            - data (dict): Complete conversion data (on success)
            - message (str): Human-readable conversion summary or error message
            - converted_amount (str): Amount of target asset received (on success)
            - exchange_rate (str): Exchange rate used for the conversion (on success)
    
    Notes:
        - Source and target assets cannot be the same
        - This tool is specifically for direct conversion; USDT-related trades should use spot_order_tool
        - User must have sufficient source asset to execute the conversion
    """
    user_id = tool_context.state.get("user_id", "user1")
    
    print(f"[Convert] Executing conversion: {amount} {from_asset} → {to_asset}")
    
    # Validate required parameters
    if not from_asset:
        return {"status": "error", "message": "Source asset not specified"}
    if not to_asset:
        return {"status": "error", "message": "Target asset not specified"}
    if not amount:
        return {"status": "error", "message": "Conversion amount not specified"}
    
    # Check source and target assets can't be the same
    if from_asset.upper() == to_asset.upper():
        return {"status": "error", "message": f"Source and target assets cannot be the same ({from_asset})"}
    
    # Check neither source nor target is USDT
    # Note: This tool is specifically for direct conversion; USDT trades should use spot_order_tool
    if from_asset.upper() == "USDT" or to_asset.upper() == "USDT":
        return {
            "status": "error", 
            "message": "USDT-related trades should use the Spot Trading feature. This conversion feature only supports direct conversion between cryptocurrencies."
        }
    
    # Execute conversion
    try:
        result = convert_currency(
            user_id=user_id,
            from_asset=from_asset,
            to_asset=to_asset,
            amount=amount
        )
        
        # Return standardized result
        return {
            "status": "success",
            "data": result,
            "message": f"Successfully converted {amount} {from_asset} to {result.get('converted_amount')} {to_asset}",
            "converted_amount": result.get("converted_amount"),
            "exchange_rate": result.get("exchange_rate")
        }
    except Exception as e:
        print(f"[Convert Error] Conversion operation failed: {str(e)}")
        return {"status": "error", "message": f"Conversion operation failed: {str(e)}"}

convert_tool = FunctionTool(func=execute_convert_operation)
