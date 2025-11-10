import argparse
import os
import json
from pathlib import Path

import pandas as pd
import weaviate
from dotenv import load_dotenv
from weaviate.classes.config import Configure, Property, DataType, Tokenization
from weaviate.classes.init import Auth


def connect_client() -> weaviate.WeaviateClient:
    """
    Connect to Weaviate Cloud using env vars.
    Honors optional EMBEDDINGS_PROVIDER_API_KEY for provider headers (OpenAI by default).
    """
    load_dotenv()
    weaviate_url = os.environ["WEAVIATE_URL"]
    if not weaviate_url.startswith("http://") and not weaviate_url.startswith("https://"):
        weaviate_url = f"https://{weaviate_url}"
    weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
    provider_key = os.environ.get("EMBEDDINGS_PROVIDER_API_KEY", "")

    headers = {}
    if provider_key:
        # Default to OpenAI header; adjust here if using another provider.
        headers["X-OpenAI-Api-Key"] = provider_key

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
        headers=headers if headers else None,
    )
    print(f"Weaviate client ready: {client.is_ready()}")
    return client


def ensure_fd_telemetry(client: weaviate.WeaviateClient, drop: bool) -> weaviate.collections.Collection:
    """
    Create FD_Telemetry with no vectors (numeric time-series).
    Drops existing collection when drop=True.
    """
    name = "FD_Telemetry"
    if client.collections.exists(name):
        if drop:
            print("Dropping existing FD_Telemetry ...")
            client.collections.delete(name)
        else:
            print("FD_Telemetry exists; using existing collection.")
            return client.collections.get(name)

    print("Creating FD_Telemetry (no vectors) ...")
    return client.collections.create(
        name=name,
        vectorizer_config=Configure.Vectorizer.none(),
        properties=[
            Property(name="asset_id", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="timestamp", data_type=DataType.DATE),
            Property(name="main_temp", data_type=DataType.NUMBER),
            Property(name="secondary_temp", data_type=DataType.NUMBER),
            Property(name="hot_gas_temp", data_type=DataType.NUMBER),
            Property(name="liquid_temp", data_type=DataType.NUMBER),
            Property(name="suction_temp", data_type=DataType.NUMBER),
            Property(name="ambient_temp", data_type=DataType.NUMBER),
            Property(name="door_open", data_type=DataType.BOOL),
            Property(name="signal_strength", data_type=DataType.NUMBER),
            Property(name="battery_level", data_type=DataType.NUMBER),
        ],
    )


def ensure_fd_documents(client: weaviate.WeaviateClient, drop: bool) -> weaviate.collections.Collection | None:
    """
    Create FD_Documents with text vectorization (OpenAI by default here).
    Drops existing collection when drop=True. Returns None if no docs found.
    """
    production_dir = Path("features/extraction/production_output")
    # We'll import from text_chunks.jsonl, visual_chunks.jsonl and pages.jsonl
    text_files = sorted(production_dir.glob("*/*.text_chunks.jsonl"))
    visual_files = sorted(production_dir.glob("*/*.visual_chunks.jsonl"))
    page_files = sorted(production_dir.glob("*/*.pages.jsonl"))

    if not (text_files or visual_files or page_files):
        print("No processed manuals found in features/extraction/production_output; skipping FD_Documents.")
        return None

    name = "FD_Documents"
    if client.collections.exists(name):
        if drop:
            print("Dropping existing FD_Documents ...")
            client.collections.delete(name)
        else:
            print("FD_Documents exists; dropping is recommended to update schema. Use --drop-docs.")
            return client.collections.get(name)

    print("Creating FD_Documents (vectorized text) ...")
    collection = client.collections.create(
        name=name,
        vector_config=[
            # Keep OpenAI vectorizer to match current .env. Switch to text2vec_weaviate if you prefer in-cluster embeddings.
            Configure.Vectors.text2vec_openai(
                name="default",
                source_properties=["content"],
                model="text-embedding-3-large",
            )
        ],
        properties=[
            Property(name="doc_id", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="section_title", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="chunk_type", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="page", data_type=DataType.NUMBER),
            Property(name="language", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="source_path", data_type=DataType.TEXT),
            Property(name="asset_path", data_type=DataType.TEXT),  # for visual chunks
        ],
    )
    return collection


def iter_text_chunks(root: Path):
    for chunk_path in sorted(root.glob("*/*.text_chunks.jsonl")):
        doc_id = chunk_path.parent.name
        title = doc_id.replace("_", " ").title()
        with open(chunk_path, "r") as infile:
            for line in infile:
                chunk = json.loads(line)
                content = (chunk.get("text_summary") or chunk.get("markdown") or "").strip()
                yield {
                    "doc_id": doc_id,
                    "title": title,
                    "section_title": chunk.get("chunk_type") or "section",
                    "content": content,
                    "chunk_type": chunk.get("chunk_type") or "text",
                    "page": chunk.get("page", 0),
                    "language": chunk.get("language") or "nl",
                    "source_path": str(chunk_path),
                    "asset_path": None,
                }


def iter_visual_chunks(root: Path):
    for chunk_path in sorted(root.glob("*/*.visual_chunks.jsonl")):
        doc_id = chunk_path.parent.name
        title = doc_id.replace("_", " ").title()
        with open(chunk_path, "r") as infile:
            for line in infile:
                chunk = json.loads(line)
                content = (chunk.get("text_summary") or chunk.get("markdown") or "").strip()
                yield {
                    "doc_id": doc_id,
                    "title": title,
                    "section_title": "figure",
                    "content": content,
                    "chunk_type": "figure",
                    "page": chunk.get("page", 0),
                    "language": chunk.get("language") or "nl",
                    "source_path": str(chunk_path),
                    "asset_path": chunk.get("asset_path"),
                }


def iter_page_chunks(root: Path):
    for chunk_path in sorted(root.glob("*/*.pages.jsonl")):
        doc_id = chunk_path.parent.name
        title = doc_id.replace("_", " ").title()
        with open(chunk_path, "r") as infile:
            for line in infile:
                chunk = json.loads(line)
                content = (chunk.get("page_summary") or chunk.get("page_text") or "").strip()
                yield {
                    "doc_id": doc_id,
                    "title": title,
                    "section_title": "page",
                    "content": content,
                    "chunk_type": "page",
                    "page": chunk.get("pdf_page_index", 0),
                    "language": (chunk.get("languages") or ["nl"])[0],
                    "source_path": str(chunk_path),
                    "asset_path": None,
                }


def load_telemetry_dataframe(parquet_path: Path, asset_id: str, start: str | None, end: str | None) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path).reset_index()
    df = df.rename(
        columns={
            "timestamp": "timestamp",
            "sGekoeldeRuimte": "main_temp",
            "p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive": "secondary_temp",
            "sHeetgasLeiding": "hot_gas_temp",
            "sVloeistofleiding": "liquid_temp",
            "sZuigleiding": "suction_temp",
            "sOmgeving": "ambient_temp",
            "sDeurcontact": "door_open",
            "sRSSI": "signal_strength",
            "sBattery": "battery_level",
        }
    )
    df["asset_id"] = asset_id
    ts = pd.to_datetime(df["timestamp"], utc=True)
    if start:
        ts_start = pd.to_datetime(start, utc=True)
        df = df.loc[ts >= ts_start]
        ts = pd.to_datetime(df["timestamp"], utc=True)  # recompute
    if end:
        ts_end = pd.to_datetime(end, utc=True)
        df = df.loc[ts <= ts_end]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df["door_open"] = df["door_open"].fillna(0).astype(int).astype(bool)
    df = df.where(pd.notnull(df), None)
    return df


def main():
    parser = argparse.ArgumentParser(description="Import freezer telemetry and manuals into Weaviate.")
    parser.add_argument("--parquet", type=Path, default=Path("features/telemetry/timeseries_freezerdata/135_1570_cleaned.parquet"))
    parser.add_argument("--asset-id", type=str, default="FZ-123")
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--drop-telemetry", action="store_true", help="Drop FD_Telemetry before create.")
    parser.add_argument("--drop-docs", action="store_true", help="Drop FD_Documents before create.")
    parser.add_argument("--no-docs", action="store_true", help="Skip documents import.")
    parser.add_argument("--start", type=str, default=None, help="Start timestamp (e.g., 2024-03-01)")
    parser.add_argument("--end", type=str, default=None, help="End timestamp (e.g., 2024-04-01)")
    args = parser.parse_args()

    client = connect_client()
    try:
        # Ensure telemetry collection (no vectors)
        telemetry_collection = ensure_fd_telemetry(client, drop=args.drop_telemetry)

        # Telemetry import
        print("Loading telemetry dataframe ...")
        telemetry_df = load_telemetry_dataframe(args.parquet, args.asset_id, args.start, args.end)
        telemetry_records = telemetry_df.to_dict(orient="records")
        print(f"Importing telemetry rows: {len(telemetry_records)}")
        with telemetry_collection.batch.fixed_size(batch_size=args.batch_size) as batch:
            for i, item in enumerate(telemetry_records, start=1):
                batch.add_object(
                    {
                        "asset_id": item["asset_id"],
                        "timestamp": item["timestamp"],
                        "main_temp": item["main_temp"],
                        "secondary_temp": item["secondary_temp"],
                        "hot_gas_temp": item["hot_gas_temp"],
                        "liquid_temp": item["liquid_temp"],
                        "suction_temp": item["suction_temp"],
                        "ambient_temp": item["ambient_temp"],
                        "door_open": item["door_open"],
                        "signal_strength": item["signal_strength"],
                        "battery_level": item["battery_level"],
                    }
                )
                if batch.number_errors > 10:
                    print("Telemetry import stopped due to excessive errors.")
                    break
                if i % 1000 == 0:
                    print(f"Imported {i} telemetry rows ...")

        # Documents import
        if not args.no_docs:
            documents_collection = ensure_fd_documents(client, drop=args.drop_docs)
            if documents_collection is not None:
                root = Path("features/extraction/production_output")
                count = 0
                with documents_collection.batch.fixed_size(batch_size=args.batch_size) as doc_batch:
                    for generator in (iter_text_chunks(root), iter_visual_chunks(root), iter_page_chunks(root)):
                        for obj in generator:
                            doc_batch.add_object(obj)
                            count += 1
                            if doc_batch.number_errors > 10:
                                print("Documents import stopped due to excessive errors.")
                                break
                            if count % 1000 == 0:
                                print(f"Imported {count} document chunks ...")
                print(f"Total document chunks imported: {count}")

        # Summary
        total = telemetry_collection.aggregate.over_all(total_count=True).total_count
        print(f"FD_Telemetry total objects: {total}")
        print("Import complete.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
