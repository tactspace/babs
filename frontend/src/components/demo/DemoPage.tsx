"use client";

import { useState, useEffect } from "react";
import CoordinateForm from "./CoordinateForm";
import RoutesList from "./RoutesList";
import CostComparison from "./CostComparison";
import "./MapStyles.css";
import dynamic from "next/dynamic";
import { ChargingStation } from "../../types/chargingStation";
import { SingleRouteWithSegments } from "../../types/route";
import { BASE_URL } from "../../lib/utils";
const MapView = dynamic(() => import("./MapView"), { ssr: false });

// Define the route type
export interface Route {
  id: string;
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
  name?: string;
  path?: Array<{lat: number, lng: number}>; // Add path coordinates
  distance_km?: number; // Add distance
  duration_minutes?: number; // Add duration
  // NEW: Enhanced route information
  routeData?: SingleRouteWithSegments;
  segments?: Array<{lat: number, lng: number}>[];
  chargingStops?: Array<{lat: number, lng: number}>;
  driverBreaks?: Array<{lat: number, lng: number}>;
}

export default function DemoPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [activeRouteId, setActiveRouteId] = useState<string>("");
  const [showChargingStations, setShowChargingStations] = useState<boolean>(false);
  const [chargingStations, setChargingStations] = useState<ChargingStation[]>([]);
  const [loadingChargingStations, setLoadingChargingStations] = useState<boolean>(false);
  const [isFindingRoutes, setIsFindingRoutes] = useState<boolean>(false); // Add loading state
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false); // NEW: Add optimizing state
  const [optimizationResult, setOptimizationResult] = useState<any>(null); // NEW: Store optimization results
  const [showCostComparison, setShowCostComparison] = useState<boolean>(false); // NEW: Control comparison modal
  const [optimizedRoutes, setOptimizedRoutes] = useState<Route[]>([]); // NEW: Store optimized routes
  const [truckSwaps, setTruckSwaps] = useState<any[]>([]); // NEW: Store truck swaps
  const [showOptimizedRoutes, setShowOptimizedRoutes] = useState<boolean>(false); // NEW: Control optimized routes display

  // Fetch charging stations when showChargingStations becomes true
  useEffect(() => {
    const fetchChargingStations = async () => {
      if (!showChargingStations) return;
      
      setLoadingChargingStations(true);
      try {
        const response = await fetch(`${BASE_URL}/charging-stations?limit=-1`);
        if (!response.ok) {
          throw new Error('Failed to fetch charging stations');
        }
        const data: ChargingStation[] = await response.json();
        setChargingStations(data);
      } catch (error) {
        console.error('Error fetching charging stations:', error);
      } finally {
        setLoadingChargingStations(false);
      }
    };

    fetchChargingStations();
  }, [showChargingStations]);

  const handleCoordinateSubmit = (startLat: number, startLng: number, endLat: number, endLng: number, name?: string) => {
    // Always add a new route - no editing allowed
    addNewRoute(startLat, startLng, endLat, endLng, name);
  };

  const handleImportCSV = (csvRoutes: Array<{name: string, startLat: number, startLng: number, endLat: number, endLng: number}>) => {
    const newRoutes: Route[] = csvRoutes.map((csvRoute, index) => ({
      id: `route-${Date.now()}-${index}`,
      name: csvRoute.name,
      start: { lat: csvRoute.startLat, lng: csvRoute.startLng },
      end: { lat: csvRoute.endLat, lng: csvRoute.endLng }
    }));

    setRoutes([...routes, ...newRoutes]);
    
    // Set the first imported route as active
    if (newRoutes.length > 0) {
      setActiveRouteId(newRoutes[0].id);
    }
  };

  const addNewRoute = (startLat: number, startLng: number, endLat: number, endLng: number, name?: string) => {
    const newRoute: Route = {
      id: `route-${Date.now()}`, // Use timestamp for unique IDs
      name: name || `Route ${routes.length + 1}`,
      start: { lat: startLat, lng: startLng },
      end: { lat: endLat, lng: endLng }
    };
    
    setRoutes([...routes, newRoute]);
    setActiveRouteId(newRoute.id);
  };

  const handleDeleteRoute = (routeId: string) => {
    if (routes.length <= 0) {
      return;
    }
    
    const newRoutes = routes.filter(route => route.id !== routeId);
    setRoutes(newRoutes);

    if (activeRouteId === routeId) {
      setActiveRouteId(newRoutes[0].id);
    }
  };

  const handleClearAll = () => {
    setRoutes([]);
    setActiveRouteId("");
  };

  const handleRouteSelect = (routeId: string) => {
    setActiveRouteId(routeId);
  };

  const handleChargingStationsToggle = () => {
    setShowChargingStations(!showChargingStations);
  };

  const handleFindRoute = async () => {
    if (routes.length === 0) {
      console.log('No routes to find paths for');
      return;
    }

    setIsFindingRoutes(true); // Start loading
    console.log(`Finding routes for ${routes.length} existing routes...`);
    
    try {
      // Process each route
      for (const route of routes) {
        try {
          // UPDATED: Use the new /calculate-costs endpoint
          const response = await fetch(`${BASE_URL}/calculate-costs`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              start_lat: route.start.lat,
              start_lng: route.start.lng,
              end_lat: route.end.lat,
              end_lng: route.end.lng,
              route_name: route.name || `Route ${route.id}`
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const routeData: SingleRouteWithSegments = await response.json();
          
          if (routeData.success) {
            console.log(`Route found for ${route.name}:`, routeData);
            
            // Convert coordinates to the format expected by frontend
            // Handle both cases: coordinates might be undefined or in different format
            let coordinates: Array<{lat: number, lng: number}> = [];
            
            if (routeData.coordinates && Array.isArray(routeData.coordinates)) {
              coordinates = routeData.coordinates.map(point => ({
                lat: point.latitude || point.lat,
                lng: point.longitude || point.lng
              }));
            }

            // Extract segment paths
            let segmentPaths: Array<{lat: number, lng: number}>[] = [];
            if (routeData.route_segments && Array.isArray(routeData.route_segments)) {
              segmentPaths = routeData.route_segments.map(segment => {
                if (segment.coordinates && Array.isArray(segment.coordinates)) {
                  return segment.coordinates.map(point => ({
                    lat: point.latitude || point.lat,
                    lng: point.longitude || point.lng
                  }));
                }
                return [];
              });
            }

            // Extract charging stop locations
            let chargingStopLocations: Array<{lat: number, lng: number}> = [];
            if (routeData.charging_stops && Array.isArray(routeData.charging_stops)) {
              chargingStopLocations = routeData.charging_stops.map(stop => ({
                lat: stop.charging_station.latitude,
                lng: stop.charging_station.longitude
              }));
            }

            // Extract driver break locations
            let driverBreakLocations: Array<{lat: number, lng: number}> = [];
            if (routeData.driver_breaks && Array.isArray(routeData.driver_breaks)) {
              driverBreakLocations = routeData.driver_breaks.map(breakItem => ({
                lat: breakItem.location[0],
                lng: breakItem.location[1]
              }));
            }
            
            // Update the existing route with enhanced data
            setRoutes(prev => prev.map(r => 
              r.id === route.id 
                ? {
                    ...r,
                    path: coordinates,
                    distance_km: routeData.distance_km,
                    duration_minutes: routeData.duration_minutes,
                    routeData: routeData,
                    segments: segmentPaths,
                    chargingStops: chargingStopLocations,
                    driverBreaks: driverBreakLocations
                  }
                : r
            ));
          } else {
            console.error(`Route calculation failed for ${route.name}:`, routeData.message);
          }
        } catch (error) {
          console.error(`Error fetching route for ${route.name}:`, error);
        }
      }
    } finally {
      setIsFindingRoutes(false); // End loading
    }
  };

  // NEW: Handle optimize with swaps
  const handleOptimizeWithSwaps = async () => {
    if (routes.length < 2) {
      console.log("Need at least 2 routes to optimize with swaps");
      return;
    }

    setIsOptimizing(true);
    console.log(`Optimizing ${routes.length} routes with swaps...`);

    try {
      // Prepare route requests for the compare-costs endpoint
      const routeRequests = routes.map(route => ({
        start_lat: route.start.lat,
        start_lng: route.start.lng,
        end_lat: route.end.lat,
        end_lng: route.end.lng,
        route_name: route.name
      }));

      const response = await fetch(`${BASE_URL}/compare-costs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(routeRequests),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const optimizationResult = await response.json();
      console.log("Optimization result:", optimizationResult);

      // Store the result and show the comparison modal
      setOptimizationResult(optimizationResult);
      setShowCostComparison(true);

      // NEW: Convert optimization result routes to display format and show on map
      if (optimizationResult.success && optimizationResult.routes) {
        const optimizedRoutes = optimizationResult.routes.map((route: any, index: number) => {
          const originalRoute = routes[index];
          
          // Extract route coordinates from segments
          let routePath: Array<{lat: number, lng: number}> = [];
          if (route.route_segments && route.route_segments.length > 0) {
            route.route_segments.forEach((segment: any) => {
              if (segment.coordinates) {
                routePath.push(...segment.coordinates.map((coord: any) => ({
                  lat: coord.lat || coord.latitude,
                  lng: coord.lng || coord.longitude
                })));
              }
            });
          }
          
          return {
            ...originalRoute,
            id: `optimized-${originalRoute.id}`,
            name: `${originalRoute.name} (Optimized)`,
            path: routePath,
            distance_km: route.distance_km,
            duration_minutes: route.duration_minutes,
            routeData: route,
            segments: route.route_segments ? route.route_segments.map((segment: any) => 
              segment.coordinates?.map((coord: any) => ({
                lat: coord.lat || coord.latitude,
                lng: coord.lng || coord.longitude
              })) || []
            ) : undefined
          };
        });
        
        setOptimizedRoutes(optimizedRoutes);
        setTruckSwaps(optimizationResult.truck_swaps || []);
        setShowOptimizedRoutes(true);
      }

      // Log detailed comparison information
      console.log("=== OPTIMIZATION SUMMARY ===");
      console.log(`Total Routes: ${optimizationResult.routes?.length || 0}`);
      console.log(`Total Cost: €${optimizationResult.total_cost_eur?.toFixed(2) || 0}`);
      console.log(`Cost Savings: €${optimizationResult.cost_savings_eur?.toFixed(2) || 0} (${optimizationResult.cost_savings_percentage?.toFixed(1) || 0}%)`);
      console.log(`Truck Swaps Found: ${optimizationResult.truck_swaps?.length || 0}`);

      if (optimizationResult.route_comparisons) {
        console.log("\n=== PER-ROUTE COMPARISONS ===");
        optimizationResult.route_comparisons.forEach((comparison: any, index: number) => {
          console.log(`\n ${comparison.route_name} (Route ${index + 1}):`);
          console.log(`  Base Cost: €${comparison.base.total_cost_eur.toFixed(2)}`);
          console.log(`  Optimized Cost: €${comparison.optimized.total_cost_eur.toFixed(2)}`);
          console.log(`  Savings: €${comparison.savings.total_cost_eur.toFixed(2)} (${comparison.savings_percentage.total_cost_eur.toFixed(1)}%)`);
          console.log(`  Swaps Applied: ${comparison.swaps_applied?.length || 0}`);
        });
      }

      if (optimizationResult.truck_swaps && optimizationResult.truck_swaps.length > 0) {
        console.log("\n=== TRUCK SWAPS DETAILS ===");
        optimizationResult.truck_swaps.forEach((swap: any, index: number) => {
          console.log(`Swap ${index + 1}:`);
          console.log(`  Drivers: ${swap.driver1_id} ↔ ${swap.driver2_id}`);
          console.log(`  Station: ${swap.station_id} (${swap.reason})`);
          console.log(`  Benefit: ${swap.benefit_km} km`);
        });
      }

    } catch (error) {
      console.error("Error optimizing routes with swaps:", error);
    } finally {
      setIsOptimizing(false);
    }
  };

  // NEW: Handle closing the cost comparison modal
  const handleCloseCostComparison = () => {
    setShowCostComparison(false);
    setOptimizationResult(null);
  };

  return (
    <div className="h-screen bg-background flex flex-col md:flex-row overflow-hidden">
      
      <div className="w-full md:w-2/5 flex flex-col border-r border-gray-200">
        {/* Header - Fixed */}
        <div className="px-8 pt-8 flex-shrink-0">
          <h1 className="text-2xl font-bold text-center">Route Planner</h1>
        </div>
        
        {/* Form - Fixed */}
        <div className="px-8 pb-8 flex-shrink-0">
          <CoordinateForm 
            onSubmit={handleCoordinateSubmit}
            onImportCSV={handleImportCSV}
            onFindRoute={handleFindRoute}
            isFindRouteEnabled={routes.length > 0 && !isFindingRoutes}
            isFindingRoutes={isFindingRoutes}
            onOptimizeWithSwaps={handleOptimizeWithSwaps}
            isOptimizeEnabled={routes.length >= 2 && !isOptimizing}
            isOptimizing={isOptimizing}
          />
        </div>
        
        {/* Routes List - Scrollable */}
        <RoutesList 
          routes={routes}
          activeRouteId={activeRouteId}
          onRouteSelect={handleRouteSelect}
          onRouteDelete={handleDeleteRoute}
          onClearAll={handleClearAll}
          showChargingStations={showChargingStations}
          onChargingStationsToggle={handleChargingStationsToggle}
          loadingChargingStations={loadingChargingStations}
        />
      </div>
      
      <div className="w-full md:w-3/5 h-full">
        <MapView 
          routes={routes} 
          activeRouteId={activeRouteId} 
          showChargingStations={showChargingStations}
          chargingStations={chargingStations}
          optimizedRoutes={optimizedRoutes}
          truckSwaps={truckSwaps}
          showOptimizedRoutes={showOptimizedRoutes}
        />
      </div>

      {/* Cost Comparison Modal */}
      {showCostComparison && (
        <CostComparison
          optimizationResult={optimizationResult}
          onClose={handleCloseCostComparison}
        />
      )}
    </div>
  );
}