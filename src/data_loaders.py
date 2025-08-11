"""
Data loader classes for different battery test equipment.
"""

import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod
import logging
from tqdm import tqdm

from .utils import convert_units

logger = logging.getLogger(__name__)


class BaseDataLoader(ABC):
    """Base class for battery test data loaders."""
    
    def __init__(self, data_path: Union[str, Path]):
        """
        Initialize data loader.
        
        Args:
            data_path: Path to battery test data directory
        """
        self.data_path = Path(data_path)
        self.channel_data = {}
        
    @abstractmethod
    def load_channel_data(self, channel_path: Path) -> pd.DataFrame:
        """Load data from a single channel."""
        pass
    
    @abstractmethod
    def load_all_channels(self) -> Dict[str, pd.DataFrame]:
        """Load data from all channels."""
        pass
    
    def merge_channel_data(self) -> pd.DataFrame:
        """Merge data from all channels into a single DataFrame."""
        if not self.channel_data:
            raise ValueError("No channel data loaded. Call load_all_channels() first.")
        
        # Add channel identifier to each dataframe
        merged_frames = []
        for channel_name, df in self.channel_data.items():
            df_copy = df.copy()
            df_copy['channel'] = channel_name
            merged_frames.append(df_copy)
        
        # Concatenate all dataframes
        merged_df = pd.concat(merged_frames, ignore_index=True)
        logger.info(f"Merged {len(self.channel_data)} channels into single DataFrame")
        return merged_df


class PNELoader(BaseDataLoader):
    """Data loader for PNE equipment."""
    
    # PNE column mapping based on documentation
    COLUMN_NAMES = [
        'index', 'default', 'step_type', 'chg_dchg', 'current_app_class',
        'cccv', 'end_state', 'step_count', 'voltage_uv', 'current_ua',
        'chg_capacity_uah', 'dchg_capacity_uah', 'chg_power_mw', 'dchg_power_mw',
        'chg_wh', 'dchg_wh', 'repeat_pattern_count', 'step_time_cs', 'tot_time_day',
        'tot_time_cs', 'impedance', 'temp1', 'temp2', 'temp3', 'temp4',
        'unknown25', 'repeat_count', 'total_cycle', 'current_cycle',
        'avg_voltage_uv', 'avg_current_ua', 'col31', 'col32', 'date',
        'time', 'col35', 'col36', 'col37', 'col38', 'col39', 'col40',
        'col41', 'col42', 'col43', 'cumulative_step', 'voltage_max_uv', 'voltage_min_uv'
    ]
    
    def load_channel_data(self, channel_path: Path) -> pd.DataFrame:
        """
        Load data from a single PNE channel.
        
        Args:
            channel_path: Path to channel directory (e.g., M01Ch003[003])
            
        Returns:
            DataFrame with channel data
        """
        restore_path = channel_path / "Restore"
        if not restore_path.exists():
            logger.warning(f"Restore folder not found in {channel_path}")
            return pd.DataFrame()
        
        # Load index files to understand file structure
        index_files = {
            'start': restore_path / 'savingFileIndex_start.csv',
            'last': restore_path / 'savingFileIndex_last.csv'
        }
        
        # Get list of SaveData files
        save_data_files = sorted([f for f in restore_path.glob('*SaveData*.csv')])
        
        if not save_data_files:
            logger.warning(f"No SaveData files found in {restore_path}")
            return pd.DataFrame()
        
        # Load and concatenate all SaveData files
        data_frames = []
        logger.info(f"Loading {len(save_data_files)} SaveData files from {channel_path.name}")
        
        for file_path in tqdm(save_data_files, desc=f"Loading {channel_path.name}"):
            try:
                # Read without headers, tab-separated
                df = pd.read_csv(file_path, sep='\t', header=None, encoding='utf-8')
                
                # Ensure we have the right number of columns
                if len(df.columns) == len(self.COLUMN_NAMES):
                    df.columns = self.COLUMN_NAMES
                else:
                    logger.warning(f"Column count mismatch in {file_path.name}: "
                                 f"expected {len(self.COLUMN_NAMES)}, got {len(df.columns)}")
                    # Use numeric column names if mismatch
                    df.columns = [f'col_{i}' for i in range(len(df.columns))]
                
                data_frames.append(df)
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue
        
        if not data_frames:
            return pd.DataFrame()
        
        # Concatenate all data
        combined_df = pd.concat(data_frames, ignore_index=True)
        
        # Convert units from micro to standard units
        if 'voltage_uv' in combined_df.columns:
            combined_df['voltage_v'] = combined_df['voltage_uv'] / 1e6
        if 'current_ua' in combined_df.columns:
            combined_df['current_ma'] = combined_df['current_ua'] / 1e3
        if 'chg_capacity_uah' in combined_df.columns:
            combined_df['chg_capacity_mah'] = combined_df['chg_capacity_uah'] / 1e3
        if 'dchg_capacity_uah' in combined_df.columns:
            combined_df['dchg_capacity_mah'] = combined_df['dchg_capacity_uah'] / 1e3
        
        logger.info(f"Loaded {len(combined_df)} rows from {channel_path.name}")
        return combined_df
    
    def load_all_channels(self) -> Dict[str, pd.DataFrame]:
        """Load data from all PNE channels."""
        pne_pattern = re.compile(r'M\d+Ch\d+')
        channels = []
        
        for item in self.data_path.iterdir():
            if item.is_dir() and pne_pattern.match(item.name):
                restore_path = item / "Restore"
                if restore_path.exists():
                    channels.append(item)
        
        if not channels:
            logger.warning("No PNE channels found")
            return {}
        
        logger.info(f"Found {len(channels)} PNE channels to load")
        
        for channel_path in channels:
            channel_name = channel_path.name
            self.channel_data[channel_name] = self.load_channel_data(channel_path)
        
        return self.channel_data


class ToyoLoader(BaseDataLoader):
    """Data loader for Toyo equipment (Toyo1 and Toyo2)."""
    
    def load_capacity_log(self, channel_path: Path) -> pd.DataFrame:
        """
        Load CAPACITY.LOG file from Toyo channel.
        
        Args:
            channel_path: Path to channel directory
            
        Returns:
            DataFrame with capacity log data
        """
        capacity_log_path = channel_path / "CAPACITY.LOG"
        
        if not capacity_log_path.exists():
            logger.warning(f"CAPACITY.LOG not found in {channel_path}")
            return pd.DataFrame()
        
        try:
            # Read CAPACITY.LOG
            df = pd.read_csv(capacity_log_path, encoding='utf-8')
            logger.info(f"Loaded CAPACITY.LOG from {channel_path.name}: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading CAPACITY.LOG from {channel_path}: {e}")
            return pd.DataFrame()
    
    def load_raw_data_files(self, channel_path: Path) -> pd.DataFrame:
        """
        Load raw data files (000001, 000002, etc.) from Toyo channel.
        
        Args:
            channel_path: Path to channel directory
            
        Returns:
            DataFrame with combined raw data
        """
        # Find all numbered files (no extension)
        raw_files = []
        for file_path in channel_path.iterdir():
            if file_path.is_file() and re.match(r'^\d{6}$', file_path.name):
                raw_files.append(file_path)
        
        raw_files.sort(key=lambda x: x.name)
        
        if not raw_files:
            logger.warning(f"No raw data files found in {channel_path}")
            return pd.DataFrame()
        
        data_frames = []
        logger.info(f"Loading {len(raw_files)} raw data files from {channel_path.name}")
        
        for file_path in tqdm(raw_files[:10], desc=f"Loading {channel_path.name}"):  # Limit to first 10 for testing
            try:
                # Read the file - format varies, try to auto-detect
                # First few lines might contain metadata
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Find where actual data starts (look for header line)
                data_start = 0
                for i, line in enumerate(lines):
                    if 'Date' in line or 'Time' in line or 'Voltage' in line:
                        data_start = i
                        break
                
                # Read data starting from header
                df = pd.read_csv(file_path, skiprows=data_start, encoding='utf-8')
                
                # Clean column names
                df.columns = [col.strip() for col in df.columns]
                
                data_frames.append(df)
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue
        
        if not data_frames:
            return pd.DataFrame()
        
        # Concatenate all data
        combined_df = pd.concat(data_frames, ignore_index=True)
        logger.info(f"Loaded {len(combined_df)} rows from raw files in {channel_path.name}")
        
        return combined_df
    
    def load_channel_data(self, channel_path: Path) -> pd.DataFrame:
        """
        Load data from a single Toyo channel.
        
        Args:
            channel_path: Path to channel directory
            
        Returns:
            DataFrame with channel data
        """
        # Load CAPACITY.LOG for summary
        capacity_df = self.load_capacity_log(channel_path)
        
        # Load raw data files for detailed data
        raw_df = self.load_raw_data_files(channel_path)
        
        # For now, return raw data if available, otherwise capacity log
        if not raw_df.empty:
            return raw_df
        else:
            return capacity_df
    
    def load_all_channels(self) -> Dict[str, pd.DataFrame]:
        """Load data from all Toyo channels."""
        channels = []
        
        for item in self.data_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                channels.append(item)
        
        if not channels:
            logger.warning("No Toyo channels found")
            return {}
        
        logger.info(f"Found {len(channels)} Toyo channels to load")
        
        for channel_path in channels:
            channel_name = f"Ch{channel_path.name}"
            self.channel_data[channel_name] = self.load_channel_data(channel_path)
        
        return self.channel_data


def get_data_loader(data_path: Union[str, Path], equipment_type: str) -> BaseDataLoader:
    """
    Get appropriate data loader based on equipment type.
    
    Args:
        data_path: Path to battery test data directory
        equipment_type: Type of equipment ("PNE", "Toyo", "Toyo1", "Toyo2")
        
    Returns:
        Data loader instance
    """
    if equipment_type == "PNE":
        return PNELoader(data_path)
    elif equipment_type in ["Toyo", "Toyo1", "Toyo2"]:
        return ToyoLoader(data_path)
    else:
        raise ValueError(f"Unsupported equipment type: {equipment_type}")