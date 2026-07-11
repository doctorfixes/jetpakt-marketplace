"""Configuration for the JetPakt CLI.

All IDs, paths, and defaults live here so the rest of the CLI can stay simple.

JetPakt runs more than one business line on this same CLI/CRM mechanism
(smoke gates, sync, outlook drafting, inbox scan, Stripe onboarding). Each
line is a *profile* with its own Sheet, Stripe catalog, and welcome copy —
the mechanism underneath is shared and vertical-agnostic.

Select the active profile with the JETPAKT_PROFILE env var. Default is
"restaurant" (the original Denver Pulse business) so existing behavior is
completely unchanged unless a profile is explicitly requested — this file
drives a live Sheet + live Stripe products for that business, so nothing
about the restaurant profile's values should change without confirming
those product IDs / that Sheet are actually safe to touch.

    JETPAKT_PROFILE=agency ./jetpakt <command>   # AI Front Desk (80134 trades/local-service)
    ./jetpakt <command>                          # restaurant Pulse (default, unchanged)
"""
import os
from pathlib import Path

# --- Paths ------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
DRAFTS_DIR = OUTPUT_DIR / "outreach"
ARCHIVE_DIR = REPO_ROOT / "archive"
WIDE_DIR = REPO_ROOT.parent / "wide"

READY_QUEUE = OUTPUT_DIR / "crm_ready_queue.json"

ACTIVE_PROFILE = os.environ.get("JETPAKT_PROFILE", "restaurant")

# --- Clients tab schema (18 cols A..R) — shared across every profile -------
CLIENTS_COLUMNS = (
    "client_id", "prospect_id", "business_name", "contact_email",
    "stripe_customer_id", "stripe_subscription_id", "tier", "cadence",
    "mrr_usd", "status", "onboarded_at", "next_deliverable_due",
    "last_memo_sent_at", "last_memo_file", "cancellation_reason", "notes",
    "created_at", "updated_at",
)

# --- Restaurant profile (LIVE — Denver Pulse business, values unchanged) --
_RESTAURANT_WELCOME_TEMPLATE = """Welcome to JetPakt.

Your {tier_name} subscription is active. Here is what happens next:

1. I will send your first drift memo by {first_due_human}. It runs across the
   five operating pillars using only verbatim public reviews and records.
2. After that, memos land on a {cadence_human} schedule. You can cancel any
   time from the link in every email.
3. If you want to change the target location, add a location, or adjust the
   focus, reply to any memo and I will handle it.

No sales calls. No dashboard logins. No auto-posting on your behalf. Every
response draft is yours to approve before anything goes out.

Sheet of record for your subscription:
client_id {client_id}

Talk soon,
Ryan
JetPakt Solutions
6222 E Pine Lane, Suite 6212, Parker, CO 80138
"""

_PROFILES = {
    "restaurant": dict(
        crm_csv_name="denver_restaurant_leads_full_audit.csv",
        sheet_id="1L2NqIcZeG_SMqoL_L3YN_IlqiVkMWy4SyBsu2Sa07yI",
        worksheet_ids={
            "Prospects": 2139708364,
            "ICP Targets": 1559684998,
            "Outreach Log": 250333527,
            "Metrics": 1953076964,
            "Pipeline": 1925316065,
            "Suppression": 1712783155,
            "Clients": 534094040,
        },
        # Stripe product_id -> (tier_label, cadence_days, mrr_usd).
        # cadence_days = memo delivery cadence (None = one-time).
        stripe_product_tier={
            "prod_UMDaHMYdnHdW2H": ("Scan",              None, 0),    # $49 one-time
            "prod_UMDbLrW0doOHPI": ("Pulse Essentials",   30,  149),
            "prod_UMDcmqaEyH1UBd": ("Pulse Pro",           7,  399),
            "prod_UMDdOzoVVKTCZj": ("Pulse Alert",         7,  899),
            "prod_UMDebs2GG5zR4B": ("Pulse Concierge",     7, 1499),
        },
        no_subscription_tier=("Scan", None, 0),
        default_one_time_product_id="prod_UMDaHMYdnHdW2H",
        welcome_template=_RESTAURANT_WELCOME_TEMPLATE,
        welcome_subject_template="{tier_name} is active, first memo {first_due_human}",
        template_version="v3-drift-personalized",
        default_touch_type="cold_drift",
    ),
    # --- AI Agency profile (NEW — AI Front Desk for 80134-area trades/local
    # service businesses: salons, dry cleaners, roofers, plumbers, etc.) ---
    # sheet_id / worksheet_ids / stripe_product_tier are intentionally empty
    # placeholders: Ryan creates the Sheet tabs and Stripe products by hand
    # (same "billing/CRM writes require a human step" rule stripe_sync.py
    # already follows), then fills these in. See docs/AGENCY_CRM_SETUP.md.
    "agency": dict(
        crm_csv_name="agency_leads_full_audit.csv",
        sheet_id=os.environ.get("JETPAKT_AGENCY_SHEET_ID", ""),
        worksheet_ids={
            "Prospects": None,
            "Outreach Log": None,
            "Suppression": None,
            "Clients": None,
        },
        stripe_product_tier={},
        no_subscription_tier=("Setup Only", None, 0),
        default_one_time_product_id="",
        welcome_template="""Welcome to JetPakt AI.

Your {tier_name} plan is active. Here is what happens next:

1. I will text/call you within 1 business day to lock in your install-week
   schedule for your AI phone number and booking calendar (plus your
   one-page site and Google Business Profile, if included in your plan).
2. Once live, you get a weekly summary: calls answered, bookings created,
   and reviews received.
3. Check-ins run on a {cadence_human} cadence for the first 90 days, then
   quarterly. Cancel any time from the link in every email.

No long-term contract beyond the plan you picked.

Sheet of record for your account:
client_id {client_id}

Talk soon,
Ryan
JetPakt Solutions
6222 E Pine Lane, Suite 6212, Parker, CO 80138
""",
        welcome_subject_template="{tier_name} is active, install starts {first_due_human}",
        template_version="v1-agency-intro",
        default_touch_type="cold_intro",
    ),
}

_P = _PROFILES[ACTIVE_PROFILE]

CRM_CSV = OUTPUT_DIR / _P["crm_csv_name"]

# --- Google Sheets (JetPakt CRM Master, profile-specific) -------------------
SHEET_ID = _P["sheet_id"]
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit" if SHEET_ID else ""
WORKSHEET_IDS = _P["worksheet_ids"]

STRIPE_PRODUCT_TIER = _P["stripe_product_tier"]
NO_SUBSCRIPTION_TIER = _P["no_subscription_tier"]
DEFAULT_ONE_TIME_PRODUCT_ID = _P["default_one_time_product_id"]
WELCOME_BODY_TEMPLATE = _P["welcome_template"]
WELCOME_SUBJECT_TEMPLATE = _P["welcome_subject_template"]

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
TEMPLATE_VERSION = _P["template_version"]
DEFAULT_CHANNEL = "outlook"
DEFAULT_TOUCH_TYPE = _P["default_touch_type"]
ROUTING = "ryan_drafts"

# --- Smoke-check gates ------------------------------------------------------
SUBJECT_MAX_CHARS = 45
BLOCKED_BODY_TOKENS = ("denver",)
FORBIDDEN_TOKENS = ("food poisoning", "made me sick", "hospital", "salmonella",
                    "e. coli", "norovirus", "got sick")
REQUIRED_POSTAL = "6222 E Pine Lane, Suite 6212, Parker, CO 80138"
