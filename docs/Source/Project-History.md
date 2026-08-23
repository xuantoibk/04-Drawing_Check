# Lịch sử triển khai — Drawing Check (chung dự án)

Tường thuật kỹ thuật chi tiết các phiên làm việc liên quan ≥2 khu vực kỹ thuật (extract/engine/
report/vision/config) hoặc vấn đề chung của dự án (kiến trúc, quy ước, hạ tầng dùng chung). Chỉ đọc
khi cần tra lại chi tiết đã làm gì/quyết định gì trong quá khứ — không đọc mặc định khi khảo sát dự
án. Xem `CLAUDE.md` mục "Ghi nhớ & Lịch sử triển khai" để hiểu đầy đủ thiết kế hệ thống này.

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

## Nhật ký triển khai — Hoàn tất Phase 1 (CLI + Excel/PDF/golden test), bắt đầu Phase 2 (rule đồng bộ nhiều tờ) (2026-08-23)

Tiếp nối phiên trước (dựng khung sườn + extractor khung tên thật). Phiên này chốt các quyết định nghiệp vụ còn treo của Phase 1, biến CLI từ stub thành công cụ chạy thật đầu ra Excel/PDF, dựng golden test đầu tiên, mở rộng rule khung tên theo checklist người dùng, rồi bắt đầu Phase 2.

### Đã hoàn thành
- Chốt `standard_profile: iso`, `projection_angle: first`, `drawing_no_pattern` cho dự án MH612/Alpha Vina (`config/projects/mh612.yaml`), xác nhận trên bằng chứng trực tiếp từ 51/51 trang thật
- Điền danh mục vật liệu chính thức 9 mã (`config/catalogs/materials.yaml`), mở khoá rule TB-011
- Viết CLI `drawing-check run` thật: nối extractor + rule engine + config vào 1 pipeline dùng chung (`pipeline.py`), thay thế bản stub cũ
- Viết report Excel (2 sheet, tô màu theo mức độ) và PDF khoanh đỏ (annotation pypdf, dùng bbox có sẵn), xuất ra `output/<yyyymmdd-hhmmss>-...`
- Dựng golden test đầu tiên (`tests/golden/mh612/`), dùng chính file PDF 51 trang đã coi tạm là tiêu chuẩn — PDF không commit git (bí mật kinh doanh), chỉ `expected.yaml` được track, test tự skip trên máy không có file
- Thêm 5 rule khung tên mới theo checklist người dùng: TB-003/004 (tỷ lệ), TB-005 (dung sai chung), TB-006/008 (số tờ) — nâng tổng số rule khung tên từ 6 lên 11
- Phát hiện + sửa lỗi định dạng số tờ (giả định `/` sai, thực tế `-`) — đồng thời phát hiện lỗi TƯƠNG TỰ đã có sẵn từ phiên trước trong `grouping.py::tach_sheet` (âm thầm không đọc được số tờ trên dữ liệu thật từ đầu, chưa ai để ý)
- Bắt đầu Phase 2: thêm 2 rule đồng bộ nhiều tờ MS-001 (thiếu tờ)/MS-002 (revision không khớp giữa các tờ) — cơ chế rule cấp BẢN VẼ mới (`chay_rule_tren_ban_ve`), khác cơ chế cấp TRANG cũ; test bằng dữ liệu giả vì chưa có bản vẽ nhiều tờ thật

### Quyết định quan trọng đã chốt
- **11 rule khung tên là đủ cho Phase 1, bỏ mục tiêu 25-30 rule của kế hoạch gốc** — Vì sao: người dùng chủ động xác nhận. Đánh đổi: giảm độ phủ rule so với kế hoạch gốc
- **Golden set tạm dùng đúng 1 file/51 trang hiện có, coi là tiêu chuẩn tạm thời** — Vì sao: chưa có thêm bản vẽ thật đa dạng hơn. Đánh đổi: precision/recall đo được chưa đủ tin cậy như kế hoạch gốc yêu cầu (30-50 bản, nhiều mẫu/nguồn CAD)
- **Phase 1 coi là hoàn tất dù golden set còn mỏng, chuyển sang Phase 2** — Vì sao: người dùng chủ động chấp nhận đánh đổi. Đánh đổi: độ tin cậy precision/recall thấp hơn kế hoạch gốc đề ra
- **Định dạng số tờ chấp nhận cả `x/y` và `x-y`** — Vì sao: dữ liệu thật dùng `-`, người dùng xác nhận chấp nhận cả 2 để phòng dự án/khách hàng khác dùng `/`
- **Tỷ lệ (scale) hợp lệ: `x:1`/`1:x` theo dãy số ISO, cộng ngoại lệ `2:3`/`3:2`/`2:5`/`5:2`** — Vì sao: dữ liệu thật có 3 trang tỷ lệ không theo dạng `1:x`, người dùng xác nhận đây là tỷ lệ hợp lệ bổ sung, không phải lỗi. Đánh đổi: danh sách ngoại lệ có thể chưa đủ nếu gặp tỷ lệ lạ hơn

### Bước tiếp theo (ưu tiên phiên sau)
1. Chế độ "dò lỏng" theo từ khóa cho khung tên không khớp mẫu Alpha Vina đã biết (kết quả tự động ở mức WARN)
2. Thêm 3-5 mẫu khung tên khách hàng khác — cần người dùng cung cấp bản vẽ mẫu thật (PDF)
3. Mở rộng golden set — cần bản vẽ nhiều tờ thật để kiểm chứng MS-001/MS-002 (hiện chỉ test bằng dữ liệu giả), và bản vẽ đa dạng hơn (khác mẫu/nguồn CAD) để precision/recall đáng tin cậy hơn
