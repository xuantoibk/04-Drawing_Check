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
- **Danh mục vật liệu, `drawing_no_pattern`, và profile chuẩn ISO/JIS cho dự án MH612/Alpha Vina
  CHƯA được người dùng xác nhận chính thức** — đã QUAN SÁT thấy vật liệu A6061/SPHC/SS400/POM và
  dạng mã "MH612-M####-VẬTLIỆU-XỬLÝ-P/L" trên bản vẽ thật, nhưng KHÔNG được tự ý đưa vào
  `config/catalogs/materials.yaml` hay `config/projects/*.yaml` như dữ liệu chính thức nếu chưa hỏi
  lại người dùng — quan sát từ 1 file chưa chắc đại diện cho toàn bộ vật liệu/mẫu mã công ty dùng.
