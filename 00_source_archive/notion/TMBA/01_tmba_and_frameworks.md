---
title: "TMBA 管顧思維 × Case Interview 結構化框架 — 問題拆解方法論萃取"
purpose: "為新 Skill S1「開案對焦階段」提供『把模糊商業提問結構化成可分析假設』的可執行方法"
fetched_date: 2026-07-26
extracted_by: "Claude (方法論萃取 subagent)"
sources:
  - path: "D:\\TMBA\\20250723 管顧思維.pdf"
    size: "6.4 MB (6,744,821 bytes)"
    pages: 16
    title: "管顧方法論 — 講師：吳紹羽（策略行銷部 社課）"
    coverage: "100% — 16/16 頁全文字層萃取成功（pdfplumber）"
    note: "投影片型 PDF，文字層完整。P7/P8 含截圖影像（共編表單、分析步驟示意），影像內文字未 OCR。"
  - path: "D:\\TMBA\\Case Interview-20250729T152159Z-1-001.zip"
    size: "52.4 MB → 解壓後 25 個 PDF"
    coverage: "見下方 per-file coverage 表"
  - url: "https://app.notion.com/p/3252b4ffdf0b814aa0b5cd2023935e89"
    title: "TMBA 暑期社課（碩二版）"
    coverage: "100% — 父頁 + 2 子頁全讀"
  - url: "https://app.notion.com/p/25b2b4ffdf0b809ab5d9c0611d99b939"
    title: "TMBA 暑期社課（碩一版）"
    coverage: "100% — 父頁 + 2 子頁全讀；內容與碩二版逐字相同（同一份筆記的兩個副本）"
  - url: "https://app.notion.com/p/3252b4ffdf0b8111a736de28a4641333"
    title: "行銷理論整理1（全球品牌管理 Global Brand Management 期中重點）"
    coverage: "100%"
  - url: "https://app.notion.com/p/3252b4ffdf0b818f8708f9d7b0357749"
    title: "行銷理論整理2"
    coverage: "見下方章節"
  - url: "https://app.notion.com/p/3252b4ffdf0b819e9b0ee5e78b10c83d"
    title: "3/26 講義隨筆+整理"
    coverage: "見下方章節"
  - url: "https://app.notion.com/p/25b2b4ffdf0b8036bb8ac680736acafa"
    title: "統計理論（16 個子頁）"
    coverage: "父頁目錄 100%；子頁聚焦非母數統計，見該章節"
coverage_summary: |
  完整讀完：管顧思維 PDF (16/16 頁, 100%)、Victor Cheng 框架 (6/6 頁, 100%)、
  Columbia 案例提示 (3/3 頁)、Minto Ch.8 問題定義全章 + Ch.9 摘要、
  Notion 全部 9 個有內容的頁面 (品牌管理×2、競爭策略、敘述統計學、TMBA 社課×6 含重複)。
  部分讀取：Ace Your Case III 市場規模 (76 頁中約 25 頁，解答章未讀)、
  Minto 全書 (275 頁中約 20 頁)、BCG/Bain/Berkeley casebook (已萃取文字，僅掃讀)。
  明確缺口：Case Interview 資料夾 25 個 PDF 中 13 個完全未讀 (>1,500 頁，含 Case in Point、
  Kellogg、Vault、McKinsey Casebook)；Notion 統計理論 16 子頁中 11 頁未讀；
  「非母數統計方法」「假說檢定」「卡方檢定」三個 Notion 頁面經確認為【空白頁，無內容】；
  D:\TMBA\TMBA.rar (321MB) 與管顧思維社課錄影 (1.98GB .mov) 完全未處理。
  詳見文末第 12 節。
---

# TMBA 管顧思維 × Case Interview 結構化框架

> **本檔定位**：這是「把模糊的商業提問 → 結構化成可分析假設」的方法論知識庫。
> 服務對象是 Skill S1 的**開案對焦階段**（intake / problem framing），
> 也就是「客戶丟一句『我們業績下滑』，分析師該怎麼把它變成一組可以跑資料的假設」。
>
> **格式約定**：
> - 【材料原文】= 來源文件的原始內容（逐字或忠實轉錄）
> - 【評註】= 萃取者的補充、翻譯成可執行步驟、或與 S1 的接合建議
> - 每個方法都標註「**這回答什麼行銷/商業問題**」

---

## 目錄

1. [核心骨幹：McKinsey 7 Steps（管顧思維 PDF）](#1-核心骨幹mckinsey-7-steps)
2. [Step 1 — SMART 原則寫 Problem Statement](#2-step-1--smart-原則寫-problem-statement)
3. [Step 2 — 拆樹：議題樹／假說樹／演繹樹 + MECE](#3-step-2--拆樹議題樹假說樹演繹樹--mece)
4. [Step 3 — 2×2 Prioritization Matrix + 80/20](#4-step-3--22-prioritization-matrix--8020)
5. [Step 4-5 — 分析規劃與假說驗證](#5-step-4-5--分析規劃與假說驗證)
6. [Step 6 — 金字塔原理（So What 向上推導）](#6-step-6--金字塔原理so-what-向上推導)
7. [Step 7 — 管顧式簡報與費米推論](#7-step-7--管顧式簡報與費米推論)
8. [Case Interview 結構化框架庫](#8-case-interview-結構化框架庫)
9. [行銷理論架構](#9-行銷理論架構)
10. [非母數統計方法](#10-非母數統計方法)
11. [可重用資產](#11-可重用資產)
12. [覆蓋率誠實聲明](#12-覆蓋率誠實聲明)

---

## 1. 核心骨幹：McKinsey 7 Steps

**來源**：`D:\TMBA\20250723 管顧思維.pdf` p.3

**這回答什麼商業問題**：「一個策略性專案，從接到模糊需求到交出建議，中間到底有哪幾個必經關卡？」
這是 S1 開案對焦最重要的骨架 —— 它明確告訴你：**結構化（Step 2）發生在定義問題（Step 1）之後、優先排序（Step 3）之前**。

### 【材料原文】

> 解決策略性問題時，需要依照 McKinsey 7 Steps 進行思考
>
> 1. **Define Problem** — 應該運用 SMART 原則進行 Problem Statement，確保正確地解決問題
> 2. **Structure Problem** — 依照不同情況，選擇運用議題樹、假說樹、演繹樹將問題結構化，並建立假說
> 3. **Prioritize Issues** — 利用 2 by 2 矩陣，將結構化問題進行歸納，找出重大問題，確保符合 80/20 法則
> 4. **Plan Analyses and Work** — 利用 excel、google 表格將欲解決的假說依照分析方法進行歸納，並指派 PIC
> 5. **Conduct Analyses** — 進行質性、量化的假說驗證，例如訪談法、問卷分析、數據分析與資料視覺化
> 6. **Synthesize Findings** — 透過金字塔原理，將驗證後的假說結合
> 7. **Develop Recommendations** — 產出策略建議，並繪製客戶簡報

### 【評註】對 S1 的意義

這 7 步可以直接切成 S1 的三個階段：

| 階段 | 對應 Steps | S1 該產出什麼 |
|---|---|---|
| **開案對焦（S1 主戰場）** | 1–3 | 一句 SMART Problem Statement + 一棵 MECE 樹 + 一張 2×2 優先序 |
| **分析執行** | 4–5 | 假說→分析方法對照表（含 PIC、資料來源） |
| **收斂交付** | 6–7 | 金字塔式結論 + Tagline 化簡報 |

**關鍵設計啟示**：Step 1→2→3 是**單向漏斗**，且每一步都有明確的「完成判準」（見各節）。
S1 不該讓使用者跳過 Step 1 直接拆樹 —— PDF 的原文措辭是「確保**正確地**解決問題」，
這是在防「解錯題」（solving the wrong problem），不是在防「解得不好」。

---

## 2. Step 1 — SMART 原則寫 Problem Statement

**來源**：`20250723 管顧思維.pdf` p.4

**這回答什麼商業問題**：「客戶說『我們想提高業績』，這句話為什麼不能直接拿來分析？要補上哪些欄位才能動工？」

### 【材料原文】

> **SMART 原則應該釐清一個特定且明確的問題，並提供可執行且有時限的敘述**
>
> 業主目標：**TMBA 希望提高招生人數**
>
> 五個維度與對應的反例：
>
> - **Specific（明確）** — 社員多來自北部，因此需要招收中南部生
>   - 反例（Not Action-oriented）：「TMBA 應該招收中南部學生」
> - **Measurable（可衡量）** — 預計提高招生率 50%
>   - 反例（Not Measurable）：「TMBA 應該更積極招生」
> - **Achievable / Action-oriented（可行動）** — 透過社群行銷與社課優化
>   - 反例（Not Relevant）：「TMBA 應該提高社費」
> - **Relevant（相關）** — 與問題本身具關聯性
> - **Time-bound（有時限）** — 具有時間限制；2025 年暑期提高招生率達 50%
>
> **最終合格的 Problem Statement（原文完整版）**：
> > 「TMBA 的社員多來自北部，藉由社群行銷與社課內容優化，可讓 2025 年暑期提高招生率達 50%」

### 【評註】拆解成可執行的檢查步驟

原投影片是「反例對照」教學法，我把它翻譯成 S1 可以直接跑的**逐欄填空模板**：

```
Problem Statement 模板（五槽位）
──────────────────────────────────────────────
[現況/根因錨點]  ______________________________   ← Specific
                 （例：社員多來自北部）
[介入手段]       藉由 ______________________      ← Action-oriented
                 （例：社群行銷與社課內容優化）
[目標指標]       可讓 ____（指標）____            ← Measurable
                 （例：招生率）
[目標水準]       達 ______________________        ← Measurable
                 （例：50%）
[時間邊界]       於 ______________________ 前     ← Time-bound
                 （例：2025 年暑期）
──────────────────────────────────────────────
Relevant 檢查：上述介入手段是否真的作用在「現況/根因錨點」上？
              若否 → 這是「提高社費」型錯誤（Not Relevant）
```

**四種不合格 Problem Statement 的診斷特徵**（從原投影片反例反推）：

| 反例類型 | 徵狀（怎麼一眼看出） | 修法 |
|---|---|---|
| Not Action-oriented | 只講「要做到什麼狀態」，沒講「靠什麼做到」 | 補上「藉由…」子句 |
| Not Measurable | 出現「更積極」「加強」「優化」等程度副詞但無數字 | 補上指標名 + 目標水準 |
| Not Relevant | 介入手段與現況錨點無因果連結（招生問題卻動社費） | 回 Step 2 拆樹重找槓桿點 |
| Not Time-bound | 沒有截止時點 | 補上期間 |

**S1 決策規則（可直接寫進 Skill）**：
> 若使用者輸入的商業提問**缺少上述五槽位中任一槽**，S1 不應開始拆樹，
> 而應先反問補齊缺的槽位。特別是「目標指標」缺失時，後續整棵樹無法定義葉節點的驗證方式。

---

## 3. Step 2 — 拆樹：議題樹／假說樹／演繹樹 + MECE

**來源**：`20250723 管顧思維.pdf` p.5

**這回答什麼商業問題**：「一個大問題該往哪個方向拆？拆到什麼時候可以停？怎麼知道拆錯了？」

### 【材料原文】

> **拆樹的目的在於將問題拆解成能夠解決的方案，直到該層無法 MECE 即停止**
>
> 核心思維是**根因分析**，不斷問自己 **Why So？** 謹記 MECE 原則
>
> - **ME：完全互斥**（Mutually Exclusive）
> - **CE：互不遺漏**（Collectively Exhaustive）

#### 三種樹的比較（原投影片表格）

| | **議題樹** | **假說樹** | **演繹樹** |
|---|---|---|---|
| 根節點 | 主要議題 | 主要假說 | 主要策略 |
| 分支 | 子議題 | 子假說 | 子策略 |
| **目的** | 目的在於將**宏觀問題**拆解成能夠**解決的子問題** | 目的在將**假說**拆解成能夠**驗證的子假說** | 目的在藉由**策略先行**的思考，發展**合適解方** |
| **每個分支的判準** | 每個分支都應該是**所欲解決的問題** | 每個分支都應該是**呼應主要假說且能銜接策略**的子假說 | 每個分支都應該是**以終為始**的解方 |
| 共同要求 | MECE | MECE | MECE |

#### MECE 違反的兩個原始範例

**違反 ME（不互斥）**：
```
TMBA 社員
├─ 大學生
├─ 研究生   ← Why So? → 「研究生」已包含「博士生」
└─ 博士生   ← 與研究生重疊 → 不 ME
```

**違反 CE（有遺漏）**：
```
TMBA 社員
├─ 大一
├─ 大二
├─ 大三
└─ 大四     ← Why So? → 沒考慮到「研究生」 → 不 CE
```

#### 「甜蜜點」概念 —— 拆到哪一層才停

原投影片用「客廳太熱／想看電視」的生活例子示範拆解深度與可行性的權衡：

| 拆出的根因 | 對應解方 | 評價 |
|---|---|---|
| 發燒 | 貼降溫貼布 | 太表層 |
| 感冒 | 吃感冒藥 | — |
| **在客廳吹冷氣／看電視** | **在客廳放一條毯子，或在房間擺一台電視** | ← **甜蜜點** |
| 人類基因缺陷 | 請專家團隊改善人類基因 | 拆太深，不可行 |

### 【評註】把「拆樹」翻譯成可執行步驟

原材料把「怎麼拆」講得很精煉但抽象。以下是我從材料本身的邏輯翻出來的操作序列（未混入材料外的內容，僅重排與具體化）：

**拆樹操作 SOP**

1. **選樹種**（這是原材料最有價值、也最少人講清楚的一步）：
   - 手上只有「現象」、還不知道原因 → **議題樹**（例：「營收為何下滑？」）
   - 已經有一個明確的猜想要驗證 → **假說樹**（例：「營收下滑是因為 A 通路流失」）
   - 問題已定、要選路徑 → **演繹樹**（例：「該用哪三條策略達成 +50%？」）
2. **對根節點問 Why So?**，列出第一層分支
3. **對每一層做 ME 檢查**：任兩個兄弟節點是否有包含關係或概念重疊？（「研究生 vs 博士生」測試）
4. **對每一層做 CE 檢查**：兄弟節點聯集是否等於父節點？漏了誰？（「大一～大四漏了研究生」測試）
5. **判斷是否觸底**：若對某節點再問 Why So? 已無法產生 MECE 的子節點 → **停止**
6. **甜蜜點檢查**：葉節點的解方是否「可執行且有意義」？
   - 太表層（治標）→ 再往下拆一層
   - 太深層（不可行，如「改善人類基因」）→ 往上收一層

**S1 決策規則**：
> - 拆樹停止條件有**兩個**，缺一不可：(a) 該層再拆會違反 MECE；(b) 葉節點落在甜蜜點（解方可執行）。
> - 只滿足 (a) 不滿足 (b)：拆得太淺或太深，需調整層級。
> - 每個葉節點必須能對應到 Step 5 的一種驗證方法（質性訪談 / 問卷 / 數據分析），否則它不是可分析的假設。

**與 Victor Cheng「SEGMENT → ISOLATE → EXPLORE」的接合**（見第 8 節）：
TMBA 的「拆樹 + Why So」是**定性的**問題分解；Victor Cheng 的 SEGMENT/ISOLATE 是**定量的**同一件事
（用歷史數據比對找出數字上的漂移點）。S1 應該把兩者串成一條流程：
拆樹給出**要切哪些維度**，SEGMENT/ISOLATE 給出**哪個切片真的是問題所在**。

---

## 4. Step 3 — 2×2 Prioritization Matrix + 80/20

**來源**：`20250723 管顧思維.pdf` p.6

**這回答什麼商業問題**：「樹拆出 20 個葉節點，但只有 6 週專案時間 —— 先驗證哪幾個？」

### 【材料原文】

> **透過 2 by 2 Prioritization Matrix 篩選出符合 80/20 法則的項目執行驗證**
>
> 利用議題樹 or 假說樹 or 演繹樹建立待驗證的問題 or 假說 or 策略
> → 利用 2 by 2 矩陣篩選出重大待驗證的問題 or 假說 or 策略

**矩陣兩軸與四象限（原投影片）**：

```
低投入 │  Do Later   │   Do Now     │
       │  (#3)       │   (#1)       │
       ├─────────────┼──────────────┤
       │  Don't Do   │   Do Next    │
高投入 │  (#5,#6,#7) │   (#2,#4)    │
       └─────────────┴──────────────┘
          低價值         高價值
```

| 象限 | 投入 | 價值 | 行動 |
|---|---|---|---|
| 右上 | 低投入 | 高價值 | **Do Now** |
| 右下 | 高投入 | 高價值 | **Do Next** |
| 左上 | 低投入 | 低價值 | **Do Later** |
| 左下 | 高投入 | 低價值 | **Don't Do** |

### 【評註】

- 兩軸定義：**投入（effort/cost）** vs **價值（value/impact）**。注意原投影片的 Y 軸是**由上而下遞增投入**（上=低投入）。
- 「符合 80/20 法則」在此的操作定義是：**選出 Do Now + Do Next 象限的項目**，
  也就是用約 20% 的驗證項目涵蓋約 80% 的問題解釋力。
- 原投影片的 #1–#7 編號顯示：拆樹產出的候選項目應**先全部列出並編號**，再一個個投放到矩陣，
  而不是邊拆邊篩（避免過早收斂）。

**S1 決策規則**：
> 拆樹完成後，強制產出一張「葉節點 × (預估投入, 預估價值)」的評分表，
> 只有落在 Do Now / Do Next 的葉節點才進入 Step 4 的分析規劃。
> Don't Do 象限的項目應**明確記錄為「已考慮但排除」**（供 Step 7 附錄用，見第 7 節）。

---

## 5. Step 4-5 — 分析規劃與假說驗證

**來源**：`20250723 管顧思維.pdf` p.7–8

### 【材料原文】

**Step 4（p.7）**
> 將篩選後的待驗證項目整理進**共編表單**中，並說明**分析方式**，指派**負責組員**
> （利用 excel、google 表格…並指派 **PIC**）

**Step 5（p.8）**
> 進行質性、量化的假說驗證，例如訪談法、問卷分析、數據分析與資料視覺化
>
> - **質性分析：訪談法**
>   - 需事先擬好**訪綱**，並建立可以**共編的訪談紀錄表**
>   - 訪談人員包含：**主訪、主筆、附筆兼會議記錄**
> - **量化分析（分析步驟，難易程度遞增）**：
>   `資料抓取 → 資料分析 → 資料視覺化`

*（註：p.8 含 14 張示意影像，影像內文字未 OCR；文字層已完整涵蓋條列內容。）*

### 【評註】

Step 4 的產出物在 S1 中應該固化成一張表 —— 這是「假說」轉「可分析任務」的交界面：

| 假說 ID | 假說敘述 | 2×2 象限 | 驗證方法 | 資料來源 | PIC | 完成判準 |
|---|---|---|---|---|---|---|
| H1 | … | Do Now | 數據分析 | … | … | … |
| H2 | … | Do Next | 訪談法 | … | … | … |

**訪談的三角色分工**（主訪／主筆／附筆兼會議記錄）是原材料裡少見的具體執行細節，
值得原樣保留進 S1 的質性驗證範本。

---

## 6. Step 6 — 金字塔原理（So What 向上推導）

**來源**：`20250723 管顧思維.pdf` p.9

**這回答什麼商業問題**：「驗證完 10 個假說，一堆零碎發現 —— 怎麼收斂成一句老闆聽得懂的結論？」

### 【材料原文】

> **驗證後的假說需要透過金字塔原則，向上推導得出結論，遵循以終為始的概念**
>
> 呼應根因分析，金字塔原則需要問自己 **So What？**
>
> ```
>        策略          ← 藉由主要議題發展策略
>         ↑ So What?
>      主要議題         ← 利用洞察支持主要議題
>         ↑ So What?
>       洞察           ← 結合多個假說後，將會得到多個洞察
>         ↑ So What?
>       假說           ← 透過質性、量化方式驗證後的假說
> ```

### 【評註】Why So? 與 So What? 的對稱關係 —— 這是整份材料的核心洞見

原材料把兩個問句**明確配對到兩個相反方向**，這點非常值得寫進 S1：

| | 方向 | 問句 | 階段 | 產出 |
|---|---|---|---|---|
| **拆解（Step 2）** | 由上而下 ↓ | **Why So?** | 開案對焦 | 議題樹／假說樹（根因分析） |
| **收斂（Step 6）** | 由下而上 ↑ | **So What?** | 收斂交付 | 金字塔（洞察→議題→策略） |

**四層金字塔的層級定義（原材料用語）**：
1. **假說**（bottom）= 經質性/量化驗證後的單一命題
2. **洞察** = 多個假說結合後得到的解釋
3. **主要議題** = 洞察支持的核心命題
4. **策略**（top） = 由主要議題發展出的行動建議

**S1 決策規則**：
> 拆樹（Why So?）與收斂（So What?）必須**結構對稱** ——
> Step 2 樹的每一個進入驗證的葉節點，在 Step 6 都要有去處（成為某個洞察的支撐，或被明確標記為「已驗偽」）。
> 若某個假說驗證完後在金字塔裡找不到位置，代表 Step 2 拆樹時該分支就不該存在（是 Not Relevant 的分支）。

---

## 7. Step 7 — 管顧式簡報與費米推論

**來源**：`20250723 管顧思維.pdf` p.10–15

**這回答什麼商業問題**：「分析做完了，怎麼包裝成客戶會採納的東西？以及：客戶臨時問一個沒算過的數字，怎麼辦？」

### 【材料原文】

管顧式簡報的**五段固定結構**（每頁投影片左側都有的導覽列）：
```
執行摘要 → 時程規劃 → 分析內容與策略 → 預期效益評估 → 附錄
```

#### 7.1 執行摘要（p.10）
> 執行摘要，包含整份簡報**最重要的內容**，通常以文字方式呈現
> - 實務上，若時間不足，執行摘要的內容可以**直接提取簡報每頁的 Tagline**
> - 通常需要包含**目標、策略、預期成效**等內容，以 **Marvin Table** 的形式呈現

原投影片附了一個真實案例（OIC Taipei M&A Project Group 3）的執行摘要範例，結構為：
```
Why M&A     • Mitigating limited growth in both major business segments - Taiwan and China
              - Rising labor costs and post-pandemic slowdown in Taiwan; Economy downgrade in China
            • Elevating our global reach and brand position
              - Address increasing overconcentration in Taiwan Market

Target      Southeast Asia
Screening     • Strong CAGR with significant growth potential; low operating costs and high
                dine-out rates support profitability
            Thailand
              • Second largest foodservice market in SEA, with low costs and competition,
                and better pricing

Target      Zen group satisfies the 4 criteria we proposed
Analysis    • Caters itself to Thai people's strong preference in hotpot and seafood
            • Despite its weak financials in the first 2 quarters of 2024, revenue growth is
              still stable with a low EV/EBITDA

Transaction • Offering a bid price of US$ 0.26 with a 25% premium, which leads to a deal size
Summary       of US$ 72,450 K
            • Creates an EPS accretion of 0.32 in FY24, and 0.62 in FY28
            • 100% equity acquisition with 48% cash, 40% debt, and 12% stock

Post        • Management Improvement
Transaction • New Hot Pot Business
Strategies  • Ingredients & Personnel Cost Savings
```

#### 7.2 時程規劃（p.11）
> 時程規劃，用來跟業主討論專案進度
> - 與執行摘要一樣，以 **Marvin Table** 的形式呈現
> - 可以配合專案的時程，利用**遮罩功能**，說明專案進度
>
> 案例（TMBA × 國泰人壽）：W1–W16 甘特軸，標記 `3/17 啟動會議`、`4/21 期中匯報`、`6/16 期末匯報`，中間有兩個 Review 節點。

#### 7.3 量化分析頁（p.12）
> 量化分析，應該著重呈現**圖表趨勢**
>
> 頁面結構：`Tagline: 最重要的內容` → `Chart: 分析結果` → `Key Insight: 圖表的洞察` → `Sources`
>
> - 撰寫 **Tagline** 時，應該思考 **Key Insight** 的內容，並彙整成**一句話**
> - 圖表上可以適時利用框線等方式，標註出重點
> - 圖表應該**避免使用圓餅圖（Pie Chart）**，因其佔空間，且不便人眼閱讀

#### 7.4 質性分析頁（p.13）
> 質性分析，需要注意呈現方式，方便 Audience 閱讀
>
> 頁面結構：`Tagline: 最重要的內容` → `Marvin Table`
>
> - 質性資料通常包含許多文字，可以使用 **Marvin Table** 繪製簡報
> - 相較於制式化的表單，Marvin Table 有更多的**自由度**，也可以放入圖表輔助說明

#### 7.5 預期效益評估 —— 費米推論（p.14）
> 預期效益評估，透過**費米推論 ＆ 公式拆解**，得出相對合理的數字
>
> - 費米推論實務上經常用在與客戶開會時，**因應客戶臨時詢問**，而透過**公式加上常識**，回答客戶一個**相對正確**的數字
> - 預期效益評估所涉及的許多「率％」實務上是經過**十分嚴謹的資料計算**後得出的結果，有時則是**業主主動給予**，而社團專案則是練習費米推論的好機會

#### 7.6 附錄（p.15）
> 附錄無需刻意製作，只需因報告時長限制，將部分內容放入即可
>
> - 繪製簡報時，大可不必擔心頁數與內容太多，只需要在結案客戶簡報時，小組討論將次要內容放入附錄即可
> - **議題樹作為管顧思維的一環，通常不會放在正報當中**，可思考放在附錄中，甚至有時不會跟客戶報告

### 【評註】

**最反直覺、也最該記住的一條**：議題樹是**思考工具，不是交付物**。
S1 應該讓使用者知道：拆樹的產出是給分析團隊自己用的，客戶看到的是金字塔頂端的策略。
這解釋了為什麼 Step 2（拆樹）與 Step 6（金字塔）要分開 —— 它們的受眾不同。

**Tagline 規則可以直接程式化**：每張圖表頁必須有「一句話 Tagline」，且 Tagline = Key Insight 的濃縮。
這其實就是金字塔原理在單頁層級的應用（圖表是假說，Key Insight 是洞察，Tagline 是議題）。

**費米推論的定位**：注意原材料的措辭是「回答客戶一個**相對正確**的數字」——
它的用途是**即時回應**，不是取代嚴謹分析。真正的「率％」要嘛來自嚴謹計算、要嘛業主給。
這在 S1 裡是一條重要的界線：估算 ≠ 分析。

---

## 8. Case Interview 結構化框架庫

**來源**：`D:\TMBA\Case Interview-...zip` 解壓後之各 PDF

**這回答什麼商業問題**：「面對『獲利下滑』『該不該進入某市場』『市場有多大』這類典型提問，有沒有現成的拆解模板？」

### 8.1 Victor Cheng — Case Interview Core Frameworks v1.0

**來源**：`Case Interview/case_interview_frameworks.pdf`（6 頁，**100% 全讀**）
著作權：© Victor Cheng, www.caseinterview.com

#### 8.1.1 PROFITABILITY FRAMEWORK（獲利樹）

**這回答什麼商業問題**：「獲利／營收下滑，原因在哪？」—— 這是行銷分析最常見的第一類提問。

**樹狀結構（原文）**：
```
                  ┌── Revenue/Unit
        ┌── Revenue ─┤
        │         └── # Units Sold
Profits ─┤
        │         ┌── Fixed Cost
        └── Cost ──┤── Variable Cost
                  └── # Units Sold
                      （Cost/Unit × # Units Sold）
```

**對「問題分支」的三步操作（原文逐字）**：

> For the problem branch (e.g., Revenue/Unit or # Units Sold)
> 1) **SEGMENT** the number, break it up into its component parts, compare to historical metrics to find where the shift is coming from
> 2) **ISOLATE** the key driver causing bulk of problem
> 3) **EXPLORE** possible resolutions

**可切的維度（原文）**：
> Possible Segments to get data for, isolate & explore:
> - By product / product line
> - By distribution channel
> - By customer type (new/old, big/small)
> - By region
> - By industry vertical

**成本側的切法（原文）**：
> For problem branch (e.g, fixed or variable cost) — **SEGMENT** into its component parts
> - Segment cost by logical components
> - Segment costs by value chain
>
> Value Chain Example: Identify fixed costs in each of the following:
> `Raw Materials -> Factory -> Distribution -> Customers`
>
> Compare to historical. Find the problem component.

**原文的關鍵提醒（Tips 逐字）**：
> 1) Keep drilling down until you isolate the problem
> 2) If you realize a branch (or sub-branch) is NOT the problem, come up a level and work the remaining branches
> 3) The name of the game is **PROBLEM ISOLATION**
> 4) When "units sold" decline, it's useful to compare the company's numbers to its competitors to determine if it's an **industry-wide or company-specific** issue

**原文另一段重要提醒**：
> Once you know mathematically what's causing the problem, you need to understand **WHY** the number has declined **in the context of the marketplace**. This may be a "compound framework" problem requiring you to use a general market analysis framework. If so, most often you will want to start with the **customer (demand side) analysis** and potentially may have to use the entire framework.

##### 【評註】這段是 S1 最重要的外部素材

Victor Cheng 在這裡講了一件 TMBA 材料沒明說的事：**數學定位 ≠ 因果解釋**。
```
SEGMENT/ISOLATE  →  回答「數字上是哪一塊掉了」（WHAT）
                        ↓ 必須接
Business Situation  →  回答「為什麼那一塊會掉」（WHY）
Framework              （從 Customer 需求端開始）
```
這正好對應 TMBA 的兩層：拆樹找到葉節點（WHAT）後，還要對葉節點做根因分析（WHY So?）。
**S1 應該把「獲利樹」定位成一棵標準化的議題樹模板**，而不是完整答案。

#### 8.1.2 BUSINESS SITUATION FRAMEWORK（4C：市場進入／新產品／成長／轉型）

**適用題型（原文逐字）**：
> New Market Entry, New Product, New Business, How to Grow, Strategy, Turnaround, Company Position Assessment

**四大區塊完整檢查清單（原文逐字）**：

**Customer**
> - Who is the customer? — identify segments (segment size, growth rate, % of total market)
> - compare current year metrics to historical metrics (look for trends)
> - What does each customer segment want? — identify keys needs
> - What price is each segment willing to pay? — determine price points and price elasticity/sensitivity
> - Distribution channel preference for each segment
> - Customer concentration and power\* (does one customer control all the demand, the "Wal-Mart" effect)

**Product**
> - Nature of product (think out loud about the product, it's benefits, why someone would buy it)
> - Commodity good or easily differentiable goods (could company increase differentiation)
> - Identify complimentary goods (can we piggy back off growth in compliments or near compliments?)
> - Identify substitutes\* (are we vulnerable to indirect competitors namely substitutes?)
> - Determine product's lifecycle (new vs. almost obsolete)
> - Packaging (optional) — what's bundled, included (ex. Razor vs. razor blades, with w/o service contract... can change in packaging make product more likely to meet needs of specific customer segments.)

**Company**
> - Capabilities and expertise
> - Distribution channels used
> - Cost structure (mainly fixed vs. variable — is it better to have higher fixed cost with lower variable, or vice versa. High fixed cost = barrier to entry.... compare to industry, often insightful)
> - Investment cost (optional: only if case involves an investment decision)
> - Intangibles (e.g., brands, brand loyalty)
> - Financial situation
> - Organizational structure (optional: e.g., is team organization in conflict with how customers want to do business. Ex: We're organized by product line, but customers want one point of contact across all product lines)

**Competition**
> - Competitor Concentration\* & Structure (monopoly, oligopoly, competitive, market share concentration)
> - Competitor behaviors (Target customer segments, products, pricing strategy, distribution strategy, brand loyalty)
> - Best practices (are they doing things we're not?)
> - Barriers to entry\* (do we need to worry any new entrants to market)?
> - Supplier concentration\* (optional: ex: Microsoft or Intel in PC Market... use full 5 forces if this is a likely issue)
> - Industry regulatory environment
> - Life-cycle of industry
>
> \* From Porter's Five Forces: An excellent framework that I've incorporated into this one. I don't use five forces separately for no other reason than habit/preference (though I do use the concepts).

##### 【評註】
這份 4C 清單對 S1 的價值不在「背下來」，而在它是一份**現成的假說產生器**：
每一個 bullet 都可以直接改寫成一個可驗證的假說（例：「Customer concentration and power」→
假說「營收下滑源自前 3 大客戶集中度過高，其中 1 家流失」）。
**建議 S1 把它做成 checklist，在拆樹卡住時用來提示遺漏的分支（補 CE）。**

#### 8.1.3 M&A "FIT" FRAMEWORK

**原文逐字**：
> Use this framework when Company A is looking to acquire or merge with Company B, AND the two companies are different. This framework determines if there's a good fit. If Company A & B are nearly identical, use a capacity expansion framework instead.
>
> "Fit Framework" — General Idea: Use "Core Business Situation Framework" and run it for **Company A, Company B, and Company A+B**
>
> This framework does **not** answer the question IF it's a good idea to merge/acquire. It **assumes you already know that it IS a good idea** and the question is whether or not this particular target company is good fit. To determine IF merging/acquiring is a good idea, use Capacity Expansion Framework instead.

**操作矩陣（原文）**：

| | Customers | Products | Company | Competition |
|---|---|---|---|---|
| **Company A** | | | | |
| **Company B** | | | | |
| **Company A+B** | | | | |

> - Identify synergy in new company
> - Identify opportunities for one-way or mutual exploitation (Classic good "fit" = Company A has huge sales force but lousy products, Company B has minimal salesforce but killer products. Potential sources of synergy: customers, products, distribution, resources, expertise, access to markets, physical assets, unique capabilities, overlapping cost structures)
> - Hint: **Every time there's a synergy, that's one vote in the "good fit" column**

#### 8.1.4 CAPACITY CHANGE FRAMEWORK

**適用（原文）**：
> ABC Company is considering adding capacity (e.g., building a new factory), reducing capacity or acquiring a DIRECT competitor. This is a good framework when understanding industry capacity is the ONLY factor.

**三欄結構（原文逐字）**：

| **Demand** | **Supply** | **Cost of Expansion** |
|---|---|---|
| Determine growth in overall market (How sustainable?) | Determine industry supply | Real costs (can the firm afford it) |
| Determine Growth in firm's market share (How sustainable?) | Segment industry supply by market / market segment | Opportunity cost |
| Segment sources of demand: <br>• Determine each segment's share of total demand <br>• Identify trends in demand by segment | Identify effect of increases in supply on prices | — payback period <br>— break even point |
| Focus on the largest sources of demand and the largest growth rates... use these few "leverage" points to help you understand where the majority of demand is heading | **Possible Benefits**: Introduce technology innovations with capacity expansion; Increase productivity → Lower marginal costs | **Alternatives**: outsource / lease / sub-contract |

**原文的分流規則**：
> For many if not most capacity related cases, figure out if this is a **conceptual case or a numerical case**. If conceptual (20% of time), use this framework. If numerical (e.g, Company A can produce 20 million units at \$4, Company B 10 million units at \$3.50), then you should **graph out supply curves and overlay them with demand curves**. (Tip: practice drawing demand curves from data quickly)
>
> The typical issue is if we add/reduce capacity, what will happen to the **market clearing price**... once we know the market clearing price what impact does that have on profitability... and given that impact should the client add/reduce capacity.

#### 8.1.5 CASE INTERVIEW REMINDERS —— 「永遠要切維度」

**原文逐字（這頁對行銷分析的可移植性最高）**：

> - Compare current year metrics to historical to **FIND THE TREND**
> - Compare "company/client" metrics (revenues, gross margins, unit sales, pricing, changes in segment mix, product mix) to competitors' metrics to determine is it a **COMPANY-SPECIFIC or INDUSTRY-WIDE** problem since you solve these problems very differently
> - **Totals and Averages are very misleading.... Always SEGMENT YOUR METRICS**
>   - Example: Total sales are flat, but Segment A represents 20% of sales, and Segment B represents 80%... Segment A grew 100% this year, Segment B declined by 25%... BUT total sales were FLAT. **If you don't segment, you MISS THE WHOLE POINT.**
> - ALWAYS, ALWAYS SEGMENT... Whenever you want to segment numbers but aren't sure which way, just say, "It seems like getting a more detailed breakdown of revenues would be helpful, do we have any more detailed data on revenues." Often the interviewer will volunteer the segmentation pattern.
> - Oh yeah, did I mention... always, always **SEGMENT YOUR NUMBERS**!
>   - Segment **revenues** (by product, channel, customer type, region) (total revenues, revenues per unit)
>   - Segment **costs** (by fixed vs variable, costs within each segment of value chain) (total costs, cost per unit)
>   - Segment **customers** (by demographics, needs, purchasing patterns, price point, other)
>   - Segment **competitors** (by channel, region, product, customer segment)
> - **Think Out Loud** (Usually in response to receiving some data and realizing your hypothesis is right or wrong)
> - **Ignore your previous knowledge and only use data from the case**

##### 【評註】辛普森悖論的實務版本

那個「Total flat 但 A +100%、B −25%」的例子，本質上就是**聚合掩蓋（aggregation masking）**，
與統計上的 Simpson's Paradox 同源。這是 S1 最該內建的一條硬規則：

> **任何「總量持平／小幅變動」的觀察，在切維度之前都不得下結論。**

而且原文提供了一個很實用的話術：不確定該怎麼切時，就**要更細的資料**，
因為資料的既有切分方式往往就洩漏了業務真正在意的維度。

---

### 8.2 Minto Pyramid Principle — Problem-Definition Framework（本批最重要的外部素材）

**來源**：`Case Interview/Barbara Minto-The Minto Pyramid Principle_ Logic in Writing, Thinking, & Problem Solving-Minto International.pdf`（275 頁）
**實際精讀**：Part Three 開頭 + **Ch.8 Defining the Problem 全章（PDF p.141–152）** + Ch.9 摘要（p.259–260）。其餘章節（Ch.1–7 寫作邏輯、Ch.10–12 版面呈現）僅掃讀目錄與摘要。

> **版權說明**：此書為商業出版品（Minto International 版權所有），本節**以方法結構與操作步驟為主，僅摘引極短句**，
> 不做長篇轉錄。完整原文留在上述本機路徑，需要原句時請直接查閱該 PDF 的對應頁碼。

**這回答什麼商業問題**：「客戶只說了一句『業績不好』——我要問出哪些資訊，才算真的把問題定義完成、可以開始分析？」
**這是 S1 開案對焦最直接可用的框架，比 SMART 更完整**，因為它同時處理了「現況、觸發事件、落差、目標、已做過什麼」。

#### 8.2.1 Sequential Analysis 五問（Minto 引用 McKinsey 內部方法，1972）

Minto 把問題解決拆成五個依序回答的問題，並明確標註每一問屬於哪個階段：

| # | 問題 | 階段 |
|---|---|---|
| 1 | Is there / is there likely to be a problem (or opportunity)? | **Define the problem** |
| 2 | Where does it lie? | **Define the problem** |
| 3 | Why does it exist? | **Structure the analysis** |
| 4 | What could we do about it? | **Find the solution** |
| 5 | What should we do about it? | **Find the solution** |

**【評註】** 這張表是整份材料裡最精確的「階段分界線」：
- 問 1–2 = S1 的開案對焦（**定位問題在哪，還不問為什麼**）
- 問 3 = 拆樹 / 診斷（TMBA 的 Why So?）
- 問 4–5 = 產出建議

注意 **問 2「Where does it lie?」與問 3「Why does it exist?」是分開的兩步** ——
這正好對應 Victor Cheng 的 `SEGMENT/ISOLATE（Where）` vs `Business Situation Framework（Why）`。
三份獨立來源（TMBA、Victor Cheng、Minto）在這一點上完全一致，**這是本批最強的收斂結論**。

#### 8.2.2 問題定義框架的五個元素

Minto 主張，在能開始找解方之前，必須先攤開下列元素（原書用戲劇比喻：布幕拉開看到的舞台場景 → 突發事件 → 劇情）：

| 元素 | 定義 | 對應的提問 |
|---|---|---|
| **Starting Point / Opening Scene** | 問題發生的那個特定領域，通常是一個**可視覺化的結構或流程** | What's going on?（現況） |
| **Disturbing Event** | 打亂上述穩定狀態的事件，觸發了 R1 | What happened?（觸發事件） |
| **R1（Undesired Result）** | 現在這個領域產出的、你**不喜歡**的結果 | What don't we like about it? |
| **R2（Desired Result）** | 你**想要**它產出什麼 | What do we want instead? |
| **Solution（若已有）** | 至今為止已經對這個問題做過什麼 | What has been done so far? |
| **Question** | 由上述推導出的、分析要回答的那一題 | What must be done? |

**Opening Scene 的兩種型態（原書列表）**

| 典型「結構」型場景 | 典型「流程」型場景 |
|---|---|
| Organization charts | Sales or marketing activities |
| Computer configurations | Information systems |
| Plant / office locations | Administrative processes |
| Geographical markets | Distribution systems |
| — | Manufacturing processes |

**Disturbing Event 的三種來源（原書分類）**

| 來源 | 定義 | 例子 |
|---|---|---|
| **External** | 環境端發起的改變 | 新競爭者出現、技術轉換、政府或客戶政策轉向 |
| **Internal** | 公司自己發起的改變 | 新增業務流程、導入新系統、拓展新市場、調整產品線 |
| **Recently Recognized** | 對「需要改變」的認知或證據浮現 | 某產品/流程績效落後、營運結果低於水準、市調暗示顧客態度轉變 |

> 原書提醒：若資訊不足以指認 Disturbing Event，**不要硬掰一個**，直接跳到 R1。

**R2 的書寫規則（原書重點）**
- 要**盡可能具體、可量化**，否則無法在多個候選解方之間做選擇。
- 應以「end-product（終局狀態）」措辭陳述，例：達成年度成長目標／上市時間縮短 1/3／有足夠產能因應預測需求。
- 若當下無法具體化 R2 → **把「確定 R2」本身列為分析的第一步**。

**【評註】R2 規則與 SMART 的關係**：Minto 的 R2 要求 ≈ TMBA SMART 的 Measurable + Time-bound。
兩者可以合併成 S1 的同一個檢查點。但 Minto 多給了一條非常實用的**逃生門**：
> 允許「R2 尚未確定」這個狀態存在，並把它明確登記為分析任務 #1。

這比 SMART 的「不合格就打回」更適合真實開案 —— 很多案子一開始客戶真的說不出目標數字。

#### 8.2.3 七種「讀者所處位置」—— 決定你該回答哪一題

這是 Minto 章節裡最可程式化的一段。**同樣的 R1/R2，客戶站在不同位置，要回答的問題完全不同**：

| # | 客戶處境 | 該回答的 Question | 常見度 |
|---|---|---|---|
| 1 | 不知道怎麼從 R1 到 R2 | How do we get from R1 to R2? | 最常見 |
| 2 | 自認知道怎麼做，但不確定對不對 | Is it the right solution? | 最常見 |
| 3 | 確定知道怎麼做，但不知道怎麼執行 | How do we implement the solution? | 最常見 |
| 4 | 做了，但方案失效了 | What should we do (now)? | 變形 |
| 5 | 有好幾個候選方案，不知道選哪個 | Which one should we pick? | 變形 |
| 6 | 知道 R1，但講不出夠具體的 R2 | （先做）What exactly is R2? | 少見 |
| 7 | 知道 R2，但不確定自己是不是在 R1 | Are we actually at R1?（典型 benchmarking 研究） | 少見 |

**【評註】這張表可以直接變成 S1 的分流器（router）**。
S1 在開案對焦時，只要問一句「**你們針對這件事已經做過什麼了嗎？**」，
就能把使用者導到 1–7 其中一格，而每一格對應完全不同的分析設計：
- 落在 #1 → 走完整議題樹 + 根因分析
- 落在 #2 → 走**假說樹**（驗證既有方案），不要重拆議題樹
- 落在 #3 → 跳過診斷，直接做**演繹樹**（實施路徑）
- 落在 #6 → 先做目標設定工作坊，不要碰資料
- 落在 #7 → 做 benchmarking / 現況量測，不做因果分析

這正好補上了 TMBA 材料中「三種樹該選哪一種」缺少的**判斷依據**。

#### 8.2.4 問題定義 → 簡報導言（SCQA）的機械轉換

原書提供一條機械規則：把問題定義框架**由左至右、由上而下讀**，
**讀者已知的最後一項永遠是 Complication（衝突）**，它觸發 Question。

```
S (Situation)    = 現況（Starting Point）
C (Complication) = 讀者已知的最後一項（依處境不同，可能是 Disturbing Event+R1+R2，
                   也可能是「我們已經有方案了」，或「方案失效了」）
Q (Question)     = 由 C 觸發的那一問
A (Answer)       = 金字塔頂端的結論
```

三種常見組合（原書圖示的結構，非逐字）：

| 客戶處境 | S | C | Q |
|---|---|---|---|
| 處境 1 | 我們有一個運作良好的流程 | 它現在沒給我們想要的結果（R1, R2） | 該怎麼辦？ |
| 處境 2/3 | 我們有個問題（Situation, R1, R2） | 我們想出了一個方案 | 這是對的方案嗎？／該怎麼執行？ |
| 處境 4 | 我們有問題且想了方案 | 方案沒效（R1-b） | 該怎麼辦？ |

**【評註】** 這與 TMBA 的「執行摘要」直接接得上：
TMBA 說執行摘要要含「目標、策略、預期成效」，Minto 則給了**導言前半段（S-C-Q）的產生規則**。
兩者合起來就是完整的簡報開場。

#### 8.2.5 Ch.9 Structuring the Analysis 摘要（原書 p.259–260 的 checklist）

原書把「結構化分析」濃縮成三步：
1. 用**診斷框架（diagnostic frameworks）**呈現問題領域的結構
   - 呈現各單元如何作為一個系統互動
   - 追蹤因果活動鏈
   - 分類可能的問題成因
2. **蒐集資料以證實／推翻**結構中哪些元素造成了問題
3. 用**邏輯樹（logic trees）** 來：
   - 產生並測試建議解方
   - 揭露一串想法之間內含的關係

配套的「Structuring an Analysis」思考技巧（原書 KEY THINKING TECHNIQUE 欄）：
> 定義問題 → 用診斷框架展開問題領域的細部結構 → 對可能成因建立假說 → 蒐集資料以證實/推翻假說

**【評註】診斷框架 vs 邏輯樹 —— 這是一個常被混淆的區分**
原書明確抱怨業界把 "Issue Analysis" 一詞濫用到幾乎指任何邏輯樹，導致大家搞混。
按原書的區分：
- **診斷框架（diagnostic framework）**= 用來找**原因**的樹（≈ TMBA 的議題樹）
- **邏輯樹（logic tree）**= 用來產生並檢驗**解方**的樹（≈ TMBA 的演繹樹）
- 兩者是**不同用途的樹**，不該混用

這與 TMBA 的三樹分類高度一致，且提供了更嚴格的用詞紀律。

---

### 8.3 市場規模估算（Market Sizing）—— Ace Your Case III

**來源**：`Case Interview/Ace-your-case-iii-market-sizing-questions.pdf`（WetFeet Insider Guide, 2nd ed., 2011, 76 頁）
**實際精讀**：Ch.1–3（At a Glance / The Interview Unplugged / Market-Sizing Case Rules）+ 15 題練習題題目。
Ch.4–5 的完整解答與評註**未逐題精讀**。

> **版權說明**：此 PDF 首頁明載「PHOTOCOPYING IS PROHIBITED」。本節只摘取**方法規則與題目清單**，不轉錄解答內文。

**這回答什麼商業問題**：「這個市場有多大？值不值得進？」以及 TMBA 材料裡的「**費米推論**」該怎麼具體操作。

#### 三條核心規則（原書逐字，短引）

> **Rule 1: Use round numbers**
> **Rule 2: Show your work**
> **Rule 3: Use paper and calculator**

原書對這三條的說明要點（改寫）：
1. **用整數** —— 因為精確答案本來就不重要，用好加減乘除的數字。原書舉例：紐約人口就算一千萬；一張標準紙長度 11 吋就進位成 1 呎。
2. **秀出過程** —— 原書說得很直白：`your exact answer matters less than the path you took to get there`。市場規模題只是個平台，用來測你的分析、創意與對數字的自在程度。
3. **可以用紙筆和計算機** —— 保持冷靜、有條理比心算快更重要。

#### 拆解方向：由大到小

原書明確指出市場規模題**不像其他案例題那樣需要框架**，但有拆解的慣用路徑：

> 大多數情況下，**work from big to small**：
> 最大的母體是什麼（例：全美人口）？→ 哪些次群體可能需要這個產品？→ 這些怎麼串起來？

原書用衝浪板市場示範要問的基本問題：
- 有多少人衝浪？
- 一個典型衝浪者擁有幾塊板？
- 多久換一次新板？
- 除了個人衝浪者，還有其他大宗採購者嗎？
- 有二手板市場嗎？

接著做基本計算：`衝浪人數 × 每年新板數 + 其他類型顧客的採購總量 …`

原書並點出面試官真正在看什麼（短引）：
> `Did you assume that everyone in the U.S. is a potential surfer, or did you try to estimate the population in prime surfing areas...`

**【評註】這句話就是「常識校準」的判準**，可以直接寫成 S1 的檢查點：
> 估算的第一層母體，是否已經套用了**合理的地理／人口／情境限縮**？
> 若直接拿全國人口當分母，幾乎必然高估。

#### 題型清單（原書 15 題中的前 9 題，作為 S1 的練習題庫種子）

| # | 題目 |
|---|---|
| 1 | How many bars of dark chocolate are sold in the U.S. each year? Is the market growing or shrinking? |
| 2 | Purina is thinking of entering the penguin-food market. Can you help Purina evaluate whether there's a reasonable market for Penguin Chow? |
| 3 | How many adult diapers are sold each year in Ohio? |
| 4 | How many coffins are sold each week in Los Angeles? |
| 5 | How many cups does Starbucks use each week in its U.S. operations? |
| 6 | How much bamboo does the world's panda population eat? |
| 7 | What is the average number of chairs in a house? |
| 8 | How many pairs of jeans are sold in the U.S. each year? |
| 9 | How many unique people attend events at the Rose Bowl every year? |

原書對每題都要求填三欄：`KEY QUESTIONS TO ASK` / `BASIC NUMBERS` / `TRACK THE NUMBERS DOWN`
——**這三欄本身就是一個可重用的估算工作表模板**（見第 11 節）。

#### 市場規模題的偽裝形式（原書要點）

原書提醒：市場規模題常常**不是直接問的**，而是藏在別的問題裡：
- 直接型：`How large is the U.S. market for surfboards?`
- 偽裝型：`Should Fidelity come out with a mutual fund targeted at high-net-worth individuals?`
  → 必須自己剝掉外層，辨識出核心是市場規模題
- 複合型：策略或營運題中內含一段市場規模估算，才能給出建議

**【評註】** 這對 S1 很重要：**「該不該做 X」類型的提問，內部幾乎一定藏著一個市場規模／效益估算子題**。
S1 在拆樹時應該主動辨識並把它獨立成一個葉節點。

---

### 8.4 各家 Casebook 的結構化紀律（Bain / BCG / Columbia / Berkeley）

**來源與覆蓋率**：

| 檔案 | 頁數 | 覆蓋 |
|---|---|---|
| `Bain Casebook/Bain Case Interview.pdf` | 14 | 已萃取全文，**掃讀** |
| `BCG Casebook/BCG Case Interview.pdf` | 14 | 已萃取全文，**掃讀 + 關鍵段精讀** |
| `Columbia Case Interview Tips.pdf` | 3 | **全讀** |
| `Berkeley - Case Interview Guide.pdf` | 26 | 已萃取全文，**掃讀** |
| `case_interview_handbook_2016_7_1.pdf` | 12 | 已萃取，**未精讀** |
| 其餘 19 個 PDF（Kellogg / Fuqua / Vault / Case in Point / Ace Your Case I & II / McKinsey Casebook 等） | 合計 >1,500 頁 | **未讀**（見第 12 節） |

#### 【材料原文】BCG —— 對「套框架」的警告

> `simplistic answer develop a framework unique to the situation presented. Imposing a generic framework is generally a recipe for failure.`

> `Interviewers look for a student to dig deep on issues instead of just skimming the issues. Students should try to determine the most important issues and ask penetrating questions regarding these issues.`

> （論「只列要看什麼、不講為什麼」的缺點）`instead they should explain why they would look at something, a hypothesis about what types of factors drive the business or a range of possibilities.`

> （論 Lack of conviction）`If I can get an interviewee to change his or her mind with one question, what will happen when I leave him or her alone with a skeptical client?`

#### 【材料原文】Columbia / Deloitte —— 框架的定位

> `Create a framework. This would guide you through your thought process and help keep you on track. Remember to keep a broad framework so that you don't hit a dead end.`

> `Stay organized. When discussing a specific point, keep in mind the reason you are discussing it and how it fits into your initial framework.`

> `Think out loud. Communicate your train of thought clearly. Even if you have considered, but rejected, some alternatives, tell the interviewer what they were and why you rejected them.`

> `Use a framework as a checklist of areas to investigate`
> `A framework is a tool, not the solution`

Columbia 對案例面試目的之陳述：
> `...ambiguous business problems and determine how you employ structured thinking to reach logical and intelligent conclusions. Firms want to know how you identify, organize, and approach problems.`

#### 【評註】這四句話合起來是 S1 最重要的「防呆」規則

把上述來源交叉起來，得到三條**互相補強**的紀律：

1. **框架是清單，不是答案**（Columbia）—— 4C／獲利樹的用途是**檢查有沒有漏**（補 CE），不是拿來當結論。
2. **不要硬套通用框架**（BCG）—— 必須針對當下情境**客製**一棵樹。這與 TMBA 的「三種樹選一種」是同一件事的兩種說法。
3. **每個分支都要附上「為什麼要看它」**（BCG）—— 也就是每個分支都要帶一個**假說**，而不只是一個要查的欄位。

**這第 3 條是 S1 最該內建的品質門檻**：
> 拆出來的每個葉節點，如果不能填完「我認為 ____，因為 ____，若為真則資料上會看到 ____」，
> 它就不是一個可分析的假設，只是一個待查清單項。

**【評註】** 這也解釋了 TMBA 材料裡「議題樹 vs 假說樹」的實務差別：
議題樹的葉節點是**問句**，假說樹的葉節點是**可證偽的陳述句**。
S1 若要輸出「可分析的假設」，最終交付的必須是**假說樹**形態，議題樹只是中間產物。

---

## 9. 行銷理論架構

### 9.1 全球品牌管理（Keller CBBE 體系）

**來源**：Notion「整理1」`3252b4ffdf0b8111a736de28a4641333` 與「整理2」`3252b4ffdf0b818f8708f9d7b0357749`（父頁：全品管 → 碩二課程 → NTU）
**覆蓋**：兩頁**皆 100% 讀完**。兩份是同一份講義的兩次整理，整理2 較完整（補上英文對照與更多細節），**內容高度重疊**。

> **【材料性質說明】** 這兩頁是包子自己整理的期中考重點筆記，內容為 Keller《Strategic Brand Management》體系。
> 以下為**筆記原文的結構化轉錄**，非萃取者自行補充。

#### 9.1.1 策略品牌管理的四大步驟

| 步驟 | 內容 | 章節 |
|---|---|---|
| I. 識別與發展品牌計畫 | 三大核心模型：品牌定位模型、品牌共鳴模型、品牌價值鏈 | Ch2, Ch3 |
| II. 設計與實施品牌行銷計畫 | 品牌要素選擇、行銷組合 4Ps、溝通策略、數位時代行銷、次級品牌聯想 | Ch4–8 |
| III. 衡量與解釋品牌績效 | 品牌稽核、品牌追蹤研究、品牌權益管理系統 | Ch9–11 |
| IV. 成長與維持品牌權益 | 品牌架構：品牌組合、品牌層級、品牌延伸 | Ch12–13 |

**次級品牌聯想（Secondary Brand Association）的八個來源**（原文列表）：
公司（品牌策略）／國家或地理區域（產品來源）／分銷管道（通路策略）／其他品牌（**co-branding**）／人物（**licensing**）／代言人（**endorsements**）／活動（**sponsorship**）／其他第三方（獎項或評論）

#### 9.1.2 CBBE（Customer-Based Brand Equity）

**定義（原文）**：品牌知識對顧客對該品牌行銷活動的反應所產生的**差異化效果（differential effect）**。

**三個組成部分**：
1. **差異化效果** — 不同品牌會導致消費者做出不同反應；*若沒有差異，競爭可能會基於價格*
2. **品牌知識** — 差異化效果是顧客學習、感受、看到、聽到的結果
3. **顧客對行銷的反應** — 可觀察的行為：品牌選擇、廣告回想、對促銷的反應、品牌延伸的評估

**正向 CBBE 的可觀測表現（→ 這是可以直接做成 KPI 的）**：
- 對**價格上漲較不敏感**（less price sensitive）
- 更易於接受**品牌延伸**（brand extension）

#### 9.1.3 品牌知識的兩大組成

**A. 品牌覺察（Brand Awareness）**

| | 品牌識別（Recognition） | 品牌回想（Recall） |
|---|---|---|
| 線索 | 給予**品牌**作為線索 | 給予**產品類別／需求／使用情境**作為線索 |
| 能力 | 確認之前曾暴露於該品牌 | 從記憶中提取品牌 |
| **何時更關鍵** | 在**銷售點（point of sale）**做決策時 | 在**遠離購買點**的情境做決策時 |

**品牌覺察的三個優勢**：
1. **學習** — 影響品牌聯想的形成與強度
2. **考慮度** — 增加品牌進入**考慮組合（consideration set）**的可能性
3. **選擇** — 在**低涉入（low involvement）**決策中，消費者可能直接購買有覺察度的品牌
   - 低涉入情境定義（原文）：消費者缺乏購買**動機**、**能力**，或**機會**做出深思熟慮的選擇
   - 此時消費者依賴**捷思法（Heuristic）**快速決策

**建立覺察的兩個方法**：重複暴露（Repeat exposure）／品牌配對（Pairing，把品牌與其產品類別配對）

**B. 品牌形象（Brand Image）**

- **建立要件**：連結**強烈（strong）、有利（favorable）、獨特（unique）**的聯想
- **聯想的兩種類型**：

| | 品牌屬性（Attributes） | 品牌利益（Benefits） |
|---|---|---|
| 定義 | 描述產品/服務的特徵 | 消費者賦予屬性的個人價值與意義 |
| 性質 | **客觀（Objective）** | **主觀（Subjective）** |
| 例 | iPhone 螢幕尺寸 | 長電池壽命帶來的安心感 |

- **衡量聯想的三個維度**：
  1. **強度（Strength）** — 越個人相關（personal relevance）、長期越一致（consistency）則越強；直接經驗與可信口碑最強
  2. **有利性（Favorability）** — 是否擁有滿足顧客需求的相關屬性與利益
  3. **獨特性（Uniqueness）** — USP 或可持續競爭優勢

#### 9.1.4 品牌定位：POD / POP（**這節對行銷分析的可操作性最高**）

**品牌定位定義（原文）**：設計公司產品和形象的行為，使其在**目標顧客的心智中佔據獨特且有價值的位置**。
**工具**：知覺圖（Perceptual maps）

**差異點 POD（Points-of-Difference）**
- 消費者**強烈聯想且僅與特定品牌相關**的屬性或利益
- 兩種類型：(1) 功能性／績效相關；(2) 抽象／形象相關
- **佐證點（Proof Points）／相信理由（RTBs）** — 確保 POD 可交付：功能設計、關鍵成分、重要背書

**共同點 POP（Points-of-Parity）的三種類型**

| 類型 | 定義 | 例 |
|---|---|---|
| **類別 POP** | 該產品類別**被期望**具備的屬性或利益 | 銀行需提供支票、儲蓄、ATM |
| **競爭性 POP** | 旨在**抵消競爭者的 POD**，在對手強項上「打平（break even）」 | — |
| **相關性 POP** | 因某些正向聯想而**衍生的潛在負向聯想** | 低價 vs 高品質；美味 vs 低卡；強大 vs 安全 |

**相關性 POP 的核心洞見（原文）**：許多構成 POP 或 POD 的屬性/利益之間是**負相關（inversely correlated）**的。
*案例（原文）*：早期 Macintosh 強調易用性（POD），但在商用市場被推論為不夠強大；
Apple 後續透過宣傳「人們真正使用的電腦才是最強大的」來重新定義「力量」，以解決相關性 POP。

**品牌金句（Brand Mantra）**：三到五個詞的短語，捕捉品牌定位的無可辯駁的本質；主要功能是**內部指導**（決定推出什麼產品、跑什麼廣告、怎麼賣）與維持形象一致。

**【評註】POD/POP 是很好的「假說產生器」**：
定位類提問可以機械地拆成三支 —— 我們的 POD 是否被感知到？我們的類別 POP 是否達標？我們是否有未處理的相關性 POP？
每一支都可以直接對應到問卷/知覺圖的量測設計。

#### 9.1.5 品牌共鳴金字塔（Brand Resonance Pyramid）

**目標（原文）**：從品牌定位的競爭優勢開始，透過一連串步驟，**創造與顧客之間強烈、活躍的忠誠關係**。

**層級 1：品牌能見度（Brand Salience）／識別**
- 品牌在多大程度上**居於心智首位（top-of-mind）**且易於回想或識別
- 兩大維度：**深度（Depth）**= 被想起的可能性與容易程度；**廣度（Breadth）**= 在不同購買/使用情境中被想起的範圍
- 關鍵啟示（原文）：**若缺乏品牌覺察，就不可能有品牌能見度**

**層級 2：品牌意義（Brand Meaning）**

| 要素 | 說明 | 關鍵屬性/利益 |
|---|---|---|
| **品牌績效（Performance）**（意義 I） | 滿足顧客**功能性需求**、客觀品質評估、實用/美學/經濟需求的程度 | 主要成分與附加特色、可靠性/耐用性/可維修性、服務有效性/效率/同理心、風格與設計、價格 |
| **品牌形象（Imagery）**（意義 II） | 品牌的**無形方面**，取決於產品的**外在屬性**，滿足**心理或社會需求** | 用戶輪廓（人口統計/心理描繪）、購買與使用情境、個性與價值觀、歷史/傳承/經驗 |

- **品牌個性五維度（原文，Aaker）**：Sincerity（真誠）、Excitement（刺激）、Competence（勝任）、Sophistication（精緻）、Ruggedness（強韌）
- **特色疲勞（Feature Fatigue）**（原文）：消費者在購買前想要**多功能（capability）**，但使用後更看重**正確的（right）**功能（**可用性 usability**），應避免**功能膨脹（Feature Bloat）**

**層級 3：品牌反應（Brand Responses）**

- **品牌判斷（Judgments）**：
  - **品質** — 基於特定屬性與利益的整體評估，是品牌選擇的基礎
  - **信譽（Credibility）** — 三成分：**專業性（expertise）**、**可信賴性（trustworthiness）**、**可愛性（likability）**
  - **考慮度** — 是否認真考慮購買
  - **優越性** — 是否認為品牌獨特且優於其他
- **品牌情感（Feelings）六種**：
  - 體驗性與即時性（強度遞增）：**溫暖 Warmth → 樂趣 Fun → 興奮 Excitement**
  - 私密性與持久性（嚴肅性遞增）：**安全感 Security → 社會認可 Social Approval → 自尊 Self-Respect**

**層級 4：品牌共鳴（Brand Resonance）**

- 定義：顧客與品牌「**同步（in sync）**」的關係性質與程度
- 兩大維度：**強度（Intensity）**= 心理連結深度；**活動水平（Activity）**= 忠誠行為的頻率與購買外活動
- **四個類別（標註 I=Intensity, A=Activity）**：

| 類別 | 維度 | 定義 |
|---|---|---|
| **行為忠誠（Behavioral loyalty）** | A | 重複購買的頻率 + 品牌佔據的**類別銷量份額（share of category volume）** |
| **態度依附（Attitudinal attachment）** | I | 超越滿意度，視品牌為「摯愛」或「最愛」 |
| **社群意識（Sense of community）** | I | 對其他用戶或公司員工的**歸屬感（sense of affiliation）** |
| **積極參與（Active engagement）** | A | 願投入時間/精力/金錢**超出**購買或消費範疇，如成為品牌大使 |

**品牌建立的啟示（原文）**：強勢品牌應同時訴諸**理性（head）**與**感性（heart）**，因為 Performance 與 Imagery 共同決定品牌意義。

**【評註】顧客忠誠的四分類 = 四組不同的量測設計**
這張表對 S1 極有價值，因為「顧客忠誠度下滑」這種模糊提問可以**機械地拆成四個可分析分支**：
- 行為忠誠 → 交易資料（回購率、購買頻率、品類份額）
- 態度依附 → 問卷（NPS、態度量表）
- 社群意識 → 社群/社群媒體資料
- 積極參與 → UGC、推薦、參與活動的行為資料

**這是把「涉入度、顧客忠誠」轉成可分析假設的現成模板**（見第 11 節）。

#### 9.1.6 品牌價值鏈（Brand Value Chain）

- **目標**：追蹤品牌價值創造過程，理解行銷支出與投資的**財務影響**
- **流程（原文）**：`行銷投入 (Marketing) → 顧客心智 (Customer Mind-set) → 績效與價值 (Performance & Values)`

**【評註】** 這條鏈就是行銷分析歸因問題的骨架：投入 → 心智中介變數 → 財務結果。
S1 在處理「行銷預算有沒有效」的提問時，應該強制使用者指出**中介變數在哪一段量測**。

---

### 9.2 競爭策略與價值創造

**來源**：Notion「3/26 講義隨筆+整理」`3252b4ffdf0b819e9b0ee5e78b10c83d`（父頁：國企策 ICU → 碩二課程 → NTU）
**覆蓋**：**100% 讀完**。內容為國企策課程的講義整理 + 課堂隨筆，混合了理論框架與實際案例評論。

#### 9.2.1 策略的兩層與價值創造公式

**【材料原文】**
> Strategy：
> - Competitive Strategy (Business) → { Internal organization (內部組織結構) ∪ External environment (外部產業結構) }
> - Growth Strategy (Corporate)

**企業如何有效提升獲利？→ 比別人多 = 競爭優勢（原文三條）**
1. **帶給消費者價值** — 問題是太貴會使產品曲高和寡 → 重點在如何提升產品的 "Value"
2. **Cost down** — Supplier 包含了員工，如果薪資福利太低他們會跑 → 產能下降 → 成本反而提升
3. **Willingness to sell** — 員工的願售價格如同他們的賣身契，價格低就能節省很多成本

**如何拉高消費者願付價格（Willingness To Pay, WTP）？**（原文）
- 特殊的互補情形；例如：電影院配合托嬰服務
- 最終目的是要提升產品附加價值

**如何降低供應商的願售價（Willingness To Sell, WTS）？**（原文）
- 大量採購 or 簽訂長期合約
- 例如：Nike 每年召集供應商辦教育訓練，更新技術資訊，並且以更低廉的價格提供給供應商產品，同時不限制供應商接其他競爭者的單
- 保證供應商會來必有一定的單量 → 形成互利互惠 → 供應商自然願意降價銷售
- 最終目的在放寬成本結構

**【評註】價值棒（Value Stick）的可分析形式**

材料描述的其實就是價值棒模型。可以寫成：

$$\text{企業創造的總價值} = \text{WTP} - \text{WTS}$$

$$\underbrace{(\text{WTP} - P)}_{\text{顧客剩餘}} + \underbrace{(P - C)}_{\text{企業利潤}} + \underbrace{(C - \text{WTS})}_{\text{供應商剩餘}} = \text{WTP} - \text{WTS}$$

其中 $P$ = 售價，$C$ = 採購/投入成本。
**這給了 S1 一棵極乾淨的「獲利改善」議題樹**：要嘛拉高 WTP（差異化），要嘛壓低 WTS（供應鏈），
兩者都不是單純的「漲價」或「砍成本」—— 這正好呼應材料裡「砍薪資反而提高成本」的警告。

**Value Creation vs Value Appropriation（原文）**
> Value appropriation → 從消費者或客戶身上獲取更多價值利益
> → Limiting imitation（限制模仿）
> → Limiting size

**如何面對進入者威脅（原文）**
> Entry deterrence strategy — 透過減低整體企業數量，藉以優化產業利益結構（就是建立進入障礙！）

#### 9.2.2 價值鏈（Value Chain）

**【材料原文】**

| Primary activities（主要活動，和產品、服務有直接相關） | Support activities（支援活動） |
|---|---|
| Inbound logistics | Firm infrastructure |
| Production operation | Finance、Accounting、Legal |
| Outbound logistics | Human resource management |
| Marketing and Sales | Technology development |
| Service | Procurement（商業模擬中不明顯） |

> 資源活動（就是管會中的 Overheads）

**商業模擬中的 12 個決策點（原文，含隨筆註記）**
1. **Outsourcing v.s. Own plants** → 要有學習效果和規模經濟，作為 First mover 進入新市場才有意義；通常 **75～85% 的產能利用率**才有經濟效益
2. **Location of plant** → 要考量學習曲線的效果
3. **Energy consumption**
4. **Product selection** → 要進入哪個市場；持續研發新科技或舊科技，單位成本逐漸產生落差；像**實質選擇權**，先後順序對決策影響很大
5. **Scrap percentage** → 新技術廢品率通常較高
6. **Inventory management** → 對 Cost leader 的策略來說超重要
7. **Features** → 對 Cost leader 來說「點到為止」就好，約等於平均即可
8. **Promotion** → 對走差異化路線的策略會很重要
9. **Pricing** → **價格就是最好的行銷**
10. **Data protection**
11. **Product market position**
12. **Logistic Priority** → 歐洲有碳的邊境稅

> Note. ESG 不見得會降低成本（前期高投入），但會改變消費者型態。
> Note. 高度影響 ESG 績效表現的因子：個別因素、CEO、產業特性（有，但其實沒很多）

#### 9.2.3 三種通用競爭策略（Generic Business Strategies）

**【材料原文】**

**1. Cost leadership strategy**
> 一套整合性的行動組合，目的在以相對低於競爭者的總成本，生產具有顧客可接受之特徵與價值的產品或服務
> 維持近乎相同的價值水準下，以更低的成本創造價值（create about same **V** for less **C**）

*資源與能力推動的整合策略*：
- 大規模、效率化產能的積極建置 — 迅速投資或擴充具經濟規模的生產／營運設施，以攤薄固定成本
- 倚賴**經驗曲線（experience curve）**持續追求成本降低 — 隨累積產量提升而精進流程、減少錯誤與材料浪費
- 嚴格的成本與間接費用控制 — 精實管理（lean management）與預算控管
- 避免邊際貢獻不足的客戶帳戶 — 篩選毛利率過低或交易成本過高的顧客
- 在價值鏈各環節進行成本最小化 — R&D、售後服務、銷售團隊、廣告皆效率導向
- 充分運用財務資源（舉債能力）
- 資產管理能力 — 技術/營運/工程效率；經驗與學習

*Pitfalls*：
- 過度聚焦於一項或少數價值鏈活動
- 所有競爭者皆使用同質的投入或原材料
- 策略過於容易被競爭者複製或跟進
- 在差異化面向上缺乏同等水準（lack of parity on differentiation）
- 當顧客可取得更透明的價格資訊時，成本優勢被侵蝕

**2. Differentiation strategy**
> 一套整合性的行動組合，目的在以顧客可接受的成本水準下，提供在顧客眼中具有重要差異之產品或服務
> 在幾乎相同的成本下，創造出更高的價值（create **more V** for about the same **C**）

*差異化的多元形式*：聲望或品牌形象／技術／創新／產品服務特徵／顧客服務／經銷通路網絡／**行銷資源（例如：大數據應用與顧客忠誠度計畫）**／創新與新產品開發能力（專利、著作權、高素質研發團隊）

*Pitfalls*：
- **無價值的獨特性** — 雖具差異，但未為顧客創造實質或感知價值
- **過度差異化** — 特徵過多或過於尖端，超出目標顧客需求或接受度
- 價格溢酬過高 — 使顧客轉向更具成本效益的替代品
- 易於模仿：
  - **水平差異化（Horizontally differentiated）** — 品質與價格相近，但因「品味差異」吸引不同顧客；若市場喜好趨同，優勢即削弱
  - **垂直差異化（Vertically differentiated）** — 在主要屬性上訴求同一顧客群；若差異幅度不足或成本過高，易被超越
- 產品線延伸稀釋品牌識別 — 過度擴張系列導致核心品牌形象模糊
- 買賣雙方對差異化的認知落差 — 賣方認為的獨特價值未必被顧客感知或認同

**3. Focus strategy**
*定義與促成動機*：大型企業可能忽視小眾利基市場；資源受限的企業無法與全方位競爭者對抗，轉而專注於狹窄市場；專注者可更有效率地服務窄幅市場區隔。

*Pitfalls*：狹窄區隔內的成本優勢流失／仍可能遭受新進入者與模仿者競爭／過度聚焦導致無法滿足顧客新需求

**Integration of Cost Leadership and Differentiation（原文）**
- 難以在所有維度上全面超越對手
- 提供卓越顧客利益通常成本高昂
- 降低成本往往伴隨品質折衝
- 為低成本配置活動的方式與為高價值配置活動的方式差異甚大
- 既缺乏成本領導的決心與專業，也無法維持真正差異化所需的獨特資產與能力 →（**stuck in the middle**）

**課堂隨筆的真實案例（原文）**

| 案例 | 對應失敗模式 |
|---|---|
| **Clubhouse** | Differentiation pitfall — 一開始主打具獨特性的聊天平台，但聲音的獨特性不足（可被 Podcast 取代）；只能邀請進入，用戶群不穩定；曲高和寡（Unique 過頭）→ **因此估計 Market share 很重要（尤其是在做需求評估的時候）** |
| **麗嬰坊** | Focus pitfall — 專打童裝市場，但因主打機能感的 Uniqlo & 主打設計感的 Zara 擠壓，銷售一直下滑 → 利基市場被進入後，聚焦在基本面的麗嬰坊被迫歇業 |
| **Lenovo** | Focus pitfall — 想進軍電競手機市場，但因市場太小，被迫退出 |
| **HTC** | Stuck in the middle 典型 — 技術追不上 Leader，價格又被後進者超越 |
| **Toyota** | Cost leadership 的 Network & relationships — 透過上下游整合建立長期合作關係 → Ecosystem；因電動車疑慮反而復活 |

> Cost leadership strategy 的 Distinctive capabilities or competence（原文）：
> Functional skills／Market skills (incremental strategy)／Network & relationships

#### 9.2.4 破壞式創新與藍海

**【材料原文】**
> Incumbent's sustaining trajectory → 傳統大廠、既存廠商大概都在這
> Entrant's disruptive trajectory → 破壞式創新：破壞既有廠商的存在價值，進而以新產品替代原先主流

| **Blue Oceans**（既要又要的策略） | **Red Oceans** |
|---|---|
| 創造無人競爭的市場空間（create uncontested market space） | 在既有市場中競爭（compete in existing markets） |
| 使競爭變得無關緊要（make the competition irrelevant） | 擊敗競爭者（beat the competition） |
| 創造並捕捉新需求（create and capture new demand） | 挖掘並利用現有需求（exploit existing demand） |
| 打破「價值–成本」權衡（break the value-cost trade-off） | 接受「價值–成本」權衡（make the value-cost trade-off） |
| 將企業價值鏈配置於「同時追求差異化與低成本」 | 使價值鏈與整體策略保持一致（低成本／差異化／聚焦） |

#### 9.2.5 商業模式（Business Model Canvas）

**【材料原文】** —— 注意每一項都附了一個**提問**，這正是 S1 需要的形式：

| 元素 | 對應提問 |
|---|---|
| **Value Proposition**（價值主張） | Why 要跟你買？ |
| **Key Activities**（怎麼主張） | How? 要做什麼？ |
| **Key Resources** | 關鍵資源是什麼？Distinctive capabilities（有什麼特殊優勢？）／Financial resources (debt)／Operational resources（例如：中美產能配置上的彈性空間） |
| **Key Partners** | 能否建立 Eco-system？（例如：CUBA） |
| **Customer Segments** | 顧客地圖，找 TA |
| **Customer Relations** | 怎麼互動？ |
| **Channel** | 怎麼接近我？ |
| **Cost** | — |
| **Revenue** | 綜合上述後得到的結果 |

> 以上 = **Profit formula**

**【評註】** 這份 canvas 的「提問版」比標準版更適合 S1 —— 每一格都已經是一個開放式問句，
可以直接當成開案訪談的訪綱骨架（呼應 TMBA Step 5 的「需事先擬好訪綱」）。

---

### 9.3 設計思考 / 極限需求設計（TMBA 07/13 社課）

**來源**：Notion `3252b4ffdf0b8163988edde4e2276a4a`（碩二版）與 `22f2b4ffdf0b802daf1be1971ad40349`（碩一版）
**覆蓋**：100%。兩頁**逐字相同**，是同一份筆記的兩個副本。筆記本身**很短且未寫完**（結尾停在「訪問：」）。

**【材料原文（全文）】**
> 為極限需求而設計 → 只有 1% Cost 的嬰兒保溫箱（For 落後環境的早產兒，每年約一百萬名）
> Initially key Q：保溫箱太貴，無法負擔
> 走訪印度、尼泊爾之後發現：電供普及度不足、基礎設施建設不足、物理距離過遠、交通障礙
> Prototype：Embrace 早產兒保溫袋（外袋 = 溫度計，內袋注入熱水）
> - Challenge：當地婦女不信任西方醫療，會自行對處方打折
> - Update：熱水持溫不夠，後來改用石蠟（有效延長溫度保存的時間）
> - 普及率：西方消費就會捐款過去
>
> 設計挑戰：協助視障者重新設計「好看且實用的手錶」
> - 核心問題在哪？
>
> 訪問：（未完）

**【評註】這則短筆記其實示範了一次完整的「問題重新定義」**，對 S1 極有價值：

```
原始提問（Initially key Q）：「保溫箱太貴，無法負擔」
        ↓ 實地走訪（質性研究）
發現真正約束：電供不足、基礎設施不足、距離過遠、交通障礙
        ↓ 問題重新定義
真正的問題不是「價格」，而是「必須在無電、無基礎設施的環境下運作」
        ↓
解方形態因此完全改變（不是做便宜的保溫箱，而是做不用電的保溫袋）
```

**這是 S1 應該內建的一條警告**：
> 客戶陳述的 R1（「太貴」）可能只是**表層症狀**。
> 在投入分析前，若成本允許，應先做一輪質性探查驗證問題陳述本身是否成立。
> 對照 Minto 的框架：這等於在挑戰客戶給的 **Starting Point / Opening Scene** 是否畫錯了範圍。

注意這裡也出現了 TMBA 主 PDF 的「甜蜜點」概念的反面案例：
若停在「太貴」這一層就拆樹，整棵樹都會長錯方向。

---

### 9.4 分析工具選型（Roger's lecture, 07/27）

**來源**：Notion `3252b4ffdf0b81a08d54f249afcb3d8d`（碩二版）與 `23d2b4ffdf0b801aa87cec717b0a2ce7`（碩一版），兩頁逐字相同
**覆蓋**：100%。內容為短筆記。

**【材料原文】**
> Learn to code：codecademy.com / w3schools.com / kaggle.com
>
> 懶人拖拉（有潛力且易）：Tableau、Excel、PowerBI
> （有潛力但難）：R、SPSS
>
> **Tableau**
> - 該欄位的內容被歸在**維度**區塊的話，代表將其視為一個**類別字串**，顯示時候也會用類別的方式呈現
> - 像經緯度這種欄位就可能被歸在**度量**（數字）
> - 度量跟維度可以手動切換（資料類別）
> - steps（可以依經緯度找出在指定時間內物流量最高的資料視覺化）
>
> analysis 不用刷 leetcode
>
> - tableau 的 coding 只能針對欄位的值來進行處理
> - vba 基本上是針對自動化來進行優化
> - python 全面

**【評註】** 這則筆記對 S1 的直接價值有限，但它記錄了一條有用的工具選型判準：
**維度（dimension, 類別）vs 度量（measure, 數值）的區分**是所有 BI 工具的共同心智模型，
也正好對應統計上的「屬質資料 vs 屬量資料」（見第 10 節）——
S1 在規劃分析時，應強制對每個變數標註它是維度還是度量，因為這決定了可用的圖表與統計方法。

---

## 10. 非母數統計方法

### 10.1 覆蓋率的誠實說明（重要）

**來源**：Notion「統計理論」`25b2b4ffdf0b8036bb8ac680736acafa`（父頁：碩二課程 → NTU），共 **16 個子頁**。

**父頁目錄（100% 取得）**：

| # | 子頁 | ID | 狀態 |
|---|---|---|---|
| 1 | 基礎微積分 | `2642b4ffdf0b807db0b4e4a7af4325b5` | 未讀 |
| 2 | 概論 | `2622b4ffdf0b80f88967e45be814a6e5` | 未讀 |
| 3 | **敘述統計學** | `2652b4ffdf0b800b8af8f6ffab1250e5` | ✅ **100% 讀完**（內容極豐富） |
| 4 | 古典機率論 | `2682b4ffdf0b8089bd55ddddd765de21` | 未讀 |
| 5 | 隨機變數 | `2682b4ffdf0b808a9168e80ee5217851` | 未讀 |
| 6 | 多元隨機變數（略） | `26a2b4ffdf0b803fb3ebf2c54a4b60a7` | 未讀 |
| 7 | 常用機率分配模型 | `26a2b4ffdf0b805590faf5eb5a129525` | 未讀 |
| 8 | 抽樣方法與抽樣分配 | `26a2b4ffdf0b8042b10bea316ec2fc95` | 未讀 |
| 9 | 點估計 | `26a2b4ffdf0b80dfb8a9c11e468af1d0` | 未讀 |
| 10 | 區間估計 | `26a2b4ffdf0b8074ae03f066ee960a64` | 未讀 |
| 11 | **假說檢定** | `26a2b4ffdf0b804b9658c828ccf5ead5` | ⚠️ **已 fetch — 頁面空白，無內容** |
| 12 | 變異數分析 | `26a2b4ffdf0b8003b5aad43e4b9a07d8` | 未讀 |
| 13 | 相關分析與線性迴歸 | `26a2b4ffdf0b806abc3bd06aef5862a0` | 未讀 |
| 14 | **卡方檢定與適合度檢定** | `26a2b4ffdf0b80b09cb6e0c450d4ee56` | ⚠️ **已 fetch — 頁面空白，無內容** |
| 15 | **其他非母數統計方法** | `26a2b4ffdf0b807eac54c01e44baae6c` | ⚠️ **已 fetch — 頁面空白，無內容** |
| 16 | 統計決策理論、時間序列與指數 | `26a2b4ffdf0b80ed89a8c36d0794c44e` | 未讀 |

> ### ⚠️ 關鍵發現
> **任務指定的重點「非母數統計方法」，其 Notion 頁面（連同「假說檢定」「卡方檢定與適合度檢定」）目前都是空白頁。**
> 這三頁只有標題，尚未撰寫內容。因此本節**無法提供非母數方法的教材內容** ——
> 這是素材本身的缺口，不是萃取的疏漏。
>
> 已讀完的「敘述統計學」子頁中，確實含有與非母數/穩健統計**直接相關**的段落
> （中位數、IQR、離群值偵測、以及對「有母數 vs 無母數」的明確註記），以下整理這部分。

### 10.2 敘述統計學中與非母數相關的內容（已讀部分）

**來源**：Notion `2652b4ffdf0b800b8af8f6ffab1250e5`，**100% 讀完**

#### 10.2.1 為什麼中位數需要非母數方法 —— 原文的關鍵註記

材料在比較中央趨勢量數時，明確點出了母數 vs 非母數的分界：

**【材料原文】中位數的重要性質（第 6 條）**
> 不易進行**有母數方法**統計推論，因樣本中位數的抽樣分配不易於推導且性質較差，牽涉到不容易處理的「順序統計量」，但**可以用無母數統計方法處理**。

對照**算術平均數**的性質：
> 5. 代數性質佳，易於計算。← 這超重要！
> 6. 易於進行統計推論，因樣本平均數 $\bar{X}$ 存在易於推導且性質優良的抽樣分配…

**【評註】這正是「什麼時候該用非母數」的根本理由**，而且材料把它講得比多數教科書清楚：
> 平均數之所以主宰傳統統計，不是因為它更能代表資料，而是因為它的**抽樣分配好推導**。
> 一旦改用中位數/分位數這類穩健量數，代數性質就變差、抽樣分配難推導 —— **這時才需要非母數方法**。

#### 10.2.2 三種中央趨勢量數的完整比較（可直接做成決策表）

**【材料原文】整理**

| 性質 | 算術平均數 $\mu, \bar{X}$ | 中位數 $\eta, m_e$ | 眾數 $m_o$ |
|---|---|---|---|
| 受離群值影響 | **極易受影響** | 不易受影響，相對穩健 | **最不易受影響，非常強健** |
| 適用尺度 | 等距、比例 | 順序、等距、比例 | **名義、順序、等距、比例** |
| 有開放組時 | 有適用困難 | 亦適用 | 也適用 |
| 對資料敏感性 | 高 | 較低 | 較低 |
| 代數性質 | **佳，易於計算** | 較差，不易計算 | 較差，不易計算 |
| 統計推論 | **易**（抽樣分配性質優良） | 不易（需無母數方法） | 不易（幾乎無法推導抽樣分配） |

> **原文特別註記**：名義尺度的資料，**僅能以眾數**代表其中央趨勢，平均數和中位數都不適用。
> **原文註記**：因算術平均數太容易受離群值影響，因此高度偏斜分配的資料，並不適合使用算術平均數作為中央趨勢量數。

**數學性質（原文公式）**

平均數使**離差平方和**最小：
$$\sum_{i=1}^{N}(X_i-\mu)^2 \leq \sum_{i=1}^{N}(X_i-a)^2, \quad \forall a$$

中位數使**離差絕對值和**最小：
$$\sum_{i=1}^N{|X_i-\eta|} \le \sum_{i=1}^N{|X_i-a|}, \quad \forall a$$

**【評註】** 這兩條就是 L2 vs L1 損失函數的差別，也是「為什麼中位數穩健」的數學根源。
在行銷分析中直接對應：**用平均客單價 vs 中位數客單價**，會得到完全不同的結論（因為消費金額幾乎必然右偏）。

#### 10.2.3 偏態下的三量數大小關係（原文）

- 對稱分配（Symmetric）：$\mu = \eta = m_o$
- **右偏**（Skewed to the right / 正偏 positively skewed）：$\mu \ge \eta \ge m_o$
- **左偏**（Skewed to the left / 負偏 negatively skewed）：$\mu \le \eta \le m_o$

> 原文說明：會有這樣的結果，是因為三種中央趨勢量數對於極端值的敏感度不同所致。

**Pearson 經驗法則（原文）**：偏斜分配中，$\mu$ 到 $m_o$ 的距離約為 $\mu$ 到 $\eta$ 的三倍：
$$| \mu - m_o | \approx 3 |\mu - \eta| \Rightarrow m_o \approx 3\eta - 2\mu$$
> 原文警告：注意！這裡僅僅只是經驗法則，故無法證明，也不保證一定正確。

**Pearson 法偏態係數**：
$$sk_P=\frac{3(\bar{X}-m_e)}{S} \quad \text{或} \quad sk_P=\frac{\bar{X}-m_o}{S}$$

$$\begin{cases}
sk_P > 0, & \text{右偏} \\
sk_P = 0, & \text{對稱分配} \\
sk_P < 0, & \text{左偏}
\end{cases}$$

**動差法偏態係數**：$\alpha_3 = \dfrac{m_3}{S^3}$，其中 $m_3 = \frac{1}{n}\sum_{i=1}^n(X_i-\bar{X})^3$

**峰態係數**：$\alpha_4 = \dfrac{m_4}{S^4}$

| 峰態係數 | 分配類型 | 尾部 |
|---|---|---|
| $> 3$ | 高狹峰（leptokurtic）/ 超高斯 | **肥尾/厚尾/重尾（fat/thick/heavy tail）** |
| $= 3$ | 常態峰（mesokurtic）—— 常態分配的峰態，作為基準 | — |
| $< 3$ | 低闊峰（platykurtic）/ 次高斯 | 瘦尾/薄尾（thin tail） |

> 超額峰態係數（原文，註記為「不是很重要」）：$\gamma_2 = \frac{m_4}{S^4}-3$

**動差體系的意義（原文）**：
1. 一階動差：中央趨勢的資訊
2. 二階動差：分散趨勢的資訊
3. 三階動差：偏態程度的資訊
4. 四階動差：峰態程度的資訊
5. 五階以上目前尚未發現用途

#### 10.2.4 穩健的分散量數

**四分位距 IQR（原文）**
$$IQR = Q_3 - Q_1$$

性質：不易受離群值影響，相對較強健／適用順序、等距、比例尺度／有開放組時亦適用／敏感性較低／代數性質較差／**不易進行統計推論**

若資料接近鐘形分配的經驗法則：$IQR \approx 1.35\,\sigma$

**全距經驗法則（原文）**：$R \approx 4\sigma \Rightarrow \sigma \approx \dfrac{R}{4}$
> 原文說明：此近似關係源自於鐘形分配。以鐘形分配而言，約有 95% 左右的數據資料分布在平均數左右各兩倍標準差的範圍內，即便不是鐘形分配，這也是一個「不差的」近似。

**變異係數 CV（原文）** —— 跨資料集比較分散程度用
$$CV = \frac{\sigma}{\mu}\times 100\% \qquad \widehat{CV} = \frac{S}{\bar{X}}\times 100\%$$
> 適用時機（原文）：兩筆資料數值（Scale）差距過大／兩筆資料單位截然不同
> 例：想比較一群大象體重的分散程度與一群螞蟻體重的分散程度

**平均絕對離差 MAD（原文）** —— L1 版本的分散量數
$$MAD=\frac{1}{N}\sum_{i=1}^N|X_i-\mu| \quad \text{或} \quad MAD = \frac{1}{N}\sum_{i=1}^N|X_i-\eta|$$
> 原文：採用「取絕對值」的方法，避免離差正負相消，好處是「相較於變異數，比較不會受到離群值的影響」。因有絕對值的運算，代數性質不佳，也不易進行統計推論，所以不常用。

#### 10.2.5 離群值偵測（原文，兩個簡易方法 + 一個進階）

**【材料原文】**
> - z-score < −3 或 z-score > 3 的資料點可視為離群值
> - 藉由盒鬚圖來偵測：比 $Q_1$ 小 **1.5 IQR** 以上，或比 $Q_3$ 大 **1.5 IQR** 以上，視之為離群值
> - 進階方法之一：**DBSCAN**

其中 z-score：$Z_i = \dfrac{X_i-\mu}{\sigma}$ 或 $Z_i = \dfrac{X_i-\bar{X}}{S}$

**盒鬚圖的內籬/外籬（原文完整規則）**

| 界線 | 位置 | 界外資料的名稱 |
|---|---|---|
| **內籬（inner fence）** | $Q_1 - 1.5\,IQR$ ／ $Q_3 + 1.5\,IQR$ | 內籬與外籬之間 = **溫和離群值（mild outliers）**，或稱嫌疑離群值（suspected outliers） |
| **外籬（outer fence）** | $Q_1 - 3\,IQR$ ／ $Q_3 + 3\,IQR$ | 外籬以外 = **嚴重離群值（extreme outliers）** |

> 繪圖慣例（原文）：溫和離群值以符號 `＊`，嚴重離群值以符號 `○` 繪出。鬚（whisker）從盒子兩端延伸至內籬以內的最小/最大值。

**五數字摘要（Five-number summary）**：$X_{(1)},\ Q_1,\ m_e,\ Q_3,\ X_{(n)}$
> 原文：這五個數字中，兩兩數字之間恰都包含了 25%，可約略看出分佈情形與分佈位置：
> - 兩相鄰數字的數值差距**越小** → 該處資料密度**越大**
> - 兩相鄰數字的數值差距**越大** → 該處資料密度**越小**

**【評註】** 「相鄰五數間距 → 密度」這條讀法很實用，可以在不畫直方圖的情況下，
單看 `describe()` 的輸出就判斷分佈形狀。

#### 10.2.6 EDA 與資料分組（MECE 在統計裡的對應）

**探測性資料分析 EDA（原文）**
> 由 John Tukey 所提倡的近代敘述統計學方法，其意義在於「試圖以簡單的計算與簡易的圖形快速地將資料的特性呈現出來」。資料分配的兩大特性是我們所感興趣的：
> 1. **分配的位置（Location of distribution）**
> 2. **分配的形狀（Shape of distribution）**：分散程度、偏態與峰態

**屬量資料分組的原則（原文）—— 注意這就是 MECE**
> 1. **互斥（Mutually exclusive）**
> 2. **週延（Exhaustive）**
> 3. 同時滿足以上兩種條件，稱為一組**分割（Partition）**

**【評註】** 這是本批材料中一個漂亮的呼應：
**統計上的「分割（Partition）」= 管顧上的「MECE」**，是同一個數學概念。
S1 可以用這一點向使用者解釋為什麼 MECE 不是管顧黑話，而是資料切分的基本要求。

**分組步驟（原文）**
1. 排序，求全距 $R = $ 最大值 $-$ 最小值
2. 決定組數 $k$ 與組距 $h$，其中 $R = k \times h$
   - 經驗法則：$k$ 以 **5 到 7 組**為最佳，組距 $h$ 最好是 **5 或 10 的倍數**
   - **Sturges' rule**（原文註記「這不是很重要」）：
     $$k = 1 + \log_2{N} = 1 + 3.322\log_{10}{N}, \qquad h = \frac{R}{k}$$
3. 決定組限與組界：
   $$\text{下組界} = \text{下組限} - \frac{\text{基本單位}}{2}, \qquad \text{上組界} = \text{上組限} + \frac{\text{基本單位}}{2}$$
   $$\text{組中點} = \frac{\text{上組限}+\text{下組限}}{2}=\frac{\text{上組界}+\text{下組界}}{2}$$

**屬質 vs 屬量資料（原文）**

| | 屬質資料（Qualitative） | 屬量資料（Quantitative） |
|---|---|---|
| 尺度 | 名義尺度、順序尺度 | 等距尺度、比例尺度 |
| 細分 | — | 離散（Discrete）／連續（Continuous），以連續型較常見 |
| 常用圖形 | 長條圖、圓餅圖、**柏拉圖（Pareto chart）** | 直方圖、圓餅圖、次數多邊圖（折線圖） |

**【評註】** 材料裡出現 **Pareto chart** —— 這正是 TMBA 材料裡「80/20 法則」的視覺化工具。
S1 的 2×2 優先序矩陣（第 4 節）與柏拉圖是同一個思想的兩種呈現，可以互相替代。
另注意：TMBA 管顧簡報材料明說**避免使用圓餅圖**，但統計教材把圓餅圖列為標準圖形之一——
**這是兩份材料的實質衝突**，S1 應採用管顧側的建議（不用圓餅圖）。

**相對次數（原文）**
$$\text{相對次數} = \frac{f_i}{N}, \quad i = 1,2,\dots,k$$
> 原文：相對次數可以類比為「機率」的概念。
> 相對次數直方圖 → 對應機率密度函數（pdf）；相對次數肩形圖（ogive） → 對應累積分配函數（cdf）

**鐘形分配經驗法則（68-95-99.7 rule，原文）**
1. 約 68% 的資料點落在 $\mu\pm\sigma$ 內
2. 約 95% 的資料點落在 $\mu\pm2\sigma$ 內
3. 約 99.7% 的資料點落在 $\mu\pm3\sigma$ 內

**其他平均數（原文）**

幾何平均數 —— *適用時機：計算「連續數期之比率、變化率、報酬率、成長率」*
$$m_G = \sqrt[N]{\prod_{i=1}^N X_i} = \left(\prod_{i=1}^N X_i\right)^{\frac{1}{N}}$$
> 原文警告：資料中有 0 或負數的時候，不適合使用幾何平均數。

調和平均數
$$m_H = \frac{N}{\frac{1}{X_1}+\frac{1}{X_2}+\dots+\frac{1}{X_N}}$$

**變異數與自由度（原文）**
$$\sigma^2 = \frac{1}{N}\sum_{i=1}^N(X_i-\mu)^2, \qquad S^2 = \frac{1}{n-1}\sum_{i=1}^n(X_i-\bar{X})^2$$
> 原文解釋 $n-1$：在樣本資料中，我們用 $\bar{X}$ 來估計 $\mu$，會使得自由度損失一個，讓整體自由度變為 $n-1$。
> 自由度可直覺理解為「能夠自由變動的變數個數」，因樣本平均數 $\bar{X}$ 被鎖住，所以 $X_1,\dots,X_n$ 能自由變動的只有 $n-1$ 個。

平移不變性與平方擴充性：$\sigma^2_{X+b} = \sigma^2_X$；$\sigma^2_{aX} = a^2\sigma^2_X$；$\sigma_{aX} = |a|\sigma_X$

**位置量數（原文）**：百分位數 $P_r$、十分位數 $D_r$、四分位數 $Q_r$ 的換算
$$D_5 = P_{50} = Q_2 = m_e, \qquad Q_1 = P_{25}, \qquad D_1 = P_{10}, \qquad D_9 = P_{90}$$

求第 $r$ 百分位數的步驟（原文）：先排序 → 計算位置 $i = n \times \frac{r}{100}$ →
$$P_r = \begin{cases} \dfrac{X_{(i)} + X_{(i+1)}}{2}, & i \text{ 為整數} \\[6pt] X_{[i]+1}, & i \text{ 非整數} \end{cases}$$
其中 $[i]$ 為高斯符號（取小於或等於某數的最大整數，如 $[2.5]=2$、$[-3.4]=-4$）。

> **原文的重要提醒**：從數學定義上來說，多數情況下第 $r$ 百分位數都「**不唯一**」——
> 當 $i$ 為整數時，理論上 $X_{(i)}$ 和 $X_{(i+1)}$ 之間的任何一個數都符合定義，公式只是求出其中一個。

**【評註】** 這條在實作上很重要：**不同軟體的分位數預設演算法不同**（pandas / numpy / R 的 `quantile()` 有 9 種 type），
會導致同一份資料算出不同的 $Q_1, Q_3$，進而影響 IQR 離群值判定。S1 應要求明確指定分位數方法。

---

## 11. 可重用資產

> 本節是給新 Skill S1 直接取用的成品。所有內容都可追溯到前述章節的材料來源。

### 11.1 【檢查清單】開案對焦五問（S1 的 intake gate）

合併 TMBA SMART（§2）+ Minto 問題定義框架（§8.2.2）而成。**五問未答完，不得進入拆樹階段。**

```
□ Q1. 現況是什麼？（Starting Point / Opening Scene）
      → 要能畫出來：一個結構（組織圖、據點、市場）或一個流程（銷售、配送、行銷活動）
      → 檢查：這個範圍是客戶劃的，還是我確認過的？（→ 早產兒保溫箱陷阱，§9.3）

□ Q2. 發生了什麼事？（Disturbing Event）
      → 分類：External（競爭者/技術/政策）｜Internal（自己改了什麼）｜Recently Recognized（績效落後/市調訊號）
      → 若真的問不出來，不要硬掰，直接跳 Q3

□ Q3. 現在不喜歡的結果是什麼？（R1）
      → 必須是可觀測的：哪個指標、掉了多少、從什麼時候開始

□ Q4. 想要的結果是什麼？（R2）
      → 必須含：指標名 + 目標水準（數字）+ 時間邊界
      → 若客戶說不出來 → 不要卡住，把「確定 R2」登記為分析任務 #1（Minto 處境 #6）

□ Q5. 至今為止做過什麼？（Solution so far）
      → 這一問決定了要回答哪一題，見 §11.2 分流器
```

**SMART 補充檢查（§2）**：完成的 Problem Statement 必須通過四個反例測試 ——
不是 Not Action-oriented（有「藉由…」）／不是 Not Measurable（有數字）／
不是 Not Relevant（手段作用在 R1 的根因上）／不是 Not Time-bound（有期限）。

### 11.2 【決策規則】客戶處境分流器 → 決定用哪種樹

來源：Minto 七種處境（§8.2.3）× TMBA 三種樹（§3）。**這是 S1 最核心的決策規則。**

| 客戶處境（由 Q5 判定） | 要回答的 Question | **該用哪種樹** | 不該做什麼 |
|---|---|---|---|
| 1. 完全不知道怎麼辦 | How do we get from R1 to R2? | **議題樹**（診斷框架）→ 再轉假說樹 | — |
| 2. 有方案但不確定對不對 | Is it the right solution? | **假說樹**（直接驗證既有方案） | 不要重新拆議題樹 |
| 3. 方案確定，不知怎麼執行 | How do we implement it? | **演繹樹**（實施路徑） | 跳過根因診斷 |
| 4. 做了但失效 | What should we do now? | **議題樹**，但根節點是「方案為何失效」 | 不要假設原診斷正確 |
| 5. 多個候選方案選不出來 | Which one? | **2×2 矩陣 + 演繹樹** | 不要再產生新方案 |
| 6. 知道 R1 但講不出 R2 | What exactly is R2? | **先不拆樹** —— 做目標設定 | 不要碰資料 |
| 7. 知道 R2 但不確定在不在 R1 | Are we actually at R1? | **現況量測 / benchmarking** | 不做因果分析 |

### 11.3 【檢查清單】MECE 拆樹品質門檻

來源：TMBA §3 + 統計「分割 Partition」§10.2.6 + BCG「每個分支要帶假說」§8.4

```
對每一層兄弟節點：
□ ME 檢查：任兩個節點是否有包含關係或概念重疊？
           （測試句：「研究生 vs 博士生」—— 有沒有一個吃掉另一個？）
□ CE 檢查：所有兄弟節點的聯集 = 父節點嗎？漏了誰？
           （測試句：「大一～大四」—— 研究生跑哪去了？）
           → 卡住時用 §11.5 的 4C 清單掃一遍補漏

對每一個葉節點：
□ 甜蜜點檢查：對應的解方可執行嗎？
           太表層（貼降溫貼布）→ 再拆一層
           太深層（改善人類基因）→ 收回一層
□ 假說化檢查：能填完這句話嗎？
           「我認為 ______，因為 ______，若為真則資料上會看到 ______」
           → 填不完 = 這只是待查清單項，不是可分析的假設
□ 驗證方法檢查：能對應到 訪談法 / 問卷 / 數據分析 其中之一嗎？

停止條件（兩個都要滿足）：
□ (a) 再往下拆會違反 MECE
□ (b) 葉節點落在甜蜜點
```

### 11.4 【決策規則】Why So? 與 So What? 的對稱律

來源：TMBA §3 + §6

| 方向 | 問句 | 階段 | 產出 |
|---|---|---|---|
| 由上而下 ↓ | **Why So?** | 拆解（Step 2） | 議題樹／假說樹 |
| 由下而上 ↑ | **So What?** | 收斂（Step 6） | 洞察 → 議題 → 策略 |

**規則**：Step 2 樹中每一個進入驗證的葉節點，在 Step 6 都必須有去處
（成為某個洞察的支撐，或被明確標記為「已驗偽」）。
**找不到位置的假說 = Step 2 就不該拆出來的分支。**

金字塔四層（由下而上）：`假說 → 洞察 → 主要議題 → 策略`

### 11.5 【範本】議題樹模板庫（依提問類型選用）

來源：Victor Cheng §8.1

**A. 獲利／營收下滑型**
```
Profits ─┬─ Revenue ─┬─ Revenue/Unit
         │           └─ # Units Sold
         └─ Cost ────┬─ Fixed Cost
                     └─ Variable Cost
操作三步：SEGMENT（切維度比歷史）→ ISOLATE（找出主因分支）→ EXPLORE（找解方）
切維度選項：產品線／通路／顧客類型(新舊、大小)／地區／產業別
成本切法：邏輯構成／價值鏈（原料→工廠→配送→顧客）
⚠ 定位出「哪一塊掉了」之後，必須換用 B 框架回答「為什麼掉」（從 Customer 端開始）
⚠ 銷量下滑時，一定要比對競爭者 → 判斷是 產業性 還是 公司特有 問題
```

**B. 市場進入／新產品／成長／轉型型（4C 檢查清單）**
```
Customer     — 分群(規模/成長率/佔比)、與歷史比、各群需求、願付價格與彈性、
               通路偏好、顧客集中度與議價力
Product      — 產品本質與利益、商品化 vs 可差異化、互補品、替代品、
               生命週期、包裝組合
Company      — 能力與專長、使用通路、成本結構(固定 vs 變動)、投資成本、
               無形資產(品牌/忠誠)、財務狀況、組織結構
Competition  — 競爭者集中度與結構、競爭者行為、最佳實務、進入障礙、
               供應商集中度、法規環境、產業生命週期
用法：當作 CE 補漏清單，逐條問「這條能不能改寫成一個可驗證的假說？」
⚠ 不要整套硬套（BCG：Imposing a generic framework is a recipe for failure）
```

**C. 併購「適配度」型**

| | Customers | Products | Company | Competition |
|---|---|---|---|---|
| Company A | | | | |
| Company B | | | | |
| Company A+B | | | | |

> 每找到一個綜效 = 「good fit」欄多一票。
> ⚠ 此框架**假設併購本身是對的**，只回答「這個標的合不合適」。要問「該不該併」請用 D。

**D. 產能變動型**

| Demand | Supply | Cost of Expansion |
|---|---|---|
| 整體市場成長（可持續嗎） | 產業供給 | 實際成本（負擔得起嗎） |
| 公司市佔成長（可持續嗎） | 依市場/區隔切分供給 | 機會成本（回收期、損益兩平點） |
| 切分需求來源、各區隔佔比與趨勢 | 供給增加對價格的影響 | 替代方案：外包／租賃／轉包 |

> 分流：概念型（約 20%）用此框架；數值型則畫供需曲線，求**市場結清價格**。

**E. 價值棒型（獲利改善的另一種拆法，§9.2.1）**
```
WTP - WTS = 總創造價值
├─ 拉高 WTP：互補品／附加價值／品牌（POD, §9.1.4）
└─ 壓低 WTS：大量採購／長約／供應商賦能（Nike 模式）
⚠ 材料警告：直接砍薪資會使人員流失 → 產能下降 → 成本反而上升
```

**F. 顧客忠誠度型（§9.1.5，四分支各對應不同資料源）**
```
品牌共鳴 ─┬─ 行為忠誠 (A)   → 交易資料：回購率、頻率、品類份額
          ├─ 態度依附 (I)   → 問卷：NPS、態度量表
          ├─ 社群意識 (I)   → 社群/社群媒體資料
          └─ 積極參與 (A)   → UGC、推薦、活動參與行為
```

**G. 品牌定位型（§9.1.4）**
```
定位問題 ─┬─ 我們的 POD 是否被目標客群感知到？    → 知覺圖、聯想強度量測
          ├─ 類別 POP 是否達標（該有的有沒有）？  → 屬性達標率
          └─ 是否有未處理的相關性 POP？          → 負相關屬性配對分析
                                                   (低價↔高品質、美味↔低卡)
```

### 11.6 【範本】市場規模／費米推論工作表

來源：Ace Your Case III §8.3 + TMBA 費米推論 §7.5

```
題目：__________________________________________

KEY QUESTIONS TO ASK（先問，別急著算）
  1. 母體是誰？__________________________________
     ⚠ 有沒有套用地理／人口／情境限縮？（別直接用全國人口）
  2. 滲透率/使用率？_____________________________
  3. 每人用量？__________________________________
  4. 更換頻率／購買週期？________________________
  5. 除了個人，還有其他大宗採購者嗎？____________
  6. 有二手／替代市場嗎？________________________

BASIC NUMBERS（用整數）
  ______________________________________________

TRACK THE NUMBERS DOWN（秀出算式）
  ______________________________________________

公式：____________ × ____________ + ____________ = ____________

三條規則：① 用整數  ② 秀出過程  ③ 可用紙筆與計算機
方向：work from big to small
定位：費米推論是「即時回應客戶臨時提問」用的，得到相對正確的數字。
      真正的「率％」要嘛來自嚴謹計算，要嘛業主給。估算 ≠ 分析。
```

**辨識規則**：「該不該做 X」型的提問，內部幾乎一定藏著一個市場規模／效益估算子題，
拆樹時應主動把它獨立成一個葉節點。

### 11.7 【決策規則】切維度紀律（S1 的硬規則）

來源：Victor Cheng Reminders §8.1.5 + 統計偏態 §10.2

```
🔴 硬規則：任何「總量持平／小幅變動」的觀察，在切維度之前不得下結論。

理由（原文範例）：
  總銷售持平，但 A 區隔佔 20% 且成長 100%，B 區隔佔 80% 且衰退 25%
  → 不切維度就完全看不到重點（aggregation masking / Simpson's Paradox 同源）

必切的四組維度：
  □ 營收 — 依產品、通路、顧客類型、地區（看總額 + 每單位）
  □ 成本 — 依固定/變動、依價值鏈各段（看總額 + 每單位）
  □ 顧客 — 依人口統計、需求、購買型態、價格帶
  □ 競爭 — 依通路、地區、產品、顧客區隔

兩個比較基準（缺一不可）：
  □ 與歷史比 → 找出趨勢
  □ 與競爭者比 → 判斷是「產業性」還是「公司特有」問題（解法完全不同）

不確定該怎麼切時的話術（原文）：
  「取得更細的營收拆解會很有幫助，我們有更細的資料嗎？」
  → 資料的既有切分方式，往往就洩漏了業務真正在意的維度

🔴 統計配套規則：
  □ 消費金額、客單價、停留時間等右偏變數 → 報中位數，不要只報平均數
    （右偏時 μ ≥ η ≥ m_o，平均數會被大戶拉高）
  □ 名義尺度變數 → 只能用眾數
  □ 跨尺度/跨單位比較分散程度 → 用變異係數 CV = σ/μ
  □ 離群值：z-score 超過 ±3，或超出 Q₁−1.5·IQR / Q₃+1.5·IQR
    嚴重離群值：超出 Q₁−3·IQR / Q₃+3·IQR
  □ 指定分位數演算法（pandas/numpy/R 預設不同，會影響 IQR 判定）
```

### 11.8 【範本】假說登錄表（Step 4 的交界面）

來源：TMBA §5 + §4

| 假說 ID | 假說敘述（可證偽的陳述句） | 預估投入 | 預估價值 | 2×2 象限 | 驗證方法 | 資料來源 | PIC | 完成判準 |
|---|---|---|---|---|---|---|---|---|
| H1 | | 低/高 | 低/高 | Do Now | 數據分析 | | | |
| H2 | | | | Do Next | 訪談法 | | | |
| H3 | | | | Don't Do | （記錄為已考慮但排除） | | | |

**2×2 優先序矩陣**

| | 低價值 | 高價值 |
|---|---|---|
| **低投入** | Do Later | **Do Now** |
| **高投入** | Don't Do | **Do Next** |

規則：只有 Do Now / Do Next 進入分析；Don't Do 需明確記錄為「已考慮但排除」（供附錄用）。

**質性驗證的三角色分工**（原文）：主訪／主筆／附筆兼會議記錄；需事先擬好訪綱 + 共編訪談紀錄表。

### 11.9 【範本】交付結構（Step 6–7）

**SCQA 導言產生規則**（§8.2.4）：由左至右、由上而下讀問題定義框架，**讀者已知的最後一項 = Complication**。

```
S = 現況（Starting Point）
C = 讀者已知的最後一項
Q = 由 C 觸發的那一問
A = 金字塔頂端的結論
```

**管顧簡報五段結構**（§7）：`執行摘要 → 時程規劃 → 分析內容與策略 → 預期效益評估 → 附錄`

**單頁規則**：
- 量化頁：`Tagline（一句話）→ Chart → Key Insight → Sources`；Tagline = Key Insight 的濃縮
- 質性頁：`Tagline → Marvin Table`
- **不用圓餅圖**（佔空間、不便人眼閱讀）
- 執行摘要 = 各頁 Tagline 的彙整，含目標／策略／預期成效
- **議題樹不放正報**（思考工具，非交付物），必要時放附錄

### 11.10 【決策規則】框架使用紀律（防呆）

來源：BCG / Columbia §8.4

```
1. 框架是清單，不是答案
   → 4C / 獲利樹的用途是「檢查有沒有漏」（補 CE），不是拿來當結論

2. 不要硬套通用框架
   → 必須針對當下情境客製一棵樹
   → 對應 TMBA：先選對樹種（議題/假說/演繹），再拆

3. 每個分支都要附「為什麼要看它」
   → 每個分支要帶一個假說，而不只是一個待查欄位
   → 議題樹葉節點 = 問句；假說樹葉節點 = 可證偽的陳述句
   → S1 最終交付必須是假說樹形態

4. Think out loud — 被否決的選項也要說出來，連同否決理由
   → 對應 §11.8 的「Don't Do 需記錄為已考慮但排除」

5. 只用手上的資料，先擱置既有成見（Ignore your previous knowledge）
```

### 11.11 【對照表】三份來源在「問題結構化」上的收斂

這是本批最重要的交叉驗證結果 —— 三個獨立來源對同一件事的說法：

| 階段 | TMBA 管顧思維 | Victor Cheng | Minto / McKinsey Sequential Analysis |
|---|---|---|---|
| 定義問題 | Step 1 SMART Problem Statement | （未涵蓋） | Q1 是否有問題？ Q2 在哪裡？ + 問題定義框架 |
| **定位（WHERE）** | Step 2 拆樹（議題樹） | **SEGMENT → ISOLATE** | Q2 Where does it lie? |
| **診斷（WHY）** | Step 2 Why So? 根因分析 | **Business Situation Framework**（從 Customer 端開始） | Q3 Why does it exist? + 診斷框架 |
| 優先排序 | Step 3 2×2 + 80/20 | （隱含在 "drill down on the problem branch"） | （未特別涵蓋） |
| 產生解方 | 演繹樹 | EXPLORE | Q4/Q5 + 邏輯樹（logic tree） |
| 收斂表達 | Step 6 金字塔 So What? | （未涵蓋） | 金字塔原理 + SCQA |

> **收斂結論**：三份來源一致主張「**定位（WHERE）與診斷（WHY）是兩個分開的步驟**」，
> 且都警告不可跳過定位直接解釋原因。這是 S1 最應該固化的流程分界。
>
> **互補之處**：
> - TMBA 提供了最完整的**端到端流程**（7 步）與**優先排序機制**（2×2）
> - Victor Cheng 提供了最具體的**定量定位手法**與**現成議題樹模板**
> - Minto 提供了最嚴謹的**問題定義元素**與**七種處境分流器**

---

## 12. 覆蓋率誠實聲明

### 12.1 完整讀完的來源（可信度高）

| 來源 | 規模 | 覆蓋 |
|---|---|---|
| `D:\TMBA\20250723 管顧思維.pdf` | 16 頁 | ✅ **100%** 文字層全部萃取並轉錄。**這是本批最重要的來源，已榨乾。** |
| `Case Interview/case_interview_frameworks.pdf`（Victor Cheng） | 6 頁 | ✅ **100%** 全文逐字轉錄（該文件明示允許自由散布） |
| `Case Interview/Columbia Case Interview Tips.pdf` | 3 頁 | ✅ **100%** |
| Minto Ch.8 Defining the Problem | PDF p.141–152 | ✅ **全章精讀**，框架完整轉出 |
| Minto Ch.9 摘要 | PDF p.259–260 | ✅ 完整 |
| Notion 整理1 + 整理2（全球品牌管理） | 2 頁 | ✅ **100%**（兩份高度重疊） |
| Notion 3/26 講義隨筆+整理（競爭策略） | 1 頁 | ✅ **100%** |
| Notion 敘述統計學 | 1 頁（極長） | ✅ **100%** |
| Notion TMBA 暑期社課（碩一 + 碩二共 6 頁） | 6 頁 | ✅ **100%**（碩一/碩二版逐字相同，實質只有 3 頁獨立內容，且內容很短） |

### 12.2 部分讀取

| 來源 | 覆蓋 | 說明 |
|---|---|---|
| `Ace-your-case-iii-market-sizing-questions.pdf` | 76 頁中約 **25 頁** | Ch.1–3（規則章）+ 15 題題目已讀；**Ch.4–5 的逐題解答與 WetFeet 評註未讀** |
| Minto Pyramid Principle 全書 | 275 頁中約 **20 頁** | 僅 Part Three 的問題定義章。**Ch.1–7（金字塔寫作邏輯、演繹/歸納、SCQA 細節）與 Ch.9 正文（診斷框架、邏輯樹的實作）未精讀** |
| `BCG Case Interview.pdf` | 14 頁 | 已全文萃取到本機文字檔，僅**精讀關鍵段落**（面試官評語） |
| `Bain Case Interview.pdf` | 14 頁 | 已全文萃取到本機文字檔，**僅掃讀** |
| `Berkeley - Case Interview Guide.pdf` | 26 頁 | 已全文萃取到本機文字檔，**僅掃讀** |

### 12.3 完全未讀（明確缺口）

**Case Interview 資料夾中未讀的 PDF（合計 >1,500 頁）**：

| 檔案 | 大小 | 為什麼值得補 |
|---|---|---|
| `CASE IN POINT_ 9th Edition - Marc Cosentino9.pdf`（及其「拷貝」副本） | 6.9 MB ×2 | **業界最知名的案例框架書**，含 Ivy Case System 與大量獲利樹變形 |
| `Vault_Guide2007.pdf` | 4.2 MB | 綜合指南 |
| `Kellogg-2012.pdf` | 3.2 MB | Kellogg casebook，含大量行銷向案例 |
| `Ace-your-case-ii-mastering-the-case-interview.pdf` | 4.2 MB | 案例框架總論（本批只讀了 III 市場規模冊） |
| `Ace_Your_Case_I.pdf` / `Ace_Your_Case_II.pdf` | 0.5/0.6 MB | 同上系列 |
| `FuquaCaseBook_2010-2011-Public.pdf` | 1.2 MB | Duke casebook |
| `50614a09-d715-46f8-842a-17764202ec61.pdf` | 2.5 MB | 檔名無意義，**內容未確認** |
| `case-interview-guide.pdf` | 0.8 MB | 未讀 |
| `case_interview_handbook_2016_7_1.pdf` | 12 頁 | 已萃取文字，未精讀 |
| `McKinsey Casebook/` 下 4 個檔（PST Coaching Guide + 3 個 McKinsey-Style Case） | 合計 ~0.8 MB | **完整的 McKinsey 式案例演練**，對驗證 7 Steps 實作很有價值 |
| `Bain Casebook/Bain Case Interview Guide.pdf` | 0.3 MB | 未讀 |
| `BCG Casebook/BCG Case Interview Preparation.pdf` | 0.6 MB | 未讀 |

**Notion 未讀頁面**：
- 統計理論 16 個子頁中，**11 頁未讀**（基礎微積分、概論、古典機率論、隨機變數、多元隨機變數、常用機率分配模型、抽樣方法與抽樣分配、點估計、區間估計、變異數分析、相關分析與線性迴歸、統計決策理論時間序列與指數）

**本機未處理的素材**：
- `D:\TMBA\TMBA.rar`（321 MB）—— **未解壓、未確認內容**。體積遠大於已處理的 zip，可能含大量社課教材
- `D:\TMBA\影片＿20250723 管顧思維.mov`（1.98 GB）+ 同名 `.rar`（269 MB）—— 管顧思維社課的**錄影**。
  投影片只有 16 頁但講者口述內容應遠豐富於此，**這可能是本批最大的未開發資產**（需轉譯）
- `20250723 管顧思維.pdf` 的 **p.7（1 張圖）與 p.8（14 張圖）內嵌影像未 OCR** ——
  p.7 是「共編表單」截圖、p.8 是「訪談法 / 資料抓取→分析→視覺化」示意圖。文字層已涵蓋條列說明，但圖內細節未取得

### 12.4 已知的材料內部衝突

| 議題 | 來源 A | 來源 B | 建議採用 |
|---|---|---|---|
| 圓餅圖能不能用 | TMBA 管顧簡報：**避免使用**（佔空間、不便閱讀） | 敘述統計學：列為屬質/屬量資料的標準圖形之一 | 採 TMBA（管顧交付情境） |
| 目標（R2）說不出來時怎麼辦 | TMBA SMART：不合格，要補齊 | Minto 處境 #6：允許，但把「確定 R2」列為分析任務 #1 | 採 Minto（更適合真實開案） |

### 12.5 本次萃取的中間產物（暫存，非永久）

以下檔案在 scratchpad，**session 結束後可能被清除**，若要保留請另行複製：

```
C:\Users\User\AppData\Local\Temp\claude\E--Projects-----\12f5620f-1d00-4952-8ce8-1138ae3aee81\scratchpad\
├── mgmt_consult.txt      # 管顧思維 PDF 全文（UTF-8）
├── minto.txt             # Minto Pyramid Principle 全書 275 頁文字層
├── ci_frameworks.txt     # Victor Cheng 框架全文
├── ci_bain.txt / ci_bcg.txt / ci_berkeley.txt / ci_columbia.txt
├── ci_marketsizing.txt   # Ace Your Case III 前 34 頁
├── ms_rules.txt          # 市場規模規則章（去頁首雜訊）
└── ci\Case Interview\    # zip 解壓後的 25 個 PDF
```

> **建議**：`minto.txt`（275 頁完整文字層）與解壓後的 `Case Interview\` 目錄很有價值，
> 若要繼續萃取 §12.3 的缺口，建議先把它們複製到 `E:\Projects\行銷分析\00_source_archive\` 下的永久位置，
> 避免重複解壓與 OCR 成本。

