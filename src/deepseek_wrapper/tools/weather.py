import os
import time
import logging
import requests
from typing import Dict, Any, List, Optional, Union
import datetime

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

class WeatherTool(Tool[Dict[str, Any]]):
    """Tool for fetching current weather and forecasts."""
    
    name = "weather"
    description = "Get current weather conditions or forecasts for a location"
    parameters = {
        "location": {
            "type": "string",
            "description": "Location to get weather for (city name, zip/postal code, or coordinates)"
        },
        "forecast_days": {
            "type": "integer",
            "description": "Number of days to forecast (0 for current weather only)",
            "minimum": 0,
            "maximum": 7,
            "default": 0
        },
        "units": {
            "type": "string",
            "description": "Unit system to use for temperatures and measurements",
            "enum": ["metric", "imperial"],
            "default": "metric"
        }
    }
    required_params = ["location"]
    
    def __init__(self, **kwargs):
        """Initialize the weather tool with optional configuration.
        
        Args:
            api_key: Optional OpenWeatherMap API key
            rate_limit: Maximum requests per minute (default: 10)
        """
        super().__init__(**kwargs)
        
        # Get API credentials from environment or config
        self.api_key = kwargs.get("api_key") or os.getenv("OPENWEATHERMAP_API_KEY")
        
        # Validate API credentials
        self._validate_api_key()
        
        # Rate limiting
        self.rate_limit = kwargs.get("rate_limit", 10)  # requests per minute
        self.request_timestamps = []
        
        # Extra configuration
        self.retry_attempts = kwargs.get("retry_attempts", 3)
        self.retry_delay = kwargs.get("retry_delay", 1)  # seconds
        self.retry_backoff = kwargs.get("retry_backoff", 2)  # exponential backoff multiplier
        
        # Last API validation time
        self.last_api_validation = None
        self.api_validation_ttl = 3600  # Re-validate API key once per hour
        
        # Network status
        self.network_error_count = 0
        self.last_network_error = None
    
    def _validate_api_key(self):
        """Validate that the API key is properly configured."""
        self.has_valid_api_key = False
        
        if not self.api_key:
            logger.warning("WeatherTool: No API key configured (OPENWEATHERMAP_API_KEY not set)")
            return
            
        # Basic validation - OpenWeatherMap API keys are typically 32 characters
        if len(self.api_key) != 32:
            logger.warning(f"WeatherTool: API key has unusual length: {len(self.api_key)} (expected 32)")
        
        # Mark as provisionally valid until tested with API
        self.has_valid_api_key = True
        logger.info("WeatherTool: API key configured and appears valid")
        
        # Schedule a validation on first use
        self.last_api_validation = None
    
    def _test_api_key(self) -> bool:
        """Test the API key with a simple API call to validate it works.
        
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        current_time = time.time()
        
        # Skip validation if we've validated recently
        if (self.last_api_validation and 
            current_time - self.last_api_validation < self.api_validation_ttl):
            return self.has_valid_api_key
        
        if not self.api_key:
            self.has_valid_api_key = False
            return False
        
        try:
            # Use a simple, quick API call to test the key
            test_url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": "London",  # Use a common city that will always exist
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(test_url, params=params, timeout=5)
            
            if response.status_code == 200:
                self.has_valid_api_key = True
                self.logger.info("WeatherTool: API key validated successfully")
            elif response.status_code == 401:
                self.has_valid_api_key = False
                self.logger.error("WeatherTool: Invalid API key (401 Unauthorized)")
            else:
                # Other error codes might not indicate an invalid key
                self.logger.warning(f"WeatherTool: API key validation returned status code {response.status_code}")
            
            # Update last validation time regardless of result
            self.last_api_validation = current_time
            
            return self.has_valid_api_key
        except Exception as e:
            self.logger.error(f"WeatherTool: Error validating API key: {str(e)}")
            # Network errors don't necessarily mean the key is invalid,
            # so we don't change the existing validation status
            self.last_api_validation = current_time
            return self.has_valid_api_key
    
    def _run(self, location: str, forecast_days: int = 0, units: str = "metric") -> Dict[str, Any]:
        """Get weather information for a location.
        
        Args:
            location: Location to get weather for (city name, zip/postal code, or coordinates)
            forecast_days: Number of days to forecast (0 for current weather only)
            units: Unit system to use ('metric' or 'imperial')
            
        Returns:
            Dictionary containing weather information
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Sanitize inputs
        location = location.strip()
        forecast_days = max(0, min(7, forecast_days))  # Clamp between 0 and 7
        units = units.lower() if units in ["metric", "imperial"] else "metric"
        
        self.logger.info(f"Getting weather for location: '{location}' (forecast days: {forecast_days})")
        
        try:
            # Validate API key on first use or if validation has expired
            if not self.last_api_validation or not self._test_api_key():
                self.logger.warning("No valid OpenWeatherMap API key, using fallback response")
                return self._generate_fallback_response(location, forecast_days, units)
            
            # Get current weather or forecast based on parameters
            if forecast_days == 0:
                result = self._get_current_weather(location, units)
            else:
                result = self._get_forecast(location, forecast_days, units)
            
            # Reset network error count on success
            self.network_error_count = 0
            self.last_network_error = None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Weather API error: {str(e)}", exc_info=True)
            return {
                "location": location,
                "success": False,
                "error": str(e),
                "forecast_days": forecast_days,
                "units": units
            }
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to prevent overuse."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [t for t in self.request_timestamps if current_time - t < 60]
        
        # If we've hit the rate limit, sleep until we can make another request
        if len(self.request_timestamps) >= self.rate_limit:
            oldest_timestamp = min(self.request_timestamps)
            sleep_time = 60 - (current_time - oldest_timestamp)
            if sleep_time > 0:
                self.logger.warning(f"Rate limit hit, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add current request timestamp
        self.request_timestamps.append(time.time())
    
    def _get_current_weather(self, location: str, units: str) -> Dict[str, Any]:
        """Get current weather for a location using OpenWeatherMap API."""
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        
        params = {
            "q": location,  # Try city name first
            "appid": self.api_key,
            "units": units
        }
        
        # Detect if location is coordinates
        if "," in location and all(part.replace(".", "").replace("-", "").isdigit() for part in location.split(",")):
            lat, lon = location.split(",")
            params = {
                "lat": lat.strip(),
                "lon": lon.strip(),
                "appid": self.api_key,
                "units": units
            }
        # Detect if it's a US zip code
        elif location.strip().isdigit() and len(location.strip()) == 5:
            params = {
                "zip": location.strip(),
                "appid": self.api_key,
                "units": units
            }
        
        # Make request with retry logic
        response = None
        last_error = None
        
        for attempt in range(self.retry_attempts + 1):
            try:
                response = requests.get(base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    break
                
                elif response.status_code == 401:
                    self.has_valid_api_key = False
                    self.logger.error("Invalid API key for OpenWeatherMap")
                    self.last_api_validation = time.time()  # Update last validation time
                    raise Exception("Invalid API key for weather service")
                
                elif response.status_code == 404:
                    raise Exception(f"Location '{location}' not found")
                
                elif response.status_code == 429:
                    self.logger.warning("Rate limit exceeded for OpenWeatherMap API")
                    if attempt < self.retry_attempts:
                        sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                        self.logger.info(f"Retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                        time.sleep(sleep_time)
                        continue
                    raise Exception("Rate limit exceeded for weather service")
                
                else:
                    error_msg = f"Weather API returned status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg += f": {error_data['message']}"
                    except:
                        error_msg += f": {response.text}"
                        
                    if attempt < self.retry_attempts:
                        sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                        self.logger.warning(f"{error_msg}. Retrying in {sleep_time}s (attempt {attempt+1}/{self.retry_attempts})")
                        time.sleep(sleep_time)
                        last_error = error_msg
                        continue
                    
                    raise Exception(error_msg)
            
            except requests.exceptions.Timeout:
                self.network_error_count += 1
                self.last_network_error = time.time()
                
                if attempt < self.retry_attempts:
                    sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                    self.logger.info(f"Request timed out, retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                    time.sleep(sleep_time)
                    last_error = "Weather API request timed out"
                    continue
                raise Exception("Weather API request timed out after multiple attempts")
            
            except requests.exceptions.ConnectionError:
                self.network_error_count += 1
                self.last_network_error = time.time()
                
                if attempt < self.retry_attempts:
                    sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                    self.logger.info(f"Connection error, retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                    time.sleep(sleep_time)
                    last_error = "Connection error when accessing weather service"
                    continue
                raise Exception("Connection error when accessing weather service after multiple attempts")
        
        if not response or response.status_code != 200:
            if last_error:
                raise Exception(last_error)
            raise Exception(f"Failed to get weather data for {location}")
        
        try:
            data = response.json()
        except ValueError:
            raise Exception("Invalid JSON response from weather service")
        
        # Format temperature and time data
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0] if data.get("weather") else {}
        wind = data.get("wind", {})
        sys = data.get("sys", {})
        
        # Determine units labels
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"
        
        # Convert Unix timestamps
        sunrise = sys.get("sunrise")
        sunset = sys.get("sunset")
        
        if sunrise:
            sunrise_dt = datetime.datetime.fromtimestamp(sunrise)
            sunrise_str = sunrise_dt.strftime("%H:%M")
        else:
            sunrise_str = "N/A"
            
        if sunset:
            sunset_dt = datetime.datetime.fromtimestamp(sunset)
            sunset_str = sunset_dt.strftime("%H:%M")
        else:
            sunset_str = "N/A"
        
        # Build a nicely formatted result
        result = {
            "location": data.get("name", location),
            "country": sys.get("country", ""),
            "description": weather.get("description", "").capitalize(),
            "temperature": f"{main.get('temp', 'N/A')} {temp_unit}",
            "feels_like": f"{main.get('feels_like', 'N/A')} {temp_unit}",
            "humidity": f"{main.get('humidity', 'N/A')}%",
            "pressure": f"{main.get('pressure', 'N/A')} hPa",
            "wind_speed": f"{wind.get('speed', 'N/A')} {speed_unit}",
            "wind_direction": self._get_wind_direction(wind.get("deg")),
            "cloudiness": f"{data.get('clouds', {}).get('all', 'N/A')}%",
            "sunrise": sunrise_str,
            "sunset": sunset_str,
            "weather_id": weather.get("id"),
            "icon": weather.get("icon"),
            "success": True,
            "units": units,
            "timestamp": data.get("dt"),
            "formatted_time": datetime.datetime.fromtimestamp(data.get("dt", time.time())).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return result
    
    def _get_forecast(self, location: str, forecast_days: int, units: str) -> Dict[str, Any]:
        """Get weather forecast for a location using OpenWeatherMap API."""
        base_url = "https://api.openweathermap.org/data/2.5/forecast"
        
        params = {
            "q": location,  # Try city name first
            "appid": self.api_key,
            "units": units
        }
        
        # Detect if location is coordinates
        if "," in location and all(part.replace(".", "").replace("-", "").isdigit() for part in location.split(",")):
            lat, lon = location.split(",")
            params = {
                "lat": lat.strip(),
                "lon": lon.strip(),
                "appid": self.api_key,
                "units": units
            }
        # Detect if it's a US zip code
        elif location.strip().isdigit() and len(location.strip()) == 5:
            params = {
                "zip": location.strip(),
                "appid": self.api_key,
                "units": units
            }
        
        # Make request with retry logic
        response = None
        last_error = None
        
        for attempt in range(self.retry_attempts + 1):
            try:
                response = requests.get(base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    break
                
                elif response.status_code == 401:
                    self.has_valid_api_key = False
                    self.logger.error("Invalid API key for OpenWeatherMap")
                    self.last_api_validation = time.time()  # Update last validation time
                    raise Exception("Invalid API key for weather service")
                
                elif response.status_code == 404:
                    raise Exception(f"Location '{location}' not found")
                
                elif response.status_code == 429:
                    self.logger.warning("Rate limit exceeded for OpenWeatherMap API")
                    if attempt < self.retry_attempts:
                        sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                        self.logger.info(f"Retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                        time.sleep(sleep_time)
                        continue
                    raise Exception("Rate limit exceeded for weather service")
                
                else:
                    error_msg = f"Weather API returned status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg += f": {error_data['message']}"
                    except:
                        error_msg += f": {response.text}"
                        
                    if attempt < self.retry_attempts:
                        sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                        self.logger.warning(f"{error_msg}. Retrying in {sleep_time}s (attempt {attempt+1}/{self.retry_attempts})")
                        time.sleep(sleep_time)
                        last_error = error_msg
                        continue
                    
                    raise Exception(error_msg)
            
            except requests.exceptions.Timeout:
                self.network_error_count += 1
                self.last_network_error = time.time()
                
                if attempt < self.retry_attempts:
                    sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                    self.logger.info(f"Request timed out, retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                    time.sleep(sleep_time)
                    last_error = "Weather API request timed out"
                    continue
                raise Exception("Weather API request timed out after multiple attempts")
            
            except requests.exceptions.ConnectionError:
                self.network_error_count += 1
                self.last_network_error = time.time()
                
                if attempt < self.retry_attempts:
                    sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                    self.logger.info(f"Connection error, retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                    time.sleep(sleep_time)
                    last_error = "Connection error when accessing weather service"
                    continue
                raise Exception("Connection error when accessing weather service after multiple attempts")
        
        if not response or response.status_code != 200:
            if last_error:
                raise Exception(last_error)
            raise Exception(f"Failed to get forecast data for {location}")
        
        try:
            data = response.json()
        except ValueError:
            raise Exception("Invalid JSON response from weather service")
        
        # Determine units labels
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"
        
        # Get city information
        city = data.get("city", {})
        city_name = city.get("name", location)
        country = city.get("country", "")
        
        # Process forecast data and organize by day
        forecast_data = data.get("list", [])
        days_data = {}
        
        for item in forecast_data:
            # Convert timestamp to date
            dt = item.get("dt")
            date = datetime.datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
            
            # Extract data
            main = item.get("main", {})
            weather = item.get("weather", [{}])[0] if item.get("weather") else {}
            wind = item.get("wind", {})
            clouds = item.get("clouds", {})
            time = datetime.datetime.fromtimestamp(dt).strftime("%H:%M")
            
            # Initialize day data if not already present
            if date not in days_data:
                days_data[date] = {
                    "date": date,
                    "min_temp": float('inf'),
                    "max_temp": float('-inf'),
                    "descriptions": [],
                    "humidity": [],
                    "wind_speeds": [],
                    "timestamps": [],
                    "details": []
                }
            
            # Update day data
            day = days_data[date]
            day["min_temp"] = min(day["min_temp"], main.get("temp_min", float('inf')))
            day["max_temp"] = max(day["max_temp"], main.get("temp_max", float('-inf')))
            day["descriptions"].append(weather.get("description", ""))
            day["humidity"].append(main.get("humidity", 0))
            day["wind_speeds"].append(wind.get("speed", 0))
            day["timestamps"].append(dt)
            
            # Add detail for this time
            day["details"].append({
                "time": time,
                "temp": f"{main.get('temp', 'N/A')} {temp_unit}",
                "description": weather.get("description", "").capitalize(),
                "humidity": f"{main.get('humidity', 'N/A')}%",
                "wind": f"{wind.get('speed', 'N/A')} {speed_unit}",
                "clouds": f"{clouds.get('all', 'N/A')}%",
                "icon": weather.get("icon")
            })
        
        # Sort days and format data
        days_sorted = sorted(days_data.keys())
        forecast = []
        
        for i, date in enumerate(days_sorted):
            if i >= forecast_days:
                break
                
            day = days_data[date]
            
            # Get most common description
            descriptions = day["descriptions"]
            most_common = max(set(descriptions), key=descriptions.count)
            
            # Calculate averages
            avg_humidity = sum(day["humidity"]) / len(day["humidity"]) if day["humidity"] else 0
            avg_wind = sum(day["wind_speeds"]) / len(day["wind_speeds"]) if day["wind_speeds"] else 0
            
            # Format data
            forecast.append({
                "date": date,
                "day_name": datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                "min_temp": f"{day['min_temp']} {temp_unit}",
                "max_temp": f"{day['max_temp']} {temp_unit}",
                "description": most_common.capitalize(),
                "humidity": f"{int(avg_humidity)}%",
                "wind": f"{avg_wind:.1f} {speed_unit}",
                "details": day["details"]
            })
        
        # Build the complete result
        result = {
            "location": city_name,
            "country": country,
            "forecast_days": len(forecast),
            "units": units,
            "forecast": forecast,
            "success": True,
            "timestamp": time.time(),
            "formatted_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return result
    
    def _get_wind_direction(self, degrees: Optional[float]) -> str:
        """Convert wind direction in degrees to cardinal direction."""
        if degrees is None:
            return "Unknown"
            
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        
        # Convert degrees to one of the 16 cardinal directions
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _generate_fallback_response(self, location: str, forecast_days: int, units: str) -> Dict[str, Any]:
        """Generate a fallback response when no API key is available."""
        if forecast_days == 0:
            return {
                "location": location,
                "success": False,
                "error": "No OpenWeatherMap API key configured",
                "description": "To use this tool, please set the OPENWEATHERMAP_API_KEY environment variable.",
                "temperature": "N/A",
                "feels_like": "N/A",
                "humidity": "N/A",
                "pressure": "N/A",
                "wind_speed": "N/A",
                "wind_direction": "N/A",
                "cloudiness": "N/A",
                "sunrise": "N/A",
                "sunset": "N/A",
                "timestamp": time.time(),
                "formatted_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {
                "location": location,
                "success": False,
                "error": "No OpenWeatherMap API key configured",
                "forecast_days": forecast_days,
                "units": units,
                "forecast": [],
                "description": "To use this tool, please set the OPENWEATHERMAP_API_KEY environment variable.",
                "timestamp": time.time(),
                "formatted_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
    def get_status(self) -> Dict[str, Any]:
        """Get additional status information specific to the weather tool."""
        status = super().get_status()
        
        # Add weather-specific information
        status.update({
            "api_key_validated": self.last_api_validation is not None,
            "api_validation_age": int(time.time() - self.last_api_validation) if self.last_api_validation else None,
            "network_errors": self.network_error_count
        })
        
        if self.last_network_error:
            last_error_dt = datetime.datetime.fromtimestamp(self.last_network_error)
            status["last_network_error"] = last_error_dt.strftime("%Y-%m-%d %H:%M:%S")
            status["last_error_age"] = int(time.time() - self.last_network_error)
        
        return status 