"""
Generate mock data for Trading Bot demo
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

script_dir = Path(__file__).resolve().parent
output_dir = script_dir.parent / "outputs"
output_dir.mkdir(exist_ok=True)

def generate_users(count=5):
    """Generate mock user data"""
    users = {}
    regions = ["CN", "US", "EU", "SG", "JP"]
    kyc_statuses = ["pending", "verified", "rejected"]
    kyc_levels = ["none", "level_1", "level_2", "level_3"]
    
    for i in range(count):
        user_id = f"user{i+1}"
        
        # Randomly decide KYC status
        kyc_status = random.choice(kyc_statuses)
        
        users[user_id] = {
            "profile": {
                "name": f"User {i+1}",
                "email": f"user{i+1}@example.com",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "last_login": datetime.now().isoformat()
            },
            "compliance": {
                "kyc_verified_at": datetime.now().isoformat() if kyc_status == "verified" else None,
                "region": random.choice(regions),
                "kyc_verified": kyc_status == "verified"
            },
            "preferences": {
                "language": random.choice(["en", "zh", "ja", "ko"]),
                # "notification_enabled": random.choice([True, False]),
                "default_fiat": "USDT"
            }
        }
    
    return users

def generate_portfolios(users):
    """Generate asset portfolios based on users"""
    portfolios = {}
    assets = ["BTC", "ETH", "BNB", "SOL", "ADA", "USDT"]
    prices = {
        "BTC": 17020.50,
        "ETH": 1258.50,
        "BNB": 312.75,
        "SOL": 43.25,
        "ADA": 0.385,
        "USDT": 1.0
    }
    
    for user_id in users:
        # # Only generate portfolios for verified users
        # if users[user_id]["compliance"]["kyc_status"] != "verified":
        #     continue
            
        user_assets = {}
        total_value = 0
        
        # Randomly assign assets to each user
        for asset in assets:
            if random.random() > 0.5 or asset == "USDT":  # Ensure every user has USDT
                free_amount = round(random.uniform(0, 2 if asset == "BTC" else 20 if asset == "ETH" else 1000), 6)
                locked_amount = 0  # Simplify with no locked amounts for now
                
                if free_amount > 0:
                    value_usdt = free_amount * prices[asset]
                    total_value += value_usdt
                    
                    user_assets[asset] = {
                        "free": str(free_amount),
                        "locked": str(locked_amount),
                        "total": str(free_amount + locked_amount),
                        "value_usdt": str(round(value_usdt, 2))
                    }
        
        portfolios[user_id] = {
            "total_balance_usdt": str(round(total_value, 2)),
            "last_updated": datetime.now().isoformat(),
            "assets": user_assets
        }
    
    return portfolios

def generate_market_data():
    """Generate market price data"""
    assets = ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP", "DOT", "DOGE", "SHIB", "AVAX"]
    prices = {
        "BTC": 17020.50,
        "ETH": 1258.50,
        "BNB": 312.75,
        "SOL": 43.25,
        "ADA": 0.385,
        "XRP": 0.42,
        "DOT": 6.75,
        "DOGE": 0.085,
        "SHIB": 0.00001,
        "AVAX": 18.50,
    }
    
    # Generate price data
    price_data = {
        "last_updated": datetime.now().isoformat(),
        "prices": {}
    }
    
    for asset in assets:
        change = round(random.uniform(-5.0, 5.0), 1)
        volume = round(random.uniform(1000000, 50000000), 2)
        
        price_data["prices"][f"{asset}USDT"] = {
            "price": str(prices[asset]),
            "change_24h": str(change),
            "volume": str(volume)
        }
    
    # Generate exchange rates
    rate_data = {
        "last_updated": datetime.now().isoformat(),
        "rates": {}
    }
    
    # Calculate exchange rates between main assets
    main_assets = ["BTC", "ETH", "BNB"]
    for base in main_assets:
        for quote in main_assets:
            if base != quote:
                rate = prices[base] / prices[quote]
                rate_data["rates"][f"{base}_{quote}"] = str(round(rate, 4))
    
    return {
        "prices": price_data,
        "exchange_rates": rate_data
    }

def symbol_price(symbol):
    """Extract price from symbol"""
    base_prices = {
        "BTC": "17020.50",
        "ETH": "1258.50",
        "BNB": "312.75",
        "SOL": "43.25",
        "ADA": "0.385"
    }
    base = symbol[:-4]  # Remove USDT
    return base_prices.get(base, "100.00")

def generate_transactions(users, portfolios, count_per_user=5):
    """Generate transaction history"""
    transactions = {}
    transaction_types = ["spot", "convert"]
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]
    order_sides = ["BUY", "SELL"]
    order_types = ["LIMIT", "MARKET"]
    
    transaction_id = 1
    
    for user_id, portfolio in portfolios.items():
        # Skip users with no assets
        if not portfolio["assets"]:
            continue
            
        # Generate multiple transactions per user
        for _ in range(random.randint(1, count_per_user)):
            tx_id = f"tx{transaction_id}"
            tx_type = random.choice(transaction_types)
            created_at = (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            
            if tx_type == "spot":
                # Spot trading transaction
                symbol = random.choice(symbols)
                side = random.choice(order_sides)
                order_type = random.choice(order_types)
                base_asset = symbol[:-4]  # Remove USDT
                
                quantity = round(random.uniform(0.001, 0.1 if base_asset == "BTC" else 1), 6)
                price = float(symbol_price(symbol))
                amount = round(quantity * price, 2)
                
                transactions[tx_id] = {
                    "user_id": user_id,
                    "type": "spot",
                    "status": "completed",
                    "created_at": created_at,
                    "updated_at": (datetime.fromisoformat(created_at) + timedelta(minutes=random.randint(1, 10))).isoformat(),
                    "order": {
                        "symbol": symbol,
                        "side": side,
                        "order_type": order_type,
                        "quantity": str(quantity),
                        "price": str(price),
                        "amount": str(amount),
                        "order_id": f"ord{random.randint(100000, 999999)}"
                    }
                }
            else:
                # Currency conversion transaction
                available_assets = list(portfolio["assets"].keys())
                if len(available_assets) < 2 or "USDT" not in available_assets:
                    continue
                    
                available_assets.remove("USDT")
                if not available_assets:
                    continue
                    
                from_asset = random.choice(available_assets)
                to_assets = [a for a in available_assets if a != from_asset]
                if not to_assets:
                    to_assets = ["USDT"]
                to_asset = random.choice(to_assets)
                
                from_amount = round(random.uniform(0.001, float(portfolio["assets"][from_asset]["free"])), 6)
                rate = random.uniform(0.5, 2.0)
                to_amount = round(from_amount * rate, 6)
                
                transactions[tx_id] = {
                    "user_id": user_id,
                    "type": "convert",
                    "status": "completed",
                    "created_at": created_at,
                    "updated_at": (datetime.fromisoformat(created_at) + timedelta(minutes=random.randint(1, 5))).isoformat(),
                    "conversion": {
                        "from_asset": from_asset,
                        "to_asset": to_asset,
                        "from_amount": str(from_amount),
                        "to_amount": str(to_amount),
                        "rate": str(round(rate, 4)),
                        "conversion_id": f"cnv{random.randint(100000, 999999)}"
                    }
                }
                
            transaction_id += 1
    
    return transactions

def generate_compliance_rules():
    """Generate compliance rules"""
    return {
        "regions": {
            "US": {
                "restricted_coins": ["XRP", "LUNA"],
                "restricted_trade_types": ["MARGIN"],
                "max_transaction_amount": 10000,
                "alternatives": {
                    "coins": {
                        "XRP": "XLM",
                        "LUNA": "USDT"
                    },
                    "trade_types": {
                        "MARGIN": "SPOT"
                    }
                }
            },
            "CN": {
                "restricted_coins": ["ALL"],
                "restricted_trade_types": ["ALL"],
                "max_transaction_amount": 0,
                "alternatives": {}
            },
            "EU": {
                "restricted_coins": [],
                "restricted_trade_types": [],
                "max_transaction_amount": 20000,
                "alternatives": {}
            },
            "SG": {
                "restricted_coins": ["DOGE", "SHIB"],
                "restricted_trade_types": [],
                "max_transaction_amount": 5000,
                "alternatives": {
                    "coins": {
                        "DOGE": "BTC",
                        "SHIB": "ETH"
                    }
                }
            }
        }
    }

def main():
    """Generate all data and save to files"""
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Generate users
    users = generate_users(count=20)
    with open(output_dir / "generated_users.json", "w") as f:
        json.dump(users, f, indent=2)
    
    # Generate portfolios
    portfolios = generate_portfolios(users)
    with open(output_dir / "generated_portfolios.json", "w") as f:
        json.dump(portfolios, f, indent=2)
    
    # Generate market data
    market_data = generate_market_data()
    with open(output_dir / "generated_market_prices.json", "w") as f:
        json.dump(market_data["prices"], f, indent=2)
    with open(output_dir / "generated_exchange_rates.json", "w") as f:
        json.dump(market_data["exchange_rates"], f, indent=2)
    
    # Generate transactions
    transactions = generate_transactions(users, portfolios)
    with open(output_dir / "generated_transactions.json", "w") as f:
        json.dump(transactions, f, indent=2)
    
    # Generate compliance rules
    compliance_rules = generate_compliance_rules()
    with open(output_dir / "generated_compliance_rules.json", "w") as f:
        json.dump(compliance_rules, f, indent=2)
    
    print("Successfully generated all data, saved to the outputs directory")

if __name__ == "__main__":
    main()
