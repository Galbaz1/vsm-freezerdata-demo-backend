from elysia import Tool, tool
from elysia.objects import Response, Status, Result, Error
from weaviate.classes.query import Filter
from datetime import datetime

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
    status="Retrieving current sensor readings...",
    branch_id="smido_melding"
)
async def get_current_status(
    asset_id: str = "135_1570",
    tree_data=None,
    **kwargs
):
    """Get current sensor readings (cached, instant) - Ultra-fast status check.
    
    Returns pre-cached synthetic "today" WorldState without any I/O operations.
    
    When to use:
    - User asks: "How are we doing?", "What's the current state?", "Status?", "Hoe gaat het?"
    - When you need quick sensor overview WITHOUT deep analysis
    - First response in M (Melding) phase for status requests
    - User wants to know if there's a problem (screening)
    
    When NOT to use:
    - User reports a specific problem → use get_alarms or get_asset_health
    - User asks "why/how/diagnose" → proceed to deeper SMIDO phases
    - User asks for historical data → use compute_worldstate with specific timestamp
    
    What it returns:
    - 5 key sensor readings (room, hot gas, suction, liquid, ambient)
    - Active flags (main_temp_high, suction_extreme, etc.)
    - 30m trend (is temp rising?)
    - Health scores summary (0-100)
    
    Performance: <100ms (reads from cache, no parquet/Weaviate)
    
    How to explain to M:
    "Ik check even de huidige sensorstand..."
    [instant response]
    "Oké, huidige status: Koelcel [X]°C, Heetgas [Y]°C, Zuigdruk [Z]°C. 
    Flags actief: [list]. Trend: [rising/stable/falling].
    [If problem detected] Dit wijst op [issue]. Wil je dat ik een diagnose start?"
    
    Example response (A3-like frozen evaporator):
    "Huidige status (12 nov 2025):
     - Koelcel: -1.3°C ⚠️ (design: -33°C)
     - Heetgas: 19.5°C (te laag)
     - Zuigdruk: -40.2°C (extreem koud)
     - Flags: main_temp_high, suction_extreme, hot_gas_low
     - Trend 30min: +1.2°C (stijgend)
     - Health: Koeling 22/100, Compressor 41/100
     Dit patroon lijkt op bevroren verdamper. Wil je diagnose?"
    
    Args:
        asset_id: Asset identifier (default: "135_1570")
    
    Returns:
        Concise status dict with current readings, flags, trend, health scores.
    """
    yield Status("Reading current sensor data...")
    
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    
    # Try to get from tree cache first (pre-seeded at startup)
    worldstate = None
    now = datetime.now()
    
    if tree_data and hasattr(tree_data.tree, '_initial_worldstate_cache'):
        cached_ws = tree_data.tree._initial_worldstate_cache
        # Check if cache is for today
        try:
            cached_date = datetime.fromisoformat(cached_ws["timestamp"]).date()
            if cached_date == now.date():
                worldstate = cached_ws
        except (KeyError, ValueError):
            pass
    
    # Fallback: generate if not cached or stale
    if worldstate is None:
        engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
        worldstate = engine.compute_worldstate(asset_id, now, 60)
        # Update cache
        if tree_data:
            tree_data.tree._initial_worldstate_cache = worldstate
    
    # Extract concise status
    current = worldstate.get("current_state", {})
    flags = worldstate.get("flags", {})
    trends = worldstate.get("trends_30m", {})
    health = worldstate.get("health_scores", {})
    
    # Build concise summary
    active_flags = [k.replace("flag_", "") for k, v in flags.items() if v]
    
    room_temp_delta = trends.get("room_temp_delta_30m", 0)
    trend_description = "stijgend" if room_temp_delta > 0.5 else "dalend" if room_temp_delta < -0.5 else "stabiel"
    
    status_summary = {
        "asset_id": asset_id,
        "timestamp": worldstate["timestamp"],
        "readings": {
            "room_temp": current.get("current_room_temp"),
            "hot_gas_temp": current.get("current_hot_gas_temp"),
            "suction_temp": current.get("current_suction_temp"),
            "liquid_temp": current.get("current_liquid_temp"),
            "ambient_temp": current.get("current_ambient_temp")
        },
        "active_flags": active_flags,
        "trend_30m": {
            "room_temp_change_C": room_temp_delta,
            "trend_description": trend_description
        },
        "health_summary": {
            "cooling_performance": health.get("cooling_performance_score"),
            "compressor_health": health.get("compressor_health_score"),
            "system_stability": health.get("system_stability_score")
        },
        "is_synthetic_today": worldstate.get("is_synthetic_today", False),
        "cache_hit": worldstate is not None
    }
    
    # Store full worldstate in environment for potential follow-up diagnostics
    if tree_data and hasattr(tree_data.environment, 'hidden_environment'):
        tree_data.environment.hidden_environment["worldstate"] = worldstate
        tree_data.environment.hidden_environment["worldstate_timestamp"] = worldstate["timestamp"]
    
    yield Result(
        objects=[status_summary],
        metadata={
            "source": "cached_worldstate",
            "response_type": "quick_status",
            "response_time_ms": "<100"
        }
    )


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
                
                # Check if VSM_Diagram collection exists
                if await client.collections.exists("VSM_Diagram"):
                    # Get diagram IDs from sections
                    diagram_ids = []
                    for obj in results.objects:
                        related_ids = obj.properties.get("related_diagram_ids", [])
                        if related_ids:
                            diagram_ids.extend(related_ids)
                    
                    if diagram_ids:
                        diagram_coll = client.collections.get("VSM_Diagram")
                        # Fetch unique diagrams
                        unique_diagram_ids = list(set(diagram_ids))
                        for diagram_id in unique_diagram_ids:
                            try:
                                diagram_result = await diagram_coll.query.fetch_objects(
                                    filters=Filter.by_property("diagram_id").equal(diagram_id),
                                    limit=1
                                )
                                if diagram_result.objects:
                                    diagram_objects.extend(diagram_result.objects)
                            except Exception as e:
                                # Skip if diagram not found
                                continue
                
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
                }
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
    
    Args:
        asset_id: Asset identifier (e.g., "135_1570"). Optional - if not provided, returns alarms for all assets.
        severity: Filter by severity level. Options: "critical", "warning", "info", "all". Default: "all"
    
    Returns:
        - List of alarm objects from VSM_TelemetryEvent
    
    Used in: M (Melding), P1 (Power) nodes
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
    Query historical telemetry events (similar incidents).
    Uses hybrid search if query provided, filter-only for structured search.
    
    Args:
        failure_mode: Filter by failure mode (e.g., "ingevroren_verdamper")
        components: Filter by component names (list)
        severity: Filter by severity level
        limit: Maximum number of events to return. Default: 5
    
    Returns:
        - List of telemetry event objects with WorldState summaries
    
    Used in: P4 (Productinput), O (Onderdelen) nodes
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
    """Compute WorldState (W) - 58+ sensor features from telemetry parquet.

When to use:
- P3 (PROCESPARAMETERS): When you need detailed sensor analysis
- P4 (PRODUCTINPUT): To check environmental trends
- After M reports symptom, to correlate with sensor data

What it computes:
- Current readings (temps, pressures, compressor status)
- Trends (30min, 2h, 24h windows) - rising/falling?
- Flags (_flag_main_temp_high, _flag_suction_extreme, etc.)
- Health scores (0-100, lower = worse)
- Anomaly detection

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
    timestamp: ISO format timestamp (e.g., "2025-01-01T12:00:00"). If None, uses current date (clamped to data max).
    window_minutes: Time window for computation. Default: 60 minutes.

Returns:
    WorldState dict with 58+ computed features including current_state, trends, flags, health_scores.
"""
    yield Status(f"Loading telemetry data for asset {asset_id}...")
    
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    # Parse timestamp - remove clamping to data_max, let engine handle time zones
    now = datetime.now()
    
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            ts = now  # Default to current if parse fails
    else:
        ts = now  # No timestamp = current state (will use synthetic today)
    
    # Initialize engine
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    yield Status(f"Computing WorldState for {window_minutes}-minute window...")
    
    try:
        # Compute features (engine handles time zones: past/present/future)
        worldstate = engine.compute_worldstate(asset_id, ts, window_minutes)
        
        # Store in hidden environment if available (for cross-tool access)
        if tree_data and hasattr(tree_data.environment, 'hidden_environment'):
            tree_data.environment.hidden_environment["worldstate"] = worldstate
            tree_data.environment.hidden_environment["worldstate_timestamp"] = ts.isoformat()
        
        # Extract is_future flag if present (set by engine for future zone)
        is_future = worldstate.get("is_future", False)
        
        yield Result(
            objects=[worldstate],
            metadata={
                "source": "worldstate_engine",
                "window_minutes": window_minutes,
                "features_computed": len(worldstate.keys()) if isinstance(worldstate, dict) else 0,
                "is_future": is_future,
                "is_synthetic_today": worldstate.get("is_synthetic_today", False)
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
    
    # Handle timestamp - remove clamping to data_max, let engine handle time zones
    now = datetime.now()
    
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            ts = now  # Default to current if parse fails
    else:
        ts = now  # No timestamp = current state (will use synthetic today)
    
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    try:
        # Engine handles time zones: past/present/future
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
    
    # Parse timestamp - remove clamping to data_max, let engine handle time zones
    now = datetime.now()
    
    if timestamp and timestamp != 'None' and timestamp.strip():
        try:
            ts = datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            ts = now  # Default to current if parse fails
    else:
        ts = now  # No timestamp = current state (will use synthetic today)
    
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    try:
        # Engine handles time zones: past/present/future
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
    status="Loading diagram...",
    branch_id=None  # Available in all branches
)
async def show_diagram(
    diagram_id: str,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Display a user-facing diagram (PNG) while loading the corresponding complex diagram internally for agent understanding.
    
    Args:
        diagram_id: ID of the diagram to show (e.g., "smido_overview", "basic_cycle").
    
    Use this tool when:
    - User asks "What is SMIDO?" → show_diagram("smido_overview")
    - User asks "How does it work?" → show_diagram("basic_cycle")
    - User needs visual explanation during any SMIDO phase
    
    Available diagrams:
    - smido_overview: 5-phase SMIDO workflow
    - diagnose_4ps: 4 P's checklist
    - basic_cycle: Refrigeration cycle basics
    - measurement_points: Where to measure P/T
    - system_balance: "Uit balans" concept
    - pressostat_settings: Pressostat adjustment
    - troubleshooting_template: Response format
    - frozen_evaporator: A3 case example
    
    Returns:
        - PNG URL for frontend display
        - Diagram metadata (title, description)
        - Complex Mermaid code loaded in tree environment for agent context
    """
    if not client_manager:
        yield Error("Client manager not available. Cannot query Weaviate.")
        return
    
    if not client_manager.is_client:
        yield Error("Weaviate client not configured. Please set WCD_URL and WCD_API_KEY.")
        return
    
    try:
        yield Status(f"Loading diagram '{diagram_id}'...")
        
        async with client_manager.connect_to_async_client() as client:
            # 1. Fetch user-facing diagram from VSM_DiagramUserFacing
            if not await client.collections.exists("VSM_DiagramUserFacing"):
                yield Error("VSM_DiagramUserFacing collection not found. Please upload diagrams first.")
                return
            
            user_facing_coll = client.collections.get("VSM_DiagramUserFacing")
            user_result = await user_facing_coll.query.fetch_objects(
                filters=Filter.by_property("diagram_id").equal(diagram_id),
                limit=1
            )
            
            if not user_result.objects:
                yield Error(f"Diagram '{diagram_id}' not found in VSM_DiagramUserFacing collection.")
                return
            
            user_diagram = user_result.objects[0]
            user_props = user_diagram.properties
            
            # Get agent diagram ID from user-facing diagram
            agent_diagram_id = user_props.get("agent_diagram_id")
            
            if not agent_diagram_id:
                yield Error(f"User-facing diagram '{diagram_id}' has no linked agent diagram.")
                return
            
            # 2. Fetch agent-internal diagram from VSM_DiagramAgentInternal
            if not await client.collections.exists("VSM_DiagramAgentInternal"):
                yield Error("VSM_DiagramAgentInternal collection not found. Please upload diagrams first.")
                return
            
            agent_coll = client.collections.get("VSM_DiagramAgentInternal")
            agent_result = await agent_coll.query.fetch_objects(
                filters=Filter.by_property("diagram_id").equal(agent_diagram_id),
                limit=1
            )
            
            agent_mermaid_code = None
            agent_title = None
            
            if agent_result.objects:
                agent_diagram = agent_result.objects[0]
                agent_props = agent_diagram.properties
                agent_mermaid_code = agent_props.get("mermaid_code", "")
                agent_title = agent_props.get("title", "")
            
            # 3. Store complex Mermaid in tree environment for agent context
            if tree_data and agent_mermaid_code:
                if not hasattr(tree_data.environment, 'hidden_environment'):
                    tree_data.environment.hidden_environment = {}
                
                tree_data.environment.hidden_environment[f"diagram_{diagram_id}_mermaid"] = agent_mermaid_code
                tree_data.environment.hidden_environment[f"diagram_{diagram_id}_agent_title"] = agent_title
            
            # 4. Return Result with PNG URL for frontend display
            thumb_url = ""
            try:
                png_url_val = user_props.get("png_url", "")
                if isinstance(png_url_val, str) and png_url_val:
                    thumb_url = png_url_val.replace("/static/diagrams/", "/static/diagrams/thumbs/")
            except Exception:
                thumb_url = user_props.get("png_url", "")
            yield Result(
                objects=[{
                    "diagram_id": diagram_id,
                    "png_url": user_props.get("png_url", ""),
                    "thumb_url": thumb_url,
                    "title": user_props.get("title", ""),
                    "description": user_props.get("description", ""),
                    "when_to_show": user_props.get("when_to_show", ""),
                    "png_width": user_props.get("png_width", 1200),
                    "png_height": user_props.get("png_height", 800),
                }],
                payload_type="product",  # Use built-in type with image support
                name="diagram",
                mapping={
                    "name": "title",
                    "description": "description",
                    "image": "thumb_url",
                    "url": "png_url",
                },
                unmapped_keys=["diagram_id", "when_to_show", "png_width", "png_height", "thumb_url", "_REF_ID"],
                metadata={
                    "agent_mermaid_loaded": agent_mermaid_code is not None,
                    "agent_diagram_id": agent_diagram_id,
                    "agent_title": agent_title,
                },
                llm_message=f"Displayed diagram '{user_props.get('title', diagram_id)}' to technician. Complex version loaded internally for your understanding."
            )
            
    except Exception as e:
        yield Error(f"Error loading diagram: {str(e)}")
        return
