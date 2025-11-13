import dspy
from elysia.tools.visualisation.objects import (
    BarChart,
    HistogramChart,
    ScatterOrLineChart,
    AreaChart,
    PieChart,
    RadialBarChart,
    ComposedChart,
    RadarChart,
    FunnelChart,
    TreemapChart,
)


class CreateBarChart(dspy.Signature):
    """
    Create one or more bar charts.

    Create a maximum of 9 bar charts.
    Each bar chart should have a maximum of 10 categories.
    Hence each chart should also have a maximum of 10 values per category.
    Pick the most relevant categories and values.
    """

    charts: list[BarChart] = dspy.OutputField(description="The bar chart to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string. "
        ),
    )


class CreateHistogramChart(dspy.Signature):
    """
    Create one or more histogram charts.

    Create a maximum of 9 histogram charts.
    Do not produce more than 50 values per histogram chart. Pick the most relevant values.
    """

    charts: list[HistogramChart] = dspy.OutputField(
        description="The histogram chart to create."
    )
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string. "
        ),
    )


class CreateScatterOrLineChart(dspy.Signature):
    """
    Create one or more scatter or line charts.

    Create a maximum of 9 scatter or line charts.
    Create a maximum of 50 points per scatter or line chart. Pick the most relevant points.

    A scatter or line chart can have multiple y-axis values, each with a different label.
    You can combine a line chart with a scatter chart by creating multiple
    """

    charts: list[ScatterOrLineChart] = dspy.OutputField(
        description="The scatter or line chart to create."
    )
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string. "
        ),
    )


class CreateAreaChart(dspy.Signature):
    """
    Create area charts for time series data showing trends over time.
    
    WHEN TO USE:
    - Telemetry data over time (temperature, pressure readings)
    - Cumulative metrics that need stacking
    - Showing continuous data flow with filled regions
    
    AVOID WHEN:
    - Data is categorical (use bar chart)
    - Comparing discrete points (use scatter)
    - Need precise value comparison (use line chart)
    
    Maximum 1000 data points. Agent should intelligently sample if data exceeds limit.
    Maximum 9 charts per request.
    """
    
    charts: list[AreaChart] = dspy.OutputField(description="The area chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )


class CreatePieChart(dspy.Signature):
    """
    Create pie/donut charts for part-to-whole relationships.
    
    WHEN TO USE:
    - Showing distribution (alarm types, component breakdown)
    - Percentage/proportion visualization
    - 2-10 categories that sum to meaningful whole
    
    AVOID WHEN:
    - More than 10 categories (use bar chart)
    - Values don't sum to whole (use bar chart)
    - Time series data (use area/line chart)
    
    Maximum 10 slices per chart.
    """
    
    charts: list[PieChart] = dspy.OutputField(description="The pie chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )


class CreateRadialBarChart(dspy.Signature):
    """
    Create radial bar (gauge) charts for progress/score metrics.
    
    WHEN TO USE:
    - Health scores, performance metrics (0-100 scale)
    - Progress toward target value
    - Current vs maximum capacity
    
    AVOID WHEN:
    - More than 5 metrics (gets crowded)
    - No meaningful maximum value
    - Historical trends needed (use line chart)
    
    Maximum 5 gauges per chart.
    """
    
    charts: list[RadialBarChart] = dspy.OutputField(description="The radial bar chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )


class CreateComposedChart(dspy.Signature):
    """
    Create composed charts mixing line, bar, and area on same axes.
    
    WHEN TO USE:
    - Comparing different metrics with different types (actual vs target)
    - Showing relationships between bar and line data
    - Overlay patterns on top of base data
    
    AVOID WHEN:
    - Metrics have vastly different scales (normalize or use separate charts)
    - Simple single-type visualization sufficient
    
    Maximum 1000 points, maximum 5 series.
    """
    
    charts: list[ComposedChart] = dspy.OutputField(description="The composed chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )


class CreateRadarChart(dspy.Signature):
    """
    Create radar charts for multi-dimensional comparison.
    
    WHEN TO USE:
    - Comparing multiple metrics across categories (health scores)
    - Showing balance/imbalance across dimensions
    - 3-8 metrics that form meaningful pattern
    
    AVOID WHEN:
    - Less than 3 metrics (use bar chart)
    - More than 8 metrics (too crowded)
    - Time series (use line chart)
    """
    
    charts: list[RadarChart] = dspy.OutputField(description="The radar chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )


class CreateFunnelChart(dspy.Signature):
    """
    Create funnel charts for sequential process stages.
    
    WHEN TO USE:
    - SMIDO phase progression (M→T→I→D→O)
    - Diagnostic workflow stages
    - Sequential reduction process
    
    Maximum 8 stages.
    """
    
    charts: list[FunnelChart] = dspy.OutputField(description="The funnel chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )


class CreateTreemapChart(dspy.Signature):
    """
    Create treemap charts for hierarchical data.
    
    WHEN TO USE:
    - Component hierarchy with sizes
    - Nested category breakdowns
    - Space-constrained proportional display
    
    Maximum 50 total nodes (including children).
    """
    
    charts: list[TreemapChart] = dspy.OutputField(description="The treemap chart(s) to create.")
    overall_title: str = dspy.OutputField(
        description=(
            "If providing more than one chart, they will be displayed in a grid. "
            "This is the overall title for above the grid. "
            "Otherwise provide an empty string."
        ),
    )
    message_update: str = dspy.OutputField(
        description="A brief message to the user about the chart(s) created."
    )
