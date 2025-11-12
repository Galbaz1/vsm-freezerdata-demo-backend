# VSM Project - TODO List

**Last Updated**: November 12, 2025  
**Project Phase**: 3 of 5 (UX & Performance)  
**Completion**: 85%

---

## 🔴 CRITICAL (Must Fix for Production)

### 1. Implement Improved Branching Strategy (PRIMARY BLOCKER)
**Problem**: 
- Status queries take 2-3 minutes (no fast path)
- No native Elysia tools (query, aggregate, visualise)
- Deep SMIDO hierarchy inefficient
**Impact**: Poor UX, limited capabilities, doesn't follow Elysia best practices  
**Target**: Flat root + native tools + fast path

**Tasks**:
- [ ] Create `get_current_status` tool
  - Return cached/synthetic WorldState (<200ms)
  - 5 key sensors: room, hot_gas, suction, liquid, ambient
  - Active flags + health score
  - Clear description: "Quick status check - current temps, flags, health"
  - No run_if_true (let agent decide via description)
- [ ] Rewrite `vsm_smido_bootstrap()` in `features/vsm_tree/bootstrap.py`
  - Flat root pattern (Weaviate's one_branch style)
  - Add all tools at base: 7 VSM + 5 native
  - Use `from_tool_ids` for post-tool chains
  - Remove hierarchical SMIDO branch functions
- [ ] Add native tools to root:
  - Query (flexible Weaviate search)
  - Aggregate (statistics, counts)
  - Visualise (charts after data tools)
  - CitedSummarizer, FakeTextResponse (always)
- [ ] Write clear root instruction (no keyword detection)
  - Guide agent with tool purposes
  - Let LLM decide based on user intent
  - Example: "Choose tool that matches request - read descriptions carefully"
- [ ] Test all flows: status, query, SMIDO, visualize

**Reference**: `docs/IMPROVED_VSM_BRANCHING_STRATEGY.md` (archived after migration)

---

### 2. Fix Diagram Search in SearchManualsBySMIDO
**Problem**: Returns "0 related diagrams" despite 9 diagrams in Weaviate  
**Impact**: Users don't see visual aids (schemas, flowcharts)

**Tasks**:
- [ ] Investigate `search_manuals_by_smido` lines ~160-189 (diagram fetching logic)
- [ ] Verify VSM_Diagram objects have correct `smido_step` properties in Weaviate
- [ ] Test Filter.by_property("diagram_id") query directly
- [ ] Check if `related_diagram_ids` field is populated in VSM_ManualSections
- [ ] Add debug logging to diagram fetch logic
- [ ] Fix and re-test with SearchManuals queries

**File**: `elysia/api/custom_tools.py`

---

## 🟡 HIGH PRIORITY (Performance & UX)

### 3. Optimize get_asset_health Performance
**Current**: 20-30 seconds  
**Target**: <10 seconds

**Tasks**:
- [ ] Profile parquet read performance
  - Identify bottlenecks in WorldState computation
  - Consider column-only reads (not full dataframe)
- [ ] Implement session-level caching
  - Cache W in `tree_data.environment["worldstate"]`
  - Reuse if same timestamp requested
- [ ] Pre-compute health scores for common windows
  - 30min, 60min, 120min standard windows
  - Cache results within session
- [ ] Test with `scripts/test_plan4_tools.py`
- [ ] Verify 50%+ performance improvement

---

### 4. Optimize compute_worldstate Performance
**Current**: 30+ seconds for 785K rows  
**Target**: <15 seconds

**Tasks**:
- [ ] Profile feature computation bottlenecks
  - Time each of 58 features
  - Identify slowest computations
- [ ] Use pandas query optimization
  - Index on timestamp (if not already)
  - Pre-filter by asset_id
  - Use vectorized operations
- [ ] Implement caching in WorldStateEngine
  - Session-level cache (same timestamp → cached result)
  - Store in class attribute
- [ ] Test with `tests/requires_env/test_worldstate_engine.py`
- [ ] Verify P3 phase faster

---

### 5. Fix I Phase Repetitive Looping
**Problem**: Agent asks 3-4 times "Ben je bekend met dit systeem?"  
**Impact**: Poor UX, frustrating for users

**Tasks**:
- [ ] Add keyword detection in I branch instruction
  - Detect: "Ja, ik ken het systeem", "Ik heb het schema", "Ik zie de regelaar"
  - If user mentions specific components → assume familiar
- [ ] Improve I→D transition criteria
  - Single confirmation sufficient
  - Skip repetitive asking
- [ ] Test with interactive flow (not just scripts)

**File**: `features/vsm_tree/smido_tree.py` (I branch instruction, lines ~184-214)

---

### 6. Add Response Time Monitoring
**Goal**: Track tool performance in production

**Tasks**:
- [ ] Add timing wrapper to all tools in `elysia/api/custom_tools.py`
  - Start timer before work
  - Log duration after yield Result
- [ ] Log SMIDO phase transitions in tree execution
  - Log when entering M, T, I, D, O
  - Track time in each phase
- [ ] Add performance metrics format to `elysia/logs/`
  - Format: `[PERF] Tool: get_asset_health | Duration: 23.4s | Branch: smido_melding`
- [ ] Create performance monitoring dashboard (optional)

---

## 🟢 MEDIUM PRIORITY (Testing & Polish)

### 7. Complete Full SMIDO Cycle Testing
**Evidence**: User testing shows flows don't always reach O phase

**Tasks**:
- [ ] Test A3 end-to-end with all phases (M→T→I→D→O)
  - Verify all 4 P's execute
  - Verify O phase provides solution from vlogs
  - Verify agent generates complete workflow
- [ ] Test A1 condenser fan scenario
- [ ] Test edge cases (multiple failures, ambiguous symptoms)
- [ ] Test escalation logic (safety-critical scenarios)

**Scripts**: `scripts/test_plan7_full_tree.py` exists, expand coverage

---

### 8. UI Enhancements (Frontend)
**Note**: Frontend is separate repo, requires coordination

**Tasks**:
- [ ] Display real-time tool status (not just "Thinking...")
  - Tools already yield Status messages
  - Frontend should display these
- [ ] Add SMIDO phase progress indicator
  - Visual: M ✓ → T ✓ → I (current) → D → O
  - Show user where they are in troubleshooting flow
- [ ] Add response time metrics to conversation view
- [ ] Integrate diagram preview/display
  - Show Mermaid diagrams inline
  - Link to manual sections
- [ ] Add video clip playback for vlog references

---

### 9. Additional Scenario Testing
**Goal**: Validate beyond A3

**Tasks**:
- [ ] Test A1: Condenser fan failure
  - Pressostaat + electrical connection
  - P2 (Settings) + P4 (Condenser conditions)
- [ ] Test A2: Expansion valve blockage
  - TXV issues
  - P3 (Parameters)
- [ ] Test A5: Refrigerant leakage
  - Low refrigerant
  - P3 (Pressures) + Safety escalation
- [ ] Test edge case: Multiple simultaneous failures
- [ ] Test safety-critical: Koudemiddel lekkage (verify escalation)

---

### 10. Performance Profiling Suite
**Goal**: Establish baseline, identify bottlenecks

**Tasks**:
- [ ] Profile all 7 tools with Python profiler
  - Use cProfile or line_profiler
  - Identify hot spots
- [ ] Profile pandas operations in WorldStateEngine
  - Time parquet read vs computation
  - Optimize slowest features
- [ ] Monitor Weaviate query performance
  - Track query times for all collections
  - Identify slow queries
- [ ] Create benchmark baseline document
  - File: `docs/PERFORMANCE_BASELINE.md`
  - Track metrics over time

---

## 🔵 LOW PRIORITY (Future Features)

### 11. Service Report Generation
**Goal**: Auto-generate formatted troubleshooting reports

**Tasks**:
- [ ] Design report template (Dutch)
  - Symptomen, diagnose, oplossing, preventie
  - SMIDO steps performed
  - Time spent, next maintenance
- [ ] Implement report generator tool
- [ ] Add to O phase completion

---

### 12. Multi-Asset Support
**Current**: Single asset (135_1570)  
**Future**: Support multiple installations

**Tasks**:
- [ ] Extend parquet files to include asset_id column
- [ ] Update WorldStateEngine for multi-asset filtering
- [ ] Update all tools for asset_id parameter
- [ ] Test with multiple assets

---

### 13. Adaptive Prompting
**Goal**: Adjust tone based on technician experience

**Tasks**:
- [ ] Track technician experience level in user profile
- [ ] Adjust explanation depth dynamically
- [ ] Skip basic explanations for experienced techs
- [ ] Provide more detail for beginners

---

### 14. Predictive Maintenance
**Goal**: Forecast failures before they occur

**Tasks**:
- [ ] Analyze sensor trends for early warnings
- [ ] Identify patterns preceding failures
- [ ] Create prediction models
- [ ] Alert before problems occur

---

### 15. Mobile Interface
**Goal**: Support technicians on phones/tablets

**Tasks**:
- [ ] Mobile-responsive frontend
- [ ] Voice input support (Dutch)
- [ ] Photo upload for visual symptoms
- [ ] Offline mode (cached data)

---

## 🔧 Technical Debt

### Code Quality
- [ ] Add comprehensive error handling to all tools
- [ ] Remove hardcoded values (asset IDs, file paths)
- [ ] Add logging to all scripts
- [ ] Add type hints everywhere
- [ ] Add docstrings to all functions

### Testing
- [ ] Increase test coverage to >80%
- [ ] Add integration tests
- [ ] Add performance regression tests
- [ ] Add data quality tests

### Documentation
- [ ] Create deployment guide
- [ ] Create troubleshooting guide
- [ ] Update API documentation
- [ ] Add architecture decision records (ADRs)

---

## 📋 Immediate Next Steps (This Week)

**Priority Order**:
1. ✅ Read all .md files (completed)
2. ✅ Create 4 consolidated docs (in progress)
3. [ ] Implement get_current_status tool (1-2 days)
4. [ ] Fix diagram search bug (0.5-1 day)
5. [ ] Profile and optimize get_asset_health (1 day)
6. [ ] Test full SMIDO cycle with A3 (0.5 day)

**Total**: 4-5 days to production-ready

---

## 🎯 Success Criteria (Production Ready)

**Must Have** (before production):
- [ ] get_current_status tool working (<200ms)
- [ ] Diagram search fixed (returns diagrams)
- [ ] get_asset_health optimized (<10s)
- [ ] Full A3 cycle tested (M→O complete)
- [ ] No critical UX issues (I phase fixed)

**Should Have** (for good demo):
- [ ] compute_worldstate optimized (<15s)
- [ ] Response times consistent <30s
- [ ] Tool status visible in frontend
- [ ] SMIDO progress indicator

**Nice to Have** (future):
- [ ] Additional scenarios tested (A1, A2, A5)
- [ ] Service report generation
- [ ] Performance monitoring dashboard

---

## 📊 Progress Tracking

### Phase 3: UX & Performance (Current)
**Started**: November 12, 2025  
**Target Completion**: December 2025

**Progress** (20% complete):
- [x] User testing completed
- [x] Issues identified and documented
- [x] Solutions designed
- [ ] get_current_status implemented
- [ ] Diagram search fixed
- [ ] Performance optimizations applied
- [ ] All issues resolved

**Remaining Work**: 4-5 days (1 developer)

---

### Phase 4: Production Features (Planned)
**Target Start**: January 2026  
**Tasks**:
- Additional scenarios
- Service reports
- Monitoring dashboard
- Multi-asset support

**Estimated**: 2-3 weeks

---

### Phase 5: Advanced Features (Future)
**Target Start**: Q1 2026  
**Tasks**:
- Predictive maintenance
- Mobile interface
- Offline mode
- Multi-language support

**Estimated**: 1-2 months

---

## 📁 Related Documents

- **Current Status**: PROJECT_STATUS.md
- **History**: PROJECT_HISTORY.md
- **Knowledge**: PROJECT_KNOWLEDGE.md
- **Comprehensive Guide**: CLAUDE.md

---

**Maintained By**: Development Team  
**Review Frequency**: Weekly during active development  
**Last Review**: November 12, 2025

