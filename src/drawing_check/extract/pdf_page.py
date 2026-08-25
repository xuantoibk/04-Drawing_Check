"""Tien ich doc PDF bang pypdfium2: quy toa do ve mm, cat vung, gom ky tu thanh dong/tu.

Da kiem chung tren du lieu that (00_input/MH612-DATA GIA CONG FULL.pdf, trang 1-2): pdfplumber
dan 2 cot khung ten thanh 1 dong lien nhau (dung nhu canh bao muc 6.3 tai lieu ke hoach), trong
khi tach tu bang khoang cach x giua cac ky tu (gom_tu_trong_dong) tach dung tung o rieng biet.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import NamedTuple

import pdfplumber
import pypdfium2 as pdfium

from drawing_check.extract.text_utils import chuan_hoa_fullwidth

PT_TO_MM = 25.4 / 72.0


def mm(pt: float) -> float:
    return pt * PT_TO_MM


def tinh_hash_file(duong_dan: Path) -> str:
    return hashlib.sha1(duong_dan.read_bytes()).hexdigest()[:12]


def render_trang_thanh_anh(page: pdfium.PdfPage, dpi: int = 300):
    """Render 1 trang PDF thanh anh PIL trong bo nho - dau vao cho detector Vision (Phase 4,
    xem vision/detector.py::detect_symbols). Dung 300 DPI vi da kiem chung du chi tiet de thay
    ky hieu GD&T/do nham nho (xem tools/render_pages_for_labeling.py - cung DPI voi luc gan
    nhan, tranh lech phan giai giua luc train va luc chay that)."""
    scale = dpi / 72.0
    bitmap = page.render(scale=scale)
    return bitmap.to_pil()


class Tu(NamedTuple):
    """1 'tu'/o da gom tu cac ky tu gan nhau - toa do he PDF (goc duoi trai, y tang len tren)."""

    left: float
    bottom: float
    right: float
    top: float
    text: str


def lay_ky_tu_trong_vung(
    page: pdfium.PdfPage,
    x0: float,
    y1_top: float,
    x1: float | None = None,
    y0_bottom: float = 0.0,
) -> list[tuple[float, float, float, float, str]]:
    """Lay danh sach ky tu (left, bottom, right, top, text) nam trong vung [x0,x1] x [y0_bottom,y1_top].
    Tu dong chuan hoa ky tu toan chieu rong (xem extract/text_utils.py)."""
    w, h = page.get_size()
    x1 = w if x1 is None else x1
    textpage = page.get_textpage()
    ket_qua = []
    for i in range(textpage.count_chars()):
        left, bottom, right, top = textpage.get_charbox(i)
        ch = textpage.get_text_range(i, 1)
        if not ch.strip():
            continue
        if x0 <= left and top <= y1_top and right <= x1 and bottom >= y0_bottom:
            ket_qua.append((left, bottom, right, top, chuan_hoa_fullwidth(ch)))
    return ket_qua


def gom_dong(
    chars: list[tuple[float, float, float, float, str]], nguong_bottom: float = 5.5
) -> list[list[tuple[float, float, float, float, str]]]:
    """Gom ky tu thanh dong theo cum toa do 'bottom' (baseline) gan nhau, khong dung 'top'.

    Da kiem chung tren du lieu that: dau cham/gach ngang co 'top' thap hon han chu cai cung
    dong (vd "." trong "B.X.TOI") nen gom theo 'top' se tach nham dau cham ra dong rieng; gom
    theo 'bottom' (baseline) on dinh hon vi hau het ky tu deu dat tren cung 1 duong baseline.

    So sanh THEO CHUOI (chain-linkage): moi ky tu so voi ky tu VUA THEM TRUOC DO, khong phai ky
    tu DAU TIEN cua dong. (2026-08-24) Phat hien tren du lieu that (mau khung ten du an M2613,
    trang bi xoay doc qua pdfplumber): neu so co dinh voi ky tu dau, sai so 'bottom' cong don qua
    nhieu ky tu lien tiep (vd ten cong ty 2 dong gan sat khung tren) co the vuot nguong dung ngay
    tai ranh gioi truong can doc (SHEET bi tach rieng dong dù chi cach gia tri ke ben 0.7pt), gay
    mat du lieu. Da xac nhan sua theo chuoi khong lam hong ket qua tren toan bo 51 trang MH612 da
    kiem chung truoc do (chay lai golden test sau khi sua).
    """
    chars_sorted = sorted(chars, key=lambda c: (-c[1], c[0]))
    dong_list: list[list] = []
    cur_bottom = None
    cur: list = []
    for c in chars_sorted:
        if cur_bottom is None or abs(c[1] - cur_bottom) > nguong_bottom:
            if cur:
                dong_list.append(cur)
            cur = [c]
        else:
            cur.append(c)
        cur_bottom = c[1]
    if cur:
        dong_list.append(cur)
    return dong_list


def gom_tu_trong_dong(
    dong: list[tuple[float, float, float, float, str]], nguong_khoang: float = 3.0
) -> list[Tu]:
    """Tach 1 dong ky tu thanh danh sach 'tu' dua vao khoang trong giua 2 ky tu lien tiep.

    Xu ly chinh bay 3 (chu bi tach roi tung ky tu) theo huong nguoc: o day PDF CAD dat gan nhu
    lien tuc trong cung 1 o nhung co khoang cach lon hon han giua 2 o khac nhau, nen dung nguong
    khoang trong de GOM lai thanh tu/o, thay vi TACH ra nhu van ban thuong.
    """
    dong_sorted = sorted(dong, key=lambda c: c[0])
    if not dong_sorted:
        return []
    tu_list: list[list] = [[dong_sorted[0]]]
    for prev, c in zip(dong_sorted, dong_sorted[1:]):
        if c[0] - prev[2] > nguong_khoang:
            tu_list.append([c])
        else:
            tu_list[-1].append(c)
    ket_qua = []
    for tu in tu_list:
        left = min(c[0] for c in tu)
        bottom = min(c[1] for c in tu)
        right = max(c[2] for c in tu)
        top = max(c[3] for c in tu)
        text = "".join(c[4] for c in tu)
        ket_qua.append(Tu(left, bottom, right, top, text))
    return ket_qua


def lay_dong_tu_trong_vung(
    page: pdfium.PdfPage,
    x0: float,
    y1_top: float,
    x1: float | None = None,
    y0_bottom: float = 0.0,
    nguong_dong: float = 5.5,
    nguong_tu: float = 3.0,
) -> list[list[Tu]]:
    """Ham tong hop: cat vung -> gom dong -> tach tu. Dung truc tiep trong titleblock.py."""
    chars = lay_ky_tu_trong_vung(page, x0, y1_top, x1, y0_bottom)
    dong_list = gom_dong(chars, nguong_dong)
    return [gom_tu_trong_dong(dong, nguong_tu) for dong in dong_list]


def lay_ky_tu_trong_vung_pdfplumber(
    trang: pdfplumber.page.Page,
    x0: float,
    y1_top: float,
    x1: float | None = None,
    y0_bottom: float = 0.0,
) -> list[tuple[float, float, float, float, str]]:
    """Ban sao cua lay_ky_tu_trong_vung nhung doc ky tu qua pdfplumber thay vi pypdfium2.

    Can dung cho trang bi /Rotate != 0: pypdfium2 tra toa do RAW khong khop voi page.get_size()
    tren trang xoay (da kiem chung tren du lieu that - xem ghi chu trong titleblock.py), trong
    khi pdfplumber tu dong xu ly dung rotation. Doi truc y tu he tren-xuong (top/bottom cua
    pdfplumber, goc o tren) sang he duoi-len (goc o duoi) da dung xuyen suot module nay."""
    h = trang.height
    w = trang.width
    x1 = w if x1 is None else x1
    ket_qua = []
    for ch in trang.chars:
        text = ch.get("text", "")
        if not text.strip():
            continue
        left, right = ch["x0"], ch["x1"]
        bottom, top = h - ch["bottom"], h - ch["top"]
        if x0 <= left and top <= y1_top and right <= x1 and bottom >= y0_bottom:
            ket_qua.append((left, bottom, right, top, chuan_hoa_fullwidth(text)))
    return ket_qua


def lay_dong_tu_trong_vung_pdfplumber(
    trang: pdfplumber.page.Page,
    x0: float,
    y1_top: float,
    x1: float | None = None,
    y0_bottom: float = 0.0,
    nguong_dong: float = 5.5,
    nguong_tu: float = 3.0,
) -> list[list[Tu]]:
    """Ban sao cua lay_dong_tu_trong_vung dung cho trang bi xoay - xem lay_ky_tu_trong_vung_pdfplumber.
    Tai su dung NGUYEN gom_dong/gom_tu_trong_dong, chi doi nguon ky tu."""
    chars = lay_ky_tu_trong_vung_pdfplumber(trang, x0, y1_top, x1, y0_bottom)
    dong_list = gom_dong(chars, nguong_dong)
    return [gom_tu_trong_dong(dong, nguong_tu) for dong in dong_list]
