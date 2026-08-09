import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db

class State(db.Model):
    __tablename__ = 'states'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    districts = db.relationship('District', backref='state', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class District(db.Model):
    __tablename__ = 'districts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id = db.Column(UUID(as_uuid=True), db.ForeignKey('states.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    cities = db.relationship('City', backref='district', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class City(db.Model):
    __tablename__ = 'cities'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    district_id = db.Column(UUID(as_uuid=True), db.ForeignKey('districts.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

