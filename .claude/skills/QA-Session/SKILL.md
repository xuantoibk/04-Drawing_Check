---
name: QA-Session
description: Tự động tra cứu ghi nhớ dự án (Remember) trước khi trả lời — kích hoạt khi người dùng nêu vấn đề/câu hỏi về nghiệp vụ, quyết định kiến trúc, hoặc "vì sao hệ thống làm theo cách này/vấn đề này nên xử lý sao". Đọc Project-Remember.md + <khu-vuc>-Remember.md liên quan, tổng hợp đưa vào hội thoại cho người dùng kiểm tra, lặp lại cho các câu hỏi tiếp theo tới khi người dùng yêu cầu dừng. KHÔNG nạp toàn bộ History vào context. Gọi bằng "QA Session" hoặc tự động khi phù hợp.
disable-model-invocation: false
---

# 🔎 QA Session — Tự động tra cứu Ghi nhớ dự án trước khi trả lời

Skill này giúp câu trả lời của Claude bám sát các quyết định/quy tắc **đã chốt trước đó** trong dự
án Drawing Check, thay vì chỉ suy luận từ code hiện tại hoặc trả lời chung chung — bằng cách tra cứu
`docs/Source/Project-Remember.md` + `docs/Source/<khu-vuc>-Remember.md` liên quan NGAY TRƯỚC khi trả
lời câu hỏi/vấn đề người dùng nêu ra.

Đây là "phía đọc" của cặp cơ chế Remember/History — "phía ghi" là skill `Works_End` (xem
`.claude/skills/Works_End/SKILL.md`). Không sửa tay bất kỳ file `*-Remember.md`/`*-History.md` nào từ
skill này — skill này CHỈ ĐỌC.

**Lưu ý trạng thái hiện tại:** dự án chưa có dòng code sản phẩm nào, nên các file
`docs/Source/*-Remember.md`/`*-History.md` có thể chưa tồn tại — nếu vậy, coi như "chưa có ghi nhớ
áp dụng" và trả lời bình thường (không chặn câu trả lời chỉ vì thiếu file).

---

## Khi nào kích hoạt

Tự động cân nhắc dùng skill này (không cần người dùng gõ lệnh riêng) khi tin nhắn của người dùng
thuộc 1 trong các dạng sau:
- Hỏi **"vì sao"/"tại sao"** hệ thống/khu vực kỹ thuật nào đó hoạt động theo 1 cách cụ thể.
- Nêu **1 vấn đề/lỗi/băn khoăn** và cần Claude đề xuất hướng xử lý (trước khi đề xuất, nên biết đã
  từng quyết định gì liên quan trước đó, tránh đề xuất lại thứ đã bị bác bỏ hoặc mâu thuẫn quyết định
  cũ) — vd đã từng thử một cách trích xuất glyph GD&T mà không hiệu quả, hoặc đã chốt ngưỡng
  `confidence_gate` cho 1 rule cụ thể.
- Hỏi về **quy tắc/ràng buộc nghiệp vụ** của 1 khu vực kỹ thuật cụ thể (vd "Rule engine có cho phép
  1 rule vừa FAIL vừa áp dụng cho cả ISO lẫn JIS không?", "Golden set hiện có bao nhiêu bản JIS?").
- Câu hỏi mang tính **thảo luận/ra quyết định**, không phải yêu cầu code trực tiếp một tính năng đã
  rõ đặc tả.

KHÔNG cần kích hoạt cho: yêu cầu thực thi rõ ràng không cần bối cảnh quyết định cũ (vd "sửa lỗi
typo dòng X", "chạy pytest giúp tôi"), câu trả lời ngắn kiểu xác nhận ("ok", "làm đi"), hoặc khi người
dùng đã yêu cầu dừng tra cứu (xem mục "Dừng lại" bên dưới).

## Quy trình

### Bước 1: Xác định phạm vi câu hỏi
Đọc câu hỏi/vấn đề, xác định thuộc khu vực kỹ thuật nào trong 5 khu vực chuẩn của Drawing Check
(khớp với cấu trúc `src/drawing_check/` — xem `master-architecture/SKILL.md`):
- `extract` — trích xuất PDF, phân loại trang, khung tên, glyphmap, bẫy font SHX.
- `engine` — rule engine, định dạng YAML, primitives, checks tuỳ biến.
- `report` — xuất Excel, khoanh đỏ PDF, console output.
- `vision` — OCR/detection Phase 4 (PaddleOCR-VL, RT-DETR, VLM fallback).
- `config` — template khung tên (mm), danh mục vật liệu/ren/dung sai, profile dự án ISO/JIS.

Hay là câu hỏi chung/liên quan nhiều khu vực (model dữ liệu `PageDoc`/`DrawingDoc`, lộ trình Phase,
tech stack, golden set, nguyên tắc AI-trích-xuất/rule-engine-phán-xử...)?

### Bước 2: Đọc Remember liên quan (KHÔNG đọc History ở bước này)
- Luôn đọc `docs/Source/Project-Remember.md` nếu đã tồn tại (thường đã nạp sẵn đầu phiên — chỉ đọc
  lại nếu nghi ngờ đã lỗi thời hoặc chưa từng đọc trong phiên này).
- Nếu xác định được khu vực cụ thể ở Bước 1: đọc thêm `docs/Source/<khu-vuc>-Remember.md` nếu tồn
  tại.
- Nếu KHÔNG chắc chắn thuộc khu vực nào: đọc thử 1-2 file `<khu-vuc>-Remember.md` có khả năng liên
  quan nhất thay vì đọc cả 5 file — nếu vẫn không tìm thấy gì liên quan, coi như "chưa có ghi nhớ áp
  dụng", không cố đọc hết toàn bộ 5 file cho 1 câu hỏi hẹp.
- Nếu file Remember chưa tồn tại hoặc đang rỗng: bỏ qua, không chặn bước trả lời tiếp theo.

### Bước 3: Chỉ đọc thêm History khi Remember không đủ trả lời
Remember chỉ ghi "quyết định còn hiệu lực", không có diễn biến/lý do chi tiết đầy đủ. Nếu câu hỏi cần
biết **đã xảy ra chuyện gì, khi nào, chi tiết kỹ thuật ra sao** (không chỉ "hiện đang thế nào"):
- Dùng **Grep** (không phải Read nguyên file) trên đúng `docs/Source/<khu-vuc>-History.md` hoặc
  `docs/Source/Project-History.md` đã xác định (nếu tồn tại), tìm từ khoá liên quan tới câu hỏi, lấy
  vài dòng ngữ cảnh (`-C` 10-20 dòng) quanh chỗ khớp.
- Nếu Grep khớp nhiều chỗ, đọc thêm bằng Read với `offset`/`limit` đúng đoạn cần, KHÔNG đọc nguyên
  file hàng nghìn dòng vào context.
- Không bao giờ đọc toàn bộ 1 file `*-History.md` chỉ để "cho chắc" — nếu Grep không ra kết quả liên
  quan, coi như không tìm thấy tiền lệ, nói rõ điều đó với người dùng thay vì im lặng bỏ qua bước tra
  cứu.

### Bước 4: Tổng hợp & đưa vào hội thoại
Trước khi trả lời chính (hoặc lồng ngay đầu câu trả lời), tóm tắt ngắn gọn những gì tìm được, theo
đúng giọng văn báo cáo đã quy định ở CLAUDE.md mục "Quy ước giao tiếp trong dự án" (không thuật ngữ
kỹ thuật khó hiểu, không dán nguyên văn Markdown thô của file Remember/History — diễn giải lại bằng
lời). Ví dụ:

```
Theo ghi nhớ dự án (khu vực extract): trước đây đã quyết định KHÔNG render trang ra ảnh để OCR nếu
trang đó đã có text layer — chỉ dùng OCR khi text layer thật sự rỗng (bẫy SHX). [Trả lời/đề xuất
chính dựa trên nền đó...]
```

Nếu không tìm thấy gì liên quan trong Remember lẫn History: nói ngắn 1 câu ("Chưa có ghi nhớ nào về
việc này trong dự án") rồi trả lời bằng hiểu biết thông thường (đọc code/tài liệu kế hoạch nếu cần)
— KHÔNG để việc "không tìm thấy" chặn đứng câu trả lời.

### Bước 5: Lặp lại cho các câu hỏi tiếp theo
Áp dụng lại đúng quy trình Bước 1-4 cho MỖI câu hỏi/vấn đề mới người dùng nêu trong cùng phiên, không
chỉ 1 lần đầu — cho tới khi người dùng yêu cầu dừng.

### Dừng lại
Khi người dùng nói rõ kiểu "không cần tra cứu nữa", "trả lời bình thường thôi", "khỏi cần đọc
Remember" — ngừng tự động kích hoạt skill này cho phần còn lại của phiên (vẫn có thể áp dụng lại nếu
người dùng chủ động gọi lại "QA Session").

---

## Giới hạn có chủ đích

- Skill này **không ghi** gì — mọi cập nhật Remember/History luôn qua `/Works_End`.
- Không tự ý coi Remember là "chân lý tuyệt đối không cần kiểm chứng" — nếu Remember nhắc tới 1
  file/hàm/rule cụ thể, vẫn nên xác nhận nó còn tồn tại (đọc code thật) trước khi dựa vào đó để đề
  xuất hành động thật, đúng nguyên tắc chung "trước khi khuyến nghị từ ghi nhớ, phải xác minh vẫn còn
  đúng ở hiện tại".
- Không đọc `DATA_DOC/` hay các nội dung nằm ngoài phạm vi `docs/Source/*-Remember.md`/
  `*-History.md` — các ngoại lệ khác của dự án (vd tài liệu kế hoạch gốc, script Phase 0) không thuộc
  phạm vi tra cứu của skill này.
