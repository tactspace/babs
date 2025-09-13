import folium
from typing import List, Dict, Optional
import webbrowser
import os

def plot_route(
    coordinates: List[Dict],
    labels: Optional[List[Dict]] = None,
    output_file: str = "route_map.html",
    open_browser: bool = True
):
    """
    Plot a route on an interactive map with optional labels
    
    Args:
        coordinates: List of dicts with 'latitude' and 'longitude' keys
        labels: List of dicts with:
            - 'position': Dict with 'latitude' and 'longitude'
            - 'text': String to display in popup
            - 'type': String indicating label type ('start', 'end', 'charging', 'break', etc.)
        output_file: Path to save the HTML map file
        open_browser: Whether to automatically open the map in a browser
        
    Returns:
        Path to the saved HTML file
    """
    # If no coordinates provided, return early
    if not coordinates:
        print("No coordinates provided to plot")
        return None
    
    # Calculate center of the map
    center_lat = sum(coord['latitude'] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord['longitude'] for coord in coordinates) / len(coordinates)
    
    # Create a map
    route_map = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Add the route as a polyline
    route_points = [(coord['latitude'], coord['longitude']) for coord in coordinates]
    folium.PolyLine(
        route_points,
        color='red',
        weight=5,
        opacity=0.7,
        tooltip='Route'
    ).add_to(route_map)
    
    # Add start and end markers by default
    folium.Marker(
        location=[coordinates[0]['latitude'], coordinates[0]['longitude']],
        popup='Start',
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(route_map)
    
    folium.Marker(
        location=[coordinates[-1]['latitude'], coordinates[-1]['longitude']],
        popup='End',
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(route_map)
    
    # Add labels if provided
    if labels:
        for label in labels:
            # Skip if missing required fields
            if 'position' not in label or 'text' not in label:
                continue
                
            position = label['position']
            text = label['text']
            label_type = label.get('type', 'default')
            
            # Set icon based on label type
            if label_type == 'start':
                icon = folium.Icon(color='green', icon='play', prefix='fa')
            elif label_type == 'end':
                icon = folium.Icon(color='red', icon='stop', prefix='fa')
            elif label_type == 'charging':
                icon = folium.Icon(color='blue', icon='bolt', prefix='fa')
            elif label_type == 'break':
                icon = folium.Icon(color='orange', icon='bed', prefix='fa')
            else:
                icon = folium.Icon(color='purple', icon='info', prefix='fa')
            
            # Add marker
            folium.Marker(
                location=[position['latitude'], position['longitude']],
                popup=folium.Popup(text, max_width=300),
                icon=icon
            ).add_to(route_map)
    
    # Save the map to an HTML file
    route_map.save(output_file)
    
    # Open the map in a browser if requested
    if open_browser:
        webbrowser.open('file://' + os.path.abspath(output_file))
    
    return os.path.abspath(output_file)


# Example usage
if __name__ == "__main__":

    import json
    with open('route.json', 'r') as f:
        example_coordinates = json.load(f)['coordinates']
    # Example labels
    example_labels = [
        {
            'position': {'latitude': 52.52001, 'longitude': 13.40502},
            'text': 'Berlin - Starting Point',
            'type': 'start'
        },
        {
            'position': {'latitude': 50.50000, 'longitude': 11.50000},
            'text': '<b>Charging Stop</b><br>Operator: Aral<br>Price: 0.49 €/kWh<br>Charging Time: 45 minutes',
            'type': 'charging'
        },
        {
            'position': {'latitude': 49.50000, 'longitude': 11.00000},
            'text': '<b>Driver Break</b><br>Type: short_break<br>Duration: 45 minutes',
            'type': 'break'
        },
        {
            'position': {'latitude': 48.13510, 'longitude': 11.58200},
            'text': 'Munich - Destination',
            'type': 'end'
        }
    ]
    
    # Plot the example route
    plot_route(
        coordinates=example_coordinates,
        labels=example_labels,
        output_file="example_route.html"
    )
