from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Any
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
    """Model representing a driver break (used by route_calculator.py)"""
    break_type: DriverBreakType
    location: List[float]  # [latitude, longitude] as expected by route_calculator
    start_time: float  # seconds from start of journey
    duration: float  # in seconds


class Driver(BaseModel):
    """Simplified driver model with essential attributes"""
    id: str
    name: Optional[str] = None
    current_location: Tuple[float, float]  # (latitude, longitude)
    home_location: Tuple[float, float]  # (latitude, longitude)
    mins_driven: float = 0.0  # Total minutes driven
    continuous_driving_minutes: float = 0.0  # Minutes driven since last break
    breaks_taken_min: float = 0.0  # Total minutes spent on breaks
    current_truck_id: Optional[int] = None  # ID of the truck currently assigned to this driver


class DetailedDriverBreak(BaseModel):
    """Model representing a detailed driver break"""
    break_number: int
    break_type: DriverBreakType
    location: Tuple[float, float]
    start_time_minutes: float  # Minutes from start of journey
    duration_minutes: float
    reason: str
    charging_station: Optional[ChargingStation] = None


class ChargingStop(BaseModel):
    """Model representing a charging stop"""
    charging_station: ChargingStation
    arrival_battery_level: float  # in kWh
    departure_battery_level: float  # in kWh
    charging_time: float  # in seconds
    charging_cost: float  # in EUR
    reason: Optional[str] = None


class RouteResult(BaseModel):
    """Model representing the final route result"""
    total_distance: float  # in meters
    total_duration: float  # in seconds including breaks and charging
    driving_duration: float  # in seconds of actual driving
    total_energy_consumption: float  # in kWh
    total_cost: float  # in EUR
    route_segments: List[RouteSegment]
    driver_breaks: List[DetailedDriverBreak]
    charging_stops: List[ChargingStop]
    nearby_charging_stations: List[ChargingStation] = []
    battery_capacity_kwh: Optional[float] = None
    battery_trace: List[Dict] = []  # items: {"location": (lat,lon), "time": s, "battery_kwh": float, "soc_percent": float}
    feasible: bool  # whether the route is feasible with the given constraints


class RouteRequest(BaseModel):
    """Model representing a route request"""
    start_point: Tuple[float, float]  # (latitude, longitude)
    end_point: Tuple[float, float]  # (latitude, longitude)
    truck_model: str  # reference to a truck model
    initial_battery_level: Optional[float] = None  # in kWh, if None assume full battery
    optimize_by: Optional[str] = Field(default="time", description="Optimize by 'time' or 'cost'")
    num_drivers: Optional[int] = Field(default=1, description="Number of available drivers for swapping")
    driver_ids: Optional[List[str]] = None


class SingleRouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    route_name: Optional[str] = None

class DetailedRouteSegment(BaseModel):
    """Model representing a detailed route segment with costs"""
    segment_number: int
    start_point: Tuple[float, float]  # (latitude, longitude)
    end_point: Tuple[float, float]  # (latitude, longitude)
    distance_km: float
    duration_minutes: float
    energy_consumption_kwh: float
    coordinates: List[Dict[str, float]]  # Route coordinates for this segment
    costs: Dict[str, float]  # Cost breakdown for this segment
    driver_id: Optional[str] = None  # Driver who drove this segment


class DetailedChargingStop(BaseModel):
    """Model representing a detailed charging stop"""
    stop_number: int
    charging_station: ChargingStation
    arrival_battery_kwh: float
    energy_to_charge_kwh: float
    charging_time_hours: float
    charging_cost_eur: float
    departure_battery_kwh: float


class RouteCosts(BaseModel):
    """Model representing total route costs"""
    driver_cost_eur: float
    depreciation_cost_eur: float
    tolls_cost_eur: float
    charging_cost_eur: float
    total_cost_eur: float

class SingleRouteResponse(BaseModel):
    distance_km: float
    route_name: str
    duration_minutes: float
    coordinates: List[Dict[str, float]]
    success: bool
    message: Optional[str] = None


class SingleRouteWithSegments(BaseModel):
    distance_km: float
    route_name: str
    duration_minutes: float
    success: bool
    message: Optional[str] = None
    # NEW: Enhanced fields
    route_segments: List[DetailedRouteSegment] = []
    charging_stops: List[DetailedChargingStop] = []
    driver_breaks: List[DetailedDriverBreak] = []
    driver: Optional[Driver] = None  # Single driver object
    total_costs: Optional[RouteCosts] = None
    truck_model: Optional[str] = None
    starting_battery_kwh: Optional[float] = None
    final_battery_kwh: Optional[float] = None
    eu_compliant: bool = True  # NEW: EU compliance flag


class TruckSwap(BaseModel):
    """Model representing a truck swap between drivers"""
    station_id: int
    station_location: Tuple[float, float]
    driver1_id: str
    driver2_id: str
    benefit_km: float
    alignment_dot: float
    reason: str
    detour_km_total: float
    iteration: int
    route_idx: int
    global_iteration: int


class RouteComparison(BaseModel):
    """Model representing comparison between base and optimized route"""
    route_name: str
    route_index: int
    base: Dict[str, float]  # base cost, duration, distance, etc.
    optimized: Dict[str, float]  # optimized cost, duration, distance, etc.
    savings: Dict[str, float]  # savings in cost, duration, etc.
    savings_percentage: Dict[str, float]  # percentage savings
    swaps_applied: List[TruckSwap] = []  # swaps that affected this route

class MultiRouteWithSegments(BaseModel):
    """Model representing multiple routes with optimization and swapping"""
    routes: List[SingleRouteWithSegments]
    total_distance_km: float
    total_duration_minutes: float
    total_cost_eur: float
    total_charging_cost_eur: float
    success: bool
    message: Optional[str] = None
    # Optimization results
    driver_assignments: List[Dict[str, Any]] = []
    truck_swaps: List[TruckSwap] = []
    drivers: List[Driver] = []
    optimization_summary: Optional[Dict[str, Any]] = None
    # Cost comparison
    base_cost_eur: Optional[float] = None
    optimized_cost_eur: Optional[float] = None
    cost_savings_eur: Optional[float] = None
    cost_savings_percentage: Optional[float] = None
    route_comparisons: List[RouteComparison] = []

