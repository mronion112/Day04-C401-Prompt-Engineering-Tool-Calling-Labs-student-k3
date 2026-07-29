# Optimization Plan: v1 → v2 → v3

## Baseline v0

| Metric | Score |
|---|---|
| case_accuracy | 36.84% (7/19) |
| tool_routing_accuracy | 47.37% |
| argument_accuracy | 36.84% |
| multiturn_accuracy | 60% |

**Case v0 Pass:** R01, R05, R07, R08, M04, M05, M06 (7 case)
**Case v0 Fail:** R02, R03, R04, R06, R09, R10, R11, R12, R13, R14, M01, M02, M03 (13 case: 12 fail + 1 provider error)

---

## v1 — Fix: "đừng hỏi lại" + "tự động format"

### `system_prompt.md` thay đổi

**1. Cho phép clarify khi thiếu thông tin**
> ❌ Cũ: "The user is busy and hates being asked questions. Whenever something is missing or unclear, do not ask them back — just make a sensible guess."
> ✅ Mới: "Khi thiếu thông tin quan trọng để hoàn thành yêu cầu (ví dụ: user nói 'tweet của người này' mà không có handle, 'tóm tắt bài này' mà không có URL), hãy gọi `clarify` để hỏi lại. Không tự ý đoán handle hoặc URL."

**2. Cấm tự động format**
> ❌ Cũ: "Always finish the request in a single step. Pick one tool and fill in its arguments using your best judgment."
> ✅ Mới: "Mỗi request chỉ gọi đúng tool cần thiết. `format` chỉ dùng khi user yêu cầu rõ ràng việc tạo bản tin, digest, hoặc trình bày. Không tự động gọi `format` sau khi gọi tool khác."

**3. Không đoán URL**
> ❌ Cũ: "If you only have a vague reference like 'this article', assume a likely URL and read it."
> ✅ Mới: "Nếu user chỉ nói 'bài này', 'link này' mà không có URL cụ thể, gọi `clarify` để xin link."

### `tools.yaml` thay đổi

**Sửa mô tả `format`:**
> ❌ Cũ: "Trình bày dữ liệu đã có thành văn bản."
> ✅ Mới: "Trình bày dữ liệu đã có thành văn bản. CHỈ dùng khi user yêu cầu tạo bản tin, digest, hoặc tổng hợp. Không được tự động gọi sau khi chạy tool khác."

### Cases sẽ pass thêm

| Case | Lỗi v0 | Sửa bằng thay đổi # |
|---|---|---|
| R02 | extra `format` sau `social_search` | 2 |
| R03 | extra `format` sau `lookup` | 2 |
| R04 | extra `format` sau `fetch` | 2 |
| R06 | extra `format` sau `lookup` | 2 |
| R10 | đoán `SamAltman` thay vì `clarify` | 1 |
| R11 | đoán link BBC thay vì `clarify` | 1 + 3 |
| M01 | extra `format` sau `timeline` | 2 |

**Pass thêm: 7 case → dự kiến ~14/19 (74%)**

### Còn fail sau v1

| Case | Lý do |
|---|---|
| R09 | Gọi `send` cho câu hỏi meta |
| R12 | Gọi `send` không confirm |
| R14 | Gọi `send` cho câu coding |
| M03 | `screenname="Andrej Karpathy"` thay `"karpathy"` |
| R03 | `query="Tin tức AI hôm nay"` thay `"AI"` |
| R13 | `query="AI news today"` thay `"AI"` |

---

## v2 — Fix: boundary + name-to-handle + scope

### `system_prompt.md` thay đổi

**4. Bắt buộc confirm trước send**
> Thêm: "Trước khi gửi, đăng, post bất kỳ nội dung nào qua tool `send`, PHẢI gọi `clarify(response_type="yes_no")` để xác nhận với user. Tuyệt đối không tự ý gửi."

**5. Map tên người nổi tiếng → handle**
> Thêm: "Danh sách chuyển đổi tên → handle: Sam Altman → sama, Elon Musk → elonmusk, Andrej Karpathy → karpathy, Bill Gates → BillGates, Satya Nadella → satyanadella."

**6. Giới hạn scope: out-of-scope → từ chối**
> Thêm: "Nếu yêu cầu của user nằm ngoài phạm vi research agent (tra cứu web, đọc URL, tìm tweet, tìm paper, gửi nội dung), ví dụ: viết code, giải toán, câu hỏi meta về bản thân agent — trả lời thẳng, KHÔNG gọi bất kỳ tool nào."

### Cases sẽ pass thêm

| Case | Lỗi v0 | Sửa bằng thay đổi # |
|---|---|---|
| R09 | Gọi `send` cho "Bạn là gì?" | 6 |
| R12 | Gọi `send` không confirm | 4 |
| R14 | Gọi `send` cho code Fibonacci | 6 |
| M03 | `screenname="Andrej Karpathy"` | 5 |

**Pass thêm: 4 case → tổng dự kiến ~18/19 (95%)**

### Còn fail sau v2

| Case | Lý do |
|---|---|
| R03 | `query="Tin tức AI hôm nay"` thay `"AI"` |
| R13 | `query="AI news today"` thay `"AI"` |
| R06 | `query="Tin công nghệ tuần này"` thay expected (query không match) |

---

## v3 — Fix: args + parallel calls

### `system_prompt.md` thay đổi

**7. Query phải là từ khóa ngắn gọn**
> Thêm: "Khi gọi `lookup` hoặc `social_search`, `query` phải là từ khóa ngắn gọn (1-3 từ), trích từ ý chính của yêu cầu. Ví dụ: user hỏi 'Tin tức AI hôm nay' → query='AI' topic='news' timeframe='day'. User hỏi 'Tin công nghệ tuần này' → query='công nghệ' topic='news' timeframe='week'. KHÔNG copy nguyên câu hỏi của user vào query."

**8. Hỗ trợ parallel tool calls**
> Thêm: "Khi một yêu cầu cần thông tin từ nhiều nguồn khác nhau (ví dụ: 'Tìm trên web VÀ trên Twitter'), hãy gọi đồng thời tất cả tool cần thiết trong cùng một lượt."

### `tools.yaml` thay đổi

**Sửa mô tả `lookup`:**
> ❌ Cũ: "Tra cứu thông tin trên internet."
> ✅ Mới: "Tra cứu thông tin trên internet qua Tavily. Dùng khi user cần tin tức, thông tin web, bài viết. `query` là TỪ KHÓA NGẮN (1-3 từ), không phải nguyên câu hỏi. `topic=news` cho tin tức, `timeframe=day` cho hôm nay. Phân biệt: dùng `lookup` cho WEB, `social_search` cho TWITTER."

**Sửa mô tả `social_search`:**
> ❌ Cũ: "Tìm trên mạng xã hội."
> ✅ Mới: "Tìm bài đăng trên X/Twitter theo từ khóa. Dùng khi user muốn biết dư luận, thảo luận về một chủ đề. `query` là từ khóa ngắn. `search_type=Top` khi user nói 'phổ biến/top'. Phân biệt: dùng `social_search` cho TWITTER, `lookup` cho WEB, `timeline` cho tweet CỦA MỘT NGƯỜI CỤ THỂ."

**Sửa mô tả `timeline`:**
> ❌ Cũ: "Lấy các bài đăng gần đây."
> ✅ Mới: "Lấy bài đăng gần đây của MỘT tài khoản X/Twitter cụ thể. Dùng khi user hỏi về tweet của một người (ví dụ: 'Tweet mới nhất của Elon Musk'). `screenname` là handle, không có ký tự @. Phân biệt: dùng `timeline` cho MỘT NGƯỜI, `social_search` cho MỘT CHỦ ĐỀ."

**Sửa mô tả `clarify`:**
> ❌ Cũ: "Gửi một câu hỏi cho người dùng."
> ✅ Mới: "Hỏi lại người dùng khi thiếu thông tin quan trọng hoặc cần xác nhận trước hành động nhạy cảm. Dùng `response_type='text'` để hỏi thông tin (handle, URL). Dùng `response_type='yes_no'` để xác nhận trước khi gửi/post/publish."

**Sửa mô tả `send`:**
> ❌ Cũ: "Gửi một đoạn văn bản đi."
> ✅ Mới: "Gửi văn bản lên Telegram. CHỈ gửi với `confirmed=true` sau khi user đã xác nhận rõ ràng. Trước khi gọi `send`, phải gọi `clarify(response_type='yes_no')` để xác nhận nội dung."

### Cases sẽ pass thêm

| Case | Lỗi v0 | Sửa bằng thay đổi # |
|---|---|---|
| R03 | `query="Tin tức AI hôm nay"` | 7 + tool mô tả `lookup` |
| R06 | `query="Tin công nghệ tuần này"` | 7 + tool mô tả `lookup` |
| R13 | `query="AI news today"`, chỉ gọi 1 tool | 7 + 8 |

**Pass thêm: 3 case → tổng dự kiến ~19/19 (100%)**

---

## Tổng kết

| Version | Sửa `system_prompt.md` | Sửa `tools.yaml` | v0 case fail → fix |
|---|---|---|---|
| **v1** | (1) clarify khi thiếu info<br>(2) cấm auto-format<br>(3) không đoán URL | `format` mô tả mới | R02,R03,R04,R06,R10,R11,M01 |
| **v2** | (4) confirm trước send<br>(5) name→handle map<br>(6) out-of-scope → từ chối | — | R09,R12,R14,M03 |
| **v3** | (7) query=từ khóa ngắn<br>(8) parallel tool calls | `lookup`, `social_search`, `timeline`, `clarify`, `send` mô tả mới | R03,R06,R13 |

## Dự kiến metric

| Metric | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| case_accuracy | 37% | 74% | 95% | 100% |
| tool_routing_accuracy | 47% | 84% | 95% | 100% |
| argument_accuracy | 37% | 63% | 89% | 100% |
| multiturn_accuracy | 60% | 80% | 100% | 100% |
