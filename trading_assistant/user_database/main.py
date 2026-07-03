import argparse
import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parent / "scripts"
sys.path.append(str(scripts_dir))

from generate_data import main as generate_data
from upload_data import main as upload_data
from update_market_data import main as update_market_data
from clear_data import main as clear_data

def setup_environment():
    directories = [
        "config",
        "data_templates",
        "outputs",
        "scripts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    config_path = Path("config/firebase_config.json")
    if not config_path.exists():
        print("Warning: Firebase configuration file doesn't exist.")
        print("Please create config/firebase_config.json file.")
        print("Example configuration:")
        print("""
        {
            "project_id": "your-project-id",
            "service_account_key_path": "/path/to/serviceAccountKey.json"
        }
        """)

def run_generate_data():
    """Run the generate_data script"""
    import sys
    original_argv = sys.argv
    sys.argv = [sys.argv[0]]  # Reset argv to avoid confusing the script's argument parser
    try:
        generate_data()
    finally:
        sys.argv = original_argv

def run_upload_data():
    import sys
    original_argv = sys.argv
    sys.argv = [sys.argv[0], "--all"]
    try:
        upload_data()
    finally:
        sys.argv = original_argv

def run_update_market_data(variation=2.0):
    import sys
    original_argv = sys.argv
    sys.argv = [sys.argv[0], "--variation", str(variation)]
    try:
        update_market_data()
    finally:
        sys.argv = original_argv

def run_clear_data(data_type="all"):
    import sys
    original_argv = sys.argv
    sys.argv = [sys.argv[0], "--type", data_type]
    try:
        clear_data()
    finally:
        sys.argv = original_argv

def main():
    parser = argparse.ArgumentParser(description="Trading Bot - User Database Management")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("generate", help="Generate mock data")
    
    subparsers.add_parser("upload", help="Upload data to Firestore")
    
    update_parser = subparsers.add_parser("update_market", help="Update market data")
    update_parser.add_argument("--variation", type=float, default=2.0, help="Price variation percentage range")
    
    clear_parser = subparsers.add_parser("clear", help="Clear Firestore data")
    clear_parser.add_argument("--type", choices=["all", "users", "portfolios", "market", "transactions", "rules"], 
                             default="all", help="Type of data to clear")
    
    subparsers.add_parser("init", help="Initialize environment")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        run_generate_data()
    elif args.command == "upload":
        run_upload_data()
    elif args.command == "update_market":
        run_update_market_data(args.variation if hasattr(args, 'variation') else 2.0)
    elif args.command == "clear":
        run_clear_data(args.type if hasattr(args, 'type') else "all")
    elif args.command == "init":
        setup_environment()
        print("Environment initialized")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
