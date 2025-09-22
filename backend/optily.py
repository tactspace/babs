from models import SingleRouteRequest, SingleRouteWithSegments, ChargingStation, TruckModel, DetailedRouteSegment, DetailedChargingStop, RouteCosts
from charging_stations import load_charging_stations
from tomtom import get_route
from typing import List, Optional, Dict, Tuple
from trucks import load_truck_specs, calculate_energy_consumption, calculate_max_range
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def plan_route(request: SingleRouteRequest, truck_model: str = None, starting_battery_kwh: float = None) -> SingleRouteWithSegments:
    """
    Custom route planner that plans routes between two points with truck capacity and cost calculations.
    
    Args:
        request: SingleRouteRequest object containing start/end coordinates and optional route name
        truck_model: Name of the truck model to use for calculations (optional)
        starting_battery_kwh: Starting battery charge in kWh (optional, defaults to full battery)
        
    Returns:
        SingleRouteWithSegments object with route details including segments and cost information
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
        
        # Plan route using simplified approach
        return _plan_simplified_route(request, truck, charging_stations, starting_battery_kwh, truck_model)
            
    except Exception as e:
        return _create_error_response(request, f"Unexpected error: {str(e)}")


def _plan_simplified_route(request: SingleRouteRequest, truck: TruckModel, charging_stations: List[ChargingStation], starting_battery_kwh: float, truck_model: str) -> SingleRouteWithSegments:
    """
    Simplified route planning: find charging stations at max range points
    """
    route_segments = []
    charging_stops = []
    detailed_segments = []
    detailed_charging_stops = []
    total_costs = {
        "driver_cost": 0,
        "energy_cost": 0,
        "depreciation_cost": 0,
        "tolls_cost": 0,
        "charging_cost": 0
    }
    
    current_battery = starting_battery_kwh
    current_position = (request.start_lat, request.start_lng)
    destination = (request.end_lat, request.end_lng)
    
    # NEW: First check if destination is reachable directly with 80% battery
    direct_distance = _get_route_distance(current_position, destination)
    if direct_distance > 0:
        energy_needed = calculate_energy_consumption(direct_distance, truck)
        # Check if we can reach with 80% of battery capacity (safety margin)
        max_usable_battery = truck.battery_capacity * 0.8
        
        if current_battery >= energy_needed and energy_needed <= max_usable_battery:
            # Can reach destination directly!
            print(f"Direct route possible: {direct_distance:.1f}km, Energy needed: {energy_needed:.1f}kWh, Current battery: {current_battery:.1f}kWh")
            
            # Create direct route segment
            direct_segment = _create_route_segment(current_position, destination, truck)
            if direct_segment:
                route_segments.append(direct_segment)
                _add_segment_costs(direct_segment, total_costs)
                
                # Create detailed segment
                detailed_segment = DetailedRouteSegment(
                    segment_number=1,
                    start_point=current_position,
                    end_point=destination,
                    distance_km=direct_segment["distance_km"],
                    duration_minutes=direct_segment["duration_minutes"],
                    energy_consumption_kwh=direct_segment["energy_consumption"],
                    coordinates=direct_segment["coordinates"],
                    costs=_calculate_segment_costs_dict(direct_segment)
                )
                detailed_segments.append(detailed_segment)
                
                # Create success message for direct route
                message = _create_direct_route_success_message(truck, direct_segment, total_costs)
                
                # Create route costs object
                route_costs = RouteCosts(
                    driver_cost_eur=total_costs["driver_cost"],
                    energy_cost_eur=total_costs["energy_cost"],
                    depreciation_cost_eur=total_costs["depreciation_cost"],
                    tolls_cost_eur=total_costs["tolls_cost"],
                    charging_cost_eur=total_costs["charging_cost"],
                    total_cost_eur=sum(total_costs.values())
                )
                
                return SingleRouteWithSegments(
                    distance_km=direct_segment["distance_km"],
                    route_name=request.route_name or f"{truck.manufacturer} {truck.model} Direct Route",
                    duration_minutes=direct_segment["duration_minutes"],
                    success=True,
                    message=message,
                    route_segments=detailed_segments,
                    charging_stops=detailed_charging_stops,
                    total_costs=route_costs,
                    truck_model=truck_model,
                    starting_battery_kwh=starting_battery_kwh,
                    final_battery_kwh=current_battery - direct_segment["energy_consumption"]
                )
    
    # If direct route not possible, proceed with charging station planning
    segment_count = 0
    
    while True:
        segment_count += 1
        
        # Step 1: Calculate max range (until 20% battery remaining) in KM
        max_range_km = _calculate_max_range_until_20_percent(truck, current_battery)
        
        # Step 2: Find the point at max range along the route to destination
        max_range_point = _find_point_at_distance(current_position, destination, max_range_km)
        
        # Step 3: Find 5 closest charging stations to this max range point
        candidate_stations = _find_closest_stations_to_point(max_range_point, charging_stations, num_candidates=5)
        
        # Step 4: Select best station based on cost and power capacity
        best_station = _select_best_station_by_score(candidate_stations)
        
        if not best_station:
            return _create_error_response(request, f"No suitable charging station found for segment {segment_count}")
        
        # Step 5: Check if we can reach destination directly from this station
        station_position = (best_station.latitude, best_station.longitude)
        direct_distance = _get_route_distance(station_position, destination)
        
        if direct_distance > 0:
            energy_needed = calculate_energy_consumption(direct_distance, truck)
            # Assume we charge to 80% at the station
            charged_battery = truck.battery_capacity * 0.8
            
            if charged_battery >= energy_needed:
                # Can reach destination directly from this station
                # Create segment to charging station
                segment_to_station = _create_route_segment(current_position, station_position, truck)
                if segment_to_station:
                    route_segments.append(segment_to_station)
                    _add_segment_costs(segment_to_station, total_costs)
                    
                    # Create detailed segment
                    detailed_segment = DetailedRouteSegment(
                        segment_number=segment_count,
                        start_point=current_position,
                        end_point=station_position,
                        distance_km=segment_to_station["distance_km"],
                        duration_minutes=segment_to_station["duration_minutes"],
                        energy_consumption_kwh=segment_to_station["energy_consumption"],
                        coordinates=segment_to_station["coordinates"],
                        costs=_calculate_segment_costs_dict(segment_to_station)
                    )
                    detailed_segments.append(detailed_segment)
                
                # Add charging stop
                charging_stop = _create_charging_stop(best_station, segment_count, current_battery, segment_to_station["energy_consumption"], truck)
                charging_stops.append(charging_stop)
                _add_charging_costs(charging_stop, total_costs)
                
                # Create detailed charging stop
                detailed_charging_stop = DetailedChargingStop(
                    stop_number=segment_count,
                    charging_station=best_station,
                    arrival_battery_kwh=charging_stop["arrival_battery"],
                    energy_to_charge_kwh=charging_stop["energy_to_charge"],
                    charging_time_hours=charging_stop["charging_time_hours"],
                    charging_cost_eur=charging_stop["charging_cost"],
                    departure_battery_kwh=truck.battery_capacity * 0.8
                )
                detailed_charging_stops.append(detailed_charging_stop)
                
                # Create final segment to destination
                final_segment = _create_route_segment(station_position, destination, truck)
                if final_segment:
                    route_segments.append(final_segment)
                    _add_segment_costs(final_segment, total_costs)
                    
                    # Create detailed final segment
                    detailed_final_segment = DetailedRouteSegment(
                        segment_number=segment_count + 1,
                        start_point=station_position,
                        end_point=destination,
                        distance_km=final_segment["distance_km"],
                        duration_minutes=final_segment["duration_minutes"],
                        energy_consumption_kwh=final_segment["energy_consumption"],
                        coordinates=final_segment["coordinates"],
                        costs=_calculate_segment_costs_dict(final_segment)
                    )
                    detailed_segments.append(detailed_final_segment)
                
                break
        
        # Step 6: Create segment to charging station
        segment = _create_route_segment(current_position, station_position, truck)
        if not segment:
            return _create_error_response(request, f"Failed to create route segment {segment_count}")
        
        route_segments.append(segment)
        _add_segment_costs(segment, total_costs)
        
        # Create detailed segment
        detailed_segment = DetailedRouteSegment(
            segment_number=segment_count,
            start_point=current_position,
            end_point=station_position,
            distance_km=segment["distance_km"],
            duration_minutes=segment["duration_minutes"],
            energy_consumption_kwh=segment["energy_consumption"],
            coordinates=segment["coordinates"],
            costs=_calculate_segment_costs_dict(segment)
        )
        detailed_segments.append(detailed_segment)
        
        # Step 7: Add charging stop
        charging_stop = _create_charging_stop(best_station, segment_count, current_battery, segment["energy_consumption"], truck)
        charging_stops.append(charging_stop)
        _add_charging_costs(charging_stop, total_costs)
        
        # Create detailed charging stop
        detailed_charging_stop = DetailedChargingStop(
            stop_number=segment_count,
            charging_station=best_station,
            arrival_battery_kwh=charging_stop["arrival_battery"],
            energy_to_charge_kwh=charging_stop["energy_to_charge"],
            charging_time_hours=charging_stop["charging_time_hours"],
            charging_cost_eur=charging_stop["charging_cost"],
            departure_battery_kwh=truck.battery_capacity * 0.8
        )
        detailed_charging_stops.append(detailed_charging_stop)
        
        # Step 8: Update current position and battery
        current_position = station_position
        current_battery = truck.battery_capacity * 0.8  # Charge to 80%
        
        print(f"Segment {segment_count}: {segment['distance_km']:.1f}km, "
              f"Energy used: {segment['energy_consumption']:.1f}kWh, "
              f"Charging at: {best_station.operator_name}")
    
    # Combine all coordinates from segments
    all_coordinates = []
    total_distance = 0
    total_duration = 0
    
    for segment in route_segments:
        all_coordinates.extend(segment["coordinates"])
        total_distance += segment["distance_km"]
        total_duration += segment["duration_minutes"]
    
    # Create success message
    message = _create_simplified_success_message(truck, route_segments, total_costs, charging_stops)
    
    # Create route costs object
    route_costs = RouteCosts(
        driver_cost_eur=total_costs["driver_cost"],
        energy_cost_eur=total_costs["energy_cost"],
        depreciation_cost_eur=total_costs["depreciation_cost"],
        tolls_cost_eur=total_costs["tolls_cost"],
        charging_cost_eur=total_costs["charging_cost"],
        total_cost_eur=sum(total_costs.values())
    )
    
    # Calculate final battery level
    final_battery = current_battery
    if route_segments:
        final_segment = route_segments[-1]
        final_battery = current_battery - final_segment["energy_consumption"]
    
    return SingleRouteWithSegments(
        distance_km=total_distance,
        route_name=request.route_name or f"{truck.manufacturer} {truck.model} Route",
        duration_minutes=total_duration,
        success=True,
        message=message,
        route_segments=detailed_segments,
        charging_stops=detailed_charging_stops,
        total_costs=route_costs,
        truck_model=truck_model,
        starting_battery_kwh=starting_battery_kwh,
        final_battery_kwh=final_battery
    )


def _calculate_max_range_until_20_percent(truck: TruckModel, current_battery: float) -> float:
    """
    Calculate maximum range in KM until battery drops to 20%
    """
    MIN_BATTERY_PERCENT = 0.20
    min_battery_kwh = truck.battery_capacity * MIN_BATTERY_PERCENT
    usable_battery = current_battery - min_battery_kwh
    
    if usable_battery <= 0:
        return 0.0
    
    return usable_battery / truck.consumption


def _find_point_at_distance(start_point: Tuple[float, float], end_point: Tuple[float, float], distance_km: float) -> Tuple[float, float]:
    """
    Find a point at a specific distance along the route from start to end
    Uses TomTom API route coordinates for accurate positioning
    """
    try:
        # Get the full route from TomTom API
        route_data = get_route(start_point, end_point, vehicle_type="truck", route_type="fastest")
        
        if not route_data:
            return start_point
        
        # Extract route coordinates
        route_coordinates = route_data["coordinates"]
        
        if not route_coordinates:
            return start_point
        
        # Calculate cumulative distances along the route
        cumulative_distance = 0.0
        target_distance_meters = distance_km * 1000  # Convert to meters
        
        for i in range(len(route_coordinates) - 1):
            current_point = route_coordinates[i]
            next_point = route_coordinates[i + 1]
            
            # Calculate distance between consecutive points
            segment_distance = _calculate_segment_distance(current_point, next_point)
            
            # Check if target distance falls within this segment
            if cumulative_distance + segment_distance >= target_distance_meters:
                # Find the exact point within this segment
                remaining_distance = target_distance_meters - cumulative_distance
                ratio = remaining_distance / segment_distance
                
                # Interpolate between current and next point
                lat1, lon1 = current_point["latitude"], current_point["longitude"]
                lat2, lon2 = next_point["latitude"], next_point["longitude"]
                
                interpolated_lat = lat1 + (lat2 - lat1) * ratio
                interpolated_lon = lon1 + (lon2 - lon1) * ratio
                
                return (interpolated_lat, interpolated_lon)
            
            cumulative_distance += segment_distance
        
        # If target distance exceeds total route, return end point
        return (route_coordinates[-1]["latitude"], route_coordinates[-1]["longitude"])
        
    except Exception as e:
        print(f"Error finding point at distance: {e}")
        return start_point


def _calculate_segment_distance(point1: Dict, point2: Dict) -> float:
    """
    Calculate distance between two route points using Haversine formula
    """
    lat1, lon1 = point1["latitude"], point1["longitude"]
    lat2, lon2 = point2["latitude"], point2["longitude"]
    
    # Haversine formula for accurate distance calculation
    R = 6371000  # Earth radius in meters
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in meters


def _find_closest_stations_to_point(target_point: Tuple[float, float], charging_stations: List[ChargingStation], num_candidates: int = 5) -> List[ChargingStation]:
    """
    Find the closest charging stations to a target point using Euclidean distance
    """
    station_distances = []
    
    for station in charging_stations:
        distance = _euclidean_distance(target_point, (station.latitude, station.longitude))
        station_distances.append((station, distance))
    
    # Sort by distance and take top candidates
    station_distances.sort(key=lambda x: x[1])
    candidates = [station for station, _ in station_distances[:num_candidates]]
    
    print(f"Found {len(candidates)} closest stations to target point")
    for i, station in enumerate(candidates):
        distance = station_distances[i][1]
        print(f"  {i+1}. {station.operator_name} - {distance:.1f}km away")
    
    return candidates


def _select_best_station_by_score(candidate_stations: List[ChargingStation]) -> Optional[ChargingStation]:
    """
    Select the best station based on cost and power capacity score
    Lower score is better
    """
    if not candidate_stations:
        return None
    
    best_station = None
    best_score = float('inf')
    
    for station in candidate_stations:
        # Score = (charging_cost_weight * price) + (power_weight / max_power)
        # Lower price and higher power = better score
        charging_cost_weight = 0.7  # 70% weight on cost
        power_weight = 0.3  # 30% weight on power
        
        cost_score = charging_cost_weight * station.price_per_kWh
        power_score = power_weight / station.max_power_kW if station.max_power_kW > 0 else float('inf')
        
        total_score = cost_score + power_score
        
        print(f"Station {station.operator_name}: Cost={station.price_per_kWh:.3f}€/kWh, "
              f"Power={station.max_power_kW}kW, Score={total_score:.4f}")
        
        if total_score < best_score:
            best_score = total_score
            best_station = station
    
    if best_station:
        print(f"Selected: {best_station.operator_name} with score {best_score:.4f}")
    
    return best_station


def _create_charging_stop(station: ChargingStation, segment_count: int, current_battery: float, energy_used: float, truck: TruckModel) -> Dict:
    """
    Create a charging stop record
    """
    arrival_battery = current_battery - energy_used
    energy_to_charge = (truck.battery_capacity * 0.8) - arrival_battery  # Charge to 80%
    charging_cost = energy_to_charge * station.price_per_kWh
    
    return {
        "station": station,
        "segment": segment_count,
        "arrival_battery": arrival_battery,
        "energy_to_charge": energy_to_charge,
        "charging_time_hours": energy_to_charge / station.max_power_kW if station.max_power_kW > 0 else 1.0,
        "charging_cost": charging_cost
    }


def _add_charging_costs(charging_stop: Dict, total_costs: Dict[str, float]):
    """Add charging costs to total costs"""
    total_costs["charging_cost"] += charging_stop["charging_cost"]
    total_costs["driver_cost"] += 35.0 * charging_stop["charging_time_hours"]  # Driver waiting time


def _euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points (rough approximation)
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Rough conversion: 1 degree ≈ 111 km
    lat_diff = (lat2 - lat1) * 111
    lon_diff = (lon2 - lon1) * 111 * 0.7  # Adjust for longitude at European latitudes
    
    return (lat_diff**2 + lon_diff**2)**0.5


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


def _calculate_segment_costs_dict(segment: Dict) -> Dict[str, float]:
    """Calculate costs for a single segment and return as dictionary"""
    duration_hours = segment["duration_minutes"] / 60
    distance_km = segment["distance_km"]
    energy_consumption = segment["energy_consumption"]
    
    # Cost parameters
    DRIVER_HOURLY_PAY = 35.0
    ENERGY_COST_PER_KWH = 0.39
    DEPRECIATION_PER_KM = 0.05
    TOLLS_PER_KM = 0.00
    
    driver_cost = DRIVER_HOURLY_PAY * duration_hours
    energy_cost = ENERGY_COST_PER_KWH * energy_consumption
    depreciation_cost = DEPRECIATION_PER_KM * distance_km
    tolls_cost = TOLLS_PER_KM * distance_km
    
    return {
        "driver_cost_eur": driver_cost,
        "energy_cost_eur": energy_cost,
        "depreciation_cost_eur": depreciation_cost,
        "tolls_cost_eur": tolls_cost,
        "total_cost_eur": driver_cost + energy_cost + depreciation_cost + tolls_cost
    }


def _create_simplified_success_message(truck: TruckModel, route_segments: List[Dict], total_costs: Dict[str, float], charging_stops: List[Dict]) -> str:
    """Create success message for simplified route"""
    total_distance = sum(segment["distance_km"] for segment in route_segments)
    total_duration = sum(segment["duration_minutes"] for segment in route_segments)
    
    message = f"Route planned successfully!\n"
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
            message += f"Stop {i}: {stop['station'].operator_name}, Stop_id: {stop['station'].id} "
            message += f"Cost: €{stop['charging_cost']:.2f}, "
            message += f"Power: {stop['station'].max_power_kW}kW\n"
    
    # Add cost breakdown
    message += f"\nCost breakdown:\n"
    message += f"Driver: €{total_costs['driver_cost']:.2f}\n"
    message += f"Energy: €{total_costs['energy_cost']:.2f}\n"
    message += f"Depreciation: €{total_costs['depreciation_cost']:.2f}\n"
    message += f"Tolls: €{total_costs['tolls_cost']:.2f}\n"
    message += f"Charging: €{total_costs['charging_cost']:.2f}\n"
    message += f"Total: €{sum(total_costs.values()):.2f}"
    
    return message


def _create_direct_route_success_message(truck: TruckModel, segment: Dict, total_costs: Dict[str, float]) -> str:
    """Create success message for direct route"""
    total_distance = segment["distance_km"]
    total_duration = segment["duration_minutes"]
    
    message = f"Direct route planned successfully!\n"
    message += f"Truck: {truck.manufacturer} {truck.model}\n"
    message += f"Total distance: {total_distance:.1f} km\n"
    message += f"Total duration: {total_duration:.1f} minutes\n"
    message += f"Number of segments: 1\n"
    message += f"Charging stops: 0\n\n"
    
    message += f"Segment: {segment['distance_km']:.1f}km, "
    message += f"{segment['duration_minutes']:.1f}min, "
    message += f"{segment['energy_consumption']:.1f}kWh\n"
    
    message += f"\nCost breakdown:\n"
    message += f"Driver: €{total_costs['driver_cost']:.2f}\n"
    message += f"Energy: €{total_costs['energy_cost']:.2f}\n"
    message += f"Depreciation: €{total_costs['depreciation_cost']:.2f}\n"
    message += f"Tolls: €{total_costs['tolls_cost']:.2f}\n"
    message += f"Charging: €{total_costs['charging_cost']:.2f}\n"
    message += f"Total: €{sum(total_costs.values()):.2f}"
    
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


def _create_error_response(request: SingleRouteRequest, message: str) -> SingleRouteWithSegments:
    """Helper function to create error responses"""
    return SingleRouteWithSegments(
        distance_km=0.0,
        route_name=request.route_name or "Custom Route",
        duration_minutes=0.0,
        success=False,
        message=message,
        route_segments=[],
        charging_stops=[],
        total_costs=None,
        truck_model=None,
        starting_battery_kwh=None,
        final_battery_kwh=None
    )


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

    berlin_munich = SingleRouteRequest(
        start_lat=52.52,
        start_lng=13.405,
        end_lat=48.14,
        end_lng=11.58,
        route_name="Berlin to Munich"
    )
    
    # Test with a specific truck model
    if trucks:
        first_truck = list(trucks.keys())[0]
        print(f"\nTesting with truck: {first_truck}")
        
        res = plan_route(
            berlin_munich,
            truck_model=first_truck,
            starting_battery_kwh=400
        )
        if res:
            print(res.message)
        else:
            print("Error: cant go in one go")


        print("*"*100)
        res2 = plan_route(
            frankfurt_stuttgart,
            truck_model=first_truck,
            starting_battery_kwh=400
        )
        if res2:
            print(res2.message)