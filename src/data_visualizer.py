"""
Data visualization module for battery test data.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


class BatteryDataVisualizer:
    """Visualizer for battery test data."""
    
    def __init__(self, data: pd.DataFrame, battery_info: Dict = None):
        """
        Initialize visualizer.
        
        Args:
            data: Battery test data DataFrame
            battery_info: Dictionary with battery information
        """
        self.data = data
        self.battery_info = battery_info or {}
        
    def plot_voltage_current_profile(self, cycle_number: Optional[int] = None, 
                                    save_path: Optional[str] = None):
        """
        Plot voltage and current profiles over time.
        
        Args:
            cycle_number: Specific cycle to plot (if None, plots all)
            save_path: Path to save the figure
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        # Filter data for specific cycle if requested
        plot_data = self.data
        if cycle_number is not None and 'current_cycle' in self.data.columns:
            plot_data = self.data[self.data['current_cycle'] == cycle_number]
            title_suffix = f" - Cycle {cycle_number}"
        else:
            title_suffix = ""
        
        # Determine time column
        time_col = None
        for col in ['tot_time_cs', 'PassTime[Sec]', 'time', 'TotlPassTime']:
            if col in plot_data.columns:
                time_col = col
                break
        
        if time_col is None:
            logger.warning("No time column found in data")
            return
        
        # Determine voltage column
        voltage_col = None
        for col in ['voltage_v', 'Voltage[V]', 'voltage_uv']:
            if col in plot_data.columns:
                voltage_col = col
                break
        
        # Determine current column
        current_col = None
        for col in ['current_ma', 'Current[mA]', 'current_ua']:
            if col in plot_data.columns:
                current_col = col
                break
        
        # Plot voltage
        if voltage_col:
            ax1.plot(plot_data[time_col], plot_data[voltage_col], 'b-', linewidth=0.5)
            ax1.set_ylabel('Voltage (V)', fontsize=12)
            ax1.set_title(f'Voltage Profile{title_suffix}', fontsize=14)
            ax1.grid(True, alpha=0.3)
        
        # Plot current
        if current_col:
            ax2.plot(plot_data[time_col], plot_data[current_col], 'r-', linewidth=0.5)
            ax2.set_ylabel('Current (mA)', fontsize=12)
            ax2.set_xlabel('Time', fontsize=12)
            ax2.set_title(f'Current Profile{title_suffix}', fontsize=14)
            ax2.grid(True, alpha=0.3)
        
        # Add battery info to title
        if self.battery_info:
            info_text = f"{self.battery_info.get('manufacturer', '')} {self.battery_info.get('model', '')} " \
                       f"{self.battery_info.get('capacity_mah', '')}mAh"
            fig.suptitle(info_text, fontsize=16, y=1.02)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved voltage-current profile to {save_path}")
        
        plt.show()
    
    def plot_capacity_fade(self, save_path: Optional[str] = None):
        """
        Plot capacity fade over cycles.
        
        Args:
            save_path: Path to save the figure
        """
        # Look for capacity columns
        chg_cap_col = None
        dchg_cap_col = None
        cycle_col = None
        
        for col in ['chg_capacity_mah', 'Cap[mAh]', 'chg_capacity_uah']:
            if col in self.data.columns:
                chg_cap_col = col
                break
        
        for col in ['dchg_capacity_mah', 'Cap[mAh]', 'dchg_capacity_uah']:
            if col in self.data.columns:
                dchg_cap_col = col
                break
        
        for col in ['total_cycle', 'TotlCycle', 'Cycle']:
            if col in self.data.columns:
                cycle_col = col
                break
        
        if not (chg_cap_col or dchg_cap_col) or not cycle_col:
            logger.warning("Required columns for capacity fade plot not found")
            return
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Group by cycle and get max capacity for each cycle
        if cycle_col in self.data.columns:
            cycle_data = self.data.groupby(cycle_col).agg({
                col: 'max' for col in [chg_cap_col, dchg_cap_col] 
                if col and col in self.data.columns
            }).reset_index()
            
            # Plot charge capacity
            if chg_cap_col in cycle_data.columns:
                ax.plot(cycle_data[cycle_col], cycle_data[chg_cap_col], 
                       'b-', marker='o', markersize=3, label='Charge Capacity')
            
            # Plot discharge capacity
            if dchg_cap_col in cycle_data.columns:
                ax.plot(cycle_data[cycle_col], cycle_data[dchg_cap_col], 
                       'r-', marker='s', markersize=3, label='Discharge Capacity')
            
            ax.set_xlabel('Cycle Number', fontsize=12)
            ax.set_ylabel('Capacity (mAh)', fontsize=12)
            ax.set_title('Capacity Fade Over Cycles', fontsize=14)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            # Add battery info
            if self.battery_info:
                info_text = f"{self.battery_info.get('manufacturer', '')} {self.battery_info.get('model', '')} " \
                           f"{self.battery_info.get('capacity_mah', '')}mAh"
                ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                       fontsize=10, verticalalignment='top')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved capacity fade plot to {save_path}")
        
        plt.show()
    
    def plot_cycle_statistics(self, save_path: Optional[str] = None):
        """
        Plot cycle statistics including efficiency and energy.
        
        Args:
            save_path: Path to save the figure
        """
        cycle_col = None
        for col in ['total_cycle', 'TotlCycle', 'Cycle']:
            if col in self.data.columns:
                cycle_col = col
                break
        
        if not cycle_col:
            logger.warning("Cycle column not found for statistics plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Calculate cycle statistics
        cycle_stats = self.data.groupby(cycle_col).agg({
            col: ['mean', 'max', 'min'] for col in self.data.columns 
            if any(keyword in col.lower() for keyword in ['capacity', 'energy', 'voltage', 'current'])
        })
        
        # Plot 1: Coulombic Efficiency
        ax = axes[0, 0]
        if 'chg_capacity_mah' in self.data.columns and 'dchg_capacity_mah' in self.data.columns:
            chg_cap = self.data.groupby(cycle_col)['chg_capacity_mah'].max()
            dchg_cap = self.data.groupby(cycle_col)['dchg_capacity_mah'].max()
            efficiency = (dchg_cap / chg_cap * 100).replace([np.inf, -np.inf], np.nan)
            ax.plot(efficiency.index, efficiency.values, 'g-', marker='o', markersize=3)
            ax.set_ylabel('Coulombic Efficiency (%)')
            ax.set_title('Coulombic Efficiency')
            ax.grid(True, alpha=0.3)
        
        # Plot 2: Energy
        ax = axes[0, 1]
        for col in ['chg_wh', 'Pow[mWh]', 'chg_power_mw']:
            if col in self.data.columns:
                energy_data = self.data.groupby(cycle_col)[col].max()
                ax.plot(energy_data.index, energy_data.values, marker='o', markersize=3, label=col)
        ax.set_ylabel('Energy')
        ax.set_title('Energy per Cycle')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Plot 3: Average Voltage
        ax = axes[1, 0]
        for col in ['avg_voltage_uv', 'AveVolt[V]', 'voltage_v']:
            if col in self.data.columns:
                if 'uv' in col:
                    voltage_data = self.data.groupby(cycle_col)[col].mean() / 1e6
                else:
                    voltage_data = self.data.groupby(cycle_col)[col].mean()
                ax.plot(voltage_data.index, voltage_data.values, marker='o', markersize=3)
                ax.set_ylabel('Average Voltage (V)')
                ax.set_title('Average Voltage per Cycle')
                ax.grid(True, alpha=0.3)
                break
        
        # Plot 4: Temperature (if available)
        ax = axes[1, 1]
        temp_cols = [col for col in self.data.columns if 'temp' in col.lower()]
        if temp_cols:
            for temp_col in temp_cols[:3]:  # Limit to 3 temperature sensors
                temp_data = self.data.groupby(cycle_col)[temp_col].mean()
                ax.plot(temp_data.index, temp_data.values, marker='o', markersize=3, label=temp_col)
            ax.set_ylabel('Temperature (°C)')
            ax.set_title('Average Temperature per Cycle')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
        
        # Set common x-label
        for ax in axes.flat:
            ax.set_xlabel('Cycle Number')
        
        # Add battery info
        if self.battery_info:
            info_text = f"{self.battery_info.get('manufacturer', '')} {self.battery_info.get('model', '')} " \
                       f"{self.battery_info.get('capacity_mah', '')}mAh"
            fig.suptitle(info_text, fontsize=16, y=1.02)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved cycle statistics to {save_path}")
        
        plt.show()
    
    def plot_channel_comparison(self, channels: List[str] = None, 
                               save_path: Optional[str] = None):
        """
        Compare data across different channels.
        
        Args:
            channels: List of channel names to compare
            save_path: Path to save the figure
        """
        if 'channel' not in self.data.columns:
            logger.warning("Channel column not found in data")
            return
        
        available_channels = self.data['channel'].unique()
        
        if channels:
            channels = [ch for ch in channels if ch in available_channels]
        else:
            channels = available_channels[:5]  # Limit to 5 channels for clarity
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot capacity comparison
        ax = axes[0]
        for channel in channels:
            channel_data = self.data[self.data['channel'] == channel]
            
            # Find cycle and capacity columns
            cycle_col = None
            cap_col = None
            
            for col in ['total_cycle', 'TotlCycle', 'Cycle']:
                if col in channel_data.columns:
                    cycle_col = col
                    break
            
            for col in ['dchg_capacity_mah', 'Cap[mAh]']:
                if col in channel_data.columns:
                    cap_col = col
                    break
            
            if cycle_col and cap_col:
                cycle_cap = channel_data.groupby(cycle_col)[cap_col].max()
                ax.plot(cycle_cap.index, cycle_cap.values, marker='o', 
                       markersize=3, label=channel, alpha=0.7)
        
        ax.set_xlabel('Cycle Number')
        ax.set_ylabel('Discharge Capacity (mAh)')
        ax.set_title('Capacity Comparison Across Channels')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Plot capacity retention comparison
        ax = axes[1]
        for channel in channels:
            channel_data = self.data[self.data['channel'] == channel]
            
            if cycle_col and cap_col:
                cycle_cap = channel_data.groupby(cycle_col)[cap_col].max()
                if len(cycle_cap) > 0:
                    initial_cap = cycle_cap.iloc[0] if len(cycle_cap) > 0 else 1
                    retention = (cycle_cap / initial_cap * 100)
                    ax.plot(retention.index, retention.values, marker='o', 
                           markersize=3, label=channel, alpha=0.7)
        
        ax.set_xlabel('Cycle Number')
        ax.set_ylabel('Capacity Retention (%)')
        ax.set_title('Capacity Retention Comparison')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=80, color='r', linestyle='--', alpha=0.5, label='80% Retention')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved channel comparison to {save_path}")
        
        plt.show()