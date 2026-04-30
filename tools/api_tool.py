"""
API Tools for Real-time Weather and Disaster Data
"""
import requests
from typing import Dict, List, Optional, Any
from config.config import Config
import json

class WeatherAPITool:
    """
    Weather API tool using OpenWeatherMap
    Retrieves current and forecast weather data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.OPENWEATHER_API_KEY
        self.base_url = Config.OPENWEATHER_API_URL
    
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dictionary
        """
        if not self.api_key:
            return {"error": "OpenWeatherMap API key not configured"}
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "location": data.get("name", "Unknown"),
                "coordinates": {"lat": lat, "lon": lon},
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"].get("deg", 0),
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "visibility": data.get("visibility", 0),
                "clouds": data["clouds"]["all"],
                "timestamp": data["dt"]
            }
        
        except Exception as e:
            return {"error": f"Weather API error: {str(e)}"}
    
    def get_weather_by_city(self, city: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current weather by city name
        
        Args:
            city: City name
            country_code: Optional ISO country code
            
        Returns:
            Weather data dictionary
        """
        if not self.api_key:
            return {"error": "OpenWeatherMap API key not configured"}
        
        try:
            url = f"{self.base_url}/weather"
            query = f"{city},{country_code}" if country_code else city
            params = {
                "q": query,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "location": data.get("name", "Unknown"),
                "country": data["sys"]["country"],
                "coordinates": {
                    "lat": data["coord"]["lat"],
                    "lon": data["coord"]["lon"]
                },
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"].get("deg", 0),
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "visibility": data.get("visibility", 0),
                "clouds": data["clouds"]["all"]
            }
        
        except Exception as e:
            return {"error": f"Weather API error: {str(e)}"}
    
    def get_forecast(self, lat: float, lon: float, days: int) -> List[Dict]:
        """
        Get weather forecast
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days (max 5 for free API)
            
        Returns:
            List of forecast data
        """
        if not self.api_key:
            return [{"error": "OpenWeatherMap API key not configured"}]
        
        days = max(1, min(int(days), 5))
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "cnt": min(days * 8, 40)  # 8 forecasts per day
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            forecasts = []
            
            for item in data["list"]:
                forecasts.append({
                    "datetime": item["dt_txt"],
                    "temperature": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "pressure": item["main"]["pressure"],
                    "wind_speed": item["wind"]["speed"],
                    "weather": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "clouds": item["clouds"]["all"],
                    "rain_3h": item.get("rain", {}).get("3h", 0)
                })
            
            return forecasts
        
        except Exception as e:
            return [{"error": f"Forecast API error: {str(e)}"}]


class DisasterAPITool:
    """
    Disaster API tool using NASA EONET
    Retrieves natural disaster and environmental event data
    """
    
    def __init__(self):
        self.base_url = Config.EONET_API_URL
    
    def get_active_events(self, limit: int) -> List[Dict]:
        """
        Get currently active natural disaster events
        
        Args:
            limit: Maximum number of events
            
        Returns:
            List of disaster events
        """
        limit = max(1, min(int(limit), 500))
        try:
            params = {
                "status": "open",
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            for event in data.get("events", []):
                # Extract first geometry point
                geometry = event.get("geometry", [])
                coords = geometry[0]["coordinates"] if geometry else [None, None]
                
                events.append({
                    "event_id": event["id"],
                    "title": event["title"],
                    "description": event.get("description", ""),
                    "event_type": event["categories"][0]["title"] if event.get("categories") else "Unknown",
                    "lat": coords[1] if len(coords) > 1 else None,
                    "lon": coords[0] if len(coords) > 0 else None,
                    "start_date": geometry[0]["date"] if geometry else None,
                    "sources": [s["url"] for s in event.get("sources", [])],
                    "categories": [c["title"] for c in event.get("categories", [])]
                })
            
            return events
        
        except Exception as e:
            print(f"❌ EONET API error: {e}")
            return []
    
    def get_events_by_category(self, category: str, limit: int) -> List[Dict]:
        """
        Get events by category
        
        Categories: wildfires, volcanoes, earthquakes, floods, 
                   storms, landslides, drought, dust_haze, water_color
        
        Args:
            category: Event category
            limit: Maximum number of events
            
        Returns:
            List of disaster events
        """
        limit = max(1, min(int(limit), 500))
        try:
            params = {"category": category, "limit": limit, "status": "open"}
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            for event in data.get("events", []):
                geometry = event.get("geometry", [])
                coords = geometry[0]["coordinates"] if geometry else [None, None]
                
                events.append({
                    "event_id": event["id"],
                    "title": event["title"],
                    "description": event.get("description", ""),
                    "event_type": category,
                    "lat": coords[1] if len(coords) > 1 else None,
                    "lon": coords[0] if len(coords) > 0 else None,
                    "start_date": geometry[0]["date"] if geometry else None,
                    "sources": [s["url"] for s in event.get("sources", [])]
                })
            
            return events
        
        except Exception as e:
            print(f"❌ EONET API error: {e}")
            return []
    
    def get_events_in_area(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        limit: int
    ) -> List[Dict]:
        """
        Get events in geographic bounding box
        Note: EONET API doesn't support bbox filtering directly,
        so we filter client-side
        """
        limit = max(1, min(int(limit), 500))
        all_events = self.get_active_events(limit=200)
        
        filtered_events = []
        for event in all_events:
            lat = event.get("lat")
            lon = event.get("lon")
            
            if lat and lon:
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    filtered_events.append(event)
        
        return filtered_events[:limit]
    
    def get_event_details(self, event_id: str) -> Dict[str, Any]:
        """
        Get detailed information about specific event
        
        Args:
            event_id: EONET event ID
            
        Returns:
            Event details dictionary
        """
        try:
            url = f"{self.base_url}/{event_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            event = response.json()
            
            # Parse all geometry points (event progression)
            timeline = []
            for geom in event.get("geometry", []):
                timeline.append({
                    "date": geom["date"],
                    "coordinates": geom["coordinates"],
                    "lat": geom["coordinates"][1] if len(geom["coordinates"]) > 1 else None,
                    "lon": geom["coordinates"][0] if len(geom["coordinates"]) > 0 else None
                })
            
            return {
                "event_id": event["id"],
                "title": event["title"],
                "description": event.get("description", ""),
                "categories": [c["title"] for c in event.get("categories", [])],
                "sources": event.get("sources", []),
                "timeline": timeline,
                "closed": event.get("closed")
            }
        
        except Exception as e:
            return {"error": f"Event details error: {str(e)}"}


if __name__ == "__main__":
    # Test APIs
    print("Testing Weather API...")
    weather_tool = WeatherAPITool()
    result = weather_tool.get_weather_by_city("London", "GB")
    print(json.dumps(result, indent=2))
    
    print("\nTesting Disaster API...")
    disaster_tool = DisasterAPITool()
    events = disaster_tool.get_active_events(limit=5)
    print(f"Found {len(events)} active disaster events")
    if events:
        print(json.dumps(events[0], indent=2))