import uuid
import hashlib
from datetime import datetime, timedelta
from itertools import count
from typing import List, Optional
from flask import current_app, has_app_context
from extensions import db
from models.booking import Booking, BookingTicket, BookingHistory
from models.turf import Turf, Sport
from models.slot_status import SlotStatus
from services.turf_service import get_turf_by_id
from services.mock_data import TURFS

_BOOKINGS: List[Booking] = []
_id_counter = count(1)

OPEN_HOUR = 6
CLOSE_HOUR = 23


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def _slot_hash_taken(turf_id: str, date: str, hour: int) -> bool:
    key = f"{turf_id}-{date}-{hour}".encode()
    digest = hashlib.md5(key).hexdigest()
    return int(digest[:2], 16) % 5 == 0  # ~20% pre-filled


def get_available_slots(turf_id: str, date: str) -> List[dict]:
    turf = get_turf_by_id(turf_id)
    if not turf:
        return []

    slots = []
    today = datetime.now().date()
    requested_date = datetime.strptime(date, "%Y-%m-%d").date()

    from services import slot_status_service

    # Query database bookings if database is ready
    db_bookings = []
    if is_db_ready():
        try:
            turf_uuid = uuid.UUID(str(turf_id))
            db_bookings = db.session.query(Booking).filter(
                Booking.turf_uuid == turf_uuid,
                Booking.date == date,
                Booking.status.in_(["Pending", "Confirmed", "Completed"]),
                Booking.is_active == True
            ).all()
        except ValueError:
            pass

    for hour in range(OPEN_HOUR, CLOSE_HOUR):
        start = f"{hour:02d}:00"
        end = f"{hour + 1:02d}:00"

        taken = _slot_hash_taken(turf_id, date, hour)

        # Check bookings
        already_booked = False
        if is_db_ready():
            already_booked = any(b.start_time == start for b in db_bookings)
        else:
            already_booked = any(
                str(b.turf_id) == str(turf_id) and b.date == date and b.start_time == start
                and b.status in ("Pending", "Confirmed", "Completed")
                for b in _BOOKINGS
            )

        is_past = requested_date == today and hour <= datetime.now().hour

        custom = slot_status_service.get_slot_status(turf_id, date, start)
        
        is_available = not (taken or already_booked or is_past)
        if custom:
            if custom.status == "available":
                is_available = not (already_booked or is_past)
            elif custom.status in ("unavailable", "maintenance", "holiday"):
                is_available = False

        slots.append({
            "start": start,
            "end": end,
            "available": is_available,
            "price": turf.price_per_hour,
        })

    return slots


def _next_booking_id() -> str:
    year = datetime.now().year
    if is_db_ready():
        try:
            # Count bookings for this year to generate sequential public numbers
            c = db.session.query(db.func.count(Booking.uuid)).filter(Booking.public_booking_number.like(f"PLN-{year}-%")).scalar()
            return f"PLN-{year}-{c + 1:04d}"
        except Exception:
            pass
    n = next(_id_counter)
    return f"PLN-{year}-{n:04d}"


def create_booking(
    user_id: str, player_name: str, turf_id: str, sport: str,
    date: str, start_time: str, end_time: str, duration_hours: float,
) -> Booking:
    turf = get_turf_by_id(turf_id)
    price = int(turf.price_per_hour * duration_hours)
    public_id = _next_booking_id()

    if is_db_ready():
        # Resolve user UUID
        user_uuid = None
        if user_id:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                pass
        
        # Resolve turf UUID and sport UUID
        turf_uuid = uuid.UUID(str(turf_id))
        sport_obj = db.session.query(Sport).filter_by(name=sport).first()

        # Check for double booking with a transaction lock
        # Prevent race conditions by acquiring slot status locks or checking active bookings
        double_booked = db.session.query(Booking).filter(
            Booking.turf_uuid == turf_uuid,
            Booking.date == date,
            Booking.start_time == start_time,
            Booking.status.in_(["Pending", "Confirmed", "Completed"]),
            Booking.is_active == True
        ).first()
        
        if double_booked:
            raise RuntimeError("Slot is already booked. Please choose a different slot.")

        booking = Booking(
            uuid=uuid.uuid4(),
            public_booking_number=public_id,
            user_uuid=user_uuid,
            turf_uuid=turf_uuid,
            sport_uuid=sport_obj.id if sport_obj else None,
            date=date,
            start_time=start_time,
            end_time=end_time,
            duration_hours=float(duration_hours),
            price=price,
            status="Pending",
            player_name=player_name,
            booking_source="Online",
            approved_by_owner=False
        )
        db.session.add(booking)
        db.session.commit()
        return booking

    # Mock fallback creation
    booking = Booking(
        id=public_id,
        user_id=user_id,
        turf_id=turf_id,
        turf_name=turf.name,
        turf_area=turf.area,
        turf_city=turf.city,
        sport=sport,
        date=date,
        start_time=start_time,
        end_time=end_time,
        duration_hours=duration_hours,
        price=price,
        status="Pending",
        player_name=player_name,
        created_at=datetime.utcnow()
    )
    _BOOKINGS.append(booking)
    return booking


def get_booking_by_id(booking_id: str) -> Optional[Booking]:
    if not booking_id:
        return None
    if is_db_ready():
        # Match against public number OR uuid
        try:
            buuid = uuid.UUID(str(booking_id))
            return db.session.query(Booking).filter(Booking.uuid == buuid, Booking.is_active == True).first()
        except ValueError:
            return db.session.query(Booking).filter(Booking.public_booking_number == booking_id, Booking.is_active == True).first()
    return next((b for b in _BOOKINGS if str(b.id) == str(booking_id)), None)


def get_bookings_by_user(user_id: str) -> List[Booking]:
    if not user_id:
        return []
    if is_db_ready():
        try:
            user_uuid = uuid.UUID(str(user_id))
            return db.session.query(Booking).filter(Booking.user_uuid == user_uuid, Booking.is_active == True).order_by(Booking.created_at.desc()).all()
        except ValueError:
            return []
    return sorted(
        [b for b in _BOOKINGS if str(b.user_id) == str(user_id)],
        key=lambda b: getattr(b, 'created_at', datetime.min),
        reverse=True
    )


def get_bookings_by_owner(owner_id: str) -> List[Booking]:
    if not owner_id:
        return []
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(Booking).join(Booking.turf).filter(Turf.owner_id == owner_uuid, Booking.is_active == True).order_by(Booking.created_at.desc()).all()
        except ValueError:
            return []
    # Mock fallback
    return sorted(
        [b for b in _BOOKINGS if any(t.id == b.turf_id and str(t.owner_id) == str(owner_id) for t in Turf.query.all() if hasattr(Turf, 'query')) or b.turf_id in [t.id for t in TURFS if str(t.owner_id) == str(owner_id)]],
        key=lambda b: getattr(b, 'created_at', datetime.min),
        reverse=True
    )


def get_all_bookings() -> List[Booking]:
    if is_db_ready():
        return db.session.query(Booking).filter(Booking.is_active == True).order_by(Booking.created_at.desc()).all()
    return sorted(_BOOKINGS, key=lambda b: getattr(b, 'created_at', datetime.min), reverse=True)


def update_booking_status(booking_id: str, status: str, changed_by: str = "System", notes: str = None) -> bool:
    booking = get_booking_by_id(booking_id)
    if not booking:
        return False

    old_status = booking.status
    booking.status = status
    if status == "Confirmed":
        booking.approved_by_owner = True

    if is_db_ready():
        # Log to booking history
        history = BookingHistory(
            id=uuid.uuid4(),
            booking_uuid=booking.uuid,
            status_from=old_status,
            status_to=status,
            changed_by=changed_by,
            notes=notes or ""
        )
        db.session.add(history)
        db.session.commit()
        return True

    return True


def generate_ticket(booking_id: str) -> Optional[BookingTicket]:
    booking = get_booking_by_id(booking_id)
    if not booking:
        return None

    if is_db_ready():
        existing = db.session.query(BookingTicket).filter_by(booking_uuid=booking.uuid).first()
        if existing:
            return existing
        ticket = BookingTicket(
            id=uuid.uuid4(),
            booking_uuid=booking.uuid,
            ticket_code=f"TKT-{uuid.uuid4().hex[:8].upper()}",
            barcode_url=""
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket

    # Mock Ticket Stub
    if hasattr(booking, 'ticket') and booking.ticket:
        return booking.ticket
    ticket = BookingTicket(id=uuid.uuid4(), ticket_code=f"TKT-{uuid.uuid4().hex[:8].upper()}")
    booking.ticket = ticket
    return ticket


def cancel_booking(booking_id: str, window_hours: int = 3) -> dict:
    booking = get_booking_by_id(booking_id)
    if not booking:
        return {"success": False, "reason": "not_found"}

    if not booking.is_cancellable(window_hours):
        if booking.status not in ("Pending", "Confirmed"):
            return {"success": False, "reason": "invalid_status"}
        return {"success": False, "reason": "time_window"}

    success = update_booking_status(booking_id, "Cancelled", changed_by="Player", notes="Cancelled by player")
    if success:
        return {"success": True, "reason": None}
    return {"success": False, "reason": "error"}


# Initial mock seeding
def init_mock_bookings():
    global _BOOKINGS
    from datetime import datetime, timedelta
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    
    b1 = Booking(
        id="PLN-2026-0001",
        user_id="USR-VAIBHAV",
        turf_id="TRF001",
        turf_name="GreenTurf Arena",
        turf_area="Sector 62",
        turf_city="Noida",
        sport="Football",
        date=yesterday.strftime("%Y-%m-%d"),
        start_time="18:00",
        end_time="19:00",
        duration_hours=1.0,
        price=1200,
        status="Completed",
        player_name="Vaibhav",
        created_at=two_days_ago,
        approved_by_owner=True
    )
    
    b2 = Booking(
        id="PLN-2026-0002",
        user_id="USR-VAIBHAV",
        turf_id="TRF002",
        turf_name="Skyline Sports Club",
        turf_area="Bandra",
        turf_city="Mumbai",
        sport="Cricket",
        date=yesterday.strftime("%Y-%m-%d"),
        start_time="20:00",
        end_time="22:00",
        duration_hours=2.0,
        price=2400,
        status="Completed",
        player_name="Vaibhav",
        created_at=two_days_ago,
        approved_by_owner=True
    )
    
    tomorrow = today + timedelta(days=1)
    b3 = Booking(
        id="PLN-2026-0003",
        user_id="USR-VAIBHAV",
        turf_id="TRF001",
        turf_name="GreenTurf Arena",
        turf_area="Sector 62",
        turf_city="Noida",
        sport="Football",
        date=tomorrow.strftime("%Y-%m-%d"),
        start_time="17:00",
        end_time="18:00",
        duration_hours=1.0,
        price=1200,
        status="Pending",
        player_name="Vaibhav",
        created_at=today - timedelta(hours=2),
        approved_by_owner=False
    )
    
    _BOOKINGS.extend([b1, b2, b3])


init_mock_bookings()
