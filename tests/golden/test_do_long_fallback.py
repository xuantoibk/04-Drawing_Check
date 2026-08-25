"""Kiem chung co che fallback sang 'do long' trong pipeline.chay_1_file (2026-08-24): khi mau
Alpha Vina KHONG doc duoc ma ban ve, phai tu dong chuyen sang trich_khung_ten_do_long thay vi tra
ve None luon.

Gia lap mau chinh that bai bang monkeypatch (khong co san 1 file PDF that dung mau khung ten LA
de kiem chung tu nhien) - van chay tren PDF THAT (MH612) de trich_khung_ten_do_long co du lieu
that de quet, chi ep nhanh chinh tra ve rong."""

from __future__ import annotations

from pathlib import Path

import pytest

from drawing_check.core.model import Field, Provenance, TitleBlock
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check import pipeline

THU_MUC_GOC = Path(__file__).resolve().parents[2]
FILE_PDF = Path(__file__).resolve().parent / "mh612" / "MH612-DATA GIA CONG FULL.pdf"

pytestmark = pytest.mark.skipif(
    not FILE_PDF.exists(),
    reason="Khong co ban sao PDF khach hang tren may nay (bi mat kinh doanh, khong commit git)",
)


def _titleblock_rong(page_no: int) -> TitleBlock:
    truong_rong = Field(value=None, prov=Provenance(source="pdf_text", confidence=0.0, page=page_no))
    return TitleBlock(**{ten: truong_rong for ten in TitleBlock.model_fields})


def test_tu_dong_chuyen_sang_do_long_khi_mau_chinh_khong_doc_duoc_ma_ban_ve(monkeypatch):
    monkeypatch.setattr(
        pipeline, "trich_khung_ten_alpha_vina", lambda page, page_no, trang_pdfplumber=None: _titleblock_rong(page_no)
    )

    rules = doc_thu_muc_rule(THU_MUC_GOC / "rules")
    trang_list, _ = pipeline.chay_1_file(FILE_PDF, rules, [], {"materials": []})

    trang1 = trang_list[0]
    assert trang1.title_block.drawing_no.value == "MH612-M1001-A6-AW-P"
    assert trang1.title_block.drawing_no.prov.source == "pdf_text_loose"
