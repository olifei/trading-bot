from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.genai import types
from typing import Optional, Dict, Any

def kyc_compliance_check(callback_context: CallbackContext, 
                       llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    KYC compliance check callback
    
    Checks if the user has completed KYC verification.
    If not, interrupts the flow with an appropriate message.
    """
    kyc_verified = callback_context.state.get("kyc_verified", False)
    
    if not kyc_verified:
        # print(f"[Compliance] KYC verification failed, intercepting request")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Please complete KYC verification before using trading functions. Visit our kyc-center website to complete verification.")]
            )
        )
    
    return None

def region_compliance_check(callback_context: CallbackContext,
                         llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    Region compliance check callback
    
    Checks if trading is allowed in the user's region.
    Adds region-specific restrictions to system instructions.
    """
    region = callback_context.state.get("region", "UNKNOWN")
    
    if region in ["RESTRICTED", "UNKNOWN"]:
        # print(f"[Compliance] User region {region} restricted, intercepting request")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Sorry, trading features are currently unavailable in your region {region}.")]
            )
        )
    
    restricted_coins = callback_context.state.get("restricted_coins", [])
    restricted_trade_types = callback_context.state.get("restricted_trade_types", [])
    max_amount = callback_context.state.get("max_transaction_amount", 0)
    
    restrictions_text = "Note: Trading Restrictions of this user:\n"
    if restricted_coins:
        restrictions_text += f"- Restricted Coins: {', '.join(restricted_coins)}\n"
    if restricted_trade_types:
        restrictions_text += f"- Restricted Trade Types: {', '.join(restricted_trade_types)}\n"
    restrictions_text += f"- Maximum Transaction Amount: {max_amount} USDT\n"
    llm_request.config.system_instruction += f"\n\n{restrictions_text}"
    
    # Allow continued processing
    return None

def trade_params_compliance_check(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Trade parameters compliance check
    
    Verifies that the trading parameters comply with region restrictions:
    1. Checks if the cryptocurrencies are restricted in the user's region
    2. Ensures the transaction amount doesn't exceed the maximum allowed
    """
    if tool.name not in ["execute_spot_order", "execute_convert_operation"]:
        return None
        
    # print(f"[Compliance] Checking trade parameters {args}")
    
    # 1. Check coin restrictions
    restricted_coins = tool_context.state.get("restricted_coins", [])
    symbol = args.get("symbol", "")
    coin = symbol.split("USDT")[0] if "USDT" in symbol else symbol
    from_asset = args.get("from_asset", "")
    to_asset = args.get("to_asset", "")
    
    check_coins = [c for c in [coin, from_asset, to_asset] if c]
    
    for c in check_coins:
        if c in restricted_coins:
            # print(f"[Compliance] Coin {c} is in restricted list")
            return {
                "status": "error",
                "message": f"Trading {c} is not supported in your region"
            }
    
    # 2. Check transaction amount limits
    max_amount = tool_context.state.get("max_transaction_amount", 0)
    
    # Get parameters for different tool types
    amount = float(args.get("amount", 0) or 0)
    quantity = float(args.get("quantity", 0) or 0)
    price = float(args.get("price", 0) or 0)
    order_type = args.get("order_type", "LIMIT")
    
    # Import here to avoid circular imports
    from trading_assistant.services.market.market_api import get_market_price, get_conversion_rate
    
    # Calculate transaction value based on tool type and parameters
    transaction_value = 0
    
    if tool.name == "execute_spot_order":
        if quantity:
            # For LIMIT orders with price specified
            if order_type == "LIMIT" and price > 0:
                transaction_value = quantity * price
            # For MARKET orders or missing price, we get the current market price
            else:
                try:
                    # Get current market price for the coin
                    price_data = get_market_price(coin)
                    if "error" not in price_data:
                        current_price = float(price_data.get("price", 0))
                        transaction_value = quantity * current_price
                        # print(f"[Compliance] Calculated value for MARKET order: {quantity} * {current_price} = {transaction_value}")
                    else:
                        # print(f"[Compliance] Error getting market price: {price_data.get('error')}")
                        # Fall back to amount if specified
                        transaction_value = amount
                except Exception as e:
                    # print(f"[Compliance] Error getting market price: {str(e)}")
                    # Fall back to amount if specified
                    transaction_value = amount
    
    elif tool.name == "execute_convert_operation":
        if amount > 0 and from_asset:
            try:
                # Get the USDT value of the source asset being converted
                price_data = get_market_price(from_asset)
                if "error" not in price_data:
                    from_asset_price = float(price_data.get("price", 0))
                    transaction_value = amount * from_asset_price
                    # print(f"[Compliance] Calculated value for conversion: {amount} {from_asset} * {from_asset_price} = {transaction_value} USDT")
                else:
                    # print(f"[Compliance] Error getting price for conversion: {price_data.get('error')}")
                    # If we can't get the price, we can't properly check, so we use the amount as is
                    transaction_value = amount
            except Exception as e:
                # print(f"[Compliance] Error calculating conversion value: {str(e)}")
                # If exception occurs, use amount as is
                transaction_value = amount
    
    # print(f"[Compliance] Transaction value: {transaction_value} USDT")
    
    if max_amount and transaction_value > max_amount:
        # print(f"[Compliance] Transaction amount {transaction_value} exceeds limit {max_amount}")
        return {
            "status": "error",
            "message": f"Transaction amount {transaction_value} USDT exceeds your limit of {max_amount} USDT"
        }
    # All checks passed
    return None
