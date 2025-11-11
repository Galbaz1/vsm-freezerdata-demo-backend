# Manual Files Overview

## Summary

This document catalogs all parsed manual files found in the repository. The manuals are technical training materials from ROVC (Dutch cooling technology training organization) and have been parsed using Landing AI.

**Status**: Manuals were reprocessed in November 2024. Current production versions are in `production_output/`, previous versions are archived in `archive_output/`.

## Current Production Manuals

| Manual Name | Dutch Title | English Translation | Pages | Text Chunks | Visual Chunks | Version | Location |
|-------------|-------------|---------------------|-------|-------------|---------------|---------|----------|
| `storingzoeken-koeltechniek_theorie_179` | Storingzoeken koeltechniek | Troubleshooting cooling technology | 29 | 79 | 11 | 20 maart 2018 | `production_output/` |
| `koelinstallaties-inspectie-en-onderhoud_theorie_168` | Koelinstallaties inspectie en onderhoud | Cooling installations inspection and maintenance | 61 | 188 | 43 | 20 maart 2018 | `production_output/` |
| `koelinstallaties-opbouw-en-werking_theorie_2016` | Koelinstallaties opbouw en werking | Cooling installations structure and operation | 163 | 422 | 179 | 7 januari 2021 | `production_output/` |

**Total (Production)**: 3 manuals, 253 pages, 689 text chunks, 233 visual chunks

---

## Archived Manuals (Previous Versions)

Previous versions of the manuals are stored in `features/extraction/archive_output/` for reference:

| Manual Name | Pages | Text Chunks | Visual Chunks | Status |
|-------------|-------|-------------|---------------|--------|
| `storingzoeken-koeltechniek_theorie` | 29 | 74 | 9 | Archived (superseded by `_179`) |
| `koelinstallaties-inspectie-en-onderhoud_theorie` | 61 | 188 | 41 | Archived (superseded by `_168`) |
| `koelinstallaties-opbouw-en-werking_theorie` | 18 | 38 | 15 | Archived (superseded by `_2016`) |

**Total (Archived)**: 3 manuals, 108 pages, 300 text chunks, 65 visual chunks

### Changes Summary

| Manual | Pages Change | Text Chunks Change | Visual Chunks Change | Notes |
|--------|--------------|-------------------|---------------------|-------|
| storingzoeken | 29 → 29 (no change) | 74 → 79 (+5) | 9 → 11 (+2) | Minor improvements |
| inspectie-en-onderhoud | 61 → 61 (no change) | 188 → 188 (no change) | 41 → 43 (+2) | Minor improvements |
| opbouw-en-werking | **18 → 163 (+145)** | **38 → 422 (+384)** | **15 → 179 (+164)** | **Significantly expanded** |

**Overall**: 108 → 253 pages (+145), 300 → 689 text chunks (+389), 65 → 233 visual chunks (+168)

---

## File Formats Available

For each manual, the following file formats are available in `features/extraction/production_output/{manual_name}/`:

### 1. `.meta.json` - Metadata
- Document ID
- Source filename
- Page count
- Title
- Version/date
- Languages (Dutch/English)

### 2. `.parsed.json` - Complete parsed document
- Full markdown text
- Array of all chunks (text + visual)
- Batch processing info
- **Structure**:
  ```json
  {
    "markdown": "...",      // Full document as markdown
    "chunks": [...],         // Array of all chunks
    "batch_info": null/[...] // Processing metadata
  }
  ```

### 3. `.parsed.md` - Markdown version
- Human-readable markdown format
- All text and image descriptions
- Includes anchor IDs for chunks
- Best for quick inspection

### 4. `.text_chunks.jsonl` - Text chunks only
- One JSON object per line
- Each chunk has:
  - `chunk_id`: Unique UUID
  - `chunk_type`: "text"
  - `page`: Page number (0-indexed)
  - `markdown`: Chunk content
  - `bbox`: Bounding box coordinates
  - `source_pdf`: Original PDF path
  - `language`: Detected language

### 5. `.visual_chunks.jsonl` - Visual/image chunks only
- One JSON object per line
- Similar structure to text chunks
- `chunk_type`: "visual" or "figure"
- Contains image descriptions

### 6. `.pages.jsonl` - Page-level data
- One page per line
- Full page content and metadata

### 7. `.qa.json` - Q&A format (if available)
- Question-answer pairs extracted from content
- Currently mostly empty/placeholder

---

## Directory Structure

### Production Output (Current)

```
features/extraction/production_output/
├── storingzoeken-koeltechniek_theorie_179/
│   ├── storingzoeken-koeltechniek_theorie_179/        [subdirectory with assets]
│   ├── storingzoeken-koeltechniek_theorie_179.meta.json
│   ├── storingzoeken-koeltechniek_theorie_179.parsed.json
│   ├── storingzoeken-koeltechniek_theorie_179.parsed.md
│   ├── storingzoeken-koeltechniek_theorie_179.pages.jsonl
│   ├── storingzoeken-koeltechniek_theorie_179.text_chunks.jsonl
│   ├── storingzoeken-koeltechniek_theorie_179.visual_chunks.jsonl
│   └── storingzoeken-koeltechniek_theorie_179.qa.json
├── koelinstallaties-inspectie-en-onderhoud_theorie_168/
│   └── [same file structure]
└── koelinstallaties-opbouw-en-werking_theorie_2016/
    └── [same file structure]
```

### Archive Output (Previous Versions)

```
features/extraction/archive_output/
├── storingzoeken-koeltechniek_theorie/        [old version, archived]
├── koelinstallaties-inspectie-en-onderhoud_theorie/  [old version, archived]
└── koelinstallaties-opbouw-en-werking_theorie/       [old version, archived]
```

**Note**: The archive folder contains the previous versions of the manuals that were replaced during reprocessing in November 2024. These are kept for reference but should not be used for new development.

---

## File Sizes

### storingzoeken-koeltechniek_theorie_179 (Troubleshooting)
- `.parsed.json`: ~120 KB (estimated)
- `.parsed.md`: ~40 KB (estimated)
- `.text_chunks.jsonl`: ~65 KB (79 chunks)
- `.visual_chunks.jsonl`: ~12 KB (11 chunks)
- `.pages.jsonl`: ~45 KB (29 pages)

### koelinstallaties-inspectie-en-onderhoud_theorie_168 (Inspection & Maintenance)
- `.parsed.json`: ~320 KB (estimated)
- `.parsed.md`: ~110 KB (estimated)
- `.text_chunks.jsonl`: ~165 KB (188 chunks)
- `.visual_chunks.jsonl`: ~46 KB (43 chunks)
- `.pages.jsonl`: ~125 KB (61 pages)

### koelinstallaties-opbouw-en-werking_theorie_2016 (Structure & Operation)
- `.parsed.json`: ~500 KB (estimated, 163 pages)
- `.parsed.md`: ~200 KB (estimated)
- `.text_chunks.jsonl`: ~350 KB (422 chunks)
- `.visual_chunks.jsonl`: ~150 KB (179 chunks)
- `.pages.jsonl`: ~200 KB (163 pages)

**Note**: The opbouw-en-werking manual was significantly expanded from 18 to 163 pages in the reprocessed version, resulting in a much larger number of chunks (from 53 to 601 total).

---

## Content Overview by Manual

### 1. Troubleshooting Cooling Technology (`storingzoeken-koeltechniek_theorie_179`)

**Focus**: Systematic troubleshooting methodology for cooling installations

**Key sections**:
- Chapter 1: Gestructureerde aanpak storingzoeken (Structured troubleshooting approach)
  - SMIDO methodology explanation
  - The cooling process out of balance
  - Case studies (e.g., "Too warm in the train")
- Chapter 2: Veelvoorkomende storingen (Common failures)
  - Troubleshooting tables
  - StoringzoekApp (Troubleshooting app)

**Relevance**: **PRIMARY** manual for VSM demo - contains the SMIDO methodology

### 2. Cooling Installations Inspection & Maintenance (`koelinstallaties-inspectie-en-onderhoud_theorie_168`)

**Focus**: Inspection, maintenance, and repair procedures

**Size**: Largest manual (61 pages)

**Key content**:
- Preparation and safety procedures
- Component inspection protocols
- Maintenance schedules
- Repair procedures
- Refrigerant handling

**Relevance**: **SECONDARY** - useful for component-specific maintenance knowledge

### 3. Cooling Installations Structure & Operation (`koelinstallaties-opbouw-en-werking_theorie_2016`)

**Focus**: Fundamentals of cooling system design and operation

**Size**: **163 pages** (significantly expanded from previous 18-page version)

**Key content**:
- Refrigeration cycle basics
- Component descriptions (compressor, evaporator, condenser, expansion valve)
- System configurations
- Operating principles
- Extensive technical diagrams and illustrations (179 visual chunks)

**Relevance**: **TERTIARY** - foundational knowledge, useful for understanding system behavior

**Note**: This manual was reprocessed and expanded significantly. The new version contains 422 text chunks and 179 visual chunks (compared to 38 and 15 in the previous version), making it the largest manual by chunk count.

---

## Languages

All manuals are bilingual:
- **Primary language**: Dutch (Nederlands)
- **Secondary language**: English (some sections)

For the VSM demo, we should prioritize Dutch content as it's the primary language and matches the sensor naming convention.

---

## Quality Notes

1. **Parsing quality**: Generally excellent
   - Text extraction is clean and well-structured
   - Image descriptions are detailed (marked with `<::...: figure::>`)
   - Tables are captured (though formatting may need adjustment)

2. **Chunk anchors**: Each chunk has a unique ID anchor (`<a id='...'></a>`)
   - Useful for referencing specific sections
   - Can be used for chunk-level retrieval

3. **Visual content**:
   - Photos, diagrams, flowcharts are described textually
   - Original images may be in subdirectories (to verify)

4. **Metadata**: Consistent across all files
   - Source PDF paths are preserved
   - Page numbers are 0-indexed
   - Bounding boxes available for spatial queries

---

## Recommended Processing Strategy

For Weaviate ingestion:

1. **Use `.text_chunks.jsonl`** as the primary data source
   - Already chunked at logical boundaries
   - Easier to process line-by-line
   - Each chunk is self-contained with metadata

2. **Supplement with visual_chunks.jsonl** for diagrams/flowcharts
   - Important for SMIDO flowchart
   - Component diagrams
   - Troubleshooting decision trees

3. **Use `.parsed.md`** for context/validation
   - Human-readable format
   - Useful for manual inspection

4. **Parse `.meta.json`** for document-level metadata
   - Link chunks back to source document
   - Version tracking
   - Language filtering
