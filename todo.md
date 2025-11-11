# TODO – VSM demo op Elysia skeleton

Deze TODO is voor de AI coding agent (/ Cursor) met volledige toegang tot de codebase, data en docs.

Doel:  
Een werkende VSM-demo bouwen bovenop Elysia + Weaviate, waarin een (junior) servicemonteur met een agent samen een storing triageert op basis van:

- Telemetry (timeseries)
- Manuals (parsed PDFs)
- Vlogs (problem → triage → oplossing)
- Synthetic WorldState/Context (C, W) rondom de installatie

Alle basis-analyses van de data 
- `data/README.md`
- `data/data_analysis_summary.md`
- `data/telemetry_schema.md`
- `data/telemetry_features.md`
- `data/telemetry_files.md`
- `data/manuals_structure.md`
- `data/manuals_files.md`
- `data/manuals_weaviate_design.md`
- `data/vlogs_structure.md`
- `data/vlogs_files.md`
- `data/vlogs_processing_results.md`



---

## Data Storage Strategy

### Weaviate vs Local Files

**Weaviate** (voor semantic search, RAG, discovery):
- **VSM_TelemetryEvent**: ~500-1000 event summaries met WorldState features (aggregated metadata)
- **VSM_ManualSections**: ~170-240 logische secties met SMIDO/failure mode tags
- **VSM_VlogCase**: 5 geaggregeerde cases met problem-solution workflows
- **VSM_VlogClip**: 15 individuele clips met timestamps en components

**Local Files** (voor raw data, detail queries, playback):
- **Telemetry parquet**: 785K datapunten (1-min intervals, 2.2 jaar) - efficiënt voor tijdvenster-queries
- **Manual JSONL**: 922 chunks (audit trail, source data)
- **Vlog .mov files**: 15 videos (21.7 MB, voor playback)

### Hybrid Query Pattern
1. Agent queries Weaviate voor incident discovery
2. Tool leest parquet voor detailed WorldState computation
3. Agent presenteert combined insights aan gebruiker

**Voordeel**: Best of both worlds - semantic search + efficient timeseries

---

## 1. Telemetry Data Strategy

**Bestands- en schema-info vind je in:**
- `data/telemetry_files.md`
- `data/telemetry_schema.md`
- `data/telemetry_features.md`
- `data/data_analysis_summary.md`

### Data Storage Architecture
- **Raw timeseries**: BLIJFT in parquet files (785K rows, efficiënt voor tijdvenster-queries)
- **Events/Incidents**: IN Weaviate als VSM_TelemetryEvent (aggregated metadata, semantic search)
- **Rationale**: 
  - Parquet optimaal voor tijdreeks-queries en WorldState berekeningen
  - Weaviate optimaal voor incident discovery en semantic matching
  - Voorkomt 785K objecten in Weaviate (costly, slow)

### 1.1 Event Detection from Telemetry

- [ ] 📝 PLANNED: Script: `features/telemetry_vsm/src/detect_events.py`
  - Detecteert incidents op basis van flags (_flag_main_temp_high, etc.)
  - Berekent WorldState features per event (min/max/avg, trends)
  - Output: JSONL met event metadata (niet alle datapunten)
  - Schatting: ~500-1000 events uit 785K datapunten

### 1.2 VSM_TelemetryEvent Schema

- [ ] 📝 PLANNED: Schema properties (zie data/telemetry_features.md):
  - Identification: event_id, asset_id, t_start, t_end, duration_minutes
  - Classification: failure_mode, affected_components, severity
  - Aggregates: temp_min/max/mean/trend per sensor
  - Description: Nederlandse samenvatting voor RAG (vectorized)
  - WorldState: JSON met key features
  - File reference: parquet_path + time_range (voor detail-lookup)

### 1.3 WorldState Computation Tool (Elysia)

- [ ] 📝 PLANNED: Tool: `elysia/tools/vsm/compute_worldstate.py`
  - Input: asset_id, timestamp, window_minutes
  - Leest direct uit parquet file (niet Weaviate)
  - Berekent 60+ features on-the-fly
  - Output: WorldState dict voor agent reasoning

### 1.4 Weaviate Import Script

- [ ] 📝 PLANNED: Script: `features/telemetry_vsm/src/import_telemetry_weaviate.py`
  - Weaviate client bouwt (url/api-key uit `.env`)
  - Creëert VSM_TelemetryEvent collection
  - Import event JSONL naar Weaviate
  - Verifieert collection is queryable

---

## 2. Manuals Data Strategy

**Relevante docs:**
- `data/manuals_structure.md`
- `data/manuals_files.md`
- `data/manuals_weaviate_design.md`

### Data Storage Architecture
- **Logical sections**: IN Weaviate als VSM_ManualSections (grouped chunks, classified)
- **Source chunks**: BLIJFT in JSONL files (audit trail)
- **Test/exercise content**: IN Weaviate maar FLAGGED met content_type="opgave" voor filtering
- **Rationale**:
  - Sections beter voor semantic retrieval dan individuele chunks
  - Test content nuttig voor prompt engineering, maar filterbaar
  - ~170-240 sections vs 922 chunks (betere granulariteit)

### 2.1 Section Grouping Script

- [ ] 📝 PLANNED: Script: `features/manuals_vsm/src/parse_sections.py`
  - Groepeert chunks op basis van heading hierarchy
  - Combineert 2-4 chunks per logische section
  - Detecteert content_type: uitleg, stappenplan, flowchart, tabel, voorbeeldcase, opgave
  - Output: JSONL met section objects

### 2.2 SMIDO Classification Script

- [ ] 📝 PLANNED: Script: `features/manuals_vsm/src/classify_smido.py`
  - Automatische classificatie via heading keywords
  - LLM-based classificatie voor ambiguous sections
  - Tags per section: smido_step, failure_modes, components
  - Output: Enriched section JSONL

### 2.3 Filter Test Content

- [ ] 📝 PLANNED: In section parsing:
  - Detecteer "Theorie opgaven", "Werkplekopdracht" headings
  - Flag met content_type="opgave"
  - Include in Weaviate (nuttig voor agent training)
  - Default queries filteren opgave content uit

### 2.4 Weaviate Schema & Import

- [ ] 📝 PLANNED: Schema: VSM_ManualSections (zie data/manuals_weaviate_design.md)
  - Properties: manual_id, title, section_path, page_range, body, content_type, smido_step, failure_modes, components, tags
  - Named vector op body, title, section_path
  - Filterable op content_type, smido_step, failure_modes

- [ ] 📝 PLANNED: Script: `features/manuals_vsm/src/import_manuals_weaviate.py`
  - Creëert VSM_ManualSections collection
  - Import enriched section JSONL
  - Verifieert collection is queryable

### 2.5 SMIDO Triage Flow Extraction

- [ ] 📝 PLANNED: Script: `features/manuals_vsm/src/extract_triage_flow.py`
  - Lokaliseer SMIDO-flowchart en storingstabellen in parsed manuals
  - Exporteer in machineleesbaar format (JSON met nodes/edges)
  - Sla op in Weaviate als VSM_TriageFlow (optioneel, voor structured knowledge)

---

## 3. Vlogs Data Strategy

**Relevante docs:**
- `data/vlogs_structure.md`
- `data/vlogs_files.md`
- `data/vlogs_processing_results.md`
- Up-to-date `process_vlogs.py` in `features/vlogs_vsm/src/`

### Data Storage Architecture
- **Case metadata**: IN Weaviate als VSM_VlogCase (5 cases, aggregated)
- **Clip metadata**: IN Weaviate als VSM_VlogClip (15 clips, individual)
- **Video files**: BLIJFT als .mov files locally (21.7 MB total)
- **Rationale**:
  - Weaviate voor discovery en semantic matching
  - Local files voor video playback
  - Voorkomt grote blobs in vector database

### 3.1 Metadata Enrichment

- [ ] 📝 PLANNED: Script: `features/vlogs_vsm/src/enrich_vlog_metadata.py`
  - Leest vlogs_vsm_annotations.jsonl (20 records)
  - Voegt SMIDO step tags toe
  - Standardiseert failure_modes naar controlled vocab
  - Genereert sensor pattern mappings
  - Output: Enriched JSONL

### 3.2 Weaviate Schema & Import

- [ ] 📝 PLANNED: Schema: VSM_VlogCase (zie data/vlogs_structure.md)
  - Properties: case_id, problem_summary, solution_summary, smido_steps, failure_modes, components, related_manual_sections
  - Named vector op problem_summary, solution_summary, transcript

- [ ] 📝 PLANNED: Schema: VSM_VlogClip (zie data/vlogs_structure.md)
  - Properties: case_id, clip_index, video_filename, video_path (local), duration, transcript, steps, tags, technical_components
  - Named vector op transcript, problem_summary, solution_summary

- [ ] 📝 PLANNED: Script: `features/vlogs_vsm/src/import_vlogs_weaviate.py`
  - Creëert VSM_VlogCase collection (5 cases)
  - Creëert VSM_VlogClip collection (15 clips)
  - Import enriched metadata
  - Video_path property verwijst naar local .mov file
  - Verifieert collections zijn queryable

### 3.3 Verify Processing Pipeline

- [ ] ✅ IMPLEMENTED: `process_vlogs.py` bestaat en werkt
  - Async, set-based verwerking (A1_1→A1_2→A1_3→case A1, etc.)
  - CoolingCaseCore-schema (inclusief `transcript` in het Nederlands)
  - Output: `features/vlogs_vsm/output/vlogs_vsm_annotations.jsonl` (20 records)

---

## 4. Cross-links tussen Telemetry ↔ Manuals ↔ Vlogs

We willen uiteindelijk één geïntegreerde “wereld” in Weaviate / Elysia.

### 4.1. Conceptuele mapping

- [ ] 📝 PLANNED: Lees in `data/data_analysis_summary.md` welke synthetic scenario's zijn gedefinieerd (bv. "condenser fan failure", "liquid line blockage", etc.).
- [ ] 📝 PLANNED: Leg een mapping vast (in code, bijv. Python dict) van:
  - `scenario_id` → relevante:
    - `VSM_VlogCase` (A1–A5)
    - `VSM_ManualSections` subsets (storingstabellen, SMIDO-stappen, component-specific sections)
- [ ] 📝 PLANNED: Bedenk en implementatie-voorstel:
  - Cross-refs in Weaviate:
    - `VSM_TelemetryEvent.related_manual_sections`
    - `VSM_TelemetryEvent.related_vlog_cases`
    - `VSM_VlogCase.related_manual_sections`
    - etc.

### 4.2. Implementatie cross-refs

- [ ] 📝 PLANNED: Script (bv. `features/integration_vsm/src/link_entities_weaviate.py`) dat:
  - Scenario/issue-tags vergelijkt tussen events, vlogs en manuals.
  - Op basis van configuraties / mapping-tabel cross-references aanmaakt.
  - Zoveel mogelijk deterministisch, niet alleen LLM-guessing.

---

## 5. Elysia + Weaviate configuratie

We gaan er vanuit dat Elysia en Weaviate al draaien (`vsm-hva` env).

### 5.1. Elysia Weaviate client & config

- [ ] ✅ IMPLEMENTED: `.env` / `CLAUDE.md` bevatten:
  - Weaviate URL + API-key configuratie
  - LLM-provider keys (Gemini/OpenAI/etc.) setup
- [ ] 📝 PLANNED: Zorg dat de Elysia backend:
  - De VSM-Weaviate client kan pakken (eventueel via `ELYSIA_CUSTOM_WEAVIATE_URL`-achtig mechanisme, zie Elysia docs).
  - De VSM-collecties ziet (`VSM_*`).

### 5.2. Elysia preprocess

- [ ] 📝 PLANNED: Gebruik Elysia's `preprocess`-mechanisme op de relevante collecties:
  - `preprocess(["VSM_TelemetryEvent", "VSM_ManualSections", "VSM_VlogClip", "VSM_VlogCase"])`
- [ ] 📝 PLANNED: Controleer in de Elysia UI (Data tab) of:
  - Display types logisch zijn (bv. vlogs als "documents" + "timeline style", manuals als "documents", telemetry als "generic data" of "tables").
  - Metadata en voorbeeld-queries zinvol zijn.

---

## 6. Agent / Tree design (SMIDO + WorldState)

We willen 1 of meerdere agents die de SMIDO-methodiek + WorldState (W) gebruiken.

### 6.1. Agent prompts / tools

- [ ] 📝 PLANNED: Definieer in de Elysia tree:
  - Een "VSM_ServiceAgent" node met instructies in het Nederlands:
    - Werkt volgens SMIDO: Melding → Technisch → Installatie vertrouwd → 3 P's → Ketens.
    - Gebruik Weaviate-tools om:
      - TelemetryEvents te zoeken rond de huidige tijd (`t-now`, `t-history`).
      - Relevante manual-sections (SMIDO-stappen, storingstabellen) op te halen.
      - Passende vlogs te tonen (als voorbeeldcases).
- [ ] 📝 PLANNED: Zorg dat:
  - De agent snapt welke info van de user (monteur) komt (WorldState: visuele bevindingen, geluid, klantinfo).
  - De agent vragen kan stellen om C/W completer te maken.

### 6.2. Beslissingsboom (tree) aanpassen

- [ ] 📝 PLANNED: Voeg (in Python) een VSM-specifieke branch toe aan de Elysia tree, bv.:
  - Node "Detect_intent_VSM"
  - Node "Fetch_telemetry_context"
  - Node "Fetch_manual_knowledge"
  - Node "Fetch_vlog_examples"
  - Node "Generate_SMIDO_plan"
- [ ] 📝 PLANNED: Koppel de juiste tools aan deze nodes (Weaviate query/aggregate, custom tools voor tijdvensters, etc.).

---

## 7. Demo-flow & evaluatie

### 7.1. Demo-scenario's

**⭐ PRIMARY SCENARIO: A3 "Ingevroren Verdamper" (Frozen Evaporator)**

This is the **best case scenario** identified in `data/data_analysis_summary.md` and `data/README.md` with perfect alignment across ALL data sources (manual + vlog + telemetry). All demo development should prioritize this scenario.

- [ ] 📝 PLANNED: Op basis van `data/data_analysis_summary.md` en `vlogs_processing_results.md`:
  - **PRIMARY**: A3 = ingevroren verdamper (Frozen Evaporator) ⭐
    - Perfect match: Manual page ~7 + A3_1/A3_2/A3_3 vlogs + telemetry flags
    - Complete SMIDO flow: M→T→I→D→O
    - Definieer tijdwindow in telemetry en ground truth manual-secties/vlogs
  - **ALTERNATIVE**: A1 = condensorventilator (Condenser Fan)
    - Good for demonstrating 3P-Procesinstellingen
    - Definieer tijdwindow en ground truth voor secundaire demo

### 7.2. Golden answers / tests

- [ ] 📝 PLANNED: Bouw een klein testscript dat:
  - **PRIMARY**: Test met A3 "Ingevroren Verdamper" scenario ⭐
    - Prompt stuurt naar Elysia met A3 context
    - Checkt of de agent:
      - De juiste componenten noemt (verdamper, defrost, thermostaat, luchtkanalen)
      - Het probleem correct identificeert (frozen evaporator)
      - Relevante manual section citeert (page ~7, "Koelproces uit balans")
      - Relevante vlog-case citeert (A3_1, A3_2, A3_3)
      - SMIDO flow correct volgt (M→T→I→D→O)
  - **ALTERNATIVE**: Test met A1 scenario voor secundaire validatie

---

## 8. Open vragen (voor de mens, niet voor de code agent)

Deze kan de code agent waarschijnlijk niet zelf beantwoorden en moeten nog samen met jou worden besloten:

1. **Taal UI / output**
   - Moet *alles* (UI-tekst, agent-antwoord, tags) strikt in het Nederlands zijn, of is Engels toegestaan voor meta-velden?

   Antwoord: Nederlands voor prompts, Engels voor metadata (bv. tags, labels).
2. **Aantal assets / installatietypes**
   - Willen we in de demo expliciet doen alsof dit één specifiek installatietype is 

   Ja: zie de verkozen usecase  

3. **Privacy / deployment**
   - Komt de demo alleen lokaal te draaien (classroom / lab) of moet deze in een (demo-)cloudomgeving kunnen? Lokaal voor nu, maar weaviate cloud!
4. **Logging / telemetry-logging in Weaviate**
   - Wil je interactie-logs (agent reasoning, vragen/antwoorden) óók als documenten in Weaviate opslaan voor later leren? 
   Volg de huidige set up van Elysia, er is al een oplossing voor dit.


