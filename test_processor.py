#!/usr/bin/env python
"""
Test script for battery data processor using Reference data.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils import (
    parse_battery_info_from_path,
    detect_equipment_type,
    validate_data_path
)


def test_utils():
    """Test utility functions with example paths."""
    print("=== Testing Utility Functions ===\\n")
    
    # Test path parsing
    test_paths = [
        "D:/pne/LGES_G3_MP1_4352mAh_상온수명",
        "D:/toyo/Samsung_SDI_2170_3500mAh_고온수명",
        "CATL_LFP_6000mAh_사이클테스트"
    ]
    
    print("1. Battery Info Extraction:")
    for path in test_paths:
        info = parse_battery_info_from_path(path)
        print(f"Path: {path}")
        print(f"  -> {info}\\n")
    
    # Test equipment detection with Reference folder
    reference_path = Path(__file__).parent / "Reference"
    print(f"2. Equipment Detection for Reference folder:")
    print(f"Path: {reference_path}")
    
    if reference_path.exists():
        equipment_type = detect_equipment_type(reference_path)
        print(f"  -> Equipment Type: {equipment_type}")
        
        is_valid, message = validate_data_path(reference_path)
        print(f"  -> Validation: {message}\\n")
    else:
        print(f"  -> Reference folder not found\\n")


def test_reference_data_structure():
    """Analyze the Reference data structure."""
    print("=== Reference Data Structure Analysis ===\\n")
    
    reference_path = Path(__file__).parent / "Reference"
    
    if not reference_path.exists():
        print("Reference folder not found")
        return
    
    print("Directory structure:")
    for item in reference_path.rglob("*"):
        if item.is_file():
            size = item.stat().st_size
            print(f"  {item.relative_to(reference_path)} ({size} bytes)")
    
    # Analyze PNE sample data
    pne_path = reference_path / "PNE"
    if pne_path.exists():
        print(f"\\nPNE sample data:")
        
        # Check SaveData file
        save_data_file = pne_path / "ch03_SaveData0001.csv"
        if save_data_file.exists():
            with open(save_data_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                print(f"  SaveData first line: {first_line[:100]}...")
        
        # Check index files
        for index_file in ["savingFileIndex_start.csv", "savingFileIndex_last.csv"]:
            file_path = pne_path / index_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    print(f"  {index_file}: {content}")
    
    # Analyze Toyo sample data
    toyo_path = reference_path / "Toyo"
    if toyo_path.exists():
        print(f"\\nToyo sample data:")
        
        # Check CAPACITY.LOG
        capacity_log = toyo_path / "CAPACITY.LOG"
        if capacity_log.exists():
            with open(capacity_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"  CAPACITY.LOG header: {lines[0].strip()}")
                if len(lines) > 1:
                    print(f"  First data line: {lines[1].strip()}")
        
        # Check raw data file
        raw_file = toyo_path / "000001"
        if raw_file.exists():
            with open(raw_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:5]):
                    print(f"  000001 line {i+1}: {line.strip()}")


if __name__ == "__main__":
    test_utils()
    test_reference_data_structure()