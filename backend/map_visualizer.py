import folium
from typing import List, Dict, Optional, Tuple
import webbrowser
import os
import json
from folium import FeatureGroup

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


def visualize_report_json(
    report_path: str = "report.json",
    output_file: str = "report_visualization.html",
    open_browser: bool = True
):
    """
    Visualize the optimization results from report.json
    
    Args:
        report_path: Path to the report JSON file
        output_file: Path to save the HTML map file
        open_browser: Whether to open the map in browser after creation
    
    Returns:
        Path to the saved HTML file
    """
    # Load report data
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Extract routes
    routes = report.get('routes', [])
    if not routes:
        print("No routes found in report")
        return None
    
    # Extract driver assignments and truck swaps
    driver_assignments = report.get('driver_assignments', [])
    truck_swaps = report.get('truck_swaps', [])
    
    # Calculate map center based on all points
    all_points = []
    for route in routes:
        all_points.append(route['start_coord'])
        all_points.append(route['end_coord'])
        for iteration in route.get('iterations', []):
            all_points.append(iteration['start_position'])
            all_points.append(iteration['end_position'])
    
    center_lat = sum(p[0] for p in all_points) / len(all_points)
    center_lon = sum(p[1] for p in all_points) / len(all_points)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Color palette for routes
    route_colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkblue', 'darkred', 'darkgreen']

    total_cost = 0
    total_time_elapsed_minutes = 0
    total_distance = 0
    
    # Add routes to map
    for i, route in enumerate(routes):
        route_color = route_colors[i % len(route_colors)]
        
        # Create a feature group for this route
        route_group = folium.FeatureGroup(name=f"Route {i+1}")
        
        # Add start and end markers
        start_coord = route['start_coord']
        end_coord = route['end_coord']
        
        # Find initial driver for this route
        initial_driver_id = None
        for assignment in driver_assignments:
            if assignment['route_id'] == i:
                initial_driver_id = assignment['driver_id']
                break
        
        driver_text = f" (Driver {initial_driver_id})" if initial_driver_id else ""
        
        # Start marker
        folium.Marker(
            location=start_coord,
            popup=f"Route {i+1} Start{driver_text}",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(route_group)
        
        # End marker
        folium.Marker(
            location=end_coord,
            popup=f"Route {i+1} End{driver_text}",
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(route_group)
        
        # Track current driver for this route
        current_driver_id = initial_driver_id
        
        # Add route segments and charging stations
        for j, iteration in enumerate(route.get('iterations', [])):
            start_pos = iteration['start_position']
            end_pos = iteration['end_position']
            
            # Calculate segment metrics
            distance = iteration.get('distance', 0)
            time_elapsed_minutes = iteration.get('time_elapsed_minutes', 0)
            time_hours = time_elapsed_minutes / 60
            cost_to_company = iteration.get('cost_to_company', 0)
            charging_cost = iteration.get('charging_cost', 0)
            sum_cost = iteration.get('sum_cost', 0)

            total_cost += cost_to_company
            total_time_elapsed_minutes += time_elapsed_minutes
            total_distance += distance

            # Segment tooltip
            segment_tooltip = f"""
            <div style="width: 200px;">
                <b>Route {i+1}, Segment {j+1}</b><br>
                <b>Driver:</b> {current_driver_id}<br>
                Distance: {distance:.1f} km<br>
                Time: {time_hours:.1f} hours<br>
                Cost to Company: €{cost_to_company:.2f}<br>
                Charging Cost: €{charging_cost:.2f}<br>
                Sum Cost: €{sum_cost:.2f}
            </div>
            """
            
            # Draw route segment
            folium.PolyLine(
                locations=[start_pos, end_pos],
                color=route_color,
                weight=4,
                opacity=0.8,
                tooltip=segment_tooltip
            ).add_to(route_group)
            
            # Add charging station marker if available
            if 'charging_station' in iteration:
                station = iteration['charging_station']
                station_name = station.get('name', 'Unknown')
                station_id = station.get('id', 'Unknown')
                station_location = station.get('location', end_pos)
                
                # Check if there was a truck swap at this station
                swap_info = None
                for swap in truck_swaps:
                    if (swap.get('station_id') == station_id and 
                        swap.get('iteration') == iteration.get('iteration')):
                        swap_info = swap
                        break
                
                # Update current driver if there was a swap
                if swap_info:
                    # If this driver was involved in the swap
                    if current_driver_id == swap_info['driver1_id']:
                        new_driver_id = swap_info['driver2_id']
                    elif current_driver_id == swap_info['driver2_id']:
                        new_driver_id = swap_info['driver1_id']
                    else:
                        new_driver_id = current_driver_id
                        
                    # Add swap marker with special icon
                    swap_popup = f"""
                    <div style="width: 220px;">
                        <h4>Truck Swap!</h4>
                        <b>Station:</b> {station_name}<br>
                        <b>Driver {swap_info['driver1_id']}</b> swapped with <b>Driver {swap_info['driver2_id']}</b><br>
                        <b>Benefit:</b> {swap_info['benefit_km']:.1f} km closer to home<br>
                    </div>
                    """
                    
                    folium.Marker(
                        location=station_location,
                        popup=folium.Popup(swap_popup, max_width=300),
                        icon=folium.Icon(color='pink', icon='exchange', prefix='fa')
                    ).add_to(route_group)
                    
                    # Update current driver
                    current_driver_id = new_driver_id
                
                # Station popup
                station_popup = f"""
                <div style="width: 200px;">
                    <b>{station_name}</b><br>
                    Station ID: {station_id}<br>
                    After segment {j+1}<br>
                    <b>Current Driver:</b> {current_driver_id}
                </div>
                """
                
                folium.Marker(
                    location=station_location,
                    popup=folium.Popup(station_popup, max_width=300),
                    icon=folium.Icon(color='blue', icon='bolt', prefix='fa')
                ).add_to(route_group)
        
        # Add driver breaks
        for break_info in route.get('driver_breaks', []):
            break_type = break_info.get('break_type', '')
            break_location = break_info.get('location', [0, 0])
            break_duration_hours = break_info.get('duration', 0) / 3600
            break_reason = break_info.get('reason', '')
            
            # Break popup
            break_popup = f"""
            <div style="width: 200px;">
                <b>{break_type.replace('_', ' ').title()}</b><br>
                Duration: {break_duration_hours:.1f} hours<br>
                Reason: {break_reason}
            </div>
            """
            
            # Icon based on break type
            if break_type == 'short_break':
                icon_color = 'orange'
                icon_name = 'coffee'
            else:  # long_rest
                icon_color = 'purple'
                icon_name = 'bed'
            
            folium.Marker(
                location=break_location,
                popup=folium.Popup(break_popup, max_width=300),
                icon=folium.Icon(color=icon_color, icon=icon_name, prefix='fa')
            ).add_to(route_group)
        
        # Add route summary box
        total_time_hours = total_time_elapsed_minutes / 60
        
        summary_html = f'''
            <div style="position: fixed; 
                        top: {10 + i*120}px; 
                        left: 10px; 
                        width: 250px; 
                        background-color: white;
                        padding: 10px;
                        border-radius: 5px;
                        border: 2px solid {route_color};
                        z-index: 9999;">
                <h4>Route {i+1} Summary</h4>
                <b>Initial Driver:</b> {initial_driver_id}<br>
                <b>Total Distance:</b> {total_distance:.1f} km<br>
                <b>Total Time:</b> {total_time_hours:.1f} hours<br>
                <b>Total Cost:</b> €{total_cost:.2f}<br>
                <b>Segments:</b> {len(route.get('iterations', []))}<br>
                <b>Breaks:</b> {len(route.get('driver_breaks', []))}
            </div>
        '''
        m.get_root().html.add_child(folium.Element(summary_html))
        
        # Add the route group to the map
        route_group.add_to(m)
    
    # Add truck swap summary if any swaps occurred
    if truck_swaps:
        swap_summary = f'''
            <div style="position: fixed; 
                        bottom: 150px; 
                        right: 10px; 
                        width: 250px; 
                        background-color: white;
                        padding: 10px;
                        border-radius: 5px;
                        border: 2px solid pink;
                        z-index: 9999;">
                <h4>Truck Swaps Summary</h4>
        '''
        
        for i, swap in enumerate(truck_swaps):
            swap_summary += f'''
                <b>Swap {i+1}:</b> Drivers {swap['driver1_id']} & {swap['driver2_id']}<br>
                <b>Location:</b> Station {swap['station_id']}<br>
                <b>Benefit:</b> {swap['benefit_km']:.1f} km<br>
                <hr style="margin: 5px 0;">
            '''
        
        swap_summary += '</div>'
        m.get_root().html.add_child(folium.Element(swap_summary))
    
    # Add legend
    legend_html = f'''
        <div style="position: fixed; 
                    bottom: 20px; 
                    left: 10px; 
                    width: 180px; 
                    background-color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: 2px solid gray;
                    z-index: 9999;">
            <h4>Legend</h4>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: green; margin-right: 5px;"></div>
                <span>Start Point</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: red; margin-right: 5px;"></div>
                <span>End Point</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: blue; margin-right: 5px;"></div>
                <span>Charging Station</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: pink; margin-right: 5px;"></div>
                <span>Truck Swap</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: orange; margin-right: 5px;"></div>
                <span>Short Break</span>
            </div>
            <div style="display: flex; align-items: center; margin-top: 5px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background-color: purple; margin-right: 5px;"></div>
                <span>Long Rest</span>
            </div>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save the map
    m.save(output_file)
    
    # Open in browser if requested
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
