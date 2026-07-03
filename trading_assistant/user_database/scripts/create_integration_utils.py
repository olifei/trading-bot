"""
Generate utility code for integrating Firestore with the trading bot mock APIs
"""
import os
from pathlib import Path

# Create the integration directory
integration_dir = Path("../integration")
os.makedirs(integration_dir, exist_ok=True)

# Create the firestore_client.py file
firestore_client_path = integration_dir / "firestore_client.py"
firestore_client_content = """
\"\"\"
Firestore client utilities for the trading bot
\"\"\"
import firebase_admin
from firebase_admin import credentials, firestore
import json
from pathlib import Path
import os

# Singleton to ensure we only initialize Firebase once
_db = None

def get_firestore_client():
    \"\"\"Get a Firestore client instance, initializing it if necessary\"\"\"
    global _db
    if _db is not None:
        return _db
        
    # Load configuration
    config_path = Path(__file__).resolve().parent.parent / "user_database/config/firebase_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Firebase configuration file doesn't exist: {config_path}")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Get project ID and database ID (env-first, config file as fallback)
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or config.get("project_id")
    database_id = os.environ.get("FIRESTORE_DATABASE_ID") or config.get("database_id")
    
    # Initialize Firebase with Application Default Credentials
    try:
        # Check if Firebase app is already initialized
        app = firebase_admin.get_app()
    except ValueError:
        # Initialize with ADC
        app = firebase_admin.initialize_app(options={
            'projectId': project_id,
        })
    
    # Create a client with the specific database
    _db = firestore.client(database_id=database_id)
    return _db
"""

with open(firestore_client_path, "w") as f:
    f.write(firestore_client_content)

# Create the portfolio_api.py example integration file
portfolio_api_path = integration_dir / "portfolio_api_example.py"
portfolio_api_content = """
\"\"\"
Example integration of the portfolio API with Firestore
\"\"\"
from integration.firestore_client import get_firestore_client

def get_user_portfolio(user_id):
    \"\"\"
    Retrieve a user's cryptocurrency portfolio from Firestore
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A dictionary containing the user's portfolio information
    \"\"\"
    # Get Firestore client
    db = get_firestore_client()
    
    # Retrieve portfolio document
    portfolio_doc = db.collection("portfolios").document(user_id).get()
    
    # Check if portfolio exists
    if not portfolio_doc.exists:
        # Return empty portfolio if not found
        return {
            "balances": [],
            "total_value_usdt": "0.00"
        }
    
    # Get portfolio data
    portfolio_data = portfolio_doc.to_dict()
    
    # Format portfolio for the trading bot API
    formatted_portfolio = {
        "balances": [],
        "total_value_usdt": portfolio_data.get("total_balance_usdt", "0.00")
    }
    
    # Format assets
    for asset, details in portfolio_data.get("assets", {}).items():
        formatted_portfolio["balances"].append({
            "asset": asset,
            "free": details.get("free", "0.00"),
            "locked": details.get("locked", "0.00")
        })
    
    return formatted_portfolio
"""

with open(portfolio_api_path, "w") as f:
    f.write(portfolio_api_content)

# Create the market_api.py example integration file
market_api_path = integration_dir / "market_api_example.py"
market_api_content = """
\"\"\"
Example integration of the market API with Firestore
\"\"\"
from integration.firestore_client import get_firestore_client

def get_market_price(symbol):
    \"\"\"
    Retrieve the current market price for a cryptocurrency from Firestore
    
    Args:
        symbol: The trading pair symbol (e.g., "BTC", "ETH", "BTCUSDT")
        
    Returns:
        A dictionary containing price information
    \"\"\"
    # Get Firestore client
    db = get_firestore_client()
    
    # Clean up the symbol
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
    
    # Retrieve market data document
    prices_doc = db.collection("market_data").document("prices").get()
    
    # Check if document exists
    if not prices_doc.exists:
        return {"error": "Market data not found"}
    
    # Get prices data
    prices_data = prices_doc.to_dict()
    all_prices = prices_data.get("prices", {})
    
    # Check if symbol exists
    if symbol not in all_prices:
        return {"error": f"Symbol {symbol} not found"}
    
    # Format price data for the trading bot API
    price_data = all_prices[symbol]
    return {
        "symbol": symbol,
        "price": price_data.get("price", "0.00"),
        "change_24h": price_data.get("change_24h", "0.00"),
        "volume": price_data.get("volume", "0.00"),
        "last_updated": prices_data.get("last_updated")
    }

def get_conversion_rate(from_asset, to_asset):
    \"\"\"
    Retrieve the exchange rate between two cryptocurrencies from Firestore
    
    Args:
        from_asset: The source cryptocurrency (e.g., "BTC")
        to_asset: The target cryptocurrency (e.g., "ETH")
        
    Returns:
        A dictionary containing conversion rate information
    \"\"\"
    # Get Firestore client
    db = get_firestore_client()
    
    # Clean up the assets
    from_asset = from_asset.upper()
    to_asset = to_asset.upper()
    
    # Direct rate lookup
    rate_key = f"{from_asset}_{to_asset}"
    
    # Retrieve exchange rates document
    rates_doc = db.collection("market_data").document("exchange_rates").get()
    
    # Check if document exists
    if not rates_doc.exists:
        return {"error": "Exchange rates not found"}
    
    # Get rates data
    rates_data = rates_doc.to_dict()
    all_rates = rates_data.get("rates", {})
    
    # Check if direct rate exists
    if rate_key in all_rates:
        return {
            "from_asset": from_asset,
            "to_asset": to_asset,
            "rate": all_rates[rate_key],
            "last_updated": rates_data.get("last_updated")
        }
    
    # Try inverse rate
    inverse_key = f"{to_asset}_{from_asset}"
    if inverse_key in all_rates:
        inverse_rate = float(all_rates[inverse_key])
        if inverse_rate == 0:
            return {"error": f"Invalid conversion rate for {from_asset}-{to_asset}"}
        
        direct_rate = 1.0 / inverse_rate
        return {
            "from_asset": from_asset,
            "to_asset": to_asset,
            "rate": str(round(direct_rate, 8)),
            "last_updated": rates_data.get("last_updated")
        }
    
    # If no direct or inverse rate, calculate via USDT
    # Get prices from market data
    prices_doc = db.collection("market_data").document("prices").get()
    if not prices_doc.exists:
        return {"error": "Market prices not found"}
    
    prices_data = prices_doc.to_dict()
    all_prices = prices_data.get("prices", {})
    
    # Get price in USDT for both assets
    from_symbol = f"{from_asset}USDT"
    to_symbol = f"{to_asset}USDT"
    
    if from_symbol not in all_prices or to_symbol not in all_prices:
        return {"error": f"Price data not available for {from_asset} or {to_asset}"}
    
    from_price = float(all_prices[from_symbol]["price"])
    to_price = float(all_prices[to_symbol]["price"])
    
    if to_price == 0:
        return {"error": f"Invalid price for {to_asset}"}
    
    # Calculate rate
    calculated_rate = from_price / to_price
    
    return {
        "from_asset": from_asset,
        "to_asset": to_asset,
        "rate": str(round(calculated_rate, 8)),
        "last_updated": prices_data.get("last_updated"),
        "note": "Rate calculated via USDT prices"
    }
"""

with open(market_api_path, "w") as f:
    f.write(market_api_content)

# Create the trading_api.py example integration file
trading_api_path = integration_dir / "trading_api_example.py"
trading_api_content = """
\"\"\"
Example integration of the trading API with Firestore
\"\"\"
import uuid
from datetime import datetime
from integration.firestore_client import get_firestore_client

def create_spot_order(user_id, symbol, side, order_type="LIMIT", quantity=None, price=None, amount=None):
    \"\"\"
    Create a spot trading order and save it to Firestore
    
    Args:
        user_id: The ID of the user
        symbol: The trading pair symbol (e.g., "BTCUSDT")
        side: "BUY" or "SELL"
        order_type: "LIMIT" or "MARKET"
        quantity: Amount of the base asset to trade
        price: Limit price (required for LIMIT orders)
        amount: Total value in USDT (alternative to quantity)
        
    Returns:
        A dictionary containing the order details
    \"\"\"
    # Get Firestore client
    db = get_firestore_client()
    
    # Generate a unique order ID
    order_id = f"ord-{uuid.uuid4().hex[:8]}"
    transaction_id = f"tx-{uuid.uuid4().hex[:8]}"
    
    # Clean up symbol
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
    
    # Extract base asset
    base_asset = symbol[:-4]
    
    # Prepare order data
    now = datetime.now().isoformat()
    
    # Calculate amount if quantity is provided, or vice versa
    if price is None:
        # For market orders, get current price
        prices_doc = db.collection("market_data").document("prices").get()
        if prices_doc.exists:
            prices_data = prices_doc.to_dict()
            price_data = prices_data.get("prices", {}).get(symbol, {})
            price = price_data.get("price", "0.00")
        else:
            price = "0.00"
    
    # Convert price to float for calculations
    price_float = float(price)
    
    if quantity is not None:
        quantity_float = float(quantity)
        amount = str(round(quantity_float * price_float, 2))
    elif amount is not None:
        amount_float = float(amount)
        quantity = str(round(amount_float / price_float, 8)) if price_float > 0 else "0.00"
    else:
        # Both quantity and amount are missing
        return {"error": "Either quantity or amount must be provided"}
    
    # Create order document
    order_data = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "amount": amount,
        "status": "FILLED",  # Mock API always fills orders immediately
        "order_id": order_id,
        "created_at": now,
        "updated_at": now
    }
    
    # Create transaction document
    transaction_data = {
        "user_id": user_id,
        "type": "spot",
        "status": "completed",
        "created_at": now,
        "updated_at": now,
        "order": order_data
    }
    
    # Save transaction to Firestore
    db.collection("transactions").document(transaction_id).set(transaction_data)
    
    # Update user's portfolio
    portfolio_ref = db.collection("portfolios").document(user_id)
    portfolio_doc = portfolio_ref.get()
    
    if portfolio_doc.exists:
        portfolio_data = portfolio_doc.to_dict()
        assets = portfolio_data.get("assets", {})
        
        if side == "BUY":
            # Update base asset (increase)
            base_asset_data = assets.get(base_asset, {
                "free": "0.00",
                "locked": "0.00",
                "total": "0.00",
                "value_usdt": "0.00"
            })
            current_free = float(base_asset_data.get("free", "0.00"))
            new_free = current_free + float(quantity)
            base_asset_data["free"] = str(round(new_free, 8))
            base_asset_data["total"] = str(round(new_free + float(base_asset_data.get("locked", "0.00")), 8))
            base_asset_data["value_usdt"] = str(round(new_free * price_float, 2))
            assets[base_asset] = base_asset_data
            
            # Update USDT (decrease)
            usdt_data = assets.get("USDT", {
                "free": "0.00",
                "locked": "0.00",
                "total": "0.00",
                "value_usdt": "0.00"
            })
            current_free = float(usdt_data.get("free", "0.00"))
            new_free = max(0, current_free - float(amount))
            usdt_data["free"] = str(round(new_free, 2))
            usdt_data["total"] = str(round(new_free + float(usdt_data.get("locked", "0.00")), 2))
            usdt_data["value_usdt"] = usdt_data["free"]
            assets["USDT"] = usdt_data
            
        elif side == "SELL":
            # Update base asset (decrease)
            base_asset_data = assets.get(base_asset, {
                "free": "0.00",
                "locked": "0.00",
                "total": "0.00",
                "value_usdt": "0.00"
            })
            current_free = float(base_asset_data.get("free", "0.00"))
            new_free = max(0, current_free - float(quantity))
            base_asset_data["free"] = str(round(new_free, 8))
            base_asset_data["total"] = str(round(new_free + float(base_asset_data.get("locked", "0.00")), 8))
            base_asset_data["value_usdt"] = str(round(new_free * price_float, 2))
            assets[base_asset] = base_asset_data
            
            # Update USDT (increase)
            usdt_data = assets.get("USDT", {
                "free": "0.00",
                "locked": "0.00",
                "total": "0.00",
                "value_usdt": "0.00"
            })
            current_free = float(usdt_data.get("free", "0.00"))
            new_free = current_free + float(amount)
            usdt_data["free"] = str(round(new_free, 2))
            usdt_data["total"] = str(round(new_free + float(usdt_data.get("locked", "0.00")), 2))
            usdt_data["value_usdt"] = usdt_data["free"]
            assets["USDT"] = usdt_data
        
        # Update portfolio assets
        portfolio_data["assets"] = assets
        
        # Calculate total value
        total_value = 0
        for asset_data in assets.values():
            total_value += float(asset_data.get("value_usdt", "0.00"))
        
        portfolio_data["total_balance_usdt"] = str(round(total_value, 2))
        portfolio_data["last_updated"] = now
        
        # Update portfolio in Firestore
        portfolio_ref.set(portfolio_data)
    else:
        # Create new portfolio if it doesn't exist
        portfolio_data = {
            "total_balance_usdt": "0.00",
            "last_updated": now,
            "assets": {}
        }
        portfolio_ref.set(portfolio_data)
    
    return order_data

def get_order_status(user_id, order_id):
    \"\"\"
    Get the status of an order from Firestore
    
    Args:
        user_id: The ID of the user
        order_id: The ID of the order
        
    Returns:
        A dictionary containing the order status
    \"\"\"
    # Get Firestore client
    db = get_firestore_client()
    
    # Query transactions to find the order
    query = db.collection("transactions").where("user_id", "==", user_id).where("order.order_id", "==", order_id)
    results = query.get()
    
    for doc in results:
        transaction_data = doc.to_dict()
        # Return the order data if found
        if "order" in transaction_data:
            return transaction_data["order"]
    
    # Return error if order not found
    return {"error": f"Order {order_id} not found for user {user_id}"}
"""

with open(trading_api_path, "w") as f:
    f.write(trading_api_content)

# Create the README.md file for integration instructions
readme_path = integration_dir / "README.md"
readme_content = """# Firestore Integration for Trading Bot

This directory contains utility code and examples for integrating the trading bot with Firestore.

## Setup

1. Make sure the Firestore database is set up and data has been uploaded:
   ```bash
   cd user_database
   python scripts/check_database.py
   python scripts/upload_data.py --all
   ```

2. Install required dependencies:
   ```bash
   pip install firebase-admin google-cloud-firestore
   ```

3. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project YOUR_GCP_PROJECT_ID
   ```

## Integration Steps

To integrate the trading bot with Firestore, you need to modify the mock API files to use the Firestore database instead of hardcoded data:

1. **Copy the Firestore client** (`firestore_client.py`) to your project.

2. **Modify the service API files** to use Firestore:
   - `services/portfolio/portfolio_api.py` - See `portfolio_api_example.py` for reference
   - `services/market/market_api.py` - See `market_api_example.py` for reference
   - `services/trading/trading_api.py` - See `trading_api_example.py` for reference

3. **Test the integration**:
   - Run the web UI: `python web.py`
   - Test various operations: fetch portfolio, get market data, execute a trade

## Example Integration

Here's a simplified example of how to replace a hardcoded function with Firestore:

**Original code (hardcoded):**
```python
def get_user_portfolio(user_id):
    # Mock data
    return {
        "balances": [
            {"asset": "BTC", "free": "0.5", "locked": "0.0"},
            {"asset": "ETH", "free": "10.0", "locked": "0.0"},
            {"asset": "USDT", "free": "1000.0", "locked": "0.0"}
        ]
    }
```

**New code (Firestore):**
```python
from integration.firestore_client import get_firestore_client

def get_user_portfolio(user_id):
    # Get Firestore client
    db = get_firestore_client()
    
    # Retrieve portfolio document
    portfolio_doc = db.collection("portfolios").document(user_id).get()
    
    # Format portfolio for the trading bot API
    formatted_portfolio = {"balances": []}
    
    if portfolio_doc.exists:
        portfolio_data = portfolio_doc.to_dict()
        for asset, details in portfolio_data.get("assets", {}).items():
            formatted_portfolio["balances"].append({
                "asset": asset,
                "free": details.get("free", "0.00"),
                "locked": details.get("locked", "0.00")
            })
    
    return formatted_portfolio
```

## Benefits

- **Real Data Persistence**: Changes to user portfolios and market data persist between sessions
- **Dynamic Updates**: Market data can be updated using the `update_market_data.py` script
- **Realistic Demo**: The trading bot will behave more like a real application
"""

with open(readme_path, "w") as f:
    f.write(readme_content)

print(f"Generated integration files in {integration_dir.resolve()} directory")
print("These files provide examples of how to integrate the trading bot with Firestore")
print("See the README.md file for detailed instructions")
