from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app

from extensions import db
from services import turf_service, booking_service, user_service, owner_service, email_service
from services.mock_data import TURFS, CITIES, SPORTS
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ADMIN_PASSCODE = "270607"


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("admin.dashboard"))

    passcode = current_app.config.get("ADMIN_PASSCODE", ADMIN_PASSCODE)

    if request.method == "POST":
        code = request.form.get("passcode", "")
        if code == passcode:
            session["is_admin"] = True
            flash("Welcome to the PlayNest control room.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Incorrect passcode.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    all_bookings = booking_service.get_all_bookings()
    all_owners = owner_service.get_all_owners()
    
    stats = {
        "users": user_service.total_users(),
        "owners": len(all_owners),
        "pending_owners": len([o for o in all_owners if o.status == "Pending"]),
        "turfs": len(TURFS),
        "bookings": len(all_bookings),
        "cities": len(CITIES),
        "sports": len(SPORTS),
        "revenue": sum(b.price for b in all_bookings if b.status in ("Confirmed", "Completed")),
        "pending": len([b for b in all_bookings if b.status == "Pending"]),
    }
    return render_template(
        "admin/dashboard.html", stats=stats, recent_bookings=all_bookings[:8],
        turfs=TURFS[:6],
    )


@admin_bp.route("/users")
@admin_required
def users():
    return render_template("admin/users.html", users=user_service.get_all_users())


@admin_bp.route("/turfs")
@admin_required
def turfs():
    return render_template("admin/turfs.html", turfs=TURFS)


@admin_bp.route("/bookings")
@admin_required
def bookings():
    return render_template("admin/bookings.html", bookings=booking_service.get_all_bookings())


@admin_bp.route("/partners")
@admin_required
def partners():
    all_owners = owner_service.get_all_owners()
    return render_template("admin/partners.html", partners=all_owners)


@admin_bp.route("/partners/<owner_id>/approve", methods=["POST"])
@admin_required
def approve_partner(owner_id):
    success = owner_service.update_owner_status(owner_id, "Approved")
    if success:
        owner = owner_service.get_owner_by_id(owner_id)
        # Notify via email
        email_service._dispatch(
            subject="PlayNest Partner Profile Approved! 🎉",
            recipient=owner.email,
            html=f"<h3>Congratulations {owner.name}!</h3><p>Your partner account for <strong>{owner.turf_name}</strong> has been approved. You can now log in and add your turf details and manage slots.</p>",
            kind="Partner Approved"
        )
        flash(f"Partner {owner_id} approved successfully.", "success")
    else:
        flash(f"Failed to approve partner {owner_id}.", "danger")
    return redirect(url_for("admin.partners"))


@admin_bp.route("/partners/<owner_id>/reject", methods=["POST"])
@admin_required
def reject_partner(owner_id):
    success = owner_service.update_owner_status(owner_id, "Rejected")
    if success:
        owner = owner_service.get_owner_by_id(owner_id)
        email_service._dispatch(
            subject="PlayNest Partner Profile Update",
            recipient=owner.email,
            html=f"<h3>Hello {owner.name},</h3><p>We regret to inform you that your partner application for <strong>{owner.turf_name}</strong> was rejected. Please verify your document uploads and resubmit.</p>",
            kind="Partner Rejected"
        )
        flash(f"Partner {owner_id} rejected.", "info")
    else:
        flash(f"Failed to update status for partner {owner_id}.", "danger")
    return redirect(url_for("admin.partners"))


@admin_bp.route("/reports")
@admin_required
def reports():
    all_bookings = booking_service.get_all_bookings()
    by_city = {}
    for t in TURFS:
        by_city.setdefault(t.city, {"turfs": 0, "bookings": 0, "revenue": 0})
        by_city[t.city]["turfs"] += 1
    for b in all_bookings:
        city = b.turf_city
        by_city.setdefault(city, {"turfs": 0, "bookings": 0, "revenue": 0})
        by_city[city]["bookings"] += 1
        if b.status in ("Confirmed", "Completed"):
            by_city[city]["revenue"] += b.price
    return render_template("admin/reports.html", by_city=by_city, sports=SPORTS)


@admin_bp.route("/complaints")
@admin_required
def complaints():
    from services import complaint_service, owner_service
    all_complaints = complaint_service.get_all_complaints()
    owner_warnings = {owner.id: owner.warnings_count for owner in owner_service.get_all_owners()}
    return render_template("admin/complaints.html", complaints=all_complaints, owner_warnings=owner_warnings)


@admin_bp.route("/partners/<owner_id>/remove", methods=["POST"])
@admin_required
def remove_partner(owner_id):
    owner = owner_service.get_owner_by_id(owner_id)
    if owner:
        if owner.warnings_count < 3:
            flash(f"Partner {owner.name} is not eligible for removal yet. They must have at least 3 warnings (Current warnings: {owner.warnings_count}/3).", "danger")
            return redirect(request.referrer or url_for("admin.partners"))
        name = owner.name
        success = owner_service.delete_owner(owner_id)
        if success:
            flash(f"Partner {name} (ID: {owner_id}) and all associated turfs have been removed successfully.", "success")
        else:
            flash("Failed to remove partner.", "danger")
    else:
        flash("Partner not found.", "danger")
    return redirect(request.referrer or url_for("admin.partners"))


@admin_bp.route("/partners/<owner_id>/warn", methods=["POST"])
@admin_required
def warn_partner(owner_id):
    owner = owner_service.get_owner_by_id(owner_id)
    if owner:
        new_count = owner_service.warn_owner(owner_id)
        
        # Dispatch Email Notice
        from services import email_service
        email_service._dispatch(
            subject=f"[WARNING {new_count}/3] PlayNest Partner Compliance Notice",
            recipient=owner.email,
            html=f"""<h3>Dear {owner.name},</h3>
            <p>This is a formal warning (<strong>Warning {new_count} of 3</strong>) regarding player complaints registered against your turf, <strong>{owner.turf_name}</strong>.</p>
            <p>Please resolve outstanding complaints immediately. Following 3 warnings, your partner profile and all associated turfs will be eligible for removal from the platform.</p>
            <br>
            <p>Best regards,<br>PlayNest Compliance Team</p>""",
            kind=f"Warning {new_count}"
        )
        
        flash(f"Warning {new_count}/3 sent to {owner.name}.", "warning")
    else:
        flash("Partner not found.", "danger")
    return redirect(request.referrer or url_for("admin.complaints"))


@admin_bp.route("/flagged-customers")
@admin_required
def flagged_customers():
    from services.restriction_service import get_flagged_customers
    flagged = get_flagged_customers()
    return render_template("admin/flagged_customers.html", flagged=flagged)


@admin_bp.route("/flagged-customers/<user_id>/action", methods=["POST"])
@admin_required
def flagged_customer_action(user_id):
    user = user_service.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.flagged_customers"))
        
    action = request.form.get("action")
    
    from datetime import datetime, timedelta
    
    if action == "warning":
        user.warnings_count = getattr(user, "warnings_count", 0) + 1
        # Send warning email
        email_service._dispatch(
            subject=f"[WARNING #{user.warnings_count}] PlayNest User Conduct Notice",
            recipient=user.email,
            html=f"""<h3>Dear {user.name},</h3>
            <p>We have received reports from turf owners regarding your conduct (Warning {user.warnings_count}).</p>
            <p>Please follow turf guidelines. Repeat offenses will result in temporary suspension or permanent ban from all turfs on PlayNest.</p>
            <br>
            <p>Best regards,<br>PlayNest Safety Team</p>""",
            kind=f"User Warning {user.warnings_count}"
        )
        flash(f"Issued Warning #{user.warnings_count} to {user.name}.", "warning")
        
    elif action == "suspend":
        days = int(request.form.get("suspension_days", 7))
        user.status = "suspended"
        user.suspension_until = datetime.now() + timedelta(days=days)
        # Send suspension email
        email_service._dispatch(
            subject=f"PlayNest Account Temporarily Suspended",
            recipient=user.email,
            html=f"""<h3>Dear {user.name},</h3>
            <p>Your PlayNest account has been temporarily suspended for <strong>{days} days</strong> due to reports of inappropriate behavior.</p>
            <p>You will not be able to book any turfs until {user.suspension_until.strftime('%Y-%m-%d %H:%M')}.</p>
            <br>
            <p>Best regards,<br>PlayNest Safety Team</p>""",
            kind="User Account Suspended"
        )
        flash(f"Suspended {user.name} for {days} days.", "danger")
        
    elif action == "ban":
        user.status = "banned"
        user.suspension_until = None
        # Send ban email
        email_service._dispatch(
            subject=f"PlayNest Account Permanently Banned",
            recipient=user.email,
            html=f"""<h3>Dear {user.name},</h3>
            <p>Your PlayNest account has been permanently banned from booking any turfs due to multiple violations of turf policies.</p>
            <br>
            <p>Best regards,<br>PlayNest Safety Team</p>""",
            kind="User Account Banned"
        )
        flash(f"Permanently banned {user.name} from PlayNest.", "danger")
        
    elif action == "restore":
        user.status = "active"
        user.suspension_until = None
        # Send restore email
        email_service._dispatch(
            subject=f"PlayNest Account Restored",
            recipient=user.email,
            html=f"""<h3>Dear {user.name},</h3>
            <p>Your PlayNest account has been restored. You are now permitted to book turfs on the platform.</p>
            <br>
            <p>Best regards,<br>PlayNest Safety Team</p>""",
            kind="User Account Restored"
        )
        flash(f"Restored account status to active for {user.name}.", "success")
        
    if user_service.is_db_ready():
        db.session.commit()
        
    return redirect(url_for("admin.flagged_customers"))


