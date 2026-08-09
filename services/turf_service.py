import uuid
from typing import List, Optional
from flask import current_app, has_app_context
from extensions import db
from models.turf import Turf, TurfImage, Sport, Amenity, Review
from models.location import City
from models.owner import Owner
from services.mock_data import TURFS, SPORTS, CITIES, ALL_FACILITIES


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def get_all_turfs() -> List[Turf]:
    if is_db_ready():
        return db.session.query(Turf).filter(Turf.is_active == True).all()
    return TURFS


def get_turf_by_id(turf_id: str) -> Optional[Turf]:
    if not turf_id:
        return None
    if is_db_ready():
        try:
            turf_uuid = uuid.UUID(str(turf_id))
            return db.session.query(Turf).filter(Turf.id == turf_uuid, Turf.is_active == True).first()
        except ValueError:
            # Fallback if turf_id is non-UUID string
            return db.session.query(Turf).filter(Turf.name == turf_id, Turf.is_active == True).first()
    return next((t for t in TURFS if str(t.id) == str(turf_id)), None)


def get_sports() -> list:
    if is_db_ready():
        sports = db.session.query(Sport).filter_by(is_active=True).all()
        return [{"name": s.name, "icon": s.icon, "color": s.color} for s in sports]
    return SPORTS


def get_cities() -> list:
    if is_db_ready():
        cities = db.session.query(City).filter_by(is_active=True).order_by(City.name).all()
        return [c.name for c in cities]
    return CITIES


def get_facilities() -> list:
    if is_db_ready():
        amenities = db.session.query(Amenity).filter_by(is_active=True).order_by(Amenity.name).all()
        return [a.name for a in amenities]
    return ALL_FACILITIES


def get_featured_turfs(limit: int = 6) -> List[Turf]:
    if is_db_ready():
        return db.session.query(Turf).filter(Turf.is_active == True).order_by(Turf.rating.desc()).limit(limit).all()
    return sorted(TURFS, key=lambda t: t.rating, reverse=True)[:limit]


def search_turfs(
    query: str = "",
    sport: str = "",
    city: str = "",
    facilities: Optional[List[str]] = None,
    indoor_outdoor: str = "",
    min_rating: float = 0,
    sort: str = "recommended",
) -> List[Turf]:
    if not is_db_ready():
        # Fallback to mock search
        results = TURFS
        if query:
            q = query.lower()
            results = [
                t for t in results
                if q in t.name.lower() or q in t.city.lower() or q in t.area.lower()
                or any(q in s.lower() for s in t.sports)
            ]
        if sport:
            results = [t for t in results if sport in t.sports]
        if city:
            results = [t for t in results if t.city == city]
        if facilities:
            results = [t for t in results if all(f in t.facilities for f in facilities)]
        if indoor_outdoor == "Indoor":
            results = [t for t in results if t.indoor]
        elif indoor_outdoor == "Outdoor":
            results = [t for t in results if not t.indoor]
        if min_rating:
            results = [t for t in results if t.rating >= min_rating]
        if sort == "price_low":
            results = sorted(results, key=lambda t: t.price_per_hour)
        elif sort == "price_high":
            results = sorted(results, key=lambda t: t.price_per_hour, reverse=True)
        elif sort == "rating":
            results = sorted(results, key=lambda t: t.rating, reverse=True)
        else:
            results = sorted(results, key=lambda t: (t.rating, t.review_count), reverse=True)
        return results

    # Database search query builder
    query_obj = db.session.query(Turf).filter(Turf.is_active == True)

    if query:
        q = f"%{query}%"
        # Search by name, area, city name, or sport names
        query_obj = query_obj.join(Turf.city_rel).filter(
            db.or_(
                Turf.name.ilike(q),
                Turf.area.ilike(q),
                City.name.ilike(q),
                Turf.sports_rel.any(Sport.name.ilike(q))
            )
        )

    if sport:
        query_obj = query_obj.filter(Turf.sports_rel.any(Sport.name == sport))

    if city:
        query_obj = query_obj.join(Turf.city_rel).filter(City.name == city)

    if facilities:
        for facility in facilities:
            query_obj = query_obj.filter(Turf.amenities_rel.any(Amenity.name == facility))

    if indoor_outdoor == "Indoor":
        query_obj = query_obj.filter(Turf.indoor == True)
    elif indoor_outdoor == "Outdoor":
        query_obj = query_obj.filter(Turf.indoor == False)

    if min_rating:
        query_obj = query_obj.filter(Turf.rating >= min_rating)

    if sort == "price_low":
        query_obj = query_obj.order_by(Turf.price_per_hour.asc())
    elif sort == "price_high":
        query_obj = query_obj.order_by(Turf.price_per_hour.desc())
    elif sort == "rating":
        query_obj = query_obj.order_by(Turf.rating.desc())
    else:
        query_obj = query_obj.order_by(Turf.rating.desc(), Turf.review_count.desc())

    return query_obj.all()


def get_turfs_by_owner(owner_id: str) -> List[Turf]:
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(Turf).filter(Turf.owner_id == owner_uuid, Turf.is_active == True).all()
        except ValueError:
            return []
    return [t for t in TURFS if str(t.owner_id) == str(owner_id)]


def add_new_turf(
    name: str, city: str, area: str, sports: List[str], price_per_hour: int,
    facilities: List[str], indoor: bool, hero_image: str, gallery: List[str],
    description: str, opening_hours: str, owner_id: str, owner_name: str,
    lat: float, lng: float
) -> Turf:
    if is_db_ready():
        owner_uuid = uuid.UUID(str(owner_id))
        
        # Lookup city
        city_obj = db.session.query(City).filter_by(name=city).first()
        if not city_obj:
            # Create city if it doesn't exist
            # Find any fallback district
            from models.location import District
            dist = db.session.query(District).first()
            city_obj = City(id=uuid.uuid4(), district_id=dist.id if dist else None, name=city)
            db.session.add(city_obj)
            db.session.commit()

        turf = Turf(
            id=uuid.uuid4(),
            name=name,
            city_id=city_obj.id,
            area=area,
            price_per_hour=int(price_per_hour),
            rating=5.0,
            review_count=0,
            indoor=indoor,
            description=description,
            opening_hours=opening_hours,
            owner_id=owner_uuid,
            lat=float(lat) if lat else 19.07,
            lng=float(lng) if lng else 72.87,
            verified=True,
            status="active"
        )
        db.session.add(turf)
        db.session.commit()

        # Add sports and amenities
        turf.sports = sports
        turf.facilities = facilities

        # Add image URLs
        if hero_image:
            db.session.add(TurfImage(id=uuid.uuid4(), turf_id=turf.id, url=hero_image, image_type="cover"))
        if gallery:
            for display_order, url in enumerate(gallery):
                if url:
                    db.session.add(TurfImage(id=uuid.uuid4(), turf_id=turf.id, url=url, image_type="gallery", display_order=display_order))
        
        db.session.commit()
        return turf

    # Fallback to mock store
    next_id = f"TRF{len(TURFS) + 1:03d}"
    new_turf = Turf(
        id=next_id,
        name=name,
        city=city,
        area=area,
        sports=sports,
        price_per_hour=int(price_per_hour),
        rating=5.0,
        review_count=0,
        facilities=facilities,
        indoor=indoor,
        hero_image=hero_image,
        gallery=gallery,
        description=description,
        opening_hours=opening_hours,
        owner_id=owner_id,
        owner_name=owner_name,
        lat=float(lat) if lat else 19.07,
        lng=float(lng) if lng else 72.87,
        verified=True,
    )
    TURFS.append(new_turf)
    return new_turf


def update_turf(
    turf_id: str, name: str, city: str, area: str, sports: List[str], price_per_hour: int,
    facilities: List[str], indoor: bool, hero_image: str, gallery: List[str],
    description: str, opening_hours: str, lat: float, lng: float
) -> Optional[Turf]:
    t = get_turf_by_id(turf_id)
    if not t:
        return None

    if is_db_ready():
        t.name = name
        t.area = area
        t.price_per_hour = int(price_per_hour)
        t.indoor = indoor
        t.description = description
        t.opening_hours = opening_hours
        t.lat = float(lat) if lat else t.lat
        t.lng = float(lng) if lng else t.lng

        # Lookup and update City
        city_obj = db.session.query(City).filter_by(name=city).first()
        if city_obj:
            t.city_id = city_obj.id

        # Update sports and amenities
        t.sports = sports
        t.facilities = facilities

        # Update hero image
        if hero_image:
            t.hero_image = hero_image
        # Update gallery
        if gallery:
            t.gallery = gallery

        db.session.commit()
        return t

    # Fallback mock update
    t.name = name
    t.city = city
    t.area = area
    t.sports = sports
    t.price_per_hour = int(price_per_hour)
    t.facilities = facilities
    t.indoor = indoor
    if hero_image:
        t.hero_image = hero_image
    if gallery:
        t.gallery = gallery
    t.description = description
    t.opening_hours = opening_hours
    t.lat = float(lat) if lat else t.lat
    t.lng = float(lng) if lng else t.lng
    return t


def add_review(turf_id: str, author: str, rating: float, comment: str) -> bool:
    from datetime import datetime
    t = get_turf_by_id(turf_id)
    if not t:
        return False

    if is_db_ready():
        review = Review(
            id=uuid.uuid4(),
            booking_id=None,
            turf_id=t.id,
            author_name=author,
            rating_overall=float(rating),
            comment=comment,
            date=datetime.now().strftime("%Y-%m-%d"),
            status="Approved"
        )
        db.session.add(review)
        db.session.commit()

        # Recalculate average rating
        total_rating = sum(r.rating for r in t.reviews_rel)
        t.review_count = len(t.reviews_rel)
        t.rating = round(total_rating / t.review_count, 1) if t.review_count > 0 else 5.0
        db.session.commit()
        return True

    # Fallback to mock review
    new_review = Review(
        author=author,
        rating=float(rating),
        comment=comment,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    t.reviews.insert(0, new_review)
    total_rating = sum(r.rating for r in t.reviews)
    t.review_count = len(t.reviews)
    t.rating = round(total_rating / t.review_count, 1)
    return True
