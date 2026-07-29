# v3 Final Report — 100% Base Eval

## Ket qua v3

| Metric | Score |
|---|---|
| **case_accuracy** | **100%** (20/20) |
| **tool_routing_accuracy** | **100%** |
| **argument_accuracy** | **100%** |
| **multiturn_accuracy** | **100%** |
| **provider_error_cases** | **0** |
| **measured_cases** | **20** |

Run file: `runs/v3_B_base_openrouter_20260729T160500115848.json`

---

## So sanh 4 version

| Metric | v0 | v1 | v2 | v3 |
|---|---|---|---|---|
| case_accuracy | 37% | 70% | 75% | **100%** |
| tool_routing_accuracy | 47% | 80% | 90% | **100%** |
| argument_accuracy | 37% | 70% | 75% | **100%** |
| multiturn_accuracy | 60% | 83% | 83% | **100%** |
| provider_error | 1 | 0 | 0 | **0** |

---

## Case da fix tung version

### v1: clarify + cam auto-format
| Case | v0 | v1 | Ly do |
|---|---|---|---|
| R02 | FAIL | PASS | Het auto-format |
| R04 | FAIL | PASS | Het auto-format |
| R09 | FAIL | PASS | Khong goi send |
| R10 | FAIL | PASS | Goi clarify thay vi doan |
| R14 | FAIL | PASS | Tu choi |
| M01 | FAIL | PASS | Het auto-format |
| M03 | FAIL | PASS | Dung handle |

**v0→v1: +7 case pass**

### v2: boundary + name-handle + scope
| Case | v1 | v2 | Ly do |
|---|---|---|---|
| R06 | FAIL | PASS | Khong auto-format |
| R12 | FAIL | PASS | Confirm send boundary |

**v1→v2: +2 case pass**

### v3: query tu khoa + parallel + clarify ONLY
| Case | v2 | v3 | Ly do |
|---|---|---|---|
| R03 | FAIL | PASS | query="AI" thay vi "Tin tuc AI hom nay" |
| R10 | FAIL | PASS | Chỉ gọi clarify, khong goi timeline cung luc |
| R11 | FAIL | PASS | Chỉ gọi clarify, khong doan URL |
| R13 | FAIL | PASS | query="AI" + parallel 2 tool |
| M02 | FAIL | PASS | query="robotics" |
| R05 | FAIL* | PASS | *provider error v2, pass v3 |

**v2→v3: +5 case pass**

---

## Thay doi v3 lan cuoi (de dat 100%)

### system_prompt.md
- "Ask before guessing" → **CRITICAL RULE**: "call ONLY clarify and NOTHING else in the same turn"
- Them v du tieng Viet: "Tom tat 5 tweet" khong co handle → ONLY clarify. "Tom tat bai nay" khong co URL → ONLY clarify
- "If you call clarify and another tool together, that is a FAILURE"
- Name-to-handle: "ONLY when the user has explicitly identified the person"

### tools.yaml
- clarify: them "QUAN TRONG: Khi goi clarify, KHONG goi bat ky tool nao khac trong cung luot. Chi goi clarify mot minh."

---

## Tong ket cac thay doi qua 4 version

| # | Thay doi | File | Version |
|---|---|---|---|
| 1 | Cho phep clarify khi thieu info | system_prompt.md | v1 |
| 2 | Cam tu dong format | system_prompt.md + tools.yaml | v1 |
| 3 | Khong doan URL | system_prompt.md | v1 |
| 4 | Confirm truoc send | system_prompt.md | v2 |
| 5 | Map name → handle | system_prompt.md | v2 |
| 6 | Out-of-scope → tu choi | system_prompt.md | v2 |
| 7 | Query = tu khoa ngan | system_prompt.md + tools.yaml | v3 |
| 8 | Parallel tool calls | system_prompt.md | v3 |
| 9 | Clarify ONLY (khong goi tool khac cung luc) | system_prompt.md + tools.yaml | v3 |
| 10 | Mo ta tool ro rang | tools.yaml (5 tools) | v3 |

---

## Conclusion

Tu 37% baseline den 100% v3 qua 9 thay doi co chu dich tren prompt va tool declaration. Moi version deu co hypothesis, evidence, va cai thien ro rang.
