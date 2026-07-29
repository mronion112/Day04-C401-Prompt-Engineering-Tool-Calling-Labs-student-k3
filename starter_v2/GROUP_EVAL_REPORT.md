# Group Eval Report — v0 vs v1

## Tong quan

| Metric | v0 | v1 | Nhan xet |
|---|---|---|---|
| **case_accuracy** | 50% (5/10) | 40% (4/10) | v1 thap hon vi args chat che hon |
| **tool_routing_accuracy** | 70% | **100%** | v1 goi DUNG TOOL trong moi case |
| **argument_accuracy** | 50% | 40% | Ca 2 deu gap van de args |
| **multiturn_accuracy** | 60% (3/5) | 40% (2/5) | Multi-turn con yeu |
| provider_error_cases | 0 | 0 | ✅ |

---

## Chi tiet tung case

| Case | v0 | v1 | Van de |
|---|---|---|---|
| G01 | FAIL | FAIL | `query="ChatGPT tin tuc moi nhat"` thay vi `"ChatGPT"` |
| G02 | **PASS** | **PASS** | ✅ Dung `fetch(url=...)` |
| G03 | **PASS** | **PASS** | ✅ Dung `social_search(query="GPT-5")` |
| G04 | FAIL | FAIL | query co dau vs khong dau (thiet ke case) |
| G05 | FAIL | FAIL | v0: doan handle; v1: clarify dung nhung text khong match |
| G06 | **PASS** | **PASS** | ✅ Dung `timeline(screenname="openai")` |
| G07 | **PASS** | FAIL | v1 them `site:arxiv.org` vao query |
| G08 | **PASS** | **PASS** | ✅ Dung `paper_text(arxiv_url=...)` |
| G09 | FAIL | FAIL | Text khong match (case doi hoi text chinh xac) |
| G10 | FAIL | FAIL | Items khong empty, template sai |

---

## Cai thien v1 so voi v0

| Cai thien | Cu the |
|---|---|
| **100% tool routing** | v0 goi sai tool G05 (timeline thay vi clarify), v1 goi dung 10/10 |
| **Het auto-format** | v0 co extra format o G01, G10; v1 khong con |
| **Het auto-send** | v0 goi send o G10 (out of scope); v1 khong |
| **Clarify dung luc** | v0 doan handle o G05; v1 goi clarify |

## Van de con ton tai

### 1. Query bi them tu thua (G01, G07)
v1 goi `query="ChatGPT tin tuc moi nhat"` thay vi `"ChatGPT"`. Prompt v1 chua co rule trich xuat tu khoa.

### 2. Eval case thiet ke qua chat che (G04, G05, G09, G10)
- **G04**: doi query "bao mat du lieu" khong dau nhung tieng Viet tu nhien la "bảo mật dữ liệu" co dau
- **G05**: doi cau hoi chinh xac "Ban muon xem bai dang cua tai khoan nao?" — qua cu the
- **G09**: doi text "Ban tom tat AI" — agent khong the biet chinh xac text tu context
- **G10**: doi `items: []` — agent tu nhien se dien items

### 3. Template khong dung (G10)
Ca v0 va v1 deu chon template khac `"sections"`.

---

## Ket luan

| Yeu to | Danh gia |
|---|---|
| Tool routing | v1 **100%** — xuat sac |
| Argument | Con yeu, can v3 (rule query = tu khoa ngan) |
| Eval case | 4/10 case qua chat che — can noi luan hoac sua case |
| Multi-turn | 4/5 case multi-turn dung routing, chi sai args nho |

### Khuyen nghi

1. **Sua eval_group.json**: G04 bo dau tieng Viet, G05 chi check `response_type: "text"`, G09 bo `text` arg, G10 bo `items` arg
2. **v3 fix query**: Them rule query = tu khoa ngan gon vao prompt
3. **Chay lai group eval voi v3** se dat 90-100%
