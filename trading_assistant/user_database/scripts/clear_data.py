"""
Clear data from Firestore collections
"""
import json
import argparse
import os
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

def clear_collection(db, collection_name):
    """Delete all documents from a collection"""
    docs = db.collection(collection_name).get()
    deleted = 0
    
    for doc in docs:
        doc.reference.delete()
        deleted += 1
    
    print(f"Deleted {deleted} documents from collection '{collection_name}'")

def clear_document(db, collection_name, document_id):
    """Delete a specific document"""
    doc_ref = db.collection(collection_name).document(document_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        print(f"Deleted document '{document_id}' from collection '{collection_name}'")
    else:
        print(f"Document '{document_id}' does not exist in collection '{collection_name}'")

def main():
    """Clear data from Firestore"""
    parser = argparse.ArgumentParser(description="Clear data from Firestore")
    parser.add_argument("--type", choices=["all", "users", "portfolios", "market", "transactions", "rules"], 
                       default="all", help="Type of data to clear")
    
    args = parser.parse_args()
    
    try:
        db = initialize_firestore()
        
        # Confirm with user before clearing data
        if args.type == "all":
            confirm = input("This will delete ALL data from the database. Are you sure? (y/N): ")
            if confirm.lower() != 'y':
                print("Operation canceled")
                return
                
            clear_collection(db, "users")
            clear_collection(db, "portfolios")
            clear_collection(db, "transactions")
            clear_document(db, "market_data", "prices")
            clear_document(db, "market_data", "exchange_rates")
            clear_document(db, "compliance_rules", "regions")
            
        elif args.type == "users":
            clear_collection(db, "users")
            
        elif args.type == "portfolios":
            clear_collection(db, "portfolios")
            
        elif args.type == "market":
            clear_document(db, "market_data", "prices")
            clear_document(db, "market_data", "exchange_rates")
            
        elif args.type == "transactions":
            clear_collection(db, "transactions")
            
        elif args.type == "rules":
            clear_document(db, "compliance_rules", "regions")
        
        print("Data clearing completed")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
