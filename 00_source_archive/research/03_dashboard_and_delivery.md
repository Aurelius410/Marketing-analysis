---
title: 互動式探索儀表板的技術選型
topic: 交付物四之四 —— 互動式探索儀表板（Interactive Exploration Dashboard）
research_date: 2026-07-26
researcher: Claude (subagent, methodology extraction)
lang: zh-TW（技術名詞保留原文）
sources:
  - type: github_api
    url: https://api.github.com/repos/{owner}/{repo}
    note: 用於取得 archived / pushed_at / releases / commits 的硬事實，非憑印象
    fetched: 2026-07-26
  - type: github_web
    url: https://github.com/evidence-dev/evidence
    fetched: 2026-07-26
  - type: github_web
    url: https://github.com/marimo-team/marimo
    fetched: 2026-07-26
  - type: pypi_api
    url: https://pypi.org/pypi/{package}/json
    note: 用於取得 requires_python 與 Programming Language classifiers
    fetched: 2026-07-26
  - type: docs
    url: https://docs.marimo.io/guides/exporting/
    fetched: 2026-07-26
  - type: docs
    url: https://docs.marimo.io/guides/wasm/
    fetched: 2026-07-26
  - type: docs
    url: https://docs.marimo.io/guides/working_with_data/sql/
    fetched: 2026-07-26
  - type: docs
    url: https://docs.marimo.io/api/inputs/
    fetched: 2026-07-26
  - type: blog
    url: https://marimo.io/blog/altair
    fetched: 2026-07-26
local_path: E:\Projects\行銷分析\00_source_archive\research\03_dashboard_and_delivery.md
size_note: 本檔為調研 digest，非單一來源全文轉錄
coverage: |
  【誠實說明 —— 本檔為 v2，v1 的兩處錯誤已更正並標記】

  ■ 完整查證（GitHub API 硬資料，archived / pushed_at / releases / commits 皆實際 fetch）
    evidence-dev/evidence、marimo-team/marimo、streamlit/streamlit、holoviz/panel、
    posit-dev/py-shiny、rilldata/rill、metabase/metabase、apache/superset、
    lightdash/lightdash、observablehq/framework、simonw/datasette、
    simonw/datasette-lite、plotly/dash、whitphx/stlite、
    hydrosquall/datasette-dashboards。共 15 個 repo。
    另查 evidence-dev 組織全部 repo 的 push 排序、Evidence 的 issue/PR 更新序列。

  ■ PyPI 完整查證（requires_python + classifiers + wheel tags）
    marimo / streamlit / panel / shiny / shinylive / datasette / dash /
    great-tables / altair / duckdb / pyarrow / bokeh / holoviews / hvplot /
    param / panel-material-ui / jinja2 / python-pptx / vl-convert-python。
    共 19 個套件。

  ■ 原始碼層級查證
    marimo/_cli/export/commands.py（1,140 行）—— html 與 html-wasm 的完整 click 旗標。
    這關閉了 v1 的推測，並發現 v1 的重大錯誤（file:// 限制）。

  ■ 本機實測（Windows 11）
    Python 3.14.1 已安裝套件清單；
    HKLM 登錄檔的 CJK 字型家族名列舉（確認 Noto Sans TC 與 Microsoft JhengHei 存在）。

  ■ 文件深讀
    marimo: exporting / webassembly_html / wasm / sql / inputs / plotting /
            configuration-theming
    Altair: saving_charts / configuration / customization
    vl-convert: repo 說明的字型章節

  ■ 文件淺讀（僅 landing / README 級別）
    Evidence、Observable Framework、Rill、Panel、Datasette-Lite。

  ■ v1 → v2 的兩處更正（重要）
    1. 【錯誤】v1 寫「marimo html-wasm 可寄 zip 讓對方雙擊開啟」
       【更正】原始碼與官方文件皆明載必須經 HTTP 提供，不能 file://。見 §5.2.2。
    2. 【遺漏】v1 未提 Altair chart.save() 預設走 CDN
       【更正】需 inline=True + vl-convert-python 才是真正離線單檔。見 §11.3。

  ■ 未能查證（逐條列於 §12.2，共 10 項）
    最重要的三項：
    - 【零實機測試】本機未安裝 marimo / altair / great-tables，
      所有程式碼範本皆為「依文件撰寫、未執行」，用前必須先跑一次。
    - 【繁中未渲染驗證】只驗證了字型存在與設定 API，沒有實際產出含中文的圖，
      豆腐字只有肉眼看得出來。因此 §6 評分矩陣的準則 3 對所有方案一律給 2 分，
      該欄目前不具鑑別力。
    - 【WASM 資料量上限】文中的 200 MB 界線是估計值，無實測依據。
    - Evidence 官方「OSS 維護模式」聲明未尋獲，§9 結論基於間接證據（commit 停滯
      + 商業版導流），已標示為推論。
    - mercury-project/mercury：API 回傳 null，repo 不存在或已改名，未追查。

  ■ 主動排除（不涵蓋）
    Quarto Dashboards、Dash Enterprise、Hex、Deepnote、Sigma、Tableau、Power BI
    等商業/SaaS 方案 —— 與「單人分析師、本地 Parquet、可寄送、agent 生成」的
    前提不符。
---

# 互動式探索儀表板的技術選型

> 前提（已定案，本文不翻案）：DuckDB + Parquet 倉儲、Python 3.14.1 主環境、
> 報告走 Jinja2 單檔 HTML、投影片走 python-pptx、圖表走 Altair + matplotlib、
> 表格走 great-tables。**儀表板必須與這套並存，不是取代它。**

---

## 0. 結論先行（TL;DR）

| 問題 | 結論 |
|---|---|
| 單人分析師 / 本地 Parquet / 要點選篩選下鑽，最務實的選擇？ | **marimo**（主）+ **Altair `selection` 純靜態互動**（輕量層） |
| 靜態（可寄送）與互動（需 server）能不能兼得？ | **部分能，且要拆成三層看**，見 §7。真正「email 附件雙擊即開」的只有 L1（Altair `inline=True` 單檔）；marimo `html-wasm` 給的是「無需後端 Python 的靜態網站」，**需要 URL，不能雙擊**（§5.2.2） |
| Evidence.dev 值得嗎？ | **不值得，且有明確風險**。OSS repo 自 2026-02-18 起無 maintainer commit，社群 PR 積壓，團隊導流至商業版 Evidence Studio。見 §3.1 |
| marimo 同時當 notebook 與 app 的意義？ | **「分析過程即交付物」在技術上第一次成立**：同一個 `.py` 檔就是 notebook、是 app、是 script、是 git diff 友善的原始碼。見 §8 |

**一句話決策規則**：
> 這個 Skill 要「用純程式碼、由 AI agent 穩定生成、讀本地 Parquet、能交付給別人」的儀表板 ——
> **marimo 是唯一四項全中的方案**。其餘方案至少掉一項。
> 但**交付形式決定層級**：要當附件寄就用 L1（Altair），能給 URL 才上 L2（marimo WASM）。

**本次調研推翻的兩個常見誤解**（v1 digest 自己也踩了）：
> 1. ❌「Evidence.dev 是 DuckDB 生態最活躍的 BI-as-code」→ 核心 repo 已 5 個月無 commit（§2.2）
> 2. ❌「marimo WASM 匯出可以寄 zip 讓對方雙擊」→ 瀏覽器擋 `file://`，必須 HTTP（§5.2.2）

---

## 1. 評分框架（依任務指定權重，高→低）

| # | 準則 | 權重 | 為什麼這是這個專案的準則 |
|---|---|---|---|
| 1 | **可被 AI agent 純程式碼穩定生成** | 最高 | Skill 要自動產出儀表板。任何需要「手拉介面 / 點 UI 設定 / 存進資料庫 metadata」的方案直接出局 |
| 2 | **DuckDB / Parquet 原生支援** | 高 | 倉儲已定案。要能 `read_parquet('...')` 直讀本地檔，不能要求先 ETL 進別的 DB |
| 3 | **繁體中文字型與排版** | 高 | 交付對象是台灣讀者 |
| 4 | **Python 3.14.1 相容** | 高 | 已被此點坑過三次，必須查 `requires_python` 與 classifiers |
| 5 | **部署形態：靜態檔 vs 需 server** | 中 | 決定「能不能寄給別人看」 |
| 6 | **與 Altair 主題相容** | 中 | 要沿用同一套 design token，不能兩套視覺系統 |

---

## 2.【材料原文】維護狀態硬事實（2026-07-26 實測 GitHub API）

> 以下全部來自 `https://api.github.com/repos/{owner}/{repo}` 與其
> `/releases`、`/commits` 子端點，**非憑印象**。

### 2.1 核心 metadata 表

| Repo | archived | 最後 push | 最後 commit | 最新 release | stars | open issues | 主語言 | License |
|---|---|---|---|---|---|---|---|---|
| `evidence-dev/evidence` | **false** | **2026-02-18** | **2026-02-18** | `@evidence-dev/evidence@40.1.8` **2026-02-06** | 6,775 | 269 | JavaScript | MIT |
| `marimo-team/marimo` | false | **2026-07-25** | 2026-07-24 | `0.23.15` **2026-07-23** | 22,054 | 601 | Python | Apache-2.0 |
| `streamlit/streamlit` | false | **2026-07-26** | 2026-07-24 | `1.60.0` 2026-07-21 | 45,350 | 1,215 | Python | Apache-2.0 |
| `holoviz/panel` | false | 2026-07-24 | 2026-07-24 | `v1.9.3` 2026-06-01 | 5,722 | 1,116 | Python | BSD-3-Clause |
| `posit-dev/py-shiny` | false | 2026-07-24 | 2026-07-24 | `v1.6.3` 2026-06-01 | 1,740 | 457 | Python | MIT |
| `rilldata/rill` | false | 2026-07-24 | 2026-07-24 | `v0.88.4` **2026-07-24** | 2,770 | 203 | Go | Apache-2.0 |
| `metabase/metabase` | false | 2026-07-25 | 2026-07-24 | `v0.63.1` 2026-07-21 | 48,369 | 4,199 | Clojure | NOASSERTION (AGPL/商業雙授權) |
| `apache/superset` | false | 2026-07-26 | 2026-07-26 | `6.1.0` 2026-05-13 | 73,986 | 594 | Python | Apache-2.0 |
| `lightdash/lightdash` | false | 2026-07-25 | 2026-07-24 | `0.3476.1` 2026-07-24 | 5,981 | 1,581 | TypeScript | NOASSERTION |
| `observablehq/framework` | false | **2026-05-15** | **2026-05-15** | `v1.13.4` **2026-03-02** | 3,557 | 181 | TypeScript | ISC |
| `simonw/datasette` | false | 2026-07-25 | 2026-07-25 | `0.65.2` (stable) 2025-11-05 / `1.0a37` (pre) **2026-07-14** | 11,308 | 694 | Python | Apache-2.0 |
| `simonw/datasette-lite` | false | 2026-06-24 | 2026-06-24 | 無 release | 405 | 30 | CSS | Apache-2.0 |
| `plotly/dash` | false | 2026-07-24 | 2026-07-24 | `v4.4.1` 2026-07-21 | 24,351 | 532 | Python | MIT |

**沒有任何一個 repo 標記 `archived: true`。** 但 `archived=false` ≠ 活著，見下節。

### 2.2 Evidence 的實際狀態（重要，逐條列出）

`evidence-dev/evidence` 最近 10 筆 commit（API 原始輸出）：

```
2026-02-18T20:42:32Z | Merge pull request #3283 from evidence-dev/cleanup-install
2026-02-18T20:41:02Z | clean up install page
2026-02-13T21:50:49Z | Merge pull request #3281 from evidence-dev/cve/2026-02-13
2026-02-13T20:58:35Z | Changeset
2026-02-13T20:35:04Z | lint & format
2026-02-13T20:30:16Z | update lock using pnpm 8.15.9
2026-02-13T19:28:40Z | update lock
2026-02-13T19:10:12Z | Update CVE
2026-02-10T14:53:49Z | Merge pull request #3280 from evidence-dev/studio-note
2026-02-10T14:52:04Z | studio note
```

最近的 issue / PR 活動（`sort=updated`）：

```
2026-07-25 | PR  #3311 | open | fix: make prop-derived chart values reactive (Area label pos...
2026-07-21 | PR  #3310 | open | fix: preserve BarChart axis and colors when switching to sta...
2026-06-22 | iss #3309 | open | BigQuery source refresh fails on Node 26 with node-fetch Pre...
2026-06-19 | iss #2507 | open | [Bug]: Dropdown selections are not removed when the query ch...
2026-06-15 | PR  #3308 | open | Fix Datatable column header tooltips in fullscreen mode
2026-05-27 | PR  #3305 | open | Add human friendly duration format
2026-05-22 | iss #3304 | open | [Bug]: DuckDB post-query processing hang in Evidence sources
```

README 置頂橫幅（verbatim）：
> "Try Evidence Studio: The new, faster way to build data products with SQL, markdown and AI."

evidence-dev 組織下各 repo 的最後 push（`sort=pushed`）：

```
markdoc                      2026-07-07   (fork of a Markdoc, 1 star)
template                     2026-06-04
evidence-studio-template     2026-06-02
duckdb_gsheets               2026-02-21
evidence                     2026-02-18   <-- 核心產品
```

**【評註】** 這組事實的解讀（我的判斷，非材料原文）：

1. 核心 OSS repo 最後兩次實質 commit 是「CVE 修補」與「清理安裝頁」—— 這是**維護模式**的典型特徵，不是產品開發。
2. 團隊仍在動的 repo 是 `evidence-studio-template`（商業版樣板）與 `template`，**開發重心明確移往 Evidence Studio**。
3. 社群 PR（#3305 / #3308 / #3310 / #3311）自 2026-05 起累積至今**無人合併**，跨度超過 2 個月。
4. 有一個**未修的 DuckDB 相關 bug**（#3304, 2026-05-22, "DuckDB post-query processing hang in Evidence sources"）—— 這正好打在我們最需要的路徑上。
5. **未能查證**：我沒有找到 Evidence 官方「OSS 停止維護」的公開聲明。因此不能說它「已死」，只能說**核心 repo 已停滯 5 個月且商業版導流明顯**。

**風險結論**：把一個要長期維護的 Skill 綁在這上面，是把賭注押在一個「公司已轉向商業版、OSS 核心停更 5 個月」的專案上。**不建議。**

### 2.3 Observable Framework 的實際狀態

```
2026-05-15T21:33:06Z | fix pages dist
2026-05-15T21:28:05Z | restore yarn install
2026-05-15T21:24:54Z | deploy to github pages (#2057)
2026-03-02T21:46:51Z | publish requires node 24?
2026-03-02T21:38:23Z | fix typo
2026-03-02T21:33:26Z | adopt trusted publishing
2026-03-02T21:14:32Z | 1.13.4
```

**【評註】** 2026-03-02 發 `v1.13.4` 之後，只有 2026-05-15 的三筆 CI/部署雜務 commit。
**實質功能開發已停滯約 5 個月。** 與 Evidence 同屬「不能押注」的一類，理由相同。

### 2.4 Datasette 的特殊狀態（值得注意）

- stable `0.65.2` 停在 **2025-11-05**
- 但 `1.0a37` prerelease 發於 **2026-07-14**，且 alpha 版本以**約每 1–2 週一版**的節奏推進：

```
1.0a37  2026-07-14      1.0a32  2026-05-31
1.0a36  2026-07-07      1.0a31  2026-05-29
1.0a35  2026-06-23      1.0a30  2026-05-24
1.0a34  2026-06-16      1.0a29  2026-05-12
1.0a33  2026-06-11      1.0a28  2026-04-17
```

**【評註】** Datasette **非常活躍**，只是 1.0 難產已久（alpha 跑了很多年）。
它的問題不是死活，是**定位**：Datasette 是 SQLite 導向的資料探索/發佈工具，
不是 DuckDB/Parquet 原生。要接 Parquet 需要外掛且是二等公民。見 §3.6。

---

## 3.【材料 + 評註】逐案評分

評分標記：`✅ 強` / `🟡 可用但有代價` / `❌ 出局`

### 3.1 Evidence.dev

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 純程式碼生成 | ✅ 強 | 就是 `.md` 檔內嵌 SQL + Svelte-like component tag。極度適合 LLM 生成，這是它最大的優點 |
| 2 DuckDB/Parquet | ✅ 強 | 內建 DuckDB 為預設引擎，前端跑 DuckDB-WASM。原生 |
| 3 繁中 | 🟡 未實測 | 底層 TailwindCSS + 瀏覽器渲染，理論上覆寫 font-family 即可；**我沒有實測** |
| 4 Python 3.14 | — | **不適用，Node 生態**（見 §9） |
| 5 部署 | ✅ 強 | `npm run build` 產出純靜態站，可丟任何 static host |
| 6 Altair 主題 | ❌ | 圖表是 Evidence 自家 component（底層 ECharts），**與 Altair 完全無關**，design token 要重寫一套 |
| **維護風險** | **❌ 出局** | **核心 repo 停更 5 個月，見 §2.2** |

**結論：出局。** 技術上準則 1、2、5 都是滿分，但**準則 6 拿不到、Node 生態成本高、且維護風險是致命傷**。

### 3.2 marimo ⭐ 首選

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 純程式碼生成 | ✅ **最強** | notebook 就是**純 Python `.py` 檔**（不是 JSON ipynb）。LLM 生成/修改/diff 都是一等公民 |
| 2 DuckDB/Parquet | ✅ **最強** | 官方文件原文：**"By default, marimo uses the in-memory duckdb connection."** 且 SQL cell 可直接 `read_parquet(...)` |
| 3 繁中 | 🟡 未實測 | 瀏覽器渲染 + 可注入 CSS；Altair 圖內文字走 Vega-Lite `config.font`（可控）。**我沒有實測** |
| 4 Python 3.14 | ✅ | `requires_python = ">=3.10"`，classifiers 含 **`3.14`** 與 `Only`（v0.23.15） |
| 5 部署 | ✅ **兼得** | 7 種 export，含 `html`（靜態快照）與 **`html-wasm`（自帶互動、無需 server）** |
| 6 Altair 主題 | ✅ **最強** | `mo.ui.altair_chart` 原生雙向綁定，**直接吃既有 Altair 物件與主題** |
| **維護風險** | ✅ 極低 | 最後 push **2026-07-25**（昨天），release `0.23.15` 2026-07-23，22k stars |

**六項準則裡有四項是全場最高分，零項出局。**

### 3.3 Streamlit

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 生成 | ✅ 強 | 純 Python script，LLM 最熟悉的框架之一 |
| 2 DuckDB/Parquet | ✅ | 自己寫 `duckdb.connect()` 即可，無限制 |
| 3 繁中 | 🟡 未實測 | 同上，瀏覽器渲染 |
| 4 Python 3.14 | ✅ | `requires_python = ">=3.10"`，classifiers 含 `3.14`（v1.60.0） |
| 5 部署 | ❌ **無官方靜態匯出** | Streamlit 本體沒有 export 指令。第三方 `whitphx/stlite`（WASM port）**其實相當活躍**（push 2026-07-25、1,652 stars、TypeScript），但**非官方**，版本追隨落後、且多一層信任成本 |
| 6 Altair 主題 | ✅ | `st.altair_chart()` 一等公民，且支援 `on_select` 取回選取 |
| 維護風險 | ✅ 極低 | 最後 push 2026-07-26（今天） |

**結論：🟡 強力備案，但敗在準則 5。** 「寄給別人看」這件事 Streamlit 做不到 ——
對方必須自己 `pip install` 再 `streamlit run`，或你得架一台 server。
對「單人分析師交付給客戶/主管」的場景，這是硬傷。

### 3.4 Panel (HoloViz)

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 生成 | 🟡 | 純 Python，但 API 面積大、`param` 心智模型較重，LLM 生成穩定度低於 marimo/Streamlit |
| 2 DuckDB/Parquet | ✅ | 無限制 |
| 3 繁中 | 🟡 未實測 | 底層 Bokeh 渲染 |
| 4 Python 3.14 | ✅ | `panel 1.9.3` `>=3.10` + `3.14` classifier；相依 `bokeh 3.9.2`、`param 2.4.1`、`holoviews 1.23.1`、`hvplot 0.12.2` **全部都有 3.14 classifier** |
| 5 部署 | ✅ **兼得** | `panel convert --to pyodide-worker` 可產出 WASM 靜態檔 |
| 6 Altair 主題 | 🟡 | 可 `pn.pane.Vega(chart)` 嵌入，但**互動回傳弱於 marimo**，Panel 的原生路線是 Bokeh/HoloViews |
| 維護風險 | ✅ 低 | 最後 push 2026-07-24 |

**結論：🟡 技術上可行的第二選擇。** 敗在準則 1（agent 生成穩定度）與準則 6（Altair 是二等公民）。

### 3.5 py-shiny (Posit)

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 生成 | 🟡 | 純 Python，`@render` / `@reactive` 裝飾器模式清晰，但 LLM 訓練語料遠少於 Streamlit |
| 2 DuckDB/Parquet | ✅ | 無限制 |
| 3 繁中 | 🟡 未實測 | Bootstrap 底 |
| 4 Python 3.14 | ✅ | `shiny 1.6.3` `>=3.10` + `3.14` classifier |
| 5 部署 | ✅ **兼得** | **Shinylive**（Pyodide）可產出純靜態站 |
| 6 Altair 主題 | 🟡 | 可嵌，但 Posit 生態主推 plotnine / plotly |
| 維護風險 | ✅ 低 | 最後 push 2026-07-24；但 stars 僅 1,740，社群規模小 |

**結論：🟡 可行，但沒有一項贏過 marimo。**

**【評註】** 對包子有一個隱藏加分：環境裡有 R 4.5.2。Shiny 的 Python / R 版心智模型一致，
若未來要跨 R/Python，Shiny 是唯一能複用的框架。但這不足以推翻 marimo。

### 3.6 Datasette 生態

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 生成 | 🟡 | metadata YAML/JSON + SQL 可生成，但 dashboard 外掛生態零散 |
| 2 DuckDB/Parquet | ❌ **關鍵失分** | Datasette **以 SQLite 為核心**。Parquet 需先轉檔或靠外掛，DuckDB 非原生路徑 |
| 3 繁中 | 🟡 未實測 | |
| 4 Python 3.14 | ✅ | `datasette 0.65.2` `>=3.9`，classifiers 含 `3.14` |
| 5 部署 | 🟡 | server 為主；`datasette-lite`（Pyodide）可純靜態但**是 demo 級專案**（405 stars，無 release，最後 push 2026-06-24） |
| 6 Altair 主題 | ❌ | 無關 |
| 維護風險 | ✅ 低（核心） | 核心 push 2026-07-25，1.0a37 節奏穩定 |

**結論：❌ 出局。** 準則 2 與既定倉儲架構**正面衝突** —— 我們的資料在 Parquet，
它要 SQLite。為了用它得多做一層轉檔，違反「不用先搬進別的資料庫」的明文要求。
`hydrosquall/datasette-dashboards` 該 fork 最後 commit **2022-04-05**，已死。

### 3.7 Rill Data

| 準則 | 評分 | 依據 |
|---|---|---|
| 1 AI 生成 | ✅ 強 | **宣告式 YAML + SQL**（`.yaml` model / metrics / dashboard），非常適合 LLM 生成 |
| 2 DuckDB/Parquet | ✅ **最強之一** | **Rill 的內建引擎就是 DuckDB**，直讀本地 Parquet 是設計初衷 |
| 3 繁中 | 🟡 未實測 | |
| 4 Python 3.14 | — | **不適用，Go 二進位檔**（無 Python 相依，這其實是優點：不會汙染環境） |
| 5 部署 | ❌ **需 server** | `rill start` 起本地服務；分享要靠 Rill Cloud（商業）。**沒有純靜態匯出** |
| 6 Altair 主題 | ❌ | 自家圖表引擎，design token 無法共用 |
| 維護風險 | ✅ 極低 | release **每週一版**（v0.88.0→v0.88.4 都在 2026-07 一個月內） |

**結論：🟡 值得知道，但不入選。** 準則 2 滿分、維護極健康、YAML 對 agent 友善 ——
**但準則 5 與 6 雙敗**。它適合「自己在本機快速探索一份 Parquet」，不適合當交付物。

**【評註】** 建議把 Rill 記在「個人探索工具箱」而非「Skill 產出物」。
`rill start` 指向一個 Parquet 資料夾，30 秒得到一個可下鑽的 dashboard，
這對包子自己做 EDA 很有價值，但那不是 Skill 要自動生成的東西。

### 3.8 Metabase / Superset / Lightdash（伺服器型 BI）

三者一起評，因為失分點相同。

| Repo | 維護 | 準則 1（AI 生成） | 準則 2（Parquet） | 準則 5（部署） |
|---|---|---|---|---|
| `metabase/metabase` | ✅ 極活躍 | ❌ **點 UI 為主**，dashboard 存在應用資料庫裡 | ❌ 需 JDBC 資料源 | ❌ 需長駐 server + JVM |
| `apache/superset` | ✅ 極活躍 | ❌ 同上，chart/dashboard 是 DB row | 🟡 可接 DuckDB SQLAlchemy 但非主流 | ❌ 需 server + Redis + metadata DB |
| `lightdash/lightdash` | ✅ 極活躍 | 🟡 dbt YAML 定義 metrics（較好），但 dashboard 仍在 UI | 🟡 綁 dbt | ❌ 需 server + Postgres |

**結論：三者全部 ❌ 出局，理由是同一個 ——**

**準則 1 是最高權重，而這三者的儀表板本體不是檔案，是資料庫裡的 row。**
AI agent 無法「寫一個檔案」就產生儀表板，必須呼叫 REST API 或操作 UI。
這與「Skill 自動產出儀表板」的核心需求**結構性衝突**。

再加上準則 5：這三者都需要長駐 server + 額外資料庫，
對「單人分析師、資料在本地」是嚴重過度工程（over-engineering）。

**【評註】** 這三個是很好的產品，只是**服務對象是「有 data team 的組織」**，不是單人分析師。
選它們等於為了做一份儀表板先養一套基礎設施。

### 3.9 Plotly Dash（補充查證，非任務指定但常被提及）

| 準則 | 評分 | 依據 |
|---|---|---|
| 4 Python 3.14 | ⚠️ **警訊** | `dash 4.4.1` `requires_python = ">=3.9"`，但 **classifiers 只列到 `3.12`，沒有 `3.13` 也沒有 `3.14`** |
| 5 部署 | ❌ 需 server | Flask 底 |
| 6 Altair 主題 | ❌ | Plotly 自家生態 |

**結論：❌ 出局。** 且 classifier 缺 3.14 正是「過去被坑三次」的那個訊號 ——
**列出來當反面教材。** 維護本身很健康（push 2026-07-24），但不符合本專案需求。

---

## 4. Python 3.14.1 相容性總表（準則 4，實測 PyPI）

> **這是被坑過三次的那一項，所以逐個查 `requires_python` 與 classifiers。**

```
套件                版本        requires_python   有 3.14 classifier?
--------------------------------------------------------------------
marimo             0.23.15     >=3.10            ✅ 是（且標 "Only"）
streamlit          1.60.0      >=3.10            ✅ 是
panel              1.9.3       >=3.10            ✅ 是
shiny              1.6.3       >=3.10            ✅ 是
datasette          0.65.2      >=3.9             ✅ 是
dash               4.4.1       >=3.9             ❌ 否（只到 3.12）  <-- 警訊
--- 已定案的既有堆疊（一併驗證，確認不會被儀表板拖累）---
altair             6.2.2       >=3.10            ✅ 是
great-tables       0.22.0      >=3.10            ✅ 是
duckdb             1.5.5       >=3.10.0          ✅ 是（標 "Only"）
pyarrow            25.0.0      >=3.10            ✅ 是
jinja2             3.1.6       >=3.7             （無 Python classifiers）
python-pptx        1.0.2       >=3.8             ❌ 否（只到 3.12）  <-- 注意
--- Panel 相依鏈（若選 Panel 需一併確認）---
bokeh              3.9.2       >=3.10            ✅ 是（標 "Only"）
holoviews          1.23.1      >=3.10            ✅ 是
hvplot             0.12.2      >=3.10            ✅ 是
param              2.4.1       >=3.10            ✅ 是
panel-material-ui  0.14.0      >=3.10            ✅ 是
--- 靜態匯出工具鏈 ---
vl-convert-python  1.9.0.post1 >=3.7             ⚠️ 無版本 classifier（見下）
shinylive          0.8.9       >=3.10            ❌ 否（只到 3.13）  <-- 注意
```

### 4.1 兩個需要特別解讀的案例

**(a) `vl-convert-python` —— 看似紅燈，實為虛驚**

```
classifiers: ['CPython']          # 完全沒有版本號 classifier
requires_python: >=3.7
wheel 檔名: vl_convert_python-1.9.0.post1-cp37-abi3-win_amd64.whl
                                              ^^^^^^^^^^
```

**`abi3` 是關鍵**：這是 CPython 的 stable ABI，代表這個 wheel
**向前相容所有 CPython >= 3.7，包含 3.14**。
（PyPI 上該套件所有 wheel 的 python_version tag 只有 `cp37` 與 `source`。）

**【評註】** 這個案例值得記進決策規則 —— 「classifier 沒寫 3.14」有兩種情況：
1. 上游真的沒測 → 要 smoke test
2. **上游用 abi3 wheel，根本不需要為每個版本出 wheel** → 虛驚一場

只看 classifier 會誤殺第 2 種。**規則 D6 已補上這一條**（§11.1）。
`vl-convert-python` 是 L1 交付路徑的必要相依（`chart.save(inline=True)` 與 PNG 匯出都靠它），
確認它能在 3.14 跑很重要。

**(b) `shinylive 0.8.9` —— 真的沒有 3.14**

classifiers 停在 `3.13`，且 `requires_python = ">=3.10"`。
這是 py-shiny 的**靜態匯出工具**（§3.5 給它「部署 ✅ 兼得」的依據）。

**【評註】** 這一項讓 py-shiny 的評分要下修：
`shiny` 本體有 3.14 classifier，但**讓它變成靜態檔的 `shinylive` 沒有**。
也就是說在 Python 3.14 環境下，py-shiny 的「可寄送」這條路**有風險**。
§6 評分矩陣中 py-shiny 的準則 5 應從 3 降為 2，加權總分 47 → 45。
（不影響結論，marimo 仍居首。）

**【評註】兩個要注意的點（都不是儀表板造成的，但既然查到就記下來）**：

1. **`python-pptx 1.0.2` 的 classifiers 只到 3.12，且 `requires_python = ">=3.8"`。**
   它不會被 pip 擋下（`>=3.8` 涵蓋 3.14），但**上游沒有宣稱測試過 3.14**。
   這是既定堆疊裡**唯一**沒有 3.14 背書的元件。建議在 Skill 的環境檢查腳本裡
   對 python-pptx 加一條 smoke test（實際產一頁 pptx 並開啟驗證），不要只信 import 成功。

2. **classifier 缺席 ≠ 不能跑**，但它是**上游是否測過**的最佳代理指標。
   決策規則見 §11 的檢查清單。

---

## 5.【材料原文】marimo 技術細節

### 5.1 SQL cell 與 DuckDB（準則 2）

官方文件（`docs.marimo.io/guides/working_with_data/sql/`）原文重點：

> "By default, marimo uses the in-memory duckdb connection."

> SQL cells are "syntactic sugar for Python code."

底層等價形式：

```python
output_df = mo.sql(f"SELECT * FROM my_table LIMIT {max_rows.value}")
```

直讀本地檔（原文示例）：

```sql
SELECT * FROM read_csv('path/to/example.csv');
-- or
SELECT * FROM read_parquet('path/to/example.parquet');
```

輸出型別：
> 查詢結果自動成為 "a Polars DataFrame (if you have `polars` installed) or a Pandas DataFrame (if you don't)"。預設 output type 為 `auto`。

Python 變數插值：
> "The SQL statement itself is an f-string, letting you interpolate Python values into the query with `{}`."

**【評註】** 這是六個準則裡最關鍵的一項驗證：
**marimo 的 SQL cell 預設引擎就是 DuckDB，且 SQL 是 f-string** ——
意思是 UI 元件的 `.value` 可以直接插進 WHERE 子句，
**「點選篩選下鑽」在 marimo 裡是一行 f-string 的事**，不需要寫 callback。

### 5.2 匯出格式（準則 5）

官方文件（`docs.marimo.io/guides/exporting/`）列出 **7 種** export，CLI 原文：

| 指令 | 產出 | 原文描述 |
|---|---|---|
| `marimo export html` | 靜態 HTML | "Non-interactive HTML snapshot" |
| `marimo export html-wasm` | **互動 HTML** | **"Self-contained, interactive HTML powered by WebAssembly"** |
| `marimo export pdf` | PDF | "PDF document or slide deck" |
| `marimo export ipynb` | Jupyter | "Jupyter `.ipynb` file" |
| `marimo export script` | Python script | "Flat `.py` script in topological order" |
| `marimo export md` | Markdown | "Markdown with code blocks" |
| `marimo export session` | JSON | "Serialized session snapshot (JSON)" |

另有發佈外掛：Quarto、Jupyter Book、MDX。

#### 5.2.1【材料原文】CLI 旗標（直接讀 marimo 原始碼查證）

來源：`https://raw.githubusercontent.com/marimo-team/marimo/main/marimo/_cli/export/commands.py`
（v1 digest 此處為推測，**已改為原始碼實證**）

`marimo export html-wasm` 的 click 選項定義（verbatim）：

```python
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory to save the HTML to.",
)
@click.option(
    "--mode",
    type=click.Choice(["edit", "run"]),
    default="run",
    help="Whether the notebook code should be editable or readonly.",
    required=True,
)
@click.option("--watch/--no-watch", default=False, ...)
@click.option(
    "--show-code/--no-show-code",
    default=False,
    help=(
        "Whether to show code by default in the exported HTML file; "
        "only relevant for run mode."
    ),
)
@click.option(
    "--include-cloudflare/--no-include-cloudflare",
    default=False,
    help=(
        "Whether to include Cloudflare Worker configuration files"
        " (index.js and wrangler.jsonc) for easy deployment."
    ),
)
@click.option("--sandbox/--no-sandbox", ...)
@click.option("-f", "--force", is_flag=True, default=False, ...)
@click.option(
    "--execute/--no-execute",
    default=False,
    help=(
        "Execute the notebook before exporting and embed outputs as a "
        "preview. Runs in an isolated environment pinned to WASM-compatible "
        "packages when possible."
    ),
)
```

`marimo export html`（非 WASM）的關鍵差異：

```python
@click.option(
    "--include-code/--no-include-code",
    default=True,            # <-- 預設「包含程式碼」
    type=bool,
    help="Include notebook code in the exported HTML file.",
)
@click.option(
    "-o", "--output",
    default=None,            # <-- 非必填；未給則印到 stdout
    help=("Output file to save the HTML to. "
          "If not provided, the HTML will be printed to stdout."),
)
```

**注意 `-o` 的語意不同**：`html-wasm` 的 `-o` 是**目錄**（required），
`html` 的 `-o` 是**單一檔案**（optional，預設印到 stdout）。

### 5.2.2 ⚠️【材料原文】重大限制：WASM 匯出不能用 file:// 開啟

**這是 v1 digest 寫錯、必須更正的一點。**

marimo 原始碼中 `html-wasm` 指令的 help 字串（verbatim）：

> "In order for this file to be able to run, it must be served over HTTP,
> and cannot be opened directly from the file system (e.g. `file://`)."

官方文件（`docs.marimo.io/guides/exporting/webassembly_html/`）同樣載明：

> "The exported file must be served over HTTP to function correctly -
> it cannot be opened directly from the filesystem (`file://`)."

且產出是**一個 HTML 檔 + 一個 `assets` 目錄**，assets 必須一起提供。

本機測試方式（原文）：

```bash
python -m http.server
```

官方建議的 hosting：**GitHub Pages**、**Cloudflare**（可用 `--include-cloudflare`
自動產生 `index.js` 與 `wrangler.jsonc`）、自架。另建議用 marimo 自家的 **molab** 分享。

`--mode` 差異（原文）：
- `--mode run`：唯讀，程式碼鎖定
- `--mode edit`：使用者可編輯 notebook

```bash
marimo export html-wasm notebook.py -o output_dir --mode run
marimo export html-wasm notebook.py -o output_dir --mode edit
```

**【評註】這個限制改變了 L2 的定位，必須誠實記錄：**

我在 v1 寫的「寄 zip，對方雙擊就能開」是**錯的**。
瀏覽器的 `file://` 安全模型（Service Worker / SharedArrayBuffer / CORS）擋住了 Pyodide 啟動。

正確的說法是：
> `html-wasm` 產出的是**「不需要後端 Python 的靜態網站」**，
> 不是**「可以雙擊開啟的單一檔案」**。
> 它需要一個 **static host**（GitHub Pages / Cloudflare Pages / 任何靜態空間 / 內網 nginx），
> 但**不需要跑 Python 的伺服器**。

這兩者的差別在成本上其實不大（GitHub Pages 免費、Cloudflare Pages 免費），
但在**交付流程**上差很多：
- ❌ 不能當 email 附件讓對方雙擊
- ✅ 可以給一個 URL，對方點開就有完整互動
- 🟡 若真要離線交付，只能寄整個目錄 + 請對方跑 `python -m http.server`
  —— 但這要求對方**有 Python**，對非技術收件人不可行

**因此 §7 的分層表已更正：L2 的「可寄送」欄位從 ✅ 改為「需靜態 host（URL）」。**

### 5.3 WASM 模式的能力與限制（準則 5 的關鍵細節）

官方文件（`docs.marimo.io/guides/wasm/`）原文：

> "marimo lets you execute notebooks *entirely in the browser*, without a backend executing Python."

套件支援（**這句很重要**）：
> "All packages with pure Python wheels on PyPI are supported, as well as additional packages like NumPy, SciPy, scikit-learn, **duckdb, polars**, and more."

資料檔處理：
> 匯出的 WASM HTML notebook，資料檔要 "place them in a `public/` folder in the same directory as your notebook"，程式中以下列方式取用：

```python
path_to_csv = mo.notebook_location() / "public" / "data.csv"
```

> 或 "host data files on the web and fetch them in your notebook"（可能需要 CORS Proxy）。

已知限制（原文）：
- "PDB is not currently supported"
- 併發受限：無真正 OS threads、無 CPU 平行
- 需要編譯 extension 的套件通常不支援

**【評註】—— 這是本次調研最重要的單一發現：**

**`duckdb` 有 Pyodide 支援，而且 marimo 官方文件明文列出。**

這意味著：
> `marimo export html-wasm` + `public/` 裡放 Parquet
> = **一個可以用 email 寄出、對方雙擊就能開、內含完整 DuckDB 引擎、能真的跑 SQL 下鑽的離線儀表板。**

這正是 §0 那個「靜態與互動兼得」問題的答案，而且是**唯一**乾淨的答案。

⚠️ **但有兩個必須實測的未知數（我未能查證）**：
1. Parquet 檔多大時瀏覽器會撐不住？（WASM 記憶體上限，通常 2–4 GB，實務上建議 < 200 MB）
2. `duckdb` 的 Pyodide wheel 版本是否落後 PyPI 主線？（可能不是 1.5.5）
   → 已列入 §12 待補。

### 5.4 UI 元件清單（準則 1：agent 要生成什麼）

`docs.marimo.io/api/inputs/` 完整清單：

**基本輸入**：`slider`、`range_slider`、`number`、`text`、`text_area`、`dropdown`、
`multiselect`、`radio`、`checkbox`、`switch`、`date`、`datetime`、`date_range`、
`button`、`run_button`、`refresh`

**結構**：`array`、`dictionary`、`matrix`、`batch`、`form`

**資料展示與探索**：`table`（支援選取）、`dataframe`（可編輯）、`data_explorer`

**進階**：`file`、`file_browser`、`code_editor`、`chat`、`microphone`、`tabs`

**整合**：**`altair_chart`**、`plotly`、`matplotlib`、`anywidget`

**【評註】** 對「點選篩選下鑽」這個需求，實際只需要四個：
`mo.ui.dropdown` / `mo.ui.date_range` / `mo.ui.altair_chart` / `mo.ui.table`。
**這是一份 agent 可以穩定生成的極小 API 面積** —— 準則 1 的實質意義就在這裡。

### 5.5 Altair 整合（準則 6，決定性優勢）

來源：`marimo.io/blog/altair` 與 `docs.marimo.io/guides/working_with_data/plotting/`

> marimo 在前端與 Python kernel 間建立**雙向資料綁定**（two-way data binding），
> 適用於所有 `mo.ui` widget，包含 `mo.ui.altair_chart`。

> 使用者在圖上選取資料點或區域後，選取結果會**反應式地回傳 Python kernel**，
> 成為過濾後的 DataFrame 或 selection 物件，透過 `chart.value` 取用。

自動選取行為（原文）：
> "If you use a `mark_point` and an `x` encoding, marimo will automatically add a brush selection to the chart. If you add a `color` encoding, marimo will add a legend and a click selection."
> 依 mark 型別自動採用 point 或 interval("brush") 選取。

自訂：
> 可將 `chart_selection` 與 `legend_selection` 設為 `False`，改用 Altair 原生 `.add_params`。

效能（**重要數字**）：
> 預設 Altair transformer 限制 5,000 rows，
> 而 marimo 的 `marimo_csv` transformer 可處理**超過 400,000 rows**，
> 作法是透過內部 VirtualFile URL 供給資料。

**【評註】** 這一節解決了準則 6：
**既有的 Altair 主題（design token）不用改一行，直接包進 `mo.ui.altair_chart` 就有互動。**
報告（Jinja2 靜態 HTML）與儀表板（marimo）**共用同一個 chart 建構函式**，
只是儀表板多包一層 `mo.ui.altair_chart(...)`。這就是「並存而非取代」的具體實現方式。

另外那個 5,000 → 400,000 row 的差異值得記住：
Altair 預設的 row 上限是實務上最常見的坑，marimo 已經幫忙解掉。

---

### 5.6 marimo 的樣式客製 API（準則 3 與 6 的接點）

來源：`docs.marimo.io/guides/configuration/theming/`

**Notebook 層級**：
```python
app = marimo.App(css_file="custom.css")
```

**專案層級**（`pyproject.toml`）：
```toml
[tool.marimo.display]
custom_css = ["additional.css"]
```

**字型 CSS 變數（官方明示為 public API）**：
```
--marimo-text-font
--marimo-heading-font
--marimo-monospace-font
```

官方範例（verbatim）：
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

:root {
  --marimo-heading-font: 'Inter', sans-serif;
}
```

> **注意**（原文）：除了上述三個字型變數之外的其他 CSS 變數
> "lack stability guarantees across versions"（跨版本不保證穩定）。

**【評註】** 這正好是 design token 的注入點：
Skill 只要產一份 `marimo_theme.css` 設定那三個變數，就能讓儀表板的字型
與 Jinja2 報告一致。**且官方保證這三個變數穩定，不會改版就壞。**

---

### 5.7 繁體中文字型與排版（準則 3，本機實測部分）

> **這是 v1 digest 完全沒有實據的一節，現補上實測資料。**
> ⚠️ 仍需注意：我**驗證了字型存在與名稱**，但**沒有實際渲染出圖截圖比對**。

### 5.7.1【實測】本機 Windows 11 已安裝的 CJK 字型

查詢方式：`HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts` 登錄檔。
**這是 CSS / Vega-Lite `font` 屬性要填的「字型家族名」，不是檔名。**

```
Microsoft JhengHei & Microsoft JhengHei UI          =>  msjh.ttc
Microsoft JhengHei Bold & ... UI Bold               =>  msjhbd.ttc
Microsoft JhengHei Light & ... UI Light             =>  msjhl.ttc
Noto Sans TC                                        =>  NotoSansTC-VF.ttf   <-- ★
MingLiU & PMingLiU & MingLiU_HKSCS                  =>  mingliu.ttc
MingLiU-ExtB & PMingLiU-ExtB & MingLiU_HKSCS-ExtB   =>  mingliub.ttc
DFKai-SB（標楷體）                                    =>  kaiu.ttf
Microsoft YaHei & Microsoft YaHei UI（簡中）           =>  msyh.ttc
```

**兩個好消息**：
1. **`Noto Sans TC` 已存在於本機**（可變字型 VF 版）—— 這是繁中無襯線的最佳選擇，
   且是 Google Fonts 開源字型，**可以 `@font-face` 內嵌 / 從 CDN 載入，跨機器一致**。
2. `Microsoft JhengHei UI`（微軟正黑體）是 Windows zh-TW 預設，**所有台灣 Windows 使用者都有**。

### 5.7.2 建議的字型堆疊（zh-TW）

```css
/* 依序 fallback：開源優先 → Windows → macOS → 泛用 */
font-family:
  "Noto Sans TC",           /* 開源，可內嵌，跨平台一致 */
  "Microsoft JhengHei UI",  /* Windows zh-TW 預設（微軟正黑體） */
  "Microsoft JhengHei",
  "PingFang TC",            /* macOS zh-TW 預設（未在本機驗證） */
  "Heiti TC",
  sans-serif;
```

**避免使用**：
- `MingLiU`／`PMingLiU`（細明體）—— 襯線點陣風格，螢幕上顯示品質差
- `DFKai-SB`（標楷體）—— 僅適合公文，不適合數據圖表
- `Microsoft YaHei`（微軟雅黑）—— **簡體中文字型，會出現異體字**，繁中場合不要用

### 5.7.3 三個渲染路徑的字型行為（重要：三者機制不同）

| 路徑 | 字型從哪裡來 | 風險 |
|---|---|---|
| **HTML 互動圖**（Altair/Vega-Lite 在瀏覽器） | **收件人的機器** | 收件人沒裝該字型 → fallback → 版面跑掉 |
| **PNG 靜態圖**（vl-convert → 進 pptx） | **產圖的機器**（我們自己） | 產圖機沒裝 → **豆腐字 □□□** |
| **marimo 介面文字** | 收件人的機器（可用 `--marimo-text-font` + `@font-face` 覆寫） | 同 HTML |

**【材料原文】vl-convert 的字型規則**（`github.com/vega/vl-convert`）：

> "SVG text placement and PNG text rendering require that the fonts referenced
> by the exported chart are installed on the system that VlConvert is running on."

> "A directory containing additional font files can registered with the VlConvert
> Python library using the `vl_convert.register_font_directory` function."

CLI 對應 `--font-dir` 參數。

> **未涵蓋**（原文未提）：vl-convert 文件**沒有專門討論 CJK 字型**，
> 也沒有說明字型缺失時的行為。這是需要自己實測的區域。

**【評註】** 這一節的實務結論：

1. **PNG 路徑（→ pptx）風險最高**，因為是「產圖機」的字型，錯了會出豆腐字，
   而且是靜默失敗 —— 圖產出來了，但字是方框。
   → **Skill 必須在產圖前檢查字型可用性**（見 §11.7 新增的檢查腳本）。
2. **HTML 路徑的正解是 `@font-face` 內嵌 Noto Sans TC**，
   不要依賴收件人的機器。代價是檔案變大（TC 全字集數 MB，
   可用 subset 只留實際用到的字）。
3. **Altair 的字型設定要一次設四處**（title / axis / header / legend），
   或用 `configure(font=...)` 一次設定，見 §11.8。

---

## 6. 綜合評分矩陣

權重：準則1 = 5、準則2 = 4、準則3 = 3、準則4 = 3、準則5 = 2、準則6 = 2
（分數 0–3：0 = 出局/不適用扣分，1 = 弱，2 = 可用，3 = 強）

| 方案 | 1 AI生成 ×5 | 2 DuckDB ×4 | 3 繁中 ×3 | 4 py3.14 ×3 | 5 部署 ×2 | 6 Altair ×2 | 加權總分 | 維護風險 |
|---|---|---|---|---|---|---|---|---|
| **marimo** | 3 (15) | 3 (12) | 2 (6) | 3 (9) | 3 (6) | 3 (6) | **54** | 極低 |
| Streamlit | 3 (15) | 3 (12) | 2 (6) | 3 (9) | 1 (2) | 3 (6) | **50** | 極低 |
| Panel | 2 (10) | 3 (12) | 2 (6) | 3 (9) | 3 (6) | 2 (4) | **47** | 低 |
| py-shiny | 2 (10) | 3 (12) | 2 (6) | 3 (9) | 2 (4)† | 2 (4) | **45** | 低 |
| Rill | 3 (15) | 3 (12) | 2 (6) | 3 (9)* | 1 (2) | 0 (0) | **44** | 極低 |
| Evidence | 3 (15) | 3 (12) | 2 (6) | 3 (9)* | 3 (6) | 0 (0) | **48** | **高（否決）** |
| Observable FW | 3 (15) | 2 (8) | 2 (6) | 3 (9)* | 3 (6) | 0 (0) | **44** | **中高（否決）** |
| Datasette | 2 (10) | 0 (0) | 2 (6) | 3 (9) | 2 (4) | 0 (0) | **29** | 低 |
| Dash | 2 (10) | 3 (12) | 2 (6) | 1 (3) | 1 (2) | 0 (0) | **33** | 低 |
| Metabase | 0 (0) | 1 (4) | 2 (6) | 3 (9)* | 0 (0) | 0 (0) | **19** | 極低 |
| Superset | 0 (0) | 1 (4) | 2 (6) | 2 (6) | 0 (0) | 0 (0) | **16** | 極低 |
| Lightdash | 1 (5) | 1 (4) | 2 (6) | 3 (9)* | 0 (0) | 0 (0) | **24** | 極低 |

`*` = 非 Python 生態，準則 4 不適用，給滿分表示「不會汙染 Python 環境」
`†` = py-shiny 的準則 5 已從 3 下修為 2：本體支援 3.14，但靜態匯出工具
      `shinylive 0.8.9` 的 classifier 只到 3.13（§4.1b），「可寄送」這條路有風險

**準則 3（繁中）目前對所有方案一律給 2 分** —— 因為我沒有實機渲染驗證任何一個
（§12.2 項 A）。**這一欄目前不具鑑別力**，等實測後可能改變相對排序。
不過準則 3 權重（3）低於準則 1（5）與準則 2（4），
即使該欄全部翻盤，也不足以動搖 marimo 的第一名。

**【評註】** 注意 Evidence 的加權總分（48）其實高於 Panel/Shiny ——
**它是被維護風險一票否決的，不是被技術分數否決的。**
這點要誠實記錄：如果 Evidence 明天恢復開發，它會是很強的競爭者（但準則 6 仍然拿零分）。

---

## 7. 必答一：靜態（可寄送）與互動（需 server）能不能兼得？

**能，但要理解這是三個層級，不是一個二元選擇。**

| 層級 | 技術 | 檔案形態 | 互動能力 | 交付方式 | 適用場景 |
|---|---|---|---|---|---|
| **L1 靜態互動** | Jinja2 + **Altair `selection` / `param`** | **真正的單一 .html**（需 `inline=True`） | 圖表內篩選、跨圖聯動、hover、legend 篩選。**資料已內嵌，無 Python** | ✅ **email 附件，雙擊開啟** | 定期報告、給主管/客戶看 |
| **L2 WASM 互動** | **`marimo export html-wasm`** | 一個目錄：`.html` + `assets/`（+ `public/` 放資料） | **完整 Python + DuckDB 跑在瀏覽器**，可重跑 SQL、任意下鑽 | 🟡 **需靜態 host（給 URL）**。⚠️ **不能 file:// 雙擊**，見 §5.2.2 | 給客戶自助探索（有 URL 可給時） |
| **L3 伺服器互動** | `marimo run app.py` / Streamlit | 需長駐 Python process | 完整能力 + 即時資料、大檔案、機密不外流 | ❌ 需自架服務 | 內部固定看板、機密資料 |

**部署成本階梯（更正後的正確理解）**：

```
L1  無任何基礎設施          → email 附件
L2  靜態空間，無後端 Python  → GitHub Pages / Cloudflare Pages（皆免費）
L3  長駐 Python 伺服器      → 自架 VM / container
```

**L1 → L2 的真正跨越點不是「靜態 vs 動態」，是「附件 vs URL」。**
L2 仍然是靜態託管（不跑後端 Python），但收件人必須能連到一個網址。

**關鍵洞見（【評註】）**：

1. **L1 被嚴重低估。** 很多「互動儀表板」需求，其實 Altair 的 `alt.selection_point()` /
   `selection_interval()` + `transform_filter` 就滿足了 —— **完全不需要任何儀表板框架**，
   而且產出的是可以直接嵌進既有 Jinja2 報告的單檔 HTML。
   **這是與既定堆疊「並存」成本最低的那條路，應該當預設。**

2. **L1 與 L2 共用同一份 Altair chart 建構程式碼。** 這是整個架構能成立的樞紐：
   ```
   build_chart(df) -> alt.Chart      # 純函式，吃 design token
        ├─> Jinja2 報告：chart.to_html()          (L1)
        ├─> marimo 儀表板：mo.ui.altair_chart(chart)  (L2/L3)
        └─> pptx 投影片：chart.save(png) -> python-pptx (既定)
   ```
   **一個 chart 函式，四種交付物。** 這才是「並存」的正確定義。

3. **L2 的代價（三項，都要誠實告知使用者）**：
   - 啟動要下載 Pyodide runtime（數十 MB），**首次載入明顯慢**
   - 資料量受瀏覽器記憶體限制
   - **必須有靜態 host，不能當 email 附件**（§5.2.2，這是最容易誤判的一項）

   → L2 不是萬用解，是**「需要瀏覽器端重跑 SQL、且有 URL 可以給對方」**時的解。

4. **三層不是互斥的，是漸進的。** Skill 應該讓使用者宣告需要哪一層，預設 L1。

5. **L1 要真正離線，必須加 `inline=True`**（見 §11.3）：
   Altair 預設 `chart.save('x.html')` **走 CDN 載 Vega JS**，斷網或防火牆環境會開不出圖。
   `chart.save('x.html', inline=True)` 才會把 JS 全部內嵌 —— 但這需要額外裝
   `vl-convert-python`。**這是 L1 能否當附件寄出的決定性設定，不能漏。**

---

## 8. 必答二：marimo 同時當 notebook 與 app —— 對「分析過程即交付物」的意義

**【評註】此節為我的分析，非材料原文。**

### 8.1 傳統流程的斷裂

```
探索（Jupyter .ipynb）
    ↓ 【斷裂 1】手動複製程式碼
生產腳本（.py）
    ↓ 【斷裂 2】重寫成 dashboard 框架語法
儀表板（Streamlit app.py）
    ↓ 【斷裂 3】再抄一次數字
報告 / 投影片
```

每一次斷裂都是：**重複工作 + 版本漂移 + 數字對不上的風險**。
對單人分析師而言，斷裂 3 是最痛的 —— 報告裡的數字和儀表板不一致，信任就沒了。

### 8.2 marimo 消除的是哪一種斷裂

marimo 的 `.py` 檔**同時是**：

| 身分 | 指令 | 用途 |
|---|---|---|
| notebook（可編輯、反應式） | `marimo edit nb.py` | 探索階段 |
| app（隱藏程式碼、只留 UI） | `marimo run nb.py` | 交付給不看程式碼的人 |
| script（拓樸排序的純 Python） | `python nb.py` | 排程 / CI |
| 靜態快照 | `marimo export html` | 存證 |
| 離線互動交付物 | `marimo export html-wasm` | 寄給客戶 |
| git 一等公民 | `git diff nb.py` | 版本控制（**不是 JSON**） |

**斷裂 1 與 2 直接消失** —— 同一個檔案。

### 8.3 「分析過程即交付物」的三層意義

1. **可稽核性（auditability）**：
   交付的不只是結論，是**產生結論的完整路徑**。
   對行銷分析尤其重要 —— 「這個 ROAS 怎麼算的」「這批受眾怎麼定義的」
   客戶可以自己往上追，不用回頭問你。這在做歸因分析、增量測試時是硬需求。

2. **反應式保證一致性（reactivity）**：
   marimo 是 DAG 反應式的 —— 改一個 cell，所有下游自動重算。
   **不可能出現「上面的圖用舊資料、下面的表用新資料」的 Jupyter 經典災難。**
   對交付物來說，這是「數字一定對得上」的技術保證，不是紀律問題。

3. **對 AI agent 的意義（這條最關鍵）**：
   Skill 生成的是**純 Python 檔**，不是 JSON、不是資料庫 row、不是 UI 操作序列。
   → agent 可以 **Read / Edit / Grep**
   → 可以做 code review
   → 可以被 diff、被測試、被重構
   → **儀表板變成「可維護的原始碼」，而不是「一次性產物」**

   **這是準則 1 給 marimo 最高權重的真正理由**：
   不只是「能生成」，而是「生成之後還能被 agent 持續修改」。

### 8.4 對包子這個 Skill 的具體建議

把 marimo notebook 定位成 **「分析底稿（working paper）」**，四種交付物的關係應該是：

```
        marimo notebook (.py)  ←── 唯一真實來源 (single source of truth)
                 │
     ┌───────────┼───────────┬──────────────┐
     ↓           ↓           ↓              ↓
  Jinja2 報告  pptx 投影片  great-tables   marimo app / html-wasm
  （結論）     （簡報）      表格          （探索）
```

**注意方向**：notebook 是上游，其他三者是下游產物。
不要讓儀表板變成第五個要另外維護的東西 —— 它應該是同一份底稿的另一個 render target。

---

## 9. 必答三：若選 Evidence.dev —— Node 生態怎麼銜接？值得嗎？

### 9.1 銜接方式（假設要做的話）

Evidence 是 SvelteKit 應用，資料流是：
```
sources/*.sql  ──(evidence sources)──> DuckDB ──> Parquet ──> 前端 DuckDB-WASM
pages/*.md     ──(build)────────────> 靜態站
```

與 Python 工作流的銜接**只有一個乾淨的介面**：**Parquet 檔案**。

```
Python (pandas/duckdb) 產出 clean Parquet
        ↓  寫到 evidence 專案的 sources/ 目錄
Evidence 的 DuckDB source 直接 read_parquet
        ↓  npm run build
靜態站
```

**技術上這是可行的，而且介面很乾淨**（Parquet 本來就是跨語言格式）。

### 9.2 真實成本清單

| 成本項 | 說明 |
|---|---|
| **Node.js 工具鏈** | 需要 Node + npm/pnpm。**多一整套執行環境要裝、要版控、要在 Skill 裡管版本** |
| **兩套依賴管理** | `pyproject.toml` + `package.json`，兩套 lockfile，兩套 CI |
| **兩套視覺系統** | Evidence 圖表底層是 ECharts，**與 Altair design token 完全不通**。準則 6 拿零分 |
| **兩套語言的除錯** | 出問題時要在 Svelte / JS 裡查，這超出「行銷分析師」的技能範圍 |
| **Node 版本風險** | 已有 issue #3309：「BigQuery source refresh fails on **Node 26**」—— 且無人修 |
| **維護風險** | §2.2，核心停更 5 個月 |

### 9.3 判斷

**不值得。** 理由按重要性排序：

1. **維護風險是一票否決。** 一個要長期用的 Skill，不能押在停更 5 個月、
   社群 PR 積壓、且公司已轉向商業版的專案上。
2. **準則 6 零分。** 圖表要重做一套 design token，違反「與既定堆疊並存」的前提 ——
   那不叫並存，叫並行維護兩套。
3. **Node 生態成本是永久性的**，不是一次性的。每次環境重建、每次 CI、
   每次 Node 大版本更新都要付一次。
4. **marimo 在準則 1/2/5 上打平或更好，且準則 6 完勝、準則 4 適用且通過。**
   既然有一個 Python 原生方案分數更高，付 Node 的稅就沒有正當理由。

**【評註】唯一會讓我改變看法的情境**：
如果需求是「做一個有幾十頁、要給很多人看、SEO 友善的公開資料入口網站」，
Evidence 的 markdown-driven 靜態站模型確實比 marimo 適合。
**但那不是「單人分析師的探索儀表板」，是另一個產品。**
而且即使那樣，我也會先看 Observable Framework —— 只是它同樣停更（§2.3）。

---

## 10. 必答四：最務實的選擇（完整答案）

**情境**：單人分析師、資料在本地 Parquet、要能點選篩選下鑽。

### 推薦架構：分層，預設最輕

```
┌─────────────────────────────────────────────────────────┐
│ 資料層（已定案，不動）                                    │
│   本地 Parquet  ──  DuckDB  ──  build_chart(df) 純函式    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   ┌─────────┐      ┌──────────┐     ┌───────────┐
   │ L1 預設 │      │ L2 需要時│     │ L3 少數   │
   │ Altair  │      │ marimo   │     │ marimo    │
   │selection│      │ html-wasm│     │ run       │
   │+ Jinja2 │      │          │     │           │
   │單檔 HTML│      │離線可互動│     │本機 server│
   └─────────┘      └──────────┘     └───────────┘
   寄 email          寄 zip           自己用/內網
```

### 為什麼是這個組合

| 判斷 | 理由 |
|---|---|
| **預設 L1（Altair selection）** | 零新依賴、零新框架、直接嵌進既有 Jinja2 報告、單檔可寄。**多數「下鑽」需求其實在這層就夠** |
| **需要真互動時升 L2（marimo html-wasm）** | 唯一能「離線 + 真 Python + 真 DuckDB + 可寄送」的方案。DuckDB 有 Pyodide 支援（§5.3 原文佐證） |
| **只在必要時用 L3** | 資料太大塞不進瀏覽器、或資料機密不能外流時 |
| **不引入第二個框架** | L2 與 L3 都是 marimo，**只學一套 API**。這對單人分析師的認知負擔是決定性的 |

### 明確不做的事

- ❌ 不裝 Metabase / Superset / Lightdash（為單人養基礎設施）
- ❌ 不引入 Node 生態（Evidence / Observable Framework）
- ❌ 不把 Parquet 轉成 SQLite 去餵 Datasette
- ❌ 不用 Streamlit 當主力（無靜態匯出，交付斷鏈）
- 🟡 Rill 可裝來當**個人 EDA 工具**，但**不列入 Skill 產出路徑**

---

## 11. 可重用資產

### 11.1 決策規則（可直接寫進 SKILL.md）

```
規則 D1（預設層級）：
  若需求是「圖表內篩選 / 跨圖聯動 / hover 看細節」
  → 用 Altair selection + transform_filter，產單檔 HTML，嵌進 Jinja2 報告。
  不要開新框架。

規則 D2（升級條件）：
  若需求包含以下任一，才升級到 marimo：
    - 需要在瀏覽器端重新執行 SQL（任意維度下鑽，非預先定義的篩選）
    - 需要使用者上傳自己的資料
    - 需要跑 Python 計算（非純視覺篩選）
  → marimo notebook + `marimo export html-wasm`

規則 D3（server 條件）：
  只有以下情況才用 `marimo run`（需長駐 process）：
    - 資料 > 200 MB（瀏覽器塞不下）
    - 資料機密不可離開本機
    - 需要連即時資料源
  → 明確告知使用者「這份不能寄，只能自己看或架內網」

規則 D4（框架否決）：
  任何「儀表板定義不是純文字檔」的方案一律否決
  （Metabase / Superset / Lightdash：dashboard 存在資料庫 row 裡）。
  理由：AI agent 無法用 Read/Edit 維護它。

規則 D5（維護狀態查核）：
  引入任何新的儀表板/視覺化套件前，必須實際查：
    a) GitHub API `pushed_at` 與最新 commit 日期 —— 超過 6 個月停滯 = 高風險
    b) 最新 release 日期（不是 star 數）
    c) 近 3 個月的社群 PR 是否有被合併（積壓 = 團隊已離開）
    d) 母公司是否有商業版導流跡象（README 置頂橫幅）
  「archived = false」不等於「活著」。

規則 D6（Python 版本查核，被坑三次的那條）：
  引入任何 Python 套件前，查 https://pypi.org/pypi/{pkg}/json：
    a) requires_python 是否涵蓋 3.14
    b) classifiers 是否含 "Programming Language :: Python :: 3.14"
    c) 【新增，避免假警報】若 b 缺席，去看 urls[].filename 的 wheel tag：
         - 有 "abi3" (例 cp37-abi3-win_amd64) → 向前相容，3.14 可用，放行
         - 只有 cp312/cp313 等特定版 tag     → 真的沒有 3.14 wheel，會退回編譯原始碼
         - "none-any"（純 Python）           → 通常沒問題
  b 缺席且非 abi3 ≠ 一定不能跑，但代表上游沒測過 → 必須自己跑 smoke test 才准用。
  連相依鏈一起查（例：選 Panel 就要查 bokeh / param / holoviews / hvplot）。

  【實例】vl-convert-python 1.9.0.post1：
    requires_python=">=3.7"，classifiers 只有 "CPython"（無任何版本號）
    → 乍看是紅燈，但 wheel 是 vl_convert_python-1.9.0.post1-cp37-abi3-win_amd64.whl
    → abi3 = 向前相容所有 CPython >= 3.7 → 3.14 可用。虛驚。

規則 D7（單一真實來源）：
  chart 建構邏輯必須是一個純函式 build_chart(df) -> alt.Chart。
  四種交付物（Jinja2 報告 / pptx / great-tables / marimo）都從它衍生，
  不准各寫一套。實作見 §11.7。

規則 D8（繁中字型，三條路徑分開處理）：
  a) HTML 互動圖 → 字型來自「收件人的機器」
     → 用 fallback 堆疊 + 最好 @font-face 內嵌 Noto Sans TC
  b) PNG -> pptx  → 字型來自「產圖的機器」
     → 缺字是靜默失敗（豆腐字 □□□），必須產圖前檢查 + 肉眼驗收
     → vl_convert.register_font_directory() 可指定字型目錄
  c) marimo 介面  → --marimo-text-font / --marimo-heading-font /
                    --marimo-monospace-font（官方保證跨版本穩定的三個變數）
  永遠不要用 Microsoft YaHei（簡體字型）做繁中排版。

規則 D9（交付形式優先於技術偏好）：
  選型的第一個問題不是「哪個框架好」，是「這份東西怎麼送到對方手上」。
    email 附件 → 只有 L1 做得到（Altair inline=True 單檔）
    可以給 URL → L2 可用（marimo html-wasm，需靜態 host）
    只有自己看 → L3 也可以
  ⚠️ marimo export html-wasm 的產出【不能】雙擊開啟（file:// 被瀏覽器擋），
     必須用 HTTP 提供。這一點極容易誤判，寫進 Skill 時要明講。
```

### 11.2 環境查核腳本（可直接放進 Skill 的 scripts/）

```python
#!/usr/bin/env python3
"""check_dashboard_deps.py —— 對應規則 D6。
用法： python check_dashboard_deps.py
在引入任何新套件前跑一次，避免重蹈「classifier 沒有 3.14」的覆轍。
"""
from __future__ import annotations
import json
import sys
import urllib.request

TARGET = f"{sys.version_info.major}.{sys.version_info.minor}"  # 例如 "3.14"

PACKAGES = [
    # 儀表板候選
    "marimo", "streamlit", "panel", "shiny",
    # 既定堆疊（回歸檢查）
    "altair", "great-tables", "duckdb", "pyarrow", "jinja2", "python-pptx",
]


def check(pkg: str) -> dict:
    url = f"https://pypi.org/pypi/{pkg}/json"
    with urllib.request.urlopen(url, timeout=30) as r:
        info = json.load(r)["info"]
    classifiers = [
        c.rsplit("::", 1)[-1].strip()
        for c in info.get("classifiers", [])
        if c.startswith("Programming Language :: Python ::")
    ]
    return {
        "package": pkg,
        "version": info["version"],
        "requires_python": info.get("requires_python"),
        "has_target_classifier": TARGET in classifiers,
        "classifiers": classifiers,
    }


def main() -> int:
    print(f"目標 Python 版本：{TARGET}\n")
    warnings = 0
    for pkg in PACKAGES:
        try:
            r = check(pkg)
        except Exception as exc:  # noqa: BLE001
            print(f"  ?  {pkg:16} 查詢失敗：{exc}")
            warnings += 1
            continue
        mark = "OK " if r["has_target_classifier"] else "!! "
        if not r["has_target_classifier"]:
            warnings += 1
        print(
            f"  {mark} {pkg:16} v{r['version']:10} "
            f"requires_python={r['requires_python']!s:12} "
            f"{TARGET}-classifier={r['has_target_classifier']}"
        )
    print(
        f"\n{warnings} 個套件需要人工確認"
        f"（無 {TARGET} classifier 者必須自行 smoke test 後才准使用）。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 11.3 L1 範本：Altair 純靜態互動（可寄送單檔）

**這回答什麼行銷/商業問題**：
「我要給主管一份月報，他想自己點通路看細分數字，但我不想架 server，也不想他裝任何東西。」

```python
"""L1 靜態互動範本：selection + transform_filter。
產出單一 HTML，資料內嵌，可直接 email。無需 Python / server。
"""
import altair as alt
import duckdb
import pandas as pd

PARQUET = r"E:\Projects\行銷分析\data\marts\fact_campaign_daily.parquet"

con = duckdb.connect()
df: pd.DataFrame = con.execute(
    f"""
    SELECT date, channel, campaign, spend, revenue, conversions
    FROM read_parquet('{PARQUET}')
    WHERE date >= CURRENT_DATE - INTERVAL 90 DAY
    """
).df()

# --- 選取器：點 legend 或長條即篩選全頁 ---
channel_sel = alt.selection_point(fields=["channel"], bind="legend")
brush = alt.selection_interval(encodings=["x"])

base = alt.Chart(df).add_params(channel_sel)

trend = (
    base.mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="日期"),
        y=alt.Y("sum(revenue):Q", title="營收"),
        color=alt.Color("channel:N", title="通路"),
        opacity=alt.condition(channel_sel, alt.value(1.0), alt.value(0.15)),
        tooltip=["date:T", "channel:N", "sum(revenue):Q", "sum(spend):Q"],
    )
    .add_params(brush)
    .properties(width=680, height=260, title="營收趨勢（點 legend 篩選、拖曳選期間）")
)

# 下方長條會被上方 brush 的期間篩選 —— 這就是「下鑽」
breakdown = (
    base.mark_bar()
    .transform_filter(brush)
    .transform_filter(channel_sel)
    .encode(
        x=alt.X("sum(revenue):Q", title="營收"),
        y=alt.Y("campaign:N", sort="-x", title="活動"),
        color=alt.Color("channel:N", legend=None),
        tooltip=["campaign:N", "sum(revenue):Q", "sum(conversions):Q"],
    )
    .properties(width=680, height=300, title="選定期間的活動明細")
)

dashboard = (
    (trend & breakdown)
    .configure_view(stroke=None)
    .configure(font="Noto Sans TC")  # 見 §11.8：一行設定全圖字型
)

# ★ inline=True 是關鍵：把 Vega JS 全部內嵌，產出真正離線可用的單檔
#   沒有它 → 預設走 CDN → 收件人斷網或防火牆擋 CDN 就開不出圖
#   需先 pip install vl-convert-python
dashboard.save("monthly_report_interactive.html", inline=True)
```

**要點**：
- `add_params` 定義選取器，`transform_filter` 消費它 —— **這對組合就是全部的秘訣**
- `bind="legend"` 讓 legend 直接變成篩選器，零額外 UI 程式碼
- **`inline=True` 不能漏**，否則產出的不是真正可寄的單檔

**【材料原文】Altair 官方文件對 `inline` 的說明**：

> "the `inline=True` keyword argument may be provided to `chart.save` to generate
> an HTML file that includes all necessary JavaScript dependencies inline."

> 需額外安裝 `vl-convert`：`pip install vl-convert-python`
> 產出的檔案較大，但 "completely self-contained and viewable without internet access"。

### 11.4 L2 範本：marimo notebook（同時是 app）

**這回答什麼行銷/商業問題**：
「客戶想自己切維度看 ROAS，我事先不知道他要切哪些。而且他公司防火牆連不到我的 server。」

```python
# dashboard.py —— 用 `marimo edit dashboard.py` 開發
#                 用 `marimo run dashboard.py` 當 app
#                 用 `marimo export html-wasm dashboard.py -o dist/ --mode run` 產離線交付物
import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import duckdb
    return alt, duckdb, mo


@app.cell
def _(mo):
    # 資料位置：WASM 模式下要放 public/，用 mo.notebook_location() 取用
    data_path = str(mo.notebook_location() / "public" / "fact_campaign_daily.parquet")
    return (data_path,)


@app.cell
def _(duckdb, data_path):
    con = duckdb.connect()
    channels = con.execute(
        f"SELECT DISTINCT channel FROM read_parquet('{data_path}') ORDER BY 1"
    ).df()["channel"].tolist()
    return channels, con


@app.cell
def _(channels, mo):
    channel_pick = mo.ui.multiselect(
        options=channels, value=channels, label="通路"
    )
    date_pick = mo.ui.date_range(label="期間")
    mo.hstack([channel_pick, date_pick])
    return channel_pick, date_pick


@app.cell
def _(channel_pick, con, data_path, date_pick, mo):
    # SQL 是 f-string —— UI 的 .value 直接插進 WHERE，這就是「下鑽」
    picked = "', '".join(channel_pick.value)
    df = mo.sql(
        f"""
        SELECT date, channel, campaign,
               SUM(spend)   AS spend,
               SUM(revenue) AS revenue,
               SUM(revenue) / NULLIF(SUM(spend), 0) AS roas
        FROM read_parquet('{data_path}')
        WHERE channel IN ('{picked}')
          AND date BETWEEN '{date_pick.value[0]}' AND '{date_pick.value[1]}'
        GROUP BY 1, 2, 3
        """,
        engine=con,
    )
    return (df,)


@app.cell
def _(alt, df, mo):
    # 沿用既有 design token 的 build_chart()，只多包一層 mo.ui.altair_chart
    base = (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X("spend:Q", title="花費"),
            y=alt.Y("roas:Q", title="ROAS"),
            color=alt.Color("channel:N", title="通路"),
            size=alt.Size("revenue:Q", title="營收"),
            tooltip=["campaign:N", "spend:Q", "revenue:Q", "roas:Q"],
        )
        .properties(height=380)
    )
    chart = mo.ui.altair_chart(base)  # 選取結果會回傳 Python
    chart
    return (chart,)


@app.cell
def _(chart, mo):
    # chart.value 就是使用者在圖上刷選出來的 DataFrame
    mo.md(f"### 已選取 {len(chart.value)} 個活動")
    mo.ui.table(chart.value, page_size=15)
    return


if __name__ == "__main__":
    app.run()
```

**要點**：
- `mo.sql(f"...")` —— UI `.value` 插進 SQL，**不需要寫任何 callback**
- `mo.ui.altair_chart(base)` —— 既有 Altair 主題原封不動，`chart.value` 拿到選取結果
- 同一個檔：`marimo edit` 探索 / `marimo run` 當 app / `export html-wasm` 交付

### 11.5 交付指令速查表（旗標皆已對原始碼查證，§5.2.1）

```bash
# ============ L1：靜態互動單檔（Altair）— 唯一能當 email 附件的 ============
python build_report.py     # 內部：chart.save("out.html", inline=True)
                           # 前置：pip install vl-convert-python

# ============ L2：WASM 互動（marimo）— 需靜態 host，不能 file:// ============
mkdir -p dist_src/public
cp data/marts/*.parquet dist_src/public/

marimo export html-wasm dashboard.py -o dist/ --mode run
#   -o            = 【目錄】(required)，產出 index.html + assets/
#   --mode run    = 唯讀，程式碼鎖定（給客戶）           [default]
#   --mode edit   = 使用者可編輯 notebook（給同事/教學）
#   --show-code   = run 模式下預設顯示程式碼            [default: --no-show-code]
#   --execute     = 匯出前先執行，把輸出嵌入當預覽（首屏不會空白，推薦）
#   --include-cloudflare = 一併產生 index.js + wrangler.jsonc，方便部署 CF

# ⚠️ 必須用 HTTP 提供，不能雙擊開啟：
cd dist && python -m http.server 8000     # 本機驗證
# 正式：推 GitHub Pages / Cloudflare Pages（皆免費靜態託管）

# ============ L3：本機 / 內網 server（需長駐 Python）============
marimo run dashboard.py --port 2718
marimo run dashboard.py --headless --host 0.0.0.0   # 內網分享

# ============ 其他 render target（同一份 notebook，零重寫）============
marimo export html   dashboard.py -o snapshot.html   # 單檔靜態存證，可 file:// 開
                                                     # --include-code 預設為 True，
                                                     # 給客戶時記得加 --no-include-code
marimo export script dashboard.py -o pipeline.py     # 排程用（拓樸排序）
marimo export ipynb  dashboard.py -o share.ipynb     # 給還在用 Jupyter 的人
marimo export pdf    dashboard.py -o report.pdf      # 存檔 / 列印
```

**兩個最容易踩的坑**：

1. `marimo export html` 的 `--include-code` **預設是 `True`**
   → 交付給外部客戶時要記得 `--no-include-code`，否則原始碼一起送出去。
2. `marimo export html-wasm` 的 `-o` 是**目錄不是檔案**
   → 寫成 `-o out.html` 會產生一個叫 `out.html` 的**資料夾**。

### 11.6 字型檢查腳本（對應 §5.7，防豆腐字）

**這回答什麼行銷/商業問題**：
「投影片交出去，圖表的中文標題全變成方框 □□□，在客戶面前開簡報才發現。」

```python
#!/usr/bin/env python3
"""check_cjk_fonts.py —— 產圖前的繁中字型可用性檢查。
針對 vl-convert（Altair -> PNG -> python-pptx）路徑，
因為該路徑用的是「產圖這台機器」的字型，缺字會靜默產出豆腐字。
"""
from __future__ import annotations

import sys

# 依偏好排序的 zh-TW 字型堆疊；與 §5.7.2 的 CSS font-family 對齊
PREFERRED = [
    "Noto Sans TC",
    "Microsoft JhengHei UI",
    "Microsoft JhengHei",
    "PingFang TC",
]

# 明確不要用的（簡體字型 / 點陣襯線）
DISCOURAGED = {
    "Microsoft YaHei": "簡體中文字型，繁中會出現異體字",
    "MingLiU": "點陣襯線，螢幕顯示品質差",
    "PMingLiU": "點陣襯線，螢幕顯示品質差",
    "DFKai-SB": "標楷體，不適合數據圖表",
}

PROBE = "行銷分析：轉換率與投資報酬率"  # 探針字串，含常用繁中字


def installed_font_families() -> set[str]:
    """列出本機已註冊的字型家族名（Windows 走登錄檔，其他平台走 matplotlib）。"""
    if sys.platform == "win32":
        import winreg

        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
        families: set[str] = set()
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            for i in range(winreg.QueryInfoKey(key)[1]):
                name, _value, _type = winreg.EnumValue(key, i)
                # 登錄檔名稱形如 "Microsoft JhengHei & Microsoft JhengHei UI (TrueType)"
                name = name.replace("(TrueType)", "").replace("(OpenType)", "")
                for part in name.split("&"):
                    if part.strip():
                        families.add(part.strip())
        return families

    from matplotlib import font_manager

    return {f.name for f in font_manager.fontManager.ttflist}


def main() -> int:
    families = installed_font_families()

    available = [f for f in PREFERRED if f in families]
    print("繁中字型檢查")
    print("=" * 52)
    for f in PREFERRED:
        print(f"  {'OK ' if f in families else '-- '} {f}")

    if not available:
        print(
            "\n[FAIL] 沒有任何建議的繁中字型。"
            "\n       PNG/PPTX 產出會是豆腐字。"
            "\n       解法：安裝 Noto Sans TC "
            "(https://fonts.google.com/noto/specimen/Noto+Sans+TC)"
            "\n       或用 vl_convert.register_font_directory() 指定字型目錄。"
        )
        return 1

    print(f"\n[OK] 將使用：{available[0]}")

    found_bad = [f for f in DISCOURAGED if f in families]
    if found_bad:
        print("\n[提醒] 本機存在但不建議用於繁中圖表的字型：")
        for f in found_bad:
            print(f"       - {f}：{DISCOURAGED[f]}")

    # 實際渲染驗證（需 vl-convert-python）——這一步才是真的證明沒有豆腐字
    try:
        import vl_convert as vlc
    except ImportError:
        print("\n[SKIP] 未安裝 vl-convert-python，跳過實際渲染驗證。")
        print("       pip install vl-convert-python 之後再跑一次。")
        return 0

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"values": [{"a": PROBE, "b": 1}]},
        "mark": "bar",
        "encoding": {"x": {"field": "b", "type": "quantitative"},
                     "y": {"field": "a", "type": "nominal"}},
        "title": PROBE,
        "config": {"font": available[0]},
    }
    png = vlc.vegalite_to_png(vl_spec=spec, scale=2)
    out = "font_probe.png"
    with open(out, "wb") as fh:
        fh.write(png)
    print(f"\n[OK] 已產出 {out}（{len(png):,} bytes）——請用肉眼確認沒有 □ 方框。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

⚠️ **這個腳本我沒有實際執行過**（本機未安裝 altair / vl-convert-python）。
字型列舉的部分邏輯來自實際查過的登錄檔結構（§5.7.1 的輸出就是這樣取得的），
但整支腳本需要先跑一次驗證。

### 11.7 Altair 繁中主題（design token 共用的具體實作）

**這回答什麼行銷/商業問題**：
「四種交付物（報告 / 投影片 / 表格 / 儀表板）的視覺要像同一家公司出的，
不能報告是一種字、簡報是另一種字。」

```python
"""marketing_theme.py —— 單一視覺來源。
四種交付物都 import 這支，確保 design token 一致。
"""
from __future__ import annotations

import altair as alt

# --- design token（與 Jinja2 報告的 CSS 變數、pptx 母片共用同一組值）---
FONT = "Noto Sans TC"          # 見 §5.7.2 的 fallback 討論
FONT_MONO = "JetBrains Mono"

PALETTE = [
    "#2E5C8A", "#C7522A", "#4E8067", "#8A6D3B",
    "#6B4E71", "#3D7A8A", "#A34D6B", "#5C6B3D",
]

INK = "#1A1A1A"
MUTED = "#6B6B6B"
GRID = "#E5E5E5"


@alt.theme.register("marketing_tw", enable=True)
def marketing_tw() -> alt.theme.ThemeConfig:
    """繁中行銷分析主題。註冊後全域生效，所有 chart 自動套用。"""
    return {
        "config": {
            # 全域字型（最省事的一招，見 §11.8）
            "font": FONT,
            "title": {
                "font": FONT,
                "fontSize": 16,
                "fontWeight": 600,
                "color": INK,
                "anchor": "start",
                "offset": 12,
            },
            "axis": {
                "labelFont": FONT,
                "titleFont": FONT,
                "labelFontSize": 11,
                "titleFontSize": 12,
                "labelColor": MUTED,
                "titleColor": INK,
                "gridColor": GRID,
                "domainColor": GRID,
                "tickColor": GRID,
            },
            "legend": {
                "labelFont": FONT,
                "titleFont": FONT,
                "labelFontSize": 11,
                "titleFontSize": 12,
                "labelColor": MUTED,
                "titleColor": INK,
            },
            "header": {"labelFont": FONT, "titleFont": FONT},
            "range": {"category": PALETTE},
            "view": {"stroke": None, "continuousWidth": 640, "continuousHeight": 320},
        }
    }


def build_chart(df, *, kind: str = "trend") -> alt.Chart:
    """★ 規則 D7 的實作：唯一的 chart 建構函式。

    四種交付物都呼叫它：
      Jinja2 報告   -> build_chart(df).save(..., inline=True)
      pptx 投影片   -> vlc.vegalite_to_png(build_chart(df).to_dict())
      marimo 儀表板 -> mo.ui.altair_chart(build_chart(df))
      great-tables -> 不用（表格走另一條路，但共用 PALETTE / FONT）
    """
    if kind == "trend":
        return (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="日期"),
                y=alt.Y("sum(revenue):Q", title="營收"),
                color=alt.Color("channel:N", title="通路"),
                tooltip=["date:T", "channel:N", "sum(revenue):Q"],
            )
        )
    raise ValueError(f"未知的圖表類型：{kind}")
```

**【材料原文】主題註冊 API 的來源**：
Altair 6.x 的裝飾器形式（來自 Altair 官方文件與社群範例）：

```python
@alt.theme.register("custom_font", enable=True)
def custom_font() -> alt.theme.ThemeConfig:
    font = "Your Font Name"
    return {
        "config": {
            "title": {'font': font},
            "axis": {"labelFont": font, "titleFont": font},
            "header": {"labelFont": font, "titleFont": font},
            "legend": {"labelFont": font, "titleFont": font},
        }
    }
```

### 11.8 一行設定全圖字型（比逐項設定省事）

Altair 官方文件（`configuration.html`）對頂層 `font` 屬性的說明（verbatim）：

> "Default font for all text marks, titles, and labels."

```python
# 方式 A：單一 chart
chart.configure(font="Noto Sans TC")

# 方式 B：主題內（推薦，見 §11.7）
{"config": {"font": "Noto Sans TC"}}
```

逐項設定（需要細調時）：
```python
chart.configure_axis(labelFont="Noto Sans TC", titleFont="Noto Sans TC")
chart.configure_title(font="Noto Sans TC")
chart.configure_legend(labelFont="Noto Sans TC", titleFont="Noto Sans TC")
```

**【評註】** `configure(font=...)` 是 Vega-Lite 的頂層預設，
其他 `configure_*` 是覆寫。**先用頂層設一次，只在需要差異化時才覆寫** ——
這樣主題檔最短、最不容易漏掉某個元素（漏掉的那個就會變成豆腐字或英文預設字型）。

### 11.9 選型檢查清單（新專案照跑）

```
[ ] 1. 交付形式是什麼？（★ 這題決定一切，先問）
       email 附件，對方雙擊    → 只能 L1（Altair inline=True）
       給一個 URL              → L1 或 L2 皆可
       只有自己 / 內網看       → L1 / L2 / L3 皆可
       → 排除 Streamlit / Rill / Metabase / Superset / Lightdash（若需附件或無伺服器）

[ ] 2. 使用者需要「重跑 SQL」還是只要「篩選既有圖」？
       只篩選（維度已知）→ L1 Altair selection，不要開框架
       要重跑（維度未知）→ L2 marimo html-wasm

[ ] 3. 資料量多大？
       < 50 MB   → L1 或 L2 都行
       50-200 MB → L2（注意 Pyodide 首次載入時間）
       > 200 MB  → L3，且明確告知不可寄送
       ※ 200 MB 這個界線我沒實測，是估計值，見 §12

[ ] 4. 相依套件都查過 PyPI 了嗎？（規則 D6）
       → 跑 scripts/check_dashboard_deps.py
       → classifier 缺 3.14 時，記得先看是不是 abi3 wheel（可能是假警報）

[ ] 5. chart 建構是純函式嗎？四種交付物共用同一個嗎？（規則 D7）
       → 見 §11.7 的 build_chart()

[ ] 6. 繁中字型檢查過了嗎？（規則 D8）
       → 跑 scripts/check_cjk_fonts.py
       → HTML 路徑：確認有 @font-face 內嵌或 fallback 堆疊
       → PNG/pptx 路徑：確認產圖機有字型，肉眼看過沒有 □ 方框

[ ] 7. L1 有加 inline=True 嗎？（否則斷網打不開）

[ ] 8. L2 有記得它不能 file:// 雙擊嗎？靜態 host 準備好了嗎？

[ ] 9. marimo export html 給外部時有加 --no-include-code 嗎？
       （--include-code 預設為 True，會把原始碼一起送出）

[ ] 10. 引入的新套件過去 6 個月有 commit 嗎？社群 PR 有被合併嗎？（規則 D5）
```

---

## 12. 查證狀態總表（誠實區）

### 12.1 ✅ 已在本次調研中查證（v1 遺留問題已關閉）

| # | 項目 | 結論 | 出處 |
|---|---|---|---|
| 1 | marimo `export html-wasm` 的 CLI 旗標 | **已對原始碼查證**。`--mode {edit,run}` 存在，default=`run`。另有 `--show-code`、`--include-cloudflare`、`--execute` | §5.2.1 |
| 2 | **WASM 產出能否 file:// 開啟** | **不能**。原始碼與官方文件皆明載須經 HTTP。**v1 寫錯，已更正** | §5.2.2 |
| 3 | Altair 離線單檔 | **可以**，`chart.save('x.html', inline=True)`，需 `vl-convert-python` | §11.3 |
| 4 | Altair 全域字型 API | `configure(font=...)` 為頂層預設；主題用 `@alt.theme.register(..., enable=True)` | §11.7 / §11.8 |
| 5 | 本機繁中字型盤點 | **已查登錄檔**。`Noto Sans TC`、`Microsoft JhengHei UI` 皆已安裝 | §5.7.1 |
| 6 | vl-convert 字型機制 | 用**產圖機**的系統字型；`register_font_directory()` 可加目錄 | §5.7.3 |
| 7 | marimo 主題/字型 API | `App(css_file=)` / `[tool.marimo.display] custom_css`；三個字型 CSS 變數為 public API | §5.6 |
| 8 | vl-convert-python 的 3.14 相容 | **abi3 wheel，可用**。classifier 缺席是假警報 | §4.1(a) |
| 9 | shinylive 的 3.14 相容 | **classifier 只到 3.13**，py-shiny 靜態路徑有風險 | §4.1(b) |
| 10 | stlite 是否還活著 | **活躍**（push 2026-07-25，1,652 stars），但非官方 | §3.3 |

### 12.2 ⚠️ 仍未查證 —— **不要當成結論使用**

| # | 待驗證項目 | 為什麼重要 | 建議驗證方式 |
|---|---|---|---|
| A | **實際渲染出圖看中文** | 我驗證了「字型存在」與「怎麼設定」，但**沒有實際產出任何一張含中文的圖**。豆腐字只有肉眼看得出來 | 裝 `altair` + `vl-convert-python`，跑 §11.6 腳本，開 `font_probe.png` 目視 |
| B | **marimo WASM 裡的 duckdb 版本與行為** | 文件明列 Pyodide 支援 duckdb，但**版本可能落後** PyPI 的 1.5.5，且 `read_parquet` 讀 `public/` 路徑的行為未測 | export 一份含 `read_parquet` 的 notebook，起 `python -m http.server` 實測 |
| C | **WASM 的 Parquet 大小上限** | 決定 L2/L3 分界。**我寫的 200 MB 是估計值，沒有依據** | 用 10/50/100/200/500 MB 實測首次載入時間與是否 OOM |
| D | **marimo 在 Windows 11 的實際行為** | 環境是 Windows，路徑分隔符/UTF-8 編碼常出事；§11.4 範本的 `data_path` 用 `str()` 包 Path，未驗證 | 裝起來跑 §11.4 |
| E | §11.6 字型檢查腳本本身 | **我寫了但沒執行過**（本機無 altair/vl-convert） | 直接跑一次 |
| F | Evidence 官方「OSS 維護模式」聲明 | 影響 §9 結論的**強度**（目前是 commit 停滯 + Studio 導流的**間接**證據，非官方聲明） | 查 Evidence blog / changelog / Slack |
| G | `python-pptx 1.0.2` 在 3.14 實跑 | 既定堆疊裡唯一無 3.14 背書者（且非 abi3，是純 Python 套件） | 產一份含中文的 pptx 並開啟 |
| H | macOS 端字型 fallback | §5.7.2 我列了 `PingFang TC`，**沒有 mac 可驗證** | 有 mac 時測 |
| I | Panel `convert --to pyodide-worker` | §3.4 我給它「部署 ✅」，但**沒有實際查證該指令與其 3.14 相容性**（僅憑既有認知） | 查 Panel 文件 + 實測 |
| J | `mercury-project/mercury` | GitHub API 回傳 null，**repo 不存在或已改名** | 未追查，判定不影響結論 |

### 12.3 本次調研的方法論限制（要說清楚）

1. **全部是文件與 metadata 調研，零實機測試。** 本機只裝了
   `duckdb 1.5.5` / `pandas 2.3.3` / `pyarrow 23.0.0` / `python-pptx 1.0.2`，
   **marimo、altair、great-tables、jinja2 都沒裝**，因此所有程式碼範本都是
   「依文件撰寫、未執行」。用之前請先跑一次。
2. **維護狀態用 GitHub API 的 `pushed_at` / commits / releases 判斷**，
   這是硬資料；但「為什麼停更」是我的推論（例如 Evidence 轉商業版），
   已在文中標為【評註】。
3. **繁中支援（準則 3）全部方案我都給 🟡「未實測」**，
   因此 §6 評分矩陣中該欄對所有方案一律給 2 分 —— **這一欄目前不具鑑別力**，
   實測後可能改變排序。不過準則 3 的權重（3）低於準則 1（5）與 2（4），
   即使全部翻盤也不足以動搖 marimo 的第一名。

---

## 13. 一頁總結（貼進 SKILL.md 的版本）

```
儀表板選型定案：marimo（主）+ Altair selection（輕量層）

分三層，預設最輕：
  L1  Altair selection + Jinja2   → 真單檔 HTML，可當 email 附件
                                     ★ 必須 chart.save(..., inline=True)
                                     ★ 需 pip install vl-convert-python
  L2  marimo export html-wasm     → 瀏覽器端跑 Python+DuckDB，無需後端
                                     ⚠️ 產出是「目錄」，且【不能】file:// 雙擊
                                     ⚠️ 必須靜態 host（GitHub/Cloudflare Pages）
  L3  marimo run                  → 需長駐 Python server，資料大/機密時才用

為什麼是 marimo（六準則加權 54 分，全場最高）：
  1 AI 生成    純 .py 檔，agent 可 Read/Edit/diff/review       ★決定性
  2 DuckDB     官方預設引擎就是 DuckDB，SQL cell 直讀 parquet  ★決定性
  3 繁中       未實測（三個字型 CSS 變數是官方 public API）
  4 py3.14     requires_python >=3.10，有 3.14 classifier ✅
  5 部署       7 種 export，html-wasm 無需後端 Python
  6 Altair     mo.ui.altair_chart 原生雙向綁定，主題直接沿用   ★決定性

為什麼不是別的（皆為 2026-07-26 實測 GitHub API）：
  Evidence.dev  最後 commit 2026-02-18（5 個月前），社群 PR 積壓未合，
                README 置頂導流商業版 Evidence Studio → 否決（維護風險）
  Observable FW 最後 release 2026-03-02，之後僅 3 筆 CI commit → 否決
  Streamlit     無官方靜態匯出（stlite 活躍但非官方）→ 備案
  Panel         技術可行，但 agent 生成穩定度與 Altair 整合遜於 marimo
  py-shiny      同上；且 shinylive 0.8.9 classifier 只到 3.13，靜態路徑有風險
  Rill          DuckDB 原生、release 每週一版，但無靜態匯出 + 圖表 token 不通
                → 不入 Skill，但推薦當個人 EDA 工具（rill start 指向 parquet 目錄）
  Datasette     核心活躍（1.0a37, 2026-07-14）但 SQLite 導向，與 Parquet 倉儲衝突 → 否決
  Metabase/Superset/Lightdash
                三者皆極活躍，但儀表板存在資料庫 row 而非檔案，
                agent 無法用 Read/Edit 維護 → 結構性否決（準則 1 為最高權重）
  Dash          PyPI classifier 只到 3.12，無 3.13/3.14 → 否決

三個最容易踩的坑（血淚，寫進 SKILL.md）：
  1. marimo export html-wasm 產出【不能雙擊開啟】，必須 HTTP 提供
  2. Altair chart.save() 不加 inline=True 會走 CDN，斷網開不出圖
  3. marimo export html 的 --include-code 預設 True，交外部要加 --no-include-code

架構樞紐（最重要的一條）：
  build_chart(df) -> alt.Chart  必須是純函式，
  Jinja2 報告 / pptx 投影片 / great-tables / marimo 儀表板 四者共用它。
  這才是「並存而非取代」。實作見 §11.7。
```
