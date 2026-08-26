"""Xuat PDF da khoanh do quanh vung loi - dung annotation Square/Rectangle cua pypdf, KHONG
dung PyMuPDF/fitz (AGPL - xem bang tech stack CLAUDE.md).

Chi khoanh duoc Finding co bbox (toa do lay tu Provenance khi trich xuat). Finding tu OCR/VLM
(Phase 4 tro di) co the khong co bbox chinh xac - se tu dong bi bo qua, khong khoanh sai vi tri.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject
from pypdf.annotations import Rectangle
from pypdf.generic import ArrayObject, FloatObject, NameObject, TextStringObject

from drawing_check.core.finding import Finding

MAU_DO = (1.0, 0.0, 0.0)
# Bbox trich xuat thuong sat sat chu - nong them 1mm quanh de nhin ro vien khi mo PDF.
DEM_MM = 1.0
PT_PER_MM = 72.0 / 25.4


def _quy_doi_bbox_ve_goc_chua_xoay(
    bbox: tuple[float, float, float, float], rotation: int, w_raw: float, h_raw: float
) -> tuple[float, float, float, float]:
    """/Rect cua annotation PDF luon tinh theo he toa do GOC (truoc khi ap dung /Rotate de hien
    thi), trong khi bbox cua Finding lay tu pdfplumber (extract/*.py, dung cho trang bi xoay -
    xem titleblock.py) da o he toa do HIEN THI (SAU xoay). Neu ghi thang bbox hien thi vao /Rect
    ma khong quy doi nguoc, annotation se lech han vi tri that (loi that phat hien 2026-08-25,
    file CYS-M1004-SC-NI-T.pdf - trang xoay 90 do, khung do thanh 1 hinh hep dai sai vi tri thay
    vi hinh chu nhat nam ngang dung cho chuoi kich thuoc). Ham nay quy doi NGUOC lai he goc, dao
    cong thuc da dung trong extract/pdf_page.py cho chieu xuoi.

    w_raw, h_raw: kich thuoc MediaBox GOC (truoc xoay, tuc page.mediabox.width/height cua pypdf -
    KHAC page.get_size() cua pypdfium2, vi ham do da tra kich thuoc SAU xoay)."""
    left, bottom, right, top = bbox
    if rotation % 360 == 0:
        return left, bottom, right, top
    if rotation % 360 == 90:
        # thuan (extract): x_disp = y_raw; y_disp = w_raw - x_raw
        # nguoc: x_raw = w_raw - y_disp; y_raw = x_disp
        return (w_raw - top, left, w_raw - bottom, right)
    if rotation % 360 == 180:
        return (w_raw - right, h_raw - top, w_raw - left, h_raw - bottom)
    if rotation % 360 == 270:
        # thuan: x_disp = h_raw - y_raw; y_disp = x_raw
        # nguoc: x_raw = y_disp; y_raw = h_raw - x_disp
        return (bottom, h_raw - right, top, h_raw - left)
    raise ValueError(f"Goc xoay khong hop le: {rotation}")


def khoanh_do_1_file(duong_dan_vao: Path, findings: list[Finding], duong_dan_ra: Path) -> int:
    """Ve khung do quanh bbox cua tung Finding len dung trang tuong ung, ghi ra duong_dan_ra.

    Tra ve so luong khung da ve (co the < len(findings) neu co Finding thieu bbox).
    """
    reader = PdfReader(str(duong_dan_vao))
    writer = PdfWriter()
    writer.append(reader)

    dem_pt = DEM_MM * PT_PER_MM
    so_da_khoanh = 0
    for f in findings:
        if f.bbox is None:
            continue
        trang: PageObject = reader.pages[f.page_no - 1]
        xoay = trang.rotation
        w_raw = float(trang.mediabox.width)
        h_raw = float(trang.mediabox.height)
        left, bottom, right, top = _quy_doi_bbox_ve_goc_chua_xoay(f.bbox, xoay, w_raw, h_raw)
        # sau khi xoay 90/270, trai/phai hoac tren/duoi co the dao chieu - sap lai cho dung thu tu [llx,lly,urx,ury]
        left, right = min(left, right), max(left, right)
        bottom, top = min(bottom, top), max(bottom, top)
        annot = Rectangle(rect=(left - dem_pt, bottom - dem_pt, right + dem_pt, top + dem_pt))
        annot[NameObject("/C")] = ArrayObject(FloatObject(c) for c in MAU_DO)
        annot[NameObject("/Contents")] = TextStringObject(f"{f.rule_id}: {f.message_vi}")
        writer.add_annotation(page_number=f.page_no - 1, annotation=annot)
        so_da_khoanh += 1

    duong_dan_ra.parent.mkdir(parents=True, exist_ok=True)
    with duong_dan_ra.open("wb") as fh:
        writer.write(fh)
    return so_da_khoanh
