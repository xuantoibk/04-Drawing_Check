"""Trich xuat Dimension (Phase 3, lat cat dau tien - xem docs/Source/Project-Remember.md muc
Phase 3). Chi lam ma lap ghep (fit code, vd "36G6", "6H7") - CHUA lam dung sai +/- rieng le, GD&T
frame, do nham.

(2026-08-24) DA THU va RUT LAI phan dung sai +/- di kem fit-code (vd "(+0.03/+0.01)"): logic dau
tien chi kiem chung dung tren vi du CHU VIET DOC (dung sai nam TREN fit-code). Khi chay rong tren
130 trang that, lo ra vi du CHU VIET NGANG (fit-code + dung sai nam CANH NHAU theo chieu ngang,
khong phai tren-duoi) - vi tri tuong doi cua dung sai PHU THUOC huong chu, khong co 1 huong co
dinh. Ket qua tren du lieu that: sai nghiem trong tren ~7-9/22 truong hop (vd doc ra tol_upper=5.0
thay vi ~0.01 - sai lech hang tram lan). Vi day la du lieu ky thuat quyet dinh an toan gia cong,
so lieu sai nguy hiem hon khong co so lieu - CHU DONG khong dua vao san pham. Muon lam lai can
phat hien HUONG CHU (doc/ngang) truoc khi tim vung dung sai, hoac cho toi Phase 4 (nhan dien hinh
anh, hieu duoc bo cuc 2D thay vi doan theo toa do).

QUAN TRONG - khac han titleblock.py: KHONG dung lay_dong_tu_trong_vung (gom dong/gom tu) vi ham do
duoc chinh cho vung khung ten HEP, gom dong theo chuoi lien ket (chain-linkage) tren CA TRANG se
gop nham rat nhieu dong khong lien quan (da thu va xac nhan that bai - "36G6" khong con la 1 token
gon sau khi gom qua ca trang). Thay vao do QUET THANG theo THU TU KY TU trong PDF (dung
lay_ky_tu_trong_vung/_pdfplumber - KHONG gom dong), gop cac ky tu lien tiep thuoc bang chu so/chu
cai/dau cham thanh 1 "buffer", roi ap regex len buffer do - don gian va dung hon cho kieu du lieu
kich thuoc/dung sai (khong co khai niem "hang/o" nhu khung ten).
"""

from __future__ import annotations

import re

import pdfplumber
import pypdfium2 as pdfium

from drawing_check.core.model import Dimension, Provenance
from drawing_check.extract.pdf_page import lay_ky_tu_trong_vung, lay_ky_tu_trong_vung_pdfplumber

# Bang chu cai lech chuan ISO 286/JIS B 0401 CHAP NHAN cho rule nay - co Y LOAI TRU "x"/"X" (chu
# "R"/"r" cung loai vi ly do tuong tu). Da kiem chung tren du lieu that 2026-08-24: "x" trung voi
# ky hieu so luong lap ("2x4", "15x6"), "R"/"r" trung voi ky hieu ban kinh ("25R2", "40R2") - ca 2
# xuat hien NHIEU trong du lieu that trong khi CHUA co vi du fit-code that nao dung x/R - chon huong
# bo sot con hon bao sai (dung tinh than precision > recall cua du an). Mo rong lai khi co bang
# chung that can den 2 chu nay.
_CHU_LECH_CHUAN = (
    "a|b|c|cd|d|e|ef|f|fg|g|h|js|j|k|m|n|p|s|t|u|v|y|z|za|zb|zc"
)
RE_FIT_CODE = re.compile(
    rf"(?<![A-Za-z0-9.])(\d{{1,3}}(?:\.\d+)?)"
    rf"(({_CHU_LECH_CHUAN.upper()})|({_CHU_LECH_CHUAN}))"
    rf"(\d{{1,2}})(?![A-Za-z0-9])"
)

_KY_TU_TICH_LUY = re.compile(r"[A-Za-z0-9.]")

# Vung bang chu giai "TOLERANCE LIMITS" co dinh (cung 1 vi tri vat ly tren MOI trang, da do bang
# pdfplumber tren ca trang A3 lan A4 that 2026-08-24: goc tren-trai, x0..~90pt, tu dinh trang toi
# ~250pt) - LOAI TRU khoi vung quet, khong phai kich thuoc that. Dung toa do TUYET DOI (khong phai
# ty le %) vi day la 1 con dau tham chieu in co dinh theo mm thuc te, khong phu thuoc kho giay.
_BANG_CHU_GIAI_X_MAX = 110.0
_BANG_CHU_GIAI_Y_TOP_MAX = 280.0  # tinh tu dinh trang (topdown)


def _trong_vung_chu_giai(c: tuple[float, float, float, float, str], h: float) -> bool:
    left, _bottom, _right, top, _text = c
    topdown_top = h - top
    return left < _BANG_CHU_GIAI_X_MAX and topdown_top < _BANG_CHU_GIAI_Y_TOP_MAX


_NGUONG_KHOANG_CACH = 3.0  # pt - cung nguong voi gom_tu_trong_dong (pdf_page.py)


def _tim_fit_code_trong_ky_tu(
    chars: list[tuple[float, float, float, float, str]], page_no: int
) -> list[Dimension]:
    """QUAN TRONG: khong chi gop ky tu theo LOAI (chu/so) ma con phai gop theo KHOANG CACH VI
    TRI - da phat hien tren du lieu that (2026-08-24): trong luong ky tu tho cua PDF, 2 nhan khac
    nhau tren trang (vd fit-code "36G6" va 1 gia tri GD&T "0.05 A" o ke ben) co the noi lien nhau
    KHONG co ky tu ngan cach nao (khong dau cach/dau phay) vi chung nam o 2 VI TRI vat ly khac
    nhau, chi la lien tuc trong LUONG du lieu. Neu chi gop theo loai ky tu se dinh nham thanh 1
    chuoi dai ("36G6A0.05A2"), lam regex khong con khop dung bien (h7/g6 bi dinh voi ky tu sau).
    Phai ngat buffer moi khi khoang cach vi tri (x hoac y) giua 2 ky tu lien tiep vuot nguong,
    giong dung nguyen tac gom_tu_trong_dong (pdf_page.py) nhung ap dung tren CA TRANG trong 1
    lan quet thang, khong qua gom_dong (xem ly do o docstring dau file)."""
    ket_qua: list[Dimension] = []
    buf = ""
    buf_chars: list[tuple[float, float, float, float, str]] = []

    def xu_ly_buf() -> None:
        for m in RE_FIT_CODE.finditer(buf):
            cac_ky_tu_khop = buf_chars[m.start() : m.end()]
            bbox = (
                min(c[0] for c in cac_ky_tu_khop),
                min(c[1] for c in cac_ky_tu_khop),
                max(c[2] for c in cac_ky_tu_khop),
                max(c[3] for c in cac_ky_tu_khop),
            )
            nominal_str = m.group(1)
            ket_qua.append(
                Dimension(
                    nominal=float(nominal_str),
                    fit_code=m.group(0)[len(nominal_str) :],
                    dim_type="diameter",
                    is_reference=False,
                    is_basic=False,
                    # confidence=0.8 (khong phai 1.0 nhu titleblock) - CO Y: extractor nay moi,
                    # chi kiem chung tren 22 vi du that (2026-08-24), chua nhieu bang khung ten
                    # (51 trang MH612). Rule DIM-001 dat confidence_gate=0.9 nen tam thoi CHI len
                    # WARN cho toi khi co du kiem chung de nang len 1.0 va cho phep FAIL.
                    prov=Provenance(source="pdf_text", confidence=0.8, page=page_no, bbox=bbox),
                )
            )

    for c in chars:
        ch = c[4]
        khop_loai = bool(_KY_TU_TICH_LUY.match(ch))
        lien_tuc_vi_tri = False
        if khop_loai and buf_chars:
            truoc = buf_chars[-1]
            khoang_x = c[0] - truoc[2]  # left cua c - right cua ky tu truoc (khoang cach ngang)
            lech_y_ngang = abs(c[1] - truoc[1])  # lech bottom - dung cho dong NGANG
            lech_x_doc = abs(c[0] - truoc[0])  # lech left - dung cho cot DOC
            khoang_y_doc = c[1] - truoc[3]  # bottom cua c - top cua ky tu truoc (khoang cach doc)
            cao_ky_tu_truoc = truoc[3] - truoc[1]
            # Dong NGANG (doc trai->phai binh thuong): x gan nhau, cung do cao bottom.
            la_dong_ngang = khoang_x <= _NGUONG_KHOANG_CACH and lech_y_ngang <= _NGUONG_KHOANG_CACH
            # Cot DOC (viet tung ky tu chong len nhau tu tren xuong - da kiem chung that tren
            # MH612 trang 1, chu "φ36G6" xep doc, khoang cach giua 2 ky tu ~1-1.5 lan chieu cao
            # ky tu, KHONG phai gan 0 nhu doc ngang - phai xu ly rieng, khong the dung 1 nguong):
            # Cho phep khoang_y_doc am nhe (ky tu chong len nhau chut it, da gap that tren file
            # PHAY - font render 2 ky tu lien tiep khi xep doc co the cham/de len nhau vai chuc
            # diem thap phan, khong phai khoang trong that).
            la_cot_doc = (
                lech_x_doc <= _NGUONG_KHOANG_CACH
                and -_NGUONG_KHOANG_CACH <= khoang_y_doc <= 1.5 * max(cao_ky_tu_truoc, 1.0)
            )
            lien_tuc_vi_tri = la_dong_ngang or la_cot_doc

        if khop_loai and (not buf_chars or lien_tuc_vi_tri):
            buf += ch
            buf_chars.append(c)
        else:
            xu_ly_buf()
            if khop_loai:
                buf, buf_chars = ch, [c]
            else:
                buf, buf_chars = "", []
    xu_ly_buf()
    return ket_qua


def trich_kich_thuoc(
    page: pdfium.PdfPage,
    page_no: int,
    trang_pdfplumber: pdfplumber.page.Page | None = None,
) -> list[Dimension]:
    """Quet CA TRANG tim ma lap ghep (fit code) - xem docstring dau file de biet vi sao KHONG dung
    lay_dong_tu_trong_vung. trang_pdfplumber chi can khi page.get_rotation() != 0 (cung dieu kien
    nhu trich_khung_ten_alpha_vina - xem titleblock.py)."""
    w, h = page.get_size()
    if page.get_rotation() != 0 and trang_pdfplumber is not None:
        chars = lay_ky_tu_trong_vung_pdfplumber(trang_pdfplumber, 0, h, w, 0)
    else:
        chars = lay_ky_tu_trong_vung(page, 0, h, w, 0)

    chars = [c for c in chars if not _trong_vung_chu_giai(c, h)]
    return _tim_fit_code_trong_ky_tu(chars, page_no)
