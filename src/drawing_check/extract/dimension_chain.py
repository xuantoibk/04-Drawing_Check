"""Trich xuat kich thuoc THUONG (khac fit-code) + ghep voi duong kich thuoc hinh hoc that - phuc
vu DIM-007 (chuoi kich thuoc cong don khep kin, xem docs/Source/Project-Remember.md muc Phase 3/
DIM-007). Module nay CHI lo phan TRICH XUAT (dien axis/line_span/line_cross vao Dimension) - thuat
toan phat hien chuoi khep kin nam o engine/primitives_dimension.py (dung nguyen tac kien truc
"extractor khong phan xu" - xem CLAUDE.md).

NANG LUC HOAN TOAN MOI cua du an (2026-08-25): lan dau doc DU LIEU HINH HOC (duong ke) tu PDF qua
pdfplumber.lines, khong chi doc text nhu Phase 1-3 truoc do. Vi vay pdfplumber phai duoc mo cho
MOI trang (khac truoc day: chi mo khi co trang xoay) - xem pipeline.py, co gate qua cờ CLI rieng
(--dimension-chain/--no-dimension-chain, nguoi dung xac nhan 2026-08-25 mac dinh BAT vi "thuong
ngay se check luon" - chap nhan cham hon ~40 lan de doi lay kha nang bat DIM-007).

QUAN TRONG - da kiem chung 2026-08-25: pdfplumber.extract_words() KHONG dung duoc cho du lieu nay -
thu tu ky tu tho trong luong PDF CAD that BI XAO TRON (vi du 1 o dung sai lap ghep doc ra
"）３０.０＋（６Ｇ６３φ" thay vi dung thu tu nhin thay tren ban ve) - giong het van de da gap va
rut kinh nghiem o dimension.py (fit-code, xem docstring dau file do). Phai dung dung
quet_buffer_theo_vi_tri (gom ky tu theo VI TRI THUC TE, khong theo thu tu trong luong du lieu).
"""

from __future__ import annotations

import re
from collections import defaultdict

import pdfplumber

from drawing_check.core.model import Dimension, Provenance
from drawing_check.extract.dimension import _trong_vung_chu_giai, quet_buffer_theo_vi_tri
from drawing_check.extract.pdf_page import lay_ky_tu_trong_vung_pdfplumber

_KY_TU_SO_KT = re.compile(r"[0-9().±+\-]")
RE_SO_KICH_THUOC = re.compile(r"(\()?(\d{1,4}(?:\.\d+)?)(\))?")
_KY_HIEU_DUNG_SAI = re.compile(r"[±+\-]")

# Nguong hieu chinh tren du lieu that (trang 5 MH612, chuoi "15"+"20" + kich thuoc bao "50" -
# xem docs/Source/Project-Remember.md): khoang cach text->duong quan sat duoc ~2.9pt, cho bien do
# rong hon nhieu de an toan voi cac mau khac chua kiem chung.
_NGUONG_GAN_FIT_CODE = 20.0  # pt - vung loai tru quanh 1 fit-code (tranh dem trung tri so dung sai)
_NGUONG_KHOP_DUONG = 12.0  # pt - text phai cach duong kich thuoc trong khoang nay moi coi la khop
_NGUONG_TRUNG_DIEM = 40.0  # pt - tam text phai nam trong [duong.min-nguong, duong.max+nguong]

# Gom cum hinh hoc (HINH CHIEU) - xem docs/Source/Project-Remember.md muc DIM-007. Da kiem chung
# 2026-08-25 tren trang 28 MH612 (anh mau tach cum): 2 diem cuoi cach nhau <=9pt duoc coi la
# "cham nhau" (bu khe ho ve thuong le giua duong bao chi tiet va duong giong), du ve tach dung 2
# hinh chieu gan nhau (khong bi gop lam 1).
_NGUONG_CUM = 9.0
_KICH_THUOC_O_LUOI = 12.0  # pt - kich thuoc o luoi khong-gian, PHAI >= _NGUONG_CUM


def _bbox_tu_ky_tu(cac_ky_tu: list[tuple[float, float, float, float, str]]):
    return (
        min(c[0] for c in cac_ky_tu),
        min(c[1] for c in cac_ky_tu),
        max(c[2] for c in cac_ky_tu),
        max(c[3] for c in cac_ky_tu),
    )


def _huong_doc(cac_ky_tu: list[tuple[float, float, float, float, str]]) -> str:
    """'doc' neu buffer trai theo chieu doc (cot), 'ngang' neu trai theo chieu ngang (dong).

    QUAN TRONG (loi that phat hien 2026-08-25, trang 27 MH612): phai dung BE RONG TOAN PHAN
    (max(right) - min(left)), KHONG duoc dung max(left)-min(left) - voi so NGAN (vd "15", chi 2
    chu so), khoang cach giua 2 CANH TRAI co the nho hon CHIEU CAO 1 chu so (vd chu so rong ~7pt
    nhung khoang cach 2 canh trai chi ~6pt trong khi chieu cao ~11pt), lam nham tuong la "cot doc"
    du thuc te la 1 dong ngang binh thuong - khien kich thuoc bi khop nham sang duong doc khong
    lien quan va bien mat khoi chuoi (da gay bao sai DIM-007 tren trang 27, thieu mat xich "15")."""
    if len(cac_ky_tu) < 2:
        return "ngang"
    x_range = max(c[2] for c in cac_ky_tu) - min(c[0] for c in cac_ky_tu)
    y_range = max(c[3] for c in cac_ky_tu) - min(c[1] for c in cac_ky_tu)
    return "doc" if y_range > x_range else "ngang"


def _gan_fit_code(bbox, fit_code_bboxes: list[tuple[float, float, float, float]]) -> bool:
    left, bottom, right, top = bbox
    for fl, fb, fr, ft in fit_code_bboxes:
        if (
            left - _NGUONG_GAN_FIT_CODE <= fr
            and right + _NGUONG_GAN_FIT_CODE >= fl
            and bottom - _NGUONG_GAN_FIT_CODE <= ft
            and top + _NGUONG_GAN_FIT_CODE >= fb
        ):
            return True
    return False


def _gom_cum_hinh_hoc(trang_pdfplumber: pdfplumber.page.Page) -> list[tuple[float, float, float, float, int]]:
    """Gom TOAN BO doan thang tren trang (tu .lines + 4 canh cua .rects) thanh cac CUM HINH HOC
    (union-find) - 2 doan cung 1 cum neu co it nhat 1 cap dau mut cach nhau <= _NGUONG_CUM. Moi
    cum tuong ung 1 HINH CHIEU (duong bao chi tiet + duong giong + duong kich thuoc CUA CHINH no
    deu noi lien nhau thanh 1 mang) - da kiem chung bang mat tren trang 28 MH612 (2026-08-25): 2
    hinh chieu tren/duoi tach thanh 2 cum rieng biet, khong bi gop nham.

    Dung luoi khong gian (spatial hashing) de tranh do phuc tap O(n^2) - trang that co the co
    hang nghin doan (page 28: 876 doan)."""
    doans: list[tuple[float, float, float, float]] = []
    for ln in trang_pdfplumber.lines:
        doans.append((ln["x0"], ln["y0"], ln["x1"], ln["y1"]))
    for r in trang_pdfplumber.rects:
        x0, x1, y0, y1 = r["x0"], r["x1"], r["y0"], r["y1"]
        doans += [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]

    n = len(doans)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    O = _KICH_THUOC_O_LUOI
    luoi: dict[tuple[int, int], list[int]] = defaultdict(list)
    for i, (x0, y0, x1, y1) in enumerate(doans):
        for px, py in ((x0, y0), (x1, y1)):
            luoi[(round(px / O), round(py / O))].append(i)

    for i, (x0, y0, x1, y1) in enumerate(doans):
        for px, py in ((x0, y0), (x1, y1)):
            gx, gy = round(px / O), round(py / O)
            for dgx in (-1, 0, 1):
                for dgy in (-1, 0, 1):
                    for j in luoi.get((gx + dgx, gy + dgy), []):
                        if j == i:
                            continue
                        xj0, yj0, xj1, yj1 = doans[j]
                        if (abs(px - xj0) <= _NGUONG_CUM and abs(py - yj0) <= _NGUONG_CUM) or (
                            abs(px - xj1) <= _NGUONG_CUM and abs(py - yj1) <= _NGUONG_CUM
                        ):
                            union(i, j)

    return [(x0, y0, x1, y1, find(i)) for i, (x0, y0, x1, y1) in enumerate(doans)]


def _duong_ngang_va_doc(trang_pdfplumber: pdfplumber.page.Page):
    """Tach doan thang (da gom cum hinh hoc) thanh 2 nhom: ngang [(x0,x1,y,cum_id)] va doc
    [(y0,y1,x,cum_id)] - toa do da o he PDF goc duoi-trai."""
    ngang: list[tuple[float, float, float, int]] = []
    doc: list[tuple[float, float, float, int]] = []
    for x0, y0, x1, y1, cum_id in _gom_cum_hinh_hoc(trang_pdfplumber):
        if abs(y0 - y1) < 0.5 and abs(x1 - x0) > 3:
            ngang.append((min(x0, x1), max(x0, x1), y0, cum_id))
        elif abs(x0 - x1) < 0.5 and abs(y1 - y0) > 3:
            doc.append((min(y0, y1), max(y0, y1), x0, cum_id))
    return ngang, doc


def _khop_duong(bbox, cac_duong: list[tuple[float, float, float, int]], la_ngang: bool):
    """Tim duong GAN NHAT khop voi bbox cua 1 gia tri kich thuoc - tra ve (span, cross, cum_id)
    hoac None. span = 2 dau mut doc truc chinh (vd x0,x1 cho duong ngang); cross = toa do truc
    con lai (y).

    QUAN TRONG (loi that phat hien 2026-08-25, file CYS-M1004-SC-NI-T): khi NHIEU duong nam SAT
    NHAU tren CUNG 1 hang/cot (vd chuoi "15|800|15" lien tiep), bien do _NGUONG_TRUNG_DIEM (40pt)
    co the cho phep gia tri "15" khop NHAM sang duong cua "800" ben canh (ca 2 cung khoang cach
    cross, tam_chinh cua "15" van roi trong khoang [800.lo-40, 800.hi+40]) - danh sach nhieu duong
    cung cross thi chon dai theo THU TU GAP, khong theo do chinh xac. Sua bang 2 vong: uu tien
    duong THUC SU CHUA tam_chinh trong pham vi [lo,hi] cua chinh no (khong co bien do) truoc, chi
    dung bien do _NGUONG_TRUNG_DIEM khi KHONG co duong nao chua duoc (truong hop that: 1 dau mut
    text hoi lech ra ngoai duong that do ve/do dac)."""
    left, bottom, right, top = bbox
    tam_chinh = (left + right) / 2 if la_ngang else (bottom + top) / 2
    canh_gan_nhat = (bottom, top) if la_ngang else (left, right)

    def tim(bien_do: float):
        tot = None
        tot_khoang = None
        for lo, hi, cross, cum_id in cac_duong:
            if not (lo - bien_do <= tam_chinh <= hi + bien_do):
                continue
            khoang = min(abs(cross - canh_gan_nhat[0]), abs(cross - canh_gan_nhat[1]))
            if khoang > _NGUONG_KHOP_DUONG:
                continue
            if tot is None or khoang < tot_khoang:
                tot, tot_khoang = (lo, hi, cross, cum_id), khoang
        return tot

    tot = tim(0.0) or tim(_NGUONG_TRUNG_DIEM)
    if tot is None:
        return None
    lo, hi, cross, cum_id = tot
    return (lo, hi), cross, cum_id


def trich_kich_thuoc_thuong_va_duong(
    page_no: int,
    trang_pdfplumber: pdfplumber.page.Page,
    fit_code_bboxes: list[tuple[float, float, float, float]],
) -> list[Dimension]:
    """Quet CA TRANG tim gia tri kich thuoc thuong (khac fit-code) + ghep voi duong kich thuoc gan
    nhat. CHI tra ve Dimension da ghep duoc voi 1 duong that (khong ghep duoc = bo qua, khong dua
    vao ket qua - tranh nhieu tu cac chu so khong lien quan trong khung ten/bang chu giai/nhan lo)."""
    h = trang_pdfplumber.height
    chars = lay_ky_tu_trong_vung_pdfplumber(trang_pdfplumber, 0, h, trang_pdfplumber.width, 0)
    chars = [c for c in chars if not _trong_vung_chu_giai(c, h)]

    duong_ngang, duong_doc = _duong_ngang_va_doc(trang_pdfplumber)

    ket_qua: list[Dimension] = []
    for buf, buf_chars in quet_buffer_theo_vi_tri(chars, lambda ch: bool(_KY_TU_SO_KT.match(ch))):
        # Vi tri ky hieu dung sai DAU TIEN (±, +, -) trong buffer - moi con so tu vi tri nay tro
        # di la GIA TRI DUNG SAI (vd "10±0.02" -> chi "10" la kich thuoc that, "0.02" la dung sai
        # di kem, KHONG phai 1 mat xich rieng) - phat hien tren du lieu that trang 28 MH612
        # (2026-08-25): "0.02" tu "10±0.02"/"105.3±0.02" bi ghep nham thanh mat xich, trung hop
        # khop voi 1 kich thuoc bao KHONG lien quan o view khac, bao sai hoan toan.
        m_dau_sai = _KY_HIEU_DUNG_SAI.search(buf)
        gioi_han = m_dau_sai.start() if m_dau_sai else len(buf)
        for m in RE_SO_KICH_THUOC.finditer(buf):
            if m.group(2) is None or m.start() >= gioi_han:
                continue
            cac_ky_tu_khop = buf_chars[m.start() : m.end()]
            bbox = _bbox_tu_ky_tu(cac_ky_tu_khop)
            if _gan_fit_code(bbox, fit_code_bboxes):
                continue

            la_ngang = _huong_doc(cac_ky_tu_khop) == "ngang"
            khop = _khop_duong(bbox, duong_ngang if la_ngang else duong_doc, la_ngang)
            if khop is None:
                continue
            span, cross, view_id = khop

            is_reference = m.group(1) == "(" and m.group(3) == ")"
            ket_qua.append(
                Dimension(
                    nominal=float(m.group(2)),
                    dim_type="linear",
                    is_reference=is_reference,
                    is_basic=False,
                    axis="horizontal" if la_ngang else "vertical",
                    line_span=span,
                    line_cross=cross,
                    view_id=view_id,
                    # confidence=0.7: nang luc moi, nhieu tang suy doan (doc text + khop duong) -
                    # thap hon fit-code (0.8) - xem DIM-007 confidence_gate trong rules/20_dimension.yaml.
                    prov=Provenance(source="pdf_text", confidence=0.7, page=page_no, bbox=bbox),
                )
            )
    return ket_qua
