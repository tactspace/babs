import folium
from typing import List, Dict, Optional
import webbrowser
import os

def plot_route(
    coordinates: List[Dict],
    plot_labels: bool = True,
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
    
    if plot_labels:
        import pandas as pd
        pd = pd.read_csv('/Users/ashish/Desktop/Hackathons/Libergy/babs/backend/data/public_charge_points.csv')
        charging_labels = []
        for index, row in pd.iterrows():
            charging_labels.append({
                'position': {'latitude': row['latitude'], 'longitude': row['longitude']},
                'text': row['operator_name'] + ' ' + row['price_€/kWh'] + ' ' + row['truck_suitability'] + ' ' + str(row['max_power_kW']),
                'type': 'charging'
            })
    labels = charging_labels
    
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

    start_point = (54.7937, 9.4470)
    end_point = (48.1351, 11.5820)

    example_coordinates = [start_point, end_point]
    from tomtom import get_route
    route = get_route(start_point, end_point)
    example_coordinates = route['coordinates']

    # Plot the example route
    plot_route(
        coordinates=example_coordinates,
        plot_labels=True,
        output_file="example_route.html"
    )
