from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import googlemaps
from dotenv import load_dotenv
import os
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from datetime import datetime
import random

load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Initialize mapping clients based on MODE
MAP_MODE = os.getenv("MAP_MODE", "osm")
if MAP_MODE == "google":
    gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
else:
    geolocator = Nominatim(user_agent="route_planner")

@app.route('/')
def index():
    return render_template('index.html', 
                         map_mode=MAP_MODE,
                         google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"))

@app.route('/plan_route', methods=['POST'])
def plan_route():
    user_request = request.json.get('request')
    location = request.json.get('location')

    try:
        # Use LLM to understand the request and extract key information
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Route Planner",
            },
            model="openai/gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Extract route information and return ONLY a JSON object with these exact fields: total_distance_km (number), stop_type (string), stop_at_km (number). For example: {\"total_distance_km\": 10.0, \"stop_type\": \"bar\", \"stop_at_km\": 5.0}"
                },
                {
                    "role": "user",
                    "content": user_request
                }
            ]
        )

        # Parse LLM response with default values
        try:
            route_requirements = json.loads(completion.choices[0].message.content)
            # Ensure all required fields exist with proper types
            route_requirements = {
                'total_distance_km': float(route_requirements.get('total_distance_km', 10.0)),
                'stop_type': str(route_requirements.get('stop_type', 'bar')),
                'stop_at_km': float(route_requirements.get('stop_at_km', 5.0))
            }
        except (json.JSONDecodeError, ValueError, TypeError, KeyError):
            # If parsing fails, use default values
            route_requirements = {
                'total_distance_km': 10.0,
                'stop_type': 'bar',
                'stop_at_km': 5.0
            }

        if MAP_MODE == "google":
            return handle_google_maps_route(location, route_requirements)
        else:
            return handle_osm_route(location, route_requirements)
            
    except Exception as e:
        return jsonify({
            'error': str(e),
            'route': [],
            'stops': [],
            'map_mode': MAP_MODE
        }), 500

def handle_google_maps_route(location, route_requirements):
    # Use Google Maps to find points of interest
    places_result = gmaps.places_nearby(
        location=location,
        radius=2000,
        keyword=route_requirements.get('stop_type', 'bar')
    )

    # Calculate route with waypoints
    directions_result = gmaps.directions(
        origin=location,
        destination=location,
        waypoints=[place['geometry']['location'] for place in places_result['results'][:1]],
        mode="bicycling"
    )

    return jsonify({
        'route': directions_result,
        'stops': places_result['results'][:1],
        'map_mode': 'google'
    })

def handle_osm_route(location, route_requirements):
    try:
        # For OSM, we'll create a varied route with waypoints
        lat, lng = location['lat'], location['lng']
        
        # Values are already converted to float in plan_route
        total_distance = max(route_requirements['total_distance_km'], 0.5)  # Minimum 0.5km
        stop_at = min(route_requirements['stop_at_km'], total_distance)  # Ensure stop is not beyond total distance
        
        # Create waypoints for a varied route starting from the selected point
        points = generate_varied_route(lat, lng, total_distance)
        
        # Calculate stop point based on stop_at distance
        stop_index = min(int((stop_at / total_distance) * len(points)), len(points) - 1)
        stop_point = points[stop_index]
        
        # Add timestamp to stop name for uniqueness
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        return jsonify({
            'route': points,
            'stops': [{
                'geometry': {
                    'location': {'lat': stop_point[0], 'lng': stop_point[1]},
                },
                'name': f"Suggested {route_requirements['stop_type']} ({timestamp})"
            }],
            'map_mode': 'osm'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'route': [],
            'stops': [],
            'map_mode': 'osm'
        }), 500

def generate_varied_route(lat, lng, total_distance_km, num_points=40):
    """Generate a varied route with different shapes based on distance"""
    import math
    
    # Prevent division by zero and very small numbers that could cause issues
    if abs(math.cos(math.radians(lat))) < 0.01:
        lat_factor = 111.32  # km per degree at equator
    else:
        lat_factor = 111.32 * math.cos(math.radians(lat))
    
    points = []
    # Base radius in kilometers (minimum 0.1 km to prevent too small routes)
    base_radius = max(total_distance_km / (2 * math.pi), 0.1)
    
    # Choose a route type based on distance
    if total_distance_km <= 5:
        # Short routes: Create a figure-8 pattern
        for i in range(num_points):
            angle = (i / num_points) * 4 * math.pi
            r = base_radius * math.sin(angle/2)
            dlat = r * math.cos(angle) / 111.32
            dlng = r * math.sin(angle) / lat_factor
            points.append([lat + dlat, lng + dlng])
    
    elif total_distance_km <= 10:
        # Medium routes: Create a cloverleaf pattern
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            r = base_radius * (1 + 0.5 * math.sin(2 * angle))
            dlat = r * math.cos(angle) / 111.32
            dlng = r * math.sin(angle) / lat_factor
            points.append([lat + dlat, lng + dlng])
    
    else:
        # Longer routes: Create a more complex pattern with random variations
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            # Add some random variation to the radius
            variation = random.uniform(0.8, 1.2)
            r = base_radius * variation * (1 + 0.3 * math.sin(3 * angle))
            dlat = r * math.cos(angle) / 111.32
            dlng = r * math.sin(angle) / lat_factor
            points.append([lat + dlat, lng + dlng])
    
    # Ensure the route is closed by adding the first point at the end
    if points:
        points.append(points[0])
    
    # Smooth the route
    smoothed_points = []
    window_size = 3
    for i in range(len(points)):
        # Calculate average of nearby points
        window_start = max(0, i - window_size)
        window_end = min(len(points), i + window_size + 1)
        window_points = points[window_start:window_end]
        avg_lat = sum(p[0] for p in window_points) / len(window_points)
        avg_lng = sum(p[1] for p in window_points) / len(window_points)
        smoothed_points.append([avg_lat, avg_lng])
    
    return smoothed_points

if __name__ == '__main__':
    app.run(debug=True) 