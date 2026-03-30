import json
import re
import io
import base64
from pathlib import Path

import fitz  # pymupdf
import PIL.Image
import requests

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from ocr.prompts import PROMPTS


def detect_report_type(image_bytes: bytes) -> str:
    """Auto-detect the report type from an image."""
    prompt = "Look at this medical lab report image. Identify what type it is. Reply with ONLY one word: 'liver', 'ckd', or 'cbc'. Nothing else."
    detected = _call_openrouter_vision(prompt, image_bytes).strip().lower()
    
    detected = re.sub(r'[^a-z]', '', detected)
    
    if detected not in PROMPTS:
        return "cbc"
    return detected


def detect_type_from_text(description: str) -> str:
    """Auto-detect the report type from a user description."""
    prompt = f"The user described their medical lab report as: '{description}'. Identify what type it is. Reply with ONLY one word: 'liver', 'ckd', or 'cbc'. Nothing else."
    detected = _call_openrouter_vision(prompt).strip().lower()
    
    detected = re.sub(r'[^a-z]', '', detected)
    
    if detected not in PROMPTS:
        return "cbc"
    return detected


def get_first_page_image(file_path: str) -> bytes:
    """Extracts first page as image bytes for auto-detection."""
    path = Path(file_path)
    raw = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(stream=raw, filetype="pdf")
        pix = doc[0].get_pixmap(dpi=150)
        return pix.tobytes("png")
    return raw


def extract_values(image_bytes: bytes, report_type: str) -> dict:
    """Send image to Gemini and extract structured values."""
    if report_type not in PROMPTS:
        raise ValueError(f"Unknown report type: {report_type}")

    prompt = PROMPTS[report_type]
    raw_text = _call_openrouter_vision(prompt, image_bytes)
    raw = re.sub(r"```json|```", "", raw_text).strip()
    return json.loads(raw)


def _call_openrouter_vision(prompt: str, image_bytes: bytes | None = None) -> str:
    """Call OpenRouter vision model (Nemotron) for text/image understanding."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    if image_bytes is not None:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_image}",
                },
            },
        ]
    else:
        content = [{"type": "text", "text": prompt}]

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def pdf_to_image_and_merge(pdf_bytes: bytes, report_type: str) -> dict:
    """Handle multi-page PDFs, running OCR on each page and merging results."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    merged_result = {}
    
    for page_num in range(len(doc)):
        pix = doc[page_num].get_pixmap(dpi=150)
        image_bytes = pix.tobytes("png")
        page_result = extract_values(image_bytes, report_type)
        
        if not merged_result:
            merged_result = page_result
        else:
            for k, v in page_result.items():
                if merged_result.get(k) is None:
                    merged_result[k] = v
                    
    return merged_result


def run_ocr(file_path: str, report_type: str) -> dict:
    """Load a file (image or PDF) and extract values via OCR without CLI logic."""
    path = Path(file_path)
    raw = path.read_bytes()
    
    if path.suffix.lower() == ".pdf":
        return pdf_to_image_and_merge(raw, report_type)
    else:
        return extract_values(raw, report_type)