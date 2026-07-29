# Day 04 Lab — Phân công nhóm 5 người

## Timeline hôm nay

| Giờ | Mốc |
|---|---|
| 09:00–09:15 | Kickoff |
| 09:15–09:40 | Setup (venv, keys, preflight) |
| 09:40–10:15 | Baseline v0 + UI local |
| 10:15–10:50 | v1 + Tool mới |
| 10:50–11:05 | Nghỉ |
| 11:05–11:30 | Eval + v2 + Report A |
| 11:30–12:15 | Demo Showdown |
| 12:15–12:35 | v3 + Report B |
| 12:35–12:40 | Final gate (nộp) |

---

## 👤 Person 1 — Agent Core (Prompt + Tool Optimization)

**Trách nhiệm**: Sửa `system_prompt.md` và `tools.yaml`, chạy eval, ghi `version_log.csv`.

**Chỉ được sửa 2 file**: `artifacts/system_prompt.md` và `artifacts/tools.yaml`

### Việc cần làm

| # | Task | Khi nào |
|---|---|---|
| 1.1 | Đọc kỹ `system_prompt.md` + `tools.yaml` hiện tại, hiểu vì sao baseline fail | 09:15–09:40 |
| 1.2 | Chạy baseline: `python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json` | 09:40–09:55 |
| 1.3 | Đọc run JSON (thư mục `runs/`), xác định các case fail + `observed_mismatch` | 09:55–10:05 |
| 1.4 | Đặt hypothesis → sửa prompt/tools → chạy v1 | 10:15–10:40 |
| 1.5 | Ghi `version_log.csv` sau mỗi run | liên tục |
| 1.6 | Chạy v2 (sau khi có eval_group.json từ Person 3) | 11:05–11:20 |
| 1.7 | Chạy group eval: `python run_eval.py --provider openrouter --version v2 --suite group --eval-cases data/eval_group.json` | 11:05–11:20 |
| 1.8 | Chạy v3 sau demo | 12:15–12:30 |

### Lệnh cần dùng

```bash
cd starter_v0
source .venv/bin/activate

# Baseline
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json

# Các vòng sau
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json

# Group eval
python run_eval.py --provider openrouter --version v2 --suite group --eval-cases data/eval_group.json

# Phân tích run JSON
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv
```

### Output
- `runs/*.json` (v0, v1, v2, v3)
- `artifacts/version_log.csv` đầy đủ
- `artifacts/system_prompt.md` và `artifacts/tools.yaml` đã tối ưu

---

## 👤 Person 2 — Custom Tool

**Trách nhiệm**: Viết ít nhất 1 tool mới (đủ điều kiện bắt buộc), nhiều hơn để lấy bonus.

### Việc cần làm

| # | Task | Khi nào |
|---|---|---|
| 2.1 | Đọc contract: `tools/README.md`, `tools/_shared.py`, 1 tool mẫu (`tools/lookup/`) | 09:15–09:30 |
| 2.2 | Chọn ý tưởng tool mới, tạo folder `tools/<tên_tool>/` | 09:30–09:35 |
| 2.3 | Viết `TOOL.md` (frontmatter YAML + mô tả) | 09:35–09:45 |
| 2.4 | Viết `tool.py` (hàm implementation, dùng `_shared.err()` để bắt lỗi) | 09:45–10:15 |
| 2.5 | Đăng ký vào `tools/__init__.py` (import + thêm vào `TOOL_FUNCTIONS` dict) | 10:15–10:20 |
| 2.6 | Thêm declaration vào `artifacts/tools.yaml` | 10:20–10:25 |
| 2.7 | Smoke test tool mới | 10:25–10:30 |
| 2.8 | Báo Person 1 để đồng bộ `tools.yaml` | 10:30 |

### Contract tool mới cần tuân thủ

```
tools/<tên_tool>/
  TOOL.md    # frontmatter: name, track, kind, provider, requires_env, inputs, outputs, side_effect
  tool.py    # hàm def <tên_hàm>(...) -> dict[str, Any]
```

Frontmatter fields bắt buộc:
```yaml
name: tên_tool
track: core | bonus
kind: live_api | local_formatter | local_knowledge | action | control
provider: tên provider (nếu có)
requires_env: [DANH_SÁCH_ENV_VAR]
inputs: [tên_các_arg]
outputs: [tên_các_field]
side_effect: false | true
```

### Ý tưởng tool mới (gợi ý)

| Ý tưởng | Mô tả |
|---|---|
| `translate` | Dịch văn bản (dùng free API hoặc local lib) |
| `sentiment` | Phân tích sentiment của text |
| `weather` | Lấy thời tiết hiện tại theo thành phố |
| `stock` | Lấy giá cổ phiếu |
| `calculator` | Tính toán biểu thức toán học |
| `summarize` | Tóm tắt văn bản dài bằng model local |
| `github_trending` | Lấy trending repos trên GitHub |
| `news_headlines` | Lấy headline từ news API |
| `hashtag_trending` | Lấy trending hashtags trên X/Twitter |
| `screenshot_url` | Chụp ảnh màn hình một URL |

### Output
- `tools/<tên_tool>/TOOL.md`
- `tools/<tên_tool>/tool.py`
- Đã import vào `tools/__init__.py`
- Đã thêm vào `artifacts/tools.yaml`

---

## 👤 Person 3 — Team Eval Cases

**Trách nhiệm**: Viết đúng 10 eval case (5 single-turn + 5 multi-turn) vào `data/eval_group.json`.

### Schema mỗi case

```json
{
  "id": "GXX_tên_case",
  "phase": "B",
  "query": "câu hỏi của user",           // single-turn
  "failure_type": "wrong_tool | wrong_arg_value | wrong_boundary | unnecessary_tool | out_of_scope | missing_info",
  "expect": {
    "tool_calls": [
      {"name": "tên_tool", "args": {"arg1": "value1"}}
    ]
  },
  "metadata": {"what_it_tests": "mô tả ngắn"}
}
```

Multi-turn dùng `turns` thay `query`:
```json
{
  "turns": [
    {"role": "user", "content": "turn 1"},
    {"role": "user", "content": "turn 2"},
    {"role": "user", "content": "turn cuối cùng được chấm"}
  ],
  "expect": { ... }
}
```

### Việc cần làm

| # | Task | Khi nào |
|---|---|---|
| 3.1 | Đọc mẫu: `samples/eval_group.schema.example.json` + `data/eval_base.json` | 09:15–09:25 |
| 3.2 | Phân bổ 6 `failure_type` vào 10 case (mỗi loại xuất hiện ít nhất 1 lần) | 09:25–09:30 |
| 3.3 | Viết 5 single-turn cases | 09:30–09:55 |
| 3.4 | Viết 5 multi-turn cases | 09:55–10:15 |
| 3.5 | Validate: đủ fields, đúng schema, tool tồn tại trong `tools.yaml` | 10:15–10:25 |
| 3.6 | Báo Person 1 để chạy group eval | 10:25 |

### Yêu cầu phân bổ failure_type

| failure_type | Số case tối thiểu |
|---|---|
| `wrong_tool` | 2 |
| `wrong_arg_value` | 2 |
| `wrong_boundary` | 2 |
| `unnecessary_tool` | 1 |
| `out_of_scope` | 2 |
| `missing_info` | 1 |

### Lưu ý
- Multi-turn: phần tử cuối của `turns` là turn được chấm, các turn trước là context
- Tất cả `id` phải unique
- Không trùng với case trong `eval_base.json`

### Output
- `data/eval_group.json` hoàn chỉnh 10 case

---

## 👤 Person 4 — UI (Streamlit)

**Trách nhiệm**: Dựng `app.py` với Streamlit, chạy được local.

### Yêu cầu UI

- Request/response cuối cùng
- Trace của từng tool: tên, args, round/status, result/error
- Transcript/run/artifact version
- Demo được cùng scenario qua nhiều version (v0 → v3)
- Tái dùng `run_model_tool_loop` từ `chat.py`

### Việc cần làm

| # | Task | Khi nào |
|---|---|---|
| 4.1 | `pip install "streamlit>=1.30.0"` → thêm vào `requirements.txt` | 09:15–09:20 |
| 4.2 | Đọc `chat.py`, hiểu `run_model_tool_loop`, cấu trúc transcript | 09:20–09:30 |
| 4.3 | Tạo `app.py` cơ bản: input box, gọi agent, hiển thị response | 09:30–09:50 |
| 4.4 | Hiển thị trace từng round: tool name, args, result/error | 09:50–10:10 |
| 4.5 | Cho phép chọn version (v0/v1/v2/v3) để so sánh | 10:10–10:25 |
| 4.6 | Lưu transcript mỗi session | 10:25–10:35 |
| 4.7 | Test: `streamlit run app.py` → mở `http://localhost:8501` | 10:35–10:45 |
| 4.8 | Sửa lỗi, hoàn thiện | 10:45–10:50 |

### Cấu trúc app.py gợi ý

```python
import streamlit as st
from pathlib import Path
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, json_text

ROOT = Path(__file__).parent
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", layout="wide")
st.title("Research Agent")

# Sidebar: chọn version, provider, model
version = st.sidebar.selectbox("Version", ["v0", "v1", "v2", "v3"])
provider_name = st.sidebar.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"])

# Load prompt + tools theo version
prompt_path = ROOT / "artifacts" / "system_prompt.md"
tools_path = ROOT / "artifacts" / "tools.yaml"
system_prompt = prompt_path.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)
provider = make_provider(provider_name)

# Chat input
user_input = st.chat_input("Your request...")
if user_input:
    # Chạy agent loop
    result = run_model_tool_loop(
        provider=provider,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}],
        tools=openai_tools,
        model=None,
        max_tool_rounds=4,
    )
    
    # Hiển thị response
    st.chat_message("assistant").write(result["assistant_text"])
    
    # Hiển thị tool trace
    with st.expander("Tool Trace", expanded=True):
        for round_data in result["rounds"]:
            st.write(f"### Round {round_data['round']}")
            for call in round_data["tool_calls"]:
                st.write(f"- **{call['name']}**")
                st.json(call["args"])
            for event in round_data.get("tool_results", []):
                if event.get("result", {}).get("error"):
                    st.error(event["result"])
                else:
                    st.success(event["tool"])
```

### Output
- `app.py` chạy được `streamlit run app.py`
- URL: `http://localhost:8501`

---

## 👤 Person 5 — Report + Demo Scenarios + Tích hợp

**Trách nhiệm**: Viết `REPORT.md`, chuẩn bị demo, kiểm tra nộp bài.

### Việc cần làm

| # | Task | Khi nào |
|---|---|---|
| 5.1 | Viết draft Phần A: mô tả agent, bảng tool, 3–5 câu hỏi mẫu | 09:15–09:35 |
| 5.2 | Cùng Person 1 đọc v0 run JSON, hiểu failure pattern để ghi vào Report B | 09:40–10:00 |
| 5.3 | Thiết kế 3–5 kịch bản demo cụ thể (scenario + expected tool trace + version improvement) | 10:00–10:30 |
| 5.4 | Tập hợp evidence từ mọi người, điền dần Report | 10:30–10:50 |
| 5.5 | Hoàn thiện Phần A trước 11:30 (bắt buộc) | 11:05–11:25 |
| 5.6 | Rehearse demo trên UI của Person 4 | 11:25–11:30 |
| 5.7 | Ghi chú feedback từ showdown → áp dụng vào v3 + Report B | 11:30–12:15 |
| 5.8 | Hoàn thiện Phần B (bảng v0–v3, failure analysis, eval cases, live chat, reflection) | 12:15–12:35 |
| 5.9 | Final gate: kiểm tra tất cả file nộp | 12:35–12:40 |

### Kịch bản demo mẫu

| Scenario | Tool trace mong đợi | Câu chuyện version |
|---|---|---|
| 1. Tìm tweet mới nhất của Sam Altman | `timeline(screenname="sama")` | v0 gọi sai tool → v2 gọi đúng |
| 2. Tin AI hôm nay + tweet về AI | `lookup` + `social_search` (2 tool songsong) | v0 chỉ gọi 1 tool → v1 gọi đủ 2 |
| 3. Yêu cầu gửi Telegram nhưng chưa confirm | `clarify(response_type="yes_no")` | v0 tự gửi luôn → v2 hỏi confirm |
| 4. Thiếu handle → hỏi lại → được cung cấp → gọi đúng | Multi-turn: `clarify` → `timeline` | v0 đoán bừa → v2 hỏi lại |
| 5. Tool mới của nhóm (ví dụ: dịch bài báo) | Tool mới của Person 2 | Demo tool mới hoạt động |

### Checklist nộp bài

- [ ] `artifacts/system_prompt.md`
- [ ] `artifacts/tools.yaml`
- [ ] `artifacts/version_log.csv` (v0 → v3)
- [ ] `artifacts/REPORT.md`
- [ ] `data/eval_group.json` (10 case)
- [ ] `runs/*.json` (v0, v1, v2, v3)
- [ ] `transcripts/*.transcript.json`
- [ ] `app.py`
- [ ] Tool mới (`tools/<tên>/TOOL.md` + `tool.py`)
- [ ] Không có `.env`, keys, `.venv/`, cache

### Output
- `artifacts/REPORT.md` hoàn chỉnh
- Demo scenarios đã rehearse
- Tất cả file nộp đã kiểm tra

---

## Dependency graph

```
Setup ──────┬── Person 1 (prompt/tools) ──── evidence ──┬── Person 5 (report)
            │                                           │
            ├── Person 2 (tool mới) ── sync ── Person 1 │
            │                                           │
            ├── Person 3 (eval cases) ──── evidence ────┤
            │                                           │
            ├── Person 4 (UI) ─────────── nền demo ─────┘
            │
            └── Person 5 (report draft, demo script)
```

## Điểm đồng bộ

| Khi nào | Ai → Ai | Nội dung |
|---|---|---|
| Person 2 code xong tool | Person 2 → Person 1 | Tên tool + args để Person 1 thêm vào `tools.yaml` |
| Person 1 chạy eval xong mỗi version | Person 1 → Person 5 | Gửi run JSON + các metric |
| Person 3 viết xong eval_group.json | Person 3 → Person 1 | File để Person 1 chạy group eval |
| Person 4 UI chạy được | Person 4 → Person 5 | Test demo scenario |
| Person 5 cần evidence cho Report | Person 5 ← Tất cả | Run JSON, transcript, tool mới |
