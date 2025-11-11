# Manual Files Overview

## Summary

This document catalogs all parsed manual files found in the repository. The manuals are technical training materials from ROVC (Dutch cooling technology training organization) and have been parsed using Landing AI.

## Available Manuals

| Manual Name | Dutch Title | English Translation | Pages | Text Chunks | Visual Chunks | Version |
|-------------|-------------|---------------------|-------|-------------|---------------|---------|
| `storingzoeken-koeltechniek_theorie` | Storingzoeken koeltechniek | Troubleshooting cooling technology | 29 | 74 | 9 | 20 maart 2018 |
| `koelinstallaties-inspectie-en-onderhoud_theorie` | Koelinstallaties inspectie en onderhoud | Cooling installations inspection and maintenance | 61 | 188 | 41 | 20 maart 2018 |
| `koelinstallaties-opbouw-en-werking_theorie` | Koelinstallaties opbouw en werking | Cooling installations structure and operation | 18 | 38 | 15 | 7 januari 2021 |

**Total**: 3 manuals, 108 pages, 300 text chunks, 65 visual chunks

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

```
features/extraction/production_output/
├── storingzoeken-koeltechniek_theorie/
│   ├── storingzoeken-koeltechniek_theorie/        [subdirectory with assets]
│   ├── storingzoeken-koeltechniek_theorie.meta.json
│   ├── storingzoeken-koeltechniek_theorie.parsed.json
│   ├── storingzoeken-koeltechniek_theorie.parsed.md
│   ├── storingzoeken-koeltechniek_theorie.pages.jsonl
│   ├── storingzoeken-koeltechniek_theorie.text_chunks.jsonl
│   ├── storingzoeken-koeltechniek_theorie.visual_chunks.jsonl
│   └── storingzoeken-koeltechniek_theorie.qa.json
├── koelinstallaties-inspectie-en-onderhoud_theorie/
│   └── [same file structure]
└── koelinstallaties-opbouw-en-werking_theorie/
    └── [same file structure]
```

---

## File Sizes

### storingzoeken-koeltechniek_theorie (Troubleshooting)
- `.parsed.json`: 118 KB
- `.parsed.md`: 40 KB
- `.text_chunks.jsonl`: 63 KB
- `.visual_chunks.jsonl`: 11 KB
- `.pages.jsonl`: 45 KB

### koelinstallaties-inspectie-en-onderhoud_theorie (Inspection & Maintenance)
- `.parsed.json`: 315 KB (largest)
- `.parsed.md`: 106 KB
- `.text_chunks.jsonl`: 162 KB
- `.visual_chunks.jsonl`: 44 KB
- `.pages.jsonl`: 120 KB

### koelinstallaties-opbouw-en-werking_theorie (Structure & Operation)
- `.parsed.json`: 91 KB
- `.parsed.md`: 33 KB
- `.text_chunks.jsonl`: 32 KB
- `.visual_chunks.jsonl`: 24 KB
- `.pages.jsonl`: 37 KB

---

## Content Overview by Manual

### 1. Troubleshooting Cooling Technology (`storingzoeken-koeltechniek_theorie`)

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

### 2. Cooling Installations Inspection & Maintenance (`koelinstallaties-inspectie-en-onderhoud_theorie`)

**Focus**: Inspection, maintenance, and repair procedures

**Size**: Largest manual (61 pages)

**Key content**:
- Preparation and safety procedures
- Component inspection protocols
- Maintenance schedules
- Repair procedures
- Refrigerant handling

**Relevance**: **SECONDARY** - useful for component-specific maintenance knowledge

### 3. Cooling Installations Structure & Operation (`koelinstallaties-opbouw-en-werking_theorie`)

**Focus**: Fundamentals of cooling system design and operation

**Key content**:
- Refrigeration cycle basics
- Component descriptions (compressor, evaporator, condenser, expansion valve)
- System configurations
- Operating principles

**Relevance**: **TERTIARY** - foundational knowledge, useful for understanding system behavior

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
