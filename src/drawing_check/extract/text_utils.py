"""Tien ich xu ly text dung chung cho moi extractor - hien chi co chuan hoa ky tu toan chieu
rong (fullwidth), phat hien khi lam Phase 3 (2026-08-24, xem docs/Source/Project-Remember.md).

Ban ve theo quy uoc JIS thuong dung chu so/chu cai/dau cau TOAN CHIEU RONG (Unicode block
"Fullwidth Forms", U+FF01-U+FF5E) thay vi ASCII thuong - vd "３０" thay vi "30", "－" thay vi "-".
Da kiem chung tren du lieu that: 130/130 trang deu co it nhat vai ky tu dang nay trong vung kich
thuoc/dung sai (chua tung gap trong vung khung ten nen titleblock.py chua bi anh huong, nhung nen
goi ham nay o moi noi de nhat quan, phong truong hop gap sau nay)."""

from __future__ import annotations

_LECH_FULLWIDTH = 0xFEE0  # ASCII '!'-'~' (U+0021-U+007E) + lech nay = Fullwidth Forms tuong ung


def chuan_hoa_fullwidth(text: str) -> str:
    """Doi ky tu toan chieu rong (U+FF01-U+FF5E) ve ASCII thuong, khoang trang toan chieu rong
    (U+3000, IDEOGRAPHIC SPACE) ve space thuong. Ky tu khac giu nguyen."""
    ket_qua = []
    for ch in text:
        cp = ord(ch)
        if 0xFF01 <= cp <= 0xFF5E:
            ket_qua.append(chr(cp - _LECH_FULLWIDTH))
        elif cp == 0x3000:
            ket_qua.append(" ")
        else:
            ket_qua.append(ch)
    return "".join(ket_qua)
