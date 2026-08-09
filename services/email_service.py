"""
Email service.

Sends premium HTML emails via Flask-Mail when MAIL_CONFIGURED is True.
When no SMTP credentials are set (fresh clone, no .env yet), PlayNest
runs in DEV MODE: emails are logged to the console instead of sent, so
the whole OTP → booking → confirmation flow can be demoed with zero
setup. Nothing about the calling code changes either way.
"""

from flask import current_app, render_template
from flask_mail import Message

mail = None  # set by app.py via init_mail()


def init_mail(mail_instance):
    global mail
    mail = mail_instance


def _dispatch(subject: str, recipient: str, html: str, kind: str):
    if current_app.config.get("MAIL_CONFIGURED") and mail is not None:
        try:
            msg = Message(subject=subject, recipients=[recipient], html=html)
            mail.send(msg)
            return
        except Exception as exc:  # pragma: no cover - network dependent
            current_app.logger.warning(f"Email send failed, falling back to console: {exc}")

    # DEV MODE fallback
    current_app.logger.info(
        f"\n{'=' * 60}\n📧  [DEV MODE EMAIL] {kind}\nTo: {recipient}\nSubject: {subject}\n{'=' * 60}\n"
    )


def send_otp_email(email: str, name: str, otp_code: str):
    html = render_template(
        "emails/otp.html",
        name=name,
        otp_code=otp_code,
        valid_minutes=current_app.config["OTP_VALID_MINUTES"],
    )
    _dispatch("Your PlayNest verification code", email, html, "OTP")


def send_welcome_email(email: str, name: str):
    html = render_template("emails/welcome.html", name=name)
    _dispatch("Welcome to PlayNest 🎉", email, html, "Welcome")


def send_booking_confirmation_email(email: str, booking):
    html = render_template("emails/booking_confirmation.html", booking=booking)
    _dispatch(f"Booking Confirmed — {booking.id}", email, html, "Booking Confirmation")


def send_booking_cancellation_email(email: str, booking):
    html = render_template("emails/booking_cancellation.html", booking=booking)
    _dispatch(f"Booking Cancelled — {booking.id}", email, html, "Booking Cancellation")


def send_booking_reminder_email(email: str, booking):
    html = render_template("emails/booking_reminder.html", booking=booking)
    _dispatch(f"Reminder: your game is coming up — {booking.id}", email, html, "Booking Reminder")
