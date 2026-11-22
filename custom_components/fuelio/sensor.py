"""Sensors for Fuelio."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.util import dt as dt_util
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSORS = [
    ("odometer", "Przebieg", "km", "measurement", None),
    ("last_refuel_liters", "Ostatnie tankowanie – litry", "L", "measurement", None),
    ("last_refuel_cost", "Ostatnie tankowanie – koszt", "PLN", "measurement", None),
    ("last_refuel_price", "Ostatnie tankowanie – cena litra", "PLN/L", "measurement", None),
    ("last_refuel_date", "Data ostatniego tankowania", None, None, "timestamp"),
    ("last_refuel_station", "Stacja ostatniego tankowania", None, None, None),
    ("last_calculated_consumption", "Ostatnie obliczone spalanie", "L/100 km", "measurement", None),
    ("average_consumption", "Średnie spalanie z historii", "L/100 km", "measurement", None),
    ("fuel_cost_month", "Koszt paliwa w tym miesiącu", "PLN", "measurement", None),
    ("fuel_cost_year", "Koszt paliwa w tym roku", "PLN", "measurement", None),
    ("fuel_liters_month", "Paliwo w tym miesiącu", "L", "measurement", None),
    ("fuel_liters_year", "Paliwo w tym roku", "L", "measurement", None),
    ("maintenance_cost_total", "Koszty eksploatacji – suma historii", "PLN", "total", None),
    ("maintenance_cost_year", "Koszty eksploatacji w tym roku", "PLN", "measurement", None),
    ("next_service_distance", "Pozostało do najbliższego przypomnienia", "km", "measurement", None),
    ("next_service_name", "Najbliższe przypomnienie serwisowe", None, None, None),
    ("next_service_date_name", "Najbliższe przypomnienie – data", None, None, None),
    ("next_service_date", "Data najbliższego przypomnienia", None, None, "timestamp"),
    ("latest_cost_name", "Ostatni wpis kosztowy – nazwa", None, None, None),
    ("latest_cost_amount", "Ostatni wpis kosztowy – kwota", "PLN", "measurement", None),
    ("latest_cost_date", "Data ostatniego wpisu kosztowego", None, None, "timestamp"),
    ("latest_cost_category", "Ostatni wpis kosztowy – kategoria", None, None, None),
    ("refuel_count", "Liczba tankowań", None, "total", None),
    ("cost_count", "Liczba wpisów kosztowych", None, "total", None),
]

ICONS = {
    "odometer": "mdi:counter",
    "last_refuel_liters": "mdi:gas-station",
    "last_refuel_cost": "mdi:cash",
    "last_refuel_price": "mdi:tag",
    "last_refuel_date": "mdi:calendar-clock",
    "last_refuel_station": "mdi:map-marker",
    "last_calculated_consumption": "mdi:chart-line",
    "average_consumption": "mdi:chart-bar",
    "fuel_cost_month": "mdi:calendar-month",
    "fuel_cost_year": "mdi:calendar",
    "fuel_liters_month": "mdi:gas-station",
    "fuel_liters_year": "mdi:gas-station",
    "maintenance_cost_total": "mdi:tools",
    "maintenance_cost_year": "mdi:wrench",
    "next_service_distance": "mdi:car-wrench",
    "next_service_name": "mdi:clipboard-check",
    "next_service_date_name": "mdi:calendar-alert",
    "next_service_date": "mdi:calendar-clock",
    "latest_cost_name": "mdi:receipt-text",
    "latest_cost_amount": "mdi:cash",
    "latest_cost_date": "mdi:calendar",
    "latest_cost_category": "mdi:tag",
    "refuel_count": "mdi:counter",
    "cost_count": "mdi:receipt-text",
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FuelioSensor(coordinator, entry, key, name, unit, state_class, device_class)
        for key, name, unit, state_class, device_class in SENSORS
    )


class FuelioSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name, unit, state_class, device_class):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = ICONS.get(key, "mdi:eye")
        self._attr_native_unit_of_measurement = unit
        if state_class:
            self._attr_state_class = getattr(SensorStateClass, state_class.upper())
        if device_class == "timestamp":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        vehicle = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=vehicle.get("vehicle_name", "Fuelio"),
            manufacturer=vehicle.get("make", "") or "Fuelio",
            model=vehicle.get("model", "") or "Pojazd z Fuelio",
            sw_version=str(vehicle.get("year", "")) or None,
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        latest = data["latest"]
        reminder = data.get("next_reminder")
        date_reminder = data.get("next_date_reminder")
        latest_cost = data.get("latest_cost")
        values = {
            "odometer": data.get("odometer"),
            "last_refuel_liters": latest.get("fuel_liters"),
            "last_refuel_cost": latest.get("cost"),
            "last_refuel_price": (latest.get("cost", 0) / latest.get("fuel_liters", 0)) if latest.get("fuel_liters", 0) else None,
            "last_refuel_date": latest.get("date").replace(tzinfo=dt_util.DEFAULT_TIME_ZONE) if latest.get("date") else None,
            "last_refuel_station": latest.get("station") or None,
            "last_calculated_consumption": data.get("latest_calculated_consumption"),
            "average_consumption": data.get("average_consumption"),
            "fuel_cost_month": data.get("fuel_cost_month"),
            "fuel_cost_year": data.get("fuel_cost_year"),
            "fuel_liters_month": data.get("fuel_liters_month"),
            "fuel_liters_year": data.get("fuel_liters_year"),
            "maintenance_cost_total": data.get("maintenance_cost_total"),
            "maintenance_cost_year": data.get("maintenance_cost_year"),
            "next_service_distance": max(0, reminder["remind_odometer"] - data["odometer"]) if reminder else None,
            "next_service_name": reminder["title"] if reminder else None,
            "next_service_date_name": date_reminder["title"] if date_reminder else None,
            "next_service_date": (
                date_reminder["remind_date"].replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
                if date_reminder else None
            ),
            "latest_cost_name": latest_cost["title"] if latest_cost else None,
            "latest_cost_amount": latest_cost["cost"] if latest_cost else None,
            "latest_cost_date": (
                latest_cost["date"].replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
                if latest_cost else None
            ),
            "latest_cost_category": latest_cost["category"] if latest_cost else None,
            "refuel_count": data.get("refuel_count"),
            "cost_count": data.get("cost_count"),
        }
        value = values.get(self.key)
        numeric_keys = {
            "odometer", "last_refuel_liters", "last_refuel_cost", "last_refuel_price",
            "last_calculated_consumption", "average_consumption", "fuel_cost_month",
            "fuel_cost_year", "fuel_liters_month", "fuel_liters_year",
            "maintenance_cost_total", "maintenance_cost_year", "next_service_distance",
            "latest_cost_amount",
        }
        if self.key in numeric_keys and value is not None:
            return round(value, 2)
        return value

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        latest = data["latest"]
        date_reminder = data.get("next_date_reminder")
        mileage_reminder = data.get("next_reminder")
        attributes = {
            "vehicle": data.get("vehicle_name"),
            "make": data.get("make"),
            "model": data.get("model"),
            "year": data.get("year"),
            "last_refuel_full_tank": latest.get("full"),
            "last_refuel_station": latest.get("station"),
            "last_calculated_consumption_date": next(
                (x["date"].isoformat() for x in data.get("logs", []) if x.get("consumption", 0) > 0),
                None,
            ),
            "records_refuels": data.get("refuel_count"),
            "records_costs": data.get("cost_count"),
            "csv_last_modified": data.get("last_updated").isoformat() if data.get("last_updated") else None,
            "next_service_due_at_odometer": (
                mileage_reminder.get("remind_odometer") if mileage_reminder else None
            ),
            "next_service_due_at_date": (
                date_reminder.get("remind_date").isoformat() if date_reminder else None
            ),
        }
        if self.key == "cost_count":
            attributes["cost_history"] = [
                {
                    "title": item["title"],
                    "date": item["date"].isoformat(),
                    "category": item["category"],
                    "cost": item["cost"],
                    "odometer": item["odometer"],
                    "remind_date": item["remind_date"].isoformat() if item["remind_date"] else None,
                    "remind_odometer": item["remind_odometer"] or None,
                }
                for item in data.get("costs", [])
            ]
        return attributes
