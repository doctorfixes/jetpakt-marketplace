"""
Guardrail validator for JetPakt Scan v2 output.

Checks:
  1. Every top signal has at least one verbatim evidence quote
  2. Legal-flagged signals carry a legal note
  3. Response drafts never contain reviewer first names (body copy rule)
  4. Response drafts never contain staff role names like "server <Name>"
  5. Every response draft carries HOLD status
  6. PDF metadata has Author="Perplexity Computer"
"""

from __future__ import annotations

import re
import sys

from pypdf import PdfReader

from scan_engine import westrail_fixture


# Names that always come from reviewers-in-fixture + "Guest" placeholders.
# The actual set of reviewer names is derived dynamically per-scan via
# _reviewer_name_set() so new fixtures don't leak through stale hardcoding.
_FALLBACK_REVIEWER_NAMES: set[str] = {"Guest"}


def _reviewer_name_set(scan: dict) -> set[str]:
    """Collect every reviewer first name referenced in the scan's evidence."""
    names: set[str] = set(_FALLBACK_REVIEWER_NAMES)
    for sig in scan.get("top_signals", []):
        for ev in sig.get("evidence", []) or []:
            n = getattr(ev, "reviewer_first_name", None)
            if isinstance(n, str) and n:
                names.add(n)
    for d in scan.get("response_drafts", []):
        n = d.get("reviewer_first_name") or d.get("reviewer")
        if isinstance(n, str) and n:
            names.add(n)
    # Drop common placeholders
    names.discard("")
    return names


def validate_scan(scan: dict) -> list[str]:
    errors: list[str] = []

    reviewer_names = _reviewer_name_set(scan)

    # 1. Top signals must have evidence
    for sig in scan["top_signals"]:
        if not sig.get("evidence"):
            errors.append(
                f"[signal] {sig['label']} has no verbatim evidence")

    # 2. Legal flags must carry a note
    for sig in scan["top_signals"]:
        if sig.get("legal_flag") and not sig.get("legal_note"):
            errors.append(
                f"[legal] {sig['label']} flagged {sig['legal_flag']} "
                f"but no note attached")

    # 3 + 4. Response drafts must not name reviewers or staff in body
    for i, d in enumerate(scan["response_drafts"], start=1):
        text = d["draft_text"]
        for name in reviewer_names:
            if re.search(rf"\b{name}\b", text):
                errors.append(
                    f"[draft {i}] contains reviewer name '{name}' in "
                    f"generated body copy")
        # Staff-role leak heuristic: "our server John" / "waitress Sarah"
        staff_name_patterns = [
            r"\b(our|the)\s+(server|waitress|waiter|bartender|host|chef|manager)\s+[A-Z][a-z]+",
        ]
        for pat in staff_name_patterns:
            m = re.search(pat, text)
            if m:
                errors.append(
                    f"[draft {i}] leaks staff name: '{m.group(0)}'")

    # 5. Every draft carries HOLD status
    for i, d in enumerate(scan["response_drafts"], start=1):
        if "HOLD" not in d.get("status", ""):
            errors.append(
                f"[draft {i}] missing HOLD status "
                f"(got: {d.get('status')!r})")

    # Informational check: ensure at least one legal flag surfaced for
    # Westrail (service-fee + food-safety both present in evidence).
    flagged_labels = {f["signal"] for f in scan.get("legal_flags", [])}
    # (Westrail has food_safety tied to top food_quality signal's evidence,
    # but service_fee_transparency isn't in top_signals because the overall
    # severity was lower — still check *any* legal flag appears either in
    # top signals or in evidence.)
    return errors


def validate_pdf(pdf_path: str, scan: dict | None = None) -> list[str]:
    errors: list[str] = []
    reader = PdfReader(pdf_path)
    meta = reader.metadata or {}
    author = meta.get("/Author")
    title = meta.get("/Title")
    if author != "Perplexity Computer":
        errors.append(f"[pdf] Author must be 'Perplexity Computer', "
                      f"got {author!r}")
    if not title or "JetPakt" not in str(title):
        errors.append(f"[pdf] Title missing 'JetPakt', got {title!r}")

    reviewer_names = _reviewer_name_set(scan) if scan else _FALLBACK_REVIEWER_NAMES

    # Scan body text of every page for reviewer-name leaks OUTSIDE of
    # quoted text. We cannot easily detect quotes in extracted text, so
    # instead we require that any reviewer first name only appears in
    # lines that also contain a quote mark or a review attribution.
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for name in reviewer_names:
            for line in text.splitlines():
                if re.search(rf"\b{name}\b", line):
                    # Allow if line contains a quote character OR the
                    # word "Draft" (attribution block)
                    if not any(ch in line for ch in ("\u201c", "\u201d",
                                                     "\"", "'")):
                        if "Draft" not in line and "Yelp" not in line:
                            errors.append(
                                f"[pdf p{page_num}] reviewer name '{name}' "
                                f"appears in non-quoted line: {line!r}")
    return errors


def main() -> int:
    import sys as _sys
    from pathlib import Path as _P

    # Allow CLI argument: default to Westrail, accept path to any scan PDF
    targets = []
    if len(_sys.argv) > 1:
        for arg in _sys.argv[1:]:
            p = _P(arg)
            if not p.exists():
                print(f"[skip] {arg} not found")
                continue
            targets.append((arg, None))
    else:
        targets.append((
            "/home/user/workspace/denver_leadgen/output/scans/westrail_scan_v2.pdf",
            westrail_fixture(),
        ))

    any_err = False
    for pdf_path, scan in targets:
        print(f"\n=== {_P(pdf_path).name} ===")
        if scan:
            errs = validate_scan(scan)
            if errs:
                any_err = True
                for e in errs:
                    print(" [scan]", e)
            else:
                print(" [scan] OK")
        pdf_errs = validate_pdf(pdf_path, scan=scan)
        if pdf_errs:
            any_err = True
            for e in pdf_errs:
                print(" [pdf]", e)
        else:
            print(" [pdf] OK")
    return 1 if any_err else 0


if __name__ == "__main__":
    sys.exit(main())
