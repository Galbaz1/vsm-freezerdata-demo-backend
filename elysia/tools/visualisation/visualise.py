from logging import Logger
from elysia.objects import Tool, Error
from elysia.util.elysia_chain_of_thought import ElysiaChainOfThought
from elysia.tools.visualisation.objects import (
    ChartResult,
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
from elysia.tools.visualisation.util import convert_chart_types_to_matplotlib
from elysia.tools.visualisation.prompt_templates import (
    CreateBarChart,
    CreateHistogramChart,
    CreateScatterOrLineChart,
    CreateAreaChart,
    CreatePieChart,
    CreateRadialBarChart,
    CreateComposedChart,
    CreateRadarChart,
    CreateFunnelChart,
    CreateTreemapChart,
)
from elysia.objects import Response
from elysia.util.objects import TrainingUpdate, TreeUpdate


class Visualise(Tool):

    def __init__(self, logger: Logger | None = None, **kwargs):
        super().__init__(
            name="visualise",
            description=(
                "Visualise data in a chart from the environment. "
                "You can only visualise data that is in the environment. "
                "If there is nothing relevant in the environment, do not choose this tool.\n"
                "Choose chart type based on data:\n"
                "- `bar`: Categorical comparisons\n"
                "- `histogram`: Distribution of continuous data\n"
                "- `scatter_or_line`: X-Y relationships, trends\n"
                "- `area`: Time series with filled regions\n"
                "- `pie`: Part-to-whole percentages (2-10 categories)\n"
                "- `radial_bar`: Gauge/progress metrics (scores, capacity)\n"
                "- `composed`: Mix multiple chart types (line+bar)\n"
                "- `radar`: Multi-dimensional comparison (3-8 metrics)\n"
                "- `funnel`: Sequential process stages\n"
                "- `treemap`: Hierarchical proportions"
            ),
            status="Visualising...",
            end=True,
            inputs={
                "chart_type": {
                    "type": str,
                    "description": (
                        "The type of chart to create. "
                        "Must be one of: `bar`, `histogram`, `scatter_or_line`, `area`, `pie`, `radial_bar`, `composed`, `radar`, `funnel`, `treemap`."
                    ),
                    "required": True,
                    "default": "",
                }
            },
        )
        self.logger = logger

    async def __call__(
        self,
        tree_data,
        inputs: dict,
        base_lm,
        complex_lm,
        client_manager,
        **kwargs,
    ):
        chart_type = inputs["chart_type"]

        try:
            type_mapping = {
                "bar": CreateBarChart,
                "histogram": CreateHistogramChart,
                "scatter_or_line": CreateScatterOrLineChart,
                "area": CreateAreaChart,
                "pie": CreatePieChart,
                "radial_bar": CreateRadialBarChart,
                "composed": CreateComposedChart,
                "radar": CreateRadarChart,
                "funnel": CreateFunnelChart,
                "treemap": CreateTreemapChart,
            }

            create_chart = ElysiaChainOfThought(
                type_mapping[chart_type],
                tree_data=tree_data,
                environment=True,
                impossible=True,
                tasks_completed=True,
                reasoning=tree_data.settings.BASE_USE_REASONING,
            )
            prediction = await create_chart.aforward(lm=base_lm)
            charts = prediction.charts
            title = prediction.overall_title

            yield Response(text=prediction.message_update)
            yield TrainingUpdate(
                module_name="visualise",
                inputs={
                    "chart_type": chart_type,
                    **tree_data.to_json(),
                },
                outputs=prediction.__dict__["_store"],
            )

            if prediction.impossible:
                yield ChartResult(
                    [],
                    chart_type,
                    title,
                    metadata={
                        "impossible": True,
                        "impossible_reasoning": (
                            prediction.reasoning
                            if tree_data.settings.BASE_USE_REASONING
                            else ""
                        ),
                    },
                )
                return

            if self.logger and self.logger.level <= 20:
                fig = convert_chart_types_to_matplotlib(charts)
                fig.show()

            yield ChartResult(charts, chart_type, title)
        except Exception as e:
            yield Error(f"Error visualising data: {str(e)}")

    async def is_tool_available(self, tree_data, base_lm, complex_lm, client_manager):
        """
        Available when there are relevant objects in the environment.
        """
        return not tree_data.environment.is_empty()
