import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db
from models.location import City
from models.owner import Owner
from flask import has_app_context

# Pivot tables
turf_sports = db.Table(
    'turf_sports',
    db.Column('turf_id', UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('sport_id', UUID(as_uuid=True), db.ForeignKey('sports.id', ondelete='CASCADE'), primary_key=True)
)

turf_amenities = db.Table(
    'turf_amenities',
    db.Column('turf_id', UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), primary_key=True),
    db.Column('amenity_id', UUID(as_uuid=True), db.ForeignKey('amenities.id', ondelete='CASCADE'), primary_key=True)
)


class Sport(db.Model):
    __tablename__ = 'sports'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(20))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Amenity(db.Model):
    __tablename__ = 'amenities'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Turf(db.Model):
    __tablename__ = 'turfs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(150), nullable=False)
    city_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cities.id'), nullable=False)
    area = db.Column(db.String(150))
    price_per_hour = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, default=5.0)
    review_count = db.Column(db.Integer, default=0)
    indoor = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    opening_hours = db.Column(db.String(150))
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('owners.id'), nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    verified = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='active') # active | disabled

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    city_rel = db.relationship('City', backref='turfs')
    owner_rel = db.relationship('Owner', backref='turfs')
    images_rel = db.relationship('TurfImage', backref='turf', cascade="all, delete-orphan", lazy='joined')
    sports_rel = db.relationship('Sport', secondary=turf_sports)
    amenities_rel = db.relationship('Amenity', secondary=turf_amenities)
    reviews_rel = db.relationship('Review', backref='turf', cascade="all, delete-orphan", order_by="desc(Review.created_at)")

    @property
    def city(self):
        if hasattr(self, '_mock_city') and self._mock_city:
            return self._mock_city
        return self.city_rel.name if self.city_rel else ""

    @city.setter
    def city(self, value):
        if hasattr(value, 'name'):
            self.city_rel = value
        else:
            self._mock_city = value
            if has_app_context():
                try:
                    city_obj = City.query.filter_by(name=value).first()
                    if city_obj:
                        self.city_rel = city_obj
                except Exception:
                    pass

    @property
    def owner(self):
        if hasattr(self, '_mock_owner') and self._mock_owner:
            return self._mock_owner
        return self.owner_rel

    @owner.setter
    def owner(self, value):
        if hasattr(value, 'name') and hasattr(value, 'email'):
            self.owner_rel = value
        else:
            self._mock_owner = value
            if has_app_context():
                try:
                    owner_obj = Owner.query.filter_by(name=value).first()
                    if owner_obj:
                        self.owner_rel = owner_obj
                except Exception:
                    pass

    @property
    def owner_name(self):
        if hasattr(self, '_mock_owner_name') and self._mock_owner_name:
            return self._mock_owner_name
        if hasattr(self, '_mock_owner') and isinstance(self._mock_owner, str):
            return self._mock_owner
        return self.owner_rel.name if self.owner_rel else ""

    @owner_name.setter
    def owner_name(self, value):
        self._mock_owner_name = value

    @property
    def city_name(self):
        return self.city

    @property
    def sports(self):
        if hasattr(self, '_mock_sports') and self._mock_sports is not None:
            return self._mock_sports
        return [s.name for s in self.sports_rel]

    @sports.setter
    def sports(self, sport_names):
        self._mock_sports = sport_names
        if has_app_context():
            try:
                sports_list = []
                for name in sport_names:
                    s = Sport.query.filter_by(name=name).first()
                    if s:
                        sports_list.append(s)
                self.sports_rel = sports_list
            except Exception:
                pass

    @property
    def facilities(self):
        if hasattr(self, '_mock_facilities') and self._mock_facilities is not None:
            return self._mock_facilities
        return [a.name for a in self.amenities_rel]

    @facilities.setter
    def facilities(self, facility_names):
        self._mock_facilities = facility_names
        if has_app_context():
            try:
                amenities_list = []
                for name in facility_names:
                    a = Amenity.query.filter_by(name=name).first()
                    if a:
                        amenities_list.append(a)
                self.amenities_rel = amenities_list
            except Exception:
                pass

    @property
    def reviews(self):
        return self.reviews_rel

    @reviews.setter
    def reviews(self, value):
        self.reviews_rel = value

    @property
    def hero_image(self):
        img = next((i for i in self.images_rel if i.image_type == 'cover'), None)
        if img:
            return img.url
        return self.images_rel[0].url if self.images_rel else ""

    @hero_image.setter
    def hero_image(self, url):
        cover_img = next((i for i in self.images_rel if i.image_type == 'cover'), None)
        if cover_img:
            cover_img.url = url
        else:
            self.images_rel.append(TurfImage(url=url, image_type='cover'))

    @property
    def gallery(self):
        return [i.url for i in self.images_rel if i.image_type == 'gallery']

    @gallery.setter
    def gallery(self, urls):
        covers = [i for i in self.images_rel if i.image_type == 'cover']
        new_gallery = [TurfImage(url=url, image_type='gallery') for url in urls]
        self.images_rel = covers + new_gallery

    @property
    def facility_icons(self):
        icon_map = {
            "Parking": "fa-square-parking",
            "Washroom": "fa-restroom",
            "Changing Room": "fa-shirt",
            "Floodlights": "fa-lightbulb",
            "Cafe": "fa-mug-saucer",
            "Locker": "fa-lock",
            "WiFi": "fa-wifi",
            "Indoor": "fa-house",
            "Outdoor": "fa-sun",
        }
        return {f: icon_map.get(f, "fa-circle-check") for f in self.facilities}

    def __init__(self, **kwargs):
        self._mock_city = kwargs.pop('city', None)
        self._mock_owner = kwargs.pop('owner', None)
        self._mock_owner_name = kwargs.pop('owner_name', None)
        self._mock_sports = kwargs.pop('sports', None)
        self._mock_facilities = kwargs.pop('facilities', None)
        super().__init__(**kwargs)
        if self._mock_city:
            self.city = self._mock_city
        if self._mock_owner:
            self.owner = self._mock_owner
        if self._mock_owner_name:
            self.owner_name = self._mock_owner_name
        if self._mock_sports:
            self.sports = self._mock_sports
        if self._mock_facilities:
            self.facilities = self._mock_facilities


class TurfImage(db.Model):
    __tablename__ = 'turf_images'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turf_id = db.Column(UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.String(256), nullable=False)
    image_type = db.Column(db.String(50), default='gallery') # cover | gallery | night | parking | washroom | changing_room
    display_order = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bookings.id'), unique=True, nullable=True)
    turf_id = db.Column(UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), nullable=False)
    author_name = db.Column(db.String(150), nullable=False)
    rating_overall = db.Column(db.Float, nullable=False)
    rating_ground_quality = db.Column(db.Integer, nullable=True)
    rating_lighting = db.Column(db.Integer, nullable=True)
    rating_cleanliness = db.Column(db.Integer, nullable=True)
    rating_staff = db.Column(db.Integer, nullable=True)
    rating_value = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text)
    date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    status = db.Column(db.String(50), default='Approved') # Approved | Flagged | Hidden
    ai_summary = db.Column(db.Text, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    reply = db.relationship('ReviewReply', backref='review', uselist=False, cascade="all, delete-orphan")

    @property
    def author(self):
        return self.author_name

    @author.setter
    def author(self, value):
        self.author_name = value

    @property
    def rating(self):
        return self.rating_overall

    @rating.setter
    def rating(self, value):
        self.rating_overall = float(value)

    def __init__(self, **kwargs):
        author = kwargs.pop('author', None)
        rating = kwargs.pop('rating', None)
        super().__init__(**kwargs)
        if author is not None:
            self.author = author
        if rating is not None:
            self.rating = rating



class ReviewReply(db.Model):
    __tablename__ = 'review_replies'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reviews.id', ondelete='CASCADE'), unique=True, nullable=False)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('owners.id', ondelete='CASCADE'), nullable=False)
    reply_text = db.Column(db.Text, nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
