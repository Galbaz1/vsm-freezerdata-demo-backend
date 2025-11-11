# Manual Structure Analysis

## Overview

This document provides a detailed analysis of how the parsed manual content is structured, with focus on identifying logical sections for the `ManualSections` Weaviate collection.

---

## File Structure

### Chunk Object Schema

Each chunk in `.text_chunks.jsonl` and `.visual_chunks.jsonl` has the following structure:

```json
{
  "chunk_id": "11cdb058-316e-44ba-a0fb-1903707c51e2",
  "chunk_type": "text" | "visual",
  "page": 0,
  "markdown": "...",
  "bbox": {
    "x": float,
    "y": float,
    "width": float,
    "height": float
  },
  "source_pdf": "/path/to/original.pdf",
  "asset_path": null | "path/to/image.png",
  "text_summary": null | "...",
  "language": "nl" | "en"
}
```

### Parsed JSON Schema

The `.parsed.json` files have:

```json
{
  "markdown": "Full document as markdown string",
  "chunks": [
    { /* chunk objects */ }
  ],
  "batch_info": null | [ /* processing metadata */ ]
}
```

---

## Content Structure Analysis

### 1. Troubleshooting Manual (`storingzoeken-koeltechniek_theorie`)

#### Document Outline (from Table of Contents)

**Chapter 1: Gestructureerde aanpak storingzoeken** (Structured troubleshooting approach)
- Inleiding (Introduction) - page 7
- De SMIDO-methodiek - page 8
  - Aanvalsplan (Attack plan / flowchart)
  - Toelichting stappen (Step explanation):
    - Melding (Report)
    - Technisch (Technical)
    - Installatie vertrouwd (Installation familiar)
    - 3 P's (Power, Process settings, Process parameters, Product input)
    - Ketens en onderdelen uitsluiten (Chains & components)
- Het koelproces uit balans (The cooling process out of balance) - page 12
- Bijlagen (Appendices) - page 14
- Theorie opgaven (Theory assignments) - page 15
- **Case 1: Te warm in de trein** (Too warm in the train) - page 16
- Werkplekopdracht: Storingsregistratie (Workplace assignment: Fault registration) - page 19
- Storingsregistratie (Fault registration form) - page 20

**Chapter 2: Veelvoorkomende storingen** (Common failures)
- Inleiding (Introduction) - page 23
- Storingstabel (Troubleshooting table) - page 24
- StoringzoekApp (Troubleshooting app) - page 26
- Bijlagen (Appendices) - page 27
- Theorie opgaven (Theory assignments) - page 28
- **Case 2: Mobiele inkoel-/invriescel** (Mobile cooling/freezing cell)

#### Key Content Types Identified

1. **Methodological explanations** (SMIDO steps)
2. **Flowcharts** (SMIDO attack plan)
3. **Tables** (Troubleshooting/diagnostic tables)
4. **Case studies** (Real-world examples)
5. **Photos** (Equipment, failures like frozen evaporators)
6. **Definitions and concepts** (Cooling process imbalance)

#### Identifiable SMIDO Sections

The manual explicitly covers each SMIDO step:

| SMIDO Step | Dutch Term | Page/Section | Content Type |
|------------|------------|--------------|--------------|
| **M** - Melding | Melding | ~page 8 | Explanation, checklist questions |
| **T** - Technisch | Technisch | ~page 8-9 | Explanation, quick checks |
| **I** - Installatie | Installatie vertrouwd | ~page 9 | Familiarity checklist |
| **D** - Diagnose | De 3 P's | ~page 9-10 | Power, Process settings, Process parameters, Product input |
| **O** - Onderdelen | Ketens en onderdelen uitsluiten | ~page 10 | Chain/component isolation |

---

### 2. Inspection & Maintenance Manual (`koelinstallaties-inspectie-en-onderhoud_theorie`)

**Size**: 61 pages, 188 text chunks, 41 visual chunks

**Structure**: (Need to examine table of contents - likely includes)
- Safety procedures
- Component-specific maintenance
- Inspection checklists
- Refrigerant handling
- Tools and equipment
- Regulatory compliance

**Content Types**:
- **Procedural steps** (maintenance procedures)
- **Safety warnings** (highlighted sections)
- **Component diagrams** (exploded views, parts)
- **Checklists** (inspection points)
- **Tables** (maintenance schedules, specifications)

**Relevance to SMIDO**: Primarily supports **Ketens & Onderdelen** (chains & components) phase

---

### 3. Structure & Operation Manual (`koelinstallaties-opbouw-en-werking_theorie`)

**Size**: 18 pages, 38 text chunks, 15 visual chunks

**Structure**: (Likely includes)
- Refrigeration cycle fundamentals
- Component descriptions:
  - Compressor
  - Condenser
  - Expansion valve
  - Evaporator
- System types (direct/indirect, single/multi-stage)
- P-H diagrams (pressure-enthalpy)

**Content Types**:
- **Diagrams** (cycle diagrams, P-H charts)
- **Component illustrations** (cutaway views)
- **Theoretical explanations** (thermodynamics)
- **System schematics** (piping & instrumentation diagrams)

**Relevance to SMIDO**: Foundational knowledge, supports **Installatie Vertrouwd** and **3 P's**

---

## Structural Patterns for Chunking

### Current Chunking (Landing AI)

Landing AI has already chunked the documents at logical boundaries:
- Paragraphs
- Headings
- Tables
- Images/figures
- Captions

**Chunk size**: Variable, typically 100-500 words per text chunk

### Proposed Logical Sections for ManualSections

To create meaningful `ManualSections` for Weaviate, we should **group related chunks** into coherent sections:

#### Grouping Strategy

1. **By heading hierarchy**:
   - Detect markdown headings (`#`, `##`, `###`)
   - Group chunks under each heading until next heading of same/higher level

2. **By content type**:
   - Explanatory text sections
   - Tables (keep entire table together)
   - Flowcharts (description + transcription)
   - Case studies (full case as one section)

3. **By SMIDO step** (for troubleshooting manual):
   - Explicitly tag sections with their SMIDO step
   - Example: "Melding" section → `smido_step: "melding"`

#### Example Section Boundaries

**Section 1: SMIDO Melding**
- **Chunks**: All chunks from "# Melding" heading through end of that subsection
- **Properties**:
  - `manual_id`: "storingzoeken-koeltechniek_theorie"
  - `section_id`: "smido_melding"
  - `title`: "Melding"
  - `body_text`: Combined text of all chunks
  - `page_range`: [8, 8]
  - `smido_step`: "melding"
  - `content_type`: "uitleg" (explanation)

**Section 2: SMIDO Flowchart**
- **Chunks**: Flowchart figure + transcription
- **Properties**:
  - `section_id`: "smido_flowchart"
  - `title`: "SMIDO-aanvalsplan"
  - `body_text`: Flowchart transcription
  - `smido_step`: "overzicht" (overview)
  - `content_type`: "flowchart"

**Section 3: Case Study - Te warm in de trein**
- **Chunks**: All chunks from case start to end
- **Properties**:
  - `section_id`: "case_te_warm_in_de_trein"
  - `title`: "Case 1: Te warm in de trein"
  - `body_text`: Full case description
  - `page_range`: [16, 18]
  - `failure_mode`: "te_hoge_temperatuur"
  - `content_type`: "voorbeeldcase"

---

## Headings and Section Markers

### Heading Detection

In markdown format, sections are marked by:
- `#` - Top-level section (chapter)
- `##` - Sub-section
- `###` - Sub-sub-section
- Bold text without `#` may also indicate subsections

### Example Heading Hierarchy

```
Hoofdstuk 1: Gestructureerde aanpak storingzoeken
  # Inleiding
  De SMIDO-methodiek
    ## Aanvalsplan
    # Toelichting stappen in aanvalsplan
    # Melding
    **Technisch**
    Installatie vertrouwd
    3-P's
    # Ketens en onderdelen uitsluiten
  Het koelproces uit balans
```

**Issue**: Inconsistent heading markers (some use `#`, some use `**bold**`)

**Solution**: Use heuristics to detect section boundaries:
- Explicit headings (`#`)
- Bold text at start of paragraph
- Page breaks (new page often = new section)
- Table of contents as reference

---

## Content Type Classification

Based on manual analysis, we can classify sections into these types:

| Content Type | Dutch | Description | Examples |
|--------------|-------|-------------|----------|
| `uitleg` | Uitleg | Explanatory text | SMIDO step descriptions |
| `stappenplan` | Stappenplan | Step-by-step procedure | Troubleshooting steps |
| `flowchart` | Stroomschema | Flowchart/decision tree | SMIDO attack plan |
| `tabel` | Tabel | Table | Diagnostic tables, specifications |
| `voorbeeldcase` | Voorbeeldcase | Case study/example | "Te warm in de trein" |
| `diagram` | Diagram | Technical diagram | P-H diagrams, cycle diagrams |
| `foto` | Foto | Photograph | Frozen evaporator photo |
| `schema` | Schema | Schematic | Piping diagrams |
| `checklist` | Checklist | Checklist | Inspection points |
| `definitie` | Definitie | Definition/concept | "Koelproces uit balans" |

### Detection Heuristics

- **Flowchart**: Contains `<::transcription of the content : flowchart::>`
- **Table**: Contains `<table id="...">` tags
- **Photo**: Contains `<::...description... : photo::>`
- **Diagram**: Contains `<::... : figure::>` with technical terms
- **Case study**: Title contains "Case" or starts with "Case N:"
- **Checklist**: Contains bullet points with checkable items
- **Definition**: Begins with bold term followed by explanation

---

## SMIDO Step Identification

### Manual Labeling Required

The SMIDO steps are **explicitly mentioned** in the troubleshooting manual, making them relatively easy to tag:

| SMIDO Step | Keywords to Detect | Section Indicators |
|------------|-------------------|-------------------|
| `melding` | "Melding", "rapport", "symptomen" | Questions about symptoms |
| `technisch` | "Technisch", "waarneembaar defect" | Direct observation checks |
| `installatie_vertrouwd` | "Installatie vertrouwd", "schema", "componenten kennen" | Familiarity questions |
| `3P_power` | "Power", "voeding", "spanning" | Voltage/power checks |
| `3P_procesinstellingen` | "Procesinstellingen", "parameters", "pressostaten" | Settings checks |
| `3P_procesparameters` | "Procesparameters", "drukken", "temperaturen", "metingen" | Measurement checks |
| `3P_productinput` | "Productinput", "condities", "belading" | Environmental checks |
| `ketens_onderdelen` | "Ketens", "onderdelen uitsluiten", "signaalgevers" | Component isolation |
| `koelproces_uit_balans` | "Koelproces uit balans", "verdamper", "condensor" | System imbalance |

### Semi-Automatic Labeling Strategy

1. **Use heading-based rules** for explicit SMIDO sections
2. **Use LLM classification** for ambiguous sections:
   ```
   Prompt: "Which SMIDO step(s) does this section primarily support?
   Options: melding, technisch, installatie_vertrouwd, 3P, ketens_onderdelen"
   ```
3. **Manual review** for edge cases

---

## Failure Mode Identification

### Explicit Failure Modes in Manuals

From the troubleshooting manual, identifiable failure modes include:

| Failure Mode | Dutch Term | Manual Reference | Description |
|--------------|------------|------------------|-------------|
| `te_hoge_temperatuur` | Te hoge temperatuur | Multiple sections | Room temperature too high |
| `ingevroren_verdamper` | Ingevroren verdamper | Photo on page ~7 | Evaporator covered in frost |
| `compressor_draait_niet` | Compressor draait niet | Troubleshooting table | Compressor not running |
| `hoge_druk` | Hoge druk | Troubleshooting table | High pressure fault |
| `lage_druk` | Lage druk | Troubleshooting table | Low pressure fault |
| `te_weinig_koudemiddel` | Te weinig koudemiddel | Troubleshooting table | Insufficient refrigerant |
| `vuile_condensor` | Vuile condensor | Maintenance manual | Dirty condenser |
| `slecht_ontdooien` | Slecht ontdooien | Troubleshooting | Poor defrost performance |

### Semi-Automatic Detection

Use LLM to classify sections:
```
Prompt: "What failure mode(s) does this section address?
Extract from: [te_hoge_temperatuur, ingevroren_verdamper, compressor_draait_niet, ...]"
```

---

## Component Identification

Cooling system components mentioned in manuals:

| Component | Dutch | English |
|-----------|-------|---------|
| `compressor` | Compressor | Compressor |
| `verdamper` | Verdamper | Evaporator |
| `condensor` | Condensor | Condenser |
| `expansieventiel` | Expansieventiel | Expansion valve |
| `ventilator` | Ventilator | Fan |
| `regelaar` | Regelaar | Controller |
| `magneetklep` | Magneetklep | Solenoid valve |
| `pressostaat` | Pressostaat | Pressure switch |
| `thermostat` | Thermostaat | Thermostat |
| `vloeistofvat` | Vloeistofvat | Liquid receiver |
| `filter_droger` | Filterdroger | Filter drier |
| `kijkglas` | Kijkglas | Sight glass |

### Detection: Use Named Entity Recognition or keyword matching

---

## Recommended Section Creation Workflow

### Step 1: Parse and Group Chunks

```python
def create_sections(chunks: List[dict]) -> List[Section]:
    sections = []
    current_section = None

    for chunk in chunks:
        if is_heading(chunk):
            # Save previous section
            if current_section:
                sections.append(current_section)
            # Start new section
            current_section = create_new_section(chunk)
        else:
            # Add chunk to current section
            current_section.add_chunk(chunk)

    return sections
```

### Step 2: Classify Sections

```python
def classify_section(section: Section) -> Section:
    # Detect content type
    section.content_type = detect_content_type(section.body_text)

    # Detect SMIDO step
    section.smido_step = detect_smido_step(section.title, section.body_text)

    # Detect failure modes
    section.failure_modes = detect_failure_modes(section.body_text)

    # Detect components
    section.components = detect_components(section.body_text)

    return section
```

### Step 3: Enrich with LLM

For ambiguous sections, use LLM:

```python
def llm_classify(section: Section) -> dict:
    prompt = f"""
    Classify this cooling technology manual section:

    Title: {section.title}
    Content: {section.body_text[:500]}...

    Return JSON:
    {{
      "smido_step": "melding|technisch|...",
      "failure_modes": ["te_hoge_temperatuur", ...],
      "components": ["compressor", ...],
      "content_type": "uitleg|stappenplan|..."
    }}
    """
    return call_llm(prompt)
```

---

## Estimated Section Counts

Based on chunk counts and structure:

| Manual | Estimated Sections | Reasoning |
|--------|-------------------|-----------|
| Troubleshooting | **30-40 sections** | ~3 chunks per section average |
| Inspection & Maintenance | **60-80 sections** | Larger, more detailed manual |
| Structure & Operation | **15-25 sections** | Smaller, focused manual |
| **Total** | **~110-140 sections** | For initial ingestion |

Each section would be a document in the `ManualSections` Weaviate collection.

---

## Next Steps

1. ✅ Document structure analysis (this document)
2. ⏳ Create section parsing script
3. ⏳ Implement content type detection
4. ⏳ Implement SMIDO step classification
5. ⏳ Design Weaviate schema
6. ⏳ Test with sample sections
