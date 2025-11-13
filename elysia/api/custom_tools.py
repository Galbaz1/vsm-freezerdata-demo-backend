from elysia import Tool, tool
from elysia.objects import Response, Status, Result, Error
from weaviate.classes.query import Filter

# Import a custom tool from a separate file
from elysia.tools.visualisation.linear_regression import BasicLinearRegression

# Import existing tools
from elysia.tools.retrieval.query import Query
from elysia.tools.retrieval.aggregate import Aggregate
from elysia.tools.text.text import CitedSummarizer, FakeTextResponse


# Or you can define the tool inline here
class TellAJoke(Tool):
    """
    Example tool for testing/demonstration purposes.
    Simply returns a joke as a text response that was an input to the tool.
    """

    def __init__(self, **kwargs):

        # Init requires initialisation of the super class (Tool)
        super().__init__(
            name="tell_a_joke",
            description="Displays a joke to the user.",
            inputs={
                "joke": {
                    "type": str,
                    "description": "A joke to tell.",
                    "required": True,
                }
            },
            end=True,
        )

    # Call must be a async generator function that yields objects to the decision tree
    async def __call__(
        self, tree_data, inputs, base_lm, complex_lm, client_manager, **kwargs
    ):

        # This example tool only returns the input to the tool, so is not very useful
        yield Response(inputs["joke"])

        # You can include more complex logic here via a custom function


@tool(
    status="Searching SMIDO manuals and diagrams...",
    branch_id="smido_installatie"
)
async def search_manuals_by_smido(
    query: str = "",
    smido_step: str = None,
    failure_mode: str = None,
    component: str = None,
    include_diagrams: bool = True,
    include_test_content: bool = False,
    limit: int = 5,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Search manual sections filtered by SMIDO step, with optional diagram inclusion.
    
    Source: VSM_ManualSections collection (167 sections from 3 manuals)
    Diagrams: VSM_DiagramUserFacing (8) + VSM_DiagramAgentInternal (8)
    
    Args:
        query: Natural language query to search for in manual sections. If empty, uses filter-only search.
        smido_step: SMIDO methodology step to filter by. Options: melding, technisch, installatie_vertrouwd, 
                    3P_power, 3P_procesinstellingen, 3P_procesparameters, 3P_productinput, ketens_onderdelen.
        failure_mode: Filter by specific failure mode (e.g., "ingevroren_verdamper", "te_hoge_temperatuur").
        component: Filter by component name (e.g., "verdamper", "compressor", "pressostaat").
        include_diagrams: Whether to fetch and return related Mermaid diagrams. Default: True.
        include_test_content: Whether to include test content (opgave). Default: False (filters out test content).
        limit: Maximum number of manual sections to return. Default: 5.
    
    Returns:
        - Manual sections (text) matching the query and filters
        - Related diagrams (Mermaid code) if include_diagrams=True
    
    Automatically filters out test content (opgave) unless include_test_content=True.
    
    Used in: I (Installatie), P2 (Procesinstellingen), O (Onderdelen) nodes
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Searching manual sections...")
    
    # Build filters
    filters = []
    
    # SMIDO step filter
    if smido_step:
        filters.append(Filter.by_property("smido_step").equal(smido_step))
    
    # Failure mode filter (check both single and array fields)
    if failure_mode:
        filters.append(Filter.by_property("failure_modes").contains_any([failure_mode]))
    
    # Component filter (check both single and array fields)
    if component:
        filters.append(Filter.by_property("components").contains_any([component]))
    
    # Filter out test content (opgave) by default
    if not include_test_content:
        filters.append(Filter.by_property("content_type").not_equal("opgave"))
    
    # Combine filters with AND
    combined_filter = None
    if filters:
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
    
    try:
        async with client_manager.connect_to_async_client() as client:
            # Check if collection exists
            if not await client.collections.exists("VSM_ManualSections"):
                yield Error("VSM_ManualSections collection not found in Weaviate.")
                return
            
            collection = client.collections.get("VSM_ManualSections")
            
            # Query VSM_ManualSections
            if query:
                # Hybrid search (semantic + keyword)
                if combined_filter:
                    results = await collection.query.hybrid(
                        query=query,
                        filters=combined_filter,
                        limit=limit
                    )
                else:
                    results = await collection.query.hybrid(
                        query=query,
                        limit=limit
                    )
            else:
                # Filter-only search
                if combined_filter:
                    results = await collection.query.fetch_objects(
                        filters=combined_filter,
                        limit=limit
                    )
                else:
                    # No filters and no query - return recent items
                    results = await collection.query.fetch_objects(
                        limit=limit
                    )
            
            yield Status(f"Found {len(results.objects)} manual sections")
            
            # Get related diagrams if requested
            diagram_objects = []
            if include_diagrams:
                yield Status("Fetching related diagrams...")
                
                # Check both diagram collections exist
                user_exists = await client.collections.exists("VSM_DiagramUserFacing")
                agent_exists = await client.collections.exists("VSM_DiagramAgentInternal")
                
                if not (user_exists or agent_exists):
                    yield Status("No diagram collections found")
                else:
                    # Strategy 1: Fetch by related_diagram_ids (if populated)
                    diagram_ids = []
                    for obj in results.objects:
                        related_ids = obj.properties.get("related_diagram_ids", [])
                        if related_ids:
                            diagram_ids.extend(related_ids)
                    
                    if diagram_ids:
                        # Batch fetch by IDs from both collections
                        unique_ids = list(set(diagram_ids))
                        
                        if user_exists:
                            user_coll = client.collections.get("VSM_DiagramUserFacing")
                            user_results = await user_coll.query.fetch_objects(
                                filters=Filter.by_property("diagram_id").contains_any(unique_ids),
                                limit=20
                            )
                            diagram_objects.extend(user_results.objects)
                        
                        if agent_exists:
                            agent_coll = client.collections.get("VSM_DiagramAgentInternal")
                            agent_results = await agent_coll.query.fetch_objects(
                                filters=Filter.by_property("diagram_id").contains_any(unique_ids),
                                limit=20
                            )
                            diagram_objects.extend(agent_results.objects)
                    
                    # Strategy 2: Fallback to SMIDO phase matching (if no IDs found)
                    elif smido_step:
                        # Map SMIDO step to phase tags
                        phase_map = {
                            "melding": ["M", "melding"],
                            "technisch": ["T", "technisch"],
                            "installatie_vertrouwd": ["I", "installatie"],
                            "3P_power": ["P1", "power"],
                            "3P_procesinstellingen": ["P2", "procesinstellingen"],
                            "3P_procesparameters": ["P3", "procesparameters"],
                            "3P_productinput": ["P4", "productinput"],
                            "ketens_onderdelen": ["O", "onderdelen"],
                        }
                        
                        if smido_step in phase_map:
                            phases = phase_map[smido_step]
                            
                            # Only AgentInternal has populated smido_phases
                            # UserFacing has empty arrays, so we only search AgentInternal
                            if agent_exists:
                                agent_coll = client.collections.get("VSM_DiagramAgentInternal")
                                agent_results = await agent_coll.query.fetch_objects(
                                    filters=Filter.by_property("smido_phases").contains_any(phases),
                                    limit=10
                                )
                                diagram_objects.extend(agent_results.objects)
                
                yield Status(f"Found {len(diagram_objects)} related diagrams")
            
            # Convert objects to dictionaries for Result
            manual_objects = []
            for obj in results.objects:
                obj_dict = {k: v for k, v in obj.properties.items()}
                obj_dict["uuid"] = str(obj.uuid)
                manual_objects.append(obj_dict)
            
            # Convert diagram objects to dictionaries
            diagram_dicts = []
            for obj in diagram_objects:
                diagram_dict = {k: v for k, v in obj.properties.items()}
                diagram_dict["uuid"] = str(obj.uuid)
                diagram_dicts.append(diagram_dict)
            
            # If diagrams found, output them as Response (handle both PNG and Mermaid)
            if diagram_dicts:
                for diagram in diagram_dicts:
                    title = diagram.get("title", "Diagram")
                    description = diagram.get("description", "")
                    png_url = diagram.get("png_url")
                    mermaid_code = diagram.get("mermaid_code", "")
                    
                    # Check for PNG first (UserFacing diagrams)
                    if png_url:
                        # Build full URL for PNG image
                        full_url = f"http://localhost:8000{png_url}"
                        markdown = f"\n\n**📊 {title}**\n\n"
                        if description:
                            markdown += f"*{description}*\n\n"
                        markdown += f"![{title}]({full_url})\n"
                        yield Response(markdown)
                    
                    # Fallback to Mermaid (AgentInternal diagrams)
                    elif mermaid_code:
                        markdown = f"\n\n**📊 {title}**\n\n"
                        if description:
                            markdown += f"*{description}*\n\n"
                        markdown += f"```mermaid\n{mermaid_code}\n```\n"
                        yield Response(markdown)
            
            # Yield results
            yield Result(
                objects=manual_objects,
                metadata={
                    "diagrams": diagram_dicts,
                    "smido_step": smido_step,
                    "failure_mode": failure_mode,
                    "component": component,
                    "test_content_included": include_test_content,
                    "diagram_count": len(diagram_dicts),
                    "manual_section_count": len(manual_objects)
                },
                payload_type="document"
            )
            
    except Exception as e:
        yield Error(f"Error querying manuals: {str(e)}")
        return


@tool(
    status="Checking active alarms...",
    branch_id="smido_melding"
)
async def get_alarms(
    asset_id: str = None,
    severity: str = "all",  # "critical", "warning", "info", "all"
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Get active alarms for asset from VSM_TelemetryEvent collection.
    
    Source: VSM_TelemetryEvent collection (12 tagged incidents)
    Used in: M (Melding), P1 (Power) SMIDO phases
    
    Args:
        asset_id: Asset identifier (e.g., "135_1570"). Optional - if not provided, returns alarms for all assets.
        severity: Filter by severity level. Options: "critical", "warning", "info", "all". Default: "all"
    
    Returns:
        - List of alarm objects with timestamp, severity, message, alarm_code
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Querying active alarms...")
    
    try:
        async with client_manager.connect_to_async_client() as client:
            if not await client.collections.exists("VSM_TelemetryEvent"):
                yield Error("VSM_TelemetryEvent collection not found in Weaviate.")
                return
            
            collection = client.collections.get("VSM_TelemetryEvent")
            
            # Build filters - only add asset_id filter if provided and not None/empty
            filters = None
            if asset_id and asset_id != 'None' and asset_id.strip():
                filters = Filter.by_property("asset_id").equal(asset_id)
            
            if severity != "all":
                severity_filter = Filter.by_property("severity").equal(severity)
                if filters:
                    filters = filters & severity_filter
                else:
                    filters = severity_filter
            
            # Query with filters (or None if no filters)
            # Note: Weaviate v4 doesn't support sort in fetch_objects directly
            # Results are returned in insertion order, which should be chronological
            query_kwargs = {"limit": 20}  # Get recent alarms
            if filters:
                query_kwargs["filters"] = filters
            
            results = await collection.query.fetch_objects(**query_kwargs)
            
            yield Status(f"Found {len(results.objects)} alarm(s)")
            
            # Convert to dictionaries
            alarm_objects = []
            for obj in results.objects:
                obj_dict = {k: v for k, v in obj.properties.items()}
                obj_dict["uuid"] = str(obj.uuid)
                alarm_objects.append(obj_dict)
            
            yield Result(
                objects=alarm_objects,
                metadata={
                    "asset_id": asset_id,
                    "severity_filter": severity,
                    "alarm_count": len(alarm_objects)
                }
            )
            
    except Exception as e:
        yield Error(f"Error querying alarms: {str(e)}")
        return


@tool(
    status="Searching historical incidents...",
    branch_id="smido_diagnose"
)
async def query_telemetry_events(
    failure_mode: str = None,
    components: list = None,
    severity: str = None,
    limit: int = 5,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Query historical "uit balans" incidents to find patterns.
    
    IMPORTANT: VSM_TelemetryEvent contains only 12 REFERENCE incidents (not daily/monthly data).
    For monthly stats or trends, use compute_worldstate + parquet data instead.
    
    Use when:
    - You've identified a failure mode and want to see when it happened before
    - Looking for patterns in the 12 tagged reference incidents
    - Comparing current incident to past similar events
    
    NOT for:
    - Monthly statistics (use compute_worldstate → parquet has 785K rows)
    - Daily trends (use compute_worldstate with time window)
    - Aggregating continuous sensor data (use compute_worldstate or custom parquet query)
    
    Different from get_alarms:
    - get_alarms: Current active alarms (what's wrong RIGHT NOW)
    - query_telemetry_events: Historical incidents (when did this happen BEFORE)
    
    Source: VSM_TelemetryEvent collection (12 tagged incidents, Jul 2024 - Jan 2025)
    
    Args:
        failure_mode: Filter by failure mode (e.g., "ingevroren_verdamper")
        components: Filter by component names (list)
        severity: Filter by severity level
        limit: Maximum number of events to return. Default: 5
    
    Returns:
        - List of telemetry event objects with timestamp, severity, failure mode
    
    Used in: M (Melding), D (Diagnose) nodes for pattern analysis
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Querying historical incidents...")
    
    try:
        async with client_manager.connect_to_async_client() as client:
            if not await client.collections.exists("VSM_TelemetryEvent"):
                yield Error("VSM_TelemetryEvent collection not found in Weaviate.")
                return
            
            collection = client.collections.get("VSM_TelemetryEvent")
            
            # Build filters
            filters = []
            
            if failure_mode:
                filters.append(Filter.by_property("failure_mode").equal(failure_mode))
            
            if components:
                filters.append(Filter.by_property("components").contains_any(components))
            
            if severity:
                filters.append(Filter.by_property("severity").equal(severity))
            
            # Combine filters
            combined_filter = None
            if filters:
                combined_filter = filters[0]
                for f in filters[1:]:
                    combined_filter = combined_filter & f
            
            # Query
            if combined_filter:
                results = await collection.query.fetch_objects(
                    filters=combined_filter,
                    limit=limit
                )
            else:
                results = await collection.query.fetch_objects(limit=limit)
            
            yield Status(f"Found {len(results.objects)} event(s)")
            
            # Convert to dictionaries
            event_objects = []
            for obj in results.objects:
                obj_dict = {k: v for k, v in obj.properties.items()}
                obj_dict["uuid"] = str(obj.uuid)
                event_objects.append(obj_dict)
            
            yield Result(
                objects=event_objects,
                metadata={
                    "failure_mode": failure_mode,
                    "components": components,
                    "severity": severity,
                    "event_count": len(event_objects)
                }
            )
            
    except Exception as e:
        yield Error(f"Error querying telemetry events: {str(e)}")
        return


@tool(
    status="Searching video case library...",
    branch_id="smido_onderdelen"
)
async def query_vlog_cases(
    problem_description: str = None,
    failure_mode: str = None,
    component: str = None,
    smido_step: str = None,
    limit: int = 3,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """Query vlog cases for similar problem→solution workflows - learn from past repairs.

Source: VSM_VlogCase collection (5 cases: A1-A5)
Related: VSM_VlogClip collection (15 individual video segments)

When to use:
- O (ONDERDELEN): After identifying failure mode, to find repair procedures
- When you've completed P1-P4 checks and need component-specific guidance
- To show M a similar case with step-by-step solution

What it returns:
- VSM_VlogCase objects: Complete problem→triage→solution workflows (A1-A5)
- Each case includes: problem_summary, root_cause, solution_summary, transcript_nl
- Cases are real troubleshooting sessions with Dutch language
- Related components, failure modes, SMIDO steps tagged

Output interpretation:
- case_id (A1-A5): Reference to specific troubleshooting video
- problem_summary: What was wrong initially
- root_cause: What caused the problem (component + contributing factors)
- solution_summary: Step-by-step fix that worked
- transcript_nl: Full Dutch narrative of troubleshooting session

How to explain to M:
"Ik zoek nu vergelijkbare cases in de database..."
[after tool runs]
"Ik heb case [ID] gevonden: [problem]. Root cause was: [cause]. Oplossing: [steps]. Laten we dit ook checken."

Example (A3 frozen evaporator):
"Case A3 gevonden (frozen evaporator). Probleem: Koelcel bereikt temp niet, verdamper vol ijs.
Root cause: Ontdooitimer op 'handmatig' + vervuilde luchtkanalen.
Oplossing: 1) Handmatig ontdooien 2) Luchtkanalen reinigen 3) Timer reset 4) Test cyclus."

Available cases:
- A1: Condenser fan (pressostaat + electrical issue)
- A2: Expansion valve blockage
- A3: Frozen evaporator (defrost timer + dirty ducts) ⭐ Primary demo case
- A4: Controller settings incorrect
- A5: Clogged refrigerant line (filter-dryer)

Args:
    problem_description: Natural language description (e.g., "koelcel te warm verdamper bevroren")
    failure_mode: Filter by failure mode (e.g., "ingevroren_verdamper")
    component: Filter by component name (e.g., "verdamper", "condensor")
    smido_step: Filter by SMIDO step
    limit: Maximum number of cases. Default: 3.

Returns:
    List of vlog case dicts with problem_summary, root_cause, solution_summary, transcript_nl.
"""
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Querying video case library...")
    
    try:
        async with client_manager.connect_to_async_client() as client:
            if not await client.collections.exists("VSM_VlogCase"):
                yield Error("VSM_VlogCase collection not found in Weaviate.")
                return
            
            collection = client.collections.get("VSM_VlogCase")
            
            # Build filters
            filters = []
            
            if failure_mode:
                filters.append(Filter.by_property("failure_mode").equal(failure_mode))
            
            if component:
                filters.append(Filter.by_property("components").contains_any([component]))
            
            if smido_step:
                filters.append(Filter.by_property("smido_steps").contains_any([smido_step]))
            
            # Combine filters
            combined_filter = None
            if filters:
                combined_filter = filters[0]
                for f in filters[1:]:
                    combined_filter = combined_filter & f
            
            # Query - use hybrid if problem_description provided, else filter-only
            if problem_description:
                if combined_filter:
                    results = await collection.query.hybrid(
                        query=problem_description,
                        filters=combined_filter,
                        limit=limit
                    )
                else:
                    results = await collection.query.hybrid(
                        query=problem_description,
                        limit=limit
                    )
            else:
                if combined_filter:
                    results = await collection.query.fetch_objects(
                        filters=combined_filter,
                        limit=limit
                    )
                else:
                    results = await collection.query.fetch_objects(limit=limit)
            
            yield Status(f"Found {len(results.objects)} case(s)")
            
            # Convert to dictionaries
            case_objects = []
            for obj in results.objects:
                obj_dict = {k: v for k, v in obj.properties.items()}
                obj_dict["uuid"] = str(obj.uuid)
                case_objects.append(obj_dict)
            
            yield Result(
                objects=case_objects,
                metadata={
                    "problem_description": problem_description,
                    "failure_mode": failure_mode,
                    "component": component,
                    "case_count": len(case_objects)
                }
            )
            
    except Exception as e:
        yield Error(f"Error querying vlog cases: {str(e)}")
        return


@tool(
    status="Retrieving current status...",
    branch_id="smido_melding"
)
async def get_current_status(
    asset_id: str = "135_1570",
    tree_data=None,
    **kwargs
):
    """Quick status check - current temps, flags, health.

    Use when the user requests the current system status.
    
    NOTE: For demo purposes, if current timestamp is TODAY (datetime.now()),
    returns synthetic A3 problem (frozen evaporator). Otherwise returns real sensor data.

    Returns:
    - 5 key sensors (room, hot-gas, suction, liquid, ambient)
    - Active warning flags
    - 30-minute trend (stijgend/stabiel/dalend)
    - Health score summary (cooling, compressor, stability)
    """
    yield Status("Loading system status...")

    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime

    engine = WorldStateEngine(
        "features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet"
    )
    
    # Use current time - worldstate_engine auto-detects "today" and injects A3
    now = datetime.now()
    worldstate = engine.compute_worldstate(asset_id, now, 60)

    current = worldstate.get("current_state", {})
    flags = worldstate.get("flags", {})
    trends = worldstate.get("trends_30m", {})
    health = worldstate.get("health_scores", {})

    active_flags = [flag for flag, active in flags.items() if active]

    room_delta = trends.get("room_temp_delta_30m", 0.0)
    if room_delta > 0.5:
        trend_description = "stijgend"
    elif room_delta < -0.5:
        trend_description = "dalend"
    else:
        trend_description = "stabiel"

    status_summary = {
        "asset_id": asset_id,
        "timestamp": worldstate.get("timestamp"),
        "readings": {
            "room_temp_C": current.get("current_room_temp"),
            "hot_gas_temp_C": current.get("current_hot_gas_temp"),
            "suction_temp_C": current.get("current_suction_temp"),
            "liquid_temp_C": current.get("current_liquid_temp"),
            "ambient_temp_C": current.get("current_ambient_temp"),
        },
        "active_flags": active_flags,
        "trend_30m": {
            "room_temp_delta_C": room_delta,
            "description": trend_description,
        },
        "health_scores": {
            "cooling": health.get("cooling_performance_score"),
            "compressor": health.get("compressor_health_score"),
            "stability": health.get("system_stability_score"),
        },
        "is_synthetic_today": worldstate.get("is_synthetic_today", False),
    }

    yield Result(objects=[status_summary])


@tool(
    status="Computing WorldState features from telemetry...",
    branch_id="smido_p3_procesparameters"
)
async def compute_worldstate(
    asset_id: str,
    timestamp: str = None,
    window_minutes: int = 60,
    tree_data=None,
    **kwargs
):
    """Compute WorldState (W) - 58+ sensor features from telemetry parquet (785K rows).

When to use:
- P3 (PROCESPARAMETERS): When you need detailed sensor analysis
- P4 (PRODUCTINPUT): To check environmental trends
- After M reports symptom, to correlate with sensor data
- User asks for trends, monthly data, historical analysis, or visualization
- BEFORE visualize: This tool makes 'visualise' available after it completes

What it computes:
- Current readings (temps, pressures, compressor status)
- Trends (30min, 2h, 24h windows) - rising/falling?
- Flags (_flag_main_temp_high, _flag_suction_extreme, etc.)
- Health scores (0-100, lower = worse)
- Anomaly detection

Timestamp flexibility:
- Can query ANY timestamp from Jul 2024 - Jan 2026 (785K rows, 1-min intervals)
- For "last month": pick a timestamp from last month (e.g., 15 Oct 2025)
- For "trends": can compute multiple snapshots at different times

Output interpretation:
- If _flag_main_temp_high=True → Koelcel te warm
- If _flag_suction_extreme=True → Mogelijk bevroren verdamper
- If trend_2h positive → Temperatuur stijgt afgelopen 2 uur

How to explain to M:
"Ik ga nu de sensordata analyseren van de afgelopen [window_minutes] minuten..."
[after tool runs]
"Oké, ik zie: [key findings]. Dit betekent: [interpretation]."

Example (A3 frozen evaporator):
"Ik analyseer sensordata... Verdampertemp -40°C (te koud door ijs), zuigdruk extreem laag, koelcel temp stijgt 2.8°C/uur. Dit patroon = bevroren verdamper."

Args:
    asset_id: Asset identifier (e.g., "135_1570")
    timestamp: ISO format timestamp (e.g., "2024-10-15T12:00:00"). If None, uses historical demo timestamp.
              Can be ANY timestamp from Jul 2024 - Jan 2026 for historical analysis.
    window_minutes: Time window for computation. Default: 60 minutes.

Returns:
    WorldState dict with 58+ computed features including current_state, trends, flags, health_scores.
"""
    yield Status(f"Loading telemetry data for asset {asset_id}...")
    
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    # Parse timestamp - use historical demo timestamp within data range
    # Telemetry data range: 2022-10-20 to 2024-04-01
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            # Default to historical timestamp within data range
            ts = datetime(2024, 1, 15, 12, 0, 0)
    else:
        # Use default historical timestamp for demo (data ends 2024-04-01)
        ts = datetime(2024, 1, 15, 12, 0, 0)
    
    # Initialize engine
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    yield Status(f"Computing WorldState for {window_minutes}-minute window...")
    
    try:
        # Compute features
        worldstate = engine.compute_worldstate(asset_id, ts, window_minutes)
        
        # Store in hidden environment if available (for cross-tool access)
        if tree_data and hasattr(tree_data.environment, 'hidden_environment'):
            tree_data.environment.hidden_environment["worldstate"] = worldstate
            tree_data.environment.hidden_environment["worldstate_timestamp"] = ts.isoformat()
        
        yield Result(
            objects=[worldstate],
            metadata={
                "source": "worldstate_engine",
                "window_minutes": window_minutes,
                "features_computed": len(worldstate.keys()) if isinstance(worldstate, dict) else 0
            }
        )
    except Exception as e:
        yield Error(f"Error computing WorldState: {str(e)}")
        return


@tool(
    status="Computing asset health (W vs C)...",
    branch_id="smido_diagnose"
)
async def get_asset_health(
    asset_id: str,
    timestamp: str = None,
    window_minutes: int = 60,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """Compare WorldState (W) against Context (C) - implements "Koelproces uit balans" check.

When to use:
- M (MELDING): Quick health check after symptom reported
- T (TECHNISCH): Verify if system operating within design parameters
- P2 (PROCESINSTELLINGEN): Compare actual vs design settings

What it analyzes:
- Computes current WorldState (W) from sensors
- Loads commissioning data (Context C) - design parameters
- Compares W vs C for: room temp, hot gas, suction, liquid temps
- Identifies deviations from design (out of balance factors)

Output interpretation:
- overall_health="in_balance" → System operating within design
- overall_health="uit_balans" → System outside design parameters
- out_of_balance_factors → List of specific deviations with severity
- recommendations → Suggested next steps based on balance issues

How to explain to M:
"Ik vergelijk nu de huidige metingen (WorldState) met de ontwerpwaarden (Context)..."
[after tool runs]
"Het systeem is [in_balance/uit_balans]. Ik zie: [factor] is [deviation]. Dit wijst op [interpretation]."

Example (A3 frozen evaporator):
"W vs C vergelijking toont: koelcel 0°C (design: -33°C) = 33°C afwijking. System UIT BALANS. Verdamper waarschijnlijk bevroren (blokkeert koeling)."

Key concept:
Een storing betekent NIET altijd een defect component. System kan "uit balans" zijn door:
verkeerde instellingen, omgevingscondities, of capaciteit mismatch.

Args:
    asset_id: Asset identifier (e.g., "135_1570")
    timestamp: ISO format timestamp. If None, uses historical demo timestamp.
    window_minutes: Time window for WorldState computation. Default: 60.

Returns:
    Health summary dict with overall_health, out_of_balance_factors, recommendations.
"""
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Loading installation context (C)...")
    
    # 1. Get Context (C) from FD_Assets or enrichment file
    import json
    from pathlib import Path
    from datetime import datetime
    
    # Load commissioning data from enrichment file
    enrichment_path = Path("features/integration_vsm/output/fd_assets_enrichment.json")
    if not enrichment_path.exists():
        yield Error(f"Enrichment file not found: {enrichment_path}")
        return
    
    with open(enrichment_path) as f:
        context = json.load(f)
    
    commissioning = context["commissioning_data"]
    balance_params = context["balance_check_parameters"]
    operational_limits = context["operational_limits"]
    
    yield Status("Computing current WorldState (W)...")
    
    # 2. Compute WorldState (W) - use WorldStateEngine
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    
    # Handle timestamp: check for None, empty string, or string 'None'
    # Use current time (will auto-detect "today" and inject A3 if needed)
    # Data range after rebase: Jul 2024 - Jan 2026
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            # Default to current time (datetime.now() triggers A3 demo)
            ts = datetime.now()
    else:
        # Use current time by default (triggers A3 demo if today)
        ts = datetime.now()
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    try:
        worldstate = engine.compute_worldstate(asset_id, ts, window_minutes)
    except Exception as e:
        yield Error(f"Error computing WorldState: {str(e)}")
        return
    
    yield Status("Comparing W vs C (balance check)...")
    
    # 3. Compare W vs C - balance check
    current_state = worldstate.get("current_state", {})
    out_of_balance = []
    
    # Room temp check
    current_temp = current_state.get("current_room_temp")
    target_temp = commissioning.get("target_temp")
    if current_temp is not None and target_temp is not None:
        deviation = abs(current_temp - target_temp)
        if deviation > 5:  # More than 5°C deviation
            out_of_balance.append({
                "factor": "room_temperature",
                "current": current_temp,
                "design": target_temp,
                "deviation": current_temp - target_temp,
                "severity": "critical" if current_temp > operational_limits.get("room_temp_alarm_critical_C", -10) else "warning"
            })
    
    # Hot gas temp check
    hot_gas = current_state.get("current_hot_gas_temp")
    if hot_gas is not None:
        min_hot_gas = balance_params.get("hot_gas_temp_min_C", 45.0)
        max_hot_gas = balance_params.get("hot_gas_temp_max_C", 65.0)
        if hot_gas < min_hot_gas or hot_gas > max_hot_gas:
            out_of_balance.append({
                "factor": "hot_gas_temperature",
                "current": hot_gas,
                "design_range": f"{min_hot_gas}-{max_hot_gas}",
                "severity": "warning"
            })
    
    # Suction temp check
    suction_temp = current_state.get("current_suction_temp")
    if suction_temp is not None:
        min_suction = balance_params.get("suction_temp_min_C", -40.0)
        max_suction = balance_params.get("suction_temp_max_C", -35.0)
        if suction_temp < min_suction or suction_temp > max_suction:
            out_of_balance.append({
                "factor": "suction_temperature",
                "current": suction_temp,
                "design_range": f"{min_suction}-{max_suction}",
                "severity": "warning"
            })
    
    # Liquid temp check (should be reasonable)
    liquid_temp = current_state.get("current_liquid_temp")
    if liquid_temp is not None:
        design_liquid = commissioning.get("liquid_temp_design", 28.0)
        if abs(liquid_temp - design_liquid) > 10:
            out_of_balance.append({
                "factor": "liquid_temperature",
                "current": liquid_temp,
                "design": design_liquid,
                "deviation": liquid_temp - design_liquid,
                "severity": "warning"
            })
    
    # Generate health summary
    health = {
        "asset_id": asset_id,
        "timestamp": ts.isoformat(),
        "overall_health": "uit_balans" if out_of_balance else "in_balance",
        "out_of_balance_factors": out_of_balance,
        "worldstate_summary": {
            "current_room_temp": current_state.get("current_room_temp"),
            "current_hot_gas_temp": current_state.get("current_hot_gas_temp"),
            "current_suction_temp": current_state.get("current_suction_temp"),
            "current_liquid_temp": current_state.get("current_liquid_temp"),
            "current_ambient_temp": current_state.get("current_ambient_temp"),
            "flags": worldstate.get("flags", {}),
            "health_scores": worldstate.get("health_scores", {})
        },
        "commissioning_data": commissioning,
        "recommendations": []
    }
    
    # Generate recommendations based on out-of-balance factors
    if out_of_balance:
        for factor in out_of_balance:
            if factor["factor"] == "room_temperature":
                if factor["current"] > target_temp:
                    health["recommendations"].append("Check koelproces balance: temperatuur te hoog. Mogelijk verdamper bevroren of ontdooicyclus defect.")
                else:
                    health["recommendations"].append("Check koelproces balance: temperatuur te laag. Mogelijk regelaar instellingen.")
            elif factor["factor"] == "hot_gas_temperature":
                health["recommendations"].append("Heetgastemperatuur buiten ontwerpbereik. Check condensor ventilatoren en warmteafvoer.")
            elif factor["factor"] == "suction_temperature":
                health["recommendations"].append("Zuigtemperatuur buiten ontwerpbereik. Check verdamper en koudemiddel circulatie.")
            elif factor["factor"] == "liquid_temperature":
                health["recommendations"].append("Vloeistoftemperatuur afwijkend. Check condensor en vloeistofleiding.")
    
    # Store in hidden environment if available (for cross-tool access)
    if tree_data and hasattr(tree_data.environment, 'hidden_environment'):
        tree_data.environment.hidden_environment["asset_health"] = health
    
    yield Result(
        objects=[health],
        metadata={
            "balance_check": "completed",
            "factors_checked": len(balance_params),
            "out_of_balance_count": len(out_of_balance)
        }
    )


@tool(
    status="Analyzing sensor patterns...",
    branch_id="smido_diagnose"
)
async def analyze_sensor_pattern(
    asset_id: str,
    timestamp: str = None,
    window_minutes: int = 60,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """Match current WorldState against reference patterns - pattern recognition for failure modes.

When to use:
- P3 (PROCESPARAMETERS): After ComputeWorldState, to identify which failure mode
- P4 (PRODUCTINPUT): To detect environmental/loading issues
- When sensor readings are abnormal but you need to identify the specific problem

What it does:
- Computes current WorldState (W) with all sensor readings
- Creates summary of current conditions + flags
- Searches VSM_WorldStateSnapshot for similar patterns
- Matches against 13 reference patterns (5 from vlogs + 8 from manual)
- Returns best matching failure modes with similarity scores

Output interpretation:
- matched_patterns[0] → Best matching reference pattern
- failure_mode → Detected problem (e.g., "ingevroren_verdamper", "te_weinig_koudemiddel")
- balance_type → "factor_side", "component_defect", "settings_incorrect", or "in_balance"
- similarity_score → How well current pattern matches reference (0-1)

How to explain to M:
"Ik vergelijk nu het huidige sensorpatroon met bekende storingen..."
[after tool runs]
"Dit patroon komt overeen met: [failure_mode]. Score: [similarity]. Dit is typisch wanneer [explanation]."

Example (A3 frozen evaporator):
"Patroon match: 'ingevroren_verdamper' (90% match). Typisch: room temp hoog, zuigdruk extreem laag, hot gas laag. Dit past bij bevroren verdamper die luchtcirculatie blokkeert."

Reference patterns available:
- ws_frozen_evaporator_A3: Frozen evaporator (defrost issue)
- ws_condenser_fan_A1: Condenser fan problem
- ws_expansion_valve_A2: Expansion valve blockage
- ws_low_refrigerant_A5: Refrigerant leakage
- 8 balance patterns from manual (overbelading, vuile condensor, etc.)

Args:
    asset_id: Asset identifier (e.g., "135_1570")
    timestamp: ISO format timestamp. If None, uses historical demo timestamp.
    window_minutes: Time window for WorldState computation. Default: 60.

Returns:
    Dict with current_worldstate_summary, matched_patterns (top 3), detected_failure_mode.
"""
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Computing current WorldState...")
    
    # 1. Compute current WorldState (W)
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    # Parse timestamp - use historical demo timestamp within data range
    # Telemetry data range: 2022-10-20 to 2024-04-01
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            # Default to historical timestamp within data range
            ts = datetime(2024, 1, 15, 12, 0, 0)
    else:
        # Use default historical timestamp for demo (data ends 2024-04-01)
        ts = datetime(2024, 1, 15, 12, 0, 0)
    
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    try:
        worldstate = engine.compute_worldstate(asset_id, ts, window_minutes)
    except Exception as e:
        yield Error(f"Error computing WorldState: {str(e)}")
        return
    
    yield Status("Querying reference patterns...")
    
    # 2. Query VSM_WorldStateSnapshot for similar patterns
    current_state = worldstate.get("current_state", {})
    flags = worldstate.get("flags", {})
    trends_30m = worldstate.get("trends_30m", {})
    
    # Create summary string for semantic search
    ws_summary = f"Room temp: {current_state.get('current_room_temp', 'N/A')}°C, "
    ws_summary += f"Hot gas: {current_state.get('current_hot_gas_temp', 'N/A')}°C, "
    ws_summary += f"Suction: {current_state.get('current_suction_temp', 'N/A')}°C, "
    ws_summary += f"Liquid: {current_state.get('current_liquid_temp', 'N/A')}°C"
    
    # Add flag information
    flag_descriptions = []
    if flags.get("main_temp_high"):
        flag_descriptions.append("main temp high")
    if flags.get("suction_extreme"):
        flag_descriptions.append("suction extreme")
    if flags.get("hot_gas_low"):
        flag_descriptions.append("hot gas low")
    if flags.get("liquid_extreme"):
        flag_descriptions.append("liquid extreme")
    
    if flag_descriptions:
        ws_summary += f". Flags: {', '.join(flag_descriptions)}"
    
    try:
        async with client_manager.connect_to_async_client() as client:
            # Check if collection exists
            if not await client.collections.exists("VSM_WorldStateSnapshot"):
                yield Error("VSM_WorldStateSnapshot collection not found in Weaviate.")
                return
            
            snapshots = client.collections.get("VSM_WorldStateSnapshot")
            
            # Semantic search on typical_pattern
            results = await snapshots.query.near_text(
                query=ws_summary,
                limit=3
            )
            
            yield Status(f"Found {len(results.objects)} similar patterns")
            
            # 3. Match patterns - find best match
            matches = []
            for snapshot in results.objects:
                props = snapshot.properties
                match = {
                    "snapshot_id": props.get("snapshot_id"),
                    "failure_mode": props.get("failure_mode"),
                    "typical_pattern": props.get("typical_pattern"),
                    "balance_factors": props.get("balance_factors", []),
                    "uit_balans_type": props.get("uit_balans_type"),
                    "affected_components": props.get("affected_components", []),
                    "related_failure_modes": props.get("related_failure_modes", []),
                    "similarity_score": 0.8  # Placeholder - can compute actual similarity based on worldstate_json
                }
                matches.append(match)
            
            # 4. Generate analysis
            analysis = {
                "current_worldstate": {
                    "room_temp": current_state.get("current_room_temp"),
                    "hot_gas_temp": current_state.get("current_hot_gas_temp"),
                    "suction_temp": current_state.get("current_suction_temp"),
                    "liquid_temp": current_state.get("current_liquid_temp"),
                    "ambient_temp": current_state.get("current_ambient_temp"),
                    "door_open": current_state.get("current_door_open"),
                    "flags": flags,
                    "trends_30m": trends_30m,
                    "health_scores": worldstate.get("health_scores", {})
                },
                "matched_patterns": matches,
                "detected_failure_mode": matches[0]["failure_mode"] if matches else None,
                "is_uit_balans": matches[0]["uit_balans_type"] != "in_balance" if matches and matches[0].get("uit_balans_type") else False,
                "balance_factors_violated": matches[0]["balance_factors"] if matches else [],
                "affected_components": matches[0]["affected_components"] if matches else []
            }
            
            # Store in hidden environment if available (for cross-tool access)
            if tree_data and hasattr(tree_data.environment, 'hidden_environment'):
                tree_data.environment.hidden_environment["sensor_pattern_analysis"] = analysis
            
            yield Result(
                objects=[analysis],
                metadata={
                    "patterns_checked": len(results.objects),
                    "best_match": matches[0]["failure_mode"] if matches else None,
                    "uit_balans_detected": analysis["is_uit_balans"]
                }
            )
            
    except Exception as e:
        yield Error(f"Error querying patterns: {str(e)}")
        return


@tool(
    status="Fetching diagram...",
    branch_id="smido_installatie"
)
async def show_diagram(
    diagram_id: str = None,
    smido_step: str = None,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Show a Mermaid diagram to the user - displays visual flowcharts and schematics.
    
    Use this when:
    - User asks "show me a diagram", "laat een schema zien", "visualiseer het systeem"
    - Explaining SMIDO methodology (use diagram_id="smido_overview")
    - Showing refrigeration cycle (use diagram_id="basic_cycle")  
    - Explaining diagnosis steps (use diagram_id="diagnose_4ps")
    - SMIDO phase needs visual aid (use smido_step filter)
    
    Available diagrams:
    - smido_overview: Complete SMIDO M→T→I→D→O flow
    - diagnose_4ps: 4 P's diagnostic checklist  
    - basic_cycle: Refrigeration cycle basics
    - measurement_points: Where to measure P/T
    - system_balance: "Uit balans" concept explained
    - pressostat_settings: Pressostat adjustment guide
    - frozen_evaporator: A3 frozen evaporator case
    
    Args:
        diagram_id: Specific diagram ID to fetch (optional)
        smido_step: Filter diagrams by SMIDO phase (optional, e.g., "3P_power", "installatie_vertrouwd")
    
    Returns:
        Mermaid diagram code in markdown format for frontend rendering
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    if not diagram_id and not smido_step:
        yield Error("Either diagram_id or smido_step must be provided.")
        return
    
    yield Status("Searching for diagram...")
    
    try:
        async with client_manager.connect_to_async_client() as client:
            # Check collections exist
            user_exists = await client.collections.exists("VSM_DiagramUserFacing")
            agent_exists = await client.collections.exists("VSM_DiagramAgentInternal")
            
            if not (user_exists or agent_exists):
                yield Error("Diagram collections not found in Weaviate.")
                return
            
            diagram_objects = []
            
            # Strategy 1: Fetch by diagram_id
            if diagram_id:
                if user_exists:
                    user_coll = client.collections.get("VSM_DiagramUserFacing")
                    user_results = await user_coll.query.fetch_objects(
                        filters=Filter.by_property("diagram_id").equal(diagram_id),
                        limit=1
                    )
                    if user_results.objects:
                        diagram_objects.extend(user_results.objects)
                
                if agent_exists and not diagram_objects:
                    agent_coll = client.collections.get("VSM_DiagramAgentInternal")
                    agent_results = await agent_coll.query.fetch_objects(
                        filters=Filter.by_property("diagram_id").equal(diagram_id),
                        limit=1
                    )
                    if agent_results.objects:
                        diagram_objects.extend(agent_results.objects)
            
            # Strategy 2: Fetch by smido_step
            elif smido_step:
                phase_map = {
                    "melding": ["M", "melding"],
                    "technisch": ["T", "technisch"],
                    "installatie_vertrouwd": ["I", "installatie"],
                    "3P_power": ["P1", "power"],
                    "3P_procesinstellingen": ["P2", "procesinstellingen"],
                    "3P_procesparameters": ["P3", "procesparameters"],
                    "3P_productinput": ["P4", "productinput"],
                    "ketens_onderdelen": ["O", "onderdelen"],
                }
                
                if smido_step in phase_map:
                    phases = phase_map[smido_step]
                    
                    if agent_exists:
                        agent_coll = client.collections.get("VSM_DiagramAgentInternal")
                        agent_results = await agent_coll.query.fetch_objects(
                            filters=Filter.by_property("smido_phases").contains_any(phases),
                            limit=3
                        )
                        diagram_objects.extend(agent_results.objects)
            
            if not diagram_objects:
                yield Error(f"No diagram found for diagram_id='{diagram_id}' or smido_step='{smido_step}'")
                return
            
            yield Status(f"Found {len(diagram_objects)} diagram(s)")
            
            # Format diagrams for display - handle both PNG (UserFacing) and Mermaid (AgentInternal)
            diagram_output = []
            for obj in diagram_objects:
                props = obj.properties
                
                # Build markdown output
                title = props.get("title", "Diagram")
                description = props.get("description", "")
                png_url = props.get("png_url")
                mermaid_code = props.get("mermaid_code", "")
                
                markdown = None
                
                # Check for PNG first (UserFacing diagrams)
                if png_url:
                    # Build full URL for PNG image
                    full_url = f"http://localhost:8000{png_url}"
                    markdown = f"**📊 {title}**\n\n"
                    if description:
                        markdown += f"*{description}*\n\n"
                    markdown += f"![{title}]({full_url})"
                    
                    diagram_output.append({
                        "diagram_id": props.get("diagram_id"),
                        "title": title,
                        "description": description,
                        "markdown": markdown,
                        "png_url": png_url
                    })
                
                # Fallback to Mermaid (AgentInternal diagrams)
                elif mermaid_code:
                    markdown = f"**📊 {title}**\n\n"
                    if description:
                        markdown += f"*{description}*\n\n"
                    markdown += f"```mermaid\n{mermaid_code}\n```"
                    
                    diagram_output.append({
                        "diagram_id": props.get("diagram_id"),
                        "title": title,
                        "description": description,
                        "markdown": markdown,
                        "mermaid_code": mermaid_code
                    })
            
            if not diagram_output:
                yield Error("Diagram found but contains neither PNG nor Mermaid code")
                return
            
            # Return as Response with formatted markdown for direct display
            yield Response(diagram_output[0]["markdown"])
            
            # Also yield Result for structured data with payload_type for frontend rendering
            yield Result(
                objects=diagram_output,
                payload_type="diagram",
                metadata={
                    "diagram_count": len(diagram_output),
                    "diagram_id": diagram_id,
                    "smido_step": smido_step
                }
            )
            
    except Exception as e:
        yield Error(f"Error fetching diagram: {str(e)}")
        return


@tool(
    status="Creating temperature timeline visualization...",
    branch_id="smido_p3_procesparameters"
)
async def visualize_temperature_timeline(
    asset_id: str = "135_1570",
    hours_back: int = 24,
    timestamp: str = None,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Visualize temperature trends over time with setpoint comparison - area chart for telemetry analysis.
    
    Use this when:
    - P3 (PROCESPARAMETERS): Analyzing temperature trends vs design values
    - Need to show how room temp changed over time
    - Comparing actual performance against target setpoint
    - Identifying when system went "uit balans"
    
    What it shows:
    - Room temperature timeline (area chart with gradient)
    - Target setpoint line (from FD_Assets Context C)
    - Visual threshold bands (critical/warning/ok zones)
    - Time range: last N hours of telemetry data
    
    Output interpretation:
    - Blue area = Actual room temperature
    - Green line = Design setpoint (-22.5°C typically)
    - Red zone = Critical (temp too high)
    - Yellow zone = Warning
    - Green zone = OK range
    
    How to explain to M:
    "Ik laat nu een temperatuuroverzicht zien van de laatste 24 uur..."
    [after tool runs]
    "Je ziet hier dat de kamertemperatuur rond [time] begon te stijgen boven het setpoint. 
    Dit duidt op verminderde koelprestaties."
    
    Args:
        asset_id: Asset identifier (default: "135_1570")
        hours_back: Hours of history to show (default: 24)
        timestamp: Reference timestamp (ISO format). If None, uses historical demo data.
    
    Returns:
        Area chart with temperature timeline, setpoint, and threshold bands
    """
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime, timedelta
    import pandas as pd
    
    yield Status(f"Loading telemetry data for last {hours_back} hours...")
    
    # Parse timestamp - use historical demo timestamp
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            end_time = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            end_time = datetime(2024, 1, 15, 12, 0, 0)
    else:
        end_time = datetime(2024, 1, 15, 12, 0, 0)
    
    start_time = end_time - timedelta(hours=hours_back)
    
    # Load parquet data
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    try:
        # Read parquet directly for time range
        df = pd.read_parquet("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
        
        # Reset index to make timestamp a column (it's the index in the parquet file)
        df = df.reset_index()
        
        # Filter to time range
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        mask = (df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)
        df_filtered = df[mask].sort_values('timestamp')
        
        if len(df_filtered) == 0:
            yield Error(f"No telemetry data found between {start_time} and {end_time}")
            return
        
        # Get target setpoint from FD_Assets (Context C)
        target_temp = -22.5  # Default target
        
        if client_manager and client_manager.is_client:
            try:
                async with client_manager.connect_to_async_client() as client:
                    if await client.collections.exists("FD_Assets"):
                        assets = client.collections.get("FD_Assets")
                        result = await assets.query.fetch_objects(limit=1)
                        if result.objects:
                            commissioning = result.objects[0].properties.get("commissioning_data", {})
                            target_temp = commissioning.get("design_room_temp", -22.5)
            except Exception as e:
                yield Status(f"Using default setpoint (couldn't load from FD_Assets): {str(e)}")
        
        yield Status(f"Found {len(df_filtered)} data points, creating visualization...")
        
        # Sample if too many points (keep max 500 for performance)
        if len(df_filtered) > 500:
            step = len(df_filtered) // 500
            df_filtered = df_filtered.iloc[::step]
        
        # Prepare data for area chart
        timestamps = df_filtered['timestamp'].dt.strftime('%H:%M').tolist()
        room_temps = df_filtered['sGekoeldeRuimte'].tolist()  # Room temperature column
        setpoint_data = [target_temp] * len(timestamps)
        
        # Create area chart
        chart_data = {
            "title": f"Temperature Timeline - Last {hours_back} Hours",
            "description": f"Room temperature vs setpoint (target: {target_temp}°C)",
            "x_axis_label": "Time",
            "y_axis_label": "Temperature (°C)",
            "data": {
                "x_axis": timestamps,
                "series": [
                    {
                        "name": "Room Temperature",
                        "data": room_temps,
                        "color": "#3B82F6",
                        "fill_opacity": 0.4
                    },
                    {
                        "name": "Setpoint",
                        "data": setpoint_data,
                        "color": "#10B981",
                        "fill_opacity": 0.1
                    }
                ]
            }
        }
        
        # Store in hidden environment for cross-tool access
        if tree_data:
            tree_data.environment.hidden_environment["temperature_timeline"] = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_points": len(timestamps),
                "avg_temp": sum(room_temps) / len(room_temps),
                "target_temp": target_temp,
                "deviation": (sum(room_temps) / len(room_temps)) - target_temp
            }
        
        yield Result(
            objects=[chart_data],
            payload_type="area_chart",
            metadata={
                "asset_id": asset_id,
                "time_range_hours": hours_back,
                "data_points": len(timestamps),
                "target_temp": target_temp,
                "avg_temp": round(sum(room_temps) / len(room_temps), 2)
            }
        )
        
    except Exception as e:
        yield Error(f"Error creating temperature timeline: {str(e)}")
        return


@tool(
    status="Creating health score dashboard...",
    branch_id="smido_diagnose"
)
async def show_health_dashboard(
    asset_id: str = "135_1570",
    timestamp: str = None,
    window_minutes: int = 60,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Display system health scores as gauge-style radial bars - visual health overview.
    
    Use this when:
    - D (DIAGNOSE): Need quick visual of overall system health
    - M (MELDING): First assessment after symptom reported
    - Want to show monteur current state in one view
    
    What it shows:
    - Cooling Performance (0-100): How well system maintains target temp
    - Compressor Health (0-100): Compressor efficiency and operation
    - System Stability (0-100): Overall system stability and consistency
    
    Color coding:
    - Green (70-100): Good / Gezond
    - Yellow (30-70): Warning / Waarschuwing
    - Red (0-30): Critical / Kritiek
    
    How to explain to M:
    "Ik laat nu de gezondheidsscores van het systeem zien..."
    [after tool runs]
    "Koelprestaties: [score]/100 ([status]). Dit betekent dat [interpretation]."
    
    Args:
        asset_id: Asset identifier (default: "135_1570")
        timestamp: Reference timestamp (ISO format). If None, uses historical demo.
        window_minutes: Time window for health computation (default: 60)
    
    Returns:
        Radial bar chart with 3 health gauges
    """
    yield Status("Computing health scores...")
    
    # Compute asset health using existing tool logic
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    # Parse timestamp
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            ts = datetime(2024, 1, 15, 12, 0, 0)
    else:
        ts = datetime(2024, 1, 15, 12, 0, 0)
    
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    try:
        # Compute WorldState
        worldstate = engine.compute_worldstate(asset_id, ts, window_minutes)
        health_scores = worldstate.get("health_scores", {})
        
        # Get scores
        cooling_score = health_scores.get("cooling_performance_score", 50)
        compressor_score = health_scores.get("compressor_health_score", 50)
        stability_score = health_scores.get("system_stability_score", 50)
        
        # Helper function for color coding
        def get_color_for_score(score):
            if score >= 70:
                return "#10B981"  # Green
            elif score >= 30:
                return "#F59E0B"  # Yellow
            else:
                return "#EF4444"  # Red
        
        yield Status("Creating health dashboard...")
        
        chart_data = {
            "title": "System Health Overview",
            "description": f"Current health metrics for asset {asset_id}",
            "data": [
                {
                    "name": "Cooling Performance",
                    "value": round(cooling_score, 1),
                    "max_value": 100,
                    "color": get_color_for_score(cooling_score)
                },
                {
                    "name": "Compressor Health",
                    "value": round(compressor_score, 1),
                    "max_value": 100,
                    "color": get_color_for_score(compressor_score)
                },
                {
                    "name": "System Stability",
                    "value": round(stability_score, 1),
                    "max_value": 100,
                    "color": get_color_for_score(stability_score)
                }
            ]
        }
        
        # Store in hidden environment
        if tree_data:
            tree_data.environment.hidden_environment["health_dashboard"] = {
                "cooling": cooling_score,
                "compressor": compressor_score,
                "stability": stability_score,
                "timestamp": ts.isoformat()
            }
        
        yield Result(
            objects=[chart_data],
            payload_type="radial_bar_chart",
            metadata={
                "asset_id": asset_id,
                "timestamp": str(ts),
                "window_minutes": window_minutes,
                "avg_score": round((cooling_score + compressor_score + stability_score) / 3, 1)
            }
        )
        
    except Exception as e:
        yield Error(f"Error creating health dashboard: {str(e)}")
        return


@tool(
    status="Analyzing alarm distribution...",
    branch_id="smido_melding"
)
async def show_alarm_breakdown(
    asset_id: str = "135_1570",
    period_days: int = 30,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Show pie chart of alarm type distribution - overview of incident patterns.
    
    Use this when:
    - M (MELDING): Initial assessment to understand alarm history
    - Need to identify most common failure modes
    - Showing monteur what types of problems occur most often
    
    What it shows:
    - Pie chart with alarm distribution by failure mode
    - Each slice shows: alarm type, count, percentage
    - Color-coded by severity/type
    
    How to explain to M:
    "Ik bekijk nu de alarmhistorie van de laatste 30 dagen..."
    [after tool runs]
    "De meeste alarmen zijn [type] ([count] keer, [%]%). Dit suggereert een patroon van [interpretation]."
    
    Args:
        asset_id: Asset identifier (default: "135_1570")
        period_days: Number of days to look back (default: 30)
    
    Returns:
        Pie chart showing alarm distribution by type
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status(f"Querying alarms for last {period_days} days...")
    
    try:
        async with client_manager.connect_to_async_client() as client:
            if not await client.collections.exists("VSM_TelemetryEvent"):
                yield Error("VSM_TelemetryEvent collection not found in Weaviate.")
                return
            
            collection = client.collections.get("VSM_TelemetryEvent")
            
            # Fetch all events (we have 12 total)
            results = await collection.query.fetch_objects(limit=50)
            
            if not results.objects:
                yield Error("No alarm events found in database")
                return
            
            yield Status(f"Found {len(results.objects)} events, analyzing distribution...")
            
            # Group by failure mode
            alarm_counts = {}
            for obj in results.objects:
                failure_mode = obj.properties.get("failure_mode", "Unknown")
                alarm_counts[failure_mode] = alarm_counts.get(failure_mode, 0) + 1
            
            # Map failure modes to readable names and colors
            failure_mode_names = {
                "ingevroren_verdamper": "Frozen Evaporator",
                "te_weinig_koudemiddel": "Low Refrigerant",
                "condensor_ventilator": "Condenser Fan Issue",
                "expansieventiel_blokkade": "Expansion Valve Block",
                "verkeerde_instellingen": "Incorrect Settings",
                "Unknown": "Other/Unknown"
            }
            
            failure_mode_colors = {
                "ingevroren_verdamper": "#EF4444",  # Red - critical
                "te_weinig_koudemiddel": "#F59E0B",  # Orange - warning
                "condensor_ventilator": "#3B82F6",  # Blue
                "expansieventiel_blokkade": "#8B5CF6",  # Purple
                "verkeerde_instellingen": "#EC4899",  # Pink
                "Unknown": "#6B7280"  # Gray
            }
            
            # Create pie chart data
            pie_slices = []
            total_alarms = sum(alarm_counts.values())
            
            for failure_mode, count in sorted(alarm_counts.items(), key=lambda x: x[1], reverse=True):
                pie_slices.append({
                    "name": failure_mode_names.get(failure_mode, failure_mode),
                    "value": count,
                    "color": failure_mode_colors.get(failure_mode, "#6B7280")
                })
            
            chart_data = {
                "title": f"Alarm Distribution - Last {period_days} Days",
                "description": f"Breakdown of {total_alarms} alarm events by failure mode",
                "data": pie_slices
            }
            
            # Store in hidden environment
            if tree_data:
                tree_data.environment.hidden_environment["alarm_breakdown"] = {
                    "total_alarms": total_alarms,
                    "most_common": pie_slices[0]["name"] if pie_slices else "None",
                    "period_days": period_days
                }
            
            yield Result(
                objects=[chart_data],
                payload_type="pie_chart",
                metadata={
                    "asset_id": asset_id,
                    "period_days": period_days,
                    "total_alarms": total_alarms,
                    "unique_types": len(pie_slices)
                }
            )
            
    except Exception as e:
        yield Error(f"Error creating alarm breakdown: {str(e)}")
        return


@tool(
    status="Searching manual images...",
    branch_id="smido_installatie"
)
async def search_manual_images(
    query: str = "",
    smido_step: str = None,
    component: str = None,
    limit: int = 2,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Search manual images for visual troubleshooting support.
    
    Use when:
    - T (TECHNISCH): Show what healthy components look like
    - I (INSTALLATIE): Show schema/wiring photos for reference
    - D (DIAGNOSE): Visual comparison - 'Lijkt dit op wat je ziet?'
    - O (ONDERDELEN): Show component photos for identification
    - User asks to see a photo/image of a component
    
    Source: VSM_ManualImage collection (233 images from 3 manuals)
    
    Args:
        query: Description of what to find (e.g., "verdamper foto", "pressostaat aansluiting")
        smido_step: Filter by SMIDO phase (optional)
        component: Filter by component name (verdamper, compressor, etc.)
        limit: Max images to return. Default: 5
    
    Returns:
        List of image objects with:
        - image_url: URL to display in frontend
        - image_description: What the image shows
        - manual_name: Which manual it's from
        - page_number: Original page
        - component_tags: Relevant components
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    yield Status("Searching manual images...")
    
    try:
        async with client_manager.connect_to_async_client() as client:
            # Check collection exists
            if not await client.collections.exists("VSM_ManualImage"):
                yield Error("VSM_ManualImage collection not found. Run upload_manual_images_weaviate.py first.")
                return
            
            collection = client.collections.get("VSM_ManualImage")
            
            # Build filters
            from weaviate.classes.query import Filter
            filters = None
            
            if component:
                filters = Filter.by_property("component_tags").contains_any([component])
            
            if smido_step:
                # Map SMIDO step to tag
                step_map = {
                    "melding": ["M"],
                    "technisch": ["T"],
                    "installatie_vertrouwd": ["I"],
                    "3P_power": ["P1"],
                    "3P_procesinstellingen": ["P2"],
                    "3P_procesparameters": ["P3"],
                    "3P_productinput": ["P4"],
                    "ketens_onderdelen": ["O"],
                }
                
                if smido_step in step_map:
                    smido_filter = Filter.by_property("smido_tags").contains_any(step_map[smido_step])
                    filters = filters & smido_filter if filters else smido_filter
            
            # Perform search
            if query:
                # Hybrid search (semantic + keyword)
                results = await collection.query.hybrid(
                    query=query,
                    filters=filters,
                    limit=limit
                )
            else:
                # Filter-only search
                results = await collection.query.fetch_objects(
                    filters=filters,
                    limit=limit
                )
            
            yield Status(f"Found {len(results.objects)} images")
            
            # Format results
            image_objects = []
            for obj in results.objects:
                props = obj.properties
                image_objects.append({
                    "image_id": props.get("image_id"),
                    "image_url": props.get("image_url"),
                    "image_description": props.get("image_description", ""),
                    "manual_name": props.get("manual_name"),
                    "page_number": props.get("page_number"),
                    "component_tags": props.get("component_tags", []),
                    "smido_tags": props.get("smido_tags", []),
                })
            
            # Store in tree environment for context (no direct assignment needed - Result handles it)
            
            yield Result(
                objects=image_objects,
                metadata={
                    "num_images": len(image_objects),
                    "query": query,
                    "filters": {"component": component, "smido_step": smido_step}
                },
                payload_type="image_gallery"
            )
    
    except Exception as e:
        yield Error(f"Error searching images: {str(e)}")
        return
