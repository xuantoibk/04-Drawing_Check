"""Test rule DIM-007 (chuoi_kich_thuoc_khep_kin, engine/primitives_dimension.py) - dung Dimension
gia lap co axis/line_span/line_cross (khong can PDF that/pdfplumber). Vi du 2 lien-ket/1 kich
thuoc bao mo phong dung truong hop that da kiem chung tren trang 5 va trang 27 file MH612 (xem
docs/Source/Project-Remember.md muc DIM-007)."""

from __future__ import annotations

from pathlib import Path

import pytest

from drawing_check.core.model import Dimension, Provenance
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.primitives_dimension import chuoi_kich_thuoc_khep_kin
from drawing_check.engine.runner import chay_rule_tren_trang_kich_thuoc
from factories import page_mau

THU_MUC_RULES = Path(__file__).resolve().parents[2] / "rules"
CONTEXT_BAT = {"dimension_chain_enabled": True}


@pytest.fixture(scope="module")
def rules():
    return doc_thu_muc_rule(THU_MUC_RULES)


def _dim_ngang(
    nominal: float, x0: float, x1: float, y: float = 100.0, is_reference: bool = False, view_id=0
) -> Dimension:
    return Dimension(
        nominal=nominal,
        dim_type="linear",
        is_reference=is_reference,
        axis="horizontal",
        line_span=(x0, x1),
        line_cross=y,
        view_id=view_id,
        prov=Provenance(source="pdf_text", confidence=0.7, page=1),
    )


def test_chuoi_khep_kin_khong_co_tham_khao_bi_bao():
    """2 mat xich (15,20) + 1 kich thuoc bao co dau mut TRUNG KHOP (0->35) - dung mo phong tinh
    huong that (trang 5 MH612 neu "50" thuc su tra tu 0 den 35 thay vi 0 den 47.6 nhu thuc te).
    Kich thuoc bao dat KHAC line_cross (y=120) voi chuoi (y=100) - dung quy uoc ve that (duong
    kich thuoc bao luon xep O HANG/COT KHAC voi chuoi con de tranh de len nhau tren ban ve, da
    kiem chung tren trang 5 MH612: chuoi o y=505.3, bao o y=529.4)."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 0, 15, y=100),
        _dim_ngang(20, 15, 35, y=100),
        _dim_ngang(35, 0, 35, y=120),  # kich thuoc bao - khac hang voi chuoi, khop dung tong
    ]
    vi_pham = chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT)
    assert len(vi_pham) == 1


def test_co_1_kich_thuoc_tham_khao_khong_bao():
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 0, 15, y=100, is_reference=True),
        _dim_ngang(20, 15, 35, y=100),
        _dim_ngang(35, 0, 35, y=120),
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_khong_co_kich_thuoc_bao_khop_khong_bao():
    """Dung mo phong THAT tren trang 5 MH612: chuoi 15+20 (0->35) nhung kich thuoc bao "50" do
    toi 1 diem KHAC (0->47.6, khong phai 0->35) - KHONG duoc bao, vi 2 dau mut khong khop nhau
    (day chinh la ly do phai so khop CHINH XAC dau mut, khong chi "gan nhau trong 1 view")."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 0, 15),
        _dim_ngang(20, 15, 35),
        _dim_ngang(50, 0, 47.6),  # KHONG khop dau mut voi chuoi (35 != 47.6)
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_chi_1_mat_xich_khong_du_thanh_chuoi():
    trang = page_mau()
    trang.dimensions = [_dim_ngang(15, 0, 15), _dim_ngang(15, 0, 15)]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_khong_bat_khi_chua_bat_co_dimension_chain():
    """context thieu 'dimension_chain_enabled' (hoac False) - KHONG duoc ket luan, tranh nham
    'chua chay DIM-007' voi 'da chay va khong thay vi pham' (giong nguyen tac o SYM-001)."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 0, 15),
        _dim_ngang(20, 15, 35),
        _dim_ngang(35, 0, 35),
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, {}) == []
    assert chuoi_kich_thuoc_khep_kin(trang, {}, {"dimension_chain_enabled": False}) == []


def test_dim001_va_dim007_khong_lan_nhau():
    """Dimension co fit_code (DIM-001) khong duoc dua vao phan tich chuoi (axis=None mac dinh)."""
    trang = page_mau()
    trang.dimensions = [
        Dimension(
            nominal=6, fit_code="H7", dim_type="diameter",
            prov=Provenance(source="pdf_text", confidence=0.8, page=1),
        )
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_uu_tien_ung_vien_khop_gia_tri_so_khi_nhieu_ung_vien_khop_vi_tri():
    """Loi that (2026-08-25, trang 28 MH612, nguoi dung phat hien): ca 2 kich thuoc "215" va
    "213.5" deu khop VI TRI voi chuoi (10+50.5+50+60+45=215.5) - truoc khi sua, ham chi lay ung
    vien DAU TIEN gap trong danh sach (co the la "213.5", chenh 2.0) thay vi ung vien dung hon
    ("215", chi chenh 0.5). Sau khi sua, phai luon chon dung "215"."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(10, 391.0, 409.9, y=765.4),
        _dim_ngang(50.5, 409.9, 505.3, y=765.4),
        _dim_ngang(50, 505.3, 599.8, y=765.4),
        _dim_ngang(60, 599.8, 713.2, y=765.4),
        _dim_ngang(45, 713.2, 798.2, y=765.4),
        _dim_ngang(213.5, 391.0, 794.5, y=615.3),  # khop vi tri nhung SAI gia tri (chenh 2.0)
        _dim_ngang(215, 391.0, 797.4, y=637.4),  # khop vi tri VA dung gia tri hon (chenh 0.5)
    ]
    vi_pham = chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT)
    assert len(vi_pham) == 1
    assert vi_pham[0]["gia_tri"].endswith("=215")


def test_khac_cum_hinh_chieu_khong_bao_du_khop_vi_tri_va_gia_tri():
    """Loi that (2026-08-25, trang 28 MH612, nguoi dung phat hien): chuoi "10+50.5+50+60+45=215.5"
    thuoc HINH CHIEU TREN nhung "215" thuc ra la kich thuoc cua HINH CHIEU DUOI - khop vi tri VA
    gia tri (chi la trung hop toa do X) nhung KHAC cum hinh hoc (view_id) nen KHONG duoc bao.
    Day la diem nguoi dung de xuat sua: dung duong noi nhau de xac dinh dung hinh chieu, xem
    extract/dimension_chain.py::_gom_cum_hinh_hoc."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 0, 15, y=100, view_id=1),
        _dim_ngang(20, 15, 35, y=100, view_id=1),
        _dim_ngang(35, 0, 35, y=120, view_id=2),  # khop vi tri + gia tri nhung KHAC view_id
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_kich_thuoc_bao_qua_xa_theo_truc_kia_khong_bao():
    """Loi that (2026-08-25, trang 26 MH612): 1 duong khop dau mut VA cung view_id nhung nam CACH
    XA chuoi 945pt theo truc con lai (cross) van bi ghep nham - phai co gioi han khoang cach hop
    ly theo truc kia, khong chi dua vao view_id + khop dau mut truc chinh."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(20, 0, 20, y=100, view_id=1),
        _dim_ngang(20, 20, 40, y=100, view_id=1),
        _dim_ngang(40, 0, 40, y=1050, view_id=1),  # khop dau mut + view nhung cross cach 950pt
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_kich_thuoc_bao_lech_gia_tri_qua_nhieu_khong_bao():
    """Loi that (2026-08-25, trang 27 MH612): duong "64" khop VI TRI (dau mut + cross + view) voi
    chuoi nhung TONG chuoi la 560 (lech 775%) - van la ung vien DUY NHAT nen truoc do van bi chap
    nhan. Phai co nguong hop ly cho do lech GIA TRI, khong chi vi tri hinh hoc."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(520, 0, 28.3, y=100, view_id=1),
        _dim_ngang(20, 28.3, 56.6, y=100, view_id=1),
        _dim_ngang(20, 56.6, 84.9, y=100, view_id=1),
        _dim_ngang(64, 0, 84.9, y=120, view_id=1),  # khop vi tri nhung gia tri lech qua xa (560 vs 64)
    ]
    assert chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT) == []


def test_chuoi_that_tren_file_cys_m1004():
    """Tai hien dung ca THAT DAU TIEN duoc xac nhan tren du lieu that (2026-08-25, file
    CYS-M1004-SC-NI-T.pdf, con lan bang tai): chuoi "15+800+15" khop dung kich thuoc bao "830"."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 415.2, 466.2, y=979.6, view_id=1),
        _dim_ngang(800, 466.2, 1062.9, y=979.6, view_id=1),
        _dim_ngang(15, 1062.9, 1113.9, y=979.6, view_id=1),
        _dim_ngang(830, 415.2, 1113.9, y=996.6, view_id=1),
    ]
    vi_pham = chuoi_kich_thuoc_khep_kin(trang, {}, CONTEXT_BAT)
    assert len(vi_pham) == 1
    assert vi_pham[0]["gia_tri"] == "15+800+15=830"


def test_qua_rule_engine_luon_len_muc_WARN(rules):
    """confidence=0.7 < confidence_gate=0.95 cua DIM-007 - CO Y luon WARN, khong bao gio FAIL cho
    toi khi kiem chung du tren du lieu that (xem rules/20_dimension.yaml)."""
    trang = page_mau()
    trang.dimensions = [
        _dim_ngang(15, 0, 15, y=100),
        _dim_ngang(20, 15, 35, y=100),
        _dim_ngang(35, 0, 35, y=120),
    ]
    findings = chay_rule_tren_trang_kich_thuoc(trang, rules, CONTEXT_BAT)
    dim007 = [f for f in findings if f.rule_id == "DIM-007"]
    assert len(dim007) == 1
    assert dim007[0].level == "WARN"
