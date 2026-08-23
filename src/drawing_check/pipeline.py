"""Pipeline dung chung: doc 1 file PDF -> danh sach PageDoc + Finding.

Tach rieng khoi cli.py de dung lai duoc o golden test (tests/golden/) ma khong phai chep code -
ca 2 noi deu can dung Y HET 1 duong di extractor+rule engine de ket qua nhat quan.
"""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium

from drawing_check.core.finding import Finding
from drawing_check.core.model import PageDoc
from drawing_check.engine.loader import Rule
from drawing_check.engine.runner import chay_rule_tren_trang
from drawing_check.extract.pdf_page import tinh_hash_file
from drawing_check.extract.titleblock import phan_loai_trang_don_gian, trich_khung_ten_alpha_vina


def chay_1_file(
    duong_dan: Path, rules: list[Rule], context: dict
) -> tuple[list[PageDoc], list[Finding]]:
    """Trich khung ten (mau Alpha Vina) + chay rule tren toan bo trang cua 1 file PDF."""
    ma_file = tinh_hash_file(duong_dan)
    doc = pdfium.PdfDocument(str(duong_dan))
    n_pages = len(doc)

    trang_list: list[PageDoc] = []
    findings: list[Finding] = []
    for i in range(n_pages):
        page = doc[i]
        khung_ten = trich_khung_ten_alpha_vina(page, page_no=i + 1)
        trang = PageDoc(
            file_hash=ma_file,
            file_name=duong_dan.name,
            page_no=i + 1,
            pages_total=n_pages,
            page_kind=phan_loai_trang_don_gian(page),
            sheet_size="A3",
            rotation=page.get_rotation(),
            title_block=khung_ten,
        )
        trang_list.append(trang)
        findings.extend(chay_rule_tren_trang(trang, rules, context))
    return trang_list, findings
