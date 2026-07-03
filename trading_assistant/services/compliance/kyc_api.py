from trading_assistant.services.database.firestore_client import get_firestore_client

def get_kyc_status(user_id: str) -> dict:
    try:
        db = get_firestore_client()
        user_doc = db.collection("users").document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            compliance_data = user_data.get("compliance", {})
            
            return {
                "kyc_verified": compliance_data.get("kyc_verified", False),
                "verification_date": compliance_data.get("kyc_verified_at")
            }
        
        portfolio_doc = db.collection("portfolios").document(user_id).get()
        if portfolio_doc.exists:
            return {
                "kyc_verified": False,
                "verification_date": portfolio_doc.to_dict().get("last_updated")
            }
            
    except Exception as e:
        print(f"[KYC API Error] {str(e)}")

    return {"kyc_verified": False, "verification_date": None}
