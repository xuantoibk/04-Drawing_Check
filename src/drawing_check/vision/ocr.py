"""OCR vung da khoanh (PaddleOCR) - Phase 4.

Dung class `PaddleOCR` chuan (detection+recognition mot vung nho) thay vi `PaddleOCRVL` (pipeline
phan tich CA TRANG tai lieu - layout detection, chart/seal recognition... qua nang cho nhu cau o
day chi la doc 1 chuoi chu ngan trong 1 vung da khoanh san, vd "Ra6.3"). Van dung ho PaddleOCR vi
ho tro CJK tot (ban ve chuan JIS co Kanji) - Tesseract khong dung, theo tech stack da chot.

CHUA co rule nao trong rules/*.yaml can doc gia tri chu ben trong vung (SYM-001 hien tai chi can
biet CO/KHONG co ky hieu, khong can doc chu) - module nay la tien ich san sang dung khi co rule
can, chua duoc goi tu pipeline.py.

GIOI HAN MOI TRUONG DA BIET (2026-08-25): `paddleocr` 3.7.0 (moi nhat tren PyPI) can API
PaddlePaddle moi hon (vd AnalysisConfig.set_optimization_level) so voi `paddlepaddle-gpu` 2.6.2 -
DAY LA BAN MOI NHAT CO SAN qua pip cho Windows (kiem chung bang `pip index versions
paddlepaddle-gpu` - khong co ban cao hon). Goi ocr_region() hien tai se loi AttributeError khi
khoi tao PaddleOCR. Chua sua vi CHUA CO RULE NAO CAN OCR (chi la tien ich chuan bi san) - neu can
dung that, huong sua: (1) cai paddlepaddle-gpu tu index rieng cua paddlepaddle.org.cn (ngoai
PyPI, co ban moi hon cho Windows), hoac (2) ha cap paddleocr xuong ban tuong thich 2.6.2."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel

from drawing_check.vision.detector import DetectedRegion

_ocr_cache: dict[str, object] = {}


def _nap_ocr(lang: str):
    if lang not in _ocr_cache:
        # paddlepaddle 2.6.2 bundle san .pb2 bien dich voi protobuf cu, xung dot voi protobuf
        # moi (vd 7.x) cai kem transformers - loi "Descriptors cannot be created directly" khi
        # import paddle. Fallback ve trinh doc protobuf thuan Python (cham hon chut, khong can
        # ha cap protobuf va pha transformers) - phai dat TRUOC lan import paddle dau tien.
        os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
        from paddleocr import PaddleOCR

        _ocr_cache[lang] = PaddleOCR(
            lang=lang, use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False
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
