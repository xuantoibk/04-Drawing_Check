"""VLM fallback (Qwen3-VL 8B qua Ollama) - Phase 4.

Chi goi khi PaddleOCR that bai/confidence thap o 1 vung da khoanh - khong bao gio thay
the OCR lam nguon chinh. Ket qua tra ve luon o muc WARN, khong bao gio FAIL (xem nguyen
tac kien truc cot loi trong CLAUDE.md - AI chi trich xuat, khong bao gio phan xu).

CHUA duoc goi tu pipeline.py - chua co rule nao can doc gia tri chu (xem ocr.py), va OCR (nguon
chinh, re hon nhieu) dang bi chan boi loi moi truong rieng (xem ocr.py). Module nay da kiem chung
hoat dong doc lap (Ollama chay ngoai paddlepaddle, khong dinh loi tren)."""

from __future__ import annotations

import base64
from pathlib import Path

from drawing_check.vision.detector import DetectedRegion

OLLAMA_URL_MAC_DINH = "http://localhost:11434/api/generate"
MODEL_MAC_DINH = "qwen3-vl:8b"


def vlm_read_region(
    image_path: Path,
    region: DetectedRegion,
    prompt: str,
    model: str = MODEL_MAC_DINH,
    ollama_url: str = OLLAMA_URL_MAC_DINH,
    timeout: float = 60.0,
) -> str:
    """Cat vung theo region.bbox, gui anh + prompt cho Qwen3-VL qua Ollama, tra ve text tho
    (chua chuan hoa). Ollama phai dang chay (`ollama serve`, mac dinh port 11434)."""
    import requests
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    x0, y0, x1, y1 = region.bbox
    vung = image.crop((x0, y0, x1, y1))

    import io

    buf = io.BytesIO()
    vung.save(buf, format="PNG")
    anh_base64 = base64.b64encode(buf.getvalue()).decode("ascii")

    resp = requests.post(
        ollama_url,
        json={"model": model, "prompt": prompt, "images": [anh_base64], "stream": False},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()
