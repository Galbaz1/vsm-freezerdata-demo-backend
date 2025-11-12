#!/usr/bin/env python3
"""
Generate PNG files from user-facing Mermaid diagrams using Mermaid CLI.

Usage:
    python3 generate_pngs.py

Output:
    PNG files in features/diagrams_vsm/output/pngs/
"""

import json
import subprocess
import sys
from pathlib import Path

# Get script directory
SCRIPT_DIR = Path(__file__).parent
DIAGRAMS_DIR = SCRIPT_DIR.parent
MAPPING_FILE = SCRIPT_DIR / "diagram_mapping.json"
OUTPUT_DIR = DIAGRAMS_DIR / "output" / "pngs"

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

def generate_png(mermaid_file: Path, output_png: Path, diagram_id: str):
    """
    Generate PNG from Mermaid file using mmdc CLI.
    
    Args:
        mermaid_file: Path to input .mermaid file
        output_png: Path to output .png file
        diagram_id: Diagram ID for error messages
    """
    if not mermaid_file.exists():
        print(f"ERROR: Mermaid file not found: {mermaid_file}")
        return False
    
    # Mermaid CLI command
    # -i: input file
    # -o: output file
    # -w: width in pixels (1200px)
    # -b: background color (white)
    # -t: theme (default)
    cmd = [
        "mmdc",
        "-i", str(mermaid_file),
        "-o", str(output_png),
        "-w", "1200",
        "-b", "white",
        "-t", "default"
    ]
    
    try:
        print(f"Generating PNG for {diagram_id}...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✓ Created: {output_png}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error generating PNG for {diagram_id}:")
        print(f"    {e.stderr}")
        return False
    except FileNotFoundError:
        print("ERROR: Mermaid CLI (mmdc) not found!")
        print("Install with: npm install -g @mermaid-js/mermaid-cli")
        return False

def main():
    """Main function to generate all PNGs."""
    print("=" * 60)
    print("Mermaid to PNG Generator")
    print("=" * 60)
    
    # Load mapping file
    if not MAPPING_FILE.exists():
        print(f"ERROR: Mapping file not found: {MAPPING_FILE}")
        sys.exit(1)
    
    with open(MAPPING_FILE, "r") as f:
        mappings = json.load(f)
    
    print(f"Loaded {len(mappings)} diagram mappings")
    
    # Ensure output directory exists
    ensure_output_dir()
    
    # Generate PNGs
    success_count = 0
    failed = []
    
    for diagram_id, mapping in mappings.items():
        user_facing_path = DIAGRAMS_DIR / mapping["user_facing"]
        output_png = DIAGRAMS_DIR / mapping["png_path"]
        
        if generate_png(user_facing_path, output_png, diagram_id):
            success_count += 1
        else:
            failed.append(diagram_id)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Summary: {success_count}/{len(mappings)} PNGs generated successfully")
    
    if failed:
        print(f"Failed diagrams: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("All PNGs generated successfully!")
        print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

