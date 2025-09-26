"use client";

import { useState, useEffect } from "react";
import CoordinateForm from "./CoordinateForm";
import RoutesList from "./RoutesList";
import "./MapStyles.css";
import dynamic from "next/dynamic";
import { ChargingStation } from "../../types/chargingStation";
import { SingleRouteWithSegments } from "../../types/route";
import { BASE_URL } from "../../lib/utils";
const MapView = dynamic(() => import("./MapView"), { ssr: false });

export interface Route {
  id: string;
  start: { lat: number; lng: number };
  end: { lat: number; lng: number };
  name?: string;
  path?: Array<{lat: number, lng: number}>;
  distance_km?: number; 
  duration_minutes?: number;
  routeData?: SingleRouteWithSegments;
  segments?: Array<{lat: number, lng: number}>[];
  chargingStops?: Array<{lat: number, lng: number}>;
  driverBreaks?: Array<{lat: number, lng: number}>;
  driverSalary?: number; // Add driver salary to Route interface
}

export default function DemoPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [activeRouteId, setActiveRouteId] = useState<string>("");
  const [showChargingStations, setShowChargingStations] = useState<boolean>(false);
  const [chargingStations, setChargingStations] = useState<ChargingStation[]>([]);
  const [loadingChargingStations, setLoadingChargingStations] = useState<boolean>(false);
  const [isFindingRoutes, setIsFindingRoutes] = useState<boolean>(false);

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

  const handleCoordinateSubmit = (startLat: number, startLng: number, endLat: number, endLng: number, name?: string, driverSalary?: number) => {
    addNewRoute(startLat, startLng, endLat, endLng, name, driverSalary);
  };

  const handleImportCSV = (csvRoutes: Array<{name: string, startLat: number, startLng: number, endLat: number, endLng: number, driverSalary?: number}>) => {
    const newRoutes: Route[] = csvRoutes.map((csvRoute, index) => ({
      id: `route-${Date.now()}-${index}`,
      name: csvRoute.name,
      start: { lat: csvRoute.startLat, lng: csvRoute.startLng },
      end: { lat: csvRoute.endLat, lng: csvRoute.endLng },
      driverSalary: csvRoute.driverSalary
    }));

    setRoutes([...routes, ...newRoutes]);
    
    if (newRoutes.length > 0) {
      setActiveRouteId(newRoutes[0].id);
    }
  };

  const addNewRoute = (startLat: number, startLng: number, endLat: number, endLng: number, name?: string, driverSalary?: number) => {
    const newRoute: Route = {
      id: `route-${Date.now()}`, 
      name: name || `Route ${routes.length + 1}`,
      start: { lat: startLat, lng: startLng },
      end: { lat: endLat, lng: endLng },
      driverSalary: driverSalary
    };
    console.log("DemoPage - addNewRoute with driverSalary:", driverSalary);
    console.log("DemoPage - newRoute created:", newRoute);
    
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

    setIsFindingRoutes(true);
    console.log(`Finding routes for ${routes.length} existing routes...`);
    
    try {
      // Process each route
      for (const route of routes) {
        try {
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
              route_name: route.name || `Route ${route.id}`,
              driver_salary: route.driverSalary
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
          console.error(`Error finding route for ${route.name}:`, error);
        }
      }
    } finally {
      setIsFindingRoutes(false); // End loading
    }
  };

  return (
    <div className="h-screen bg-background flex flex-col md:flex-row overflow-hidden">
      
      <div className="w-full md:w-2/5 flex flex-col border-r border-gray-200 overflow-y-auto">
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
          />
        </div>
        
        {/* Routes List - Now unscrollable, consumes full height */}
        <div className="flex-1">
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
      </div>
      
      <div className="w-full md:w-3/5 h-full">
        <MapView 
          routes={routes} 
          activeRouteId={activeRouteId} 
          showChargingStations={showChargingStations}
          chargingStations={chargingStations}
        />
      </div>
    </div>
  );
}