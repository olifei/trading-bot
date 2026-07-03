from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.trading.trading_api import convert_currency
from trading_assistant.schemas import ConvertArgs, validate_args
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
    model, err = validate_args(ConvertArgs, {
        "from_asset": from_asset, "to_asset": to_asset, "amount": amount,
    })
    if err:
        return err
    from_asset, to_asset, amount = model.from_asset, model.to_asset, model.amount

    user_id = tool_context.state.get("user_id", "user1")

    print(f"[Convert] Executing conversion: {amount} {from_asset} → {to_asset}")

    if not amount:
        return {"status": "error", "message": "Conversion amount not specified"}

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
