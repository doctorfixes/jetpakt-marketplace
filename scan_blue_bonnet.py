"""
Scan #6 — Blue Bonnet (South Broadway / Baker, Denver).

50-year Denver Mexican institution. Key CRM signal: pricing/value decline
+ mandatory service charge ("2.5% extra charge for workers") referenced
in multiple Yelp reviews. Legal Review Flag HIGH on CO HB25-1090
(Junk Fees Law, effective Jan 1, 2026) — mandatory service-charge
distribution must be disclosed.
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def blue_bonnet_scan():
    biz = Business(
        name="Blue Bonnet Restaurant",
        address="457 S Broadway",
        city="Denver, CO 80209 (Baker / South Broadway)",
        phone="(303) 778-0147",
        website="https://bluebonnetrestaurant.com",
        public_rating=3.4,
        review_count=1638,
        negative_share_recent=0.30,   # CRM: 30% recent-negative (30d)
        review_sources={
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33388-d379547-Reviews-Blue_Bonnet_Restaurant-Denver_Colorado.html",
            "Yelp": "https://www.yelp.com/biz/blue-bonnet-restaurant-denver",
            "Google": "https://www.google.com/maps/search/Blue+Bonnet+Restaurant+Denver",
            "Reddit": "https://www.reddit.com/r/Denver/comments/bl16h0/worst_mexican_restaurant/",
        },
        price_tier="$$",
    )

    evidence = [
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/blue-bonnet-restaurant-denver",
            reviewer_first_name="Guest",
            date="2025-01-08",
            stars=2.0,
            text=(
                "Average price $23.00. Over $125 for family of four with "
                "tax and tip. They also include the BS kitchen surcharge. "
                "Staff is friendly, but bottom line is prices. Too many "
                "Mexican restaurants at almost half the price."
            ),
            signals=["pricing_value", "service_fee_transparency"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/blue-bonnet-restaurant-denver",
            reviewer_first_name="Guest",
            date="2024-08-25",
            stars=2.0,
            text=(
                "The chips tasted old and cold — the salsa was bland. "
                "The cheese dip was the weirdest thing I've ever seen, "
                "orange and super stringy. To end the night we saw one "
                "of the waitresses packing up the baskets of chips into "
                "bins — maybe this is standard practice but this would "
                "explain why the chips were cold and tasted old."
            ),
            signals=["food_quality", "cleanliness"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379547-Reviews-Blue_Bonnet_Restaurant-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2025-01-15",
            stars=2.0,
            text=(
                "Have been coming here 30 years and pricing has gone up "
                "but sadly food quality has gone way down. Had an issue "
                "with our meal and our waiter was the one who offered to "
                "fix it as the manager walked around and avoided our "
                "table. Not asking for royal treatment but own a mistake."
            ),
            signals=["food_quality", "server_attitude"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/blue-bonnet-restaurant-denver",
            reviewer_first_name="Guest",
            date="2024-11-02",
            stars=2.0,
            text=(
                "3 of us had burnt chili rellenos. I had a watery "
                "margarita, probably one of the worst ones I have ever "
                "had. Then the 2.5% extra charge for workers was the "
                "final straw."
            ),
            signals=["service_fee_transparency", "food_quality"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/xoohth/worst_of_denver_recommendations/",
            reviewer_first_name="Guest",
            date="2024-09-20",
            stars=2.0,
            text=(
                "A decades-old, family-run Denver institution with some "
                "of the blandest Mexican food you can find. It's sad "
                "because 10-15 years ago it was so good."
            ),
            signals=["food_quality", "pricing_value"],
        ),
    ]

    # South Broadway / Baker Mexican-restaurant peers.
    peers = [
        Peer(
            name="Tacos Tequila Whiskey",
            address="1514 York St, Denver CO 80206",
            rating=4.1,
            review_count=1245,
            price_tier="$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=Mexican&find_loc=South+Broadway+Denver+CO",
        ),
        Peer(
            name="El Taco de Mexico",
            address="714 Santa Fe Dr, Denver CO 80204",
            rating=4.5,
            review_count=1487,
            price_tier="$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
        Peer(
            name="Adelitas Cocina y Cantina",
            address="1294 S Broadway, Denver CO 80210",
            rating=4.2,
            review_count=1012,
            price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-Denver_Colorado.html",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="bluebonnetcafe1@yahoo.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = blue_bonnet_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/blue_bonnet_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
