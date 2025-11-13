#!/usr/bin/env python3
"""
Enrich manual image metadata with SMIDO relevance and component tags.

Reads visual_chunks.jsonl files, extracts component keywords from image descriptions,
and creates enriched metadata for Weaviate upload.
"""
import json
from pathlib import Path
import re

# Component keywords for tagging
COMPONENT_KEYWORDS = {
    "verdamper": ["verdamper", "evaporator"],
    "compressor": ["compressor", "comp"],
    "condensor": ["condensor", "condenser"],
    "pressostaat": ["pressostaat", "pressostat", "pressure switch"],
    "expansieventiel": ["expansieventiel", "expansion valve", "smoorventiel"],
    "filter": ["filter", "droger", "drier"],
    "thermostat": ["thermostat", "temperatuur", "temperature sensor"],
    "ventilator": ["ventilator", "fan", "lucht"],
    "leiding": ["leiding", "pipe", "heetgas", "zuig", "vloeistof"],
    "kijkglas": ["kijkglas", "sight glass", "zichtglas"],
    "regelaar": ["regelaar", "controller", "regeling"],
}

# SMIDO phase keywords (simplified - can be enhanced)
SMIDO_KEYWORDS = {
    "M": ["symptoom", "alarm", "storing", "probleem", "melding"],
    "T": ["visueel", "inspectie", "controle", "check"],
    "I": ["schema", "diagram", "circuit", "wiring", "installatie"],
    "P1": ["elektrisch", "spanning", "stroom", "power", "voeding"],
    "P2": ["instelling", "parameter", "setpoint", "configuratie"],
    "P3": ["meting", "sensor", "temperatuur", "druk", "measurement"],
    "P4": ["omgeving", "ambient", "buitentemperatuur", "environment"],
    "O": ["component", "onderdeel", "demontage", "vervangen"],
}

def extract_component_tags(description: str) -> list[str]:
    """Extract component tags from image description."""
    description_lower = description.lower()
    tags = []
    
    for component, keywords in COMPONENT_KEYWORDS.items():
        if any(kw in description_lower for kw in keywords):
            tags.append(component)
    
    return list(set(tags))

def extract_smido_tags(description: str) -> list[str]:
    """Infer SMIDO relevance from image description."""
    description_lower = description.lower()
    tags = []
    
    for phase, keywords in SMIDO_KEYWORDS.items():
        if any(kw in description_lower for kw in keywords):
            tags.append(phase)
    
    return list(set(tags))

def get_manual_short_name(full_path: str) -> str:
    """Map full manual name to short name."""
    if "storingzoeken" in full_path:
        return "storingzoeken"
    elif "opbouw-en-werking" in full_path:
        return "opbouw-werking"
    elif "inspectie-en-onderhoud" in full_path:
        return "inspectie-onderhoud"
    return "unknown"

def main():
    print("=" * 80)
    print("Enriching Manual Image Metadata")
    print("=" * 80)
    
    source_base = Path("features/extraction/production_output")
    output_file = Path("features/manuals_vsm/output/manual_images_enriched.jsonl")
    
    # Ensure output dir exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Process each manual
    enriched_images = []
    
    manuals = [
        ("storingzoeken-koeltechniek_theorie_179", "storingzoeken"),
        ("koelinstallaties-opbouw-en-werking_theorie_2016", "opbouw-werking"),
        ("koelinstallaties-inspectie-en-onderhoud_theorie_168", "inspectie-onderhoud")
    ]
    
    for source_name, target_name in manuals:
        jsonl_file = source_base / source_name / f"{source_name}.visual_chunks.jsonl"
        
        if not jsonl_file.exists():
            print(f"\n⚠️  Skipping {source_name}: visual_chunks.jsonl not found")
            continue
        
        print(f"\n{source_name}:")
        print("-" * 80)
        
        with open(jsonl_file) as f:
            chunks = [json.loads(line) for line in f if line.strip()]
        
        print(f"  Loaded {len(chunks)} visual chunks")
        
        for chunk in chunks:
            # Extract description from markdown
            markdown = chunk.get("markdown", "")
            
            # Remove markdown formatting to get clean description
            # Format: <::Description: figure::>
            description = re.sub(r'<::.*?:', '', markdown)
            description = re.sub(r': (figure|diagram|image)::>', '', description)
            description = description.strip()
            
            # Extract tags
            component_tags = extract_component_tags(description)
            smido_tags = extract_smido_tags(description)
            
            # Build enriched object
            enriched = {
                "chunk_id": chunk["chunk_id"],
                "image_url_path": f"/static/manual_images/{target_name}/{chunk['chunk_id']}.png",
                "image_description": description if description else "Manual image",
                "manual_name": target_name,
                "page_number": chunk["page"] + 1,  # Convert 0-indexed to 1-indexed
                "chunk_type": chunk.get("chunk_type", "figure"),
                "component_tags": component_tags,
                "smido_tags": smido_tags,
                "bbox": chunk.get("bbox", {}),
            }
            
            enriched_images.append(enriched)
        
        # Show sample tags
        tagged_count = sum(1 for img in enriched_images if img["component_tags"] or img["smido_tags"])
        print(f"  Tagged {tagged_count}/{len(enriched_images)} images with components/SMIDO")
    
    # Save enriched metadata
    print(f"\n" + "=" * 80)
    print(f"Saving enriched metadata...")
    
    with open(output_file, 'w') as f:
        for img in enriched_images:
            f.write(json.dumps(img) + '\n')
    
    print(f"✅ Saved {len(enriched_images)} enriched image records to:")
    print(f"   {output_file}")
    
    # Statistics
    print(f"\n" + "=" * 80)
    print("Statistics:")
    print("=" * 80)
    
    total_with_components = sum(1 for img in enriched_images if img["component_tags"])
    total_with_smido = sum(1 for img in enriched_images if img["smido_tags"])
    
    print(f"  Total images: {len(enriched_images)}")
    print(f"  With component tags: {total_with_components}")
    print(f"  With SMIDO tags: {total_with_smido}")
    
    # Top components
    all_components = {}
    for img in enriched_images:
        for comp in img["component_tags"]:
            all_components[comp] = all_components.get(comp, 0) + 1
    
    print(f"\n  Top components:")
    for comp, count in sorted(all_components.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {comp}: {count} images")
    
    print("\n✅ Ready for Weaviate upload!")

if __name__ == "__main__":
    main()

