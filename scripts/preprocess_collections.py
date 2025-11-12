import os
import argparse
from dotenv import load_dotenv

# Ensure the local package is importable if running from repo root
try:
    from elysia.preprocessing.collection import preprocess
except Exception as e:
    raise SystemExit(
        "Failed to import Elysia. Make sure you've activated your virtual environment (.venv) and installed the repo:\n"
        "  pip install -e .\n"
        f"Import error: {e}"
    )


def main():
    parser = argparse.ArgumentParser(description="Run Elysia preprocessing on Weaviate collections.")
    parser.add_argument(
        "--collections",
        nargs="+",
        default=["FD_Assets", "FD_Telemetry", "FD_Alarms", "FD_Documents", "FD_Cases"],
        help="Collections to preprocess for Elysia UI.",
    )
    args = parser.parse_args()

    load_dotenv()
    # Map WEAVIATE_* env to Elysia's expected WCD_* if not set
    if not os.environ.get("WCD_URL") and os.environ.get("WEAVIATE_URL"):
        os.environ["WCD_URL"] = os.environ["WEAVIATE_URL"]
    if not os.environ.get("WCD_API_KEY") and os.environ.get("WEAVIATE_API_KEY"):
        os.environ["WCD_API_KEY"] = os.environ["WEAVIATE_API_KEY"]

    print(f"Preprocessing collections: {args.collections}")
    preprocess(collection_names=args.collections)
    print("Preprocess complete.")


if __name__ == "__main__":
    main()

