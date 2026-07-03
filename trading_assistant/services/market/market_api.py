import time
from trading_assistant.services.database.firestore_client import get_firestore_client

def get_market_price(symbol: str) -> dict:
    # print(f"[Market API] Getting price for symbol {symbol}")
    symbol = symbol.upper()
    if not symbol.endswith("USDT") and symbol != "":
        symbol = f"{symbol}USDT"
    
    try:
        db = get_firestore_client()
        prices_doc = db.collection("market_data").document("prices").get()
        
        if not prices_doc.exists:
            return {
                "symbol": symbol,
                "price": "0.00",
                "time": int(time.time() * 1000),
                "error": "Market data not found"
            }
        
        prices_data = prices_doc.to_dict()
        all_prices = prices_data.get("prices", {})
        
        if symbol in all_prices:
            price_data = all_prices[symbol]
            return {
                "symbol": symbol,
                "price": price_data.get("price", "0.00"),
                "time": int(time.time() * 1000)
            }
        
        return {
            "symbol": symbol,
            "price": "0.00",
            "time": int(time.time() * 1000),
            "error": "Symbol not found"
        }
    except Exception as e:
        print(f"[Market API Error] {str(e)}")
        return {
            "symbol": symbol,
            "price": "0.00",
            "time": int(time.time() * 1000),
            "error": str(e)
        }

def get_conversion_rate(from_asset: str, to_asset: str) -> dict:
    # print(f"[Market API] Getting conversion rate from {from_asset} to {to_asset}")
    try:
        db = get_firestore_client()
        from_asset = from_asset.upper()
        to_asset = to_asset.upper()
        
        if from_asset == "USDT" or to_asset == "USDT":
            return {
                "from_asset": from_asset, 
                "to_asset": to_asset,
                "rate": "0.00",
                "time": int(time.time() * 1000),
                "error": f"You want to convert {to_asset} from {from_asset}. It's not a conversion rate request, should use get price instead."
            }
        else:
            rate_key = f"{from_asset}_{to_asset}"
            rates_doc = db.collection("market_data").document("exchange_rates").get()
            if rates_doc.exists:
                rates_data = rates_doc.to_dict()
                all_rates = rates_data.get("rates", {})
                
                if rate_key in all_rates:
                    return {
                        "from_asset": from_asset,
                        "to_asset": to_asset,
                        "rate": all_rates[rate_key],
                        "time": int(time.time() * 1000)
                    }
                    
                # Try inverse rate
                inverse_key = f"{to_asset}_{from_asset}"
                if inverse_key in all_rates:
                    inverse_rate = float(all_rates[inverse_key])
                    if inverse_rate == 0:
                        return {
                            "from_asset": from_asset,
                            "to_asset": to_asset,
                            "rate": "0.00",
                            "time": int(time.time() * 1000),
                            "error": f"Invalid conversion rate for {from_asset}-{to_asset}"
                        }
                    
                    direct_rate = 1.0 / inverse_rate
                    return {
                        "from_asset": from_asset,
                        "to_asset": to_asset,
                        "rate": str(round(direct_rate, 8)),
                        "time": int(time.time() * 1000)
                    }
            
            # If we can't find a direct rate, calculate via USDT
            prices_doc = db.collection("market_data").document("prices").get()
            if not prices_doc.exists:
                return {
                    "from_asset": from_asset,
                    "to_asset": to_asset,
                    "rate": "0.00",
                    "time": int(time.time() * 1000),
                    "error": "Market data not found"
                }
                
            prices_data = prices_doc.to_dict()
            all_prices = prices_data.get("prices", {})
            
            from_symbol = f"{from_asset}USDT"
            to_symbol = f"{to_asset}USDT"
            
            if from_symbol not in all_prices or to_symbol not in all_prices:
                return {
                    "from_asset": from_asset,
                    "to_asset": to_asset,
                    "rate": "0.00",
                    "time": int(time.time() * 1000),
                    "error": f"Price data not available for {from_asset} or {to_asset}"
                }
            
            from_price = float(all_prices[from_symbol].get("price", "0.00"))
            to_price = float(all_prices[to_symbol].get("price", "0.00"))
            
            # Calculate rate (handle division by zero)
            if to_price == 0:
                rate = 0
            else:
                rate = from_price / to_price
        
        return {
            "from_asset": from_asset,
            "to_asset": to_asset,
            "rate": str(rate),
            "time": int(time.time() * 1000)
        }
        
    except Exception as e:
        print(f"[Market API Error] {str(e)}")
        return {
            "from_asset": from_asset,
            "to_asset": to_asset,
            "rate": "0.00",
            "time": int(time.time() * 1000),
            "error": str(e)
        }
