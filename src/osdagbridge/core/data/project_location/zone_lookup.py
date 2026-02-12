"""Zone lookup module for IRC:6 wind and seismic zone determination.

This module performs point-in-polygon queries against digitized IRC:6 zone maps
to determine wind speed (Vb) and seismic zone/factor for a given lat/long.

SHAPEFILE SETUP:
-----------------
1. Digitize IRC:6 wind and seismic zone maps in QGIS
2. Export as shapefiles to: core/data/project_location/shapefiles/
3. Required files:
   - wind_zones.shp (with attributes: zone_id, Vb, source)
   - seismic_zones.shp (with attributes: zone_id, seismic_zone, zone_factor, source)

Once shapefiles are available, set USE_MOCK_DATA = False to enable real lookups.
"""

from __future__ import annotations

import os
from typing import Dict, Optional, Any

# Path to shapefiles directory
SHAPEFILES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "shapefiles")
)

WIND_SHAPEFILE = os.path.join(SHAPEFILES_DIR, "wind_zones.shp")
SEISMIC_SHAPEFILE = os.path.join(SHAPEFILES_DIR, "seismic_zones.shp")

# Cache for loaded geometries (load once, reuse)
_wind_zones = None
_seismic_zones = None


def _load_shapefile(filepath: str):
    """Load a shapefile and return list of (geometry, attributes) tuples."""
    try:
        import fiona
        from shapely.geometry import shape
        
        zones = []
        with fiona.open(filepath, 'r') as src:
            for feature in src:
                geom = shape(feature['geometry'])
                props = dict(feature['properties'])
                zones.append((geom, props))
        return zones
    except ImportError:
        print("Warning: fiona/shapely not installed. Install with: pip install fiona shapely")
        return None
    except Exception as e:
        print(f"Warning: Could not load shapefile {filepath}: {e}")
        return None


def _ensure_zones_loaded():
    """Lazy-load shapefiles on first use."""
    global _wind_zones, _seismic_zones
    

    
    if _wind_zones is None and os.path.exists(WIND_SHAPEFILE):
        _wind_zones = _load_shapefile(WIND_SHAPEFILE)
    
    if _seismic_zones is None and os.path.exists(SEISMIC_SHAPEFILE):
        _seismic_zones = _load_shapefile(SEISMIC_SHAPEFILE)


def _point_in_polygon_lookup(lat: float, lon: float, zones) -> Optional[Dict]:
    """Find which polygon contains the given point."""
    if not zones:
        return None
    
    try:
        from shapely.geometry import Point
        point = Point(lon, lat)  # Note: lon, lat order for shapely
        
        for geom, props in zones:
            if geom.contains(point):
                return props
        
        # Check for nearest polygon within threshold (e.g. 0.5 deg ~= 55km)
        # This handles points slightly outside boundaries (coastlines, borders)
        min_dist = float('inf')
        nearest_props = None
        
        for geom, props in zones:
            dist = geom.distance(point)
            if dist < min_dist:
                min_dist = dist
                nearest_props = props
                
        if nearest_props and min_dist < 0.5:
             return nearest_props

        return None
    except ImportError:
        return None


def get_zones_for_coordinates(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get wind and seismic zone data for given coordinates.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
    
    Returns:
        Dictionary with keys:
        - wind_Vb: Basic wind speed in m/s (or None)
        - seismic_zone: Zone designation (II/III/IV/V or None)
        - zone_factor: Z value for seismic design (or None)
        - source: Data source ("IRC6" or None)
    """
    _ensure_zones_loaded()
    
    result = {
        "wind_Vb": None,
        "seismic_zone": None,
        "zone_factor": None,
        "source": "IRC6"
    }
    
    # Wind zone lookup
    if _wind_zones:
        wind_props = _point_in_polygon_lookup(lat, lon, _wind_zones)
        if wind_props:
            result["wind_Vb"] = wind_props.get("Vb")
    
    # Seismic zone lookup
    if _seismic_zones:
        seismic_props = _point_in_polygon_lookup(lat, lon, _seismic_zones)
        if seismic_props:
            # Handle possible attribute name truncation (DBF has 10 char limit)
            # seismic_zone -> seismic_zo
            # zone_factor -> zone_facto
            
            s_zone = seismic_props.get("seismic_zone")
            if s_zone is None:
                s_zone = seismic_props.get("seismic_zo")
                
            z_factor = seismic_props.get("zone_factor")
            if z_factor is None:
                z_factor = seismic_props.get("zone_facto")
            
            result["seismic_zone"] = s_zone
            result["zone_factor"] = z_factor
    
    return result





def get_temperature_for_coordinates(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get temperature data for the nearest station to given coordinates.
    
    Returns:
        Dictionary with keys:
        - max_temp: Maximum temperature in °C (or None)
        - min_temp: Minimum temperature in °C (or None)
        - nearest_station: Name of the nearest station (or None)
        - nearest_state: State of the nearest station (or None)
    """
    from .database import Database
    
    result = {
        "max_temp": None,
        "min_temp": None,
        "nearest_station": None,
        "nearest_state": None,
    }
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), "weather.sqlite")
    
    if not os.path.exists(db_path):
        return result
    
    try:
        db = Database(db_path)
        db.connect()
        temp_data = db.get_nearest_station_temperature(lat, lon)
        db.close()
        
        if temp_data:
            result["max_temp"] = temp_data.get("max_temp")
            result["min_temp"] = temp_data.get("min_temp")
            result["nearest_station"] = temp_data.get("station")
            result["nearest_state"] = temp_data.get("state")
    except Exception as e:
        print(f"Warning: Temperature lookup failed: {e}")
    
    return result


def shapefiles_available() -> Dict[str, bool]:
    """Check which shapefiles are available."""
    return {
        "wind_zones": os.path.exists(WIND_SHAPEFILE),
        "seismic_zones": os.path.exists(SEISMIC_SHAPEFILE)
    }
