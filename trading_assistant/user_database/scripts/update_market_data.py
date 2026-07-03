"""
Update market data in Firestore
This script can be run periodically to simulate changing market conditions
"""
import json
import argparse
import random
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firestore():
    """Initialize Firestore connection using Application Default Credentials"""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir.parent / "config/firebase_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Firebase configuration file doesn't exist: {config_path}")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Get project ID from config
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or config.get("project_id")
    
    # Get database ID from config
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
    db = firestore.client()
    
    # Check if we need to specify a database_id for the Firestore operations
    try:
        # Try using the database_id directly
        db = firestore.client(database_id=database_id)
    except TypeError:
        # If that fails, create a regular client and print a warning
        db = firestore.client()
        print(f"Warning: Using default database instead of {database_id}")
    
    return db

def update_market_prices(db, variation_percent=2.0):
    """Update market prices with random variations"""
    # Get current prices
    prices_doc = db.collection("market_data").document("prices").get()
    if not prices_doc.exists:
        print("Market prices document doesn't exist in Firestore")
        return
    
    prices_data = prices_doc.to_dict()
    current_prices = prices_data.get("prices", {})
    
    # Generate new prices with random variations
    new_prices = {}
    for symbol, data in current_prices.items():
        current_price = float(data["price"])
        # Random variation between -variation_percent% and +variation_percent%
        variation = random.uniform(-variation_percent, variation_percent) / 100
        new_price = current_price * (1 + variation)
        
        # Random 24h change
        change_24h = random.uniform(-5.0, 5.0)
        
        # Random volume
        volume = float(data["volume"]) * random.uniform(0.8, 1.2)
        
        new_prices[symbol] = {
            "price": str(round(new_price, 8 if new_price < 0.1 else 2)),
            "change_24h": str(round(change_24h, 1)),
            "volume": str(round(volume, 2))
        }
    
    # Update the prices document
    db.collection("market_data").document("prices").update({
        "last_updated": datetime.now().isoformat(),
        "prices": new_prices
    })
    
    print(f"Updated market prices with {variation_percent}% variation")
    return new_prices

def update_exchange_rates(db, prices):
    """Update exchange rates based on price changes"""
    # Get current exchange rates
    rates_doc = db.collection("market_data").document("exchange_rates").get()
    if not rates_doc.exists:
        print("Exchange rates document doesn't exist in Firestore")
        return
    
    # Extract current prices from the updated price data
    current_prices = {}
    for symbol, data in prices.items():
        asset = symbol[:-4]  # Remove "USDT"
        current_prices[asset] = float(data["price"])
    
    # Calculate new exchange rates
    new_rates = {}
    main_assets = ["BTC", "ETH", "BNB"]
    for base in main_assets:
        for quote in main_assets:
            if base != quote and base in current_prices and quote in current_prices:
                rate = current_prices[base] / current_prices[quote]
                new_rates[f"{base}_{quote}"] = str(round(rate, 4))
    
    # Update the exchange rates document
    db.collection("market_data").document("exchange_rates").update({
        "last_updated": datetime.now().isoformat(),
        "rates": new_rates
    })
    
    print("Updated exchange rates")

def main():
    """Update market data in Firestore"""
    parser = argparse.ArgumentParser(description="Update market data in Firestore")
    parser.add_argument("--variation", type=float, default=2.0, 
                       help="Maximum price variation percentage (default: 2.0)")
    
    args = parser.parse_args()
    
    try:
        db = initialize_firestore()
        new_prices = update_market_prices(db, args.variation)
        if new_prices:
            update_exchange_rates(db, new_prices)
        print("Market data update completed")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    import os
    main()
