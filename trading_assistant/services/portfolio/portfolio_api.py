from datetime import datetime
from trading_assistant.services.database.firestore_client import get_firestore_client

def get_user_portfolio(user_id: str) -> dict:
    # print(f"[Portfolio API] Getting portfolio for user {user_id}")
    try:
        db = get_firestore_client()
        portfolio_doc = db.collection("portfolios").document(user_id).get()
        
        if not portfolio_doc.exists:
            return {
                "balances": [
                    {"asset": "USDT", "free": "0.0", "locked": "0.0"},
                ],
                "last_updated": None
            }
        
        portfolio_data = portfolio_doc.to_dict()
        formatted_portfolio = {
            "balances": [],
            "last_updated": portfolio_data.get("last_updated")
        }
        
        for asset, details in portfolio_data.get("assets", {}).items():
            formatted_portfolio["balances"].append({
                "asset": asset,
                "free": details.get("free", "0.0"),
                "locked": details.get("locked", "0.0")
            })
        
        return formatted_portfolio
        
    except Exception as e:
        print(f"[Portfolio API Error] {str(e)}")
        return {
            "balances": [
                {"asset": "USDT", "free": "0.0", "locked": "0.0"},
            ],
            "last_updated": None,
            "error": str(e)
        }

def update_user_balance(user_id: str, transactions: list) -> dict:
    # print(f"[Portfolio API] Updating portfolio for user {user_id}")
    try:
        db = get_firestore_client()
        portfolio_ref = db.collection("portfolios").document(user_id)
        portfolio_doc = portfolio_ref.get()
        
        if portfolio_doc.exists:
            portfolio_data = portfolio_doc.to_dict()
            assets = portfolio_data.get("assets", {})
        else:
            portfolio_data = {
                "total_balance_usdt": "0.0",
                "assets": {},
                "last_updated": datetime.now().isoformat()
            }
            assets = {}
        
        balances = {}
        for asset, details in assets.items():
            balances[asset] = float(details.get("free", "0.0"))
        
        for transaction in transactions:
            asset = transaction["asset"]
            amount = float(transaction["amount"])
            
            if asset in balances:
                balances[asset] += amount
            else:
                balances[asset] = amount
        
        now = datetime.now().isoformat()
        for asset, amount in balances.items():
            if asset not in assets:
                assets[asset] = {
                    "free": "0.0",
                    "locked": "0.0",
                    "total": "0.0",
                    "value_usdt": "0.0"
                }
            
            assets[asset]["free"] = str(max(0, amount))  # Ensure no negative balances
            assets[asset]["total"] = str(max(0, amount + float(assets[asset].get("locked", "0.0"))))
        
        # Update portfolio in Firestore
        portfolio_data["assets"] = assets
        portfolio_data["last_updated"] = now
        
        # Calculate total balance in USDT
        try:
            # Try to get market prices to calculate USDT value
            prices_doc = db.collection("market_data").document("prices").get()
            if prices_doc.exists:
                prices_data = prices_doc.to_dict()
                all_prices = prices_data.get("prices", {})
                
                total_value = 0
                for asset, details in assets.items():
                    amount = float(details["free"]) + float(details.get("locked", "0.0"))
                    if asset == "USDT":
                        price = 1.0
                    else:
                        symbol = f"{asset}USDT"
                        if symbol in all_prices:
                            price = float(all_prices[symbol].get("price", "0.0"))
                        else:
                            price = 0.0
                    
                    value = amount * price
                    assets[asset]["value_usdt"] = str(round(value, 2))
                    total_value += value
                
                portfolio_data["total_balance_usdt"] = str(round(total_value, 2))
            
        except Exception as price_error:
            print(f"[Portfolio API Warning] Error calculating USDT values: {str(price_error)}")
        
        # Save to Firestore
        portfolio_ref.set(portfolio_data)
        
        # Format response for the API
        updated_balances = []
        for asset, details in assets.items():
            updated_balances.append({
                "asset": asset,
                "free": details.get("free", "0.0"),
                "locked": details.get("locked", "0.0")
            })
        
        # Create updated portfolio in the expected format
        updated_portfolio = {
            "balances": updated_balances,
            "last_updated": now
        }
        
        return updated_portfolio
        
    except Exception as e:
        print(f"[Portfolio API Error] {str(e)}")
        # Return current portfolio on error
        return get_user_portfolio(user_id)
