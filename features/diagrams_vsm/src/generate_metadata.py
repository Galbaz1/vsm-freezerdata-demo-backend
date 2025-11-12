#!/usr/bin/env python3
"""
Generate metadata JSONL files for user-facing and agent-internal diagrams.

Parses Mermaid files to extract metadata from comments and creates JSONL files
for Weaviate import.

Usage:
    python3 generate_metadata.py

Output:
    - output/user_facing_diagrams.jsonl
    - output/agent_internal_diagrams.jsonl
"""

import json
import re
from pathlib import Path
from PIL import Image

# Get script directory for relative paths
SCRIPT_DIR = Path(__file__).parent
DIAGRAMS_DIR = SCRIPT_DIR.parent
MAPPING_FILE = SCRIPT_DIR / "diagram_mapping.json"
OUTPUT_DIR = DIAGRAMS_DIR / "output"

def parse_mermaid_metadata(mermaid_file: Path):
    """
    Parse metadata from Mermaid file comments.
    
    Returns dict with extracted metadata.
    """
    if not mermaid_file.exists():
        return None
    
    content = mermaid_file.read_text(encoding="utf-8")
    
    # Extract metadata from comments (%% lines)
    metadata = {}
    lines = content.split("\n")
    
    for line in lines:
        if line.startswith("%%"):
            # Remove %% and strip
            line = line[2:].strip()
            
            # Parse key: value pairs
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                metadata[key] = value
    
    # Extract mermaid code (everything after first non-comment line)
    mermaid_code = ""
    in_code = False
    for line in lines:
        if not line.startswith("%%") and line.strip():
            in_code = True
        if in_code:
            mermaid_code += line + "\n"
    
    metadata["mermaid_code"] = mermaid_code.strip()
    
    return metadata

def get_png_dimensions(png_path: Path):
    """Get PNG width and height."""
    if not png_path.exists():
        return None, None
    
    try:
        img = Image.open(png_path)
        return img.width, img.height
    except Exception:
        return None, None

def extract_smido_phases_from_metadata(metadata: dict):
    """Extract SMIDO phases from metadata or infer from when_to_show."""
    phases = []
    
    # Check if explicitly mentioned
    if "smido_phases" in metadata:
        return metadata["smido_phases"].split(",") if isinstance(metadata["smido_phases"], str) else metadata["smido_phases"]
    
    # Infer from when_to_show
    when_to_show = metadata.get("when_to_show", "").lower()
    
    phase_mapping = {
        "m phase": "melding",
        "t phase": "technisch",
        "i phase": "installatie_vertrouwd",
        "p2": "procesinstellingen",
        "p3": "procesparameters",
        "p4": "productinput",
        "d phase": ["power", "procesinstellingen", "procesparameters", "productinput"],
        "o phase": "ketens_onderdelen",
    }
    
    for key, phase in phase_mapping.items():
        if key in when_to_show:
            if isinstance(phase, list):
                phases.extend(phase)
            else:
                phases.append(phase)
    
    return list(set(phases)) if phases else []

def generate_user_facing_metadata(mappings: dict):
    """Generate user-facing diagrams metadata."""
    user_facing_records = []
    
    for diagram_id, mapping in mappings.items():
        user_facing_path = DIAGRAMS_DIR / mapping["user_facing"]
        png_path = DIAGRAMS_DIR / mapping["png_path"]
        agent_diagram_id = Path(mapping["agent_internal"]).stem
        
        # Parse metadata
        metadata = parse_mermaid_metadata(user_facing_path)
        if not metadata:
            print(f"WARNING: Could not parse metadata from {user_facing_path}")
            continue
        
        # Get PNG dimensions
        png_width, png_height = get_png_dimensions(png_path)
        
        # Build record
        record = {
            "diagram_id": diagram_id,
            "title": metadata.get("title", diagram_id.replace("_", " ").title()),
            "description": metadata.get("description", metadata.get("purpose", "")),
            "when_to_show": metadata.get("when_to_show", metadata.get("purpose", "")),
            "png_url": f"/static/diagrams/{diagram_id}.png",
            "png_width": png_width or 1200,
            "png_height": png_height or 800,
            "smido_phases": extract_smido_phases_from_metadata(metadata),
            "failure_modes": [],  # Can be enhanced later
            "components": [],  # Can be enhanced later
            "agent_diagram_id": agent_diagram_id,
        }
        
        user_facing_records.append(record)
    
    return user_facing_records

def generate_agent_internal_metadata(mappings: dict):
    """Generate agent-internal diagrams metadata."""
    agent_records = []
    
    # Load existing metadata if available
    existing_metadata_file = OUTPUT_DIR / "diagrams_metadata.jsonl"
    existing_metadata = {}
    
    if existing_metadata_file.exists():
        with open(existing_metadata_file, "r") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    existing_metadata[record["diagram_id"]] = record
    
    # Process each agent diagram
    for diagram_id, mapping in mappings.items():
        agent_internal_path = DIAGRAMS_DIR / mapping["agent_internal"]
        agent_diagram_id = Path(mapping["agent_internal"]).stem
        
        # Parse metadata
        metadata = parse_mermaid_metadata(agent_internal_path)
        if not metadata:
            print(f"WARNING: Could not parse metadata from {agent_internal_path}")
            continue
        
        # Use existing metadata if available (has more complete info)
        if agent_diagram_id in existing_metadata:
            existing = existing_metadata[agent_diagram_id]
            record = {
                "diagram_id": agent_diagram_id,
                "title": existing.get("title", metadata.get("title", "")),
                "description": existing.get("description", metadata.get("description", "")),
                "agent_usage": existing.get("agent_usage", metadata.get("agent_usage", "")),
                "mermaid_code": metadata.get("mermaid_code", existing.get("mermaid_code", "")),
                "source_chunk_id": existing.get("source_chunk_id", ""),
                "smido_phases": existing.get("smido_phases", []),
                "failure_modes": existing.get("failure_modes", []),
                "diagram_type": existing.get("diagram_type", "flowchart"),
            }
        else:
            # Build from parsed metadata
            record = {
                "diagram_id": agent_diagram_id,
                "title": metadata.get("title", agent_diagram_id.replace("_", " ").title()),
                "description": metadata.get("description", metadata.get("purpose", "")),
                "agent_usage": metadata.get("agent_usage", metadata.get("usage", "")),
                "mermaid_code": metadata.get("mermaid_code", ""),
                "source_chunk_id": metadata.get("source_chunk_id", ""),
                "smido_phases": extract_smido_phases_from_metadata(metadata),
                "failure_modes": [],
                "diagram_type": metadata.get("diagram_type", "flowchart"),
            }
        
        agent_records.append(record)
    
    return agent_records

def main():
    """Main function."""
    print("=" * 60)
    print("Diagram Metadata Generator")
    print("=" * 60)
    
    # Load mapping file
    if not MAPPING_FILE.exists():
        print(f"ERROR: Mapping file not found: {MAPPING_FILE}")
        return
    
    with open(MAPPING_FILE, "r") as f:
        mappings = json.load(f)
    
    print(f"Loaded {len(mappings)} diagram mappings")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate user-facing metadata
    print("\nGenerating user-facing diagrams metadata...")
    user_facing_records = generate_user_facing_metadata(mappings)
    user_facing_file = OUTPUT_DIR / "user_facing_diagrams.jsonl"
    
    with open(user_facing_file, "w") as f:
        for record in user_facing_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"  ✓ Created {len(user_facing_records)} user-facing records")
    print(f"  ✓ Output: {user_facing_file}")
    
    # Generate agent-internal metadata
    print("\nGenerating agent-internal diagrams metadata...")
    agent_records = generate_agent_internal_metadata(mappings)
    agent_file = OUTPUT_DIR / "agent_internal_diagrams.jsonl"
    
    with open(agent_file, "w") as f:
        for record in agent_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"  ✓ Created {len(agent_records)} agent-internal records")
    print(f"  ✓ Output: {agent_file}")
    
    print("\n" + "=" * 60)
    print("Metadata generation complete!")
    print(f"User-facing: {len(user_facing_records)} diagrams")
    print(f"Agent-internal: {len(agent_records)} diagrams")

if __name__ == "__main__":
    main()

