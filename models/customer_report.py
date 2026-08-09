import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db

class CustomerReport(db.Model):
    __tablename__ = 'customer_reports'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('owners.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    booking_uuid = db.Column('booking_id', UUID(as_uuid=True), db.ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)
    reason = db.Column(db.String(100), nullable=False) # rude_behaviour | damaged_property | repeated_late_arrival | no_show | violated_turf_rules | other
    description = db.Column(db.Text, default="")
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    owner = db.relationship('Owner', backref='customer_reports')
    user = db.relationship('User', backref='customer_reports')
    booking = db.relationship('Booking', backref='customer_reports')

    @property
    def booking_id(self):
        return self.booking.public_booking_number if self.booking else ""

    @booking_id.setter
    def booking_id(self, value):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

