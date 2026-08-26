"""Pipeline dung chung: doc 1 file PDF -> danh sach PageDoc + Finding.

Tach rieng khoi cli.py de dung lai duoc o golden test (tests/golden/) ma khong phai chep code -
ca 2 noi deu can dung Y HET 1 duong di extractor+rule engine de ket qua nhat quan.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium

from drawing_check.core.finding import Finding
from drawing_check.core.model import GDTFrame, PageDoc, Provenance, SurfaceFinish
from drawing_check.engine.loader import Rule
from drawing_check.engine.runner import chay_rule_tren_trang, chay_rule_tren_trang_kich_thuoc
from drawing_check.extract.dimension import trich_kich_thuoc, trich_nhan_pcd
from drawing_check.extract.dimension_chain import trich_kich_thuoc_thuong_va_duong
from drawing_check.extract.pdf_page import render_trang_thanh_anh, tinh_hash_file
from drawing_check.extract.titleblock import (
    phan_loai_trang_don_gian,
    trich_khung_ten_alpha_vina,
    trich_khung_ten_do_long,
)

DPI_RENDER_VISION = 300  # phai khop DPI luc gan nhan (tools/render_pages_for_labeling.py)


def _chuyen_bbox_pixel_sang_pdf_point(
    bbox_px: tuple[float, float, float, float], dpi: int, chieu_cao_pt: float
) -> tuple[float, float, float, float]:
    """Anh vision render o he pixel (goc TREN trai, y tang xuong duoi) - quy doi ve he PDF point
    (goc DUOI trai, y tang len tren) cho khop quy uoc bbox dung trong toan bo du an (xem
    extract/titleblock.py, extract/dimension.py)."""
    scale = dpi / 72.0
    x0, y0, x1, y1 = bbox_px
    return (x0 / scale, chieu_cao_pt - (y1 / scale), x1 / scale, chieu_cao_pt - (y0 / scale))


def _trich_goc_chieu_vision(page, page_no: int):
    """So khop mau anh ky hieu goc chieu - xem drawing_check.vision.projection_symbol. Import O
    TRONG ham (khong o dau file) de nhat quan voi _trich_ky_hieu_vision, tuy module nay khong can
    torch/transformers (chi numpy/PIL) nhung van CHI can thiet khi bat --vision."""
    from drawing_check.vision.projection_symbol import nhan_dien_goc_chieu

    return nhan_dien_goc_chieu(page, page_no=page_no)


def _trich_ky_hieu_vision(page, page_no: int) -> tuple[list[SurfaceFinish], list[GDTFrame]]:
    """Render trang -> chay detector RT-DETR -> gom thanh SurfaceFinish/GDTFrame. Import
    detect_symbols O TRONG ham (khong o dau file) de KHONG bat buoc torch/transformers cho luot
    chay khong bat --vision (vd golden test Phase 1-3 hien co, khong can GPU)."""
    from drawing_check.vision.detector import detect_symbols

    anh = render_trang_thanh_anh(page, dpi=DPI_RENDER_VISION)
    _, chieu_cao_pt = page.get_size()
    vung_phat_hien = detect_symbols(anh, page_no=page_no)

    surface_finishes: list[SurfaceFinish] = []
    gdt_frames: list[GDTFrame] = []
    for v in vung_phat_hien:
        bbox_pdf = _chuyen_bbox_pixel_sang_pdf_point(v.bbox, DPI_RENDER_VISION, chieu_cao_pt)
        prov = Provenance(source="vision", confidence=v.confidence, page=page_no, bbox=bbox_pdf)
        if v.label == "surface_finish":
            surface_finishes.append(SurfaceFinish(raw_text=f"[{v.label}]", prov=prov))
        else:
            gdt_frames.append(GDTFrame(raw_text=f"[{v.label}]", prov=prov))
    return surface_finishes, gdt_frames


def tim_du_an_khop(ma_ban_ve: str | None, danh_sach_du_an: list[dict]) -> dict | None:
    """Xac dinh trang thuoc DU AN NAO theo TIEN TO "<project_id>-" cua ma ban ve (config/
    projects/*.yaml) - KHONG khop theo drawing_no_pattern day du. Mot file PDF co the tron lan
    nhieu du an (da gap that: MH612 + M2613 + VPK25 trong cung 1 lo ban ve) - moi trang phai tu
    xac dinh dung du an cua no, khong ep ca file theo 1 profile duy nhat.

    QUAN TRONG (2026-08-24): co y KHONG dung drawing_no_pattern de xac dinh du an, vi lam vay se
    lam "bien mat" chinh nhung ma ban ve SAI dinh dang can bat loi - vd ma "VPK25-03-M1007-S4-L"
    (dung sai quy uoc, thieu "-03" o giua) se KHONG khop duoc pattern VPK25 chuan, nen se bi coi
    la "khong thuoc du an nao" va rule TB-002 se AM THAM bo qua thay vi bao FAIL dung nhu mong
    muon. Dung tien to project_id (on dinh, khong doi ke ca khi ma ban ve sai dinh dang) de xac
    dinh du an TRUOC, roi de rieng TB-002 (field_matches + drawing_no_pattern) kiem tra dung/sai
    dinh dang SAU - 2 buoc phai tach biet.

    Tra ve None khi khong khop project nao da biet (khong co tien to nao trung) - rule TB-002/
    PROJ-002 se tu bo qua an toan cho trang do (xem field_matches/field_equals_project trong
    engine/primitives.py, da tra False khi project rong), KHONG bao FAIL sai."""
    if not ma_ban_ve:
        return None
    for du_an in danh_sach_du_an:
        ma_du_an = du_an.get("project_id")
        if ma_du_an and ma_ban_ve.startswith(f"{ma_du_an}-"):
            return du_an
    return None


def chay_1_file(
    duong_dan: Path,
    rules: list[Rule],
    danh_sach_du_an: list[dict],
    catalogs: dict,
    chay_vision: bool = False,
    chay_dimension_chain: bool = True,
) -> tuple[list[PageDoc], list[Finding]]:
    """Trich khung ten (mau Alpha Vina, tu dong sang che do do long neu mau chinh khong doc duoc
    ma ban ve) + chay rule tren toan bo trang cua 1 file PDF.

    danh_sach_du_an: TOAN BO profile du an da biet (config/projects/*.yaml) - moi trang tu khop
    dung project qua tim_du_an_khop(), khong nhan cung 1 project cho ca file.

    chay_vision: MAC DINH TAT. Bat len se render + chay detector RT-DETR (Phase 4) tren TUNG
    trang - can GPU/torch/transformers va model da train (models/rtdetr_symbols_v1/best/), cham
    hon nhieu so voi chi doc text (Phase 1-3). De TAT theo mac dinh de khong lam gay cac luot
    chay/test hien co (vd golden test) von khong can GPU.

    chay_dimension_chain: MAC DINH BAT (nguoi dung xac nhan 2026-08-25 - "thuong ngay se check
    luon"). Bat DIM-007 (chuoi kich thuoc khep kin, xem extract/dimension_chain.py) - can doc du
    lieu HINH HOC (duong ke) qua pdfplumber cho MOI trang (khong chi trang xoay nhu truoc), cham
    hon ~40 lan so voi chi dung pypdfium2. Tat qua CLI (--no-dimension-chain) neu can toc do.
    """
    ma_file = tinh_hash_file(duong_dan)
    doc = pdfium.PdfDocument(str(duong_dan))
    n_pages = len(doc)

    # pdfplumber mo khi CO trang bi xoay HOAC dang bat DIM-007 (can du lieu hinh hoc moi trang) -
    # file khong xoay trang nao VA tat --dimension-chain van giu duoc toc do nhanh cu (~40 lan).
    co_trang_xoay = any(doc[i].get_rotation() != 0 for i in range(n_pages))
    doc_pdfplumber = (
        pdfplumber.open(str(duong_dan)) if (co_trang_xoay or chay_dimension_chain) else None
    )

    trang_list: list[PageDoc] = []
    findings: list[Finding] = []
    try:
        for i in range(n_pages):
            page = doc[i]
            trang_pdfplumber = doc_pdfplumber.pages[i] if doc_pdfplumber is not None else None
            khung_ten = trich_khung_ten_alpha_vina(
                page, page_no=i + 1, trang_pdfplumber=trang_pdfplumber
            )
            la_mau_alpha_vina = khung_ten.drawing_no.value is not None
            if not la_mau_alpha_vina:
                # Mau Alpha Vina khong doc duoc ca ma ban ve - co the la mau khung ten LA (cong
                # ty/khach hang khac) hoac trang loi - chuyen sang do long theo tu khoa (WARN,
                # khong bao gio FAIL, xem trich_khung_ten_do_long va NGUON_KHONG_CHAC_CHAN).
                khung_ten = trich_khung_ten_do_long(
                    page, page_no=i + 1, trang_pdfplumber=trang_pdfplumber
                )
            dimensions = trich_kich_thuoc(page, page_no=i + 1, trang_pdfplumber=trang_pdfplumber)
            pcd_labels = trich_nhan_pcd(page, page_no=i + 1, trang_pdfplumber=trang_pdfplumber)
            if chay_dimension_chain and trang_pdfplumber is not None:
                fit_code_bboxes = [d.prov.bbox for d in dimensions if d.fit_code and d.prov.bbox]
                dimensions = dimensions + trich_kich_thuoc_thuong_va_duong(
                    page_no=i + 1,
                    trang_pdfplumber=trang_pdfplumber,
                    fit_code_bboxes=fit_code_bboxes,
                )
            surface_finishes: list[SurfaceFinish] = []
            gdt_frames: list[GDTFrame] = []
            if chay_vision:
                surface_finishes, gdt_frames = _trich_ky_hieu_vision(page, page_no=i + 1)
                if la_mau_alpha_vina:
                    # So khop mau CHI dung cho mau Alpha Vina (vi tri crop tuyet doi da do dac
                    # rieng cho mau nay - xem vision/projection_symbol.py). Trang mau khac giu
                    # nguyen projection=None nhu truoc (khong doan bua).
                    khung_ten = khung_ten.model_copy(
                        update={"projection": _trich_goc_chieu_vision(page, page_no=i + 1)}
                    )
            trang = PageDoc(
                file_hash=ma_file,
                file_name=duong_dan.name,
                page_no=i + 1,
                pages_total=n_pages,
                page_kind=phan_loai_trang_don_gian(page),
                sheet_size="A3",
                rotation=page.get_rotation(),
                title_block=khung_ten,
                dimensions=dimensions,
                pcd_labels=pcd_labels,
                surface_finishes=surface_finishes,
                gdt_frames=gdt_frames,
            )
            trang_list.append(trang)

            du_an_khop = tim_du_an_khop(khung_ten.drawing_no.value, danh_sach_du_an)
            context_trang = {
                "project": du_an_khop or {},
                "catalogs": catalogs,
                "vision_enabled": chay_vision,
                "dimension_chain_enabled": chay_dimension_chain,
            }
            findings.extend(chay_rule_tren_trang(trang, rules, context_trang))
            findings.extend(chay_rule_tren_trang_kich_thuoc(trang, rules, context_trang))
    finally:
        if doc_pdfplumber is not None:
            doc_pdfplumber.close()

    return trang_list, findings
