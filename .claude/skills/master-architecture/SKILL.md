---
name: master-architecture
description: Kiến trúc kỹ thuật gốc của toàn bộ dự án Drawing Check PHẢI tham chiếu và tuân theo tài liệu này, không được định nghĩa lại kiến trúc.
---

# Master Skill — Kiến trúc tổng dự án Drawing Check

Tài liệu này là nguồn sự thật duy nhất (single source of truth) về kiến trúc kỹ thuật của dự án
**Drawing Check** — công cụ kiểm tra bản vẽ kỹ thuật (PDF) tự động. Khi tạo skill con cho từng khu
vực kỹ thuật (extract/engine/report/vision), skill con chỉ mô tả logic riêng của khu vực đó và
**luôn dẫn ngược lại file này** cho phần stack/quy tắc chung. Tài liệu kế hoạch đầy đủ (lý do chọn
từng quyết định, bẫy kỹ thuật, lộ trình Phase, định dạng rule YAML chi tiết...) nằm ở
`DATA_DOC/DrawingCheck_KeHoachXayDung.md` — file này chỉ tóm tắt phần cần tra cứu nhanh khi code.

## 0. Trạng thái triển khai hiện tại (cập nhật 2026-08-22)

Đã dựng khung sườn: `pyproject.toml` + venv (`.venv/`), model dữ liệu lõi (`core/`), rule engine
(`engine/loader.py`/`runner.py`/`primitives.py`) chạy được 6 rule khung tên, CLI `typer`, 12 test
`pytest` (dữ liệu giả, đang pass). Đã có extractor thật đầu tiên (`extract/pdf_page.py` +
`extract/titleblock.py`) cho ĐÚNG 1 mẫu khung tên ("Alpha Vina Machinery and Automation JSC", A3
ngang) — đã kiểm chứng trên 2 trang PDF thật do người dùng cung cấp, trích đúng hầu hết field trừ
`projection` (ký hiệu góc chiếu là đồ hoạ, không phải text — cố tình để confidence thấp, không đoán
bừa). 2 script Phase 0 (`probe_pdf.py`, `bench_pdf_libs.py`) đã chuyển vào `tools/`; thêm
`tools/thu_nghiem_titleblock.py` (công cụ dev chạy extractor+rule engine trên 1 file thật).
**Việc bắt buộc trước khi làm tiếp** (mở rộng extractor sang mẫu khác, danh mục vật liệu thật, report,
golden set): cần thêm bản vẽ thật (đủ đa dạng mẫu khung tên, cả AutoCAD lẫn SolidWorks/Inventor) và
xác nhận nghiệp vụ (danh mục vật liệu, mẫu drawing_no chuẩn, profile ISO/JIS) từ người dùng — xem chi
tiết đầy đủ ở CLAUDE.md mục "Trạng thái hiện tại" và `DATA_DOC/Planer/Drawing-Check-Tien-Do.html`.

## 0.1 Ngăn xếp đã chốt cho Phase 1

- Ngôn ngữ: Python 3.11+.
- Đọc PDF (chính): `pypdfium2`. Đối chứng golden set: `pdfplumber` (không dùng khi chạy thật).
- Khoanh đỏ/ghi chú PDF: `pypdf`. **Không dùng PyMuPDF/fitz** (AGPL-3.0 — ràng buộc cả khi chạy như
  dịch vụ mạng, không phù hợp nếu sau này có web dashboard).
- Rule engine: Python thuần + `PyYAML` + `pydantic v2`, tự viết — không dùng framework rule engine
  ngoài.
- Xuất báo cáo: `xlsxwriter` (Excel), PDF markup qua `pypdf`.
- CLI: `typer`.
- Test: `pytest`, có gate precision trên golden set (build đỏ nếu precision tụt).

**Đã có quyết định mặc định (chưa xác nhận chính thức với chủ dự án, có thể đổi nếu cần):**
- Quản lý dependency: `pip` cài kiểu editable (`pip install -e ".[dev]"`) từ `pyproject.toml`, venv
  ở `.venv/` (không commit) — chưa dùng `poetry`/`uv`, chọn vì đơn giản nhất cho 1 máy/1 người dùng.

**Chưa chốt — hỏi và xác nhận với chủ dự án trước khi đụng tới**, không tự suy diễn:
- Chiến lược logging chi tiết (mức độ, định dạng, có ghi file log hay chỉ console).
- Toàn bộ stack cho Phase 4+ (OCR/vision) và Phase 6+ (dashboard web nếu có người dùng thứ hai) —
  các skill `erp-dashboard-builder`, `frontend-design`, `frontend-design-audit` trong dự án chỉ áp
  dụng KHI tới giai đoạn đó, không áp dụng cho Phase 1–5 (CLI thuần, không có UI).

## 1. Quy tắc đặt tên

- Module/file Python: `snake_case.py` (vd `pdf_page.py`, `titleblock.py`).
- Hàm/biến Python: `snake_case` tiếng Anh chuẩn PEP 8 (vd `extract_title_block`, `page_kind`).
- Class/pydantic model: `PascalCase` (vd `PageDoc`, `DrawingDoc`, `TitleBlock`, `Provenance`).
- Comment trong code: tiếng Việt KHÔNG dấu (vd `# gom trang theo drawing_no`).
- File rule YAML: `rules/NN_ten_nhom.yaml` (số thứ tự 2 chữ số + tên nhóm, vd `10_title_block.yaml`,
  `20_dimension.yaml`). Mã quy tắc (`id`) trong mỗi file: tiền tố viết hoa + số 3 chữ số (vd `TB-007`,
  `PROJ-002`, `DIM-009`) — tiền tố đặt theo nhóm (`TB` = title block, `PROJ` = projection, `DIM` =
  dimension, `SUR` = surface, `WLD` = weld, `THR` = thread).
- File config: `config/templates/*.yaml` (toạ độ khung tên theo mm), `config/glyphmaps/*.yaml` (ánh
  xạ font ký hiệu), `config/catalogs/*.yaml` (danh mục vật liệu/ren/dung sai), `config/projects/*.yaml`
  (profile chuẩn ISO/JIS theo từng dự án khách hàng).

## 2. Skill hỗ trợ sẵn có trong dự án

- **`pdf`** (`.claude/skills/pdf/SKILL.md`) — skill chuẩn của Claude Code (pypdf, pdfplumber,
  reportlab, poppler-utils...) để CHÍNH Claude Code xử lý file PDF khi hỗ trợ người dùng (đọc tài
  liệu, tạo file tham khảo). Đây KHÔNG phải thư viện chạy trong extractor sản phẩm của Drawing Check
  — extractor sản phẩm dùng đúng `pypdfium2`/`pypdf`/`pdfplumber` đã chốt ở mục 0.1, không lẫn với
  công cụ hỗ trợ Claude này. Lưu ý môi trường máy hiện tại: gói Python cho skill `pdf` (pypdf,
  pdfplumber, reportlab...) CHƯA được cài sẵn, cần `pip install` trước khi dùng lần đầu; trong Bash
  tool ở máy này lệnh `python`/`python3` trỏ vào Windows Store alias không chạy được, phải gọi bằng
  `py`.
- **`erp-dashboard-builder`, `frontend-design`, `frontend-design-audit`** — chỉ liên quan khi dự án
  tới giai đoạn có dashboard web (ngoài lộ trình Phase 0–5 hiện tại, chỉ mở khi có người dùng thứ
  hai — xem tài liệu kế hoạch §12). Không dùng cho công việc CLI/extractor/rule engine hiện tại.

## 3. Nguyên tắc bắt buộc khi code bất kỳ phần nào của pipeline

- **AI chỉ trích xuất, rule engine phán xử** — không để logic pass/fail nằm trong code extractor hay
  trong prompt AI. Mọi kết luận phải truy được về 1 mã quy tắc trong `rules/*.yaml`.
- **Đơn vị xử lý = trang PDF**, gom thành bản vẽ theo `drawing_no` + `sheet` sau khi trích xuất xong
  toàn bộ trang — không xử lý theo file.
- **3 mức kết luận** `FAIL`/`WARN`/`INFO` — không bao giờ để kết quả từ OCR/AI rơi vào `FAIL`.
- **`Provenance`** (source, confidence, page, bbox) đi kèm mọi field trong `PageDoc`/`DrawingDoc` —
  không bỏ field này khi thêm field mới vào model.

## 4. Ràng buộc cho skill con theo khu vực kỹ thuật (extract/engine/report/vision)

- Chỉ định nghĩa: logic trích xuất riêng của khu vực đó, quy tắc nghiệp vụ cụ thể (nhóm rule nào),
  bẫy kỹ thuật đặc thù của khu vực (vd bẫy font SHX thuộc `extract`).
- KHÔNG được định nghĩa lại tech stack, model dữ liệu (`PageDoc`/`DrawingDoc`), hay quy tắc đặt tên —
  luôn tham chiếu ngược lại file này (`.claude/skills/master-architecture/SKILL.md`).
