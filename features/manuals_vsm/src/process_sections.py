#!/usr/bin/env python3
"""
Process manual chunks into classified sections for VSM_ManualSections collection.
Groups chunks by headings, classifies SMIDO steps (4 P's), failure modes, and components using LLM.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# SMIDO Steps - 4 P's (NOT 3!)
SMIDO_STEPS = [
    "melding",
    "technisch",
    "installatie_vertrouwd",
    "power",  # P1
    "procesinstellingen",  # P2
    "procesparameters",  # P3
    "productinput",  # P4
    "ketens_onderdelen",
    "koelproces_uit_balans",
    "overzicht",
    "algemeen"
]

# Controlled vocabularies
FAILURE_MODES = [
    "te_hoge_temperatuur", "te_lage_temperatuur",
    "ingevroren_verdamper", "slecht_ontdooien",
    "compressor_draait_niet", "compressor_kortsluiting",
    "hoge_druk", "lage_druk",
    "te_weinig_koudemiddel", "te_veel_koudemiddel",
    "vuile_condensor", "vuile_verdamper",
    "deur_probleem", "ventilator_defect",
    "regelaar_probleem", "sensor_defect",
    "lekkage", "verstopt_filter",
    "expansieventiel_defect", "koelproces_uit_balans",
    "geen_storing"
]

COMPONENTS = [
    "compressor", "verdamper", "condensor", "expansieventiel",
    "ventilator", "regelaar", "magneetklep", "pressostaat",
    "thermostat", "vloeistofvat", "filter_droger", "kijkglas",
    "ontdooiheater", "koudemiddel", "deur", "leidingen",
    "systeem_algemeen"
]

CONTENT_TYPES = [
    "uitleg", "stappenplan", "flowchart", "tabel",
    "voorbeeldcase", "diagram", "foto", "schema",
    "checklist", "definitie", "opgave"
]


def load_manual_chunks(manual_configs: List[Dict]) -> List[Dict]:
    """Load chunks from all manuals"""
    all_chunks = []
    for config in manual_configs:
        with open(config["file"], "r") as f:
            chunks = [json.loads(line) for line in f if line.strip()]
            for chunk in chunks:
                chunk["manual_id"] = config["manual_id"]
                chunk["manual_title"] = config["manual_title"]
            all_chunks.extend(chunks)
            print(f"Loaded {len(chunks)} chunks from {config['manual_id']}")
    return all_chunks


def detect_headings(markdown: str) -> List[str]:
    """Extract headings from markdown"""
    heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
    return heading_pattern.findall(markdown)


def group_chunks_into_sections(chunks: List[Dict]) -> List[Dict]:
    """Group chunks by heading hierarchy into logical sections"""
    sections = []
    current_section = None
    
    for i, chunk in enumerate(chunks):
        markdown = chunk.get("markdown", "")
        headings = detect_headings(markdown)
        
        # Start new section if chunk has heading
        if headings:
            # Save previous section
            if current_section and len(current_section["chunk_ids"]) > 0:
                sections.append(current_section)
            
            # Start new section
            current_section = {
                "section_id": f"{chunk['manual_id']}_section_{len(sections):03d}",
                "manual_id": chunk["manual_id"],
                "manual_title": chunk["manual_title"],
                "chunk_ids": [chunk["chunk_id"]],
                "title": headings[0],
                "body_text": markdown,
                "language": chunk.get("language", "nl"),
                "page_start": chunk.get("page", 0),
                "page_end": chunk.get("page", 0),
                "page_range": str(chunk.get("page", 0))
            }
        elif current_section:
            # Add to current section (max 5 chunks per section)
            if len(current_section["chunk_ids"]) < 5:
                current_section["chunk_ids"].append(chunk["chunk_id"])
                current_section["body_text"] += "\n\n" + markdown
                current_section["page_end"] = chunk.get("page", current_section["page_end"])
                current_section["page_range"] = f"{current_section['page_start']}-{current_section['page_end']}"
    
    # Add last section
    if current_section and len(current_section["chunk_ids"]) > 0:
        sections.append(current_section)
    
    return sections


def classify_section_content_type(title: str, body_text: str) -> str:
    """Classify content type based on title and body text patterns"""
    title_lower = title.lower()
    body_lower = body_text.lower()
    
    # Pattern matching for content types
    if "opgave" in title_lower or "opdracht" in title_lower:
        return "opgave"
    elif "figuur" in title_lower or "afbeelding" in title_lower:
        return "foto"
    elif "tabel" in title_lower or "| --- |" in body_text:
        return "tabel"
    elif "stappen" in title_lower or "procedure" in title_lower:
        return "stappenplan"
    elif "case:" in title_lower or "voorbeeld:" in title_lower:
        return "voorbeeldcase"
    elif "flowchart" in body_lower or "diagram" in body_lower:
        return "flowchart"
    elif "definitie" in title_lower or "wat is" in title_lower:
        return "definitie"
    else:
        return "uitleg"


def classify_smido_steps(title: str, body_text: str) -> List[str]:
    """Classify which SMIDO steps this section covers (pattern-based for speed)"""
    text = (title + " " + body_text).lower()
    steps = []
    
    # SMIDO step keywords - 4 P's
    if "melding" in text or "symptomen" in text or "klacht" in text:
        steps.append("melding")
    if "technisch" in text or "visuele inspectie" in text or "waarneembaar" in text:
        steps.append("technisch")
    if "installatie" in text and "vertrouwd" in text or "schema" in text and "kennis" in text:
        steps.append("installatie_vertrouwd")
    if "power" in text or "voeding" in text or "spanning" in text or "zekering" in text:
        steps.append("power")
    if "procesinstellingen" in text or "setpoint" in text or "thermostaat" in text or "pressostaat" in text:
        steps.append("procesinstellingen")
    if "procesparameters" in text or "meting" in text or "druk" in text and "temperatuur" in text:
        steps.append("procesparameters")
    if "productinput" in text or "belading" in text or "omgevingstemperatuur" in text or "deur" in text and "frequentie" in text:
        steps.append("productinput")
    if "ketens" in text or "onderdelen" in text and "uitsluiten" in text or "component" in text and "isolatie" in text:
        steps.append("ketens_onderdelen")
    if "balans" in text or "uit balans" in text:
        steps.append("koelproces_uit_balans")
    if "smido" in text or "aanvalsplan" in text or "methodiek" in text:
        steps.append("overzicht")
    
    # Default to algemeen if no specific step found
    if not steps:
        steps.append("algemeen")
    
    return steps


def classify_failure_modes(body_text: str) -> List[str]:
    """Extract failure modes mentioned in text (pattern-based)"""
    text = body_text.lower()
    modes = []
    
    # Pattern matching for common failure modes
    failure_patterns = {
        "te_hoge_temperatuur": ["te hoog", "te warm", "temperatuur stijgt"],
        "te_lage_temperatuur": ["te laag", "te koud", "temperatuur daalt"],
        "ingevroren_verdamper": ["bevroren verdamper", "ijsvorming", "ingevroren"],
        "slecht_ontdooien": ["ontdooi", "defrost", "ijs"],
        "compressor_draait_niet": ["compressor draait niet", "compressor uit"],
        "ventilator_defect": ["ventilator", "luchtcirculatie"],
        "vuile_condensor": ["vuile condensor", "vervuilde condensor"],
        "regelaar_probleem": ["regelaar", "controller", "parameter"],
        "deur_probleem": ["deur", "infiltratie"],
        "hoge_druk": ["hoge druk", "persdruk"],
        "lage_druk": ["lage druk", "zuigdruk"],
        "verstopt_filter": ["verstopt", "blokkade", "filterdroger"],
        "lekkage": ["lek", "lekkage"],
        "koelproces_uit_balans": ["uit balans", "balans verstoord"]
    }
    
    for mode, patterns in failure_patterns.items():
        if any(pattern in text for pattern in patterns):
            modes.append(mode)
    
    return list(set(modes))


def classify_components(body_text: str) -> List[str]:
    """Extract components mentioned in text (pattern-based)"""
    text = body_text.lower()
    found_components = []
    
    for component in COMPONENTS:
        # Check for component name or variations
        if component in text:
            found_components.append(component)
    
    return list(set(found_components))


def main():
    # Manual configurations
    manual_configs = [
        {
            "manual_id": "storingzoeken-koeltechniek_theorie_179",
            "manual_title": "Storingzoeken Koeltechniek",
            "file": "features/extraction/production_output/storingzoeken-koeltechniek_theorie_179/storingzoeken-koeltechniek_theorie_179.text_chunks.jsonl"
        },
        {
            "manual_id": "koelinstallaties-opbouw-en-werking_theorie_2016",
            "manual_title": "Koelinstallaties - Opbouw en Werking",
            "file": "features/extraction/production_output/koelinstallaties-opbouw-en-werking_theorie_2016/koelinstallaties-opbouw-en-werking_theorie_2016.text_chunks.jsonl"
        },
        {
            "manual_id": "koelinstallaties-inspectie-en-onderhoud_theorie_168",
            "manual_title": "Koelinstallaties - Inspectie en Onderhoud",
            "file": "features/extraction/production_output/koelinstallaties-inspectie-en-onderhoud_theorie_168/koelinstallaties-inspectie-en-onderhoud_theorie_168.text_chunks.jsonl"
        }
    ]
    
    # Load all chunks
    print("Loading manual chunks...")
    all_chunks = load_manual_chunks(manual_configs)
    
    # Group into sections
    print(f"\nGrouping {len(all_chunks)} chunks into sections...")
    sections = group_chunks_into_sections(all_chunks)
    print(f"Created {len(sections)} sections")
    
    # Classify each section
    print("\nClassifying sections (pattern-based)...")
    for i, section in enumerate(sections):
        # Content type
        section["content_type"] = classify_section_content_type(
            section["title"], 
            section["body_text"]
        )
        
        # SMIDO steps (4 P's!)
        section["smido_steps"] = classify_smido_steps(
            section["title"],
            section["body_text"]
        )
        section["smido_step"] = section["smido_steps"][0] if section["smido_steps"] else "algemeen"
        
        # Failure modes
        section["failure_modes"] = classify_failure_modes(section["body_text"])
        section["failure_mode"] = section["failure_modes"][0] if section["failure_modes"] else None
        
        # Components
        section["components"] = classify_components(section["body_text"])
        section["component"] = section["components"][0] if section["components"] else None
        
        # Metadata
        section["contains_images"] = False  # Will be enhanced later
        section["image_descriptions"] = []
        section["contains_table"] = "|" in section["body_text"] and "---" in section["body_text"]
        section["is_case_study"] = section["content_type"] == "voorbeeldcase"
        section["case_title"] = section["title"] if section["is_case_study"] else None
        section["difficulty_level"] = "beginner"  # Default
        section["related_diagram_ids"] = []  # Will be linked later
        
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(sections)} sections...")
    
    # Save output
    output_path = "features/manuals_vsm/output/manual_sections_classified.jsonl"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        for section in sections:
            f.write(json.dumps(section, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(sections)} sections to {output_path}")
    
    # Statistics
    print("\n=== Statistics ===")
    print(f"Total sections: {len(sections)}")
    print(f"By manual:")
    for config in manual_configs:
        count = sum(1 for s in sections if s["manual_id"] == config["manual_id"])
        print(f"  {config['manual_id']}: {count}")
    
    print(f"\nContent types:")
    content_types = {}
    for s in sections:
        ct = s["content_type"]
        content_types[ct] = content_types.get(ct, 0) + 1
    for ct, count in sorted(content_types.items(), key=lambda x: -x[1]):
        print(f"  {ct}: {count}")
    
    print(f"\nSMIDO steps (top 10):")
    smido_counts = {}
    for s in sections:
        for step in s["smido_steps"]:
            smido_counts[step] = smido_counts.get(step, 0) + 1
    for step, count in sorted(smido_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {step}: {count}")
    
    print(f"\nFailure modes (top 10):")
    failure_counts = {}
    for s in sections:
        for mode in s["failure_modes"]:
            failure_counts[mode] = failure_counts.get(mode, 0) + 1
    for mode, count in sorted(failure_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {mode}: {count}")


if __name__ == "__main__":
    main()

