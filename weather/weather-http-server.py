from typing import Any
import httpx
import logging
import os
from datetime import datetime
from fastmcp import FastMCP

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create log file with timestamp
log_file = os.path.join(log_dir, f'weather_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # This will also show logs in console
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error making request to NWS API: {str(e)}")
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    logger.info(f"Fetching alerts for state: {state}")
    data = await make_nws_request(url)

    if not data or "features" not in data:
        logger.warning(f"No alerts data found for state: {state}")
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        logger.info(f"No active alerts for state: {state}")
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    logger.info(f"Found {len(alerts)} alerts for state: {state}")
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    logger.info(f"Getting forecast for coordinates: lat={latitude}, lon={longitude}")

    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        logger.error(f"Failed to fetch points data for coordinates: {latitude},{longitude}")
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    logger.debug(f"Fetching forecast from URL: {forecast_url}")
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        logger.error("Failed to fetch detailed forecast data")
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    logger.info(f"Successfully retrieved forecast with {len(forecasts)} periods")
    return "\n---\n".join(forecasts)


@mcp.tool()
async def easter_egg() -> str:
    """easter egg function in the server that answers to the prompt timbuktu 
    """
    print("hello")
    return """Fun fact: The actual Timbuktu in Mali was so legendary for being remote that Europeans didn't believe it existed for centuries. When they finally found it, they probably felt like someone who finally discovers that their parents weren't just making up that ice cream shop they kept talking about. Though I bet the residents of Timbuktu are pretty tired of being everyone's go-to reference for "middle of nowhere" when they've got this amazing historical city with centuries-old libraries and architecture. It's like their city is the geographical equivalent of "I walked to school uphill both ways!"""


if __name__ == "__main__":
    # Initialize and run the server
    logger.info("Starting weather service")
    mcp.run()
