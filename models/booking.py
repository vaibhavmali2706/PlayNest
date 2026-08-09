import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db
from flask import has_app_context

class Booking(db.Model):
    __tablename__ = 'bookings'

    uuid = db.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_booking_number = db.Column('public_booking_number', db.String(50), unique=True, nullable=False, index=True)
    user_uuid = db.Column('user_id', UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    turf_uuid = db.Column('turf_id', UUID(as_uuid=True), db.ForeignKey('turfs.id'), nullable=False)
    sport_uuid = db.Column('sport_id', UUID(as_uuid=True), db.ForeignKey('sports.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    start_time = db.Column(db.String(20), nullable=False) # HH:MM (24h)
    end_time = db.Column(db.String(20), nullable=False) # HH:MM (24h)
    duration_hours = db.Column(db.Float, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending | Confirmed | Completed | Cancelled | Expired
    player_name = db.Column(db.String(150), nullable=False)
    booking_source = db.Column(db.String(50), default='Online') # Online | Walk-in | Phone | WhatsApp | Tournament | Maintenance | Holiday | Personal Use
    approved_by_owner = db.Column(db.Boolean, default=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='bookings')
    turf = db.relationship('Turf', backref='bookings')
    sport_rel = db.relationship('Sport', backref='bookings')
    ticket = db.relationship('BookingTicket', backref='booking', uselist=False, cascade='all, delete-orphan')

    @property
    def id(self):
        return self.public_booking_number

    @id.setter
    def id(self, value):
        self.public_booking_number = value

    @property
    def user_id(self):
        if hasattr(self, '_mock_user_id') and self._mock_user_id:
            return self._mock_user_id
        return str(self.user_uuid) if self.user_uuid else None

    @user_id.setter
    def user_id(self, value):
        if not value:
            self.user_uuid = None
            return
        try:
            self.user_uuid = uuid.UUID(str(value))
        except ValueError:
            self._mock_user_id = value

    @property
    def turf_id(self):
        if hasattr(self, '_mock_turf_id') and self._mock_turf_id:
            return self._mock_turf_id
        return str(self.turf_uuid) if self.turf_uuid else None

    @turf_id.setter
    def turf_id(self, value):
        if not value:
            self.turf_uuid = None
            return
        try:
            self.turf_uuid = uuid.UUID(str(value))
        except ValueError:
            self._mock_turf_id = value

    @property
    def sport_id(self):
        if hasattr(self, '_mock_sport_id') and self._mock_sport_id:
            return self._mock_sport_id
        return str(self.sport_uuid) if self.sport_uuid else None

    @sport_id.setter
    def sport_id(self, value):
        if not value:
            self.sport_uuid = None
            return
        try:
            self.sport_uuid = uuid.UUID(str(value))
        except ValueError:
            self._mock_sport_id = value

    @property
    def sport(self):
        if hasattr(self, '_mock_sport') and self._mock_sport:
            return self._mock_sport
        return self.sport_rel.name if self.sport_rel else ""

    @sport.setter
    def sport(self, value):
        if hasattr(value, 'name'):
            self.sport_rel = value
            self.sport_uuid = value.id
        else:
            self._mock_sport = value
            if has_app_context():
                try:
                    from models.turf import Sport
                    sport_obj = Sport.query.filter_by(name=value).first()
                    if sport_obj:
                        self.sport_rel = sport_obj
                        self.sport_uuid = sport_obj.id
                except Exception:
                    pass

    @property
    def turf_name(self):
        if hasattr(self, '_mock_turf_name') and self._mock_turf_name:
            return self._mock_turf_name
        return self.turf.name if self.turf else ""

    @turf_name.setter
    def turf_name(self, value):
        self._mock_turf_name = value

    @property
    def turf_area(self):
        if hasattr(self, '_mock_turf_area') and self._mock_turf_area:
            return self._mock_turf_area
        return self.turf.area if self.turf else ""

    @turf_area.setter
    def turf_area(self, value):
        self._mock_turf_area = value

    @property
    def turf_city(self):
        if hasattr(self, '_mock_turf_city') and self._mock_turf_city:
            return self._mock_turf_city
        return self.turf.city_name if self.turf else ""

    @turf_city.setter
    def turf_city(self, value):
        self._mock_turf_city = value

    @property
    def datetime_start(self) -> datetime:
        return datetime.strptime(f"{self.date} {self.start_time}", "%Y-%m-%d %H:%M")

    def hours_until_start(self) -> float:
        delta = self.datetime_start - datetime.now()
        return delta.total_seconds() / 3600

    def is_cancellable(self, window_hours: int) -> bool:
        return self.status in ("Pending", "Confirmed") and self.hours_until_start() > window_hours

    def __init__(self, **kwargs):
        self._mock_user_id = kwargs.pop('user_id', None)
        self._mock_turf_id = kwargs.pop('turf_id', None)
        self._mock_sport_id = kwargs.pop('sport_id', None)
        self._mock_sport = kwargs.pop('sport', None)
        self._mock_turf_name = kwargs.pop('turf_name', None)
        self._mock_turf_area = kwargs.pop('turf_area', None)
        self._mock_turf_city = kwargs.pop('turf_city', None)
        super().__init__(**kwargs)
        if self._mock_user_id:
            self.user_id = self._mock_user_id
        if self._mock_turf_id:
            self.turf_id = self._mock_turf_id
        if self._mock_sport_id:
            self.sport_id = self._mock_sport_id
        if self._mock_sport:
            self.sport = self._mock_sport
        if self._mock_turf_name:
            self.turf_name = self._mock_turf_name
        if self._mock_turf_area:
            self.turf_area = self._mock_turf_area
        if self._mock_turf_city:
            self.turf_city = self._mock_turf_city


class BookingTicket(db.Model):
    __tablename__ = 'booking_tickets'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_uuid = db.Column('booking_id', UUID(as_uuid=True), db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False)
    ticket_code = db.Column(db.String(100), unique=True, nullable=False)
    barcode_url = db.Column(db.String(256), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class BookingHistory(db.Model):
    __tablename__ = 'booking_history'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_uuid = db.Column('booking_id', UUID(as_uuid=True), db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    status_from = db.Column(db.String(50))
    status_to = db.Column(db.String(50))
    changed_by = db.Column(db.String(150))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
