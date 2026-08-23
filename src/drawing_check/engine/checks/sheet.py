"""Custom check cho truong sheet (so to ban ve) - dinh dang "x/y" hoac "x-y" voi 1<=x<=y. Khong
dien ta duoc bang field_matches (regex thuan) vi phai so sanh SO HOC giua x va y, khong chi
kiem tra dinh dang chuoi.

Du lieu that tren 00_input/MH612-DATA GIA CONG FULL.pdf dung dau gach ngang (vd "1-1"), khong
phai gach cheo nhu gia dinh ban dau khi viet rule nay - chap nhan ca 2 dang theo xac nhan cua
nguoi dung 2026-08-23, phong truong hop du an/khach hang khac dung dau "/"."""

from __future__ import annotations

import re

from drawing_check.core.model import Field

_MAU_SO_TO = re.compile(r"^(\d+)[/-](\d+)$")


def sheet_khong_hop_le(field: Field, params: dict, context: dict) -> bool:
    if field.value is None:
        return False
    khop = _MAU_SO_TO.fullmatch(str(field.value))
    if not khop:
        return True
    to_hien_tai, tong_so_to = int(khop.group(1)), int(khop.group(2))
    return not (1 <= to_hien_tai <= tong_so_to)
