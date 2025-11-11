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
