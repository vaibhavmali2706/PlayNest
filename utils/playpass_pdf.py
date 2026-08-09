"""
Generates the PlayPass — a premium digital ticket-stub PDF — for a
confirmed booking. Kept separate from routes/ so the PDF layout can
evolve (QR code, barcode, etc.) without touching booking logic.
"""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

CHARCOAL = HexColor("#0B0F0E")
NAVY = HexColor("#101B2D")
EMERALD = HexColor("#10B981")
NEON = HexColor("#39FF88")
GRAY = HexColor("#8892A0")
LIGHT = HexColor("#E7EAF0")


def build_playpass_pdf(booking) -> bytes:
    buf = io.BytesIO()
    width, height = 105 * mm, 220 * mm  # tall ticket format
    c = canvas.Canvas(buf, pagesize=(width, height))

    # Background
    c.setFillColor(CHARCOAL)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Top brand band
    c.setFillColor(NAVY)
    c.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)

    c.setFillColor(NEON)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 20 * mm, "PLAYNEST")

    c.setFillColor(LIGHT)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, height - 27 * mm, "Book. Play. Repeat.")

    c.setFillColor(EMERALD)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, height - 38 * mm, "P L A Y P A S S")

    # Perforation line
    y_perf = height - 47 * mm
    c.setStrokeColor(HexColor("#33404F"))
    c.setDash(3, 3)
    c.line(6 * mm, y_perf, width - 6 * mm, y_perf)
    c.setDash()

    # Body content
    y = height - 60 * mm
    left = 10 * mm
    line_gap = 12 * mm

    def field(label, value):
        nonlocal y
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(left, y, label.upper())
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        lines = simpleSplit(str(value), "Helvetica-Bold", 12, width - 2 * left)
        yy = y - 5.5 * mm
        for ln in lines:
            c.drawString(left, yy, ln)
            yy -= 5.5 * mm
        y = yy - 2 * mm

    field("Booking ID", booking.id)
    field("Player Name", booking.player_name)
    field("Sport", booking.sport)
    field("Turf", f"{booking.turf_name}")
    field("Location", f"{booking.turf_area}, {booking.turf_city}")
    field("Date", booking.date)
    field("Time", f"{booking.start_time} - {booking.end_time}")

    # Status chip
    c.setFillColor(EMERALD if booking.status == "Confirmed" else GRAY)
    c.roundRect(left, y - 2 * mm, 40 * mm, 8 * mm, 4, fill=1, stroke=0)
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(left + 20 * mm, y + 1.3 * mm, booking.status.upper())
    y -= 16 * mm

    # Perforation line before footer
    c.setStrokeColor(HexColor("#33404F"))
    c.setDash(3, 3)
    c.line(6 * mm, y, width - 6 * mm, y)
    c.setDash()
    y -= 8 * mm

    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7)
    terms = (
        "Please arrive 10 minutes before your slot. This pass is valid only for "
        "the sport, date and time printed above. Cancellations are permitted up "
        "to 3 hours before the slot start time via the PlayNest dashboard."
    )
    for ln in simpleSplit(terms, "Helvetica", 7, width - 2 * left):
        c.drawString(left, y, ln)
        y -= 4 * mm

    y -= 4 * mm
    c.setFillColor(NEON)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(left, y, "Support: support@playnest.app  |  +91 90000 00000")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
