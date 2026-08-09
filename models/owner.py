import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db
from models.location import City, State
from models.role import Role

class Owner(db.Model):
    __tablename__ = 'owners'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending | Approved | Rejected
    
    # Business Information
    turf_name = db.Column(db.String(150), default="")
    aadhaar = db.Column(db.String(20), default="")
    pan = db.Column(db.String(20), default="")
    gst = db.Column(db.String(20), default="")
    business_license = db.Column(db.String(100), default="")
    address = db.Column(db.Text, default="")
    city_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cities.id'), nullable=True)
    state_id = db.Column(UUID(as_uuid=True), db.ForeignKey('states.id'), nullable=True)
    pincode = db.Column(db.String(10), default="")
    bank_details = db.Column(db.Text, default="")
    google_maps_location = db.Column(db.Text, default="")
    
    # Uploaded Images
    identity_proof = db.Column(db.String(256), default="")
    warnings_count = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    city_rel = db.relationship('City', backref='owners')
    state_rel = db.relationship('State', backref='owners')
    role_rel = db.relationship('Role', backref='owners')
    images = db.relationship('OwnerImage', backref='owner', cascade='all, delete-orphan')

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
            try:
                city_obj = City.query.filter_by(name=value).first()
                if city_obj:
                    self.city_rel = city_obj
            except Exception:
                pass

    @property
    def state(self):
        if hasattr(self, '_mock_state') and self._mock_state:
            return self._mock_state
        return self.state_rel.name if self.state_rel else ""

    @state.setter
    def state(self, value):
        if hasattr(value, 'name'):
            self.state_rel = value
        else:
            self._mock_state = value
            try:
                state_obj = State.query.filter_by(name=value).first()
                if state_obj:
                    self.state_rel = state_obj
            except Exception:
                pass

    @property
    def city_name(self):
        return self.city

    @property
    def state_name(self):
        return self.state

    @property
    def front_image(self):
        img = next((i.url for i in self.images if i.image_type == 'front'), "")
        return img

    @property
    def ground_images(self):
        return [i.url for i in self.images if i.image_type == 'ground']

    @property
    def night_images(self):
        return [i.url for i in self.images if i.image_type == 'night']

    @property
    def parking_images(self):
        return [i.url for i in self.images if i.image_type == 'parking']

    @property
    def washroom_images(self):
        return [i.url for i in self.images if i.image_type == 'washroom']

    @property
    def changing_room_images(self):
        return [i.url for i in self.images if i.image_type == 'changing_room']

    def __init__(self, **kwargs):
        self._mock_city = kwargs.pop('city', None)
        self._mock_state = kwargs.pop('state', None)
        super().__init__(**kwargs)
        if self._mock_city:
            self.city = self._mock_city
        if self._mock_state:
            self.state = self._mock_state


class OwnerImage(db.Model):
    __tablename__ = 'owner_images'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('owners.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.String(256), nullable=False)
    image_type = db.Column(db.String(50), default='gallery') # front | ground | night | parking | washroom | changing_room
    display_order = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

