# VSM Agent: Data Access Clarity Analysis
**Date**: Nov 12, 2025  
**Issue**: Agent unclear about data sources and what to ask user

---

## 🔴 Critical Finding: **Poor Data Access Clarity**

### Current State

**Agent description says** (smido_tree.py line 48):
```
Toegang tot: sensordata (real-time + historisch), manuals, schemas, eerdere cases
```

**Problem**: This was **too vague** and created confusion about:
1. What data is automatically available vs must be requested
2. Whether sensordata is LIVE or historical (it's parquet file!)
3. What parameters are needed (asset_id, timestamp, etc.)
4. What the user (mechanic) should provide

**✅ FIXED**: Now explicitly lists data sources and what to ask user (Nov 12, 2025)

---

## Gap Analysis

### ❌ What Agent DOESN'T Know

| Topic | Current Knowledge | What's Missing |
|-------|------------------|----------------|
| **Asset ID** | None | Must ask user or defaults to "135_1570" |
| **Data Source** | "sensordata (real-time + historisch)" | Actually: **785K rows parquet file**, not live sensors! |
| **Time Range** | None | Data from March 2024, can query any timestamp |
| **Sensor Coverage** | None | 5 key temps + compressor + 58 computed features |
| **Manual Scope** | "manuals, schemas" | 167 sections, 3 manuals, 16 diagrams, SMIDO-tagged |
| **Vlog Cases** | "eerdere cases" | 5 cases (A1-A5), 15 clips, frozen evaporator specialty |
| **User Context** | None | Should ask: problem symptom, urgency, customer name |

### ✅ What Agent DOES Know (Physical Limitations)

```
Je bent afhankelijk van de monteur voor: 
visuele inspectie, handmatige acties, klantcontact, en veiligheidscontroles ter plaatse.
```

This is **good** - agent knows what to ask mechanic to observe/do physically.

---

## Real-World Scenario (Current Behavior)

### User: "De koelcel is te warm"

**What agent SHOULD do**:
1. ✅ Ask: "Wat is de huidige celtemperatuur?" (physical observation)
2. ✅ Ask: "Welk installatie nummer?" (asset_id for data lookup)
3. ✅ Use: get_current_status(asset_id) to see sensor data
4. ❌ **PROBLEM**: Agent doesn't know it has historical data to compare!

**What agent MIGHT do** (confused):
1. ❓ Think "real-time sensordata" means live MQTT feed
2. ❓ Not realize it can query historical patterns
3. ❓ Ask user for sensor readings manually (inefficient!)

---

## Recommended Agent Description Enhancement

### Current (Line 48):
```
Toegang tot: sensordata (real-time + historisch), manuals, schemas, eerdere cases
```

### Improved:
```
Je hebt toegang tot de volgende databronnen (via tools):

**Sensordata (installatie 135_1570)**:
- 785.000 metingen van maart 2024 (1-minuut interval)
- 5 temperaturen: ruimte, heetgas, zuigleiding, vloeistof, omgeving
- Compressor status, drukken, on/off cycli
- 58 berekende kenmerken (trends, stabiliteit, balans scores)
- GEEN live data - historische analyse voor troubleshooting

**Kennisbank**:
- 167 manual secties (3 handboeken, SMIDO-getagd)
- 16 schema's/diagrammen (Mermaid flowcharts)
- 5 vlog cases (A1-A5: frozen evaporator, high temp, etc.)
- 12 historische "uit balans" events (patterns, severity)

**Wat je MOET vragen aan de monteur**:
- Actuele symptomen: "Wat zie/hoor/ruik je nu?"
- Klantinformatie: "Sinds wanneer? Hoe urgent?"
- Visuele waarnemingen: "Zie je ijs? Lekt er iets?"
- Handmatige metingen: "Wat meet jouw manometer?"
- Veiligheidschecks: "Is de stroom er af? Koudemiddel rook?"

**Wat je NIET hoeft te vragen**:
- Historische sensordata (heb je al via tools)
- Installatiegegevens (in database als Context C)
- Eerdere storingsgeschiedenis (in vlog cases)
- Theoretische uitleg (in manuals)
```

---

## Tool Description Improvements

### 1. get_current_status (custom_tools.py line 596)

**Current**:
```python
"""Quick status check - current temps, flags, health.

Use when the user requests the current system status.
```

**Problem**: Says "current" but actually returns **synthetic/historical** data!

**Improved**:
```python
"""Quick status check - latest available sensor readings + health scores.

IMPORTANT: Data source is HISTORICAL (March 2024 parquet), NOT live sensors.
Returns synthetic "current" state based on typical A3 frozen evaporator scenario.

Use when:
- Mechanic asks "Wat is de status?" or "Hoe staat het ervoor?"
- Starting diagnosis (M phase) - need system overview
- Want quick health check before deep analysis

Returns:
- 5 key temperatures (room, hot-gas, suction, liquid, ambient)
- Active warning flags (_flag_main_temp_high, _flag_suction_extreme, etc.)
- 30-min trends (stijgend/stabiel/dalend)
- Health scores (cooling, compressor, stability)

NOTE: For historical pattern analysis, use compute_worldstate instead.
Response time: <100ms (cached/synthetic data)
"""
```

### 2. compute_worldstate (custom_tools.py line 667)

**Current**:
```python
"""Compute WorldState (W) - 58+ sensor features from telemetry parquet.
```

**Improved**:
```python
"""Compute WorldState (W) - 58+ sensor features from 785K historical measurements.

Data source: features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet
Time range: March 2024 (1-minute interval)
Sensor coverage: temps, pressures, compressor, flags

Use when:
- P3 (PROCESPARAMETERS): Need detailed sensor analysis
- P4 (PRODUCTINPUT): Check environmental trends
- Want to compare specific timestamp vs design parameters

Parameters:
- asset_id: "135_1570" (currently only available asset)
- timestamp: ISO format or "now" for synthetic current state
- window_minutes: Analysis window (default 60min)

Returns 58 features including:
- Current readings (5 temps, 2 pressures, compressor state)
- Trends (30min/60min slopes, change rates)
- Stability scores (variance, coefficient of variation)
- Health indicators (cooling_health, compressor_health, etc.)

Response time: <500ms
"""
```

### 3. search_manuals_by_smido (custom_tools.py line 64)

**Current**:
```python
"""Search manual sections filtered by SMIDO step, with optional diagram inclusion.
```

**Improved**:
```python
"""Search 167 manual sections from 3 refrigeration handbooks (SMIDO-tagged).

Content coverage:
- "Storingzoeken Koeltechniek" (troubleshooting methodology)
- "Koelinstallaties - Opbouw en Werking" (system design)
- "Inspectie en Onderhoud" (maintenance procedures)
- 16 diagrams (8 UserFacing + 8 AgentInternal Mermaid flowcharts)

Use when:
- Need procedure for specific SMIDO phase (M, T, I, P1-P4, O)
- Want diagram/flowchart for troubleshooting step
- Mechanic asks "Hoe moet ik X checken?"

Filters available:
- smido_step: melding, technisch, installatie_vertrouwd, 3P_power, etc.
- failure_mode: "ingevroren_verdamper", "te_hoge_temperatuur"
- component: "verdamper", "compressor", "pressostaat"

Returns:
- Manual sections (Dutch text, SMIDO methodology)
- Related diagrams (Mermaid code, auto-rendered in frontend)

NOTE: Automatically filters out test content (opgave) unless requested.
"""
```

---

## Root Instruction Enhancement

### Add Data Source Context

**Current** (bootstrap.py line 223):
```python
"""
Choose tool based on user's immediate need.
Decide based on tools available and their descriptions.
```

**Improved**:
```python
"""
You're guiding a junior mechanic through SMIDO troubleshooting (M→T→I→D→O).

**Data you have via tools** (don't ask user for this):
- Historical sensor data (785K measurements, March 2024)
- Manual sections (167), diagrams (16), vlog cases (5)
- Failure patterns, reference snapshots

**Data you MUST ask mechanic** (tools can't provide):
- Current physical observations ("Wat zie je nu?")
- Customer context ("Sinds wanneer? Hoe urgent?")
- Manual measurements ("Wat meet je manometer?")
- Safety confirmations ("Is stroom er af?")

Choose tools based on diagnosis phase:

**First contact (M - Melding)**:
- Ask: symptom, urgency, customer → store in context
- Use: get_current_status (overview), get_alarms (active warnings)

**After symptoms** → use appropriate tools for T/I/D/O phases
```

---

## Specific Gaps to Address

### 1. Asset ID Ambiguity

**Problem**: Tools default to `asset_id="135_1570"` but agent doesn't know this

**Fix Options**:

A. **Make it explicit in agent description** (recommended):
```
Je werkt met installatie 135_1570 (test dataset).
Als de monteur een ander nummer noemt, leg uit dat je alleen 135_1570 data hebt.
```

B. **Tool error messages clarify**:
```python
if asset_id != "135_1570":
    yield Error(f"Data alleen beschikbaar voor installatie 135_1570 (demo). Je vroeg: {asset_id}")
```

### 2. Time Range Confusion

**Problem**: "real-time + historisch" implies live data

**Fix**: Change to:
```
Sensordata (historisch archief, maart 2024):
- Voor troubleshooting training/analyse
- Geen live verbinding met installatie
- Monteur rapporteert actuele situatie, jij analyseert patronen
```

### 3. What to Ask User (M Phase)

**Problem**: Agent doesn't have checklist for initial contact

**Fix**: Add to agent description:
```
Bij eerste contact (M - Melding), vraag altijd:
1. "Wat is het symptoom?" (te warm, geluid, lekkage)
2. "Sinds wanneer merkt u dit?" (urgentie inschatten)
3. "Wat is de huidige celtemperatuur?" (actuele meting)
4. "Ziet u iets ongewoons?" (ijs, water, olie)

Daarna gebruik je tools om historische patronen te analyseren.
```

---

## Implementation Priority

### 🔴 CRITICAL (Do First)

1. **Clarify data is historical, not live** (smido_tree.py line 48)
   - Change "real-time" → "historisch archief (maart 2024)"
   - Add "GEEN live sensoren" warning
   - **Impact**: Prevents agent confusion about data freshness

2. **Add "What to Ask User" section** (smido_tree.py line 48)
   - List M-phase questions (symptom, urgency, observations)
   - **Impact**: Agent knows to gather context first

3. **Update get_current_status description** (custom_tools.py line 596)
   - Clarify it's synthetic/historical, not live
   - **Impact**: Prevents agent from misleading user

### 🟡 HIGH (Do Soon)

4. **Enhance tool descriptions with data sources** (custom_tools.py)
   - compute_worldstate: mention parquet file, 785K rows
   - search_manuals: list 3 manuals, 167 sections
   - query_vlog_cases: mention A1-A5 cases
   - **Impact**: Agent understands data scope

5. **Add asset_id clarification** (smido_tree.py)
   - "Je werkt met installatie 135_1570 (demo dataset)"
   - **Impact**: Prevents confusion if user mentions other IDs

### 🟢 MEDIUM (Nice to Have)

6. **Add root instruction data context** (bootstrap.py line 223)
   - Split "ask user" vs "use tools" clearly
   - **Impact**: Better decision-making on when to query vs ask

---

## Example Improved Agent Description

```python
agent_description="""Je bent een ervaren Virtual Service Mechanic (VSM) die een junior koelmonteur op locatie begeleidt via de SMIDO methodiek.

Je rol:
- Geduldig en educatief - de monteur is nog aan het leren
- Gebruik duidelijke Nederlandse technische termen (leg jargon uit waar nodig)
- Denk stap-voor-stap, spring niet naar conclusies
- Veiligheid eerst: koudemiddel, elektriciteit, bewegende delen

Je expertise:
- 5+ jaar ervaring met storingzoeken koelinstallaties
- Diepgaande kennis van "Koelproces uit balans" concept
- Getraind in SMIDO methodiek (M→T→I→D→O)

Je databronnen (via tools - HOEF JE NIET TE VRAGEN):
- Installatie 135_1570 (demo/training dataset)
- Sensordata: 785.000 metingen maart 2024 (historisch archief, GEEN live data)
  * 5 temperaturen, drukken, compressor status
  * 58 berekende kenmerken (trends, stabiliteit, health scores)
- Kennisbank: 167 manual secties, 16 schema's, 5 vlog cases (A1-A5)
- Historische "uit balans" events (12 getagde incidents)

Wat je WEL moet vragen aan de monteur:
- Actuele symptomen: "Wat zie/hoor/ruik je NU?" (jij hebt historische data, niet live)
- Klantinfo: "Sinds wanneer? Hoe urgent? Klant naam?"
- Visuele checks: "Zie je ijs op verdamper? Lekt er iets?"
- Handmatige metingen: "Wat meet je manometer?" (ter verificatie)
- Veiligheid: "Is de stroom eraf? Ruik je koudemiddel?"

Je bent op afstand - je hebt GEEN fysieke toegang.
Je analyseert historische patronen en begeleidt de monteur bij fysieke inspectie.

Bij eerste contact (M - Melding):
1. Vraag: symptoom, urgentie, visuele waarnemingen
2. Gebruik: get_current_status → overzicht sensor situatie
3. Gebruik: get_alarms → actieve waarschuwingen
4. Vergelijk: actuele waarneming vs historische patronen

[Rest of agent description: veiligheid, escalatie criteria...]
"""
```

---

## Summary

**Current State**: ❌ Agent has **vague knowledge** about data - thinks it's "real-time" when it's historical

**Risk**: Agent might:
- Ask user for data it already has (inefficient)
- Think data is live when it's from March 2024 (misleading)
- Not know when to use tools vs ask questions (confusion)

**Solution**: Add **explicit data source documentation** to agent description and tool descriptions

**Priority**: 🔴 **CRITICAL** - Implement items 1-3 immediately for clarity

**Impact**: Agent will clearly distinguish:
- ✅ Historical data (via tools)
- ✅ Current observations (ask mechanic)
- ✅ When to analyze vs when to ask

---

**Generated**: Nov 12, 2025  
**Status**: Ready for implementation

