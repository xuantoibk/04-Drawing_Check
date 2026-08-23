---
name: deployment-planner
description: Lập kế hoạch triển khai công việc chi tiết với phân tích sâu. Sử dụng skill này khi người dùng có một công việc/dự án cần lập kế hoạch, yêu cầu phân tích chi tiết, chia nhỏ thành các phases, và tạo danh sách công việc cụ thể. Skill sẽ phân tích yêu cầu, gọi các AI Assistant hỗ trợ phân tích kỹ thuật/business, lập timeline, và tạo báo cáo progress có checkbox theo dõi.
compatibility: Cần Claude API để gọi các AI Assistant phân tích
---

# Lập Kế Hoạch Triển Khai Công Việc (Deployment Planner)

Skill này giúp bạn phân tích công việc phức tạp và lập kế hoạch chi tiết, từng bước, với timeline cụ thể.

## Quy Trình Hoạt Động

### 1️⃣ **Giai Đoạn Phân Tích**
Khi nhận một yêu cầu công việc, skill sẽ:
- 📋 **Phân tích chi tiết** yêu cầu, xác định scope, mục tiêu, constraints
- 🔍 **Xác định dependencies** - công việc nào phải làm trước, cái nào có thể song song
- 💡 **Gọi AI Assistant phân tích** - nếu cần chuyên môn kỹ thuật, business, design, v.v.
- ⏱️ **Ước lượng timeline** cho từng phase

### 2️⃣ **Giai Đoạn Lập Kế Hoạch**
Lập danh sách chi tiết:
- **Phase 0.X** - Chuẩn bị, setup, requirements
- **Phase 1.X** - Phát triển, implementation chính
- **Phase 2.X** - Testing, refinement, deployment

Mỗi phase có:
- 🎯 Mô tả rõ ràng bằng tiếng Việt có dấu
- ✅ Checkbox để đánh dấu hoàn thành
- ⏳ Timeline ước lượng

### 3️⃣ **Giai Đoạn Báo Cáo**
- 📊 Tạo HTML widget hiển thị danh sách phases (yêu cầu lưu offline trên PC)
- 📈 Tracking progress real-time
- 🔄 Có thể cập nhật, thêm/xóa phases theo yêu cầu

## Cách Sử Dụng

**Người dùng chỉ cần:**
```
Tôi cần [mô tả công việc chi tiết]
```

**Skill sẽ:**
1. Phân tích yêu cầu
2. Tự động gọi các AI Assistant để phân tích kỹ hơn (nếu cần)
3. Tạo danh sách phases và tasks
4. Hiển thị báo cáo dạng checklist interative

## Ví Dụ

**Input:**
> Tôi cần triển khai Phase 3 của Drawing Check: trích xuất kích thước, dung sai, GD&T từ PDF và validate theo ISO 286/JIS B 0401

**Output:** (Danh sách phases chi tiết)
```
Phase 0.1: Xây bảng ánh xạ glyph cho font ký hiệu GD&T (config/glyphmaps/*.yaml)
Phase 0.2: Thu thập mẫu kích thước/dung sai thật từ golden set để viết regex
Phase 1.1: Viết regex parse dung sai (±0.05, +0.1/-0, 50H7, g6...)
Phase 1.2: Dựng bảng tra ISO 286 / JIS B 0401 dạng YAML
Phase 1.3: Viết checks.fits.validate_iso286 + rule DIM-001
Phase 2.1: Parse GD&T frame (ghép ký hiệu + datum + giá trị theo cụm toạ độ)
Phase 2.2: Chạy lại golden set, đo precision, tinh chỉnh
Phase 2.3: Cập nhật tài liệu + rules/20_dimension.yaml hoàn chỉnh
```

## Tính Năng Thêm

- 🤖 **AI-powered phân tích** - Gọi Claude để phân tích thêm các góc độ bạn chưa nghĩ tới
- 🔗 **Dependency tracking** - Tự động xác định công việc có thể làm song song
- 📱 **Progress tracking** - Checkbox realtime, báo cáo tiến độ
- 🔄 **Flexible updates** - Dễ dàng thêm/sửa/xóa phases khi có thay đổi
- 📊 **Visual reports** - HTML widget đẹp, dễ theo dõi

---

## Kỹ Thuật Triển Khai (Dành cho Claude)

### Prompt Internal cho AI Analysis
Khi skill trigger, sử dụng prompt này để phân tích công việc:

```
Bạn là project manager chuyên phân tích công việc phức tạp.
Phân tích yêu cầu sau:
[USER REQUEST]

Hãy:
1. Xác định scope, mục tiêu chính, constraints
2. Liệt kê các risks/challenges có thể gặp
3. Xác định các dependencies (công việc nào phải trước, nào có thể song song)
4. Ước lượng timeline cho từng component

Trả lời bằng tiếng Việt, chi tiết và thực tế.
```

### Output Format

HTML widget hiển thị:
```html
<div class="todo-list">
  <h2>📋 [Tên Công Việc]</h2>
  <div class="phase">
    <input type="checkbox">
    <span>Phase X.X: [Mô tả chi tiết]</span>
    <span class="timeline">⏳ Timeline</span>
  </div>
  ...
</div>
```

---

## Quy Trình Sử Dụng Bước-Từng-Bước

1. **Người dùng input**: Mô tả công việc cần lập kế hoạch
2. **Skill triggers** → Phân tích requirements
3. **Gọi Claude API** → AI phân tích chi tiết các khía cạnh
4. **Lập danh sách phases** → Tạo timeline, dependencies
5. **Render HTML widget** → Hiển thị checklist interative
6. **Tracking & Updates** → Người dùng có thể update progress, thêm/xóa tasks

---

✨ **Đặc điểm chính**: Skill này sẽ làm việc như một Project Manager AI, tự động phân tích công việc phức tạp thành các phases nhỏ, lập timeline, và giúp bạn tracking progress một cách hiệu quả.
