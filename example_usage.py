#!/usr/bin/env python
"""
Example usage of the battery data processing tool.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.battery_data_processor import BatteryDataProcessor
from src.utils import validate_data_path


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")
    
    # Example data path (adjust to your actual data location)
    data_path = "D:/pne/LGES_G3_MP1_4352mAh_상온수명"
    
    # Note: This example uses a hypothetical path
    # Replace with actual path to your battery test data
    print(f"Data path: {data_path}")
    
    # Validate path (would fail with example path)
    is_valid, message = validate_data_path(data_path)
    print(f"Path validation: {message}")
    
    if not is_valid:
        print("Note: This is an example with a hypothetical path.")
        print("Replace with your actual data path to run.")
        return
    
    try:
        # Initialize processor
        processor = BatteryDataProcessor(data_path)
        
        # Print battery info
        print("\\nBattery Information:")
        for key, value in processor.battery_info.items():
            if value:
                print(f"  {key}: {value}")
        
        print(f"Equipment Type: {processor.equipment_type}")
        
        # Load data
        print("\\nLoading data...")
        channel_data = processor.load_data()
        print(f"Loaded {len(channel_data)} channels")
        
        # Merge channels
        merged_data = processor.merge_channels()
        print(f"Merged data shape: {merged_data.shape}")
        
        # Export to CSV
        print("\\nExporting to CSV...")
        exported_files = processor.export_to_csv()
        print(f"Exported {len(exported_files)} files")
        
        # Create visualizations (optional)
        print("\\nCreating visualizations...")
        processor.visualize_data()
        
    except Exception as e:
        print(f"Error: {e}")


def example_advanced_usage():
    """Advanced usage example with specific options."""
    print("\\n=== Advanced Usage Example ===")
    
    # Example with Reference folder data (for testing)
    data_path = Path(__file__).parent / "Reference"
    print(f"Using reference data: {data_path}")
    
    # This would work if we had proper test data
    print("This example shows how to use advanced features:")
    print("1. Load specific channels")
    print("2. Export with custom options")
    print("3. Create specific visualizations")
    
    example_code = '''
    # Initialize processor
    processor = BatteryDataProcessor(data_path)
    
    # Load specific channels only
    channel_data = processor.load_data(channels=['Ch86', 'Ch93'])
    
    # Merge and export with custom options
    merged_data = processor.merge_channels()
    exported_files = processor.export_to_csv(
        output_path="custom_output/",
        separate_channels=True,
        include_battery_info=True
    )
    
    # Create specific visualizations
    processor.visualize_data(
        output_dir="plots/",
        plots=['capacity_fade', 'voltage_current']
    )
    
    # Get summary statistics
    stats = processor.get_summary_statistics()
    print(stats)
    '''
    
    print(example_code)


def example_cli_usage():
    """Show CLI usage examples."""
    print("\\n=== CLI Usage Examples ===")
    
    examples = [
        {
            'description': 'Basic processing with CSV export',
            'command': 'python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명" --export-csv'
        },
        {
            'description': 'Process with visualizations',
            'command': 'python main.py "D:/toyo/battery_data" --visualize --export-csv'
        },
        {
            'description': 'Process specific channels only',
            'command': 'python main.py "D:/data" --channels Ch86 Ch93 --separate-channels'
        },
        {
            'description': 'Full processing with custom output directory',
            'command': 'python main.py "D:/data" --export-csv --visualize --output-dir "results/" --summary'
        },
        {
            'description': 'Create specific plots only',
            'command': 'python main.py "D:/data" --visualize --plots capacity_fade voltage_current'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   {example['command']}\\n")


if __name__ == "__main__":
    example_basic_usage()
    example_advanced_usage()
    example_cli_usage()