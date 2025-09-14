from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Tuple, Any
import os

from models import RouteRequest, RouteResult, Driver
from trucks import load_truck_specs
from charging_stations import load_charging_stations
from route_calculator import calculate_detailed_route, calculate_multi_route
from optimizer import optimize_routes

app = FastAPI(title="E-Truck Routing Optimizer")

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data at startup
truck_specs = {}
charging_stations = []
drivers: dict[str, Driver] = {}

@app.on_event("startup")
async def startup_event():
    global truck_specs, charging_stations, drivers
    
    # Load truck specifications
    truck_specs = load_truck_specs("data/truck_specs.csv")
    
    # Load charging stations
    charging_stations = load_charging_stations("data/public_charge_points.csv")
    
    # Load drivers (mock + from xlsx if available)
    try:
        from openpyxl import load_workbook
        wb = load_workbook("data/drivers_distribution.xlsx")
        ws = wb.active
        # Expect headers in first row: id, name
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            if not row:
                continue
            did = str(row[0]) if row[0] is not None else f"drv_{i}"
            name = str(row[1]) if len(row) > 1 and row[1] is not None else f"Driver {i}"
            drivers[did] = Driver(id=did, name=name)
    except Exception:
        # Fallback mock drivers
        
        print("Error loading drivers")


@app.get("/")
async def root():
    return {"message": "E-Truck Routing Optimizer API"}


@app.get("/trucks")
async def get_trucks() -> Dict:
    """Get available truck models"""
    return {model: truck.dict() for model, truck in truck_specs.items()}
@app.get("/drivers")
async def get_drivers() -> Dict:
    return {k: v.dict() for k, v in drivers.items()}



@app.get("/charging-stations")
async def get_charging_stations(
    country: str = None,
    truck_suitable_only: bool = False,
    limit: int = 100
) -> List:
    """Get charging stations with optional filters"""
    filtered = charging_stations
    
    if country:
        filtered = [s for s in filtered if s.country == country]
    
    if truck_suitable_only:
        filtered = [s for s in filtered if s.truck_suitability == "yes"]
    
    # Return limited number of stations
    return [station.dict() for station in filtered[:limit]]


@app.get("/charging-stations/{station_id}")
async def get_charging_station(station_id: int):
    """Get details of a specific charging station"""
    for station in charging_stations:
        if station.id == station_id:
            return station.dict()
    
    raise HTTPException(status_code=404, detail="Charging station not found")


@app.post("/route", response_model=RouteResult)
async def calculate_route(request: RouteRequest):
    """Calculate optimal route for an e-truck"""
    # Validate truck model
    if request.truck_model not in truck_specs:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown truck model: {request.truck_model}. Available models: {list(truck_specs.keys())}"
        )
    
    # Find optimal route
    try:
        result = find_optimal_route(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize", response_model=RouteResult)
async def optimize_route(request: RouteRequest):
    """Optimize route with driver swaps and charging stations"""
    # Validate truck model
    if request.truck_model not in truck_specs:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown truck model: {request.truck_model}. Available models: {list(truck_specs.keys())}"
        )
    
    # Convert request to format expected by optimizer
    routes = [{
        "start_coord": {"latitude": request.start_point[0], "longitude": request.start_point[1]},
        "end_coord": {"latitude": request.end_point[0], "longitude": request.end_point[1]}
    }]
    
    # Create driver instances based on request
    num_drivers = request.num_drivers or 1
    optimizer_drivers = []
    for i in range(num_drivers):
        driver_id = request.driver_ids[i] if request.driver_ids and i < len(request.driver_ids) else i+1
        optimizer_drivers.append(Driver(
            id=driver_id, 
            name=f"Driver {driver_id}",
            home_location=request.start_point
        ))
    
    try:
        # Run optimization
        result = optimize_routes(routes, charging_stations, optimizer_drivers)
        
        # Convert result to RouteResult format
        route_result = RouteResult(
            total_distance=result["total_distance"] * 1000,  # convert km to meters
            total_duration=sum(iter["time_elapsed_minutes"] * 60 for iter in result["iterations"]),
            driving_duration=sum(iter.get("driving_time_seconds", 0) for iter in result["iterations"]),
            total_energy_consumption=sum(iter.get("energy_consumption", 0) for iter in result["iterations"]),
            total_cost=sum(iter["sum_cost"] for iter in result["iterations"]),
            route_segments=[],  # Would need to convert iterations to route segments
            driver_breaks=[],  # Would need to extract from iterations
            charging_stops=[],  # Would need to extract from iterations
            driver_swaps=[],  # Would need to convert from result["truck_swaps"]
            feasible=True
        )
        
        return route_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "loaded_trucks": len(truck_specs),
        "loaded_charging_stations": len(charging_stations)
    }


# Add new models for the detailed route API
from pydantic import BaseModel
from typing import List, Optional, Tuple

class DetailedRouteRequest(BaseModel):
    start_point: List[float]
    end_point: List[float]
    truck_type: Optional[str] = "electric"

class MultiRouteRequest(BaseModel):
    routes: List[DetailedRouteRequest]

@app.post("/detailed-route")
async def get_detailed_route(request: DetailedRouteRequest):
    """Calculate a route with detailed cost breakdown"""
    try:
        start_point = (request.start_point[0], request.start_point[1])
        end_point = (request.end_point[0], request.end_point[1])
        
        result = calculate_detailed_route(
            start_point=start_point,
            end_point=end_point,
            truck_type=request.truck_type
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/multi-route")
async def calculate_multiple_routes(request: MultiRouteRequest):
    """Calculate multiple routes with detailed cost information"""
    try:
        routes = []
        for route in request.routes:
            routes.append({
                "start_point": route.start_point,
                "end_point": route.end_point,
                "truck_type": route.truck_type
            })
        
        result = calculate_multi_route(routes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)