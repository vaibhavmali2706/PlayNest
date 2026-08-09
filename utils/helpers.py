from datetime import datetime, timedelta


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def next_n_days(n: int = 7):
    base = datetime.now().date()
    return [(base + timedelta(days=i)) for i in range(n)]


def format_date_pretty(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a, %d %b %Y")


def format_time_12h(time_str: str) -> str:
    dt = datetime.strptime(time_str, "%H:%M")
    return dt.strftime("%I:%M %p").lstrip("0")


def status_badge_class(status: str) -> str:
    return {
        "Pending": "badge-pending",
        "Confirmed": "badge-confirmed",
        "Completed": "badge-completed",
        "Cancelled": "badge-cancelled",
        "Expired": "badge-expired",
    }.get(status, "badge-pending")


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return round(c * r, 1)

