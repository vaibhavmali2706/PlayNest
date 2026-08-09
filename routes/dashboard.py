from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify

from services import booking_service, user_service, turf_service
from services.mock_data import TURFS
from utils.decorators import login_required
from utils.helpers import today_str, calculate_distance

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def home():
    user = user_service.get_user_by_id(session["user_id"])
    bookings = booking_service.get_bookings_by_user(user.id)
    upcoming = [b for b in bookings if b.status in ("Pending", "Confirmed")][:3]

    favourite_turfs = [
        turf_service.get_turf_by_id(tid) for tid in user.favourite_turf_ids
    ]
    favourite_turfs = [t for t in favourite_turfs if t][:4]

    stats = {
        "total_bookings": len(bookings),
        "upcoming": len([b for b in bookings if b.status in ("Pending", "Confirmed")]),
        "completed": len([b for b in bookings if b.status == "Completed"]),
        "favourites": len(user.favourite_turf_ids),
    }

    # Location-based sorting & distance calculation
    user_lat = session.get("user_lat")
    user_lng = session.get("user_lng")
    location_allowed = session.get("location_permission") == "allowed"

    all_turfs = list(TURFS)
    distances = {}

    if location_allowed and user_lat is not None and user_lng is not None:
        for t in all_turfs:
            dist = calculate_distance(user_lat, user_lng, t.lat, t.lng)
            distances[t.id] = f"{dist} km"
            t.temp_dist = dist  # Store temporarily for sorting
        
        # Sort Nearby Turfs by distance
        nearby_turfs = sorted(all_turfs, key=lambda t: getattr(t, 'temp_dist', 99999))
    else:
        # Fallback: Sort by matching city, then others
        nearby_turfs = sorted(
            all_turfs,
            key=lambda t: (0 if t.city.lower() == user.city.lower() else 1, t.name)
        )
        for t in all_turfs:
            distances[t.id] = t.area  # display area as location fallback

    # Sections setup
    from datetime import datetime
    curr_hour = datetime.now().hour
    if curr_hour < 12:
        greeting = "Good Morning"
    elif curr_hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    featured_turfs = sorted(all_turfs, key=lambda t: t.rating, reverse=True)[:4]
    trending_turfs = sorted(all_turfs, key=lambda t: t.review_count, reverse=True)[:4]
    highest_rated = sorted(all_turfs, key=lambda t: t.rating, reverse=True)[:4]
    recently_added = all_turfs[-4:]  # Last 4 turfs
    recommendations = [t for t in all_turfs if t.rating >= 4.7][:4]
    sports = turf_service.get_sports()

    return render_template(
        "dashboard/home.html",
        user=user,
        greeting=greeting,

        upcoming=upcoming,
        stats=stats,
        favourite_turfs=favourite_turfs,
        today=today_str(),
        nearby_turfs=nearby_turfs[:6],
        featured_turfs=featured_turfs,
        trending_turfs=trending_turfs,
        highest_rated=highest_rated,
        recently_added=recently_added,
        recommendations=recommendations,
        sports=sports,
        distances=distances,
        location_permission=session.get("location_permission")
    )


@dashboard_bp.route("/dashboard/update-location", methods=["POST"])
@login_required
def update_location():
    data = request.get_json() or {}
    permission = data.get("permission")
    lat = data.get("lat")
    lng = data.get("lng")

    if permission == "allowed" and lat is not None and lng is not None:
        session["location_permission"] = "allowed"
        session["user_lat"] = float(lat)
        session["user_lng"] = float(lng)
        return jsonify({"success": True})
    else:
        session["location_permission"] = "denied"
        session.pop("user_lat", None)
        session.pop("user_lng", None)
        return jsonify({"success": True})


@dashboard_bp.route("/dashboard/bookings")
@login_required
def bookings():
    user = user_service.get_user_by_id(session["user_id"])
    all_bookings = booking_service.get_bookings_by_user(user.id)
    return render_template("dashboard/bookings.html", bookings=all_bookings)


@dashboard_bp.route("/dashboard/favourites")
@login_required
def favourites():
    user = user_service.get_user_by_id(session["user_id"])
    favourite_turfs = [
        turf_service.get_turf_by_id(tid) for tid in user.favourite_turf_ids
    ]
    favourite_turfs = [t for t in favourite_turfs if t]
    return render_template("dashboard/favourites.html", turfs=favourite_turfs)


@dashboard_bp.route("/dashboard/profile")
@login_required
def profile():
    user = user_service.get_user_by_id(session["user_id"])
    return render_template("dashboard/profile.html", user=user)


@dashboard_bp.route("/dashboard/notifications")
@login_required
def notifications():
    user = user_service.get_user_by_id(session["user_id"])
    bookings = booking_service.get_bookings_by_user(user.id)
    # Derive simple notification feed from booking activity (mock)
    feed = []
    for b in bookings[:8]:
        feed.append({
            "title": f"Booking {b.status.lower()}",
            "message": f"{b.turf_name} · {b.sport} · {b.date} at {b.start_time}",
            "status": b.status,
            "id": b.id,
        })
    return render_template("dashboard/notifications.html", feed=feed)
