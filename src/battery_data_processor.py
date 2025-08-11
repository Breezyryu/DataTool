"""
Main battery data processor class with CSV export functionality.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime

from .utils import (
    parse_battery_info_from_path,
    detect_equipment_type,
    validate_data_path,
    get_channel_folders
)
from .data_loaders import get_data_loader
from .data_visualizer import BatteryDataVisualizer
from .toyo_labeling import ToyoDataLabeler

logger = logging.getLogger(__name__)


class BatteryDataProcessor:
    """Main class for processing battery test data."""
    
    def __init__(self, data_path: Union[str, Path]):
        """
        Initialize battery data processor.
        
        Args:
            data_path: Path to battery test data directory
        """
        self.data_path = Path(data_path)
        self.battery_info = None
        self.equipment_type = None
        self.data_loader = None
        self.channel_data = {}
        self.merged_data = None
        
        # Validate path
        is_valid, message = validate_data_path(data_path)
        if not is_valid:
            raise ValueError(f"Invalid data path: {message}")
        
        logger.info(f"Initialized processor for: {data_path}")
        logger.info(message)
        
        # Extract battery information from path
        self.battery_info = parse_battery_info_from_path(data_path)
        
        # Detect equipment type
        self.equipment_type = detect_equipment_type(data_path)
        
        # Initialize appropriate data loader
        self.data_loader = get_data_loader(data_path, self.equipment_type)
    
    def load_data(self, channels: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Load battery test data from specified channels.
        
        Args:
            channels: List of channel names to load (if None, loads all)
            
        Returns:
            Dictionary of channel data DataFrames
        """
        logger.info(f"Loading data from {self.equipment_type} equipment...")
        
        # Load all channel data
        self.channel_data = self.data_loader.load_all_channels()
        
        # Filter channels if specified
        if channels:
            self.channel_data = {
                ch: data for ch, data in self.channel_data.items() 
                if ch in channels
            }
        
        logger.info(f"Loaded data from {len(self.channel_data)} channels")
        return self.channel_data
    
    def merge_channels(self) -> pd.DataFrame:
        """
        Merge data from all loaded channels.
        
        Returns:
            Merged DataFrame with all channel data
        """
        if not self.channel_data:
            raise ValueError("No channel data loaded. Call load_data() first.")
        
        self.merged_data = self.data_loader.merge_channel_data()
        logger.info(f"Merged data shape: {self.merged_data.shape}")
        return self.merged_data
    
    def export_to_csv(self, output_path: Optional[Union[str, Path]] = None,
                      separate_channels: bool = False,
                      include_battery_info: bool = True) -> List[str]:
        """
        Export processed data to CSV files.
        
        Args:
            output_path: Output directory or file path
            separate_channels: If True, export each channel to separate file
            include_battery_info: If True, include battery info in filename
            
        Returns:
            List of exported file paths
        """
        exported_files = []
        
        # Determine output directory and initialize base_filename
        base_filename = None
        
        if output_path is None:
            output_dir = self.data_path / "processed_data"
        else:
            output_path = Path(output_path)
            if output_path.suffix == '.csv':
                output_dir = output_path.parent
                base_filename = output_path.stem
            else:
                output_dir = output_path
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate base filename with battery info
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            info_parts = []
            
            if include_battery_info and self.battery_info:
                if self.battery_info.get('manufacturer'):
                    info_parts.append(self.battery_info['manufacturer'])
                if self.battery_info.get('model'):
                    info_parts.append(self.battery_info['model'])
                if self.battery_info.get('capacity_mah'):
                    info_parts.append(f"{self.battery_info['capacity_mah']}mAh")
            
            # Add equipment type if available
            if self.equipment_type:
                info_parts.append(self.equipment_type)
            else:
                info_parts.append("unknown")
                
            info_parts.append(timestamp)
            
            base_filename = "_".join(info_parts)
        
        # Ensure base_filename is not empty
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"battery_data_{timestamp}"
        
        # Handle Toyo equipment differently - always separate raw_data and capacity_log
        if self.equipment_type in ["Toyo", "Toyo1", "Toyo2"]:
            return self.export_toyo_separate_files(output_dir, base_filename, include_battery_info)
        
        # For PNE equipment, always export only merged data (single file)
        if self.merged_data is None:
            self.merge_channels()
        
        if self.merged_data.empty:
            logger.warning("No data to export")
            return exported_files
        
        filename = f"{base_filename}_merged.csv"
        file_path = output_dir / filename
        
        # Add metadata columns
        export_df = self.merged_data.copy()
        if include_battery_info:
            for key, value in self.battery_info.items():
                if value is not None:
                    export_df[f'battery_{key}'] = value
        
        export_df['equipment_type'] = self.equipment_type
        
        # Export to CSV
        export_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        exported_files.append(str(file_path))
        logger.info(f"Exported merged data to {file_path}")
        
        # Also export a summary file
        summary_file = output_dir / f"{base_filename}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Battery Test Data Processing Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Battery Information:\n")
            for key, value in self.battery_info.items():
                f.write(f"  {key}: {value}\n")
            
            f.write(f"\nEquipment Type: {self.equipment_type}\n")
            f.write(f"Data Path: {self.data_path}\n")
            f.write(f"Processing Time: {datetime.now()}\n\n")
            
            f.write("Channels Processed:\n")
            for channel_name, channel_df in self.channel_data.items():
                f.write(f"  {channel_name}: {len(channel_df)} rows\n")
            
            if self.merged_data is not None:
                f.write(f"\nMerged Data: {len(self.merged_data)} total rows\n")
            
            f.write(f"\nExported Files:\n")
            for file_path in exported_files:
                f.write(f"  - {file_path}\n")
        
        exported_files.append(str(summary_file))
        logger.info(f"Exported summary to {summary_file}")
        
        return exported_files
    
    def export_toyo_separate_files(self, output_dir: Path, base_filename: str, 
                                  include_battery_info: bool = True,
                                  apply_labeling: bool = True) -> List[str]:
        """
        Export Toyo data as separate files: raw_data.csv and capacity_log.csv for each channel.
        
        Args:
            output_dir: Output directory
            base_filename: Base filename for output files
            include_battery_info: Whether to include battery info in files
            apply_labeling: Whether to apply labeling (사이클, 패턴, 스텝, C-rate, Cutoff)
            
        Returns:
            List of exported file paths
        """
        exported_files = []
        
        # Get channel folders for Toyo equipment
        from .utils import get_channel_folders
        channel_folders = get_channel_folders(self.data_path, self.equipment_type)
        
        for channel_folder in channel_folders:
            channel_name = f"Ch{channel_folder.name}"
            
            try:
                # Create Toyo loader for this specific channel
                from .data_loaders import ToyoLoader
                toyo_loader = ToyoLoader(self.data_path)
                
                # Load raw data only
                raw_data = toyo_loader.load_raw_data_only(channel_folder)
                # Load capacity log only
                capacity_data = toyo_loader.load_capacity_log_only(channel_folder)
                
                # Apply labeling if requested
                if apply_labeling and not capacity_data.empty:
                    # Get rated capacity from battery info or use default
                    rated_capacity = self.battery_info.get('capacity_mah', 1730) if self.battery_info else 1730
                    
                    # Initialize labeler
                    labeler = ToyoDataLabeler(rated_capacity)
                    
                    # Label capacity log
                    if not raw_data.empty:
                        capacity_data = labeler.label_capacity_log(capacity_data, raw_data)
                        raw_data = labeler.label_raw_data(raw_data, capacity_data)
                    else:
                        capacity_data = labeler.label_capacity_log(capacity_data)
                    
                    logger.info(f"Applied labeling to {channel_name} data")
                
                # Export raw data if exists
                if not raw_data.empty:
                    # Add metadata columns
                    if include_battery_info:
                        for key, value in self.battery_info.items():
                            if value is not None:
                                raw_data[f'battery_{key}'] = value
                    
                    raw_data['equipment_type'] = self.equipment_type
                    raw_data['channel'] = channel_name
                    
                    # Export raw data file
                    suffix = "_labeled" if apply_labeling else ""
                    raw_filename = f"{base_filename}_{channel_name}_raw_data{suffix}.csv"
                    raw_file_path = output_dir / raw_filename
                    raw_data.to_csv(raw_file_path, index=False, encoding='utf-8-sig')
                    exported_files.append(str(raw_file_path))
                    logger.info(f"Exported {channel_name} raw data to {raw_file_path}")
                
                # Export capacity log if exists
                if not capacity_data.empty:
                    # Add metadata columns
                    if include_battery_info:
                        for key, value in self.battery_info.items():
                            if value is not None:
                                capacity_data[f'battery_{key}'] = value
                    
                    capacity_data['equipment_type'] = self.equipment_type
                    capacity_data['channel'] = channel_name
                    
                    # Export capacity log file
                    suffix = "_labeled" if apply_labeling else ""
                    capacity_filename = f"{base_filename}_{channel_name}_capacity_log{suffix}.csv"
                    capacity_file_path = output_dir / capacity_filename
                    capacity_data.to_csv(capacity_file_path, index=False, encoding='utf-8-sig')
                    exported_files.append(str(capacity_file_path))
                    logger.info(f"Exported {channel_name} capacity log to {capacity_file_path}")
                
            except Exception as e:
                logger.error(f"Error exporting {channel_name}: {e}")
                continue
        
        # Export summary file
        summary_file = output_dir / f"{base_filename}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Battery Test Data Processing Summary (Toyo)\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Battery Information:\n")
            for key, value in self.battery_info.items():
                f.write(f"  {key}: {value}\n")
            
            f.write(f"\nEquipment Type: {self.equipment_type}\n")
            f.write(f"Data Path: {self.data_path}\n")
            f.write(f"Processing Time: {datetime.now()}\n\n")
            
            f.write("Channels Processed:\n")
            for channel_folder in channel_folders:
                channel_name = f"Ch{channel_folder.name}"
                f.write(f"  {channel_name}: raw_data.csv + capacity_log.csv\n")
            
            f.write(f"\nExported Files:\n")
            for file_path in exported_files:
                f.write(f"  - {file_path}\n")
        
        exported_files.append(str(summary_file))
        logger.info(f"Exported Toyo summary to {summary_file}")
        
        return exported_files
    
    def visualize_data(self, output_dir: Optional[Union[str, Path]] = None,
                       plots: List[str] = None):
        """
        Create visualizations of the battery test data.
        
        Args:
            output_dir: Directory to save plots (if None, displays only)
            plots: List of plot types to create (if None, creates all)
                  Options: 'voltage_current', 'capacity_fade', 'statistics', 'channels'
        """
        if self.merged_data is None:
            self.merge_channels()
        
        if self.merged_data.empty:
            logger.warning("No data to visualize")
            return
        
        # Initialize visualizer
        visualizer = BatteryDataVisualizer(self.merged_data, self.battery_info)
        
        # Determine which plots to create
        if plots is None:
            plots = ['voltage_current', 'capacity_fade', 'statistics', 'channels']
        
        # Create output directory if saving
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create plots
        for plot_type in plots:
            save_path = None
            if output_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = output_dir / f"{plot_type}_{timestamp}.png"
            
            try:
                if plot_type == 'voltage_current':
                    visualizer.plot_voltage_current_profile(save_path=save_path)
                elif plot_type == 'capacity_fade':
                    visualizer.plot_capacity_fade(save_path=save_path)
                elif plot_type == 'statistics':
                    visualizer.plot_cycle_statistics(save_path=save_path)
                elif plot_type == 'channels':
                    visualizer.plot_channel_comparison(save_path=save_path)
                else:
                    logger.warning(f"Unknown plot type: {plot_type}")
                    
            except Exception as e:
                logger.error(f"Error creating {plot_type} plot: {e}")
    
    def get_summary_statistics(self) -> Dict:
        """
        Calculate summary statistics for the battery test data.
        
        Returns:
            Dictionary with summary statistics
        """
        if self.merged_data is None:
            self.merge_channels()
        
        if self.merged_data.empty:
            return {}
        
        stats = {
            'battery_info': self.battery_info,
            'equipment_type': self.equipment_type,
            'total_rows': len(self.merged_data),
            'channels': list(self.channel_data.keys()),
            'channel_count': len(self.channel_data)
        }
        
        # Calculate cycle statistics
        cycle_cols = ['total_cycle', 'TotlCycle', 'Cycle', 'current_cycle']
        for col in cycle_cols:
            if col in self.merged_data.columns:
                stats['total_cycles'] = self.merged_data[col].max()
                break
        
        # Calculate capacity statistics
        cap_cols = ['dchg_capacity_mah', 'Cap[mAh]']
        for col in cap_cols:
            if col in self.merged_data.columns:
                stats['max_capacity_mah'] = self.merged_data[col].max()
                stats['min_capacity_mah'] = self.merged_data[col].min()
                stats['avg_capacity_mah'] = self.merged_data[col].mean()
                break
        
        return stats