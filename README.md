# PlayNest 🟢

**Book. Play. Repeat.**

An online sports turf booking platform — discover turfs, check live
availability, book a slot, verify by email OTP, and get a downloadable
digital PlayPass. Built with Flask, no payment gateway, database-ready
mock data layer.

## Quick start

```bash
cd PlayNest
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # optional — see "Email" below
python3 app.py
```

Visit **http://localhost:5000**.

## Email — dev mode by default

PlayNest needs no SMTP setup to run. If `MAIL_USERNAME` /
`MAIL_PASSWORD` aren't set in `.env`, every OTP and transactional email
is logged to the console instead of sent, **and the OTP is also shown
in a flash banner in the UI** so you can complete the login flow
end-to-end with zero configuration. Fill in real SMTP credentials in
`.env` to send real email — no code changes required.

## Demo logins

- **Player**: any email → OTP is shown on screen in dev mode.
- **Owner portal** (`/owner/login`): pick any seeded owner from the dropdown — this is a demo account switcher, since the platform has no owner database yet.
- **Admin panel** (`/admin/login`): passcode `270607`.

## Architecture

```
app.py                 Application factory, blueprint + error registration
config.py               Environment-driven configuration

routes/                 Blueprints (thin — validation + orchestration only)
  main.py                 Landing, about, contact
  auth.py                 Email OTP login/registration
  turfs.py                Search, filters, turf detail, favourites
  booking.py               Slot picker, booking creation, PlayPass, cancellation
  dashboard.py              Player dashboard (bookings, favourites, profile)
  owner.py                  Owner portal (manage turfs/bookings, analytics)
  admin.py                   Admin panel (users, turfs, bookings, reports)

services/                Business logic + the mock "database"
  mock_data.py              Seed data for turfs/sports/cities (swap for real DB)
  turf_service.py            Turf search/filter/detail
  user_service.py             User repository (in-memory, keyed by email)
  booking_service.py           Slot availability engine + booking lifecycle
  otp_service.py                OTP generation/validation/throttling
  email_service.py               Flask-Mail wrapper with dev-mode fallback

models/                  Plain dataclasses (User, Turf, Booking) — ORM-ready
utils/                   Decorators, formatting helpers, PlayPass PDF generator
templates/                Jinja2 templates, organised to mirror routes/
static/                   CSS design system + vanilla JS (no build step)
```

### Why mock data instead of a database?

Every service function (`get_turf_by_id`, `create_booking`,
`get_bookings_by_user`, ...) is written the way a repository-backed
version would be. Swapping `services/mock_data.py`'s in-memory lists
for real SQLAlchemy models — and pointing `config.py`'s
`DATABASE_READY` flag at a real connection — is the only work needed
to go live. Routes and templates don't need to change.

### Design system

Dark, premium, sports-tech palette (charcoal/navy base, emerald +
neon-green + electric-blue accents). The PlayPass ticket — with its
dashed perforation and rounded notches — is the signature visual
motif, echoed in section dividers and the booking summary panel
throughout the product.

## What's intentionally stubbed

- **Payments**: out of scope by design — all bookings are instantly "Confirmed".
- **Real database**: mock repositories reset on server restart (in-memory).
- **Owner/turf editing, image upload**: UI is scaffolded, actions are disabled with a tooltip pending DB integration.
- **Push/browser notifications**: dashboard shows an in-app notification feed derived from booking activity; browser push is not wired up.
