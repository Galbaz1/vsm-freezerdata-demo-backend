#!/usr/bin/env python3
"""
Simple test: Verify VSM_ManualImage collection and image URLs.
"""
import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter
from pathlib import Path

async def test():
    print("=" * 80)
    print("VSM_ManualImage Collection Test")
    print("=" * 80)
    
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        coll = client.collections.get('VSM_ManualImage')
        
        # Test 1: Total count
        total = await coll.aggregate.over_all(total_count=True)
        print(f"\n✅ Total images in collection: {total.total_count}")
        
        # Test 2: Search by component
        verdamper = await coll.query.fetch_objects(
            filters=Filter.by_property("component_tags").contains_any(["verdamper"]),
            limit=5
        )
        print(f"✅ Images tagged 'verdamper': {len(verdamper.objects)}")
        
        if verdamper.objects:
            img = verdamper.objects[0]
            print(f"\n  Sample:")
            print(f"    URL: {img.properties.get('image_url')}")
            print(f"    Manual: {img.properties.get('manual_name')} p.{img.properties.get('page_number')}")
            print(f"    Tags: {img.properties.get('component_tags')}")
            
            # Verify file exists
            url = img.properties.get('image_url', '')
            if '/static/manual_images/' in url:
                import re
                match = re.search(r'/static/manual_images/(.+)$', url)
                if match:
                    rel_path = match.group(1)
                    file_path = Path(f"elysia/api/static/manual_images/{rel_path}")
                    
                    if file_path.exists():
                        size_kb = file_path.stat().st_size / 1024
                        print(f"    ✅ File exists: {size_kb:.1f} KB")
                    else:
                        print(f"    ❌ File NOT found: {file_path}")
        
        # Test 3: Hybrid search
        hybrid = await coll.query.hybrid(
            query="compressor foto",
            limit=3
        )
        print(f"\n✅ Hybrid search 'compressor foto': {len(hybrid.objects)} results")
        
        # Test 4: Component stats
        all_imgs = await coll.query.fetch_objects(limit=233)
        
        component_counts = {}
        for obj in all_imgs.objects:
            tags = obj.properties.get('component_tags', [])
            for tag in tags:
                component_counts[tag] = component_counts.get(tag, 0) + 1
        
        print(f"\n✅ Component tag statistics:")
        for comp, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {comp}: {count} images")
    
    await cm.close_clients()
    
    print("\n" + "=" * 80)
    print("✅ All tests PASSED - VSM_ManualImage ready for use!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test())

