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
- **Rule engine có 3 cấp chạy riêng, không trộn lẫn** (`engine/runner.py`):
  `chay_rule_tren_trang` (rule trên 1 TRƯỜNG của 1 TRANG, dùng `PRIMITIVES` trong
  `primitives.py`), `chay_rule_tren_ban_ve` (rule trên QUAN HỆ giữa nhiều trang cùng 1
  `drawing_no`, dùng `PRIMITIVES_BAN_VE` trong `primitives_drawing.py`, chỉ gọi được SAU khi đã
  gom trang thành bản vẽ), và `chay_rule_tren_trang_kich_thuoc` (rule trên `page.dimensions` —
  1 DANH SÁCH trong 1 trang, dùng `PRIMITIVES_KICH_THUOC` trong `primitives_dimension.py`, thêm
  2026-08-24 cho Phase 3). Cả 3 loại rule cùng nằm trong `rules/*.yaml`, phân biệt bằng tên
  `check` — mỗi runner tự bỏ qua rule không thuộc phạm vi mình, không raise lỗi. Thêm rule cấp
  mới thì viết hàm trong đúng module `primitives_*.py`, đăng ký vào đúng `PRIMITIVES_*` dict.
- **Xác định trang/bản vẽ thuộc DỰ ÁN nào phải khớp theo TIỀN TỐ `project_id-`, KHÔNG khớp theo
  `drawing_no_pattern` đầy đủ** (`pipeline.py::tim_du_an_khop`, sửa 2026-08-24 sau khi phát hiện
  bug thật: khớp theo pattern đầy đủ làm "biến mất" đúng những mã ghi sai quy ước — thứ TB-002
  cần bắt lỗi — vì mã sai không khớp pattern nên bị coi "không thuộc dự án nào" rồi bị bỏ qua
  thay vì báo FAIL). Xác định dự án và kiểm tra đúng/sai định dạng PHẢI là 2 bước tách biệt.

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
- **Trang bị `/Rotate != 0` phải đọc qua `pdfplumber`, KHÔNG dùng toạ độ thô của `pypdfium2`**
  (phát hiện 2026-08-24 trên file M2613/VPK25) — `pypdfium2.get_charbox()` trả toạ độ RAW không
  khớp với `page.get_size()` trên trang xoay, trong khi `pdfplumber` tự xử lý đúng rotation. Xem
  `extract/pdf_page.py::lay_dong_tu_trong_vung_pdfplumber` — chỉ mở `pdfplumber.open()` khi CÓ
  trang xoay trong file (lazy, tránh tốn chi phí ~40x chậm hơn cho file không xoay như MH612).
- **`gom_dong()` (gom ký tự thành dòng) phải so sánh THEO CHUỖI với ký tự vừa thêm trước đó,
  KHÔNG so với ký tự đầu tiên của dòng** (sửa 2026-08-24) — so cố định với ký tự đầu gây "trôi"
  toạ độ cộng dồn qua nhiều ký tự liên tiếp (vd 2 dòng tên công ty gần khung tên), có thể vượt
  ngưỡng ngay tại ranh giới trường cần đọc, gây mất dữ liệu. Lỗi có sẵn từ Phase 1, chỉ chưa lộ
  ra vì dữ liệu MH612 không rơi đúng tình huống này.
- **Chữ số/ký hiệu TOÀN CHIỀU RỘNG kiểu Nhật (Fullwidth Forms, U+FF01-U+FF5E)** — quy ước phổ
  biến trên bản vẽ theo chuẩn JIS (vd `３０`, `－`, `．`, `Ａ` thay vì `30`, `-`, `.`, `A`). Đã
  chuẩn hoá về ASCII ngay tại nguồn đọc ký tự (`extract/pdf_page.py`, hàm
  `extract/text_utils.py::chuan_hoa_fullwidth`) — áp dụng cho MỌI extractor, không chỉ riêng
  vùng khung tên.
- **Quét TOÀN TRANG tìm dữ liệu ngoài khung tên (vd kích thước/dung sai) KHÔNG được dùng
  `lay_dong_tu_trong_vung`/`gom_dong`** — hàm đó được tinh chỉnh cho vùng khung tên HẸP, áp dụng
  trên cả trang sẽ gộp nhầm nhiều nội dung không liên quan. Phải quét thẳng theo thứ tự ký tự,
  tự gộp buffer theo khoảng cách vị trí (cả chiều ngang lẫn chiều dọc — một số ký hiệu JIS viết
  DỌC từng ký tự chồng lên nhau, không phải trái→phải). Xem `extract/dimension.py`.

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
- **11 rule khung tên (TB-001/002/003/004/005/006/007/008/011, PROJ-001/002, MS-001/002) là ĐỦ
  cho Phase 1+2 theo xác nhận của người dùng (2026-08-23)** — KHÔNG cần đạt 25-30 rule như mục
  tiêu ban đầu trong tài liệu kế hoạch, không dùng số lượng rule làm tiêu chí "xong Phase" nữa.
  (2026-08-24 có thêm DIM-001 cho Phase 3 — tổng hiện tại 14 rule, nhưng con số 11 vẫn là quyết
  định lịch sử áp dụng riêng cho phạm vi Phase 1+2 khung tên/đồng bộ nhiều tờ.)
- **Golden set giờ có 2 bộ tách biệt, tổng 130 trang** (`tests/golden/mh612/` 51 trang sạch +
  `tests/golden/m2613_vpk25/` 79 trang, thêm 2026-08-24) — cả 2 coi TẠM là tiêu chuẩn theo đồng ý
  của người dùng. Bộ M2613/VPK25 CỐ Ý có nhiều FAIL thật (69 TB-002 do lỗi đánh mã, 1 TB-011 do
  vật liệu sai quy ước) — khác bản chất với bộ MH612 (gần sạch), không được coi 2 bộ là cùng loại
  khi diễn giải kết quả. Cả 2 file PDF nguồn đều KHÔNG commit git (bí mật kinh doanh), chỉ
  `expected.yaml` được track — 2 golden test tự động skip trên máy không có bản sao file.
- **`config/projects/m2613.yaml` và `vpk25.yaml` đã được người dùng xác nhận (2026-08-24)** —
  cùng công ty Alpha Vina, cùng `standard_profile: iso`/`projection_angle: first` như MH612.
  Pattern `VPK25-M####-...` (KHÔNG có số nhánh `-01/-02/...` — các số nhánh đang thấy trên bản vẽ
  là lỗi đánh mã thật, cố ý để TB-002 bắt). Danh mục vật liệu dùng CHUNG 1 file với MH612
  (`config/catalogs/materials.yaml`), không tách riêng theo dự án.
- **`config/catalogs/iso286_letters.yaml` (bảng chữ cái lệch chuẩn + cấp chính xác ISO 286/JIS B
  0401) đã được người dùng xác nhận (2026-08-24)** — dùng cho rule DIM-001 (Phase 3, kiểm tra cú
  pháp mã lắp ghép vd "H7"/"g6"). Rule nay CHỈ kiểm tra CÚ PHÁP (chữ cái + cấp có hợp lệ không),
  KHÔNG tính giá trị dung sai số theo đường kính. Cố ý loại `X`/`x` và `R`/`r` khỏi phạm vi dò
  tìm tự động (không phải khỏi danh mục) vì trùng ký hiệu số lượng lặp/bán kính trên dữ liệu
  thật, dù cả 2 vẫn là chữ cái hợp lệ theo chuẩn. DIM-001 tạm khoá mức WARN (`confidence_gate:
  0.9`, Dimension trích ra có `confidence: 0.8`) — mới kiểm chứng 22 ví dụ thật, chưa đủ như 51
  trang khung tên MH612 trước khi cho phép lên FAIL.
- **Trích dung sai +/- riêng lẻ (khác `general_tol` khung tên) ĐÃ THỬ và BỊ RÚT LẠI (2026-08-24)**
  — logic chỉ đúng khi chữ viết dọc, sai nghiêm trọng (lệch hàng trăm lần) khi chữ viết ngang.
  KHÔNG tự làm lại theo cùng hướng tiếp cận cũ — cần phát hiện hướng chữ trước, hoặc đợi Phase 4
  (nhận diện hình ảnh). Cùng lý do, khung GD&T đầy đủ và rule chéo độ nhám↔dung sai lắp ghép được
  xác nhận KHÔNG khả thi bằng text-only trên dữ liệu hiện có (không có tín hiệu text phù hợp).
- **Định dạng trường `sheet` (số tờ) chấp nhận cả `x/y` và `x-y`** — dữ liệu thật dùng dấu gạch
  ngang (`1-1`), không phải gạch chéo như giả định ban đầu. Áp dụng nhất quán ở cả
  `core/grouping.py::tach_sheet` và `engine/checks/sheet.py`.
- **Định dạng trường `scale` (tỷ lệ) hợp lệ:** `1:x` hoặc `x:1` với x thuộc dãy số ưu tiên ISO
  (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100),
  CỘNG THÊM 4 ngoại lệ đã xác nhận với người dùng: `2:3`, `3:2`, `2:5`, `5:2`. Danh sách ngoại lệ
  có thể chưa đầy đủ nếu gặp tỷ lệ khác lạ hơn trên bản vẽ mới — hỏi lại người dùng thay vì tự
  thêm ngoại lệ.
