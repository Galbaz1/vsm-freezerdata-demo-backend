# Data Upload Strategy - Executive Summary

**Date**: November 11, 2024  
**Purpose**: Quick reference for implementing VSM data upload to Weaviate Cloud

---

## Key Findings

### 1. Manual Reveals 4 P's (Not 3!)

**Finding**: Manual heading says "3-P's" but lists **4 P's**:
- P1: Power (electrical supply)
- P2: Procesinstellingen (settings vs design)
- P3: Procesparameters (measurements vs design)
- **P4: Productinput** (external conditions - condenser air/water, product load, ambient vs design)

**Impact**: P4_Node checks if fault is **outside installation** (not a broken component).

### 2. WorldState (W) vs Context (C) Split

**Finding**: Manual distinguishes dynamic state from static design data:
- **W (WorldState)**: Current sensors, technician observations, urgency
- **C (Context)**: "Gegevens bij inbedrijfstelling" (commissioning data, design parameters, schemas)

**Impact**: 
- GetAssetHealth compares W vs C (balance check)
- Context Manager manages both W and C separately
- Matches manual's conceptual model exactly

### 3. "Uit Balans" Concept is Central

**Finding**: Manual section "Het koelproces uit balans" states: **"Een storing betekent dus niet altijd dat er een component defect is"**

**Impact**:
- Faults can be system operating outside design parameters (balance violated)
- AnalyzeSensorPattern detects which balance factor is violated
- Events represent "uit balans" states, not just broken parts

### 4. Elysia Preprocessing is Critical

**Finding**: Elysia's `preprocess()` function is essential for intelligent querying.

**Action**: Run `preprocess()` on all VSM_* collections after uploading data.

---

### 2. Hybrid Storage Strategy Confirmed

**Finding**: The strategy in `todo.md` is correct - store **metadata summaries** in Weaviate, keep **raw data** locally.

**Rationale**:
- Weaviate: Optimized for semantic search (500-1000 events vs 785K datapoints)
- Parquet: Optimized for time-window queries (efficient columnar format)
- Best of both worlds: Discovery via Weaviate, detail via tools reading parquet

**Collections**:
- `VSM_TelemetryEvent`: ~500-1000 aggregated events (not all 785K rows)
- `VSM_ManualSections`: ~170-240 logical sections (not all 922 chunks)
- `VSM_VlogCase`: 5 aggregated cases
- `VSM_VlogClip`: 15 individual clips
- `VSM_Diagram`: 9 Mermaid diagrams (NEW)

---

### 3. Upload Sequence Matters

**Finding**: Collections have dependencies - upload in correct order to enable cross-linking.

**Sequence**:
1. **VSM_Diagram** (no dependencies) ✅ First
2. **VSM_ManualSections** (can link to diagrams) ✅ Second
3. **VSM_TelemetryEvent** (can link to manuals/diagrams) ✅ Third
4. **VSM_VlogClip** (can link to manuals/diagrams) ✅ Fourth
5. **VSM_VlogCase** (depends on clips) ✅ Fifth
6. **Cross-linking** (requires all collections) ✅ Sixth
7. **Elysia Preprocessing** (final step) ✅ Seventh

---

### 5. Two New Collections Required

**VSM_Diagram**: Visual logic diagrams
- SearchManualsBySMIDO returns diagrams alongside text
- Links to manual sections via chunk_id

**VSM_WorldStateSnapshot**: Reference patterns (SYNTHETIC)
- AnalyzeSensorPattern needs typical "uit balans" patterns
- Generate 8-12 snapshots from real events + manual descriptions
- Represents balance factors from manual page 11

---

### 6. Cross-Collection Linking Strategy

**Finding**: Cross-references enable unified troubleshooting across all data sources.

**Linking Patterns**:
- **TelemetryEvent ↔ ManualSections**: Match by failure mode, component
- **TelemetryEvent ↔ VlogCase**: Match by failure mode, world_state_pattern
- **VlogCase ↔ ManualSections**: Match by SMIDO step, failure mode
- **All ↔ Diagrams**: Via chunk_id, failure mode, SMIDO step

**Implementation**: Use semantic search + deterministic rules (chunk_id matching)

---

## Implementation Roadmap

### Step 1: Create Upload Scripts (Week 1)

**Priority Order**:

1. **Diagrams** (simplest, no dependencies)
   - `features/diagrams_vsm/src/extract_diagram_metadata.py`
   - `features/diagrams_vsm/src/import_diagrams_weaviate.py`

2. **Manual Sections** (foundation for other collections)
   - `features/manuals_vsm/src/parse_sections.py`
   - `features/manuals_vsm/src/classify_smido.py`
   - `features/manuals_vsm/src/import_manuals_weaviate.py`

3. **Telemetry Events** (requires event detection)
   - `features/telemetry_vsm/src/detect_events.py`
   - `features/telemetry_vsm/src/import_telemetry_weaviate.py`

4. **Vlogs** (requires enrichment)
   - `features/vlogs_vsm/src/enrich_vlog_metadata.py`
   - `features/vlogs_vsm/src/import_vlogs_weaviate.py`

5. **Cross-Linking** (requires all collections)
   - `features/integration_vsm/src/link_entities_weaviate.py`

### Step 2: Upload Data (Week 1-2)

Follow the upload sequence above. Test each collection before moving to next.

### Step 3: Elysia Integration (Week 2)

```python
from elysia import preprocess

preprocess([
    "VSM_TelemetryEvent",
    "VSM_ManualSections",
    "VSM_VlogCase",
    "VSM_VlogClip",
    "VSM_Diagram"
])
```

### Step 4: Validation (Week 2)

- Test queries for each collection
- Verify cross-links work
- Test Elysia Query tool
- Validate A3 "Frozen Evaporator" scenario

---

## Key Design Decisions

### 1. Vectorization: Use `text2vec-weaviate`

**Decision**: Start with built-in Weaviate embeddings (no API key needed)

**Rationale**: 
- Simpler setup for MVP
- Can upgrade to OpenAI embeddings later if needed
- Good enough quality for semantic search

### 2. Display Types for Elysia

**Decision**: Set appropriate display types during preprocessing

**Mapping**:
- `VSM_ManualSections` → `"document"` (text-heavy)
- `VSM_TelemetryEvent` → `"table"` (structured)
- `VSM_VlogCase` → `"conversation"` (workflow)
- `VSM_VlogClip` → `"message"` (steps)
- `VSM_Diagram` → `"document"` (reference)

### 3. Batch Size: 200 objects

**Decision**: Use `batch.fixed_size(batch_size=200)` for imports

**Rationale**: Optimal balance between speed and error handling

---

## Size Estimates

| Collection | Objects | Size | Status |
|------------|---------|------|--------|
| VSM_Diagram | 9 | ~18 KB | 📝 Planned |
| VSM_ManualSections | ~170-240 | ~500-700 KB | 📝 Planned |
| VSM_TelemetryEvent | ~500-1000 | ~1-2 MB | 📝 Planned |
| VSM_VlogCase | 5 | ~25 KB | 📝 Planned |
| VSM_VlogClip | 15 | ~45 KB | 📝 Planned |
| VSM_WorldStateSnapshot | 8-12 | ~20 KB | 📝 Planned (SYNTHETIC) |
| FD_Assets (enriched) | 1 | ~5 KB | 📝 Planned (SYNTHETIC) |
| **Total** | **~700-1270** | **~2.5-3 MB** | |

**Cost Estimate**: <$10/month for Weaviate Cloud (demo usage)

---

## Critical Success Factors

### 1. SMIDO Classification Accuracy

**Risk**: Incorrect SMIDO step classification breaks agent queries

**Mitigation**: 
- Use keyword matching + LLM classification
- Validate against known examples (A3 scenario)
- Manual review of ambiguous sections

### 2. Cross-Collection Linking Quality

**Risk**: Poor linking reduces agent's ability to find related information

**Mitigation**:
- Use semantic search + deterministic rules
- Validate links manually for A3 scenario
- Test query patterns before finalizing

### 3. Elysia Preprocessing Success

**Risk**: Preprocessing fails or produces poor metadata

**Mitigation**:
- Ensure collections have diverse sample data (≥10 objects)
- Test preprocessing on one collection first
- Review generated metadata before proceeding

---

## Testing Strategy

### Unit Tests (Per Script)

- Schema validation
- Data type checks
- Required field validation
- Controlled vocabulary validation

### Integration Tests (Per Collection)

- Upload verification (object counts)
- Query testing (filters, semantic search)
- Cross-link verification

### End-to-End Test (A3 Scenario)

**Test Case**: A3 "Frozen Evaporator"

**Validation**:
1. Query for "ingevroren verdamper" → Returns relevant events, manuals, vlogs
2. Filter by `smido_step="3P_procesparameters"` → Returns correct sections
3. Cross-link verification → Events link to A3 vlog case
4. Diagram reference → Manual sections link to balance diagram
5. Elysia Query tool → Can retrieve and format results correctly

---

## Next Actions

### Immediate (This Week)

1. ✅ Review strategy documents (updated with manual insights)
2. ⏳ Create diagram extraction + upload scripts
3. ⏳ Create manual section parsing + SMIDO classification scripts
4. ⏳ Generate WorldState snapshots (8-12 patterns from vlogs + manual balance factors)
5. ⏳ Enrich FD_Assets with commissioning data (C)

### Short-term (Next 2 Weeks)

1. ⏳ Implement all upload scripts
2. ⏳ Upload all collections
3. ⏳ Run cross-linking
4. ⏳ Run Elysia preprocessing
5. ⏳ Validate with A3 scenario

### Long-term (Month 1)

1. ⏳ Optimize queries based on agent usage
2. ⏳ Add more events from historical data
3. ⏳ Refine SMIDO classification
4. ⏳ Add more diagrams if needed

---

## References

- **Full Strategy**: `docs/data/DATA_UPLOAD_STRATEGY.md`
- **Schema Designs**: 
  - `docs/data/manuals_weaviate_design.md`
  - `docs/data/vlogs_structure.md`
  - `docs/data/telemetry_features.md`
- **Elysia Preprocessing**: `docs/diagrams/elysia/20_collection_preprocessing.mermaid`
- **Weaviate Import Guide**: `docs/adding_data.md`

---

**Status**: ✅ Strategy Complete - Ready for Implementation  
**Next Step**: Create diagram extraction script

