import os
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "Otto - AI Spending Controller"
    app_env: str = os.getenv("APP_ENV", "sandbox")
    port: int = int(os.getenv("PORT", "8000"))
    
    # PayPal Sandbox Configuration
    paypal_client_id: str = os.getenv("PAYPAL_CLIENT_ID", "sb-dummy-client-id")
    paypal_client_secret: str = os.getenv("PAYPAL_CLIENT_SECRET", "sb-dummy-client-secret")
    paypal_api_base: str = os.getenv(
        "PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com"
    )
    
    # Policy and Firewall Defaults
    max_auto_approve_amount: float = float(os.getenv("MAX_AUTO_APPROVE_AMOUNT", "50.00"))
    quarantine_threshold_amount: float = float(os.getenv("QUARANTINE_THRESHOLD_AMOUNT", "150.00"))
    hourly_velocity_limit: float = float(os.getenv("HOURLY_VELOCITY_LIMIT", "250.00"))
    
settings = Settings()
