"""
Scan #8 — City, O' City (Capitol Hill, Denver).

Long-running vegetarian/vegan institution. Key CRM signal: server
attitude + 20% automatic service charge ("BOH fee") that is
alleged in multiple reviews to not flow to tipped staff. Legal
Review Flag HIGH on CO HB25-1090 (effective Jan 1, 2026) — the law
specifically requires disclosure of how the mandatory service
charge is distributed; Yelp/TripAdvisor reviewers have publicly
questioned the current disclosure language.

IMPORTANT: Response templates must remain strictly factual and
non-accusatory regarding wage allocation. Do not quote reviewer
first names. Keep any service-fee advice as "review against
HB25-1090 disclosure requirements with your attorney."
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def city_o_city_scan():
    biz = Business(
        name="City, O' City",
        address="206 E 13th Ave",
        city="Denver, CO 80203 (Capitol Hill)",
        phone="(303) 831-6443",
        website="https://cityocitydenver.com",
        public_rating=3.4,
        review_count=1456,
        negative_share_recent=0.30,   # CRM: 30% recent-negative (30d)
        review_sources={
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33388-d1020565-Reviews-City_O_City-Denver_Colorado.html",
            "Yelp": "https://www.yelp.com/biz/city-o-city-denver",
            "Google": "https://www.google.com/maps/search/City+O+City+Denver",
            "HappyCow": "https://www.happycow.net/reviews/city-o-city-denver-10649",
            "Reddit": "https://www.reddit.com/r/denverfood/comments/1emwi4t/am_i_the_only_who_thinks_city_o_city_is_massively/",
        },
        price_tier="$$",
    )

    evidence = [
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d1020565-Reviews-City_O_City-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2023-07-13",
            stars=1.0,
            text=(
                "Terrible, rude service. Food was below average. 20% "
                "forced gratuity. The hostess saw us come in and "
                "continued having a conversation while occasionally "
                "making bored eye contact with us. In this completely "
                "empty restaurant while still waiting to be seated she "
                "went back in the kitchen. We watched the hostess do "
                "this over and over again to other customers."
            ),
            signals=["server_attitude", "service_fee_transparency"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1emwi4t/am_i_the_only_who_thinks_city_o_city_is_massively/",
            reviewer_first_name="Guest",
            date="2024-08-08",
            stars=2.0,
            text=(
                "The last few times I was there, I've had not the best "
                "service, and one of the times, the server told me that "
                "the gratuity that's added in didn't go directly to them "
                "so I should make sure to tip her. It was just awkward "
                "and off putting."
            ),
            signals=["service_fee_transparency", "server_attitude"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d1020565-Reviews-City_O_City-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2023-03-13",
            stars=2.0,
            text=(
                "The service is truly hit or miss and lacks tact, "
                "respect and friendliness. If you visit the bakery next "
                "door and order a pastry to go, you're charged an "
                "extravagant service fee for the back of house. How can "
                "you keep a straight face while attempting to charge me "
                "8 dollars and change for a brownie?"
            ),
            signals=["service_fee_transparency", "pricing_value"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d1020565-Reviews-City_O_City-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2023-07-06",
            stars=2.0,
            text=(
                "Food was mediocre. Burger was too dry, tomatoes were "
                "mealy, a measly limp slice of romaine. Jerk cauliflower "
                "just okay. Poor presentation as well as taste. Never "
                "again."
            ),
            signals=["food_quality"],
        ),
        ReviewEvidence(
            source="HappyCow",
            source_url="https://www.happycow.net/reviews/city-o-city-denver-10649",
            reviewer_first_name="Guest",
            date="2024-05-14",
            stars=2.0,
            text=(
                "Pricy, BOH fee, slow service. The menu promises a lot "
                "but the execution has dropped off compared to previous "
                "years."
            ),
            signals=["service_pacing", "service_fee_transparency", "pricing_value"],
        ),
    ]

    # Capitol Hill / Cap Hill vegetarian + casual-dining peers.
    peers = [
        Peer(
            name="Watercourse Foods",
            address="837 E 17th Ave, Denver CO 80218",
            rating=4.3,
            review_count=1012,
            price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Somebody People",
            address="1165 S Broadway, Denver CO 80210",
            rating=4.5,
            review_count=487,
            price_tier="$$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=vegan&find_loc=Capitol+Hill+Denver+CO",
        ),
        Peer(
            name="Beet Box Bakery + Cafe",
            address="1030 E 22nd Ave, Denver CO 80205",
            rating=4.5,
            review_count=624,
            price_tier="$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=vegan&find_loc=Capitol+Hill+Denver+CO",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="hello@cityocitydenver.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "phone": "303-549-1697",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = city_o_city_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/city_o_city_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
