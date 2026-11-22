"""Parser for Fuelio's sectioned CSV export."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _parse_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _sections(path: str) -> dict[str, list[list[str]]]:
    """Read Fuelio CSV sections, each introduced by ## SectionName."""
    sections: dict[str, list[list[str]]] = {}
    current: str | None = None
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if not row:
                continue
            first = row[0].strip()
            if first.startswith("## "):
                current = first[3:].strip()
                sections[current] = []
            elif current:
                sections[current].append(row)
    return sections


def _records(section: list[list[str]]) -> list[dict[str, str]]:
    if len(section) < 2:
        return []
    headers = section[0]
    return [
        {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
        for row in section[1:]
        if any(str(cell).strip() for cell in row)
    ]


def parse_fuelio_csv(path: str) -> dict[str, Any]:
    """Parse Fuelio's CSV export into normalized vehicle, refuel and cost data."""
    sections = _sections(path)
    vehicle_rows = _records(sections.get("Vehicle", []))
    if not vehicle_rows:
        raise ValueError("Nie znaleziono sekcji ## Vehicle lub danych samochodu.")
    vehicle = vehicle_rows[0]

    logs: list[dict[str, Any]] = []
    for row in _records(sections.get("Log", [])):
        dt = _parse_date(row.get("Data", ""))
        if dt is None:
            continue
        logs.append({
            "date": dt,
            "odometer": _to_float(row.get("Odo (km)")),
            "fuel_liters": _to_float(row.get("Fuel (litres)")),
            "full": str(row.get("Full", "0")).strip() == "1",
            "cost": _to_float(row.get("Price (optional)")),
            "consumption": _to_float(row.get("l/100km (optional)")),
            "station": row.get("City (optional)", "").strip(),
            "unique_id": row.get("UniqueId", "").strip(),
        })
    logs.sort(key=lambda item: item["date"], reverse=True)
    if not logs:
        raise ValueError("Sekcja ## Log nie zawiera poprawnych wpisów tankowań.")

    category_names = {
        _to_int(row.get("CostTypeID")): row.get("Name", "Inne").strip() or "Inne"
        for row in _records(sections.get("CostCategories", []))
    }
    costs: list[dict[str, Any]] = []
    for row in _records(sections.get("Costs", [])):
        dt = _parse_date(row.get("Date", ""))
        if dt is None:
            continue
        costs.append({
            "title": row.get("CostTitle", "Wydatek").strip() or "Wydatek",
            "date": dt,
            "odometer": _to_float(row.get("Odo")),
            "category": category_names.get(_to_int(row.get("CostTypeID")), "Inne"),
            "cost": _to_float(row.get("Cost")),
            "remind_odometer": _to_float(row.get("RemindOdo")),
            "remind_date": _parse_date(row.get("RemindDate", "")),
            "repeat_odometer": _to_float(row.get("RepeatOdo")),
            "repeat_months": _to_int(row.get("RepeatMonths")),
        })
    costs.sort(key=lambda item: item["date"], reverse=True)

    now = datetime.now()
    current_month = [x for x in logs if x["date"].year == now.year and x["date"].month == now.month]
    current_year = [x for x in logs if x["date"].year == now.year]
    valid_consumption = [x["consumption"] for x in logs if x["consumption"] > 0]
    valid_costs = [x for x in costs if x["cost"] > 0]

    latest = logs[0]
    latest_cost = costs[0] if costs else None
    latest_calculated_consumption = next(
        (x["consumption"] for x in logs if x["consumption"] > 0), None
    )
    current_odometer = latest["odometer"]

    # Mileage and calendar reminders are independent: a date reminder is valid
    # even when Fuelio exports RemindOdo as 0.
    mileage_reminders = [
        x for x in costs
        if x["remind_odometer"] > current_odometer and x["title"]
    ]
    mileage_reminders.sort(key=lambda x: x["remind_odometer"])

    date_reminders = [
        x for x in costs
        if x["remind_date"] is not None and x["remind_date"] > now and x["title"]
    ]
    date_reminders.sort(key=lambda x: x["remind_date"])

    return {
        "vehicle_name": vehicle.get("Name", "Fuelio"),
        "make": vehicle.get("Make", ""),
        "model": vehicle.get("Model", ""),
        "year": _to_int(vehicle.get("Year")),
        "odometer": current_odometer,
        "logs": logs,
        "costs": costs,
        "latest": latest,
        "latest_cost": latest_cost,
        "latest_calculated_consumption": latest_calculated_consumption,
        "average_consumption": (sum(valid_consumption) / len(valid_consumption)) if valid_consumption else None,
        "fuel_cost_month": sum(x["cost"] for x in current_month),
        "fuel_cost_year": sum(x["cost"] for x in current_year),
        "fuel_liters_month": sum(x["fuel_liters"] for x in current_month),
        "fuel_liters_year": sum(x["fuel_liters"] for x in current_year),
        "maintenance_cost_total": sum(x["cost"] for x in valid_costs),
        "maintenance_cost_year": sum(x["cost"] for x in valid_costs if x["date"].year == now.year),
        "next_reminder": mileage_reminders[0] if mileage_reminders else None,
        "next_date_reminder": date_reminders[0] if date_reminders else None,
        "refuel_count": len(logs),
        "cost_count": len(costs),
        "last_updated": datetime.fromtimestamp(Path(path).stat().st_mtime),
    }
