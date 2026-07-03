from trading_assistant.services.database.firestore_client import get_firestore_client

def get_user_info(user_id: str) -> dict:
    try:
        db = get_firestore_client()
        user_doc = db.collection("users").document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            compliance_data = user_data.get("compliance", {})
            preferences_data = user_data.get("preferences", {})
            
            return {
                "region": compliance_data.get("region", "UNKNOWN"),
                "country_code": compliance_data.get("region", "UNK"),  # Using region as fallback for country code
                "last_updated": user_data.get("profile", {}).get("last_login"),
                "language": preferences_data.get("language", "english"),
            }
            
        # If user not found in Firestore, assume non-restricted for test users with portfolios
        portfolio_doc = db.collection("portfolios").document(user_id).get()
        if portfolio_doc.exists:
            # For test users, assume they're in Singapore
            return {
                "region": "SG",
                "country_code": "SGP",
                "last_updated": portfolio_doc.to_dict().get("last_updated"),
                "language": preferences_data.get("language", "english"),
            }
            
    except Exception as e:
        print(f"[Region API Error] {str(e)}")
    
    return {"region": "UNKNOWN", "country_code": "UNK", "last_updated": None, "language": "english"}

def get_region_restrictions(region: str) -> dict:
    # print(f"[Region API] Getting restrictions for region {region}")
    try:
        db = get_firestore_client()
        rules_doc = db.collection("compliance_rules").document("regions").get()
        
        if rules_doc.exists:
            rules_data = rules_doc.to_dict()
            all_regions = rules_data.get("regions", {})
            
            if region in all_regions:
                return all_regions[region]
                
            if region in ["RESTRICTED", "UNKNOWN"]:
                return {
                    "restricted_coins": ["ALL"],
                    "restricted_trade_types": ["ALL"],
                    "max_transaction_amount": 0,
                    "alternatives": {}
                }
        
    except Exception as e:
        print(f"[Region API Error] {str(e)}")
    
    return {
        "restricted_coins": ["ALL"],
        "restricted_trade_types": ["ALL"],
        "max_transaction_amount": 0,
        "alternatives": {}
    }
