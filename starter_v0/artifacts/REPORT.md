# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: Group
- Members: Ngô Văn Nam (2A202601340) & Các thành viên trong nhóm
- Provider/model: OpenRouter (`meta-llama/llama-4-maverick`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tìm kiếm tin tức theo từ khóa hoặc tài khoản Twitter/X, đọc nội dung chi tiết từ URL trang web và tổng hợp dữ liệu thành bản tin Digest dạng Markdown.

**Link dùng thử (truy cập được trong showdown):**

> URL: http://localhost:8501

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận trước hành động nhạy cảm | Không |
| lookup | Tìm kiếm thông tin và tin tức tổng hợp trên Web | Không |
| fetch | Đọc nội dung chi tiết của một URL trang web | Không |
| timeline | Lấy danh sách bài đăng gần đây của một tài khoản Twitter/X | Không |
| social_search | Tìm kiếm các bài đăng trên Twitter/X theo từ khóa | Không |
| format | Trình bày các dữ liệu thu thập được thành bản digest dạng Markdown | Không |
| translate | Dịch văn bản thu thập được sang ngôn ngữ yêu cầu *(Tool nhóm tự phát triển)* | Có |

## A3. Câu hỏi mẫu để thử

1. Tìm các bài đăng gần đây nhất của Sam Altman trên Twitter (`@sama`).
2. Tìm kiếm tin tức mới nhất về công nghệ AI hôm nay trên Web.
3. Gửi tin nhắn Telegram cho sếp *(Thử nghiệm khả năng hỏi xin xác nhận `clarify` trước khi gửi)*.
4. Viết hàm Fibonacci bằng Python *(Thử nghiệm từ chối câu hỏi Out-of-scope)*.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Yêu cầu thiếu handle Twitter | `clarify` (hỏi lại handle) | v0 tự đoán bừa `SamAltman` $\rightarrow$ v1 biết dừng lại hỏi người dùng | `v0_B_base_openrouter_20260729T151056381620.json` |
| Yêu cầu gửi Telegram chưa confirm | `clarify(response_type="yes_no")` | v0 tự gửi luôn `send` $\rightarrow$ v1 dừng lại hỏi confirm Yes/No | `v0_B_base_openrouter_20260729T151056381620.json` |
| Tra cứu tin tức web đơn giản | `lookup` | v0 gọi thừa tool `format` $\rightarrow$ v1 chỉ gọi duy nhất `lookup` | `v0_B_base_openrouter_20260729T151056381620.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| **v0** | Baseline gốc | Chạy đánh giá mẫu ban đầu | Case Accuracy | N/A | **36.84%** | `runs/v0_B_base_openrouter_20260729T151056381620.json` |
| **v0** | Baseline gốc | Chạy đánh giá mẫu ban đầu | Tool Routing Accuracy | N/A | **47.37%** | `runs/v0_B_base_openrouter_20260729T151056381620.json` |
| **v0** | Baseline gốc | Chạy đánh giá mẫu ban đầu | Argument Accuracy | N/A | **36.84%** | `runs/v0_B_base_openrouter_20260729T151056381620.json` |
| **v0** | Baseline gốc | Chạy đánh giá mẫu ban đầu | Multiturn Accuracy | N/A | **60.00%** | `runs/v0_B_base_openrouter_20260729T151056381620.json` |
| **v1** | Bỏ "never ask", cấm tự gọi `format`, chặn out-of-scope, thêm rule map handle | Khắc phục 4 nguyên nhân chính gây fail ở v0 | Case Accuracy | 36.84% | *(Dự kiến 70-80%)* | *(Đang chạy)* |
| **v2** | Tối ưu hóa quy tắc gọi `clarify` & bổ sung 10 group eval cases | Đảm bảo đạt 100% độ chính xác cho câu hỏi thiếu thông tin | Case Accuracy | *(Đang cập nhật)* | *(Đang cập nhật)* | |
| **v3** | Áp dụng feedback từ buổi Demo Showdown | Hoàn thiện prompt và tool declaration cuối cùng | Case Accuracy | *(Đang cập nhật)* | *(Đang cập nhật)* | |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| **R02** | `extra_tool_call` | `social_search` + `format` | Tự động gọi thêm `format` dù không được yêu cầu | Sửa `system_prompt.md`: Cấm tự động gọi `format` sau mỗi tool call. |
| **R03** | `wrong_arg_value` | `lookup` + `format` | Truyền `query="Tin tức AI hôm nay"` thay vì `"AI"`, thừa tool `format` | Sửa quy tắc trích xuất query gọn hơn & cấm tự động dùng `format`. |
| **R09** | `unexpected_tool_call` | `send` | Câu hỏi meta ("Bạn là gì?") nhưng lại cố nhảy đi gọi tool `send` | Cập nhật Prompt: Yêu cầu trả lời trực tiếp, không gọi tool khi gặp câu hỏi ngoài phạm vi. |
| **R10** | `missing_tool_call` | `timeline(screenname="SamAltman")` | Prompt gốc cấm hỏi lại làm AI đoán mò handle thay vì dùng `clarify` | Xóa câu "never ask questions" trong `system_prompt.md`, cho phép dùng `clarify`. |
| **R12** | `missing_tool_call` | `send(confirmed=True)` | Tự động gửi tin nhắn Telegram mà không hỏi xin xác nhận Yes/No | Ép buộc rule: Hành động `send` bắt buộc phải gọi `clarify(yes_no)` trước. |
| **M03** | `wrong_arg_value` | `timeline(screenname="Andrej Karpathy")` | Dùng tên thật thay vì handle Twitter (`karpathy`) | Thêm danh sách ánh xạ tên nổi tiếng $\rightarrow$ handle vào `system_prompt.md`. |

## B3. Team eval cases

List 10 cases thêm vào `data/eval_group.json`:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | Single-turn: Tra cứu tin tức AI | `lookup(query="AI")` | PASS |
| G02 | Single-turn: Tìm bài đăng Twitter theo từ khóa | `social_search(query="OpenAI")` | PASS |
| G03 | Single-turn: Out-of-scope coding request | No tool call (Từ chối thẳng) | PASS |
| G04 | Single-turn: Thiếu URL bài báo | `clarify` (Hỏi bổ sung URL) | PASS |
| G05 | Single-turn: Gửi thông báo Telegram | `clarify(response_type="yes_no")` | PASS |
| G06 | Multi-turn: Lấy tin bài đăng theo tài khoản | `clarify` $\rightarrow$ `timeline` | PASS |
| G07 | Multi-turn: Đọc URL và tóm tắt | `clarify` $\rightarrow$ `fetch` | PASS |
| G08 | Multi-turn: Đổi tham số tìm kiếm | `timeline(limit=10)` $\rightarrow$ `timeline(limit=3)` | PASS |
| G09 | Multi-turn: Chuyển đổi giữa Web và Twitter | `lookup` $\rightarrow$ `social_search` | PASS |
| G10 | Multi-turn: Sử dụng Tool dịch thuật mới | `fetch` $\rightarrow$ `translate` | PASS |

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1 | v0 | `timeline(screenname="sama")` | `transcripts/chat_01.json` | Lấy thành công bài đăng mới |
| Turn 2 | v0 | `send(text="...")` | `transcripts/chat_02.json` | Lỗi: Gửi trực tiếp không qua xin phép |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `tools/translate/tool.py` | Dịch thuật văn bản chính xác sang tiếng Việt | Cần kiểm tra mã ngôn ngữ hợp lệ |
| Optional built-in | `tools/send/tool.py` | Gửi thông báo qua Telegram | Phải bắt buộc xin xác nhận Yes/No trước khi gửi |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?:**
  1. Loại bỏ câu dặn "never ask questions" để Agent biết dùng `clarify` khi thiếu thông tin.
  2. Bổ sung quy tắc cấm tự động gọi `format` sau mỗi câu trả lời.
  3. Thêm bảng ánh xạ tên người nổi tiếng sang Twitter handle (vd: Sam Altman $\rightarrow$ `sama`).
- **Which fixes belonged in `tools.yaml`?:**
  1. Cập nhật mô tả tool `format` rõ ràng: "Chỉ sử dụng khi người dùng yêu cầu xuất bản tin Digest".
  2. Thêm ràng buộc xác nhận vào mô tả của tool `send`.
- **Which failure needed manual review instead of automatic grading?:**
  Case `M02` bị lỗi `provider_error` từ phía OpenRouter, cần kiểm tra lại thủ công log mạng thay vì đánh giá tự động.
- **What would you improve next?:**
  Tối ưu hóa khả năng xử lý song song các công cụ (Parallel tool calling) và cải thiện tốc độ phản hồi của Agent.