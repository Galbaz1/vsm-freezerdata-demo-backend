#!/usr/bin/env python3
"""
Copy manual images from extraction output to static directory for FastAPI serving.

This makes images accessible via HTTP at /static/manual_images/{manual}/{filename}.png
"""
import shutil
from pathlib import Path

def main():
    print("=" * 80)
    print("Copying Manual Images to Static Directory")
    print("=" * 80)
    
    source_base = Path("features/extraction/production_output")
    target_base = Path("elysia/api/static/manual_images")
    
    # Create target directory
    target_base.mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Created target directory: {target_base}")
    
    # Manual mappings (source dir → target dir)
    manuals = {
        "storingzoeken-koeltechniek_theorie_179": "storingzoeken",
        "koelinstallaties-opbouw-en-werking_theorie_2016": "opbouw-werking",
        "koelinstallaties-inspectie-en-onderhoud_theorie_168": "inspectie-onderhoud"
    }
    
    total_copied = 0
    
    for source_name, target_name in manuals.items():
        print(f"\n{source_name}:")
        print("-" * 80)
        
        # Find all PNG files in this manual's assets
        source_dir = source_base / source_name / source_name / "assets"
        
        if not source_dir.exists():
            print(f"  ⚠️  Source directory not found: {source_dir}")
            continue
        
        # Find all PNGs
        png_files = list(source_dir.glob("**/*.png"))
        print(f"  Found {len(png_files)} PNG files")
        
        # Create target subdirectory
        target_dir = target_base / target_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy each file
        for png_file in png_files:
            # Use chunk_id as filename (from filename, not path)
            filename = png_file.name
            target_file = target_dir / filename
            
            shutil.copy2(png_file, target_file)
            total_copied += 1
            
            if total_copied % 50 == 0:
                print(f"  Copied {total_copied} images...")
        
        print(f"  ✅ Copied {len(png_files)} images to {target_dir}")
    
    print("\n" + "=" * 80)
    print(f"✅ Total images copied: {total_copied}")
    print("=" * 80)
    print("\nImages accessible at:")
    print("  http://localhost:8000/static/manual_images/storingzoeken/{filename}.png")
    print("  http://localhost:8000/static/manual_images/opbouw-werking/{filename}.png")
    print("  http://localhost:8000/static/manual_images/inspectie-onderhoud/{filename}.png")

if __name__ == "__main__":
    main()

