import L from "leaflet";

// Create a location pin marker with hex color
const createLocationMarkerIcon = (hexColor: string = "#ef4444"): L.DivIcon => {
  return L.divIcon({
    className: "location-marker",
    html: `
      <div class="location-marker-container">
        <!-- Circle -->
        <div class="location-marker-circle" style="background-color: ${hexColor};">
          <!-- Center dot -->
          <div class="location-marker-dot"></div>
          
          <!-- Glow effect -->
          <div class="location-marker-glow" style="background: radial-gradient(circle, ${hexColor}50 0%, transparent 70%);"></div>
        </div>
        
        <!-- Vertical line -->
        <div class="location-marker-line-container">
          <!-- Black outline -->
          <div class="location-marker-line-outline"></div>
          
          <!-- Colored line -->
          <div class="location-marker-line" style="background-color: ${hexColor};"></div>
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

export const activeHighlightMarker = (hexColor: string = "#FF2A00"): L.DivIcon => {
    return L.divIcon({
      className: "location-marker-active",
      html: `
        <div class="location-marker-container-active">
          <!-- Outer ring for emphasis -->
          <div class="location-marker-ring" style="border: 3px solid ${hexColor};"></div>
          
          <!-- Circle -->
          <div class="location-marker-circle-active" style="background-color: ${hexColor};">
            <!-- Center dot -->
            <div class="location-marker-dot-active"></div>
            
            <!-- Enhanced glow effect -->
            <div class="location-marker-glow-active" style="background: radial-gradient(circle, ${hexColor}80 0%, transparent 70%);"></div>
          </div>
          
          <!-- Vertical line -->
          <div class="location-marker-line-container-active">
            <!-- Black outline -->
            <div class="location-marker-line-outline-active"></div>
            
            <!-- Colored line -->
            <div class="location-marker-line-active" style="background-color: ${hexColor};"></div>
          </div>
        </div>
      `,
      iconSize: [40, 56], // Larger than default (32, 44)
      iconAnchor: [20, 50],
      popupAnchor: [0, -50],
    });
  };

export default createLocationMarkerIcon;