#!/usr/bin/env python3
"""
Enrich vlog metadata with SMIDO classification and standardized failure modes.
Creates VSM_VlogClip and VSM_VlogCase collections data.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

# Controlled vocabularies
SMIDO_STEPS = [
    "melding", "technisch", "installatie_vertrouwd",
    "power", "procesinstellingen", "procesparameters", "productinput",
    "ketens_onderdelen"
]

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
    "expansieventiel_defect", "koelproces_uit_balans"
]


def classify_smido_steps_vlog(problem: str, root_cause: str, solution: str, tags: List[str]) -> List[str]:
    """Classify SMIDO steps based on vlog content (pattern-based)"""
    text = f"{problem} {root_cause} {solution} {' '.join(tags)}".lower()
    steps = []
    
    # Melding - always if problem is mentioned
    if problem:
        steps.append("melding")
    
    # Technisch - visual inspection, physical checks
    if any(word in text for word in ["visuele", "inspectie", "waarneembaar", "fysiek", "controleren"]):
        steps.append("technisch")
    
    # Installatie vertrouwd - schemas, components knowledge
    if any(word in text for word in ["schema", "documentatie", "installatie", "systeem"]):
        steps.append("installatie_vertrouwd")
    
    # P1 - Power
    if any(word in text for word in ["voeding", "spanning", "elektrisch", "bedrading", "schakelkast"]):
        steps.append("power")
    
    # P2 - Procesinstellingen
    if any(word in text for word in ["instelling", "parameter", "pressostaat", "thermostaat", "regelaar", "setpoint"]):
        steps.append("procesinstellingen")
    
    # P3 - Procesparameters
    if any(word in text for word in ["meting", "temperatuur", "druk", "oververhitting", "onderkoeling"]):
        steps.append("procesparameters")
    
    # P4 - Productinput
    if any(word in text for word in ["belading", "omgeving", "deur", "luchtstroom", "condities"]):
        steps.append("productinput")
    
    # O - Onderdelen
    if any(word in text for word in ["vervangen", "repareren", "component", "onderdeel", "demonteer"]):
        steps.append("ketens_onderdelen")
    
    return list(set(steps)) if steps else ["algemeen"]


def standardize_failure_modes(tags: List[str], problem: str, root_cause: str) -> List[str]:
    """Map vlog tags to controlled failure mode vocabulary"""
    text = f"{' '.join(tags)} {problem} {root_cause}".lower()
    modes = []
    
    # Map patterns to controlled vocabulary
    patterns = {
        "te_hoge_temperatuur": ["te hoog", "te warm", "temperatuur"],
        "ingevroren_verdamper": ["ijsvorming", "bevroren", "ingevroren"],
        "slecht_ontdooien": ["ontdooi", "defrost"],
        "ventilator_defect": ["ventilator", "condensorventilator"],
        "regelaar_probleem": ["regelaar", "parameter", "instelling"],
        "expansieventiel_defect": ["expansieventiel", "verstopping"],
        "verstopt_filter": ["filterdroger", "verstopping", "vervuiling"],
        "vuile_condensor": ["vervuiling condensor", "vuile condensor"],
        "deur_probleem": ["deur"],
        "hoge_druk": ["hoge druk", "persdruk"],
        "lage_druk": ["lage druk", "zuigdruk"],
        "te_weinig_koudemiddel": ["koudemiddeltekort", "geen stroming"],
        "lekkage": ["lek"],
        "compressor_kortsluiting": ["kortsluiting"],
        "sensor_defect": ["sensor"],
        "koelproces_uit_balans": ["uit balans", "balans"]
    }
    
    for mode, keywords in patterns.items():
        if any(kw in text for kw in keywords):
            modes.append(mode)
    
    return list(set(modes)) if modes else ["algemeen"]


def generate_worldstate_pattern(problem: str, root_cause: str, tags: List[str]) -> str:
    """Generate WorldState pattern description from vlog content"""
    # Extract key sensor indicators from problem and root cause
    text = f"{problem} {root_cause}".lower()
    
    patterns = []
    
    if "te hoog" in text or "te warm" in text:
        patterns.append("Room temp >-18°C (too warm)")
    if "bevroren" in text or "ijs" in text:
        patterns.append("evaporator frozen")
    if "ventilator" in text and "niet" in text:
        patterns.append("fans not running")
    if "condensor" in text and ("heet" in text or "warm" in text):
        patterns.append("condenser hot")
    if "geen stroming" in text:
        patterns.append("no refrigerant flow")
    if "druk" in text:
        patterns.append("abnormal pressures")
    
    return ", ".join(patterns) if patterns else "System out of balance"


def main():
    # Load existing annotations
    input_file = "features/vlogs_vsm/output/vlogs_vsm_annotations.jsonl"
    with open(input_file, "r") as f:
        records = [json.loads(line) for line in f if line.strip()]
    
    print(f"Loaded {len(records)} vlog records")
    
    # Separate clips and cases
    clips = [r for r in records if r.get("record_kind") == "clip"]
    cases = [r for r in records if r.get("record_kind") == "case_set"]
    
    print(f"  {len(clips)} clips")
    print(f"  {len(cases)} case sets")
    
    # Enrich clips
    enriched_clips = []
    for clip in clips:
        payload = clip.get("payload", {})
        
        enriched = {
            "clip_id": f"{clip['set_id']}_{clip['clip_index']}",
            "case_id": clip["set_id"],
            "clip_number": clip["clip_index"],
            "video_filename": clip["video_filename"],
            "video_path": clip["video_local_path"],
            "duration_seconds": sum(step.get("end_time_s", 0) - step.get("start_time_s", 0) 
                                   for step in payload.get("steps", [])),
            
            # Content
            "title": f"{clip['set_id']}_{clip['clip_index']}: {payload.get('problem_summary', '')[:50]}...",
            "language": payload.get("language", "nl"),
            "problem_summary": payload.get("problem_summary", ""),
            "root_cause": payload.get("root_cause", ""),
            "solution_summary": payload.get("solution_summary", ""),
            "steps_text": " | ".join([s.get("description", "") for s in payload.get("steps", [])]),
            
            # Classification (pattern-based)
            "smido_steps": classify_smido_steps_vlog(
                payload.get("problem_summary", ""),
                payload.get("root_cause", ""),
                payload.get("solution_summary", ""),
                payload.get("tags", [])
            ),
            "failure_modes": standardize_failure_modes(
                payload.get("tags", []),
                payload.get("problem_summary", ""),
                payload.get("root_cause", "")
            ),
            "components": payload.get("technical_components", []),
            
            # Sensor correlation
            "world_state_pattern": generate_worldstate_pattern(
                payload.get("problem_summary", ""),
                payload.get("root_cause", ""),
                payload.get("tags", [])
            ),
            
            # Tags
            "tags": payload.get("tags", []),
            "skill_level": "beginner",
            "is_complete_case": False,
            
            # Set primary fields
            "smido_step_primary": "",
            "failure_mode": "",
            "component_primary": ""
        }
        
        # Set primary fields
        enriched["smido_step_primary"] = enriched["smido_steps"][0] if enriched["smido_steps"] else "algemeen"
        enriched["failure_mode"] = enriched["failure_modes"][0] if enriched["failure_modes"] else None
        enriched["component_primary"] = enriched["components"][0] if enriched["components"] else None
        
        enriched_clips.append(enriched)
    
    # Enrich cases
    enriched_cases = []
    for case in cases:
        payload = case.get("payload", {})
        case_clips = [c for c in enriched_clips if c["case_id"] == case["set_id"]]
        
        # Aggregate SMIDO steps and failure modes from clips
        all_smido = list(set(step for clip in case_clips for step in clip["smido_steps"]))
        all_failures = list(set(mode for clip in case_clips for mode in clip["failure_modes"] if mode))
        all_components = list(set(comp for clip in case_clips for comp in clip["components"]))
        
        enriched = {
            "case_id": case["set_id"],
            "case_title": f"Case {case['set_id']}: {payload.get('problem_summary', '')[:60]}...",
            "clip_ids": [f"{case['set_id']}_{i}" for i in range(1, len(case.get("clip_filenames", [])) + 1)],
            
            # Content
            "problem_summary": payload.get("problem_summary", ""),
            "root_cause": payload.get("root_cause", ""),
            "solution_summary": payload.get("solution_summary", ""),
            "transcript_nl": payload.get("transcript", ""),
            
            # Classification
            "smido_steps": all_smido,
            "smido_step_primary": all_smido[0] if all_smido else "algemeen",
            "failure_modes": all_failures,
            "failure_mode": all_failures[0] if all_failures else None,
            "components": all_components,
            "component_primary": all_components[0] if all_components else None,
            
            # Sensor correlation
            "world_state_pattern": generate_worldstate_pattern(
                payload.get("problem_summary", ""),
                payload.get("root_cause", ""),
                payload.get("tags", [])
            ),
            "typical_sensor_conditions": json.dumps({
                "description": "Pattern inferred from problem and solution"
            }),
            
            # Cross-references (will be linked later)
            "related_manual_sections": [],
            "related_telemetry_events": [],
            "related_diagrams": []
        }
        
        enriched_cases.append(enriched)
    
    # Save enriched data
    clips_output = "features/vlogs_vsm/output/vlog_clips_enriched.jsonl"
    cases_output = "features/vlogs_vsm/output/vlog_cases_enriched.jsonl"
    
    with open(clips_output, "w") as f:
        for clip in enriched_clips:
            f.write(json.dumps(clip, ensure_ascii=False) + "\n")
    
    with open(cases_output, "w") as f:
        for case in enriched_cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    
    print(f"\n=== Output ===")
    print(f"Saved {len(enriched_clips)} clips to {clips_output}")
    print(f"Saved {len(enriched_cases)} cases to {cases_output}")
    
    # Statistics
    print(f"\n=== Statistics ===")
    print(f"Clips by case:")
    for case_id in ["A1", "A2", "A3", "A4", "A5"]:
        count = sum(1 for c in enriched_clips if c["case_id"] == case_id)
        print(f"  {case_id}: {count} clips")
    
    print(f"\nSMIDO steps coverage (cases):")
    smido_counts = {}
    for case in enriched_cases:
        for step in case["smido_steps"]:
            smido_counts[step] = smido_counts.get(step, 0) + 1
    for step, count in sorted(smido_counts.items(), key=lambda x: -x[1]):
        print(f"  {step}: {count}")
    
    print(f"\nFailure modes (cases):")
    failure_counts = {}
    for case in enriched_cases:
        for mode in case["failure_modes"]:
            failure_counts[mode] = failure_counts.get(mode, 0) + 1
    for mode, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
        print(f"  {mode}: {count}")


if __name__ == "__main__":
    main()

