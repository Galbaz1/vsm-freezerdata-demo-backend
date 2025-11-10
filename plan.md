# VSM FreezerData Ingestion Plan

## Current Findings
- Only `FD_Telemetry` and `FD_Documents` are seeded via `import_data.py:1-196`, leaving `FD_Assets`, `FD_Alarms`, and optional `FD_Cases` empty, so VSM-specific tools lack required collections (`docs/vsm_freezer_demo.md:173-365`).
- The telemetry importer vectorizes every numeric record with OpenAI (`import_data.py:31-54`) despite the spec recommending `Configure.Vectorizer.none()` for time-series metrics (`docs/vsm_freezer_demo.md:212-233`), which inflates cost without aiding filters/aggregates.
- Document ingestion uses only `*.text_chunks.jsonl` (`import_data.py:102-158`), omitting tables, figures, page summaries, and metadata that exist in `features/extraction/production_output/*` (`docs/vsm_freezer_demo.md:155-168`, `features/extraction/README.md:31-150`).
- The importer deletes and recreates `FD_Documents` but never guards `FD_Telemetry`, lacks CLI flags, and always loads the full 528-day dataset in a single run, making retries or partial imports difficult.
- VSM custom tools (`docs/vsm_freezer_demo.md:372-449`) are not implemented yet, so even with data present, Elysia cannot execute the intended diagnostic workflow.

## Recommended Actions
1. **Align Collection Schemas**
   - Recreate `FD_Telemetry` with `Configure.Vectors.none()` and remove the synthetic `readout_text` embedding; keep scalar properties for numeric filters.
   - Seed `FD_Assets`, `FD_Alarms`, and (optionally) `FD_Cases` using the example schemas/data in the VSM guide for end-to-end coverage.

2. **Complete Document Coverage**
   - Extend ingestion to load `*.visual_chunks.jsonl` and `*.pages.jsonl`, storing figure captions, asset paths, and page summaries. Include `asset_model`/`section_title` from `.meta.json` to support filtering.

3. **Improve Import Ergonomics**
   - Parameterize the script (asset ID, batch size, start/end dates) and add safe `--drop/--upsert` behaviors for every collection so repeated runs are idempotent.
   - Chunk telemetry imports by day or month to make retries faster and monitor `batch.number_errors` per chunk.

4. **Implement VSM Tools**
   - Build the `GetAssetHealth`, `GetTelemetryWindow`, and `SearchDocuments` tools under `elysia/tools/vsm/`, ensuring they query the appropriate collections and leverage the cleaned telemetry stats (`docs/eda/README.md:62-170`).
   - Consider precomputing aggregates or anomaly flags during ingestion to minimize on-demand processing inside the tools.

5. **Future Extensions**
   - Decide whether to ingest the `features/vlogs_vsm` videos (e.g., via transcripts) once the core telemetry/manual flows are stable.
   - Add automated tests/scripts to validate collection counts and sample queries after each import run.


########

Got it — I’ve made the changes but won’t run anything.

What I changed

import_data.py
Telemetry now uses Configure.Vectorizer.none() (no embeddings) and drops readout_text.
Added CLI flags: --drop-telemetry, --drop-docs, --asset-id, --start, --end, --batch-size, --no-docs.
Robust cloud URL handling (adds https:// if missing).
Documents import now covers *.text_chunks.jsonl, *.visual_chunks.jsonl, and *.pages.jsonl, adding an asset_path field for figures.
scripts/seed_assets_alarms.py
Seeds FD_Assets, FD_Alarms, and optional FD_Cases with sensible demo rows.
Uses text2vec_weaviate for these text-heavy collections.
Flags: --drop-assets, --drop-alarms, --with-cases, --drop-cases, --asset-id.
scripts/preprocess_collections.py
Runs Elysia preprocessing for UI/tooling. Auto-maps WEAVIATE_* → WCD_* env vars for Elysia.
Files to review

import_data.py (line 1)
scripts/seed_assets_alarms.py (line 1)
scripts/preprocess_collections.py (line 1)
How to run in your conda env (vsm-hva)

Install deps (Elysia + pandas/pyarrow if needed):
pip install -e ".[dev]" pandas pyarrow
Export env:
set -a && source .env && set +a
Seed small text collections:
python scripts/seed_assets_alarms.py --drop-assets --drop-alarms --with-cases --drop-cases --asset-id FZ-123
Import telemetry + manuals (example window):
python import_data.py --drop-telemetry --drop-docs --asset-id FZ-123 --start 2024-03-01 --end 2024-04-01
Preprocess for Elysia:
python scripts/preprocess_collections.py --collections FD_Assets FD_Telemetry FD_Alarms FD_Documents FD_Cases
Start Elysia app (optional):
elysia start then add keys/cluster in Settings
Notes

If you prefer in-cluster embeddings for docs, switch FD_Documents vectorizer to Configure.Vectors.text2vec_weaviate(...) in import_data.py.
The preprocess script maps WEAVIATE_URL/API_KEY to WCD_URL/API_KEY so Elysia picks up your cluster.
Want me to also scaffold the three VSM tools (health.py, telemetry.py, docs.py) under elysia/tools/vsm/ next?

3 files changed
+458
-152

Undo

View all changes
import_data.py
+245
-152

preprocess_collections.py
+40
-0

seed_assets_alarms.py
+173
-0
