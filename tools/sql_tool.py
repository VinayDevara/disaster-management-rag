"""
SQL Tool for Flight Agent
Pre-defined queries optimized for ADS-B flight data
"""
from typing import List, Dict, Any, Optional
from utils.database import DatabaseManager

class SQLTool:
    """
    SQL query tool with predefined common queries
    Used by agents to retrieve structured data
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_all_flights(self, limit: int) -> List[Dict]:
        """Get all flights with basic information"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT DISTINCT aircraft__hex, aircraft__flight, aircraft__alt_baro, 
                   aircraft__gs, aircraft__track, aircraft__lat, aircraft__lon, 
                   aircraft__squawk, aircraft__category, aircraft__emergency, 
                   now as timestamp
            FROM aircraft
            WHERE aircraft__flight IS NOT NULL AND aircraft__flight != ''
            ORDER BY now DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))
    
    def get_flight_by_callsign(self, callsign: str) -> List[Dict]:
        """Get flight information by callsign"""
        query = """
            SELECT * FROM aircraft
            WHERE aircraft__flight LIKE ?
            ORDER BY now DESC
            LIMIT 50
        """
        return self.db.execute_query(query, (f"%{callsign}%",))
    
    def get_flight_by_hex(self, hex_code: str) -> List[Dict]:
        """Get flight information by hex code"""
        query = """
            SELECT * FROM aircraft
            WHERE aircraft__hex = ?
            ORDER BY now DESC
            LIMIT 50
        """
        return self.db.execute_query(query, (hex_code,))
    
    def get_flights_in_area(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        limit: int
    ) -> List[Dict]:
        """Get flights in a geographic area"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT aircraft__hex, aircraft__flight, aircraft__alt_baro, 
                   aircraft__gs, aircraft__track, aircraft__lat, aircraft__lon, 
                   aircraft__squawk, aircraft__emergency, now as timestamp
            FROM aircraft
            WHERE aircraft__lat BETWEEN ? AND ?
              AND aircraft__lon BETWEEN ? AND ?
              AND aircraft__lat IS NOT NULL
              AND aircraft__lon IS NOT NULL
            ORDER BY now DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (lat_min, lat_max, lon_min, lon_max, limit))
    
    def get_emergency_flights(self, limit: int) -> List[Dict]:
        """Get flights with emergency squawks or status"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM aircraft
            WHERE aircraft__emergency IS NOT NULL 
              AND aircraft__emergency != 'none'
              AND aircraft__emergency != ''
            ORDER BY now DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))
    
    def get_flights_by_altitude_range(
        self,
        min_altitude: int,
        max_altitude: int,
        limit: int
    ) -> List[Dict]:
        """Get flights within altitude range"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT aircraft__hex, aircraft__flight, aircraft__alt_baro, 
                   aircraft__gs, aircraft__track, aircraft__lat, aircraft__lon, 
                   now as timestamp
            FROM aircraft
            WHERE aircraft__alt_baro BETWEEN ? AND ?
            ORDER BY now DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (min_altitude, max_altitude, limit))
    
    def get_high_speed_flights(self, min_speed: float, limit: int) -> List[Dict]:
        """Get flights exceeding a minimum speed"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT aircraft__hex, aircraft__flight, aircraft__alt_baro, 
                   aircraft__gs, aircraft__track, aircraft__lat, aircraft__lon, 
                   now as timestamp
            FROM aircraft
            WHERE aircraft__gs >= ?
            ORDER BY aircraft__gs DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (min_speed, limit))
    
    def get_flights_by_squawk(self, squawk: str) -> List[Dict]:
        """Get flights by squawk code"""
        query = """
            SELECT * FROM aircraft
            WHERE aircraft__squawk = ?
            ORDER BY now DESC
            LIMIT 50
        """
        return self.db.execute_query(query, (squawk,))
    
    def get_flight_trajectory(self, hex_code: str) -> List[Dict]:
        """Get flight path/trajectory for a specific aircraft"""
        query = """
            SELECT now as timestamp, aircraft__lat as lat, aircraft__lon as lon, 
                   aircraft__alt_baro as alt_baro, aircraft__gs as gs, 
                   aircraft__track as track, aircraft__flight as flight
            FROM aircraft
            WHERE aircraft__hex = ?
              AND aircraft__lat IS NOT NULL
              AND aircraft__lon IS NOT NULL
            ORDER BY now ASC
        """
        return self.db.execute_query(query, (hex_code,))
    
    def get_flights_near_location(
        self,
        lat: float,
        lon: float,
        radius_deg: float,
        limit: int
    ) -> List[Dict]:
        """
        Get flights near a specific location
        radius_deg: approximate radius in degrees (1 deg ≈ 111 km)
        """
        limit = max(1, min(int(limit), 500))
        radius_deg = max(0.1, min(float(radius_deg), 10.0))
        lat_min = lat - radius_deg
        lat_max = lat + radius_deg
        lon_min = lon - radius_deg
        lon_max = lon + radius_deg
        
        return self.get_flights_in_area(lat_min, lat_max, lon_min, lon_max, limit)
    
    def get_flight_count_by_time_window(self, hours: int) -> int:
        """Get count of unique flights in time window"""
        hours = max(1, min(int(hours), 72))
        query = """
            SELECT COUNT(DISTINCT aircraft__hex) as count
            FROM aircraft
            WHERE now >= (SELECT MAX(now) - (? * 3600) FROM aircraft)
        """
        result = self.db.execute_query(query, (hours,))
        return result[0]['count'] if result else 0
    
    def get_flights_by_category(self, category: str, limit: int) -> List[Dict]:
        """Get flights by aircraft category"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT DISTINCT aircraft__hex, aircraft__flight, aircraft__alt_baro, 
                   aircraft__gs, aircraft__category, aircraft__lat, aircraft__lon, 
                   now as timestamp
            FROM aircraft
            WHERE aircraft__category = ?
            ORDER BY now DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (category, limit))
    
    def get_latest_snapshot(self, limit: int) -> List[Dict]:
        """Get most recent snapshot of all active flights"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT a1.*
            FROM aircraft a1
            INNER JOIN (
                SELECT aircraft__hex, MAX(now) as max_timestamp
                FROM aircraft
                GROUP BY aircraft__hex
            ) a2 ON a1.aircraft__hex = a2.aircraft__hex AND a1.now = a2.max_timestamp
            ORDER BY a1.now DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))
    
    def execute_custom_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """
        Execute custom SQL query
        Use with caution - validate query before execution
        """
        return self.db.execute_query(query, params)


class WeatherSQLTool:
    """SQL queries for weather events"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_weather_events_by_type(self, event_type: str, limit: int) -> List[Dict]:
        """Get weather events by type"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM weather_events
            WHERE event_type = ?
            ORDER BY start_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (event_type, limit))
    
    def get_weather_events_in_area(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        limit: int
    ) -> List[Dict]:
        """Get weather events in geographic area"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM weather_events
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
            ORDER BY start_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (lat_min, lat_max, lon_min, lon_max, limit))
    
    def get_active_weather_events(self, limit: int) -> List[Dict]:
        """Get currently active weather events"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM weather_events
            WHERE (end_time IS NULL OR end_time > datetime('now'))
            ORDER BY start_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))


class DisasterSQLTool:
    """SQL queries for disaster events"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_disaster_events_by_type(self, event_type: str, limit: int) -> List[Dict]:
        """Get disaster events by type"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM disaster_events
            WHERE event_type = ?
            ORDER BY start_date DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (event_type, limit))
    
    def get_disaster_events_in_area(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        limit: int
    ) -> List[Dict]:
        """Get disaster events in geographic area"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM disaster_events
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
            ORDER BY start_date DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (lat_min, lat_max, lon_min, lon_max, limit))
    
    def get_recent_disasters(self, days: int, limit: int) -> List[Dict]:
        """Get recent disaster events"""
        days = max(1, min(int(days), 365))
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM disaster_events
            WHERE start_date >= date('now', '-' || ? || ' days')
            ORDER BY start_date DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (days, limit))
    
    def get_high_severity_disasters(self, limit: int) -> List[Dict]:
        """Get high severity disasters"""
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM disaster_events
            WHERE severity IN ('high', 'critical', 'severe')
            ORDER BY start_date DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))


# ======================================================================
# New SQL tool classes for ingested external data sources
# ======================================================================

class AlertsSQLTool:
    """SQL queries for official alerts (SACHET / NDMA)."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_latest_alerts(self, limit: int = 50, district: str = None) -> List[Dict]:
        return self.db.get_latest_alerts(limit=limit, district=district)

    def get_alerts_by_severity(self, severity: str, limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM official_alerts
            WHERE severity = ?
            ORDER BY issued_at DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (severity, limit))

    def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM official_alerts
            WHERE status IN ('Actual', 'active', 'Alert')
              AND (expires_at IS NULL OR expires_at > datetime('now'))
            ORDER BY issued_at DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))


class ForecastSQLTool:
    """SQL queries for Open-Meteo forecast signals."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_latest_forecasts(self, limit: int = 100, location: str = None) -> List[Dict]:
        return self.db.get_latest_forecasts(limit=limit, location=location)

    def get_high_precipitation_forecasts(self, threshold: float = 5.0,
                                          limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM forecast_signals_hot
            WHERE precipitation >= ?
            ORDER BY forecast_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (threshold, limit))

    def get_forecasts_for_location(self, location: str, limit: int = 48) -> List[Dict]:
        limit = max(1, min(int(limit), 200))
        query = """
            SELECT * FROM forecast_signals_hot
            WHERE location_name = ?
            ORDER BY forecast_time ASC
            LIMIT ?
        """
        return self.db.execute_query(query, (location, limit))


class RainfallSQLTool:
    """SQL queries for GPM IMERG rainfall observations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_latest_rainfall(self, limit: int = 50) -> List[Dict]:
        return self.db.get_latest_rainfall(limit=limit)

    def get_heavy_rainfall(self, threshold: float = 10.0, limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM rainfall_observations
            WHERE rainfall_mm >= ?
            ORDER BY observation_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (threshold, limit))


class LandslideSQLTool:
    """SQL queries for LHASA landslide nowcast snapshot."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_latest_snapshot(self, limit: int = 50) -> List[Dict]:
        return self.db.get_latest_landslide_snapshot(limit=limit)

    def get_high_risk_cells(self, limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM landslide_snapshot_current
            WHERE risk_level IN ('high', 'very_high', 'critical')
               OR probability >= 0.7
            ORDER BY probability DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (limit,))


class ExternalEventsSQLTool:
    """SQL queries for GDACS external events."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_latest_events(self, limit: int = 50, event_type: str = None) -> List[Dict]:
        return self.db.get_latest_external_events(limit=limit, event_type=event_type)

    def get_events_by_severity(self, severity: str, limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM external_events
            WHERE severity = ?
            ORDER BY event_date DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (severity, limit))


class CycloneSQLTool:
    """SQL queries for IBTrACS historical cyclones."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_cyclones_in_basin(self, basin: str = "NI", limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM historical_cyclones
            WHERE basin = ?
            ORDER BY iso_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (basin, limit))

    def get_cyclones_near_region(self, lat_min: float = 12.5, lat_max: float = 13.6,
                                  lon_min: float = 74.5, lon_max: float = 75.4,
                                  limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM historical_cyclones
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
            ORDER BY iso_time DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (lat_min, lat_max, lon_min, lon_max, limit))

    def get_intense_cyclones(self, min_wind_kt: float = 64, limit: int = 50) -> List[Dict]:
        limit = max(1, min(int(limit), 500))
        query = """
            SELECT * FROM historical_cyclones
            WHERE wind_kt >= ?
            ORDER BY wind_kt DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (min_wind_kt, limit))