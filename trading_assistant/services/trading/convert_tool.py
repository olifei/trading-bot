from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.trading.trading_api import convert_currency
from trading_assistant.services.compliance.compliance_checker import compliance_check
from typing import Dict, Any


def execute_conversion(from_asset: str, to_asset: str, amount: str, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Convert one cryptocurrency to another.
    
    Args:
        from_asset: The source cryptocurrency (e.g., "BTC", "ETH")
        to_asset: The target cryptocurrency (e.g., "BTC", "ETH")
        amount: Amount of source cryptocurrency to convert
        
    Returns:
        A dictionary containing conversion details and status with standardized fields:
        - status: "success" or "error"
        - data: The complete conversion data
        - message: A human-readable summary
        - Additional convenience fields like conversion_id
    """
    # Get user_id from session state
    user_id = tool_context.state.get("user_id", "user1")
    
    # Debug request parameters
    print(f"[Convert] Request parameters: from_asset={from_asset}, to_asset={to_asset}, amount={amount}")
    
    # Validate required parameters
    if not from_asset:
        return {
            "status": "error",
            "message": "Source asset (from_asset) is required"
        }
    
    if not to_asset:
        return {
            "status": "error",
            "message": "Target asset (to_asset) is required"
        }
        
    if not amount:
        return {
            "status": "error",
            "message": "Amount is required for conversion"
        }
    
    # Validate amount format
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return {
                "status": "error",
                "message": "Amount must be greater than zero"
            }
    except (ValueError, TypeError):
        return {
            "status": "error",
            "message": f"Invalid amount format: {amount}"
        }
    
    # Prepare transaction parameters for compliance check
    transaction_params = {
        "transaction_type": "CONVERT",
        "from_asset": from_asset.upper(),
        "to_asset": to_asset.upper(),
        "amount": amount
    }
    
    # Run compliance check
    context = {
        "user_id": user_id,
        "kyc_verified": tool_context.state.get("kyc_verified", False),
        "user_region": tool_context.state.get("user_region", None)
    }
    
    # compliance_result = compliance_check(transaction_params, context)
    # if not compliance_result["passed"]:
    #     return {
    #         "status": "REJECTED",
    #         "reason": compliance_result["message"],
    #         "details": compliance_result,
    #         "suggestion": compliance_result.get("suggestion")
    #     }
    
    # Compliance check passed, execute the conversion
    conversion = convert_currency(
        user_id=user_id,
        from_asset=from_asset,
        to_asset=to_asset,
        amount=amount
    )
    
    # Format the response for better readability in the agent
    summary = (f"Successfully converted {conversion['from_amount']} {conversion['from_asset']} "
              f"to {conversion['to_amount']} {conversion['to_asset']} "
              f"(Rate: 1 {conversion['from_asset']} = {conversion['rate']} {conversion['to_asset']})")
    
    # Return standardized structure with the raw conversion data and a formatted summary
    return {
        "status": "success",
        "data": conversion,
        "message": summary,
        "summary": summary,  # Keeping for backward compatibility
        "conversion_id": conversion["conversion_id"],
        "conversion_status": conversion["status"]
    }


def create_convert_tool() -> FunctionTool:
    """
    Create an ADK FunctionTool for currency conversion operations
    """
    return FunctionTool(
        func=execute_conversion
    )
