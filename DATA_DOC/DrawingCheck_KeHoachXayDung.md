# DRAWING CHECK — KẾ HOẠCH XÂY DỰNG
### Ứng dụng kiểm tra bản vẽ & review thiết kế

**Tên dự án:** Drawing Check
**Mã dự án:** DRAWING-CHECK
**Phiên bản:** 1.3 — 22/08/2026
**Thay đổi 1.1:** phạm vi chuyển sang **PDF-first**; hoãn nhánh CAD (DXF/DWG); 3D chỉ *lập kế hoạch*; Phase 1 chỉ CLI, một mẫu khung tên công ty.
**Thay đổi 1.2:** đổi engine đọc PDF sang **pypdfium2** và engine khoanh đỏ sang **pypdf** — nhanh hơn ~40×, tách khung tên hai cột sạch hơn, và **loại bỏ hoàn toàn ràng buộc AGPL** (§6.2–6.5).
**Thay đổi 1.3:** đổi tên dự án thành **Drawing Check** (repo `drawing-check`, package `drawing_check`, lệnh CLI `drawing-check`).
**Người lập:** Quản lý kỹ thuật (vai trò tư vấn)

---

## 0. TÓM TẮT CHO NGƯỜI QUYẾT ĐỊNH

| Hạng mục | Kết luận |
|---|---|
| Mô hình triển khai | **100% on-premise, offline**. Không đàm phán. Lý do tại §2 |
| Đầu vào Phase 1 | **Chỉ PDF vector**. Hoãn DXF/DWG. 3D chỉ lập kế hoạch (§10 Phase 5) |
| Phạm vi Phase 1 | Một mẫu khung tên công ty + nhóm lỗi khung tên/metadata. CLI, chạy một máy |
| Chi phí phần mềm | **0 đ** — stack Phase 1 toàn license sạch (Apache/BSD/MIT), **không AGPL** |
| Chi phí vận hành | Chỉ điện + khấu hao GPU đã có (Phase 1 **không cần GPU**) |
| Nguyên tắc kiến trúc | **Deterministic trước, AI sau.** AI chỉ *trích xuất*, KHÔNG *phán xử* |
| Thời gian tới MVP có giá trị | **3 tuần** (Phase 1) |
| Thời gian tới hệ thống đầy đủ | **4–5 tháng** |
| Rủi ro số 1 | **Bẫy font SHX** của AutoCAD làm PDF mất text — xem §1.4. Chạy `tools/probe_pdf.py` để biết ngay |
| Rủi ro số 2 | **False positive** khiến người dùng bỏ công cụ — xem §8 |

**Câu chốt:** Đừng xây "AI đọc bản vẽ". Hãy xây **"máy kiểm tra tuân thủ, có AI hỗ trợ đọc"**. Hai thứ này khác nhau hoàn toàn về mặt kỹ thuật lẫn số phận dự án.

---

## 1. HIỂU ĐÚNG BÀI TOÁN

### 1.1 Đầu vào — phạm vi đã điều chỉnh

| Nguồn | Độ tin cậy | Giai đoạn | Ghi chú |
|---|---|---|---|
| **PDF vector xuất từ CAD** | ★★★★☆ ~99% | **Phase 1–3** | Mẫu số chung: mọi phần mềm CAD đều xuất ra PDF. Là đường đi chính |
| STEP / IGES (3D) | ★★★★★ hình học | Phase 5 — *chỉ lập kế hoạch* | Mục tiêu: đối chiếu 3D ↔ 2D |
| DXF / DWG | ★★★★★ 100% | Hoãn vô thời hạn | Mở lại khi cần các phép kiểm tra chỉ CAD mới làm được (§1.3) |
| Raster / scan | ★★☆☆☆ 85–95% | Phase 3 | Bản vẽ khách hàng, bản vẽ đã ký |

**Vì sao PDF-first là lựa chọn đúng — nhưng không phải vì lý do bạn nghĩ.**

Bạn chọn PDF vì "CAD mỗi người trình bày một kiểu". Thực ra DXF *khắc phục* vấn đề đó tốt hơn PDF, vì nó cho đọc dữ liệu có cấu trúc thay vì đoán qua tọa độ chữ. Nhưng kết luận của bạn vẫn đúng, vì một lý do khác và mạnh hơn:

> **Bạn ở vai trò REVIEW, không phải vai trò VẼ.** Bản vẽ đến bàn bạn từ AutoCAD, SolidWorks, Inventor, Creo, và từ khách hàng. Thứ duy nhất **tất cả** chúng đều có là PDF. Viết một extractor PDF phủ 100% đầu vào tốt hơn viết ba extractor CAD phủ 60%.

### 1.2 Bạn mất gì khi bỏ nhánh CAD — ghi nhận để không quên

Những phép kiểm tra sau **không thể** làm từ PDF, dù PDF có sạch đến đâu:

| Không làm được từ PDF | Vì sao |
|---|---|
| Phát hiện kích thước trùng lặp (over-dimensioning) | PDF không lưu quan hệ giữa dimension và hình học |
| Kiểm tra layer / font / lineweight sai quy định | PDF đã "dẹt hóa", không còn layer |
| Kiểm tra kích thước bị ghi đè bằng tay (dimension override) | Đây là dạng gian lận nguy hiểm: người vẽ sửa con số hiển thị khác giá trị thật. **Chỉ CAD mới phát hiện được** |
| Đối chiếu kích thước với hình học thật trên bản vẽ | PDF chỉ có chữ và nét, không có mô hình |

→ Ghi vào sổ rủi ro. Nếu sau này bạn gặp sự cố do dimension override, đó là tín hiệu để mở lại nhánh DXF cho riêng bản vẽ nội bộ.

### 1.3 Nguyên tắc THANG BẬC NGUỒN DỮ LIỆU (áp dụng bên trong đường PDF)

> **Luôn khai thác nguồn có độ tin cậy cao nhất còn khả dụng.**

```
PDF text layer  ─────►  nếu trang không có text ─►  OCR / VLM trên ảnh render
  (gần chắc chắn)                                        (xác suất)
```

Không bao giờ render một trang PDF *đã có text* ra ảnh rồi OCR. Đó là tự nguyện đổi 99% lấy 90%, đổi 0.2 giây lấy 15 giây, và đổi kết quả tái lập được lấy kết quả mỗi lần chạy một khác.

### 1.4 ⚠️ BẪY ĐẶC THÙ CỦA ĐƯỜNG PDF — ĐỌC KỸ TRƯỚC KHI CODE

Bạn xuất PDF từ **cả AutoCAD lẫn SolidWorks/Inventor/Creo**. Hai nguồn này hành xử rất khác nhau.

#### Bẫy 1 — Font SHX của AutoCAD (nguy hiểm nhất)

AutoCAD dùng font `.shx` (romans.shx, txt.shx, isocp.shx) rất phổ biến. Khi in ra PDF, **chữ SHX bị chuyển thành nét vẽ vector, không còn là text**. File PDF trông y hệt, mở ra đọc được bằng mắt, nhưng máy trích xuất được **0 ký tự**.

Đây là nguyên nhân số 1 khiến dự án loại này chết ở tuần đầu: bạn viết xong extractor, chạy lên bản vẽ thật, và nhận về chuỗi rỗng.

**Cách xử lý, theo thứ tự ưu tiên:**

1. **Sửa ở nguồn (rẻ nhất, hiệu quả nhất).** Đổi style chữ trong template AutoCAD sang font TrueType (Arial, hoặc ISOCPEUR TTF nếu muốn giữ dáng chữ kỹ thuật). Một lần sửa template → mọi bản vẽ về sau đều đọc được. **Đây là việc quản lý, không phải việc lập trình, và nó tiết kiệm cho bạn hàng tháng công sức.**
2. Nếu không sửa được nguồn (bản vẽ cũ, bản vẽ khách hàng): render trang ra ảnh 300 DPI và OCR — chấp nhận tụt xuống 85–95%.
3. Với bản vẽ SolidWorks/Inventor/Creo: thường dùng TrueType sẵn → không dính bẫy này.

`tools/probe_pdf.py` phát hiện chính xác trường hợp này (phân loại `VECTOR_NO_TEXT`: nhiều nét vẽ, gần như không có ký tự).

#### Bẫy 2 — Ký hiệu GD&T ra ký tự rác

Ký hiệu GD&T (⌀, ⊥, ⌖, ⏥...) trong bản vẽ CAD thường đến từ font ký hiệu riêng (GDT.shx, AMGDT) dùng **bảng mã riêng, không phải Unicode**. Trích xuất ra bạn sẽ nhận `n` thay vì `⌀`, `j` thay vì ký hiệu vị trí.

→ Cần một **bảng ánh xạ glyph** cho từng font ký hiệu: `config/glyphmaps/amgdt.yaml`. Xây một lần, dùng mãi. Script probe liệt kê sẵn các font ký hiệu đang có trong bản vẽ của bạn.

#### Bẫy 3 — Chữ bị tách rời từng ký tự

PDF xuất từ CAD thường đặt **từng glyph một cách độc lập**, không có khái niệm "từ". Dùng `extract_text()` mặc định sẽ ra `S H A F T   S U P P O R T`. Phải chỉnh `x_tolerance` (~1.5) và `y_tolerance` (~2) trong pdfplumber. Đây là lỗi mất nửa ngày nếu không biết trước.

#### Bẫy 4 — Xoay trang và khổ dựng

PDF từ CAD hay mang `/Rotate 90`. Nếu crop vùng khung tên theo tọa độ thô mà quên chuẩn hóa góc xoay, bạn sẽ cắt nhầm góc. Ngoài ra có bản vẽ khổ dựng (A4 portrait) — template khung tên phải xử lý cả hai hướng.

#### Bẫy 5 — Một file PDF ≠ một bản vẽ

Bạn đã xác nhận có cả ba tình huống. Đây là quy tắc gom nhóm bắt buộc:

```
Đơn vị xử lý cơ bản = TRANG (page), không phải file.
Sau khi đọc xong tất cả trang:
    gom các trang có cùng `drawing_no` → một BẢN VẼ
    trong mỗi bản vẽ, sắp xếp theo trường `sheet` ("1/3", "2/3", "3/3")
    → kiểm tra: đủ tờ chưa? revision các tờ có khớp nhau không?
```

Thiết kế theo trang ngay từ đầu. Đổi từ per-file sang per-page ở giữa dự án là việc phải sửa toàn bộ model, report và database.

### 1.5 Ba nhóm lỗi ưu tiên (theo bạn chọn)

| # | Nhóm | % tổng lỗi (ước lượng ngành) | Độ khó từ PDF | ROI |
|---|---|---|---|---|
| A | Khung tên & metadata | ~40% | Thấp | ★★★★★ |
| B | Kích thước, dung sai, GD&T | ~35% | Cao (vướng bẫy 2) | ★★★☆☆ |
| C | Ký hiệu công nghệ (nhám/hàn/ren) | ~25% | Trung bình | ★★★★☆ |

→ **Phase 1 chỉ làm nhóm A, chỉ với mẫu khung tên công ty.** Bắt được 40% lỗi với 15% công sức.

---

## 2. TƯ VẤN BẢO MẬT — BẠN CHƯA CHỐT, TÔI CHỐT HỘ

**Khuyến nghị: 100% on-premise, không gửi bất kỳ byte nào lên cloud.**

Lý do, xếp theo trọng số:

1. **Bạn có khách hàng Nhật (JIS).** Doanh nghiệp Nhật gần như luôn có 秘密保持契約 (NDA) với điều khoản cấm chuyển dữ liệu kỹ thuật sang bên thứ ba, cấm lưu trữ ngoài lãnh thổ được thỏa thuận. Đưa bản vẽ của họ qua API cloud là **vi phạm hợp đồng**, không phải "rủi ro kỹ thuật". Hậu quả là mất khách, không phải mất file.

2. **Bản vẽ chế tạo là bí mật kinh doanh có thể tái tạo được.** Một bản vẽ chi tiết đủ để đối thủ làm ra sản phẩm. Khác với văn bản hành chính, giá trị rò rỉ ở đây là tuyệt đối.

3. **Quy mô >300 bản/tuần giết chết free tier.** 300 bản × ~3 trang × 1 request = 900+ request/tuần. Mọi free tier hiện có sẽ chặn bạn trong 2–3 ngày. Khi đó bạn hoặc trả tiền, hoặc dự án chết. On-prem không có trần này.

4. **Bạn đã có GPU NVIDIA.** Chi phí biên để chạy local gần bằng 0. Không có lý do kinh tế nào để lên cloud.

5. **Kết quả tái lập được.** Model cloud bị nhà cung cấp cập nhật âm thầm → hôm nay pass, tháng sau fail cùng một bản vẽ. Với công cụ dùng để *đánh giá nhân viên*, đây là vấn đề nghiêm trọng về tính công bằng.

**Ngoại lệ duy nhất được phép (Phase 4+):** gửi lên cloud LLM một chuỗi text đã tách rời khỏi bản vẽ, đã ẩn danh (bỏ mã bản vẽ, tên khách hàng, tên dự án), chỉ để diễn giải câu ghi chú kỹ thuật mơ hồ bằng ngôn ngữ tự nhiên. **Không bao giờ gửi hình ảnh.** Và phải có công tắc tắt trong config, mặc định = TẮT.

---

## 3. NGUYÊN TẮC THIẾT KẾ CỐT LÕI

### 3.1 AI trích xuất — Rule engine phán xử

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐    ┌──────────┐
│  EXTRACTOR  │───►│  NORMALIZED DATA │───►│ RULE ENGINE │───►│ FINDINGS │
│ (có thể AI) │    │   (JSON schema)  │    │ (thuần code)│    │ (có mã)  │
└─────────────┘    └──────────────────┘    └─────────────┘    └──────────┘
   không chắc              chắc chắn            xác định         truy vết được
```

**Tại sao tách đôi:**

- Khi bạn nói với nhân viên "bản vẽ này sai", bạn phải chỉ ra được **mã quy tắc** (ví dụ `TB-007: Thiếu ô người kiểm tra`), không phải "AI bảo thế". Không ai chấp nhận bị đánh giá bởi một hộp đen.
- Rule engine bằng code → **test được bằng unit test**, sửa được không cần train lại, chạy trong mili giây.
- Có thể thay extractor (đổi OCR model) mà không đụng vào logic nghiệp vụ.
- Khi có tranh cãi, bạn mở file YAML ra và chỉ vào dòng quy tắc. Kết thúc tranh cãi.

### 3.2 Ba mức kết luận — KHÔNG dùng nhị phân pass/fail

| Mức | Ý nghĩa | Điều kiện | Hành động |
|---|---|---|---|
| **FAIL** | Chắc chắn sai | Suy ra từ dữ liệu tin cậy ★★★★★, không cần diễn giải | Chặn duyệt |
| **WARN** | Nghi ngờ, cần người xem | Dữ liệu từ OCR/AI, hoặc quy tắc có ngoại lệ | Đưa vào danh sách người review |
| **INFO** | Ghi nhận | Lệch chuẩn nhưng có thể cố ý | Chỉ thống kê |

Không bao giờ để một kết quả từ AI rơi vào FAIL. AI chỉ được sinh ra WARN.

### 3.3 Phân loại mức nghiêm trọng (độc lập với mức tin cậy ở trên)

| Mức | Định nghĩa | Ví dụ |
|---|---|---|
| **Critical** | Sai → phế phẩm hoặc tai nạn | Sai góc chiếu, thiếu dung sai lắp ghép, sai vật liệu |
| **Major** | Sai → phải hỏi lại, chậm tiến độ | Thiếu kích thước, thiếu độ nhám bề mặt lắp |
| **Minor** | Sai quy cách, không ảnh hưởng chế tạo | Sai font, sai layer, thiếu ngày tháng |

---

## 4. CẢNH BÁO ĐẶC THÙ: BẠN DÙNG SONG SONG JIS VÀ ISO/TCVN

Đây là điểm nguy hiểm nhất trong toàn bộ hồ sơ của bạn, và là lý do tôi khuyên đưa nó lên **Phase 1, mức Critical**.

### 4.1 Góc chiếu — lỗi im lặng tốn tiền nhất

| Hệ | Góc chiếu mặc định | Ký hiệu |
|---|---|---|
| ISO / TCVN | **Góc phần tư thứ nhất** (First Angle) | Hình nón cụt, đáy lớn bên trái |
| JIS | **Góc phần tư thứ ba** (Third Angle) — 第三角法 | Hình nón cụt, đáy lớn bên phải |

Một bản vẽ vẽ theo Third Angle nhưng ghi ký hiệu First Angle (hoặc không ghi ký hiệu gì) sẽ được xưởng gia công **lật gương toàn bộ chi tiết**. Không ai phát hiện cho tới khi lắp thử. Đây là lỗi phế nguyên lô.

**Quy tắc bắt buộc Phase 1:**
- `PROJ-001` (Critical): Khung tên phải có ký hiệu góc chiếu. Không có → FAIL.
- `PROJ-002` (Critical): Góc chiếu phải khớp với chuẩn đã khai báo cho dự án đó. Dự án JIS mà ghi First Angle → FAIL.

### 4.2 Các khác biệt khác phải mã hóa vào rule

| Hạng mục | ISO/TCVN | JIS |
|---|---|---|
| Chuẩn nền | ISO 128, ISO 5457 | JIS B 0001, JIS B 0002 |
| GD&T | ISO 1101, ISO 5459 | JIS B 0021 (tương thích ISO, có khác biệt nhỏ) |
| Độ nhám | ISO 21920 (thay ISO 1302) | JIS B 0031 |
| Ký hiệu hàn | ISO 2553 | JIS Z 3021 |
| Ren | ISO 68 / ISO 261 (M) | JIS B 0205 (M), có cả ren ống R/Rc/G |
| Dung sai lắp ghép | ISO 286 | JIS B 0401 (số liệu trùng ISO 286) |
| Ngôn ngữ ghi chú | Việt / Anh | **Nhật (Kanji + Katakana)** |

→ **Hệ quả kỹ thuật:** OCR bắt buộc phải xử lý được tiếng Nhật. Tesseract xử lý CJK kém. Đây là lý do chọn **PaddleOCR-VL** (100+ ngôn ngữ, mạnh CJK) làm mặc định. Nếu chọn sai OCR ở bước này, bạn phải làm lại toàn bộ Phase 3.

### 4.3 Thiết kế cho đa chuẩn ngay từ đầu

Không hardcode. Mỗi dự án khai báo profile chuẩn của mình:

```yaml
# config/projects/PRJ-KOBE-2026.yaml
project_id: PRJ-KOBE-2026
customer: Kobe Precision K.K.
standard_profile: jis          # jis | iso | asme
projection_angle: third
language: [ja, en]
title_block_template: templates/kobe_a3.yaml
drawing_no_pattern: '^KB-\d{5}-[A-Z]\d{2}$'
```

---

## 5. KIẾN TRÚC HỆ THỐNG

### 5.1 Sơ đồ tổng thể

```
   CLI: drawing-check run "D:\BanVe\*.pdf"
                    │
                    ▼
     ┌──────────────────────────────────┐
     │           INGEST                 │
     │  duyệt file, hash chống trùng    │
     │  TÁCH THÀNH TỪNG TRANG           │  ◄── đơn vị xử lý = TRANG
     └───────────────┬──────────────────┘
                     ▼
     ┌──────────────────────────────────┐
     │        PAGE CLASSIFIER           │
     │  vector-có-text / vector-mất-text│  ◄── logic của probe_pdf.py
     │  / scan / lai                    │
     └────┬────────────────────────┬────┘
          │ có text                │ không có text
          ▼                        ▼
 ┌──────────────────┐   ┌──────────────────────────┐
 │ PDF TEXT EXTRACT │   │  VISION LAYER (Phase 4)  │
 │  pdfplumber      │   │  render 300 DPI          │
 │  - chuẩn hoá xoay│   │  RT-DETR → khoanh vùng   │
 │  - dò khổ giấy   │   │  PaddleOCR-VL → đọc chữ  │
 │  - crop khung tên│   │  Qwen3-VL → fallback     │
 │    theo mm       │   └────────────┬─────────────┘
 │  - ánh xạ glyph  │                │
 └────────┬─────────┘                │
          └──────────────┬───────────┘
                         ▼
     ┌──────────────────────────────────┐
     │   GOM TRANG → BẢN VẼ             │
     │   theo drawing_no + sheet x/y    │
     └───────────────┬──────────────────┘
                     ▼
                    ┌──────────────────────────────┐
                    │   DRAWING DOCUMENT MODEL     │  ◄── JSON schema chuẩn hóa
                    │  (pydantic, có confidence &  │      Đây là hợp đồng
                    │   bbox cho từng trường)      │      giữa 2 nửa hệ thống
                    └───────────────┬──────────────┘
                                    ▼
                    ┌──────────────────────────────┐
                    │        RULE ENGINE           │  ◄── rules/*.yaml
                    │  thuần Python, không AI      │      + checks/*.py
                    └───────────────┬──────────────┘
                                    ▼
                    ┌──────────────────────────────┐
                    │   FINDINGS (SQLite / JSON)   │
                    └───────┬─────────────┬────────┘
                            ▼             ▼
                      PDF markup     Excel/CSV
                      (PyMuPDF)     (xlsxwriter)

        (Redis queue + PostgreSQL + Web dashboard: chỉ thêm khi
         có người dùng thứ hai — xem §12)
```

### 5.2 Vì sao có lớp "Drawing Document Model" ở giữa

Đây là **hợp đồng dữ liệu**. Mọi extractor đều phải sinh ra đúng cấu trúc này, bất kể nguồn là PDF text, OCR, hay (sau này) DXF. Nhờ vậy:

- Rule engine viết **một lần**, chạy cho mọi định dạng.
- Thêm định dạng mới (ví dụ CATIA) = viết thêm 1 extractor, không sửa rule.
- Test rule engine bằng JSON giả, không cần file CAD thật → CI chạy trong vài giây.
- Mỗi trường mang theo `confidence` và `bbox` → biết được kết luận đến từ đâu, và vẽ khoanh đỏ được lên PDF.

```python
# core/model.py  (rút gọn)
from pydantic import BaseModel
from typing import Literal, Optional, Generic, TypeVar

T = TypeVar("T")

class Provenance(BaseModel):
    source: Literal["pdf_text", "ocr", "vlm", "manual", "dxf"]
    confidence: float          # ~1.0 với pdf_text; <1 với ocr/vlm
    page: int
    bbox: tuple[float, float, float, float] | None   # để khoanh đỏ

class Field(BaseModel, Generic[T]):
    value: Optional[T]
    prov: Provenance

class TitleBlock(BaseModel):
    drawing_no:     Field[str]
    title:          Field[str]
    material:       Field[str]
    mass_kg:        Field[float]
    scale:          Field[str]
    revision:       Field[str]
    projection:     Field[Literal["first", "third"]]
    general_tol:    Field[str]      # vd "JIS B 0405-m"
    unit:           Field[str]
    drawn_by:       Field[str]
    checked_by:     Field[str]
    approved_by:    Field[str]
    date_drawn:     Field[str]
    sheet:          Field[str]      # "1/3"
    size:           Field[str]      # A3

class Dimension(BaseModel):
    nominal: float
    tol_upper: Optional[float]
    tol_lower: Optional[float]
    fit_code: Optional[str]         # "H7", "g6"
    dim_type: Literal["linear","radial","diameter","angular","ordinate"]
    is_reference: bool              # kích thước tham khảo (trong ngoặc)
    is_basic: bool                  # kích thước lý thuyết (đóng khung)
    prov: Provenance

class PageDoc(BaseModel):
    """ĐƠN VỊ XỬ LÝ CƠ BẢN = MỘT TRANG PDF, không phải một file.
    Xem bẫy 5, §1.4 — đổi từ per-file sang per-page giữa dự án là sửa lại tất cả."""
    file_hash: str
    file_name: str
    page_no: int
    pages_total: int
    page_kind: Literal["vector_text_ok", "vector_no_text", "raster_scan",
                       "mixed", "low_text"]
    sheet_size: str                 # "A3", "A4"...
    rotation: int
    title_block: TitleBlock
    dimensions: list[Dimension]
    gdt_frames: list["GDTFrame"]
    surface_finishes: list["SurfaceFinish"]
    welds: list["WeldSymbol"]
    threads: list["Thread"]
    notes: list["Note"]

class DrawingDoc(BaseModel):
    """Một BẢN VẼ = các trang có cùng drawing_no, sắp theo sheet x/y."""
    drawing_no: str
    pages: list[PageDoc]
    sheets_expected: Optional[int]  # lấy từ "1/3" -> 3
    sheets_found: int               # thiếu tờ = lỗi Major
```

---

## 6. TECH STACK — TOÀN BỘ MIỄN PHÍ

### 6.1 Bảng chọn công nghệ

| Lớp | Thư viện | License | Phase | Ghi chú quan trọng |
|---|---|---|---|---|
| Ngôn ngữ | Python 3.11+ | PSF | 1 | |
| **Đọc PDF (chính)** | **pypdfium2** | Apache-2.0 / BSD-3 | **1** | Lõi PDFium của Chrome. Cắt text theo vùng, char bbox, font name, font size. **Nhanh gấp ~40 lần pdfplumber** (§6.3) |
| Đọc PDF (đối chứng) | **pdfplumber** | MIT | 1 | Giữ làm *engine thứ hai* để đối chứng golden set (§6.4) và để dựng template ban đầu |
| **Ghi chú PDF (khoanh đỏ)** | **pypdf** | BSD-3 | **1** | `Rectangle` + `FreeText` — đã kiểm chứng ghi được khung đỏ và comment. License sạch |
| Ghi chú PDF (tuỳ chọn) | PyMuPDF (fitz) | ⚠️ **AGPL-3.0** | — | API dễ hơn, nhưng AGPL. Chỉ dùng nếu chấp nhận ràng buộc (§6.2) |
| Rule engine | Python + **PyYAML** + **pydantic v2** | MIT | 1 | Tự viết, ~800 dòng |
| Xuất Excel | **xlsxwriter** | BSD | 1 | |
| CLI | **typer** | MIT | 1 | |
| Test | **pytest** | MIT | 1 | |
| CSDL | **SQLite** (chuẩn thư viện) | PD | 2 | Đủ cho một người dùng. Lên PostgreSQL khi có nhiều người |
| OCR chính | **PaddleOCR-VL v1.6** (~0.9B) | Apache 2.0 | 4 | **Chọn vì hỗ trợ 100+ ngôn ngữ gồm CJK** (bản vẽ JIS có Kanji). VRAM 2–4GB |
| OCR nhanh | **PP-OCRv5** | Apache 2.0 | 4 | Cho batch lớn, không cần VLM |
| Phát hiện ký hiệu | **RT-DETR** hoặc **YOLOv11** | Apache 2.0 / ⚠️ AGPL | 4 | Ultralytics YOLO là AGPL. Nội bộ OK, thương mại phải cân nhắc. RT-DETR (Apache) là phương án sạch |
| VLM dự phòng | **Qwen3-VL 8B** qua vLLM/Ollama | Apache 2.0 | 4 | Chỉ gọi khi các lớp trên thất bại |
| Gán nhãn dữ liệu | **Label Studio** | Apache 2.0 | 4 | |
| Đọc STEP | **pythonocc-core** | LGPL-2.1 | 5 | Chỉ AP242 mới có PMI (dung sai 3D) |
| — *hoãn* — | ezdxf / ODA File Converter | MIT / free | — | Mở lại nếu cần bắt lỗi dimension override, layer, font (§1.2) |
| — *hoãn* — | Redis + RQ, FastAPI + HTMX, Docker | BSD/MIT | — | Chỉ khi có người dùng thứ hai |

**Toàn bộ Phase 1 chỉ cần:**

```bash
pip install pypdfium2 pypdf pdfplumber xlsxwriter pyyaml pydantic typer pytest
```

Không GPU, không Docker, không server, **không license AGPL nào**.

### 6.2 ⚠️ Về PyMuPDF và bẫy license AGPL

PyMuPDF là thư viện PDF dễ dùng nhất và tôi đã đưa nó vào bản kế hoạch 1.0. Bản 1.1 hạ nó xuống *tuỳ chọn*, vì:

- PyMuPDF là **AGPL-3.0**. AGPL không chỉ ràng buộc khi bán phần mềm, mà cả khi **chạy nó như một dịch vụ mạng** — nghĩa là ngay khi bạn dựng web dashboard cho phòng dùng, nghĩa vụ công bố mã nguồn đã có thể phát sinh.
- License thương mại từ Artifex nằm ở mức **10.000–50.000 USD/năm**.
- Toàn bộ việc PyMuPDF làm cho dự án này (đọc text theo vùng, char bbox, render ảnh, khoanh đỏ) đều làm được bằng `pypdfium2` + `pypdf` với license sạch.

Dùng nội bộ thuần tuý hôm nay thì không sao. Nhưng đây là loại ràng buộc rất khó gỡ về sau khi mã đã bám sâu vào một thư viện. Tránh từ đầu rẻ hơn nhiều.

### 6.3 Số đo thật trên bản vẽ (không phải benchmark trên mạng)

Đo trên PDF dạng bản vẽ, tác vụ *cắt vùng khung tên góc dưới phải rồi đọc text* — đúng việc Phase 1 phải làm:

| Thư viện | ms/trang | Nhanh gấp | License | Cắt được theo vùng? |
|---|---|---|---|---|
| **pypdfium2** | **0.89** | 1.0× | Apache-2.0 / BSD-3 | Có (native) |
| pypdf | 7.82 | 8.8× chậm hơn | BSD-3 | Không (chỉ cả trang) |
| pdfplumber | 42.24 | **47.7× chậm hơn** | MIT | Có (crop) |

Chạy lại trên bản vẽ của chính bạn: `python tools/bench_pdf_libs.py "D:\BanVe"`.

**Chênh lệch chất lượng còn đáng nói hơn chênh lệch tốc độ.** Khung tên thường có **hai cột** nhãn:giá trị. pdfplumber gom ký tự theo *hàng ngang*, nên nó dán hai cột vào cùng một dòng:

```
pdfplumber:  DRAWING NO.: KB-00123-A01   DRAWN: NVA 2026-07-14
             TITLE: SHAFT SUPPORT BRACKET   CHECKED:
```

→ Trường `title` bị dính đuôi `CHECKED:`, và rule "thiếu người kiểm tra" sẽ **báo sai**. Phải viết thêm logic tách cột.

```
pypdfium2:   DRAWING NO.: KB-00123-A01
             TITLE: SHAFT SUPPORT BRACKET
             CHECKED:
```

→ Mỗi trường một dòng, parse thẳng. Ít code hơn, ít lỗi hơn.

> **Cảnh báo về benchmark trên mạng:** các bảng xếp hạng thư viện PDF đều chấm điểm theo *thứ tự đọc*, *văn bản nhiều cột* và *bảng biểu* — ba thứ mà bản vẽ kỹ thuật không có. Một thư viện đứng đầu bảng cho tài liệu văn xuôi có thể là lựa chọn tệ cho bản vẽ, và ngược lại. Chỉ tin số đo trên dữ liệu của bạn.

### 6.4 Mẹo: chạy hai engine để tự phát hiện ca khó

Trên **golden set** (không phải khi chạy thật), đọc bằng cả `pypdfium2` và `pdfplumber` rồi so kết quả:

- Hai engine **khớp nhau** → tin được, không cần nhìn.
- Hai engine **lệch nhau** → trang đó đúng là ca khó: font CID lạ, encoding hỏng, ký hiệu ánh xạ sai, chữ chồng lấn.

Bạn có ngay danh sách các trang cần soi tay, thay vì phải mở từng file. Tốn thêm ~40ms/trang trong CI, đổi lại tìm đúng chỗ cần sửa. Đây là cách rẻ nhất để nâng precision mà không cần thêm dữ liệu.

### 6.5 Những thứ KHÔNG nên dùng cho bản vẽ

| Công cụ | Vì sao không |
|---|---|
| **Docling, marker, MinerU, unstructured** | Là bộ chuyển tài liệu → Markdown cho RAG. Chúng mô hình hoá *đoạn văn, tiêu đề, thứ tự đọc, bảng*. Bản vẽ không có gì trong số đó. Chậm hơn 100 lần và trả về cấu trúc vô nghĩa |
| **LLM/VLM đọc thẳng cả trang bản vẽ** | Chậm, không tái lập được, và ảo giác ở đúng những trường quan trọng (§10 Phase 4) |
| **Camelot, tabula** | Trích bảng trong báo cáo tài chính. Khung tên bản vẽ không phải bảng theo nghĩa đó |
| **pdftotext (poppler)** | Nhanh và ổn định, nhưng GPL và không hơn pypdfium2 ở điểm nào cho việc này |

### 6.6 Vì sao PaddleOCR-VL chứ không phải Tesseract

| | Tesseract | PaddleOCR-VL v1.6 |
|---|---|---|
| Tiếng Nhật trên bản vẽ | Kém, hay nhầm Kanji | Tốt, huấn luyện sẵn CJK |
| Text xoay dọc / nghiêng | Rất kém | Tốt |
| Chữ nhỏ trong khung tên | Kém | Tốt |
| Đọc bảng (khung tên, BOM) | Không hiểu cấu trúc | Có nhận dạng layout |
| Yêu cầu GPU | Không | 2–4 GB VRAM (bạn đã có) |

Bản vẽ JIS có Kanji dọc trong ô ghi chú — Tesseract sẽ trả rác. Đây không phải chuyện tối ưu, đây là chuyện dùng được hay không.

### 6.7 Yêu cầu phần cứng

| Cấu hình | GPU | Thông lượng ước tính |
|---|---|---|
| Tối thiểu | GTX 1660 6GB | ~1–2 bản/phút (có OCR) |
| **Khuyến nghị** | RTX 3060 12GB / 4060 Ti 16GB | ~4–6 bản/phút |
| Thoải mái | RTX 4090 24GB | ~15 bản/phút, chạy được VLM 8B song song |

Với 300 bản/tuần: **Phase 1–3 chạy trên CPU là dư** (~200 trang/phút với PDF vector). GPU chỉ vào cuộc ở Phase 4 (nhận dạng ký hiệu, xử lý trang mất text và bản scan).

---

## 7. RULE ENGINE — TRÁI TIM CỦA HỆ THỐNG

### 7.1 Định dạng quy tắc

```yaml
# rules/10_title_block.yaml
version: 1
ruleset: title_block
applies_to:
  standard: [iso, jis]

rules:
  - id: TB-001
    name: "Thiếu mã bản vẽ"
    severity: critical
    confidence_gate: 0.95          # dưới ngưỡng này → hạ xuống WARN
    check: field_present
    params: { field: title_block.drawing_no }
    message_vi: "Khung tên thiếu mã bản vẽ."
    message_en: "Title block missing drawing number."
    fix_hint: "Điền mã theo quy tắc {pattern} của dự án."

  - id: TB-002
    name: "Mã bản vẽ sai định dạng"
    severity: major
    check: field_matches
    params:
      field: title_block.drawing_no
      pattern_from_project: drawing_no_pattern
    message_vi: "Mã '{value}' không khớp quy tắc đặt tên '{pattern}'."

  - id: TB-007
    name: "Thiếu người kiểm tra"
    severity: major
    check: field_present
    params: { field: title_block.checked_by }
    message_vi: "Chưa có người kiểm tra. Bản vẽ không được phát hành khi chưa qua kiểm."

  - id: TB-011
    name: "Vật liệu không có trong danh mục"
    severity: critical
    check: field_in_catalog
    params:
      field: title_block.material
      catalog: catalogs/materials.yaml
    message_vi: "Vật liệu '{value}' không có trong danh mục vật liệu công ty."
    fix_hint: "Dùng ký hiệu chuẩn, vd SS400, S45C, SUS304, A5052."

  - id: PROJ-001
    name: "Thiếu ký hiệu góc chiếu"
    severity: critical
    check: field_present
    params: { field: title_block.projection }
    message_vi: "Bản vẽ không ghi ký hiệu góc chiếu — nguy cơ gia công lật gương."

  - id: PROJ-002
    name: "Góc chiếu sai chuẩn dự án"
    severity: critical
    check: field_equals_project
    params:
      field: title_block.projection
      project_key: projection_angle
    message_vi: "Bản vẽ ghi góc chiếu '{value}' nhưng dự án dùng '{expected}'."

  - id: TB-014
    name: "Revision không khớp lịch sử sửa đổi"
    severity: major
    check: custom
    params: { handler: checks.revision.rev_matches_history }
    message_vi: "Rev '{value}' trong khung tên không có dòng tương ứng ở bảng sửa đổi."
```

```yaml
# rules/20_dimension.yaml
rules:
  - id: DIM-001
    name: "Dung sai lắp ghép không hợp lệ"
    severity: critical
    check: custom
    params: { handler: checks.fits.validate_iso286 }
    message_vi: "Ký hiệu lắp ghép '{value}' không tồn tại trong ISO 286 / JIS B 0401."

  - id: DIM-004
    name: "Kích thước lỗ ren không có dung sai và không ghi cấp ren"
    severity: major
    check: custom
    params: { handler: checks.threads.thread_has_class }

  - id: DIM-007
    name: "Chuỗi kích thước cộng dồn quá 3 mắt xích"
    severity: major
    check: custom
    params: { handler: checks.tolstack.chain_depth }
    message_vi: "Chuỗi kích thước {chain} cộng dồn {n} mắt xích → sai số tích lũy ±{total}mm."

  - id: DIM-009
    name: "Kích thước trùng lặp (over-dimensioning)"
    severity: major
    check: custom
    params: { handler: checks.redundancy.duplicate_dims }
    requires: dxf               # HOÃN — chỉ chạy được khi mở lại nhánh CAD (§1.2)
```

```yaml
# rules/30_symbols.yaml
rules:
  - id: SUR-001
    name: "Bề mặt lắp ghép không ghi độ nhám"
    severity: major
    check: custom
    params: { handler: checks.roughness.fit_surface_has_ra }
    confidence_gate: 0.90
    message_vi: "Bề mặt có dung sai lắp ghép {fit} nhưng không chỉ định độ nhám."

  - id: WLD-002
    name: "Ký hiệu hàn thiếu kích thước chân mối hàn"
    severity: major
    check: custom
    params: { handler: checks.weld.has_size }

  - id: THR-001
    name: "Ren không đúng danh mục tiêu chuẩn"
    severity: critical
    check: field_in_catalog
    params: { field: threads[].designation, catalog: catalogs/threads_iso_jis.yaml }
```

### 7.2 Vì sao YAML mà không hardcode

Bạn là quản lý, không phải người ngồi code mỗi ngày. Khi phát hiện một dạng lỗi mới trong buổi review, bạn phải thêm được quy tắc **trong 2 phút** bằng cách sửa file text — không phải mở issue, chờ dev, chờ deploy. `checks.*` chỉ là các hàm nguyên thủy dùng lại; 80% quy tắc mới sẽ chỉ là ghép các nguyên thủy có sẵn.

---

## 8. RỦI RO LỚN NHẤT: FALSE POSITIVE

Đây là chỗ 90% dự án loại này chết, và nó không liên quan gì đến AI.

**Kịch bản thất bại điển hình:** Công cụ chạy, báo 47 lỗi trên một bản vẽ. Nhân viên xem, thấy 40 lỗi là sai (công cụ hiểu nhầm). Tuần sau họ không mở công cụ nữa. Dự án chết sau 3 tuần, mặc dù OCR đạt 94%.

**Vì sao:** một công cụ review được đánh giá bằng **precision**, không phải recall. Bỏ sót một lỗi thì bạn vẫn ở nguyên hiện trạng (con người phải soi). Báo nhầm một lỗi thì bạn **làm tăng** khối lượng công việc so với không có công cụ. Cái sau tệ hơn hẳn cái trước.

### Đối sách bắt buộc

| # | Biện pháp |
|---|---|
| 1 | **Chỉ tiêu Phase 1: precision ≥ 98% ở mức FAIL.** Recall bao nhiêu cũng được, kể cả 30% |
| 2 | Chỉ đưa vào FAIL những quy tắc chạy trên dữ liệu ★★★★★. Mọi thứ từ OCR → tối đa là WARN |
| 3 | Bật quy tắc theo từng nhóm nhỏ. Mỗi lần bật thêm 3–5 quy tắc, chạy trên golden set, đo precision. Chưa đạt thì không phát hành |
| 4 | Có nút **"Báo sai"** ngay trên từng finding. Đây là nguồn dữ liệu quý nhất để tinh chỉnh |
| 5 | Cho phép **bỏ qua có lý do**: `# CHECKER-IGNORE: DIM-007 (thiết kế cố ý, đã duyệt bởi NVA)` — ghi vào note bản vẽ hoặc bảng exception |
| 6 | Dashboard hiển thị công khai tỉ lệ "báo sai" của chính công cụ. Minh bạch tạo lòng tin |

---

## 9. GOLDEN SET — VIỆC PHẢI LÀM TRƯỚC KHI VIẾT DÒNG CODE ĐẦU TIÊN

Không có bộ này, bạn không đo được gì, và mọi cải tiến chỉ là cảm tính.

**Yêu cầu:**

- **30–50 bản vẽ thật**, đã được bạn hoặc kỹ sư trưởng review thủ công.
- Mỗi bản kèm một file `.expected.json` liệt kê **toàn bộ lỗi đã biết**, mỗi lỗi có: mã quy tắc, mức nghiêm trọng, vị trí.
- Thành phần bắt buộc:
  - ~10 bản **hoàn toàn đúng** (để đo false positive — đây là phần quan trọng nhất, đừng bỏ qua)
  - ~10 bản JIS (có tiếng Nhật)
  - ~10 bản ISO/TCVN
  - ~10 bản có lỗi thật đã từng gây hậu quả ngoài xưởng
  - Đủ cả 2 nguồn xuất: AutoCAD và SolidWorks/Inventor/Creo
  - Vài trang dính bẫy SHX (không có text) và vài bản scan, để test nhánh dự phòng

```
tests/golden/
├── PRJ-KOBE-2026/
│   ├── KB-00123-A01.pdf          # 3 tờ trong 1 file
│   ├── KB-00123-A01.expected.json
│   ├── KB-00124-B02.pdf
│   └── KB-00124-B02.expected.json
└── manifest.yaml
```

```json
// KB-00123-A01.expected.json
{
  "must_find": [
    {"rule": "TB-007", "severity": "major"},
    {"rule": "PROJ-002", "severity": "critical"}
  ],
  "must_not_find": ["DIM-009"],
  "notes": "Bản vẽ dùng chuỗi kích thước 4 mắt xích nhưng đã được duyệt ngoại lệ."
}
```

CI chạy toàn bộ golden set mỗi lần commit. Precision tụt → build đỏ.

---

## 10. LỘ TRÌNH THEO PHASE

### Phase 0 — Dò dữ liệu thật (2–3 ngày, chưa viết code sản phẩm)

**Việc đầu tiên, làm ngay hôm nay:** chạy `tools/probe_pdf.py` lên thư mục bản vẽ thật.

```bash
pip install pdfplumber
python tools/probe_pdf.py "D:\BanVe" --dump-titleblock
```

Script trả lời bằng số liệu 7 câu hỏi mà nếu đoán sai sẽ phải viết lại extractor:

1. Bao nhiêu % trang đọc được text trực tiếp (và bao nhiêu % dính bẫy SHX)
2. Trang nào là vector, là scan, là lai
3. Khổ giấy / hướng giấy / góc xoay đang dùng
4. Vùng khung tên góc dưới phải có text không, text trông thế nào
5. Font nào đang dùng, có font ký hiệu GD&T không
6. Bắt được mã bản vẽ và "Sheet 1/3" không → biết PDF nhiều trang là bộ hay là tờ
7. Có tiếng Nhật trên bản vẽ không

**Cách đọc kết luận:**

| Kết quả | Nghĩa là | Hành động |
|---|---|---|
| ≥90% `VECTOR_TEXT_OK` | Đường đi sạch | Code thẳng Phase 1, không cần OCR, không cần GPU |
| 60–90% | Một phần bản vẽ mất text | **Sửa template AutoCAD trước** (đổi SHX → TrueType). Rẻ hơn viết OCR rất nhiều |
| <60% | Phần lớn mất text | Dừng lại. Đây là vấn đề quy trình xuất PDF, không phải vấn đề phần mềm |

Song song trong tuần đó:

| Việc | Đầu ra |
|---|---|
| Thu thập 150–200 bản vẽ thật (PDF), đủ cả 2 nguồn AutoCAD & SolidWorks | Kho mẫu |
| Xây golden set 30–50 bản (§9) | `tests/golden/` |
| Chụp/đo mẫu khung tên **công ty** — tọa độ từng ô, tính theo mm từ góc dưới phải | `config/templates/company_a3.yaml` |
| Liệt kê danh mục vật liệu / ren / xử lý bề mặt đang dùng | `config/catalogs/*.yaml` |
| Viết checklist review thủ công hiện tại của bạn ra giấy | Nguồn của rule Phase 1 |

> Việc cuối quan trọng hơn vẻ ngoài của nó: checklist trong đầu bạn chính là đặc tả sản phẩm. Nếu không viết ra, nó không tồn tại.

### Phase 1 — MVP: Khung tên từ PDF vector (3 tuần) ⭐

Phạm vi: **chỉ PDF vector, chỉ mẫu khung tên công ty, chỉ nhóm lỗi A, chỉ CLI, chỉ máy bạn.** Không AI, không GPU, không web, không database.

| Tuần | Việc |
|---|---|
| 1 | Khung dự án + `DrawingDoc` (per-page) + PDF extractor: chuẩn hóa xoay, dò khổ giấy, crop khung tên theo template mm, đọc text với `x_tolerance` đã chỉnh |
| 2 | Rule engine + 25–30 quy tắc khung tên. Gom trang → bản vẽ theo `drawing_no` + `sheet` |
| 3 | Xuất Excel + PDF markup khoanh đỏ. Chạy golden set, tinh chỉnh tới precision ≥98%. CLI hoàn chỉnh |

**Nghiệm thu Phase 1:**

- `drawing-check run "D:\BanVe\*.pdf"` → ra 1 file Excel + thư mục PDF đã khoanh đỏ
- Precision ≥ 98% ở mức FAIL trên golden set
- Bắt ≥ 80% lỗi khung tên trong golden set
- 300 trang xử lý < 3 phút trên CPU

**Giá trị nhận được ngay:** bạn thôi phải soi khung tên bằng mắt — khoảng 40% thời gian review.

### Phase 2 — Mở rộng độ phủ khung tên (2–3 tuần)

- Thêm 3–5 template khung tên khách hàng (chọn khách có sản lượng lớn nhất trước)
- Chế độ "dò lỏng": khi không khớp template nào, tìm nhãn theo từ khóa (`DRAWING NO`, `図番`, `MATERIAL`, `材質`) thay vì theo tọa độ. Kết quả chỉ được ở mức WARN
- Rule đồng bộ nhiều tờ: đủ tờ chưa, revision các tờ có khớp không
- Rule góc chiếu (`PROJ-001/002`) — xem §4.1

### Phase 3 — Kích thước, dung sai, GD&T từ PDF (4–6 tuần)

| Việc | Ghi chú |
|---|---|
| Xây bảng ánh xạ glyph cho font ký hiệu (bẫy 2, §1.4) | Việc phải làm trước, không né được |
| Parse dung sai: `±0.05`, `+0.1/-0`, `50H7`, `g6` | Regex trên text đã ánh xạ glyph |
| Validate mã lắp ghép theo ISO 286 / JIS B 0401 | Bảng tra dựng thành YAML |
| Parse GD&T frame | Ghép ký hiệu + datum + giá trị theo cụm tọa độ |
| Kiểm tra bề mặt có dung sai lắp ghép mà thiếu độ nhám | Rule ghép chéo, giá trị cao |

⚠️ **Cảnh báo phạm vi:** "Kiểm tra thiếu kích thước" theo nghĩa đầy đủ (bản vẽ đã đủ ràng buộc để chế tạo chưa) chưa giải được tự động hóa ở mức công nghiệp — và từ PDF thì càng không. Hãy giới hạn ở các dạng cụ thể, kiểm chứng được.

### Phase 4 — Ký hiệu công nghệ + Vision + bản vẽ scan (4–5 tuần)

*Đây là lúc GPU của bạn bắt đầu có việc.*

| Việc | Công nghệ |
|---|---|
| Gán nhãn 300–500 trang cho 9 nhóm ký hiệu | Label Studio (miễn phí) |
| Train detector khoanh vùng | RT-DETR hoặc YOLOv11, 1–2 giờ trên GPU của bạn |
| OCR vùng đã khoanh (VN/JP/EN) | PaddleOCR-VL |
| Nhánh xử lý trang `VECTOR_NO_TEXT` và `RASTER_SCAN` | Render 300 DPI → detector → OCR |
| VLM fallback cho vùng OCR thất bại | Qwen3-VL 8B, Ollama |

Tham chiếu: nghiên cứu 2025 dùng đúng kiến trúc hai tầng này (YOLOv11 khoanh vùng → model parse) đạt **F1 97.3%, precision GD&T 94.8%** trên 9 nhóm. Nhưng cũng báo **ảo giác 80%+ ở nhóm ít dữ liệu (vật liệu, dung sai chung)** — bằng chứng trực tiếp cho nguyên tắc "AI không được phán xử" ở §3.1.

### Phase 5 — Đối chiếu 3D ↔ 2D (CHỈ LẬP KẾ HOẠCH, chưa triển khai)

Mục tiêu bạn đã chốt: **"Kích thước ghi trên bản vẽ có đúng với mô hình 3D không?"** Đây là phép kiểm tra giá trị nhất trong toàn bộ hệ thống, vì nó bắt được dạng lỗi mà con người gần như không bắt nổi: *sửa model rồi quên cập nhật bản vẽ*.

**Điều kiện tiên quyết — chưa đủ thì đừng bắt đầu:**

1. Phase 3 đã chạy ổn định: phải trích được kích thước từ PDF đủ tin cậy trước đã. Không có vế 2D thì không có gì để đối chiếu.
2. Có cách ghép cặp file 3D ↔ file PDF (thường qua mã bản vẽ trong tên file).
3. Biết rõ định dạng 3D thực tế nhận được (xem bảng dưới).

**Định dạng 3D quyết định làm được gì:**

| Định dạng | Có hình học | Có dung sai/PMI | Kết luận |
|---|---|---|---|
| STEP AP242 | ✔ | ✔ (nếu người vẽ có gắn) | Tốt nhất — đối chiếu được cả dung sai |
| STEP AP203 / AP214 | ✔ | ✘ | Chỉ đối chiếu được kích thước danh nghĩa |
| IGES | ✔ (thường là mặt rời, dễ lỗi) | ✘ | Yếu nhất. Nên tránh nếu có lựa chọn khác |

**Phạm vi thực tế làm được (đừng hứa quá):** chỉ một số loại kích thước ghép cặp được tin cậy.

| Đối chiếu được | Không đối chiếu được |
|---|---|
| Kích thước bao (dài × rộng × cao) | Kích thước có chuỗi tham chiếu phức tạp |
| Đường kính lỗ trụ và số lượng lỗ | Kích thước tới mặt phẳng ảo/đường tâm dựng |
| Khoảng cách tâm lỗ ↔ tâm lỗ | Kích thước góc trên mặt cong |
| Bề dày tấm | Kích thước tham khảo trong ngoặc |
| Bán kính bo tiêu chuẩn | GD&T (trừ khi có AP242 PMI) |

**Cách làm dự kiến:** dùng `pythonocc-core` đọc STEP → trích *danh mục đặc trưng* (lỗ trụ: tâm+đường kính+chiều sâu; hộp bao; bề dày; bán kính) → so khớp mờ với danh sách kích thước lấy từ PDF theo giá trị + dung sai → chỉ báo khi lệch quá dung sai cho phép, và **luôn ở mức WARN, không bao giờ FAIL** (vì việc ghép cặp là suy đoán).

**Sản phẩm phụ đáng làm trước:** cũng với `pythonocc-core`, kiểm tra khả năng chế tạo (bề dày tối thiểu, bán kính bo nhỏ hơn dao, tỉ lệ sâu/đường kính lỗ) — không cần vế 2D, độc lập hoàn toàn, và có thể làm sớm nếu bạn thấy cần.

---

## 11. CẤU TRÚC REPO

```
drawing-check/
├── pyproject.toml
├── README.md
│
├── tools/
│   ├── probe_pdf.py                  # ⭐ CHẠY ĐẦU TIÊN — dò bản vẽ thật (Phase 0)
│   └── bench_pdf_libs.py             # so tốc độ + chất lượng thư viện trên bản vẽ của bạn
│
├── config/
│   ├── settings.yaml
│   ├── templates/                    # tọa độ ô khung tên, tính theo MM
│   │   ├── company_a3.yaml            #   từ góc DƯỚI PHẢI của trang
│   │   ├── company_a4.yaml
│   │   └── _loose.yaml               # chế độ dò theo từ khóa (Phase 2)
│   ├── glyphmaps/                    # ánh xạ font ký hiệu → Unicode (bẫy 2, §1.4)
│   │   ├── amgdt.yaml
│   │   └── gdt_shx.yaml
│   └── catalogs/
│       ├── materials.yaml
│       ├── threads_iso_jis.yaml
│       ├── fits_iso286.yaml
│       └── surface_treatments.yaml
│
├── rules/
│   ├── 10_title_block.yaml           # Phase 1
│   ├── 15_multisheet.yaml            # Phase 2 — đồng bộ nhiều tờ
│   ├── 20_dimension.yaml             # Phase 3
│   └── 30_symbols.yaml               # Phase 4
│
├── src/drawing_check/
│   ├── core/
│   │   ├── model.py                  # PageDoc, DrawingDoc, Field, Provenance
│   │   ├── finding.py                # Finding, Severity, Confidence
│   │   └── grouping.py               # gom trang → bản vẽ theo drawing_no + sheet
│   ├── extract/
│   │   ├── pdf_page.py               # chuẩn hoá xoay, dò khổ giấy, phân loại trang
│   │   ├── titleblock.py             # crop theo template mm + đọc text
│   │   ├── glyphmap.py               # sửa ký tự rác từ font ký hiệu
│   │   └── text_utils.py             # gộp glyph rời thành từ (bẫy 3)
│   ├── vision/                       # Phase 4 — để trống tới lúc đó
│   ├── engine/
│   │   ├── loader.py
│   │   ├── runner.py
│   │   ├── primitives.py             # field_present, field_matches, field_in_catalog...
│   │   └── checks/
│   ├── report/
│   │   ├── excel.py                  # xlsxwriter
│   │   ├── pdf_markup.py             # PyMuPDF khoanh đỏ + comment
│   │   └── console.py
│   └── cli.py                        # typer
│
└── tests/
    ├── golden/                       # §9
    ├── unit/
    └── test_precision.py             # CI gate: precision tụt → build đỏ
```

---

## 12. CÔNG SỨC & MỐC THỜI GIAN

| Phase | Nội dung | Thời gian | GPU? | Giá trị tích lũy |
|---|---|---|---|---|
| 0 | Dò dữ liệu (`probe_pdf.py`) + golden set + template | 2–3 ngày | Không | Nền tảng đo lường |
| 1 | Khung tên từ PDF vector, mẫu công ty, CLI | **3 tuần** | Không | **~40% lỗi** |
| 2 | Thêm template khách hàng + đồng bộ nhiều tờ | 2–3 tuần | Không | ~50% lỗi |
| 3 | Kích thước, dung sai, GD&T từ PDF | 4–6 tuần | Không | ~75% lỗi |
| 4 | Ký hiệu công nghệ + Vision + bản vẽ scan | 4–5 tuần | **Có** | ~88% lỗi |
| 5 | Đối chiếu 3D ↔ 2D | *chưa triển khai* | Không | — |
| — | Dashboard + hàng đợi (chỉ khi có người dùng thứ 2) | 3 tuần | Không | Cả phòng dùng được |
| | **Tổng tới hết Phase 4** | **~4 tháng** | | |

**Chi phí phần mềm: 0 đ.** Chi phí thật là **2–3 ngày Phase 0** — khoản đầu tư có tỉ suất sinh lời cao nhất trong cả dự án.

**Lưu ý về Dashboard:** bạn đã chốt Phase 1 chỉ mình bạn dùng trên máy cá nhân. Vậy nên dashboard và hàng đợi **rơi khỏi đường găng** — chỉ xây khi có người dùng thứ hai. Riêng điều này tiết kiệm khoảng 3 tuần so với bản kế hoạch 1.0.

---

## 13. NHỮNG ĐIỀU TÔI KHUYÊN BẠN KHÔNG LÀM

| Đừng | Vì sao |
|---|---|
| Đừng bắt đầu bằng scan/ảnh | PDF vector cho 99% độ chính xác. Render ra ảnh rồi OCR là tự nguyện tụt xuống 90% |
| Đừng để LLM quyết định pass/fail | Không tái lập được, không giải thích được, không bảo vệ được trước nhân viên |
| Đừng làm dashboard ở Phase 1 | Bạn là người dùng duy nhất. Excel + CLI là đủ. Dashboard chỉ xây khi có người dùng thứ hai |
| Đừng viết OCR trước khi sửa template AutoCAD | Nếu bản vẽ dính bẫy SHX, sửa font trong template là việc 1 giờ và giải quyết vĩnh viễn. Viết OCR để chữa nó là việc 3 tuần và chỉ đạt 90% |
| Đừng chốt kiến trúc trước khi chạy `probe_pdf.py` | Mọi con số trong tài liệu này là ước lượng. Script cho bạn số thật trong 5 phút |
| Đừng cố "kiểm tra thiếu kích thước" một cách tổng quát | Bài toán chưa giải được. Hãy làm các trường hợp cụ thể, kiểm chứng được |
| Đừng train model riêng ở Phase 1–2 | Chưa có dữ liệu gán nhãn, chưa biết cần gì. Train sớm là lãng phí GPU và thời gian |
| Đừng bật hết quy tắc cùng lúc | Bật từng nhóm, đo precision từng nhóm. Đây là kỷ luật giữ cho công cụ đáng tin |
| Đừng dùng thống kê lỗi để phạt nhân viên | Họ sẽ tối ưu để qua checker, không phải để bản vẽ đúng. Dùng để tìm lỗ hổng đào tạo |

---

## 14. BƯỚC KẾ TIẾP NGAY

**Hôm nay (30 phút):**

```bash
pip install pdfplumber
python tools/probe_pdf.py "D:\ThuMucBanVe" --dump-titleblock
```

Gửi tôi ba thứ:

1. `probe_report.csv` — tôi đọc được ngay tình trạng thật của bản vẽ công ty bạn
2. `probe_titleblocks.txt` — tôi thấy được cấu trúc khung tên thật, dựng luôn template
3. **1 file PDF mẫu** (bản vẽ nội bộ, che thông tin nhạy cảm nếu cần)

**Tuần này:**

4. Viết ra checklist review thủ công bạn đang dùng → tôi chuyển thành `rules/10_title_block.yaml` hoàn chỉnh
5. Danh mục vật liệu công ty đang dùng (một danh sách text đơn giản là đủ)

Có đủ 5 thứ trên, tôi viết được extractor + rule engine chạy thật trên bản vẽ của bạn, không cần đoán chỗ nào.

---

## PHỤ LỤC A — Nguồn tham khảo

- Automated Parsing of Engineering Drawings for Structured Information Extraction — arXiv 2505.01530 (kiến trúc YOLOv11 + parser, F1 97.3%)
- Intelligent GD&T symbol detection in mechanical drawings: YOLOv11 vs Faster R-CNN vs RetinaNet
- pypdfium2 — https://github.com/pypdfium2-team/pypdfium2
- pypdf — https://github.com/py-pdf/pypdf
- pdfplumber — https://github.com/jsvine/pdfplumber
- Benchmark thư viện trích xuất PDF — https://github.com/justin-aj/pdf-extraction-benchmark
- ezdxf documentation (dự phòng, nhánh CAD) — https://ezdxf.readthedocs.io/
- Open CASCADE STEP Translator — https://dev.opencascade.org/doc/overview/html/occt_user_guides__step.html
- CadQuery — https://cadquery.readthedocs.io/
- Best Open-Source OCR Models 2026 — bảng so sánh PaddleOCR-VL / DeepSeek-OCR / GLM-OCR / olmOCR
