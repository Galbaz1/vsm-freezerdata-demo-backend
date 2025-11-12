# VSM Project - Development History

**Project**: Virtual Service Mechanic AI Agent  
**Timeline**: October 2024 - November 2025  
**Current Version**: Phase 3 (In Progress)

---

## November 2024: Foundation & Data Preparation

### Data Acquisition & Processing
- **Telemetry**: 785K rows (asset 135_1570) cleaned with 6 anomaly flags
  - Removed 17,576 outliers (2.24%), sensor error codes (882.6°C readings)
  - 1-minute sampling over 2.2 years
  - Final quality: ⭐⭐⭐⭐⭐ production-ready
- **Manuals**: 3 PDFs parsed by Landing AI
  - storingzoeken-koeltechniek (29 pages) - SMIDO methodology
  - inspectie-en-onderhoud (61 pages) - Maintenance procedures  
  - opbouw-en-werking (163 pages) - System fundamentals (expanded from 18 pages)
  - Total: 689 text chunks, 233 visual chunks
- **Vlogs**: 15 service videos processed with Gemini 2.5 Pro
  - 5 cases (A1-A5), 15 clips, full Dutch transcripts
  - A3 "Frozen Evaporator" identified as star scenario

### November 11, 2024: Phase 1 Complete
**Milestone**: All data uploaded to Weaviate
- Created 6 VSM collections (221 objects total)
- Implemented 4 P's classification (Power, Procesinstellingen, Procesparameters, Productinput)
- Generated 13 synthetic WorldState snapshots
- Created commissioning data (Context C) for balance checks
- All collections preprocessed with ELYSIA_METADATA__

**Key Achievement**: Perfect data alignment for A3 scenario across manual + vlog + telemetry

---

## November 11, 2024: Phase 2 Implementation (7 Plans in Parallel)

### Plan 1: WorldState Engine
- Built `worldstate_engine.py` computing 58 features from parquet
- Performance: <500ms for 60-min window ✅
- Tests: 18/18 pytest passing
- **Learnings**: Pandas lazy loading critical, NaN handling required

### Plan 2: Simple Query Tools
- `get_alarms`: Query VSM_TelemetryEvent by severity
- `query_telemetry_events`: Find historical incidents
- `query_vlog_cases`: Search A1-A5 cases
- Tests: 3/3 tools working
- **Learnings**: Optional params must handle None gracefully

### Plan 3: SearchManualsBySMIDO
- SMIDO filtering (power/settings/parameters/input)
- Diagram integration (VSM_Diagram linked to sections)
- Opgave filtering (excludes 9 test sections by default)
- Tests: 3/3 passing
- **Learnings**: Filter API requires `by_property()` not dict syntax

### Plan 4: Advanced Diagnostic Tools
- `get_asset_health`: W vs C comparison ("uit balans" detection)
- `analyze_sensor_pattern`: Match against 13 reference patterns
- Tests: 3/3 passing
- **Learnings**: Timestamp handling tricky (historical vs current), needed pandas install

### Plan 5: SMIDO Tree Structure
- 9 branches with proper hierarchy (M→T→I→D[P1-P4]→O)
- Dutch prompts with conversational A3 examples
- Safety criteria at multiple levels
- **Learnings**: Must use `tree_data.branches` not `tree.branches`

### Plan 6: Orchestrator + Context Manager
- ContextManager: Separates W (WorldState) vs C (Context)
- SMIDOOrchestrator: Tracks phase progression
- Imports successful
- **Learnings**: Environment persistence via `tree_data.environment`

### Plan 7: A3 End-to-End Test
- Full tree execution: 164s → identifies frozen evaporator ✅
- Calls get_alarms, get_asset_health, compute_worldstate, query_vlog_cases
- Agent uses Dutch, explains reasoning, references A3 case
- **Learnings**: 3-5 minutes is expected for full SMIDO workflow

**Phase 2 Complete**: November 11, 2024 (all tests passing)

---

## November 12, 2025: Logging & Config Improvements

### Dual-Handler Logging System
- **Problem**: Terminal flooded with 1000+ lines/min
- **Solution**: File handler (DEBUG→logs/) + Console handler (INFO→terminal)
- Split: `elysia.log` (app) + `uvicorn.log` (HTTP)
- **Result**: Clean terminal, complete audit trail

### Model Configuration Verified
- Base: gemini-2.5-flash (decision agent)
- Complex: gemini-2.5-pro (semantic search, complex reasoning)
- **Critical fix**: Use `COMPLEX_PROVIDER=gemini` not `google`
- **Learnings**: Elysia concatenates provider/model → `gemini/gemini-2.5-pro`

### Telemetry Rebase
- Shifted timestamps +639 days (Oct 2022 → Jul 2024, Apr 2024 → Jan 2026)
- Data appears "current" through Jan 1, 2026
- Updated tools for dynamic timestamp handling
- **Learnings**: Can simulate "future" predictions with `is_future` flag

---

## November 12, 2025: User Testing & Gap Discovery

### Testing Review (Real Interaction Flows)
- **Flow 1** (vague start): Got stuck in I phase, diagram search failed
- **Flow 2** (specific start): Progressed efficiently, ready for diagnosis
- **Findings**: 
  - ✅ Dutch excellent, SMIDO awareness good, educational tone strong
  - ⚠️ Performance slow (2-3 min/interaction)
  - ⚠️ Diagram search broken (0 diagrams returned)
  - ⚠️ I phase asks repeatedly for confirmation

### Quick Status Implementation Discovery
- **Problem**: "What's current state?" → 2-3 minute response
- **Root Cause**: `get_current_status` tool documented but **NOT implemented**
- Falls back to get_asset_health (parquet reads) + search_manuals (unnecessary)
- **Solution designed**: Fast-path tool reading pre-seeded cache (<200ms)
- **Status**: Documented in QUICK_STATUS_IMPLEMENTATION.md, NOT coded

---

## Key Architectural Decisions

### 1. Hybrid Data Storage (Weaviate + Parquet)
**Rationale**: Semantic search (Weaviate) + time-series efficiency (parquet)
- Events/manuals/vlogs in Weaviate for discovery
- 785K raw telemetry in parquet for WorldState computation
- **Outcome**: Best of both worlds, no performance issues

### 2. WorldState (W) vs Context (C) Separation
**Rationale**: "Uit balans" concept - not all failures are broken components
- W = dynamic (current sensors, observations)
- C = static (commissioning data, design parameters)
- Balance check = W vs C comparison
- **Outcome**: Core diagnostic capability

### 3. 4 P's (Not 3!)
**Discovery**: Manual lists 4 P's despite calling it "3 P's"
- P1: Power (electrical)
- P2: Procesinstellingen (settings)
- P3: Procesparameters (measurements)
- P4: Productinput (environmental/loading)
- **Outcome**: All 4 implemented in D branch

### 4. Bootstrap System for Tree Auto-Loading
**Rationale**: Dynamic tree construction without hardcoding
- `feature_bootstrappers=["vsm_smido"]` in config
- Bootstrap runs at tree creation
- **Outcome**: SMIDO tree + tools load automatically

### 5. Test Content Flagging (Not Filtering Out)
**Rationale**: Useful for prompt engineering, but exclude from production queries
- 9 sections flagged `content_type="opgave"`
- Included in Weaviate
- Filtered with `Filter.by_property("content_type").not_equal("opgave")`
- **Outcome**: Flexibility for training vs production

---

## Critical Learnings

### Technical
1. **Weaviate v4 API**: Use `Configure.Vectors` + `Filter.by_property()` (not old dict syntax)
2. **DSPy + Elysia**: Provider/model concatenation requires careful naming
3. **Async generators**: Tools must `yield Status` then `yield Result`
4. **Parquet performance**: Lazy loading essential for 785K rows
5. **Timestamp handling**: Historical demo data needs clamping to data range

### Domain Knowledge
1. **"Uit balans" is core**: System imbalance ≠ broken component (must emphasize repeatedly)
2. **SMIDO is sequential**: Can't skip phases (M→T→I→D→O order matters)
3. **One question at a time**: Technician must walk around, don't overload
4. **Praise observations**: "Uitstekend gevonden!" builds confidence
5. **Safety-first**: Escalation criteria at multiple levels (agent/branch/action)

### Process
1. **Parallel development works**: Plans 1,2,3,5 developed simultaneously
2. **Test early, test often**: Individual tool tests prevented integration issues
3. **Documentation first helps**: Clear specs → smooth implementation
4. **Synthetic data valuable**: WorldState snapshots enable pattern matching
5. **Real examples critical**: A3 vlog transcripts teach natural Dutch language

---

## Major Refactoring Events

### Manual Reprocessing (Nov 2024)
- Expanded opbouw-en-werking from 18→163 pages
- Moved old versions to archive_output/
- Increased total chunks from ~300 to 689
- **Impact**: Much richer content, better coverage

### Telemetry Rebase (Nov 12, 2025)
- Shifted all timestamps +639 days forward
- Oct 2022→Jul 2024, Apr 2024→Jan 2026
- Updated all tools for dynamic timestamp handling
- **Impact**: Data appears "current" for demos

---

## Problems Solved

### Problem 1: No Fast-Path for Status Queries
**Date**: Nov 12, 2025 (identified, not yet solved)
- Status queries took 2-3 minutes (diagnostic tools)
- **Design**: get_current_status tool with pre-seeded cache
- **Documented**: Yes (QUICK_STATUS_IMPLEMENTATION.md)
- **Implemented**: No (still pending)

### Problem 2: Diagram Search Returns 0
**Date**: Nov 12, 2025 (identified)
- 9 diagrams in Weaviate but tool doesn't find them
- **Root Cause**: Unknown (needs investigation)
- **Status**: Open issue

### Problem 3: Missing Pandas Dependency
**Date**: Nov 11, 2024  
**Solved**: Installed pandas 2.3.3 + pyarrow 22.0.0
- WorldState tests failed with ModuleNotFoundError
- Added to project dependencies

### Problem 4: Model Name Double-Prefixing
**Date**: Nov 11, 2024  
**Solved**: Changed COMPLEX_PROVIDER from `google` to `gemini`
- Created invalid `google/gemini/gemini-2.5-pro`
- **Fix**: Use `COMPLEX_PROVIDER=gemini` + `COMPLEX_MODEL=gemini-2.5-pro`
- Elysia concatenates to `gemini/gemini-2.5-pro` (routes to Google AI Studio)

### Problem 5: Opgave Content in Production Queries
**Date**: Nov 11, 2024  
**Solved**: Flag + filter pattern
- 9 test/exercise sections mixed with real content
- Flagged with `content_type="opgave"`
- Default queries filter out with `not_equal("opgave")`
- Kept in Weaviate for prompt engineering

---

## Milestones

| Date | Milestone | Deliverables |
|------|-----------|--------------|
| **Nov 11, 2024** | Phase 1 Complete | 221 objects in Weaviate, 6 collections |
| **Nov 11, 2024** | Phase 2 Complete | 7 tools, 9 SMIDO branches, all tests pass |
| **Nov 12, 2025** | Logging System | Clean terminal, file-based audit trail |
| **Nov 12, 2025** | Config Verified | Both LLM models working correctly |
| **Nov 12, 2025** | Testing Review | Identified 8 issues for Phase 3 |
| **Nov 12, 2025** | Info Flow Diagram | Documented fast-path gap |

---

## Team Contributions

### Data Preparation
- Landing AI: PDF parsing (3 manuals)
- Gemini 2.5 Pro: Video processing (15 vlogs)
- Claude Agent: Data analysis, enrichment, classification

### Implementation
- Claude Agent: Phase 1 & 2 complete implementation
  - 7 tools, SMIDO tree, bootstrap system
  - Context manager, orchestrator
  - All documentation

### Testing
- Claude Agent: All test scripts, validation, A3 end-to-end

---

## Evolution of Understanding

### Initial Assumptions (Oct 2024)
- SMIDO has "3 P's" → **WRONG** (actually 4!)
- Need RawTelemetryWindows collection → **WRONG** (parquet more efficient)
- Diagrams need separate collection → **RIGHT** (VSM_Diagram created)
- Vlogs might be difficult to process → **WRONG** (Gemini handled perfectly)

### Refined Understanding (Nov 2024)
- 4 P's essential (Power, Settings, Parameters, Input)
- Hybrid storage better than Weaviate-only
- "Uit balans" is THE core concept (system imbalance vs broken components)
- A3 frozen evaporator has perfect data alignment

### Current Understanding (Nov 2025)
- Fast-path needed for status queries (learned from user testing)
- Intent detection critical (status vs diagnosis different paths)
- Performance matters (2-3 min too slow for status check)
- Diagram search needs debugging (implementation gap found)
- I phase transition needs improvement (UX issue discovered)

---

## Technology Evolution

### Oct 2024: Framework Selection
- Evaluated: LangChain, AutoGen, Custom
- **Selected**: Elysia
- **Reasons**: Decision tree structure, Weaviate integration, tool extensibility

### Nov 2024: Data Stack Finalized
- Weaviate v4 (semantic search)
- Pandas + Parquet (time-series)
- DSPy (LLM orchestration)
- Gemini 2.5 Pro (video processing, complex reasoning)
- Gemini 2.5 Flash (decision agent)

### Nov 2025: System Architecture Matured
- Bootstrap system for dynamic loading
- Three-zone time handling (PAST/PRESENT/FUTURE)
- Dual-handler logging
- Session-based caching

---

## Lessons from Each Phase

### Phase 1: Data Upload
**What Worked**:
- Parallel processing (diagrams, manuals, telemetry, vlogs)
- Pattern-based classification (fast, effective for 689 chunks)
- Synthetic data strategy (snapshots + commissioning)

**What Didn't**:
- First version of opbouw manual too small (needed reprocessing)
- Initial timestamp approach too rigid (needed dynamic handling)

**Key Learning**: "Perfect is the enemy of good" - iterate on data quality

### Phase 2: Agent & Tools
**What Worked**:
- Parallel development (4 plans simultaneously)
- Test-driven (individual tool tests before integration)
- Bootstrap system (clean separation of framework vs feature)

**What Didn't**:
- Initial prompts too task-focused (needed conversational examples)
- Forgot to implement get_current_status (documented but missed)
- Diagram search logic has bug (still investigating)

**Key Learning**: Test with real users early - found UX issues immediately

### Phase 3: UX & Polish (In Progress)
**What's Working**:
- Fast engine architecture (synthetic today, caching)
- Intent detection strategy (status vs diagnosis)
- Documentation comprehensive

**What's Not**:
- Fast-path not implemented yet
- Performance optimization pending
- Diagram search broken

**Key Learning**: "Fast engine ≠ fast UX" - need fast API layer too

---

## Abandoned Approaches

### 1. All Data in Weaviate
**Why Abandoned**: 785K telemetry rows too large, inefficient for time-series
**Replaced With**: Hybrid (Weaviate for events, parquet for raw data)

### 2. LLM-Based Classification for All Chunks
**Why Abandoned**: Too expensive, too slow for 689 chunks
**Replaced With**: Pattern matching + keyword detection (fast, effective)

### 3. Separate WorldState Collection
**Why Abandoned**: On-demand computation more flexible than pre-computed
**Replaced With**: WorldState engine computing on-the-fly from parquet

### 4. Complex Multi-Collection Schema with Extensive Cross-Links
**Why Abandoned**: Over-engineering for MVP
**Replaced With**: Simpler schemas with strategic cross-references

---

## Version History

### v0.1 (Oct 2024)
- Initial setup, data acquisition
- Elysia integration
- Basic collection schemas (FD_Assets, FD_Alarms, FD_Cases)

### v0.5 (Nov 11, 2024) - "Phase 1 Complete"
- 221 objects in Weaviate
- 6 VSM collections uploaded
- Complete data processing pipeline

### v1.0 (Nov 11, 2024) - "Phase 2 Complete"
- 7 VSM tools implemented
- SMIDO tree with 9 branches
- All tests passing
- Bootstrap system working
- A3 end-to-end validation

### v1.1 (Nov 12, 2025) - "Logging & Config"
- Dual-handler logging
- Model verification
- Telemetry rebase (current through 2026)

### v1.2 (Nov 12, 2025 - Current) - "Phase 3 In Progress"
- User testing completed
- Fast-path gap identified
- Performance issues documented
- Diagram search issue found

---

## Future Roadmap (Planned)

### Phase 3: UX & Performance (1-2 weeks)
- Implement get_current_status tool
- Fix diagram search
- Optimize get_asset_health (<10s)
- Optimize compute_worldstate (<15s)
- Fix I phase looping

### Phase 4: Production Features (2-3 weeks)
- Additional scenarios (A1, A2, A5)
- Service report generation
- Performance monitoring dashboard
- Session replay functionality

### Phase 5: Advanced Features (Future)
- Predictive maintenance (forecast failures)
- Multi-asset support
- Custom commissioning data import
- Mobile technician interface
- Offline mode support

---

## Timeline Summary

```
Oct 2024        Framework selection, data acquisition
Nov 2024        Data cleaning, vlog processing
Nov 11, 2024    Phase 1 complete (data upload)
                Phase 2 complete (tools & tree)
Nov 12, 2025    Logging improvements, config fixes
                User testing, gap discovery
                Phase 3 started (UX & performance)
Dec 2025        (Planned) Phase 3 completion
Q1 2026         (Planned) Production deployment
```

---

## Metrics Over Time

| Metric | Oct 2024 | Nov 11, 2024 | Nov 12, 2025 |
|--------|----------|--------------|--------------|
| Weaviate Objects | 0 | 221 | 221 |
| Custom Tools | 0 | 7 | 7 |
| SMIDO Branches | 0 | 9 | 9 |
| Tests Passing | N/A | 18/18 (Plan 1) | All Plans 1-7 |
| A3 Detection | N/A | ✅ | ✅ |
| Response Time | N/A | ~3 min | ~3 min (diagn) |
| Terminal Lines/min | ~1000 | ~1000 | ~5 (cleaned) |
| Documentation Pages | ~10 | ~80 | ~90+ |

---

## Acknowledgments

- **Elysia Team**: Excellent framework, great documentation
- **Weaviate**: Reliable vector database, clean v4 API
- **Landing AI**: High-quality PDF parsing
- **Google Gemini**: Excellent video processing capabilities
- **DSPy Team**: Solid LLM framework

---

**Last Updated**: November 12, 2025  
**Project Phase**: 3 of 5 (UX & Performance Optimization)  
**Completion**: 85%

