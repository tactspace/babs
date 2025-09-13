from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict
from enum import Enum


class TruckModel(BaseModel):
    """Model representing truck specifications"""
    manufacturer: str
    model: str
    battery_capacity: float  # in kWh
    consumption: float  # in kWh/km
    range: float  # in km


class ChargingStation(BaseModel):
    """Model representing a charging station"""
    id: int
    country: str
    latitude: float
    longitude: float
    truck_suitability: str  # "yes" or "limited"
    operator_name: str
    max_power_kW: float
    price_per_kWh: float


class RouteSegment(BaseModel):
    """Model representing a segment of the route"""
    start_point: Tuple[float, float]  # (latitude, longitude)
    end_point: Tuple[float, float]  # (latitude, longitude)
    distance: float  # in meters
    duration: float  # in seconds
    energy_consumption: float  # in kWh


class DriverBreakType(str, Enum):
    SHORT_BREAK = "short_break"  # 45 minutes break
    LONG_REST = "long_rest"  # 11 hours rest


class DriverBreak(BaseModel):
    """Model representing a driver break"""
    break_type: DriverBreakType
    location: Tuple[float, float]  # (latitude, longitude)
    start_time: float  # seconds from start of journey
    duration: float  # in seconds


class ChargingStop(BaseModel):
    """Model representing a charging stop"""
    charging_station: ChargingStation
    arrival_battery_level: float  # in kWh
    departure_battery_level: float  # in kWh
    charging_time: float  # in seconds
    charging_cost: float  # in EUR


class RouteResult(BaseModel):
    """Model representing the final route result"""
    total_distance: float  # in meters
    total_duration: float  # in seconds including breaks and charging
    driving_duration: float  # in seconds of actual driving
    total_energy_consumption: float  # in kWh
    total_cost: float  # in EUR
    route_segments: List[RouteSegment]
    driver_breaks: List[DriverBreak]
    charging_stops: List[ChargingStop]
    feasible: bool  # whether the route is feasible with the given constraints


class RouteRequest(BaseModel):
    """Model representing a route request"""
    start_point: Tuple[float, float]  # (latitude, longitude)
    end_point: Tuple[float, float]  # (latitude, longitude)
    truck_model: str  # reference to a truck model
    initial_battery_level: Optional[float] = None  # in kWh, if None assume full battery