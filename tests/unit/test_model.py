from factories import page_mau, title_block_mau


def test_tao_page_doc_toi_thieu():
    trang = page_mau(drawing_no="KB-00123-A01", sheet="1/3")
    assert trang.title_block.drawing_no.value == "KB-00123-A01"
    assert trang.title_block.drawing_no.prov.source == "pdf_text"
    assert trang.dimensions == []


def test_field_khong_dien_van_co_provenance():
    khung_ten = title_block_mau()
    assert khung_ten.checked_by.value is None
    assert khung_ten.checked_by.prov.confidence == 1.0
