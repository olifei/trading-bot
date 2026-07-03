from google.adk.tools import FunctionTool, ToolContext
from trading_assistant.services.portfolio.portfolio_api import get_user_portfolio


def get_portfolio(tool_context: ToolContext = None) -> dict:
    """
    Retrieve a user's complete cryptocurrency portfolio.
    
    This tool provides a comprehensive view of all cryptocurrency assets currently held by the user,
    including available balances, frozen funds, and other detailed portfolio information.
    
    Args:
        tool_context (ToolContext): ADK tool context used to access the user ID
    
    Returns:
        dict: User's portfolio information, containing:
            - status (str): "success" or "error"
            - data (dict): The complete portfolio data
            - message (str): Human-readable portfolio summary
            - summary (str): Brief description of the portfolio
            - portfolio (dict): Raw portfolio data
            - has_balances (bool): Whether the user has any asset balances
    
    Notes:
        - If the user doesn't hold any assets, has_balances will be False
        - User ID is obtained from tool_context.state, defaulting to "user1"
        - Only assets with balance greater than zero are included in the summary
    """
    user_id = tool_context.state.get("user_id", "user1")
    portfolio = get_user_portfolio(user_id)
    
    formatted_balances = []
    for balance in portfolio["balances"]:
        if float(balance["free"]) > 0:
            formatted_balances.append(
                f"{balance['asset']}: {balance['free']} (Available)")
    
    if formatted_balances:
        summary = "Portfolio contains: " + ", ".join(formatted_balances)
    else:
        summary = "Portfolio is empty - no assets found"
    
    return {
        "status": "success",
        "data": portfolio,
        "message": summary,
        "summary": summary,
        "portfolio": portfolio,
        "has_balances": len(formatted_balances) > 0
    }


def create_get_portfolio_tool() -> FunctionTool:
    return FunctionTool(
        func=get_portfolio
    )
