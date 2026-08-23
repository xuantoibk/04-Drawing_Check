"""In ket qua kiem tra ra console - report dau tien cua CLI, khong phu thuoc thu vien ngoai.

Gom Finding theo drawing_no roi theo page_no, FAIL len truoc WARN/INFO trong cung 1 trang de
nguoi dung xu ly loi nghiem trong truoc. Excel/PDF markup (report/excel.py, pdf_markup.py) chua
lam trong buoc nay - cho co Finding that tu nhieu du an de biet dinh dang nao thuc su can.
"""

from __future__ import annotations

from drawing_check.core.finding import Finding

_THU_TU_LEVEL = {"FAIL": 0, "WARN": 1, "INFO": 2}


def in_bao_cao(findings: list[Finding], so_trang: int, so_ban_ve: int) -> None:
    so_luong = {"FAIL": 0, "WARN": 0, "INFO": 0}
    for f in findings:
        so_luong[f.level] += 1

    print(f"\nDa kiem tra {so_trang} trang, gom thanh {so_ban_ve} ban ve.")
    print(f"Ket qua: {so_luong['FAIL']} FAIL, {so_luong['WARN']} WARN, {so_luong['INFO']} INFO.\n")

    if not findings:
        print("Khong co phat hien nao.")
        return

    theo_ban_ve: dict[str, list[Finding]] = {}
    for f in findings:
        theo_ban_ve.setdefault(f.drawing_no or "(khong xac dinh duoc ma ban ve)", []).append(f)

    for drawing_no in sorted(theo_ban_ve):
        cac_finding = sorted(
            theo_ban_ve[drawing_no], key=lambda f: (f.page_no, _THU_TU_LEVEL[f.level])
        )
        print(f"[{drawing_no}]")
        for f in cac_finding:
            print(f"  trang {f.page_no:>3}  [{f.level:<4}] {f.rule_id:<8} {f.message_vi}")
            if f.fix_hint and f.level == "FAIL":
                print(f"              -> {f.fix_hint}")
        print()
