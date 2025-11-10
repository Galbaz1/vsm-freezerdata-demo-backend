# PDF Processing Pipeline

Enhanced PDF processing with intelligent batching for large technical manuals.

## Quick Start

```bash
# Process a PDF (auto-batches if >45MB or >45 pages)
python src/process_pdfs.py data/manual.pdf

# Test mode (first 20 pages)
python src/process_pdfs.py --pages 20 data/manual.pdf

# Custom output location
python src/process_pdfs.py --output-dir my_outputs data/manual.pdf
```

## Features

- ✅ **Intelligent batching**: Automatically splits large PDFs into 20-page batches
- ✅ **Global page numbering**: Seamless page tracking across batches
- ✅ **Multi-language support**: Detects NL and EN content
- ✅ **Visual asset extraction**: Crops figures with bounding boxes
- ✅ **Page-level artifacts**: Context Engineering-ready page records
- ✅ **Table text summaries**: Compact text from HTML tables for embeddings
- ✅ **Quality assurance**: Automatic QA checks and warnings
- ✅ **Full traceability**: Batch artifacts preserved for debugging

## Output Structure

```
outputs/{document}/
├── .batches/                     # Intermediate batch artifacts
│   ├── {doc}_batch_001-020.pdf
│   └── batch_001-020/
│       ├── parsed.json
│       └── parsed.md
├── {document}/
│   └── assets/                   # Visual crops (global page numbers)
│       ├── page-001/
│       │   └── chunk-{id}.png
│       └── page-020/
├── {document}.parsed.json        # Merged ADE response
├── {document}.parsed.md          # Merged markdown
├── {document}.text_chunks.jsonl  # Text/table chunks
├── {document}.visual_chunks.jsonl # Figure chunks
├── {document}.pages.jsonl        # Page-level artifacts
├── {document}.meta.json          # Metadata + batch info
└── {document}.qa.json            # QA summary
```

## Requirements

```bash
pip install landingai-ade pypdfium2 Pillow langdetect
```

## Environment

Set your LandingAI API key:

```bash
export VISION_AGENT_API_KEY='your-api-key'
```

## Examples

### Process Large PDF

```bash
# Automatically batches if >45MB or >45 pages
python src/process_pdfs.py data/koelinstallaties-opbouw-en-werking_theorie.pdf
```

Output:
```
📦 Large PDF detected - splitting into batches...
  Created batch: ..._batch_001-020.pdf (pages 1-20)
  Created batch: ..._batch_021-040.pdf (pages 21-40)
  ...
  Processing batch: pages 1-20...
  ✓ Batch complete: 72 chunks
  ...
✅ Processing complete
  Pages: 171
  Batches: 9
```

### Test Mode

```bash
# Process only first 20 pages (still uses batching if needed)
python src/process_pdfs.py --pages 20 data/large_manual.pdf
```

### Multiple Files

```bash
# Process all PDFs in data folder
python src/process_pdfs.py data/*.pdf
```

### Advanced Options

```bash
# EU environment
python src/process_pdfs.py --env eu data/manual.pdf

# High-DPI assets
python src/process_pdfs.py --asset-dpi 300 data/manual.pdf

# Disable batching (force single-pass, may fail on large files)
python src/process_pdfs.py --no-batching data/small_manual.pdf
```

## Output Files Explained

### Text Chunks (`*.text_chunks.jsonl`)

Each line is a JSON record:

```json
{
  "chunk_id": "uuid",
  "chunk_type": "text" | "table",
  "page": 5,
  "markdown": "Original markdown with <a> tags",
  "bbox": {"left": 0.1, "top": 0.2, "right": 0.9, "bottom": 0.8},
  "source_pdf": "/path/to/source.pdf",
  "text_summary": "Compact text for embeddings (tables only)",
  "language": "nl" | "en" | null
}
```

### Visual Chunks (`*.visual_chunks.jsonl`)

Similar to text chunks but with `asset_path`:

```json
{
  "chunk_id": "uuid",
  "chunk_type": "figure",
  "page": 7,
  "markdown": "Figure description from ADE",
  "bbox": {...},
  "asset_path": "doc/assets/page-007/chunk-{id}.png",
  "language": "en"
}
```

### Page Artifacts (`*.pages.jsonl`)

One record per page:

```json
{
  "doc_id": "manual",
  "pdf_page_index": 5,
  "printed_page_number": "6",
  "chunk_ids": ["id1", "id2", ...],
  "table_ids": ["table_id"],
  "figure_ids": ["fig_id1", "fig_id2"],
  "languages": ["nl", "en"],
  "page_text": "Concatenated text (anchors removed)",
  "page_summary": ""
}
```

### Metadata (`*.meta.json`)

Document-level info:

```json
{
  "doc_id": "manual",
  "filename": "manual.pdf",
  "source_pdf": "/path/to/manual.pdf",
  "page_count": 171,
  "title": "Koelinstallaties",
  "version": "7 januari 2021",
  "languages": ["nl", "en"],
  "batches": [
    {"start": 0, "end": 19, "batch_file": "..._batch_001-020.pdf"},
    ...
  ]
}
```

### QA Summary (`*.qa.json`)

Quality checks:

```json
{
  "total_pages": 171,
  "total_chunks": 850,
  "text_chunks": 450,
  "table_chunks": 25,
  "figure_chunks": 200,
  "marginalia_chunks": 175,
  "visual_crops_saved": 200,
  "pages_with_content": 169,
  "warnings": []
}
```

## Troubleshooting

### PDF Too Large Error

If you get `PDF size should be less than 50MB` error:

- Batching should handle this automatically
- Ensure you're not using `--no-batching`
- The script uses 45MB threshold for safety

### Missing API Key

```bash
export VISION_AGENT_API_KEY='your-key-here'
```

### Rate Limiting

If you hit rate limits, the script will fail on that file and continue with others. Process files one at a time or add delays.

## Next Steps

These artifacts are ready for:

1. **Vector Indexing**: Load `*_chunks.jsonl` into Weaviate
2. **Retrieval API**: Implement search and `load_pages()` functions
3. **Agent Integration**: Expose as tools with proper citations

See `plan.md` for full implementation details.

## References

- **LandingAI ADE**: https://docs.landing.ai/ade/
- **Context Engineering**: `../docs/context_engineering/`
- **RAG Best Practices**: `../docs/rag/`

