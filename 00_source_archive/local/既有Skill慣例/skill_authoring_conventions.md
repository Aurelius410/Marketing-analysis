---
title: 既有自製 Skill 撰寫慣例萃取（包子風格規格書）
purpose: 供新建「行銷分析 Skill」沿用同一套撰寫風格、檔案粒度、程式風格與互動規範
capture_date: 2026-07-25
analyst: 包子（andychen050229@gmail.com，台大國企所）
language: 繁體中文
environment:
  os: Windows 11 Home 10.0.26200
  python: 3.14.1 (in PATH)
  r: E:\R\R-4.5.2
  bash: Git Bash (POSIX)
  powershell: Windows PowerShell 5.1（無 && 、無 ??）
coverage:
  - SKILL.md 的 frontmatter 寫法與段落結構（兩個 skill 對照）
  - CLAUDE.md 的定位與內容邊界
  - references/ 的切分邏輯與檔案粒度（6 檔全覆蓋）
  - scripts/ 的程式風格：CLI 介面、docstring、錯誤處理、編碼處理、輸出格式、退出碼（5 檔 + 1 個一次性腳本）
  - templates/ 的範本粒度
  - AskUserQuestion 卡點確認的觸發時機
  - 與使用者互動的語氣規範
  - 路徑與命名慣例、Windows／中文路徑處理
  - 對話紀錄（工作日誌）檔的格式
  - scripts 對新行銷分析 Skill 的可重用性評估
sources:
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\SKILL.md
    bytes: 10768
    lines: 227
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\CLAUDE.md
    bytes: 1345
    lines: 29
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\HW4_批改對話紀錄.md
    bytes: 5988
    lines: 141
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\course_context.md
    bytes: 5521
    lines: 116
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\folder_structure.md
    bytes: 7485
    lines: 191
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\grading_policy.md
    bytes: 6192
    lines: 169
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\text_extraction.md
    bytes: 8618
    lines: 231
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\grade_recording.md
    bytes: 6015
    lines: 200
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\attendance_grading.md
    bytes: 3843
    lines: 117
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\references\大數據行銷作業批改.zip
    bytes: 19987
    note: 內含 references 6 檔的扁平打包版（folder_structure / grade_recording / grading_policy / text_extraction / attendance_grading / course_context），內容與 references/ 下同名檔一致
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\scripts\extract_xlsx_content.py
    bytes: 4457
    lines: 141
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\scripts\extract_pdf_content.py
    bytes: 2375
    lines: 89
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\scripts\parse_filename.py
    bytes: 2288
    lines: 86
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\scripts\setup_new_hw.py
    bytes: 2171
    lines: 64
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\scripts\validate_folder_structure.py
    bytes: 5019
    lines: 164
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\templates\appeal_reply_examples.md
    bytes: 2503
    lines: 31
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\templates\grade_csv_template.csv
    bytes: 114
    lines: 5
  - path: C:\Users\User\Desktop\大數據行銷\大數據行銷作業批改\local_19058eca-8dde-4271-b3b4-7ff857b5311e\outputs\hw7_work\auto_grade.py
    bytes: 11316
    lines: 325
  - path: C:\Users\User\Desktop\大數據\lecture-to-notion.skill
    bytes: 4418
    note: 實為 ZIP，內含單一檔 lecture-to-notion/SKILL.md（8393 bytes, 187 lines）
---

# 既有自製 Skill 撰寫慣例（包子風格規格書）

> **本檔的閱讀約定**
> 標題含 **【原文】** 的段落 = 直接來自使用者既有檔案的內容（逐字或高保真摘錄），是「教材」。
> 標題含 **【評註】** 的段落 = 本次萃取者的觀察、推論、風險提示與建議，**不是**使用者原本寫下的規範。
> 兩者不混排。若某節同時需要兩者，會拆成兩個相鄰子節。

---

## 0. 材料全景與兩個 Skill 的定位差異

### 0.1 【原文】既有兩套 Skill 的實體形態

| Skill | 實體形態 | 檔案數 | 有 references/ | 有 scripts/ | 有 templates/ | 有 CLAUDE.md |
|-------|----------|--------|----------------|-------------|---------------|--------------|
| 大數據行銷作業批改 | 展開的資料夾（放在工作根目錄底下） | SKILL.md + CLAUDE.md + 6 references + 5 scripts + 2 templates | 是（6 檔） | 是（5 檔） | 是（2 檔） | 是 |
| lecture-to-notion | 單一 `.skill` 檔（ZIP，內含 `lecture-to-notion/SKILL.md`） | 只有 1 個 SKILL.md | 否 | 否 | 否 | 否 |

`大數據行銷作業批改/references/大數據行銷作業批改.zip` 顯示使用者也會把 references 打包（扁平、無資料夾層），推測是為了搬移／上傳到 Skill 平台。

### 0.2 【評註】兩種形態的分工推論

- **單檔 `.skill`（lecture-to-notion）= 「純方法論型」**：任務是「輸入素材 → 產出一份文件」，沒有跨次累積的狀態、沒有固定資料夾、沒有需要記住的歷史案例。整套規範塞得進一個 SKILL.md（187 行）就夠。
- **展開資料夾（作業批改）= 「長期營運型」**：每週重複跑同一條流程、有固定工作根目錄、有跨次累積的踩雷經驗與人名案例、需要可執行腳本。所以拆出 references/scripts/templates。
- **新的「行銷分析 Skill」屬於後者**（有資料集、有反覆執行的分析流程、有專案目錄），應採「展開資料夾 + SKILL.md + CLAUDE.md + references/ + scripts/ + templates/」的完整形態。

---

## 1. SKILL.md 的 frontmatter 寫法

### 1.1 【原文】作業批改 SKILL.md 的 frontmatter（逐字）

```yaml
---
name: 大數據行銷作業批改
description: 「大數據行銷」（NTU IB5082）課程的完整批改工具包，由助教包子（andychen050229@gmail.com）使用。負責每週作業（HW1–HW4 及後續）的批改、漏掃補強、成績登錄、Cool 匯入檔產出，以及實體出席成績處理。觸發條件：使用者提到批改、評分、HW、作業、登分、評分標準、Cool 匯入、成績登錄、實體簽到、出席成績、補繳、遲交、申訴重評，或上傳 .xlsx/.pdf/.docx 形式的學生作業時。
---
```

### 1.2 【原文】lecture-to-notion SKILL.md 的 frontmatter（逐字）

```yaml
---
name: lecture-to-notion
description: |
  將教授的 PDF 講義與個人 Markdown 筆記，轉化為可直接匯入 Notion 的完整教學講義。輸出為 Notion 相容的 Markdown，數學式使用 KaTeX 格式。每個概念都包含正式定義、詳細解釋、白話說明三層結構，並補充公式推導、範例計算、方法論詳解與比較表。
  MANDATORY TRIGGERS: 任何涉及「把講義/投影片/上課內容整理成筆記」、「做 Notion 講義」、「整理 PDF 課程內容」、「幫我做完整筆記」、「把教授的講義變成可以讀的東西」的請求都應觸發此 skill。即使使用者沒有明確說「Notion」，只要是把課程素材整理成結構化講義的需求，都適用。
---
```

### 1.3 【原文】兩者可歸納出的 frontmatter 硬性寫法

- 只有 `name` 與 `description` 兩個 key，**沒有** `version`、`author`、`tags`、`license` 等欄位。
- `name`：作業批改用**中文名**（`大數據行銷作業批改`）；lecture-to-notion 用**英文 kebab-case**（`lecture-to-notion`）。兩種都存在，取決於 skill 是「中文業務流程」還是「英文工具型」。
- `description` 一律**繁體中文長句**，不是一行標語。結構固定為三段：
  1. **它是什麼**（一句定位，含課程代碼／輸出格式等硬事實）
  2. **它負責哪些工作**（列舉具體任務，用「、」串接）
  3. **觸發條件**（明文寫出 `觸發條件：` 或 `MANDATORY TRIGGERS:`，接一串使用者可能說出口的關鍵字／句子）
- 觸發關鍵字寫的是**使用者的口語**，不是技術術語：「改 HW？」「登分」「幫我做完整筆記」「把教授的講義變成可以讀的東西」。
- 觸發條件會包含**檔案型別觸發**（「或上傳 .xlsx/.pdf/.docx 形式的學生作業時」）。
- lecture-to-notion 額外用 `|` block scalar + 全大寫 `MANDATORY TRIGGERS:` 加強觸發力度，並補一句**兜底條款**：「即使使用者沒有明確說『Notion』，只要是……都適用。」

### 1.4 【評註】新 Skill 的 frontmatter 建議

沿用「定位 + 任務列舉 + 觸發條件」三段式，並把 lecture-to-notion 的兩個強化技巧都用上（block scalar、兜底條款）。`name` 建議用中文（因為新 skill 是中文業務流程，與作業批改同類）。觸發字串要包含包子真的會說的話（例：「跑一下 RFM」「這份資料能看出什麼」「幫我做客群分析」「做個儀表板」），以及檔案型別觸發（`.csv`／`.xlsx`／`.sav`／`.R`）。

---

## 2. SKILL.md 的段落結構

### 2.1 【原文】作業批改 SKILL.md 的完整段落骨架（依原順序）

```
---（frontmatter）---
# 大數據行銷作業批改 Skill
> NTU IB5082 大數據行銷課程專屬批改工具包       ← blockquote 一行副標
（一段散文式定位說明，說「這 skill 是給誰用的、它自己就是什麼」）

## 何時載入這個 Skill                            ← bullet list，用包子的口語
## 內建 Skill 檔案地圖                            ← ``` 圍籬內的 ASCII 樹狀圖 + 每行 ← 註解
## 課程基本資料（速查）                           ← markdown 兩欄表（項目 | 值）
## 工作根目錄的標準結構                           ← ASCII 樹狀圖 + ← 註解
## 批改作業的七步流程                             ← 先列「開工前務必先讀」5 個 references
  ### Step 1 — 讀評分標準                        ← 每步一個 h3，標題格式「Step N — 動詞短語」
  ### Step 2 — 盤點繳交資料夾
  ### Step 3 — 逐份提取內容
  ### Step 4 — 自動標分
  ### Step 5 — 漏掃補強（**最關鍵**）
  ### Step 6 — 產出 `HW{N}_成績.csv`
  ### Step 7 — 同步寫入 Cool 匯入用檔案
## 給分基調（一句話）                             ← 刻意壓成一句的核心原則
## 與包子互動的習慣                               ← 語氣規範 bullet list
## 工作流程摘要圖                                 ← ASCII 流程圖（含分支）
## 不同情境的入口指引                             ← 兩欄表（包子說的 | 你該做的）
```

### 2.2 【原文】lecture-to-notion SKILL.md 的完整段落骨架（依原順序）

```
---（frontmatter）---
# Lecture-to-Notion：課程講義生成器
## 你在做什麼                                     ← 角色設定（第二人稱「你是一個資深補教團隊的名師」）
## 輸入素材                                       ← 編號列表，說明各素材的權威層級
## 讀取素材的流程
  ### 第一步：完整讀取所有檔案
  ### 第二步：建立知識地圖
## 輸出格式規範
  ### Notion Markdown 格式要求
  ### 絕對不要出現的東西                          ← 負面清單
## 三層結構寫作法                                 ← 核心方法論
  ### 第一層：正式定義（Formal Definition）
  ### 第二層：詳細解釋（Detailed Explanation）
  ### 第三層：白話說明（Colloquial Explanation）
## 白話說明的口吻調整                             ← 依科目分流的語氣表
## 必備元素清單
  ### 1. 公式推導 / 2. 範例計算 / 3. 方法論補充 / 4. 比較表 / 5. 章節總結
## 工作流程
  ### 大型講義的分段策略
  ### Agent 撰寫時的 prompt 結構
  ### 最終輸出
## 品質檢查清單                                   ← - [ ] 勾選框
```

### 2.3 【原文】兩個 SKILL.md 共有的寫法特徵

1. **h1 只有一個**，格式為「名稱 + Skill」或「名稱：一句話定位」。
2. h1 之後**立刻**一段定位散文（不是條列），說明「這 skill 是什麼、給誰、為什麼存在」。作業批改用 `>` blockquote 放一行副標。
3. **每個 h2 都是短的中文名詞短語或問句**：「何時載入這個 Skill」、「你在做什麼」、「給分基調（一句話）」、「不同情境的入口指引」。不用英文標題。
4. **流程步驟一定有編號與破折號標題**：`### Step N — 動詞短語` 或 `### 第一步：動詞短語`。
5. **大量使用 ASCII 圖**：檔案地圖、目錄結構、決策樹、流程圖，全部包在 ``` 圍籬內，且用 `←` 在行尾加註解。
6. **大量使用 markdown 兩欄／三欄表**做「輸入 → 動作」對應。
7. **關鍵句用 `**粗體**` 且常帶語氣詞**：「**必讀**」、「**最關鍵**」、「**這是錯的**」、「**對不上一定要找出原因**」、「**先驗證再說**」。
8. **收尾一定有「入口指引表」或「品質檢查清單」**——讓 agent 知道「使用者說 X 時我該做 Y」或「交件前要自己過一遍什麼」。
9. **負面清單獨立成節**：lecture-to-notion 的「絕對不要出現的東西」；作業批改散在 references 中（「不要用 Homework_1、HW01、Hw3」、「不要自創縮寫或英文化」）。
10. 每個 h2 內部**都會回指 references**：「詳見 `references/grading_policy.md`」、「完整命名規則……見 `references/folder_structure.md`」。SKILL.md 自己只放摘要與流程，細節一律外推。

### 2.4 【原文】SKILL.md 內的「開工前必讀」機制（逐字）

```
開工前 **務必**先讀：
1. `references/course_context.md` — 確認當週主題與評分結構
2. `references/folder_structure.md` — 確認檔案位置
3. `references/grading_policy.md` — 確認寬鬆度與等第規則
4. `references/text_extraction.md` — 確認漏掃處理（**必讀**）
5. `references/grade_recording.md` — 確認輸出格式
```

格式為「編號 + 反引號路徑 + ` — ` + 一句話說明讀它是為了確認什麼」。同一份清單在 CLAUDE.md 以 7 項的形式重複出現（多了 attendance_grading.md 與 SKILL.md 自身）。

### 2.5 【原文】完整的檔案地圖寫法（逐字，含 ← 註解）

```
大數據行銷作業批改/
├── SKILL.md                         ← 本檔（總覽與七步流程）
├── CLAUDE.md                        ← 工作目錄速查（被 Cowork 自動載入）
│
├── references/                      ← 詳細參考文件，開工前必讀
│   ├── course_context.md            ← 課程資訊（IB5082、週次主題、Cool）
│   ├── folder_structure.md          ← 資料夾命名與位置規範
│   ├── grading_policy.md            ← 寬鬆給分、等第判定、遲交補繳
│   ├── text_extraction.md           ← Excel/PDF/DOCX 漏掃處理（**必讀**）
│   ├── grade_recording.md           ← 成績 CSV 與 Cool 匯入檔
│   └── attendance_grading.md        ← 實體簽到批改流程
│
├── scripts/                         ← 可重複使用的 Python 工具
│   ├── extract_xlsx_content.py      ← Excel 全位置文字提取
│   ├── extract_pdf_content.py       ← PDF 文字＋OCR fallback
│   ├── parse_filename.py            ← 學號姓名解析（含 ntnu_/ntust_ 前綴）
│   ├── validate_folder_structure.py ← 開工前驗證資料夾正確性
│   └── setup_new_hw.py              ← 為新作業建立標準目錄
│
└── templates/                       ← 範本與範例
    ├── grade_csv_template.csv       ← HW{N}_成績.csv 三欄格式
    └── appeal_reply_examples.md     ← 給學生的委婉道歉信範本
```

注意：地圖裡用**正斜線**（`references/`），但同一份 SKILL.md 描述**工作根目錄**時改用**反斜線**（`HW{N}\`）。這是有意識的區分（skill 內部路徑 vs Windows 使用者路徑）。

### 2.6 【原文】ASCII 流程圖的寫法（逐字）

```
新作業開工
   │
   ▼
讀評分標準 ──→ 跟包子確認 ──→ 盤點檔案數 ──→ 與包子對齊
   │                                              │
   │                                              ▼
   │                                        逐份提取（六位置）
   │                                              │
   │                                              ▼
   │                                          自動標分
   │                                              │
   │                                              ▼
   │                                  ┌─── B+ 以下 ─── 人工視覺判讀
   │                                  │                    │
   ▼                                  ▼                    ▼
產出 HW{N}_成績.csv ←─── 匯總全部結果 ←─────────────────────┘
   │
   ▼
寫入 Cool 匯入用檔案 ──→ 列異動清單給包子 ──→ 持續處理申訴與調分
```

字元集：`│ ▼ ── ──→ ← ┌ ┘`（全形方框繪製字元 + 全形箭頭）。

### 2.7 【原文】「不同情境的入口指引」表（逐字）

| 包子說的 | 你該做的 |
|----------|----------|
| 「幫我改 HW{N}」、「批改第 N 週作業」 | 走完整七步流程 |
| 「重新檢查圖片漏掃」 | 進入 `text_extraction.md` 的人工判讀 SOP |
| 「某某同學補繳，扣一級」 | 評分後將該人等第降一級 |
| 「某某同學遲交但不算遲交」 | 正常評分，不扣分 |
| 「某某同學申訴」 | 立刻對該檔案重做完整漏掃檢查 |
| 「重新登一次 Cool 匯入檔」 | 重讀最新 Cool 原始檔 + 既有 `HW{N}_成績.csv` 重新產出 |
| 「實體簽到批改」 | 走 `attendance_grading.md` 的流程 |
| 「D 都改 C-、E 改 F」 | 直接 mass-update CSV 的等第欄位 |
| 「準備新作業 HW{N}」 | `python scripts/setup_new_hw.py {N}` 建立標準目錄 |

左欄用**全形引號包住包子的原話**，右欄是動作（含要跑的指令或要進的 reference）。

### 2.8 【評註】段落結構的可移植骨架

作業批改型 SKILL.md 的骨架是可直接搬的，順序不要動：

1. h1 + blockquote 副標 + 定位散文
2. `## 何時載入這個 Skill`（口語 bullet）
3. `## 內建 Skill 檔案地圖`（ASCII 樹 + `←` 註解）
4. `## <領域> 基本資料（速查）`（兩欄表）
5. `## 工作根目錄的標準結構`（ASCII 樹）
6. `## <主流程名稱>的 N 步流程`（先列開工前必讀 references，再 `### Step N — ...`）
7. `## <核心原則>（一句話）`
8. `## 與包子互動的習慣`
9. `## 工作流程摘要圖`（ASCII）
10. `## 不同情境的入口指引`（兩欄表）

lecture-to-notion 多出兩個值得借用的節：`## 絕對不要出現的東西`（負面清單）與 `## 品質檢查清單`（`- [ ]` 勾選框）。**新 skill 建議兩套都收**——分析型工作最需要「不要做什麼」與「交件前自檢」。

---

## 3. CLAUDE.md 的定位與內容邊界

### 3.1 【原文】CLAUDE.md 全文（逐字）

```markdown
# 大數據行銷作業批改 — 工作目錄速查

這個資料夾是 **NTU IB5082 大數據行銷課程** 的批改工具包，給助教包子（andychen050229@gmail.com）用。

## 開工前必讀

1. **`SKILL.md`** — 完整流程總覽（七步流程、觸發條件、檔案地圖）
2. **`references/text_extraction.md`** — Excel/PDF 漏掃處理（必讀，過去 9 個漏掃案例的教訓）
3. **`references/grading_policy.md`** — 寬鬆給分原則、等第判定、遲交補繳
4. **`references/folder_structure.md`** — 包子的資料夾命名習慣與位置規範
5. **`references/grade_recording.md`** — CSV 與 Cool 匯入檔輸出
6. **`references/course_context.md`** — 課程背景、過去四週作業主題
7. **`references/attendance_grading.md`** — 實體簽到批改流程

## 工作根目錄

```
C:\Users\User\Desktop\大數據行銷\
```

底下有 HW1–HW4 作業資料夾、`匯入用檔案\`、`Cool 原始檔案\`、`第一次實體簽到\` 等。詳細位置在 `references/folder_structure.md`。

## 觸發本 skill 的關鍵字

批改、評分、HW、作業、登分、評分標準、Cool 匯入、成績登錄、實體簽到、出席成績、補繳、遲交、申訴重評、漏掃、IB5082。

## 給分基調（一句話）

寬鬆給分。邊界往上給。A+ 應佔繳交者 75–85%。
```

### 3.2 【原文】CLAUDE.md 的內容邊界（觀察自原文）

CLAUDE.md 只有 4 個 h2、29 行、1345 bytes，內容嚴格限制在：

| 段落 | 內容 | 是否與 SKILL.md 重複 |
|------|------|----------------------|
| （h1 下的一段） | 這資料夾是什麼、給誰用 | 重複（濃縮版） |
| `## 開工前必讀` | 7 個檔案的閱讀順序 + 一句話理由 | 重複（SKILL.md 是 5 項，這裡 7 項且第 1 項指回 SKILL.md） |
| `## 工作根目錄` | 一個 Windows 絕對路徑 + 底下有什麼 | 重複（濃縮版） |
| `## 觸發本 skill 的關鍵字` | 純關鍵字，用「、」串接，句末句號 | 重複 frontmatter 的觸發條件 |
| `## 給分基調（一句話）` | 三個短句：`寬鬆給分。邊界往上給。A+ 應佔繳交者 75–85%。` | 重複 SKILL.md |

CLAUDE.md **不含**：流程步驟、程式碼、表格資料、案例、語氣規範。它純粹是「導覽卡」。

SKILL.md 中對 CLAUDE.md 的定位註記為：`CLAUDE.md ← 工作目錄速查（被 Cowork 自動載入）`。

### 3.3 【評註】CLAUDE.md 的設計意圖

因為 CLAUDE.md 會被**自動注入 context**（不需要 agent 主動 Read），所以它只放三種必須零成本知道的東西：(a) 我在哪、(b) 該去讀什麼、(c) 一句話核心原則。刻意重複 SKILL.md 是特徵不是缺陷——目的是「即使 SKILL.md 沒被載入，agent 也不會做錯方向」。

新 skill 的 CLAUDE.md 應照抄這個 5 段結構，長度控制在 30 行 / 1.5 KB 以內，並把「一句話核心原則」換成行銷分析的等價物（例如「先看資料再開口。任何數字都要能回推到欄位。」）。

---

## 4. references/ 的切分邏輯與檔案粒度

### 4.1 【原文】6 份 references 的職責與規模

| 檔名 | bytes | 行數 | 職責（原文自述的第一句／標題） | 切分軸 |
|------|-------|------|--------------------------------|--------|
| `course_context.md` | 5521 | 116 | 「# 課程背景：NTU IB5082 大數據行銷」 | **領域背景**（不變的事實、歷史） |
| `folder_structure.md` | 7485 | 191 | 「# 資料夾結構與命名規範」 | **路徑與命名**（我在哪、東西叫什麼） |
| `grading_policy.md` | 6192 | 169 | 「# 評分政策」 | **判斷規則**（怎麼決定輸出值） |
| `text_extraction.md` | 8618 | 231 | 「# 文字提取與漏掃處理」 | **技術方法 + 失敗案例庫** |
| `grade_recording.md` | 6015 | 200 | 「# 成績登錄與檔案輸出」 | **輸出規格**（產出什麼、什麼格式） |
| `attendance_grading.md` | 3843 | 117 | 「# 實體簽到批改流程」 | **旁支流程**（同一 skill 的第二條 workflow） |

規模一致性：**3.8–8.6 KB / 116–231 行**。沒有 20 KB 的巨檔，也沒有 1 KB 的碎檔。

### 4.2 【原文】切分軸的歸納

六份檔案對應六個問句，彼此**不重疊**：

1. `course_context.md` — 「這個領域的固定事實是什麼？過去發生過什麼？」
2. `folder_structure.md` — 「檔案在哪？該叫什麼名字？」
3. `grading_policy.md` — 「怎麼決定輸出的值？邊界怎麼判？」
4. `text_extraction.md` — 「怎麼把輸入的資料挖出來？以前在哪裡挖漏過？」
5. `grade_recording.md` — 「產出什麼檔？欄位與編碼怎麼定？」
6. `attendance_grading.md` — 「另一條不同的工作流怎麼走？」

### 4.3 【原文】每份 references 的內部結構特徵

**共同特徵：**
- h1 = 檔名對應的中文主題，**不含** frontmatter（references 沒有 YAML）。
- h1 之後一段「為什麼這份文件重要」的散文，常帶威脅性語氣：
  - `text_extraction.md`：「**沒有把這份文件全部讀過，就會像 HW3 一樣大規模漏掃。**」
  - `folder_structure.md`：「每次接到新工作……要 **完全沿用** 這套命名規則，不要自創縮寫或英文化。」
- h2 用**中文數字編號**：`## 一、寬鬆給分原則`、`## 二、目標分數比例（用來自我校準）`、`## 三、等第判定的決策樹`……（`grading_policy.md`、`course_context.md`、`grade_recording.md`、`attendance_grading.md` 都用中文數字；`folder_structure.md` 與 `text_extraction.md` 用純名詞 h2 + 阿拉伯數字 h3）。
- 幾乎每節都以**表格**或**程式碼區塊**收尾，不是純散文。
- 末尾常有「維護條款」：
  - `folder_structure.md` 末節：「## 變動紀錄 / 如果某次包子改變命名習慣（例如把「準時」改成「on_time」），**這份文件要立刻更新**，並把舊命名也保留作為向後相容。」
  - `attendance_grading.md` 末節：「## 六、未來課程可能的擴充」

**`text_extraction.md` 的特有結構（案例驅動）：**
先列「為什麼這份文件很重要」＋一張**失敗案例表**，再按優先順序列出六個檢查位置，每個位置附可執行程式碼。

### 4.4 【原文】失敗案例表（text_extraction.md，逐字）

| 學號 | 漏掃位置 | 原成績 → 新成績 |
|------|----------|----------------|
| B12704068 李政澐 | 4 張嵌入圖片 | B → A+ |
| B12610003 張瑋庭 | 儲存格文字（max_row 限制） | B+ → A+ |
| B12610051 黃姸寧 | 嵌入圖片 | A- → A+ |
| R14724072 陳柏瑜 | 嵌入圖片 | A- → A+ |
| B11703015 學生I | 4 張嵌入圖片 | B → A+ |
| B12704019 林禹青 | 嵌入圖片 | B → B+ |
| B12704061 朱浩瑄 | 嵌入圖片 | B- → B |
| R14724039 學生O | **文字方塊**（drawing XML） | A- → A+ |
| T14704118 Yat YEUNG | **英文分頁名與英文作答** | B+ → A+ |

原文緊接一句：「每一個都是因為『程式以為他沒寫』而誤判。」

### 4.5 【原文】歷史決策時序表（course_context.md，逐字）

| 時間 | 事件 | 影響 |
|------|------|------|
| HW2 批完 | 包子要求 D → C-、E → F | 之後等第改用 C- 與 F |
| HW3 學生I申訴 | 發現嵌入圖片漏掃 | 啟動「圖片漏掃 SOP」，HW3 一次升等 9 人 |
| HW3 學生O申訴 | 發現文字方塊漏掃 | 加入 ZIP+drawing XML 檢查 |
| HW4 Yat YEUNG 申訴 | 英文分頁名漏掃 | 關鍵字偵測加中英對照 |
| HW4 開始 | 引入 A-/B+/B- 等第細分 | 計算錯與缺題分開計分 |

原文緊接一句：「每次新作業批改前，務必把這些經驗放在心上。」

### 4.6 【評註】references 切分規則的抽象化

可歸納成一條規則：**「一份 reference = 一個問句」**，且要滿足三個條件：

1. **獨立可讀**：不必讀其他 reference 就能執行該問句對應的任務。
2. **規模 4–9 KB / 110–230 行**：超過就再切一刀，不足就併回去。
3. **以表格或程式碼收尾**：如果一節只寫得出散文，說明這節還沒想清楚。

另一個關鍵特徵是：**至少要有一份「失敗案例庫」型 reference**（此處是 `text_extraction.md`）。它記錄「哪些具名的個案曾經被做錯、錯在哪個技術位置、修正後結果」。這是整包 skill 裡最高價值的資產，因為它把抽象的「小心一點」變成「去看 `xl/drawings/*.xml`」。

新 skill 的 references 對應切分建議（維持 6 檔 ± 1）：

| 建議檔名 | 對應原軸 | 應寫什麼 |
|----------|----------|----------|
| `analysis_context.md` | course_context | 分析領域固定事實、過去做過哪些分析、每次的結論與轉折 |
| `folder_structure.md` | folder_structure（同名沿用） | 專案根目錄、資料／輸出／圖表命名規範 |
| `analysis_policy.md` | grading_policy | 判斷規則：什麼算顯著、要不要剔除離群、樣本不足怎麼辦、預設參數 |
| `data_loading.md` | text_extraction | 讀檔技術 + **踩雷案例庫**（編碼、欄名空白、混型欄、日期格式、遺漏值編碼） |
| `output_spec.md` | grade_recording | 輸出檔規格：檔名、欄位、編碼、圖表尺寸、報告結構 |
| `<旁支流程>.md` | attendance_grading | 第二條 workflow（例：定期更新、儀表板產出） |

---

## 5. scripts/ 的程式風格

### 5.1 【原文】共通的檔頭與 docstring 格式

五份 `scripts/*.py` 與一次性的 `auto_grade.py` 都遵循：

```python
#!/usr/bin/env python3
"""
<一句話說明這支腳本做什麼>（中文）

<若有需要，列舉它處理的位置／情境，用縮排數字清單>

用法：
    python <script>.py <args>
    python <script>.py <args> --option value   # 附中文註解

依賴：
    <外部工具，如 poppler-utils（pdftotext, pdftoppm）>

輸出（stdout，JSON）：
{
  "key": ...,
}

檢查項目：
  1. ...

退出碼：
  0 = 全部 OK
  1 = 有警告但可繼續
  2 = 嚴重錯誤需處理
"""
```

實例（`extract_xlsx_content.py` 逐字）：

```python
#!/usr/bin/env python3
"""
從一份 .xlsx 提取所有可能藏文字的位置：
  1. 儲存格（公式 + 計算值兩種模式）
  2. 文字方塊（drawing XML）
  3. 嵌入圖片（提取為獨立檔案，回傳路徑供視覺判讀）
  4. 儲存格註解
  5. 隱藏工作表

用法：
    python extract_xlsx_content.py path/to/student.xlsx [--media-dir out_images/]

輸出（stdout，JSON）：
{
  "sheets": [{"name": "答案", "hidden": false, "cells": [{"coord": "A1", "text": "..."}], "comments": [...]}],
  "textboxes": [{"file": "xl/drawings/drawing1.xml", "text": "..."}],
  "images": ["out_images/image1.png", ...],
  "all_text_normalized": "...全部文字正規化後串接..."
}
"""
```

實例（`validate_folder_structure.py` 逐字）：

```python
#!/usr/bin/env python3
"""
驗證 HW{N} 資料夾是否符合包子的標準結構，給批改前的快速健檢。

用法：
    python validate_folder_structure.py 4
    python validate_folder_structure.py 4 --root "C:/Users/User/Desktop/大數據行銷"

檢查項目：
  1. HW{N}\ 資料夾存在
  2. 評分標準 docx 存在（fuzzy match：第.*?(周|次).*?評分標準\.docx）
  3. 準時\ 資料夾存在且有檔案
  4. 遲交\ 資料夾（可選）
  5. 匯入用檔案\ 資料夾存在
  6. Cool 原始檔案\ 至少有一份 .csv
  7. 列出 ~$lock、.DS_Store 等需要忽略的暫存檔

退出碼：
  0 = 全部 OK
  1 = 有警告但可繼續
  2 = 嚴重錯誤需處理
"""
```

### 5.2 【原文】import 風格

一律**標準庫在前、字母序、一個 import 一行**，第三方套件空一行放後面：

```python
import argparse
import json
import os
import re
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

from openpyxl import load_workbook
```

例外：一次性腳本 `auto_grade.py` 用單行合併寫法 `import json, os, re, sys, unicodedata, zipfile`，且把 `subprocess`、`tempfile` **在函式內部**才 import：

```python
def extract_pdf(path):
    """用 pdftotext 提取，retain 文字長度與是否需要 OCR"""
    import subprocess, tempfile
```

### 5.3 【原文】CLI 介面（argparse）

四種模式全部出現在原始碼中：

```python
# 模式 A：單一位置參數（extract_xlsx_content.py / extract_pdf_content.py）
ap = argparse.ArgumentParser()
ap.add_argument('path')
ap.add_argument('--media-dir', default=None,
                help='若提供，把嵌入圖片提取到這個資料夾')
args = ap.parse_args()
```

```python
# 模式 B：位置參數 type=int + --root 有 Windows 預設值（setup_new_hw.py / validate_folder_structure.py）
ap = argparse.ArgumentParser()
ap.add_argument('hw_num', type=int)
ap.add_argument('--root', default=r'C:/Users/User/Desktop/大數據行銷')
ap.add_argument('--week-naming', default=None,
                help='評分標準檔的週次數字／文字。預設與 hw_num 相同（阿拉伯數字）')
args = ap.parse_args()
```

```python
# 模式 C：互斥群組（單檔 or 整個資料夾）（parse_filename.py）
ap = argparse.ArgumentParser()
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument('filename', nargs='?')
g.add_argument('--dir', help='掃描整個資料夾')
args = ap.parse_args()
```

```python
# 模式 D：帶數值閾值的可調參數（extract_pdf_content.py）
ap.add_argument('--text-threshold', type=int, default=20,
                help='提取出的字元數低於此值即視為圖片型 CV PDF')
```

CLI 慣例要點：
- `ArgumentParser()` **不傳 description**（說明全在 docstring）。
- 變數名固定 `ap`；互斥群組固定 `g`。
- 所有 `--option` 用 kebab-case（`--media-dir`、`--image-dir`、`--text-threshold`、`--week-naming`），argparse 自動轉 `args.media_dir`。
- 所有 `--option` 都有 `help=` 且**用中文寫**。
- **Windows 路徑預設值一律用 raw string + 正斜線**：`default=r'C:/Users/User/Desktop/大數據行銷'`。
- 沒有 `--verbose`／`--quiet`／`--dry-run` 這類旗標；沒有 logging 模組，全部用 `print()`。

### 5.4 【原文】錯誤處理風格

**(a) 靜默降級 —— 外部工具缺失或超時回傳空值，不拋例外：**

```python
def pdftotext(path):
    try:
        out = subprocess.run(
            ['pdftotext', '-layout', path, '-'],
            capture_output=True, text=True, timeout=60
        )
        return out.stdout
    except FileNotFoundError:
        return ''
    except subprocess.TimeoutExpired:
        return ''
```

```python
def pdftoppm(path, out_dir, dpi=150):
    os.makedirs(out_dir, exist_ok=True)
    prefix = os.path.join(out_dir, 'page')
    try:
        subprocess.run(
            ['pdftoppm', '-jpeg', '-r', str(dpi), path, prefix],
            check=True, timeout=120
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    return sorted([
        os.path.join(out_dir, f) for f in os.listdir(out_dir)
        if f.startswith('page-') and f.endswith('.jpg')
    ])
```

**(b) 逐項 continue —— 單一項目壞掉不影響整批：**

```python
for n in names:
    try:
        xml = z.read(n).decode('utf-8', errors='ignore')
    except Exception:
        continue
```

**(c) 錯誤打包進回傳值 —— 讓呼叫端決定怎麼辦（`auto_grade.py`）：**

```python
try:
    wb_f = load_workbook(path, data_only=False)
    wb_v = load_workbook(path, data_only=True)
except Exception as e:
    return {'error': f'open fail: {e}', 'text': '', 'sheet_names': [], 'image_count': 0, 'drawing_count': 0, 'has_textbox': False}
```

以及不支援副檔名的統一回傳：

```python
return {'text': '', 'sheet_names': [], 'image_count': 0, 'drawing_count': 0, 'has_textbox': False, 'text_len': 0, 'error': f'unsupported ext: {ext}'}
```

**(d) 三桶收集 + 退出碼 —— 驗證型腳本（`validate_folder_structure.py`）：**

```python
    errors = []
    warnings = []
    info = []
    ...
    if not os.path.isdir(hw_dir):
        errors.append(f'❌ {hw_dir} 不存在 — 先執行 setup_new_hw.py {args.hw_num}')
    else:
        info.append(f'✅ {hw_dir}')
    ...
    if errors:
        print(f'⛔ 有 {len(errors)} 項嚴重問題')
        sys.exit(2)
    if warnings:
        print(f'⚠ 有 {len(warnings)} 項警告但可繼續')
        sys.exit(1)
    print('🎉 所有檢查通過，可以開始批改')
    sys.exit(0)
```

**(e) 冪等（idempotent）—— 建立型腳本不覆蓋既有物（`setup_new_hw.py`）：**

```python
    if os.path.isdir(hw_dir):
        print(f'⚠ {hw_dir} 已存在 — 不覆蓋')
    else:
        os.makedirs(hw_dir)
        print(f'✅ 建立 {hw_dir}')

    for sub in ('準時', '遲交'):
        p = os.path.join(hw_dir, sub)
        if not os.path.isdir(p):
            os.makedirs(p)
            print(f'✅ 建立 {p}')
```

**(f) 錯誤訊息一定附「下一步該做什麼」：**

```python
errors.append(f'❌ {hw_dir} 不存在 — 先執行 setup_new_hw.py {args.hw_num}')
errors.append(f'❌ 找不到評分標準 docx — 應放在 {hw_dir}\\第{{N}}周作業評分標準.docx')
warnings.append(f'⚠ {import_dir} 不存在 — 寫入 Cool 匯入檔前要先建立')
errors.append('❌ Cool 原始檔案 資料夾為空 — 請包子先匯出最新名單')
```

格式恆為：`<emoji> <事實> — <祈使句動作>`。破折號用全形 `—`。

### 5.5 【原文】emoji 語意約定（腳本輸出用）

| emoji | 語意 | 出現處 |
|-------|------|--------|
| `✅` | 檢查通過 / 已建立 | info.append、setup 的 print |
| `⚠` | 警告，可繼續 | warnings.append、已存在不覆蓋 |
| `❌` | 嚴重錯誤，需處理 | errors.append |
| `⛔` | 總結：有 N 項嚴重問題 | 退出前 |
| `🎉` | 全部通過 | 退出前 |

（註：此為**腳本 stdout** 的約定；與 agent 回覆使用者的文字無關。）

### 5.6 【原文】編碼處理

| 場景 | 原文寫法 | 出處 |
|------|----------|------|
| 寫 CSV | `open(path, 'w', encoding='utf-8-sig', newline='')` | grade_recording.md、SKILL.md |
| 讀 CSV | `open(cool_csv, 'r', encoding='utf-8-sig')` | grade_recording.md |
| 為何用 BOM | 「編碼：UTF-8 with BOM（讓 Excel 開不會亂碼）」 | grade_recording.md |
| 讀 ZIP 內 XML | `z.read(n).decode('utf-8', errors='ignore')` | extract_xlsx_content.py、auto_grade.py、text_extraction.md |
| subprocess 取文字（風格一） | `subprocess.run([...], capture_output=True, text=True, timeout=60)` → `out.stdout` | extract_pdf_content.py |
| subprocess 取文字（風格二） | `subprocess.run([...], capture_output=True, timeout=60)` → `r.stdout.decode('utf-8', errors='ignore')` | auto_grade.py |
| 讀未知編碼的 CSV | `open(path,'rb').read()` → `data.decode('utf-8', errors='ignore')` | auto_grade.py `extract_csv()` |
| JSON 輸出 | `json.dump(out, sys.stdout, ensure_ascii=False, indent=2)` | 全部 extract 腳本 |
| JSON 寫檔 | `open('grade_results.json','w',encoding='utf-8')` + `ensure_ascii=False, indent=2` | auto_grade.py |
| 讀 JSON 輸入 | `open('students.json','r',encoding='utf-8')` | auto_grade.py |

**文字正規化函式（三支腳本逐字重複同一份實作）：**

```python
def norm(s: str) -> str:
    return unicodedata.normalize('NFKC', s).lower().strip()
```

`auto_grade.py` 版本無型別註記：

```python
def norm(s):
    return unicodedata.normalize('NFKC', s).lower().strip()
```

`text_extraction.md` 對此的規範說明（逐字）：

```python
import unicodedata
def norm(s):
    return unicodedata.normalize('NFKC', s).lower()

# 「Ｂob Stone」（全形 B）→ 「bob stone」  ✓
# 「BOB STONE」 → 「bob stone」  ✓
```

以及「務必做 NFKC 正規化並小寫」的原文要求：「提取完所有文字後，比對關鍵字之前 **務必做 NFKC 正規化** 並 **小寫**」。

### 5.7 【原文】輸出格式

**格式一：JSON to stdout（給 agent 消費）**

```python
    out = {
        'sheets': sheets,
        'textboxes': textboxes,
        'images': images,
        'all_text_normalized': blob,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
```

```python
    out = {
        'text': text,
        'is_image_pdf': is_image_pdf,
        'page_images': images,
        'all_text_normalized': norm(text),
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
```

`parse_filename.py` 兩種模式都輸出 JSON，掃資料夾時**失敗項也進陣列並標記**：

```python
            r = parse(f)
            if r:
                results.append(r)
            else:
                results.append({'filename': f, 'parse_failed': True})
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
```

**格式二：人眼看的分隔線報表（給包子看）**

```python
    print('=' * 60)
    print(f' HW{args.hw_num} 資料夾結構驗證')
    print('=' * 60)
    for line in info:
        print(line)
    for line in warnings:
        print(line)
    for line in errors:
        print(line)
    print('=' * 60)
```

順序恆為 **info → warnings → errors**（好消息先講）。

**格式三：對齊欄寬的逐列進度 + Summary（`auto_grade.py`）**

```python
        print(f"{sid_norm:25s} {info['name'][:20]:20s}  {g['grade']:5s}  "
              f"spss={g['has_spss']:1d} score={g['has_score']:1d} "
              f"cmp={g['has_compare']:1d} pref={g['has_preference']:1d} "
              f"img={total_images}")
```

```python
    grade_count = {}
    for r in results.values():
        g = r['grade']
        grade_count[g] = grade_count.get(g, 0) + 1
    print(f"\n=== Summary ===")
    for g in ['A+', 'A-', 'B', 'D', 'NEEDS_VISUAL']:
        if g in grade_count:
            print(f"  {g}: {grade_count[g]}")
    print(f"  Total: {len(results)}")
```

**格式四：「接下來請你做的事」交棒清單（`setup_new_hw.py`）**

```python
    print()
    print('=== 接下來請包子做的事 ===')
    print(f'1. 把學生繳交檔案放到：{os.path.join(hw_dir, "準時")}\\')
    print(f'2. 把評分標準 docx 放到：{rubric_hint}')
    print(f'   （命名可微調：第{week}周/第{week}次 都會被自動辨識）')
    print(f'3. 確認 Cool 原始檔案/ 中有最新的成績單匯出')
    print()
    print('完成後執行：')
    print(f'    python validate_folder_structure.py {args.hw_num}')
```

腳本**主動指出下一支該跑的腳本**，形成鏈：`setup_new_hw.py` → `validate_folder_structure.py` → 七步流程。

### 5.8 【原文】fuzzy match 與 junk file 過濾（可移植的兩個小工具）

```python
def find_rubric(hw_dir: str):
    """fuzzy match 評分標準 docx"""
    pattern = re.compile(r'第.*?(周|次).*?評分標準\.docx$')
    for f in os.listdir(hw_dir):
        if pattern.search(f):
            return os.path.join(hw_dir, f)
    return None
```

```python
def check_submission_folder(hw_dir: str):
    """準時資料夾（HW1 是 作業檔案/準時/，其他是 準時/）"""
    candidates = [
        os.path.join(hw_dir, '準時'),
        os.path.join(hw_dir, '作業檔案', '準時'),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None
```

```python
def find_junk_files(folder: str):
    """找 ~$lock、.DS_Store 等需要忽略的"""
    junk = []
    if not os.path.isdir(folder):
        return junk
    for root, _, files in os.walk(folder):
        for f in files:
            if f.startswith('~$') or f.startswith('._') or f == '.DS_Store':
                junk.append(os.path.join(root, f))
    return junk
```

計數時同步排除 junk：

```python
            count = sum(
                1 for r, _, fs in os.walk(sub)
                for f in fs
                if not (f.startswith('~$') or f.startswith('._') or f == '.DS_Store')
            )
```

```python
def latest_cool_csv(root: str):
    """找 Cool 原始檔案 中最新的 CSV"""
    cool_dir = os.path.join(root, 'Cool 原始檔案')
    if not os.path.isdir(cool_dir):
        return None
    csvs = sorted(glob.glob(os.path.join(cool_dir, '*.csv')))
    return csvs[-1] if csvs else None
```

### 5.9 【原文】關鍵字字典 + 閾值判定的規則式分類器（`auto_grade.py`）

字典宣告風格：模組層級全大寫常數，`_PATTERNS` 後綴，**中英混列、含拼寫變體與縮寫**，逐行以逗號結尾、同義字同一行：

```python
SPSS_OUTPUT_PATTERNS = [
    'spss', '統計分析', 'kmo', 'bartlett', 'kaiser', 'meyer', 'olkin',
    '球形', '球型', 'sphericity',
    '共同性', 'communalit',
    '解釋總變異', '解說總變異', '總變異量', 'total variance', '解說的總變異',
    '特徵值', 'eigenvalue', 'eigen',
    '成分矩陣', 'component matrix', '因素矩陣', 'factor matrix',
    '轉軸', '旋轉', 'rotated', 'rotation', 'varimax', 'oblimin', '斜交',
    '陡坡', 'scree',
    '因素負荷', '因素荷量', 'loading', 'loadings',
    '萃取法', '萃取方法', 'extraction', '主成分', 'principal component',
    'kmo 與 bartlett', 'kmo and bartlett', 'kmo 和 bartlett',
    'communalities', 'reproduced', '再生', '重製',
    '相關矩陣', 'correlation matrix',
]
```

偵測函式極簡（子字串比對，不用 regex）：

```python
def detect_keywords(text, patterns):
    matches = []
    for p in patterns:
        if p in text:
            matches.append(p)
    return matches
```

**閾值化布林**（避免單一關鍵字誤觸）：

```python
    has_spss = len(spss_hits) >= 2  # 至少兩個關鍵字才算
    has_score = len(score_hits) >= 1
    has_compare = len(cmp_hits) >= 2
    has_preference = len(pref_hits) >= 2
```

**逃生門旗標**（承認自動判定不可靠）：

```python
    # If many images and few text matches, content likely in screenshots → flag for visual review
    needs_visual = (total_image_count >= 3 and not has_spss)
    ...
    elif total_image_count >= 5:
        # 大量圖片但沒識別出 SPSS → 需要視覺判讀
        grade = 'NEEDS_VISUAL'
```

**回傳「判斷 + 證據」而非只回傳判斷**：

```python
    return {
        'grade': grade,
        'has_spss': has_spss,
        'has_score': has_score,
        'has_compare': has_compare,
        'has_preference': has_preference,
        'spss_hits': spss_hits[:8],
        'score_hits': score_hits[:8],
        'cmp_hits': cmp_hits[:8],
        'pref_hits': pref_hits[:8],
        'image_count': total_image_count,
        'needs_visual': needs_visual,
    }
```

（命中證據截斷到前 8 個，避免 JSON 爆掉。）

**多來源合併後再判定**（同一人多檔）：

```python
        for fi in info['files']:
            ext = fi['ext']
            if ext == 'py':
                # skip python script
                files_info.append({'file': fi['filename'], 'skip_reason': 'python script'})
                continue
            r = extract_any(fi['fullpath'])
            merged_text.append(r.get('text', ''))
            total_images += r.get('image_count', 0)
            ...
        full_text = ' '.join(merged_text)
        g = grade_one(full_text, total_images)
```

**統一介面的 dispatcher**：

```python
def extract_any(path):
    ext = path.rsplit('.', 1)[-1].lower()
    if ext == 'xlsx':
        return extract_xlsx(path)
    if ext == 'pdf':
        return extract_pdf(path)
    if ext == 'docx':
        return extract_docx(path)
    if ext in ('csv', 'tsv'):
        return extract_csv(path)
    return {'text': '', 'sheet_names': [], 'image_count': 0, 'drawing_count': 0, 'has_textbox': False, 'text_len': 0, 'error': f'unsupported ext: {ext}'}
```

所有 extractor **回傳相同 key 集合**（`text` / `sheet_names` / `image_count` / `drawing_count` / `has_textbox` / `text_len`，錯誤時多一個 `error`），呼叫端可無條件 `.get()`。

### 5.10 【原文】其他被 references 規範但未落入 scripts 的程式碼片段

**Excel 儲存格雙模式讀取（text_extraction.md 逐字）：**

```python
from openpyxl import load_workbook

wb_formula = load_workbook(path)              # 拿公式
wb_values = load_workbook(path, data_only=True)  # 拿計算結果

for sheet_name in wb_formula.sheetnames:
    ws = wb_formula[sheet_name]
    # 不要設 max_row/max_col 限制
    for row in ws.iter_rows():
        for cell in row:
            if cell.value:
                yield (sheet_name, cell.coordinate, str(cell.value))
```

**文字方塊提取（text_extraction.md 逐字）：**

```python
import zipfile
import re
from xml.etree import ElementTree as ET

def extract_textbox_text(xlsx_path):
    texts = []
    with zipfile.ZipFile(xlsx_path) as z:
        drawing_files = [n for n in z.namelist() if n.startswith('xl/drawings/') and n.endswith('.xml')]
        for df in drawing_files:
            xml = z.read(df).decode('utf-8', errors='ignore')
            # <a:t>...</a:t> 是 DrawingML 的文字節點
            matches = re.findall(r'<a:t[^>]*>(.*?)</a:t>', xml, re.DOTALL)
            for m in matches:
                if m.strip():
                    texts.append((df, m))
    return texts
```

**嵌入圖片提取（text_extraction.md 逐字）：**

```python
import zipfile
import os

def extract_embedded_images(xlsx_path, out_dir):
    """把所有嵌入圖片存成獨立檔案，回傳路徑清單"""
    paths = []
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(xlsx_path) as z:
        media = [n for n in z.namelist() if n.startswith('xl/media/')]
        for m in media:
            data = z.read(m)
            fname = os.path.basename(m)
            outpath = os.path.join(out_dir, fname)
            with open(outpath, 'wb') as f:
                f.write(data)
            paths.append(outpath)
    return paths
```

**儲存格註解與隱藏分頁（text_extraction.md 逐字）：**

```python
for row in ws.iter_rows():
    for cell in row:
        if cell.comment:
            yield cell.comment.text
```

```python
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    if ws.sheet_state == 'hidden':
        # 仍然要掃這張表的內容
        ...
```

原文附註：「**注意**：`load_workbook(read_only=True)` 模式下讀不到註解，要用一般模式。」

**拼寫變體 regex（text_extraction.md 逐字）：**

```python
BOB_STONE_PATTERN = re.compile(r'\b(bo[bnm])\s*stone\b', re.I)
# 抓 "Bob Stone", "Bon Stone"（HW3 學生I）, "Bom Stone"
```

**分頁名中英搜尋清單（text_extraction.md 逐字）：**

```python
ANSWER_SHEET_PATTERNS = [
    '答案', '回答', '說明', '討論', '比較', '分析',
    'answer', 'ans', 'discussion', 'summary', 'comparison', 'differentiation',
    'q1', 'q2', 'question'
]
```

**CSV 寫出（grade_recording.md 逐字）：**

```python
import csv
with open('HW4_成績.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['學號', '姓名', '等第'])
    for sid, name, grade in rows:
        w.writerow([sid, name, grade])
```

**保留完整欄位順序的 DictReader / DictWriter 迴圈（grade_recording.md 逐字）：**

```python
import csv

# 讀 Cool 原始檔
with open(cool_csv, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames

# 找 HW{N} 對應欄位（用 contains 比對）
hw_col = next(c for c in fieldnames if 'HW{N}' 對應的關鍵字 in c)

# 比對學號（小寫 + 移除前綴）
def normalize_sid(s):
    s = s.strip().lower()
    for prefix in ('ntnu_', 'ntust_', 'ntu_'):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s

grade_map = {normalize_sid(sid): grade for sid, _, grade in graded}

for row in rows:
    sid_norm = normalize_sid(row['學號'])
    if sid_norm in grade_map:
        row[hw_col] = grade_map[sid_norm]
    else:
        row[hw_col] = 'F'   # 名單上但找不到繳交 → 未繳交

# 寫回（保持原欄位順序）
with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
```

（注意 `hw_col = next(c for c in fieldnames if 'HW{N}' 對應的關鍵字 in c)` 這行在原文是**偽碼佔位**，不是可執行程式碼。）

**檔名解析 regex（parse_filename.py 逐字，與 grade_recording.md 的版本略有差異）：**

```python
PATTERN = re.compile(
    r'^(?P<prefix>ntnu_|ntust_|ntu_)?'
    r'(?P<sid>[A-Za-z0-9]+)#_'
    r'(?P<name>[^_]+?)'
    r'_\d+_\d+_'
    r'(?P<rest>.*?)'
    r'\.(?P<ext>[A-Za-z0-9]+)$'
)


def parse(fname: str):
    base = os.path.basename(fname)
    m = PATTERN.match(base)
    if not m:
        return None
    prefix = m.group('prefix') or ''
    sid = m.group('sid')
    name = m.group('name').strip()
    return {
        'filename': base,
        'prefix': prefix,
        'sid_raw': prefix + sid,
        'sid_normalized': sid.lower(),
        'name': name,
        'ext': m.group('ext').lower(),
        'rest': m.group('rest'),
    }


def normalize_sid(sid_raw: str) -> str:
    s = sid_raw.strip().lower()
    for pre in ('ntnu_', 'ntust_', 'ntu_'):
        if s.startswith(pre):
            s = s[len(pre):]
    return s
```

grade_recording.md 中的版本（用 `m['sid']` 下標語法而非 `m.group()`，且無 ext 群組）：

```python
import re

PATTERN = re.compile(
    r'^(?P<prefix>ntnu_|ntust_|ntu_)?'
    r'(?P<sid>[A-Za-z0-9]+)#_'
    r'(?P<name>[^_]+?)_'
    r'\d+_\d+_'
    r'(?P<rest>.*)$'
)

def parse_filename(fname):
    m = PATTERN.match(fname)
    if not m:
        return None
    return {
        'sid': m['sid'],
        'name': m['name'].strip(),
        'prefix': m['prefix'] or '',
        'full_sid': (m['prefix'] or '') + m['sid'],
    }
```

### 5.11 【原文】命令列（非 Python）指令慣例

references / SKILL.md 內給的 shell 指令一律用 ```bash 標語言，路徑用雙引號包住：

```bash
pandoc "C:\...\HW{N}\第{N}周作業評分標準.docx" -t plain
```

```bash
find "C:\...\HW{N}\準時" -type f | wc -l
find "C:\...\HW{N}\遲交" -type f | wc -l 2>/dev/null || echo 0
```

```bash
python scripts/extract_xlsx_content.py "/path/to/student.xlsx" --media-dir /tmp/imgs/
python scripts/extract_pdf_content.py "/path/to/student.pdf" --image-dir /tmp/pages/
```

```bash
pdftotext -layout input.pdf output.txt
pdftotext -raw input.pdf output.txt
pdftoppm -jpeg -r 150 input.pdf page_prefix
pdftoppm -jpeg -r 200 "手寫_2026-03-30_224432.pdf" page
pandoc input.docx -t plain -o output.txt
pandoc input.docx -t plain --track-changes=all
ls -t "C:/.../Cool 原始檔案/" | head -1
```

外部工具依賴：**pandoc**（docx→plain）、**poppler-utils**（pdftotext / pdftoppm）、**openpyxl**。

### 5.12 【評註】程式風格的品質觀察與待修點

以下是本次閱讀發現的具體問題，新 skill 若沿用這些腳本要先修：

1. **`extract_pdf_content.py:76` 的條件式贅餘且語意錯誤**
   ```python
   if args.image_dir and (is_image_pdf or args.image_dir):
   ```
   後半段 `(is_image_pdf or args.image_dir)` 在 `args.image_dir` 為真時恆為真，等價於 `if args.image_dir:`。docstring 說「若 PDF 是圖片型或希望同時轉圖」，實際行為是「只要給了 `--image-dir` 就一定轉圖」。若要省配額，應改成 `if args.image_dir and is_image_pdf:` 並另加 `--always-render` 旗標。

2. **「最新檔」有兩套互相矛盾的定義**
   - `folder_structure.md` 寫：`ls -t "C:/.../Cool 原始檔案/" | head -1`（依 **mtime**）
   - `validate_folder_structure.py:latest_cool_csv()` 寫：`sorted(glob.glob(...))[-1]`（依 **檔名字典序**）
   兩者只在檔名為 ISO 時間戳（`2026-04-12T0649_...`）時才會巧合一致。新 skill 應明訂一套（建議字典序 + 檔名 ISO 時間戳，因為它不受複製檔案改變 mtime 影響），並在 reference 與腳本中寫成同一種。

3. **`extract_xlsx_content.py` 有未使用的 import**：`from xml.etree import ElementTree as ET` 全檔未用（因為改用 regex 抓 `<a:t>`）。

4. **`extract_xlsx_content.py` 同時 `load_workbook` 兩次且不能用 `read_only=True`**（因為要讀 comment）。對 200+ 檔 × 大 xlsx 是記憶體與時間熱點。`text_extraction.md` 已記載為刻意取捨，但新 skill 若處理大資料檔（行銷分析常見數十萬列），這個實作**不能直接照用**，必須改成 `read_only=True` + 分開跑 comment 掃描，或直接用 `pandas.read_excel` / `polars`。

5. **沒有設定 stdout 編碼**：所有腳本靠 `print()` 與 `json.dump(..., sys.stdout)` 輸出中文。在 Windows PowerShell 5.1（預設 cp950）直接跑會有 `UnicodeEncodeError` 風險。既有腳本能運作是因為部分在 Linux sandbox 執行（見下一點）。**新 skill 的腳本應在檔頭加：**
   ```python
   import sys
   if sys.platform == 'win32':
       sys.stdout.reconfigure(encoding='utf-8')
       sys.stderr.reconfigure(encoding='utf-8')
   ```

6. **兩種執行環境混用的證據**：`scripts/*.py` 的 `--root` 預設是 Windows 路徑 `r'C:/Users/User/Desktop/大數據行銷'`，但 `auto_grade.py` 寫死 `HW7_DIR = "/sessions/optimistic-festive-mayer/mnt/大數據行銷/HW7/"`（Cowork Linux sandbox 掛載點）。這對應 `folder_structure.md` 的「路徑書寫慣例」四條規則。新 skill 的腳本**不應寫死任一種**，一律 `--root` 參數化 + `pathlib`。

7. **一次性腳本 vs 可重用腳本的分野是有意的**：`auto_grade.py` 放在 `local_.../outputs/hw7_work/`（session 產出區）而非 `scripts/`，且寫死 `HW7_DIR`、寫死 `students.json`／`grade_results.json` 相對路徑、關鍵字字典綁定 HW7 主題。**這個分層值得沿用**：每次分析的即興腳本落在專案 outputs 區，只有「跨次都會用」的才升級進 `scripts/`。

8. **無測試、無 type hints 一致性**：型別註記只出現在部分函式簽名（`def norm(s: str) -> str`、`def find_rubric(hw_dir: str)`），不強制。沒有 pytest。新 skill 維持這個輕量程度即可，不要過度工程化——但**驗證型腳本本身就是測試**（`validate_folder_structure.py` 扮演這個角色）。

---

## 6. AskUserQuestion 卡點確認的時機

### 6.1 【原文】明文出現 AskUserQuestion 的兩處

**(a) `SKILL.md` Step 1 結尾（逐字）：**

> 從輸出萃取：題目數、各題標準答案、評分要點、致命傷條件、A+/A/B/D/F 級距語。
>
> 把萃取結果整成一段 markdown，**先 AskUserQuestion 跟包子確認**才繼續。

**(b) `folder_structure.md` §「接到新作業時的開工 SOP」第 3 步（逐字）：**

```
### 3. 開工前的對齊確認

跟包子用 AskUserQuestion 確認以下事項：

- 評分標準的等第有哪些（A+/A/A-/B+/B/B-/C-/D/F 哪幾個）
- 寬鬆度與過去一致？（預設：是）
- 遲交處理：扣一級 還是 一律 C-？
- 未繳交給 F=0 還是 F=50？
- CSV 欄位用「等第」還是「分數」？（預設：等第）
- 預期繳交檔案總數？
```

### 6.2 【原文】`grading_policy.md` §七 的同一份清單（逐字）

```
## 七、必須在開始批改前向使用者確認的事

每次新作業都要先問清楚：

1. 評分標準的等第有哪些（A+/A/A-/B+/B/B-/C-/D/F 哪幾個）
2. 寬鬆度是否與過去一致（預設「是」）
3. 遲交處理：扣一級 還是 一律 C-
4. 未繳交給 F=0 還是 F=50
5. CSV 欄位用「等第」還是「分數」（預設等第）
6. 資料夾總檔案數（驗證讀取）

確認完才開始實際批改。
```

同一份清單在 `folder_structure.md` 與 `grading_policy.md` **重複出現兩次**（措辭略異）。

### 6.3 【原文】其他「不用 AskUserQuestion 但仍必須卡住對齊」的節點

| 節點 | 原文 | 卡點性質 |
|------|------|----------|
| Step 2 盤點檔案數 | 「向包子確認檔案總數對得上（過去經驗：HW2=266、HW3=249、HW4=280）。**對不上一定要找出原因**」 | 數字對帳，不對就不准往下 |
| Step 5 每批補掃後 | 「每批補掃完，列出 **成績異動清單**（學號、姓名、原成績、新成績、異動原因）給包子。」 | 主動回報，不是提問 |
| 遲交／補繳 | 「包子有時候會在批完後說『某某同學是遲交，幫我扣一級』或『某某同學不算遲交』，**要明確問清楚再動分數**。」 | 動分數前必問 |
| 等第命名 | 「包子在 HW2 一開始要求用 D / E，後來說『D 改 C-，E 改 F』。**之後的作業預設用 C-/F，但每次仍要再確認一次**。」 | 即使有預設值也要複問 |
| 等第 vs 分數 | 「包子在 HW4 一開始說『直接打分數』，後來改口『不要打分數，用等第』。**預設用等第**……除非使用者明確說『用分數』才用數字。」 | 有預設 + 明確覆寫條件 |
| 輸出檔完成後 | 「列出 D / F 的同學名單給包子看，他會說『啊這位他是遲交所以扣到 B-』之類的微調」 | 交件後預期會收到修正 |

### 6.4 【評註】卡點時機的抽象規則

從原文可以歸納出 **四個必卡點 + 一個不卡點** 的模式：

**必須 AskUserQuestion 卡住的四個時機：**

1. **讀完規格／標準之後、動手之前** —— 把「我理解的規格」整成一段 markdown 回讀給使用者確認。（Step 1）
2. **有多個合法選項且會影響全部輸出時** —— 每個問題都要附「（預設：X）」，讓使用者可以一句「都照預設」通過。（開工前 6 問）
3. **輸入數量與預期不符時** —— 檔案總數對不上、樣本數對不上、欄位數對不上。
4. **要修改已交付的結果時** —— 動分數／改數字前一定問清楚，即使使用者已經口頭說了（因為使用者的指令本身可能歧義，例如「遲交」是「扣一級」還是「一律 C-」）。

**明確不卡點、改為「主動回報」的時機：**
- 每批處理完的異動清單、最終分佈統計、D/F 名單 —— 這些是**推送資訊**而不是提問，讓使用者主動挑錯。原文措辭：「修分時要列『異動清單』回覆，**不要默默改掉**」。

**選項寫法慣例：** 每個問題都是「A 還是 B？」的二選一或短列舉，並在括號中給預設值。**不問開放式問題**（沒有「你想怎麼做？」這種）。

**新 skill 的等價卡點（建議）：**
1. 讀完資料集後，把「我看到的欄位／grain／筆數／期間」整成 markdown 回讀確認。
2. 分析口徑六問（要不要剔離群？遺漏值怎麼處理？時間窗多長？分群數固定還是自動選？指標定義用哪一版？輸出要 CSV 還是圖？），每問附預設值。
3. 筆數／金額總和與使用者預期不符時停下來對帳。
4. 要覆寫或重算已交付的結果前必問。

---

## 7. 與使用者互動的語氣規範

### 7.1 【原文】`SKILL.md` §「與包子互動的習慣」（逐字）

```
- 對話用繁體中文；包子的口氣偏直接、條列式
- 不要過度堆疊 bullet point
- 完成後用 `[View 檔名](computer://...)` 提供連結
- **學生申訴 → 預設可能漏掃**，先重檢再回覆
- 主動提供委婉的回信文字給包子轉發（見 `templates/appeal_reply_examples.md`）
- 修分時要列「異動清單」回覆，不要默默改掉
```

### 7.2 【原文】`grading_policy.md` §八 申訴處理 SOP（逐字）

```
學生申訴時（透過包子轉述），**先預設可能是漏掃**：

1. 立刻重看那位同學的檔案
2. 用「ZIP 解壓 + drawing XML + 提取所有圖片」方式徹底掃過
3. 如果發現確實漏掃 → 主動道歉並升等
4. 提供包子一段委婉的回信文字（兩三句話即可，見 `templates/appeal_reply_examples.md`）
5. 同時自我反省：這次漏掃的位置，其他同學會不會也有？是否要全面重掃？

不要直接告訴包子「他確實是 B 沒錯」，**先驗證再說**。
```

### 7.3 【原文】`templates/appeal_reply_examples.md` 的語氣規範（逐字）

```
當學生對成績有疑問、申訴，且查證後確認是 **我們漏掃** 或誤判時，幫包子寫一段委婉的回信文字（兩三句話即可）。語氣要：
- 主動承認疏失
- 不卸責
- 簡述「漏掃在哪裡」（如果學生有特別問）
- 告知已更正
```

末段（逐字）：

```
語氣的拿捏：**有錯就道歉、沒錯就溫和說明**，不要過度卸責也不要讓學生覺得被駁回。
```

### 7.4 【原文】對外回信範本（4 則，逐字保留）

**範例 1：圖片漏掃（HW3 學生I案）**

> 楊同學你好，非常抱歉，經過重新檢閱你的作業後，我們發現在批改過程中疏忽了你嵌入在 Excel 中的文字分析內容，導致成績有所低估。你的作業無論是自訂模型的設計理由、方法比較分析都非常完整且深入，成績已更正為 A+，再次為這次的疏失向你致歉。

**範例 2：文字方塊漏掃（HW3 學生O案）**

> 李同學妳好，感謝妳的來信。經重新檢閱後發現是我們在批改過程中的疏失，妳的第一題和第二題回答都非常完整且分析深入，成績已更正為 A+，很抱歉造成妳的困擾。

**範例 3：英文分頁名漏掃（HW4 Yat YEUNG 案）**

> Hi YAT, my apologies for the earlier mis-grading. Upon re-checking your file we found that both Q1 and Q2 are fully completed (CAI calculation plus the Differentiation Comparison and Summary tabs), and the issue was that our keyword scan missed the English-named sheets. Your grade has been updated to A+. Sorry again for the confusion.

> 中文版：你好，非常抱歉先前批改時誤判了你的作業。重新檢閱後我們發現你的第一題（CAI 計算）和第二題（活躍/不活躍分群比較，以 Differentiation Comparison 與 Summary 兩個分頁呈現）都完整完成，先前是因為我們的程式只搜尋中文關鍵字而未偵測到你以英文命名的分頁。成績已更正為 A+，再次為造成的困擾致歉。

**範例 4：確認沒漏掃但成績維持（學生R HW2 案）**

> 朱同學妳好，謝謝妳對成績的關注。我們已經再次仔細檢閱了妳的繳交檔案（PDF 與 XLSX 都包含完整的文字內容，沒有圖片漏掃的問題），確認 Q1 中（B）「最常使用」的尺度與（D）「最好不要使用」的尺度兩小題的答案與標準答案不同，因此整體判為 B。如果妳對作答內容仍有疑問，歡迎進一步討論。

範本結構固定為五段：稱謂 + 致謝／道歉 → 「經重新檢閱後」→ 具體指出對方寫了什麼／哪裡沒對 → 「成績已更正為 X」→ 再次致歉／歡迎討論。**注意性別代名詞（你／妳）依學生調整**，英文名學生給中英雙版。

### 7.5 【原文】給使用者的回報格式（`attendance_grading.md` §五，逐字）

```
最終結果：
- 到場 N 人
- 遲到 N 人
- 缺席 N 人

[檔案連結 1] 出席成績清單.xlsx
[檔案連結 2] 大數據行銷_成績登錄_實體課.csv

如有需修正請隨時告知。
```

### 7.6 【原文】輸出檔的最終檢查清單（`grade_recording.md` §四，逐字）

```
寫完之後務必：

1. 用 `csv.DictReader` 重讀一次自己寫的檔，確認欄位齊全
2. 計算各等第人數，跟批改時記下的人數對得上
3. 列出 D / F 的同學名單給包子看，他會說「啊這位他是遲交所以扣到 B-」之類的微調
4. 用 `[View 檔名](computer://...)` 提供連結
```

### 7.7 【原文】修正流程（`grade_recording.md` §五，逐字）

```
包子常會在最後說：「D 都改 C-」「E 改 F」「某同學要扣一級」。

修正流程：
1. 重讀 CSV
2. 用 pandas 或 csv 修改特定 row
3. 重寫，再產一份新 CSV（不要覆蓋舊的，保留 backup）
4. 列出修改清單回給包子確認
```

（注意這與 `attendance_grading.md` §四第 4 步「直接覆蓋舊檔」相反 —— 出席檔可覆蓋，成績檔要留 backup。）

### 7.8 【評註】語氣規範的可移植要點

1. **繁體中文、直接、條列式，但「不要過度堆疊 bullet point」** —— 這兩句同時存在是刻意的張力：使用者要條列式的**結構**，但不要每一句都變成 bullet。實務上意味著：一段散文說結論，然後用短表或 3–5 項清單放細節。
2. **檔案交付一定附連結**：`[View 檔名](computer://...)`（Windows 絕對路徑）。
3. **「先驗證再說」是最強的一條語氣規則**：使用者提出質疑時，預設是自己錯了，不要先辯解。這條可以原封不動搬到分析場景（使用者說「這個數字怪怪的」→ 先重算，不要先解釋方法論）。
4. **主動產出對外可轉發的文字**：批改場景是給學生的回信；分析場景的等價物是「給老師／老闆的一段結論摘要」或「投影片可貼的一句 takeaway」。這是很強的服務型行為，值得移植。
5. **任何改動都要列清單回覆，不准默默改**。
6. **回報格式固定為：數字摘要 → 檔案連結 → 一句邀請修正的收尾**（「如有需修正請隨時告知。」）。

---

## 8. 路徑與命名慣例、Windows／中文路徑處理

### 8.1 【原文】路徑書寫慣例四條（`folder_structure.md` §「路徑書寫慣例」，逐字）

```
寫路徑時：

- **跟包子對話用 Windows 路徑**：`C:\Users\User\Desktop\大數據行銷\HW3\`
- **`computer://` 連結用 Windows 路徑**：`computer://C:\Users\User\Desktop\...`
- **bash 內部用 Linux mount 路徑**：`/sessions/.../mnt/大數據行銷/HW3/`
- **Python 程式用 raw string 或 `pathlib.Path`** 避免 backslash 問題
```

### 8.2 【原文】命名規則（`folder_structure.md`，逐字）

```
### 作業資料夾

- **`HW{N}\`** — 大寫 HW，N 是阿拉伯數字（1, 2, 3, 4…）
- 不要用 `Homework_1`、`HW01`、`Hw3`、`第一次作業` 等變體
```

```
### 評分標準檔

包子的評分標準檔命名 **不一致**，要小心：

| 第 N 週 | 實際檔名 |
|---------|----------|
| 1 | 第一周作業評分標準.docx |
| 2 | 第2周作業評分標準.docx |
| 3 | 第三周作業評分標準.docx |
| 4 | 第四次作業評分標準.docx |

中文數字 vs 阿拉伯數字、「周」vs「次」交雜。**找檔案要用 fuzzy match**（regex `第.*?(周|次).*?評分標準\.docx`），不要寫死命名。
```

```
### 成績輸出

固定兩種命名：

| 用途 | 檔名 | 位置 |
|------|------|------|
| 內部記錄 | `HW{N}_成績.csv` | `HW{N}\` |
| 寬鬆版備份 | `HW{N}_成績_寬鬆版.csv` | `HW{N}\` |
| Cool 匯入 | `大數據行銷_成績登錄_HW{N}.csv` | `匯入用檔案\` |
| 實體課 Cool 匯入 | `大數據行銷_成績登錄_實體課.csv` | `匯入用檔案\` |
```

```
### Cool 原始檔（包子定期會更新）

{YYYY-MM-DD}T{HHMM}_成績-大數據行銷_(IB5082).csv

範例：`2026-04-12T0649_成績-大數據行銷_(IB5082).csv`。每次包子重新匯出就會多一個。**讀 Cool 原始檔時，永遠用最新的時間戳**
```

```
### 實體簽到資料夾

第{N}次實體簽到\
├── 出席成績清單.xlsx              ← 包子自己整理的名單
├── 待確認簽到截圖\                ← 補簽到的截圖證據
└── 手寫_{YYYY-MM-DD}_{HHMMSS}.pdf  ← 簽到單掃描
```

開頭段落的總則（逐字）：「包子的資料夾組織方式有自己一套習慣命名。這份文件記錄目前的結構，每次接到新工作（新作業、新一次簽到、新匯入需求）時要 **完全沿用** 這套命名規則，不要自創縮寫或英文化。」

### 8.3 【原文】命名慣例可歸納的規則

| 規則 | 原文依據 |
|------|----------|
| 資料夾與輸出檔名一律**中文**，不英文化 | 「不要自創縮寫或英文化」；`準時\`、`遲交\`、`補交\`、`匯入用檔案\`、`Cool 原始檔案\`、`作業分配\`、`第{N}次實體簽到\` |
| 專案內部檔（SKILL/references/scripts）一律**英文 snake_case** | `course_context.md`、`extract_xlsx_content.py`、`validate_folder_structure.py` |
| 輸出檔用**底線分段**：`<領域>_<用途>_<批次>.csv` | `大數據行銷_成績登錄_HW4.csv`、`HW4_成績_寬鬆版.csv` |
| 批次識別碼用 `HW{N}` / `第{N}次` 的 placeholder 寫法 | 文件中大量出現 `HW{N}`、`第{N}周`、`{YYYY-MM-DD}` |
| 時間戳格式 `YYYY-MM-DDTHHMM`（ISO 無秒）或 `YYYY-MM-DD_HHMMSS` | `2026-04-12T0649_...`、`手寫_2026-03-30_224432.pdf` |
| 目錄樹寫在文件裡時，資料夾後面**加反斜線**：`準時\` | 全文一致 |
| 變體版本用 `_寬鬆版` 後綴，不用 `_v2` | `HW3_成績_寬鬆版.csv` |
| 備份用日期後綴資料夾：`_補交批改備份_20260619\` | 實際存在的目錄（YYYYMMDD 無分隔） |

### 8.4 【原文】常見地雷（`folder_structure.md` §「常見地雷」，逐字）

```
1. **`~$lock` 暫存檔**：包子如果剛打開過某份 xlsx，資料夾裡會多出 `~$xxx.xlsx` 隱藏檔，掃描時要 skip
2. **macOS 元資料**：`.DS_Store`、`._xxx` 開頭檔，掃描要 skip
3. **檔名大小寫**：學號的 B/b 大小寫不一致，比對前先 `.lower()`
4. **檔名空白**：有些學生檔名含 `(1)`、`(2)`、`(YAT YEUNG)` 等括號，regex 要包容
5. **重複繳交**：同一學號多份檔案，取最新時間戳的版本
6. **Cool 名單包含旁聽生與測試帳號**：不在繳交資料夾的不一定是「未繳交」，要過濾 18 位左右的非修課人員（HW4 經驗）
```

### 8.5 【評註】中文／Windows 路徑處理的實作要點

原文的規範是對的但不完整，以下是本次執行環境下應補的實作細節：

1. **Bash（Git Bash）** 中文路徑可用，但**必須雙引號**：`"C:/Users/User/Desktop/大數據行銷/HW4"`。用正斜線比反斜線安全（反斜線在 POSIX shell 是轉義字元）。`mkdir -p "路徑"` 建含中文與空白的深層目錄可行。
2. **PowerShell 5.1** 對含中文路徑基本可用，但 `Set-Content`／`Add-Content` 預設寫入 ANSI（cp950），寫給其他工具讀的檔**必須** `-Encoding utf8`；`>` 與 `Out-File` 在此環境多半是 UTF-8 with BOM。PowerShell 5.1 **沒有** `&&`、`??`、`?.`、三元運算子，鏈式命令要用 `A; if ($?) { B }`。
3. **Python** 在 Windows 上 `open()` 的預設編碼是 locale（cp950），**所有** `open()` 都要顯式 `encoding=`。`os.path` 與 `pathlib` 對中文路徑無礙。`subprocess` 傳中文路徑用 list 形式（不要拼字串）。
4. **`--root` 預設值寫法**沿用原文：`default=r'C:/Users/User/Desktop/...'`（raw string + 正斜線），這個組合在 Windows Python 與跨環境都成立。
5. **既有腳本缺 stdout 重設**（見 §5.12 第 5 點），新 skill 的每支腳本檔頭都應補上。
6. **兩套路徑環境的判別**：如果 skill 可能在 Cowork Linux sandbox 執行，腳本不要寫死任一種，改為讀環境變數或 `--root`，並在 reference 中同時列 Windows 與 mount 兩種樣本路徑（原文 §8.1 已做到）。

---

## 9. templates/ 的粒度慣例

### 9.1 【原文】兩個 template 檔

**`grade_csv_template.csv` 全文（逐字，114 bytes）：**

```csv
學號,姓名,等第
B12702068,學生R,B
B12702113,學生M,B-
41183903I,學生S,A+
學號001,某同學,A
```

只有 header + 4 列**真實範例資料**（含跨校前綴與匿名列 `學號001,某同學,A`）。不是空模板。

**`appeal_reply_examples.md`（2503 bytes / 31 行）結構：**

```
# 給學生的委婉回信範例
（一段語氣規範：主動承認疏失 / 不卸責 / 簡述漏掃在哪 / 告知已更正）
---
## 範例 1：圖片漏掃（HW3 學生I案）      ← blockquote 放整段可直接複製的文字
## 範例 2：文字方塊漏掃（HW3 學生O案）
## 範例 3：英文分頁名漏掃（HW4 Yat YEUNG 案）  ← 英文 + 中文兩版
## 範例 4：確認沒漏掃但成績維持
（末段：語氣的拿捏一句話）
```

### 9.2 【評註】templates 的粒度規則

1. **template = 「可直接複製貼上的成品」**，不是骨架、不是佔位符。CSV template 直接給真名真等第；回信 template 給整段可轉發的文字。
2. **每個 template 都標註它來自哪個真實案例**：`（HW3 學生I案）`、`（HW4 Yat YEUNG 案）`。這讓使用者能判斷「我這次的情境像哪一個」。
3. **含一個「反向案例」**：範例 4 是「查證後沒錯，怎麼溫和說明」。正反都給，避免 agent 只會道歉。
4. **範本檔開頭與結尾各夾一句語氣規範**（開頭列 4 點要求、結尾一句拿捏原則）。
5. 新 skill 的 templates 建議至少 3 檔：輸出檔範例（含真實數據的 CSV 或 xlsx 欄位表）、對外結論摘要範本（含「有發現／沒發現」正反兩版）、分析工作日誌範本。

---

## 10. 工作日誌／對話紀錄檔的格式

### 10.1 【原文】`HW4_批改對話紀錄.md` 的結構骨架

```
# HW4 批改對話紀錄

**日期**：2026-06-17
**課程**：NTU IB5082 大數據行銷
**作業**：HW4 — 03_顧客價值的解析與策略運用：ARFM模型\_作業2
**批改者**：助教包子

---

## 作業說明（評分標準）
來源：`第四次作業評分標準.docx`
（題目列表）
**評分標準**：（等第 | 條件 兩欄表）
**批改基調**：（一句話）
**CAI 標準計算流程（參考 CAI範例.xlsx）**：（Step 0 → Step 5 用兩空格換行連寫）

---

## 批改結果總覽
**繳交人數**：245 人（準時）
**無繳交（F）**：34 人
**總計**：279 人（排除測試帳號）
（等第 | 人數 | 說明 三欄表）

---

## 特殊案例說明
### C 或以下的同學
#### <學號> <姓名> → <等第>
- 檔案內容：...
- 問題：...
- 判定：...
### 需特別說明的 A- 同學
### 特別確認後改為 A+ 的同學
#### <學號> <姓名>
- **原狀況**：...
- **確認方式**：用 pdftoppm 轉圖後逐頁確認
- **內容**：...
- **結論**：A+
（最後一個 #### 把多位同類案例併成一條）

---

## 無繳交同學（F）清單（34 人）
（學號+姓名 用「、」串成一段，不換行）

---

## 輸出檔案
（檔案 | 路徑 | 用途 三欄表）

---

*本紀錄由 Claude（Cowork 模式）自動批改，批改日期：2026-06-17*
```

### 10.2 【原文】關鍵欄位寫法（逐字節錄）

評分標準表：

| 等第 | 條件 |
|------|------|
| A+ | 有繳交，計算過程完整無誤，兩題都完成 |
| A- | 有繳交，計算過程有誤（跳步驟/用錯函數），兩題都完成 |
| B+ | 有繳交，計算過程完整無誤，但僅完成第一題 |
| B- | 有繳交，計算過程有誤，且僅完成第一題 |
| C  | 遲繳 |
| D  | 有繳交但無計算過程，直接貼結果 |
| F  | 無繳交 |

方法流程（逐字，注意用行尾兩空格換行）：

```
**CAI 標準計算流程（參考 CAI範例.xlsx）**：
Step 0 → 篩選每位客戶的交易紀錄
Step 1 → 去除重複產業，保留唯一日期
Step 2 → 計算 int（交易間隔天數）
Step 3 → 加入 weight（第幾筆交易）與 int × weight
Step 4 → 樞紐分析：平均 int、加總 weight、加總 int×weight
Step 5 → 計算 MLE、WMLE、CAI
```

結果總覽表：

| 等第 | 人數 | 說明 |
|------|------|------|
| A+  | 238  | 第一、二題完整 |
| A-  | 3    | 有嘗試但方法略有不足 |
| B+  | 2    | 僅完成第一題 |
| B-  | 1    | 計算有誤，且僅完成第一題 |
| D   | 1    | 有繳交但無標準 CAI 計算過程 |
| F   | 34   | 無繳交 |

單一案例的逐字樣本（誤判修正型）：

```
#### T14704118 Yat YEUNG
- **原判 B+**（自動掃描未偵測到 Q2）
- **實際內容**：全英文命名，Differentiation Comparison 分頁含 100 位客戶完整 CAI 排名 + 年齡/性別/婚姻/職業等特徵；Summary 分頁有 Gradually Active / Steady / Gradually Unactive 三群體比較 + 英文 Insights
- **誤判原因**：自動掃描只搜尋中文關鍵字，全英文分頁名未被偵測
- **結論**：改為 A+
```

輸出檔案表：

| 檔案 | 路徑 | 用途 |
|------|------|------|
| HW4\_成績.csv | `大數據行銷/HW4/HW4_成績.csv` | 學號、姓名、等第、備註 |
| 大數據行銷\_成績登錄\_HW4.csv | `大數據行銷/匯入用檔案/` | Cool 匯入用，直接上傳 |

（注意檔名中的底線被轉義成 `\_`，因為這份 md 預期給 Notion／Markdown 渲染器讀。）

### 10.3 【評註】工作日誌的作用與移植

這份檔案放在 skill 根目錄（不在 references/），檔名格式 `HW{N}_批改對話紀錄.md`。它的作用不是給 agent 讀規則，而是**單次執行的可審計紀錄**：規格是什麼、結果分佈、每個非典型案例的判斷理由與證據、產出檔位置、誰在什麼時候做的。

這正是 references 中案例庫（`text_extraction.md` 的失敗案例表、`course_context.md` 的歷史決策表）的**原料來源** —— 先寫日誌，再把重複出現的教訓升級進 reference。

新 skill 應建立同樣的機制：
- 檔名 `<批次>_分析紀錄.md`（例：`2026Q3_客群分析紀錄.md`）
- 骨架：中繼資料 → 需求／規格（含使用者確認過的口徑）→ 結果總覽（表）→ 特殊案例／異常值說明（每個附證據與判斷）→ 排除清單 → 輸出檔案表 → 署名行
- 署名行沿用格式：`*本紀錄由 Claude（Cowork 模式）自動<動作>，<動作>日期：YYYY-MM-DD*`

---

## 11. lecture-to-notion 的格式差異（另一套風格對照）

### 11.1 【原文】lecture-to-notion 特有、作業批改沒有的六個元素

**(a) 角色設定段（`## 你在做什麼`，逐字）：**

> 你是一個資深補教團隊的名師，正在把教授的上課素材轉化成一份學生可以直接拿來讀、拿來考試的完整講義。你的目標不是「翻譯投影片」，而是「讓學生真正理解每個概念」。

**(b) 素材權威層級聲明（逐字）：**

> 1. **PDF 講義**（教授的投影片）：這是主要知識骨架，但投影片通常有跳步、省略、只放圖沒解釋的問題
> 2. **Markdown 筆記**（使用者自己整理的）：這是補充素材，裡面可能有白話解釋、額外整理、個人觀點
>
> 兩者都要仔細讀完再開始寫。PDF 是權威來源（定義、公式、例子不能改），Markdown 筆記是風格參考和補充資訊。

**(c) 「不要急著動筆」的節流指令（逐字）：**

```
### 第一步：完整讀取所有檔案

1. 先用 `ls` 確認資料夾中有哪些檔案
2. 用 Read tool 讀取所有 PDF（每次最多 20 頁，大的 PDF 要分批讀）
3. 用 Read tool 讀取所有 Markdown（大檔案分段讀取，用 offset + limit）
4. **不要急著動筆** —— 全部讀完後再開始規劃架構
```

**(d) 格式規範 + 負面清單（逐字）：**

```
1. **數學式**：
   - 行內數學：`$...$`（例如 `$P(A|B)$`）
   - 區塊數學：`$$...$$`（獨立一行，前後各空一行）
   - **絕對不要用** `\[...\]` 或 `\(...\)` 格式，Notion 不支援
   - 使用標準 KaTeX 語法（`\frac`, `\sum`, `\prod`, `\arg\max`, `\log`, `\vec`, `\|...\|` 等）

2. **標題層級**：
   - `#` 大章節（如「Naive Bayes 分類器」）
   - `##` 中章節（如「訓練流程」）
   - `###` 小節（如「為什麼要 Smoothing？」）
   - `####` 細項（較少使用）

3. **引用區塊** `>`：用於白話說明或重要提醒
4. **粗體** `**...**`：用於專有名詞第一次出現時
5. **表格**：用 Markdown 表格語法，Notion 可以直接渲染
6. **分隔線** `---`：用於大章節之間
```

```
### 絕對不要出現的東西

- LaTeX 專用語法（如 `\begin{align}`、`\text{}`、`\label{}`）
- HTML 標籤
- Notion 不支援的 Markdown 擴展語法
```

**(e) 三層結構寫作法（核心方法論，含 LaTeX 公式範例，逐字）：**

第一層寫法範例：

```
**貝氏定理（Bayes' Rule）** 描述了在觀測到證據 $X$ 後，假設 $C$ 的後驗機率如何從先驗機率更新而來：

$$
P(C|X) = \frac{P(X|C) \cdot P(C)}{P(X)}
$$

其中 $P(C)$ 為先驗機率，$P(X|C)$ 為似然函數，$P(X)$ 為邊際機率（正規化常數）。
```

第三層寫法範例：

```
> 白話來說，貝氏定理就是在問：「我本來覺得這封信有 30% 機率是垃圾信，但現在我看到裡面有 "免費" 和 "點擊" 這些詞，那我該把垃圾信的機率往上調多少？」先驗就是你原本的直覺，看到證據後更新的結果就是後驗。
```

語氣分流表（逐字）：

```
- **數學/統計/ML 類**：像學長解題，可以用「你可以想成...」「簡單來說就是...」「為什麼？因為...」
- **文科/社會科學類**：像說故事，可以用更多比喻和情境
- **工程/程式類**：像 code review，可以用「這段的意思其實就是...」「你把它想成 function 就對了」
- **醫學/生物類**：像看病解釋，可以用身體運作的比喻
```

**(f) 大型任務的分段／委派策略 + 機械化驗收（逐字）：**

```
如果素材內容很多（例如超過 40 頁 PDF），不要試圖一次寫完。建議：

1. 根據知識地圖，將講義分成 2-4 個 Part
2. 每個 Part 分別用 Agent tool 撰寫（可以平行執行以節省時間）
3. 最後用 bash `cat` 合併成一份完整檔案
4. 合併後做最終檢查
```

```
當你把撰寫任務委派給 Agent 時，prompt 中要包含：

1. **角色設定**：「你是一個資深補教團隊的名師」
2. **格式要求**：「Notion markdown，行內 $...$，區塊 $$...$$」
3. **風格要求**：「三層結構：正式定義 + 詳細解釋 + 白話說明」
4. **具體要寫的章節大綱**：詳細列出每個小節應包含的內容
5. **素材中的關鍵資訊**：把相關的 PDF 內容和 Markdown 筆記的重點整理給 Agent
```

```
### 最終輸出

1. 將合併後的完整檔案存到使用者的工作資料夾
2. 用 `grep` 快速檢查：
   - 沒有 `\[` 或 `\]` 的不相容數學格式
   - 有足夠數量的 `$$` 區塊數學式
   - 有足夠數量的 `$` 行內數學式
3. 用 `wc -l` 確認檔案行數合理（一份完整講義通常 1000-4000 行）
4. 提供 `computer://` 連結讓使用者直接存取
```

**品質檢查清單（逐字，`- [ ]` 勾選框）：**

```
- [ ] 所有 PDF 中的核心概念都有涵蓋嗎？
- [ ] 所有 Markdown 筆記中的補充內容都有整合嗎？
- [ ] 每個重要概念都有三層結構嗎？
- [ ] 數學式都用 KaTeX 格式嗎？沒有 `\[...\]`？
- [ ] 投影片上只簡單帶過的方法論，有補充到合理深度嗎？
- [ ] 有範例計算嗎？
- [ ] 有比較表嗎？
- [ ] 章節之間的銜接順暢嗎？
- [ ] 白話說明的口吻一致嗎？
```

### 11.2 【原文】兩套 Skill 的格式差異對照

| 面向 | 大數據行銷作業批改 | lecture-to-notion |
|------|-------------------|-------------------|
| name 語言 | 中文 | 英文 kebab-case |
| description | 單行長句 | `\|` block scalar，含 `MANDATORY TRIGGERS:` |
| 角色設定 | 無（只說「這 skill 是給包子用的」） | 有（「你是一個資深補教團隊的名師」） |
| h2 編號 | 無編號名詞短語 | 無編號名詞短語（相同） |
| 流程步驟標題 | `### Step N — 動作` | `### 第一步：動作` |
| references | 6 檔外掛 | 無（全塞 SKILL.md） |
| scripts | 5 支 Python | 無（只用 ls / grep / wc / cat） |
| ASCII 圖 | 大量（檔案地圖、目錄樹、決策樹、流程圖） | 無 |
| 表格 | 大量 | 少（只有語氣分流表） |
| 負面清單 | 散在 references | 獨立成節「絕對不要出現的東西」 |
| 品質檢查清單 | 散在各 reference 末（「最終檢查清單」） | 獨立成節，用 `- [ ]` |
| 委派子 agent | 無提及 | 有（Agent tool + prompt 五要素） |
| 機械化驗收 | csv.DictReader 重讀 + 人數對帳 | grep 檢查格式 + wc -l 檢查行數 |
| 卡點確認 | AskUserQuestion（明文兩處） | 無（「不要急著動筆」是自我節流，不問使用者） |
| 案例／歷史庫 | 有（漏掃案例表、決策時序表） | 無 |
| 交付連結 | `[View 檔名](computer://...)` | 「提供 `computer://` 連結」 |

### 11.3 【評註】哪些差異該吸收、哪些該捨棄

**新 skill 應同時吸收兩邊的優點：**

| 從作業批改拿 | 從 lecture-to-notion 拿 |
|--------------|-------------------------|
| references/scripts/templates 三層拆分 | 角色設定段（讓 agent 進入正確的專業人格） |
| ASCII 檔案地圖與流程圖 | 素材權威層級聲明（哪個來源不可改、哪個只是參考） |
| 「情境 → 動作」入口指引表 | 「不要急著動筆」的節流指令 |
| AskUserQuestion 卡點清單 | 獨立的「絕對不要出現的東西」負面清單 |
| 失敗案例庫 reference | 獨立的 `- [ ]` 品質檢查清單 |
| 「一句話核心原則」節 | 大型任務分段 + 委派子 agent 的 prompt 五要素 |
| 工作日誌檔機制 | 機械化驗收（用 grep / wc 客觀檢查自己的產出） |

**捨棄：** lecture-to-notion 沒有 references/scripts 的單檔形態不適用（新 skill 是長期營運型）。

**行銷分析的等價物：**
- 角色設定 → 「你是一個做過很多次客群與行銷成效分析的資料分析師，服務對象是台大國企所的包子。你的目標不是產出一堆圖，而是讓包子能拿著結論去做決策／交報告。」
- 素材權威層級 → 「原始資料表是權威來源（數字不能改、口徑不能私自調整）；包子的舊分析檔／講義是口徑參考與風格參考。」
- 負面清單 → 「絕對不要出現的東西」：憑印象給數字、沒說樣本數的百分比、沒標單位的軸、把相關講成因果、預設剔除離群值而不說。
- 機械化驗收 → 用程式重算一次關鍵數字並比對、檢查百分比加總為 100%、檢查圖檔都存在、檢查輸出 CSV 列數等於預期。

---

## 12. 【評註】scripts 對新「行銷分析 Skill」的可重用性評估

評估基準：新 skill 的工作型態推定為「讀進本地資料檔（CSV/XLSX，可能還有 PDF 產業報告與 SPSS/R 輸出）→ 驗證 → 分析／建模 → 產出圖表與結論檔」。

### 12.1 逐支評估

| 腳本 | 可重用度 | 判斷 | 具體做法 |
|------|----------|------|----------|
| `validate_folder_structure.py` | **★★★★★ 直接改寫，最高價值** | 骨架與領域無關：三桶收集（info/warnings/errors）+ 全形破折號的「事實 — 動作」訊息 + emoji + exit code 0/1/2 + fuzzy match + junk 過濾 | 改名 `validate_project_inputs.py`。檢查項換成：專案根目錄存在／資料檔存在（fuzzy match 檔名）／資料檔非空且可讀／欄位含必要欄／輸出目錄存在／`~$`鎖檔與`.DS_Store`清單／編碼可解。保留退出碼語意，讓 agent 依 code 決定是否停下 |
| `setup_new_hw.py` | **★★★★★ 直接改寫** | 冪等建目錄 + 「接下來請包子做的事」交棒清單 + 主動指出下一支腳本，這三點是完整可搬的 pattern | 改名 `setup_new_analysis.py <批次代號>`。建立 `01_raw/ 02_clean/ 03_output/ 04_figures/` 之類標準結構，末尾印出「1. 把原始資料放到 …  2. 確認 … 3. 完成後執行 validate_project_inputs.py」 |
| `extract_pdf_content.py` | **★★★★☆ 幾乎原封可用** | 讀產業報告／論文／老師講義 PDF 時直接可用。JSON 輸出、`--text-threshold`、圖片型 fallback 都通用 | 修掉 §5.12 第 1 點的條件式 bug；加 Windows stdout 重設；把 `--image-dir` 改為只在 `is_image_pdf` 時才轉圖（省時間與 token）；若本機無 poppler，需改用 `pypdf` / `pdfplumber` 或先安裝 poppler |
| `auto_grade.py`（一次性） | **★★★★☆ 高度可改寫（pattern 而非程式碼）** | 它的價值不在 SPSS 關鍵字，而在整套「規則式分類器 + 人工複核旗標」架構 | 抽出 5 個可搬元素：(1) `_PATTERNS` 模組層級常數字典（中英混列、含變體）；(2) `detect_keywords()` 子字串比對；(3) **閾值化布林**（`>=2` 才算命中，避免單字誤觸）；(4) **`NEEDS_VISUAL` 逃生門旗標**；(5) **回傳「判斷 + 命中證據（截斷前 8）」**。在行銷分析可改成：欄位語意自動歸類器（把欄名／值 sample 對到 R/F/M/客群/通路/金額/日期）、資料品質檢核器（回傳問題 + 證據列號）、報告完整性檢核器 |
| `extract_xlsx_content.py` | **★★★☆☆ 部分重用，需重寫核心** | 六位置全掃的思路對「讀懂客戶／老師給的 xlsx」極有用（尤其 drawing 文字方塊與嵌入圖片常藏著欄位說明與口徑備註）；但雙 `load_workbook` 不設 `read_only` 的實作對大資料檔會爆記憶體 | 拆成兩支：(a) `inspect_xlsx.py`（結構偵察：sheet 清單含隱藏、每 sheet 的 used range、前 N 列預覽、偵測 header 列位置、drawing 文字方塊、嵌入圖片清單、comment）→ 用 `read_only=True` 掃格子、另開一般模式只掃 comment 與 drawing；(b) 實際載入資料用 `pandas.read_excel(sheet_name=..., header=...)`。**保留** `extract_textboxes()` 與 `extract_images()` 兩函式原樣（純 zipfile，與檔案大小無關） |
| `parse_filename.py` | **★★☆☆☆ 程式碼不可用，pattern 可用** | `PATTERN` 綁死 NTU Cool 檔名（`<sid>#_<name>_<id1>_<id2>_...`），行銷分析用不到 | 但三個 pattern 可搬：(1) 一個模組層級 `re.compile` 的具名群組 PATTERN；(2) `parse()` 失敗回 `None`，掃資料夾時失敗項仍進結果陣列並標 `{'parse_failed': True}`（**不靜默丟棄**）；(3) 互斥群組 CLI（單檔 or `--dir` 整批）。可改成解析資料檔名的批次／期間／版本（例：`銷售明細_2026Q2_v3.csv`） |
| `templates/grade_csv_template.csv` | **★★★★☆ 概念直接可用** | 「給真實範例列而非空模板」的做法可搬 | 改成 `output_csv_template.csv`：header + 3–4 列真實範例（含各種邊界：跨校前綴等價的特殊值、空值表示法、小數位數） |

### 12.2 完全缺、需要為新 skill 新寫的腳本

既有五支腳本沒有涵蓋分析型工作的三個關鍵環節，這是新 skill 必須補的：

1. **`profile_dataset.py`（資料剖析）** —— 對每個 CSV/XLSX 輸出：列數、欄數、每欄 dtype 推定、遺漏值比例、唯一值數、數值欄的五數摘要、類別欄的 top-10 值與占比、日期欄的 min/max、疑似 ID 欄、疑似重複列數。輸出 JSON to stdout（沿用 `ensure_ascii=False, indent=2`）＋ 一份人眼看的分隔線報表（沿用 `'=' * 60`）。**這是 AskUserQuestion 第一個卡點的原料。**
2. **`check_data_quality.py`（品質檢核）** —— 沿用 `validate_folder_structure.py` 的三桶 + exit code：errors（無法分析：關鍵欄缺失、編碼壞、grain 不唯一）／warnings（可繼續但要說明：遺漏值 >20%、離群值、日期跨界）／info（通過項）。
3. **`verify_outputs.py`（機械化驗收，取自 lecture-to-notion 的 grep/wc 精神）** —— 檢查：輸出 CSV 列數 == 預期、百分比欄加總 ≈ 100、圖檔都存在且非 0 bytes、報告中提到的每個數字都能在輸出 CSV 找到、沒有 `NaN`／`#DIV/0!`／`inf` 洩漏到交付檔。

### 12.3 必須在新 skill 中一併沿用的三個「非程式」資產

1. **`norm()` 函式**（NFKC + lower + strip）—— 行銷分析比對欄名、類別值、產業名稱時同樣必要（全形／半形、大小寫、前後空白是台灣資料集的日常災難）。
2. **`utf-8-sig` 寫 CSV 的鐵則**（「讓 Excel 開不會亂碼」）—— 包子最終是在 Excel 開檔，這條不能省。
3. **junk file 過濾三件套**（`~$` / `._` / `.DS_Store`）—— 掃資料目錄計數時同樣要排除，否則「檔案數對不上」。

---

## 13. 可重用資產（可直接寫進新 Skill）

### 13.1 SKILL.md frontmatter 範本

```yaml
---
name: <中文 skill 名稱>
description: |
  <一句定位：這 skill 是什麼、給誰、產出什麼>。<第二句：它負責哪些具體任務，用「、」串接>。
  MANDATORY TRIGGERS: 任何涉及「<口語句 1>」、「<口語句 2>」、「<口語句 3>」的請求都應觸發此 skill。使用者上傳 <檔案型別清單> 時同樣觸發。即使使用者沒有明確說「<關鍵詞>」，只要是<抽象需求描述>的需求，都適用。
---
```

### 13.2 SKILL.md 段落骨架（依序，可逐節照填）

```
# <名稱> Skill
> <一行副標>
<一段定位散文：這 skill 是給誰用的、它自己就是什麼工作流程>

## 你在做什麼                      ← 角色設定（第二人稱，來自 lecture-to-notion）
## 何時載入這個 Skill              ← 口語 bullet
## 內建 Skill 檔案地圖              ← ASCII 樹 + ← 註解
## 輸入素材與權威層級                ← 哪個來源不可改、哪個只是參考
## <領域>基本資料（速查）            ← 兩欄表
## 工作根目錄的標準結構              ← ASCII 樹 + ← 註解
## <主流程>的 N 步流程
    （先列「開工前務必先讀」的 references，格式：編號 + `路徑` + — + 讀它為了確認什麼）
    ### Step 1 — <動詞短語>
    ...
## <核心原則>（一句話）
## 絕對不要出現的東西                ← 負面清單
## 與包子互動的習慣
## 工作流程摘要圖                    ← ASCII
## 不同情境的入口指引                ← 兩欄表「包子說的 | 你該做的」
## 品質檢查清單                      ← - [ ] 勾選框
```

### 13.3 CLAUDE.md 範本（30 行 / 1.5 KB 上限）

```markdown
# <名稱> — 工作目錄速查

這個資料夾是 **<領域／專案>** 的<用途>工具包，給<使用者>（<email>）用。

## 開工前必讀

1. **`SKILL.md`** — 完整流程總覽（<N>步流程、觸發條件、檔案地圖）
2. **`references/<最關鍵那份>.md`** — <一句話>（必讀，<為什麼必讀>）
3. **`references/<第二份>.md`** — <一句話>
...

## 工作根目錄

```
<Windows 絕對路徑>
```

底下有 <主要子目錄列舉>。詳細位置在 `references/folder_structure.md`。

## 觸發本 skill 的關鍵字

<關鍵字、關鍵字、關鍵字…>。

## <核心原則>（一句話）

<三個短句，每句一個句號。>
```

### 13.4 references 切分決策規則（檢查清單）

- [ ] 每份 reference 對應**一個問句**，且問句彼此不重疊
- [ ] 六份問句齊備：領域固定事實／路徑命名／判斷規則／輸入技術+踩雷庫／輸出規格／旁支流程
- [ ] 每份 **4–9 KB、110–230 行**（超過就切，不足就併）
- [ ] 每份 h1 之後有一段「為什麼這份文件重要」的散文，帶後果警語
- [ ] h2 用中文數字編號（`## 一、`）或名詞短語，不用英文
- [ ] 每節以**表格或程式碼區塊**收尾，不以純散文結束
- [ ] 至少一份是**失敗案例庫**（具名個案 / 錯在哪個技術位置 / 修正後結果）
- [ ] 至少一份有**歷史決策時序表**（時間 | 事件 | 影響）
- [ ] 末尾有**維護條款**（「如果使用者改了習慣，這份文件要立刻更新，並保留舊寫法向後相容」）
- [ ] references 沒有 YAML frontmatter

### 13.5 Python 腳本骨架範本（把包子的風格固化）

```python
#!/usr/bin/env python3
"""
<一句話說明這支腳本做什麼>（繁體中文）

<處理的位置／情境，縮排數字清單>
  1. ...
  2. ...

用法：
    python <script>.py <arg>
    python <script>.py <arg> --root "C:/Users/User/Desktop/<專案>"   # 中文註解

依賴：
    <外部工具或套件>

輸出（stdout，JSON）：
{
  "key": ...,
}

退出碼：
  0 = 全部 OK
  1 = 有警告但可繼續
  2 = 嚴重錯誤需處理
"""
import argparse
import json
import os
import re
import sys
import unicodedata

if sys.platform == 'win32':                      # ← 既有腳本缺這段，新 skill 必加
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def norm(s: str) -> str:
    return unicodedata.normalize('NFKC', s).lower().strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target')
    ap.add_argument('--root', default=r'C:/Users/User/Desktop/<專案>')
    ap.add_argument('--out-dir', default=None, help='若提供，把產出寫到這個資料夾')
    args = ap.parse_args()

    info, warnings, errors = [], [], []
    # ... 檢查與處理 ...

    print('=' * 60)
    print(f' <報表標題>')
    print('=' * 60)
    for line in info:
        print(line)
    for line in warnings:
        print(line)
    for line in errors:
        print(line)
    print('=' * 60)

    if errors:
        print(f'⛔ 有 {len(errors)} 項嚴重問題')
        sys.exit(2)
    if warnings:
        print(f'⚠ 有 {len(warnings)} 項警告但可繼續')
        sys.exit(1)
    print('🎉 所有檢查通過，可以開始<下一步>')
    sys.exit(0)


if __name__ == '__main__':
    main()
```

### 13.6 程式風格硬規則清單

- [ ] `#!/usr/bin/env python3` + 中文 docstring（含「用法」「依賴」「輸出」「退出碼」四節，視適用性取用）
- [ ] import：標準庫字母序一行一個 → 空行 → 第三方
- [ ] `ArgumentParser()` 不傳 description（說明全在 docstring）；變數名 `ap`
- [ ] 選項用 kebab-case（`--media-dir`），每個都有中文 `help=`
- [ ] Windows 路徑預設值用 `default=r'C:/Users/.../專案'`（raw string + 正斜線）
- [ ] 不用 logging，全部 `print()`
- [ ] 外部工具缺失／超時 → **靜默降級回傳空值**（`except FileNotFoundError: return ''`）
- [ ] 單項失敗 → `except Exception: continue`，不中斷整批
- [ ] 錯誤打包進回傳 dict 的 `'error'` key，所有 extractor **回傳同一組 key**
- [ ] 錯誤訊息格式：`<emoji> <事實> — <祈使句動作>`，破折號用全形 `—`
- [ ] emoji 語意：`✅` 通過／`⚠` 警告／`❌` 錯誤／`⛔` 總結有錯／`🎉` 全通過
- [ ] 建立型腳本冪等：已存在則 `⚠ ... 已存在 — 不覆蓋`
- [ ] 建立型腳本末尾印「=== 接下來請包子做的事 ===」+ 下一支要跑的腳本
- [ ] 退出碼 0/1/2 語意固定
- [ ] JSON to stdout：`json.dump(out, sys.stdout, ensure_ascii=False, indent=2)`
- [ ] 人眼報表：`print('=' * 60)` 包夾，順序 **info → warnings → errors**
- [ ] 一次性腳本放專案 outputs 區並寫死路徑；只有跨次都用得到的才升級進 `scripts/`

### 13.7 編碼處理規則表（照抄可用）

| 場景 | 寫法 |
|------|------|
| 寫給 Excel 開的 CSV | `open(p, 'w', encoding='utf-8-sig', newline='')` |
| 讀 Excel 產出的 CSV | `open(p, 'r', encoding='utf-8-sig')` |
| 讀來源不明的文字檔 | `open(p, 'rb').read().decode('utf-8', errors='ignore')` |
| 讀 ZIP 內 XML | `z.read(n).decode('utf-8', errors='ignore')` |
| subprocess 取文字 | `subprocess.run([...], capture_output=True, text=True, timeout=60).stdout` |
| JSON 輸出 | `ensure_ascii=False, indent=2` |
| JSON 寫檔 | `open(p, 'w', encoding='utf-8')` |
| Windows stdout | `sys.stdout.reconfigure(encoding='utf-8')`（僅 `sys.platform == 'win32'`） |
| PowerShell 寫檔給別的工具讀 | `Out-File -Encoding utf8` / `Set-Content -Encoding utf8`（絕不用預設 ANSI） |
| 比對前正規化 | `unicodedata.normalize('NFKC', s).lower().strip()` |

### 13.8 路徑書寫規則表（照抄可用）

| 場合 | 寫法 |
|------|------|
| 跟包子對話 | Windows 反斜線絕對路徑：`E:\Projects\行銷分析\01_raw\` |
| 交付連結 | `[View 檔名](computer://E:\Projects\行銷分析\...)` |
| Git Bash 內 | 正斜線 + **雙引號**：`"E:/Projects/行銷分析/01_raw"`；建目錄 `mkdir -p "含中文 的/路徑"` |
| Cowork Linux mount | `/sessions/.../mnt/行銷分析/...` |
| Python 程式 | raw string 或 `pathlib.Path`，一律 `--root` 參數化，不寫死 |
| SKILL/references 內部檔案引用 | 正斜線：`references/analysis_policy.md`、`scripts/profile_dataset.py` |
| 文件裡畫目錄樹 | 資料夾後加反斜線：`01_raw\` |

### 13.9 命名慣例規則

| 對象 | 規則 | 範例 |
|------|------|------|
| 使用者可見的資料夾／輸出檔 | **中文**，不英文化、不自創縮寫 | `匯入用檔案\`、`大數據行銷_成績登錄_HW4.csv` |
| skill 內部檔（references/scripts） | 英文 snake_case | `folder_structure.md`、`validate_folder_structure.py` |
| 輸出檔命名 | `<領域>_<用途>_<批次>.csv` | `行銷分析_客群結果_2026Q2.csv` |
| 批次 placeholder | `HW{N}` / `第{N}次` / `{YYYY-MM-DD}` 樣式 | 文件中一律用大括號佔位 |
| 時間戳 | `YYYY-MM-DDTHHMM` 或 `YYYY-MM-DD_HHMMSS` | `2026-04-12T0649_...` |
| 變體版本 | `_寬鬆版` 之類**中文語意後綴**，不用 `_v2` | `HW3_成績_寬鬆版.csv` |
| 備份資料夾 | `_<用途>備份_YYYYMMDD\` | `_補交批改備份_20260619\` |
| 找檔案 | **一律 fuzzy match**，不寫死檔名 | `re.compile(r'第.*?(周|次).*?評分標準\.docx$')` |
| 「最新檔」定義 | 明訂一套（建議：檔名 ISO 時間戳字典序），reference 與腳本用同一套 | `sorted(glob.glob(...))[-1]` |

### 13.10 AskUserQuestion 卡點決策規則

**必須卡住（用 AskUserQuestion，每問附「（預設：X）」）：**

1. **讀完規格／資料之後、動手之前** —— 把「我理解到的」整成一段 markdown 回讀確認
2. **有多個合法選項且影響全部輸出時** —— 二選一或短列舉，附預設值，讓使用者能一句「照預設」過關
3. **輸入數量與預期不符時** —— 檔案數／筆數／金額總和對不上就停下對帳，「**對不上一定要找出原因**」
4. **要修改已交付結果之前** —— 即使使用者已口頭指示，指令本身有歧義就要問清楚（「遲交」＝扣一級 or 一律 C-？）
5. **即使有預設值也要複問的項目** —— 那些使用者曾經改口過的（等第命名、等第 vs 分數）

**不要卡住，改為主動推送（讓使用者挑錯）：**

- 每批處理完的**異動清單**（原值、新值、異動原因）—— 「不要默默改掉」
- 最終**分佈統計** —— 讓使用者對照直覺
- **邊界個案名單**（原文是 D/F 名單）—— 使用者會回頭給微調
- 輸出**檔案連結**

**不問開放式問題。** 沒有「你想怎麼做？」，一律「A 還是 B？（預設：A）」。

**新 skill 的開工六問範本（沿用作業批改的六問結構）：**

```
1. 分析口徑：<指標>用哪個定義？（預設：<上次用的>）
2. 嚴謹度是否與過去一致？（預設：是）
3. 離群值處理：保留 還是 剔除（並註明）？（預設：保留並註明）
4. 遺漏值：整列剔除 還是 填補 還是 單獨成一組？（預設：單獨成一組）
5. 輸出格式：CSV＋圖 還是 只要 CSV？（預設：CSV＋圖）
6. 預期的資料筆數／期間？（用來驗證讀取是否完整）

確認完才開始實際分析。
```

### 13.11 互動語氣規範清單

- [ ] 全程繁體中文；使用者口氣直接、條列式
- [ ] **不要過度堆疊 bullet point**（散文說結論 + 短表／3–5 項清單放細節）
- [ ] 交付檔案一定附 `[View 檔名](computer://<Windows 絕對路徑>)`
- [ ] **使用者質疑 → 預設是自己錯了，先重驗證再回覆。「先驗證再說」，不要先辯解**
- [ ] 主動提供**可直接轉發的對外文字**（結論摘要／回信／簡報 takeaway）
- [ ] 任何改動都**列異動清單**回覆，不准默默改
- [ ] 回報格式固定：**數字摘要 → 檔案連結 → 「如有需修正請隨時告知。」**
- [ ] 對外文字語氣：**有錯就道歉、沒錯就溫和說明**，不過度卸責、不讓對方覺得被駁回
- [ ] 成品交付前自己跑一遍機械化驗收（重讀輸出檔、對帳、格式 grep）

### 13.12 對外回信／結論摘要範本（五段結構）

```
<稱謂>你好，<致謝或致歉>。
經重新<檢閱／重算>後，<具體指出對方寫了什麼／哪個數字怎麼來的>，
<結果已更正為 X ／ 確認原結果為 X>，
<再次致歉 ／ 歡迎進一步討論>。
```

必備變體：**(a) 有錯的版本**（主動承認疏失、不卸責、簡述錯在哪、告知已更正）；**(b) 沒錯的版本**（先說明已徹底重查過什麼、再溫和說明為何維持原結果、末句邀請進一步討論）。英文對象給中英雙版。

### 13.13 工作日誌檔範本

```markdown
# <批次> <工作類型>紀錄

**日期**：YYYY-MM-DD
**專案**：<專案名>
**批次／主題**：<批次識別>
**執行者**：<角色>

---

## 需求說明（規格）
來源：`<規格檔名>`
（需求列表）
**判斷標準**：（<類別> | <條件> 兩欄表）
**基調**：（一句話）
**標準流程**：Step 0 → … → Step N

---

## 結果總覽
**<主要計數>**：N
**<排除計數>**：N
**總計**：N（<排除說明>）
（<類別> | <人數/筆數> | <說明> 三欄表）

---

## 特殊案例說明
### <分類 1>
#### <識別碼> <名稱> → <結果>
- <證據>：...
- <問題>：...
- <判定>：...
### <分類 2：修正過的>
#### <識別碼> <名稱>
- **原狀況**：...
- **確認方式**：<用什麼工具怎麼查的>
- **內容**：...
- **結論**：<新結果>

---

## <排除／未涵蓋>清單（N 項）
（用「、」串成一段）

---

## 輸出檔案
（檔案 | 路徑 | 用途 三欄表）

---

*本紀錄由 Claude（Cowork 模式）自動<動作>，<動作>日期：YYYY-MM-DD*
```

### 13.14 自我校準紅線（決策規則，可移植的形式）

原文（`grading_policy.md` §二）的分數比例紅線，抽象後是一條**「先看分佈再相信自己」**的規則：

```
跑完一輪後，先看結果分佈，對照歷史基準：
- 如果 <主要類別比例> 低於 <下限> → 太嚴／方法有問題，回頭檢查是不是漏抓
- 如果 <邊緣類別比例> 超過 <上限> → 同上
- 如果 <極端類別> 完全沒有 → 正常，那是真正的特例
- 如果 <缺漏類別> 超過 <上限> → 檢查鍵值比對是否漏對（特別是有前綴／格式變體的）
```

原文的具體實例（逐字）：

```
- 如果 **A+ 比例低於 70%** → 太嚴了，重新檢查 B 段是不是漏掃，或邊界判斷太嚴格
- 如果 **B 段超過 20%** → 同上
- 如果 **完全沒有 D** → 正常，D 是真的繳錯/亂繳的特例
- 如果 **F（未繳）超過 15%** → 檢查學號比對是否漏對（特別是 ntnu_/ntust_ 前綴）
```

**行銷分析的等價紅線（建議）：** 分群結果最大群超過 70% → 特徵可能沒縮放或分群數不足；有群體小於 1% → 檢查是不是離群值自成一群；遺漏值比例超過 20% → 回頭確認欄位口徑；key join 後匹配率低於 95% → 檢查 ID 格式變體（大小寫、前綴、全形）。

### 13.15 分數／等級對照表（原文公式，如新 skill 需要類似映射可參照）

```python
GRADE_TO_SCORE = {
    'A+': 97,
    'A':  90,
    'A-': 85,
    'B+': 82,
    'B':  80,
    'B-': 78,
    'C+': 75,
    'C':  73,
    'C-': 70,
    'D':  60,
    'F':  50,   # HW4 之後（HW2 用 0）
    'E':  0,    # 舊版（已改成 F）
}
```

（原文 `grading_policy.md` §五，逐字。註解保留了版本演進資訊 —— 這種「在資料結構裡寫下歷史變更」的做法值得沿用。）

### 13.16 通用決策樹寫法（ASCII，可作為新 skill 判斷規則的呈現範本）

```
                  全部繳交了嗎？
                   /          \
                  否            是
                  ↓             ↓
                  F          有計算過程／有實質內容嗎？
                              /                \
                             否                 是
                             ↓                  ↓
                             D（亂繳/僅連結）  繳錯週次嗎？
                                              /         \
                                             是          否
                                             ↓           ↓
                                             D       客觀題對了嗎？
                                                     /           \
                                                  全對            部分錯
                                                   ↓               ↓
                                          開放題如何？        看開放題救得回來嗎
                                          /     |    \              ↓
                                       完美   小瑕疵  多瑕疵    A-（救回來）/ B（救不回）
                                        ↓     ↓      ↓
                                       A+    A      B
```

字元集：`/ \ ↓ |` + 全形空格對齊。搭配文字補充「門檻」與「瑕疵清單」：

```
### 客觀題「對」的門檻
- 4 小題的客觀題：對 ≥ 3 題算對，對 ≤ 2 題算錯
- 若客觀題只對一題，且開放題完美 → B（不是 D）
- 若客觀題全錯，但開放題完美 → A-（非常少見的特例，斟酌）
```

`「一項瑕疵 → A」「兩項以上 → B」「沒解釋理由 → 直接 B」` —— 這種**把邊界寫成一行判斷式**的做法，是新 skill 定義「什麼算顯著／什麼算異常」時應沿用的表達方式。

---

## 14. 【評註】給新 Skill 的一頁行動清單

1. 建 `E:\Projects\行銷分析\<skill 名>\`，形態採「展開資料夾」（非單檔 `.skill`）。
2. 寫 `SKILL.md`，照 §13.2 骨架，frontmatter 照 §13.1（`|` block scalar + MANDATORY TRIGGERS + 兜底條款）。
3. 寫 `CLAUDE.md`，照 §13.3，30 行以內，含「一句話核心原則」。
4. 建 6 份 `references/`，照 §4.6 的對應表切分，逐份過 §13.4 檢查清單。**其中 `data_loading.md` 必須是失敗案例庫型**（一開始可以空著案例表，第一次分析完就回填）。
5. 建 `scripts/`：`setup_new_analysis.py`、`validate_project_inputs.py`、`profile_dataset.py`、`check_data_quality.py`、`verify_outputs.py`、`inspect_xlsx.py`、`extract_pdf_content.py`（改寫版）。每支照 §13.5 骨架 + §13.6 硬規則 + §13.7 編碼表。
6. 建 `templates/`：輸出 CSV 範例（含真實範例列）、對外結論摘要範本（正反兩版）、分析紀錄範本（§13.13）。
7. 把 §13.10 的開工六問寫進 `analysis_policy.md` 與 `folder_structure.md` **兩處**（原文就是刻意重複兩次，確保不會漏問）。
8. 把 §13.14 的自我校準紅線填上行銷分析的具體數字。
9. 每次執行完寫一份 `<批次>_分析紀錄.md`，然後把重複出現的教訓**升級**進對應的 reference（案例表、決策時序表）。
