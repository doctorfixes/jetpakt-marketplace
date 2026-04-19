"""Configuration for the JetPakt CLI.

All IDs, paths, and defaults live here so the rest of the CLI can stay simple.
"""
from pathlib import Path

# --- Paths ------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
DRAFTS_DIR = OUTPUT_DIR / "outreach"
ARCHIVE_DIR = REPO_ROOT / "archive"
WIDE_DIR = REPO_ROOT.parent / "wide"

CRM_CSV = OUTPUT_DIR / "denver_restaurant_leads_full_audit.csv"
READY_QUEUE = OUTPUT_DIR / "crm_ready_queue.json"

# --- Google Sheets (JetPakt CRM Master) -------------------------------------
SHEET_ID = "1L2NqIcZeG_SMqoL_L3YN_IlqiVkMWy4SyBsu2Sa07yI"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# Worksheet IDs (integers, from google_sheets-get-spreadsheet-info)
WORKSHEET_IDS = {
    "Prospects": 2139708364,
    "ICP Targets": 1559684998,
    "Outreach Log": 250333527,
    "Metrics": 1953076964,
    "Pipeline": 1925316065,
    "Suppression": 1712783155,
    "Clients": 534094040,
}

# --- Clients tab schema (18 cols A..R) --------------------------------------
CLIENTS_COLUMNS = (
    "client_id", "prospect_id", "business_name", "contact_email",
    "stripe_customer_id", "stripe_subscription_id", "tier", "cadence",
    "mrr_usd", "status", "onboarded_at", "next_deliverable_due",
    "last_memo_sent_at", "last_memo_file", "cancellation_reason", "notes",
    "created_at", "updated_at",
)

# --- Stripe product catalog -> JetPakt tier -------------------------------
# Maps Stripe product_id to (tier_label, cadence_days, mrr_usd).
# cadence_days = memo delivery cadence (None = one-time).
STRIPE_PRODUCT_TIER = {
    "prod_UMDaHMYdnHdW2H": ("Scan",              None, 0),    # $49 one-time
    "prod_UMDbLrW0doOHPI": ("Pulse Essentials",   30,  149),
    "prod_UMDcmqaEyH1UBd": ("Pulse Pro",           7,  399),
    "prod_UMDdOzoVVKTCZj": ("Pulse Alert",         7,  899),
    "prod_UMDebs2GG5zR4B": ("Pulse Concierge",     7, 1499),
}

# --- Inbox-scan defaults ----------------------------------------------------
# Bounce signal phrases used by Microsoft Exchange / Outlook postmasters.
BOUNCE_SUBJECT_TOKENS = (
    "undeliverable", "undelivered", "delivery status notification",
    "mail delivery failed", "returned mail", "delivery has failed",
    "message not delivered",
)
BOUNCE_FROM_TOKENS = (
    "mailer-daemon", "postmaster", "mail delivery subsystem",
    "mailer_daemon", "no-reply-delivery",
)
# Phrases that indicate an opt-out / unsubscribe intent in the reply body.
UNSUB_TOKENS = (
    "unsubscribe", "take me off", "remove me", "stop emailing",
    "do not email", "don't email me", "stop contacting",
    "not interested", "please remove",
)

# --- Outreach policy --------------------------------------------------------
TEMPLATE_VERSION = "v3-drift-personalized"
DEFAULT_CHANNEL = "outlook"
DEFAULT_TOUCH_TYPE = "cold_drift"
ROUTING = "ryan_drafts"

# --- Smoke-check gates ------------------------------------------------------
SUBJECT_MAX_CHARS = 45
BLOCKED_BODY_TOKENS = ("denver",)
FORBIDDEN_TOKENS = ("food poisoning", "made me sick", "hospital", "salmonella",
                    "e. coli", "norovirus", "got sick")
REQUIRED_POSTAL = "6222 E Pine Lane, Suite 6212, Parker, CO 80138"
