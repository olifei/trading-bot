"""
Check if the Firestore database exists and provide setup instructions
"""
import firebase_admin
from firebase_admin import credentials, firestore
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
import argparse
import os

def initialize_firestore(verbose=True):
    """Initialize Firestore connection and check database existence"""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir.parent / "config/firebase_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Firebase configuration file doesn't exist: {config_path}")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Get project ID and database ID from config
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or config.get("project_id")
    database_id = os.environ.get("FIRESTORE_DATABASE_ID") or config.get("database_id")
    
    if verbose:
        print(f"\n=== Firestore Configuration ===")
        print(f"Project ID: {project_id}")
        print(f"Database ID: {database_id}")
        print(f"==================================\n")
    
    # Initialize Firebase with Application Default Credentials
    try:
        # Check if Firebase app is already initialized
        app = firebase_admin.get_app()
    except ValueError:
        # Initialize with ADC
        app = firebase_admin.initialize_app(options={
            'projectId': project_id,
        })
    
    # Try to connect and perform a simple operation
    try:
        db = firestore.client()
        # Try a simple operation - list collections
        db.collections()
        
        if verbose:
            print(f"✅ Successfully connected to default Firestore database")
        
        # Check if we can use database_id
        try:
            db_specific = firestore.client(database_id=database_id)
            # Try the same operation with the specified database
            db_specific.collections()
            if verbose:
                print(f"✅ Successfully connected to database '{database_id}'")
            return True, db_specific
        except Exception as e:
            if "database does not exist" in str(e).lower():
                if verbose:
                    print(f"❌ Database '{database_id}' does not exist")
                    print_database_creation_instructions(project_id, database_id)
                return False, None
            else:
                if verbose:
                    print(f"⚠️ Could not connect to database '{database_id}': {str(e)}")
                    print(f"   Using default database instead")
                return True, db
        
    except Exception as e:
        if "database does not exist" in str(e).lower() or "not_found" in str(e).lower():
            if verbose:
                print(f"❌ No Firestore database exists in project '{project_id}'")
                print_database_creation_instructions(project_id, database_id)
            return False, None
        else:
            if verbose:
                print(f"❌ Error connecting to Firestore: {str(e)}")
            raise e

def print_database_creation_instructions(project_id, database_id):
    """Print instructions for creating a Firestore database"""
    print("\n=== Firestore Database Creation Instructions ===")
    print("You need to create a Firestore database before using these scripts.")
    print("\nOption 1: Create via Google Cloud Console")
    print(f"1. Visit: https://console.cloud.google.com/firestore/databases?project={project_id}")
    print("2. Click 'Create Database'")
    print("3. Choose 'Start in Native mode'")
    print("4. Select a location (e.g., 'nam5 (United States)')") 
    print("5. Set database ID to: " + database_id)
    print("6. Click 'Create'")
    print("\nOption 2: Create via gcloud CLI")
    print(f"Run the following command:")
    print(f"gcloud firestore databases create --project={project_id} --location=nam5 --database={database_id}")
    print("\nAfter creating the database, run this script again to verify the connection.")
    print("================================================\n")

def main():
    """Check Firestore database and provide setup instructions"""
    parser = argparse.ArgumentParser(description="Check Firestore database setup")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    
    args = parser.parse_args()
    
    try:
        success, _ = initialize_firestore(not args.quiet)
        return 0 if success else 1
    
    except Exception as e:
        if not args.quiet:
            print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
