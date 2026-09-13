from __future__ import annotations


def hours_from_credit(credit: float | None, cup_per_hour: float) -> float:
    if not credit or cup_per_hour is None or cup_per_hour <= 0:
        return 0.0
    return credit / cup_per_hour


def format_hours(hours: float) -> str:
    hours = max(0.0, hours)
    total_minutes = int(hours * 60)
    minutes = total_minutes % 60
    total_hours = total_minutes // 60
    days, hours_part = divmod(total_hours, 24)
    parts = []
    if days:
        parts.append(f"{days} d")
    if hours_part:
        parts.append(f"{hours_part} h")
    if minutes or not parts:
        parts.append(f"{minutes} m")
    return " ".join(parts)