---
name: erp-dashboard-builder
description: Tham khảo khi xây dựng màn hình bảng điều khiển (dashboard) cho Drawing Check — CHỈ áp dụng ở Phase 6+ (khi có người dùng thứ hai, dự án chuyển từ CLI 1 máy sang có web dashboard). Gợi ý bộ KPI, biểu đồ, bộ lọc theo dữ liệu findings/rule engine. Không tự chốt thư viện hay schema — mọi quyết định về stack vẫn theo master-architecture/SKILL.md.
disable-model-invocation: false
---

# Bảng điều khiển cho Drawing Check (Phase 6+ — chưa tới lượt)

**Chưa áp dụng ở giai đoạn hiện tại.** Theo lộ trình đã chốt (`DATA_DOC/DrawingCheck_KeHoachXayDung.md`
§10/§12), Phase 1–5 chỉ là CLI chạy trên 1 máy, không có dashboard/web — dashboard "rơi khỏi đường
găng", chỉ xây khi có người dùng thứ hai. Skill này giữ lại làm tài liệu tham khảo cho lúc đó, **không
tự ý xây dashboard nếu người dùng chưa xác nhận dự án đã tới giai đoạn đa người dùng.**

Khi thật sự tới lúc xây dashboard, skill này chỉ đóng vai trò **gợi ý nội dung** (KPI nào, biểu đồ
nào, lọc theo gì) — không tự quyết định công nghệ, không tạo sẵn code mẫu. Luôn:
- Lấy quyết định stack (framework web, thư viện biểu đồ, CSDL — SQLite hay chuyển PostgreSQL) từ
  `.claude/skills/master-architecture/SKILL.md` khi mục đó đã được cập nhật cho Phase 6 — **không**
  tự thêm thư viện mới nếu chưa được xác nhận với người dùng.
- Nguồn dữ liệu là `Finding`/`DrawingDoc` do rule engine sinh ra (SQLite ở Phase 2+, có thể chuyển
  PostgreSQL khi nhiều người dùng) — không phải dữ liệu nghiệp vụ ERP (không có khái niệm bán hàng/
  kho/nhân sự trong dự án này).

## Cách dùng

Khi tới lúc thiết kế dashboard thật, hỏi rõ:
1. Dùng cho vai trò nào? (Người vẽ / Người kiểm tra (checker) / Quản lý kỹ thuật) — quyết định phạm
   vi dữ liệu được xem.
2. Cần so sánh nhiều dự án khách hàng (nhiều `standard_profile` ISO/JIS khác nhau) không?
3. Dữ liệu giả (mock) để dựng UI trước, hay đã có `findings` thật từ rule engine chạy trên golden set/
   dữ liệu thật?

Sau đó chọn KPI/biểu đồ/bộ lọc gợi ý bên dưới làm điểm khởi đầu, điều chỉnh theo đúng nhu cầu thật.

## Gợi ý KPI/biểu đồ theo dữ liệu Drawing Check

### Chất lượng công cụ (quan trọng nhất — xem §8 tài liệu kế hoạch)
- KPI: precision ở mức FAIL (mục tiêu ≥98%), tỷ lệ "báo sai" do người dùng bấm nút phản hồi, recall
  trên golden set.
- Biểu đồ: precision theo thời gian (mỗi lần bật thêm nhóm rule mới), tỷ lệ báo sai theo mã quy tắc
  (`rule_id`) — để biết rule nào đang gây phiền, không phải để phạt người báo sai.
- Bộ lọc: khoảng thời gian, nhóm rule (title_block/dimension/symbols), mức tin cậy (FAIL/WARN/INFO).

### Tổng quan bản vẽ đã kiểm tra
- KPI: số bản vẽ đã chạy trong kỳ, số bản vẽ có ít nhất 1 FAIL, tỷ lệ đạt ngay lần đầu (không có
  FAIL), thời gian xử lý trung bình/bản vẽ.
- Biểu đồ: số bản vẽ theo trạng thái (Đạt / Có lỗi Critical / Có lỗi Major / Chỉ có WARN), xu hướng
  số lượng bản vẽ xử lý theo tuần.
- Bộ lọc: khoảng thời gian, dự án khách hàng, nguồn xuất PDF (AutoCAD/SolidWorks/Inventor...), chuẩn
  (ISO/TCVN hay JIS).

### Phân tích lỗi
- KPI: top 5 mã quy tắc (`rule_id`) vi phạm nhiều nhất, tỷ lệ lỗi theo mức nghiêm trọng
  (Critical/Major/Minor), tỷ lệ lỗi theo nhóm (khung tên/kích thước-dung sai-GD&T/ký hiệu công nghệ).
- Biểu đồ: Pareto lỗi theo `rule_id`, phân bố Critical/Major/Minor theo thời gian, so sánh tỷ lệ lỗi
  giữa các dự án khách hàng hoặc giữa 2 chuẩn ISO/JIS.
- Bộ lọc: dự án khách hàng, nhóm rule, mức nghiêm trọng, khoảng thời gian.

### Vận hành pipeline (nếu có hàng đợi/nhiều máy ở Phase 6+)
- KPI: thời gian xử lý trung bình/trang, tỷ lệ trang rơi vào `VECTOR_NO_TEXT` (bẫy SHX) hoặc
  `RASTER_SCAN` cần OCR (Phase 4+), tỷ lệ trang cần VLM fallback.
- Biểu đồ: phân loại `page_kind` theo thời gian, thời gian xử lý theo `page_kind`.
- Bộ lọc: khoảng thời gian, dự án khách hàng, nguồn xuất PDF.

## Kiểm soát theo vai trò (khung tham khảo, chưa chốt)

| Vai trò | Phạm vi dữ liệu dự kiến |
|---|---|
| Người vẽ (drawn_by) | Chỉ bản vẽ do chính mình vẽ |
| Người kiểm tra (checker) | Bản vẽ được giao kiểm tra |
| Quản lý kỹ thuật | Toàn bộ bản vẽ, xem được số liệu chất lượng công cụ (precision/báo sai) |

Đây chỉ là khung tham khảo — RBAC thật (nếu Phase 6 cần) phải được xác nhận với người dùng trước khi
triển khai, không suy diễn từ bảng này. Nhắc lại nguyên tắc §13 tài liệu kế hoạch: **không dùng thống
kê lỗi để đánh giá/phạt nhân viên** — chỉ dùng để tìm lỗ hổng đào tạo, nếu dashboard hiển thị số liệu
theo người vẽ thì phải nêu rõ mục đích này trong UI.
