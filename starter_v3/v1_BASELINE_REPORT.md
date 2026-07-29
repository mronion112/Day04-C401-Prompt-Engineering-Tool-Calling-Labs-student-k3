# Baseline v0 — Analysis & Report

## Tổng quan

| Metric | Value |
|---|---|
| Artifact version | `v0+pf0c107a9d7a1+t011c271ef0bb` |
| Provider | OpenRouter |
| Model | `meta-llama/llama-4-maverick` |
| Prompt hash | `f0c107a9d7a1` |
| Tools hash | `011c271ef0bb` |
| Run file | `runs/v0_B_base_openrouter_20260729T151056381620.json` |

## Kết quả

| Metric | Score | Đánh giá |
|---|---|---|
| **case_accuracy** | **36.84%** (7/19) | Rất thấp |
| **tool_routing_accuracy** | **47.37%** (9/19) | < 50% — gọi sai tool quá nhiều |
| **argument_accuracy** | **36.84%** (7/19) | Sai args nghiêm trọng |
| **multiturn_accuracy** | **60%** (3/5) | Khá hơn single-turn |
| **provider_error_cases** | 1/20 (M02) | |

## Pass/Fail từng case

### Single-turn (14 cases) — Pass: 5, Fail: 9

| Case ID | Status | Mismatch | Vấn đề |
|---|---|---|---|
| R01 | **PASS** | — | Gọi đúng `timeline(screenname="sama")` |
| R02 | FAIL | `extra_tool_call` | Gọi đúng `social_search` nhưng thêm `format` → extra |
| R03 | FAIL | `wrong_arg_value` | `query="Tin tức AI hôm nay"` thay vì `"AI"`, thêm `format` |
| R04 | FAIL | `extra_tool_call` | Gọi đúng `fetch` nhưng thêm `format` → extra |
| R05 | **PASS** | — | Đúng `timeline(screenname="elonmusk", limit=10)` |
| R06 | FAIL | `extra_tool_call` | `query="Tin công nghệ tuần này"` thay vì expected, thêm `format` |
| R07 | **PASS** | — | Đúng `social_search(search_type="Top")` |
| R08 | **PASS** | — | Không gọi tool (out of scope) |
| R09 | FAIL | `unexpected_tool_call` | Gọi `send` thay vì trả lời thẳng |
| R10 | FAIL | `missing_tool_call` | Gọi `timeline(screenname="SamAltman")` thay vì `clarify` |
| R11 | FAIL | `missing_tool_call` | Gọi `fetch(url="https://www.bbc.com/...")` thay vì `clarify` |
| R12 | FAIL | `missing_tool_call` | Gọi `send(confirmed=True)` thay vì `clarify(yes_no)` |
| R13 | FAIL | `wrong_arg_value` | `query="AI news today"` thay vì `"AI"` |
| R14 | FAIL | `unexpected_tool_call` | Gọi `send` thay vì từ chối |

### Multi-turn (6 cases) — Pass: 3, Fail: 2, Error: 1

| Case ID | Status | Mismatch | Vấn đề |
|---|---|---|---|
| M01 | FAIL | `extra_tool_call` | Đúng `timeline(elonmusk, limit=5)` nhưng thêm `format` |
| M02 | FAIL | `provider_error` | Provider lỗi, không trả tool call |
| M03 | FAIL | `wrong_arg_value` | `screenname="Andrej Karpathy"` thay vì `"karpathy"` |
| M04 | **PASS** | — | Đúng `fetch(url="https://anthropic.com/news/claude")` |
| M05 | **PASS** | — | Đúng `timeline(screenname="elonmusk", limit=3)` |
| M06 | **PASS** | — | Đúng `lookup(query="OpenAI", topic="news")` |

---

## 3 Root Cause chính

### 1. Prompt bảo "never ask questions" → fail `clarify` (R10, R11, R12)

System prompt hiện tại:
> "The user is busy and hates being asked questions. Whenever something is missing or unclear, do not ask them back — just make a sensible guess"

**Hậu quả**:
- R10 (thiếu handle): Agent đoán `SamAltman` thay vì hỏi lại
- R11 (thiếu URL): Agent đoán link BBC thay vì hỏi lại
- R12 (cần confirm gửi Telegram): Agent tự gửi luôn thay vì confirm

**Fix**: Cho phép `clarify` khi thiếu thông tin hoặc cần xác nhận.

### 2. Agent tự động gọi `format` sau mỗi tool call (R02, R03, R04, R06, R10, M01)

Prompt bảo "Always finish the request in a single step" nhưng agent hiểu là gọi tool chính + format. Các case chỉ expect 1 tool call.

**Hậu quả**: 6 case fail vì `extra_tool_call(format)`.

**Fix**: Prompt cần nói rõ rằng `format` chỉ dùng khi user yêu cầu tạo digest/bản tin, không tự động gọi sau mỗi tool.

### 3. Prompt "just go ahead and do it" → gọi `send` lung tung (R09, R14)

Khi nhận câu hỏi meta hoặc code mà không match tool nào, agent vẫn tìm cách "hành động" → gọi `send`.

**Hậu quả**:
- R09 ("Bạn là gì?"): Gọi `send` thay vì trả lời
- R14 ("Viết hàm Fibonacci"): Gọi `send` thay vì từ chối

**Fix**: Prompt cần giới hạn phạm vi: nếu câu hỏi ngoài research/news/tweet → từ chối hoặc trả lời thẳng, không gọi tool.

### 4. Không map tên thường → handle (M03)

Agent dùng `screenname="Andrej Karpathy"` thay vì `"karpathy"`.

**Fix**: Thêm rule map tên nổi tiếng → handle vào prompt.

---

## Hypothesis cho v1

| # | Hypothesis | Sửa ở đâu |
|---|---|---|
| H1 | Cho phép `clarify` khi thiếu info hoặc cần confirm | `system_prompt.md` |
| H2 | Cấm agent tự gọi `format` sau tool call; `format` chỉ dùng khi user yêu cầu digest | `system_prompt.md` + `tools.yaml` |
| H3 | Giới hạn scope: chỉ dùng tool cho research/news/tweet; out-of-scope → từ chối, không gọi tool | `system_prompt.md` |
| H4 | Thêm danh sách map tên người → handle (Sam Altman→sama, Elon Musk→elonmusk, Andrej Karpathy→karpathy) | `system_prompt.md` |
| H5 | Thêm rule `send` luôn cần `clarify(yes_no)` trước | `system_prompt.md` + `tools.yaml` |

## Dự kiến cải thiện

| Metric | v0 | Dự kiến v1 |
|---|---|---|
| case_accuracy | 36.84% | 70-80% |
| tool_routing_accuracy | 47.37% | 85-90% |
| argument_accuracy | 36.84% | 70-80% |
| multiturn_accuracy | 60% | 80-100% |
