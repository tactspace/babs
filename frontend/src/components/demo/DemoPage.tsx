"use client";

import { useState, useEffect } from "react";
import CoordinateForm from "./CoordinateForm";
import RoutesList from "./RoutesList";
import "./MapStyles.css";
import dynamic from "next/dynamic";
import { ChargingStation } from "../../types/chargingStation";
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
}

export default function DemoPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [activeRouteId, setActiveRouteId] = useState<string>("");
  const [showChargingStations, setShowChargingStations] = useState<boolean>(false);
  const [chargingStations, setChargingStations] = useState<ChargingStation[]>([]);
  const [loadingChargingStations, setLoadingChargingStations] = useState<boolean>(false);
  const [isFindingRoutes, setIsFindingRoutes] = useState<boolean>(false); // Add loading state

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
          const response = await fetch(`${BASE_URL}/get-optimal-route`, {
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

          const routeData = await response.json();
          
          if (routeData.success) {
            console.log(`Route found for ${route.name}:`, routeData);
            
            // Update the existing route with path data
            setRoutes(prev => prev.map(r => 
              r.id === route.id 
                ? {
                    ...r,
                    path: routeData.coordinates,
                    distance_km: routeData.distance_km,
                    duration_minutes: routeData.duration_minutes
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
        />
      </div>
    </div>
  );
}