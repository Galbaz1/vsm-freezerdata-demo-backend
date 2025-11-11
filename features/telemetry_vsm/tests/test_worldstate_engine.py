"""
Unit tests for WorldStateEngine.
Tests feature computation, edge cases, and performance.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine


# Test data path
PARQUET_FILE = "features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet"


@pytest.fixture
def engine():
    """Create WorldStateEngine instance"""
    return WorldStateEngine(PARQUET_FILE)


@pytest.fixture
def sample_timestamp():
    """Sample timestamp from the middle of the dataset"""
    # Use a timestamp that should have data
    return datetime(2023, 6, 15, 12, 0)


class TestWorldStateEngine:
    """Test WorldStateEngine class"""
    
    def test_init(self, engine):
        """Test engine initialization"""
        assert engine.parquet_path.exists()
        assert engine._df is None  # Lazy loading
    
    def test_lazy_load(self, engine):
        """Test lazy loading of parquet file"""
        assert engine._df is None
        df = engine._load_data()
        assert engine._df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
    
    def test_compute_worldstate_basic(self, engine, sample_timestamp):
        """Test basic WorldState computation"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        
        # Check structure
        assert "asset_id" in worldstate
        assert "timestamp" in worldstate
        assert "current_state" in worldstate
        assert "trends_30m" in worldstate
        assert "trends_2h" in worldstate
        assert "trends_24h" in worldstate
        assert "flags" in worldstate
        assert "incidents" in worldstate
        assert "health_scores" in worldstate
        assert "context" in worldstate
        
        assert worldstate["asset_id"] == "135_1570"
    
    def test_current_state_features(self, engine, sample_timestamp):
        """Test current state feature computation"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        current = worldstate["current_state"]
        
        # Check all current state features exist
        assert "current_room_temp" in current
        assert "current_hot_gas_temp" in current
        assert "current_liquid_temp" in current
        assert "current_suction_temp" in current
        assert "current_ambient_temp" in current
        assert "current_door_open" in current
        assert "current_rssi" in current
        assert "current_battery" in current
        
        # Check types
        assert isinstance(current["current_door_open"], bool)
        if current["current_room_temp"] is not None:
            assert isinstance(current["current_room_temp"], float)
    
    def test_trends_30m_features(self, engine, sample_timestamp):
        """Test 30-minute trend features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        trends_30m = worldstate["trends_30m"]
        
        # Check features exist
        assert "room_temp_min_30m" in trends_30m
        assert "room_temp_max_30m" in trends_30m
        assert "room_temp_mean_30m" in trends_30m
        assert "room_temp_std_30m" in trends_30m
        assert "room_temp_delta_30m" in trends_30m
        assert "door_open_ratio_30m" in trends_30m
        assert "door_open_count_30m" in trends_30m
        
        # Check logical consistency
        if trends_30m["room_temp_min_30m"] is not None and trends_30m["room_temp_max_30m"] is not None:
            assert trends_30m["room_temp_min_30m"] <= trends_30m["room_temp_max_30m"]
        
        assert 0.0 <= trends_30m["door_open_ratio_30m"] <= 1.0
        assert trends_30m["door_open_count_30m"] >= 0
    
    def test_trends_2h_features(self, engine, sample_timestamp):
        """Test 2-hour trend features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        trends_2h = worldstate["trends_2h"]
        
        # May be empty if insufficient data
        if len(trends_2h) > 0:
            assert "room_temp_min_2h" in trends_2h
            assert "room_temp_max_2h" in trends_2h
            assert "room_temp_mean_2h" in trends_2h
            assert "room_temp_trend_2h" in trends_2h
            assert "hot_gas_mean_2h" in trends_2h
            assert "hot_gas_std_2h" in trends_2h
            assert "ambient_mean_2h" in trends_2h
            assert "door_open_ratio_2h" in trends_2h
    
    def test_trends_24h_features(self, engine, sample_timestamp):
        """Test 24-hour trend features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        trends_24h = worldstate["trends_24h"]
        
        # May be empty if insufficient data
        if len(trends_24h) > 0:
            assert "room_temp_min_24h" in trends_24h
            assert "room_temp_max_24h" in trends_24h
            assert "room_temp_mean_24h" in trends_24h
            assert "temp_violations_24h" in trends_24h
            assert "compressor_runtime_24h" in trends_24h
            assert "compressor_cycle_count_24h" in trends_24h
            assert "door_open_ratio_24h" in trends_24h
            assert "door_open_total_24h" in trends_24h
    
    def test_flags_features(self, engine, sample_timestamp):
        """Test flag features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        flags = worldstate["flags"]
        
        assert "flag_secondary_error" in flags
        assert "flag_main_temp_high" in flags
        assert "flag_hot_gas_low" in flags
        assert "flag_liquid_extreme" in flags
        assert "flag_suction_extreme" in flags
        assert "flag_ambient_extreme" in flags
        
        # All flags should be boolean
        for flag_value in flags.values():
            assert isinstance(flag_value, bool)
    
    def test_incidents_features(self, engine, sample_timestamp):
        """Test incident features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        incidents = worldstate["incidents"]
        
        assert "is_temp_critical" in incidents
        assert "is_temp_warning" in incidents
        assert "is_temp_rising" in incidents
        assert "is_compressor_inactive" in incidents
        assert "is_door_stuck_open" in incidents
        assert "has_recent_errors" in incidents
        assert "error_duration_current" in incidents
        assert "is_ambient_high" in incidents
        assert "is_sensor_communication_poor" in incidents
        
        # Check types
        for key in ["is_temp_critical", "is_temp_warning", "is_temp_rising", 
                   "is_compressor_inactive", "is_door_stuck_open", "has_recent_errors",
                   "is_ambient_high", "is_sensor_communication_poor"]:
            assert isinstance(incidents[key], bool)
        
        assert isinstance(incidents["error_duration_current"], float)
        assert incidents["error_duration_current"] >= 0
    
    def test_health_scores_features(self, engine, sample_timestamp):
        """Test health score features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        health = worldstate["health_scores"]
        
        assert "cooling_performance_score" in health
        assert "compressor_health_score" in health
        assert "system_stability_score" in health
        assert "data_quality_score" in health
        
        # Scores should be 0-100
        for score_value in health.values():
            assert isinstance(score_value, int)
            assert 0 <= score_value <= 100
    
    def test_context_features(self, engine, sample_timestamp):
        """Test context features"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        context = worldstate["context"]
        
        assert "timestamp_current" in context
        assert "time_since_last_measurement" in context
        assert "hour_of_day" in context
        assert "day_of_week" in context
        assert "is_business_hours" in context
        assert "time_since_last_door_event" in context
        assert "sensor_data_age_max" in context
        
        # Check types and ranges
        assert isinstance(context["hour_of_day"], int)
        assert 0 <= context["hour_of_day"] <= 23
        
        assert isinstance(context["day_of_week"], int)
        assert 0 <= context["day_of_week"] <= 6
        
        assert isinstance(context["is_business_hours"], bool)
    
    def test_empty_window_error(self, engine):
        """Test error handling for empty time window"""
        # Use a timestamp far in the future
        future_timestamp = datetime(2030, 1, 1, 12, 0)
        
        with pytest.raises(ValueError, match="No data found"):
            engine.compute_worldstate("135_1570", future_timestamp, 60)
    
    def test_file_not_found_error(self):
        """Test error handling for missing parquet file"""
        with pytest.raises(FileNotFoundError):
            WorldStateEngine("nonexistent_file.parquet")
    
    def test_performance_60min_window(self, engine, sample_timestamp):
        """Test performance: <500ms for 60min window"""
        import time
        
        start = time.time()
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        elapsed = time.time() - start
        
        assert elapsed < 0.5, f"Computation took {elapsed:.3f}s, expected <0.5s"
        assert worldstate is not None
    
    def test_different_window_sizes(self, engine, sample_timestamp):
        """Test different window sizes"""
        for window in [30, 60, 120]:
            worldstate = engine.compute_worldstate("135_1570", sample_timestamp, window)
            assert worldstate is not None
            assert worldstate["asset_id"] == "135_1570"
    
    def test_linear_trend_calculation(self, engine):
        """Test linear trend calculation"""
        # Create a simple series with known trend
        series = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
        trend = engine._compute_linear_trend(series)
        
        # Should be approximately 1.0 per unit (60 per hour)
        assert abs(trend - 60.0) < 1.0
        
        # Test with NaN values
        series_with_nan = pd.Series([10.0, np.nan, 12.0, np.nan, 14.0])
        trend_nan = engine._compute_linear_trend(series_with_nan)
        assert isinstance(trend_nan, float)
    
    def test_feature_count(self, engine, sample_timestamp):
        """Verify all 60+ features are computed"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        
        # Count features in each section
        current_count = len(worldstate["current_state"])
        trends_30m_count = len(worldstate["trends_30m"])
        trends_2h_count = len(worldstate["trends_2h"]) if worldstate["trends_2h"] else 0
        trends_24h_count = len(worldstate["trends_24h"]) if worldstate["trends_24h"] else 0
        flags_count = len(worldstate["flags"])
        incidents_count = len(worldstate["incidents"])
        health_count = len(worldstate["health_scores"])
        context_count = len(worldstate["context"])
        
        total_features = (current_count + trends_30m_count + trends_2h_count + 
                         trends_24h_count + flags_count + incidents_count + 
                         health_count + context_count)
        
        # Should have at least 60 features
        assert total_features >= 60, f"Only {total_features} features computed, expected >=60"
    
    def test_nan_handling(self, engine, sample_timestamp):
        """Test handling of NaN values in data"""
        worldstate = engine.compute_worldstate("135_1570", sample_timestamp, 60)
        
        # Should not raise errors even with NaN values
        assert worldstate is not None
        
        # Current state should handle NaN gracefully
        current = worldstate["current_state"]
        for key, value in current.items():
            if value is not None:
                if key == "current_door_open":
                    assert isinstance(value, bool)
                else:
                    assert isinstance(value, (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

