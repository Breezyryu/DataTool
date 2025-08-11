#!/usr/bin/env python
"""
Main script for battery test data processing tool.

Usage:
    python main.py <data_path> [options]
    
Example:
    python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명" --visualize --export-csv
"""

import argparse
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.battery_data_processor import BatteryDataProcessor
from src.utils import validate_data_path, detect_equipment_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('battery_processing.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Battery Test Data Processing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명" --export-csv
  python main.py "D:/toyo/battery_data" --visualize --output-dir results/
  python main.py "D:/data" --channels Ch86 Ch93 --separate-channels
        """
    )
    
    # Required arguments
    parser.add_argument(
        'data_path',
        type=str,
        help='Path to battery test data directory'
    )
    
    # Optional arguments
    parser.add_argument(
        '--channels',
        nargs='+',
        help='Specific channels to process (default: all)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for processed data (default: data_path/processed_data)'
    )
    
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Export processed data to CSV files'
    )
    
    parser.add_argument(
        '--separate-channels',
        action='store_true',
        help='Export each channel to a separate CSV file'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Create data visualizations'
    )
    
    parser.add_argument(
        '--plots',
        nargs='+',
        choices=['voltage_current', 'capacity_fade', 'statistics', 'channels'],
        help='Specific plots to create (default: all)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print summary statistics'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate data path
    logger.info(f"Processing data from: {args.data_path}")
    
    is_valid, message = validate_data_path(args.data_path)
    if not is_valid:
        logger.error(f"Invalid data path: {message}")
        sys.exit(1)
    
    logger.info(message)
    
    try:
        # Initialize processor
        processor = BatteryDataProcessor(args.data_path)
        
        # Print battery information
        logger.info("Battery Information:")
        for key, value in processor.battery_info.items():
            if value is not None:
                logger.info(f"  {key}: {value}")
        
        logger.info(f"Equipment Type: {processor.equipment_type}")
        
        # Load data
        logger.info("Loading battery test data...")
        channel_data = processor.load_data(channels=args.channels)
        
        if not channel_data:
            logger.error("No data loaded")
            sys.exit(1)
        
        # Merge channels
        merged_data = processor.merge_channels()
        logger.info(f"Total data rows: {len(merged_data)}")
        
        # Print summary statistics
        if args.summary:
            logger.info("\\nSummary Statistics:")
            stats = processor.get_summary_statistics()
            for key, value in stats.items():
                if key != 'battery_info':  # Already printed above
                    logger.info(f"  {key}: {value}")
        
        # Export to CSV
        if args.export_csv:
            logger.info("Exporting to CSV...")
            exported_files = processor.export_to_csv(
                output_path=args.output_dir,
                separate_channels=args.separate_channels
            )
            logger.info(f"Exported {len(exported_files)} files:")
            for file_path in exported_files:
                logger.info(f"  - {file_path}")
        
        # Create visualizations
        if args.visualize:
            logger.info("Creating visualizations...")
            try:
                processor.visualize_data(
                    output_dir=args.output_dir,
                    plots=args.plots
                )
                logger.info("Visualizations created successfully")
            except ImportError as e:
                logger.error(f"Visualization error: {e}")
                logger.error("Please install required packages: pip install matplotlib seaborn")
            except Exception as e:
                logger.error(f"Visualization error: {e}")
        
        logger.info("Processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()