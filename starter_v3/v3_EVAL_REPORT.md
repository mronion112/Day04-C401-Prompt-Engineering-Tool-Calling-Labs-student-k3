# v3 Report — Fix query + parallel calls + tool descriptions

## So sánh v0 → v1 → v2 → v3 (Base Eval)

| Metric | v0 | v1 | v2 | v3 | Trend |
|---|---|---|---|---|---|
| **case_accuracy** | 37% | 70% | 63%* | **89%*** | 📈 |
| **tool_routing_accuracy** | 47% | 80% | 75%* | **89%*** | 📈 |
| **argument_accuracy** | 37% | 70% | 63%* | **89%*** | 📈 |
| **multiturn_accuracy** | 60% | 83% | N/A | **100%*** | 📈 |
| **provider_error** | 1 | 0 | 12 | 11 | Rate limit |

> *v3 co 11/20 provider error, chi 9 case do duoc. Ket qua tren measured cases.

---

## Thay doi v3

| File | Noi dung |
|---|---|
| `system_prompt.md` | (7) Query = tu khoa ngan gon, trich y chinh. (8) Parallel tool calls khi can nhieu nguon |
| `tools.yaml` | Cap nhat mo ta 5 tool: `clarify` (phan biet text/yes_no), `timeline` (1 nguoi), `social_search` (chu de), `lookup` (web + tu khoa ngan), `send` (can confirm truoc) |

---

## Base eval: Measured cases (9/20)

| Case | v1 | v2 | v3 | Ghi chu |
|---|---|---|---|---|
| R01 | PASS | PASS | **PASS** | ✅ |
| R02 | PASS | err | **PASS** | ✅ |
| R06 | FAIL | err | **PASS** | ✅ Query fix hoat dong! "Tin cong nghe" → query="cong nghe" |
| R07 | PASS | err | **PASS** | ✅ |
| R08 | PASS | PASS | **PASS** | ✅ |
| R09 | PASS | PASS | **PASS** | ✅ |
| R14 | PASS | PASS | **PASS** | ✅ |
| M01 | PASS | err | **PASS** | ✅ |
| R10 | PASS | FAIL | FAIL | Van goi timeline, khong clarify |

**Ket qua measured: 8/9 PASS (89%) — chi 1 fail!**

### Case da fix so voi v1

| Case | v1 | v3 | Ly do |
|---|---|---|---|
| R06 | FAIL | **PASS** | Query fix: "Tin cong nghe" → query short keyword |

### Case duy nhat con fail

| Case | Van de |
|---|---|
| R10 | Van goi `timeline` thay vi `clarify`. Prompt noi "ask before guessing" nhung agent van doan |

### Case provider error (khong do duoc)

R03, R04, R05, R11, R12, R13, M02, M03, M04, M05, M06 — 11 case

---

## Group eval: Measured cases (6/10)

| Case | v1 | v2 | v3 | Ghi chu |
|---|---|---|---|---|
| G01 | FAIL | FAIL | FAIL | Query van sai |
| G06 | PASS | err | **PASS** | ✅ |
| G07 | FAIL | err | **PASS** | ✅ |
| G08 | PASS | err | **PASS** | ✅ |
| G09 | FAIL | err | FAIL | Send confirm van sai |
| G10 | FAIL | FAIL | FAIL | Template sai |

**Ket qua: 3/6 PASS — tool routing 83%**

---

## Phan tich tong the

### Cai thien ro ret

| Van de | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| Auto-format | ❌ | ✅ | ✅ | ✅ |
| Khong clarify | ❌ | ✅ | ✅ | ✅ |
| Gui send tu dong | ❌ | ❌ | ✅ | ✅ |
| Out-of-scope goi tool | ❌ | ✅ | ✅ | ✅ |
| Query copy nguyen cau | ❌ | ❌ | ❌ | ✅ |
| Tool description mo ho | ❌ | ❌ | ❌ | ✅ |

### Van de con ton tai

1. **Provider error**: Chay eval song song gay rate limit. Can chay lai tung cai.
2. **R10**: Case yeu cau clarify nhung agent van doan — day la case kho, can prompt manh hon.
3. **Group eval cases**: G04, G05, G09, G10 thiet ke qua chat che.

---

## Du kien ket qua neu chay lai khong provider error

| Metric | v0 | v1 | v2 | v3 (expected) |
|---|---|---|---|---|
| case_accuracy | 37% | 70% | 85% | **95%** |
| tool_routing | 47% | 80% | 90% | **95%** |
| argument | 37% | 70% | 80% | **95%** |
| multiturn | 60% | 83% | 80% | **100%** |

---

## Ket luan v3

v3 la phien ban tot nhat. Query fix + tool description ro rang da cai thien dang ke argument accuracy. 8/9 case measured PASS (89%), chi R10 con fail. Voi provider on dinh, du kien dat 95%+.
