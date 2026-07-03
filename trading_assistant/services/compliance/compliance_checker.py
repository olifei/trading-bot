from typing import Dict, Any
from trading_assistant.services.compliance.kyc_api import get_kyc_status
from trading_assistant.services.compliance.region_api import get_user_info, get_region_restrictions
from trading_assistant.services.portfolio.portfolio_api import get_user_portfolio


def compliance_check(transaction_params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Comprehensive compliance check for trading operations.
    
    Args:
        transaction_params: Dictionary containing transaction parameters
            - transaction_type: "SPOT" or "CONVERT"
            - symbol/from_asset/to_asset: Trading pairs or assets
            - quantity: Transaction quantity
            - order_type: Type of order (for spot transactions)
            - other transaction-specific parameters
        context: Additional context information
            - user_id: User identifier
            - session_data: Optional session information
    
    Returns:
        Dictionary containing compliance check results:
        {
            "passed": True/False,         # Overall result
            "checks": {                   # Individual check results
                "kyc": {...},
                "region": {...},
                "assets": {...},
                "parameters": {...}
            },
            "message": "Reason message"   # Human-readable explanation
        }
    """
    context = context or {}
    user_id = context.get("user_id", "user1")
    
    result = {
        "passed": False,
        "checks": {},
        "message": "",
        "suggestion": None
    }
    
    # 1. KYC Check
    kyc_result = _check_kyc(user_id, context)
    result["checks"]["kyc"] = kyc_result
    
    if not kyc_result["passed"]:
        result["message"] = kyc_result["message"]
        return result
    
    # 2. Region Check
    region_result = _check_region_restrictions(user_id, context)
    result["checks"]["region"] = region_result
    
    if not region_result["passed"]:
        result["message"] = region_result["message"]
        return result
    
    # 3. Asset Check
    asset_result = _check_asset_availability(user_id, transaction_params)
    result["checks"]["assets"] = asset_result
    
    if not asset_result["passed"]:
        result["message"] = asset_result["message"]
        return result
    
    # 4. Parameters Check
    params_result = _check_transaction_parameters(transaction_params, region_result["restrictions"], context)
    result["checks"]["parameters"] = params_result
    
    if not params_result["passed"]:
        result["message"] = params_result["message"]
        if params_result.get("suggestion"):
            result["suggestion"] = params_result["suggestion"]
        return result
    
    # All checks passed
    result["passed"] = True
    result["message"] = "Transaction complies with all requirements"
    
    return result


def _check_kyc(user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    if context.get("kyc_verified", False):
        return {
            "passed": True,
            "message": "KYC already verified"
        }
    
    try:
        kyc_status = get_kyc_status(user_id)
        kyc_verified = kyc_status.get("kyc_verified", False)
        
        if not kyc_verified:
            return {
                "passed": False,
                "message": "KYC verification required to proceed"
            }
        
        return {
            "passed": True,
            "message": "KYC verification successful"
        }
        
    except Exception as e:
        return {
            "passed": False,
            "error": str(e),
            "message": "Unable to verify KYC status"
        }


def _check_region_restrictions(user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        cached_region = context.get("user_region")
        
        if cached_region:
            region = cached_region
        else:
            user_info = get_user_info(user_id)
            region = user_info.get("region", "UNKNOWN")
        
        restrictions = get_region_restrictions(region)
        
        if region in ["RESTRICTED", "UNKNOWN"]:
            return {
                "passed": False,
                "region": region,
                "message": f"Trading is restricted in your region ({region})",
                "restrictions": restrictions
            }
        
        return {
            "passed": True,
            "region": region,
            "message": "Region restrictions check passed",
            "restrictions": restrictions
        }
        
    except Exception as e:
        return {
            "passed": False,
            "error": str(e),
            "message": "Unable to verify region restrictions"
        }


def _check_asset_availability(user_id: str, transaction_params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        transaction_type = transaction_params.get("transaction_type", "")        
        asset = None
        required_amount = 0.0
        
        if transaction_type == "SPOT":
            side = transaction_params.get("side", "").upper()
            symbol = transaction_params.get("symbol", "")
            
            if side == "SELL":
                if "USDT" in symbol:
                    asset = symbol.replace("USDT", "")
                else:
                    asset = symbol
                required_amount = float(transaction_params.get("quantity", 0))
            elif side == "BUY":
                asset = "USDT"
                quantity = float(transaction_params.get("quantity", 0))
                price = float(transaction_params.get("price", 0))
                required_amount = quantity * price
                
        elif transaction_type == "CONVERT":
            asset = transaction_params.get("from_asset", "")
            required_amount = float(transaction_params.get("amount", 0))
        
        if not asset or required_amount <= 0:
            return {
                "passed": False,
                "message": "Invalid asset or amount specified"
            }
        
        portfolio = get_user_portfolio(user_id)
        user_balances = {balance["asset"]: float(balance["free"]) 
                         for balance in portfolio.get("balances", [])}
        
        if asset not in user_balances:
            return {
                "passed": False,
                "asset": asset,
                "required": required_amount,
                "available": 0,
                "message": f"You don't have any {asset} in your portfolio"
            }
        
        available_amount = user_balances[asset]
        if available_amount < required_amount:
            return {
                "passed": False,
                "asset": asset,
                "required": required_amount,
                "available": available_amount,
                "message": f"Insufficient {asset} balance. Required: {required_amount}, Available: {available_amount}"
            }
        
        return {
            "passed": True,
            "asset": asset,
            "required": required_amount,
            "available": available_amount,
            "message": "Sufficient funds available"
        }
        
    except Exception as e:
        return {
            "passed": False,
            "error": str(e),
            "message": f"Unable to verify asset availability, error: {str(e)}"
        }


def _check_transaction_parameters(transaction_params: Dict[str, Any], 
                                 restrictions: Dict[str, Any],
                                 context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        transaction_type = transaction_params.get("transaction_type", "")
        if not transaction_type:
            return {
                "passed": False,
                "message": "Missing transaction_type parameter"
            }
            
        # Print debug info
        print(f"[Compliance Debug] Checking parameters for {transaction_type} transaction")
        print(f"[Compliance Debug] Parameters: {transaction_params}")
        print(f"[Compliance Debug] Restrictions: {restrictions}")
        
        # 1. Check coin restrictions
        try:
            restricted_result = _check_restricted_coins(transaction_params, restrictions)
            if not restricted_result["passed"]:
                return restricted_result
        except Exception as e:
            print(f"[Compliance Error] Coin restriction check failed: {str(e)}")
            return {
                "passed": False,
                "error": str(e),
                "message": f"Error checking coin restrictions: {str(e)}"
            }
        
        # 2. Check trade type restrictions (for spot trades)
        if transaction_type == "SPOT":
            try:
                trade_type_result = _check_trade_type_restrictions(transaction_params, restrictions)
                if not trade_type_result["passed"]:
                    return trade_type_result
            except Exception as e:
                print(f"[Compliance Error] Trade type check failed: {str(e)}")
                return {
                    "passed": False,
                    "error": str(e),
                    "message": f"Error checking trade type: {str(e)}"
                }
        
        # 3. Check amount limits
        try:
            amount_result = _check_amount_limits(transaction_params, restrictions)
            if not amount_result["passed"]:
                return amount_result
        except Exception as e:
            print(f"[Compliance Error] Amount limits check failed: {str(e)}")
            return {
                "passed": False,
                "error": str(e),
                "message": f"Error checking amount limits: {str(e)}"
            }
        
        # All parameter checks passed
        return {
            "passed": True,
            "message": "Transaction parameters are valid"
        }
        
    except Exception as e:
        print(f"[Compliance Error] Transaction parameter check failed: {str(e)}")
        return {
            "passed": False,
            "error": str(e),
            "message": f"Unable to verify transaction parameters: {str(e)}"
        }


def _check_restricted_coins(transaction_params: Dict[str, Any], 
                          restrictions: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the transaction involves restricted coins"""
    restricted_coins = restrictions.get("restricted_coins", [])
    transaction_type = transaction_params.get("transaction_type", "")
    
    # Identify coins involved in the transaction
    coins_to_check = []
    
    if transaction_type == "SPOT":
        symbol = transaction_params.get("symbol", "")
        if "USDT" in symbol:
            coin = symbol.replace("USDT", "")
            coins_to_check.append(coin)
        else:
            coins_to_check.append(symbol)
    elif transaction_type == "CONVERT":
        from_asset = transaction_params.get("from_asset", "")
        to_asset = transaction_params.get("to_asset", "")
        coins_to_check.extend([from_asset, to_asset])
    
    # Check if any coin is restricted
    for coin in coins_to_check:
        if coin in restricted_coins:
            # Get alternative if available
            alternatives = restrictions.get("alternatives", {}).get("coins", {})
            suggestion = alternatives.get(coin)
            
            return {
                "passed": False,
                "coin": coin,
                "message": f"Trading {coin} is restricted in your region",
                "suggestion": suggestion
            }
    
    return {
        "passed": True,
        "message": "No restricted coins involved"
    }


def _check_trade_type_restrictions(transaction_params: Dict[str, Any], 
                                 restrictions: Dict[str, Any]) -> Dict[str, Any]:
    """Check if the trade type is restricted"""
    restricted_types = restrictions.get("restricted_trade_types", [])
    order_type = transaction_params.get("order_type", "LIMIT").upper()
    
    if order_type in restricted_types:
        # Get alternative if available
        alternatives = restrictions.get("alternatives", {}).get("trade_types", {})
        suggestion = alternatives.get(order_type)
        
        return {
            "passed": False,
            "order_type": order_type,
            "message": f"{order_type} orders are restricted in your region",
            "suggestion": suggestion
        }
    
    return {
        "passed": True,
        "message": "Trade type is allowed"
    }


def _check_amount_limits(transaction_params: Dict[str, Any], 
                        restrictions: Dict[str, Any]) -> Dict[str, Any]:
    """Check if transaction amount is within limits"""
    # Get amount from transaction
    amount = 0.0
    
    # Debug
    print(f"[Compliance Debug] Checking amount limits with params: {transaction_params}")
    
    # Case 1: Direct amount provided
    if "amount" in transaction_params and transaction_params["amount"]:
        try:
            amount_str = str(transaction_params["amount"]).strip()
            if amount_str:
                amount = float(amount_str)
                print(f"[Compliance Debug] Using direct amount: {amount}")
        except (ValueError, TypeError) as e:
            print(f"[Compliance Error] Invalid amount format: {transaction_params['amount']}, error: {str(e)}")
            return {
                "passed": False,
                "message": f"Invalid amount format: {transaction_params['amount']}"
            }
    
    # Case 2: Calculate from quantity * price
    elif ("quantity" in transaction_params and transaction_params["quantity"] and
          "price" in transaction_params and transaction_params["price"]):
        try:
            quantity_str = str(transaction_params["quantity"]).strip()
            price_str = str(transaction_params["price"]).strip()
            
            if quantity_str and price_str:
                quantity = float(quantity_str)
                price = float(price_str)
                amount = quantity * price
                print(f"[Compliance Debug] Calculated amount: {quantity} * {price} = {amount}")
        except (ValueError, TypeError) as e:
            print(f"[Compliance Error] Invalid quantity/price format: quantity={transaction_params['quantity']}, "
                  f"price={transaction_params['price']}, error: {str(e)}")
            return {
                "passed": False,
                "message": f"Invalid quantity or price format: quantity={transaction_params['quantity']}, price={transaction_params['price']}"
            }
    
    # No valid amount could be determined
    if amount <= 0:
        print("[Compliance Error] Could not determine transaction amount")
        return {
            "passed": False,
            "message": "Could not determine transaction amount. Please provide valid amount or quantity/price values."
        }
    
    # Check against max amount
    max_amount = restrictions.get("max_transaction_amount", float('inf'))
    min_amount = restrictions.get("min_transaction_amount", 0.0)
    
    if amount > max_amount:
        return {
            "passed": False,
            "amount": amount,
            "limit": max_amount,
            "message": f"Transaction amount {amount} exceeds maximum limit {max_amount}"
        }
    
    if amount < min_amount:
        return {
            "passed": False,
            "amount": amount,
            "limit": min_amount,
            "message": f"Transaction amount {amount} is below minimum limit {min_amount}"
        }
    
    return {
        "passed": True,
        "message": "Transaction amount is within limits"
    }
