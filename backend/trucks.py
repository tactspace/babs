import csv
from typing import Dict, List, Optional
from models import TruckModel


def load_truck_specs(file_path: str) -> Dict[str, TruckModel]:
    """
    Load truck specifications from CSV file
    
    Args:
        file_path: Path to the CSV file containing truck specifications
        
    Returns:
        Dictionary mapping truck model names to TruckModel objects
    """
    trucks = {}
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean and convert numeric fields
            battery_capacity = float(row['Battery capacity'].split(' ')[0])
            consumption = float(row['Consumption'].split(' ')[0])
            range_km = float(row['Range'].split(' ')[0])
            
            truck = TruckModel(
                manufacturer=row['Manufacturer'].strip(),
                model=row['Model'].strip(),
                battery_capacity=battery_capacity,
                consumption=consumption,
                range=range_km
            )
            
            # Use model name as key
            trucks[truck.model] = truck
    
    return trucks


def calculate_energy_consumption(distance_km: float, truck: TruckModel) -> float:
    """
    Calculate energy consumption for a given distance and truck model
    
    Args:
        distance_km: Distance in kilometers
        truck: TruckModel object
        
    Returns:
        Energy consumption in kWh
    """
    return distance_km * truck.consumption


def calculate_max_range(truck: TruckModel, battery_level: float) -> float:
    """
    Calculate maximum range with current battery level
    
    Args:
        truck: TruckModel object
        battery_level: Current battery level in kWh
        
    Returns:
        Maximum range in kilometers
    """
    return battery_level / truck.consumption


def calculate_charging_time(
    current_level: float,
    target_level: float,
    truck: TruckModel,
    charging_power: float
) -> float:
    """
    Calculate charging time from current to target battery level
    
    Args:
        current_level: Current battery level in kWh
        target_level: Target battery level in kWh
        truck: TruckModel object
        charging_power: Charging power in kW
        
    Returns:
        Charging time in seconds
    
    Note: This is a simplified model. In reality, charging speed depends on
    battery level and decreases as the battery fills up.
    """
    # Ensure target level doesn't exceed battery capacity
    target_level = min(target_level, truck.battery_capacity)
    
    # Calculate energy to be charged in kWh
    energy_to_charge = target_level - current_level
    
    # If no charging needed or invalid input
    if energy_to_charge <= 0:
        return 0
    
    # Calculate time in hours, then convert to seconds
    charging_time_hours = energy_to_charge / charging_power
    charging_time_seconds = charging_time_hours * 3600
    
    return charging_time_seconds