# CLAUDE.md

Hướng dẫn cho Claude Code khi làm việc trong repo này.

## 1. Dự án: Drawing Check

Công cụ tự động kiểm tra bản vẽ kỹ thuật cơ khí (PDF xuất từ CAD): khung tên, kích thước, dung sai,
GD&T, ký hiệu công nghệ — theo cả ISO/TCVN và JIS. Chạy 100% trên máy nội bộ, không gửi dữ liệu bản
vẽ lên cloud.

- **Nguồn sự thật kỹ thuật duy nhất:** `DATA_DOC/DrawingCheck_KeHoachXayDung.md` (kiến trúc, tech
  stack, định dạng rule YAML, bảng ISO/JIS, lộ trình). Khi mâu thuẫn hoặc cần chi tiết → đọc file gốc,
  không suy diễn.
- **Quyết định kỹ thuật còn hiệu lực:** `docs/Source/Project-Remember.md` — đọc đầu MỌI phiên.

### Trạng thái hiện tại

17 rule đang chạy: khung tên `TB-001..008, TB-011`, góc chiếu `PROJ-001/002`, nhiều tờ `MS-001/002`,
kích thước `DIM-001/002/007`, ký hiệu `SYM-001`. Golden set 130 trang thật (MH612 51 trang + M2613/VPK25
79 trang — PDF không commit git, test tự skip khi thiếu file). Profile dự án đã xác nhận: `mh612`,
`m2613`, `vpk25` (mẫu khung tên Alpha Vina). Tiến độ chi tiết: `DATA_DOC/Planer/Drawing-Check-Tien-Do.html`.

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Dò bản vẽ thật, dựng golden set, đo template khung tên | Xong |
| 1 | MVP khung tên từ PDF vector, CLI, Excel + PDF khoanh đỏ | Xong |
| 2 | Đồng bộ nhiều tờ, rule góc chiếu, dự án mới | Xong với mẫu Alpha Vina — mẫu khách hàng khác chờ dữ liệu |
| 3 | Kích thước, dung sai, GD&T từ PDF | Đang làm |
| 4 | Ký hiệu công nghệ + Vision (RT-DETR, PaddleOCR, Qwen3-VL) + bản vẽ scan | Đang làm (nhánh A xong; nhánh B scan/SHX hoãn) |
| 5 | Đối chiếu 3D (STEP) ↔ 2D | Chỉ lập kế hoạch |

Nhánh CAD (DXF/DWG) **hoãn vô thời hạn** — chỉ mở lại khi cần bắt lỗi mà PDF không làm được.

## 2. Nguyên tắc kiến trúc cốt lõi

```
EXTRACTOR (có thể AI) → NORMALIZED DATA (pydantic) → RULE ENGINE (thuần code) → FINDINGS (có mã)
```

- **AI chỉ trích xuất, không phán xử.** Chỉ rule engine (`rules/*.yaml` + Python) quyết định
  pass/fail; mọi kết luận truy được về 1 mã rule (vd `TB-007`).
- **3 mức kết luận:** `FAIL` (chắc chắn sai) / `WARN` (nghi ngờ — mọi kết quả từ OCR/AI chỉ dừng ở
  đây) / `INFO` (ghi nhận).
- **Đơn vị xử lý = TRANG PDF.** 1 file có thể chứa nhiều bản vẽ hoặc 1 bản vẽ nhiều tờ; gom trang
  theo `drawing_no` + sắp theo `sheet` sau khi trích xuất.
- **Ưu tiên precision hơn recall** (báo sai tệ hơn bỏ sót). FAIL chỉ dùng dữ liệu tin cậy cao (PDF
  text trực tiếp), mục tiêu precision ≥ 98%.
- **Model `DrawingDoc`/`PageDoc` là hợp đồng dữ liệu**; mỗi trường mang `Provenance` (nguồn,
  confidence, page, bbox) để truy nguồn và vẽ khoanh đỏ.
- **Không hardcode chuẩn:** mỗi dự án có `config/projects/<ma_du_an>.yaml` (`standard_profile`,
  `projection_angle`, `language`, `title_block_template`, `drawing_no_pattern`).

### Bẫy kỹ thuật của đường PDF (đọc trước khi sửa extractor)

1. **Font SHX của AutoCAD** in ra PDF thành nét vẽ, không còn text → extractor trả rỗng.
2. **Ký hiệu GD&T (⌀, ⊥, ⌖...)** ra ký tự rác — cần bảng ánh xạ glyph theo font (`config/glyphmaps/`).
3. **Chữ tách rời từng ký tự** — phải chỉnh `x_tolerance`/`y_tolerance`, không dùng mặc định.
4. **Trang xoay `/Rotate` và khổ dựng** — chuẩn hoá góc xoay trước khi crop; A3 ngang và A4 đứng cần
   tỷ lệ crop khác nhau.
5. **1 file PDF ≠ 1 bản vẽ** (xem nguyên tắc trên).

Các phát hiện chi tiết đã kiểm chứng (gom dòng theo baseline, trang xoay đọc qua pdfplumber, chữ số
toàn chiều rộng kiểu Nhật, ngưỡng RT-DETR...) nằm trong `docs/Source/Project-Remember.md`.

### Tech stack đã chốt — license sạch, không AGPL

| Việc | Thư viện |
|---|---|
| Ngôn ngữ / quản lý gói | Python 3.11+, pip + venv (`.venv/`) |
| Đọc PDF | `pypdfium2` (chính), `pdfplumber` (trang xoay + đối chứng) |
| Khoanh đỏ PDF | `pypdf` |
| Rule engine | `PyYAML` + `pydantic v2` |
| Báo cáo / CLI / Test | `xlsxwriter` / `typer` / `pytest` |
| Vision (nhóm `[vision]`) | `torch` + `torchvision` bản CUDA 12.8 (cài trước, từ index `download.pytorch.org/whl/cu128`), `transformers` (RT-DETR), `paddlepaddle` 3.3.1 CPU + `paddleocr`, Qwen3-VL qua Ollama |

**Tuyệt đối tránh:** PyMuPDF/fitz và Ultralytics YOLO (AGPL), Docling/marker/MinerU/unstructured
(thiết kế cho văn bản, không hợp bản vẽ).

## 3. Cấu trúc repo & lệnh thường dùng

```
src/drawing_check/
├── core/      # model.py, finding.py, grouping.py
├── extract/   # pdf_page.py, titleblock.py, dimension.py, dimension_chain.py, text_utils.py
├── engine/    # loader.py, runner.py, primitives*.py, checks/
├── vision/    # detector.py (RT-DETR), projection_symbol.py, ocr.py, vlm_fallback.py
├── report/    # console.py, excel.py, pdf_markup.py
├── pipeline.py
└── cli.py
rules/         # 10_title_block, 15_multisheet, 20_dimension, 30_symbols (.yaml)
config/        # projects/, catalogs/ (materials, iso286_letters), vision/
tools/         # probe/bench PDF, render ảnh gán nhãn, train/so sánh checkpoint RT-DETR
tests/         # unit/ + golden/ (chỉ commit expected.yaml)
```

Không commit git (bí mật kinh doanh / file lớn): `00_input/`, `output/`, `models/`,
`01_vision_labeling/`, `tests/golden/**/*.pdf`, `.venv/`.

```bash
.venv/Scripts/python.exe -m pip install -e ".[dev]"          # cai goi chinh + test
.venv/Scripts/python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/python.exe -m pip install -e ".[dev,vision]"   # them goi Vision (nang, vai GB)
.venv/Scripts/python.exe -m pytest -q                        # chay toan bo test
.venv/Scripts/drawing-check.exe run "D:\BanVe\*.pdf"         # chay kiem tra (--vision mac dinh TAT)
.venv/Scripts/python.exe tools/thu_nghiem_titleblock.py "file.pdf" --so-trang 2
```

## 4. Quy ước giao tiếp trong dự án

- **Luôn dùng tiếng Việt có dấu** trong mọi câu trả lời, báo cáo, tài liệu, commit message, PR
  description — trừ khi người dùng chủ động hỏi bằng tiếng Anh.
- **Không dùng thuật ngữ kỹ thuật** nếu không giải thích được trong 1 câu đơn giản.
- **Trả lời như báo cáo công việc**, không tường thuật quá trình suy nghĩ hay bước trung gian.
- **Mỗi thông báo trong phiên chat bắt đầu bằng ngày giờ hiện tại:** `yyyy/mm/dd hh:mm:ss: <Thông báo>`.
- **Bối cảnh người dùng:** quản lý kỹ thuật/chủ dự án, ra quyết định cấp cao, KHÔNG đọc code/diff/log.
  Claude Code là lập trình viên chính: tự triển khai, tự kiểm tra, chỉ báo kết quả và những gì cần
  người dùng quyết định (template khung tên, danh mục vật liệu, ngưỡng precision...).

## 5. Quy ước code & làm việc

- **Comment trong code: tiếng Việt KHÔNG dấu** (vd `# tinh tong toa do khung ten`).
- **Tên biến/hàm/class: tiếng Anh theo PEP 8** (snake_case cho biến/hàm, PascalCase cho class).
- **Tên file ảnh/tài liệu tự tạo:** chữ thường, không dấu, nối gạch ngang (vd `man-hinh-chinh.png`).
- **Không tự thêm tính năng/refactor ngoài phạm vi yêu cầu**, bám đúng Phase đang làm, không nhảy cóc
  (vd không train model khi chưa có dữ liệu gán nhãn).
- **Làm song song** các việc độc lập; chỉ làm tuần tự khi việc sau cần kết quả việc trước hoặc công
  cụ chỉ cho 1 luồng.
- **Bí mật:** không ghi mật khẩu/khoá API/token vào bất kỳ file nào. Tích hợp cloud LLM (nếu có) mặc
  định TẮT, chỉ gửi text đã ẩn danh, không bao giờ gửi ảnh/PDF bản vẽ.
- **Tự kiểm tra trước khi báo hoàn thành:** chạy `pytest` liên quan; thay đổi ảnh hưởng CLI thì chạy
  CLI thật trên ≥1 file PDF mẫu; mở lại file đầu ra (đúng cấu trúc, không vỡ dấu tiếng Việt). Chưa có
  dữ liệu thật thì dùng dữ liệu giả lập; chưa mở được bằng Excel/PDF reader thật thì nói rõ trong báo cáo.
- **Dừng lại hỏi xác nhận trước khi:** đổi cấu trúc `DrawingDoc`/`PageDoc`; bật đồng loạt nhiều rule
  mới (phải bật theo nhóm nhỏ + đo precision); xoá/ghi đè golden set; cài thư viện ngoài tech stack đã
  chốt; mọi thao tác không hoàn tác được (git push, deploy...).

### Định dạng ngày giờ

| Dùng cho | Định dạng |
|---|---|
| Thông báo của Claude Code trong phiên chat | `yyyy/mm/dd hh:mm:ss: ...` |
| Hiển thị trong báo cáo/tài liệu/UI của Drawing Check | `dd/mm/yyyy` (kèm `hh:mm:ss` khi cần giờ) |
| Tên file xuất ra, bản backup | `<ten-file>_yyyymmdd-hhmmss` — hỏi xác nhận trước mỗi tính năng xuất file mới |

## 6. Lập kế hoạch triển khai

- **Yêu cầu từ 2 bước trở lên:** tạo bảng theo dõi, cập nhật đúng dòng khi xong (không tạo bảng mới,
  không lặp lại cả bảng nếu không cần):

  | # | Việc cần làm | Trạng thái | % |
  |---|---|---|---|

  Trạng thái: Chưa làm / Đang làm / Xong / Lỗi / Chờ xác nhận.
- **Việc lớn, nhiều bước, cần chia giai đoạn** (hoặc người dùng yêu cầu "lập kế hoạch"/"plan"): sau
  khi phân tích xong, bắt buộc dùng skill `deployment-planner` — chia Phase 0.x chuẩn bị / 1.x triển
  khai / 2.x kiểm thử, mỗi phase có mô tả, checkbox, ước lượng thời gian. Không áp dụng cho sửa lỗi nhỏ
  hay thay đổi 1-2 file.
- **File kế hoạch** (html/excel/word...) lưu tại `DATA_DOC/Planer/`, KHÔNG đưa lên web (kể cả Artifact
  của tài khoản Claude) trừ khi người dùng xác nhận trực tiếp.

## 7. Quản lý file & đường dẫn

- **File `.md` của Claude Code** (skill, agent...) nằm trong `.claude/`; ngoại lệ: `CLAUDE.md` ở gốc và
  `docs/Source/` (tài liệu tra cứu cho người dùng).
- **Mọi cấu hình/dữ liệu chỉ trỏ tới file trong thư mục dự án.** Ngoại lệ đã chốt:
  - Thư viện dùng chung cài thêm (kể cả Python: `D:\Claude\Library\Python312`) và cache thư viện AI
    dùng chung toàn máy: `D:\Claude\Library` — thư mục con `huggingface`, `torch`, `pip-cache`,
    `ollama-models`, `paddlex` (biến `HF_HOME`, `TORCH_HOME`, `PIP_CACHE_DIR`, `OLLAMA_MODELS`,
    `PADDLE_PDX_CACHE_HOME`, cấp User). Ollama: `D:\Claude\Library\Ollama`; Label Studio: môi
    trường Python riêng `D:\Claude\Library\label-studio` (chạy `Scripts\label-studio.exe start`,
    dữ liệu gán nhãn giữ mặc định `%LOCALAPPDATA%\label-studio` vì `tools/export_vision_dataset.py`
    đọc từ đó).
  - Dữ liệu chạy tạm (JSON trung gian, file thử): `D:\Claude\Claude_temp`, dọn sau khi chạy xong.
  - Đường dẫn ngoài dự án mới khác → hỏi xác nhận trước, rồi bổ sung vào danh sách này.
- **`DATA_DOC/`** chứa tài liệu người dùng đưa vào — KHÔNG đọc mặc định khi khảo sát dự án, chỉ đọc
  file cụ thể khi được yêu cầu. Ngoại lệ: `DrawingCheck_KeHoachXayDung.md` (nguồn sự thật kỹ thuật).
- **Backup trước khi ghi đè file trong `docs/Source/`** (nếu file đã tồn tại): chép vào
  `DATA_DOC/Source_bak/<Tên file>_<yyyymmdd-hhmmss>_bak.md` — tự động, không cần hỏi.

## 8. Ghi nhớ (Remember) & Lịch sử triển khai (History) — `docs/Source/`

Hệ thống riêng của dự án (khác auto-memory toàn cục của Claude Code). Chia theo 5 khu vực kỹ thuật
khớp `src/drawing_check/`: `extract`, `engine`, `report`, `vision`, `config`.

| File | Nội dung | Khi nào đọc |
|---|---|---|
| `Project-Remember.md` | Quyết định còn hiệu lực, liên quan ≥2 khu vực/kiến trúc chung | Đầu mọi phiên |
| `<khu-vuc>-Remember.md` | Quyết định còn hiệu lực của 1 khu vực | Khi có tác vụ liên quan (skill `QA-Session` tự đọc) |
| `Project-History.md`, `<khu-vuc>-History.md` | Tường thuật đã làm | Chỉ khi cần tra chi tiết quá khứ |

File `<khu-vuc>-*` chưa tồn tại thì `/Works_End` tự tạo khi cần.

**Quy tắc ghi (qua `/Works_End`, xem `.claude/skills/Works_End/SKILL.md`):** mỗi mục "Nhật ký triển
khai" ghi ngay vào History đích (vĩnh viễn), đồng thời giữ bản sao ở cuối CLAUDE.md đúng 24 giờ; lần
`/Works_End` sau tự dọn mục quá hạn (script `quan-ly-nhat-ky.mjs`). Quyết định quan trọng tóm tắt
thêm vào Remember tương ứng.

## 9. Skill trong `.claude/skills/`

`Works_Start`, `Works_End`, `QA-Session`, `deployment-planner`, `master-architecture`, `commandlist`
viết riêng cho Drawing Check. `pdf` là skill PDF chung (không thay logic extractor/rule engine).
`erp-dashboard-builder`, `frontend-design`, `frontend-design-audit` chỉ dùng từ Phase 6+ (khi có web
dashboard) — chưa áp dụng cho Phase 1–5 (CLI thuần).
