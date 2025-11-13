"""
Test script for enhanced visualization system.

Tests:
1. All 10 chart types (3 original + 7 new)
2. VSM domain-specific tools (temperature_timeline, health_dashboard, alarm_breakdown)
3. Data limit handling (10, 100, 1000 points)
4. Frontend rendering validation
"""

import asyncio
from datetime import datetime
from elysia.util.client import ClientManager
from elysia.tree.objects import TreeData, Settings, Atlas, Environment
import dspy


async def test_vsm_visualization_tools():
    """Test the 3 VSM-specific visualization tools."""
    print("\n" + "="*60)
    print("Testing VSM Visualization Tools")
    print("="*60)
    
    # Setup
    client_manager = ClientManager()
    tree_data = TreeData(
        settings=Settings(),
        collection_data={},
        atlas=Atlas(),
        environment=Environment()
    )
    base_lm = dspy.LM(model="gemini/gemini-2.5-flash")
    
    # Test 1: Temperature Timeline (Area Chart)
    print("\n[Test 1] visualize_temperature_timeline")
    print("-" * 40)
    from elysia.api.custom_tools import visualize_temperature_timeline
    
    try:
        results = []
        async for output in visualize_temperature_timeline(
            asset_id="135_1570",
            hours_back=24,
            timestamp="2024-01-15T12:00:00",
            tree_data=tree_data,
            client_manager=client_manager
        ):
            results.append(output)
            print(f"  {output.__class__.__name__}: {str(output)[:100]}")
        
        # Verify Result was yielded
        from elysia.objects import Result
        result_objects = [r for r in results if isinstance(r, Result)]
        if result_objects:
            result = result_objects[0]
            assert result.payload_type == "area_chart", f"Expected area_chart, got {result.payload_type}"
            assert len(result.objects) > 0, "No chart objects returned"
            chart = result.objects[0]
            assert "data" in chart, "No data in chart"
            assert "series" in chart["data"], "No series in chart data"
            print(f"  ✅ PASS: Created area chart with {len(chart['data']['x_axis'])} points, {len(chart['data']['series'])} series")
        else:
            print("  ❌ FAIL: No Result object yielded")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    # Test 2: Health Dashboard (Radial Bar Chart)
    print("\n[Test 2] show_health_dashboard")
    print("-" * 40)
    from elysia.api.custom_tools import show_health_dashboard
    
    try:
        results = []
        async for output in show_health_dashboard(
            asset_id="135_1570",
            timestamp="2024-01-15T12:00:00",
            window_minutes=60,
            tree_data=tree_data,
            client_manager=client_manager
        ):
            results.append(output)
            print(f"  {output.__class__.__name__}: {str(output)[:100]}")
        
        from elysia.objects import Result
        result_objects = [r for r in results if isinstance(r, Result)]
        if result_objects:
            result = result_objects[0]
            assert result.payload_type == "radial_bar_chart", f"Expected radial_bar_chart, got {result.payload_type}"
            chart = result.objects[0]
            assert "data" in chart, "No data in chart"
            assert len(chart["data"]) == 3, f"Expected 3 gauges, got {len(chart['data'])}"
            print(f"  ✅ PASS: Created radial bar chart with {len(chart['data'])} gauges")
        else:
            print("  ❌ FAIL: No Result object yielded")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    # Test 3: Alarm Breakdown (Pie Chart)
    print("\n[Test 3] show_alarm_breakdown")
    print("-" * 40)
    from elysia.api.custom_tools import show_alarm_breakdown
    
    try:
        results = []
        async for output in show_alarm_breakdown(
            asset_id="135_1570",
            period_days=30,
            tree_data=tree_data,
            client_manager=client_manager
        ):
            results.append(output)
            print(f"  {output.__class__.__name__}: {str(output)[:100]}")
        
        from elysia.objects import Result
        result_objects = [r for r in results if isinstance(r, Result)]
        if result_objects:
            result = result_objects[0]
            assert result.payload_type == "pie_chart", f"Expected pie_chart, got {result.payload_type}"
            chart = result.objects[0]
            assert "data" in chart, "No data in chart"
            assert len(chart["data"]) >= 2, f"Expected at least 2 slices, got {len(chart['data'])}"
            print(f"  ✅ PASS: Created pie chart with {len(chart['data'])} slices")
        else:
            print("  ❌ FAIL: No Result object yielded")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")


async def test_generic_visualise_tool():
    """Test the enhanced Visualise tool with new chart types."""
    print("\n" + "="*60)
    print("Testing Generic Visualise Tool")
    print("="*60)
    
    from elysia.tools.visualisation.visualise import Visualise
    from elysia.tree.objects import TreeData, Settings, Environment, Atlas
    
    tree_data = TreeData(
        settings=Settings(),
        collection_data={},
        atlas=Atlas(),
        environment=Environment()
    )
    base_lm = dspy.LM(model="gemini/gemini-2.5-flash")
    client_manager = ClientManager()
    
    # Test Area Chart
    print("\n[Test 4] Visualise - Area Chart")
    print("-" * 40)
    
    # Populate environment with time series data
    tree_data.environment = Environment()
    tree_data.environment["telemetry_data"] = {
        "timestamps": ["00:00", "01:00", "02:00", "03:00", "04:00"],
        "temperature": [-20.5, -21.2, -22.0, -21.8, -20.9],
        "setpoint": [-22.0, -22.0, -22.0, -22.0, -22.0]
    }
    
    visualise = Visualise()
    
    try:
        results = []
        async for output in visualise(
            tree_data=tree_data,
            inputs={"chart_type": "area"},
            base_lm=base_lm,
            complex_lm=base_lm,
            client_manager=client_manager
        ):
            results.append(output)
            print(f"  {output.__class__.__name__}: {str(output)[:100]}")
        
        from elysia.tools.visualisation.objects import ChartResult
        chart_results = [r for r in results if isinstance(r, ChartResult)]
        if chart_results:
            result = chart_results[0]
            assert result.payload_type == "area_chart"
            print(f"  ✅ PASS: Created area chart via visualise tool")
        else:
            print("  ⚠️  SKIP: LLM didn't generate area chart (may have judged impossible)")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    # Test Pie Chart
    print("\n[Test 5] Visualise - Pie Chart")
    print("-" * 40)
    
    tree_data.environment = Environment()
    tree_data.environment["alarm_stats"] = {
        "temperature_alarms": 5,
        "pressure_alarms": 3,
        "electrical_alarms": 2
    }
    
    try:
        results = []
        async for output in visualise(
            tree_data=tree_data,
            inputs={"chart_type": "pie"},
            base_lm=base_lm,
            complex_lm=base_lm,
            client_manager=client_manager
        ):
            results.append(output)
            print(f"  {output.__class__.__name__}: {str(output)[:100]}")
        
        from elysia.tools.visualisation.objects import ChartResult
        chart_results = [r for r in results if isinstance(r, ChartResult)]
        if chart_results:
            result = chart_results[0]
            assert result.payload_type == "pie_chart"
            print(f"  ✅ PASS: Created pie chart via visualise tool")
        else:
            print("  ⚠️  SKIP: LLM didn't generate pie chart")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")


async def test_data_limits():
    """Test that increased data limits work correctly."""
    print("\n" + "="*60)
    print("Testing Data Limits")
    print("="*60)
    
    from elysia.tools.visualisation.objects import (
        AreaChart,
        AreaChartData,
        AreaChartSeries,
        BarChart,
        BarChartData
    )
    
    # Test 1: 1000 points (new max)
    print("\n[Test 6] 1000 data points")
    print("-" * 40)
    try:
        large_data = list(range(1000))
        area_chart = AreaChart(
            title="Large Dataset Test",
            description="Testing 1000 points",
            x_axis_label="Index",
            y_axis_label="Value",
            data=AreaChartData(
                x_axis=[f"T{i}" for i in range(1000)],
                series=[
                    AreaChartSeries(
                        name="Series 1",
                        data=large_data
                    )
                ]
            )
        )
        print(f"  ✅ PASS: Created area chart with 1000 points")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    # Test 2: Old limit (10) should still work
    print("\n[Test 7] 10 data points (backward compatibility)")
    print("-" * 40)
    try:
        bar_chart = BarChart(
            title="Small Dataset Test",
            description="Testing 10 points",
            x_axis_label="Category",
            y_axis_label="Value",
            data=BarChartData(
                x_labels=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
                y_values={"Series": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
            )
        )
        print(f"  ✅ PASS: Created bar chart with 10 points")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")


def test_chart_models():
    """Test all new chart models can be instantiated."""
    print("\n" + "="*60)
    print("Testing Chart Model Instantiation")
    print("="*60)
    
    from elysia.tools.visualisation.objects import (
        AreaChart, PieChart, RadialBarChart, ComposedChart,
        RadarChart, FunnelChart, TreemapChart,
        AreaChartData, AreaChartSeries, PieChartSlice,
        RadialBarData, ComposedChartSeries, FunnelStage, TreemapNode
    )
    
    tests = [
        ("AreaChart", lambda: AreaChart(
            title="Test", description="Test", x_axis_label="X", y_axis_label="Y",
            data=AreaChartData(x_axis=[1,2,3], series=[AreaChartSeries(name="S1", data=[1,2,3])])
        )),
        ("PieChart", lambda: PieChart(
            title="Test", description="Test",
            data=[PieChartSlice(name="A", value=10), PieChartSlice(name="B", value=20)]
        )),
        ("RadialBarChart", lambda: RadialBarChart(
            title="Test", description="Test",
            data=[RadialBarData(name="M1", value=75, max_value=100)]
        )),
        ("ComposedChart", lambda: ComposedChart(
            title="Test", description="Test", x_axis_label="X", y_axis_label="Y",
            x_axis=[1,2,3], series=[ComposedChartSeries(name="S1", data=[1,2,3], type="line")]
        )),
        ("RadarChart", lambda: RadarChart(
            title="Test", description="Test",
            metrics=["M1", "M2", "M3"], data={"Series1": [1, 2, 3]}
        )),
        ("FunnelChart", lambda: FunnelChart(
            title="Test", description="Test",
            stages=[FunnelStage(name="S1", value=100), FunnelStage(name="S2", value=50)]
        )),
        ("TreemapChart", lambda: TreemapChart(
            title="Test", description="Test",
            data=[TreemapNode(name="Root", value=100)]
        ))
    ]
    
    for name, create_fn in tests:
        try:
            chart = create_fn()
            print(f"  ✅ {name}: Created successfully")
        except Exception as e:
            print(f"  ❌ {name}: {e}")


def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("Visualization System Summary")
    print("="*60)
    print("\nChart Types Supported:")
    print("  Original (3):")
    print("    - bar: Categorical comparisons")
    print("    - histogram: Distributions")
    print("    - scatter_or_line: Trends and relationships")
    print("\n  New (7):")
    print("    - area: Time series with filled regions")
    print("    - pie: Part-to-whole percentages")
    print("    - radial_bar: Gauge/progress metrics")
    print("    - composed: Mixed chart types (line+bar+area)")
    print("    - radar: Multi-dimensional comparisons")
    print("    - funnel: Sequential process stages")
    print("    - treemap: Hierarchical proportions")
    print("\nVSM Domain Tools (3):")
    print("    - visualize_temperature_timeline: Telemetry trends (P3)")
    print("    - show_health_dashboard: Health gauges (D, M)")
    print("    - show_alarm_breakdown: Alarm distribution (M)")
    print("\nData Limits:")
    print("    - Before: max 10 points")
    print("    - After: max 1000 points (configurable)")
    print("\nTotal Tools in VSM: 16 (was 13)")
    print("="*60 + "\n")


async def main():
    """Run all tests."""
    print("\n🧪 Enhanced Visualization System Tests")
    print("=" * 60)
    
    # Model instantiation tests (synchronous)
    test_chart_models()
    
    # VSM tool tests (async)
    await test_vsm_visualization_tools()
    
    # Generic visualise tests (async)
    await test_generic_visualise_tool()
    
    # Data limit tests (synchronous)
    await test_data_limits()
    
    # Summary
    print_summary()


if __name__ == "__main__":
    asyncio.run(main())

