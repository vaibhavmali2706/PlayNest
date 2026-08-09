import uuid
import random
import bcrypt
from typing import Optional, List
from flask import current_app, has_app_context
from extensions import db
from models.owner import Owner, OwnerImage
from models.location import City, State
from services.mock_data import TURFS

_OWNERS = {}  # email -> Owner


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


def generate_owner_id() -> str:
    while True:
        num_part = "".join(random.choices("0123456789", k=12))
        owner_id = f"OWN-{num_part}"
        if not any(o.id == owner_id for o in _OWNERS.values()):
            return owner_id


def init_mock_owners():
    for t in TURFS:
        email = f"{t.owner_name.lower().replace(' ', '')}@playnest.app"
        if email not in _OWNERS:
            owner = Owner(
                id=t.owner_id,
                name=t.owner_name,
                email=email,
                phone="9876543210",
                password_hash=hash_password("password123"),
                status="Approved",
                turf_name=t.name,
                city=t.city,
                address=t.area,
            )
            _OWNERS[email] = owner


init_mock_owners()


def get_owner_by_email(email: str) -> Optional[Owner]:
    email = email.lower().strip()
    if is_db_ready():
        return db.session.query(Owner).filter(Owner.email == email, Owner.is_active == True).first()
    return _OWNERS.get(email)


def get_owner_by_id(owner_id: str) -> Optional[Owner]:
    if not owner_id:
        return None
    if is_db_ready():
        try:
            owner_uuid = uuid.UUID(str(owner_id))
            return db.session.query(Owner).filter(Owner.id == owner_uuid, Owner.is_active == True).first()
        except ValueError:
            return db.session.query(Owner).filter(Owner.email == owner_id, Owner.is_active == True).first()
    return next((o for o in _OWNERS.values() if str(o.id) == str(owner_id)), None)


def create_owner(
    name: str, email: str, phone: str, password: str,
    turf_name: str = "", aadhaar: str = "", pan: str = "", gst: str = "",
    business_license: str = "", address: str = "", city: str = "", state: str = "",
    pincode: str = "", bank_details: str = "", google_maps_location: str = "",
    front_image: str = "", ground_images: List[str] = None, night_images: List[str] = None,
    parking_images: List[str] = None, washroom_images: List[str] = None,
    changing_room_images: List[str] = None, identity_proof: str = ""
) -> Owner:
    email = email.lower().strip()
    password_hash = hash_password(password)

    if is_db_ready():
        owner = Owner(
            id=uuid.uuid4(),
            name=name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            status="Pending",
            turf_name=turf_name,
            aadhaar=aadhaar,
            pan=pan,
            gst=gst,
            business_license=business_license,
            address=address,
            pincode=pincode,
            bank_details=bank_details,
            google_maps_location=google_maps_location,
            identity_proof=identity_proof
        )
        if city:
            owner.city = city
        if state:
            owner.state = state

        db.session.add(owner)
        db.session.commit()

        # Add related owner images
        if front_image:
            db.session.add(OwnerImage(id=uuid.uuid4(), owner_id=owner.id, url=front_image, image_type="front"))
        
        for imgs, itype in [
            (ground_images, "ground"),
            (night_images, "night"),
            (parking_images, "parking"),
            (washroom_images, "washroom"),
            (changing_room_images, "changing_room"),
        ]:
            if imgs:
                for img_url in imgs:
                    if img_url:
                        db.session.add(OwnerImage(id=uuid.uuid4(), owner_id=owner.id, url=img_url, image_type=itype))
        db.session.commit()
        return owner

    # Fallback to mock store
    owner_id = generate_owner_id()
    owner = Owner(
        id=owner_id,
        name=name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        status="Pending",
        turf_name=turf_name,
        aadhaar=aadhaar,
        pan=pan,
        gst=gst,
        business_license=business_license,
        address=address,
        city=city,
        state=state,
        pincode=pincode,
        bank_details=bank_details,
        google_maps_location=google_maps_location,
        identity_proof=identity_proof
    )
    _OWNERS[email] = owner
    return owner


def get_all_owners() -> List[Owner]:
    if is_db_ready():
        return db.session.query(Owner).filter(Owner.is_active == True).all()
    return list(_OWNERS.values())


def update_owner_status(owner_id: str, status: str) -> bool:
    owner = get_owner_by_id(owner_id)
    if owner:
        owner.status = status
        
        # also update any associated mock/database turfs
        if is_db_ready():
            from models.turf import Turf as TurfModel
            turfs = db.session.query(TurfModel).filter_by(owner_id=owner.id).all()
            for t in turfs:
                t.verified = (status == "Approved")
            db.session.commit()
        else:
            for t in TURFS:
                if str(t.owner_id) == str(owner_id):
                    t.verified = (status == "Approved")
        return True
    return False


def delete_owner(owner_id: str) -> bool:
    owner = get_owner_by_id(owner_id)
    if not owner:
        return False

    if is_db_ready():
        owner.is_active = False
        # Soft delete associated turfs, bookings, complaint records
        from models.turf import Turf as TurfModel
        from models.booking import Booking as BookingModel
        from models.complaint import Complaint as ComplaintModel
        
        turfs = db.session.query(TurfModel).filter_by(owner_id=owner.id).all()
        for t in turfs:
            t.is_active = False
            # soft delete bookings for this turf
            bookings = db.session.query(BookingModel).filter_by(turf_uuid=t.id).all()
            for b in bookings:
                b.is_active = False
            
        complaints = db.session.query(ComplaintModel).filter_by(owner_id=owner.id).all()
        for c in complaints:
            c.is_active = False
            
        db.session.commit()
        return True

    # Mock deletion
    email_to_remove = owner.email
    if email_to_remove in _OWNERS:
        del _OWNERS[email_to_remove]
        
        # Remove associated mock turfs
        i = 0
        while i < len(TURFS):
            if str(TURFS[i].owner_id) == str(owner_id):
                TURFS.pop(i)
            else:
                i += 1
        return True
    return False


def warn_owner(owner_id: str) -> int:
    owner = get_owner_by_id(owner_id)
    if owner:
        owner.warnings_count += 1
        if is_db_ready():
            db.session.commit()
        return owner.warnings_count
    return 0
