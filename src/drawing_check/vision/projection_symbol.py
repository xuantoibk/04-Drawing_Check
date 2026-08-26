"""Nhan dien ky hieu goc chieu (PROJ-001/002) bang so khop mau anh (template matching) - CHI
danh cho mau khung ten Alpha Vina (khac RT-DETR dung cho surface_finish/gdt_datum).

Ly do dung so khop mau thay vi train detector rieng: ky hieu goc chieu nam O VI TRI CO DINH
trong khung ten (khong troi noi khap trang nhu surface_finish/gdt_datum). Da do dac tren 4 trang
That (2 trang A3 + 2 trang A4, file 00_input/MH612-DATA GIA CONG FULL.pdf, 2026-08-25): CUNG 1
toa do TUYET DOI tinh tu canh PHAI/DUOI trang cho ca 2 kho giay (vi khung ten la 1 khoi in co
kich thuoc vat ly co dinh, khong scale theo kho giay bao quanh) - khop pixel-for-pixel giua cac
trang. Vi vay khong can gan nhan/train GPU nhu 2 nhom ky hieu kia, chi can 1 anh mau tham chieu.

GIOI HAN QUAN TRONG: vi tri crop tuyet doi nay CHI dung cho mau khung ten Alpha Vina - ham
nhan_dien_goc_chieu() KHONG duoc goi cho trang dung mau khung ten khac (xem dieu kien goi trong
pipeline.py::chay_1_file, chi goi khi trich_khung_ten_alpha_vina doc duoc drawing_no). Ban ve
khach hang/mau khac se can RT-DETR (nhu surface_finish/gdt_datum) - de danh cho khi co du lieu
that (nguoi dung xac nhan 2026-08-25).

Hieu chinh nguong IoU tren toan bo 51 trang that MH612: min=0.478 (2 trang net ve mong hon binh
thuong nhung van dung ky hieu, da kiem tra bang mat), max=1.0 (khop tuyet doi), trong khi vung
TRONG thuc su (khong co ky hieu) cho IoU=0.0 - chon nguong 0.35 de co bien do an toan ca 2 phia.

Ket qua LUON gan source="vision" (Provenance) - runner.py tu dong ha xuong WARN qua
NGUON_KHONG_CHAC_CHAN, khong bao gio len FAIL, dung nguyen tac "AI chi trich xuat, khong bao gio
phan xu". Truong hop "co muc den nhung khong khop mau da biet" tam gan value="third" nhu 1 TIN
HIEU de PROJ-002 bat WARN (can nguoi kiem tra xac nhan), KHONG phai khang dinh chac chan la ky
hieu goc chieu thu ba that - vi chua co vi du that nao ve goc chieu sai de doi chieu hinh dang
chinh xac (xem docs/Source/Project-Remember.md muc Phase 4).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

from drawing_check.core.model import Field, Provenance

DPI = 300
_SCALE = DPI / 72.0

# Toa do TUYET DOI (pt), tinh tu canh PHAI/DUOI trang - do dac 2026-08-25, xem docstring dau file.
DX_MIN, DX_MAX = 470.0, 545.0
DY_MIN, DY_MAX = 130.0, 172.0
_W_PX = round((DX_MAX - DX_MIN) * _SCALE)
_H_PX = round((DY_MAX - DY_MIN) * _SCALE)

NGUONG_IOU_KHOP = 0.35
NGUONG_INK_TRONG = 0.03
NGUONG_MUC_DEN = 128  # gia tri xam (0-255) phan biet net den/nen trang

_DUONG_DAN_MAU = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "config" / "vision" / "templates" / "projection_first_angle_alpha_vina.png"
)

_mau_cache: np.ndarray | None = None


def _nap_mau() -> np.ndarray:
    global _mau_cache
    if _mau_cache is None:
        anh = Image.open(_DUONG_DAN_MAU).convert("L")
        _mau_cache = np.array(anh) < NGUONG_MUC_DEN
    return _mau_cache


def _crop_vung_ky_hieu(page: pdfium.PdfPage) -> Image.Image:
    w, h = page.get_size()
    x0 = round((w - DX_MAX) * _SCALE)
    y0 = round((h - DY_MAX) * _SCALE)
    bitmap = page.render(scale=_SCALE)
    anh = bitmap.to_pil().convert("L")
    return anh.crop((x0, y0, x0 + _W_PX, y0 + _H_PX))


def _quyet_dinh_tu_anh_nhi_phan(
    candidate: np.ndarray, mau: np.ndarray
) -> tuple[Literal["first", "third"] | None, float]:
    """Phan tach rieng phan quyet dinh (gia_tri, do_tin_cay) tu 2 mang nhi phan da co san - tach
    khoi phan render PDF de test duoc bang anh gia lap, khong can trang PDF that."""
    ty_le_muc_den = float(candidate.mean())

    giao = (candidate & mau).sum()
    hop = (candidate | mau).sum()
    iou = float(giao / hop) if hop else 0.0

    if iou >= NGUONG_IOU_KHOP:
        return "first", min(0.9, 0.5 + iou * 0.5)
    if ty_le_muc_den < NGUONG_INK_TRONG:
        return None, 0.3
    # co muc den dang ke nhung khong khop mau "first" da biet - xem canh bao trong docstring.
    return "third", 0.3


def nhan_dien_goc_chieu(page: pdfium.PdfPage, page_no: int) -> Field[Literal["first", "third"]]:
    """CHI goi khi trang da xac dinh dung mau khung ten Alpha Vina (xem gioi han o docstring dau
    file). Tra ve Field voi Provenance(source="vision") - luon bi ha WARN boi rule engine."""
    mau = _nap_mau()
    crop = _crop_vung_ky_hieu(page)
    candidate = np.array(crop) < NGUONG_MUC_DEN
    gia_tri, do_tin_cay = _quyet_dinh_tu_anh_nhi_phan(candidate, mau)

    w, h = page.get_size()
    bbox_pdf = (w - DX_MAX, DY_MIN, w - DX_MIN, DY_MAX)
    return Field(
        value=gia_tri,
        prov=Provenance(source="vision", confidence=do_tin_cay, page=page_no, bbox=bbox_pdf),
    )
