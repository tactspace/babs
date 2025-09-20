"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { createCustomMarker, COLORS, activeHighlightMarker } from "./LocationMarkerIcon";
import L from "leaflet";
import { Route } from "./DemoPage";

interface MapViewProps {
  routes: Route[];
  activeRouteId: string;
}

// Component to fit bounds when route points change
function BoundsAdjuster({ routes }: { routes: Route[] }) {
  const map = useMap();
  
  useEffect(() => {
    if (routes.length === 0) return;
    
    // Create a bounds object
    const bounds = L.latLngBounds([]);
    
    // Add all route points to the bounds
    routes.forEach(route => {
      bounds.extend([route.start.lat, route.start.lng]);
      bounds.extend([route.end.lat, route.end.lng]);
    });
    
    // Apply padding to ensure all points are visible with some margin
    map.fitBounds(bounds, {
      padding: [50, 50], // Padding in pixels [top/bottom, left/right]
      maxZoom: 13        // Limit zoom level to avoid excessive zoom on close points
    });
  }, [map, routes]);
  
  return null;
}

// Generate a unique color for each route
function getRouteColor(index: number): string {
  const colorKeys = Object.keys(COLORS) as Array<keyof typeof COLORS>;
  return COLORS[colorKeys[index % colorKeys.length]];
}

export default function MapView({ routes, activeRouteId }: MapViewProps) {
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
      key={`map-${routes.map(r => r.id).join('-')}-${activeRouteId}`}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.optily.eu">optily.eu</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {routes.map((route, index) => {
        const isActive = route.id === activeRouteId;
        const routeColor = getRouteColor(index);
        const customStartMarker = isActive ? activeHighlightMarker(routeColor) : createCustomMarker(routeColor);
        const customEndMarker = isActive ? activeHighlightMarker(routeColor) : createCustomMarker(routeColor);
        
        return (
          <div key={route.id}>
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
                </div>
              </Popup>
            </Marker>
          </div>
        );
      })}
      
      <BoundsAdjuster routes={routes} />
    </MapContainer>
  );
}
