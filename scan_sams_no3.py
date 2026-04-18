"""
Scan #7 — Sam's No. 3 (Downtown Denver / CBD).

Founded 1927, returned downtown 2003. Key CRM signal: cleanliness +
recent 3.33% "junk fee" controversy with 200+ upvote Reddit thread.
Legal Review Flag HIGH: Colorado HB25-1090 (effective Jan 1, 2026)
requires disclosure of mandatory service-charge amount AND distribution
— Reddit users explicitly cite this law by name in complaints.
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def sams_no3_scan():
    biz = Business(
        name="Sam's No. 3 — Downtown",
        address="1500 Curtis St",
        city="Denver, CO 80202 (CBD / Downtown)",
        phone="(303) 534-1927",
        website="https://samsno3.com",
        public_rating=3.4,
        review_count=3289,
        negative_share_recent=0.27,   # CRM: 27% recent-negative (30d)
        review_sources={
            "Yelp": "https://www.yelp.com/biz/sams-no-3-downtown-denver",
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33388-Reviews-Sam_s_No_3-Denver_Colorado.html",
            "Google": "https://www.google.com/maps/search/Sams+No+3+Downtown+Denver",
            "Reddit": "https://www.reddit.com/r/denverfood/comments/1l6n91z/sams_no3_gone_evil_w_333_junk_fee/",
            "BBB": "https://www.bbb.org/us/co/denver/profile/restaurants/sams-no-3-downtown-1296-90223478",
        },
        price_tier="$$",
    )

    evidence = [
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1l6n91z/sams_no3_gone_evil_w_333_junk_fee/",
            reviewer_first_name="Guest",
            date="2025-06-08",
            stars=1.0,
            text=(
                "Today I learned that my longstanding fave, Sam's No. 3 "
                "downtown, has added one of those pernicious junk fees. "
                "Now that the good guys have adopted these practices, "
                "are we doomed to see these fees persist in Denver?"
            ),
            signals=["service_fee_transparency", "billing_disputes"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1l6n91z/sams_no3_gone_evil_w_333_junk_fee/",
            reviewer_first_name="Guest",
            date="2025-06-09",
            stars=1.0,
            text=(
                "Sam's No. 3 lacks sufficient transparency regarding the "
                "allocation of its mandatory service charge. Colorado "
                "HB25-1090 requires food and beverage businesses to "
                "clearly state the total price and provide information "
                "on how the mandatory service charge is divided among "
                "employees."
            ),
            signals=["service_fee_transparency", "billing_disputes"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/sams-no-3-downtown-denver",
            reviewer_first_name="Guest",
            date="2024-07-19",
            stars=2.0,
            text=(
                "The food was ok. The service was ok except we had to "
                "remind them about our drinks, refills, and they didn't "
                "hear us when we said we wanted a plain cheeseburger or "
                "a medium rare steak (came out well done)."
            ),
            signals=["service_pacing", "food_quality"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1aqszil/what_is_it_about_sams_no_3/",
            reviewer_first_name="Guest",
            date="2024-02-14",
            stars=2.0,
            text=(
                "Personally I feel the place is moldy and smells like "
                "skunky beer. Everything about the place is 30 years "
                "behind."
            ),
            signals=["cleanliness", "noise_ambiance"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/1l6n91z/sams_no3_gone_evil_w_333_junk_fee/",
            reviewer_first_name="Guest",
            date="2025-06-10",
            stars=1.0,
            text=(
                "In recent years, they have increased their prices more "
                "than any other dining establishment I've encountered "
                "in Denver. A simple breakfast — 2 eggs, potatoes, and "
                "bacon — is $15 now. That is pretty overpriced for what "
                "you get already. Another hidden fee on top of that "
                "overpriced breakfast is maddening."
            ),
            signals=["pricing_value", "service_fee_transparency"],
        ),
    ]

    # Downtown Denver / CBD breakfast-diner peers.
    peers = [
        Peer(
            name="Snooze, an A.M. Eatery (Ballpark)",
            address="2262 Larimer St, Denver CO 80205",
            rating=4.4,
            review_count=3521,
            price_tier="$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=breakfast&find_loc=Downtown+Denver+CO",
        ),
        Peer(
            name="Pete's Kitchen",
            address="1962 E Colfax Ave, Denver CO 80206",
            rating=4.2,
            review_count=2134,
            price_tier="$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Syrup Denver",
            address="1550 Blake St #140, Denver CO 80202",
            rating=4.3,
            review_count=1487,
            price_tier="$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=breakfast&find_loc=Downtown+Denver+CO",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="downtown@samsno3.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "phone": "303-549-1697",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = sams_no3_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/sams_no3_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
