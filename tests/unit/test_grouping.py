from drawing_check.core.grouping import gom_trang_thanh_ban_ve, tach_sheet
from factories import page_mau


def test_tach_sheet_hop_le():
    assert tach_sheet("2/3") == (2, 3)


def test_tach_sheet_khong_khop():
    assert tach_sheet(None) == (None, None)
    assert tach_sheet("khong ro") == (None, None)


def test_gom_nhieu_to_cung_1_ban_ve_va_sap_dung_thu_tu():
    to_3 = page_mau(page_no=3, drawing_no="KB-001", sheet="3/3")
    to_1 = page_mau(page_no=1, drawing_no="KB-001", sheet="1/3")
    to_2 = page_mau(page_no=2, drawing_no="KB-001", sheet="2/3")

    ket_qua = gom_trang_thanh_ban_ve([to_3, to_1, to_2])

    assert len(ket_qua) == 1
    ban_ve = ket_qua[0]
    assert ban_ve.drawing_no == "KB-001"
    assert ban_ve.sheets_expected == 3
    assert ban_ve.sheets_found == 3
    assert [t.page_no for t in ban_ve.pages] == [1, 2, 3]


def test_gom_2_ban_ve_khac_ma_trong_1_lan_chay():
    a = page_mau(page_no=1, drawing_no="KB-001", sheet="1/1")
    b = page_mau(page_no=2, drawing_no="KB-002", sheet="1/1")

    ket_qua = gom_trang_thanh_ban_ve([a, b])

    ma_cac_ban_ve = {bv.drawing_no for bv in ket_qua}
    assert ma_cac_ban_ve == {"KB-001", "KB-002"}


def test_trang_khong_co_ma_ban_ve_bi_bo_qua():
    thieu_ma = page_mau(page_no=1)  # drawing_no = None
    co_ma = page_mau(page_no=2, drawing_no="KB-001", sheet="1/1")

    ket_qua = gom_trang_thanh_ban_ve([thieu_ma, co_ma])

    assert len(ket_qua) == 1
    assert ket_qua[0].drawing_no == "KB-001"
