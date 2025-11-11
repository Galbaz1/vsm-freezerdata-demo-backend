"""
Script to analyze parsed manual files and document their structure
"""
import json
from pathlib import Path
from collections import Counter
import sys

def analyze_manual_files():
    """Analyze all manual files and their structure"""

    base_path = Path(__file__).parent.parent / "features" / "extraction" / "production_output"

    manuals = [
        "storingzoeken-koeltechniek_theorie_179",
        "koelinstallaties-inspectie-en-onderhoud_theorie_168",
        "koelinstallaties-opbouw-en-werking_theorie_2016"
    ]

    results = {}

    for manual_name in manuals:
        manual_path = base_path / manual_name
        print(f"\n{'='*80}")
        print(f"Analyzing: {manual_name}")
        print('='*80)

        # Read meta file
        meta_file = manual_path / f"{manual_name}.meta.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f"\nMeta info:")
            print(f"  Title: {meta.get('title')}")
            print(f"  Pages: {meta.get('page_count')}")
            print(f"  Version: {meta.get('version')}")
            print(f"  Languages: {meta.get('languages')}")

        # Read parsed file
        parsed_file = manual_path / f"{manual_name}.parsed.json"
        if parsed_file.exists():
            print(f"\nReading parsed file: {parsed_file.name}")
            with open(parsed_file, 'r', encoding='utf-8') as f:
                parsed = json.load(f)

            print(f"\nParsed JSON structure:")
            print(f"  Type: {type(parsed)}")

            if isinstance(parsed, dict):
                print(f"  Top-level keys: {list(parsed.keys())}")
                for key in list(parsed.keys())[:5]:  # First 5 keys
                    val = parsed[key]
                    print(f"    '{key}': {type(val)} - {len(val) if isinstance(val, (list, dict, str)) else val}")

            elif isinstance(parsed, list):
                print(f"  List length: {len(parsed)}")
                if len(parsed) > 0:
                    print(f"  First element type: {type(parsed[0])}")
                    if isinstance(parsed[0], dict):
                        print(f"  First element keys: {list(parsed[0].keys())}")
                        # Sample first element
                        print(f"\n  Sample first element:")
                        for key, val in list(parsed[0].items())[:10]:
                            if isinstance(val, str):
                                print(f"    {key}: {val[:100]}...")
                            else:
                                print(f"    {key}: {type(val)} - {val if not isinstance(val, (list, dict)) else f'len={len(val)}'}")

        # Read text_chunks file
        text_chunks_file = manual_path / f"{manual_name}.text_chunks.jsonl"
        if text_chunks_file.exists():
            with open(text_chunks_file, 'r', encoding='utf-8') as f:
                chunks = [json.loads(line) for line in f]
            print(f"\n\nText chunks:")
            print(f"  Count: {len(chunks)}")
            if len(chunks) > 0:
                print(f"  Sample chunk keys: {list(chunks[0].keys())}")
                print(f"  Sample chunk:")
                for key, val in list(chunks[0].items())[:8]:
                    if isinstance(val, str) and len(val) > 100:
                        print(f"    {key}: {val[:100]}...")
                    elif isinstance(val, (list, dict)):
                        print(f"    {key}: {type(val).__name__} (len={len(val)})")
                    else:
                        print(f"    {key}: {val}")

        # Read visual_chunks file
        visual_chunks_file = manual_path / f"{manual_name}.visual_chunks.jsonl"
        if visual_chunks_file.exists():
            with open(visual_chunks_file, 'r', encoding='utf-8') as f:
                visual_chunks = [json.loads(line) for line in f]
            print(f"\n\nVisual chunks:")
            print(f"  Count: {len(visual_chunks)}")
            if len(visual_chunks) > 0:
                print(f"  Sample visual chunk keys: {list(visual_chunks[0].keys())}")

        # Check for parsed.md
        md_file = manual_path / f"{manual_name}.parsed.md"
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            print(f"\n\nMarkdown version:")
            print(f"  Size: {len(md_content)} characters")
            print(f"  Lines: {len(md_content.splitlines())}")
            print(f"\n  First 500 chars:")
            print(md_content[:500])

        results[manual_name] = {
            "meta": meta if meta_file.exists() else None,
            "has_parsed_json": parsed_file.exists(),
            "has_text_chunks": text_chunks_file.exists(),
            "has_visual_chunks": visual_chunks_file.exists(),
            "has_markdown": md_file.exists(),
            "text_chunk_count": len(chunks) if text_chunks_file.exists() else 0,
            "visual_chunk_count": len(visual_chunks) if visual_chunks_file.exists() else 0
        }

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    for name, info in results.items():
        print(f"\n{name}:")
        print(f"  Pages: {info['meta']['page_count'] if info['meta'] else 'N/A'}")
        print(f"  Text chunks: {info['text_chunk_count']}")
        print(f"  Visual chunks: {info['visual_chunk_count']}")
        print(f"  Has markdown: {info['has_markdown']}")

    return results

if __name__ == "__main__":
    analyze_manual_files()
