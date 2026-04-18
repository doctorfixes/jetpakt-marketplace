"""
Scan #9 — Big Daddy's Pizza, West Colfax (Denver).

West Colfax late-night pizza/delivery spot. CRM flag: "inconsistent recent
guest experience." Evidence cluster skews heavily toward delivery pacing,
billing/refund disputes, and food-quality inconsistency. One Yelp reviewer
explicitly describes a double-charge refund dispute — legal-flag MEDIUM on
billing. Reddit thread r/denverfood names the Colfax location as the weak
franchise in the chain (Littleton/Lakewood locations rated better).
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def big_daddys_scan():
    biz = Business(
        name="Big Daddy's Pizza — West Colfax",
        address="4250 W Colfax Ave",
        city="Denver, CO 80204 (West Colfax / Sloan's Lake)",
        phone="(720) 287-0577",
        website="https://www.bigdaddyspizza.com",
        public_rating=2.6,               # TripAdvisor 2.6; Yelp brand avg 2.4; CRM 3.2 is blended
        review_count=234,                # Yelp location-specific count
        negative_share_recent=0.52,      # heavy recent-negative skew on Yelp + Reddit
        review_sources={
            "Yelp": "https://www.yelp.com/biz/big-daddys-pizza-denver-3",
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33388-d10941725-Reviews-Big_Daddy_s_Pizza-Denver_Colorado.html",
            "Reddit": "https://www.reddit.com/r/denverfood/comments/125n7d2/worst_pizza_in_the_metro_area/",
            "Google": "https://www.google.com/maps/search/Big+Daddy%27s+Pizza+4250+W+Colfax+Denver",
        },
        price_tier="$$",
    )

    evidence = [
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/big-daddys-pizza-denver-3",
            reviewer_first_name="Julia",
            date="2024-10-30",
            stars=1.0,
            text=(
                "TLDR: charged me twice instead of refunding money for food "
                "that wasn't delivered. The food I ordered was never "
                "delivered. I called the next day and the man who answered "
                "said he would refund the money and it would show up in a "
                "few days. Instead of refunding the money he charged me "
                "AGAIN. I am now having to file a claim through my bank "
                "disputing all the charges."
            ),
            signals=["billing_disputes", "service_pacing"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/big-daddys-pizza-denver-3",
            reviewer_first_name="Guest",
            date="2024-08-14",
            stars=2.0,
            text=(
                "Pizza is very average, it's fine if you don't need any "
                "specialty toppings or after a night of drinking. It took "
                "forever for them to deliver the pizza even though I live "
                "down the block. They forgot to give me the ranch and "
                "garlic butter that I paid for. Next time I will be "
                "ordering elsewhere."
            ),
            signals=["service_pacing", "food_quality"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/big-daddys-pizza-denver-3",
            reviewer_first_name="Guest",
            date="2024-06-02",
            stars=1.0,
            text=(
                "I love when my order arrives missing what I ordered and "
                "paid extra for. Missing the pepperoni and couldn't get an "
                "answer on what they would do to fix it."
            ),
            signals=["billing_disputes", "food_quality"],
        ),
        ReviewEvidence(
            source="Reddit",
            source_url="https://www.reddit.com/r/denverfood/comments/125n7d2/worst_pizza_in_the_metro_area/",
            reviewer_first_name="Guest",
            date="2023-03-29",
            stars=1.0,
            text=(
                "Big Daddy's on Colfax. It made 7-11 pizza look amazing and "
                "the service was equally awful. I had a terrible experience "
                "at the West Colfax location — soggy dough, all the "
                "toppings dumped in the middle, and they even messed up "
                "delivery and I ended up going in to pick up the pizza "
                "after waiting over an hour past the delivery time."
            ),
            signals=["food_quality", "service_pacing"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/big-daddys-pizza-denver-3",
            reviewer_first_name="Guest",
            date="2024-03-11",
            stars=1.0,
            text=(
                "Ordered a pizza via GrubHub. Delivery window was 3:30-3:50. "
                "I called at 4:15 to see where the order was and they never "
                "answered the phone. I called 8 times in a row. Canceled "
                "the order and at 4:20 they called and asked if I was "
                "willing to wait another 30-40 minutes."
            ),
            signals=["service_pacing", "server_attitude"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d10941725-Reviews-Big_Daddy_s_Pizza-Denver_Colorado.html",
            reviewer_first_name="Jerry",
            date="2025-05-15",
            stars=1.0,
            text=(
                "I received a Happy Birthday reward via email. I printed "
                "the coupon for a birthday BOGO. The store that had its "
                "address printed on it refused to honor it. One of my worst "
                "customer service experiences."
            ),
            signals=["server_attitude", "billing_disputes"],
        ),
    ]

    # West Colfax / Sloan's Lake pizza peers — same daypart, same delivery radius.
    peers = [
        Peer(
            name="Cart-Driver (LoHi)",
            address="2500 Larimer St / 2200 W 30th Ave, Denver CO",
            rating=4.5,
            review_count=1087,
            price_tier="$$",
            source="Yelp",
            source_url="https://www.yelp.com/biz/cart-driver-denver",
        ),
        Peer(
            name="Sexy Pizza — Jefferson Park",
            address="2460 Eliot St, Denver CO 80211",
            rating=4.2,
            review_count=612,
            price_tier="$$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=pizza&find_loc=West+Colfax+Denver+CO",
        ),
        Peer(
            name="Benny Blanco's Pizza",
            address="2550 W 44th Ave, Denver CO 80211",
            rating=4.3,
            review_count=487,
            price_tier="$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=pizza&find_loc=West+Colfax+Denver+CO",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="",  # CRM has no email; outreach will go via phone + mail
        jetpakt_contact={
            "name": "Ryan B.",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = big_daddys_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/big_daddys_scan_v1.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
