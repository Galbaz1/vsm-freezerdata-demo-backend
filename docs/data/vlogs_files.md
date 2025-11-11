# Vlogs (Video Logs) Overview

## Summary

This document catalogs the service engineer video logs (vlogs) - short training videos showing problem-to-solution workflows for cooling system troubleshooting.

## Video Files

### Location
`features/vlogs_vsm/`

### Available Videos

| Filename | Size | Case | Status |
|----------|------|------|--------|
| A1_1.mov | 2.0 MB | Condenser fan failure | ✅ Processed |
| A1_2.mov | 2.1 MB | Condenser fan failure | ✅ Processed |
| A1_3.mov | 1.6 MB | Condenser fan failure | ✅ Processed |
| A2_1.mov | 1.4 MB | Expansion valve defect | ✅ Processed |
| A2_2.mov | 1.5 MB | Expansion valve defect | ✅ Processed |
| A2_3.mov | 1.4 MB | Expansion valve defect | ✅ Processed |
| A3_1.mov | 1.7 MB | Frozen evaporator | ✅ Processed |
| A3_2.mov | 1.4 MB | Frozen evaporator | ✅ Processed |
| A3_3.mov | 1.0 MB | Frozen evaporator | ✅ Processed |
| A4_1.mov | 1.4 MB | Controller parameters | ✅ Processed |
| A4_2.mov | 1.6 MB | Controller parameters | ✅ Processed |
| A4_3.mov | 1.3 MB | Controller parameters | ✅ Processed |
| A5_1.mov | 1.2 MB | Liquid line blockage | ✅ Processed |
| A5_2.mov | 1.4 MB | Liquid line blockage | ✅ Processed |
| A5_3.mov | 1.2 MB | Liquid line blockage | ✅ Processed |

**Total**: 15 video files, ~21.7 MB total, **ALL PROCESSED** ✅

### Naming Convention and Confirmed Structure

Pattern: `A{X}_{Y}.mov`
- **X** (1-5): Case identifier (different problem scenarios)
- **Y** (1-3): Clip number within case (workflow progression)

**Confirmed**: Each A{X} series represents one complete troubleshooting case split into 3 clips:
- **A1** = Condenser fan failure (pressostaat + electrical connection)
- **A2** = Expansion valve defect (TXV blockage)
- **A3** = Frozen evaporator (defrost cycle issue) ⭐ Matches manual case!
- **A4** = Controller parameter issue (incorrect settings)
- **A5** = Liquid line blockage (filter drier saturation)

---

## Processing Infrastructure

### Scripts

#### 1. `process_vlogs.py`
Located: `features/vlogs_vsm/src/process_vlogs.py`

**Purpose**: Process video files using Gemini 2.5 Pro with video understanding

**Features**:
- Uploads .mov files to Gemini Files API
- Uses structured output (Pydantic schema) for consistent extraction
- Extracts:
  - Problem-triage-solution workflow steps with timestamps
  - Installation type and context
  - Root cause analysis
  - Technical tags for RAG retrieval
  - Components involved

**Usage**:
```bash
export GEMINI_API_KEY="your-key"
python src/process_vlogs.py features/vlogs_vsm --out output/cooling_clips_annotations.jsonl
```

#### 2. `notes_to_process_vlogs.md`
Documentation explaining the Gemini 2.5 Pro approach and schema design

---

## Processed Annotations

### Location
`features/vlogs_vsm/output/vlogs_vsm_annotations.jsonl`

### Current Status ✅ COMPLETE
- **Processed**: 15 videos (ALL)
- **Case aggregations**: 5 case_set records
- **Total records**: 20 (15 clips + 5 cases)
- **Processing date**: November 11, 2024

### Output Format

The JSONL file contains two types of records:
1. **Clip records** (15): Individual video annotations with transcript, steps, components
2. **Case set records** (5): Aggregated case summaries combining all 3 clips per case

**Detailed analysis**: See [vlogs_processing_results.md](vlogs_processing_results.md)

---

## Video Content Analysis (All Cases)

### Language
**Dutch (nl)** - All videos are in Dutch with Dutch transcripts

### Installation Types
- Koelcel installatie (cooling cell installation) - training setups
- Compacte koelunit (compact cooling unit)
- Koelcel testopstelling (cooling cell test setup)

### Problem-Triage-Solution Structure

**General pattern across 3 clips per case**:

1. **Clip 1**: Problem identification + initial triage
   - Problem statement and symptoms
   - Visual inspection
   - Initial diagnosis

2. **Clip 2**: Detailed triage + solution implementation
   - Component testing
   - Root cause confirmation
   - Repair/replacement

3. **Clip 3**: Verification and/or educational context
   - Additional diagnostic checks
   - Preventive maintenance tips
   - System verification

### All 5 Cases Summary

| Case | Problem | Root Cause | Solution |
|------|---------|------------|----------|
| **A1** | Te hoge temperatuur | Pressostaat + electrical fault | Reset pressostaat, replace connection |
| **A2** | Onvoldoende koeling | TXV defect/blocked | Replace expansion valve |
| **A3** | Koelcel te warm | Defrost cycle malfunction | Manual defrost + thermostaat calibrate |
| **A4** | Onvoldoende koeling | Incorrect controller parameters | Reset to factory settings |
| **A5** | Foutmelding, geen koeling | Liquid line blockage | Clean line + replace filter drier |

**Full details**: See [vlogs_processing_results.md](vlogs_processing_results.md)

---

## Video Characteristics

### Technical Quality
- **Format**: QuickTime Movie (.mov)
- **Size**: 1-2 MB per clip (highly compressed)
- **Duration**: Estimated 10-30 seconds each (short clips)
- **Content**: Training demonstrations, likely shot on mobile/handheld

### Content Type
- **Demonstration videos**: Service technician demonstrating troubleshooting
- **Real equipment**: Actual cooling installations (training setups)
- **Narration**: Dutch voiceover explaining steps
- **Visual**: Shows equipment, measurements, physical checks

### Target Audience
Junior cooling/refrigeration technicians learning troubleshooting workflows

---

## Confirmed Coverage ✅

All 5 scenarios processed with complete problem-triage-solution workflows:

| Case | Problem Type | Components | SMIDO Steps Demonstrated |
|------|-------------|------------|--------------------------|
| **A1** | Condenser fan failure | Condenser, fan, pressostaat, electrical | M, T, D (3P), O |
| **A2** | Expansion valve defect | TXV, evaporator | M, T, D (3P), O |
| **A3** | Frozen evaporator ⭐ | Evaporator, defrost, thermostaat | M, T, D (3P), O |
| **A4** | Controller parameters | Controller, thermostaat | M, T, **D (3P-Settings)**, O |
| **A5** | Liquid line blockage | Filter drier, liquid line, sight glass | M, T, D (3P), O |

⭐ **A3 matches the "Ingevroren verdamper" case from the manual!**

---

## Integration with SMIDO

**Confirmed mapping** from processed vlogs:

| Vlog Phase | SMIDO Steps | Demonstrated in Cases |
|------------|-------------|-----------------------|
| **Problem** | Melding (M) | All cases (A1-A5) |
| **Problem/Triage** | Technisch (T) | All cases (A1-A5) |
| **Triage** | Installatie Vertrouwd (I) | Implied in all cases |
| **Triage** | 3 P's (D) | A1 (Power), A2-A5 (Parameters), **A4 (Settings)** |
| **Triage/Solution** | Ketens & Onderdelen (O) | All cases (A1-A5) |

**Special note**: A4 is an excellent example of **3P - Procesinstellingen** (Process Settings)!

---

## Next Steps for VSM Demo

### Immediate (High Priority)

1. ✅ All vlogs processed (15 videos + 5 case aggregations)
2. ⏳ **Enrich vlog metadata**:
   - Map to controlled SMIDO step vocabulary
   - Map to controlled failure mode vocabulary
   - Link to telemetry sensor patterns
   - Add difficulty ratings

3. ⏳ **Create Weaviate ServiceVlogs collection**:
   - Implement schema from [vlogs_structure.md](vlogs_structure.md)
   - Ingest enriched records
   - Test retrieval queries

4. ⏳ **Link vlogs to manuals**:
   - A3 vlog ↔ "Ingevroren verdamper" manual section
   - Component-specific vlogs ↔ component manual sections

### Medium-term (Demo Enhancement)

1. Extract key frames at problem/diagnosis/solution moments
2. Create thumbnail images for each case
3. Add English translations of case summaries
4. Create vlog-to-telemetry pattern mappings

### Long-term (Production)

1. Process additional vlog sets as they become available
2. Track which vlogs users find most helpful (analytics)
3. Create quiz/learning checks based on vlog content
4. Fine-tune embeddings on vlog transcripts
