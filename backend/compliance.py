from typing import List, Tuple, Dict
from models import DriverBreak, DriverBreakType


# EU driving regulations constants
MAX_CONTINUOUS_DRIVING_TIME = 4.5 * 3600  # 4.5 hours in seconds
SHORT_BREAK_DURATION = 45 * 60  # 45 minutes in seconds
MAX_DAILY_DRIVING_TIME = 9 * 3600  # 9 hours in seconds
LONG_REST_DURATION = 11 * 3600  # 11 hours in seconds


def calculate_required_breaks(
    route_duration: float,
    route_points: List[Tuple[float, float]],
    segment_durations: List[float]
) -> List[DriverBreak]:
    """
    Calculate required driver breaks based on EU regulations
    
    Args:
        route_duration: Total route duration in seconds
        route_points: List of (latitude, longitude) points along the route
        segment_durations: Duration of each segment in seconds
        
    Returns:
        List of required DriverBreak objects
    """
    breaks = []
    
    # If route is short enough, no breaks required
    if route_duration <= MAX_CONTINUOUS_DRIVING_TIME:
        return breaks
    
    accumulated_driving = 0
    total_driving_today = 0
    current_time = 0
    
    # Iterate through segments to find where breaks are needed
    for i, duration in enumerate(segment_durations):
        accumulated_driving += duration
        total_driving_today += duration
        current_time += duration
        
        # Need a short break after 4.5 hours of continuous driving
        if accumulated_driving >= MAX_CONTINUOUS_DRIVING_TIME:
            # Find the appropriate point for the break
            # For simplicity, we'll use the end point of the current segment
            break_location = route_points[min(i + 1, len(route_points) - 1)]
            
            breaks.append(
                DriverBreak(
                    break_type=DriverBreakType.SHORT_BREAK,
                    location=break_location,
                    start_time=current_time,
                    duration=SHORT_BREAK_DURATION
                )
            )
            
            # Reset continuous driving counter and add break time
            accumulated_driving = 0
            current_time += SHORT_BREAK_DURATION
        
        # Need a long rest after 9 hours of total daily driving
        if total_driving_today >= MAX_DAILY_DRIVING_TIME:
            # Find the appropriate point for the rest
            break_location = route_points[min(i + 1, len(route_points) - 1)]
            
            breaks.append(
                DriverBreak(
                    break_type=DriverBreakType.LONG_REST,
                    location=break_location,
                    start_time=current_time,
                    duration=LONG_REST_DURATION
                )
            )
            
            # Reset daily driving counter and add rest time
            total_driving_today = 0
            accumulated_driving = 0
            current_time += LONG_REST_DURATION
    
    return breaks


def is_route_compliant(
    route_duration: float,
    breaks: List[DriverBreak]
) -> bool:
    """
    Check if a route with its breaks is compliant with EU regulations
    
    Args:
        route_duration: Total route duration in seconds
        breaks: List of DriverBreak objects
        
    Returns:
        True if the route is compliant, False otherwise
    """
    # If no breaks needed
    if route_duration <= MAX_CONTINUOUS_DRIVING_TIME:
        return True
    
    # Check if we have the right breaks at the right times
    # This is a simplified check - a real implementation would be more complex
    
    # Sort breaks by start time
    sorted_breaks = sorted(breaks, key=lambda b: b.start_time)
    
    continuous_driving = 0
    daily_driving = 0
    current_time = 0
    
    for break_obj in sorted_breaks:
        # Driving time before this break
        driving_time = break_obj.start_time - current_time
        continuous_driving += driving_time
        daily_driving += driving_time
        
        # Check if we drove too long without a break
        if continuous_driving > MAX_CONTINUOUS_DRIVING_TIME:
            return False
        
        # Check if we drove too long in a day
        if daily_driving > MAX_DAILY_DRIVING_TIME:
            return False
        
        # Reset counters based on break type
        if break_obj.break_type == DriverBreakType.SHORT_BREAK:
            continuous_driving = 0
        elif break_obj.break_type == DriverBreakType.LONG_REST:
            continuous_driving = 0
            daily_driving = 0
        
        # Update current time
        current_time = break_obj.start_time + break_obj.duration
    
    # Check remaining driving after last break
    final_driving = route_duration - current_time
    continuous_driving += final_driving
    daily_driving += final_driving
    
    # Final checks
    if continuous_driving > MAX_CONTINUOUS_DRIVING_TIME:
        return False
    if daily_driving > MAX_DAILY_DRIVING_TIME:
        return False
    
    return True