import os
import uuid
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app, abort
from werkzeug.utils import secure_filename

from services import turf_service, booking_service, owner_service, email_service, otp_service, user_service
from services.mock_data import TURFS
from utils.image_optimizer import save_and_optimize_image

owner_bp = Blueprint("owner", __name__, url_prefix="/owner")


def owner_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("owner_id"):
            flash("Please sign in to your owner partner account.", "warning")
            return redirect(url_for("owner.login"))
        return f(*args, **kwargs)
    return wrapped


def approved_owner_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("owner_id"):
            flash("Please sign in to your owner partner account.", "warning")
            return redirect(url_for("owner.login"))
        owner = owner_service.get_owner_by_id(session["owner_id"])
        if not owner or owner.status != "Approved":
            flash("Access denied. Your partner profile is currently pending verification.", "warning")
            return redirect(url_for("owner.dashboard"))
        return f(*args, **kwargs)
    return wrapped


@owner_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("owner_id"):
        return redirect(url_for("owner.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")

        owner = owner_service.get_owner_by_email(email)
        if owner and owner_service.check_password(password, owner.password_hash):
            session["owner_id"] = str(owner.id)
            session["owner_name"] = owner.name
            flash(f"Welcome back, {owner.name}! 👋 Owner portal active.", "success")
            return redirect(url_for("owner.dashboard"))

        flash("Invalid partner credentials. Please try again.", "danger")

    return render_template("owner/login.html")


@owner_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("owner_id"):
        return redirect(url_for("owner.dashboard"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        # Business Details
        turf_name = request.form.get("turf_name")
        aadhaar = request.form.get("aadhaar")
        pan = request.form.get("pan")
        gst = request.form.get("gst", "")
        business_license = request.form.get("business_license")
        address = request.form.get("address")
        city = request.form.get("city")
        state = request.form.get("state")
        pincode = request.form.get("pincode")
        bank_details = request.form.get("bank_details", "")
        google_maps_location = request.form.get("google_maps_location", "")

        if owner_service.get_owner_by_email(email):
            flash("This email is already registered as a turf partner.", "danger")
            return render_template("owner/register.html")

        # Handle image uploads
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "owners")
        os.makedirs(upload_dir, exist_ok=True)

        def process_upload(field_name):
            file = request.files.get(field_name)
            if file and file.filename:
                filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                saved_name, _ = save_and_optimize_image(file, upload_dir, filename)
                return f"uploads/owners/{saved_name}"
            return ""

        def process_multiple_uploads(field_name):
            files = request.files.getlist(field_name)
            paths = []
            for file in files:
                if file and file.filename:
                    filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                    saved_name, _ = save_and_optimize_image(file, upload_dir, filename)
                    paths.append(f"uploads/owners/{saved_name}")
            return paths

        front_image = process_upload("front_image")
        identity_proof = process_upload("identity_proof")
        ground_images = process_multiple_uploads("ground_images")
        night_images = process_multiple_uploads("night_images")
        parking_images = process_multiple_uploads("parking_images")
        washroom_images = process_multiple_uploads("washroom_images")
        changing_room_images = process_multiple_uploads("changing_room_images")

        owner = owner_service.create_owner(
            name=name, email=email, phone=phone, password=password,
            turf_name=turf_name, aadhaar=aadhaar, pan=pan, gst=gst,
            business_license=business_license, address=address, city=city, state=state,
            pincode=pincode, bank_details=bank_details, google_maps_location=google_maps_location,
            front_image=front_image, ground_images=ground_images, night_images=night_images,
            parking_images=parking_images, washroom_images=washroom_images,
            changing_room_images=changing_room_images, identity_proof=identity_proof
        )

        # Notify owner
        email_service._dispatch(
            subject=f"PlayNest Partner Application Received — {owner.id}",
            recipient=owner.email,
            html=f"<h3>Welcome {owner.name},</h3><p>Your PlayNest Partner Application for <strong>{owner.turf_name}</strong> is under review. Your Partner ID is <strong>{owner.id}</strong>.</p>",
            kind="Partner Application Received"
        )

        flash("Partner registration submitted successfully! Under review.", "success")
        session["owner_id"] = str(owner.id)
        session["owner_name"] = owner.name
        return redirect(url_for("owner.dashboard"))

    return render_template("owner/register.html")


@owner_bp.route("/dashboard")
@owner_required
def dashboard():
    owner = owner_service.get_owner_by_id(session["owner_id"])
    if not owner:
        session.clear()
        return redirect(url_for("owner.login"))

    if owner.status != "Approved":
        return render_template("owner/pending_dashboard.html", owner=owner)

    owner_id = owner.id
    turfs = turf_service.get_turfs_by_owner(owner_id)
    bookings = booking_service.get_bookings_by_owner(owner_id)

    stats = {
        "turfs": len(turfs),
        "bookings": len(bookings),
        "pending": len([b for b in bookings if b.status == "Pending"]),
        "revenue": sum(b.price for b in bookings if b.status in ("Confirmed", "Completed")),
    }

    return render_template(
        "owner/dashboard.html", owner=owner, turfs=turfs, bookings=bookings[:8], stats=stats,
    )


@owner_bp.route("/turfs")
@approved_owner_required
def turfs():
    owner_turfs = turf_service.get_turfs_by_owner(session["owner_id"])
    return render_template("owner/turfs.html", turfs=owner_turfs)


@owner_bp.route("/bookings")
@approved_owner_required
def bookings():
    owner_bookings = booking_service.get_bookings_by_owner(session["owner_id"])
    return render_template("owner/bookings.html", bookings=owner_bookings)


@owner_bp.route("/bookings/<booking_id>/approve", methods=["POST"])
@approved_owner_required
def approve_booking(booking_id):
    booking_service.update_booking_status(booking_id, "Confirmed", changed_by="Owner")
    flash(f"Booking {booking_id} approved.", "success")
    return redirect(url_for("owner.bookings"))


@owner_bp.route("/bookings/<booking_id>/reject", methods=["POST"])
@approved_owner_required
def reject_booking(booking_id):
    booking_service.update_booking_status(booking_id, "Cancelled", changed_by="Owner")
    flash(f"Booking {booking_id} rejected.", "info")
    return redirect(url_for("owner.bookings"))


@owner_bp.route("/analytics")
@approved_owner_required
def analytics():
    owner_bookings = booking_service.get_bookings_by_owner(session["owner_id"])
    return render_template("owner/analytics.html", bookings=owner_bookings)


@owner_bp.route("/manage-slots", methods=["GET", "POST"])
@approved_owner_required
def manage_slots():
    owner_id = session["owner_id"]
    turfs = turf_service.get_turfs_by_owner(owner_id)
    if not turfs:
        flash("Please register a turf first before managing slots.", "warning")
        return redirect(url_for("owner.turfs"))

    # Selected Turf
    turf_id = request.args.get("turf_id") or request.form.get("turf_id")
    selected_turf = None
    if turf_id:
        selected_turf = next((t for t in turfs if t.id == turf_id), None)
    if not selected_turf:
        selected_turf = turfs[0]
        turf_id = selected_turf.id

    # Selected Date
    from utils.helpers import today_str, next_n_days
    date_str = request.args.get("date") or request.form.get("date") or today_str()
    
    # Handle Slot Status update
    if request.method == "POST":
        action = request.form.get("action")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        
        # Verify ownership
        if selected_turf.owner_id != owner_id:
            abort(403)
            
        from services import slot_status_service
        
        if action == "mark_unavailable":
            reason = request.form.get("reason")
            
            # Map reason to status
            if reason in ("maintenance", "holiday"):
                status = reason
            else:
                status = "unavailable"
                
            slot_status_service.set_slot_status(
                turf_id=turf_id,
                date=date_str,
                start_time=start_time,
                end_time=end_time,
                status=status,
                reason=reason,
                updated_by=owner_id
            )
            flash(f"Slot {start_time} - {end_time} marked as Unavailable ({reason.replace('_', ' ').title()}).", "success")
            
        elif action == "mark_available":
            slot_status_service.remove_slot_status(turf_id, date_str, start_time)
            flash(f"Slot {start_time} - {end_time} marked as Available.", "success")
            
        return redirect(url_for("owner.manage_slots", turf_id=turf_id, date=date_str))

    # Load slots and analytics
    from services import slot_status_service
    slots = slot_status_service.get_slots_for_owner_view(turf_id, date_str)
    
    # We want Today's Summary for Analytics (based on selected turf)
    analytics_summary = slot_status_service.get_today_summary(turf_id)
    
    dates = next_n_days(7) # Display next 7 days for selection
    
    return render_template(
        "owner/manage_slots.html",
        turfs=turfs,
        selected_turf=selected_turf,
        selected_date=date_str,
        slots=slots,
        analytics=analytics_summary,
        dates=dates
    )


@owner_bp.route("/bookings/<booking_id>")
@approved_owner_required
def booking_details(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    if not booking:
        abort(404)
        
    # Security: Verify that the turf of this booking belongs to the logged-in owner
    turf = turf_service.get_turf_by_id(booking.turf_id)
    if not turf or str(turf.owner_id) != str(session["owner_id"]):
        abort(403)
        
    # Get user information
    user = user_service.get_user_by_id(booking.user_id)
    
    # Check if this customer is currently restricted by this owner
    from services.restriction_service import get_restriction, get_reports_by_booking
    restriction = get_restriction(session["owner_id"], booking.user_id)
    reports = get_reports_by_booking(booking_id)
    
    return render_template(
        "owner/booking_details.html",
        booking=booking,
        turf=turf,
        customer=user,
        restriction=restriction,
        reports=reports
    )


@owner_bp.route("/bookings/<booking_id>/report", methods=["POST"])
@approved_owner_required
def report_and_restrict(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    if not booking:
        abort(404)
        
    turf = turf_service.get_turf_by_id(booking.turf_id)
    if not turf or str(turf.owner_id) != str(session["owner_id"]):
        abort(403)
        
    if booking.status != "Completed":
        flash("You can only report or restrict customers after a completed booking.", "danger")
        return redirect(url_for("owner.booking_details", booking_id=booking_id))
        
    reason = request.form.get("reason")
    notes = request.form.get("notes", "").strip()
    restrict = request.form.get("restrict") == "yes"
    
    from services import restriction_service
    
    try:
        # File report (customer_reports)
        restriction_service.report_customer(
            owner_id=session["owner_id"],
            user_id=booking.user_id,
            booking_id=booking_id,
            reason=reason,
            description=notes
        )
        
        # Optionally restrict (customer_restrictions)
        if restrict:
            restriction_service.restrict_customer(
                owner_id=session["owner_id"],
                user_id=booking.user_id,
                reason=reason
            )
            flash("Customer reported and restricted from booking your turf.", "success")
        else:
            flash("Customer complaint submitted successfully.", "success")
            
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for("owner.booking_details", booking_id=booking_id))


@owner_bp.route("/bookings/<booking_id>/unrestrict", methods=["POST"])
@approved_owner_required
def unrestrict_customer_route(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    if not booking:
        abort(404)
        
    turf = turf_service.get_turf_by_id(booking.turf_id)
    if not turf or str(turf.owner_id) != str(session["owner_id"]):
        abort(403)
        
    from services import restriction_service
    restriction_service.unrestrict_customer(session["owner_id"], booking.user_id)
    flash("Restriction removed. Customer can book your turf again.", "success")
    return redirect(url_for("owner.booking_details", booking_id=booking_id))


@owner_bp.route("/complaints")
@approved_owner_required
def complaints():
    from services import complaint_service
    owner_complaints = complaint_service.get_complaints_by_owner(session["owner_id"])
    return render_template("owner/complaints.html", complaints=owner_complaints)



@owner_bp.route("/turf/add", methods=["GET", "POST"])
@approved_owner_required
def add_turf():
    owner = owner_service.get_owner_by_id(session["owner_id"])
    if request.method == "POST":
        name = request.form.get("name")
        city = request.form.get("city")
        area = request.form.get("area")
        sports = request.form.getlist("sports")
        price_per_hour = request.form.get("price_per_hour")
        facilities = request.form.getlist("facilities")
        indoor = request.form.get("indoor") == "true"
        description = request.form.get("description")
        opening_hours = request.form.get("opening_hours")
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "turfs")
        os.makedirs(upload_dir, exist_ok=True)

        # Handle Cover Upload
        cover_file = request.files.get("cover_image")
        hero_image = ""
        if cover_file and cover_file.filename:
            filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{cover_file.filename}")
            saved_name, _ = save_and_optimize_image(cover_file, upload_dir, filename)
            hero_image = url_for("static", filename=f"uploads/turfs/{saved_name}")
        else:
            hero_image = "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?auto=format&fit=crop&w=1200&q=80"

        # Handle Gallery Uploads
        gallery_files = request.files.getlist("gallery_images")
        gallery = []
        for file in gallery_files:
            if file and file.filename:
                filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                saved_name, _ = save_and_optimize_image(file, upload_dir, filename)
                gallery.append(url_for("static", filename=f"uploads/turfs/{saved_name}"))

        if not gallery:
            gallery = [hero_image]

        turf_service.add_new_turf(
            name=name, city=city, area=area, sports=sports, price_per_hour=price_per_hour,
            facilities=facilities, indoor=indoor, hero_image=hero_image, gallery=gallery,
            description=description, opening_hours=opening_hours, owner_id=owner.id,
            owner_name=owner.name, lat=lat, lng=lng
        )
        flash("Turf added successfully!", "success")
        return redirect(url_for("owner.turfs"))

    return render_template("owner/add_edit_turf.html", action="Add", turf=None)


@owner_bp.route("/turf/<turf_id>/edit", methods=["GET", "POST"])
@approved_owner_required
def edit_turf(turf_id):
    turf = turf_service.get_turf_by_id(turf_id)
    if not turf or str(turf.owner_id) != str(session["owner_id"]):
        abort(404)

    if request.method == "POST":
        name = request.form.get("name")
        city = request.form.get("city")
        area = request.form.get("area")
        sports = request.form.getlist("sports")
        price_per_hour = request.form.get("price_per_hour")
        facilities = request.form.getlist("facilities")
        indoor = request.form.get("indoor") == "true"
        description = request.form.get("description")
        opening_hours = request.form.get("opening_hours")
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "turfs")
        os.makedirs(upload_dir, exist_ok=True)

        cover_file = request.files.get("cover_image")
        hero_image = ""
        if cover_file and cover_file.filename:
            filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{cover_file.filename}")
            saved_name, _ = save_and_optimize_image(cover_file, upload_dir, filename)
            hero_image = url_for("static", filename=f"uploads/turfs/{saved_name}")

        gallery_files = request.files.getlist("gallery_images")
        gallery = []
        for file in gallery_files:
            if file and file.filename:
                filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                saved_name, _ = save_and_optimize_image(file, upload_dir, filename)
                gallery.append(url_for("static", filename=f"uploads/turfs/{saved_name}"))

        turf_service.update_turf(
            turf_id=turf_id, name=name, city=city, area=area, sports=sports,
            price_per_hour=price_per_hour, facilities=facilities, indoor=indoor,
            hero_image=hero_image, gallery=gallery if gallery else None,
            description=description, opening_hours=opening_hours, lat=lat, lng=lng
        )
        flash("Turf details updated successfully!", "success")
        return redirect(url_for("owner.turfs"))

    return render_template("owner/add_edit_turf.html", action="Edit", turf=turf)


@owner_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if session.get("owner_id"):
        return redirect(url_for("owner.dashboard"))

    from forms import ForgotPasswordForm
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        owner = owner_service.get_owner_by_email(email)

        if owner:
            session["owner_reset_email"] = owner.email
            otp_code = otp_service.generate_otp(owner.email, purpose='PASSWORD_RESET')
            
            # Send OTP email
            email_service.send_otp_email(owner.email, owner.name, otp_code)
            
            if current_app.config["DEBUG"] and (not current_app.config["MAIL_CONFIGURED"] or email.endswith("@playnest.app")):
                flash(f"DEV MODE — Partner Reset OTP is: {otp_code}", "dev")
                
            flash("An OTP has been sent to your email to reset your partner password.", "info")
            return redirect(url_for("owner.reset_password"))
        else:
            form.email.errors.append("No partner account associated with this email address.")

    return render_template("owner/forgot_password.html", form=form)


@owner_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("owner_reset_email")
    if not email:
        return redirect(url_for("owner.forgot_password"))

    from forms import ResetPasswordForm
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Verify the reset OTP
        result = otp_service.verify_otp(email, form.otp_code.data, purpose='PASSWORD_RESET')
        
        if result["success"]:
            owner = owner_service.get_owner_by_email(email)
            if owner:
                owner.password_hash = owner_service.hash_password(form.password.data)
                session.pop("owner_reset_email", None)
                flash("Your partner password has been reset successfully. Please login with your new password.", "success")
                return redirect(url_for("owner.login"))
        else:
            reason_messages = {
                "expired": "Your OTP has expired. Please request another reset code.",
                "too_many_attempts": "Too many attempts. Please request another reset code.",
                "invalid": "Invalid OTP code. Please try again.",
            }
            form.otp_code.errors.append(reason_messages.get(result["reason"], "Verification failed."))

    return render_template("owner/reset_password.html", form=form, email=email)


@owner_bp.route("/logout")
def logout():
    session.pop("owner_id", None)
    session.pop("owner_name", None)
    flash("Logged out of owner portal.", "info")
    return redirect(url_for("owner.login"))
