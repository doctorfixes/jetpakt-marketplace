"""
Scan #2 — Lime on Larimer (Denver LoDo).

Uses scan_engine.build_scan() + scan_pdf.render_scan_pdf() with:
  - Verbatim reviews pulled from the business's public TripAdvisor page
  - 3 LoDo Mexican peers ranked by TripAdvisor's category listing
"""

from scan_engine import Business, Peer, ReviewEvidence, build_scan
from scan_pdf import render_scan_pdf


def lime_scan():
    biz = Business(
        name="Lime on Larimer",
        address="1424 Larimer St",
        city="Denver, CO 80202 (LoDo)",
        phone="(303) 893-5463",
        website="https://www.eatatlime.com",
        public_rating=3.2,
        review_count=732,
        negative_share_recent=0.39,   # CRM: 39% recent-negative
        review_sources={
            "TripAdvisor": "https://www.tripadvisor.com/Restaurant_Review-g33388-d379531-Reviews-Lime_At_The_Pavilion-Denver_Colorado.html",
            "Yelp": "https://www.yelp.com/biz/lime-an-american-cantina-and-tequila-bar-denver-3",
            "Google": "https://www.google.com/maps/search/Lime+on+Larimer+Denver",
        },
        price_tier="$$",
    )

    # Verbatim excerpts collected from the public TripAdvisor page above.
    # First names are those the reviewer chose to post under on TripAdvisor.
    evidence = [
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379531-Reviews-Lime_At_The_Pavilion-Denver_Colorado.html",
            reviewer_first_name="Ian",
            date="2020-02-15",
            stars=1.0,
            text=(
                "I was on my own and the restaurant was not busy but I "
                "still had to wait to be seated. My server came past and "
                "said she would be back in a minute which turned into 7 "
                "or 8 minutes. She then offered me a free tequila shot as "
                "an apology which turns out everyone got. The appatiser "
                "came out very quickly as did the entree as I put the "
                "last mouthful of my appatiser in. Overall the food was "
                "ok, nothing to write home about but the service was "
                "terrible."
            ),
            signals=["server_attitude", "service_pacing", "food_quality"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379531-Reviews-Lime_At_The_Pavilion-Denver_Colorado.html",
            reviewer_first_name="Holly",
            date="2019-09-08",
            stars=1.0,
            text=(
                "There were two servers waiting on other tables on the "
                "patio but neither acknowledged us. After 10 minutes of "
                "talking I asked my friend if maybe there were no waiters "
                "working… one of the waiters tending to the other tables "
                "on the patio turned to our table, rolled his eyes and "
                "said something with a disgusted face to his friend then "
                "turned back to the nuggets game… he acted put off by us "
                "and treated us in such a way that I was incredibly "
                "offended."
            ),
            signals=["server_attitude", "service_pacing"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379531-Reviews-Lime_At_The_Pavilion-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2019-06-20",
            stars=1.0,
            text=(
                "Yummy Watermelon Margaritas — Service was friendly and "
                "good… Food was mediocre — had a sweet potato tostada "
                "that was strange, at best. Margaritas were great! A "
                "little pricey for the food but I would go again just "
                "for the margaritas and locale."
            ),
            signals=["food_quality", "pricing_value"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379531-Reviews-Lime_At_The_Pavilion-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2019-04-10",
            stars=2.0,
            text=(
                "Had lunch there and three happy hours outings. The food "
                "is average, the chips are funky tasting but addictive "
                "and the margaritas are tasty. Service at lunch was "
                "horrible, it took us two hours from start to finish."
            ),
            signals=["service_pacing", "food_quality"],
        ),
        ReviewEvidence(
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379531-Reviews-Lime_At_The_Pavilion-Denver_Colorado.html",
            reviewer_first_name="Guest",
            date="2019-01-22",
            stars=2.0,
            text=(
                "I stopped at Lime for some drinks and dinner. It was "
                "not busy and after waiting over 30 minutes and trying "
                "to flag a waitress down just to get an order is "
                "unacceptable. The waitresses stand around chatting. Go "
                "somewhere else where they care and want your business."
            ),
            signals=["server_attitude", "service_pacing"],
        ),
    ]

    # 3 LoDo Mexican peers — TripAdvisor's Best Mexican Food in LoDo ranking
    peers = [
        Peer(
            name="Tamayo (Richard Sandoval)",
            address="1400 Larimer St, Denver CO 80202",
            rating=4.1,
            review_count=763,
            price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurant_Review-g33388-d379429-Reviews-Tamayo_By_Chef_Richard_Sandoval-Denver_Colorado.html",
        ),
        Peer(
            name="Illegal Pete's LoDo",
            address="1530 16th St Mall, Denver CO 80202",
            rating=4.3,
            review_count=302,
            price_tier="$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-c29-zfn20483809-Denver_Colorado.html",
        ),
        Peer(
            name="Blue Agave Grill",
            address="1201 16th St Mall, Denver CO 80202",
            rating=4.3,
            review_count=212,
            price_tier="$$",
            source="TripAdvisor",
            source_url="https://www.tripadvisor.com/Restaurants-g33388-c29-zfn20483809-Denver_Colorado.html",
        ),
    ]

    return (build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="info@eatalime.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    ), peers)


if __name__ == "__main__":
    scan, peers = lime_scan()
    out = render_scan_pdf(
        scan,
        "/home/user/workspace/denver_leadgen/output/scans/lime_on_larimer_scan_v2.pdf",
        peers_for_links=peers,
    )
    print(f"Wrote {out}")
