import os
from datetime import datetime
from dotenv import load_dotenv
import argparse
import weaviate
from weaviate.classes.config import Configure, Property, DataType, Tokenization
from weaviate.classes.init import Auth


def connect_client() -> weaviate.WeaviateClient:
    load_dotenv()
    url = os.environ["WEAVIATE_URL"]
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"
    key = os.environ["WEAVIATE_API_KEY"]
    return weaviate.connect_to_weaviate_cloud(cluster_url=url, auth_credentials=Auth.api_key(key))


def ensure_assets(client: weaviate.WeaviateClient, drop: bool):
    name = "FD_Assets"
    if client.collections.exists(name):
        if drop:
            print("Dropping FD_Assets ...")
            client.collections.delete(name)
        else:
            print("FD_Assets exists; using existing collection.")
            return client.collections.get(name)

    print("Creating FD_Assets ...")
    return client.collections.create(
        name=name,
        vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
        properties=[
            Property(name="asset_id", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="model", data_type=DataType.TEXT),
            Property(name="location", data_type=DataType.TEXT),
            Property(name="installation_date", data_type=DataType.DATE),
            Property(name="capacity_liters", data_type=DataType.NUMBER),
            Property(name="target_temp", data_type=DataType.NUMBER),
            Property(name="status", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
        ],
    )


def ensure_alarms(client: weaviate.WeaviateClient, drop: bool):
    name = "FD_Alarms"
    if client.collections.exists(name):
        if drop:
            print("Dropping FD_Alarms ...")
            client.collections.delete(name)
        else:
            print("FD_Alarms exists; using existing collection.")
            return client.collections.get(name)

    print("Creating FD_Alarms ...")
    return client.collections.create(
        name=name,
        vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
        properties=[
            Property(name="asset_id", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="timestamp", data_type=DataType.DATE),
            Property(name="alarm_code", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="severity", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="message", data_type=DataType.TEXT),
            Property(name="acknowledged", data_type=DataType.BOOL),
            Property(name="resolved_at", data_type=DataType.DATE),
        ],
    )


def ensure_cases(client: weaviate.WeaviateClient, drop: bool):
    name = "FD_Cases"
    if client.collections.exists(name):
        if drop:
            print("Dropping FD_Cases ...")
            client.collections.delete(name)
        else:
            print("FD_Cases exists; using existing collection.")
            return client.collections.get(name)

    print("Creating FD_Cases ...")
    return client.collections.create(
        name=name,
        vectorizer_config=Configure.Vectorizer.text2vec_weaviate(),
        properties=[
            Property(name="case_id", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="asset_id", data_type=DataType.TEXT, tokenization=Tokenization.LOWERCASE),
            Property(name="symptom", data_type=DataType.TEXT),
            Property(name="root_cause", data_type=DataType.TEXT),
            Property(name="actions_taken", data_type=DataType.TEXT),
            Property(name="outcome", data_type=DataType.TEXT),
            Property(name="created_at", data_type=DataType.DATE),
            Property(name="technician", data_type=DataType.TEXT),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Seed FD_Assets, FD_Alarms and optional FD_Cases.")
    parser.add_argument("--asset-id", default="FZ-123")
    parser.add_argument("--drop-assets", action="store_true")
    parser.add_argument("--drop-alarms", action="store_true")
    parser.add_argument("--with-cases", action="store_true")
    parser.add_argument("--drop-cases", action="store_true")
    args = parser.parse_args()

    client = connect_client()
    try:
        assets = ensure_assets(client, drop=args.drop_assets)
        alarms = ensure_alarms(client, drop=args.drop_alarms)
        cases = ensure_cases(client, drop=args.drop_cases) if args.with_cases else None

        # Upsert one asset
        print("Seeding FD_Assets ...")
        assets.data.insert(
            properties={
                "asset_id": args.asset_id,
                "model": "Industrial Freezer 135-1570",
                "location": "Warehouse A, Bay 3",
                "installation_date": "2022-10-15T00:00:00Z",
                "capacity_liters": 1500,
                "target_temp": -33.0,
                "status": "active",
            }
        )

        # Upsert example alarms
        print("Seeding FD_Alarms ...")
        alarms.data.insert(
            properties={
                "asset_id": args.asset_id,
                "timestamp": "2024-03-15T14:30:00Z",
                "alarm_code": "E305",
                "severity": "critical",
                "message": "Evaporator fan RPM signal loss",
                "acknowledged": False,
                "resolved_at": None,
            }
        )
        alarms.data.insert(
            properties={
                "asset_id": args.asset_id,
                "timestamp": "2024-03-15T14:35:00Z",
                "alarm_code": "E102",
                "severity": "warning",
                "message": "High temperature deviation from setpoint",
                "acknowledged": False,
                "resolved_at": None,
            }
        )

        if cases:
            print("Seeding FD_Cases ...")
            cases.data.insert(
                properties={
                    "case_id": "CASE-001",
                    "asset_id": args.asset_id,
                    "symptom": "Fan RPM drops to 0; temp rising",
                    "root_cause": "Loose wiring harness",
                    "actions_taken": "Re-seated connector; verified 12V supply",
                    "outcome": "Restored operation; no further alarms",
                    "created_at": "2024-03-16T10:00:00Z",
                    "technician": "J. Doe",
                }
            )

        print("Seed complete.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
