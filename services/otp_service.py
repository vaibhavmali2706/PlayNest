import uuid
import random
import string
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from flask import current_app, has_app_context
from extensions import db
from models.otp_record import OtpRecord
from models.user import User

_OTP_STORE = {}  # email -> _OtpRecord fallback


class _OtpRecordFallback:
    def __init__(self, code, created_at, purpose='EMAIL_VERIFICATION'):
        self.code = code
        self.created_at = created_at
        self.attempts = 0
        self.last_sent_at = time.time()
        self.purpose = purpose


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def _generate_code(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode('utf-8')).hexdigest()


def can_resend(email: str) -> bool:
    email = email.lower().strip()
    if is_db_ready():
        # Get newest record for this email
        record = db.session.query(OtpRecord).filter_by(email=email).order_by(OtpRecord.created_at.desc()).first()
        if not record:
            return True
        elapsed = (datetime.utcnow() - record.created_at).total_seconds()
        return elapsed >= current_app.config["OTP_RESEND_SECONDS"]

    # Fallback
    record = _OTP_STORE.get(email)
    if not record:
        return True
    elapsed = time.time() - record.last_sent_at
    return elapsed >= current_app.config["OTP_RESEND_SECONDS"]


def seconds_until_resend(email: str) -> int:
    email = email.lower().strip()
    if is_db_ready():
        record = db.session.query(OtpRecord).filter_by(email=email).order_by(OtpRecord.created_at.desc()).first()
        if not record:
            return 0
        elapsed = (datetime.utcnow() - record.created_at).total_seconds()
        remaining = current_app.config["OTP_RESEND_SECONDS"] - elapsed
        return max(0, int(remaining))

    # Fallback
    record = _OTP_STORE.get(email)
    if not record:
        return 0
    elapsed = time.time() - record.last_sent_at
    remaining = current_app.config["OTP_RESEND_SECONDS"] - elapsed
    return max(0, int(remaining))


def generate_otp(email: str, purpose: str = 'EMAIL_VERIFICATION', user_id: str = None) -> str:
    email = email.lower().strip()
    code = _generate_code(current_app.config.get("OTP_LENGTH", 6))
    hashed = _hash_code(code)

    if is_db_ready():
        # Delete old records of same purpose for this email
        try:
            db.session.query(OtpRecord).filter_by(email=email, purpose=purpose).delete()
            db.session.commit()
        except Exception:
            db.session.rollback()

        user_uuid = None
        if user_id:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                # Find user by email fallback
                u = db.session.query(User).filter_by(email=email).first()
                if u:
                    user_uuid = u.id

        record = OtpRecord(
            id=uuid.uuid4(),
            user_id=user_uuid,
            email=email,
            otp_code=hashed,
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=current_app.config.get("OTP_VALID_MINUTES", 5)),
            attempts=0
        )
        db.session.add(record)
        db.session.commit()
        return code

    # Fallback
    _OTP_STORE[email] = _OtpRecordFallback(code=code, created_at=time.time(), purpose=purpose)
    return code


def verify_otp(email: str, code: str, purpose: str = 'EMAIL_VERIFICATION') -> dict:
    email = email.lower().strip()
    code_strip = str(code).strip()

    if is_db_ready():
        # If user is already verified for email verification, treat as success (handles race conditions)
        if purpose == 'EMAIL_VERIFICATION':
            u = db.session.query(User).filter_by(email=email).first()
            if u and u.is_verified:
                return {"success": True, "reason": None}

        record = db.session.query(OtpRecord).filter_by(email=email, purpose=purpose).order_by(OtpRecord.created_at.desc()).first()
        if not record or record.verified_at:
            return {"success": False, "reason": "invalid"}

        max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)
        if record.attempts >= max_attempts:
            return {"success": False, "reason": "too_many_attempts"}

        if datetime.utcnow() > record.expires_at:
            return {"success": False, "reason": "expired"}

        record.attempts += 1
        db.session.commit()

        hashed_input = _hash_code(code_strip)
        if record.otp_code != hashed_input:
            return {"success": False, "reason": "invalid"}

        # Success: Mark verified
        record.verified_at = datetime.utcnow()
        db.session.commit()
        
        # Clean up / Delete verified records
        try:
            db.session.delete(record)
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        return {"success": True, "reason": None}

    # Fallback
    if purpose == 'EMAIL_VERIFICATION':
        from services.user_service import _USERS
        u = _USERS.get(email)
        if u and getattr(u, 'is_verified', False):
            return {"success": True, "reason": None}

    record = _OTP_STORE.get(email)
    if not record or record.purpose != purpose:
        return {"success": False, "reason": "invalid"}

    max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)
    valid_minutes = current_app.config.get("OTP_VALID_MINUTES", 5)

    if record.attempts >= max_attempts:
        return {"success": False, "reason": "too_many_attempts"}

    age_minutes = (time.time() - record.created_at) / 60
    if age_minutes > valid_minutes:
        return {"success": False, "reason": "expired"}

    record.attempts += 1

    if record.code != code_strip:
        return {"success": False, "reason": "invalid"}

    del _OTP_STORE[email]
    return {"success": True, "reason": None}



def attempts_remaining(email: str, purpose: str = 'EMAIL_VERIFICATION') -> int:
    email = email.lower().strip()
    max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)

    if is_db_ready():
        record = db.session.query(OtpRecord).filter_by(email=email, purpose=purpose).order_by(OtpRecord.created_at.desc()).first()
        if not record:
            return max_attempts
        return max(0, max_attempts - record.attempts)

    record = _OTP_STORE.get(email)
    if not record or record.purpose != purpose:
        return max_attempts
    return max(0, max_attempts - record.attempts)
