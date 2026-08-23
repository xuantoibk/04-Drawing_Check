# Ghi nhớ dự án — Drawing Check (chung dự án)

Quyết định/quy tắc CÒN HIỆU LỰC, liên quan ≥2 khu vực kỹ thuật hoặc kiến trúc chung. LUÔN nạp đầu
phiên làm việc. Xem `CLAUDE.md` mục "Ghi nhớ & Lịch sử triển khai" để hiểu đầy đủ thiết kế hệ thống
này; xem `docs/Source/Project-History.md` để đọc tường thuật chi tiết đầy đủ.

## Kiến trúc & quy ước

- **CLAUDE.md và toàn bộ `.claude/skills/` đã được viết lại cho đúng dự án Drawing Check** (trước
  đó, tính đến 2026-08-22, bị copy nhầm nội dung từ một dự án khác — EPR_MANAGE, hệ thống ERP
  Supabase/React). Không xoá skill nào, chỉ viết lại nội dung. `frontend-design`/
  `frontend-design-audit` giữ nguyên (vốn đã tổng quát); `erp-dashboard-builder` giữ lại làm tài
  liệu tham khảo cho Phase 6+ (chưa dùng ở Phase 1-5, CLI thuần không có UI).
- **5 khu vực kỹ thuật chuẩn** cho hệ thống Remember/History (thay "8 module ERP" của bản cũ):
  `extract`, `engine`, `report`, `vision`, `config` — khớp cấu trúc `src/drawing_check/`.
- **Quản lý dependency: pip + venv (`.venv/`)**, không dùng poetry/uv — chọn vì đơn giản nhất cho
  1 người dùng/1 máy ở giai đoạn hiện tại. Cài bằng `pip install -e ".[dev]"` từ `pyproject.toml`.
- **Rule engine có 2 cấp chạy riêng, không trộn lẫn:** `engine/runner.py::chay_rule_tren_trang`
  (rule trên 1 TRƯỜNG của 1 TRANG, dùng `PRIMITIVES` trong `primitives.py`) và
  `chay_rule_tren_ban_ve` (rule trên QUAN HỆ giữa nhiều trang cùng 1 `drawing_no`, dùng
  `PRIMITIVES_BAN_VE` trong `primitives_drawing.py`, chỉ gọi được SAU khi đã gom trang thành bản
  vẽ). Cả 2 loại rule cùng nằm trong `rules/*.yaml`, phân biệt bằng tên `check` — mỗi runner tự
  bỏ qua rule không thuộc phạm vi mình, không raise lỗi. Thêm rule cấp bản vẽ mới thì viết hàm
  trong `primitives_drawing.py`, đăng ký vào `PRIMITIVES_BAN_VE`.

## Kỹ thuật trích xuất PDF (áp dụng cho mọi mẫu khung tên, không riêng Alpha Vina)

- **Gom dòng ký tự PDF theo toạ độ baseline (`bottom`), không dùng `top`.** Dấu câu/gạch ngang có
  `top` khác hẳn chữ cái cùng dòng trên PDF CAD thật (đã kiểm chứng), gây tách nhầm dòng nếu gom
  theo `top`. Xem `extract/pdf_page.py` hàm `gom_dong`.
- **Vùng crop khung tên cần TỶ LỆ KHÁC NHAU theo hướng trang** — đã kiểm chứng trên mẫu Alpha Vina:
  A3 ngang ~45% chiều rộng trang, A4 đứng ~85%. Đây là "bẫy 4" (xoay trang/khổ dựng) đã cảnh báo
  trong `DATA_DOC/DrawingCheck_KeHoachXayDung.md` — mẫu khung tên khác có thể cần tỷ lệ khác, phải
  đo lại bằng ảnh render (không suy diễn từ mẫu Alpha Vina).
- **Tên người ký và mã bản vẽ có thể bị tách thành nhiều token** trên cùng 1 hàng — phải gom theo
  ĐIỀU KIỆN NỘI DUNG (không chứa chữ số → tên người; có chứa chữ số → mã bản vẽ/ngày tháng), không
  lấy cứng đúng 1 token kế nhãn. Xem `extract/titleblock.py` các hàm `_gom_sau_nhan`/`_gom_truoc_nhan`.
- **Ký hiệu góc chiếu (PROJ-001/002) là HÌNH VẼ, không phải text** — không đọc được bằng đường PDF
  text ở BẤT KỲ mẫu khung tên nào (đã xác nhận, không riêng Alpha Vina). Field `projection` phải
  luôn trả `value=None` kèm `confidence` thấp; rule PROJ-001/002 phải có `confidence_gate` để tự hạ
  xuống WARN, không được để rơi vào FAIL.
- **Không đoán bừa khi dữ liệu mơ hồ/hỏng** — nếu 1 trường có thể lẫn với trường khác (vd tiêu đề
  chi tiết trống lẫn với ngày tháng, hoặc lỗi font PDF gốc ra ký tự rác `#`), trả về `None` thay vì
  đoán giá trị gần đúng. Đã kiểm chứng cách này đúng trên dữ liệu thật (2 trường hợp thật ở trang
  35/41 của file mẫu MH612).

## Trạng thái dữ liệu thật đã có

- Đã kiểm chứng extractor + rule engine trên 51/51 trang PDF thật (1 file, mẫu khung tên công ty
  "Alpha Vina Machinery and Automation JSC", dự án MH612) — 0 finding báo sai. Chi tiết đầy đủ ở
  `docs/Source/Project-History.md`.
- **`config/projects/mh612.yaml` và `config/catalogs/materials.yaml` ĐÃ được người dùng xác nhận
  chính thức (2026-08-23)** — không còn là quan sát tạm: `standard_profile: iso` (bằng chứng trực
  tiếp "(ISO 2768-1)" trên 51/51 trang), `projection_angle: first` (người dùng xác nhận trực tiếp,
  KHÔNG đọc được từ PDF), `drawing_no_pattern` dạng `MH612-M####-<mã vật liệu>-[<mã xử lý bề
  mặt>]-<P|L|H|T>` (đoạn xử lý bề mặt tuỳ chọn), 9 mã vật liệu chính thức (A6061/SPHC/POM/SS400/
  A5052/SUS201/SUS303/SUS304/S45C). Chỉ dựa trên 1 file/1 khách hàng — cần đối chiếu lại khi có
  dự án/khách hàng khác, KHÔNG suy diễn áp dụng thẳng cho khách hàng khác.
- **11 rule khung tên hiện có (TB-001/002/003/004/005/006/007/008/011, PROJ-001/002, MS-001/002)
  là ĐỦ cho Phase 1+2 theo xác nhận của người dùng (2026-08-23)** — KHÔNG cần đạt 25-30 rule như
  mục tiêu ban đầu trong tài liệu kế hoạch. Khi đánh giá "Phase 1 đã xong chưa", không dùng tiêu
  chí số lượng rule làm chuẩn nữa.
- **Golden set (`tests/golden/mh612/`) vẫn chỉ có 1 file/51 trang/1 mẫu khung tên/1 nguồn CAD** —
  người dùng đồng ý coi tạm là tiêu chuẩn (2026-08-23), Phase 1 được coi là hoàn tất dù golden set
  còn mỏng. Con số "0 FAIL sai"/precision đo được CHỈ đáng tin trên đúng file này — không suy rộng
  ra "công cụ đã đạt precision 98%" cho dữ liệu khác khi chưa kiểm chứng thêm. File PDF nguồn
  KHÔNG commit git (bí mật kinh doanh, xem `.gitignore`), chỉ `expected.yaml` được track — golden
  test (`tests/golden/test_mh612.py`) tự động skip trên máy không có bản sao file.
- **Định dạng trường `sheet` (số tờ) chấp nhận cả `x/y` và `x-y`** — dữ liệu thật dùng dấu gạch
  ngang (`1-1`), không phải gạch chéo như giả định ban đầu. Áp dụng nhất quán ở cả
  `core/grouping.py::tach_sheet` và `engine/checks/sheet.py`.
- **Định dạng trường `scale` (tỷ lệ) hợp lệ:** `1:x` hoặc `x:1` với x thuộc dãy số ưu tiên ISO
  (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100),
  CỘNG THÊM 4 ngoại lệ đã xác nhận với người dùng: `2:3`, `3:2`, `2:5`, `5:2`. Danh sách ngoại lệ
  có thể chưa đầy đủ nếu gặp tỷ lệ khác lạ hơn trên bản vẽ mới — hỏi lại người dùng thay vì tự
  thêm ngoại lệ.
