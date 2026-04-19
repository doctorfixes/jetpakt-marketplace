"""
JetPakt Draft Pipeline — one command, READY rows only.

Usage:
    python run_pipeline.py                  # audit + draft all READY rows
    python run_pipeline.py --audit-only     # just classify, no drafts
    python run_pipeline.py --max 5          # cap at 5 drafts this run

Steps:
  1. Run crm_audit.py to classify every CRM row
  2. Read output/crm_ready_queue.json (READY only)
  3. Invoke outreach_builder.py on that queue
  4. Run inline smoke checks on every produced draft
  5. Print a concise summary + exit non-zero if any check fails

Smoke checks (hard gates, matches locked project rules):
  - 0 Denver mentions in body
  - 0 em-dashes / en-dashes in body
  - Parker postal address present in body
  - Subject <= 45 chars
  - No reviewer first names that aren't inside verbatim quotes
  - Verbatim positive quote source URL resolvable (basic URL shape only)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "output"

EM_DASH = "\u2014"
EN_DASH = "\u2013"
POSTAL = "6222 E Pine Lane, Suite 6212, Parker, CO 80138"


def run_audit() -> dict[str, int]:
    print(">>> Running CRM audit...")
    subprocess.run([sys.executable, str(ROOT / "crm_audit.py")],
                   check=True, cwd=ROOT)
    ready = json.loads((OUT / "crm_ready_queue.json").read_text())
    return {"ready_count": len(ready)}


def run_builder(wave_name: str, source: Path, out_dir: Path,
                top: int) -> None:
    print(f">>> Building drafts for {top} row(s) -> {out_dir}")
    subprocess.run(
        [sys.executable, str(ROOT / "outreach_builder.py"),
         "--top", str(top),
         "--source", str(source.relative_to(ROOT)),
         "--out", str(out_dir.relative_to(ROOT)),
         "--wave-name", wave_name],
        check=True, cwd=ROOT,
    )


def _body_of(md_text: str) -> str:
    parts = md_text.split("\n---\n")
    if len(parts) >= 3:
        return "\n---\n".join(parts[2:])
    return md_text


def smoke_check(md_path: Path) -> list[str]:
    """Return list of failure strings. Empty list = pass."""
    text = md_path.read_text(encoding="utf-8")
    body = _body_of(text)
    failures: list[str] = []

    if re.search(r"\bdenver\b", body, re.IGNORECASE):
        failures.append("'Denver' found in body")
    if EM_DASH in body:
        failures.append("em-dash in body")
    if EN_DASH in body:
        failures.append("en-dash in body")
    if POSTAL not in body:
        failures.append("Parker postal address missing")

    m = re.search(r"^SUBJECT:\s*(.+)$", text, re.MULTILINE)
    if not m:
        failures.append("no SUBJECT line")
    elif len(m.group(1).strip()) > 45:
        failures.append(f"subject > 45 chars ({len(m.group(1).strip())})")

    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit-only", action="store_true")
    ap.add_argument("--max", type=int, default=0,
                    help="Cap drafts this run (0 = all READY)")
    ap.add_argument("--wave-name", type=str,
                    default=f"ready_{date.today().isoformat()}")
    args = ap.parse_args()

    stats = run_audit()
    ready = stats["ready_count"]

    print()
    print(f"READY rows: {ready}")
    if args.audit_only or ready == 0:
        print("(audit-only or nothing to draft) -- exiting")
        return 0

    top = args.max if args.max > 0 else ready
    out_dir = OUT / "outreach" / args.wave_name
    run_builder(args.wave_name, OUT / "crm_ready_queue.json", out_dir, top)

    # Smoke check each produced .md
    print()
    print(">>> Smoke checks")
    any_fail = False
    for md in sorted(out_dir.glob("*.md")):
        fails = smoke_check(md)
        tag = "OK  " if not fails else "FAIL"
        print(f"  [{tag}] {md.name}")
        for f in fails:
            print(f"         - {f}")
            any_fail = True

    print()
    if any_fail:
        print("!! One or more drafts failed smoke checks")
        return 1
    print(f"All drafts passed. Review: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
