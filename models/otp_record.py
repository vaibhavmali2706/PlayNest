import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from extensions import db

class OtpRecord(db.Model):
    __tablename__ = 'otp_records'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    otp_code = db.Column(db.String(256), nullable=False) # hashed OTP code
    purpose = db.Column(db.String(50), nullable=False) # 'EMAIL_VERIFICATION', 'PASSWORD_RESET'
    attempts = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='otp_records')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

