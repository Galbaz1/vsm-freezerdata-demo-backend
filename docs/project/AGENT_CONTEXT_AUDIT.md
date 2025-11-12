# VSM Agent Context Audit
**Date**: Nov 12, 2025  
**Status**: Current State Analysis + Improvement Recommendations

---

## Executive Summary

**Overall Quality**: ⭐⭐⭐⭐ (4/5 - Very Good)

The VSM agent context is **well-designed** with clear persona, safety focus, and SMIDO integration. However, there are **opportunities for improvement** in tool descriptions, instruction clarity, and SMIDO workflow guidance.

---

## 1. Agent Description (smido_tree.py lines 35-64)

### ✅ Strengths

1. **Clear Persona**: "Ervaren VSM die junior begeleidt" - establishes expertise hierarchy
2. **Safety First**: Explicit safety warnings for refrigerant, electrical, pressure
3. **Remote Limitation**: Clearly states "GEEN fysieke toegang" - sets expectations
4. **Escalation Criteria**: Well-defined when to escalate (4 P's exhausted, safety risk, etc.)
5. **Educational Tone**: "Geduldig en educatief", "leg altijd waarom uit"

### ⚠️ Areas for Improvement

1. **SMIDO Integration**: Mentions "SMIDO methodiek" but doesn't explain the flow clearly
   - **Recommendation**: Add 1-2 sentences explaining M→T→I→D→O sequence
   
   ```
   Je volgt de SMIDO methodiek:
   M (Melding) → symptoom verzamelen
   T (Technisch) → snelle visuele inspectie  
   I (Installatie vertrouwd) → schema's bekijken
   D (Diagnose) → 4 P's systematisch checken (Power, Procesinstellingen, Procesparameters, Productinput)
   O (Onderdelen) → componenten uitsluiten
   ```

2. **Tool Mention**: Says "Toegang tot: sensordata, manuals, schemas" but doesn't mention **tools**
   - **Recommendation**: Add reference to available tools:
   
   ```
   Je beschikt over tools voor:
   - Realtime status checks (get_current_status)
   - Historische sensordata analyse (compute_worldstate)
   - Manual en schema's opzoeken (search_manuals_by_smido)
   - Vergelijkbare cases vinden (query_vlog_cases)
   ```

3. **"Uit balans" Concept**: Mentioned but not explained
   - **Recommendation**: Add 1 sentence:
   
   ```
   "Koelproces uit balans" betekent: systeem werkt buiten ontwerpparameters, niet per se kapotte onderdelen.
   ```

---

## 2. Style (smido_tree.py lines 65-68)

### ✅ Strengths

1. **Concise**: Clear communication guidelines
2. **Practical**: "Stel één vraag tegelijk (monteur moet rondlopen)" - very practical
3. **Educational**: "Leg technische concepten uit", "Prijs goede waarnemingen"

### ✅ No Changes Needed

This section is **perfect** as-is. Clear, actionable, appropriate for the use case.

---

## 3. End Goal (smido_tree.py lines 69-71)

### ✅ Strengths

1. **Two Outcomes**: Identifies OR escalates - realistic
2. **Understanding Focus**: "begrijpt het waarom" - emphasizes learning

### ⚠️ Minor Improvement

**Current**:
```
De monteur heeft de hoofdoorzaak geïdentificeerd en weet hoe de installatie te repareren.
```

**Recommendation**: Be more specific about SMIDO completion:
```
De monteur heeft via SMIDO de hoofdoorzaak geïdentificeerd en weet hoe te repareren.
Of: alle 4 P's zijn gechecked en je hebt escalatie aanbevolen met duidelijke diagnose tot nu toe.
```

---

## 4. Root Instruction (bootstrap.py lines 223-236)

### ✅ Strengths

1. **No Keyword Detection**: ✅ Follows best practice - trusts LLM to read descriptions
2. **Tool Grouping**: Groups tools by purpose (Quick checks, Deep analysis, etc.)
3. **Post-tool Hint**: "After a tool completes, more tools may become available"

### ⚠️ Areas for Improvement

1. **SMIDO Not Mentioned**: Instruction doesn't guide agent through SMIDO flow
   - **Current**: Generic "Choose tool based on user's immediate need"
   - **Problem**: Agent doesn't know it should follow M→T→I→D→O sequence
   
2. **No Flow Guidance**: Doesn't suggest when to use which tool category
   
3. **Missing Context**: Doesn't mention the VSM/junior mechanic scenario

### 💡 Recommended Improved Instruction

```python
tree.decision_nodes["base"].instruction = """
You're guiding a junior mechanic through SMIDO troubleshooting (M→T→I→D→O).
Choose tools based on where you are in the diagnosis, not keywords.

**First contact (M - Melding)**:
- get_current_status: Quick overview
- get_alarms: Check active warnings
- get_asset_health: Is system "uit balans"?

**After symptoms known**:
- search_manuals_by_smido: Find relevant procedures
- query_vlog_cases: Similar past cases
- compute_worldstate: Deep sensor analysis (P3/P4)
- analyze_sensor_pattern: Identify failure mode

**For statistics/visualization**:
- query, aggregate: Flexible data queries
- visualise: Charts (appears after data tools)

**Communication**:
- cited_summarize: Summarize findings
- text_response: End conversation

After each tool, consider what the mechanic needs next in the SMIDO flow.
"""
```

---

## 5. Tool Descriptions

### Analysis

| Tool | Current Quality | Issues | Priority |
|------|----------------|--------|----------|
| get_current_status | ⭐⭐⭐⭐⭐ | Perfect - clear, concise | None |
| get_alarms | ⭐⭐⭐⭐ | Good - could mention VSM_TelemetryEvent source | Low |
| get_asset_health | ⭐⭐⭐⭐⭐ | Perfect - explains "uit balans" check | None |
| compute_worldstate | ⭐⭐⭐⭐⭐ | Perfect - when to use, what it computes | None |
| analyze_sensor_pattern | ⭐⭐⭐⭐⭐ | Perfect - clear use case | None |
| search_manuals_by_smido | ⭐⭐⭐⭐ | Good - long but comprehensive | Low |
| query_vlog_cases | ⭐⭐⭐⭐⭐ | Perfect - "learn from past repairs" | None |
| query_telemetry_events | ⭐⭐⭐ | **Vague** - overlaps with get_alarms? | **MEDIUM** |

### 🔴 Issue: query_telemetry_events vs get_alarms Confusion

**Problem**: Both query VSM_TelemetryEvent, unclear when to use which

**Current Descriptions**:
- `get_alarms`: "Get active alarms for asset"
- `query_telemetry_events`: "Query historical telemetry events (similar incidents)"

**Recommendation**: Clarify the distinction

```python
# get_alarms - KEEP AS IS (clear)
"""Get active alarms for asset from VSM_TelemetryEvent collection."""

# query_telemetry_events - IMPROVE
"""Query historical "uit balans" incidents to find patterns.

Use when:
- You've identified a failure mode and want to see when it happened before
- Looking for temporal patterns (does this happen every night? weekend?)
- Comparing current incident to past similar events

Different from get_alarms:
- get_alarms: Current active alarms (what's wrong RIGHT NOW)
- query_telemetry_events: Historical incidents (when did this happen BEFORE)
"""
```

---

## 6. Missing Context

### What's Missing from Agent Knowledge

1. **No mention of preprocessing**: Agent doesn't know collections are preprocessed with Gemini 2.5 Pro
   - **Impact**: Low - internal detail
   - **Action**: None needed

2. **No collection list**: Agent doesn't explicitly know what collections exist
   - **Impact**: Low - tools abstract this
   - **Action**: None needed

3. **No SMIDO flow chart**: Agent has SMIDO knowledge but no visual reference
   - **Impact**: Medium - could help with sequencing
   - **Action**: Consider adding to agent_description or as a diagram tool result

---

## 7. Post-Tool Chain Logic

### Current State (bootstrap.py lines 173-186)

```python
# M flow: get_alarms → get_asset_health, search_manuals
# P3 flow: compute_worldstate → analyze_sensor_pattern
# O flow: query_vlog_cases → search_manuals, aggregate
```

### ✅ Strengths

1. **Smart Chaining**: Tools logically connected (alarms → health check)
2. **Cross-cutting**: Visualise available after any data tool

### ⚠️ Potential Improvement

**Add I flow** (currently missing):
- After `search_manuals_by_smido` with `smido_step=installatie_vertrouwd`
- → Offer `query` or `aggregate` to explore commissioning data (FD_Assets)

```python
# I flow: After manual schema review → offer data exploration
tree.add_tool(Query, branch_id="base", from_tool_ids=["search_manuals_by_smido"])
```

**Already exists!** Query is already chained from get_alarms. Recommend adding comment for clarity.

---

## 8. Language Consistency

### Current State

- **Agent prompts**: 🇳🇱 Dutch (correct for VSM persona)
- **Tool descriptions**: 🇬🇧 English (DSPy/Elysia standard)
- **Root instruction**: 🇬🇧 English (LLM-facing)

### ✅ Assessment

**This is CORRECT**. Keep as-is:
- Dutch for user-facing (mechanic communication)
- English for system/LLM (tool descriptions, instructions)

---

## Priority Recommendations

### 🔴 HIGH PRIORITY (Implement Now)

1. **Improve Root Instruction** (bootstrap.py line 223)
   - Add SMIDO flow context
   - Add when-to-use guidance
   - Mention VSM/mechanic scenario
   - **Estimated effort**: 10 minutes
   - **Impact**: Significantly better tool selection

2. **Clarify query_telemetry_events vs get_alarms** (custom_tools.py line 358)
   - Add distinction to docstring
   - **Estimated effort**: 5 minutes
   - **Impact**: Reduces tool confusion

### 🟡 MEDIUM PRIORITY (Consider)

3. **Enhance Agent Description with SMIDO Flow** (smido_tree.py line 35)
   - Add M→T→I→D→O explanation
   - Mention available tools
   - Explain "uit balans" concept
   - **Estimated effort**: 15 minutes
   - **Impact**: Better agent understanding of methodology

4. **Improve End Goal Specificity** (smido_tree.py line 69)
   - Mention SMIDO completion
   - Reference 4 P's explicitly
   - **Estimated effort**: 5 minutes
   - **Impact**: Clearer success criteria

### 🟢 LOW PRIORITY (Nice to Have)

5. **Add Collection Sources to Tool Descriptions**
   - Mention VSM_TelemetryEvent in get_alarms
   - Mention VSM_VlogCase in query_vlog_cases
   - **Estimated effort**: 5 minutes
   - **Impact**: Transparency (debugging aid)

---

## Summary Score Card

| Component | Score | Status |
|-----------|-------|--------|
| Agent Description | ⭐⭐⭐⭐ | Very Good - minor enhancements possible |
| Style | ⭐⭐⭐⭐⭐ | Perfect - no changes needed |
| End Goal | ⭐⭐⭐⭐ | Very Good - could be more specific |
| Root Instruction | ⭐⭐⭐ | Good - **needs SMIDO context** |
| Tool Descriptions | ⭐⭐⭐⭐ | Very Good - 1 clarification needed |
| Post-Tool Chains | ⭐⭐⭐⭐⭐ | Excellent - smart flow logic |
| Language Consistency | ⭐⭐⭐⭐⭐ | Perfect - Dutch/English separation |

**Overall**: ⭐⭐⭐⭐ (4/5) - **Strong foundation, targeted improvements recommended**

---

## Next Steps

1. Review this audit with stakeholders
2. Prioritize HIGH recommendations (root instruction + tool clarification)
3. Test improvements with A3 scenario (test_plan7)
4. Iterate based on real mechanic feedback

---

**Generated**: Nov 12, 2025  
**Reviewed by**: AI Analysis  
**Status**: Draft for review

