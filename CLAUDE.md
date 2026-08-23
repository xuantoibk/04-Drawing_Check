# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dự án: Drawing Check

Công cụ kiểm tra bản vẽ kỹ thuật (bản vẽ cơ khí xuất PDF từ CAD) tự động phát hiện lỗi khung tên,
kích thước, dung sai, GD&T, ký hiệu công nghệ — theo cả 2 chuẩn ISO/TCVN và JIS. Chạy 100% on-premise
(không gửi dữ liệu bản vẽ lên cloud — xem lý do bảo mật ở tài liệu kế hoạch).

**Trạng thái hiện tại (2026-08-22): extractor thật đã chạy ổn định trên CẢ 51 TRANG của file mẫu.**
Đã có: `pyproject.toml` + venv (`.venv/`); model dữ liệu lõi; rule engine chạy 6 rule khung tên nhóm A
(`rules/10_title_block.yaml`); CLI `typer`; 12 test `pytest` dùng dữ liệu giả — tất cả đang pass.
`extract/pdf_page.py` + `extract/titleblock.py` trích khung tên cho mẫu công ty "Alpha Vina Machinery
and Automation JSC" (CẢ khổ A3 ngang lẫn A4 đứng — 2 crop-region riêng vì bảng khung tên chiếm tỷ lệ
khác nhau theo hướng trang) — kiểm chứng trên toàn bộ `00_input/MH612-DATA GIA CONG FULL.pdf` (51
trang thật, không commit git): **drawing_no/material/scale/sheet/checked_by/approved_by/drawn_by:
51/51 đúng; title: 49/51 (2 trang thật sự để trống tên chi tiết, không phải lỗi trích xuất);
projection: 0/51 (đúng như thiết kế — ký hiệu là hình vẽ, không phải text, rule PROJ-001 tự động hạ
xuống WARN cho cả 51 trang, không có FAIL sai).** Rule engine chạy trên cả 51 trang: 0 FAIL sai, 51
WARN đúng (thiếu ký hiệu góc chiếu — cần người xem lại bằng mắt). Chạy lại bằng:
`tools/thu_nghiem_titleblock.py "00_input/..." --so-trang 51`.

**Phát hiện quan trọng cần nhớ (đã ghi vào comment trong `titleblock.py`):** (1) dấu câu/gạch ngang
trong PDF CAD có toạ độ `top` khác hẳn chữ cái cùng dòng — phải gom dòng theo baseline `bottom`; (2)
vùng crop khung tên cần TỶ LỆ KHÁC NHAU cho A3 ngang (~45% chiều rộng) và A4 đứng (~85%) — đúng "bẫy
4" đã cảnh báo trong tài liệu kế hoạch; (3) tên người ký và mã bản vẽ có thể bị tách thành nhiều
token, phải gom theo điều kiện nội dung (không chứa số / có chứa số) thay vì lấy đúng 1 token; (4)
trang 21 đọc được vật liệu `"A66061"` (thừa 1 số so với `"A6061"` thấy ở các trang khác) — đã xác minh
KHÔNG phải lỗi trích xuất (ký tự tách rời đúng khoảng cách bình thường) — nhiều khả năng là lỗi đánh
máy thật trên bản vẽ gốc, cần hỏi lại người dùng; (5) trang 35 có vài ô ngày tháng bị lỗi font ngay
trong file PDF gốc (đọc ra ký tự rác `#######`) — trường đó trả về `None`, không đoán bừa; (6) field
`revision` đôi khi đọc nhầm sang chữ ký hiệu vùng bản vẽ (`"F"`) trên trang A4 — biết nhưng CHƯA sửa
vì chưa ảnh hưởng rule nào hiện có (xem ghi chú "GIỚI HẠN ĐÃ BIẾT" trong `titleblock.py`).

**CHƯA có:** danh mục vật liệu thật (`config/catalogs/materials.yaml` rỗng — nên TB-011 chưa bật
thật), profile dự án thật cho MH612/Alpha Vina (mẫu `drawing_no` quan sát được có 4-5 đoạn, chưa chốt
regex chính thức — cần xác nhận với người dùng, không tự đặt), rule TB-014, report Excel/PDF markup,
và golden set 30-50 bản đã review thủ công (mới có 1 file/51 trang, chưa ai xác nhận đúng/sai từng
lỗi). Xem `DATA_DOC/Planer/Drawing-Check-Tien-Do.html` để theo dõi tiến độ theo Phase.

### Tài liệu gốc — đọc trước khi code bất cứ gì

`DATA_DOC/DrawingCheck_KeHoachXayDung.md` là **nguồn sự thật duy nhất** về kiến trúc, tech stack, rule
engine, lộ trình Phase và toàn bộ quyết định kỹ thuật đã chốt. Tài liệu này rất dài và chi tiết — mục
dưới đây chỉ tóm tắt phần cốt lõi để tiện tra cứu nhanh; khi có mâu thuẫn hoặc cần chi tiết (định dạng
rule YAML đầy đủ, bảng ISO/JIS, lý do chọn từng thư viện...), luôn đọc lại file gốc thay vì suy diễn.

## Nguyên tắc kiến trúc cốt lõi

```
EXTRACTOR (có thể AI) → NORMALIZED DATA (JSON/pydantic) → RULE ENGINE (thuần code) → FINDINGS (có mã)
```

- **AI chỉ trích xuất, không bao giờ phán xử.** Rule engine (Python thuần, quy tắc định nghĩa ở
  `rules/*.yaml`) là nơi duy nhất quyết định pass/fail. Mọi kết luận phải truy được về một mã quy tắc
  cụ thể (vd `TB-007`), không bao giờ "AI bảo thế".
- **3 mức kết luận, không nhị phân:** `FAIL` (chắc chắn sai, chặn duyệt) / `WARN` (nghi ngờ, cần người
  xem — mọi kết quả từ OCR/AI chỉ được dừng ở mức này) / `INFO` (ghi nhận, có thể cố ý).
- **Đơn vị xử lý cơ bản = TRANG PDF, không phải file.** Một file PDF có thể chứa nhiều bản vẽ (nhiều
  `drawing_no` khác nhau) hoặc một bản vẽ nhiều tờ (`sheet` "1/3", "2/3"...). Gom trang thành bản vẽ
  theo `drawing_no` + sắp theo `sheet` là bước bắt buộc sau khi trích xuất. Thiết kế model theo
  per-page ngay từ đầu — đổi giữa chừng phải sửa lại toàn bộ model/report/database.
- **Chỉ tiêu chất lượng là precision, không phải recall.** Báo sai một lỗi tệ hơn bỏ sót một lỗi (làm
  tăng khối lượng việc thay vì giảm). Mục tiêu Phase 1: precision ≥ 98% ở mức FAIL. Chỉ đưa vào FAIL
  những quy tắc chạy trên dữ liệu tin cậy ★★★★★ (PDF text trực tiếp), không phải OCR/AI.
- **"Drawing Document Model" (pydantic) là hợp đồng dữ liệu** giữa nửa extractor và nửa rule engine.
  Mỗi trường mang theo `Provenance` (nguồn, confidence, page, bbox) để biết kết luận đến từ đâu và vẽ
  khoanh đỏ lên PDF được. Rule engine viết một lần, không quan tâm dữ liệu đến từ PDF text hay OCR.

## Bẫy kỹ thuật đặc thù của đường PDF — phải biết trước khi đụng vào extractor

1. **Font SHX của AutoCAD** — chữ SHX khi in ra PDF biến thành nét vẽ, KHÔNG còn là text trích xuất
   được. Đây là nguyên nhân số 1 khiến extractor trả về chuỗi rỗng trên bản vẽ AutoCAD thật. Phát hiện
   bằng script probe (phân loại `VECTOR_NO_TEXT`). Cách sửa ưu tiên nhất là đổi style chữ trong
   template AutoCAD sang TrueType — việc quản lý, không phải việc code.
2. **Ký hiệu GD&T (⌀, ⊥, ⌖...) ra ký tự rác** — các font ký hiệu (GDT.shx, AMGDT) dùng bảng mã riêng,
   không phải Unicode. Cần bảng ánh xạ glyph riêng cho từng font (`config/glyphmaps/*.yaml`).
3. **Chữ bị tách rời từng ký tự** — PDF từ CAD đặt từng glyph độc lập, không có khái niệm "từ". Phải
   chỉnh `x_tolerance`/`y_tolerance` khi trích xuất, không dùng tham số mặc định.
4. **Xoay trang (`/Rotate 90`) và khổ dựng** — phải chuẩn hoá góc xoay trước khi crop vùng khung tên
   theo toạ độ mm, và template khung tên phải xử lý cả khổ ngang lẫn khổ dựng.
5. **Một file PDF ≠ một bản vẽ** — xem nguyên tắc "đơn vị xử lý = trang" ở trên.

## Tech stack đã chốt cho Phase 1 — toàn bộ license sạch, không AGPL

| Việc | Thư viện | Ghi chú |
|---|---|---|
| Ngôn ngữ | Python 3.11+ | |
| Đọc PDF (chính) | `pypdfium2` | Nhanh ~40× pdfplumber, cắt theo vùng, char bbox |
| Đọc PDF (đối chứng golden set) | `pdfplumber` | Dùng để so khớp phát hiện ca khó, KHÔNG dùng khi chạy thật |
| Khoanh đỏ / ghi chú PDF | `pypdf` | KHÔNG dùng PyMuPDF (fitz) — AGPL-3.0, ràng buộc cả khi chạy như dịch vụ mạng |
| Rule engine | `PyYAML` + `pydantic v2` | Tự viết, thuần Python |
| Xuất báo cáo | `xlsxwriter` | |
| CLI | `typer` | Lệnh dự kiến: `drawing-check run "D:\BanVe\*.pdf"` |
| Test | `pytest` | CI gate: precision tụt trên golden set → build đỏ |
| OCR (Phase 4 trở đi) | PaddleOCR-VL | Chọn vì hỗ trợ CJK tốt (bản vẽ JIS có Kanji), Tesseract không dùng |

**Tuyệt đối tránh:** PyMuPDF/fitz (AGPL), Ultralytics YOLO nếu thương mại hoá (AGPL — dùng RT-DETR
thay thế), Docling/marker/MinerU/unstructured (thiết kế cho RAG văn bản, không hợp bản vẽ kỹ thuật).

## Đa chuẩn ISO/TCVN và JIS — không hardcode

Mỗi dự án khai báo profile riêng (`config/projects/<ma_du_an>.yaml`): `standard_profile`
(iso/jis/asme), `projection_angle` (first/third), `language`, `title_block_template`,
`drawing_no_pattern`. Rule quan trọng nhất Phase 1: khung tên phải có ký hiệu góc chiếu và phải khớp
chuẩn đã khai báo cho dự án đó (`PROJ-001`, `PROJ-002`, mức Critical) — sai góc chiếu khiến xưởng gia
công lật gương toàn bộ chi tiết, phát hiện quá muộn tốn nguyên lô hàng.

## Lộ trình Phase (tóm tắt)

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Chạy `probe_pdf.py` trên bản vẽ thật, dựng golden set 30–50 bản, đo template khung tên | **Chưa chạy — làm ngay trước tiên** |
| 1 | MVP: khung tên từ PDF vector, mẫu khung tên công ty, nhóm lỗi A, CLI, 1 máy | Chưa bắt đầu |
| 2 | Thêm template khách hàng, đồng bộ nhiều tờ, rule góc chiếu | Chưa bắt đầu |
| 3 | Kích thước, dung sai, GD&T từ PDF | Chưa bắt đầu |
| 4 | Ký hiệu công nghệ + Vision (PaddleOCR-VL, RT-DETR) + bản vẽ scan — GPU vào cuộc từ đây | Chưa bắt đầu |
| 5 | Đối chiếu 3D (STEP) ↔ 2D | Chỉ lập kế hoạch, chưa triển khai |

Nhánh CAD (DXF/DWG) đang **hoãn vô thời hạn** — chỉ mở lại nếu cần bắt lỗi mà PDF không làm được
(kích thước trùng lặp, dimension override, sai layer/font — xem §1.2 tài liệu gốc).

## Cấu trúc repo hiện tại (đã tạo — khớp §11 tài liệu gốc)

```
src/drawing_check/
├── core/       # model.py, finding.py, grouping.py — ĐÃ VIẾT, có test
├── extract/    # pdf_page.py + titleblock.py ĐÃ VIẾT (mẫu Alpha Vina A3); glyphmap.py, text_utils.py chưa cần
├── vision/     # để trống tới Phase 4
├── engine/     # loader.py, runner.py, primitives.py — ĐÃ VIẾT; checks/ rỗng (chưa cần custom check)
├── report/     # excel.py, pdf_markup.py, console.py — RỖNG, chờ có Finding thật để viết/test
└── cli.py      # ĐÃ VIẾT (typer) — lệnh `version` chạy được, `run` báo rõ đang chờ Phase 0
rules/          # 10_title_block.yaml ĐÃ VIẾT (6 rule); 15_multisheet/20_dimension/30_symbols chưa có
config/         # templates/ rỗng; glyphmaps/ rỗng; catalogs/materials.yaml rỗng; projects/_vi_du.yaml (mẫu)
tools/          # probe_pdf.py, bench_pdf_libs.py — đã chuyển từ DATA_DOC/ vào đây
tests/unit/     # ĐÃ VIẾT, 12 test đang pass (factories.py + test_model/test_grouping/test_engine)
tests/golden/   # RỖNG — bắt buộc trước khi tinh chỉnh rule engine thật (§9 tài liệu gốc)
pyproject.toml  # ĐÃ TẠO — venv ở .venv/ (không commit, đã có trong .gitignore)
```

## Lệnh thường dùng

```bash
# Kich hoat venv da co san (goi truc tiep khong can activate cung duoc, vd .venv/Scripts/python.exe)
.venv/Scripts/python.exe -m pytest -q          # chay 12 test hien co
.venv/Scripts/drawing-check.exe version        # in phien ban
.venv/Scripts/drawing-check.exe run "D:\BanVe\*.pdf"  # bao dang cho Phase 0, chua chay that

# Phase 0 — dò bản vẽ thật (cần người dùng cung cấp thư mục PDF thật)
.venv/Scripts/python.exe tools/probe_pdf.py "D:\ThuMucBanVe" --dump-titleblock
.venv/Scripts/python.exe tools/bench_pdf_libs.py "D:\ThuMucBanVe"

# Thu extractor khung ten (mau Alpha Vina A3) + rule engine tren 1 file PDF that
.venv/Scripts/python.exe tools/thu_nghiem_titleblock.py "duong/dan/file.pdf" --so-trang 2

# Cài lại dependency nếu pyproject.toml đổi
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```

## Ghi nhớ (Remember) & Lịch sử triển khai (History) — docs/Source/

Cấu trúc phân tầng — tách **quyết định còn hiệu lực** (tra cứu nhanh) khỏi **tường thuật đã xảy ra**
(ít tra lại), và tách theo phạm vi ảnh hưởng (chung dự án / riêng 1 khu vực kỹ thuật). Đây là hệ
thống KHÁC với "auto-memory" toàn cục của Claude Code (lưu ở `~/.claude/projects/.../memory/`, áp
dụng cho MỌI dự án) — hệ thống dưới đây CHỈ phục vụ riêng dự án Drawing Check, nằm trong repo.

### 4 loại file, theo 5 khu vực kỹ thuật + chung dự án
Khu vực chuẩn (khớp `src/drawing_check/` — xem `master-architecture/SKILL.md`): `extract`, `engine`,
`report`, `vision`, `config`.

- **`Project-Remember.md`** — quyết định/quy tắc CÒN HIỆU LỰC, liên quan ≥2 khu vực hoặc kiến trúc
  chung (model dữ liệu, lộ trình Phase, tech stack) — LUÔN nạp đầu phiên làm việc.
- **`<khu-vuc>-Remember.md`** — quyết định/quy tắc CÒN HIỆU LỰC riêng 1 khu vực — CHỈ đọc khi có tác
  vụ liên quan trực tiếp (skill `QA-Session` tự làm việc này khi người dùng nêu vấn đề trong hội
  thoại, không cần tự tay mở file).
- **`Project-History.md`** — tường thuật kỹ thuật liên quan ≥2 khu vực hoặc vấn đề chung của dự án —
  chỉ đọc khi cần.
- **`<khu-vuc>-History.md`** — tường thuật riêng 1 khu vực — chỉ đọc khi cần.

Các file này **chưa tồn tại** (dự án chưa có phiên `/Works_End` nào chạy) — `Works_End` tự tạo khi
cần theo đúng quy trình của nó, không tự tạo trước.

### Quy tắc ghi
Mỗi khi kết thúc phiên (`/Works_End`) và soạn xong 1 mục "Nhật ký triển khai": xác định mục đó thuộc
1 khu vực cụ thể hay liên quan ≥2 khu vực/chung dự án → ghi **NGAY** vào đúng file History đích (vĩnh
viễn) → **đồng thời** giữ 1 bản sao trong CLAUDE.md đúng **24 giờ** (để tiện xem lại phiên vừa xong
mà không phải mở file khác) → phiên `/Works_End` kế tiếp tự xoá khỏi CLAUDE.md các mục đã quá 24h
(nội dung vẫn còn nguyên vẹn trong History, không mất — chỉ đổi vị trí). Quyết định quan trọng phát
sinh trong phiên còn được tổng hợp thêm 1 bản ngắn gọn vào đúng Remember đích. Xem quy trình chi tiết
tại `.claude/skills/Works_End/SKILL.md`.

### Đọc khi nào
- Đầu MỌI phiên: `Project-Remember.md` (nếu đã tồn tại).
- Khi có tác vụ liên quan trực tiếp 1 khu vực: đọc thêm đúng `<khu-vuc>-Remember.md` — skill
  `QA-Session` tự làm việc này.
- Chỉ đọc History khi cần tra lại CHI TIẾT đã làm gì/quyết định gì trong quá khứ — không đọc mặc định
  khi khảo sát/phân tích dự án.

## Ghi chú về `.claude/skills/` hiện có

Toàn bộ skill trong `.claude/skills/` (`master-architecture`, `erp-dashboard-builder`, `QA-Session`,
`Works_Start`, `Works_End`, `deployment-planner`, `commandlist`) đã được viết lại cho đúng dự án
Drawing Check (trước đó bị copy nhầm nội dung từ một dự án khác — EPR_MANAGE, hệ thống ERP
Supabase/React). `frontend-design` và `frontend-design-audit` giữ nguyên nội dung gốc vì vốn đã là
skill thẩm mỹ/audit UI tổng quát, không có nội dung riêng của EPR_MANAGE — chỉ thật sự cần dùng khi
dự án tới giai đoạn có dashboard web (Phase 6+, xem `erp-dashboard-builder/SKILL.md`), chưa áp dụng
cho Phase 1–5 (CLI thuần). `pdf` skill (`.claude/skills/pdf/`) là skill chuẩn của Claude Code, dùng
được bình thường cho các thao tác PDF chung khi Claude hỗ trợ người dùng (không thay thế logic
extractor/rule engine riêng của Drawing Check — xem phân biệt ở `master-architecture/SKILL.md` mục 2).

## Quy ước giao tiếp trong dự án

- **Luôn trao đổi bằng tiếng Việt có dấu** trong mọi câu trả lời/báo cáo ở phiên chat — kể cả khi
  không có yêu cầu rõ ràng. Không dùng thuật ngữ kỹ thuật nếu không giải thích được trong 1 câu đơn
  giản. Trả lời như báo cáo công việc, không tường thuật quá trình suy nghĩ hay bước trung gian.
- **Comment trong code: tiếng Việt KHÔNG dấu** (vd `# tinh tong toa do khung ten`, không viết
  `# tính tổng toạ độ khung tên`). Tên biến/hàm/class trong code Python: tiếng Anh chuẩn (snake_case
  cho biến/hàm, PascalCase cho class — theo PEP 8), không đặt tên tiếng Việt.
- **Không tự ý thêm tính năng/refactor ngoài phạm vi yêu cầu.** Đặc biệt quan trọng ở dự án này vì có
  rất nhiều "cạm bẫy" đã được ghi nhận sẵn trong tài liệu kế hoạch — bám sát đúng Phase đang làm, không
  nhảy cóc sang Phase sau (vd không viết OCR khi đang ở Phase 1, không train model riêng khi chưa có
  dữ liệu gán nhãn).
- **Bí mật/credentials:** không commit key/token nào vào repo (kể cả khi thêm tích hợp cloud LLM ở
  Phase 4 — công tắc gửi cloud mặc định phải TẮT, chỉ gửi text đã ẩn danh, không bao giờ gửi ảnh/PDF).
- **Định dạng ngày giờ khi người dùng nhập liệu hoặc hiển thị trên UI/báo cáo: `dd/mm/yyyy hh:mm:ss`.**
- **Định dạng ngày giờ khi đặt tên file xuất ra: `yyyymmdd-hhmmss`** — xác nhận với người dùng trước
  khi triển khai chi tiết mỗi lần có tính năng xuất file mới cần tên kèm ngày giờ.
- **Thông báo của Claude Code gửi người dùng trong phiên chat LUÔN kèm ngày giờ hiện tại ở đầu**, định
  dạng `yyyy/mm/dd hh:mm:ss: <Thông báo>` — khác với 2 định dạng ngày giờ ở trên (vốn dành cho dữ liệu/
  UI/tên file của chính ứng dụng Drawing Check).
- **Kiểm tra trước khi báo hoàn thành:** chạy `pytest` liên quan tới phần vừa sửa, không báo "Hoàn
  thành" khi còn lỗi. Với thay đổi ảnh hưởng CLI, thử chạy lệnh CLI thật trên ít nhất 1 file PDF mẫu.
- **Bối cảnh người dùng:** người yêu cầu là quản lý kỹ thuật/chủ dự án, ra quyết định nghiệp vụ và kỹ
  thuật cấp cao — KHÔNG tự đọc code, không đọc diff/log lỗi kỹ thuật. Claude Code là lập trình viên
  chính: tự triển khai, tự kiểm tra, chỉ báo cáo kết quả và những gì cần người dùng quyết định (đặc
  biệt: chọn/xác nhận template khung tên, danh mục vật liệu, ngưỡng precision chấp nhận được).
- **Dừng lại hỏi xác nhận trước khi:** thay đổi cấu trúc `DrawingDoc`/`PageDoc` đã chốt (ảnh hưởng toàn
  bộ rule engine), bật đồng loạt nhiều rule mới cùng lúc thay vì bật theo nhóm nhỏ + đo precision, xoá/
  ghi đè dữ liệu golden set, cài thêm thư viện ngoài danh sách đã chốt ở tech stack, bất kỳ thao tác
  không thể hoàn tác (git push lên remote, deploy...).

## Quy tắc quản lý file và đường dẫn

- Toàn bộ file `.md` thuộc về Claude Code (skill, agent...) phải nằm trong `.claude/` và các thư mục
  con — ngoại lệ duy nhất là chính `CLAUDE.md` ở gốc dự án.
- Mọi cấu hình/dữ liệu chỉ tham chiếu file **nằm trong thư mục dự án** — không trỏ ra ngoài trừ khi đã
  xác nhận với người dùng.
- **`DATA_DOC/` chứa tài liệu người dùng tự đưa vào, không đọc mặc định khi khảo sát dự án** — ngoại
  lệ đã áp dụng cho `DrawingCheck_KeHoachXayDung.md` (tài liệu kế hoạch gốc, đọc trực tiếp vì là nguồn
  sự thật kỹ thuật). 2 script Phase 0 (`probe_pdf.py`, `bench_pdf_libs.py`) đã chuyển ra `tools/`
  (2026-08-22) — không còn nằm ở `DATA_DOC/` nữa.

> **Ghi chú:** các mục "Nhật ký triển khai" từ đây tới cuối file có nhãn ngày trong vòng 24h gần
> nhất, tạm giữ ở đây theo đúng quy ước mới (xem mục "Ghi nhớ & Lịch sử triển khai" ở trên) — mỗi
> mục đã có bản sao vĩnh viễn tại `docs/Source/<khu-vuc>-History.md` hoặc
> `docs/Source/Project-History.md` tương ứng. Phiên `/Works_End` kế tiếp sẽ tự xoá các mục đã quá
> 24h khỏi đây (không mất nội dung, vẫn còn trong History). Dòng ghi chú này (không phải heading
> `## `, để script `quan-ly-nhat-ky.mjs` không nhầm là 1 mục nhật ký) tự xoá khi mục cuối cùng bị
> dọn hết — script tự thêm lại khi có mục mới đầu tiên sau lần dọn sạch.

## Nhật ký triển khai — Dựng khung sườn Drawing Check + extractor khung tên thật đầu tiên (2026-08-22)

Phiên đầu tiên của dự án Drawing Check: từ chỉ có tài liệu kế hoạch, dựng khung sườn code Phase 1
và viết/kiểm chứng extractor khung tên thật trên toàn bộ 1 file PDF thật do người dùng cung cấp.

### Đã hoàn thành
- Phát hiện CLAUDE.md + toàn bộ .claude/skills/ bị copy nhầm nội dung từ dự án khác (EPR_MANAGE) —
  viết lại toàn bộ cho đúng dự án Drawing Check, không xoá skill nào
- Dựng khung sườn repo: pyproject.toml, venv .venv/, cấu trúc thư mục theo §11 tài liệu kế hoạch
- Model dữ liệu lõi (core/model.py, finding.py, grouping.py), rule engine (engine/loader.py,
  runner.py, primitives.py) chạy 6 rule khung tên nhóm A, CLI typer, 12 test pytest — đều pass
- Viết extractor PDF thật đầu tiên (extract/pdf_page.py, titleblock.py) cho mẫu khung tên công ty
  "Alpha Vina Machinery and Automation JSC", hỗ trợ cả khổ A3 ngang và A4 đứng
- Kiểm chứng trên TOÀN BỘ 51 trang PDF thật (00_input/MH612-DATA GIA CONG FULL.pdf, người dùng
  cung cấp): drawing_no/material/scale/sheet/checked_by/approved_by/drawn_by đúng 51/51; title
  đúng 49/51 (2 trang trống ô này thật trên bản gốc); projection đúng đắn không đọc được (ký hiệu
  là hình vẽ, không phải text) → rule PROJ-001 tự hạ xuống WARN, không FAIL sai
- Chạy rule engine trên 51 trang: 0 FAIL sai, 51 WARN đúng
- Phát hiện 2 lỗi thật trên bản vẽ gốc (vật liệu gõ nhầm "A66061" ở trang 21, lỗi font làm hỏng
  ngày tháng ở trang 35) — người dùng đã xác nhận đây đúng là lỗi phía họ, không phải lỗi công cụ

### Quyết định quan trọng đã chốt
- **Viết lại CLAUDE.md + skills cho Drawing Check thay vì giữ nguyên bản EPR_MANAGE cũ** — Vì sao:
  file gốc bị copy nhầm dự án, phát hiện ngay khi chạy /init. Đánh đổi: giữ nguyên khung
  Remember/History nhưng đổi "8 module ERP" thành "5 khu vực kỹ thuật" (extract/engine/report/
  vision/config) cho khớp cấu trúc Drawing Check
- **Gom dòng ký tự PDF theo toạ độ baseline (bottom), không dùng top** — Vì sao: dấu câu/gạch
  ngang có toạ độ top khác hẳn chữ cái cùng dòng trên PDF CAD thật, gây tách nhầm dòng nếu gom
  theo top. Đánh đổi: không có, đây là cách đúng
- **Vùng crop khung tên dùng tỷ lệ khác nhau cho A3 (45% chiều rộng) và A4 (85%)** — Vì sao: cùng
  1 bảng khung tên nhưng chiếm tỷ lệ chiều rộng trang khác hẳn theo hướng trang (đúng "bẫy 4" đã
  cảnh báo trong tài liệu kế hoạch). Đánh đổi: phải viết 2 nhánh thay vì 1, chưa tổng quát hoá
  được cho hướng trang bất kỳ
- **Dùng pip + venv (.venv/) thay vì poetry/uv** — Vì sao: đơn giản nhất cho 1 người dùng/1 máy ở
  giai đoạn hiện tại. Đánh đổi: chưa lock version chặt như poetry, có thể đổi sau nếu cần

### Bước tiếp theo (ưu tiên phiên sau)
1. Thu thập thêm bản vẽ thật (đủ đa dạng mẫu khung tên, cả AutoCAD lẫn SolidWorks/Inventor) để mở
   rộng Phase 0 và dựng golden set 30-50 bản
2. Xác nhận danh mục vật liệu chính thức (đã thấy A6061/SPHC/SS400/POM trên bản vẽ thật) để bật
   thật rule TB-011
3. Chốt drawing_no_pattern + chuẩn ISO/JIS chính thức cho dự án MH612/Alpha Vina với người dùng
