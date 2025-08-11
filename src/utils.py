"""
Utility functions for battery data processing.
"""

import re
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_battery_info_from_path(path: Union[str, Path]) -> Dict[str, Optional[str]]:
    """
    Extract battery information from path name.
    
    Example path: "D:\\pne\\LGES_G3_MP1_4352mAh_상온수명"
    
    Args:
        path: Path to battery test data directory
        
    Returns:
        Dictionary containing:
        - manufacturer: Battery manufacturer (e.g., "LGES")
        - model: Battery model (e.g., "G3_MP1")
        - capacity_mah: Battery capacity in mAh (e.g., 4352)
        - test_condition: Test condition (e.g., "상온수명")
    """
    path_str = str(path)
    base_name = os.path.basename(path_str)
    
    info = {
        "manufacturer": None,
        "model": None,
        "capacity_mah": None,
        "test_condition": None,
        "full_name": base_name
    }
    
    # Try to extract capacity (e.g., 4352mAh)
    capacity_match = re.search(r'(\d+)mAh', base_name, re.IGNORECASE)
    if capacity_match:
        info["capacity_mah"] = int(capacity_match.group(1))
    
    # Split by underscore and extract components
    parts = base_name.split('_')
    
    if len(parts) >= 2:
        # First part is usually manufacturer
        info["manufacturer"] = parts[0]
        
        # Try to identify model (usually parts before capacity)
        model_parts = []
        for part in parts[1:]:
            if 'mAh' in part:
                break
            model_parts.append(part)
        
        if model_parts:
            info["model"] = '_'.join(model_parts)
    
    # Last part is often test condition
    if len(parts) > 0:
        last_part = parts[-1]
        if not re.search(r'\d+mAh', last_part):
            info["test_condition"] = last_part
    
    logger.info(f"Parsed battery info: {info}")
    return info


def detect_equipment_type(data_path: Union[str, Path]) -> Optional[str]:
    """
    Detect the equipment type based on directory structure.
    
    Args:
        data_path: Path to battery test data directory
        
    Returns:
        Equipment type: "PNE", "Toyo1", "Toyo2", or None if cannot detect
    """
    path = Path(data_path)
    
    if not path.exists():
        logger.error(f"Path does not exist: {data_path}")
        return None
    
    # Check for PNE pattern (M01Ch### folders with Restore subdirectory)
    pne_pattern = re.compile(r'M\d+Ch\d+')
    for item in path.iterdir():
        if item.is_dir() and pne_pattern.match(item.name):
            restore_path = item / "Restore"
            if restore_path.exists():
                logger.info("Detected PNE equipment type")
                return "PNE"
    
    # Check for Toyo pattern (numeric folders with CAPACITY.LOG)
    for item in path.iterdir():
        if item.is_dir() and item.name.isdigit():
            capacity_log = item / "CAPACITY.LOG"
            if capacity_log.exists():
                # Try to distinguish between Toyo1 and Toyo2 based on file structure
                # For now, default to Toyo1 (they have similar structure)
                logger.info("Detected Toyo equipment type")
                return "Toyo"
    
    logger.warning(f"Could not detect equipment type for path: {data_path}")
    return None


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between different units.
    
    Args:
        value: Value to convert
        from_unit: Source unit (e.g., "uV", "mA")
        to_unit: Target unit (e.g., "V", "A")
        
    Returns:
        Converted value
    """
    conversion_factors = {
        ("uV", "V"): 1e-6,
        ("V", "uV"): 1e6,
        ("mV", "V"): 1e-3,
        ("V", "mV"): 1e3,
        ("uA", "A"): 1e-6,
        ("A", "uA"): 1e6,
        ("mA", "A"): 1e-3,
        ("A", "mA"): 1e3,
        ("uA", "mA"): 1e-3,
        ("mA", "uA"): 1e3,
        ("uAh", "mAh"): 1e-3,
        ("mAh", "uAh"): 1e3,
        ("mAh", "Ah"): 1e-3,
        ("Ah", "mAh"): 1e3,
    }
    
    key = (from_unit, to_unit)
    if key in conversion_factors:
        return value * conversion_factors[key]
    elif from_unit == to_unit:
        return value
    else:
        raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")


def get_channel_folders(data_path: Union[str, Path], equipment_type: str) -> list:
    """
    Get list of channel folders based on equipment type.
    
    Args:
        data_path: Path to battery test data directory
        equipment_type: Type of equipment ("PNE" or "Toyo")
        
    Returns:
        List of channel folder paths
    """
    path = Path(data_path)
    channels = []
    
    if equipment_type == "PNE":
        # PNE pattern: M01Ch003[003], M01Ch004[004], etc.
        pne_pattern = re.compile(r'M\d+Ch\d+')
        for item in path.iterdir():
            if item.is_dir() and pne_pattern.match(item.name):
                restore_path = item / "Restore"
                if restore_path.exists():
                    channels.append(item)
                    
    elif equipment_type in ["Toyo", "Toyo1", "Toyo2"]:
        # Toyo pattern: numeric folders like 86, 93, etc.
        for item in path.iterdir():
            if item.is_dir() and item.name.isdigit():
                channels.append(item)
    
    channels.sort(key=lambda x: x.name)
    logger.info(f"Found {len(channels)} channel folders")
    return channels


def validate_data_path(data_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate that the data path exists and contains expected structure.
    
    Args:
        data_path: Path to battery test data directory
        
    Returns:
        Tuple of (is_valid, message)
    """
    path = Path(data_path)
    
    if not path.exists():
        return False, f"Path does not exist: {data_path}"
    
    if not path.is_dir():
        return False, f"Path is not a directory: {data_path}"
    
    equipment_type = detect_equipment_type(data_path)
    if equipment_type is None:
        return False, "Could not detect equipment type from directory structure"
    
    channels = get_channel_folders(data_path, equipment_type)
    if len(channels) == 0:
        return False, "No channel folders found in the directory"
    
    return True, f"Valid {equipment_type} data directory with {len(channels)} channels"