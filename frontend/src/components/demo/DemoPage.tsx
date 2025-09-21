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
}

export default function DemoPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [activeRouteId, setActiveRouteId] = useState<string>("");
  const [showChargingStations, setShowChargingStations] = useState<boolean>(false);
  const [chargingStations, setChargingStations] = useState<ChargingStation[]>([]);
  const [loadingChargingStations, setLoadingChargingStations] = useState<boolean>(false);

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