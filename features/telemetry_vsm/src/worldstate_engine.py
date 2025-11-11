"""
WorldState Engine - Computes 60+ features from telemetry parquet data.
Implements on-demand computation for flexible time windows.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path


class WorldStateEngine:
    """
    Computes 60+ WorldState features from telemetry parquet data.
    Implements on-demand computation for flexible time windows.
    """
    
    def __init__(self, parquet_path: str):
        """
        Initialize WorldState Engine.
        
        Args:
            parquet_path: Path to parquet file with telemetry data
        """
        self.parquet_path = Path(parquet_path)
        if not self.parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
        self._df = None  # Lazy load
    
    def _load_data(self) -> pd.DataFrame:
        """Lazy load parquet file"""
        if self._df is None:
            self._df = pd.read_parquet(self.parquet_path)
            # Ensure index is datetime
            if not isinstance(self._df.index, pd.DatetimeIndex):
                raise ValueError("Parquet file must have DatetimeIndex")
        return self._df
    
    def compute_worldstate(
        self,
        asset_id: str,
        timestamp: datetime,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Compute WorldState features for given time window.
        
        Args:
            asset_id: Asset identifier (e.g., "135_1570")
            timestamp: Point in time for state computation
            window_minutes: Time window in minutes (default: 60)
        
        Returns:
            Dict with:
            - current_state: Latest sensor values
            - trends_30m: 30-minute aggregates
            - trends_2h: 2-hour aggregates
            - trends_24h: 24-hour aggregates (optional)
            - flags: Boolean indicators
            - incidents: Derived incident features
            - health_scores: Composite health metrics
        """
        df = self._load_data()
        
        # Filter time window
        end_time = timestamp
        start_time = timestamp - timedelta(minutes=window_minutes)
        
        # Use boolean indexing to handle duplicate timestamps
        mask = (df.index >= start_time) & (df.index <= end_time)
        window_df = df.loc[mask].copy()
        
        if len(window_df) == 0:
            raise ValueError(f"No data found for time window {start_time} to {end_time}")
        
        # Compute features
        worldstate = {
            "asset_id": asset_id,
            "timestamp": timestamp.isoformat(),
            "current_state": self._compute_current_state(window_df),
            "trends_30m": self._compute_trends_30m(window_df),
            "trends_2h": self._compute_trends_2h(df, timestamp),
            "trends_24h": self._compute_trends_24h(df, timestamp),
            "flags": self._compute_flags(window_df),
            "incidents": self._compute_incidents(window_df, df, timestamp),
            "health_scores": self._compute_health_scores(window_df, df, timestamp),
            "context": self._compute_context_features(timestamp, window_df)
        }
        
        return worldstate
    
    def _compute_current_state(self, df: pd.DataFrame) -> Dict:
        """Latest sensor values - Section 1 from telemetry_features.md"""
        latest = df.iloc[-1]
        
        # Handle NaN values
        def safe_float(val):
            return float(val) if pd.notna(val) else None
        
        def safe_bool(val):
            return bool(val > 0.5) if pd.notna(val) else False
        
        return {
            "current_room_temp": safe_float(latest['sGekoeldeRuimte']),
            "current_room_temp_secondary": safe_float(latest.get('p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive')),
            "current_hot_gas_temp": safe_float(latest['sHeetgasLeiding']),
            "current_liquid_temp": safe_float(latest['sVloeistofleiding']),
            "current_suction_temp": safe_float(latest['sZuigleiding']),
            "current_ambient_temp": safe_float(latest['sOmgeving']),
            "current_door_open": safe_bool(latest['sDeurcontact']),
            "current_rssi": safe_float(latest['sRSSI']),
            "current_battery": safe_float(latest['sBattery'])
        }
    
    def _compute_trends_30m(self, df: pd.DataFrame) -> Dict:
        """30-minute aggregates - Section 2.1 from telemetry_features.md"""
        if len(df) == 0:
            return {}
        
        room_temp = df['sGekoeldeRuimte'].dropna()
        door_contact = df['sDeurcontact'].dropna()
        
        if len(room_temp) == 0:
            return {}
        
        # Door opening events (transitions 0→1)
        door_diff = door_contact.diff()
        door_open_count = int((door_diff > 0).sum()) if len(door_diff) > 0 else 0
        
        return {
            "room_temp_min_30m": float(room_temp.min()) if len(room_temp) > 0 else None,
            "room_temp_max_30m": float(room_temp.max()) if len(room_temp) > 0 else None,
            "room_temp_mean_30m": float(room_temp.mean()) if len(room_temp) > 0 else None,
            "room_temp_std_30m": float(room_temp.std()) if len(room_temp) > 0 else None,
            "room_temp_delta_30m": float(room_temp.iloc[-1] - room_temp.iloc[0]) if len(room_temp) > 1 else 0.0,
            "door_open_ratio_30m": float(door_contact.mean()) if len(door_contact) > 0 else 0.0,
            "door_open_count_30m": door_open_count
        }
    
    def _compute_trends_2h(self, full_df: pd.DataFrame, timestamp: datetime) -> Dict:
        """2-hour aggregates - Section 2.2 from telemetry_features.md"""
        start = timestamp - timedelta(hours=2)
        # Use boolean indexing to handle duplicate timestamps
        mask = (full_df.index >= start) & (full_df.index <= timestamp)
        df_2h = full_df.loc[mask].copy()
        
        if len(df_2h) < 10:
            return {}
        
        room_temp = df_2h['sGekoeldeRuimte'].dropna()
        hot_gas = df_2h['sHeetgasLeiding'].dropna()
        ambient = df_2h['sOmgeving'].dropna()
        door_contact = df_2h['sDeurcontact'].dropna()
        
        return {
            "room_temp_min_2h": float(room_temp.min()) if len(room_temp) > 0 else None,
            "room_temp_max_2h": float(room_temp.max()) if len(room_temp) > 0 else None,
            "room_temp_mean_2h": float(room_temp.mean()) if len(room_temp) > 0 else None,
            "room_temp_trend_2h": self._compute_linear_trend(room_temp) if len(room_temp) > 1 else 0.0,
            "hot_gas_mean_2h": float(hot_gas.mean()) if len(hot_gas) > 0 else None,
            "hot_gas_std_2h": float(hot_gas.std()) if len(hot_gas) > 0 else None,
            "ambient_mean_2h": float(ambient.mean()) if len(ambient) > 0 else None,
            "door_open_ratio_2h": float(door_contact.mean()) if len(door_contact) > 0 else 0.0
        }
    
    def _compute_trends_24h(self, full_df: pd.DataFrame, timestamp: datetime) -> Dict:
        """24-hour aggregates - Section 2.3 from telemetry_features.md"""
        start = timestamp - timedelta(hours=24)
        # Use boolean indexing to handle duplicate timestamps
        mask = (full_df.index >= start) & (full_df.index <= timestamp)
        df_24h = full_df.loc[mask].copy()
        
        if len(df_24h) < 60:  # Require at least 1 hour of data
            return {}
        
        room_temp = df_24h['sGekoeldeRuimte'].dropna()
        hot_gas = df_24h['sHeetgasLeiding'].dropna()
        door_contact = df_24h['sDeurcontact'].dropna()
        
        # Temperature violations (> -18°C)
        temp_violations = (room_temp > -18.0).sum()
        temp_violations_hours = temp_violations / 60.0  # Convert minutes to hours
        
        # Compressor runtime (hot gas > 35°C)
        compressor_runtime = (hot_gas > 35.0).sum()
        compressor_runtime_hours = compressor_runtime / 60.0
        
        # Compressor cycles (transitions low→high)
        hot_gas_diff = hot_gas.diff()
        compressor_cycles = int((hot_gas_diff > 10).sum())  # Threshold: 10°C increase
        
        # Door opening events
        door_diff = door_contact.diff()
        door_open_total = int((door_diff > 0).sum())
        
        return {
            "room_temp_min_24h": float(room_temp.min()) if len(room_temp) > 0 else None,
            "room_temp_max_24h": float(room_temp.max()) if len(room_temp) > 0 else None,
            "room_temp_mean_24h": float(room_temp.mean()) if len(room_temp) > 0 else None,
            "temp_violations_24h": float(temp_violations_hours),
            "compressor_runtime_24h": float(compressor_runtime_hours),
            "compressor_cycle_count_24h": compressor_cycles,
            "door_open_ratio_24h": float(door_contact.mean()) if len(door_contact) > 0 else 0.0,
            "door_open_total_24h": door_open_total
        }
    
    def _compute_linear_trend(self, series: pd.Series) -> float:
        """Compute linear trend (°C/hour)"""
        if len(series) < 2:
            return 0.0
        x = np.arange(len(series))
        y = series.values
        # Handle NaN values
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return 0.0
        x_clean = x[mask]
        y_clean = y[mask]
        slope = np.polyfit(x_clean, y_clean, 1)[0]
        # Convert to °C/hour (assuming 1-minute intervals)
        return float(slope * 60)
    
    def _compute_flags(self, df: pd.DataFrame) -> Dict:
        """Boolean flags - Section 3.1 from telemetry_features.md"""
        latest = df.iloc[-1]
        
        return {
            "flag_secondary_error": bool(latest.get('_flag_secondary_error_code', False)),
            "flag_main_temp_high": bool(latest.get('_flag_main_temp_high', False)),
            "flag_hot_gas_low": bool(latest.get('_flag_hot_gas_low', False)),
            "flag_liquid_extreme": bool(latest.get('_flag_liquid_extreme', False)),
            "flag_suction_extreme": bool(latest.get('_flag_suction_extreme', False)),
            "flag_ambient_extreme": bool(latest.get('_flag_ambient_extreme', False))
        }
    
    def _compute_incidents(self, window_df: pd.DataFrame, full_df: pd.DataFrame, timestamp: datetime) -> Dict:
        """Derived incidents - Section 3.2 from telemetry_features.md"""
        latest = window_df.iloc[-1]
        room_temp = latest.get('sGekoeldeRuimte')
        hot_gas = latest.get('sHeetgasLeiding')
        ambient_temp = latest.get('sOmgeving')
        rssi = latest.get('sRSSI')
        battery = latest.get('sBattery')
        
        # Compute 2h trend for is_temp_rising
        start_2h = timestamp - timedelta(hours=2)
        mask_2h = (full_df.index >= start_2h) & (full_df.index <= timestamp)
        df_2h = full_df.loc[mask_2h]
        room_temp_2h = df_2h['sGekoeldeRuimte'].dropna()
        trend_2h = self._compute_linear_trend(room_temp_2h) if len(room_temp_2h) > 1 else 0.0
        
        # Door stuck open (30m ratio > 0.8)
        door_ratio_30m = window_df['sDeurcontact'].mean() if len(window_df) > 0 else 0.0
        
        # Recent errors (flags in last 2h)
        flag_cols = [col for col in df_2h.columns if col.startswith('_flag_')]
        has_recent_errors = bool(df_2h[flag_cols].any().any()) if flag_cols else False
        
        # Error duration (minutes since first error flag)
        error_duration = 0
        if has_recent_errors:
            # Find first True flag in 2h window
            for col in flag_cols:
                error_rows = df_2h[df_2h[col] == True]
                if len(error_rows) > 0:
                    first_error_time = error_rows.index[0]
                    duration = (timestamp - first_error_time).total_seconds() / 60.0
                    error_duration = max(error_duration, duration)
                    break
        
        return {
            "is_temp_critical": bool(room_temp > -10) if pd.notna(room_temp) else False,
            "is_temp_warning": bool(room_temp > -18) if pd.notna(room_temp) else False,
            "is_temp_rising": bool(trend_2h > 0.5),
            "is_compressor_inactive": bool(hot_gas < 30) if pd.notna(hot_gas) else False,
            "is_door_stuck_open": bool(door_ratio_30m > 0.8),
            "has_recent_errors": has_recent_errors,
            "error_duration_current": float(error_duration),
            "is_ambient_high": bool(ambient_temp > 35) if pd.notna(ambient_temp) else False,
            "is_sensor_communication_poor": bool((pd.notna(rssi) and rssi < -90) or (pd.notna(battery) and battery < 20))
        }
    
    def _compute_health_scores(self, window_df: pd.DataFrame, full_df: pd.DataFrame, timestamp: datetime) -> Dict:
        """Health scores - Section 4 from telemetry_features.md"""
        latest = window_df.iloc[-1]
        room_temp = latest.get('sGekoeldeRuimte')
        hot_gas = latest.get('sHeetgasLeiding')
        
        # Cooling Performance Score
        target_temp = -34.0
        if pd.notna(room_temp):
            temp_deviation = abs(room_temp - target_temp) / 20.0  # Normalize to 0-1
            temp_deviation = min(1.0, temp_deviation)  # Cap at 1.0
        else:
            temp_deviation = 1.0
        
        # Temperature trend (2h)
        start_2h = timestamp - timedelta(hours=2)
        mask_2h = (full_df.index >= start_2h) & (full_df.index <= timestamp)
        df_2h = full_df.loc[mask_2h]
        room_temp_2h = df_2h['sGekoeldeRuimte'].dropna()
        trend_2h = self._compute_linear_trend(room_temp_2h) if len(room_temp_2h) > 1 else 0.0
        trend_factor = min(1.0, max(0.0, trend_2h / 5.0)) if trend_2h > 0 else 0.0  # Normalize
        
        # Recent flags
        flag_cols = [col for col in df_2h.columns if col.startswith('_flag_')]
        flag_factor = 0.2 if df_2h[flag_cols].any().any() else 0.0
        
        # Ambient stress
        ambient = latest.get('sOmgeving')
        ambient_factor = 0.1 if (pd.notna(ambient) and ambient > 35) else 0.0
        
        cooling_performance = 100 * (1 - (0.4 * temp_deviation + 0.3 * trend_factor + 0.2 * flag_factor + 0.1 * ambient_factor))
        cooling_performance = max(0, min(100, int(cooling_performance)))
        
        # Compressor Health Score
        if pd.notna(hot_gas):
            hot_gas_deviation = abs(hot_gas - 50.0) / 30.0  # Normalize
            hot_gas_deviation = min(1.0, hot_gas_deviation)
        else:
            hot_gas_deviation = 1.0
        
        # Cycling (2h window)
        hot_gas_2h = df_2h['sHeetgasLeiding'].dropna()
        cycles_per_hour = 0.0
        if len(hot_gas_2h) > 1:
            hot_gas_diff = hot_gas_2h.diff()
            cycles = (hot_gas_diff > 10).sum()
            cycles_per_hour = cycles / 2.0  # 2h window
        cycling_factor = min(1.0, max(0.0, (cycles_per_hour - 10) / 10.0)) if cycles_per_hour > 10 else 0.0
        
        # Low hot gas
        low_hot_gas_factor = 0.3 if (pd.notna(hot_gas) and hot_gas < 35) else 0.0
        
        # Variability
        hot_gas_std = hot_gas_2h.std() if len(hot_gas_2h) > 0 else 0.0
        variability_factor = min(1.0, hot_gas_std / 20.0) * 0.1
        
        compressor_health = 100 * (1 - (0.3 * hot_gas_deviation + 0.3 * cycling_factor + 0.3 * low_hot_gas_factor + 0.1 * variability_factor))
        compressor_health = max(0, min(100, int(compressor_health)))
        
        # System Stability Score
        room_temp_std = window_df['sGekoeldeRuimte'].std() if len(window_df) > 0 else 0.0
        stability_factor = min(1.0, room_temp_std / 10.0)
        flag_frequency = df_2h[flag_cols].any(axis=1).sum() / len(df_2h) if len(df_2h) > 0 else 0.0
        
        system_stability = 100 * (1 - (0.6 * stability_factor + 0.4 * flag_frequency))
        system_stability = max(0, min(100, int(system_stability)))
        
        # Data Quality Score
        rssi = latest.get('sRSSI')
        battery = latest.get('sBattery')
        missing_ratio = window_df.isnull().sum().sum() / (len(window_df) * len(window_df.columns)) if len(window_df) > 0 else 0.0
        
        rssi_factor = 0.0 if (pd.notna(rssi) and rssi < -90) else 0.0
        battery_factor = 0.0 if (pd.notna(battery) and battery < 20) else 0.0
        
        data_quality = 100 * (1 - (0.5 * missing_ratio + 0.25 * rssi_factor + 0.25 * battery_factor))
        data_quality = max(0, min(100, int(data_quality)))
        
        return {
            "cooling_performance_score": cooling_performance,
            "compressor_health_score": compressor_health,
            "system_stability_score": system_stability,
            "data_quality_score": data_quality
        }
    
    def _compute_context_features(self, timestamp: datetime, window_df: pd.DataFrame) -> Dict:
        """Context features - Section 5 from telemetry_features.md"""
        # Time since last measurement
        if len(window_df) > 0:
            last_measurement = window_df.index[-1]
            time_since_last = (timestamp - last_measurement).total_seconds() / 60.0
        else:
            time_since_last = None
        
        # Hour and day
        hour_of_day = timestamp.hour
        day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
        
        # Business hours (Mon-Fri 8am-6pm)
        is_business_hours = (day_of_week < 5) and (8 <= hour_of_day < 18)
        
        # Time since last door event
        door_contact = window_df['sDeurcontact'].dropna()
        time_since_door_event = None
        if len(door_contact) > 1:
            door_diff = door_contact.diff()
            door_events = door_contact[door_diff != 0]
            if len(door_events) > 0:
                last_door_event_time = door_events.index[-1]
                time_since_door_event = (timestamp - last_door_event_time).total_seconds() / 60.0
        
        # Sensor data age (max time since measurement for any null)
        sensor_data_age_max = None
        if len(window_df) > 0:
            # Check for nulls in sensor columns
            sensor_cols = ['sGekoeldeRuimte', 'sHeetgasLeiding', 'sVloeistofleiding', 
                          'sZuigleiding', 'sOmgeving', 'sDeurcontact']
            max_age = 0.0
            for col in sensor_cols:
                if col in window_df.columns:
                    null_mask = window_df[col].isnull()
                    if null_mask.any():
                        # Find oldest null
                        null_times = window_df.index[null_mask]
                        if len(null_times) > 0:
                            oldest_null = null_times[0]
                            age = (timestamp - oldest_null).total_seconds() / 60.0
                            max_age = max(max_age, age)
            sensor_data_age_max = max_age if max_age > 0 else None
        
        return {
            "timestamp_current": timestamp.isoformat(),
            "time_since_last_measurement": float(time_since_last) if time_since_last is not None else None,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "is_business_hours": is_business_hours,
            "time_since_last_door_event": float(time_since_door_event) if time_since_door_event is not None else None,
            "sensor_data_age_max": float(sensor_data_age_max) if sensor_data_age_max is not None else None
        }

