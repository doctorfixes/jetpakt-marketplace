"""Sync draft artifacts to the JetPakt CRM Master Google Sheet.

The Sheet is the canonical system of record. This module ONLY writes
artifacts that the CLI already produced locally (drafts, audits). Reads are
cheap; writes are idempotent (keyed on prospect_id + log_id).

Because this CLI runs in the main agent environment, the actual Sheet API
calls go through the google_sheets__pipedream connector — not via a Python
client library. This module prepares the payloads; the CLI's run_sync()
function walks through them and invokes the connector.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .config import SHEET_ID, WORKSHEET_IDS, TEMPLATE_VERSION, DEFAULT_CHANNEL, DEFAULT_TOUCH_TYPE


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class LogRow:
    log_id: str
    prospect_id: str
    subject: str
    body_excerpt: str
    draft_file: str
    pillar: str
    case_id: str
    direction: str = "outbound"
    channel: str = DEFAULT_CHANNEL
    touch_type: str = DEFAULT_TOUCH_TYPE
    template_version: str = TEMPLATE_VERSION
    sent_at: str = ""
    reply_received_at: str = ""
    reply_sentiment: str = ""
    result: str = "drafted"
    created_at: str = ""

    def to_row_array(self, headers: List[str]) -> List[str]:
        d = asdict(self)
        return [str(d.get(h.lower().replace(" ", "_"), "")) for h in headers]


def build_log_id(prospect_id: str, tag: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"log_{ts}_{tag}"


def excerpt_from_body(body: str, max_chars: int = 220) -> str:
    """Return the first substantive prose paragraph from the draft body.

    Skips greetings ("Hi,") and pulls the first paragraph that reads like
    prose (> 60 chars, not a quote block, not a salutation).
    """
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    for para in paras:
        first_line = para.splitlines()[0].strip()
        if first_line.lower().rstrip(",") in {"hi", "hello", "hey"}:
            continue
        # Skip indented quote blocks (start with spaces + quote mark)
        if para.lstrip().startswith('"') and len(para) < 250:
            continue
        # Take first two sentences for context.
        snippet = para.replace("\n", " ")
        if len(snippet) < 60:
            continue
        if len(snippet) > max_chars:
            snippet = snippet[:max_chars].rsplit(" ", 1)[0] + "..."
        return snippet
    return paras[0][:max_chars] if paras else ""


def draft_to_log_row(prospect_id: str, draft_path: Path, pillar: str, case_id: str, tag: str) -> LogRow:
    text = draft_path.read_text(encoding="utf-8")
    subject = ""
    for line in text.splitlines():
        if line.startswith("SUBJECT:"):
            subject = line.split("SUBJECT:", 1)[1].strip()
            break
    # body begins after second '---'
    lines = text.splitlines()
    dash_idxs = [i for i, l in enumerate(lines) if l.strip() == "---"]
    body = "\n".join(lines[dash_idxs[1] + 1 :]) if len(dash_idxs) >= 2 else text
    return LogRow(
        log_id=build_log_id(prospect_id, tag),
        prospect_id=prospect_id,
        subject=subject,
        body_excerpt=excerpt_from_body(body),
        draft_file=str(draft_path),
        pillar=pillar,
        case_id=case_id,
        created_at=now_iso(),
    )
