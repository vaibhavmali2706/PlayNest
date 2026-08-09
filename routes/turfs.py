from flask import Blueprint, render_template, request, jsonify, session

from services import turf_service, user_service
from utils.helpers import next_n_days, today_str

turfs_bp = Blueprint("turfs", __name__)


@turfs_bp.route("/turfs")
def listing():
    query = request.args.get("q", "").strip()
    sport = request.args.get("sport", "")
    city = request.args.get("city", "")
    facilities = request.args.getlist("facility")
    indoor_outdoor = request.args.get("type", "")
    sort = request.args.get("sort", "recommended")

    results = turf_service.search_turfs(
        query=query, sport=sport, city=city, facilities=facilities,
        indoor_outdoor=indoor_outdoor, sort=sort,
    )

    return render_template(
        "turfs/listing.html",
        turfs=results,
        sports=turf_service.get_sports(),
        cities=turf_service.get_cities(),
        all_facilities=turf_service.get_facilities(),
        selected={
            "q": query, "sport": sport, "city": city,
            "facilities": facilities, "type": indoor_outdoor, "sort": sort,
        },
    )


@turfs_bp.route("/turfs/<turf_id>")
def detail(turf_id):
    turf = turf_service.get_turf_by_id(turf_id)
    if not turf:
        from flask import abort
        abort(404)

    user_id = session.get("user_id")
    fav = user_service.is_favourite(user_id, turf_id) if user_id else False

    return render_template(
        "turfs/detail.html",
        turf=turf,
        is_favourite=fav,
        dates=next_n_days(7),
        today=today_str(),
    )


@turfs_bp.route("/turfs/<turf_id>/favourite", methods=["POST"])
def toggle_favourite(turf_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "login_required"}), 401

    is_fav = user_service.toggle_favourite(user_id, turf_id)
    return jsonify({"success": True, "is_favourite": is_fav})


@turfs_bp.route("/turfs/<turf_id>/review", methods=["POST"])
def add_review(turf_id):
    from flask import redirect, url_for, flash
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to leave a review.", "danger")
        return redirect(url_for("auth.login", next=url_for("turfs.detail", turf_id=turf_id)))

    author = session.get("user_name", "Player")
    rating = request.form.get("rating")
    comment = request.form.get("comment", "").strip()

    if not rating:
        flash("Please provide a rating.", "danger")
        return redirect(url_for("turfs.detail", turf_id=turf_id))

    try:
        rating_val = float(rating)
        if not (1 <= rating_val <= 5):
            raise ValueError()
    except ValueError:
        flash("Invalid rating. Must be between 1 and 5.", "danger")
        return redirect(url_for("turfs.detail", turf_id=turf_id))

    success = turf_service.add_review(turf_id, author, rating_val, comment)
    if success:
        flash("Thank you for your review!", "success")
    else:
        flash("Turf not found.", "danger")

    return redirect(url_for("turfs.detail", turf_id=turf_id))


@turfs_bp.route("/turfs/<turf_id>/complaint", methods=["POST"])
def add_complaint(turf_id):
    from flask import redirect, url_for, flash
    from services import complaint_service
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to file a complaint.", "danger")
        return redirect(url_for("auth.login", next=url_for("turfs.detail", turf_id=turf_id)))

    user_name = session.get("user_name", "Player")
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not description:
        flash("Please provide both a title and description for your complaint.", "danger")
        return redirect(url_for("turfs.detail", turf_id=turf_id))

    complaint = complaint_service.create_complaint(user_id, user_name, turf_id, title, description)
    if complaint:
        flash("Your complaint has been submitted and will be reviewed by the owner and administrators.", "success")
    else:
        flash("Turf not found.", "danger")

    return redirect(url_for("turfs.detail", turf_id=turf_id))


