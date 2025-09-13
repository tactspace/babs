import csv
import math
from typing import List, Tuple, Dict, Optional
from models import ChargingStation


def load_charging_stations(file_path: str) -> List[ChargingStation]:
    """
    Load charging stations from CSV file
    
    Args:
        file_path: Path to the CSV file containing charging station data
        
    Returns:
        List of ChargingStation objects
    """
    charging_stations = []
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean and convert the price field (remove € symbol)
            price_str = row['price_€/kWh'].replace('€', '')
            
            station = ChargingStation(
                id=int(row['ID']),
                country=row['country'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                truck_suitability=row['truck_suitability'],
                operator_name=row['operator_name'],
                max_power_kW=float(row['max_power_kW']),
                price_per_kWh=float(price_str)
            )
            charging_stations.append(station)
    
    return charging_stations


def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate the Haversine distance between two points in kilometers
    
    Args:
        point1: (latitude, longitude) of first point
        point2: (latitude, longitude) of second point
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


def find_nearest_charging_stations(
    point: Tuple[float, float],
    charging_stations: List[ChargingStation],
    max_distance: float = 50.0,  # km
    truck_suitable_only: bool = True,
    limit: int = 5
) -> List[ChargingStation]:
    """
    Find the nearest charging stations to a given point
    
    Args:
        point: (latitude, longitude) of the point
        charging_stations: List of all available charging stations
        max_distance: Maximum distance in kilometers to search
        truck_suitable_only: If True, only return stations suitable for trucks
        limit: Maximum number of stations to return
        
    Returns:
        List of nearest ChargingStation objects
    """
    stations_with_distance = []
    
    for station in charging_stations:
        # Skip stations not suitable for trucks if requested
        if truck_suitable_only and station.truck_suitability != "yes":
            continue
            
        distance = calculate_distance(point, (station.latitude, station.longitude))
        
        if distance <= max_distance:
            stations_with_distance.append((station, distance))
    
    # Sort by distance
    stations_with_distance.sort(key=lambda x: x[1])
    
    # Return only the stations, not the distances
    return [station for station, _ in stations_with_distance[:limit]]