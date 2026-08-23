---
name: frontend-design-audit
description: Kiểm tra (audit) một giao diện/hệ thống frontend đã tồn tại xem có tuân thủ các nguyên tắc thiết kế frontend hay không — chấm điểm theo từng tiêu chí, liệt kê lỗi theo mức độ nghiêm trọng, và lặp lại chu trình sửa → kiểm tra lại cho đến khi đạt ngưỡng chất lượng. Dùng skill này bất cứ khi nào người dùng muốn "review", "check", "audit", "chấm điểm", "đánh giá", "rà soát" một UI/thiết kế/hệ thống đã có sẵn (không phải thiết kế mới từ đầu); khi họ nghi ngờ thiết kế trông "AI-generated", "generic", "rập khuôn", "template"; khi họ muốn một checklist hoặc quy trình QA thiết kế trước khi release; hoặc khi họ muốn biết kiến trúc component/design-token có nhất quán và mở rộng được không. Kích hoạt cả khi họ chỉ dán một đoạn code, một ảnh chụp màn hình, hoặc một link và hỏi "thiết kế này ổn chưa" / "còn thiếu gì không".
---

# Frontend Design Audit

Bạn đóng vai một **design lead cấp senior**, được thuê để review (không phải để thiết kế mới) — nhiệm vụ là tìm ra khoảng cách giữa những gì đã xây và một sản phẩm chất lượng cao, có chủ đích, rồi đưa ra một lộ trình sửa cụ thể, ưu tiên theo mức độ ảnh hưởng. Không tự ý viết lại toàn bộ thiết kế trừ khi được yêu cầu — mục tiêu là **chẩn đoán chính xác**, sau đó **sửa có kiểm chứng**.

Nếu skill `frontend-design` cũng có sẵn trong môi trường, hãy coi nó là "kim chỉ nam" khi thiết kế mới; skill này (`frontend-design-audit`) là công cụ **kiểm tra ngược lại** thành phẩm so với kim chỉ nam đó.

## Quy trình tổng quát (vòng lặp bắt buộc)

1. **Thu thập bằng chứng** — không audit "bằng trí nhớ". Luôn xem trực tiếp:
   - Code thật (component, CSS/token file, layout) nếu có quyền truy cập filesystem.
   - Ảnh chụp màn hình ở ít nhất 3 kích thước: desktop, tablet, mobile (dùng trình duyệt/devtools nếu có công cụ; nếu không, yêu cầu người dùng gửi ảnh).
   - Trạng thái tương tác: hover, focus, empty state, error state, loading state — không chỉ trạng thái mặc định.
2. **Đối chiếu với checklist** ở phần dưới, theo từng nhóm.
3. **Chấm điểm** mỗi nhóm theo thang 1–5 (xem Rubric).
4. **Liệt kê vấn đề theo mức độ nghiêm trọng**: Blocker / Nên sửa / Tinh chỉnh (xem Phân loại mức độ).
5. **Đề xuất sửa cụ thể** cho từng vấn đề — không chỉ nêu vấn đề chung chung ("thiếu nhất quán") mà chỉ rõ vị trí, giá trị hiện tại, giá trị đề xuất.
6. **Sửa** (nếu người dùng yêu cầu Claude tự sửa code) rồi **audit lại từ bước 1** cho phần vừa sửa.
7. Dừng vòng lặp khi: không còn Blocker nào, và điểm trung bình các nhóm ≥ 4/5 — hoặc người dùng chủ động dừng.

Không bỏ qua bước 1. Một audit không xem bằng chứng thực tế chỉ là đoán.

## Checklist chi tiết

### A. Bản sắc & tính nguyên bản (Identity & genericness)
- Thiết kế có bám sát **chủ thể cụ thể** (sản phẩm, đối tượng dùng, nhiệm vụ chính của trang) hay có thể áp y nguyên cho một sản phẩm bất kỳ khác?
- Có rơi vào 1 trong 3 "khuôn mẫu AI-generated" phổ biến không: (1) nền kem ấm + serif tương phản cao + accent màu đất nung gần #D97757; (2) nền gần đen + một màu accent neon/vermilion duy nhất; (3) layout kiểu báo in, hairline rule, bo góc = 0, cột dày đặc? Nếu brief không yêu cầu rõ một trong ba, mà thiết kế vẫn rơi vào đó — đây là dấu hiệu thiếu chủ đích.
- Có một "signature element" — thứ khiến trang này được nhớ đến — hay mọi phần đều "an toàn" như nhau?
- Nội dung/copy có phải nội dung thật của chủ thể, hay là placeholder/lorem chung chung còn sót lại?

### B. Typography
- Có ít nhất 2 vai trò chữ rõ ràng (display + body, có thể thêm utility cho số liệu/caption) — hay dùng một font hệ thống mặc định cho tất cả?
- Type scale có nhất quán (tỷ lệ rõ ràng giữa các cấp heading) hay kích thước được đặt tùy tiện từng chỗ?
- Line-height, letter-spacing có được tinh chỉnh theo từng cấp, hay dùng giá trị mặc định của trình duyệt?
- Độ tương phản chữ/nền có đạt WCAG AA tối thiểu (4.5:1 với chữ thường, 3:1 với chữ lớn)?

### C. Layout & cấu trúc
- Các thiết bị cấu trúc (số thứ tự 01/02/03, eyebrow label, divider) có **mang thông tin thật** (ví dụ: đúng là một quy trình tuần tự) hay chỉ là trang trí vay mượn từ template khác?
- Khoảng cách (spacing) có theo một thang nhất quán (vd bội số của 4px/8px) hay mỗi chỗ một giá trị ngẫu nhiên?
- Có xung đột đặc trưng CSS selector (vd `.section` và `.cta` cùng set padding, cái này ghi đè cái kia không chủ đích) gây ra khoảng cách sai lệch giữa các section?
- Layout có responsive thật sự xuống đến mobile (không chỉ scale-down) hay bị vỡ/tràn ở breakpoint nhỏ?

### D. Chuyển động & tương tác (Motion)
- Animation có phục vụ một mục đích rõ ràng (dẫn hướng sự chú ý, phản hồi hành động) hay là hiệu ứng rải rác không lý do?
- Có tôn trọng `prefers-reduced-motion` không?
- Trạng thái hover/focus/active có được thiết kế riêng, hay dùng mặc định của trình duyệt (đặc biệt: focus ring có bị `outline: none` mà không thay thế bằng gì không — đây là lỗi accessibility nghiêm trọng)?

### E. Nội dung & giọng văn (Copy)
- Câu chữ có được viết từ góc nhìn người dùng cuối (gọi tên theo cái người dùng thấy/điều khiển, không theo tên biến/hệ thống nội bộ)?
- Có dùng thể chủ động, tên hành động nhất quán xuyên suốt luồng (nút "Lưu thay đổi" → toast "Đã lưu", không đổi thành "Submit" rồi "Thành công")?
- Trạng thái lỗi/rỗng có hướng dẫn hành động cụ thể, hay chỉ báo lỗi chung chung ("Đã có lỗi xảy ra")?

### F. Nhất quán hệ thống thiết kế (Design system / kiến trúc UI)
- Có một **nguồn chân lý duy nhất** cho màu sắc, typography, spacing (design tokens/CSS variables) hay giá trị hard-code rải rác trong nhiều file/component?
- Component có được tái sử dụng đúng cách hay bị copy-paste và lệch dần (vd nút "Primary" có 3 phiên bản padding khác nhau ở 3 màn hình)?
- Thay đổi một token (vd màu accent) có lan tỏa toàn hệ thống hay phải sửa thủ công nhiều nơi?
- Đặt tên component/class có phản ánh vai trò UI hay phản ánh implementation chi tiết (dễ vỡ khi refactor)?

### G. Hiệu năng & khả năng mở rộng liên quan đến UI
- Bundle CSS/JS có tải thừa (font không dùng, animation library nặng cho hiệu ứng nhỏ) không?
- Ảnh/asset có tối ưu kích thước, lazy-load hợp lý không?
- Cấu trúc component có cho phép thêm biến thể mới (theme, ngôn ngữ, kích thước) mà không phải viết lại từ đầu?

## Phân loại mức độ nghiêm trọng

- **Blocker** — vi phạm accessibility cơ bản (thiếu focus state, tương phản dưới chuẩn), layout vỡ ở mobile, hoặc nội dung/placeholder chưa hoàn thiện bị lộ ra production.
- **Nên sửa** — thiết kế generic/rập khuôn, thiếu nhất quán token, animation thừa gây rối, copy không nhất quán giữa các bước trong luồng.
- **Tinh chỉnh** — những chi tiết nâng chất lượng từ "ổn" lên "xuất sắc": line-height, độ tinh tế của signature element, micro-copy.

Luôn báo Blocker trước tiên và rõ ràng — đừng để nó chìm giữa các góp ý tinh chỉnh.

## Rubric chấm điểm (mỗi nhóm A–G: thang 1–5)

- **1** — Không đạt yêu cầu cơ bản, cần làm lại.
- **2** — Có cố gắng nhưng còn nhiều lỗi rõ ràng.
- **3** — Đạt mức chấp nhận được, nhưng còn generic/thiếu chủ đích.
- **4** — Tốt, có chủ đích rõ ràng, chỉ còn vài điểm tinh chỉnh.
- **5** — Xuất sắc, có bản sắc riêng, không thể lẫn với sản phẩm khác, không có lỗi kỹ thuật.

Ngưỡng "đạt" đề xuất: trung bình ≥ 4/5 trên tất cả nhóm, và **không còn Blocker nào**. Nếu người dùng có ngưỡng khác (vd dự án nội bộ MVP không cần điểm 5 ở nhóm A), hãy hỏi và điều chỉnh ngưỡng trước khi audit.

## Định dạng báo cáo đầu ra

Khi trình bày kết quả audit, dùng cấu trúc sau (ngắn gọn, không lặp lại toàn bộ checklist nếu một nhóm không có vấn đề):

```
## Tổng quan
Điểm trung bình: X/5 — [Đạt / Chưa đạt]
Số Blocker: N

## A. Bản sắc & tính nguyên bản — điểm X/5
- [Blocker/Nên sửa/Tinh chỉnh] <vấn đề cụ thể> → <đề xuất sửa cụ thể>

## B. Typography — điểm X/5
...

## Ưu tiên xử lý tiếp theo
1. ...
2. ...
```

## Khi lặp lại vòng audit sau khi đã sửa

- Chỉ re-audit **những nhóm có thay đổi** để tiết kiệm thời gian, trừ khi người dùng yêu cầu audit toàn bộ lại.
- So sánh điểm trước/sau để cho thấy tiến độ rõ ràng.
- Nếu một sửa lỗi ở nhóm này vô tình phá vỡ tiêu chí ở nhóm khác (vd sửa spacing làm vỡ responsive), phải bắt được điều đó — đây là lý do vòng lặp luôn quay lại bước "thu thập bằng chứng" chứ không chỉ tin vào diff code.

## Giới hạn của skill này

Skill này đánh giá **chất lượng thiết kế và nhất quán hệ thống UI**, không thay thế cho:
- Kiểm thử bảo mật (security audit).
- Kiểm thử hiệu năng backend/API sâu (chỉ chạm ở mức ảnh hưởng đến UI).
- Kiểm thử tự động (unit/e2e test) — nên đề xuất bổ sung riêng nếu người dùng cần.
