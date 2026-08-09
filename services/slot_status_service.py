import uuid
from datetime import datetime
from typing import Optional, List
from flask import current_app, has_app_context
from extensions import db
from models.slot_status import SlotStatus
from models.turf import Turf

_SLOT_STATUSES = {}  # (turf_id, date, start_time) -> SlotStatus


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def get_slot_status(turf_id: str, date: str, start_time: str) -> Optional[SlotStatus]:
    if not turf_id:
        return None
    if is_db_ready():
        try:
            turf_uuid = uuid.UUID(str(turf_id))
            return db.session.query(SlotStatus).filter_by(
                turf_id=turf_uuid, date=date, start_time=start_time, is_active=True
            ).first()
        except ValueError:
            return None
    return _SLOT_STATUSES.get((turf_id, date, start_time))


def set_slot_status(
    turf_id: str, date: str, start_time: str, end_time: str,
    status: str, reason: str = None, updated_by: str = None
) -> SlotStatus:
    if is_db_ready():
        turf_uuid = uuid.UUID(str(turf_id))
        user_or_owner_uuid = None
        if updated_by:
            try:
                user_or_owner_uuid = uuid.UUID(str(updated_by))
            except ValueError:
                pass

        slot = get_slot_status(turf_id, date, start_time)
        if slot:
            slot.status = status
            slot.reason = reason
            slot.updated_by = user_or_owner_uuid
            slot.updated_at = datetime.utcnow()
            db.session.commit()
            return slot

        slot = SlotStatus(
            id=uuid.uuid4(),
            turf_id=turf_uuid,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status=status,
            reason=reason,
            updated_by=user_or_owner_uuid
        )
        db.session.add(slot)
        db.session.commit()
        return slot

    # Fallback to mock store
    slot = SlotStatus(
        id=str(uuid.uuid4()),
        turf_id=turf_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status=status,
        reason=reason,
        updated_by=updated_by,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    _SLOT_STATUSES[(turf_id, date, start_time)] = slot
    return slot


def clear_slot_status(turf_id: str, date: str, start_time: str) -> bool:
    slot = get_slot_status(turf_id, date, start_time)
    if not slot:
        return False

    if is_db_ready():
        # Hard or soft delete override status
        db.session.delete(slot)
        db.session.commit()
        return True

    key = (turf_id, date, start_time)
    if key in _SLOT_STATUSES:
        del _SLOT_STATUSES[key]
        return True
    return False


def get_custom_slot_statuses(turf_id: str, date: str) -> List[SlotStatus]:
    if not turf_id:
        return []
    if is_db_ready():
        try:
            turf_uuid = uuid.UUID(str(turf_id))
            return db.session.query(SlotStatus).filter_by(
                turf_id=turf_uuid, date=date, is_active=True
            ).all()
        except ValueError:
            return []
    return [s for s in _SLOT_STATUSES.values() if str(s.turf_id) == str(turf_id) and s.date == date]


def get_maintenance_slots(owner_id: str) -> List[SlotStatus]:
    if not owner_id:
        return []
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(SlotStatus).join(SlotStatus.turf).filter(
                Turf.owner_id == owner_uuid,
                SlotStatus.status == 'maintenance',
                SlotStatus.is_active == True
            ).all()
        except ValueError:
            return []
    return [s for s in _SLOT_STATUSES.values() if s.status == 'maintenance' and s.updated_by == owner_id]
