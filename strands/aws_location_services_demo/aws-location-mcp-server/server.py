# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
# and limitations under the License.

"""Amazon Location Service MCP Server implementation using geo-places client only."""

import asyncio
import boto3
import botocore.config
import botocore.exceptions
import os
import sys
from loguru import logger
from mcp.server.fastmcp import Context
from fastmcp import FastMCP
from pydantic import Field
from typing import Dict, Optional
import httpx


# Set up logging
logger.remove()
logger.add(sys.stderr, level=os.getenv('FASTMCP_LOG_LEVEL', 'WARNING'))

# Initialize FastMCP server
mcp = FastMCP(
    'awslabs.aws-location-mcp-server',
    instructions="""
    # Amazon Location Service MCP Server (geo-places)

    This server provides tools to interact with Amazon Location Service geo-places capabilities, focusing on place search, details, and geocoding.

    ## Features
    - Search for places using text queries
    - Get place details by PlaceId
    - Reverse geocode coordinates
    - Search for places nearby a location
    - Search for places open now (extension)

    ## Prerequisites
    1. Have an AWS account with Amazon Location Service enabled
    2. Configure AWS CLI with your credentials and profile
    3. Set AWS_REGION environment variable if not using default

    ## Best Practices
    - Provide specific location details for more accurate results
    - Use the search_places tool for general search
    - Use get_place for details on a specific place
    - Use reverse_geocode for lat/lon to address
    - Use search_nearby for places near a point
    - Use search_places_open_now to find currently open places (if supported by data)
    """,
    dependencies=[
        'boto3',
        'pydantic',
    ],
)


class GeoPlacesClient:
    """Amazon Location Service geo-places client wrapper."""

    def __init__(self):
        """Initialize the Amazon geo-places client."""
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        self.geo_places_client = None
        config = botocore.config.Config(
            connect_timeout=15, read_timeout=15, retries={'max_attempts': 3}
        )
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
        try:
            if aws_access_key and aws_secret_key:
                client_args = {
                    'aws_access_key_id': aws_access_key,
                    'aws_secret_access_key': aws_secret_key,
                    'region_name': self.aws_region,
                    'config': config,
                }
                if aws_session_token:
                    client_args['aws_session_token'] = aws_session_token
                self.geo_places_client = boto3.client('geo-places', **client_args)
            else:
                self.geo_places_client = boto3.client(
                    'geo-places', region_name=self.aws_region, config=config
                )
            logger.debug(f'Amazon geo-places client initialized for region {self.aws_region}')
        except Exception as e:
            logger.error(f'Failed to initialize Amazon geo-places client: {str(e)}')
            self.geo_places_client = None


class GeoRoutesClient:
    """Amazon Location Service geo-routes client wrapper."""

    def __init__(self):
        """Initialize the Amazon geo-routes client."""
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        self.geo_routes_client = None
        config = botocore.config.Config(
            connect_timeout=15, read_timeout=15, retries={'max_attempts': 3}
        )
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
        try:
            if aws_access_key and aws_secret_key:
                client_args = {
                    'aws_access_key_id': aws_access_key,
                    'aws_secret_access_key': aws_secret_key,
                    'region_name': self.aws_region,
                    'config': config,
                }
                if aws_session_token:
                    client_args['aws_session_token'] = aws_session_token
                self.geo_routes_client = boto3.client('geo-routes', **client_args)
            else:
                self.geo_routes_client = boto3.client(
                    'geo-routes', region_name=self.aws_region, config=config
                )
            logger.debug(f'Amazon geo-routes client initialized for region {self.aws_region}')
        except Exception as e:
            logger.error(f'Failed to initialize Amazon geo-routes client: {str(e)}')
            self.geo_routes_client = None


# Initialize the geo-places client
geo_places_client = GeoPlacesClient()

# Initialize the geo-routes client
geo_routes_client = GeoRoutesClient()


@mcp.tool()
async def reverse_geocode(
    #ctx: Context,
    longitude: float = Field(description='Longitude of the location'),
    latitude: float = Field(description='Latitude of the location'),
) -> Dict:
    """Converts geographic coordinates into a human-readable address using Amazon Location Service.
    
    This tool takes a pair of coordinates (longitude and latitude) and returns detailed
    location information about that point, including:
    - Location name/title
    - Formatted street address
    - Exact coordinates
    - Place categories (e.g., residential, commercial, landmark)
    
    Input Parameters:
    - longitude: East-west position (-180 to +180 degrees)
        Examples: -122.3321 (Seattle), -74.0060 (New York)
    - latitude: North-south position (-90 to +90 degrees)
        Examples: 47.6062 (Seattle), 40.7128 (New York)
    
    Returns:
    A dictionary containing:
    - name: Location name or title
    - coordinates: Original longitude and latitude
    - categories: List of place categories
    - address: Formatted street address
    - error: Error message if the geocoding fails
    
    Example Usage:
    reverse_geocode(longitude=-122.3321, latitude=47.6062)
    
    Note: This tool is useful for converting GPS coordinates into meaningful addresses
    and location information. It's commonly used with data from GPS devices, mobile
    applications, or mapping services.
    """
    if not geo_places_client.geo_places_client:
        error_msg = 'AWS geo-places client not initialized'
        logger.error(error_msg)
        #await ctx.error(error_msg)
        return {'error': error_msg}
    logger.debug(f'Reverse geocoding for longitude: {longitude}, latitude: {latitude}')
    try:
        response = geo_places_client.geo_places_client.reverse_geocode(
            QueryPosition=[longitude, latitude]
        )
        print(f'reverse_geocode raw response: {response}')
        place = response.get('Place', {})
        if not place:
            return {'raw_response': response}
        result = {
            'name': place.get('Label') or place.get('Title', 'Unknown'),
            'coordinates': {
                'longitude': place.get('Geometry', {}).get('Point', [0, 0])[0],
                'latitude': place.get('Geometry', {}).get('Point', [0, 0])[1],
            },
            'categories': [cat.get('Name') for cat in place.get('Categories', [])],
            'address': place.get('Address', {}).get('Label', ''),
        }
        logger.debug(f'Reverse geocoded address for coordinates: {longitude}, {latitude}')
        return result
    except botocore.exceptions.ClientError as e:
        error_msg = f'AWS geo-places Service error: {str(e)}'
        logger.error(error_msg)
        #await ctx.error(error_msg)
        return {'error': error_msg}
    except Exception as e:
        error_msg = f'Error in reverse geocoding: {str(e)}'
        logger.error(error_msg)
        #await ctx.error(error_msg)
        return {'error': error_msg}


@mcp.tool()
async def search_nearby(
    #ctx: Context,
    longitude: float = Field(description='Longitude of the center point'),
    latitude: float = Field(description='Latitude of the center point'),
    max_results: int = Field(
        default=5, description='Maximum number of results to return', ge=1, le=50
    ),
    query: Optional[str] = Field(default=None, description='Optional search query'),
    radius: int = Field(default=500, description='Search radius in meters', ge=1, le=50000),
) -> Dict:
    """Finds places within a specified radius of a geographic point using Amazon Location Service.
    
    This tool searches for nearby places around a center point, automatically expanding the
    search radius if needed to find results. It returns detailed information about each
    nearby place including:
    - Place name and unique ID
    - Full address
    - Geographic coordinates
    - Distance from search point
    - Business categories
    - Contact details (phones, websites, emails, faxes)
    - Operating hours
    
    Input Parameters:
    - longitude: Center point longitude (-180 to +180)
    - latitude: Center point latitude (-90 to +90)
    - max_results: Number of places to return (default=5, max=50)
    - query: Optional text to filter results (e.g., "restaurant", "park"), convert the input to all lower case and have _ for all spaces 
    - radius: Initial search radius in meters (default=50000, max=50000)
    
    Advanced Features:
    - Automatic radius expansion if no results found (up to 10km)
    - Progressive search with 2x expansion factor
    - Standardized output format with all fields included
    
    Returns:
    A dictionary containing:
    - places: List of nearby places with detailed information
    - radius_used: The actual search radius that returned results
    - error: Error message if the search fails
    
    Example Usage:
    search_nearby(
        longitude=-122.3321,
        latitude=47.6062,
        max_results=3,
        query="coffee",
        radius=50000
    )
    
    Note: This tool is ideal for finding points of interest near a specific location,
    such as restaurants near a hotel, attractions near a landmark, or services in a
    neighborhood.
    """
    #print("In snb")
    # Moved from parameters to local variables
    max_results = 50  # Maximum number of results to return
    max_radius = 50000  # Maximum search radius in meters for expansion
    expansion_factor = 2.0  # Factor to expand radius by if no results
    mode = 'summary'  # Output mode: 'summary' (default) or 'raw' for all AWS fields
    # Descriptions:
    # max_results: Maximum number of results to return (default=5, ge=1, le=50)
    # max_radius: Maximum search radius in meters for expansion (default=10000, ge=1, le=50000)
    # expansion_factor: Factor to expand radius by if no results (default=2.0, ge=1.1, le=10.0)
    # mode: Output mode: 'summary' (default) or 'raw' for all AWS fields
    if not geo_places_client.geo_places_client:
        error_msg = 'AWS geo-places client not initialized'
        #await ctx.error(error_msg)
        return {'error': error_msg}
    try:
        current_radius = radius
        while current_radius <= max_radius:
            params = {
                'QueryPosition': [longitude, latitude],
                'MaxResults': max_results,
                'QueryRadius': int(current_radius),
                'Filter':{
                    "IncludeCategories" : [query]
                } 
            }
            print(params)
            response = geo_places_client.geo_places_client.search_nearby(**params)
            items = response.get('ResultItems', [])
            results = []
            for item in items:
                if mode == 'raw':
                    results.append(item)
                else:
                    contacts = {
                        'phones': [p['Value'] for p in item.get('Contacts', {}).get('Phones', [])]
                        if item.get('Contacts')
                        else [],
                        'websites': [
                            w['Value'] for w in item.get('Contacts', {}).get('Websites', [])
                        ]
                        if item.get('Contacts')
                        else [],
                        'emails': [e['Value'] for e in item.get('Contacts', {}).get('Emails', [])]
                        if item.get('Contacts')
                        else [],
                        'faxes': [f['Value'] for f in item.get('Contacts', {}).get('Faxes', [])]
                        if item.get('Contacts')
                        else [],
                    }

                    def parse_opening_hours(result):
                        oh = result.get('OpeningHours')
                        if not oh:
                            contacts = result.get('Contacts', {})
                            oh = contacts.get('OpeningHours') if contacts else None
                        if not oh:
                            return []
                        if isinstance(oh, dict):
                            oh = [oh]
                        parsed = []
                        for entry in oh:
                            parsed.append(
                                {
                                    'display': entry.get('Display', [])
                                    or entry.get('display', []),
                                    'components': entry.get('Components', [])
                                    or entry.get('components', []),
                                    'open_now': entry.get('OpenNow', None),
                                    'categories': [
                                        cat.get('Name') for cat in entry.get('Categories', [])
                                    ]
                                    if 'Categories' in entry
                                    else [],
                                }
                            )
                        return parsed

                    opening_hours = parse_opening_hours(item)
                    results.append(
                        {
                            'place_id': item.get('PlaceId', 'Not available'),
                            'name': item.get('Title', 'Not available'),
                            'address': item.get('Address', {}).get('Label', 'Not available'),
                            'coordinates': {
                                'longitude': item.get('Position', [None, None])[0],
                                'latitude': item.get('Position', [None, None])[1],
                            },
                            'categories': [cat.get('Name') for cat in item.get('Categories', [])]
                            if item.get('Categories')
                            else [],
                            'contacts': contacts,
                            'opening_hours': opening_hours,
                        }
                    )
            if results:
                #print(results)
                return {'places': results, 'radius_used': current_radius}
            current_radius *= expansion_factor
        return {'places': [], 'radius_used': current_radius / expansion_factor}
    except Exception as e:
        print(f'search_nearby error: {e}')
        #await ctx.error(f'search_nearby error: {e}')
        return {'error': str(e)}


@mcp.tool()
async def calculate_route(
    #ctx: Context,
    departure_position: list = Field(description='Departure position as [longitude, latitude]'),
    destination_position: list = Field(
        description='Destination position as [longitude, latitude]'
    ),
    travel_mode: str = Field(
        default='Car',
        description="Travel mode: 'Car', 'Truck', 'Walking', or 'Bicycle' (default: 'Car')",
    ),
    optimize_for: str = Field(
        default='FastestRoute',
        description="Optimize route for 'FastestRoute' or 'ShortestRoute' (default: 'FastestRoute')",
    ),
) -> dict:
    """Calculates a detailed route between two points using Amazon Location Service.
    
    This tool provides turn-by-turn navigation directions between any two points,
    supporting multiple transportation modes and optimization preferences.
    
    Input Parameters:
    - departure_position: Starting point coordinates as [longitude, latitude]
        Example: [-122.3321, 47.6062] for Seattle
    - destination_position: Ending point coordinates as [longitude, latitude]
        Example: [-122.3465, 47.6171] for Space Needle
    - travel_mode: Method of transportation:
        * 'Car' (default) - Standard automobile routing
        * 'Truck' - Commercial vehicle routing
        * 'Walking' - Pedestrian-friendly paths
        * 'Bicycle' - Bike-friendly routes
    - optimize_for: Route optimization preference:
        * 'FastestRoute' (default) - Minimizes travel time
        * 'ShortestRoute' - Minimizes distance traveled
    
    Returns:
    A dictionary containing:
    - distance_meters: Total route distance in meters
    - duration_seconds: Estimated travel time in seconds
    - turn_by_turn: List of navigation steps, each including:
        * Distance for this step
        * Duration for this step
        * Type of maneuver
        * Road name
    - error: Error message if route calculation fails
    
    Example Usage:
    calculate_route(
        departure_position=[-122.3321, 47.6062],
        destination_position=[-122.3465, 47.6171],
        travel_mode="Car",
        optimize_for="FastestRoute"
    )
    """
    include_leg_geometry = False
    mode = 'summary'
    client = GeoRoutesClient().geo_routes_client

    # Check if client is None before proceeding
    if client is None:
        return {'error': 'Failed to initialize Amazon geo-routes client'}

    params = {
        'Origin': departure_position,
        'Destination': destination_position,
        'TravelMode': travel_mode,
        'TravelStepType': 'TurnByTurn',
        'OptimizeRoutingFor': optimize_for,
    }
    if include_leg_geometry:
        params['LegGeometryFormat'] = 'FlexiblePolyline'
    try:
        response = await asyncio.to_thread(client.calculate_routes, **params)
        if mode == 'raw':
            return response
        routes = response.get('Routes', [])
        if not routes:
            return {'error': 'No route found'}
        route = routes[0]
        distance_meters = route.get('Distance', None)
        duration_seconds = route.get('DurationSeconds', None)
        turn_by_turn = []
        for leg in route.get('Legs', []):
            vehicle_leg_details = leg.get('VehicleLegDetails', {})
            for step in vehicle_leg_details.get('TravelSteps', []):
                step_summary = {
                    'distance_meters': step.get('Distance'),
                    'duration_seconds': step.get('Duration'),
                    'type': step.get('Type'),
                    'road_name': step.get('NextRoad', {}).get('RoadName')
                    if step.get('NextRoad')
                    else None,
                }
                turn_by_turn.append(step_summary)
        return {
            'distance_meters': distance_meters,
            'duration_seconds': duration_seconds,
            'turn_by_turn': turn_by_turn,
        }
    except Exception as e:
        return {'error': str(e)}


def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
