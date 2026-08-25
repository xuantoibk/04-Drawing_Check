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

## Nhật ký triển khai — Xử lý bản vẽ mới (M2613/VPK25), hoàn tất Phase 2, mở đầu Phase 3 (2026-08-24)

Tiếp nối phiên trước (hoàn tất Phase 1). Người dùng thêm 3 file bản vẽ mới vào `00_input/` — việc xử lý dữ liệu này lộ ra nhiều lỗi kỹ thuật thật (không phải do dữ liệu mới, mà là lỗi có sẵn từ trước chỉ chưa bị dữ liệu cũ kích hoạt), sửa xong thì hoàn tất luôn 3 mục còn lại của Phase 2. Sau đó mở đầu Phase 3 (kích thước/dung sai/GD&T), làm được đúng phần có bằng chứng thật, dừng đúng lúc ở phần rủi ro cao.

### Đã hoàn thành
- Push code lên GitHub (`https://github.com/xuantoibk/04-Drawing_Check.git`, nhánh `master`)
- Xử lý 3 file PDF mới (M2613/VPK25, 79 trang) — phát hiện và sửa 3 lỗi kỹ thuật thật:
  - Trang bị `/Rotate 90` làm `pypdfium2` đọc sai toạ độ → chuyển sang `pdfplumber` cho trang xoay
  - Lỗi `gom_dong()` (thuật toán gom dòng) so sánh với ký tự đầu tiên thay vì ký tự gần nhất, gây "trôi" toạ độ — sửa theo kiểu chuỗi liên kết
  - Cơ chế khớp dự án khớp theo *toàn bộ pattern* thay vì *tiền tố*, khiến chính các mã bản vẽ ghi sai (thứ cần bắt lỗi) bị bỏ qua thay vì báo FAIL — sửa lại khớp theo tiền tố `project_id`
- Tạo 2 profile dự án mới `m2613.yaml`, `vpk25.yaml` sau khi hỏi-đáp nghiệp vụ với người dùng (xác nhận: cùng chuẩn ISO/góc chiếu thứ nhất như MH612; các số nhánh `VPK25-01`/`VPK25-02`... là lỗi đánh mã thật, cố ý để rule bắt)
- Bổ sung 6 vật liệu mới vào danh mục chung (`AL6061`, `MIKAĐEN`, `PEEK`, `NHỰAPEEK`, `POMĐEN`, `POMTRẮNG`)
- Cài chế độ "dò lỏng" theo từ khoá (`trich_khung_ten_do_long`) + cơ chế tự động fallback khi mẫu khung tên chính không đọc được — kiểm chứng bằng test thật (monkeypatch), không chỉ chạy tay
- Mở rộng golden set: bộ thứ 2 (`m2613_vpk25/`, 79 trang, cố ý nhiều lỗi thật) bên cạnh bộ MH612 cũ (51 trang, sạch)
- Xuất thử báo cáo Excel + PDF khoanh đỏ cho toàn bộ 130 trang, gửi người dùng xem trực tiếp
- Mở đầu Phase 3: chuẩn hoá chữ số toàn chiều rộng kiểu Nhật (`text_utils.py`), trích mã lắp ghép ISO 286/JIS B 0401 (`extract/dimension.py`), tầng rule engine thứ 3 (`chay_rule_tren_trang_kich_thuoc`), danh mục `iso286_letters.yaml` (người dùng xác nhận), rule **DIM-001** — kiểm chứng đúng trên 2 điểm ngẫu nhiên đối chiếu ảnh bản vẽ thật, tạm khoá mức WARN (chưa cho FAIL) vì mới có 22 ví dụ thật
- Thử mở rộng DIM-001 sang trích dung sai +/- riêng lẻ đi kèm — phát hiện lỗi phụ thuộc hướng chữ (dọc/ngang), sai lệch hàng trăm lần trên ~1/3 ca thật → **chủ động rút lại**, không đưa số liệu sai vào hệ thống
- Khảo sát ký hiệu ren (M4Thru, M5dp10...) — người dùng xác nhận công ty không dùng cấp ren, không cần rule, dừng đúng lúc thay vì xây extractor không có nơi dùng

### Đang dang dở
Không có — mọi việc bắt đầu trong phiên đều đã hoàn thành hoặc dừng có chủ đích kèm lý do rõ ràng.

### Quyết định quan trọng đã chốt
- **VPK25/M2613 dùng CHUNG 1 mẫu khung tên với MH612** — Vì sao: đo lại chính xác bằng `pdfplumber` cho thấy tỷ lệ crop 0.45/0.20 khớp hoàn hảo, ước lượng ban đầu (~62%) chỉ là đọc nhầm ảnh phóng to. Đánh đổi: không cần thêm mẫu khung tên mới như dự tính ban đầu
- **Khớp dự án theo tiền tố `project_id`, không theo `drawing_no_pattern` đầy đủ** — Vì sao: khớp theo pattern đầy đủ vô tình làm "biến mất" đúng những lỗi cần bắt (mã ghi sai không khớp pattern → bị coi là "không thuộc dự án nào" → bỏ qua thay vì FAIL)
- **Golden set 2 bộ tách biệt** (MH612 sạch, M2613/VPK25 nhiều lỗi cố ý) — Vì sao: bảo vệ hồi quy cho cả 2 loại dữ liệu khác bản chất
- **11 rule khung tên là đủ cho Phase 1** — người dùng xác nhận, không cần đạt 25-30 rule như kế hoạch gốc
- **DIM-001 tạm khoá mức WARN** (confidence_gate=0.9, Dimension confidence=0.8) — Vì sao: mới có 22 ví dụ thật, chưa đủ kiểm chứng như 51 trang khung tên MH612 trước khi cho phép FAIL
- **Rút lại trích dung sai riêng lẻ** — Vì sao: logic chỉ đúng khi chữ viết dọc, sai nghiêm trọng (lệch hàng trăm lần) khi chữ viết ngang; dữ liệu ảnh hưởng an toàn gia công nên thà không có còn hơn sai. Điều kiện làm lại: cần phát hiện hướng chữ trước, hoặc đợi Phase 4 (nhận diện hình ảnh)
- **Không làm rule "thiếu cấp ren"** — người dùng xác nhận công ty không dùng quy ước cấp ren

### Bước tiếp theo (ưu tiên phiên sau)
1. Phase 4 (nhận diện hình ảnh) — mở khoá lại được dung sai riêng lẻ, khung GD&T, độ nhám theo bề mặt (gốc rễ chung: cần hiểu bố cục 2D thay vì đoán qua toạ độ text)
2. Thu thập thêm bản vẽ đa dạng hơn để mở rộng golden set / xác nhận thêm profile dự án khác nếu có
3. Sửa lỗi wildcard `*.pdf` trong CLI (Click tự động mở rộng dấu `*` trên Windows) — đã phát hiện, chưa sửa

## Nhật ký triển khai — Triển khai Phase 4 (Vision): hạ tầng, gán nhãn, train RT-DETR, tích hợp rule đầu tiên (2026-08-25)

Tiếp nối phiên trước (mở đầu Phase 3, dừng đúng lúc trước Phase 4). Phiên này đi hết vòng đời Phase 4 lát cắt đầu: từ dựng hạ tầng tới có 1 rule sống chạy được trên dữ liệu thật.

### Đã hoàn thành
- Lập kế hoạch chi tiết Phase 4, tách rõ Nhánh A (ký hiệu trên trang đọc text tốt — làm ngay) và Nhánh B (OCR trang scan/SHX — hoãn, chưa có dữ liệu thật)
- Cài hạ tầng: PyTorch 2.11+CUDA 12.8, PaddlePaddle-GPU+PaddleOCR, transformers (RT-DETR), Ollama+Qwen3-VL 8B, Label Studio — xác nhận chạy được trên GPU RTX 3060
- Chuyển cache AI dùng chung sang ổ G (`G:\ThuvienAI`), giải phóng ổ C từ 17GB lên ~56GB trống — áp dụng mọi dự án trên máy
- Khảo sát ảnh thật (không đoán) → chốt chỉ 2 nhóm ký hiệu cần bắt: `surface_finish`, `gdt_datum` (khác 9 nhóm đoán trong kế hoạch gốc)
- Xây công cụ render PDF→ảnh + xuất dataset COCO từ Label Studio
- Gán nhãn qua Label Studio: 130 ảnh (batch cũ) + phần lớn 125 ảnh batch mới (`00_input/joint/`, 33 file) — tổng 217+ ảnh, 616+ box
- Fine-tune RT-DETR — phát hiện lỗi phương pháp nghiêm trọng: đánh giá bằng ngưỡng cố định 0.5 khiến tưởng model "không học được gì", dẫn tới train thêm ~2.5 giờ vô ích; rà lại bằng quét nhiều ngưỡng + so sánh toàn bộ 14 checkpoint mới phát hiện model đã tốt nhất ngay từ epoch 40 của lần train ĐẦU TIÊN (F1=0.940)
- Tích hợp detector vào pipeline chính (cờ `--vision`, mặc định TẮT), rule đầu tiên **SYM-001** — kiểm chứng trên 51 trang PDF thật, đúng logic
- Phát hiện + sửa 1 lỗi thật: rule không phân biệt "vision đã chạy và không thấy gì" với "vision chưa chạy" — sửa bằng cờ context, không đổi cấu trúc PageDoc
- Viết OCR (PaddleOCR) và VLM fallback (Qwen3-VL) — VLM xác nhận hoạt động đúng; OCR bị chặn bởi xung đột phiên bản gói trên Windows
- Commit + push lên GitHub (gồm cả phần Phase 2/3 tồn đọng từ phiên trước)

### Đang dang dở
- ~38 ảnh còn lại trong project 8 Label Studio chưa gán nhãn — việc thủ công, người dùng tự làm tiếp

### Quyết định quan trọng đã chốt
- **Checkpoint tốt nhất = epoch 40 của lần train ĐẦU TIÊN**, không phải các lần train thêm sau — Vì sao: so sánh khách quan cho F1 cao nhất; train thêm gây overfit trên dữ liệu ít
- **`--vision` mặc định TẮT** — không bắt buộc GPU cho luồng Phase 1-3/golden test hiện có
- **Chỉ 2 nhóm ký hiệu, không phải 9** — bằng chứng thật, không suy đoán
- **Cache AI dùng chung tại `G:\ThuvienAI`** — áp dụng mọi dự án trên máy
- **OCR tạm hoãn** — lỗi môi trường thật, chưa có rule cần

### Bước tiếp theo (ưu tiên phiên sau)
1. Gán nốt ảnh còn lại project 8, cân nhắc train lại nếu `gdt_datum` cần thêm dữ liệu
2. Nếu cần đọc giá trị Ra/GD&T cụ thể: sửa lỗi môi trường OCR, hoặc dùng VLM fallback đã hoạt động
3. Mở rộng golden set có vision (người review thủ công đối chiếu bản vẽ gốc)
