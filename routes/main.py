from flask import Blueprint, render_template
from services.turf_service import get_featured_turfs, get_sports, get_cities

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    return render_template(
        "landing.html",
        featured_turfs=get_featured_turfs(6),
        sports=get_sports(),
        cities=get_cities(),
    )


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")
