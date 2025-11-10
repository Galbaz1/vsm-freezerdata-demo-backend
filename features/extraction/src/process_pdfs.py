#!/usr/bin/env python3
"""Enhanced PDF processing pipeline with intelligent batching and enrichment.

Workflow:
1. Check PDF size/pages; split into batches if needed (>45MB or >45 pages)
2. Parse each batch with ADE (DPT-2) to obtain markdown, chunks, and grounding
3. Merge batch results with global page numbering
4. Extract visual assets (figures) with bounding boxes
5. Build page-level artifacts for Context Engineering
6. Generate document metadata and QA summary

Features:
- Intelligent batching for large PDFs (lossless splitting)
- Page number mapping (PDF index → printed page number)
- Multi-language detection (NL/EN)
- Table text summaries for embeddings
- Hierarchical output structure for traceability

Requirements:
    pip install landingai-ade pypdfium2 Pillow langdetect

Usage:
    # Process single file
    python process_pdfs.py manual.pdf
    
    # Process with batching (auto-detected)
    python process_pdfs.py --output-dir outputs large_manual.pdf
    
    # Test mode (first N pages only)
    python process_pdfs.py --pages 20 manual.pdf

References: 
    - LandingAI ADE: https://docs.landing.ai/ade/
    - Context Engineering: docs/context_engineering/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pypdfium2 as pdfium
from PIL import Image

from landingai_ade import LandingAIADE
from landingai_ade.types import ParseResponse

try:
    from langdetect import detect, LangDetectException
except ImportError:
    detect = None
    LangDetectException = Exception


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# PDF limits (with safety margin)
MAX_PDF_SIZE_MB = 45
MAX_PDF_PAGES = 45
BATCH_SIZE_PAGES = 10  # Reduced to keep batches under 50MB for API limit

VISUAL_CHUNK_TYPES = {"figure", "logo", "card", "attestation", "scan_code"}
TEXTUAL_CHUNK_TYPES = {"text", "table"}
MARGINALIA_TYPE = "marginalia"


def ensure_api_key() -> str:
    """Acquire API key from environment variable."""
    api_key = os.environ.get("VISION_AGENT_API_KEY")
    if not api_key:
        print(
            "Error: VISION_AGENT_API_KEY environment variable is not set",
            file=sys.stderr,
        )
        print("Set it with: export VISION_AGENT_API_KEY='your-api-key'", file=sys.stderr)
        sys.exit(1)
    return api_key


@dataclass
class ChunkRecord:
    """Normalized chunk record for JSONL export."""
    chunk_id: str
    chunk_type: str
    page: int
    markdown: str
    bbox: Dict[str, float]
    source_pdf: str
    asset_path: Optional[str] = None
    text_summary: Optional[str] = None  # For tables: compact text for embeddings
    language: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class PageRecord:
    """Page-level artifact for Context Engineering."""
    doc_id: str
    pdf_page_index: int
    printed_page_number: Optional[str]
    chunk_ids: List[str]
    table_ids: List[str]
    figure_ids: List[str]
    languages: List[str]
    page_text: str  # Concatenated non-marginalia markdown
    page_summary: str = ""  # Optional: 2-3 sentence summary

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass
class DocumentMetadata:
    """Document-level metadata."""
    doc_id: str
    filename: str
    source_pdf: str
    page_count: int
    title: Optional[str] = None
    version: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    batches: List[Dict[str, int]] = field(default_factory=list)  # For large PDFs


@dataclass
class QASummary:
    """Quality assurance summary."""
    total_pages: int
    total_chunks: int
    text_chunks: int
    table_chunks: int
    figure_chunks: int
    marginalia_chunks: int
    visual_crops_saved: int
    pages_with_content: int  # Pages with non-marginalia content
    warnings: List[str] = field(default_factory=list)


def get_pdf_info(pdf_path: Path) -> Tuple[int, float]:
    """Get page count and file size in MB."""
    doc = pdfium.PdfDocument(str(pdf_path))
    page_count = len(doc)
    file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
    return page_count, file_size_mb


def should_batch_pdf(pdf_path: Path) -> bool:
    """Check if PDF needs batching based on size/page limits."""
    page_count, file_size_mb = get_pdf_info(pdf_path)
    return file_size_mb > MAX_PDF_SIZE_MB or page_count > MAX_PDF_PAGES


def create_single_page_batches(pdf_path: Path, batch_dir: Path, stem: str, start_page: int, end_page: int) -> List[Tuple[Path, int, int]]:
    """Create single-page batches for a problematic page range."""
    doc = pdfium.PdfDocument(str(pdf_path))
    batches = []
    
    for page_idx in range(start_page, end_page + 1):
        batch_name = f"{stem}_batch_{page_idx+1:03d}-{page_idx+1:03d}.pdf"
        batch_path = batch_dir / batch_name
        
        if batch_path.exists():
            print(f"  Found existing single-page batch: {batch_name}")
        else:
            # Create single-page batch
            batch_doc = pdfium.PdfDocument.new()
            batch_doc.import_pages(doc, pages=[page_idx])
            batch_doc.save(str(batch_path))
            batch_size_mb = batch_path.stat().st_size / (1024 * 1024)
            print(f"  Created single-page batch: {batch_name} ({batch_size_mb:.1f}MB)")
        
        batches.append((batch_path, page_idx, page_idx))
    
    return batches


def split_pdf_into_batches(pdf_path: Path, output_dir: Path) -> List[Tuple[Path, int, int]]:
    """Split PDF into batches and return list of (batch_path, start_page, end_page).
    
    Checks for existing batch files first and uses adaptive batch sizing if needed.
    """
    doc = pdfium.PdfDocument(str(pdf_path))
    page_count = len(doc)
    
    batch_dir = output_dir / ".batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    stem = pdf_path.stem
    batches = []
    
    # First, check for any existing batch files (manual or previous runs)
    existing_batch_files = sorted(batch_dir.glob(f"{stem}_batch_*.pdf"))
    if existing_batch_files:
        print(f"  Found {len(existing_batch_files)} existing batch files")
        for batch_path in existing_batch_files:
            # Parse the batch filename to get page range
            name = batch_path.stem
            # Extract start-end from pattern like "Name_batch_001-010"
            parts = name.split("_batch_")[-1].split("-")
            if len(parts) == 2:
                start_page = int(parts[0]) - 1  # Convert to 0-indexed
                end_page = int(parts[1]) - 1    # Convert to 0-indexed (inclusive)
                batches.append((batch_path, start_page, end_page))
                batch_size_mb = batch_path.stat().st_size / (1024 * 1024)
                print(f"  Found existing batch: {batch_path.name} ({batch_size_mb:.1f}MB)")
        return batches
    
    # If no existing batches, create them with adaptive sizing
    for start_page in range(0, page_count, BATCH_SIZE_PAGES):
        end_page = min(start_page + BATCH_SIZE_PAGES, page_count)
        
        # Create batch PDF
        batch_name = f"{stem}_batch_{start_page+1:03d}-{end_page:03d}.pdf"
        batch_path = batch_dir / batch_name
        
        # Extract pages using pypdfium2 (lossless)
        batch_doc = pdfium.PdfDocument.new()
        for i in range(start_page, end_page):
            batch_doc.import_pages(doc, pages=[i])
        
        batch_doc.save(str(batch_path))
        
        # Check batch size and auto-split if too large
        batch_size_mb = batch_path.stat().st_size / (1024 * 1024)
        if batch_size_mb > MAX_PDF_SIZE_MB:
            print(f"  ⚠️  Batch {batch_name} is {batch_size_mb:.1f}MB (exceeds {MAX_PDF_SIZE_MB}MB)")
            print(f"  🔧 Auto-splitting into single-page batches...")
            # Delete the oversized batch
            batch_path.unlink()
            # Create single-page batches instead
            single_page_batches = create_single_page_batches(pdf_path, batch_dir, stem, start_page, end_page - 1)
            batches.extend(single_page_batches)
        else:
            print(f"  Created batch: {batch_name} ({batch_size_mb:.1f}MB)")
            batches.append((batch_path, start_page, end_page - 1))
    
    return batches


def parse_document(
    client: LandingAIADE,
    pdf_path: Path,
    model: str,
    page_limit: Optional[int],
    page_offset: int = 0
) -> ParseResponse:
    """Parse document with ADE and adjust page indices by offset."""
    response = client.parse(
        document_url=str(pdf_path),
        model=model,
        split="page",
    )

    if page_limit is not None:
        allowed_pages = set(range(page_limit))
        response.splits = [split for split in response.splits if any(p in allowed_pages for p in split.pages)]
        response.chunks = [chunk for chunk in response.chunks if chunk.grounding.page in allowed_pages]
    
    # Apply page offset for batched processing
    if page_offset > 0:
        for chunk in response.chunks:
            chunk.grounding.page += page_offset
        for split in response.splits:
            split.pages = [p + page_offset for p in split.pages]
    
    return response


def render_pages(pdf_path: Path, page_indices: Sequence[int], scale: float) -> Dict[int, Image.Image]:
    """Render specific pages at given scale."""
    doc = pdfium.PdfDocument(str(pdf_path))
    images: Dict[int, Image.Image] = {}
    for page_index in page_indices:
        if page_index < len(doc):
            page = doc.get_page(page_index)
            bitmap = page.render(scale=scale)
            images[page_index] = bitmap.to_pil()
    return images


def crop_chunk_image(image: Image.Image, bbox: Dict[str, float]) -> Image.Image:
    """Crop image using normalized bbox coordinates."""
    width, height = image.size
    left = max(0, min(width, int(round(bbox["left"] * width))))
    top = max(0, min(height, int(round(bbox["top"] * height))))
    right = max(0, min(width, int(round(bbox["right"] * width))))
    bottom = max(0, min(height, int(round(bbox["bottom"] * height))))
    if right <= left or bottom <= top:
        raise ValueError(f"Invalid crop bounds: {bbox}")
    return image.crop((left, top, right, bottom))


def sanitize_chunk_id(chunk_id: str) -> str:
    """Sanitize chunk ID for filesystem use."""
    return chunk_id.replace("/", "-").replace("\\", "-")


def strip_anchor_tags(markdown: str) -> str:
    """Remove anchor tags like <a id='...'> from markdown."""
    return re.sub(r'<a\s+id=["\'].*?["\']>', '', markdown)


def detect_language(text: str) -> Optional[str]:
    """Detect language of text chunk."""
    if not detect or len(text.strip()) < 20:
        return None
    try:
        lang = detect(text[:500])  # Use first 500 chars for detection
        return lang if lang in ['nl', 'en'] else None
    except (LangDetectException, Exception):
        return None


def extract_table_text_summary(html: str) -> str:
    """Extract compact text summary from HTML table for embeddings."""
    # Remove HTML tags and extract text
    text = re.sub(r'<[^>]+>', ' ', html)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Limit length
    return text[:1000] if len(text) > 1000 else text


def extract_printed_page_number(marginalia_text: str) -> Optional[str]:
    """Extract printed page number from marginalia text."""
    # Common patterns: "12", "Page 12", "Pagina 12", "12 / 150"
    patterns = [
        r'(?:page|pagina|p\.?)\s*(\d+)',
        r'^(\d+)\s*(?:/|\|)',
        r'^(\d+)$',
    ]
    for pattern in patterns:
        match = re.search(pattern, marginalia_text.strip(), re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def build_page_number_mapping(chunks: List) -> Dict[int, Optional[str]]:
    """Build mapping from PDF page index to printed page number."""
    mapping = {}
    for chunk in chunks:
        if chunk.type == MARGINALIA_TYPE:
            page_idx = chunk.grounding.page
            if page_idx not in mapping:
                printed_num = extract_printed_page_number(chunk.markdown)
                mapping[page_idx] = printed_num
    return mapping


def extract_document_title(response: ParseResponse) -> Optional[str]:
    """Extract document title from first pages."""
    # Look for H1 headings in first few pages
    for chunk in response.chunks[:20]:
        if chunk.type == "text":
            lines = chunk.markdown.split('\n')
            for line in lines:
                if line.startswith('# ') and len(line) > 3:
                    return line[2:].strip()
    return None


def extract_document_version(response: ParseResponse) -> Optional[str]:
    """Extract version information from first pages."""
    # Look for version patterns in first few pages
    patterns = [
        r'[Vv]ersie:?\s*(.+)',
        r'[Vv]ersion:?\s*(.+)',
        r'[Dd]atum:?\s*(\d{1,2}\s+\w+\s+\d{4})',
    ]
    for chunk in response.chunks[:30]:
        if chunk.type in ("text", MARGINALIA_TYPE):
            for pattern in patterns:
                match = re.search(pattern, chunk.markdown)
                if match:
                    return match.group(1).strip()
    return None


def is_already_processed(output_dir: Path, stem: str, page_limit: Optional[int]) -> bool:
    """Check if PDF has already been fully processed."""
    doc_output_dir = output_dir / stem
    
    # Required output files
    required_files = [
        doc_output_dir / f"{stem}.parsed.json",
        doc_output_dir / f"{stem}.text_chunks.jsonl",
        doc_output_dir / f"{stem}.meta.json",
    ]
    
    # Check if all required files exist
    if not all(f.exists() for f in required_files):
        return False
    
    # If page_limit is set, this is a partial run - don't skip
    if page_limit is not None:
        return False
    
    # Check metadata to see if it was a full or partial run
    meta_path = doc_output_dir / f"{stem}.meta.json"
    try:
        with open(meta_path) as f:
            meta = json.load(f)
            # If there's batch info but we're doing a full run, it's already done
            return True
    except (json.JSONDecodeError, KeyError):
        return False


def process_single_pdf(
    client: LandingAIADE,
    pdf_path: Path,
    output_dir: Path,
    model: str,
    page_limit: Optional[int],
    asset_dpi: int,
    use_batching: bool = False,
    skip_existing: bool = True
) -> None:
    """Process a single PDF through the complete pipeline."""
    stem = pdf_path.stem
    doc_output_dir = output_dir / stem
    
    # Check if already processed
    if skip_existing and is_already_processed(output_dir, stem, page_limit):
        print(f"\n{'='*60}")
        print(f"⏭️  Skipping: {pdf_path.name} (already processed)")
        print(f"{'='*60}")
        print(f"  Output exists at: {doc_output_dir}")
        return
    
    doc_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path.name}")
    print(f"{'='*60}")
    
    # Check if batching is needed (also for test mode if file is large)
    needs_batching = use_batching and should_batch_pdf(pdf_path)
    
    all_responses = []
    batch_info = []
    
    if needs_batching:
        print(f"📦 Large PDF detected - splitting into batches...")
        batches = split_pdf_into_batches(pdf_path, doc_output_dir)
        
        # If page_limit is set, only process batches up to that limit
        if page_limit:
            batches = [(p, s, e) for p, s, e in batches if s < page_limit]
            print(f"🧪 Test mode: limiting to first {page_limit} pages")
        
        for batch_path, start_page, end_page in batches:
            print(f"\n  Processing batch: pages {start_page+1}-{end_page+1}...")
            
            # Create batch output directory
            batch_dir = doc_output_dir / ".batches" / batch_path.stem
            batch_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if this batch has already been processed
            batch_parsed_json = batch_dir / "parsed.json"
            if batch_parsed_json.exists():
                print(f"  ⏭️  Skipping batch: already processed (using cached result)")
                # Load existing batch result
                with open(batch_parsed_json) as f:
                    import json as json_module
                    batch_data = json_module.load(f)
                    # Reconstruct response from saved data
                    from landingai_ade.types import ParseResponse
                    response = ParseResponse.model_validate(batch_data)
                
                all_responses.append(response)
                batch_info.append({"start": start_page, "end": end_page, "batch_file": batch_path.name})
                print(f"  ✓ Loaded cached batch: {len(response.chunks)} chunks")
                continue
            
            # Check batch file size before processing
            batch_size_mb = batch_path.stat().st_size / (1024 * 1024)
            if batch_size_mb > MAX_PDF_SIZE_MB:
                print(f"  ⚠️  WARNING: Batch size ({batch_size_mb:.1f}MB) exceeds API limit ({MAX_PDF_SIZE_MB}MB)")
                print(f"  ⚠️  This batch needs to be split further. Skipping to avoid API error.")
                print(f"  💡 TIP: Manually split pages {start_page+1}-{end_page+1} into smaller batches and re-run.")
                continue
            
            # Apply page limit to this batch if needed
            batch_page_limit = None
            if page_limit and end_page >= page_limit:
                batch_page_limit = page_limit - start_page
                print(f"  (limiting batch to {batch_page_limit} pages)")
            
            # Parse batch
            response = parse_document(client, batch_path, model, batch_page_limit, page_offset=start_page)
            
            # Save batch artifacts
            (batch_dir / "parsed.json").write_text(response.model_dump_json(indent=2), encoding="utf-8")
            (batch_dir / "parsed.md").write_text(response.markdown, encoding="utf-8")
            
            all_responses.append(response)
            batch_info.append({"start": start_page, "end": end_page, "batch_file": batch_path.name})
            
            print(f"  ✓ Batch complete: {len(response.chunks)} chunks")
    
    else:
        # Process entire PDF (or with page limit for testing)
        if page_limit:
            print(f"🧪 Test mode: processing first {page_limit} pages only")
        response = parse_document(client, pdf_path, model, page_limit, page_offset=0)
        all_responses.append(response)
    
    # Merge all responses
    print(f"\n📝 Merging results...")
    merged_chunks = []
    merged_markdown_parts = []
    
    for response in all_responses:
        merged_chunks.extend(response.chunks)
        merged_markdown_parts.append(response.markdown)
    
    merged_markdown = "\n\n".join(merged_markdown_parts)
    
    # Save merged artifacts
    merged_json_path = doc_output_dir / f"{stem}.parsed.json"
    merged_md_path = doc_output_dir / f"{stem}.parsed.md"
    
    # Create a synthetic merged response for JSON export
    merged_data = {
        "markdown": merged_markdown,
        "chunks": [chunk.model_dump() for chunk in merged_chunks],
        "batch_info": batch_info if batch_info else None,
    }
    merged_json_path.write_text(json.dumps(merged_data, indent=2, ensure_ascii=False), encoding="utf-8")
    merged_md_path.write_text(merged_markdown, encoding="utf-8")
    
    print(f"  ✓ Saved merged markdown: {merged_md_path}")
    print(f"  ✓ Saved merged JSON: {merged_json_path}")
    
    # Extract visual assets
    print(f"\n🖼️  Extracting visual assets...")
    visual_records, pages_needed = extract_visual_assets(
        pdf_path, merged_chunks, doc_output_dir, stem, asset_dpi
    )
    print(f"  ✓ Saved {len(visual_records)} visual crops")
    
    # Build chunk records
    print(f"\n📋 Building chunk records...")
    textual_records = []
    page_number_map = build_page_number_mapping(merged_chunks)
    
    for chunk in merged_chunks:
        if chunk.type in TEXTUAL_CHUNK_TYPES:
            bbox = {
                "left": chunk.grounding.box.left,
                "top": chunk.grounding.box.top,
                "right": chunk.grounding.box.right,
                "bottom": chunk.grounding.box.bottom,
            }
            
            # Strip anchors for clean text
            clean_markdown = strip_anchor_tags(chunk.markdown)
            
            # Generate table text summary if needed
            text_summary = None
            if chunk.type == "table":
                text_summary = extract_table_text_summary(chunk.markdown)
            
            # Detect language
            lang = detect_language(clean_markdown)
            
            record = ChunkRecord(
                chunk_id=chunk.id,
                chunk_type=chunk.type,
                page=chunk.grounding.page,
                markdown=chunk.markdown,  # Keep original with anchors
                bbox=bbox,
                source_pdf=str(pdf_path),
                text_summary=text_summary,
                language=lang,
            )
            textual_records.append(record)
    
    # Save chunk records
    text_records_path = doc_output_dir / f"{stem}.text_chunks.jsonl"
    visual_records_path = doc_output_dir / f"{stem}.visual_chunks.jsonl"
    
    save_records(textual_records, text_records_path)
    save_records(visual_records, visual_records_path)
    
    print(f"  ✓ Text chunks: {text_records_path} ({len(textual_records)} records)")
    print(f"  ✓ Visual chunks: {visual_records_path} ({len(visual_records)} records)")
    
    # Build page-level artifacts
    print(f"\n📄 Building page-level artifacts...")
    page_records = build_page_artifacts(merged_chunks, stem, page_number_map)
    pages_path = doc_output_dir / f"{stem}.pages.jsonl"
    save_records(page_records, pages_path)
    print(f"  ✓ Page artifacts: {pages_path} ({len(page_records)} pages)")
    
    # Extract document metadata
    print(f"\n📊 Extracting document metadata...")
    title = extract_document_title(all_responses[0])
    version = extract_document_version(all_responses[0])
    all_languages = list(set(r.language for r in textual_records if r.language))
    
    page_count = len(page_records)
    
    metadata = DocumentMetadata(
        doc_id=stem,
        filename=pdf_path.name,
        source_pdf=str(pdf_path),
        page_count=page_count,
        title=title,
        version=version,
        languages=sorted(all_languages),
        batches=batch_info if batch_info else [],
    )
    
    meta_path = doc_output_dir / f"{stem}.meta.json"
    meta_path.write_text(json.dumps(asdict(metadata), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ Metadata: {meta_path}")
    
    # Generate QA summary
    print(f"\n✅ Generating QA summary...")
    qa = generate_qa_summary(merged_chunks, visual_records, page_records)
    qa_path = doc_output_dir / f"{stem}.qa.json"
    qa_path.write_text(json.dumps(asdict(qa), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ QA summary: {qa_path}")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"✅ Processing complete: {stem}")
    print(f"{'='*60}")
    print(f"  Pages: {page_count}")
    print(f"  Text chunks: {qa.text_chunks}")
    print(f"  Table chunks: {qa.table_chunks}")
    print(f"  Figure chunks: {qa.figure_chunks}")
    print(f"  Visual crops: {qa.visual_crops_saved}")
    print(f"  Languages: {', '.join(all_languages) if all_languages else 'unknown'}")
    if title:
        print(f"  Title: {title}")
    if version:
        print(f"  Version: {version}")
    if batch_info:
        print(f"  Batches: {len(batch_info)}")
    print(f"  Output: {doc_output_dir}")


def extract_visual_assets(
    pdf_path: Path,
    chunks: List,
    output_dir: Path,
    stem: str,
    asset_dpi: int,
) -> Tuple[List[ChunkRecord], List[int]]:
    """Extract visual assets and return visual chunk records."""
    visual_records = []
    asset_root = output_dir / stem / "assets"
    asset_root.mkdir(parents=True, exist_ok=True)
    
    pages_needed = sorted({chunk.grounding.page for chunk in chunks 
                          if chunk.type in VISUAL_CHUNK_TYPES and chunk.grounding})
    
    if not pages_needed:
        return visual_records, pages_needed
    
    scale = asset_dpi / 72.0
    page_images = render_pages(pdf_path, pages_needed, scale=scale)
    
    for chunk in chunks:
        if chunk.type not in VISUAL_CHUNK_TYPES:
            continue
        
        bbox = {
            "left": chunk.grounding.box.left,
            "top": chunk.grounding.box.top,
            "right": chunk.grounding.box.right,
            "bottom": chunk.grounding.box.bottom,
        }
        
        page_image = page_images.get(chunk.grounding.page)
        if page_image is None:
            continue
        
        try:
            crop = crop_chunk_image(page_image, bbox)
        except ValueError:
            continue
        
        page_dir = asset_root / f"page-{chunk.grounding.page+1:03d}"
        page_dir.mkdir(parents=True, exist_ok=True)
        asset_path = page_dir / f"chunk-{sanitize_chunk_id(chunk.id)}.png"
        crop.save(asset_path, format="PNG")
        
        # Detect language in figure descriptions
        lang = detect_language(chunk.markdown)
        
        record = ChunkRecord(
            chunk_id=chunk.id,
            chunk_type=chunk.type,
            page=chunk.grounding.page,
            markdown=chunk.markdown,
            bbox=bbox,
            source_pdf=str(pdf_path),
            asset_path=str(asset_path.relative_to(output_dir)),
            language=lang,
        )
        visual_records.append(record)
    
    return visual_records, pages_needed


def build_page_artifacts(
    chunks: List,
    doc_id: str,
    page_number_map: Dict[int, Optional[str]]
) -> List[PageRecord]:
    """Build page-level artifacts for Context Engineering."""
    pages_data = defaultdict(lambda: {
        "chunk_ids": [],
        "table_ids": [],
        "figure_ids": [],
        "languages": set(),
        "text_parts": [],
    })
    
    for chunk in chunks:
        page_idx = chunk.grounding.page
        
        # Skip marginalia for page text
        if chunk.type == MARGINALIA_TYPE:
            continue
        
        pages_data[page_idx]["chunk_ids"].append(chunk.id)
        
        if chunk.type == "table":
            pages_data[page_idx]["table_ids"].append(chunk.id)
        elif chunk.type in VISUAL_CHUNK_TYPES:
            pages_data[page_idx]["figure_ids"].append(chunk.id)
        
        # Collect text (strip anchors)
        if chunk.type in TEXTUAL_CHUNK_TYPES or chunk.type in VISUAL_CHUNK_TYPES:
            clean_text = strip_anchor_tags(chunk.markdown)
            pages_data[page_idx]["text_parts"].append(clean_text)
            
            # Detect language
            lang = detect_language(clean_text)
            if lang:
                pages_data[page_idx]["languages"].add(lang)
    
    # Build page records
    page_records = []
    for page_idx in sorted(pages_data.keys()):
        data = pages_data[page_idx]
        page_text = "\n\n".join(data["text_parts"])
        
        record = PageRecord(
            doc_id=doc_id,
            pdf_page_index=page_idx,
            printed_page_number=page_number_map.get(page_idx),
            chunk_ids=data["chunk_ids"],
            table_ids=data["table_ids"],
            figure_ids=data["figure_ids"],
            languages=sorted(data["languages"]),
            page_text=page_text,
            page_summary="",  # Optional: implement later with LLM
        )
        page_records.append(record)
    
    return page_records


def generate_qa_summary(
    chunks: List,
    visual_records: List[ChunkRecord],
    page_records: List[PageRecord]
) -> QASummary:
    """Generate quality assurance summary."""
    chunk_type_counts = defaultdict(int)
    for chunk in chunks:
        chunk_type_counts[chunk.type] += 1
    
    pages_with_content = sum(1 for p in page_records if len(p.chunk_ids) > 0)
    
    warnings = []
    
    # Check for suspicious ratios
    if chunk_type_counts[MARGINALIA_TYPE] > len(chunks) * 0.5:
        warnings.append("High marginalia ratio (>50% of chunks)")
    
    content_ratio = pages_with_content / max(len(page_records), 1)
    if content_ratio < 0.9:
        warnings.append(f"Low content ratio: {content_ratio:.1%} of pages have content")
    
    return QASummary(
        total_pages=len(page_records),
        total_chunks=len(chunks),
        text_chunks=chunk_type_counts["text"],
        table_chunks=chunk_type_counts["table"],
        figure_chunks=sum(chunk_type_counts[t] for t in VISUAL_CHUNK_TYPES),
        marginalia_chunks=chunk_type_counts[MARGINALIA_TYPE],
        visual_crops_saved=len(visual_records),
        pages_with_content=pages_with_content,
        warnings=warnings,
    )


def save_records(records: Iterable, output_path: Path) -> None:
    """Save records as JSONL."""
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(record.to_json())
            f.write("\n")


def resolve_files(filenames: List[str]) -> List[Path]:
    """Resolve file paths from names or full paths."""
    resolved: List[Path] = []
    for name in filenames:
        name_path = Path(name)
        
        # If it's just a filename (no directory components), look in DATA_DIR
        if len(name_path.parts) == 1:
            path = (DATA_DIR / name).resolve()
        else:
            # Otherwise treat as a full or relative path
            path = name_path.resolve()
        
        if not path.exists():
            print(f"Warning: {name} not found at {path}", file=sys.stderr)
            continue
        resolved.append(path)
    
    if not resolved:
        print("Error: no valid files to process.", file=sys.stderr)
        sys.exit(1)
    return resolved


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process PDF(s) with LandingAI ADE - intelligent batching for large files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python process_pdfs.py manual.pdf
  
  # Process multiple files
  python process_pdfs.py file1.pdf file2.pdf file3.pdf
  
  # Custom output directory
  python process_pdfs.py --output-dir outputs manual.pdf
  
  # Test mode (first 20 pages)
  python process_pdfs.py --pages 20 manual.pdf
  
  # Disable automatic batching (force single-pass)
  python process_pdfs.py --no-batching large_file.pdf
        """,
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more PDF filenames (from data folder) or full paths to PDF files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory to store processed artifacts (default: outputs)",
    )
    parser.add_argument(
        "--env",
        choices=["production", "eu"],
        default="production",
        help="LandingAI environment (default: production)",
    )
    parser.add_argument(
        "--model",
        default="dpt-2-latest",
        help="Model to use for parsing (default: dpt-2-latest)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="Optional page limit (process the first N pages only, for testing)",
    )
    parser.add_argument(
        "--asset-dpi",
        type=int,
        default=200,
        help="DPI used when rendering PDF pages for cropping visual assets (default: 200)",
    )
    parser.add_argument(
        "--no-batching",
        action="store_true",
        help="Disable automatic batching for large PDFs (may fail on files >50MB/50 pages)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing even if output already exists",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Main entry point."""
    args = parse_args(argv)

    api_key = ensure_api_key()
    client = LandingAIADE(apikey=api_key, environment=args.env)

    # Resolve file paths
    pdf_paths = resolve_files(args.files)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each PDF file
    for pdf_path in pdf_paths:
        try:
            process_single_pdf(
                client,
                pdf_path,
                output_dir,
                args.model,
                args.pages,
                args.asset_dpi,
                use_batching=not args.no_batching,
                skip_existing=not args.force,
            )
        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*60}")
    print(f"✅ All files processed. Output directory: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

