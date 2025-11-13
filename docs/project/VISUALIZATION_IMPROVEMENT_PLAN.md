# Visualization Improvement Plan

## Current State Analysis

### Backend (`elysia/tools/visualisation/`)
**Library**: Matplotlib (Python)
**Chart Types**: 3 only
- Bar charts
- Histograms
- Scatter/Line charts

**Limitations**:
- Hardcoded limits (max 10 x_labels, max 10 y_values)
- Static image output (not interactive)
- Limited customization
- LLM overhead (DSPy must generate chart structure)
- No support for:
  - Time series
  - Heatmaps
  - Gauge/radial charts
  - Area charts
  - Mixed charts
  - 3D visualizations

### Frontend (`elysia-frontend-main/`)
**Library**: Recharts (React + D3)
**Components**:
- `BarDisplay.tsx`
- `HistogramDisplay.tsx`
- `ScatterOrLineDisplay.tsx`

**Current Features**:
- Responsive containers
- Basic tooltips
- Color cycling
- Normalized Y-axis option

**Missing Features**:
- Advanced chart types
- Real-time updates
- Drill-down/zoom
- Export functionality
- Animation controls

---

## Improvement Strategy

### Phase 1: Extend Current Recharts Implementation (Quick Wins) ⚡

**Goal**: Add 5-7 new chart types without major refactoring

**New Chart Types** (all supported by Recharts):
1. **Area Chart** - For cumulative/stacked trends (perfect for telemetry over time)
2. **Composed Chart** - Mix line + bar in single chart (temp + setpoint comparison)
3. **Pie/Donut Chart** - Distribution (alarm severity breakdown)
4. **Radar Chart** - Multi-dimensional comparison (health scores across components)
5. **Radial Bar** - Gauge-style metrics (current vs target)
6. **Funnel Chart** - SMIDO phase progression
7. **Treemap** - Hierarchical data (component hierarchy)

**Implementation**:
```typescript
// New files to create:
elysia-frontend-main/app/components/chat/displays/ChartTable/
  - AreaDisplay.tsx
  - ComposedDisplay.tsx
  - PieDisplay.tsx
  - RadarDisplay.tsx
  - RadialBarDisplay.tsx
  - FunnelDisplay.tsx
  - TreemapDisplay.tsx
```

**Backend Updates**:
```python
# elysia/tools/visualisation/objects.py
class AreaChart(BaseModel): ...
class ComposedChart(BaseModel): ...
class PieChart(BaseModel): ...
class RadarChart(BaseModel): ...
class RadialBarChart(BaseModel): ...
class FunnelChart(BaseModel): ...
class TreemapChart(BaseModel): ...

# elysia/tools/visualisation/visualise.py
# Add new chart types to type_mapping
type_mapping = {
    "bar": CreateBarChart,
    "histogram": CreateHistogramChart,
    "scatter_or_line": CreateScatterOrLineChart,
    "area": CreateAreaChart,          # NEW
    "composed": CreateComposedChart,  # NEW
    "pie": CreatePieChart,            # NEW
    "radar": CreateRadarChart,        # NEW
    "radial_bar": CreateRadialBarChart, # NEW
    "funnel": CreateFunnelChart,      # NEW
    "treemap": CreateTreemapChart,    # NEW
}
```

**Estimated Time**: 2-3 days
**Impact**: High (7x more chart types)

---

### Phase 2: Remove Data Limits & Add VSM-Specific Charts 🎯

**Goal**: Support telemetry-scale data (785K rows) and domain-specific visualizations

**Changes**:
1. **Remove hardcoded limits**:
```python
# OLD (objects.py)
x_labels: list[str | int | float] = Field(
    min_length=1,
    max_length=10,  # ❌ TOO RESTRICTIVE
)

# NEW
x_labels: list[str | int | float] = Field(
    min_length=1,
    max_length=1000,  # ✅ Support time series
)
```

2. **Add pagination/windowing**:
```python
class ChartData(BaseModel):
    data_window_start: Optional[int] = None
    data_window_end: Optional[int] = None
    total_points: int
```

3. **VSM-Specific Charts**:
```python
# Temperature Timeline (area chart with threshold bands)
class TemperatureTimelineChart(AreaChart):
    setpoint_min: float
    setpoint_max: float
    alarm_thresholds: dict[str, float]

# Health Score Gauge (radial bar)
class HealthScoreGauge(RadialBarChart):
    score: float  # 0-100
    thresholds: dict[str, tuple[float, float]]  # critical/warning/ok ranges

# SMIDO Phase Progress (funnel)
class SMIDOProgressChart(FunnelChart):
    phases: list[str]  # M, T, I, D, O
    completion_status: dict[str, bool]
```

**Estimated Time**: 1-2 days
**Impact**: High (unlocks telemetry visualizations)

---

### Phase 3: Advanced Library Exploration (Optional) 🚀

**Option A: Stick with Recharts** ⭐ RECOMMENDED
- **Pros**: 
  - Already integrated
  - 10M weekly downloads
  - Perfect for React
  - Good docs
  - Declarative API
- **Cons**:
  - Not as feature-rich as Plotly/ECharts
  - Performance limits with >10K points

**Option B: Add Plotly.js** (for scientific viz)
- **Pros**:
  - 298K weekly downloads
  - 3D charts, heatmaps, contour plots
  - Publication-quality
  - Export to PNG/SVG
- **Cons**:
  - Larger bundle size (116 MB)
  - Different API paradigm
  - Overkill for most use cases

**Option C: Add ApexCharts** (modern alternative)
- **Pros**:
  - 1.2M weekly downloads
  - Beautiful defaults
  - Built-in animations
  - Better performance than Recharts
- **Cons**:
  - Learning curve
  - Migration effort

**Recommendation**: 
**Stick with Recharts** + add missing chart types. Only consider Plotly if you need scientific-grade visualizations (3D sensor maps, correlation heatmaps, etc.)

---

## Implementation Priority

### High Priority (Do First) 🔥
1. **Area Chart** - For telemetry time series
2. **Composed Chart** - Mix temp readings with setpoints
3. **Pie Chart** - Alarm/component distribution
4. **Remove data limits** - Support full parquet data

### Medium Priority
5. **Radar Chart** - Multi-dimensional health scores
6. **Radial Bar** - Gauge-style current status
7. **Add chart export** - Download as PNG/CSV

### Low Priority (Nice to Have)
8. **Funnel Chart** - SMIDO progression
9. **Treemap** - Component hierarchy
10. **Real-time updates** - WebSocket streaming

---

## VSM Use Cases

### Example 1: Temperature Timeline (Area Chart)
```python
# Backend tool
@tool(status="Creating temperature timeline...")
async def visualize_temperature_history(
    asset_id: str,
    start_time: str,
    end_time: str,
    tree_data=None,
    **kwargs
):
    """Show room temp vs setpoint over time with alarm thresholds."""
    # Query parquet for time series
    df = get_telemetry_data(asset_id, start_time, end_time)
    
    yield Result(
        objects=[{
            "title": "Temperature History",
            "x_axis": df['timestamp'].tolist(),
            "series": [
                {
                    "name": "Room Temp",
                    "data": df['room_temp'].tolist(),
                    "type": "area",
                    "color": "#3B82F6"
                },
                {
                    "name": "Setpoint",
                    "data": [target_temp] * len(df),
                    "type": "line",
                    "color": "#10B981"
                }
            ],
            "threshold_bands": [
                {"min": -25, "max": -20, "color": "#10B981", "label": "OK"},
                {"min": -20, "max": -15, "color": "#F59E0B", "label": "Warning"},
                {"min": -15, "max": 0, "color": "#EF4444", "label": "Critical"}
            ]
        }],
        payload_type="area_chart"
    )
```

### Example 2: Health Score Dashboard (Radial Bar)
```python
@tool(status="Computing health scores...")
async def show_health_dashboard(
    asset_id: str,
    tree_data=None,
    **kwargs
):
    """Display cooling/compressor/stability scores as gauges."""
    health = compute_health_scores(asset_id)
    
    yield Result(
        objects=[{
            "title": "System Health Dashboard",
            "scores": [
                {"label": "Cooling", "value": health['cooling'], "max": 100},
                {"label": "Compressor", "value": health['compressor'], "max": 100},
                {"label": "Stability", "value": health['stability'], "max": 100}
            ],
            "thresholds": {
                "critical": (0, 30),
                "warning": (30, 70),
                "good": (70, 100)
            }
        }],
        payload_type="radial_bar_chart"
    )
```

### Example 3: Alarm Distribution (Pie Chart)
```python
@tool(status="Analyzing alarm distribution...")
async def show_alarm_breakdown(
    asset_id: str,
    period_days: int = 30,
    tree_data=None,
    **kwargs
):
    """Show pie chart of alarm types over last N days."""
    alarms = get_alarms_summary(asset_id, period_days)
    
    yield Result(
        objects=[{
            "title": f"Alarms - Last {period_days} Days",
            "data": [
                {"name": "Temperature", "value": alarms['temp_count'], "color": "#EF4444"},
                {"name": "Pressure", "value": alarms['pressure_count'], "color": "#F59E0B"},
                {"name": "Electrical", "value": alarms['electrical_count'], "color": "#3B82F6"},
                {"name": "Defrost", "value": alarms['defrost_count'], "color": "#8B5CF6"}
            ]
        }],
        payload_type="pie_chart"
    )
```

---

## Quick Start: Add Area Chart

### Step 1: Backend Objects
```python
# elysia/tools/visualisation/objects.py

class AreaChartSeries(BaseModel):
    name: str
    data: list[float | int]
    color: Optional[str] = None
    fill_opacity: float = Field(default=0.3, ge=0, le=1)

class AreaChartData(BaseModel):
    x_axis: list[str | datetime | float | int]
    series: list[AreaChartSeries] = Field(min_length=1, max_length=5)
    threshold_bands: Optional[list[dict]] = None

class AreaChart(BaseModel):
    title: str
    description: str
    x_axis_label: str
    y_axis_label: str
    data: AreaChartData

class ChartResult(Result):
    # Add "area" to supported types
    def __init__(
        self,
        charts: list[BarChart | HistogramChart | ScatterOrLineChart | AreaChart],
        chart_type: Literal["bar", "histogram", "scatter_or_line", "area"],
        ...
    ):
```

### Step 2: Backend Tool Template
```python
# elysia/tools/visualisation/prompt_templates.py

class CreateAreaChart(dspy.Signature):
    """Create an area chart from environment data."""
    
    environment: str = dspy.InputField(
        desc="The environment containing data"
    )
    impossible: bool = dspy.OutputField(
        desc="True if creating chart is impossible"
    )
    reasoning: str = dspy.OutputField(
        desc="Reasoning for chart design"
    )
    charts: list[AreaChart] = dspy.OutputField(
        desc="Area charts to create"
    )
    overall_title: str = dspy.OutputField(
        desc="Title for the visualization"
    )
    message_update: str = dspy.OutputField(
        desc="Message to user about the chart"
    )
```

### Step 3: Frontend Display Component
```typescript
// elysia-frontend-main/app/components/chat/displays/ChartTable/AreaDisplay.tsx

import { Area, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AreaDisplayProps {
  result: ResultPayload;
}

const AreaDisplay: React.FC<AreaDisplayProps> = ({ result }) => {
  const chartData = result.objects[0];
  
  // Transform data
  const data = chartData.data.x_axis.map((x, i) => ({
    x_value: x,
    ...chartData.data.series.reduce((acc, series) => ({
      ...acc,
      [series.name]: series.data[i]
    }), {})
  }));
  
  return (
    <div className="w-full h-[40vh]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x_value" />
          <YAxis />
          <Tooltip />
          <Legend />
          {chartData.data.series.map((series, i) => (
            <Area
              key={series.name}
              type="monotone"
              dataKey={series.name}
              stroke={series.color || getDefaultColor(i)}
              fill={series.color || getDefaultColor(i)}
              fillOpacity={series.fill_opacity}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### Step 4: Register in RenderDisplay
```typescript
// elysia-frontend-main/app/components/chat/RenderDisplay.tsx

import AreaDisplay from "./displays/ChartTable/AreaDisplay";

// In switch statement:
case "area_chart":
  return <AreaDisplay key={`${keyBase}-chart`} result={payload} />;
```

### Step 5: Update Visualise Tool
```python
# elysia/tools/visualisation/visualise.py

type_mapping = {
    "bar": CreateBarChart,
    "histogram": CreateHistogramChart,
    "scatter_or_line": CreateScatterOrLineChart,
    "area": CreateAreaChart,  # ADD THIS
}
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_area_chart.py

def test_area_chart_creation():
    chart = AreaChart(
        title="Test Area",
        description="Test",
        x_axis_label="Time",
        y_axis_label="Temp",
        data=AreaChartData(
            x_axis=["1", "2", "3"],
            series=[
                AreaChartSeries(
                    name="Room",
                    data=[10, 20, 15]
                )
            ]
        )
    )
    assert chart.title == "Test Area"
```

### Integration Test
```bash
# Test via VSM
python3 scripts/test_visualizations.py
```

---

## Success Metrics

- ✅ Support for 10+ chart types (vs current 3)
- ✅ Remove data limits (1000+ points supported)
- ✅ VSM-specific charts (temp timeline, health gauges, alarm distribution)
- ✅ <100ms render time for typical datasets
- ✅ Export functionality (PNG/CSV)

---

## Resources

- **Recharts Docs**: https://recharts.org/
- **Recharts Examples**: https://recharts.org/en-US/examples
- **Current Implementation**: `elysia/tools/visualisation/`
- **Frontend Charts**: `elysia-frontend-main/app/components/chat/displays/ChartTable/`

