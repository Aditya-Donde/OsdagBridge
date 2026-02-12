"""Dynamic project location helpers backed by the weather database.

This keeps all project-location related data (states, stations, IRC values)
centralized so both the basic inputs combobox and the Project Location
popup can consume the same source of truth.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from osdagbridge.core.data.project_location.database import Database

# Compute absolute path to weather.sqlite sitting under core/data/project_location
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "project_location", "weather.sqlite")
)


def _with_db(func):
    """Open/close a Database handle around simple reads."""
    def wrapper(*args, **kwargs):
        db = Database(DB_PATH)
        db.connect()
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close()
    return wrapper


@_with_db
def get_state_list(db: Database, include_placeholder: bool = True) -> List[str]:
    states = db.get_states_with_temperature() or []
    if include_placeholder:
        return ["Select State", *states]
    return states


@_with_db
def get_station_list(db: Database, state: str, include_placeholder: bool = True) -> List[str]:
    # Only include stations that have temperature data
    stations = db.get_stations_by_state_with_temperature(state) if state else []
    stations = stations or []
    if include_placeholder:
        return ["Select District", *stations] if stations else ["Select District"]
    return stations


@_with_db
def get_flat_location_options(db: Database, include_placeholder: bool = True) -> List[str]:
    options: List[str] = []
    for state in db.get_states_with_temperature() or []:
        for station in db.get_stations_by_state(state) or []:
            options.append(f"{station}, {state}")
    if include_placeholder:
        return ["Select Location", *options] if options else ["Select Location"]
    return options


@_with_db
def get_weather(db: Database, state: str, station: str) -> Dict[str, Optional[float]]:
    data = db.get_weather_data_by_state_station(state, station)
    if not data:
        return {
            "wind_speed": None,
            "zone": None,
            "z_value": None,
            "max_temp": None,
            "min_temp": None,
        }
    return {
        "wind_speed": data.get("wind_speed"),
        "zone": data.get("zone"),
        "z_value": data.get("z_value"),
        "max_temp": data.get("max_temp"),
        "min_temp": data.get("min_temp"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }


def get_default_location() -> Dict[str, str]:
    """Default to placeholders so the user explicitly selects a location."""
    return {"state": "", "station": ""}
