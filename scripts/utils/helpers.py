"""
Utility functions for the EnergyPlus simulation system
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime


def setup_logging(log_dir: str = "outputs/logs") -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        Logger instance
    """
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"simulation_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary containing JSON data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to JSON file
    
    Args:
        data: Dictionary to save
        file_path: Path to save JSON file
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_configs(base_config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge override configuration into base configuration
    
    Args:
        base_config: Base configuration dictionary
        overrides: Override configuration dictionary
        
    Returns:
        Merged configuration
    """
    merged = base_config.copy()
    
    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged


def validate_geometry(geometry: Dict[str, Any]) -> bool:
    """
    Validate geometry configuration
    
    Args:
        geometry: Geometry configuration dictionary
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    required_fields = ['dimensions', 'orientation', 'location']
    
    for field in required_fields:
        if field not in geometry:
            raise ValueError(f"Missing required field in geometry: {field}")
    
    # Validate dimensions
    dims = geometry['dimensions']
    if dims['length'] <= 0 or dims['width'] <= 0 or dims['height'] <= 0:
        raise ValueError("Room dimensions must be positive")
    
    # Validate windows
    if 'windows' in geometry:
        for window in geometry['windows']:
            if window['width'] <= 0 or window['height'] <= 0:
                raise ValueError(f"Invalid window dimensions: {window['name']}")
    
    return True


def validate_materials(materials: Dict[str, Any]) -> bool:
    """
    Validate materials configuration
    
    Args:
        materials: Materials configuration dictionary
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    if 'materials' not in materials:
        raise ValueError("Missing 'materials' section")
    
    if 'constructions' not in materials:
        raise ValueError("Missing 'constructions' section")
    
    # Validate that all materials referenced in constructions exist
    material_names = set(materials['materials'].keys())
    
    for const_name, const_data in materials['constructions'].items():
        if 'layers' in const_data:
            for layer in const_data['layers']:
                if layer not in material_names:
                    raise ValueError(f"Material '{layer}' referenced in construction '{const_name}' not found")
    
    return True


def get_project_root() -> Path:
    """
    Get the project root directory
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent.parent


def ensure_dir(directory: str) -> None:
    """
    Ensure directory exists, create if not
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)


def get_weather_file_path(weather_file_name: str) -> str:
    """
    Get full path to weather file
    
    Args:
        weather_file_name: Name of weather file
        
    Returns:
        Full path to weather file
    """
    project_root = get_project_root()
    weather_dir = project_root / "data" / "weather"
    weather_path = weather_dir / weather_file_name
    
    if not weather_path.exists():
        raise FileNotFoundError(
            f"Weather file not found: {weather_path}\n"
            f"Please download from: https://energyplus.net/weather"
        )
    
    return str(weather_path)


def format_schedule_hourly(schedule_dict: Dict[str, Any]) -> str:
    """
    Format hourly schedule dictionary to EnergyPlus format
    
    Args:
        schedule_dict: Dictionary with hour ranges as keys
        
    Returns:
        Formatted schedule string
    """
    # Convert schedule dict to 24-hour array
    hourly_values = [0.0] * 24
    
    for time_range, value in schedule_dict.items():
        if '-' in str(time_range):
            start, end = map(int, str(time_range).split('-'))
            for hour in range(start, end + 1):
                if hour < 24:
                    hourly_values[hour] = value
        else:
            hour = int(time_range)
            if hour < 24:
                hourly_values[hour] = value
    
    return hourly_values
