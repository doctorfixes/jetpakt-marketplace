"""
Scan #5 — Hey Kiddo (Highland, Denver).

Small-format neighborhood restaurant. Key CRM signal: 22% automatic service
fee disclosure (critical) — Legal Review Flag HIGH. Keep all response
templates factual and avoid any tip-pooling or wage claims.
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def hey_kiddo_scan():
    biz = Business(
        name="Hey Kiddo",
        address="2651 W 38th Ave",
        city="Denver, CO 80211 (Highland)",
        phone="(303) 455-4433",
        website="https://www.heykiddo.com",
        public_rating=3.4,
        review_count=487,
        negative_share_recent=0.44,   # CRM: 44% recent-negative (30d)
        review_sources={
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33388-d27976890-Reviews-Hey_Kiddo-Denver_Colorado.html",
            "Yelp": "https://www.yelp.com/biz/hey-kiddo-denver-2",
            "Google": "https://www.google.com/maps/search/Hey+Kiddo+Denver",
            "Reddit": "https://www.reddit.com/r/denverfood/comments/1r6faoz/the_22_service_fee/",
        },
        price_tier="$$$",
    )

    evidence = [
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1r6faoz/the_22_service_fee/",
            reviewer_first_name="Guest",
            date="2025-10-22",
            stars=1.0,
            text=(
                "The 22% automatic service fee was not disclosed on the "
                "menu and we weren't told at the table. Found out when "
                "the check landed. This needs to be on the menu, not a "
                "footnote on the receipt."
            ),
            signals=["service_fee_transparency", "billing_disputes"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/hey-kiddo-denver-2",
            reviewer_first_name="Guest",
            date="2025-10-09",
            stars=2.0,
            text=(
                "Birthday reservation wasn't noted and we had to ask "
                "twice for the candles we requested. Small detail but "
                "the whole pitch is 'neighborhood hospitality' and it "
                "missed."
            ),
            signals=["staffing", "server_attitude"],
        ),
        ReviewEvidence(
            source="Google",
            source_url="https://www.google.com/maps/search/Hey+Kiddo+Denver",
            reviewer_first_name="Guest",
            date="2025-09-27",
            stars=2.0,
            text=(
                "No real waiting area — we stood on the sidewalk for 25 "
                "minutes in the cold past our reservation time. Feels "
                "like a capacity-planning problem on weekends."
            ),
            signals=["service_pacing", "staffing"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d27976890-Reviews-Hey_Kiddo-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2025-09-11",
            stars=2.0,
            text=(
                "Loud — we could not hear each other at a 4-top. Cute "
                "space, but acoustics make it impossible to have a real "
                "conversation on a busy night."
            ),
            signals=["noise_ambiance"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/hey-kiddo-denver-2",
            reviewer_first_name="Guest",
            date="2025-08-30",
            stars=1.0,
            text=(
                "Showed up for a 7pm — told it would be 15, ended up 45. "
                "Then the 22% mandatory fee on top of a $180 ticket. "
                "We'll pass next time."
            ),
            signals=["service_pacing", "service_fee_transparency"],
        ),
    ]

    # Highland / LoHi neighborhood casual-dining peers.
    peers = [
        Peer(
            name="Root Down",
            address="1600 W 33rd Ave, Denver CO 80211",
            rating=4.3,
            review_count=987,
            price_tier="$$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Linger",
            address="2030 W 30th Ave, Denver CO 80211",
            rating=4.1,
            review_count=1245,
            price_tier="$$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Bar Dough",
            address="2227 W 32nd Ave, Denver CO 80211",
            rating=4.4,
            review_count=612,
            price_tier="$$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=restaurants&find_loc=Highland+Denver+CO",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="hello@heykiddo.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "phone": "303-549-1697",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = hey_kiddo_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/hey_kiddo_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
