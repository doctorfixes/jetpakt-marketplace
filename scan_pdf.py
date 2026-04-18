"""
JetPakt Scan v2 — Branded PDF renderer.

Reads a scan dict from scan_engine.build_scan() and writes a hospitality-first
branded PDF using:
  - Instrument Serif (display) + Inter (body/UI) via Google Fonts
  - Teal #20808D chart accent, link #01696F, cream #F7F6F2 background
  - Metadata: Author=Perplexity Computer, Title="JetPakt Reputation Scan — <name>"
"""

from __future__ import annotations

import io
import os
import tempfile
import urllib.request
from html import escape as _xml_escape
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)


# ---------- Palette ----------

CREAM = HexColor("#F7F6F2")
SURFACE = HexColor("#FBFBF9")
BORDER = HexColor("#D4D1CA")
TEXT = HexColor("#28251D")
MUTED = HexColor("#7A7974")
FAINT = HexColor("#BAB9B4")
TEAL = HexColor("#20808D")          # chart primary
TEAL_DEEP = HexColor("#01696F")     # links / headings
TEAL_DARK = HexColor("#1B474D")
LIGHT_CYAN = HexColor("#BCE2E7")
ERROR = HexColor("#A13544")
WARN = HexColor("#964219")
SUCCESS = HexColor("#437A22")

FONT_DIR = Path("/tmp/fonts")
FONT_DIR.mkdir(exist_ok=True)

FONT_URLS = {
    # Inter (wght-only) and DM Sans TTFs
    "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "InstrumentSerif": "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf",
    "InstrumentSerif-Italic": "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Italic.ttf",
    "DMSans": "https://github.com/google/fonts/raw/main/ofl/dmsans/DMSans%5Bopsz%2Cwght%5D.ttf",
}


FONT_DOWNLOAD_TIMEOUT_SEC = 8


def _download_font(name: str, url: str) -> Path:
    """Download a font atomically (temp file + rename) with a timeout.

    An interrupted urlretrieve can leave a zero-byte or truncated file at the
    destination path; the next run then skips the download and registerFont
    crashes. Writing to a sibling tempfile and atomically renaming avoids that.
    """
    path = FONT_DIR / f"{name}.ttf"
    if path.exists() and path.stat().st_size >= 1000:
        return path
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=f"{name}.", suffix=".ttf.part", dir=str(FONT_DIR)
    )
    os.close(tmp_fd)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JetPakt-scan/1.0"})
        with urllib.request.urlopen(req, timeout=FONT_DOWNLOAD_TIMEOUT_SEC) as r, \
                open(tmp_name, "wb") as f:
            f.write(r.read())
        if Path(tmp_name).stat().st_size < 1000:
            raise IOError(f"font {name} download returned <1KB")
        os.replace(tmp_name, path)          # atomic on POSIX
    except Exception:
        # Clean the temp file; caller will fall back to Helvetica
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def safe_para_text(text: str) -> str:
    """Escape user-supplied strings for safe embedding in a ReportLab Paragraph.

    Paragraph parses an XML-like mini-language; an unescaped '<' or '&' in a
    reviewer quote (rare but real) raises or renders garbage. We escape
    &, <, >, and normalize straight quotes to curly so the PDF still looks clean.
    """
    if text is None:
        return ""
    return _xml_escape(str(text), quote=False)


def register_fonts() -> dict[str, str]:
    """Register Inter, Instrument Serif, DM Sans; return logical font names."""
    registered: dict[str, str] = {}
    try:
        for name, url in FONT_URLS.items():
            p = _download_font(name, url)
            pdfmetrics.registerFont(TTFont(name, str(p)))
            registered[name] = name
    except Exception as e:
        # Fallback to Helvetica
        print(f"[scan_pdf] font registration partial: {e}")
    return registered


# ---------- Styles ----------

def build_styles(fonts: dict[str, str]) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    display = fonts.get("InstrumentSerif", "Helvetica")
    body = fonts.get("Inter", "Helvetica")
    ui = fonts.get("DMSans", body)

    s = {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Normal"],
            fontName=display, fontSize=42, leading=48, textColor=TEXT,
            spaceAfter=8,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", parent=base["Normal"],
            fontName=body, fontSize=12, leading=16, textColor=MUTED,
            spaceAfter=4,
        ),
        "cover_kicker": ParagraphStyle(
            "cover_kicker", parent=base["Normal"],
            fontName=ui, fontSize=9, leading=12, textColor=TEAL_DEEP,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Normal"],
            fontName=display, fontSize=24, leading=28, textColor=TEXT,
            spaceBefore=6, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Normal"],
            fontName=ui, fontSize=13, leading=18, textColor=TEAL_DEEP,
            spaceBefore=8, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Normal"],
            fontName=ui, fontSize=11, leading=14, textColor=TEXT,
            spaceBefore=4, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName=body, fontSize=10.5, leading=15, textColor=TEXT,
            spaceAfter=6,
        ),
        "body_small": ParagraphStyle(
            "body_small", parent=base["Normal"],
            fontName=body, fontSize=9.5, leading=13, textColor=TEXT,
            spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["Normal"],
            fontName=body, fontSize=9, leading=12, textColor=MUTED,
            spaceAfter=4,
        ),
        "quote": ParagraphStyle(
            "quote", parent=base["Normal"],
            fontName=display, fontSize=11, leading=16, textColor=TEXT,
            leftIndent=12, rightIndent=6, spaceAfter=4,
            borderPadding=0,
        ),
        "quote_attr": ParagraphStyle(
            "quote_attr", parent=base["Normal"],
            fontName=body, fontSize=8.5, leading=11, textColor=MUTED,
            leftIndent=12, spaceAfter=8,
        ),
        "tag": ParagraphStyle(
            "tag", parent=base["Normal"],
            fontName=ui, fontSize=8, leading=10, textColor=TEAL_DEEP,
        ),
        "legal": ParagraphStyle(
            "legal", parent=base["Normal"],
            fontName=body, fontSize=9, leading=12, textColor=WARN,
            leftIndent=8, rightIndent=8, spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"],
            fontName=body, fontSize=7.5, leading=10, textColor=MUTED,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", parent=base["Normal"],
            fontName=display, fontSize=32, leading=34, textColor=TEAL_DEEP,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", parent=base["Normal"],
            fontName=ui, fontSize=9, leading=12, textColor=MUTED,
        ),
    }
    return s


# ---------- Severity bar ----------

def severity_chip(severity: float) -> tuple[str, HexColor]:
    if severity >= 7.5:
        return f"{severity:.1f} / 10 · HIGH", ERROR
    if severity >= 5:
        return f"{severity:.1f} / 10 · MEDIUM", WARN
    return f"{severity:.1f} / 10 · MONITOR", TEAL_DEEP


def _severity_bar(severity: float, width: float = 2.2 * inch,
                  height: float = 7) -> Table:
    """Thin horizontal bar (0-10 scale)."""
    filled_frac = max(0.05, min(severity / 10.0, 1.0))
    filled_w = width * filled_frac
    empty_w = width - filled_w
    chip_color = severity_chip(severity)[1]
    t = Table([[" ", " "]], colWidths=[filled_w, empty_w], rowHeights=[height])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), chip_color),
        ("BACKGROUND", (1, 0), (1, 0), BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# ---------- Peer benchmark chart (matplotlib) ----------

def peer_chart_image(bench: dict[str, Any]) -> Image | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    rows = bench["rows"]
    names = [r["name"] for r in rows]
    ratings = [r["rating"] for r in rows]
    colors = [
        "#20808D" if r["is_subject"] else "#A3C9CF"
        for r in rows
    ]

    fig_h = max(1.4, 0.45 * len(rows) + 0.7)
    fig, ax = plt.subplots(figsize=(6.2, fig_h), dpi=200)
    y = list(range(len(names)))
    bars = ax.barh(y, ratings, color=colors, edgecolor="none", height=0.55)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9, color="#28251D")
    ax.set_xlim(0, 5)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.tick_params(axis="x", labelsize=8, colors="#7A7974")
    ax.set_xlabel("Public rating (1–5)", fontsize=8, color="#7A7974")
    ax.invert_yaxis()

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#D4D1CA")
    ax.grid(axis="x", color="#EFEDE6", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_facecolor("#F7F6F2")
    fig.patch.set_facecolor("#F7F6F2")

    for bar, r in zip(bars, rows):
        w = bar.get_width()
        ax.text(w + 0.08, bar.get_y() + bar.get_height() / 2,
                f"{r['rating']:.1f} · {r['review_count']} rev",
                va="center", ha="left", fontsize=8, color="#28251D")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="#F7F6F2",
                bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    img = Image(buf, width=6.2 * inch, height=fig_h * inch)
    img.hAlign = "LEFT"
    return img


# ---------- Page frame / footer ----------

def _page_decor(canvas, doc, business_name: str, jetpakt_contact: dict[str, str]):
    canvas.saveState()
    w, h = letter
    # Cream background
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Top bar
    canvas.setFillColor(TEAL_DEEP)
    canvas.rect(0, h - 0.35 * inch, w, 0.35 * inch, fill=1, stroke=0)
    canvas.setFillColor(CREAM)
    try:
        canvas.setFont("DMSans", 9)
    except Exception:
        canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(0.6 * inch, h - 0.22 * inch,
                      "JETPAKT · REPUTATION SCAN")
    canvas.drawRightString(w - 0.6 * inch, h - 0.22 * inch,
                           business_name.upper())

    # Footer
    canvas.setFillColor(MUTED)
    try:
        canvas.setFont("Inter", 8)
    except Exception:
        canvas.setFont("Helvetica", 8)
    footer_l = (f"{jetpakt_contact['name']} · "
                f"{jetpakt_contact['phone']} · "
                f"{jetpakt_contact['email']} · "
                f"{jetpakt_contact['site']}")
    canvas.drawString(0.6 * inch, 0.35 * inch, footer_l)
    canvas.drawRightString(w - 0.6 * inch, 0.35 * inch,
                           f"Page {doc.page}")
    canvas.restoreState()


# ---------- Section builders ----------

def _cover(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    biz = scan["business"]
    bench = scan["peer_benchmark"]
    severity = scan["executive_severity"]
    chip_text, chip_color = severity_chip(severity)

    story = []
    story.append(Spacer(1, 0.9 * inch))
    story.append(Paragraph("JETPAKT · ONE-TIME SCAN", S["cover_kicker"]))
    story.append(Paragraph(biz.name, S["cover_title"]))
    story.append(Paragraph(
        f"{biz.address} · {biz.city}",
        S["cover_sub"],
    ))
    story.append(Paragraph(
        f"Scan generated {scan['generated_at']}",
        S["cover_sub"],
    ))
    story.append(Spacer(1, 0.35 * inch))

    # KPI row
    kpi_rows = [
        [
            Paragraph(f"{biz.public_rating:.1f}", S["kpi_value"]),
            Paragraph(f"{int(biz.negative_share_recent * 100)}%", S["kpi_value"]),
            Paragraph(f"{biz.review_count}", S["kpi_value"]),
            Paragraph(f"{bench['delta_vs_peers']:+.2f}", S["kpi_value"]),
        ],
        [
            Paragraph("Public rating", S["kpi_label"]),
            Paragraph("Recent negative share", S["kpi_label"]),
            Paragraph("Total public reviews", S["kpi_label"]),
            Paragraph("Rating vs. 3 local peers", S["kpi_label"]),
        ],
    ]
    col_w = [1.65 * inch] * 4
    kpi = Table(kpi_rows, colWidths=col_w, hAlign="LEFT")
    kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
    ]))
    story.append(kpi)
    story.append(Spacer(1, 0.3 * inch))

    # Severity headline
    story.append(Paragraph("Overall signal severity", S["h2"]))
    story.append(_severity_bar(severity, width=5.2 * inch, height=9))
    story.append(Spacer(1, 4))
    sev_style = ParagraphStyle("sev", parent=S["body"], textColor=chip_color,
                               fontSize=11)
    story.append(Paragraph(chip_text, sev_style))
    story.append(Spacer(1, 0.2 * inch))

    # Sources line
    src_parts = []
    for s_name, url in biz.review_sources.items():
        src_parts.append(
            f'<a href="{url}" color="#01696F">{s_name}</a>'
        )
    story.append(Paragraph(
        "Public review sources: " + " · ".join(src_parts),
        S["muted"],
    ))

    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        "Prepared by JetPakt · ReviewSentinel methodology · "
        "Every finding below is tied to a verbatim public review.",
        S["muted"],
    ))
    return story


def _exec_summary(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    story = []
    story.append(Paragraph("Executive snapshot", S["h1"]))
    biz = scan["business"]
    bench = scan["peer_benchmark"]
    top = scan["top_signals"]

    sig_names = " · ".join(s["label"] for s in top)
    delta_word = ("below" if bench["delta_vs_peers"] < 0
                  else "above" if bench["delta_vs_peers"] > 0
                  else "in line with")
    story.append(Paragraph(
        f"{biz.name} is sitting at {biz.public_rating:.1f} stars across "
        f"{biz.review_count} public reviews, with roughly "
        f"{int(biz.negative_share_recent * 100)}% of recent reviews rated "
        f"1–2 stars. That puts the rating "
        f"<b>{abs(bench['delta_vs_peers']):.2f} stars {delta_word}</b> the "
        f"3-peer local benchmark ({bench['avg_peer_rating']:.2f} average).",
        S["body"],
    ))
    story.append(Paragraph(
        f"The three signals driving the most guest friction right now are "
        f"<b>{sig_names}</b>. All are actionable inside 30–90 days without "
        f"capex, and none require public apology statements.",
        S["body"],
    ))
    if scan["legal_flags"]:
        names = ", ".join(f["signal"] for f in scan["legal_flags"])
        story.append(Paragraph(
            f"<b>Legal-review recommended</b> on: {names}. See flag detail "
            f"in the signals section.",
            S["legal"],
        ))
    return story


def _recovery_box(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    """Estimated recovery box for page 2. Conservative, range-only, cited.

    See roi_engine.py and docs/ROI_MODEL.md. Never a point estimate. If the
    model cannot justify the 10x floor, show qualitative language only.
    """
    rec = scan.get("recovery")
    if not rec:
        return []

    story: list = []
    story.append(Paragraph("Estimated recovery potential", S["h2"]))

    if not rec.get("qualify", False):
        # Qualitative only — drop dollar figures per ROI_MODEL.md §6.
        story.append(Paragraph(
            "Review volume and price tier sit below the threshold where we "
            "quote a specific dollar recovery range. The signals below are "
            "still actionable; this scan flags where a 30-day playbook would "
            "most likely move the needle.",
            S["body"],
        ))
        return story

    m_low = rec["monthly_low"]
    m_mid = rec["monthly_mid"]
    ann_low = rec["annualized_low"]
    roi_low = rec["roi_multiple_low"]
    roi_mid = rec["roi_multiple_mid"]
    a = rec.get("assumptions", {})

    # KPI-style row: recovery range / annualized low / ROI multiple
    label_style = ParagraphStyle(
        "roi_label", parent=S["kpi_label"], fontSize=9, textColor=MUTED,
    )
    value_style = ParagraphStyle(
        "roi_value", parent=S["kpi_value"], fontSize=22, leading=26,
        textColor=TEAL_DEEP,
    )
    small = ParagraphStyle(
        "roi_small", parent=S["muted"], fontSize=8.5, leading=11,
    )

    cells = [
        [
            Paragraph(f"${m_low:,.0f}–${m_mid:,.0f}", value_style),
            Paragraph(f"${ann_low:,.0f}", value_style),
            Paragraph(f"{roi_low}–{roi_mid}x", value_style),
        ],
        [
            Paragraph("Estimated monthly recovery range", label_style),
            Paragraph("Annualized at the conservative floor", label_style),
            Paragraph("Projected ROI on the $49 scan", label_style),
        ],
    ]
    col_w = [2.3 * inch, 2.0 * inch, 1.85 * inch]
    tbl = Table(cells, colWidths=col_w, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))

    # Plain-English explanation
    covers = a.get("covers_per_month_mid")
    check = a.get("avg_check_mid")
    reviews_pm = a.get("reviews_per_month")
    story.append(Paragraph(
        f"Estimated from ~{covers:,} monthly covers at an average check of "
        f"${check:.0f} (price tier {a.get('price_tier','$$')}, "
        f"{a.get('cuisine_hint','casual')} category). We apply a 5% revenue "
        f"lift per full star<super>1</super> and a 24% peak-hour uplift per "
        f"half-star<super>2</super>, assuming 0.1–0.2 stars of improvement "
        f"inside 60–90 days after a single recommendation lands. Manager time "
        f"saved on ≈{reviews_pm:.0f} reviews/mo using defamation-safe drafts "
        f"is added on top.<super>3</super>",
        S["body_small"],
    ))
    story.append(Paragraph(
        "Ranges, never point estimates. Recovery is conditional on executing "
        "at least one 30-day action from the plan below.",
        small,
    ))

    # Footnote sources
    citations = rec.get("citations", [])
    if citations:
        footnote = ParagraphStyle(
            "roi_footnote", parent=S["footer"], fontSize=7.5, leading=10,
            textColor=MUTED, spaceBefore=6,
        )
        for i, c in enumerate(citations[:3], start=1):
            url = c.get("url", "")
            label = c.get("label", "source")
            detail = c.get("detail", "")
            story.append(Paragraph(
                f'{i}. {label} — {detail} '
                f'(<a href="{url}" color="#01696F">{url}</a>).',
                footnote,
            ))
    return story


def _review_growth_box(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    """Review-volume growth tactics — platform-compliant, citable, and
    deliberately Yelp-aware.

    Static content across scans (tactics don't vary per business), but the
    headline pulls the business's own review count so the recommendation
    feels grounded. Every claim cites an official policy source.

    Compliance posture:
      - Google: asking is allowed but MUST be neutral and sent to ALL guests
        (no gating, no incentives).
      - Yelp: do NOT solicit. Yelp filters solicited reviews to
        "not recommended." Module explicitly recommends against Yelp asks.
      - FTC 2024 Rule: fake, incentivized, or insider reviews carry civil
        penalties up to $51,744 per violation.
    """
    biz = scan.get("business")
    if biz is None:
        return []

    story: list = []
    story.append(Paragraph("Grow review volume — the compliant way", S["h2"]))
    story.append(Paragraph(
        f"More recent reviews compound with the fixes in this scan: they "
        f"improve Google local-pack ranking, smooth out the rating when a "
        f"bad night happens, and give the 30/60/90 plan something to "
        f"measure against. You have {biz.review_count:,} lifetime reviews "
        f"today — a realistic 60-day target is +12 to +25 new Google "
        f"reviews at your current cover volume.",
        S["body"],
    ))
    story.append(Spacer(1, 6))

    # Tactic list — each one is safe on Google, never on Yelp.
    tactic_style = ParagraphStyle(
        "rg_tactic", parent=S["body_small"], fontSize=9.5, leading=13,
        leftIndent=12, bulletIndent=0, spaceAfter=4,
    )
    tactics = [
        (
            "QR card at bill drop",
            "Print a neutral \u201cHow was it? Tell us on Google\u201d QR on the "
            "check presenter. Given to <b>every</b> guest \u2014 never "
            "conditioned on a positive experience.",
        ),
        (
            "Post-meal email or SMS (opt-in only)",
            "If you capture emails at reservation, send a single neutral "
            "follow-up within 24 hours linking directly to your Google "
            "Business Profile review form. Same wording for everyone; no "
            "pre-screening for satisfaction.",
        ),
        (
            "Owner responses within 48 hours",
            "Responding to reviews \u2014 positive <i>and</i> negative \u2014 is "
            "the single biggest signal Google associates with higher local "
            "ranking. Use the defamation-safe response templates later in "
            "this scan.",
        ),
        (
            "Staff scripting, consistent across shifts",
            "Train the FOH team on one sentence: \u201cIf you had a good time, "
            "we\u2019d love a review on Google \u2014 no pressure either way.\u201d "
            "No tip-linked asks. No competitions. No rewards.",
        ),
        (
            "Google Business Profile hygiene",
            "Keep hours, photos, menu link, and reservation link current. "
            "Post a weekly update. A complete profile gets asked for "
            "reviews more often by Google itself.",
        ),
    ]
    for title, body in tactics:
        story.append(Paragraph(
            f"<b>&bull; {title}.</b> {body}",
            tactic_style,
        ))

    # Guardrail callout (visually distinct, red accent)
    warn_style = ParagraphStyle(
        "rg_warn", parent=S["body_small"], fontSize=9, leading=12,
        textColor=ERROR, leftIndent=10, spaceBefore=8, spaceAfter=4,
    )
    story.append(Paragraph(
        "<b>AVOID \u2014 these carry real penalties.</b> Do <b>not</b> "
        "solicit reviews on <b>Yelp</b> \u2014 Yelp\u2019s software actively "
        "filters solicited reviews to the \u201cnot recommended\u201d section, "
        "where they don\u2019t count toward your star rating<super>1</super>. "
        "Do not offer discounts, free items, or contest entries in "
        "exchange for reviews \u2014 Google can remove reviews and suspend "
        "your Business Profile<super>2</super>, and the FTC\u2019s 2024 Final "
        "Rule allows civil penalties up to $51,744 per violation<super>3</super>. "
        "Do not pre-screen (\u201creview gating\u201d) \u2014 asking only happy "
        "guests is an explicit policy violation.",
        warn_style,
    ))

    # Footnotes
    footnote = ParagraphStyle(
        "rg_foot", parent=S["footer"], fontSize=7.5, leading=10,
        textColor=MUTED, spaceBefore=6,
    )
    citations = [
        (
            "Yelp Support \u2014 Don\u2019t Ask for Reviews",
            "Yelp\u2019s solicitation policy and automated filter behavior",
            "https://www.yelp-support.com/article/Don-t-Ask-for-Reviews?l=en_US",
        ),
        (
            "Google Business Profile \u2014 Prohibited content",
            "No selective solicitation, no incentivized reviews, no gating",
            "https://support.google.com/contributor/answer/7400114",
        ),
        (
            "FTC Final Rule on Consumer Reviews (effective Oct 21, 2024)",
            "Bans fake, incentivized, and insider reviews; up to $51,744 "
            "per violation",
            "https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/wh_publications/client_alert_pdfs/20241009-ftc-finalizes-rule-banning-fake-reviews.pdf",
        ),
    ]
    for i, (label, detail, url) in enumerate(citations, start=1):
        story.append(Paragraph(
            f'{i}. {label} \u2014 {detail} '
            f'(<a href="{url}" color="#01696F">{url}</a>).',
            footnote,
        ))

    return story


def _signals_section(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    story = [Paragraph("Top 3 quantified signals", S["h1"])]
    story.append(Paragraph(
        "Severity is scored 1–10 from recent negative share, review "
        "recency, and evidence density. Every signal is tied to verbatim "
        "public review text — the quotes below are the only claims this "
        "document makes.",
        S["muted"],
    ))
    story.append(Spacer(1, 6))

    for i, sig in enumerate(scan["top_signals"], start=1):
        parts = []
        header_cells = [[
            Paragraph(f"{i}. {sig['label']}", S["h2"]),
            Paragraph(severity_chip(sig["severity"])[0], S["tag"]),
        ]]
        header = Table(header_cells, colWidths=[4.3 * inch, 2.0 * inch])
        header.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        parts.append(header)
        parts.append(_severity_bar(sig["severity"], width=6.3 * inch, height=6))
        parts.append(Spacer(1, 4))
        parts.append(Paragraph(
            f"Category: {sig['category']} · "
            f"Evidence count: {sig['evidence_count']} recent reviews",
            S["muted"],
        ))
        if sig.get("legal_flag"):
            parts.append(Paragraph(
                f"<b>{sig['legal_flag']}</b> · {sig['legal_note']}",
                S["legal"],
            ))
        # Evidence (up to 2 per signal on this page)
        for ev in sig["evidence"][:2]:
            quote_text = safe_para_text(ev.text.replace("\n", " ").strip())
            parts.append(Paragraph(f"\u201c{quote_text}\u201d", S["quote"]))
            parts.append(Paragraph(
                f"— {ev.source}, {ev.date} · {ev.stars:.0f}-star "
                f'(<a href="{ev.source_url}" color="#01696F">source</a>)',
                S["quote_attr"],
            ))
        parts.append(Spacer(1, 10))
        story.append(KeepTogether(parts))
    return story


def _peer_section(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    story = [Paragraph("Local peer benchmark", S["h1"])]
    story.append(Paragraph(
        "Comparison against 3 nearby peer restaurants. Ratings are pulled "
        "from public review platforms (Yelp, TripAdvisor, Google). Peers "
        "are shown at reduced emphasis so your business is the focal point.",
        S["muted"],
    ))
    story.append(Spacer(1, 6))

    chart = peer_chart_image(scan["peer_benchmark"])
    if chart:
        story.append(chart)
        story.append(Spacer(1, 8))

    # Peer detail table
    bench = scan["peer_benchmark"]
    header = ["Location", "Rating", "Reviews", "Tier"]
    rows = [header]
    for r in bench["rows"]:
        rows.append([
            r["name"],
            f"{r['rating']:.1f}",
            f"{r['review_count']}",
            r["price_tier"],
        ])
    t = Table(rows, colWidths=[3.2 * inch, 0.9 * inch, 1.0 * inch, 0.8 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL_DEEP),
        ("TEXTCOLOR", (0, 0), (-1, 0), CREAM),
        ("FONTNAME", (0, 0), (-1, 0), "DMSans"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Inter"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE, CREAM]),
        # Highlight subject row (row 1)
        ("BACKGROUND", (0, 1), (-1, 1), HexColor("#E8F2F3")),
        ("FONTNAME", (0, 1), (-1, 1), "DMSans"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Source links
    for p_idx, row in enumerate(bench["rows"]):
        if row["is_subject"]:
            continue
    peer_links = []
    for i, row in enumerate(bench["rows"]):
        if row["is_subject"]:
            continue
        # lookup peer object via scan (we stored peers only in bench rows; pull from __peers__)
    # Use peer source urls from scan's original peer list if stored.
    peers = scan.get("_peers", [])
    if peers:
        lines = []
        for p in peers:
            lines.append(
                f'· {p.name} — '
                f'<a href="{p.source_url}" color="#01696F">{p.source}</a>'
            )
        for ln in lines:
            story.append(Paragraph(ln, S["muted"]))

    delta = scan["peer_benchmark"]["delta_vs_peers"]
    direction = "gap" if delta < 0 else "lead"
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Closing half of the current {abs(delta):.2f}-star {direction} "
        f"against these peers is the commercial target for the next 90 "
        f"days.",
        S["body"],
    ))
    return story


def _plan_section(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    story = [Paragraph("30 / 60 / 90-day action plan", S["h1"])]
    story.append(Paragraph(
        "Concrete actions mapped to the top 3 signals. Owners are role-"
        "based so the plan survives staffing changes.",
        S["muted"],
    ))
    story.append(Spacer(1, 8))

    for horizon, title in [("30", "First 30 days — stabilize"),
                            ("60", "30–60 days — systematize"),
                            ("90", "60–90 days — compound")]:
        story.append(Paragraph(title, S["h2"]))
        items = scan["action_plan"].get(horizon, [])
        if not items:
            story.append(Paragraph("— no items —", S["muted"]))
            continue
        # Table: Owner · Action · Signal (wrap action text in Paragraph)
        cell_body = ParagraphStyle(
            "cell_body", parent=S["body_small"], spaceAfter=0, leading=13,
        )
        cell_bold = ParagraphStyle(
            "cell_bold", parent=S["body_small"], fontName="DMSans",
            spaceAfter=0, leading=13, textColor=TEXT,
        )
        cell_tag = ParagraphStyle(
            "cell_tag", parent=S["body_small"], fontName="DMSans",
            spaceAfter=0, leading=13, textColor=TEAL_DEEP, fontSize=9,
        )
        rows = [[
            Paragraph("Owner", ParagraphStyle(
                "hdr", fontName="DMSans", fontSize=9, leading=11,
                textColor=CREAM)),
            Paragraph("Action", ParagraphStyle(
                "hdr", fontName="DMSans", fontSize=9, leading=11,
                textColor=CREAM)),
            Paragraph("Signal", ParagraphStyle(
                "hdr", fontName="DMSans", fontSize=9, leading=11,
                textColor=CREAM)),
        ]]
        for it in items:
            rows.append([
                Paragraph(it["owner"], cell_bold),
                Paragraph(it["action"], cell_body),
                Paragraph(it["signal"], cell_tag),
            ])
        t = Table(rows, colWidths=[1.1 * inch, 3.8 * inch, 1.4 * inch],
                  repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL_DEEP),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE, CREAM]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))
    return story


def _response_drafts_section(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    story = [Paragraph("Defamation-safe response drafts", S["h1"])]
    story.append(Paragraph(
        "Five drafts tied to the most recent lower-rated public reviews. "
        "All drafts follow three rules: acknowledge without admitting "
        "fault, move the conversation off the public thread, and avoid "
        "naming any individual staff or guest. <b>Every draft requires "
        "human approval</b> before publishing.",
        S["muted"],
    ))
    story.append(Spacer(1, 8))

    for i, d in enumerate(scan["response_drafts"], start=1):
        ev = d["review"]
        block = []
        block.append(Paragraph(
            f"Draft {i} · {ev.source} · {ev.date} · {ev.stars:.0f}-star",
            S["h2"],
        ))
        block.append(Paragraph(
            f"\u201c{safe_para_text(ev.text.strip())}\u201d",
            S["quote"],
        ))
        block.append(Paragraph(
            f'<a href="{ev.source_url}" color="#01696F">Review source</a>',
            S["quote_attr"],
        ))
        if d.get("legal_flag"):
            block.append(Paragraph(
                f"<b>{d['legal_flag']}</b> · {d['legal_note']}",
                S["legal"],
            ))
        block.append(Paragraph("<b>Suggested response:</b>", S["h3"]))
        block.append(Paragraph(d["draft_text"], S["body"]))
        block.append(Paragraph(
            f"<i>Status: {d['status']}</i>",
            S["muted"],
        ))
        block.append(Spacer(1, 10))
        story.append(KeepTogether(block))
    return story


def _upsell_section(scan: dict[str, Any], S: dict[str, ParagraphStyle]) -> list:
    story = [Paragraph("Where this can go next", S["h1"])]
    story.append(Paragraph(
        "This document is the $49 One-Time Scan. JetPakt also runs "
        "continuous monitoring, multi-location dashboards, and workflow-"
        "integrated reputation operations.",
        S["body"],
    ))
    hdr_style = ParagraphStyle(
        "ladder_hdr", fontName="DMSans", fontSize=9, leading=11,
        textColor=CREAM,
    )
    tier_style = ParagraphStyle(
        "tier", fontName="DMSans", fontSize=9.5, leading=13, textColor=TEXT,
    )
    price_style = ParagraphStyle(
        "price", fontName="DMSans", fontSize=9.5, leading=13,
        textColor=TEAL_DEEP,
    )
    sum_style = ParagraphStyle(
        "summ", fontName="Inter", fontSize=9.5, leading=13, textColor=TEXT,
    )
    rows = [[
        Paragraph("Plan", hdr_style),
        Paragraph("Price", hdr_style),
        Paragraph("What's included", hdr_style),
    ]]
    for t in scan["jetpakt_ladder"]:
        rows.append([
            Paragraph(t["tier"], tier_style),
            Paragraph(t["price"], price_style),
            Paragraph(t["summary"], sum_style),
        ])
    tbl = Table(rows, colWidths=[1.6 * inch, 1.0 * inch, 3.7 * inch],
                repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL_DEEP),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE, CREAM]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, BORDER),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 14))

    c = scan["jetpakt_contact"]
    cta = (
        f"Ready to move to Monthly Essentials or run this on another "
        f"location? Reach {c['name']} at "
        f'<a href="mailto:{c["email"]}" color="#01696F">{c["email"]}</a> '
        f"or {c['phone']}."
    )
    story.append(Paragraph(cta, S["body"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "About the methodology", S["h3"],
    ))
    story.append(Paragraph(
        "JetPakt ReviewSentinel pulls verbatim public review text, maps "
        "each excerpt to a controlled signal taxonomy, and scores severity "
        "from recent negative share × recency × evidence density. No "
        "individuals are named in generated body copy. Reviewer first "
        "names may appear inside verbatim quotes because they belong to "
        "the reviewer, not the business. Response drafts are generated "
        "from templates and always require human approval before "
        "publication. Legal-flagged signals (service fees, food safety, "
        "billing disputes) should be routed through ownership and legal "
        "review prior to any public response.",
        S["body_small"],
    ))
    return story


# ---------- Document ----------

def render_scan_pdf(scan: dict[str, Any], out_path: str,
                    peers_for_links: list | None = None) -> str:
    fonts = register_fonts()
    S = build_styles(fonts)

    # Store peers for link rendering in peer section
    if peers_for_links:
        scan["_peers"] = peers_for_links

    biz = scan["business"]
    doc = BaseDocTemplate(
        out_path,
        pagesize=letter,
        title=f"JetPakt Reputation Scan — {biz.name}",
        author="Perplexity Computer",
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.65 * inch,
    )

    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height - 0.3 * inch,
        id="normal",
        showBoundary=0,
    )
    jp = scan["jetpakt_contact"]
    tmpl = PageTemplate(
        id="main",
        frames=[frame],
        onPage=lambda c, d: _page_decor(c, d, biz.name, jp),
    )
    doc.addPageTemplates([tmpl])

    story = []
    story += _cover(scan, S)
    story.append(PageBreak())
    story += _exec_summary(scan, S)
    story.append(Spacer(1, 10))
    story += _recovery_box(scan, S)
    story.append(Spacer(1, 10))
    story += _review_growth_box(scan, S)
    story.append(Spacer(1, 10))
    story += _signals_section(scan, S)
    story.append(PageBreak())
    story += _peer_section(scan, S)
    story.append(PageBreak())
    story += _plan_section(scan, S)
    story.append(PageBreak())
    story += _response_drafts_section(scan, S)
    story.append(PageBreak())
    story += _upsell_section(scan, S)

    doc.build(story)
    return out_path


if __name__ == "__main__":
    from scan_engine import westrail_fixture, Peer
    scan = westrail_fixture()
    # Re-fetch peer objects for link rendering
    # Rebuild peer list out of fixture (mirrors westrail_fixture internals)
    peers = [
        Peer(
            name="Lakewood Grill",
            address="8100 W Colfax Ave, Lakewood CO 80214",
            rating=4.6, review_count=600, price_tier="$",
            source="Uber Eats / Yelp",
            source_url="https://www.yelp.com/biz/lakewood-grill-lakewood",
        ),
        Peer(
            name="The Rusty Bucket Bar & Grill",
            address="3355 S Wadsworth Blvd Ste G101, Lakewood CO 80227",
            rating=4.1, review_count=39, price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33514-d3842452-Reviews-The_Rusty_Bucket_Bar_and_Grill-Lakewood_Colorado.html",
        ),
        Peer(
            name="Innsider Bar & Grill",
            address="7390 W Hampden Ave, Lakewood CO 80227",
            rating=4.1, review_count=152, price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33514-d1437850-Reviews-Innsider_Bar_Grill-Lakewood_Colorado.html",
        ),
    ]
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/westrail_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
