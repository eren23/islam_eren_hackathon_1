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
import overpy
import requests
import math

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

# Add this after other initializations
overpass_api = overpy.Overpass()

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
            model="openai/gpt-4.1",
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
        lat, lng = location['lat'], location['lng']
        total_distance = max(route_requirements['total_distance_km'], 0.5)
        stop_at = min(route_requirements['stop_at_km'], total_distance)
        
        # Find nearby roads that are suitable for cycling
        radius = total_distance * 1000  # Convert to meters
        query = f"""
        [out:json];
        (
          way["highway"~"^(primary|secondary|tertiary|residential|cycleway|path)$"]
              (around:{radius},{lat},{lng});
        );
        out body;
        >;
        out skel qt;
        """
        
        # Find potential stops (bars, cafes, etc.)
        stop_query = f"""
        [out:json];
        (
          node["amenity"="{route_requirements['stop_type']}"](around:{radius},{lat},{lng});
        );
        out body;
        """
        
        try:
            # Get roads
            roads_result = overpass_api.query(query)
            
            # Get stops
            stops_result = overpass_api.query(stop_query)
            
            if not roads_result.ways:
                raise Exception("No suitable roads found in the area")
            
            # Create a route using the available roads
            route_points = create_route_from_roads(
                roads_result.ways,
                (lat, lng),
                total_distance,
                stops_result.nodes
            )
            
            # Find the best stop point
            stop_point = find_best_stop(
                route_points,
                stops_result.nodes,
                stop_at,
                total_distance
            )
            
            return jsonify({
                'route': route_points,
                'stops': [{
                    'geometry': {
                        'location': {
                            'lat': float(stop_point.lat),
                            'lng': float(stop_point.lon)
                        },
                    },
                    'name': f"{getattr(stop_point, 'tags', {}).get('name', 'Unnamed')} ({route_requirements['stop_type']})"
                }],
                'map_mode': 'osm'
            })
            
        except Exception as e:
            # Fallback to simplified route if OpenStreetMap data fetch fails
            print(f"OpenStreetMap data fetch failed: {str(e)}")
            return create_simplified_route(lat, lng, total_distance, stop_at, route_requirements)
            
    except Exception as e:
        return jsonify({
            'error': str(e),
            'route': [],
            'stops': [],
            'map_mode': 'osm'
        }), 500

def create_route_from_roads(ways, start_point, target_distance, possible_stops):
    """Create a route using actual roads"""
    route_points = []
    start_lat, start_lng = start_point
    
    # Find the closest way to start point
    closest_way = min(ways, key=lambda w: min(
        geodesic(start_point, (float(n.lat), float(n.lon))).kilometers 
        for n in w.nodes
    ))
    
    # Start building the route
    current_distance = 0
    used_ways = set()
    current_way = closest_way
    
    while current_distance < target_distance:
        way_points = [(float(n.lat), float(n.lon)) for n in current_way.nodes]
        route_points.extend(way_points)
        used_ways.add(current_way.id)
        
        # Calculate current distance
        for i in range(len(way_points)-1):
            current_distance += geodesic(way_points[i], way_points[i+1]).kilometers
        
        # Find connected way that leads roughly in the right direction
        connected_ways = [
            w for w in ways 
            if w.id not in used_ways and 
            any(n.id == current_way.nodes[0].id or n.id == current_way.nodes[-1].id for n in w.nodes)
        ]
        
        if not connected_ways:
            break
            
        # Choose the next way that leads most towards the start point
        current_way = min(connected_ways, key=lambda w: 
            geodesic((float(w.nodes[0].lat), float(w.nodes[0].lon)), start_point).kilometers
        )
    
    # Close the route by connecting back to start if possible
    if route_points:
        route_points.append((start_lat, start_lng))
    
    return [[lat, lng] for lat, lng in route_points]

def find_best_stop(route_points, possible_stops, target_distance, total_distance):
    """Find the best stop point near the desired distance"""
    if not possible_stops:
        # If no stops found, create a virtual one
        target_index = int(len(route_points) * (target_distance / total_distance))
        target_point = route_points[min(target_index, len(route_points) - 1)]
        return type('VirtualStop', (), {
            'lat': str(target_point[0]),
            'lon': str(target_point[1]),
            'tags': {'name': 'Suggested Stop'}
        })
    
    # Calculate distance along route to each point
    target_point = route_points[int(len(route_points) * (target_distance / total_distance))]
    
    # Find the closest actual stop to the target point
    best_stop = min(possible_stops, key=lambda stop: 
        geodesic((float(stop.lat), float(stop.lon)), target_point).kilometers
    )
    
    return best_stop

def create_simplified_route(lat, lng, total_distance, stop_at, route_requirements):
    """Fallback to simplified route if real roads can't be found"""
    points = generate_varied_route(lat, lng, total_distance)
    
    # Calculate stop point based on stop_at distance
    stop_index = int((stop_at / total_distance) * len(points))
    stop_point = points[min(stop_index, len(points) - 1)]
    
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

if __name__ == '__main__':
    app.run(debug=True) 