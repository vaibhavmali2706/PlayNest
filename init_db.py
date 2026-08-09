import uuid
from datetime import datetime, timedelta
import bcrypt
from app import create_app
from extensions import db
from models import (
    State, District, City, Role, Permission, User, Owner, OwnerImage,
    Sport, Amenity, Turf, TurfImage, Review, ReviewReply, Booking, BookingTicket, BookingHistory,
    SlotStatus, CustomerRestriction, CustomerReport, Notification
)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Maharashtra location hierarchy
MAHARASHTRA_LOCATIONS = {
    "Mumbai City": ["Mumbai"],
    "Mumbai Suburban": ["Andheri", "Bandra", "Borivali", "Kurla", "Ghatkopar", "Malad"],
    "Thane": ["Thane", "Kalyan", "Dombivli", "Ulhasnagar", "Bhiwandi", "Mira-Bhayandar", "Navi Mumbai"],
    "Pune": ["Pune", "Pimpri-Chinchwad", "Kothrud", "Baner", "Hinjawadi", "Hadapsar", "Chinchwad"],
    "Nashik": ["Nashik", "Malegaon", "Manmad", "Deolali"],
    "Nagpur": ["Nagpur", "Kamptee", "Umred"],
    "Kolhapur": ["Kolhapur", "Ichalkaranji", "Jaysingpur", "Ajra", "Gadhinglaj"],
    "Aurangabad": ["Aurangabad", "Chhatrapati Sambhajinagar", "Vaijapur", "Kannad"],
    "Solapur": ["Solapur", "Barshi", "Pandharpur"],
    "Amravati": ["Amravati", "Achalpur", "Anjangaon"],
    "Nanded": ["Nanded", "Degloor", "Loha"],
    "Satara": ["Satara", "Karad", "Phaltan", "Wai"],
    "Sangli": ["Sangli", "Miraj", "Kupwad", "Islampur"],
    "Ahmednagar": ["Ahmednagar", "Sangamner", "Shrirampur", "Kopargaon"],
    "Jalgaon": ["Jalgaon", "Bhusawal", "Amalner", "Chalisgaon"],
    "Akola": ["Akola", "Akot", "Balapur"],
    "Latur": ["Latur", "Udgir", "Nilanga"],
    "Dhule": ["Dhule", "Shirpur", "Dondaicha"],
    "Chandrapur": ["Chandrapur", "Ballarpur", "Warora"],
    "Parbhani": ["Parbhani", "Gangakhed", "Pathri"],
    "Jalna": ["Jalna", "Bhokardan", "Partur"],
    "Beed": ["Beed", "Parli", "Ambejogai"],
    "Yavatmal": ["Yavatmal", "Pusad", "Umarkhed"],
    "Gondia": ["Gondia", "Tirora"],
    "Bhandara": ["Bhandara", "Tumsar"],
    "Washim": ["Washim", "Karanja", "Risod"],
    "Hingoli": ["Hingoli", "Basmath", "Sengaon"],
    "Nandurbar": ["Nandurbar", "Shahada", "Taloda"],
    "Sindhudurg": ["Sawantwadi", "Malvan", "Kudal", "Kankavli"],
    "Ratnagiri": ["Ratnagiri", "Chiplun", "Dapoli", "Guhagar"],
    "Raigad": ["Alibag", "Panvel", "Khopoli", "Karjat", "Pen", "Mahad"],
    "Palghar": ["Palghar", "Vasai", "Virar", "Dahanu"],
    "Buldhana": ["Buldhana", "Khamgaon", "Malkapur", "Shegaon"],
    "Wardha": ["Wardha", "Hinganghat", "Arvi"],
    "Gadchiroli": ["Gadchiroli", "Aheri", "Chamorshi"],
    "Osmanabad": ["Osmanabad", "Dharashiv", "Tuljapur", "Omerga"]
}

SPORTS_SEED = [
    {"name": "Football", "icon": "fa-futbol", "color": "#10B981"},
    {"name": "Cricket", "icon": "fa-baseball", "color": "#3B82F6"},
    {"name": "Badminton", "icon": "fa-table-tennis-paddle-ball", "color": "#39FF88"},
    {"name": "Basketball", "icon": "fa-basketball", "color": "#F59E0B"},
    {"name": "Volleyball", "icon": "fa-volleyball", "color": "#EC4899"},
    {"name": "Tennis", "icon": "fa-baseball-bat-ball", "color": "#8B5CF6"},
    {"name": "Box Cricket", "icon": "fa-cube", "color": "#06B6D4"},
    {"name": "Pickleball", "icon": "fa-table-tennis-paddle-ball", "color": "#EF4444"},
]

AMENITIES_SEED = [
    {"name": "Parking", "icon": "fa-square-parking"},
    {"name": "Washroom", "icon": "fa-restroom"},
    {"name": "Changing Room", "icon": "fa-shirt"},
    {"name": "Floodlights", "icon": "fa-lightbulb"},
    {"name": "Cafe", "icon": "fa-mug-saucer"},
    {"name": "Locker", "icon": "fa-lock"},
    {"name": "WiFi", "icon": "fa-wifi"},
    {"name": "Indoor", "icon": "fa-house"},
    {"name": "Outdoor", "icon": "fa-sun"},
]

# 12 Mock Turfs matching services/mock_data.py
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
    dict(name="Elite Hoops Court", city="Bengaluru", area="Koramangala", # fallback to Mumbai if Bengaluru not seeded, but we'll map to appropriate districts
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

def seed_db():
    app = create_app()
    with app.app_context():
        print("Ensuring database tables exist...")
        db.create_all()
        
        print("Clearing existing table records...")
        models_to_clear = [
            BookingTicket, BookingHistory, Booking, ReviewReply, Review,
            TurfImage, Turf, Amenity, Sport, OwnerImage, Owner,
            CustomerReport, CustomerRestriction, SlotStatus, Notification,
            City, District, State, User, Role
        ]
        for m in models_to_clear:
            try:
                db.session.query(m).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
        
        print("Seeding Roles...")
        role_player = Role(id=uuid.uuid4(), name="Player")
        role_owner = Role(id=uuid.uuid4(), name="Owner")
        role_admin = Role(id=uuid.uuid4(), name="Admin")
        db.session.add_all([role_player, role_owner, role_admin])
        db.session.commit()

        print("Seeding Maharashtra Locations...")
        state_mh = State(id=uuid.uuid4(), name="Maharashtra")
        db.session.add(state_mh)
        db.session.commit()

        # Keep a mapping of city name -> City object
        city_mapping = {}
        for dist_name, cities_list in MAHARASHTRA_LOCATIONS.items():
            dist = District(id=uuid.uuid4(), state_id=state_mh.id, name=dist_name)
            db.session.add(dist)
            db.session.commit()
            
            for c_name in cities_list:
                city = City(id=uuid.uuid4(), district_id=dist.id, name=c_name)
                db.session.add(city)
                city_mapping[c_name] = city
        
        db.session.commit()

        # Seed other mock cities as fallbacks so all mock data fits inside Maharashtra state
        fallback_cities = ["Bengaluru", "Delhi", "Hyderabad", "Chennai", "Ahmedabad"]
        fallback_dist = District(id=uuid.uuid4(), state_id=state_mh.id, name="Other Districts")
        db.session.add(fallback_dist)
        db.session.commit()
        for c_name in fallback_cities:
            city = City(id=uuid.uuid4(), district_id=fallback_dist.id, name=c_name)
            db.session.add(city)
            city_mapping[c_name] = city
        db.session.commit()

        print("Seeding Sports...")
        sport_mapping = {}
        for s in SPORTS_SEED:
            sport = Sport(id=uuid.uuid4(), name=s["name"], icon=s["icon"], color=s["color"])
            db.session.add(sport)
            sport_mapping[s["name"]] = sport
        db.session.commit()

        print("Seeding Amenities...")
        amenity_mapping = {}
        for a in AMENITIES_SEED:
            amenity = Amenity(id=uuid.uuid4(), name=a["name"], icon=a["icon"])
            db.session.add(amenity)
            amenity_mapping[a["name"]] = amenity
        db.session.commit()

        # Seed User Vaibhav
        print("Seeding Vaibhav...")
        p_hash = hash_password("password123")
        vaibhav_city = city_mapping.get("Kolhapur")
        vaibhav = User(
            id=uuid.uuid4(),
            role_id=role_player.id,
            name="Vaibhav",
            email="vaibhav@playnest.app",
            phone="9876543210",
            city_id=vaibhav_city.id if vaibhav_city else None,
            password_hash=p_hash,
            is_verified=True,
            status="active"
        )
        db.session.add(vaibhav)
        db.session.commit()

        # Seed Owners and Turfs
        print("Seeding Owners, Turfs and Images...")
        owner_mapping = {}
        for idx, seed in enumerate(_TURF_SEED, start=1):
            owner_name = seed["owner"]
            owner_email = f"{owner_name.lower().replace(' ', '')}@playnest.app"
            
            # Map owner's city to a Maharashtra seeded city
            seed_city_name = seed["city"]
            owner_city = city_mapping.get(seed_city_name)
            
            owner = owner_mapping.get(owner_email)
            if not owner:
                owner = Owner(
                    id=uuid.uuid4(),
                    role_id=role_owner.id,
                    name=owner_name,
                    email=owner_email,
                    phone="9876543210",
                    password_hash=p_hash,
                    status="Approved",
                    turf_name=seed["name"],
                    city_id=owner_city.id if owner_city else None,
                    state_id=state_mh.id,
                    address=seed["area"],
                    pincode="416001",
                    is_active=True
                )
                db.session.add(owner)
                db.session.commit()
                
                # Seed front cover image for owner
                img_id = seed["img"]
                front_url = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=1200&q=80"
                owner_img = OwnerImage(
                    id=uuid.uuid4(),
                    owner_id=owner.id,
                    url=front_url,
                    image_type="front"
                )
                db.session.add(owner_img)
                db.session.commit()
                owner_mapping[owner_email] = owner
            
            # Seed Turf
            t_id = uuid.uuid4()
            turf = Turf(
                id=t_id,
                name=seed["name"],
                city_id=owner_city.id if owner_city else None,
                area=seed["area"],
                price_per_hour=seed["price"],
                rating=seed["rating"],
                review_count=seed["reviews"],
                indoor=seed["indoor"],
                description=(
                    f"{seed['name']} is a premium {'indoor' if seed['indoor'] else 'outdoor'} "
                    f"facility in {seed['area']}, {seed['city']}, purpose-built for "
                    f"{', '.join(seed['sports'])}. Regulation-grade surface, professional-grade "
                    f"floodlighting, and a booking-friendly layout make it a favourite among "
                    f"regulars on PlayNest."
                ),
                opening_hours="6:00 AM – 11:00 PM, all days",
                owner_id=owner.id,
                lat=19.07 + (idx * 0.01),
                lng=72.87 + (idx * 0.01),
                verified=True,
                status="active"
            )
            db.session.add(turf)
            db.session.commit()
            
            # Map Turf images
            img_id = seed["img"]
            hero = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=1200&q=80"
            db.session.add(TurfImage(id=uuid.uuid4(), turf_id=turf.id, url=hero, image_type="cover"))
            for g_idx in range(3):
                g_url = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=800&q=80&idx={g_idx}"
                db.session.add(TurfImage(id=uuid.uuid4(), turf_id=turf.id, url=g_url, image_type="gallery", display_order=g_idx))
            db.session.commit()
            
            # Map pivot relations
            for s_name in seed["sports"]:
                sport_obj = sport_mapping.get(s_name)
                if sport_obj:
                    turf.sports_rel.append(sport_obj)
            
            for a_name in seed["facilities"]:
                amenity_obj = amenity_mapping.get(a_name)
                if amenity_obj:
                    turf.amenities_rel.append(amenity_obj)
            
            db.session.commit()

            # Seed Reviews for this Turf
            for r_idx, (author, r_rating, comment) in enumerate(_SAMPLE_REVIEWS):
                review = Review(
                    id=uuid.uuid4(),
                    booking_id=None, # Seeded reviews don't require booking references
                    turf_id=turf.id,
                    author_name=author,
                    rating_overall=r_rating,
                    rating_ground_quality=5,
                    rating_lighting=4,
                    rating_cleanliness=5,
                    rating_staff=5,
                    rating_value=5,
                    comment=comment,
                    date=(datetime.now() - timedelta(days=r_idx + 1)).strftime("%Y-%m-%d"),
                    status="Approved"
                )
                db.session.add(review)
            db.session.commit()

        # Seed Bookings for User Vaibhav
        print("Seeding Booking Records...")
        green_turf = db.session.query(Turf).filter_by(name="GreenTurf Arena").first()
        football_sport = sport_mapping.get("Football")
        
        if green_turf and football_sport:
            yesterday = datetime.now() - timedelta(days=1)
            b1 = Booking(
                uuid=uuid.uuid4(),
                public_booking_number="PLN-2026-0001",
                user_id=vaibhav.id,
                turf_id=green_turf.id,
                sport_id=football_sport.id,
                date=yesterday.strftime("%Y-%m-%d"),
                start_time="17:00",
                end_time="18:00",
                duration_hours=1.0,
                price=green_turf.price_per_hour,
                status="Completed",
                player_name=vaibhav.name,
                booking_source="Online",
                approved_by_owner=True
            )
            db.session.add(b1)
            db.session.commit()
            
            # Create booking ticket
            ticket = BookingTicket(
                id=uuid.uuid4(),
                booking_uuid=b1.uuid,
                ticket_code=f"TKT-{uuid.uuid4().hex[:8].upper()}",
                barcode_url=""
            )
            db.session.add(ticket)
            db.session.commit()

            # Create an Offline Booking (WhatsApp booking)
            b2 = Booking(
                uuid=uuid.uuid4(),
                public_booking_number="PLN-2026-0002",
                user_id=None, # None indicates offline/non-registered player
                turf_id=green_turf.id,
                sport_id=football_sport.id,
                date=datetime.now().strftime("%Y-%m-%d"),
                start_time="08:00",
                end_time="09:00",
                duration_hours=1.0,
                price=green_turf.price_per_hour,
                status="Confirmed",
                player_name="Offline Guest Player",
                booking_source="WhatsApp",
                approved_by_owner=True
            )
            db.session.add(b2)
            db.session.commit()

        print("Database Seeding Completed Successfully! [OK]")

if __name__ == "__main__":
    seed_db()
