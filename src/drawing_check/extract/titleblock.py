"""Trich khung ten cho mau "Alpha Vina A3/A4" - mau khung ten CONG TY duy nhat cua Phase 1
(xem DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 10 "Phase 1 chi mot mau khung ten cong ty").

Da hieu chinh + kiem chung tren CA 51 TRANG THAT: 00_input/MH612-DATA GIA CONG FULL.pdf (27 trang
A3 ngang, 24 trang A4 dung). Ca 51 trang deu VECTOR_TEXT_OK, khong dinh bay font SHX.

Phat hien quan trong khi hieu chinh tren du lieu that (ghi lai de khong quen):
- Cung 1 bang khung ten, nhung vung crop tinh tu goc duoi phai can TY LE KHAC NHAU cho A3 ngang
  (frac_w~0.45) va A4 dung (frac_w~0.85) - vi bang khung ten chiem ty le chieu rong khac han giua
  2 huong trang, dung mot ty le cho ca 2 se cat mat cot ten nguoi ky (APPROVED/CHECKED/DESIGNED)
  o trang A4. Day chinh la "bay 4" da canh bao trong tai lieu ke hoach.
- Ten nguoi ky co khi bi tach thanh nhieu token rieng ("B." "X." "TOI" thay vi "B.X.TOI") tuy
  trang - phai gom theo dieu kien "khong chua chu so" thay vi lay dung 1 token ke nhan.
- Ma ban ve cung co khi bi tach ("MH612-M101" + "1-PO-P") - gom theo dieu kien "co chua chu so",
  tim NGUOC tu nhan SHEET, vi ma ban ve luon co so con ten cong ty phia truoc thi khong.
- Truong 'title' (ten chi tiet) co the RONG that su tren ban ve (khong phai loi trich xuat) - phai
  phat hien dung truong hop nay (khong co token nao giua ngay thang va nhan QTY.) thay vi lay nham
  token ngay thang lam title.
- Mot vai trang co ky tu rac U+0023 '#' thay cho ngay thang (loi font/ToUnicode cua chinh file PDF
  goc, khong phai loi code o day) - field do se tra ve None, khong doan bua.
- Ky hieu goc chieu (PROJ-001/002) la HINH VE (cone/circle), khong phai text - KHONG trich xuat
  duoc bang duong PDF text o bat ky mau nao. Field 'projection' luon value=None, confidence thap
  de rule engine tu ha xuong WARN thay vi bao sai FAIL (xem confidence_gate trong rules yaml).

GIOI HAN DA BIET (chua sua, khong anh huong 6 rule Phase 1 hien co vi khong rule nao dung field
'revision'): tren khoang 20/51 trang thu nghiem, field 'revision' bi doc nham thanh chu cai vung
('F' - ky hieu vung A-F o le phai ban ve theo ISO 5457) thay vi gia tri that (thuong la '-'). Da
thu chan bang cach gioi han x1 nhung lam mat du lieu that cua scale/sheet o trang A3 (2 gia tri do
nam gan ria phai hon chu vung tren trang A3) nen da bo huong sua nay - can do lai toa do duong ke
bang that (thay vi crop theo ty le) khi co du nhieu trang de xac dinh chinh xac bien bang.
"""

from __future__ import annotations

import re
from typing import Callable

import pypdfium2 as pdfium

from drawing_check.core.model import Field, PageKind, Provenance, TitleBlock
from drawing_check.extract.pdf_page import Tu, lay_dong_tu_trong_vung

RE_ISO_TOL = re.compile(r"ISO\s*[\d.\-]+")
RE_CO_SO = re.compile(r"[0-9]")
RE_CHI_SO_HAI_CHAM = re.compile(r"^[\d:]+$")
RE_TEN_HOP_LE = re.compile(r"^[A-Za-z.]+$")

# Cac nhan da biet trong bang khung ten - dung de CHAN gom nham khi 1 truong bi loi/rong (vd
# ngay thang bien thanh '#######' do loi font cua chinh file PDF goc - xem docstring dau file).
NHAN_DA_BIET = {
    "APPROVED", "CHECKED", "DESIGNED", "NAME", "SIGN", "DATE", "HARDNESS", "SURF", "SURF.TRT",
    "TRT", "SCALE", "QTY", "DWG", "NO", "REV", "SHEET", "MATERIAL", "HEAT", "PROJECT",
}


def _chuan_hoa_nhan(text: str) -> str:
    return text.strip().upper().rstrip(".")


def _gom_sau_nhan(
    rows: list[list[Tu]], nhan: str, con_tiep: Callable[[Tu], bool], offset_bat_dau: int = 1
) -> list[Tu] | None:
    """Tim token khop 'nhan', gom cac token PHIA SAU (cung dong) trong khi con_tiep(token) dung."""
    muc_tieu = _chuan_hoa_nhan(nhan)
    for dong in rows:
        for idx, tu in enumerate(dong):
            if _chuan_hoa_nhan(tu.text) == muc_tieu:
                gom = []
                for tu2 in dong[idx + offset_bat_dau :]:
                    if not con_tiep(tu2):
                        break
                    gom.append(tu2)
                return gom
    return None


def _gom_truoc_nhan(
    rows: list[list[Tu]], nhan: str, con_tiep: Callable[[Tu], bool]
) -> list[Tu] | None:
    """Tim token khop 'nhan', gom cac token PHIA TRUOC (cung dong, theo dung thu tu trai->phai)
    trong khi con_tiep(token) dung - dung cho gia tri nam TRUOC nhan (vd ma ban ve truoc SHEET)."""
    muc_tieu = _chuan_hoa_nhan(nhan)
    for dong in rows:
        for idx, tu in enumerate(dong):
            if _chuan_hoa_nhan(tu.text) == muc_tieu:
                gom = []
                j = idx - 1
                while j >= 0 and con_tiep(dong[j]):
                    gom.append(dong[j])
                    j -= 1
                gom.reverse()
                return gom
    return None


def _field_tu_danh_sach(tu_list: list[Tu] | None, page_no: int, noi: str = "") -> Field[str]:
    if not tu_list:
        return Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))
    gia_tri = noi.join(t.text for t in tu_list)
    bbox = (
        min(t.left for t in tu_list), min(t.bottom for t in tu_list),
        max(t.right for t in tu_list), max(t.top for t in tu_list),
    )
    return Field(value=gia_tri, prov=Provenance(source="pdf_text", confidence=1.0, page=page_no, bbox=bbox))


def _la_manh_ten_hop_le(tu: Tu) -> bool:
    """Chi nhan token thuan chu cai/dau cham (vd 'B.', 'X.', 'TOI') VA khong trung 1 nhan da
    biet nao khac - chan truong hop gom nham ky tu rac (vd '#######' do loi font cua PDF goc)
    hoac lan sang cot ke tiep khi truong ngay thang bi hong (xem docstring dau file)."""
    return bool(RE_TEN_HOP_LE.match(tu.text)) and _chuan_hoa_nhan(tu.text) not in NHAN_DA_BIET


def _field_ten_nguoi(rows: list[list[Tu]], nhan: str, page_no: int) -> Field[str]:
    tu_list = _gom_sau_nhan(rows, nhan, _la_manh_ten_hop_le)
    return _field_tu_danh_sach(tu_list, page_no, noi="")


def _field_ma_ban_ve(rows: list[list[Tu]], page_no: int) -> Field[str]:
    tu_list = _gom_truoc_nhan(rows, "SHEET", lambda t: bool(RE_CO_SO.search(t.text)))
    return _field_tu_danh_sach(tu_list, page_no, noi="")


def _field_ty_le(rows: list[list[Tu]], page_no: int) -> Field[str]:
    tu_list = _gom_sau_nhan(rows, "SCALE", lambda t: bool(RE_CHI_SO_HAI_CHAM.match(t.text)))
    return _field_tu_danh_sach(tu_list, page_no, noi="")


def _tim_vi_tri_ngay(dong: list[Tu], bat_dau: int) -> int | None:
    """Tim vi tri token dau tien (tu 'bat_dau') co chua chu so - coi la ngay thang. Neu gap 1
    nhan da biet (vd 'NAME', 'QTY') TRUOC KHI gap chu so, coi nhu ngay thang bi hong/khong doc
    duoc (vd loi font ra '#######') va dung lai NGAY, khong doan tiep sang cot khac."""
    for j in range(bat_dau, len(dong)):
        t = dong[j]
        if _chuan_hoa_nhan(t.text) in NHAN_DA_BIET:
            return None
        if RE_CO_SO.search(t.text):
            return j
    return None


def _field_tieu_de(rows: list[list[Tu]], page_no: int) -> Field[str]:
    """Tieu de (ten chi tiet) nam giua ngay thang va nhan QTY. tren dong DESIGNED. Neu khong co
    token nao giua 2 vi tri do (hoac khong xac dinh duoc ngay thang), ban ve khong ghi ten chi
    tiet hoac khong the xac dinh chac chan - tra ve None, KHONG doan bua."""
    muc_tieu = _chuan_hoa_nhan("DESIGNED")
    for dong in rows:
        for idx, tu in enumerate(dong):
            if _chuan_hoa_nhan(tu.text) != muc_tieu:
                continue
            vi_tri_ngay = _tim_vi_tri_ngay(dong, idx + 1)
            if vi_tri_ngay is None:
                return Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))
            gom = []
            for tu2 in dong[vi_tri_ngay + 1 :]:
                if _chuan_hoa_nhan(tu2.text) == "QTY":
                    break
                gom.append(tu2)
            return _field_tu_danh_sach(gom or None, page_no, noi="")
    return Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))


def _field_don_gian(rows: list[list[Tu]], nhan: str, page_no: int) -> Field[str]:
    tu = None
    muc_tieu = _chuan_hoa_nhan(nhan)
    for dong in rows:
        for idx, t in enumerate(dong):
            if _chuan_hoa_nhan(t.text) == muc_tieu and idx + 1 < len(dong):
                tu = dong[idx + 1]
                break
        if tu:
            break
    return _field_tu_danh_sach([tu] if tu else None, page_no)


def _field_iso_tolerance(rows: list[list[Tu]], page_no: int) -> Field[str]:
    """'(ISO 2768-1)' thuong bi tach thanh 2 token ("(ISO" va "2768-1)") nen phai ghep ca dong
    lai roi moi regex, khong the khop tren tung token rieng le."""
    for dong in rows:
        text_dong = " ".join(tu.text for tu in dong)
        m = RE_ISO_TOL.search(text_dong)
        if m:
            dong_khop = [t for t in dong if "ISO" in t.text.upper() or re.match(r"[\d.\-]+\)?$", t.text)]
            return _field_tu_danh_sach(dong_khop or None, page_no, noi=" ")
    return Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))


def _vung_khung_ten(page: pdfium.PdfPage) -> tuple[float, float]:
    """Ty le vung crop tu goc duoi phai - KHAC NHAU giua A3 ngang va A4 dung (xem docstring dau file)."""
    w, h = page.get_size()
    if w >= h:  # A3 ngang (hoac kho ngang bat ky)
        return 0.45, 0.20
    return 0.85, 0.24  # A4 dung


def trich_khung_ten_alpha_vina(page: pdfium.PdfPage, page_no: int) -> TitleBlock:
    w, h = page.get_size()
    frac_w, frac_h = _vung_khung_ten(page)
    x0 = w * (1 - frac_w)
    y1 = h * frac_h
    rows = lay_dong_tu_trong_vung(page, x0, y1)

    projection_khong_doc_duoc = Field(
        value=None, prov=Provenance(source="pdf_text", confidence=0.3, page=page_no)
    )

    return TitleBlock(
        drawing_no=_field_ma_ban_ve(rows, page_no),
        title=_field_tieu_de(rows, page_no),
        material=_field_don_gian(rows, "MATERIAL", page_no),
        mass_kg=Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no)),
        scale=_field_ty_le(rows, page_no),
        revision=_field_don_gian(rows, "REV.", page_no),
        projection=projection_khong_doc_duoc,
        general_tol=_field_iso_tolerance(rows, page_no),
        unit=Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no)),
        drawn_by=_field_ten_nguoi(rows, "DESIGNED", page_no),
        checked_by=_field_ten_nguoi(rows, "CHECKED", page_no),
        approved_by=_field_ten_nguoi(rows, "APPROVED", page_no),
        date_drawn=_field_ngay_thiet_ke(rows, page_no),
        sheet=_field_don_gian(rows, "SHEET", page_no),
        size=Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no)),
    )


def _field_ngay_thiet_ke(rows: list[list[Tu]], page_no: int) -> Field[str]:
    """Ngay o dong DESIGNED - token chua chu so dau tien sau ten nguoi thiet ke, dung chung dieu
    kien dung voi _field_tieu_de (xem _tim_vi_tri_ngay) de khong doan sang cot khac khi hong."""
    muc_tieu = _chuan_hoa_nhan("DESIGNED")
    for dong in rows:
        for idx, tu in enumerate(dong):
            if _chuan_hoa_nhan(tu.text) != muc_tieu:
                continue
            vi_tri_ngay = _tim_vi_tri_ngay(dong, idx + 1)
            if vi_tri_ngay is None:
                return Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))
            return _field_tu_danh_sach([dong[vi_tri_ngay]], page_no)
    return Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))


def phan_loai_trang_don_gian(page: pdfium.PdfPage) -> PageKind:
    """Phan loai tam thoi dua tren so ky tu toan trang - se doi chieu lai voi tools/probe_pdf.py
    (Phase 0, dung cho toan bo golden set that) khi co du lieu day du hon."""
    n_chars = page.get_textpage().count_chars()
    if n_chars >= 60:
        return "vector_text_ok"
    if n_chars == 0:
        return "low_text"
    return "low_text"
