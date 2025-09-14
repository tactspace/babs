import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

# Load API key from environment variable (.env supported)
# Expected: set TOMTOM_APIKEY (or TOMTOM_API_KEY) to your TomTom key
TOMTOM_API_KEY = "Nyl0u6F6ObfkryIqEr3QpvQuHkniwMDT"

def get_route(start_point, end_point, vehicle_type="truck", route_type: str = "fastest"):
    """
    Get route data between two points using TomTom Routing API
    
    Args:
        start_point (tuple): Starting point coordinates as (latitude, longitude)
        end_point (tuple): Ending point coordinates as (latitude, longitude)
        vehicle_type (str): Vehicle type (car, truck, etc.)
        
    Returns:
        dict: Route data including distance, duration, and coordinates
    """
    if not TOMTOM_API_KEY:
        raise ValueError("TomTom API key not found. Set the TOMTOM_APIKEY environment variable.")
        
    # Format coordinates for API request
    start_coord = f"{start_point[0]},{start_point[1]}"
    end_coord = f"{end_point[0]},{end_point[1]}"
    
    # Build API URL
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    url = f"{base_url}/{start_coord}:{end_coord}/json"
    
    # Set query parameters
    params = {
        "key": TOMTOM_API_KEY,
        # "vehicleType": vehicle_type,
        "traffic": "true",
        "routeType": route_type,
        "travelMode": "truck",
        "vehicleMaxSpeed": 70,  # km/h, typical for trucks
        # "vehicleWeight": 40000,  # kg, for heavy-duty trucks
        # "vehicleAxleWeight": 11000,  # kg
        # "vehicleLength": 16.5,  # meters
        # "vehicleWidth": 2.55,  # meters
        # "vehicleHeight": 4,  # meters
        # "departAt": "now",
        # "sectionType": "travelTimes,travelCosts,traffic,summary",
        "computeBestOrder": "true",
        # "instructionsType": "text"
    }
    
    try:
        # Make API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse and return route data
        route_data = response.json()
        
        # Extract useful information
        if "routes" in route_data and len(route_data["routes"]) > 0:
            result = {
                "distance": route_data["routes"][0]["summary"]["lengthInMeters"],
                "duration": route_data["routes"][0]["summary"]["travelTimeInSeconds"],
                "coordinates": route_data["routes"][0]["legs"][0]["points"],
                "full_response": route_data  # Include full response for additional data if needed
            }
            return result
        else:
            print("No routes found in the response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching route data: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing response data: {e}")
        return None

# For electric vehicles, we can use a specialized function
def get_ev_route(start_point, end_point, current_charge_kWh, max_charge_kWh, consumption_kWh_per_100km):
    """
    Get route data for electric vehicles between two points using TomTom Long Distance EV Routing API
    
    Args:
        start_point (tuple): Starting point coordinates as (latitude, longitude)
        end_point (tuple): Ending point coordinates as (latitude, longitude)
        current_charge_kWh (float): Current battery charge in kWh
        max_charge_kWh (float): Maximum battery capacity in kWh
        consumption_kWh_per_100km (float): Energy consumption in kWh per 100km
        
    Returns:
        dict: Route data including distance, duration, charging stops and coordinates
    """
    if not TOMTOM_API_KEY:
        raise ValueError("TomTom API key not found. Set TOMTOM_APIKEY in your environment or .env file.")
        
    # Format coordinates for API request
    start_coord = f"{start_point[0]},{start_point[1]}"
    end_coord = f"{end_point[0]},{end_point[1]}"
    
    # Build API URL for Long Distance EV Routing
    base_url = "https://api.tomtom.com/routing/1/calculateLongDistanceEVRoute"
    url = f"{base_url}/{start_coord}:{end_coord}/json"
    
    # Set consumption rate at different speeds (example values)
    # Format: "speed1,consumption1:speed2,consumption2:..."
    # Speed in km/h, consumption in kWh per 100km
    # Adjust these values based on the truck's actual consumption profile
    speed_consumption = f"50,{consumption_kWh_per_100km}:80,{consumption_kWh_per_100km*1.2}"
    
    # Set query parameters
    params = {
        "key": TOMTOM_API_KEY,
        "vehicleEngineType": "electric",
        "constantSpeedConsumptionInkWhPerHundredkm": speed_consumption,
        "currentChargeInkWh": current_charge_kWh,
        "maxChargeInkWh": max_charge_kWh,
        "minChargeAtDestinationInkWh": max_charge_kWh * 0.1,  # 10% of max charge
        "minChargeAtChargingStopsInkWh": max_charge_kWh * 0.1,  # 10% of max charge
        "vehicleType": "truck",
        "vehicleWeight": 40000,  # kg, for heavy-duty trucks
        "departAt": "now"
    }
    
    try:
        # Make API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse and return route data
        route_data = response.json()
        
        # Extract useful information
        if "routes" in route_data and len(route_data["routes"]) > 0:
            result = {
                "distance": route_data["routes"][0]["summary"]["lengthInMeters"],
                "duration": route_data["routes"][0]["summary"]["travelTimeInSeconds"],
                "coordinates": route_data["routes"][0]["legs"][0]["points"],
                "charging_stops": route_data["routes"][0].get("chargingStops", []),
                "full_response": route_data  # Include full response for additional data if needed
            }
            return result
        else:
            print("No routes found in the response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching EV route data: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing EV response data: {e}")
        return None

# Example usage (commented out)

# For regular truck routing
# start = (52.5200, 13.4050)  # Berlin coordinates
# end = (48.8566, 2.3522)     # Paris coordinates
# route = get_route(start, end, vehicle_type="truck")
# # Export route to json file
# with open('route.json', 'w') as f:
#     json.dump(route["full_response"], f)
# if route:
#     print(f"Distance: {route['distance']/1000:.2f} km")
#     print(f"Duration: {route['duration']/60:.2f} minutes")

# # For EV truck routing
# ev_route = get_ev_route(
#     start_point=start, 
#     end_point=end, 
#     current_charge_kWh=400, 
#     max_charge_kWh=600, 
#     consumption_kWh_per_100km=120
# )
# if ev_route:
#     print(f"EV Distance: {ev_route['distance']/1000:.2f} km")
#     print(f"EV Duration: {ev_route['duration']/60:.2f} minutes")
#     print(f"Charging stops: {len(ev_route['charging_stops'])}")

