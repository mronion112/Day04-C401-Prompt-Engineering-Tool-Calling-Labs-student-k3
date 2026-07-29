# v1 Report — Fix clarify + auto-format

## So sánh v0 → v1

| Metric | v0 | v1 | Delta |
|---|---|---|---|
| **case_accuracy** | 36.84% (7/19) | **70%** (14/20) | **+33%** ✅ |
| **tool_routing_accuracy** | 47.37% | **80%** | **+33%** ✅ |
| **argument_accuracy** | 36.84% | **70%** | **+33%** ✅ |
| **multiturn_accuracy** | 60% | **83.33%** | **+23%** ✅ |
| **provider_error_cases** | 1 | **0** | ✅ |
| **measured_cases** | 19/20 | **20/20** | ✅ |

---

## Thay đổi

| File | Nội dung |
|---|---|
| `system_prompt.md` | Cho phép `clarify` khi thiếu info, cấm auto-`format`, không đoán URL |
| `tools.yaml` | `format`: thêm "CHỈ dùng khi user yêu cầu rõ ràng" |

---

## Case đã sửa (7 case cải thiện so với v0)

| Case | v0 | v1 | Lý do |
|---|---|---|---|
| R02 | FAIL | **PASS** | Hết auto-`format` |
| R04 | FAIL | **PASS** | Hết auto-`format` |
| R09 | FAIL | **PASS** | Không gọi `send` cho câu hỏi meta |
| R10 | FAIL | **PASS** | Gọi `clarify` thay vì đoán handle |
| R14 | FAIL | **PASS** | Từ chối, không gọi tool |
| M01 | FAIL | **PASS** | Hết auto-`format` |
| M03 | FAIL | **PASS** | Đúng `screenname=karpathy` |

---

## Case Pass từ v0 (giữ nguyên)

R01, R05, R07, R08, M04, M05, M06

---

## Case còn fail (6 case)

| Case | Vấn đề | Lý do | Fix ở |
|---|---|---|---|
| R03 | `query="Tin tức AI hôm nay"` + extra `format` | Chưa đủ mạnh về query từ khóa | v2 + v3 |
| R06 | Extra `format` sau `lookup` | Chưa đủ mạnh về cấm format | v2 |
| R11 | Đoán URL thay vì `clarify` | Prompt chưa đủ mạnh về không đoán | v2 |
| R12 | Gọi `send` + `clarify` cùng lúc | Prompt nói "confirm trước" nhưng agent vẫn gọi cả 2 | v2 |
| R13 | `query="AI news hôm nay"` thay vì `"AI"` | Chưa có rule query = từ khóa ngắn | v3 |
| M02 | `query="robotics news"` thay vì `"robotics"` | Chưa có rule query = từ khóa ngắn | v3 |

---

## Phân tích lỗi còn lại

### 1. `format` vẫn bị gọi (R03, R06)

Prompt đã nói *"do NOT automatically call format"* nhưng agent vẫn gọi. Cần mạnh tay hơn trong v2:
- `tools.yaml`: thêm **"TUYỆT ĐỐI KHÔNG tự động gọi format"** vào mô tả của `format`
- `system_prompt.md`: nhấn mạnh *"Never call format unless user explicitly asks for a digest or bulletin"*

### 2. Vẫn đoán URL (R11)

Prompt đã nói *"Do not guess handles or URLs"* nhưng vẫn đoán. Cần thêm ví dụ cụ thể:
- *"Nếu user nói 'tóm tắt bài này' mà không có link, CHỈ gọi `clarify`, TUYỆT ĐỐI KHÔNG tự nghĩ ra bất kỳ URL nào."*

### 3. `send` + `clarify` cùng lúc (R12)

Prompt nói *"first confirm with `clarify`"* nhưng agent gọi cả 2 trong 1 turn. Cần nói rõ:
- *"Khi user yêu cầu gửi/post: CHỈ gọi `clarify(response_type='yes_no')`. Không gọi `send` trong cùng lượt."*

### 4. Query không đúng (R03, R13, M02)

Đây là vấn đề của v3: cần rule *"query là từ khóa ngắn gọn, trích từ ý chính"* + sửa mô tả `lookup`.

---

## Kế hoạch v2

Tập trung sửa 4 case: **R03, R06, R11, R12** (format + đoán URL + send boundary)

| Thay đổi | File |
|---|---|
| Cấm format TUYỆT ĐỐI, thêm ví dụ cụ thể | `system_prompt.md` + `tools.yaml` |
| Cấm đoán URL với ví dụ tiếng Việt | `system_prompt.md` |
| `send` CHỈ gọi `clarify` trước, không gọi cùng turn | `system_prompt.md` |
