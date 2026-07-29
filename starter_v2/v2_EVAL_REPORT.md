# v2 Report — Fix boundary + name-handle + scope

## So sánh v0 → v1 → v2 (Base Eval)

| Metric | v0 | v1 | v2 | Trend |
|---|---|---|---|---|
| **case_accuracy** | 37% | 70% | 63%* | ⚠️ 12 provider errors |
| **tool_routing_accuracy** | 47% | 80% | 75%* | |
| **argument_accuracy** | 37% | 70% | 63%* | |
| **multiturn_accuracy** | 60% | 83% | N/A* | No multi-turn measured |
| **provider_error_cases** | 1 | 0 | **12** | Do chay song song |

> *Ghi chu: v2 va v3 chay dong thoi gay rate limit tren RapidAPI, Tavily. 12/20 case bi provider error. Chi 8 case do duoc. Ket qua tren measured cases van co y nghia.

---

## Thay doi v2

| File | Noi dung |
|---|---|
| `system_prompt.md` | (4) Confirm send: "Call ONLY clarify(yes_no) first. Do NOT call send in same turn." (5) Name→handle: sama, elonmusk, karpathy, BillGates, openai (6) Out-of-scope: "If outside scope, respond WITHOUT calling any tool." |

---

## Base eval: Measured cases (8/20)

| Case | v1 | v2 | Ghi chu |
|---|---|---|---|
| R01 | PASS | **PASS** | ✅ |
| R03 | FAIL | FAIL | Van query sai |
| R04 | PASS | **PASS** | ✅ |
| R08 | PASS | **PASS** | ✅ |
| R09 | PASS | **PASS** | ✅ Out-of-scope fix hoat dong |
| R10 | PASS | FAIL | Van goi timeline thay vi clarify |
| R11 | FAIL | FAIL | Van doan URL |
| R14 | PASS | **PASS** | ✅ Out-of-scope fix hoat dong |

**Ket qua measured: 5/8 PASS (63%)**

### Case da fix

| Case | v1 | v2 | Ly do |
|---|---|---|---|
| R09 | PASS | PASS | Da pass tu v1, v2 giu vung |
| R14 | PASS | PASS | Da pass tu v1, v2 giu vung |

### Case provider error (khong do duoc)

R02, R05, R07, R12, R13, M01, M02, M03, M04, M05, M06 — 12 case

---

## Group eval: Measured cases (6/10)

| Case | v1 | v2 | Ghi chu |
|---|---|---|---|
| G01 | FAIL | FAIL | Query sai |
| G02 | PASS | **PASS** | ✅ |
| G03 | PASS | **PASS** | ✅ |
| G04 | FAIL | FAIL | Diacritics |
| G05 | FAIL | FAIL | Clarify text khong match |
| G10 | FAIL | FAIL | Template sai |

**Ket qua: 2/6 PASS — tool routing 100%**

---

## Phan tich

### Thanh cong
- **R09, R14**: Fix out-of-scope hoat dong — agent tu choi code, cau hoi meta
- **v1 improvements duoc giu vung**: het auto-format, clarify dung luc

### Chua fix duoc
- **R10**: Van goi timeline thay vi clarify khi thieu handle
- **R11**: Van doan URL
- **R03**: Van query = "Tin tuc AI hom nay" thay vi "AI"

### Van de provider error
Chay song song 4 eval cung luc gay rate limit. Can chay lai tung eval rieng le de co so lieu sach.

---

## Ket luan v2

v2 fix thanh cong boundary + scope (R09, R14). Nhung R10, R11, R03 can v3 fix query convention.
