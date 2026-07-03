"""
Upload generated data to Firestore
"""
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
import os
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
    db = firestore.client()
    
    # Check if we need to specify a database_id for the Firestore operations
    # This would be used with google-cloud-firestore >= 2.0.0
    # For firebase_admin it might work differently
    # Let's try both approaches
    try:
        # Try using the database_id directly
        db = firestore.client(database_id=database_id)
    except TypeError:
        # If that fails, create a regular client and print a warning
        db = firestore.client()
        print(f"Warning: Using default database instead of {database_id}")
    
    return db
    

def upload_users(db, file_path):
    """Upload user data to Firestore"""
    with open(file_path, "r") as f:
        users = json.load(f)
    
    batch = db.batch()
    count = 0
    
    for user_id, user_data in users.items():
        ref = db.collection("users").document(user_id)
        batch.set(ref, user_data)
        count += 1
        
        # Firestore batch operations are limited to 500
        if count >= 450:
            batch.commit()
            batch = db.batch()
            count = 0
    
    if count > 0:
        batch.commit()
    
    print(f"Successfully uploaded {len(users)} user records")

def upload_portfolios(db, file_path):
    """Upload portfolio data to Firestore"""
    with open(file_path, "r") as f:
        portfolios = json.load(f)
    
    batch = db.batch()
    count = 0
    
    for user_id, portfolio_data in portfolios.items():
        ref = db.collection("portfolios").document(user_id)
        batch.set(ref, portfolio_data)
        count += 1
        
        if count >= 450:
            batch.commit()
            batch = db.batch()
            count = 0
    
    if count > 0:
        batch.commit()
    
    print(f"Successfully uploaded {len(portfolios)} portfolio records")

def upload_market_data(db, prices_path, rates_path):
    """Upload market data to Firestore"""
    # Upload price data
    with open(prices_path, "r") as f:
        prices = json.load(f)
    
    db.collection("market_data").document("prices").set(prices)
    
    # Upload exchange rates data
    with open(rates_path, "r") as f:
        rates = json.load(f)
    
    db.collection("market_data").document("exchange_rates").set(rates)
    
    print("Successfully uploaded market data")

def upload_transactions(db, file_path):
    """Upload transaction data to Firestore"""
    with open(file_path, "r") as f:
        transactions = json.load(f)
    
    batch = db.batch()
    count = 0
    
    for tx_id, tx_data in transactions.items():
        ref = db.collection("transactions").document(tx_id)
        batch.set(ref, tx_data)
        count += 1
        
        if count >= 450:
            batch.commit()
            batch = db.batch()
            count = 0
    
    if count > 0:
        batch.commit()
    
    print(f"Successfully uploaded {len(transactions)} transaction records")

def upload_compliance_rules(db, file_path):
    """Upload compliance rules to Firestore"""
    with open(file_path, "r") as f:
        rules = json.load(f)
    
    db.collection("compliance_rules").document("regions").set(rules)
    
    print("Successfully uploaded compliance rules")

def main():
    """Upload all data to Firestore"""
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir.parent / "outputs"
    
    parser = argparse.ArgumentParser(description="Upload data to Firestore")
    parser.add_argument("--users", help="Users data file path", 
                      default=str(output_dir / "generated_users.json"))
    parser.add_argument("--portfolios", help="Portfolios data file path", 
                      default=str(output_dir / "generated_portfolios.json"))
    parser.add_argument("--prices", help="Prices data file path", 
                      default=str(output_dir / "generated_market_prices.json"))
    parser.add_argument("--rates", help="Exchange rates data file path", 
                      default=str(output_dir / "generated_exchange_rates.json"))
    parser.add_argument("--transactions", help="Transactions data file path", 
                      default=str(output_dir / "generated_transactions.json"))
    parser.add_argument("--rules", help="Compliance rules file path", 
                      default=str(output_dir / "generated_compliance_rules.json"))
    parser.add_argument("--all", action="store_true", help="Upload all data")
    
    args = parser.parse_args()
    
    try:
        db = initialize_firestore()
        
        if args.all or args.users:
            upload_users(db, args.users)
        
        if args.all or args.portfolios:
            upload_portfolios(db, args.portfolios)
        
        if args.all or (args.prices and args.rates):
            upload_market_data(db, args.prices, args.rates)
        
        if args.all or args.transactions:
            upload_transactions(db, args.transactions)
        
        if args.all or args.rules:
            upload_compliance_rules(db, args.rules)
        
        print("All data upload completed")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
