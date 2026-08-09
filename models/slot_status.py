import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db

class SlotStatus(db.Model):
    __tablename__ = 'slot_statuses'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turf_id = db.Column(UUID(as_uuid=True), db.ForeignKey('turfs.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.String(20), nullable=False, index=True) # YYYY-MM-DD
    start_time = db.Column(db.String(20), nullable=False) # HH:MM (24h)
    end_time = db.Column(db.String(20), nullable=False) # HH:MM (24h)
    status = db.Column(db.String(50), default='available') # available | booked_online | unavailable | maintenance | holiday
    reason = db.Column(db.String(100), nullable=True) # walk_in | phone_booking | whatsapp_booking | maintenance | holiday | tournament | personal_use | other
    updated_by = db.Column(UUID(as_uuid=True), nullable=True) # owner_id or user_id
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    turf = db.relationship('Turf', backref='slot_statuses')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

