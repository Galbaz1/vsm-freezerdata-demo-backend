#!/usr/bin/env python3
"""
Upload enriched manual images to Weaviate VSM_ManualImage collection.

Creates collection schema and uploads 233 image metadata objects with URLs.
"""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

weaviate_url = os.environ.get("WEAVIATE_URL") or os.environ.get("WCD_URL")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY") or os.environ.get("WCD_API_KEY")

if not weaviate_url or not weaviate_api_key:
    print("❌ Error: WEAVIATE_URL/WCD_URL and WEAVIATE_API_KEY/WCD_API_KEY must be set in .env")
    exit(1)

def main():
    print("=" * 80)
    print("Uploading Manual Images to Weaviate")
    print("=" * 80)
    
    # Connect to Weaviate
    print("\nConnecting to Weaviate...")
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key)
    )
    print(f"✅ Weaviate client ready: {client.is_ready()}")
    
    try:
        # Step 1: Create collection if not exists
        print("\n" + "=" * 80)
        print("STEP 1: Creating Collection Schema")
        print("=" * 80)
        
        collection_name = "VSM_ManualImage"
        
        # Delete if exists (for fresh upload)
        if client.collections.exists(collection_name):
            print(f"  Collection '{collection_name}' already exists. Deleting...")
            client.collections.delete(collection_name)
        
        # Create collection with schema
        print(f"  Creating collection '{collection_name}'...")
        client.collections.create(
            name=collection_name,
            description="Manual images from cooling installation manuals with visual troubleshooting support",
            vectorizer_config=Configure.Vectorizer.text2vec_weaviate(
                vectorize_collection_name=False
            ),
            properties=[
                Property(name="image_id", data_type=DataType.TEXT,
                        description="Unique chunk ID from extraction"),
                Property(name="image_url", data_type=DataType.TEXT,
                        description="HTTP URL to access image via FastAPI static files",
                        skip_vectorization=True),
                Property(name="image_description", data_type=DataType.TEXT,
                        description="Vision model description of what the image shows",
                        vectorize_property_name=False),
                Property(name="manual_name", data_type=DataType.TEXT,
                        description="Short manual name (storingzoeken, opbouw-werking, inspectie-onderhoud)",
                        skip_vectorization=True),
                Property(name="page_number", data_type=DataType.INT,
                        description="Original page number in manual (1-indexed)"),
                Property(name="chunk_type", data_type=DataType.TEXT,
                        description="Type of visual (figure, diagram, photo, etc.)",
                        skip_vectorization=True),
                Property(name="component_tags", data_type=DataType.TEXT_ARRAY,
                        description="Component keywords (verdamper, compressor, pressostaat, etc.)",
                        skip_vectorization=True),
                Property(name="smido_tags", data_type=DataType.TEXT_ARRAY,
                        description="SMIDO phase relevance (M, T, I, P1, P2, P3, P4, O)",
                        skip_vectorization=True),
            ]
        )
        print(f"  ✅ Collection created successfully")
        
        # Step 2: Load enriched metadata
        print("\n" + "=" * 80)
        print("STEP 2: Loading Enriched Metadata")
        print("=" * 80)
        
        metadata_file = Path("features/manuals_vsm/output/manual_images_enriched.jsonl")
        
        with open(metadata_file) as f:
            images = [json.loads(line) for line in f if line.strip()]
        
        print(f"  Loaded {len(images)} image records")
        
        # Step 3: Batch upload
        print("\n" + "=" * 80)
        print("STEP 3: Uploading Images to Weaviate")
        print("=" * 80)
        
        collection = client.collections.get(collection_name)
        
        # Use dynamic batching for automatic optimization
        with collection.batch.dynamic() as batch:
            for i, img in enumerate(images, 1):
                # Build image URL with chunk- prefix (how files are actually named)
                filename = f"chunk-{img['chunk_id']}.png"
                image_url = f"http://localhost:8000/static/manual_images/{img['manual_name']}/{filename}"
                
                batch.add_object({
                    "image_id": img["chunk_id"],
                    "image_url": image_url,
                    "image_description": img["image_description"],
                    "manual_name": img["manual_name"],
                    "page_number": img["page_number"],
                    "chunk_type": img["chunk_type"],
                    "component_tags": img["component_tags"],
                    "smido_tags": img["smido_tags"],
                })
                
                if i % 50 == 0:
                    print(f"  Uploaded {i}/{len(images)}...")
        
        # Check for errors
        failed = collection.batch.failed_objects
        if failed:
            print(f"\n❌ Failed: {len(failed)} objects")
            print(f"   First error: {failed[0]}")
        else:
            print(f"\n✅ All {len(images)} images uploaded successfully!")
        
        # Step 4: Verification
        print("\n" + "=" * 80)
        print("STEP 4: Verification")
        print("=" * 80)
        
        total = collection.aggregate.over_all(total_count=True).total_count
        print(f"  Total objects in {collection_name}: {total}")
        
        # Test queries
        print("\n  Testing queries:")
        
        # Query 1: Find verdamper images
        from weaviate.classes.query import Filter
        
        verdamper_results = collection.query.fetch_objects(
            filters=Filter.by_property("component_tags").contains_any(["verdamper"]),
            limit=3
        )
        print(f"    Images with 'verdamper' tag: {len(verdamper_results.objects)}")
        if verdamper_results.objects:
            print(f"      Sample: {verdamper_results.objects[0].properties['image_description'][:60]}...")
        
        # Query 2: Hybrid search
        search_results = collection.query.hybrid(
            query="compressor foto",
            limit=3
        )
        print(f"    Hybrid search 'compressor foto': {len(search_results.objects)} results")
        
        print("\n✅ Weaviate upload complete!")
        print("\nNext steps:")
        print("  1. Create search_manual_images tool")
        print("  2. Preprocess collection for Dutch prompts")
        print("  3. Test image search in frontend")
    
    finally:
        client.close()

if __name__ == "__main__":
    main()

