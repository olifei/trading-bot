from google.adk.agents.callback_context import CallbackContext
from typing import Optional
from google.genai import types

def load_user_profile(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback function to load user profile and compliance information
    
    This function is used as a before_agent_callback to load user profile
    information including KYC status and region-specific restrictions.
    """
    user_id = callback_context.state.get("user_id", "user1")
    
    try:
        from trading_assistant.services.compliance.kyc_api import get_kyc_status
        from trading_assistant.services.compliance.region_api import get_user_info, get_region_restrictions
        
        kyc_status = get_kyc_status(user_id)
        user_info = get_user_info(user_id)
        region = user_info.get("region", "UNKNOWN")
        restrictions = get_region_restrictions(region)
        
        callback_context.state["user_id"] = user_id
        callback_context.state["language"] = user_info.get("language", "english")
        callback_context.state["kyc_verified"] = kyc_status.get("kyc_verified", False)
        callback_context.state["region"] = region
        callback_context.state["restricted_coins"] = restrictions.get("restricted_coins", [])
        callback_context.state["restricted_trade_types"] = restrictions.get("restricted_trade_types", [])
        callback_context.state["max_transaction_amount"] = restrictions.get("max_transaction_amount", 0)
        callback_context.state["user_profile"] = f"""
User ID: {callback_context.state["user_id"]}
Region: {callback_context.state["region"]}
KYC Verified: {callback_context.state["kyc_verified"]}
Restricted Coins: {callback_context.state["restricted_coins"]}
Restricted Trade Types: {callback_context.state["restricted_trade_types"]}
Maximum Transaction Amount: {callback_context.state["max_transaction_amount"]} USDT
"""
        # print(f"[Profile] Loaded profile for user {user_id}")
    except Exception as e:
        print(f"[Profile Error] Failed to load user profile: {str(e)}")
    return None
