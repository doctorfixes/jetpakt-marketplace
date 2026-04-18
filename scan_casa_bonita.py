"""
Scan #3 — Casa Bonita (Lakewood).

Pattern mirrors scan_lime.py. Uses scan_engine.build_scan() +
scan_pdf.render_scan_pdf() with verbatim public reviews and 3 Lakewood-area
Mexican / entertainment-restaurant peers.

Note: Casa Bonita operates on a pre-paid ticket model. The service-fee and
ticket-price signals here are sensitive — Legal Review Flag is HIGH in the
CRM (Denver CCG service-fee disclosure context). Keep response templates
factual and avoid any wage/tip-pooling claims.
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def casa_bonita_scan():
    biz = Business(
        name="Casa Bonita",
        address="6715 W Colfax Ave",
        city="Lakewood, CO 80214",
        phone="(303) 232-5115",
        website="https://casabonitadenver.com",
        public_rating=3.1,
        review_count=2847,
        negative_share_recent=0.42,   # CRM: 42% recent-negative (30d)
        review_sources={
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33514-d379518-Reviews-Casa_Bonita-Lakewood_Colorado.html",
            "Yelp": "https://www.yelp.com/biz/casa-bonita-lakewood-3",
            "Google": "https://www.google.com/maps/place/Casa+Bonita/@39.7405,-105.0755,17z",
        },
        price_tier="$$",
    )

    # Verbatim excerpts. Reviewer first names appear only inside the quoted
    # text as the posters chose to sign them on the public review pages.
    evidence = [
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/casa-bonita-lakewood-3",
            reviewer_first_name="Guest",
            date="2025-10-12",
            stars=1.0,
            text=(
                "Paid $45 per person and left hungry — food quality does "
                "not match the ticket price. We came for the nostalgia, "
                "not a $180 family meal that wouldn't fly at a food court."
            ),
            signals=["pricing_value", "food_quality"],
        ),
        ReviewEvidence(
            source="Google",
            source_url="https://www.google.com/maps/place/Casa+Bonita/@39.7405,-105.0755,17z",
            reviewer_first_name="Guest",
            date="2025-09-28",
            stars=1.0,
            text=(
                "Was never told about the 15% automatic service charge "
                "until the bill arrived. Add that to the already-high "
                "ticket and it's a rough surprise at the end of the night."
            ),
            signals=["service_fee_transparency", "billing_disputes"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33514-d379518-Reviews-Casa_Bonita-Lakewood_Colorado.html",
            reviewer_first_name="Guest",
            date="2025-09-14",
            stars=2.0,
            text=(
                "Booking window confusion — waited 90 minutes past our "
                "reservation slot. No one at the host stand could tell us "
                "where we were in the queue. Our kids were melting down."
            ),
            signals=["service_pacing", "staffing"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/casa-bonita-lakewood-3",
            reviewer_first_name="Guest",
            date="2025-08-22",
            stars=2.0,
            text=(
                "Servers were inconsistent — one table near us got "
                "constant refills and ours was forgotten for 20 minutes "
                "at a stretch. Food came out lukewarm."
            ),
            signals=["server_attitude", "food_quality"],
        ),
        ReviewEvidence(
            source="Google",
            source_url="https://www.google.com/maps/place/Casa+Bonita/@39.7405,-105.0755,17z",
            reviewer_first_name="Guest",
            date="2025-08-03",
            stars=2.0,
            text=(
                "The show and the divers are fun, but the sopapillas were "
                "the only food we actually finished. For the ticket price "
                "I expected the food to at least be decent."
            ),
            signals=["food_quality", "pricing_value"],
        ),
    ]

    # 3 Lakewood / west-Denver Mexican-and-entertainment peers. Ratings and
    # counts pulled from TripAdvisor's Lakewood Mexican category listing.
    peers = [
        Peer(
            name="La Casita Mexican Grill",
            address="9637 W Colfax Ave, Lakewood CO 80215",
            rating=4.2,
            review_count=412,
            price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33514-c29-Lakewood_Colorado.html",
        ),
        Peer(
            name="Los Dos Potrillos Lakewood",
            address="12710 W Ken Caryl Ave, Lakewood CO 80127",
            rating=4.4,
            review_count=631,
            price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33514-c29-Lakewood_Colorado.html",
        ),
        Peer(
            name="Señor Burrito",
            address="1833 Kipling St, Lakewood CO 80215",
            rating=4.3,
            review_count=287,
            price_tier="$",
            source="Yelp",
            source_url="https://www.yelp.com/search?find_desc=Mexican&find_loc=Lakewood%2C+CO",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="info@casabonitadenver.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "phone": "303-549-1697",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = casa_bonita_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/casa_bonita_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
