"""Xuat PDF da khoanh do quanh vung loi - dung annotation Square/Rectangle cua pypdf, KHONG
dung PyMuPDF/fitz (AGPL - xem bang tech stack CLAUDE.md).

Chi khoanh duoc Finding co bbox (toa do lay tu Provenance khi trich xuat). Finding tu OCR/VLM
(Phase 4 tro di) co the khong co bbox chinh xac - se tu dong bi bo qua, khong khoanh sai vi tri.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Rectangle
from pypdf.generic import ArrayObject, FloatObject, NameObject, TextStringObject

from drawing_check.core.finding import Finding

MAU_DO = (1.0, 0.0, 0.0)
# Bbox trich xuat thuong sat sat chu - nong them 1mm quanh de nhin ro vien khi mo PDF.
DEM_MM = 1.0
PT_PER_MM = 72.0 / 25.4


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
        left, bottom, right, top = f.bbox
        annot = Rectangle(rect=(left - dem_pt, bottom - dem_pt, right + dem_pt, top + dem_pt))
        annot[NameObject("/C")] = ArrayObject(FloatObject(c) for c in MAU_DO)
        annot[NameObject("/Contents")] = TextStringObject(f"{f.rule_id}: {f.message_vi}")
        writer.add_annotation(page_number=f.page_no - 1, annotation=annot)
        so_da_khoanh += 1

    duong_dan_ra.parent.mkdir(parents=True, exist_ok=True)
    with duong_dan_ra.open("wb") as fh:
        writer.write(fh)
    return so_da_khoanh
