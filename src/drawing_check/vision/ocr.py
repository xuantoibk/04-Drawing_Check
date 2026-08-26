"""OCR vung da khoanh (PaddleOCR) - Phase 4.

Dung class `PaddleOCR` chuan (detection+recognition mot vung nho) thay vi `PaddleOCRVL` (pipeline
phan tich CA TRANG tai lieu - layout detection, chart/seal recognition... qua nang cho nhu cau o
day chi la doc 1 chuoi chu ngan trong 1 vung da khoanh san, vd "Ra6.3"). Van dung ho PaddleOCR vi
ho tro CJK tot (ban ve chuan JIS co Kanji) - Tesseract khong dung, theo tech stack da chot.

CHUA co rule nao trong rules/*.yaml can doc gia tri chu ben trong vung (SYM-001 hien tai chi can
biet CO/KHONG co ky hieu, khong can doc chu) - module nay la tien ich san sang dung khi co rule
can, chua duoc goi tu pipeline.py.

DA SUA (2026-08-26): tung bi chan boi `paddleocr` 3.7.0 can API PaddlePaddle moi hon ban
`paddlepaddle-gpu` 2.6.2 (ban GPU cao nhat tren PyPI cho Windows luc do). Da thu nang cap len
`paddlepaddle-gpu` 3.3.1 (cai tu index rieng cua paddlepaddle.org.cn, PyPI khong co ban GPU
moi) nhung gap loi rieng cua Windows: `OSError WinError 127` khi khoi tao PaddleOCR (engine
cudnn JIT). Chuyen huong dung ban **CPU-only `paddlepaddle` 3.3.1 co san thang tren PyPI**
(khong can index ngoai) - vi tac vu o day chi doc 1 vung anh nho, khong can toc do GPU, va
tach biet hoan toan voi GPU (torch) dang dung cho RT-DETR trong detector.py nen khong anh
huong. Con gap tiep 1 loi CPU rieng: `enable_mkldnn` mac dinh True gay
`ConvertPirAttribute2RuntimeAttribute not support` voi model PP-OCRv6 tren paddle 3.3.1 - da
tat bang `enable_mkldnn=False` trong `_nap_ocr()`. Da kiem chung `ocr_region()` chay that, doc
dung "Ra6.3"/"Ra25" tu vung anh that (conf 1.00)."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel

from drawing_check.vision.detector import DetectedRegion

_ocr_cache: dict[str, object] = {}


def _nap_ocr(lang: str):
    if lang not in _ocr_cache:
        # paddlepaddle bundle san .pb2 bien dich voi protobuf cu, xung dot voi protobuf moi
        # (vd 7.x) cai kem transformers - loi "Descriptors cannot be created directly" khi
        # import paddle. Fallback ve trinh doc protobuf thuan Python (cham hon chut, khong can
        # ha cap protobuf va pha transformers) - phai dat TRUOC lan import paddle dau tien.
        os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
        from paddleocr import PaddleOCR

        # enable_mkldnn=False: mac dinh True gay loi "ConvertPirAttribute2RuntimeAttribute not
        # support" khi chay CPU tren paddle 3.3.1 voi model PP-OCRv6 (bug tuong thich oneDNN,
        # da kiem chung tat di la chay duoc, cham hon chut nhung on dinh).
        _ocr_cache[lang] = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
    return _ocr_cache[lang]


class OcrResult(BaseModel):
    """Ket qua doc chu trong 1 vung da khoanh."""

    text: str
    confidence: float
    region: DetectedRegion


def ocr_region(image_path: Path, region: DetectedRegion, lang: str = "en") -> OcrResult:
    """Cat vung theo region.bbox (pixel, cung he toa do voi anh render dua vao detect_symbols)
    roi chay PaddleOCR. Tra text='' confidence=0.0 neu khong doc duoc gi (khong doan bua)."""
    from PIL import Image

    ocr = _nap_ocr(lang)
    image = Image.open(image_path).convert("RGB")
    x0, y0, x1, y1 = region.bbox
    vung = image.crop((x0, y0, x1, y1))

    import numpy as np

    ket_qua = ocr.predict(np.array(vung))
    if not ket_qua:
        return OcrResult(text="", confidence=0.0, region=region)

    trang_ket_qua = ket_qua[0]
    cac_chu = trang_ket_qua.get("rec_texts") or []
    cac_diem = trang_ket_qua.get("rec_scores") or []
    if not cac_chu:
        return OcrResult(text="", confidence=0.0, region=region)

    text = " ".join(cac_chu)
    do_tin_cay = sum(cac_diem) / len(cac_diem) if cac_diem else 0.0
    return OcrResult(text=text, confidence=do_tin_cay, region=region)
