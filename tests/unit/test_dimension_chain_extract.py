"""Test _huong_doc (extract/dimension_chain.py) - doan huong doc (ngang/doc) cua 1 buffer ky tu
da gom. Loi that (2026-08-25, trang 27 MH612, nguoi dung phat hien): so NGAN (2 chu so, vd "15")
bi doan nham la "doc" vi ham cu chi so sanh CANH TRAI giua 2 ky tu (bo sot be rong chu so cuoi),
khien "15" bien mat khoi chuoi kich thuoc (khop nham sang 1 duong doc khong lien quan)."""

from __future__ import annotations

from drawing_check.extract.dimension_chain import _huong_doc, _khop_duong


def _ky_tu(left: float, bottom: float, right: float, top: float, text: str):
    return (left, bottom, right, top, text)


def test_so_2_chu_so_ngan_van_duoc_nhan_dung_la_ngang():
    """Mo phong dung toa do that cua '15' tren trang 27 MH612: 2 ky tu gan nhau, be rong tong
    (~15.4pt) LON HON chieu cao (~11.3pt) - phai la 'ngang', khong duoc la 'doc'."""
    cac_ky_tu = [
        _ky_tu(206.968, 648.466, 213.5, 659.746, "1"),
        _ky_tu(215.0, 648.466, 222.363, 659.746, "5"),
    ]
    assert _huong_doc(cac_ky_tu) == "ngang"


def test_so_viet_doc_that_van_duoc_nhan_dung_la_doc():
    """Ky tu xep chong tu tren xuong (chieu cao tong > be rong) - phai la 'doc'."""
    cac_ky_tu = [
        _ky_tu(100.0, 220.0, 108.0, 231.0, "3"),
        _ky_tu(100.0, 205.0, 108.0, 216.0, "6"),
    ]
    assert _huong_doc(cac_ky_tu) == "doc"


def test_1_ky_tu_mac_dinh_la_ngang():
    assert _huong_doc([_ky_tu(0, 0, 8, 11, "5")]) == "ngang"


def test_khop_duong_uu_tien_duong_thuc_su_chua_thay_vi_duong_ke_ben():
    """Loi that (2026-08-25, file CYS-M1004-SC-NI-T.pdf): 3 doan lien tiep '15 | 800 | 15' cung 1
    hang - gia tri '15' ben trai (tam ~440) tung bi khop NHAM sang duong cua '800' (bien do 40pt
    cho phep ca 2 duong deu 'khop'), du duong '15' rieng cua no (415.2-466.2) THUC SU CHUA diem
    440. Phai uu tien duong THUC SU CHUA tam text truoc khi xet bien do."""
    bbox_15_trai = (434.0, 979.1, 447.3, 991.1)  # tam ~440.6
    duong = [
        (415.2, 466.2, 979.6, 1),  # duong rieng cua "15" trai - THUC SU CHUA tam_chinh
        (466.2, 1062.9, 979.6, 1),  # duong cua "800" ke ben - chi khop nho co bien do 40pt
    ]
    ket_qua = _khop_duong(bbox_15_trai, duong, True)
    assert ket_qua == ((415.2, 466.2), 979.6, 1)
