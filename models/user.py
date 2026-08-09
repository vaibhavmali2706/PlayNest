import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db
from models.location import City
from models.role import Role

favorites = db.Table(
    'favorites',
    db.Column('user_id', UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('turf_id', UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('roles.id'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    city_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cities.id'), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(50), default='active') # active | suspended | banned
    is_verified = db.Column(db.Boolean, default=False)
    avatar_initials = db.Column(db.String(10))
    warnings_count = db.Column(db.Integer, default=0)
    suspension_until = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    city_rel = db.relationship('City', backref='users')
    role_rel = db.relationship('Role', backref='users')
    favourites = db.relationship('Turf', secondary=favorites, backref=db.backref('favorited_by', lazy='dynamic'))

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
            # Safe lookup
            try:
                city_obj = City.query.filter_by(name=value).first()
                if city_obj:
                    self.city_rel = city_obj
            except Exception:
                pass

    @property
    def role(self):
        return self.role_rel.name if self.role_rel else ""

    @role.setter
    def role(self, value):
        if hasattr(value, 'name'):
            self.role_rel = value
        else:
            try:
                role_obj = Role.query.filter_by(name=value).first()
                if role_obj:
                    self.role_rel = role_obj
            except Exception:
                pass

    @property
    def city_name(self):
        return self.city

    @property
    def favourite_turf_ids(self):
        return [str(t.id) for t in self.favourites]

    def __init__(self, **kwargs):
        self._mock_city = kwargs.pop('city', None)
        self._mock_role = kwargs.pop('role', None)
        super().__init__(**kwargs)
        if not self.avatar_initials and self.name:
            parts = self.name.strip().split()
            self.avatar_initials = "".join(p[0].upper() for p in parts[:2]) or "P"
        if self._mock_city:
            self.city = self._mock_city
        if self._mock_role:
            self.role = self._mock_role
