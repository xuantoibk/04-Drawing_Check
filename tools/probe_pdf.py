#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_pdf.py — Script DÒ bản vẽ PDF   |   Drawing Check / Phase 0

Mục đích: trả lời bằng SỐ LIỆU THẬT những câu mà nếu đoán sai sẽ phải viết lại
extractor. Chạy script này trên thư mục bản vẽ thật TRƯỚC KHI viết dòng code
sản phẩm đầu tiên.

Nó trả lời:
  1. PDF có text đọc được không, hay chữ đã bị biến thành nét vẽ (bẫy font SHX
     của AutoCAD) — nguyên nhân số 1 khiến dự án kiểu này vỡ ở tuần đầu.
  2. Trang là vector, là ảnh scan, hay lai.
  3. Khổ giấy, hướng giấy, góc xoay — để dựng template khung tên theo mm.
  4. Vùng góc dưới phải (khung tên theo ISO 5457 / JIS B 0001) có text không,
     và text đó trông như thế nào.
  5. Font nào đang được dùng, có font ký hiệu GD&T không (chữ sẽ ra rác).
  6. Mã bản vẽ / "Sheet 1/3" bắt được không → biết PDF nhiều trang là 1 bộ
     nhiều bản vẽ hay 1 bản vẽ nhiều tờ.
  7. Có tiếng Nhật (Kanji/Kana) trên bản vẽ không.

Cài đặt:
    pip install pdfplumber

Dùng:
    python probe_pdf.py "D:\\BanVe"                # dò cả thư mục (đệ quy)
    python probe_pdf.py "D:\\BanVe" --max 50       # giới hạn 50 file
    python probe_pdf.py file.pdf --dump-titleblock # in nguyên text khung tên
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("Thieu thu vien. Chay:  pip install pdfplumber")

PT_TO_MM = 25.4 / 72.0

# Khổ giấy ISO 216, dung sai 6mm (đủ rộng cho lề in và làm tròn của CAD)
ISO_SHEETS = {
    "A0": (841, 1189), "A1": (594, 841), "A2": (420, 594),
    "A3": (297, 420),  "A4": (210, 297), "A5": (148, 210),
}
SHEET_TOL_MM = 6.0

# Font ký hiệu GD&T / AutoCAD — chữ trích ra từ các font này sẽ là ký tự rác
# (vd 'n' = ⌀, 'j' = vị trí) vì chúng dùng bảng mã riêng, không phải Unicode.
SYMBOL_FONT_HINTS = ("gdt", "amgdt", "isocp", "isocpeur", "symap", "symath",
                     "syastro", "wingding", "webding", "cadsymbol")

# Mã bản vẽ: chuỗi in hoa/số có gạch nối, dài 6-30, phải chứa ít nhất 3 chữ số.
RE_DRAWING_NO = re.compile(r"\b[A-Z][A-Z0-9]{1,8}[-_][A-Z0-9\-_]{3,20}\b")
RE_SHEET = re.compile(r"\b(\d{1,2})\s*[/／]\s*(\d{1,2})\b")
RE_SCALE = re.compile(r"\b(\d{1,3})\s*[:：]\s*(\d{1,3})\b")
RE_REV = re.compile(r"\b(REV|Rev|rev)\.?\s*[:：]?\s*([A-Z0-9]{1,3})\b")


def mm(pts: float) -> float:
    return pts * PT_TO_MM


def detect_sheet(w_mm: float, h_mm: float) -> str:
    short, long_ = sorted((w_mm, h_mm))
    for name, (s, l) in ISO_SHEETS.items():
        if abs(short - s) <= SHEET_TOL_MM and abs(long_ - l) <= SHEET_TOL_MM:
            return name
    return f"?({short:.0f}x{long_:.0f})"


def has_cjk(text: str) -> bool:
    for ch in text:
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        if name.startswith(("CJK UNIFIED", "HIRAGANA", "KATAKANA")):
            return True
    return False


def bottom_right_text(page, frac_w=0.45, frac_h=0.35) -> str:
    """Trích text ở góc dưới phải — vị trí khung tên theo ISO 5457 / JIS B 0001."""
    x0 = page.width * (1 - frac_w)
    top = page.height * (1 - frac_h)
    try:
        crop = page.crop((x0, top, page.width, page.height))
        return crop.extract_text(x_tolerance=1.5, y_tolerance=2) or ""
    except Exception:
        return ""


def classify(n_chars: int, n_vector: int, n_images: int, img_cover: float,
             tb_chars: int = 0) -> tuple[str, str]:
    """Trả về (mã phân loại, khuyến nghị).

    tb_chars = số ký tự đọc được ở vùng khung tên. Một trang chỉ có khung tên
    (tờ tiếp theo của bản vẽ nhiều tờ) vẫn là trang TỐT, dù tổng ký tự ít.
    """
    if n_images >= 1 and img_cover > 0.55 and n_chars < 30:
        return "RASTER_SCAN", "Trang la anh scan -> bat buoc OCR (PaddleOCR-VL)"
    if n_chars >= 60 or (tb_chars >= 20 and n_chars >= 25):
        if n_images >= 1 and img_cover > 0.25:
            return "MIXED", "Vector co text + co anh chen -> doc text truoc, OCR bu vung anh"
        return "VECTOR_TEXT_OK", "TOT NHAT: doc thang text, khong can OCR"
    if n_vector > 400 and n_chars < 60:
        return "VECTOR_NO_TEXT", ("!!! BAY FONT SHX: chu da bi bien thanh net ve. "
                                  "Phai xuat lai PDF bang font TrueType, hoac OCR")
    if n_chars == 0 and n_vector < 50 and n_images == 0:
        return "EMPTY", "Trang rong hoac loi doc"
    return "LOW_TEXT", "It text bat thuong -> mo tay kiem tra trang nay"


def probe_page(page) -> dict:
    chars = page.chars or []
    n_chars = len(chars)
    n_vector = len(page.lines or []) + len(page.curves or []) + len(page.rects or [])
    images = page.images or []
    page_area = max(page.width * page.height, 1.0)
    img_cover = sum(
        abs((im.get("x1", 0) - im.get("x0", 0)) * (im.get("bottom", 0) - im.get("top", 0)))
        for im in images
    ) / page_area

    fonts = Counter(c.get("fontname", "?") for c in chars)
    symbol_fonts = sorted({
        f for f in fonts
        if any(h in f.lower() for h in SYMBOL_FONT_HINTS)
    })

    tb = bottom_right_text(page)
    full = page.extract_text(x_tolerance=1.5, y_tolerance=2) or ""

    kind, advice = classify(n_chars, n_vector, len(images), img_cover,
                            tb_chars=len(tb.strip()))

    dwg_no = RE_DRAWING_NO.findall(tb) or RE_DRAWING_NO.findall(full)
    dwg_no = [d for d in dwg_no if sum(ch.isdigit() for ch in d) >= 3]
    sheet = RE_SHEET.findall(tb)
    scale = RE_SCALE.findall(tb)
    rev = RE_REV.findall(tb)

    w_mm, h_mm = mm(page.width), mm(page.height)

    return {
        "kind": kind,
        "advice": advice,
        "sheet_size": detect_sheet(w_mm, h_mm),
        "w_mm": round(w_mm, 1),
        "h_mm": round(h_mm, 1),
        "orientation": "landscape" if page.width >= page.height else "PORTRAIT(!)",
        "rotation": page.rotation or 0,
        "n_chars": n_chars,
        "n_vector": n_vector,
        "n_images": len(images),
        "img_cover_pct": round(img_cover * 100, 1),
        "n_fonts": len(fonts),
        "top_fonts": ", ".join(f for f, _ in fonts.most_common(3)),
        "symbol_fonts": ", ".join(symbol_fonts),
        "titleblock_has_text": "YES" if len(tb.strip()) > 15 else "NO",
        "titleblock_chars": len(tb.strip()),
        "drawing_no_guess": dwg_no[0] if dwg_no else "",
        "sheet_xy": f"{sheet[0][0]}/{sheet[0][1]}" if sheet else "",
        "scale_guess": f"{scale[0][0]}:{scale[0][1]}" if scale else "",
        "rev_guess": rev[0][1] if rev else "",
        "has_japanese": "YES" if has_cjk(full) else "",
        "_tb_text": tb,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Do ban ve PDF truoc khi xay checker")
    ap.add_argument("path", help="File PDF hoac thu muc chua PDF")
    ap.add_argument("--max", type=int, default=200, help="So file toi da (mac dinh 200)")
    ap.add_argument("--out", default="probe_report.csv", help="File CSV ket qua")
    ap.add_argument("--dump-titleblock", action="store_true",
                    help="Ghi text khung tung trang ra probe_titleblocks.txt")
    args = ap.parse_args()

    root = Path(args.path)
    if root.is_file():
        pdfs = [root]
    else:
        pdfs = sorted(p for p in root.rglob("*.pdf") if p.is_file())[: args.max]

    if not pdfs:
        print(f"Khong tim thay PDF nao trong: {root}")
        return 1

    rows: list[dict] = []
    dumps: list[str] = []

    print(f"\nDang do {len(pdfs)} file PDF...\n")
    for pdf_path in pdfs:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                n_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages, start=1):
                    try:
                        r = probe_page(page)
                    except Exception as e:
                        r = {"kind": "ERROR", "advice": f"{type(e).__name__}: {e}"}
                    tb_text = r.pop("_tb_text", "")
                    r = {"file": str(pdf_path), "page": i, "pages_total": n_pages, **r}
                    rows.append(r)
                    if args.dump_titleblock:
                        dumps.append(
                            f"\n{'='*78}\n{pdf_path.name}  [trang {i}/{n_pages}]"
                            f"  {r.get('kind')}\n{'='*78}\n{tb_text}\n"
                        )
        except Exception as e:
            rows.append({"file": str(pdf_path), "page": 0, "kind": "OPEN_ERROR",
                         "advice": f"{type(e).__name__}: {e}"})

    # ---------- CSV ----------
    fieldnames = list({k for r in rows for k in r})
    order = ["file", "page", "pages_total", "kind", "sheet_size", "orientation",
             "rotation", "n_chars", "n_vector", "n_images", "img_cover_pct",
             "titleblock_has_text", "titleblock_chars", "drawing_no_guess",
             "sheet_xy", "scale_guess", "rev_guess", "has_japanese",
             "n_fonts", "top_fonts", "symbol_fonts", "w_mm", "h_mm", "advice"]
    fieldnames = [f for f in order if f in fieldnames] + \
                 [f for f in fieldnames if f not in order]
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    if args.dump_titleblock:
        Path("probe_titleblocks.txt").write_text("".join(dumps), encoding="utf-8")

    # ---------- TÓM TẮT ----------
    kinds = Counter(r.get("kind", "?") for r in rows)
    sheets = Counter(r.get("sheet_size", "?") for r in rows)
    total = len(rows)
    tb_ok = sum(1 for r in rows if r.get("titleblock_has_text") == "YES")
    dwg_ok = sum(1 for r in rows if r.get("drawing_no_guess"))
    jp = sum(1 for r in rows if r.get("has_japanese") == "YES")
    sym = sorted({s for r in rows for s in (r.get("symbol_fonts") or "").split(", ") if s})
    portrait = sum(1 for r in rows if r.get("orientation") == "PORTRAIT(!)")
    rotated = sum(1 for r in rows if r.get("rotation"))
    multi = sum(1 for r in rows if (r.get("pages_total") or 1) > 1)

    print("=" * 78)
    print(f"KET QUA DO  —  {len(pdfs)} file / {total} trang")
    print("=" * 78)
    print("\n[1] PHAN LOAI TRANG")
    for k, n in kinds.most_common():
        print(f"    {k:<18} {n:>5} trang  ({n/total*100:5.1f}%)")

    print("\n[2] KHO GIAY")
    for k, n in sheets.most_common(6):
        print(f"    {k:<18} {n:>5} trang")

    print("\n[3] KHUNG TEN (goc duoi phai)")
    print(f"    Co text doc duoc      : {tb_ok}/{total}  ({tb_ok/total*100:.1f}%)")
    print(f"    Bat duoc ma ban ve    : {dwg_ok}/{total}  ({dwg_ok/total*100:.1f}%)")

    print("\n[4] CANH BAO")
    warn = False
    n_shx = kinds.get("VECTOR_NO_TEXT", 0)
    if n_shx:
        warn = True
        print(f"    !!! {n_shx} trang dinh BAY FONT SHX (chu bien thanh net ve).")
        print("        -> Xuat lai PDF tu AutoCAD bang font TrueType (Arial/ISOCPEUR TTF),")
        print("           hoac bat 'Capture fonts as text'. Neu khong, phai OCR ca file.")
    if kinds.get("RASTER_SCAN", 0):
        warn = True
        print(f"    !!! {kinds['RASTER_SCAN']} trang la anh scan -> can OCR, de Phase 3.")
    if sym:
        warn = True
        print(f"    !!! Phat hien font ky hieu: {', '.join(sym)}")
        print("        -> Ky tu GD&T se ra RAC. Can bang anh xa glyph rieng cho font nay.")
    if portrait:
        warn = True
        print(f"    !!! {portrait} trang kho DUNG -> template khung ten phai xu ly ca 2 huong.")
    if rotated:
        warn = True
        print(f"    !!! {rotated} trang co /Rotate != 0 -> phai chuan hoa goc xoay truoc khi crop.")
    if jp:
        print(f"    (i) {jp} trang co tieng Nhat -> OCR bat buoc dung PaddleOCR-VL, khong dung Tesseract.")
    if multi:
        print(f"    (i) {multi} trang thuoc file nhieu trang -> xem cot 'drawing_no_guess'")
        print("        + 'sheet_xy' de biet la BO NHIEU BAN VE hay 1 BAN VE NHIEU TO.")
    if not warn:
        print("    Khong co canh bao nghiem trong. Duong di sach.")

    print("\n[5] KET LUAN")
    ok_ratio = (kinds.get("VECTOR_TEXT_OK", 0) + kinds.get("MIXED", 0)) / total
    if ok_ratio >= 0.9:
        print("    XANH: >=90% trang doc duoc text truc tiep. Phase 1 khong can OCR,")
        print("          khong can GPU. Uoc tinh 2-3 tuan la co ban chay duoc.")
    elif ok_ratio >= 0.6:
        print("    VANG: mot phan dang ke trang khong co text. Uu tien XU LY NGUON")
        print("          (xuat lai PDF dung font) truoc khi dau tu vao OCR.")
    else:
        print("    DO: phan lon trang khong co text. Phai giai quyet khau xuat PDF")
        print("        truoc, neu khong toan bo du an se phu thuoc vao OCR.")

    print(f"\n    Chi tiet tung trang: {args.out}")
    if args.dump_titleblock:
        print("    Text khung ten     : probe_titleblocks.txt")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
