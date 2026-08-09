"""
In-memory mock dataset for PlayNest.

Every function here mirrors what a repository layer would expose
(`get_all`, `get_by_id`, `filter`) so that plugging in a real database
later is a drop-in replacement — nothing in routes/ or services/*_service.py
needs to know the data used to live in a Python list.
"""

from models.turf import Turf, Review

SPORTS = [
    {"name": "Football", "icon": "fa-futbol", "color": "#10B981"},
    {"name": "Cricket", "icon": "fa-baseball", "color": "#3B82F6"},
    {"name": "Badminton", "icon": "fa-table-tennis-paddle-ball", "color": "#39FF88"},
    {"name": "Basketball", "icon": "fa-basketball", "color": "#F59E0B"},
    {"name": "Volleyball", "icon": "fa-volleyball", "color": "#EC4899"},
    {"name": "Tennis", "icon": "fa-baseball-bat-ball", "color": "#8B5CF6"},
    {"name": "Box Cricket", "icon": "fa-cube", "color": "#06B6D4"},
    {"name": "Pickleball", "icon": "fa-table-tennis-paddle-ball", "color": "#EF4444"},
]

CITIES = ["Mumbai", "Pune", "Bengaluru", "Delhi", "Hyderabad", "Kolhapur", "Chennai", "Ahmedabad"]

ALL_FACILITIES = [
    "Parking", "Washroom", "Changing Room", "Floodlights",
    "Cafe", "Locker", "WiFi", "Indoor", "Outdoor",
]

_TURF_SEED = [
    dict(name="GreenTurf Arena", city="Mumbai", area="Andheri West",
         sports=["Football", "Box Cricket"], price=1400, rating=4.8, reviews=214,
         facilities=["Parking", "Washroom", "Floodlights", "Cafe", "WiFi"],
         indoor=False, owner="Rohan Mehta",
         img="photo-1489944440615-453fc2b6a9a9"),
    dict(name="Skyline Sports Club", city="Mumbai", area="Powai",
         sports=["Badminton", "Tennis"], price=900, rating=4.6, reviews=132,
         facilities=["Parking", "Changing Room", "Locker", "WiFi", "Indoor"],
         indoor=True, owner="Ayesha Khan",
         img="photo-1554068865-24cecd4e34b8"),
    dict(name="Victory Ground", city="Pune", area="Kothrud",
         sports=["Cricket", "Football"], price=1200, rating=4.7, reviews=189,
         facilities=["Parking", "Washroom", "Floodlights", "Outdoor"],
         indoor=False, owner="Suresh Patil",
         img="photo-1459865264687-595d652de67e"),
    dict(name="Urban Smash Badminton", city="Pune", area="Baner",
         sports=["Badminton", "Pickleball"], price=700, rating=4.9, reviews=301,
         facilities=["Parking", "Washroom", "Changing Room", "WiFi", "Indoor", "Cafe"],
         indoor=True, owner="Neha Joshi",
         img="photo-1517649763962-0c623066013b"),
    dict(name="Elite Hoops Court", city="Bengaluru", area="Koramangala",
         sports=["Basketball", "Volleyball"], price=1000, rating=4.5, reviews=98,
         facilities=["Parking", "Floodlights", "Locker", "Outdoor"],
         indoor=False, owner="Karthik Reddy",
         img="photo-1546519638-68e109498ffc"),
    dict(name="The Football Factory", city="Bengaluru", area="Whitefield",
         sports=["Football"], price=1600, rating=4.9, reviews=412,
         facilities=["Parking", "Washroom", "Floodlights", "Cafe", "WiFi", "Changing Room"],
         indoor=False, owner="Arjun Nair",
         img="photo-1524015368236-4200aa6dda23"),
    dict(name="CourtSide Pickleball Hub", city="Delhi", area="Saket",
         sports=["Pickleball", "Badminton"], price=850, rating=4.7, reviews=156,
         facilities=["Parking", "Washroom", "Indoor", "WiFi", "Cafe"],
         indoor=True, owner="Priya Malhotra",
         img="photo-1626224583764-f87db24ac4ea"),
    dict(name="Capital Cricket Nets", city="Delhi", area="Dwarka",
         sports=["Cricket", "Box Cricket"], price=1100, rating=4.4, reviews=87,
         facilities=["Parking", "Floodlights", "Washroom", "Outdoor"],
         indoor=False, owner="Vikram Singh",
         img="photo-1531415074968-036ba1b575da"),
    dict(name="Hyderabad Turf Republic", city="Hyderabad", area="Gachibowli",
         sports=["Football", "Cricket", "Volleyball"], price=1300, rating=4.6, reviews=176,
         facilities=["Parking", "Washroom", "Floodlights", "Locker", "Cafe"],
         indoor=False, owner="Sandeep Rao",
         img="photo-1489944440615-453fc2b6a9a9"),
    dict(name="Rankala Sports Arena", city="Kolhapur", area="Rankala",
         sports=["Football", "Badminton", "Box Cricket"], price=800, rating=4.8, reviews=143,
         facilities=["Parking", "Washroom", "Changing Room", "Floodlights", "WiFi"],
         indoor=False, owner="Mahesh Kulkarni",
         img="photo-1522778119026-d647f0596c20"),
    dict(name="Ace Tennis Courts", city="Chennai", area="Adyar",
         sports=["Tennis"], price=950, rating=4.5, reviews=112,
         facilities=["Parking", "Washroom", "Floodlights", "Outdoor", "Cafe"],
         indoor=False, owner="Lakshmi Iyer",
         img="photo-1554068865-24cecd4e34b8"),
    dict(name="Sabarmati Sports Zone", city="Ahmedabad", area="Bodakdev",
         sports=["Cricket", "Football", "Basketball"], price=1250, rating=4.6, reviews=163,
         facilities=["Parking", "Washroom", "Floodlights", "Locker", "WiFi", "Indoor"],
         indoor=True, owner="Kunal Shah",
         img="photo-1517649763962-0c623066013b"),
]

_SAMPLE_REVIEWS = [
    ("Aditya R.", 5, "Turf quality is amazing, booked within seconds and the PlayPass made entry effortless."),
    ("Meera S.", 4.5, "Great lighting for night games. Parking gets full early on weekends though."),
    ("Farhan A.", 5, "Best badminton court in the area, staff is super courteous."),
    ("Sneha K.", 4, "Good facilities overall, wish the cafe had more options."),
    ("Rahul D.", 5, "Booking on PlayNest is ridiculously smooth. Slot picker is chef's kiss."),
]


def _build_turfs():
    turfs = []
    for i, seed in enumerate(_TURF_SEED, start=1):
        turf_id = f"TRF{i:03d}"
        img_id = seed["img"]
        hero = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=1200&q=80"
        gallery = [
            f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=800&q=80&sat=-10",
            f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=800&q=80&blend=000000&blend-alpha=10",
            f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=800&q=80",
        ]
        reviews = [
            Review(author=a, rating=r, comment=c, date="2026-06-1{}".format((idx % 9) + 1))
            for idx, (a, r, c) in enumerate(_SAMPLE_REVIEWS[: 3 + (i % 3)])
        ]
        turfs.append(
            Turf(
                id=turf_id,
                name=seed["name"],
                city=seed["city"],
                area=seed["area"],
                sports=seed["sports"],
                price_per_hour=seed["price"],
                rating=seed["rating"],
                review_count=seed["reviews"],
                facilities=seed["facilities"],
                indoor=seed["indoor"],
                hero_image=hero,
                gallery=gallery,
                description=(
                    f"{seed['name']} is a premium {'indoor' if seed['indoor'] else 'outdoor'} "
                    f"facility in {seed['area']}, {seed['city']}, purpose-built for "
                    f"{', '.join(seed['sports'])}. Regulation-grade surface, professional-grade "
                    f"floodlighting, and a booking-friendly layout make it a favourite among "
                    f"regulars on PlayNest."
                ),
                opening_hours="6:00 AM – 11:00 PM, all days",
                owner_id=f"OWN{i:03d}",
                owner_name=seed["owner"],
                lat=19.07 + (i * 0.01),
                lng=72.87 + (i * 0.01),
                verified=True,
                reviews=reviews,
            )
        )
    return turfs


TURFS = _build_turfs()
