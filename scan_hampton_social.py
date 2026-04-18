"""
Scan #4 — The Hampton Social (Union Station, Denver).

Chain location (multi-unit operator). Key CRM signals: peak-hour pacing
(critical), host handling (high), billing discrepancy (high). Legal Review
Flag on billing-discrepancy items — keep response templates factual.
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def hampton_social_scan():
    biz = Business(
        name="The Hampton Social — Denver",
        address="1700 Wewatta St",
        city="Denver, CO 80202 (Union Station)",
        phone="(720) 893-8400",
        website="https://www.thehamptonsocial.com/denver",
        public_rating=3.3,
        review_count=1412,
        negative_share_recent=0.37,   # CRM: 37% recent-negative (30d)
        review_sources={
            "Yelp": "https://www.yelp.com/biz/the-hampton-social-denver-2",
            "Google": "https://www.google.com/maps/search/The+Hampton+Social+Denver",
            "Reddit": "https://www.reddit.com/r/denverfood/comments/1scrcmj/whats_the_worst_restaurant_in_denver_that_youve/",
        },
        price_tier="$$$",
    )

    evidence = [
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/the-hampton-social-denver-2",
            reviewer_first_name="Guest",
            date="2025-10-18",
            stars=1.0,
            text=(
                "Waited 45 minutes for entrées after apps, then the bill "
                "had two drinks we never ordered. Manager adjusted it but "
                "the whole thing killed the night — it was our anniversary."
            ),
            signals=["service_pacing", "billing_disputes"],
        ),
        ReviewEvidence(
            source="Google",
            source_url="https://www.google.com/maps/search/The+Hampton+Social+Denver",
            reviewer_first_name="Guest",
            date="2025-10-05",
            stars=2.0,
            text=(
                "Host was dismissive when we asked about our reservation "
                "time — we had a 7:15 and were still standing at 8:00 "
                "with no updates. Felt like we were an inconvenience."
            ),
            signals=["staffing", "server_attitude"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1scrcmj/whats_the_worst_restaurant_in_denver_that_youve/",
            reviewer_first_name="Guest",
            date="2025-09-20",
            stars=2.0,
            text=(
                "Something feels off about the 5-star reviews — tone and "
                "phrasing are suspiciously uniform. The in-person "
                "experience didn't come close to matching what you see "
                "on Google."
            ),
            signals=["server_attitude"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/the-hampton-social-denver-2",
            reviewer_first_name="Guest",
            date="2025-09-08",
            stars=1.0,
            text=(
                "Brunch rush was chaos — we were told a 15-minute wait, "
                "sat down 55 minutes later, and then waited another 40 "
                "for mimosas. Kitchen clearly overwhelmed on Saturdays."
            ),
            signals=["service_pacing", "staffing"],
        ),
        ReviewEvidence(
            source="Google",
            source_url="https://www.google.com/maps/search/The+Hampton+Social+Denver",
            reviewer_first_name="Guest",
            date="2025-08-24",
            stars=2.0,
            text=(
                "Rosé all day, sure — but check your bill. We were "
                "charged for a bottle we ordered by the glass. This is "
                "the second time in three visits."
            ),
            signals=["billing_disputes", "pricing_value"],
        ),
    ]

    # LoDo / Union Station American-brunch peers from TripAdvisor and Yelp.
    peers = [
        Peer(
            name="Stoic & Genuine",
            address="1701 Wynkoop St, Denver CO 80202",
            rating=4.3,
            review_count=842,
            price_tier="$$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Mercantile Dining & Provision",
            address="1701 Wynkoop St Ste 155, Denver CO 80202",
            rating=4.2,
            review_count=726,
            price_tier="$$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Jovanina's Broken Italian",
            address="1520 Blake St, Denver CO 80202",
            rating=4.4,
            review_count=518,
            price_tier="$$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=brunch&find_loc=LoDo+Denver+CO",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="denver@thehamptonsocial.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = hampton_social_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/hampton_social_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
