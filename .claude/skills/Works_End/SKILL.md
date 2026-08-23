---
name: Works_End
description: Kết thúc phiên làm việc — hỏi tiến độ/quyết định quan trọng trong phiên, soạn 1 mục "Nhật ký triển khai", rồi ghi đúng theo hệ thống Remember/History phân tầng của dự án (docs/Source/Project-History.md hoặc <khu-vuc>-History.md, giữ bản sao 24h trong CLAUDE.md, tổng hợp quyết định vào Remember tương ứng). Không tự git commit/push. Gọi bằng "/Works_End" hoặc "Works_End".
disable-model-invocation: false
---

# 🏁 Works_End — Kết thúc phiên làm việc

Skill này giúp bạn kết thúc phiên làm việc gọn gàng: chốt lại những gì đã làm, cái gì còn dang dở,
ưu tiên cho phiên sau, và ghi đúng nội dung đó vào hệ thống ghi nhớ/lịch sử phân tầng của dự án —
xem mục "Ghi nhớ (Remember) & Lịch sử triển khai (History)" trong CLAUDE.md để hiểu đầy đủ thiết kế
hệ thống này (4 loại file, 5 khu vực kỹ thuật chuẩn). Skill này là "phía ghi" của cặp cơ chế đó;
"phía đọc" là skill `QA-Session`.

Đây là nửa "cuối phiên" của cặp skill `Works_Start`/`Works_End`. Khi bắt đầu phiên mới, dùng skill
`Works_Start`.

Phần cơ học (ghi vào History đích + giữ bản sao 24h trong CLAUDE.md + dọn mục quá hạn) do script
`.claude/skills/Works_End/scripts/quan-ly-nhat-ky.mjs` thực hiện (chạy bằng `node`, không cần cài
thêm gì — chỉ dùng thư viện lõi Node.js). Claude chỉ soạn nội dung mục nhật ký (cần phán đoán, không
máy móc được) rồi gọi script; **không tự tay Edit trực tiếp vào CLAUDE.md hay file History** ở các
bước này — làm vậy dễ lệch định dạng so với các mục do script tạo. File Remember (Bước 9) không do
script quản lý, vẫn ghi thủ công vì cần tổng hợp/diễn giải lại, không phải chép nguyên văn.

---

## 📖 CÁCH SỬ DỤNG

```bash
/Works_End
```

---

## 🔄 WORKFLOW CHI TIẾT

### Bước 1: Hỏi những gì đã hoàn thành
```
✅ NHỮNG GÌ ĐÃ HOÀN THÀNH HÔM NAY?

Liệt kê các task hoàn thành (ví dụ):
- Viết xong extractor crop khung tên theo template mm
- Sửa bẫy tách chữ rời (x_tolerance) cho bản vẽ AutoCAD
- Chạy thử trên 10 bản vẽ golden set, đo precision

Hay đó chỉ là phần của task?
```

Lưu vào biến: `COMPLETED`

### Bước 2: Hỏi trạng thái "In Progress"
```
🔄 CÓ CÁI GÌ ĐANG LÀM DANG DỞ KHÔNG?

Nếu có, mô tả:
- Task name
- % hoàn thành
- Cái gì blocking?
- Cần phải fix gì ở phiên tiếp theo?

Nếu không, gõ: "Không"
```

Lưu vào biến: `IN_PROGRESS`

### Bước 3: Hỏi Bước tiếp theo cho phiên sau
```
⏭️ ƯU TIÊN PHỤ TIẾP THEO LÀ GÌ?

Liệt kê 3 ưu tiên cho phiên tiếp theo, theo thứ tự:
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
```

Lưu vào biến: `NEXT_STEPS`

### Bước 4: Hỏi Key Decisions
```
🎯 CÓ QUYẾT ĐỊNH QUAN TRỌNG NÀO HÔM NAY KHÔNG?

Ví dụ:
- Lựa chọn một cách làm thay vì cách khác?
- Trade-off gì đã được chấp nhận?
- Architectural decision?

Nếu có, mô tả:
| Quyết định | Lý do | Trade-off |
|-----------|-------|----------|
| [Decision] | [Why] | [Cost]   |

Nếu không, gõ: "Không"
```

Lưu vào biến: `KEY_DECISIONS`

### Bước 5: Xác định phạm vi ảnh hưởng của phiên này
Dựa trên `COMPLETED`/`IN_PROGRESS`/`KEY_DECISIONS`, xác định mục nhật ký sắp soạn thuộc về:
- **1 khu vực kỹ thuật cụ thể** trong 5 khu vực chuẩn: `extract`, `engine`, `report`, `vision`,
  `config` — nếu toàn bộ việc trong phiên chỉ đụng đúng 1 khu vực này.
- **Chung dự án / liên khu vực** — nếu là kiến trúc, quy ước, hạ tầng dùng chung (model
  `PageDoc`/`DrawingDoc`, lộ trình Phase, tech stack), hoặc phiên có đụng tới ≥2 khu vực cùng lúc.

Nếu không chắc chắn, hỏi lại người dùng thay vì tự đoán — việc ghi sai file đích khiến tra cứu sau
này (qua `QA-Session`) bị lệch.

### Bước 6: Soạn nội dung mục nhật ký
Theo đúng khuôn đang dùng (tham khảo các mục hiện có trong `docs/Source/Project-History.md` hoặc
`<module>-History.md` nếu đã có, để bám giọng văn/mức độ chi tiết cũ):

```markdown
## Nhật ký triển khai — [Tóm tắt ngắn theo Focus Area] ([yyyy-mm-dd])

[1-2 câu bối cảnh: phiên này làm gì, xuất phát từ đâu.]

### Đã hoàn thành
- [Item từ COMPLETED]
- [Item từ COMPLETED]

### Đang dang dở (nếu IN_PROGRESS khác "Không")
- [Item từ IN_PROGRESS] — [% hoàn thành / đang bị chặn bởi gì / cần làm tiếp gì]

### Quyết định quan trọng đã chốt
- **[Decision]** — **Vì sao:** [Why]. **Đánh đổi:** [Trade-off]

### Bước tiếp theo (ưu tiên phiên sau)
1. [Priority 1 từ NEXT_STEPS]
2. [Priority 2 từ NEXT_STEPS]
3. [Priority 3 từ NEXT_STEPS]
```

Bỏ hẳn phần "Đang dang dở" nếu `IN_PROGRESS` = "Không". Bỏ hẳn phần "Quyết định quan trọng đã chốt"
nếu `KEY_DECISIONS` = "Không" — không để trống mục rỗng.

### Bước 7: Show user trước khi ghi bất cứ đâu
Hiển thị preview những gì SẼ ghi (chưa chạm file nào):
```
📝 SẼ GHI:
- File History: [đường dẫn file đích, vd docs/Source/extract-History.md] → nối mục nhật ký
- CLAUDE.md → dọn mục đã quá hạn (nếu có) + nối bản sao mục mới (giữ 24h)
- File Remember: [đường dẫn, chỉ nếu KEY_DECISIONS khác "Không"] → thêm quyết định

[Nội dung mục "## Nhật ký triển khai — ..." vừa soạn ở Bước 6]

Có chỉnh sửa gì không?
- a) Đã tốt rồi, ghi vào các file trên
- b) Cần sửa lại
```
Chỉ thực hiện các Bước 8-10 (ghi file thật) sau khi user chọn (a).

### Bước 8: Dọn các mục đã quá hạn trong CLAUDE.md
Chạy trước khi ghi mục mới, để dọn sạch các mục còn sót từ phiên trước đã quá hạn giữ trong
CLAUDE.md (nội dung của chúng đã nằm vĩnh viễn trong file History từ lúc được tạo, lệnh này chỉ dọn
bản tạm):
```bash
node .claude/skills/Works_End/scripts/quan-ly-nhat-ky.mjs don
```
Không cần `--ngay` (mặc định lấy ngày hệ thống hiện tại).

### Bước 9: Ghi mục nhật ký mới vào History đích + bản sao tạm trong CLAUDE.md
- Xác định file đích theo Bước 5: `docs/Source/<khu-vuc>-History.md` (khu vực cụ thể — `extract`,
  `engine`, `report`, `vision`, `config`) hoặc `docs/Source/Project-History.md` (chung/liên khu vực)
  — tương ứng tham số `--dich=<khu-vuc>` hoặc `--dich=project` của script.
- Nếu file đích chưa tồn tại (bình thường ở giai đoạn đầu dự án, khi khu vực đó chưa từng có nhật ký
  nào): tạo trước bằng Write với tiêu đề tối thiểu (vd `# Lịch sử triển khai — Extract`) — script
  chủ động từ chối chạy nếu file đích chưa có, để không âm thầm tạo file ở sai chỗ.
- Nếu file đích đã tồn tại từ trước: backup bản hiện tại vào
  `DATA_DOC/Source_bak/<Tên file>_<yyyymmdd-hhmmss>_bak.md` (đúng định dạng ngày giờ xuất file đã
  chốt ở CLAUDE.md) trước khi chạy script — script tự nó KHÔNG backup giúp.
- Ghi nội dung mục nhật ký từ Bước 6 ra 1 file tạm trong thư mục scratchpad của phiên (dòng đầu tiên
  của file phải đúng là dòng tiêu đề `## Nhật ký triển khai — ... (yyyy-mm-dd...)`, không có dòng
  trống phía trước).
- Chạy:
  ```bash
  node .claude/skills/Works_End/scripts/quan-ly-nhat-ky.mjs ghi --dich=<khu-vuc-hoặc-project> --file=<đường-dẫn-file-tạm>
  ```
  Script tự lo cả 2 việc: nối vĩnh viễn vào file History đích, và nối bản sao vào CLAUDE.md (kèm
  dòng ghi chú "trong 24h" nếu dòng đó đã bị dọn sạch trước đó).
- Nếu script báo lỗi (exit code khác 0): đọc thông báo lỗi, xử lý đúng nguyên nhân (thường là quên
  tạo file đích trước) rồi chạy lại — không bỏ qua lỗi.

### Bước 10: Tổng hợp Quyết định quan trọng vào Remember (nếu có)
Nếu `KEY_DECISIONS` khác "Không": viết thêm 1 bản NGẮN GỌN — chỉ quyết định/quy tắc còn hiệu lực,
không kể lại diễn biến — vào file Remember đích tương ứng với phạm vi đã xác định ở Bước 5
(`docs/Source/Project-Remember.md` hoặc `docs/Source/<khu-vuc>-Remember.md`). Áp dụng đúng quy tắc
tạo mới/backup như Bước 9.

### Bước 11: Commit — KHÔNG tự push
Dự án này tự quản lý git thủ công, KHÔNG tự động `git pull`/`git push`. Sau khi ghi xong các file:
```bash
echo "✅ Đã cập nhật History/Remember/CLAUDE.md (chưa commit)."
echo "Bạn tự 'git add ... && git commit' khi sẵn sàng, hoặc nhờ tôi commit riêng nếu muốn."
```
KHÔNG tự ý chạy `git add`/`git commit`/`git push` trừ khi người dùng yêu cầu rõ ràng ngay lúc đó.

### Bước 12: End of session message
```
🏁 PHIÊN LÀM VIỆC KẾT THÚC

📊 Tóm tắt:
✅ Hoàn thành: [Number] tasks
🔄 Đang làm: [Number] tasks
⏭️ Ưu tiên tiếp: [Next 3 priorities]

📝 Đã ghi: [file History đích] + bản sao 24h trong CLAUDE.md[ + file Remember nếu có]
📝 Git: chưa commit — tự commit/push khi sẵn sàng
🔗 Next session: /Works_Start

🎉 Tốt lắm! Nghỉ ngơi thôi!
```

---

## 💡 TIPS

✅ **Lúc kết thúc**:
- Kể cả % hoàn thành (ví dụ: "80% done")
- Nếu chưa xong, mô tả chính xác cái gì cần làm tiếp
- Key decisions giúp phiên sau (và `QA-Session`) hiểu tại sao code như vậy

---

## 🎯 EXAMPLE USAGE

### Cuối ngày:
```bash
/Works_End
```
Claude sẽ:
1. Hỏi hoàn thành gì?
2. Hỏi còn đang làm gì?
3. Hỏi priority tiếp?
4. Hỏi key decisions?
5. Xác định mục này thuộc module nào hay chung dự án
6. Soạn 1 mục "Nhật ký triển khai" theo đúng khuôn đã dùng
7. Ghi vào đúng file History đích + giữ bản sao 24h trong CLAUDE.md (tự dọn mục cũ >24h) + tổng hợp
   quyết định quan trọng vào Remember đích nếu có
8. KHÔNG tự commit/push — bạn tự làm khi sẵn sàng

**Done!** Không phải tự tay soạn lại và rải nội dung ra đúng từng file nữa.

---
