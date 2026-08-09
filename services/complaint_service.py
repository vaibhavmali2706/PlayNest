import uuid
from datetime import datetime
from typing import List, Optional
from flask import current_app, has_app_context
from extensions import db
from models.complaint import Complaint
from models.turf import Turf

_COMPLAINTS: List[Complaint] = []


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def create_complaint(user_id: str, user_name: str, turf_id: str, title: str, description: str) -> Optional[Complaint]:
    if is_db_ready():
        try:
            user_uuid = uuid.UUID(str(user_id))
            turf_uuid = uuid.UUID(str(turf_id))
            
            # Find owner of turf
            turf = db.session.query(Turf).filter_by(id=turf_uuid).first()
            if not turf:
                return None
            
            complaint = Complaint(
                id=uuid.uuid4(),
                user_id=user_uuid,
                user_name=user_name,
                turf_id=turf_uuid,
                owner_id=turf.owner_id,
                title=title,
                description=description,
                status="Pending"
            )
            db.session.add(complaint)
            db.session.commit()
            return complaint
        except ValueError:
            return None

    # Fallback
    from services.turf_service import get_turf_by_id
    turf = get_turf_by_id(turf_id)
    if not turf:
        return None

    complaint = Complaint(
        id=str(uuid.uuid4()),
        user_id=user_id,
        user_name=user_name,
        turf_id=turf_id,
        turf_name=turf.name,
        owner_id=turf.owner_id,
        title=title,
        description=description,
        status="Pending",
        created_at=datetime.utcnow()
    )
    _COMPLAINTS.append(complaint)
    return complaint


def get_complaints_by_owner(owner_id: str) -> List[Complaint]:
    if not owner_id:
        return []
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(Complaint).filter_by(owner_id=owner_uuid, is_active=True).order_by(Complaint.created_at.desc()).all()
        except ValueError:
            return []
    return [c for c in _COMPLAINTS if str(c.owner_id) == str(owner_id)]


def get_complaints_by_turf(turf_id: str) -> List[Complaint]:
    if not turf_id:
        return []
    if is_db_ready():
        try:
            turf_uuid = uuid.UUID(str(turf_id))
            return db.session.query(Complaint).filter_by(turf_id=turf_uuid, is_active=True).order_by(Complaint.created_at.desc()).all()
        except ValueError:
            return []
    return [c for c in _COMPLAINTS if str(c.turf_id) == str(turf_id)]


def update_complaint_status(complaint_id: str, status: str) -> bool:
    if is_db_ready():
        try:
            cuuid = uuid.UUID(str(complaint_id))
            complaint = db.session.query(Complaint).filter_by(id=cuuid).first()
            if complaint:
                complaint.status = status
                complaint.updated_at = datetime.utcnow()
                db.session.commit()
                return True
        except ValueError:
            pass
        return False

    complaint = next((c for c in _COMPLAINTS if str(c.id) == str(complaint_id)), None)
    if complaint:
        complaint.status = status
        return True
    return False


def get_all_complaints() -> List[Complaint]:
    if is_db_ready():
        return db.session.query(Complaint).filter_by(is_active=True).order_by(Complaint.created_at.desc()).all()
    return _COMPLAINTS
