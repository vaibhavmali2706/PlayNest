import uuid
import bcrypt
from typing import Optional, List
from flask import current_app, has_app_context
from extensions import db
from models.user import User
from models.location import City
from models.turf import Turf

# Mock in-memory repository for fallback
_USERS = {}  # email -> User


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def check_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def is_db_ready() -> bool:
    if has_app_context():
        return current_app.config.get("DATABASE_READY", False)
    return False


def get_user_by_email(email: str) -> Optional[User]:
    email = email.lower().strip()
    if is_db_ready():
        return db.session.query(User).filter(User.email == email, User.is_active == True).first()
    return _USERS.get(email)


def get_user_by_id(user_id: str) -> Optional[User]:
    if not user_id:
        return None
    if is_db_ready():
        try:
            user_uuid = uuid.UUID(str(user_id))
            return db.session.query(User).filter(User.id == user_uuid, User.is_active == True).first()
        except ValueError:
            # Fallback if user_id is a non-UUID string
            return db.session.query(User).filter(User.email == user_id, User.is_active == True).first()
    return next((u for u in _USERS.values() if str(u.id) == str(user_id)), None)


def create_or_update_user(name: str, email: str, phone: str, city: str, password: str = None) -> User:
    email = email.lower().strip()
    password_hash = hash_password(password) if password else ""

    if is_db_ready():
        user = get_user_by_email(email)
        if user:
            user.name = name or user.name
            user.phone = phone or user.phone
            if city:
                user.city = city
            if password_hash:
                user.password_hash = password_hash
            db.session.commit()
            return user
        
        # Create new database user
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            is_verified=False
        )
        if city:
            user.city = city
        db.session.add(user)
        db.session.commit()
        return user

    # Fallback to mock store
    existing = _USERS.get(email)
    if existing:
        existing.name = name or existing.name
        existing.phone = phone or existing.phone
        existing.city = city or existing.city
        if password_hash:
            existing.password_hash = password_hash
        return existing

    user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    user = User(
        id=user_id,
        name=name,
        email=email,
        phone=phone,
        city=city,
        password_hash=password_hash,
        is_verified=False
    )
    _USERS[email] = user
    return user


def toggle_favourite(user_id: str, turf_id: str) -> bool:
    """Returns True if turf is now a favourite, False if removed."""
    user = get_user_by_id(user_id)
    if not user:
        return False

    if is_db_ready():
        try:
            turf_uuid = uuid.UUID(str(turf_id))
            turf = db.session.query(Turf).filter_by(id=turf_uuid).first()
            if turf:
                if turf in user.favourites:
                    user.favourites.remove(turf)
                    db.session.commit()
                    return False
                else:
                    user.favourites.append(turf)
                    db.session.commit()
                    return True
        except Exception:
            pass
        return False

    # Fallback mock favourite toggle
    if turf_id in user.favourite_turf_ids:
        user.favourites.remove(next((t for t in user.favourites if str(t.id) == str(turf_id)), None))
        return False
    # Mock fallback turf object stub
    mock_turf = Turf(id=turf_id, name="Mock Turf", city="Mumbai", owner_id=uuid.uuid4())
    user.favourites.append(mock_turf)
    return True


def is_favourite(user_id: str, turf_id: str) -> bool:
    user = get_user_by_id(user_id)
    if not user:
        return False
    return str(turf_id) in user.favourite_turf_ids


def get_all_users() -> List[User]:
    if is_db_ready():
        return db.session.query(User).filter(User.is_active == True).all()
    return list(_USERS.values())


def total_users() -> int:
    if is_db_ready():
        return db.session.query(db.func.count(User.id)).filter(User.is_active == True).scalar()
    return len(_USERS)


# Seed a premium verified user Vaibhav for immediate login & demonstration
def seed_user_vaibhav():
    vaibhav = User(
        id="USR-VAIBHAV",
        name="Vaibhav",
        email="vaibhav@playnest.app",
        phone="9876543210",
        city="Kolhapur",
        password_hash=hash_password("password123"),
        is_verified=True
    )
    _USERS[vaibhav.email] = vaibhav

seed_user_vaibhav()
