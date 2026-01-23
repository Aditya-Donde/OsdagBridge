import sqlite3
import os
from typing import List, Dict, Tuple, Optional


class Database:
    """
    Weather DB with (state, station) as the canonical key.
    stations = parent; temperature/zone/windspeed = children.
    """

    def __init__(self, db_name: str = 'weather.db'):
        self.db_name = db_name
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    # -------------------- connection --------------------

    def connect(self):
        """Establish connection to the database."""
        self.connection = sqlite3.connect(self.db_name)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    # -------------------- schema --------------------

    def run_schema(self, schema_file: str = 'schema.sql'):
        """
        Execute the SQL schema file to create (and optionally seed) the database.
        Uses executescript to safely run multi-statement SQL.
        """
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file '{schema_file}' not found")

        self.connect()

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        self.connection.executescript(schema_sql)

        # If someone ran with an older schema (no stations), fix it up:
        self._bootstrap_stations_if_missing()

        print(f"Database '{self.db_name}' created and populated successfully!")

    def _table_exists(self, name: str) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,)
        )
        return self.cursor.fetchone() is not None

    def _bootstrap_stations_if_missing(self):
        """
        If the DB lacks a 'stations' table (legacy 3-table layout),
        create it and backfill from existing child tables.
        """
        if self._table_exists("stations"):
            return

        # create parent table
        self.cursor.execute("""
            CREATE TABLE stations (
                state   TEXT NOT NULL,
                station TEXT NOT NULL,
                PRIMARY KEY (state, station)
            )
        """)

        # backfill union of keys from children (if they exist)
        unions = []
        for tbl in ("temperature_data", "zone_data", "windspeed_data"):
            if self._table_exists(tbl):
                unions.append(f"SELECT state, station FROM {tbl}")

        if unions:
            union_sql = " UNION ".join(unions)
            self.cursor.execute(f"INSERT OR IGNORE INTO stations(state, station) {union_sql}")

        # helpful indexes
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stations_state ON stations(state)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stations_station ON stations(station)")

        self.connection.commit()

    # -------------------- dropdowns (use parent) --------------------

    def get_states_with_temperature(self) -> List[str]:
        """List all unique states from the canonical stations table where atleast one station has temperature data."""
        self.cursor.execute("""
            SELECT DISTINCT s.state 
            FROM stations s
            INNER JOIN temperature_data t ON s.state = t.state AND s.station = t.station
            WHERE t.max_temp IS NOT NULL AND t.min_temp IS NOT NULL
            ORDER BY s.state
        """)
        return [row[0] for row in self.cursor.fetchall()]

    def get_stations_by_state(self, state: str) -> List[str]:
        """List all stations for a given state from the canonical stations table."""
        self.cursor.execute(
            "SELECT station FROM stations WHERE state = ? ORDER BY station",
            (state,),
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_stations_by_state_with_temperature(self, state: str) -> List[str]:
        """List stations for a given state that have valid temperature data (non-NULL)."""
        self.cursor.execute(
            """
            SELECT s.station
            FROM stations s
            INNER JOIN temperature_data t ON s.state = t.state AND s.station = t.station
            WHERE s.state = ?
              AND t.max_temp IS NOT NULL
              AND t.min_temp IS NOT NULL
            ORDER BY s.station
            """,
            (state,),
        )
        return [row[0] for row in self.cursor.fetchall()]

    # -------------------- details (LEFT JOIN children) --------------------

    def get_weather_data_by_state_station(self, state: str, station: str) -> Optional[Dict]:
        """
        Get complete weather data for a specific state and station.
        Includes temperature, zone, and windspeed (NULL if not available).
        """
        self.cursor.execute(
            """
            SELECT s.state, s.station,
                   t.max_temp, t.min_temp,
                   z.zone, z.z_value,
                   w.wind_speed,
                   s.latitude, s.longitude
            FROM stations s
            LEFT JOIN temperature_data t ON s.state = t.state AND s.station = t.station
            LEFT JOIN zone_data z        ON s.state = z.state AND s.station = z.station
            LEFT JOIN windspeed_data w   ON s.state = w.state AND s.station = w.station
            WHERE s.state = ? AND s.station = ?
            """,
            (state, station),
        )
        data = self.cursor.fetchone()

        if not data:
            return None

        return {
            'state': data[0],
            'station': data[1],
            'max_temp': data[2],
            'min_temp': data[3],
            'zone': data[4],
            'z_value': data[5],
            'wind_speed': data[6],
            'latitude': data[7],
            'longitude': data[8],
        }

    def get_temperature_by_state_station(self, state: str, station: str) -> Optional[Tuple[float, float]]:
        """Get temperature data (max, min) for a specific station."""
        self.cursor.execute(
            """
            SELECT t.max_temp, t.min_temp
            FROM temperature_data t
            WHERE t.state = ? AND t.station = ?
            """,
            (state, station),
        )
        result = self.cursor.fetchone()
        return result if result else None

    def get_zone_by_station(self, state: str, station: str) -> Optional[Tuple[str, float]]:
        """Get zone info for a specific station."""
        self.cursor.execute(
            """
            SELECT z.zone, z.z_value
            FROM zone_data z
            WHERE z.state = ? AND z.station = ?
            """,
            (state, station),
        )
        result = self.cursor.fetchone()
        return result if result else None

    def get_windspeed_by_station(self, state: str, station: str) -> Optional[int]:
        """Get wind speed for a specific station."""
        self.cursor.execute(
            """
            SELECT w.wind_speed
            FROM windspeed_data w
            WHERE w.state = ? AND w.station = ?
            """,
            (state, station),
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_nearest_station_temperature(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Find the nearest station with temperature data based on coordinates.
        
        Uses simplified Euclidean distance (sufficient for nearby points within India).
        Returns station info and temperature data for the nearest match.
            
        Returns:
            Dict with keys: state, station, max_temp, min_temp, distance_deg
            or None if no station with coordinates and temperature data exists.
        """
        # Query stations with coordinates and temperature data, calculate distance
        # Using Euclidean approximation: sqrt((lat2-lat1)^2 + (lon2-lon1)^2)
        self.cursor.execute(
            """
            SELECT s.state, s.station, s.latitude, s.longitude,
                   t.max_temp, t.min_temp,
                   ((s.latitude - ?) * (s.latitude - ?) + (s.longitude - ?) * (s.longitude - ?)) as dist_sq
            FROM stations s
            INNER JOIN temperature_data t ON s.state = t.state AND s.station = t.station
            WHERE s.latitude IS NOT NULL 
              AND s.longitude IS NOT NULL
              AND t.max_temp IS NOT NULL
              AND t.min_temp IS NOT NULL
            ORDER BY dist_sq ASC
            LIMIT 1
            """,
            (lat, lat, lon, lon),
        )
        result = self.cursor.fetchone()
        
        if not result:
            return None
        
        import math
        distance_deg = math.sqrt(result[6]) if result[6] else 0
        
        return {
            'state': result[0],
            'station': result[1],
            'latitude': result[2],
            'longitude': result[3],
            'max_temp': result[4],
            'min_temp': result[5],
            'distance_deg': round(distance_deg, 4),
        }

    def search_stations(self, search_term: str) -> List[Dict]:
        """
        Fuzzy search over canonical stations; great for autocomplete.
        """
        like = f'%{search_term}%'
        self.cursor.execute(
            """
            SELECT state, station FROM stations
            WHERE station LIKE ? OR state LIKE ?
            ORDER BY state, station
            """,
            (like, like),
        )
        return [{'state': row[0], 'station': row[1]} for row in self.cursor.fetchall()]

    def get_stations_with_zone_data(self) -> List[Dict]:
        """All stations that have zone data."""
        self.cursor.execute(
            """
            SELECT z.state, z.station, z.zone, z.z_value
            FROM zone_data z
            ORDER BY z.state, z.station
            """
        )
        return [{'state': r[0], 'station': r[1], 'zone': r[2], 'z_value': r[3]} for r in self.cursor.fetchall()]

    def get_stations_with_windspeed_data(self) -> List[Dict]:
        """All stations that have windspeed data."""
        self.cursor.execute(
            """
            SELECT w.state, w.station, w.wind_speed
            FROM windspeed_data w
            ORDER BY w.state, w.station
            """
        )
        return [{'state': r[0], 'station': r[1], 'wind_speed': r[2]} for r in self.cursor.fetchall()]

    # -------------------- stats (count from parent) --------------------

    def get_statistics(self) -> Dict:
        """
        Database statistics including record counts and data ranges.
        """
        stats: Dict[str, Optional[float]] = {}

        # Unique station count (ground truth)
        self.cursor.execute("SELECT COUNT(*) FROM stations")
        stats['total_stations'] = self.cursor.fetchone()[0]

        # Child row counts
        self.cursor.execute("SELECT COUNT(*) FROM temperature_data")
        stats['records_with_temperature'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM zone_data")
        stats['records_with_zone'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM windspeed_data")
        stats['records_with_windspeed'] = self.cursor.fetchone()[0]

        # Stations that lack BOTH zone and wind entries
        self.cursor.execute("""
            SELECT COUNT(*) FROM stations s
            LEFT JOIN zone_data z ON s.state = z.state AND s.station = z.station
            LEFT JOIN windspeed_data w ON s.state = w.state AND s.station = w.station
            WHERE z.state IS NULL AND w.state IS NULL
        """)
        stats['stations_without_zone_and_wind'] = self.cursor.fetchone()[0]

        # Temperature statistics (only where both present)
        self.cursor.execute("""
            SELECT MAX(max_temp), MIN(min_temp), AVG(max_temp), AVG(min_temp)
            FROM temperature_data
            WHERE max_temp IS NOT NULL AND min_temp IS NOT NULL
        """)
        t = self.cursor.fetchone()
        stats['highest_max_temp'] = t[0]
        stats['lowest_min_temp'] = t[1]
        stats['avg_max_temp'] = round(t[2], 2) if t[2] is not None else None
        stats['avg_min_temp'] = round(t[3], 2) if t[3] is not None else None

        # Wind stats
        self.cursor.execute("SELECT MAX(wind_speed), MIN(wind_speed), AVG(wind_speed) FROM windspeed_data")
        w = self.cursor.fetchone()
        stats['max_wind_speed'] = w[0]
        stats['min_wind_speed'] = w[1]
        stats['avg_wind_speed'] = round(w[2], 2) if w[2] is not None else None

        return stats


# -------------------- quick manual test --------------------

if __name__ == '__main__':
    db = Database('weather.db')

    print("Creating and populating database...")
    db.run_schema('schema.sql')

    print("\n" + "="*50)
    print("TESTING DATABASE QUERIES")
    print("="*50)

    print("\n1. Getting all states...")
    states = db.get_states_with_temperature()
    print(f"Total states: {len(states)}")
    print(f"First 5 states: {states[:5]}")

    print("\n2. Getting stations for 'Andhra Pradesh'...")
    stations = db.get_stations_by_state('Andhra Pradesh')
    print(f"Total stations: {len(stations)}")
    print(f"First 5 stations: {stations[:5]}")

    print("\n3. Getting complete weather data for 'Andhra Pradesh' - 'Anantapur'...")
    data = db.get_weather_data_by_state_station('Andhra Pradesh', 'Anantapur')
    if data:
        print(f"State: {data['state']}")
        print(f"Station: {data['station']}")
        print(f"Max Temperature: {data['max_temp']}°C")
        print(f"Min Temperature: {data['min_temp']}°C")
        print(f"Zone: {data['zone'] if data['zone'] else 'NULL'}")
        print(f"Z Value: {data['z_value'] if data['z_value'] else 'NULL'}")
        print(f"Wind Speed: {data['wind_speed'] if data['wind_speed'] else 'NULL'} m/s")

    print("\n4. Searching for stations with 'Mumbai'...")
    results = db.search_stations('Mumbai')
    for result in results[:10]:
        print(f"  - {result['state']}: {result['station']}")

    print("\n5. Database Statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n6. Stations with Zone Data (first 5):")
    zone_stations = db.get_stations_with_zone_data()
    for station in zone_stations[:5]:
        print(f"  - {station['state']}: {station['station']} (Zone {station['zone']})")

    db.close()

    print("\n" + "="*50)
    print("Database testing completed successfully!")
    print("="*50)
