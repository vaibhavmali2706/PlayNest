import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db

class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_name = db.Column(db.String(150), nullable=False)
    turf_id = db.Column(UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), nullable=False)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('owners.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_email = db.Column(db.String(150), default="")
    status = db.Column(db.String(50), default='Pending') # Pending | In Progress | Resolved
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='complaints')
    turf = db.relationship('Turf', backref='complaints')
    owner = db.relationship('Owner', backref='complaints')

    @property
    def turf_name(self):
        return self.turf.name if self.turf else ""

    @turf_name.setter
    def turf_name(self, value):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

