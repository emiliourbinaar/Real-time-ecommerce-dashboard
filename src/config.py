"""
Central configuration for paths, model parameters, and business rules.
"""
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent.parent
DATA_RAW       = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_POWERBI   = BASE_DIR / "data" / "powerbi"

# ── Dataset generation ───────────────────────────────────────────────────────
RANDOM_SEED       = 42
N_CUSTOMERS       = 500
N_PRODUCTS        = 80
MONTHS_OF_DATA    = 14          # slightly more than 12 for richer history
START_DATE        = "2024-01-01"

# ── Business rules ───────────────────────────────────────────────────────────
CHURN_INACTIVE_DAYS = 60        # customer considered at-risk after 60 days
REPEAT_MIN_ORDERS   = 2         # orders needed to be a "repeat customer"

# ── ML ───────────────────────────────────────────────────────────────────────
TEST_WEEKS          = 8         # hold-out weeks for forecast evaluation
FORECAST_HORIZON    = 4         # weeks to predict ahead

# ── Segments ─────────────────────────────────────────────────────────────────
CUSTOMER_SEGMENTS = ["Enterprise", "SMB", "Startup", "Government"]
SALES_CHANNELS    = ["Direct", "Marketplace", "Partner", "Online Store"]
PAYMENT_METHODS   = ["Credit Card", "Bank Transfer", "PayPal", "Invoice"]
ORDER_STATUSES    = ["Completed", "Pending", "Cancelled", "Refunded"]

PRODUCT_CATEGORIES = {
    "Electronics":    ["Laptop", "Monitor", "Keyboard", "Mouse", "Webcam", "Headset"],
    "Office Supply":  ["Desk Chair", "Standing Desk", "Notebook", "Pen Set", "Organizer"],
    "Software":       ["CRM License", "ERP Module", "Analytics Tool", "Security Suite"],
    "Networking":     ["Router", "Switch", "Access Point", "Firewall", "Cable Kit"],
    "Cloud Services": ["Storage Plan", "Compute Credits", "CDN Package", "Backup Plan"],
}

CAMPAIGNS = [
    "Spring Promo", "Summer Sale", "Back-to-Business", "Q4 Push",
    "New Year Deal", "Flash Sale", "Partner Week", "Loyalty Drive",
    "Organic / None",
]
