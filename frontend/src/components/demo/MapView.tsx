"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { createCustomMarker, COLORS, activeHighlightMarker } from "./LocationMarkerIcon";
import L from "leaflet";
import { Route } from "./DemoPage";
import { ChargingStation } from "../../types/chargingStation";

interface MapViewProps {
  routes: Route[];
  activeRouteId: string;
  showChargingStations: boolean;
  chargingStations: ChargingStation[];
}

// Create charging station icon
const createChargingStationIcon = (isTruckSuitable: boolean) => {
  return L.divIcon({
    html: `
      <div class="charging-station-marker ${isTruckSuitable ? 'truck-suitable' : 'limited'}">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
    `,
    className: 'custom-charging-station-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Component to fit bounds when route points change
function BoundsAdjuster({ routes, chargingStations, showChargingStations }: { 
  routes: Route[]; 
  chargingStations: ChargingStation[];
  showChargingStations: boolean;
}) {
  const map = useMap();
  
  useEffect(() => {
    const bounds = L.latLngBounds([]);
    
    // Add all route points to the bounds
    routes.forEach(route => {
      bounds.extend([route.start.lat, route.start.lng]);
      bounds.extend([route.end.lat, route.end.lng]);
    });
    
    // Add charging stations to bounds if they're visible
    if (showChargingStations && chargingStations.length > 0) {
      chargingStations.forEach(station => {
        bounds.extend([station.latitude, station.longitude]);
      });
    }
    
    if (bounds.isValid()) {
      // Apply padding to ensure all points are visible with some margin
      map.fitBounds(bounds, {
        padding: [50, 50], // Padding in pixels [top/bottom, left/right]
        maxZoom: 13        // Limit zoom level to avoid excessive zoom on close points
      });
    }
  }, [map, routes, chargingStations, showChargingStations]);
  
  return null;
}

// Generate a unique color for each route
function getRouteColor(index: number): string {
  const colorKeys = Object.keys(COLORS) as Array<keyof typeof COLORS>;
  return COLORS[colorKeys[index % colorKeys.length]];
}

export default function MapView({ routes, activeRouteId, showChargingStations, chargingStations }: MapViewProps) {
  const [isMounted, setIsMounted] = useState(false);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return <div className="w-full h-screen bg-gray-100 flex items-center justify-center">Loading map...</div>;
  }

  // Default center when no routes exist (Europe center)
  const defaultCenter = [52.5200, 13.4050]; // Berlin coordinates
  const defaultZoom = 6;

  // Calculate center based on routes
  let centerLat: number;
  let centerLng: number;
  let zoom: number;

  if (routes.length === 0) {
    // No routes - use default center
    centerLat = defaultCenter[0];
    centerLng = defaultCenter[1];
    zoom = defaultZoom;
  } else {
    // Routes exist - calculate center from active route or first route
    const activeRoute = routes.find(route => route.id === activeRouteId) || routes[0];
    centerLat = (activeRoute.start.lat + activeRoute.end.lat) / 2;
    centerLng = (activeRoute.start.lng + activeRoute.end.lng) / 2;
    zoom = 10;
  }

  return (
    <MapContainer 
      center={[centerLat, centerLng]} 
      zoom={zoom} 
      style={{ height: "100%", width: "100%" }}
      key={`map-${routes.map(r => r.id).join('-')}-${activeRouteId}-${showChargingStations}`}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.optily.eu">optily.eu</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {/* Render Routes */}
      {routes.map((route, index) => {
        const isActive = route.id === activeRouteId;
        const routeColor = getRouteColor(index);
        const customStartMarker = isActive ? activeHighlightMarker(routeColor) : createCustomMarker(routeColor);
        const customEndMarker = isActive ? activeHighlightMarker(routeColor) : createCustomMarker(routeColor);
        
        return (
          <div key={route.id}>
            {/* Render route path if available */}
            {route.path && route.path.length > 0 && (
              <>
                {/* Black border - rendered first (underneath) */}
                <Polyline
                  positions={route.path.map(coord => [coord.lat, coord.lng])}
                  color="#000000"
                  weight={isActive ? 6 : 5}
                  opacity={0.8}
                />
                {/* Main colored path - rendered on top */}
                <Polyline
                  positions={route.path.map(coord => [coord.lat, coord.lng])}
                  color={routeColor}
                  weight={isActive ? 4 : 3}
                  opacity={isActive ? 0.9 : 0.7}
                />
              </>
            )}
            
            <Marker 
              position={[route.start.lat, route.start.lng]} 
              icon={customStartMarker}
              zIndexOffset={isActive ? 1000 : 0}
            >
              <Popup>
                <div className="font-medium p-1">
                  <div className="font-bold mb-1">{route.name || 'Route'} - Starting Point</div>
                  <div>Latitude: {route.start.lat.toFixed(5)}</div>
                  <div>Longitude: {route.start.lng.toFixed(5)}</div>
                  {route.distance_km && <div>Distance: {route.distance_km.toFixed(1)} km</div>}
                  {route.duration_minutes && <div>Duration: {route.duration_minutes.toFixed(0)} min</div>}
                </div>
              </Popup>
            </Marker>
            <Marker 
              position={[route.end.lat, route.end.lng]} 
              icon={customEndMarker}
              zIndexOffset={isActive ? 1000 : 0}
            >
              <Popup>
                <div className="font-medium p-1">
                  <div className="font-bold mb-1">{route.name || 'Route'} - Destination</div>
                  <div>Latitude: {route.end.lat.toFixed(5)}</div>
                  <div>Longitude: {route.end.lng.toFixed(5)}</div>
                  {route.distance_km && <div>Distance: {route.distance_km.toFixed(1)} km</div>}
                  {route.duration_minutes && <div>Duration: {route.duration_minutes.toFixed(0)} min</div>}
                </div>
              </Popup>
            </Marker>
          </div>
        );
      })}
      
      {/* Render Charging Stations */}
      {showChargingStations && chargingStations.map((station) => (
        <Marker
          key={station.id}
          position={[station.latitude, station.longitude]}
          icon={createChargingStationIcon(station.truck_suitability === "yes")}
          zIndexOffset={500}
        >
          <Popup>
            <div className="font-medium p-2 min-w-[200px]">
              <div className="font-bold mb-2 text-lg">{station.operator_name}</div>
              <div className="space-y-1 text-sm">
                <div><strong>ID:</strong> {station.id}</div>
                <div><strong>Country:</strong> {station.country}</div>
                <div><strong>Truck Suitable:</strong> 
                  <span className={`ml-1 px-2 py-1 rounded text-xs ${
                    station.truck_suitability === "yes" 
                      ? "bg-green-100 text-green-800" 
                      : "bg-yellow-100 text-yellow-800"
                  }`}>
                    {station.truck_suitability === "yes" ? "Yes" : "Limited"}
                  </span>
                </div>
                <div><strong>Max Power:</strong> {station.max_power_kW} kW</div>
                <div><strong>Price:</strong> €{station.price_per_kWh}/kWh</div>
                <div><strong>Coordinates:</strong></div>
                <div className="text-xs text-gray-600">
                  Lat: {station.latitude.toFixed(5)}<br/>
                  Lng: {station.longitude.toFixed(5)}
                </div>
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
      
      <BoundsAdjuster 
        routes={routes} 
        chargingStations={chargingStations}
        showChargingStations={showChargingStations}
      />
    </MapContainer>
  );
}
