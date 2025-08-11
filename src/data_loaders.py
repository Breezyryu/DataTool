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
    
    # PNE column mapping based on documentation (46개 컬럼)
    COLUMN_NAMES = [
        'Index',                    # 0: Index
        'Default',                  # 1: default(2)
        'Step_Type',                # 2: Step_type (1:충전, 2:방전, 3:휴지, 4:OCV, 5:Impedance, 8:loop)
        'ChgDchg',                  # 3: ChgDchg (1:CV, 2:CC, 255:rest)
        'Current_App_Class',        # 4: Current application classification (1:전류 비인가 직전 포인트, 2:전류인가)
        'CCCV',                     # 5: CCCV (0:CC, 1:CV)
        'End_State',                # 6: EndState (0:Pattern 시작, 64:휴지, 65:CC, 66:CV, 69:Pattern종료, 78:용량)
        'Step_Count',               # 7: Step count (CC/CCCV/Rest/Loop)
        'Voltage_uV',               # 8: Voltage[uV]
        'Current_uA',               # 9: Current[uA]
        'Chg_Capacity_uAh',         # 10: Chg Capacity(uAh) - step 충방전의 경우 합산 필요
        'Dchg_Capacity_uAh',        # 11: Dchg Capacity(uAh)
        'Chg_Power_mW',             # 12: Chg Power(mW)
        'Dchg_Power_mW',            # 13: Dchg Power(mW)
        'Chg_WattHour_Wh',          # 14: Chg WattHour(Wh)
        'Dchg_WattHour_Wh',         # 15: Dchg WattHour(Wh)
        'Repeat_Pattern_Count',     # 16: repeat pattern count (per 8 or 9) 0, 1, 2, ...
        'Step_Time_cs',             # 17: StepTime(1/100s)
        'Tot_Time_day',             # 18: TotTime(day)
        'Tot_Time_cs',              # 19: TotTime(/100s)
        'Impedance',                # 20: Impedance
        'Temperature_1',            # 21: Temperature
        'Temperature_2',            # 22: Temperature
        'Temperature_3',            # 23: Temperature
        'Temperature_4',            # 24: Temperature
        'Unknown_25',               # 25: ?2 or 0
        'Repeat_Count',             # 26: Repeat count
        'Total_Cycle',              # 27: TotalCycle
        'Current_Cycle',            # 28: Current Cycle
        'Avg_Voltage_uV',           # 29: Average Voltage(uV)
        'Avg_Current_uA',           # 30: Average Current(uA)
        'Col_31',                   # 31: -
        'CV_Section',               # 32: CV 구간
        'Date_YYYYMMDD',            # 33: Date(YYYY/MM/DD)
        'Time_HHmmss',              # 34: Time(HH/mm/ssss(/100s))
        'Col_35',                   # 35: -
        'Col_36',                   # 36: -
        'Col_37',                   # 37: -
        'Step_Info',                # 38: Step별?
        'CC_Charge',                # 39: CC 충전 ?
        'CV_Section_2',             # 40: CV 구간
        'Discharge',                # 41: 방전
        'Col_42',                   # 42: -
        'Avg_Voltage_Section',      # 43: 구간별 평균 전압
        'Cumulative_Step',          # 44: 누적 step
        'Voltage_Max_uV',           # 45: Voltage max(uV)
        'Voltage_Min_uV'            # 46: Voltage min(uV)
    ]
    
    def apply_column_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply proper column names with intelligent mapping for mismatched column counts.
        
        Args:
            df: DataFrame with numeric column indices
            
        Returns:
            DataFrame with meaningful column names
        """
        num_cols = len(df.columns)
        expected_cols = len(self.COLUMN_NAMES)
        
        if num_cols == expected_cols:
            # Perfect match - use all defined column names
            df.columns = self.COLUMN_NAMES
            logger.info(f"Applied {expected_cols} column names (perfect match)")
        elif num_cols < expected_cols:
            # Fewer columns than expected - use available column names
            df.columns = self.COLUMN_NAMES[:num_cols]
            logger.warning(f"Applied {num_cols} column names (expected {expected_cols})")
        else:
            # More columns than expected - use all defined names + extras
            extra_cols = [f'Extra_Col_{i+1}' for i in range(num_cols - expected_cols)]
            df.columns = self.COLUMN_NAMES + extra_cols
            logger.warning(f"Applied {expected_cols} defined + {len(extra_cols)} extra column names")
        
        return df
    
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
                
                # Apply column mapping intelligently
                df = self.apply_column_mapping(df)
                
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
    
    def remove_unnamed_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove unnamed or empty columns from DataFrame.
        
        Args:
            df: DataFrame with potential unnamed columns
            
        Returns:
            DataFrame with unnamed columns removed
        """
        columns_to_keep = []
        for col in df.columns:
            col_str = str(col).strip()
            # Keep columns that are not unnamed, empty, or NaN
            if not (col_str.startswith('Unnamed') or 
                   col_str == '' or 
                   col_str == 'nan' or 
                   pd.isna(col) or
                   col_str.lower() == 'none'):
                columns_to_keep.append(col)
        
        filtered_df = df[columns_to_keep]
        removed_count = len(df.columns) - len(columns_to_keep)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} unnamed/empty columns")
        
        return filtered_df
    
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
        
        for file_path in tqdm(raw_files, desc=f"Loading {channel_path.name}"):
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
                
                # Remove unnamed columns
                df = self.remove_unnamed_columns(df)
                
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
    
    def load_raw_data_only(self, channel_path: Path) -> pd.DataFrame:
        """
        Load only raw data files (000001, 000002, etc.) from Toyo channel.
        
        Args:
            channel_path: Path to channel directory
            
        Returns:
            DataFrame with combined raw data only
        """
        return self.load_raw_data_files(channel_path)
    
    def load_capacity_log_only(self, channel_path: Path) -> pd.DataFrame:
        """
        Load only CAPACITY.LOG file from Toyo channel.
        
        Args:
            channel_path: Path to channel directory
            
        Returns:
            DataFrame with capacity log data only
        """
        return self.load_capacity_log(channel_path)
    
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