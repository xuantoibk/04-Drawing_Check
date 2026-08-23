---
name: Works_Start
description: Bắt đầu phiên làm việc có cấu trúc — đọc mục "Nhật ký triển khai" gần nhất trong CLAUDE.md, xác nhận trạng thái/ưu tiên đợt trước, hỏi focus task hôm nay, kiểm tra git status/dependencies. Gọi bằng "/Works_Start" hoặc "Works_Start".
disable-model-invocation: false
---

# 🚀 Works_Start — Bắt đầu phiên làm việc

Skill này giúp bạn bắt đầu một phiên làm việc có cấu trúc: nắm lại trạng thái đợt trước, xác nhận
focus hôm nay, và chuẩn bị môi trường — trước khi bắt tay vào code.

Đây là nửa "đầu phiên" của cặp skill `Works_Start`/`Works_End`. Khi kết thúc phiên, dùng skill
`Works_End`.

---

## 📖 CÁCH SỬ DỤNG

```bash
/Works_Start
```

---

## 🔄 WORKFLOW CHI TIẾT

### Bước 1: Kiểm tra CLAUDE.md tồn tại
```bash
test -f CLAUDE.md && echo "CLAUDE.md found" || echo "CLAUDE.md not found"
```

Nếu tồn tại → Đọc mục `## Nhật ký triển khai — ...` GẦN NHẤT (cuối file) và trích xuất:
- Tóm tắt/ngày của đợt gần nhất
- Phần "Đã hoàn thành"
- Phần "Đang dang dở" (nếu có)
- Phần "Bước tiếp theo" (ưu tiên cho phiên này)

Nếu không tìm thấy mục "Nhật ký triển khai" nào (bình thường ở giai đoạn đầu dự án Drawing Check,
trước khi có phiên `/Works_End` nào chạy) → bỏ qua bước trích xuất, hỏi thẳng người dùng focus hôm
nay (Bước 3), không cần tạo template dự phòng.

### Bước 2: Xác nhận trạng thái hiện tại
Hiển thị cho user (đúng nội dung đã trích xuất ở Bước 1, từ mục "Nhật ký triển khai" gần nhất — bỏ
qua bước này nếu chưa có mục nào):
```
📋 TRẠNG THÁI PHIÊN LÀM VIỆC HIỆN TẠI

🏁 Đợt gần nhất: [Tóm tắt + ngày, lấy từ tiêu đề "## Nhật ký triển khai — ..." cuối CLAUDE.md]

✅ Đã hoàn thành:
- [Task 1]
- [Task 2]
- ...

🔄 Đang dang dở (nếu mục gần nhất có phần này):
- [Task x - status]

⏭️ Bước tiếp theo (đã ghi lại từ đợt trước):
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

---
```

### Bước 3: Hỏi focus task hôm nay
Dùng AskUserQuestion để hỏi:
```
Hôm nay bạn muốn tập trung vào task nào từ danh sách "Bước tiếp theo"?

a) [Priority 1]
b) [Priority 2]
c) [Priority 3]
d) Task khác (vui lòng mô tả)
```

Nếu chưa có "Bước tiếp theo" nào (phiên đầu tiên của dự án), hỏi thẳng: "Hôm nay muốn bắt đầu từ đâu?
(vd chạy Phase 0 — `probe_pdf.py` trên bản vẽ thật, hay dựng khung `pyproject.toml`/`src/`?)"

### Bước 4: Hiểu task chi tiết
Hỏi user:
```
Tôi hiểu như sau, đúng không?

📌 Task: [Task name]
📝 Mô tả: [Description]
✅ Acceptance criteria:
  - [Criterion 1]
  - [Criterion 2]
  - [Criterion 3]

Có cần thay đổi gì không?
```

### Bước 5: Chuẩn bị môi trường
Dự án này **không tự động pull/push git** (tự commit/push thủ công, xem `Works_End`) — bước này chỉ
kiểm tra trạng thái, không đụng tới remote.

```bash
# 1. Kiểm tra git status (chỉ xem, KHÔNG tự pull/commit/push)
echo "=== GIT STATUS ===" && git status

# 2. Kiểm tra môi trường Python — CHỈ cài lại nếu pyproject.toml/requirements vừa đổi hoặc venv
# chưa tồn tại (tránh chạy pip install vô ích mỗi phiên). Dự án Python, KHÔNG có package.json/npm.
# Trên máy này lệnh "python"/"python3" trỏ Windows Store alias không chạy được — dùng "py".
echo "=== CHECKING PYTHON ENV ===" && py --version
```

Dự án Drawing Check là **CLI thuần** (Phase 1–5, không có dev server/web) — không có bước "khởi động
dev server" nào cần làm ở đầu phiên. Khi có lệnh CLI thật (`drawing-check run ...`) và cần thử trên 1
file PDF mẫu, chạy trực tiếp khi cần, không phải tiến trình nền dài hạn.

### Bước 6: Startup message
Hiển thị:
```
🎯 PHIÊN LÀM VIỆC SẴN SÀNG

✅ Git: đã xem trạng thái (không tự pull)
✅ Python: đã kiểm tra phiên bản/môi trường

📌 TASK: [Task name]
💪 Let's go!

---
🔗 Khi xong, dùng: /Works_End
```

---

## 💡 TIPS

✅ **Lúc bắt đầu**:
- Nếu bị block từ phiên trước, nhắc Claude để fix nó trước
- Nếu cần thay đổi task, nói rõ lý do

✅ **Context management**:
- Mỗi phiên 1 focus area
- Nếu có 2 tasks không liên quan, split thành 2 phiên

---

## 🎯 EXAMPLE USAGE

### Sáng hôm sau:
```bash
/Works_Start
```
Claude sẽ:
1. Đọc CLAUDE.md
2. Hiển thị next priorities (nếu đã có)
3. Hỏi focus task hôm nay
4. Xem git status, kiểm tra môi trường Python (KHÔNG tự pull, không có dev server để chạy)

---
