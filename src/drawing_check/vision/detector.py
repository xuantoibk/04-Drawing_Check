"""Detector khoanh vung ky hieu cong nghe (RT-DETR) - Phase 4.

Model da fine-tune tai models/rtdetr_symbols_v1/best/ (checkpoint-epoch40 cua lan train dau -
xem docs/Source/... ghi chu 2026-08-25: cac lan train them SAU DO lam model TE HON do overfit
tren tap du lieu nho, KHONG duoc dung nham checkpoint moi hon tuong la tot hon). Nguong tin cay
van hanh: 0.08 (KHONG dung 0.5 mac dinh - RT-DETR fine-tune tren it du lieu co thang do confidence
rat thap, da kiem chung bang cach quet nhieu nguong tren tap validation).

Khong dung Ultralytics YOLO ban thuong mai (AGPL) - dung RT-DETR qua thu vien transformers,
dung theo tech stack da chot trong DATA_DOC/DrawingCheck_KeHoachXayDung.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

MODEL_CHECKPOINT_MAC_DINH = Path("models/rtdetr_symbols_v1/best")
NGUONG_TIN_CAY_MAC_DINH = 0.08

# Chi 2 nhom da xac nhan qua khao sat anh that (khong phai 9 nhom doan tu nghien cuu tham chieu -
# xem DATA_DOC/Planer/Phase4-Ke-Hoach-Chi-Tiet.html), khop dung thu tu id2label luc train
# (xem tools/train_symbol_detector.py::ID2LABEL).
SymbolLabel = Literal["surface_finish", "gdt_datum"]
_ID2LABEL: dict[int, SymbolLabel] = {0: "surface_finish", 1: "gdt_datum"}


class DetectedRegion(BaseModel):
    """1 vung anh duoc detector khoanh ra, chua qua OCR."""

    label: SymbolLabel
    bbox: tuple[float, float, float, float]
    confidence: float
    page_no: int


_model_cache: dict[str, tuple] = {}


def _nap_model(model_checkpoint: Path):
    """Cache model theo duong dan - tranh nap lai (~1-2s) cho moi trang khi xu ly hang loat."""
    key = str(model_checkpoint)
    if key not in _model_cache:
        import torch
        from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

        processor = RTDetrImageProcessor.from_pretrained(model_checkpoint)
        model = RTDetrForObjectDetection.from_pretrained(model_checkpoint)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device).eval()
        _model_cache[key] = (processor, model, device)
    return _model_cache[key]


def detect_symbols(
    image,
    model_checkpoint: Path = MODEL_CHECKPOINT_MAC_DINH,
    threshold: float = NGUONG_TIN_CAY_MAC_DINH,
    page_no: int = 1,
) -> list[DetectedRegion]:
    """Chay RT-DETR da fine-tune tren 1 anh trang (300 DPI) de khoanh vung ky hieu.

    image: duong dan file (str/Path) HOAC PIL.Image co san trong bo nho (vd render truc tiep tu
    pypdfium2 khi chay pipeline that - xem extract/pdf_page.py::render_trang_thanh_anh - tranh
    ghi/doc lai file tam khong can thiet)."""
    import torch
    from PIL import Image as PILImage

    processor, model, device = _nap_model(model_checkpoint)

    pil_image = image if isinstance(image, PILImage.Image) else PILImage.open(image)
    pil_image = pil_image.convert("RGB")
    w, h = pil_image.size
    encoded = processor(images=[pil_image], return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**encoded)
    results = processor.post_process_object_detection(
        outputs, target_sizes=torch.tensor([[h, w]]), threshold=threshold
    )[0]

    vung_phat_hien: list[DetectedRegion] = []
    for box, label_id, score in zip(
        results["boxes"].tolist(), results["labels"].tolist(), results["scores"].tolist()
    ):
        vung_phat_hien.append(
            DetectedRegion(
                label=_ID2LABEL[label_id],
                bbox=tuple(box),
                confidence=score,
                page_no=page_no,
            )
        )
    return vung_phat_hien
