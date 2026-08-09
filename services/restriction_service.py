import uuid
from datetime import datetime
from typing import List, Optional
from flask import current_app, has_app_context
from extensions import db
from models.customer_report import CustomerReport
from models.customer_restriction import CustomerRestriction
from models.booking import Booking

_RESTRICTIONS: List[CustomerRestriction] = []
_REPORTS: List[CustomerReport] = []


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def report_customer(owner_id: str, user_id: str, booking_id: str, reason: str, description: str) -> Optional[CustomerReport]:
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            user_uuid = uuid.UUID(str(user_id))
            booking_uuid = None
            if booking_id:
                # Resolve public booking number to UUID
                b = db.session.query(Booking).filter_by(public_booking_number=booking_id).first()
                if b:
                    booking_uuid = b.uuid

            report = CustomerReport(
                id=uuid.uuid4(),
                owner_id=owner_uuid,
                user_id=user_uuid,
                booking_uuid=booking_uuid,
                reason=reason,
                description=description
            )
            db.session.add(report)
            db.session.commit()
            return report
        except ValueError:
            return None

    # Fallback
    report = CustomerReport(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        user_id=user_id,
        booking_id=booking_id,
        reason=reason,
        description=description,
        created_at=datetime.utcnow()
    )
    _REPORTS.append(report)
    return report


def restrict_customer(owner_id: str, user_id: str, booking_id: str, reason: str, notes: str) -> Optional[CustomerRestriction]:
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            user_uuid = uuid.UUID(str(user_id))
            booking_uuid = None
            if booking_id:
                b = db.session.query(Booking).filter_by(public_booking_number=booking_id).first()
                if b:
                    booking_uuid = b.uuid

            restriction = CustomerRestriction(
                id=uuid.uuid4(),
                owner_id=owner_uuid,
                user_id=user_uuid,
                booking_reference_id=booking_uuid,
                reason=reason,
                notes=notes
            )
            db.session.add(restriction)
            db.session.commit()
            return restriction
        except ValueError:
            return None

    # Fallback
    restriction = CustomerRestriction(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        user_id=user_id,
        booking_id=booking_id,
        reason=reason,
        notes=notes,
        created_at=datetime.utcnow()
    )
    _RESTRICTIONS.append(restriction)
    return restriction


def is_customer_restricted(owner_id: str, user_id: str) -> bool:
    if not owner_id or not user_id:
        return False

    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            user_uuid = uuid.UUID(str(user_id))
            r = db.session.query(CustomerRestriction).filter_by(
                owner_id=owner_uuid, user_id=user_uuid, is_active=True
            ).first()
            return r is not None
        except ValueError:
            return False

    return any(
        str(r.owner_id) == str(owner_id) and str(r.user_id) == str(user_id) and getattr(r, 'is_active', True)
        for r in _RESTRICTIONS
    )


def remove_restriction(owner_id: str, user_id: str) -> bool:
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            user_uuid = uuid.UUID(str(user_id))
            r = db.session.query(CustomerRestriction).filter_by(
                owner_id=owner_uuid, user_id=user_uuid, is_active=True
            ).first()
            if r:
                r.is_active = False
                r.deleted_at = datetime.utcnow()
                db.session.commit()
                return True
        except ValueError:
            pass
        return False

    restriction = next(
        (r for r in _RESTRICTIONS if str(r.owner_id) == str(owner_id) and str(r.user_id) == str(user_id)), None
    )
    if restriction:
        _RESTRICTIONS.remove(restriction)
        return True
    return False


def get_restrictions_by_owner(owner_id: str) -> List[CustomerRestriction]:
    if not owner_id:
        return []
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(CustomerRestriction).filter_by(owner_id=owner_uuid, is_active=True).all()
        except ValueError:
            return []
    return [r for r in _RESTRICTIONS]


def get_reports_by_customer(user_id: str) -> List[CustomerReport]:
    if not user_id:
        return []
    if is_db_ready():
        try:
            user_uuid = uuid.UUID(str(user_id))
            return db.session.query(CustomerReport).filter_by(user_id=user_uuid, is_active=True).all()
        except ValueError:
            return []
    return [r for r in _REPORTS if str(r.user_id) == str(user_id)]


def get_reports_by_owner(owner_id: str) -> List[CustomerReport]:
    if not owner_id:
        return []
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(CustomerReport).filter_by(owner_id=owner_uuid, is_active=True).all()
        except ValueError:
            return []
    return [r for r in _REPORTS if str(r.owner_id) == str(owner_id)]
