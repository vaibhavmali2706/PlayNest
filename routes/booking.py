from flask import (
    Blueprint, render_template, request, jsonify, session,
    redirect, url_for, flash, current_app, Response, abort,
)

from services import turf_service, booking_service, email_service, user_service
from utils.decorators import login_required
from utils.helpers import next_n_days, today_str
from utils.playpass_pdf import build_playpass_pdf

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/book/<turf_id>")
@login_required
def new_booking(turf_id):
    turf = turf_service.get_turf_by_id(turf_id)
    if not turf:
        abort(404)

    # Customer Restriction Check
    from services.restriction_service import is_customer_restricted
    if is_customer_restricted(turf.owner_id, session["user_id"]):
        flash("This turf is currently unavailable for booking from your account. If you believe this is a mistake, please contact the turf owner.", "danger")
        return redirect(url_for("turfs.detail", turf_id=turf_id))

    preselect_date = request.args.get("date", today_str())
    return render_template(
        "booking/book.html",
        turf=turf,
        dates=next_n_days(7),
        preselect_date=preselect_date,
    )


@booking_bp.route("/book/<turf_id>/slots")
@login_required
def slots(turf_id):
    turf = turf_service.get_turf_by_id(turf_id)
    if not turf:
        abort(404)

    from services.restriction_service import is_customer_restricted
    if is_customer_restricted(turf.owner_id, session["user_id"]):
        return jsonify({
            "slots": [],
            "restricted": True,
            "message": "This turf is currently unavailable for booking from your account. If you believe this is a mistake, please contact the turf owner."
        })

    date = request.args.get("date", today_str())
    return jsonify({"slots": booking_service.get_available_slots(turf_id, date)})


@booking_bp.route("/book/<turf_id>/confirm", methods=["POST"])
@login_required
def confirm(turf_id):
    turf = turf_service.get_turf_by_id(turf_id)
    if not turf:
        abort(404)

    # Customer Restriction Check
    from services.restriction_service import is_customer_restricted
    if is_customer_restricted(turf.owner_id, session["user_id"]):
        flash("This turf is currently unavailable for booking from your account. If you believe this is a mistake, please contact the turf owner.", "danger")
        return redirect(url_for("turfs.detail", turf_id=turf_id))

    date = request.form.get("date")
    start_time = request.form.get("start_time")
    sport = request.form.get("sport")
    duration = float(request.form.get("duration", 1))
    player_name = request.form.get("player_name") or session.get("user_name", "Player")

    if not (date and start_time and sport):
        flash("Please choose a sport, date and slot before confirming.", "danger")
        return redirect(url_for("booking.new_booking", turf_id=turf_id))

    # Re-validate the slot is still open (protects against race conditions)
    day_slots = {s["start"]: s for s in booking_service.get_available_slots(turf_id, date)}
    chosen = day_slots.get(start_time)
    if not chosen or not chosen["available"]:
        flash("Sorry, that slot was just taken. Please pick another.", "warning")
        return redirect(url_for("booking.new_booking", turf_id=turf_id, date=date))

    end_hour = int(start_time.split(":")[0]) + int(duration)
    end_time = f"{end_hour:02d}:00"

    booking = booking_service.create_booking(
        user_id=session["user_id"],
        player_name=player_name,
        turf_id=turf_id,
        sport=sport,
        date=date,
        start_time=start_time,
        end_time=end_time,
        duration_hours=duration,
        )

    user = user_service.get_user_by_id(session["user_id"])
    if user:
        email_service.send_booking_confirmation_email(user.email, booking)

    return redirect(url_for("booking.success", booking_id=booking.id))


@booking_bp.route("/booking/<booking_id>/success")
@login_required
def success(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    if not booking or str(booking.user_id) != str(session["user_id"]):
        abort(404)
    return render_template("booking/success.html", booking=booking, turf_id=booking.turf_id)


@booking_bp.route("/booking/<booking_id>/playpass")
@login_required
def playpass(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    if not booking or str(booking.user_id) != str(session["user_id"]):
        abort(404)
    return render_template("booking/playpass.html", booking=booking)


@booking_bp.route("/booking/<booking_id>/playpass/download")
@login_required
def playpass_download(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    if not booking or str(booking.user_id) != str(session["user_id"]):
        abort(404)

    pdf_bytes = build_playpass_pdf(booking)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PlayPass-{booking.id}.pdf"},
    )


@booking_bp.route("/booking/<booking_id>/cancel", methods=["POST"])
@login_required
def cancel(booking_id):
    booking = booking_service.get_booking_by_id(booking_id)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.args.get("ajax") == "true"
    
    if not booking or str(booking.user_id) != str(session["user_id"]):
        if is_ajax:
            return jsonify({"success": False, "reason": "not_found"}), 404
        abort(404)

    # Simulating a server error for testing the custom retry/close banner requirement
    if request.args.get("simulate_error") == "true":
        return jsonify({"success": False, "message": "Simulated DB Lockout Error"}), 500

    result = booking_service.cancel_booking(
        booking_id, current_app.config["CANCELLATION_WINDOW_HOURS"]
    )

    if result["success"]:
        user = user_service.get_user_by_id(session["user_id"])
        if user:
            email_service.send_booking_cancellation_email(user.email, booking)
        
        if is_ajax:
            return jsonify({"success": True})
        flash(f"Booking {booking_id} has been cancelled.", "info")
    else:
        if is_ajax:
            return jsonify({
                "success": False, 
                "reason": result["reason"],
                "message": "Booking Cancellation Unavailable"
            })
        flash(
            f"This booking can no longer be cancelled — it starts in under "
            f"{current_app.config['CANCELLATION_WINDOW_HOURS']} hours.",
            "danger",
        )

    return redirect(url_for("dashboard.bookings"))

