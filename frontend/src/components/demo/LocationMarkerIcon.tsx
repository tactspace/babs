import L from "leaflet";

// Create a location pin marker with hex color
const createLocationMarkerIcon = (hexColor: string = "#ef4444"): L.DivIcon => {
  return L.divIcon({
    className: "location-marker",
    html: `
      <style>
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes glow {
          0% { opacity: 0.5; }
          50% { opacity: 0.8; }
          100% { opacity: 0.5; }
        }
      </style>
      <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        filter: drop-shadow(0 0 8px rgba(0, 0, 0, 0.3));
        animation: pulse 1.5s infinite ease-in-out;
        transform-origin: center bottom;
      ">
        <!-- Circle -->
        <div style="
          width: 1.5rem; 
          height: 1.5rem; 
          background-color: ${hexColor}; 
          border-radius: 50%; 
          border: 1px solid black; 
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
          display: flex; 
          align-items: center; 
          justify-content: center;
          position: relative;
          z-index: 2;
        ">
          <!-- Center dot -->
          <div style="width: 0.5rem; height: 0.5rem; background-color: black; border-radius: 50%;"></div>
          
          <!-- Glow effect -->
          <div style="
            position: absolute;
            width: 2.5rem;
            height: 2.5rem;
            background: radial-gradient(circle, ${hexColor}50 0%, transparent 70%);
            border-radius: 50%;
            z-index: -1;
            animation: glow 2s infinite ease-in-out;
          "></div>
        </div>
        
        <!-- Vertical line -->
        <div style="position: relative; z-index: 1; margin-top: -2px;">
          <!-- Black outline -->
          <div style="
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 4px;
            height: 16px;
            background-color: black;
            border-radius: 0 0 2px 2px;
          "></div>
          
          <!-- Colored line -->
          <div style="
            position: absolute;
            top: 1px;
            left: 50%;
            transform: translateX(-50%);
            width: 2px;
            height: 14px;
            background-color: ${hexColor};
            border-radius: 0 0 1px 1px;
          "></div>
        </div>
      </div>
    `,
    iconSize: [32, 44],
    iconAnchor: [16, 40],
    popupAnchor: [0, -40],
  });
};

// Define common colors
export const COLORS = {
  RED: "#ef4444",
  GREEN: "#22c55e",
  BLUE: "#3b82f6",
  PURPLE: "#a855f7",
  ORANGE: "#f97316",
  TEAL: "#14b8a6",
};

// Export marker types
export const startMarker = createLocationMarkerIcon(COLORS.GREEN);
export const endMarker = createLocationMarkerIcon(COLORS.RED);
export const waypointMarker = createLocationMarkerIcon(COLORS.BLUE);
export const defaultMarker = createLocationMarkerIcon(COLORS.RED);

// Get marker by type
export const getMarkerByType = (type: "start" | "end" | "waypoint" | "default" = "default"): L.DivIcon => {
  switch (type) {
    case "start": return startMarker;
    case "end": return endMarker;
    case "waypoint": return waypointMarker;
    default: return defaultMarker;
  }
};

// Create custom marker
export const createCustomMarker = (hexColor: string): L.DivIcon => {
  return createLocationMarkerIcon(hexColor);
};

export default createLocationMarkerIcon;