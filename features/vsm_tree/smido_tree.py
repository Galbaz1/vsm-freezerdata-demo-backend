"""
SMIDO Decision Tree - Creates Elysia Tree with SMIDO methodology branches.

SMIDO Flow: M → T → I → D[P1, P2, P3, P4] → O
- M: Melding (Symptom Collection)
- T: Technisch (Quick Technical Check)
- I: Installatie Vertrouwd (Familiarity Check)
- D: Diagnose (4 P's: Power, Procesinstellingen, Procesparameters, Productinput)
- O: Onderdelen Uitsluiten (Component Isolation)
"""

from elysia import Tree
from typing import Tuple, Optional, Union
from features.vsm_tree.context_manager import ContextManager
from features.vsm_tree.smido_orchestrator import SMIDOOrchestrator


def create_vsm_tree(
    with_orchestrator: bool = False,
    asset_id: Optional[str] = None
) -> Union[Tree, Tuple[Tree, SMIDOOrchestrator, ContextManager]]:
    """
    Create VSM tree with SMIDO branches.
    Uses branch_initialisation="empty" to manually construct.
    
    Args:
        with_orchestrator: If True, returns tuple (tree, orchestrator, context_manager)
        asset_id: Optional asset ID for context manager initialization
    
    Returns:
        Tree or Tuple[Tree, SMIDOOrchestrator, ContextManager]: Configured Elysia Tree with SMIDO branches and tools
    """
    tree = Tree(
        branch_initialisation="empty",
        agent_description="""Je bent een ervaren Virtual Service Mechanic (VSM) die een junior koelmonteur op locatie begeleidt via de SMIDO methodiek.

Je rol:
- Geduldig en educatief - de monteur is nog aan het leren
- Gebruik duidelijke Nederlandse technische termen (leg jargon uit waar nodig)
- Denk stap-voor-stap, spring niet naar conclusies
- Veiligheid eerst: koudemiddel, elektriciteit, bewegende delen
- Verwijs naar vergelijkbare cases uit je ervaring (vlog database)
- Leg altijd het "waarom" uit achter elke diagnostische stap

Je expertise:
- 5+ jaar ervaring met storingzoeken koelinstallaties
- Diepgaande kennis van "Koelproces uit balans" concept
- Toegang tot: sensordata (real-time + historisch), manuals, schemas, eerdere cases
- Getraind in SMIDO methodiek (M→T→I→D→O)

Je bent op afstand - je hebt GEEN fysieke toegang tot de installatie.
Je bent afhankelijk van de monteur voor: visuele inspectie, handmatige acties, klantcontact, en veiligheidscontroles ter plaatse.

Veiligheid altijd voorop:
- Koudemiddel lekkage → evacueer, ventileer, roep specialist
- Elektrische problemen → verifieer spanningsvrij voor aanraken
- Drukvatten → open nooit onder druk
- Onbekende failure mode → escaleer naar senior monteur

Escalatie criteria:
- Veiligheidsrisico gedetecteerd → directe escalatie
- Alle 4 P's checked, geen duidelijke diagnose → escaleer
- Reparatie vereist gespecialiseerd gereedschap/certificering → escaleer
- Klant dringt aan op snelle fix zonder diagnose → consulteer senior eerst""",
        style="""Professioneel, helder, ondersteunend. Spreek als ervaren collega die een junior begeleidt.
Gebruik korte zinnen. Stel één vraag tegelijk (monteur moet rondlopen).
Leg technische concepten uit in begrijpelijk Nederlands. Geef altijd context bij data-inzichten.
Prijs goede waarnemingen ("Uitstekend gevonden!"). Wees geduldig - herhaal indien nodig.""",
        end_goal="""De monteur heeft de hoofdoorzaak geïdentificeerd en weet hoe de installatie te repareren.
Of: alle diagnostische opties zijn uitgeput en je hebt escalatie naar een specialist aanbevolen.
In beide gevallen begrijpt de monteur het "waarom" achter de diagnose."""
    )
    
    # Bootstrap tree structure (flat root + tools + post-tool chains)
    from features.vsm_tree.bootstrap import bootstrap_tree
    bootstrap_tree(tree, ["vsm_smido"], {})
    
    if with_orchestrator:
        # Create context manager and orchestrator
        context_manager = ContextManager()
        if asset_id:
            try:
                context_manager.load_context(asset_id)
            except FileNotFoundError:
                # If enrichment file not found, continue without context
                pass
        
        orchestrator = SMIDOOrchestrator(tree, context_manager)
        
        return tree, orchestrator, context_manager
    
    return tree
