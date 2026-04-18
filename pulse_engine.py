"""
JetPakt Pulse — recurring insight engine.

Pulse is scheduled surveillance. For each active client in data/accounts.yaml:

  1. Build a current-state *snapshot* by running the account's scan fixture
     (this already runs scan_engine signals, ROI, pillar rollup, etc.).
  2. Persist the snapshot to data/snapshots/{account_id}/{YYYY-MM-DD}.json.
  3. Diff the snapshot against the most recent prior snapshot (if any).
  4. Classify each change as LOW / MED / HIGH based on material-impact rules.
  5. Emit a PulseInsight object per account — ready for pulse_report to render.

Everything here is deterministic and side-effect-free except for the snapshot
write. No emails sent; no drafts created. Delivery is a separate module
(pulse_deliver) so Ryan's "drafts-over-auto-send" rule is physically enforced
by the architecture.

The engine runs entirely on locally-computed data today. When Yelp Fusion /
Google Places connectors come online, replace the `_run_scan_fixture()` call
with a live-data fetcher — the rest of the pipeline is unchanged.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import importlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------- Config ----------

WORKSPACE = Path(__file__).resolve().parent
SNAPSHOT_DIR = WORKSPACE / "data" / "snapshots"
ACCOUNTS_FILE = WORKSPACE / "data" / "accounts.yaml"


# Material-impact thresholds — changing these changes what counts as "an insight".
# Keep them conservative: the product is judged on signal-to-noise, not volume.
THRESHOLDS: dict[str, float] = {
    "rating_informational": 0.05,   # below this = ignored (noise)
    "rating_medium": 0.10,
    "rating_high_drop": 0.30,       # rating fell ≥0.3 in one period → same-day alert
    "severity_medium": 1.00,
    "peer_gap_medium": 0.25,
    "peer_gap_high": 0.25,          # widening ≥0.25★ → same-day alert (per Ryan)
    "negative_share_high": 0.40,    # first time crossing 40% recent-negative
}


# ---------- Data classes ----------

@dataclass
class Account:
    account_id: str
    name: str
    tier: int
    cadence: str                     # "weekly" | "monthly"
    scan_module: str
    scan_fn: str
    delivery_mode: str               # "client_cc_ryan" | "ryan_only"
    client_email: str
    ryan_email: str
    contract_started: str
    # Optional billing config. Both must be set for the Stripe gate to apply.
    # Accounts without them run unchanged (no gate) — preserves the demo roster.
    stripe_customer_id: str | None = None
    stripe_price_lookup_key: str | None = None

    def effective_delivery_mode(self, has_legal_high: bool) -> str:
        """Legal-HIGH items always route to Ryan, regardless of default mode."""
        if has_legal_high:
            return "ryan_only"
        if not self.client_email:
            return "ryan_only"        # no client email known ⇒ fall back to Ryan
        return self.delivery_mode


@dataclass
class Change:
    kind: str                        # e.g. "rating_drop", "new_legal_flag"
    severity: str                    # "LOW" | "MED" | "HIGH"
    description: str
    prior: Any | None = None
    current: Any | None = None
    signal_key: str | None = None


@dataclass
class PulseInsight:
    """The serializable result of one Pulse run for one account."""
    account: Account
    run_timestamp: str
    snapshot_date: str
    prior_date: str | None
    is_first_run: bool
    rating: float
    review_count: int
    executive_severity: float
    dominant_pillar: str | None
    legal_flags: list[dict[str, Any]]
    changes: list[Change]
    overall_severity: str            # "LOW" | "MED" | "HIGH"
    requires_same_day_alert: bool
    snapshot_path: str


# ---------- Accounts I/O (minimal YAML — no PyYAML dep) ----------

def _parse_yaml_minimal(text: str) -> list[dict[str, Any]]:
    """Tiny parser for the specific accounts.yaml shape.

    Supports only what the file above uses: top-level `accounts:` list of
    `key: value` blocks, one level of nesting, `#` comments, quoted strings.
    This keeps the package dependency-free — adding PyYAML would double install
    time and we don't need it.
    """
    accounts: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_accounts = False
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("accounts:"):
            in_accounts = True
            continue
        if not in_accounts:
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("- "):
            if current is not None:
                accounts.append(current)
            current = {}
            stripped = stripped[2:]
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            val = val.strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.isdigit():
                val = int(val)
            if current is not None:
                current[key.strip()] = val
    if current is not None:
        accounts.append(current)
    return accounts


def load_accounts(path: Path | str = ACCOUNTS_FILE) -> list[Account]:
    text = Path(path).read_text(encoding="utf-8")
    raw = _parse_yaml_minimal(text)
    return [Account(**r) for r in raw]


# ---------- Snapshot ----------

def _run_scan_fixture(account: Account) -> dict[str, Any]:
    """Call the account's scan fixture and return the scan dict.

    scan_engine fixtures return the scan dict directly; per-business scan
    modules return (scan, peers) tuples. Handle both.
    """
    mod = importlib.import_module(account.scan_module)
    fn = getattr(mod, account.scan_fn)
    result = fn()
    if isinstance(result, tuple) and len(result) == 2:
        scan, _peers = result
        return scan
    return result


def _signals_to_dict(signals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index signals by key for O(1) diff lookup."""
    out: dict[str, dict[str, Any]] = {}
    for s in signals:
        out[s["key"]] = {
            "severity": s["severity"],
            "evidence_count": s.get("evidence_count", 0),
            "pillar": s.get("pillar"),
            "case_refs": s.get("case_refs", []),
            "legal_flag": s.get("legal_flag"),
            "label": s.get("label"),
        }
    return out


def snapshot(account: Account, scan: dict[str, Any],
             now: _dt.datetime | None = None) -> dict[str, Any]:
    """Reduce a full scan to the fields Pulse needs — small, durable JSON."""
    now = now or _dt.datetime.now()
    biz = scan["business"]
    biz_dict = dataclasses.asdict(biz) if dataclasses.is_dataclass(biz) else dict(biz)

    return {
        "account_id": account.account_id,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_date": now.strftime("%Y-%m-%d"),
        "rating": biz_dict.get("public_rating"),
        "review_count": biz_dict.get("review_count"),
        "negative_share_recent": biz_dict.get("negative_share_recent"),
        "executive_severity": scan["executive_severity"],
        "signals": _signals_to_dict(scan["top_signals"]),
        "ros_pillars": scan.get("ros_pillars", {}),
        "dominant_pillar": scan.get("ros_pillars", {}).get("dominant_pillar"),
        "peer_benchmark": {
            "gap": scan["peer_benchmark"].get("gap"),
            "peer_avg": scan["peer_benchmark"].get("peer_avg"),
            "n_peers": scan["peer_benchmark"].get("n_peers"),
        },
        "legal_flags": scan.get("legal_flags", []),
    }


def write_snapshot(snap: dict[str, Any]) -> Path:
    account_dir = SNAPSHOT_DIR / snap["account_id"]
    account_dir.mkdir(parents=True, exist_ok=True)
    path = account_dir / f"{snap['snapshot_date']}.json"
    path.write_text(json.dumps(snap, indent=2, default=str), encoding="utf-8")
    return path


def load_prior_snapshot(account_id: str,
                        before_date: str) -> dict[str, Any] | None:
    account_dir = SNAPSHOT_DIR / account_id
    if not account_dir.exists():
        return None
    candidates = sorted(account_dir.glob("*.json"))
    priors = [c for c in candidates if c.stem < before_date]
    if not priors:
        return None
    return json.loads(priors[-1].read_text(encoding="utf-8"))


# ---------- Diff ----------

def diff(prior: dict[str, Any] | None,
         curr: dict[str, Any]) -> list[Change]:
    """Enumerate material changes between two snapshots."""
    changes: list[Change] = []

    # --- First-run baseline ---
    if prior is None:
        changes.append(Change(
            kind="baseline",
            severity="LOW",
            description=(
                f"First Pulse snapshot — baseline established at {curr['rating']}\u2605 "
                f"with {curr['review_count']} public reviews."
            ),
            current={"rating": curr["rating"], "review_count": curr["review_count"]},
        ))
        # Still surface any legal flag on day-one — a HIGH flag on baseline is
        # still a HIGH flag.
        for flag in curr.get("legal_flags", []):
            if flag.get("flag") == "LEGAL-HIGH":
                changes.append(Change(
                    kind="new_legal_flag",
                    severity="HIGH",
                    description=(
                        f"Legal-HIGH flag active on baseline: {flag['signal']}. "
                        "Loop counsel before any public response."
                    ),
                    current=flag,
                ))
        return changes

    # --- Rating movement ---
    pr = prior.get("rating") or 0.0
    cr = curr.get("rating") or 0.0
    delta_r = round(cr - pr, 2)
    if abs(delta_r) >= THRESHOLDS["rating_high_drop"] and delta_r < 0:
        changes.append(Change(
            kind="rating_drop_high",
            severity="HIGH",
            description=(
                f"Rating dropped {abs(delta_r)}\u2605 in one period "
                f"({pr}\u2605 → {cr}\u2605). Usually a single bad night going viral. "
                "Same-day alert triggered."
            ),
            prior=pr, current=cr,
        ))
    elif abs(delta_r) >= THRESHOLDS["rating_medium"]:
        direction = "rose" if delta_r > 0 else "fell"
        changes.append(Change(
            kind="rating_move",
            severity="MED",
            description=(
                f"Rating {direction} {abs(delta_r)}\u2605 "
                f"({pr}\u2605 → {cr}\u2605)."
            ),
            prior=pr, current=cr,
        ))
    elif abs(delta_r) >= THRESHOLDS["rating_informational"]:
        changes.append(Change(
            kind="rating_drift",
            severity="LOW",
            description=f"Rating drift: {pr}\u2605 → {cr}\u2605.",
            prior=pr, current=cr,
        ))

    # --- New review volume ---
    pc = prior.get("review_count") or 0
    cc = curr.get("review_count") or 0
    if cc > pc:
        changes.append(Change(
            kind="new_reviews",
            severity="LOW",
            description=f"{cc - pc} new public reviews since last check ({pc} → {cc}).",
            prior=pc, current=cc,
        ))

    # --- Signal severity movement ---
    prior_sigs = prior.get("signals") or {}
    curr_sigs = curr.get("signals") or {}
    for key, cur in curr_sigs.items():
        pri = prior_sigs.get(key)
        if pri is None:
            if cur.get("legal_flag") == "LEGAL-HIGH":
                changes.append(Change(
                    kind="new_legal_flag",
                    severity="HIGH",
                    description=(
                        f"New LEGAL-HIGH signal emerged: {cur.get('label', key)}. "
                        "Route to Ryan + counsel before any public response."
                    ),
                    current=cur, signal_key=key,
                ))
            else:
                changes.append(Change(
                    kind="new_signal",
                    severity="MED",
                    description=(
                        f"New signal appeared in top 3: {cur.get('label', key)} "
                        f"(severity {cur['severity']:.1f}/10)."
                    ),
                    current=cur, signal_key=key,
                ))
            continue
        delta_s = cur["severity"] - pri["severity"]
        if abs(delta_s) >= THRESHOLDS["severity_medium"]:
            direction = "worsened" if delta_s > 0 else "improved"
            changes.append(Change(
                kind="signal_severity_shift",
                severity="MED",
                description=(
                    f"{cur.get('label', key)} {direction} "
                    f"({pri['severity']:.1f} → {cur['severity']:.1f})."
                ),
                prior=pri["severity"], current=cur["severity"],
                signal_key=key,
            ))

    # --- Signals that dropped out of top 3 ---
    for key, pri in prior_sigs.items():
        if key not in curr_sigs:
            changes.append(Change(
                kind="signal_resolved",
                severity="LOW",
                description=(
                    f"{pri.get('label', key)} no longer in top-3 signals "
                    "— recent reviews no longer emphasize this issue."
                ),
                prior=pri, signal_key=key,
            ))

    # --- Dominant pillar shift ---
    pp = prior.get("dominant_pillar")
    cp = curr.get("dominant_pillar")
    if pp and cp and pp != cp:
        changes.append(Change(
            kind="pillar_shift",
            severity="MED",
            description=(
                f"Dominant ROS pillar shifted: {pp} → {cp}. The nature of the "
                "guest friction has moved — revisit the 30/60/90 plan."
            ),
            prior=pp, current=cp,
        ))

    # --- Peer gap widening (HIGH trigger per Ryan) ---
    pg = (prior.get("peer_benchmark") or {}).get("gap") or 0.0
    cg = (curr.get("peer_benchmark") or {}).get("gap") or 0.0
    # gap is negative when below peers; "widening" = more negative
    if cg < pg and abs(cg - pg) >= THRESHOLDS["peer_gap_high"]:
        changes.append(Change(
            kind="peer_gap_widened",
            severity="HIGH",
            description=(
                f"Peer gap widened {abs(cg - pg):.2f}\u2605 "
                f"({pg:+.2f} → {cg:+.2f}). Either you slipped or a neighbor "
                "got better fast. Same-day alert triggered."
            ),
            prior=pg, current=cg,
        ))

    # --- Negative-share threshold crossed ---
    pns = prior.get("negative_share_recent") or 0.0
    cns = curr.get("negative_share_recent") or 0.0
    if pns < THRESHOLDS["negative_share_high"] <= cns:
        changes.append(Change(
            kind="negative_share_crossed",
            severity="HIGH",
            description=(
                f"Recent-negative share crossed 40% "
                f"({pns*100:.0f}% → {cns*100:.0f}%). "
                "Pause any paid acquisition until the signal stabilizes."
            ),
            prior=pns, current=cns,
        ))

    return changes


# ---------- Insight assembly ----------

def _overall_severity(changes: list[Change]) -> str:
    levels = {c.severity for c in changes}
    if "HIGH" in levels:
        return "HIGH"
    if "MED" in levels:
        return "MED"
    return "LOW"


def run_for_account(account: Account,
                    now: _dt.datetime | None = None) -> PulseInsight:
    """Top-level per-account run: scan → snapshot → diff → insight."""
    now = now or _dt.datetime.now()
    scan = _run_scan_fixture(account)
    snap = snapshot(account, scan, now=now)
    path = write_snapshot(snap)
    prior = load_prior_snapshot(account.account_id, snap["snapshot_date"])
    changes = diff(prior, snap)
    return PulseInsight(
        account=account,
        run_timestamp=snap["timestamp"],
        snapshot_date=snap["snapshot_date"],
        prior_date=(prior["snapshot_date"] if prior else None),
        is_first_run=(prior is None),
        rating=snap["rating"],
        review_count=snap["review_count"],
        executive_severity=snap["executive_severity"],
        dominant_pillar=snap.get("dominant_pillar"),
        legal_flags=snap.get("legal_flags", []),
        changes=changes,
        overall_severity=_overall_severity(changes),
        requires_same_day_alert=any(c.severity == "HIGH" for c in changes),
        snapshot_path=str(path),
    )


def filter_accounts_for_cadence(accounts: list[Account],
                                cadence: str) -> list[Account]:
    """Select accounts scheduled for the given cadence. Monthly accounts are
    included in weekly runs too, but their *report* is produced only on
    month-end (the report module handles that gate)."""
    cadence = cadence.lower()
    if cadence == "weekly":
        return [a for a in accounts if a.cadence == "weekly"]
    if cadence == "monthly":
        return [a for a in accounts if a.cadence in ("weekly", "monthly")]
    raise ValueError(f"Unknown cadence: {cadence!r}")
