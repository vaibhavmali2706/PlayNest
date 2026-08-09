from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, current_app,
)
from datetime import datetime, timedelta
from extensions import db
from forms import LoginForm, RegistrationForm, OtpForm, ForgotPasswordForm, ResetPasswordForm
from services import otp_service, user_service, email_service
from services.turf_service import get_cities

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("owner_id"):
        flash("You are currently logged in as a turf partner. Please log out first to sign in as a player.", "warning")
        return redirect(url_for("owner.dashboard"))

    if session.get("user_id"):
        return redirect(url_for("dashboard.home"))

    form = LoginForm()
    next_url = request.args.get("next", "")

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = user_service.get_user_by_email(email)

        if user:
            # Check if account is temporarily locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                lock_duration_seconds = int((user.locked_until - datetime.utcnow()).total_seconds())
                lock_minutes = max(1, lock_duration_seconds // 60)
                form.email.errors.append(f"Account is temporarily locked. Please try again after {lock_minutes} minutes.")
                return render_template("auth/login.html", form=form, next_url=next_url)

            if user_service.check_password(form.password.data, user.password_hash):
                # Reset locking counters on successful login
                user.failed_login_attempts = 0
                user.locked_until = None
                if user_service.is_db_ready():
                    db.session.commit()

                if not user.is_verified:
                    # User needs to complete OTP verification
                    session["pending_email"] = user.email
                    session["pending_name"] = user.name
                    session["pending_next"] = next_url
                    
                    otp_code = otp_service.generate_otp(user.email)
                    email_service.send_otp_email(user.email, user.name, otp_code)
                    
                    if current_app.config["DEBUG"] and not current_app.config["MAIL_CONFIGURED"]:
                        flash(f"DEV MODE — no SMTP configured. Your OTP is: {otp_code}", "dev")
                    
                    flash("Please verify your account using the OTP sent to your email.", "warning")
                    return redirect(url_for("auth.verify_otp"))
                
                # Successful Login
                session["user_id"] = user.id
                session["user_name"] = user.name
                
                if form.remember_me.data:
                    session.permanent = True
                else:
                    session.permanent = False
                
                flash(f"Welcome back, {user.name.split()[0]}! 👋", "success")
                return redirect(next_url or url_for("dashboard.home"))
            else:
                # Increment failed attempts
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    form.email.errors.append("Account temporarily locked due to 5 failed login attempts. Try again in 15 minutes.")
                else:
                    remaining = 5 - user.failed_login_attempts
                    form.password.errors.append(f"Invalid password. {remaining} attempts remaining before lock.")
                if user_service.is_db_ready():
                    db.session.commit()
        else:
            form.email.errors.append("Email address not found. Sign up instead?")

    return render_template("auth/login.html", form=form, next_url=next_url)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("owner_id"):
        flash("You are currently logged in as a turf partner. Please log out first to sign up as a player.", "warning")
        return redirect(url_for("owner.dashboard"))

    if session.get("user_id"):
        return redirect(url_for("dashboard.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existing = user_service.get_user_by_email(email)

        if existing:
            form.email.errors.append("This email address is already registered.")
            return render_template("auth/signup.html", form=form, cities=get_cities())

        # Create unverified user
        user = user_service.create_or_update_user(
            name=form.name.data,
            email=email,
            phone=form.phone.data,
            city=form.city.data,
            password=form.password.data
        )

        session["pending_email"] = user.email
        session["pending_name"] = user.name
        session["pending_next"] = url_for("dashboard.home")

        otp_code = otp_service.generate_otp(user.email)
        email_service.send_otp_email(user.email, user.name, otp_code)

        if current_app.config["DEBUG"] and (not current_app.config["MAIL_CONFIGURED"] or email.endswith("@playnest.app")):
            flash(f"DEV MODE — OTP is: {otp_code}", "dev")

        flash("Registration successful. Please enter the OTP sent to your email.", "info")
        return redirect(url_for("auth.verify_otp"))

    return render_template("auth/signup.html", form=form, cities=get_cities())


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("auth.login"))

    user = user_service.get_user_by_email(email)
    if user and user.is_verified:
        session["user_id"] = user.id
        session["user_name"] = user.name
        next_url = session.get("pending_next") or url_for("dashboard.home")
        for k in ("pending_email", "pending_name", "pending_next"):
            session.pop(k, None)
        return redirect(next_url)

    form = OtpForm()

    if form.validate_on_submit():
        result = otp_service.verify_otp(email, form.otp_code.data, purpose='EMAIL_VERIFICATION')

        if result["success"]:
            user = user_service.get_user_by_email(email)
            if user:
                user.is_verified = True
                if user_service.is_db_ready():
                    db.session.commit()
                session["user_id"] = user.id
                session["user_name"] = user.name
                
                next_url = session.get("pending_next") or url_for("dashboard.home")
                
                # Clear pending keys
                for k in ("pending_email", "pending_name", "pending_next"):
                    session.pop(k, None)

                email_service.send_welcome_email(user.email, user.name)
                flash(f"Welcome to PlayNest, {user.name.split()[0]}! 🎉 Account activated.", "success")
                return redirect(next_url)

        reason_messages = {
            "expired": "Your OTP has expired. Please request a new one.",
            "too_many_attempts": "Too many incorrect attempts. Please request a new OTP.",
            "invalid": "That code doesn't look right. Please try again.",
        }
        flash(reason_messages.get(result["reason"], "Verification failed."), "danger")

    can_resend = otp_service.can_resend(email)
    resend_wait = otp_service.seconds_until_resend(email)

    return render_template(
        "auth/verify_otp.html", form=form, email=email,
        can_resend=can_resend, resend_wait=resend_wait,
        attempts_remaining=otp_service.attempts_remaining(email, purpose='EMAIL_VERIFICATION'),
        valid_minutes=current_app.config["OTP_VALID_MINUTES"],
    )


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("auth.login"))

    if not otp_service.can_resend(email):
        flash("Please wait before requesting another OTP.", "warning")
        return redirect(url_for("auth.verify_otp"))

    otp_code = otp_service.generate_otp(email, purpose='EMAIL_VERIFICATION')
    email_service.send_otp_email(email, session.get("pending_name") or "Player", otp_code)

    if current_app.config["DEBUG"] and not current_app.config["MAIL_CONFIGURED"]:
        flash(f"DEV MODE — new OTP is: {otp_code}", "dev")
    else:
        flash("A new OTP has been sent to your email.", "success")

    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if session.get("user_id"):
        return redirect(url_for("dashboard.home"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = user_service.get_user_by_email(email)

        if user:
            session["reset_email"] = user.email
            otp_code = otp_service.generate_otp(user.email, purpose='PASSWORD_RESET')
            
            # Send OTP or Reset Link - We send an OTP for secure reset
            email_service.send_otp_email(user.email, user.name, otp_code)
            
            if current_app.config["DEBUG"] and (not current_app.config["MAIL_CONFIGURED"] or email.endswith("@playnest.app")):
                flash(f"DEV MODE — Reset OTP is: {otp_code}", "dev")
                
            flash("An OTP has been sent to your email to reset your password.", "info")
            return redirect(url_for("auth.reset_password"))
        else:
            form.email.errors.append("No account associated with this email address.")

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Verify the reset OTP
        result = otp_service.verify_otp(email, form.otp_code.data, purpose='PASSWORD_RESET')
        
        if result["success"]:
            user = user_service.get_user_by_email(email)
            if user:
                user.password_hash = user_service.hash_password(form.password.data)
                if user_service.is_db_ready():
                    db.session.commit()
                session.pop("reset_email", None)
                flash("Your password has been reset successfully. Please login with your new password.", "success")
                return redirect(url_for("auth.login"))
        else:
            reason_messages = {
                "expired": "Your OTP has expired. Please request another reset code.",
                "too_many_attempts": "Too many attempts. Please request another reset code.",
                "invalid": "Invalid OTP code. Please try again.",
            }
            form.otp_code.errors.append(reason_messages.get(result["reason"], "Verification failed."))

    return render_template("auth/reset_password.html", form=form, email=email)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out. See you on the turf!", "info")
    return redirect(url_for("main.landing"))
