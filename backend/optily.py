from models import SingleRouteRequest, SingleRouteResponse, ChargingStation, TruckModel
from charging_stations import load_charging_stations
from tomtom import get_route
from typing import List, Optional, Dict, Tuple
from trucks import load_truck_specs, calculate_energy_consumption, calculate_max_range
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def plan_route(request: SingleRouteRequest, truck_model: str = None, starting_battery_kwh: float = None) -> SingleRouteResponse:
    """
    Custom route planner that plans routes between two points with truck capacity and cost calculations.
    
    Args:
        request: SingleRouteRequest object containing start/end coordinates and optional route name
        truck_model: Name of the truck model to use for calculations (optional)
        starting_battery_kwh: Starting battery charge in kWh (optional, defaults to full battery)
        
    Returns:
        SingleRouteResponse object with route details including capacity and cost information
    """
    try:
        # Load data
        charging_stations = load_charging_stations("data/public_charge_points.csv")
        trucks = load_truck_specs("data/truck_specs.csv")
        
        # Validate data
        if not charging_stations:
            return _create_error_response(request, "No charging stations found")
        
        if not trucks:
            return _create_error_response(request, "No truck specifications found")
        
        # Select truck
        if truck_model is None:
            truck_model = list(trucks.keys())[0]
        
        if truck_model not in trucks:
            return _create_error_response(request, f"Truck model '{truck_model}' not found")
        
        truck = trucks[truck_model]
        
        # Set starting battery charge
        if starting_battery_kwh is None:
            starting_battery_kwh = truck.battery_capacity
        else:
            starting_battery_kwh = min(starting_battery_kwh, truck.battery_capacity)
        
        # Plan route (handles both direct and segmented routes)
        return _plan_segmented_route(request, truck, charging_stations, starting_battery_kwh)
            
    except Exception as e:
        return _create_error_response(request, f"Unexpected error: {str(e)}")


def _plan_segmented_route(request: SingleRouteRequest, truck: TruckModel, charging_stations: List[ChargingStation], starting_battery_kwh: float) -> SingleRouteResponse:
    """
    Plan route in segments with charging stops when battery gets low (~20%)
    
    Args:
        request: Route request
        truck: Truck model
        charging_stations: Available charging stations
        starting_battery_kwh: Starting battery level
        
    Returns:
        SingleRouteResponse with segmented route details
    """
    LOW_BATTERY_THRESHOLD = 0.20  # 20% of battery capacity
    MIN_BATTERY_RESERVE = truck.battery_capacity * LOW_BATTERY_THRESHOLD
    
    route_segments = []
    charging_stops = []
    total_costs = {
        "driver_cost": 0,
        "energy_cost": 0,
        "depreciation_cost": 0,
        "tolls_cost": 0,
        "total_cost": 0,
        "charging_cost": 0
    }
    
    current_battery = starting_battery_kwh
    current_position = (request.start_lat, request.start_lng)
    destination = (request.end_lat, request.end_lng)
    
    # Get the original route coordinates once for the entire journey
    original_route_data = get_route(current_position, destination, vehicle_type="truck", route_type="fastest")
    if not original_route_data:
        return _create_error_response(request, "Failed to get original route from TomTom API")
    
    route_coordinates = [
        {"latitude": point["latitude"], "longitude": point["longitude"]}
        for point in original_route_data["coordinates"]
    ]
    
    segment_count = 0
    
    while True:
        segment_count += 1
        
        # Check if we can reach destination directly
        direct_distance = _get_route_distance(current_position, destination)
        if direct_distance > 0:
            energy_needed = calculate_energy_consumption(direct_distance, truck)
            
            if current_battery >= energy_needed:
                # Can reach destination directly
                segment = _create_route_segment(current_position, destination, truck)
                if segment:
                    route_segments.append(segment)
                    _add_segment_costs(segment, total_costs)
                    logger.info(f"Direct route is possible. Found segment {len(route_segments)}")
                break
        
        # Need to find charging station using route-based heuristics
        max_range = calculate_max_range(truck, current_battery)
        charging_station = _find_best_charging_station(
            current_position, destination, charging_stations, max_range, route_coordinates
        )
        
        if not charging_station:
            return _create_error_response(request, f"No suitable charging station found for segment {segment_count}")
        
        # Create segment to charging station
        charging_position = (charging_station.latitude, charging_station.longitude)
        segment = _create_route_segment(current_position, charging_position, truck)
        
        if not segment:
            return _create_error_response(request, f"Failed to create route segment {segment_count}")
        
        route_segments.append(segment)
        _add_segment_costs(segment, total_costs)
        
        # Add charging stop
        charging_stop = {
            "station": charging_station,
            "segment": segment_count,
            "arrival_battery": current_battery - segment["energy_consumption"],
            "charging_time_hours": 1.0,  # Assume 1 hour charging
            "charging_cost": _calculate_charging_cost(charging_station, truck.battery_capacity * 0.8)  # Charge to 80%
        }
        charging_stops.append(charging_stop)
        
        # Add charging costs
        total_costs["charging_cost"] += charging_stop["charging_cost"]
        total_costs["driver_cost"] += 35.0 * charging_stop["charging_time_hours"]  # Driver waiting time
        
        # Update current position and battery
        current_position = charging_position
        current_battery = truck.battery_capacity * 0.8  # Charge to 80%
        
        print(f"Segment {segment_count}: {segment['distance_km']:.1f}km, "
              f"Energy used: {segment['energy_consumption']:.1f}kWh, "
              f"Charging at: {charging_station.operator_name}")
    
    # Combine all coordinates from segments
    all_coordinates = []
    total_distance = 0
    total_duration = 0
    
    for segment in route_segments:
        all_coordinates.extend(segment["coordinates"])
        total_distance += segment["distance_km"]
        total_duration += segment["duration_minutes"]
    
    # Create success message
    message = _create_segmented_success_message(truck, route_segments, total_costs, charging_stops)
    
    return SingleRouteResponse(
        distance_km=total_distance,
        route_name=request.route_name or f"{truck.manufacturer} {truck.model} Segmented Route",
        duration_minutes=total_duration,
        coordinates=all_coordinates,
        success=True,
        message=message
    )


def _find_best_charging_station(current_position: Tuple[float, float], destination: Tuple[float, float], 
                               charging_stations: List[ChargingStation], max_range: float, route_coordinates: List[Dict] = None) -> Optional[ChargingStation]:
    """
    Find the best charging station within range using route-based heuristics
    """
    best_station = None
    best_score = float('inf')
    
    if route_coordinates:
        # Use route-based filtering for much faster performance
        candidate_stations = _find_stations_along_route(current_position, destination, charging_stations, max_range, route_coordinates)
    else:
        # Fallback to old method if no route coordinates provided
        candidate_stations = _find_stations_in_range_old_method(current_position, charging_stations, max_range)
    
    print(f"Checking {len(candidate_stations)} candidate charging stations...")
    
    for station in candidate_stations:
        # Get accurate distance using TomTom API
        route_to_station = _get_route_distance(current_position, (station.latitude, station.longitude))
        
        if route_to_station and route_to_station <= max_range:
            # Calculate score: prefer stations closer to destination
            route_to_destination = _get_route_distance((station.latitude, station.longitude), destination)
            
            if route_to_destination:
                # Score based on distance to destination (lower is better)
                score = route_to_destination
                
                if score < best_score:
                    best_score = score
                    best_station = station
                    print(f"Found better station: {station.operator_name} "
                          f"(distance to station: {route_to_station:.1f}km, "
                          f"distance to destination: {score:.1f}km)")
    
    if best_station:
        print(f"Selected charging station: {best_station.operator_name}")
    else:
        print("No suitable charging station found within range")
    
    return best_station


def _find_stations_along_route(current_position: Tuple[float, float], destination: Tuple[float, float], 
                              charging_stations: List[ChargingStation], max_range: float, route_coordinates: List[Dict]) -> List[ChargingStation]:
    """
    Find charging stations that are within 10km of the planned route
    """
    DETOUR_RANGE_KM = 10.0  # 10km detour range
    candidate_stations = []
    
    # Calculate current position index in route coordinates
    current_index = _find_closest_route_point(current_position, route_coordinates)
    
    # Only check stations that are ahead of current position
    relevant_coordinates = route_coordinates[current_index:]
    
    print(f"Checking stations along route from position {current_index}/{len(route_coordinates)}")
    
    for station in charging_stations:
        # Quick check: is station within 10km of any point on the route?
        min_distance_to_route = _min_distance_to_route_segment(station, relevant_coordinates)
        
        if min_distance_to_route <= DETOUR_RANGE_KM:
            # Additional check: is station reachable with current battery?
            rough_distance_to_station = _rough_distance_estimate(current_position, (station.latitude, station.longitude))
            
            if rough_distance_to_station <= max_range:
                candidate_stations.append(station)
                print(f"Station {station.operator_name} is {min_distance_to_route:.1f}km from route")
    
    return candidate_stations


def _find_closest_route_point(position: Tuple[float, float], route_coordinates: List[Dict]) -> int:
    """
    Find the index of the route coordinate closest to current position
    """
    min_distance = float('inf')
    closest_index = 0
    
    for i, coord in enumerate(route_coordinates):
        distance = _rough_distance_estimate(position, (coord['latitude'], coord['longitude']))
        if distance < min_distance:
            min_distance = distance
            closest_index = i
    
    return closest_index


def _min_distance_to_route_segment(station: ChargingStation, route_coordinates: List[Dict]) -> float:
    """
    Calculate minimum distance from station to any point on the route segment
    """
    min_distance = float('inf')
    station_pos = (station.latitude, station.longitude)
    
    for coord in route_coordinates:
        distance = _rough_distance_estimate(station_pos, (coord['latitude'], coord['longitude']))
        if distance < min_distance:
            min_distance = distance
    
    return min_distance


def _find_stations_in_range_old_method(current_position: Tuple[float, float], charging_stations: List[ChargingStation], max_range: float) -> List[ChargingStation]:
    """
    Fallback method: find stations within range using old approach
    """
    candidate_stations = []
    distance_margin_km = 10
    
    for station in charging_stations:
        rough_distance = _rough_distance_estimate(current_position, (station.latitude, station.longitude)) + distance_margin_km
        if rough_distance <= max_range:  
            candidate_stations.append(station)
    
    return candidate_stations


def _get_route_distance(start_point: Tuple[float, float], end_point: Tuple[float, float]) -> float:
    """
    Get route distance using TomTom API
    
    Args:
        start_point: Starting coordinates (lat, lng)
        end_point: Ending coordinates (lat, lng)
        
    Returns:
        Distance in kilometers, or 0 if failed
    """
    try:
        route_data = get_route(start_point, end_point, vehicle_type="truck", route_type="fastest")
        
        if route_data:
            return route_data["distance"] / 1000
        return 0.0
        
    except Exception as e:
        print(f"Error getting route distance: {e}")
        return 0.0


def _rough_distance_estimate(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Rough distance estimate for filtering (not for final calculations)
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Rough conversion: 1 degree ≈ 111 km
    lat_diff = (lat2 - lat1) * 111
    lon_diff = (lon2 - lon1) * 111 * 0.7  # Adjust for longitude at European latitudes
    
    return (lat_diff**2 + lon_diff**2)**0.5


def _create_route_segment(start_point: Tuple[float, float], end_point: Tuple[float, float], truck: TruckModel) -> Optional[Dict]:
    """
    Create a route segment between two points using TomTom API
    """
    try:
        route_data = get_route(start_point, end_point, vehicle_type="truck", route_type="fastest")
        
        if not route_data:
            return None
        
        coordinates = [
            {"latitude": point["latitude"], "longitude": point["longitude"]}
            for point in route_data["coordinates"]
        ]
        
        distance_km = route_data["distance"] / 1000
        duration_minutes = route_data["duration"] / 60
        energy_consumption = calculate_energy_consumption(distance_km, truck)
        
        return {
            "coordinates": coordinates,
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "energy_consumption": energy_consumption,
            "start_point": start_point,
            "end_point": end_point
        }
        
    except Exception as e:
        print(f"Error creating route segment: {e}")
        return None


def _add_segment_costs(segment: Dict, total_costs: Dict[str, float]):
    """Add segment costs to total costs"""
    duration_hours = segment["duration_minutes"] / 60
    distance_km = segment["distance_km"]
    energy_consumption = segment["energy_consumption"]
    
    # Cost parameters
    DRIVER_HOURLY_PAY = 35.0
    ENERGY_COST_PER_KWH = 0.39
    DEPRECIATION_PER_KM = 0.05
    TOLLS_PER_KM = 0.00
    
    total_costs["driver_cost"] += DRIVER_HOURLY_PAY * duration_hours
    total_costs["energy_cost"] += ENERGY_COST_PER_KWH * energy_consumption
    total_costs["depreciation_cost"] += DEPRECIATION_PER_KM * distance_km
    total_costs["tolls_cost"] += TOLLS_PER_KM * distance_km


def _calculate_charging_cost(station: ChargingStation, energy_to_charge: float) -> float:
    """Calculate charging cost at a station"""
    return energy_to_charge * station.price_per_kWh


def _create_segmented_success_message(truck: TruckModel, route_segments: List[Dict], total_costs: Dict[str, float], charging_stops: List[Dict]) -> str:
    """Create success message for segmented route"""
    total_distance = sum(segment["distance_km"] for segment in route_segments)
    total_duration = sum(segment["duration_minutes"] for segment in route_segments)
    
    message = f"Segmented route planned successfully!\n"
    message += f"Truck: {truck.manufacturer} {truck.model}\n"
    message += f"Total distance: {total_distance:.1f} km\n"
    message += f"Total duration: {total_duration:.1f} minutes\n"
    message += f"Number of segments: {len(route_segments)}\n"
    message += f"Charging stops: {len(charging_stops)}\n\n"
    
    # Add segment details
    for i, segment in enumerate(route_segments, 1):
        message += f"Segment {i}: {segment['distance_km']:.1f}km, "
        message += f"{segment['duration_minutes']:.1f}min, "
        message += f"{segment['energy_consumption']:.1f}kWh\n"
    
    # Add charging stops
    if charging_stops:
        message += "\nCharging stops:\n"
        for i, stop in enumerate(charging_stops, 1):
            message += f"Stop {i}: {stop['station'].operator_name}, "
            message += f"Cost: €{stop['charging_cost']:.2f}\n"
    
    # Add cost breakdown
    message += f"\nCost breakdown:\n"
    message += f"Driver: €{total_costs['driver_cost']:.2f}\n"
    message += f"Energy: €{total_costs['energy_cost']:.2f}\n"
    message += f"Depreciation: €{total_costs['depreciation_cost']:.2f}\n"
    message += f"Tolls: €{total_costs['tolls_cost']:.2f}\n"
    message += f"Charging: €{total_costs['charging_cost']:.2f}\n"
    message += f"Total: €{total_costs['total_cost'] + total_costs['charging_cost']:.2f}"
    
    return message


def _calculate_route_costs(distance_km: float, duration_hours: float, energy_consumption_kwh: float) -> Dict[str, float]:
    """
    Calculate all route costs based on the detour_costs.csv structure
    
    Args:
        distance_km: Total distance in kilometers
        duration_hours: Total driving time in hours
        energy_consumption_kwh: Total energy consumption in kWh
        
    Returns:
        Dictionary with cost breakdown
    """
    # Cost parameters from detour_costs.csv
    DRIVER_HOURLY_PAY = 35.0  # €/h
    ENERGY_COST_PER_KWH = 0.39  # €/kWh (average energy price for public charging)
    DEPRECIATION_PER_KM = 0.05  # €/km (vehicle variable cost)
    TOLLS_PER_KM = 0.00  # €/km (EV trucks exempt from tolls in EU)
    
    # Calculate individual cost components
    driver_cost = DRIVER_HOURLY_PAY * duration_hours
    energy_cost = ENERGY_COST_PER_KWH * energy_consumption_kwh
    depreciation_cost = DEPRECIATION_PER_KM * distance_km
    tolls_cost = TOLLS_PER_KM * distance_km
    
    # Calculate total cost
    total_cost = driver_cost + energy_cost + depreciation_cost + tolls_cost
    
    return {
        "driver_cost": driver_cost,
        "energy_cost": energy_cost,
        "depreciation_cost": depreciation_cost,
        "tolls_cost": tolls_cost,
        "total_cost": total_cost,
        "cost_per_km": total_cost / distance_km if distance_km > 0 else 0
    }


def _create_error_response(request: SingleRouteRequest, message: str) -> SingleRouteResponse:
    """Helper function to create error responses"""
    return SingleRouteResponse(
        distance_km=0.0,
        route_name=request.route_name or "Custom Route",
        duration_minutes=0.0,
        coordinates=[],
        success=False,
        message=message
    )


def _create_success_message(truck: TruckModel, energy_consumption: float, remaining_battery: float, feasible: bool, costs: Dict[str, float]) -> str:
    """Helper function to create success messages with truck information and costs"""
    message = f"Route planned successfully. "
    message += f"Truck: {truck.manufacturer} {truck.model}, "
    message += f"Energy consumption: {energy_consumption:.1f} kWh, "
    message += f"Remaining battery: {remaining_battery:.1f} kWh\n"
    
    # Add cost breakdown
    message += f"Cost breakdown: "
    message += f"Driver: €{costs['driver_cost']:.2f}, "
    message += f"Energy: €{costs['energy_cost']:.2f}, "
    message += f"Depreciation: €{costs['depreciation_cost']:.2f}, "
    message += f"Tolls: €{costs['tolls_cost']:.2f}\n"
    message += f"Total cost: €{costs['total_cost']:.2f} (€{costs['cost_per_km']:.2f}/km)"
    
    return message


if __name__ == "__main__": 
    # Test with different truck models
    trucks = load_truck_specs("data/truck_specs.csv")
    print("Available truck models:", list(trucks.keys()))

    frankfurt_stuttgart = SingleRouteRequest(
        start_lat=50.11,
        start_lng=8.6842,
        end_lat=48.78,
        end_lng=9.18,
        route_name="Frankfurt to Stuttgart"
    )
    
    # Test with a specific truck model
    if trucks:
        first_truck = list(trucks.keys())[0]
        print(f"\nTesting with truck: {first_truck}")
        
        res = plan_route(
            SingleRouteRequest(
                start_lat=52.52,
                start_lng=13.405,
                end_lat=48.8566,
                end_lng=2.3522,
                route_name="Berlin to Paris"
            ),
            truck_model=first_truck,
            starting_battery_kwh=400
        )
        if res:
            print(res.message)
        else:
            print("Error: cant go in one go")

        res2 = plan_route(
            frankfurt_stuttgart,
            truck_model=first_truck,
            starting_battery_kwh=400
        )
        if res2:
            print(res2.message)