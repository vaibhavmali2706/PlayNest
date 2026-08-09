"""
PlayNest — Book. Play. Repeat.

Application factory. Blueprints, mail, and template globals are wired
up here; everything else lives in routes/, services/, models/, utils/.
"""

from flask import Flask, render_template, session 
from flask_mail import Mail
from datetime import datetime

from config import Config
from services import email_service
from extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    mail = Mail(app)
    email_service.init_mail(mail)

    # ---- Blueprints ----
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.turfs import turfs_bp
    from routes.booking import booking_bp
    from routes.dashboard import dashboard_bp
    from routes.owner import owner_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(turfs_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(admin_bp)

    # ---- Template globals & filters ----
    from utils.helpers import format_date_pretty, format_time_12h, status_badge_class

    app.jinja_env.filters["pretty_date"] = format_date_pretty
    app.jinja_env.filters["time_12h"] = format_time_12h
    app.jinja_env.filters["status_badge"] = status_badge_class

    @app.context_processor
    def inject_globals():
        from services import user_service, owner_service
        user_id = session.get("user_id")
        owner_id = session.get("owner_id")
        fav_ids = []
        if user_id:
            user = user_service.get_user_by_id(user_id)
            if user:
                fav_ids = user.favourite_turf_ids
        
        owner_warnings = 0
        if owner_id:
            owner = owner_service.get_owner_by_id(owner_id)
            if owner:
                owner_warnings = owner.warnings_count
                
        return {
            "current_year": datetime.now().year,
            "is_logged_in": bool(user_id),
            "current_user_name": session.get("user_name"),
            "user_favourite_ids": fav_ids,
            "is_owner_logged_in": bool(owner_id),
            "current_owner_name": session.get("owner_name"),
            "current_owner_warnings": owner_warnings,
            "is_admin_logged_in": bool(session.get("is_admin")),
        }

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        app.logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
        if app.debug:
            raise e
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
