from typing import List, Dict, Tuple
from models import TruckModel, ChargingStation, ChargingStop


def calculate_energy_cost(
    distance_km: float,
    truck: TruckModel
) -> float:
    """
    Calculate the energy consumption cost for a given distance
    
    Args:
        distance_km: Distance in kilometers
        truck: TruckModel object
        
    Returns:
        Energy consumption in kWh
    """
    # Calculate energy consumption
    energy_consumption = distance_km * truck.consumption
    
    return energy_consumption


def calculate_charging_cost(
    energy_amount: float,
    charging_station: ChargingStation
) -> float:
    """
    Calculate the cost of charging a given amount of energy
    
    Args:
        energy_amount: Amount of energy to charge in kWh
        charging_station: ChargingStation object
        
    Returns:
        Cost in EUR
    """
    return energy_amount * charging_station.price_per_kWh


def calculate_total_route_cost(
    total_distance_km: float,
    truck: TruckModel,
    charging_stops: List[ChargingStop]
) -> Dict:
    """
    Calculate the total cost of a route including energy consumption and charging
    
    Args:
        total_distance_km: Total distance in kilometers
        truck: TruckModel object
        charging_stops: List of ChargingStop objects
        
    Returns:
        Dictionary with cost breakdown
    """
    # Calculate energy consumption
    total_energy_consumption = calculate_energy_cost(total_distance_km, truck)
    
    # Calculate charging costs
    total_charging_cost = sum(stop.charging_cost for stop in charging_stops)
    
    return {
        "total_energy_consumption_kWh": total_energy_consumption,
        "total_charging_cost_EUR": total_charging_cost,
        "total_cost_EUR": total_charging_cost  # In this simplified model, total cost is just charging cost
    }