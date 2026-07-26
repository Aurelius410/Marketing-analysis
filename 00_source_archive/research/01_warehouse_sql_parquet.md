# 單機行銷資料倉儲技術選型調研：DuckDB + Parquet + SQL

**調研日期**：2026-07-26
**目標環境**：Windows 11 Home (10.0.26200)、Python 3.14.1、繁體中文
**倉儲層前提**：DuckDB + Parquet + SQL（已定案，本文不再比較其他引擎）
**資料型態**：CRM 交易、網站行為事件、廣告投放成效、零售 POS 門市（四種全部）

---

## 0. 查證方法與可信度聲明

本文所有「維護狀態、版本、是否 deprecated」的敘述，來源限於以下三種**我實際抓取過的**端點：

| 來源 | 用途 | 可信度 |
|---|---|---|
| `api.github.com/repos/{owner}/{repo}` | stars、archived 旗標、`pushed_at`（最後推送） | 高（原始 JSON） |
| `pypi.org/pypi/{pkg}/json` | 版本號、上傳時間、`requires_python`、wheel 檔名、授權、classifiers | 高（原始 JSON，本機 Python 解析，非摘要） |
| `duckdb.org/docs/current/*`、`ducklake.select/docs/stable/*` | 官方行為規格與最佳實務 | 高（HTML 抓取後抽 `#main_content_wrap`） |

**兩點方法論警告**（這影響你怎麼讀下面的表）：

1. **PyPI classifiers 不可信，wheel 檔名才可信。** 例：`statsmodels 0.14.6` 的 classifier 最高只到 Python 3.13，但它**實際有** `statsmodels-0.14.6-cp314-cp314-win_amd64.whl`。反過來，`requires_python` 是 pip 會**真正強制執行**的欄位。下文區分「classifier 沒寫」（軟訊號）與「requires_python 擋住」（硬阻擋）。
2. **GitHub `pushed_at` ≠ 專案健康。** 它包含機器人推送與分支。我另外用 PyPI 的**發版節奏**交叉驗證，兩者都列出。

**GitHub API 匿名額度（60 req/hr）在調研中途耗盡**，因此部分 repo 的「最後 release」改由 PyPI 上傳時間佐證（同一份發布物，時間戳等價）。凡是我沒抓到的，第 8 節誠實列出。

---

## 1. 各工具逐一檢視

### 1.1 duckdb/duckdb

- **repo**：https://github.com/duckdb/duckdb
- **star 數量級**：約 39.7k（39,706）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T20:42:48Z**（調研前 2 天）
- **最新正式版**：**v1.5.5**，release 發佈於 **2026-07-22**，PyPI 同版上傳 2026-07-22T10:53:19
- **archived**：否。授權 MIT。open issues 692
- **額外訊號**：PyPI 上同時可見 `1.6.0.dev339`（2026-07-25）與 `1.5.6.dev5`（2026-07-25）——代表 **1.5.x 維護分支與 1.6 開發分支並行**，是健康的雙軌發布，不是停滯。官方文件另提到 **DuckDB v2.0 預計 2026 秋季**。

**定位**：整個架構的核心。in-process OLAP 引擎，直接對 Parquet 做 zero-copy 掃描。

**Python 3.14 相容性（關鍵）**：`requires_python = >=3.10.0`，且**實際存在** `duckdb-1.5.5-cp314-cp314-win_amd64.whl`。你的 Python 3.14.1 可直接 `pip install duckdb`，無需降版。

**適用**：本專案 100% 的倉儲層。四種資料型態全部適用。
**不適用**：多行程並發寫入（見 6.8）；需要低延遲高頻小查詢的線上服務（官方明說「不是主要設計目標」）。

**取捨**：沒有取捨，這是前提。真正的取捨在「用 DuckDB 原生 `.duckdb` 格式，還是 Parquet 檔案，還是 DuckLake」——見第 3 節。

---

### 1.2 duckdb/ducklake

- **repo**：https://github.com/duckdb/ducklake
- **star 數量級**：約 2.9k（2,885）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-23T09:13:03Z**
- **archived**：否。授權 MIT。open issues 168。建立於 2025-03-03
- **GitHub Releases**：**沒有任何 release**（我抓 `github.com/duckdb/ducklake/releases`，頁面明示 "There aren't any releases here"）。版本管理走**規格版本**而非 git tag。
- **規格版本（實際看到）**：官方文件寫 **DuckLake 規格 1.0，標記 stable**；DuckDB 文件頁寫 **「DuckLake 1.0 was released in April 2026」**；DuckLake 文件寫 **「DuckLake v1.0 is supported by DuckDB v1.5.2+」**。

**定位**：整合式 data lake + catalog 格式。metadata 存在一個 SQL 資料庫（需支援 transaction 與 primary key，SQL-92 等級），實際資料存 Parquet。

**這是本專案最重要的「可選升級路徑」**。它給你：

- **ACID 交易 + snapshot**：`ducklake_snapshots('my_lake')` 列出所有快照，含 `snapshot_id`、`snapshot_time`、`schema_version`
- **time travel**
- **零重寫的 schema evolution**（見 6.3）
- **CDC 查詢**：`ducklake_table_insertions()` / `ducklake_table_deletions()`，可查兩個 snapshot 之間新增/刪除了哪些列
- **partition 演進**：分區鍵只影響**新寫入**的資料，舊資料維持原分區佈局
- **data inlining**：小批次寫入（預設 <10 列）直接寫進 metadata catalog，不產生小 Parquet 檔

**適用**：需要「重跑安全 + 可回溯 + 增量更新」的 mart 層；事件資料的長期累積。
**不適用**：只想要一次性丟幾個 Parquet 檔給同事看的場景（過度設計）。

**取捨**：多一層 catalog 資料庫（單機可用 DuckDB 檔或 SQLite 當 catalog，不必架 Postgres）。換來的是 `MERGE INTO` + snapshot 帶來的 idempotency，這正好解掉你的第 5 題。**規格 1.0 stable 且 2026 年 4 月才正式發佈，成熟度上仍屬「新」**——建議先在 mart 層試點，raw/staging 維持純 Parquet。

---

### 1.3 dbt-labs/dbt-core

- **repo**：https://github.com/dbt-labs/dbt-core
- **star 數量級**：約 13.5k（13,514）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-25T12:15:00Z**（調研前 1 天）
- **最新正式版**：**v1.12.0**，release 發佈 **2026-07-16**（PyPI 上傳 2026-07-16T13:57:32）
- **archived**：否。授權 Apache-2.0。open issues 1,441
- **額外訊號**：PyPI 上有 **`2.0.0a5`（2026-07-20）**——**dbt-core 2.0 正在 alpha**。這是選型時必須知道的：現在導入 1.12，一年內會面臨 2.0 遷移。
- **Python 3.14**：`requires_python = >=3.10`，classifier **有 3.14**。dbt-core 本身沒問題。

**定位**：SQL transformation 框架。ref/source DAG、incremental materialization、testing、docs 生成。

---

### 1.4 duckdb/dbt-duckdb

- **repo**：https://github.com/duckdb/dbt-duckdb
- **star 數量級**：約 1.3k（1,324）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T20:08:06Z**
- **最新正式版**：**1.10.1**，發佈於 **2026-02-17**（GitHub releases 與 PyPI 一致）
- **前幾版**：1.10.0 @ 2025-11-05、1.9.6 @ 2025-09-08、1.9.5 @ 2025-09-08、1.9.4 @ 2025-06-25
- **archived**：否。授權 Apache-2.0。open issues 87
- **依賴宣告（實際讀 PyPI metadata）**：`dbt-core>=1.8.0`、`duckdb>=1.0.0`（無上限 pin）

**這是本次調研最需要注意的一個落差**：

| | 版本 | 日期 |
|---|---|---|
| dbt-core | 1.12.0 | 2026-07-16 |
| dbt-duckdb | 1.10.1 | 2026-02-17 |

adapter 比 core **落後 2 個 minor 版本、5 個月**。repo 本身有 commit 活動（7/24 有推送），所以**不是死專案**，但**發版節奏明顯慢於 core**。因為 `dbt-core>=1.8.0` 沒有上限 pin，`pip` **會讓你裝上 dbt-core 1.12 + dbt-duckdb 1.10.1 的組合，而這個組合沒有經過 adapter 作者的發版驗證**。

- **Python 3.14**：dbt-duckdb classifier 最高 **3.13**，沒有 3.14。`requires_python` 是 `>=3.10` 沒擋，所以**裝得起來**，但屬於未宣告支援的區域。

**取捨**：見 6.6。簡短版——這個版本落差 + dbt-core 2.0 alpha 在路上，讓「單人分析師現在導入 dbt」的 CP 值明顯下降。

---

### 1.5 TobikoData/sqlmesh

- **repo**：https://github.com/TobikoData/sqlmesh
- **star 數量級**：約 3.2k（3,222）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T14:22:05Z**
- **最新正式版**：**v0.236.1**，發佈 **2026-07-24T14:22:23Z**（當天發版）
- **發版節奏**：0.236.0 @ 2026-07-06、0.235.4 @ 2026-06-11、0.235.3 @ 2026-05-21——**約每 2～4 週一版，非常活躍**
- **archived**：否。授權 Apache-2.0。open issues 263
- **Python 3.14**：`requires_python = >=3.9`，**沒有任何 Python classifier**（無法從 classifier 判斷）。

**定位**：dbt 的替代者，宣稱「backwards compatible with dbt」。核心差異是**內建 column-level lineage 與 virtual data environments**，以及對 incremental model 的 **`start`/`end` 區間語意**——它把「這次要跑哪段時間」變成一等公民，這對你的事件資料回填（backfill）比 dbt 的 `is_incremental()` 巨集乾淨很多。

**適用**：如果最終決定要上 transformation 框架，SQLMesh 對 DuckDB 的支援是**內建 adapter**（不像 dbt 需要外掛 adapter），沒有 1.4 那個版本落差問題。
**不適用**：團隊已有大量 dbt 資產、或需要大量 dbt 生態套件時。

**取捨**：版本號仍在 `0.x`（0.236），API 穩定性承諾低於 dbt 1.x；但發版頻繁、issue 回應快。對單人專案，「adapter 與 core 同一個 repo 發版」這點反而比 dbt 更安全。

---

### 1.6 ibis-project/ibis

- **repo**：https://github.com/ibis-project/ibis
- **star 數量級**：約 6.6k（6,609）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T02:42:12Z**
- **最新正式版**：**12.0.0**，發佈 **2026-02-07**（PyPI 上傳 2026-02-07T14:31:10）
- **發版落差**：距今 **5.5 個月無正式版**。PyPI 上最近的是 `11.0.1.dev133`（2026-02-01）等 dev 版，**dev 版也停在 2 月**。
- **archived**：否。授權 Apache-2.0。open issues 513
- **Python 3.14**：`requires_python = >=3.10`，**沒有任何 Python classifier**。
- **12.0.0 破壞性變更（release note 實際內容）**：drop PySpark <3.5、drop Python 3.9；新增 Materialize、SingleStoreDB backend。

**定位**：Python dataframe API，編譯成各 backend 的 SQL。可以用 Python 寫、底層跑 DuckDB。

**判讀**：repo 有 commit 活動（7/24 推送），但**正式版與 dev 版都停在 2 月**，這個組合值得留意——可能是發版流程調整，也可能是動能下降。我**無法從抓到的資料判定原因**（列入第 8 節）。

**適用**：如果你想「用 Python 寫查詢但不想寫字串 SQL」。
**不適用**：本專案。你的前提已明確「DuckDB + Parquet + **SQL**」，Ibis 是在 SQL 之上再加一層抽象，對單人分析師是**淨增加**心智負擔——你要 debug 的東西從「我的 SQL」變成「我的 Ibis 表達式 → 它生成的 SQL」。**明確不建議採用**（見第 7 節）。

---

### 1.7 pola-rs/polars

- **repo**：https://github.com/pola-rs/polars
- **star 數量級**：約 39.1k（39,101）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-25T13:12:49Z**（調研前 1 天）
- **最新正式版**：**py-1.43.0**，發佈 **2026-07-21**
- **發版節奏**：1.43.0 @ 2026-07-21、1.42.1 @ 2026-06-30、1.42.0 @ 2026-06-24、1.41.2 @ 2026-05-29——**每月 1～2 版，非常活躍**
- **archived**：否。授權 MIT。open issues 2,802

**打包結構已改變（實際查證，影響安裝）**：`polars 1.43.0` 在 PyPI 上**只有一個 `polars-1.43.0-py3-none-any.whl`**（純 Python wrapper）加 sdist。真正的二進位在拆出去的 runtime 套件：

- `polars-runtime-32==1.43.0`（**必要依賴**，預設安裝）→ wheel 為 `polars_runtime_32-1.43.0-cp310-abi3-win_amd64.whl`
- `polars-runtime-64==1.43.0`（extra `rt64`）
- `polars-runtime-compat==1.43.0`（extra `rtcompat`）

**`cp310-abi3` 是關鍵**：abi3 wheel 向前相容，所以**在 Python 3.14 上可直接安裝**，即使 classifier 只寫到 3.13。

**官方安裝文件明確定義三個變體**（我實際抓 docs.pola.rs/user-guide/installation）：

| 安裝指令 | 意義 |
|---|---|
| `pip install polars` | 預設。DataFrame 上限 **2^32 列（約 43 億）** |
| `pip install polars[rt64]` | **Big Index**，上限提升到 2^64。官方原文：「By default, Polars dataframes are limited to 2^32 rows (~4.3 billion)」 |
| `pip install polars[rtcompat]` | 給**沒有 AVX 支援的老 CPU** |

（我在搜尋結果中看到有來源宣稱 `rt64` 是「針對現代 CPU 最佳化」——**這是錯的**，官方文件明確指出 `rt64` 對應 Rust 的 `bigidx` feature，而老 CPU 用的是 `rtcompat`。以官方文件為準。）

**定位**：Rust 寫的 DataFrame 引擎。
**適用**：DuckDB 出來之後、進 statsmodels 之前的中間整形；以及 DuckDB 不擅長的某些 reshape。
**不適用**：取代 DuckDB 當倉儲層。

**取捨**：你的四種資料裡，事件資料**理論上**可能逼近 43 億列（見 6.7 的實際估算，結論是「不會」）。**預設的 `polars` 就夠**，不需要 `rt64`。而且加了 `rt64` 官方明說「Polars will be a bit slower... many data structures are less cache efficient」。

---

### 1.8 dlt-hub/dlt

- **repo**：https://github.com/dlt-hub/dlt
- **star 數量級**：約 5.7k（5,660）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-25T13:53:27Z**（調研前 1 天）
- **最新正式版**：**1.29.1**，發佈 **2026-07-24T11:26:05**
- **發版節奏**：1.29.1 @ 2026-07-24、1.29.0 @ 2026-07-13、1.28.2 @ 2026-07-10、1.28.1 @ 2026-06-19——**每 1～2 週一版，極活躍**
- **archived**：否。授權 Apache-2.0。open issues 435。default branch 是 `devel`
- **Python 3.14**：`requires_python = <3.15,>=3.10`，classifier **有 3.14**。**明確支援你的環境。**

**關鍵發現（實際讀 PyPI requires_dist）**：dlt **有 `ducklake` extra**：

```
duckdb>=1.2.0; extra == "ducklake"
pyarrow>=16.0.0; extra == "ducklake"
```

也就是 **dlt 原生支援 DuckLake 當 destination**，不需要自己寫膠水。同時有 `duckdb` extra（`duckdb>=0.9`）。

**定位**：Python-first 的 EL（extract-load）函式庫，不需要 backend 服務。它幫你處理**增量載入的 state 管理、schema 推導與演進、normalization**。

**適用**：你的**廣告投放成效**與**電商/網站行為**——這兩類幾乎都是打 API（Meta/Google Ads、GA4、電商平台），dlt 的 `dlt.resource` + `write_disposition="merge"` + `primary_key` 直接給你 idempotent 增量載入，這正是第 5 題的答案之一。
**不適用**：手上已經是一批 CSV/Excel 檔的場景——那直接 DuckDB `read_csv` 更快，dlt 是多餘的。

**取捨**：dlt 會**自己管一份 schema 與 state**（存在 destination 的 `_dlt_*` 表），這是它 idempotency 的來源，但也代表**多一個要理解的狀態機**。建議只在 API 來源用它，檔案來源不用。

---

### 1.9 unionai-oss/pandera

- **repo**：https://github.com/unionai-oss/pandera
- **star 數量級**：約 4.4k（4,410）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-18T17:15:57Z**
- **最新正式版**：**0.32.1**，發佈 **2026-06-29T16:01:46**
- **發版節奏**：0.32.1 @ 2026-06-29、0.32.0 @ 2026-06-19、0.31.1 @ 2026-04-15、0.31.0 @ 2026-04-14
- **archived**：否。**授權 MIT**（我實際讀了 PyPI 上的完整授權全文，是標準 MIT，Copyright (c) 2018 Niels Bantilan）
- **Python 3.14**：`requires_python = >=3.10`，**classifier 明確列出 `Programming Language :: Python :: 3.14`**。三個 QA 工具裡**只有 pandera 明確宣告支援 Python 3.14**。
- **extras（實際讀到）**：`pandas`、`polars`、`ibis`、`narwhals`、`pyspark`、`dask`、`modin`、`geopandas`、`strategies`、`mypy`、`fastapi`、`io`、`xarray`、`hypotheses`、`frictionless`

**定位**：以「schema 即 Python class」的方式做 DataFrame 驗證。核心套件本身**不強制依賴 pandas**（pandas 是 extra），足跡很小。

**適用**：本專案的 staging 層與 mart 層出口驗證。
**不適用**：需要「資料品質儀表板 / 跨團隊 data contract 治理」的組織場景。

**取捨**：pandera 驗證的是**已經進到 Python 的 DataFrame**，不是直接對 SQL 表下檢查。對「上億列事件資料」你不會、也不該把整張表拉進 Python 來驗——所以 pandera 的正確用法是**驗 DuckDB 聚合後的結果**，而不是驗原始事件。原始事件層的檢查用純 SQL 斷言（見 6.4）。

---

### 1.10 great-expectations/great_expectations

- **repo**：https://github.com/great-expectations/great_expectations
- **star 數量級**：約 11.7k（11,668）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T15:27:57Z**
- **最新正式版**：**1.19.1**，發佈 **2026-07-24T13:31:41**
- **發版節奏**：1.19.1 @ 2026-07-24、1.19.0 @ 2026-07-13、1.18.2 @ 2026-06-26——**很活躍**
- **archived**：否。授權 Apache-2.0。open issues 33（異常地低，代表 issue 管理積極或被導向 Cloud 支援）
- **default branch**：`develop`

**對本專案的硬阻擋（實際查證，非推測）**：

```
requires_python = <3.14,>=3.10
classifiers 最高 = Programming Language :: Python :: 3.13
```

`requires_python` 的上界 `<3.14` 是 **pip 會強制執行**的。在 **Python 3.14.1 上，`pip install great-expectations` 會直接失敗**（pip 找不到相容版本）。這不是「classifier 沒更新」的軟問題，是硬性排除。

**結論**：GE 專案本身非常健康（一週內發版），但**與你的 Python 3.14.1 環境不相容**。除非你為它另開一個 Python 3.13 的虛擬環境——對單人分析師而言，為了一個驗證工具維護第二套 Python 環境，成本明顯不划算。

**取捨**：GE 的價值在「Data Docs」自動生成的 HTML 驗證報告與跨資料源的 Expectation 複用，適合有資料治理需求的團隊。單人專案用不到那個治理層，卻要付出全部的設定成本（Context / Datasource / Suite / Checkpoint 四層概念）。

---

### 1.11 sodadata/soda-core

- **repo**：https://github.com/sodadata/soda-core
- **star 數量級**：約 2.4k（2,397）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T16:11:43Z**
- **最新正式版**：**4.18.0**，發佈 **2026-07-20T14:48:40**
- **發版節奏**：4.18.0 @ 2026-07-20、4.17.1 @ 2026-07-15、4.17.0 @ 2026-07-08、4.16.0 @ 2026-06-29——**每週一版，極活躍**
- **archived**：否
- **授權（重要，實際讀了 LICENSE 全文）**：GitHub API 回報 `Other (NOASSERTION)`。我抓 `raw.githubusercontent.com/sodadata/soda-core/main/LICENSE`，第一行就是：

  > **Elastic License 2.0**

  且條款明文包含：
  > "You may not provide the software to third parties as a hosted or managed service..."
  > "You may not move, change, disable, or circumvent the **license key functionality** in the software"

  PyPI metadata 的 `license` 欄位寫的是 **`Proprietary`**。

- **Python 支援（實際讀 README）**：
  > "**Python 3.9, 3.10, 3.11, or 3.12** ... **Note:** While Python 3.12 is the highest officially supported version, there are no known issues preventing use of Python 3.13+."

  `requires_python` 是 `>=3.10`（無上界），所以在 3.14 **裝得起來**，但**官方宣告支援上限是 3.12**。

- **DuckDB 支援**：README 明列 "Run checks on PostgreSQL, Snowflake, BigQuery, Databricks, **DuckDB**, and more"
- **安裝方式**：v4 拆成 `soda-{data source}` 套件（例：`pip install soda-postgres`）

**定位**：YAML 定義的 data contract 驗證引擎 + CLI。

**取捨（對單人分析師是決定性的）**：
1. **不是開源軟體**。Elastic License 2.0 是 source-available。個人分析用途幾乎不會踩到限制條款，但**有 license key 機制存在於程式碼中**，且產品設計明顯往 Soda Cloud 導流。
2. Python 官方支援上限 3.12，落後你的環境兩個版本。
3. 每週發版對「一個人維護的專案」是**負擔而非優點**——你不會想每週處理 breaking change。

---

### 1.12 DAGWorks-Inc/hamilton

- **repo**：https://github.com/DAGWorks-Inc/hamilton
- **star 數量級**：約 2.6k（2,552）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-25T10:55:17Z**（調研前 1 天）
- **archived**：否。授權 Apache-2.0。open issues 160
- **重大變更（實際查證）**：專案已**捐給 Apache 基金會並改名**。
  - repo description 已改為 **"Apache Hamilton helps data scientists and engineers define testable, modular, self-documenting dataflows..."**
  - PyPI 舊套件 `sf-hamilton` 的 summary 現在是：**"This package has moved to apache-hamilton. Install apache-hamilton instead."**
  - **新套件 `apache-hamilton` 最新版 1.90.0，上傳 2026-04-25T18:45:17**
  - 舊套件 `sf-hamilton` 也是 1.90.0，上傳 2026-04-25T19:44:29（同日同步發版，仍在維護但已標示遷移）
- **發版節奏（新套件）**：1.90.0 @ 2026-04-25、1.90.0.dev0 @ 2026-03-15、1.89.0 @ 2025-10-12 —— **3 個月無新版；且上一版距離再上一版有 6 個月**。發版節奏明顯偏慢（可能與 Apache 孵化流程有關）。
- **Python 3.14**：`requires_python = <4,>=3.10.1`，classifier **有 3.14**。

**定位**：用「函式名稱即節點名稱」定義 DAG。`def customer_ltv(orders: pd.DataFrame) -> pd.Series:` 這種寫法自動組成依賴圖。

**適用**：Python 側的**建模流程**編排（你的 lm/glm/ANOVA 那套重寫），不是 SQL 側。
**不適用**：SQL transformation 編排（那是 dbt/SQLMesh 的地盤）。

**取捨**：概念優雅、侵入性極低（就是普通 Python 函式 + type hint）。但**發版節奏慢 + 正在經歷 Apache 改名遷移**，現在導入要承受套件改名的過渡期噪音。對單人專案，一個 200 行的 Python runner 就能取代它的核心價值。

---

### 1.13 kedro-org/kedro

- **repo**：https://github.com/kedro-org/kedro
- **star 數量級**：約 10.9k（10,931）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-24T23:21:05Z**
- **最新正式版**：**1.5.0**，發佈 **2026-06-29T14:53:18**
- **發版節奏**：1.5.0 @ 2026-06-29、1.4.0 @ 2026-05-22、1.3.1 @ 2026-04-07、1.3.0 @ 2026-03-31、1.2.0 @ 2026-01-29 —— **每 1～2 個月一版，穩定**
- **archived**：否。授權 Apache-2.0。open issues 159。**由 LF AI & Data Foundation 託管**（基金會治理，不依賴單一公司）
- **Python 3.14**：`requires_python = >=3.10`，classifier **有 3.14**

**定位**：完整的資料科學專案框架——專案模板、Data Catalog（YAML 宣告資料集）、Pipeline 抽象、節點依賴自動解析。

**適用**：多人團隊、需要專案結構標準化、需要把 notebook 轉成 production pipeline 的場景。
**不適用**：**本專案**。Kedro 的價值在「強制專案結構」，而強制結構的收益隨團隊人數增長；一個人用，它的 `conf/base/catalog.yml` + `src/pipelines/` + `settings.py` 這套約定會變成純開銷。

**取捨**：Kedro 的 Data Catalog 概念（YAML 宣告 dataset 與其 I/O）其實很適合你的四種資料源。但你可以**借用這個概念寫 30 行 YAML + 一個 loader**，不必引入整個框架。

---

### 1.14 apache/iceberg

- **repo**：https://github.com/apache/iceberg
- **star 數量級**：約 9.1k（9,079）
- **實際看到的最後活躍時間**：`pushed_at` = **2026-07-25T02:27:26Z**
- **archived**：否。授權 Apache-2.0。open issues 851
- **Python 實作 `pyiceberg`（實際查證）**：最新 **0.11.1，上傳 2026-03-03T00:09:49**；前版 0.11.0 @ 2026-02-10
  - `requires_python = <4.0.0,>=3.10.0`
  - **wheel 只到 `cp313`，沒有 cp314**。classifier 最高 3.13。
  - → **在 Python 3.14.1 上，pyiceberg 沒有預編譯 wheel**（會嘗試從 source 編譯，Windows 上大機率失敗）

**DuckDB 端的 Iceberg 支援（實際讀 DuckDB 官方文件，這段是決定性的）**：

> "Individual tables are read directly from storage, by pointing at a table's metadata. **This requires no catalog and is read-only.**"
> "Catalog-managed tables are accessed by attaching an Iceberg REST catalog. **This unlocks the full feature set, including writing.**"

換句話說：**在單機、沒有 REST catalog 的情況下，DuckDB 對 Iceberg 是唯讀的**。要寫入 Iceberg，你必須跑一個 Iceberg REST catalog 服務（Polaris、Lakekeeper、AWS Glue、S3 Tables…）。

**適用**：與外部 Iceberg 生態（Spark、Snowflake、雲端 lakehouse）交換資料時**讀取**。
**不適用**：**本專案的寫入路徑**。單機分析師架一個 REST catalog 服務，成本與 DuckLake 相比完全不成比例。

**取捨**：Iceberg 是業界標準、生態最大；DuckLake 是新格式、生態只有 DuckDB。但對「單機 + Windows + 一個人」，DuckLake 用一個本機檔案當 catalog 就能跑，Iceberg 要一個服務。**選 DuckLake。**（若未來要與公司的 Iceberg lakehouse 對接，DuckDB 的 `iceberg_scan` 讀取路徑隨時可用，不衝突。）

---

## 2. 總結比較表

「最後活躍」欄位一律是**我實際抓到的時間戳**。

| 工具 | repo | star | 最新版 / 日期（實際看到） | repo pushed_at | archived | Py3.14 | 本專案採用 |
|---|---|---|---|---|---|---|---|
| **DuckDB** | duckdb/duckdb | ~39.7k | v1.5.5 / 2026-07-22 | 2026-07-24 | 否 | **wheel 有 cp314** | **核心** |
| **DuckLake** | duckdb/ducklake | ~2.9k | 規格 1.0（無 git release）/ 2026-04 | 2026-07-23 | 否 | 隨 DuckDB | **mart 層採用** |
| **dlt** | dlt-hub/dlt | ~5.7k | 1.29.1 / 2026-07-24 | 2026-07-25 | 否 | **classifier 有** | **API 來源採用** |
| **pandera** | unionai-oss/pandera | ~4.4k | 0.32.1 / 2026-06-29 | 2026-07-18 | 否 | **classifier 有** | **採用** |
| **Polars** | pola-rs/polars | ~39.1k | 1.43.0 / 2026-07-21 | 2026-07-25 | 否 | abi3 wheel，可 | **輔助採用** |
| SQLMesh | TobikoData/sqlmesh | ~3.2k | 0.236.1 / 2026-07-24 | 2026-07-24 | 否 | 未宣告 | **備選**（跨過臨界點才上） |
| dbt-core | dbt-labs/dbt-core | ~13.5k | 1.12.0 / 2026-07-16（2.0 已 alpha） | 2026-07-25 | 否 | classifier 有 | 不採用 |
| dbt-duckdb | duckdb/dbt-duckdb | ~1.3k | **1.10.1 / 2026-02-17（落後 core 5 個月）** | 2026-07-24 | 否 | 無 3.14 classifier | 不採用 |
| Ibis | ibis-project/ibis | ~6.6k | **12.0.0 / 2026-02-07（5.5 個月無新版）** | 2026-07-24 | 否 | 未宣告 | 不採用 |
| Great Expectations | great-expectations/great_expectations | ~11.7k | 1.19.1 / 2026-07-24 | 2026-07-24 | 否 | **`requires_python <3.14` 硬擋** | **不可用** |
| Soda Core | sodadata/soda-core | ~2.4k | 4.18.0 / 2026-07-20 | 2026-07-24 | 否 | 官方上限 3.12 | 不採用（**Elastic License 2.0**） |
| Hamilton | DAGWorks-Inc/hamilton | ~2.6k | apache-hamilton 1.90.0 / 2026-04-25 | 2026-07-25 | 否（**已改名 Apache Hamilton**） | classifier 有 | 不採用 |
| Kedro | kedro-org/kedro | ~10.9k | 1.5.0 / 2026-06-29 | 2026-07-24 | 否 | classifier 有 | 不採用 |
| Iceberg | apache/iceberg | ~9.1k | pyiceberg 0.11.1 / 2026-03-03 | 2026-07-25 | 否 | **pyiceberg 無 cp314 wheel** | 僅唯讀備用 |

---

## 3. 問題 1：medallion 在檔案系統上怎麼落地？

### 3.1 頂層結構

```
E:\Projects\行銷分析\
├── 00_source_archive\          # 原始檔的不可變存檔（含本調研）
├── 10_raw\                     # bronze：原樣落地，不改欄位、不改型別
├── 20_staging\                 # silver：清洗、正規化、型別統一
├── 30_mart\                    # gold：可直接餵給分析/儀表板
├── 40_output\                  # 交付物（HTML / 儀表板 / 投影片 / Excel）
├── warehouse\
│   ├── marketing.ducklake      # DuckLake catalog（mart 層）
│   └── marketing.duckdb        # 開發用暫存 DB（可隨時刪）
├── sql\                        # 你的 SQL 檔（見第 8 節的 runner）
└── .venv\
```

**分層原則**（這是 medallion 的實質，不是資料夾長相）：

| 層 | 允許做的事 | 禁止做的事 | 格式 |
|---|---|---|---|
| `10_raw` | 型別一律最寬鬆（VARCHAR）、加 `_ingested_at` / `_source_file` | 任何商業邏輯、任何 JOIN、任何過濾 | Parquet（zstd） |
| `20_staging` | 型別轉換、欄位改名成統一命名、去重、時區正規化 | 跨資料源 JOIN、聚合 | Parquet（zstd） |
| `30_mart` | 跨源 JOIN、聚合、指標計算、SCD | 再回頭改 raw | **DuckLake** |

**為什麼 raw/staging 用純 Parquet、mart 用 DuckLake**：raw 與 staging 是「重跑就整段重建」的，不需要 snapshot 與交易；mart 是「增量累積、會被下游引用、重跑不能重複灌」的，正好需要 DuckLake 的 `MERGE INTO` + snapshot。

### 3.2 資料夾與 partition 命名

DuckDB 的 Hive partition 慣例（官方文件實例）是 `key=value` 的目錄結構：

```
10_raw/
├── source=ga4_events/
│   └── event_date=2026-07-01/
│       └── data_0.parquet
├── source=meta_ads/
│   └── report_date=2026-07-01/
│       └── data_0.parquet
├── source=crm_orders/
│   └── ingest_month=2026-07/
│       └── data_0.parquet
└── source=pos_txn/
    └── biz_date=2026-07-01/
        └── data_0.parquet
```

**命名規約（建議你直接採用並寫進 CLAUDE.md）**：

1. **一律小寫、底線分隔**。理由見第 8 節——Windows 檔案系統大小寫不敏感，但 Parquet 內的欄位名大小寫敏感，混用必踩雷。
2. **partition key 一律用純 ASCII**。**中文絕對不要出現在資料夾名或 partition value**（例如不要 `門市=台北信義店`）。改用代碼 `store_id=T001`，中文名放在維度表裡 JOIN 回來。
3. **日期 partition 用 `YYYY-MM-DD` 字串或分成 `year=/month=/day=`**。DuckDB 對 `DATE`、`TIMESTAMP`、`BIGINT` 三種型別會**自動推斷 hive_types**（官方文件明述），其他型別要手動指定：
   ```sql
   FROM read_parquet('10_raw/source=ga4_events/**/*.parquet',
                     hive_partitioning = true,
                     hive_types = {'event_date': DATE});
   ```
4. **欄位名不要有斜線**。官方文件特別提醒斜線要用 `url_encode` 處理——直接避免。

### 3.3 分區粒度：DuckDB 官方的硬性建議

官方 `partitioned_writes` 頁面有一條明確的 Bestpractice：

> **"Writing data into many small partitions is expensive. It is generally recommended to have at least 100 MB of data per partition."**

還有兩個實作細節：

- **「Currently, one file is written per thread to each directory.」** → 你有 N 個 thread，每個 partition 目錄就會產生 N 個檔。8 核心 × 365 天 partition = 2,920 個檔案，這在 Windows 上會很痛。
- `partitioned_write_max_open_files` **預設 100**。超過就會 flush。分區數多時要調高（代價是記憶體）。

**對照你的四種資料，直接給粒度建議**：

| 資料型態 | 年資料量級 | partition 粒度 | 理由 |
|---|---|---|---|
| CRM 交易（百萬列） | ~200 MB | **不分區**，單一 Parquet | 全年資料還不到 100MB × 2，分了只會產生小檔 |
| 廣告投放成效 | ~50 MB | **不分區** | 通常是日彙總，量極小 |
| 零售 POS | 千萬列 / ~2 GB | **`year=/month=`** | 每月約 170MB，剛好過 100MB 門檻 |
| 網站行為事件（上億列） | ~20-50 GB | **`year=/month=/day=`** | 每日約 60-140MB，符合門檻；且查詢幾乎都帶日期範圍 |

**不要**對事件資料用 `hour=` 分區——每小時 3-6MB，遠低於 100MB 建議值。

---

## 4. 問題 2：事件型（上億列）與交易型（百萬列）如何共存？

### 4.1 核心答案：它們不該用同一種儲存策略

「同一個 DuckDB 專案」不代表「同一種物理佈局」。正確做法是**一個 DuckDB session，ATTACH 多個來源**：

```sql
-- 事件資料：留在 Parquet，用 VIEW 暴露，永遠不進 DuckDB 原生表
CREATE OR REPLACE VIEW ev_events AS
SELECT * FROM read_parquet('10_raw/source=ga4_events/**/*.parquet',
                           hive_partitioning = true);

-- 交易資料：量小，直接進 DuckLake 成為實體表
ATTACH 'ducklake:warehouse/marketing.ducklake' AS mart
       (DATA_PATH 'warehouse/mart_data/');

-- 查詢時自由跨越
SELECT c.segment, count(*) AS sessions
FROM ev_events e
JOIN mart.dim_customer c ON e.user_id = c.user_id
WHERE e.event_date BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
GROUP BY 1;
```

**關鍵洞察**：DuckDB 對 Parquet 的 filter pushdown 讓「事件資料留在檔案裡」幾乎沒有代價。官方文件明確說明 partition key 上的 filter 會自動下推、**完全跳過不需要的檔案**。把上億列事件灌進 DuckDB 原生表反而失去這個好處，還讓 `.duckdb` 檔膨脹到難以備份。

### 4.2 何時該 partition？

用**查詢模式**決定，不是用資料量決定：

| 條件 | 決策 |
|---|---|
| 幾乎每次查詢都帶同一個欄位的範圍條件（通常是日期） | **partition 該欄位** |
| 單一分區能到 100 MB 以上 | 可以分 |
| 單一分區 <100 MB | **不要分**，用單檔 + row group 內的 min/max 統計就夠 |
| 資料總量 < 幾百 MB | **完全不要分區** |

DuckDB 對**未分區**的 Parquet 仍會用 row group 統計做 pruning——分區不是唯一的加速手段，只是最粗的那一層。

### 4.3 何時該用 DuckLake / Iceberg？

| 情境 | 選擇 | 理由（實際查證） |
|---|---|---|
| 一次性分析、資料不會再變 | **純 Parquet** | 零額外概念 |
| raw / staging 層（重跑即全量重建） | **純 Parquet** | 不需要交易 |
| mart 層，需要增量更新且重跑要 idempotent | **DuckLake** | `MERGE INTO` + snapshot |
| 需要 time travel / 稽核「上週的數字為什麼不一樣」 | **DuckLake** | `ducklake_snapshots()`、`ducklake_table_insertions/deletions()` |
| 資料放在網路磁碟機 / NAS，且要讀寫 | **DuckLake（必須）** | 見下方官方警告 |
| 要與公司的 Spark/Snowflake lakehouse 交換 | **Iceberg（唯讀）** | DuckDB 無 catalog 時對 Iceberg 唯讀 |
| 單機、要寫入 Iceberg | **不要做** | 需要架 REST catalog 服務 |

**DuckDB 官方對 NAS 的警告（原文，這條對 Windows 使用者特別重要）**：

> "it is recommended to **avoid using DuckDB's native database format in read-write mode on network-attached storage (NAS)**. These setups include NFS, network drives such as SMB and Samba... running read-write workloads on network-attached storage can result in **slow and unpredictable performance, as well as spurious errors**... **Instead of using DuckDB's native database format, consider using the DuckLake lakehouse format.**"

如果你的 `E:\` 是網路磁碟機、或專案在 OneDrive / Google Drive 同步資料夾裡——**`.duckdb` 原生格式會出問題，必須改用 DuckLake（或至少把 `.duckdb` 放在本機 SSD）**。

### 4.4 事件資料的小檔問題與 DuckLake data inlining

如果事件是**每小時小批次**進來，會產生大量小 Parquet 檔。DuckLake 有兩個對應機制（實際查證）：

1. **data inlining**：預設開啟，`data_inlining_row_limit` **預設 10 列**。少於此列數的 insert/delete 直接寫進 metadata catalog，不產生 Parquet 檔。可調：
   ```sql
   SET ducklake_default_data_inlining_row_limit = 1000;
   ```
2. **merge_adjacent_files**：官方 Recommended Maintenance 明述——
   > "When snapshots write small batches of data at a time and data inlining is not used **small Parquet files will be written to storage. It is recommended to merge these Parquet files using the `merge_adjacent_files` function.**"

   以及：
   > "**DuckLake also never deletes old data files.** As old data remains accessible through time travel. Even when a table is dropped, the data files associated with that table are not deleted."

   → **這是個會咬人的點**：DuckLake 的資料目錄會單調成長。你必須定期 `expire_snapshots` + cleanup，否則磁碟會被吃光。官方建議用 `CHECKPOINT` 統一觸發這些維護動作。

---

## 5. 問題 3：schema 演進怎麼處理？

分兩種情況，機制完全不同。

### 5.1 純 Parquet 層（raw / staging）：`union_by_name`

DuckDB 讀多檔時**預設按欄位位置（by position）合併**。只要有一個檔多了一欄，位置就全錯，或直接報錯。

解法是官方的 `union_by_name`（實際文件原文）：

> "If you are processing multiple files that have different schemas, perhaps because **columns have been added or renamed**, it might be desirable to unify the columns of different files by name instead... When specifying the `union_by_name` option, the columns are correctly unified, and **any missing values are set to NULL**."

```sql
-- raw 層讀取一律加這個，不要省
SELECT * FROM read_parquet('10_raw/source=ga4_events/**/*.parquet',
                           union_by_name = true,
                           hive_partitioning = true);
```

**代價**：`union_by_name` 需要讀取所有檔案的 metadata 才能建立聯集 schema，檔案很多時**規劃階段會變慢**。這是另一個「不要製造太多小檔」的理由。

**三種變更在純 Parquet 層的處理**：

| 變更 | 處理方式 |
|---|---|
| **新增欄位** | `union_by_name = true`，舊檔該欄自動為 NULL。**零成本**。 |
| **改名欄位** | `union_by_name` 會把它當成**兩個不同欄位**（舊檔有 A、新檔有 B，結果是 A 和 B 兩欄都在，各自一半 NULL）。必須在 staging 層用 `COALESCE(new_name, old_name) AS new_name` 手動縫合。 |
| **型別變更** | DuckDB 會嘗試隱式轉換，失敗則報錯。**建議 raw 層一律存 VARCHAR**，型別轉換全部延到 staging 層做，這樣上游型別怎麼變都不會炸掉 raw。 |

### 5.2 DuckLake 層（mart）：真正的 schema evolution

DuckLake 的處理明顯優雅，官方原文：

> "DuckLake supports the evolution of the schemas of tables **without requiring any data files to be rewritten**."

支援的操作（全部是標準 `ALTER TABLE`）：

```sql
ALTER TABLE tbl ADD COLUMN new_col INTEGER;                    -- 預設 NULL
ALTER TABLE tbl ADD COLUMN new_col VARCHAR DEFAULT 'my_default';
ALTER TABLE tbl DROP COLUMN old_col;
ALTER TABLE tbl RENAME old_col TO new_col;                     -- 真正的改名
ALTER TABLE tbl RENAME TO tbl_new_name;
ALTER TABLE tbl ALTER col1 SET TYPE BIGINT;                    -- 型別提升
-- struct 內的欄位也支援
ALTER TABLE tbl ADD COLUMN nested_col.new_field INTEGER;
```

**運作原理（field identifiers）**：每個欄位有一個 `column_id`，寫進 Parquet 的 `field_id` 欄位。讀取時做 field id remapping：

- data file 有、但 schema 沒有的 field_id → **忽略**
- schema 有、但 data file 沒有的 field_id → **用 `initial_default` 填補**
- 型別不符 → **cast 到 schema 的型別**

這就是為什麼改名不需要重寫檔案：改的是 catalog 裡的名字，`column_id` 沒變。

**型別變更的限制（完整表格，官方原文「Only type promotions are supported. Type promotions must be lossless.」）**：

| Source | 可提升為 |
|---|---|
| int8 | int16, int32, int64 |
| int16 | int32, int64 |
| int32 | int64 |
| uint8 | uint16, uint32, uint64 |
| uint16 | uint32, uint64 |
| uint32 | uint64 |
| float32 | float64 |

**注意這個表沒有的東西**：`VARCHAR → INTEGER`、`INTEGER → VARCHAR`、`float → int`、`DATE → TIMESTAMP` 全都**不支援**。遇到這類變更，只能新增一個欄位、回填、再 drop 舊欄。

### 5.3 實務建議

**在 `sql/` 下維護一個 `_schema_changes.sql`**，所有 `ALTER TABLE` 按時間順序 append，永不修改既有行。這是窮人版 migration，但對單人專案完全夠用，而且比 dbt 的 schema 管理更透明。

---

## 6. 問題 4：資料品質驗證放哪一層、用什麼工具？

### 6.1 分層放置

| 層 | 檢查什麼 | 用什麼 | 失敗時 |
|---|---|---|---|
| **載入時（raw 寫入前）** | 檔案能不能讀、編碼對不對、列數是否為 0 | Python `try/except` + 列數斷言 | **中止**，不寫 raw |
| **raw → staging** | 主鍵唯一性、必填非空、日期範圍合理、金額非負、enum 值在白名單內 | **純 SQL 斷言**（不是任何框架） | **中止**，不寫 staging |
| **staging → mart** | 跨源一致性（例：POS 總額 vs CRM 總額差異 <1%）、JOIN 後列數不應暴增 | **純 SQL 斷言** | 警告 or 中止（看檢查性質） |
| **mart → 交付物** | 最終 DataFrame 的 schema 與型別 | **pandera** | **中止** |

### 6.2 為什麼「純 SQL 斷言」是主力

因為**你的資料在 DuckDB 裡，不在 Python 裡**。上億列的事件資料，任何要求「把資料拉進 Python DataFrame 才能驗」的工具都是錯的架構。

一個 20 行的 SQL 斷言 helper 就能覆蓋 90% 需求：

```python
# tools/assert_sql.py
def check(con, name: str, sql: str, expect_zero: bool = True):
    """sql 應回傳「違規列」；回傳 0 列 = 通過。"""
    n = con.execute(f"SELECT count(*) FROM ({sql})").fetchone()[0]
    if expect_zero and n > 0:
        sample = con.execute(f"SELECT * FROM ({sql}) LIMIT 5").fetchdf()
        raise AssertionError(f"[{name}] 有 {n} 列違規\n{sample}")
    print(f"  OK  {name}")
```

搭配放在 `sql/checks/` 的檢查檔：

```sql
-- sql/checks/stg_orders__pk_unique.sql
SELECT order_id, count(*) AS n
FROM stg_orders GROUP BY 1 HAVING count(*) > 1
```

```sql
-- sql/checks/stg_orders__amount_nonneg.sql
SELECT * FROM stg_orders WHERE amount < 0
```

**這個做法的優勢**：檢查邏輯是 SQL，跟你的 transformation 同語言；違規列可以直接看；沒有任何框架版本相依。

### 6.3 pandera vs Great Expectations vs Soda：單人分析師的實際取捨

**先講硬性事實（全部實際查證）**：

| | pandera 0.32.1 | Great Expectations 1.19.1 | Soda Core 4.18.0 |
|---|---|---|---|
| 授權 | **MIT** | Apache-2.0 | **Elastic License 2.0（source-available，非開源，含 license key 機制）** |
| `requires_python` | `>=3.10` | **`<3.14,>=3.10`** | `>=3.10` |
| 官方宣告 Python 上限 | **classifier 有 3.14** | classifier 3.13 | **README 寫 3.12** |
| **在你的 Python 3.14.1 上** | **可用** | **`pip install` 直接失敗** | 裝得起來但超出官方支援 |
| 驗證對象 | Python DataFrame | DataFrame + SQL 資料源 | SQL 資料源（YAML 定義） |
| 概念層數 | 1（Schema class） | 4（Context/Datasource/Suite/Checkpoint） | 2（config + contract YAML） |
| 最近發版 | 2026-06-29 | 2026-07-24 | 2026-07-20 |

**取捨判斷**：

**Great Expectations — 直接出局，理由不是品質而是相容性。** `requires_python = <3.14` 是 pip 強制執行的上界，你的 3.14.1 裝不上。專案本身很健康（一週內發版、open issues 只有 33），但要用它就得為它單獨維護一個 Python 3.13 環境。**單人分析師為了一個驗證工具維護第二套 Python 環境，不划算。** 而且 GE 的核心賣點——Data Docs 治理報告、跨團隊 Expectation 複用——對一個人的專案沒有價值，你卻要付全部的四層概念設定成本。

**Soda Core — 出局，理由是授權與定位。** 三個問題疊加：(1) **Elastic License 2.0，PyPI 上 license 欄位寫 `Proprietary`**，程式碼裡明文有 license key 機制且條款禁止規避；(2) README 明寫官方支援上限 Python 3.12，落後你兩個版本；(3) 每週發版節奏——對一個人維護的專案是負擔而非優點。它的 YAML contract 語法確實優雅，且**原生支援 DuckDB**，但整體產品重心明顯在 Soda Cloud 導流。對於「一個人、本機、繁體中文行銷分析」，這些治理功能是純開銷。

**pandera — 採用，但只用在正確的位置。** MIT 授權乾淨、**唯一明確宣告支援 Python 3.14**、核心不強制依賴 pandas（pandas 是 extra，足跡小）、概念只有一層（一個 Schema class）。

但要清楚它的**邊界**：pandera 驗的是**已經在記憶體裡的 DataFrame**。你**不會、也不該**把上億列事件拉進 Python 來驗。所以：

- **不要**用 pandera 驗 raw / staging 的事件資料 → 用 SQL 斷言
- **要**用 pandera 驗「送進統計模型前的 DataFrame」與「輸出到 Excel 前的 DataFrame」

```python
import pandera.pandas as pa

class MartCustomerMonthly(pa.DataFrameModel):
    customer_id: str = pa.Field(nullable=False)
    month: pa.typing.Series[pa.DateTime]
    revenue: float = pa.Field(ge=0)
    orders: int = pa.Field(ge=0)
    channel: str = pa.Field(isin=["organic", "paid_search", "social", "email", "direct"])

    class Config:
        strict = True          # 多餘欄位 = 失敗
        unique = ["customer_id", "month"]

df = MartCustomerMonthly.validate(con.execute(SQL).fetchdf())
```

這一層 pandera 剛好接住你的建模流程——`lm/glm/ANOVA` 對輸入的型別與 NA 極度敏感，在進 statsmodels 前擋一道，能省掉大量詭異的 debug。

### 6.4 結論

**主力是純 SQL 斷言（覆蓋 90%），出口用 pandera（覆蓋建模與交付）。GE 與 Soda 都不採用。**

---

## 7. 問題 5：增量更新與 idempotency

「重跑不會重複灌資料」有三個層次的解法，按資料層選用。

### 7.1 層次一：raw / staging —— 全量重建（最簡單、最可靠）

分區覆寫。DuckDB 的 `COPY ... PARTITION_BY` 有三種覆寫語意（官方文件實際內容）：

| 選項 | 行為 |
|---|---|
| 預設（不加） | **不允許覆寫既有目錄**，會報錯 |
| `OVERWRITE` / `OVERWRITE_OR_IGNORE` | **在本機檔案系統上會移除既有目錄**。官方註明「On remote file systems, overwriting is not supported」 |
| `APPEND` | 追加。行為等同 `OVERWRITE_OR_IGNORE, FILENAME_PATTERN '{uuid}'`，但**額外檢查檔案是否已存在，若碰撞會重新產生 UUID** |

**idempotent 的寫法（重跑安全）**：

```sql
-- 只重建指定日期範圍的分區，重跑結果完全相同
COPY (
  SELECT *, CAST(event_ts AS DATE) AS event_date
  FROM read_csv('00_source_archive/local/ga4_2026-07-*.csv',
                encoding = 'utf-8', union_by_name = true)
  WHERE CAST(event_ts AS DATE) BETWEEN DATE '2026-07-01' AND DATE '2026-07-31'
)
TO '10_raw/source=ga4_events'
(FORMAT parquet, COMPRESSION zstd,
 PARTITION_BY (event_date), OVERWRITE_OR_IGNORE);
```

**關鍵**：`OVERWRITE_OR_IGNORE` + 明確的日期範圍 = 重跑會**取代**該範圍的分區，不會累加。**不要用 `APPEND` 做日常載入**——它就是為了累加設計的，重跑必然重複。

**陷阱**：`OVERWRITE` 會**刪除整個目錄**。如果你的 `PARTITION_BY` 只有 `event_date`，而你寫入時只算了 7 月的資料，`OVERWRITE`（非 `_OR_IGNORE`）可能連 6 月的分區一起清掉。**一律用 `OVERWRITE_OR_IGNORE`，它只覆寫實際產生的分區。**

### 7.2 層次二：mart —— `MERGE INTO`（DuckLake）

DuckLake **不支援 primary key**，但支援 `MERGE INTO`（官方原文：「DuckLake, on the other hand, does not support primary keys. However, the `MERGE INTO` syntax provides the same upserting functionality.」）：

```sql
MERGE INTO mart.fct_orders AS t
USING (
    SELECT * FROM stg_orders
    WHERE order_date >= DATE '2026-07-01'
) AS s
ON (t.order_id = s.order_id)
WHEN MATCHED THEN UPDATE
WHEN NOT MATCHED THEN INSERT;
```

**這就是 idempotency 的核心**：跑一次跟跑一百次結果相同，因為 `order_id` 相同的列會被 UPDATE 而非再 INSERT。

也支援只更新部分欄位、與 delete set：

```sql
-- 只更新變動欄位
MERGE INTO mart.fct_orders AS t
USING changed_amounts AS s ON (t.order_id = s.order_id)
WHEN MATCHED THEN UPDATE SET amount = s.amount;

-- 處理刪除
MERGE INTO mart.fct_orders AS t
USING deleted_ids AS s ON (t.order_id = s.order_id)
WHEN MATCHED THEN DELETE;
```

### 7.3 層次三：API 來源 —— dlt 的 merge write disposition

對廣告投放與網站行為這類**打 API** 的來源，dlt 幫你管 incremental state：

```python
import dlt

@dlt.resource(
    write_disposition="merge",
    primary_key="ad_id",
    columns={"report_date": {"data_type": "date"}},
)
def meta_ads_insights(
    start=dlt.sources.incremental("report_date", initial_value="2026-01-01")
):
    yield from fetch_meta_insights(since=start.last_value)

pipeline = dlt.pipeline(
    pipeline_name="meta_ads",
    destination="duckdb",           # 或 "ducklake"（dlt 有 ducklake extra）
    dataset_name="raw_meta_ads",
)
pipeline.run(meta_ads_insights)
```

dlt 把「上次跑到哪」存在 destination 的 `_dlt_*` 表，重跑時自動接續；`write_disposition="merge"` + `primary_key` 保證不重複。

### 7.4 統一的 idempotency 檢查

不管用哪個層次，**在 runner 裡加一個「跑兩次結果應相同」的自我檢查**：

```python
before = con.execute("SELECT count(*), sum(amount) FROM mart.fct_orders").fetchone()
run_pipeline()          # 再跑一次同樣的區間
after  = con.execute("SELECT count(*), sum(amount) FROM mart.fct_orders").fetchone()
assert before == after, f"非 idempotent！{before} -> {after}"
```

這比任何框架的保證都實在。**第一次建 pipeline 時就跑這個檢查**，之後可以關掉。

### 7.5 DuckLake 的額外保障

因為每次寫入都產生 snapshot，出錯時可以**看見究竟改了什麼**：

```sql
FROM ducklake_snapshots('mart');
-- 看 snapshot 3 到 4 之間，fct_orders 新增了哪些列
FROM ducklake_table_insertions('mart', 'main', 'fct_orders', 3, 4);
FROM ducklake_table_deletions('mart', 'main', 'fct_orders', 3, 4);
```

「重跑之後數字變了，但我不知道哪裡變了」是這類專案最常見的痛點，這組函式直接解掉。

---

## 8. 問題 6：純 SQL + runner vs dbt-duckdb，臨界點在哪？

### 8.1 先講結論

**你現在應該用「純 SQL 檔 + 一支 runner」。** 而且以本次查證的證據，**如果未來要升級，應該跳過 dbt-duckdb，直接評估 SQLMesh。**

### 8.2 為什麼現在不用 dbt-duckdb（基於實際查證，不是偏好）

| 證據 | 意涵 |
|---|---|
| dbt-duckdb 最新版 **1.10.1 / 2026-02-17**；dbt-core 最新版 **1.12.0 / 2026-07-16** | adapter 落後 core **2 個 minor、5 個月** |
| dbt-duckdb 宣告 `dbt-core>=1.8.0`（**無上限 pin**） | pip 會裝出 **未經 adapter 驗證的組合**，而且不會警告你 |
| PyPI 上有 **dbt-core `2.0.0a5`（2026-07-20）** | dbt 2.0 已進 alpha，一年內要面對大版本遷移 |
| dbt-duckdb classifier 無 3.14 | 你的 Python 3.14.1 屬未宣告支援區 |

dbt-duckdb **不是死專案**（repo 7/24 還有推送），但「adapter 由與 core 不同的團隊、以不同節奏發版」這個結構性風險，在單人專案上會直接變成你的維護負擔。

### 8.3 純 SQL + runner 的實作

一支不到 100 行的 runner 就能覆蓋 dbt 80% 的日常價值：

```python
# tools/run_sql.py
import re, pathlib, duckdb, time

SQL_DIR = pathlib.Path("sql/models")

def dep_order(files):
    """從 SQL 裡的 -- depends_on: xxx 註解建立執行順序。"""
    nodes = {f.stem: f for f in files}
    deps = {}
    for name, f in nodes.items():
        txt = f.read_text(encoding="utf-8")
        deps[name] = [d for d in re.findall(r"--\s*depends_on:\s*(\w+)", txt)
                      if d in nodes]
    done, order = set(), []
    while len(done) < len(nodes):
        progress = False
        for name in nodes:
            if name not in done and all(d in done for d in deps[name]):
                order.append(nodes[name]); done.add(name); progress = True
        if not progress:
            raise RuntimeError(f"循環相依：{set(nodes) - done}")
    return order

def main():
    con = duckdb.connect("warehouse/marketing.duckdb")
    con.execute("SET threads = 6")
    con.execute("SET memory_limit = '20GB'")
    con.execute("SET temp_directory = 'E:/duckdb_tmp'")
    con.execute("SET preserve_insertion_order = false")

    for f in dep_order(sorted(SQL_DIR.glob("*.sql"))):
        t0 = time.time()
        con.execute(f.read_text(encoding="utf-8"))
        print(f"  {f.stem:40s} {time.time()-t0:6.2f}s")

if __name__ == "__main__":
    main()
```

每個 model 檔自己宣告物化方式：

```sql
-- sql/models/mart_customer_monthly.sql
-- depends_on: stg_orders
-- depends_on: stg_customers
CREATE OR REPLACE TABLE mart_customer_monthly AS
SELECT ...
```

**你放棄了什麼**（誠實列出）：`ref()` 的自動 lineage、`dbt docs` 的互動式 DAG、內建 test 語法、macro/Jinja 重用、package 生態、snapshot（SCD Type 2）。

**你換到什麼**：零框架版本相依、SQL 檔就是純 SQL（可直接貼進 DuckDB CLI 執行）、debug 路徑短、不用學 Jinja。

### 8.4 臨界點：什麼時候該升級？

**不要用「model 數量」當唯一指標**（常見的「50 個 model」說法太粗）。用下面這五個訊號，**任兩個成立**就該升級：

1. **你開始手動維護執行順序，而且改一個 model 要想 10 秒才知道會影響誰。**（lineage 認知超載）
2. **同一段 SQL 邏輯（如日期維度、渠道分類 CASE WHEN）複製超過 3 次。**（需要 macro）
3. **你需要「只重跑 7 月」而現在的做法是手動改 SQL 裡的日期字串。**（需要參數化 incremental）
4. **有第二個人要碰這些 SQL。**（需要共同約定與文件）
5. **你開始需要「先在測試環境驗證再套到正式」。**（需要 virtual environment）

**訊號 3 和 5 特別指向 SQLMesh 而非 dbt**——SQLMesh 把 incremental model 的 `start`/`end` 時間區間做成一等公民，而 dbt 要你自己在 `is_incremental()` 巨集裡拼 WHERE 條件。對你的事件資料回填場景，這個差異很大。

### 8.5 若真的要升級，選 SQLMesh 的理由

| | dbt + dbt-duckdb | SQLMesh |
|---|---|---|
| DuckDB 支援 | **外掛 adapter，獨立發版（落後 5 個月）** | **內建，與核心同 repo 同版發布** |
| 最近發版 | core 2026-07-16 / adapter **2026-02-17** | **2026-07-24（同時）** |
| 版本穩定性承諾 | 1.x（但 2.0 alpha 已出） | 0.x（API 承諾較低） |
| incremental 回填 | `is_incremental()` 手工 WHERE | `start`/`end` 一等公民 |
| dbt 相容性 | — | 宣稱 backwards compatible with dbt |

**SQLMesh 的代價**：版本號還在 `0.236`，每 2-4 週一版，API 可能變動。但**單一 repo 發版**這點，對單人維護者的實際風險低於 dbt 的雙 repo 結構。

---

## 9. 問題 7：單機規模的實際極限

### 9.1 官方的記憶體規則（實際引用，非估算）

DuckDB `guides/performance/environment` 頁面的原文：

> **Bestpractice: Aim for 1-4 GB memory per thread.**
> "As a rule of thumb, DuckDB requires a **minimum of 125 MB of memory per thread**. For example, if you use 8 threads, you need at least 1 GB of memory."
> "As an approximation, **aggregation-heavy workloads require 1-2 GB memory per thread and join-heavy workloads require 3-4 GB memory per thread**."

**這給了你一個直接可算的公式**：

| RAM | 建議 threads（聚合型） | 建議 threads（JOIN 型） |
|---|---|---|
| 16 GB | `SET threads = 6`（留 4GB 給 OS/Python） | `SET threads = 3` |
| 32 GB | `SET threads = 12` | `SET threads = 6` |

**注意 Windows 上 DuckDB 預設會用滿實體核心數**，在 16GB 機器上跑 join-heavy 查詢時，預設值幾乎必然 OOM。**`SET threads` 是你最該先調的參數，不是 `memory_limit`。**

### 9.2 larger-than-memory 到底能撐多大？

官方明述支援 out-of-core：

> "DuckDB can process larger-than-memory workloads by **spilling to disk**. This is possible thanks to out-of-core support for **grouping, joining, sorting and windowing** operators."

但也明確列出**限制**（這段最重要，很多人不知道）：

> - "If **multiple blocking operators appear in the same query**, DuckDB may still throw an out-of-memory exception due to the complex interplay of these operators."
> - "Some aggregate functions, such as **`list()` and `string_agg()`, do not support offloading to disk**."
> - "Aggregate functions that use sorting are holistic... these functions can cause an out-of-memory exception when run on large datasets."
> - "**The `PIVOT` operation internally uses the `list()` function**, therefore is subject to the same limitation."

**實務結論**：
- 單一 `GROUP BY` 或單一 `JOIN` 掃 100GB Parquet → **16GB 機器可以跑完**（會 spill，慢但會完成）
- `JOIN` + `GROUP BY` + `ORDER BY` + 視窗函數擠在一個 query → **即使 32GB 也可能 OOM**
- **`PIVOT` 大表 → 高風險**。你的行銷分析很可能要做 pivot（例如渠道 × 月份的交叉表）——**在已聚合的小結果上 pivot，絕不要在明細上 pivot**

### 9.3 給你的實際數字

假設四種資料的量級（Parquet + zstd 壓縮後）：

| 資料 | 列數 | 原始 CSV | Parquet(zstd) | 16GB 可行？ | 32GB 可行？ |
|---|---|---|---|---|---|
| CRM 交易 | 5M | ~2 GB | **~200 MB** | 輕鬆 | 輕鬆 |
| 廣告成效 | 500K | ~200 MB | **~30 MB** | 輕鬆 | 輕鬆 |
| POS 門市 | 50M | ~15 GB | **~1.5 GB** | 可以 | 輕鬆 |
| 網站事件 | 300M | ~120 GB | **~12 GB** | **可以，但要調參** | 舒適 |
| 網站事件 | 1B+ | ~400 GB | **~40 GB** | 勉強（需嚴格分區裁剪） | 可以 |

**16GB 機器的實務上限**：**單次查詢實際掃描的資料量控制在 30-50 GB Parquet 以內**（不是總資料量——分區裁剪後實際讀取的量）。這對「上億列事件」完全夠用，前提是**查詢一定要帶日期範圍**。

**32GB 機器**：舒適區可到 100-150 GB Parquet 掃描量。

### 9.4 必調的參數組合

```sql
-- 開場先跑這一組
SET threads = 6;                       -- 16GB 機器；32GB 可設 10-12
SET memory_limit = '11GB';             -- 約實體記憶體的 70%
SET temp_directory = 'E:/duckdb_tmp';  -- 必須是本機 SSD，不能是網路碟
SET preserve_insertion_order = false;  -- 大量 import/export 時降低記憶體
```

`preserve_insertion_order` 的官方說明：

> "When importing or exporting datasets... which are much larger than the available memory, an out of memory error may occur... consider setting the `preserve_insertion_order` configuration option to `false`. This allows the system to re-order any results that do not contain `ORDER BY` clauses, potentially reducing memory usage."

**副作用**：沒有 `ORDER BY` 的查詢結果順序會不固定。對分析無影響，但**如果你的測試斷言依賴列順序，會壞掉**。

### 9.5 平行度的隱藏門檻

> "DuckDB parallelizes the workload based on **row groups**... The default row group size in DuckDB's database format is **122,880 rows**. Parallelism starts at the level of row groups, therefore, **for a query to run on k threads, it needs to scan at least k * 122,880 rows.**"

**意涵**：6 threads 需要至少 737,280 列才能跑滿平行度。你的 CRM 交易（百萬列）剛好在邊緣，**廣告成效資料（50 萬列）根本無法跑滿平行**——這不是問題（資料小、本來就快），但別困惑於「為什麼加 CPU 沒變快」。

---

## 10. 問題 8：Windows 上的實際踩雷

### 10.1 中文編碼（最高頻，我在本次調研中就踩到）

**踩雷實錄**：本次調研執行 Python 腳本輸出時，直接遇到：

```
UnicodeEncodeError: 'cp950' codec can't encode character '\u2248'
```

Windows 繁體中文版的 console 預設編碼是 **cp950（Big5 的微軟變體）**，不是 UTF-8。任何印出非 Big5 字元（甚至只是 `≈`、`→`、emoji）的 Python 腳本都會直接 crash。

**解法（三選一，建議全做）**：

```powershell
# 1. 專案層級：在 .venv/pyvenv.cfg 或啟動腳本設環境變數
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

```python
# 2. 程式層級：所有檔案 I/O 顯式指定 encoding，一次都不要省
open(path, "r", encoding="utf-8")
df.to_csv(path, encoding="utf-8-sig")   # -sig 讓 Excel 正確辨識
pathlib.Path(p).read_text(encoding="utf-8")
```

```sql
-- 3. DuckDB 讀 Big5 CSV：用 encodings extension
INSTALL encodings; LOAD encodings;
FROM read_csv('pos_export.csv', encoding = 'big5');
```

**`encodings` extension 實際查證的支援清單裡確實包含**：`big5`、`windows-950-2000`、`windows-950_hkscs-2001`。官方說支援「more than 1,000 character encodings」（透過 ICU）。

**這條對你極重要**——台灣的 POS 系統、CRM 匯出、政府開放資料**大量使用 Big5/CP950**。沒有這個 extension，你會看到滿螢幕亂碼或 `Invalid unicode` 錯誤。

**Excel 輸出的特殊陷阱**：交付 CSV 給同事時，**一定要用 `utf-8-sig`**（帶 BOM）。純 `utf-8` 的 CSV 在 Excel 開啟時中文會變亂碼，這是台灣辦公室最常見的抱怨。

### 10.2 路徑

| 問題 | 說明 | 解法 |
|---|---|---|
| **反斜線被當跳脫字元** | `"E:\Projects\行銷分析\new"` → `\n` 變換行 | Python 一律用 `pathlib.Path` 或正斜線 `E:/Projects/...`。**DuckDB SQL 裡一律用正斜線**，它在 Windows 上完全支援 |
| **MAX_PATH 260 字元** | medallion + hive partition 路徑很長：`10_raw/source=ga4_events/year=2026/month=07/day=15/data_0.parquet` 加上專案根目錄容易超標 | 專案根目錄**放淺**（`E:\mkt\` 而非 `E:\Users\...\Documents\Projects\...`）。或啟用長路徑支援（需管理員權限改登錄檔，非我可代勞） |
| **中文路徑** | `E:\Projects\行銷分析\` 本身沒問題（DuckDB/Python 都用 UTF-8 內部處理），但**部分工具鏈會炸** | **專案根目錄可以有中文，但 `10_raw/` 以下的所有路徑、檔名、partition value 一律純 ASCII** |
| **Git Bash vs PowerShell 路徑不一致** | 我在本次調研就踩到：Git Bash 寫 `/tmp/x.json`，Windows Python 讀不到 | 跨工具時**一律用絕對 Windows 路徑** |

### 10.3 記憶體

- Windows 的**分頁檔（pagefile）**會讓 OOM 表現成「極慢」而非「報錯」。**先設 `SET memory_limit`**，讓 DuckDB 主動 spill 到 `temp_directory`（快得多），而不是讓 OS 換頁。
- `temp_directory` **務必指向本機 SSD**。若指到 `C:\Users\...\AppData\Local\Temp` 而 C 槽快滿，spill 會失敗。
- **防毒軟體（Windows Defender）會即時掃描 spill 產生的暫存檔**，嚴重拖慢大查詢。建議把 `temp_directory` 與 `10_raw/` 加入排除清單。

### 10.4 檔案鎖（單機最容易卡住的問題）

DuckDB 官方 Concurrency 頁面的原文：

> **"File locks.** DuckDB handles concurrent database access requests using file locks. **Exercise extra caution when accessing a DuckDB database file in a shared directory** (e.g., from different operating systems using different file systems or on network attached storage)."

以及並發模型：

> "Read-write mode: **one process** can both read and write to the database."
> "Read-only mode: multiple processes can read from the database, but no processes can write (`access_mode = 'READ_ONLY'`)."

**實際會發生什麼**：

| 場景 | 結果 |
|---|---|
| VS Code 開著 DuckDB extension 連著 `.duckdb`，同時跑 Python 腳本 | **腳本拿不到鎖，直接失敗** |
| 跑著 Jupyter kernel 沒關，又開 DuckDB CLI | 同上 |
| 兩支腳本同時寫同一個 `.duckdb` | 第二支失敗 |
| **多支腳本唯讀** | **可以**，全部加 `access_mode = 'READ_ONLY'` |

**解法**：

```python
# 唯讀場景（儀表板、報告生成）一律這樣連
con = duckdb.connect("warehouse/marketing.duckdb", read_only=True)
```

寫入場景則確保**同時只有一個行程**。實務上最常見的兇手是**忘記關掉的 Jupyter kernel 或 VS Code 的資料庫外掛**——遇到 lock 錯誤時先檢查這兩個。

**如果你需要真正的並發寫入**，官方給兩條路：
- **Quack remote protocol**：「Quack in beta stage as of DuckDB v1.5.2, and is expected to become mature by **DuckDB v2.0 in fall 2026**」→ **現在是 beta，不要用在正式流程**
- **DuckLake + PostgreSQL catalog**：「For a stable solution, consider using the DuckLake format with PostgreSQL as the catalog database」→ 穩定但要架 Postgres

單人專案兩個都不需要。

### 10.5 OneDrive / 雲端同步資料夾（強烈警告）

如果專案在 OneDrive / Google Drive / Dropbox 同步的資料夾裡，會同時踩到三個雷：

1. **檔案鎖**：同步程式會持有檔案 handle，造成 DuckDB 拿不到鎖
2. **官方明確不建議**：前引 NAS 警告涵蓋「network drives such as SMB」，雲端同步資料夾行為類似
3. **同步流量爆炸**：每次重建 mart，數 GB 的 Parquet 會被重新上傳

**建議**：
- `warehouse/`（`.duckdb`、`.ducklake`）與 `10_raw/`～`30_mart/` → **放本機 SSD，且排除同步**
- `00_source_archive/` 與 `40_output/` → 可以同步（原始檔與交付物值得備份）
- 在專案根目錄放 `.gitignore` 同時，也在 OneDrive 設定裡排除資料目錄

### 10.6 其他

- **檔名大小寫**：Windows 不敏感、Parquet 欄位名敏感。**一律小寫底線**。
- **`polars` 安裝**：預設會拉 `polars-runtime-32`，wheel 是 `cp310-abi3-win_amd64`，Python 3.14 可正常安裝。
- **`pyiceberg` 在 Python 3.14 上無 wheel**，若不慎被相依拉進來會嘗試 source build 並失敗——鎖定不要安裝。

---

## 11. 推薦堆疊

### 11.1 核心（現在就裝）

```powershell
# Python 3.14.1
pip install duckdb pyarrow polars pandera
```

| 層 | 選擇 | 版本（查證日 2026-07-26） | 理由 |
|---|---|---|---|
| **查詢引擎** | **DuckDB** | 1.5.5 | 前提；cp314 win_amd64 wheel 已備 |
| **儲存（raw/staging）** | **Parquet + zstd + Hive partition** | — | 零額外概念，DuckDB 原生最佳化 |
| **儲存（mart）** | **DuckLake** | 規格 1.0（DuckDB ≥1.5.2） | `MERGE INTO` 給 idempotency，snapshot 給可稽核性 |
| **編排** | **純 SQL 檔 + 100 行 Python runner** | — | 跨過 8.4 的臨界點再升級 |
| **品質（主力）** | **純 SQL 斷言** | — | 資料在 DuckDB 裡，就在那裡驗 |
| **品質（出口）** | **pandera** | 0.32.1 | MIT；唯一明確支援 Python 3.14 |
| **輔助整形** | **Polars** | 1.43.0 | abi3 wheel，3.14 可用；預設版即可 |

### 11.2 條件性採用

| 工具 | 版本 | 何時加入 |
|---|---|---|
| **dlt** | 1.29.1 | **當你開始打 API**（Meta/Google Ads、GA4、電商平台）。有原生 `ducklake` extra。檔案來源不要用。 |
| **SQLMesh** | 0.236.1 | **當 8.4 的五個訊號中有兩個成立**。跳過 dbt。 |

### 11.3 建議的初始設定檔

```python
# tools/db.py
import duckdb, os

def connect(read_only: bool = False, threads: int = 6, mem: str = "11GB"):
    con = duckdb.connect("warehouse/marketing.duckdb", read_only=read_only)
    if not read_only:
        con.execute(f"SET threads = {threads}")
        con.execute(f"SET memory_limit = '{mem}'")
        con.execute("SET temp_directory = 'E:/duckdb_tmp'")
        con.execute("SET preserve_insertion_order = false")
    con.execute("INSTALL encodings; LOAD encodings;")   # Big5/CP950 必備
    return con
```

---

## 12. 明確不用的東西 + 理由

| 不用 | 決定性理由（全部基於實際查證） |
|---|---|
| **Great Expectations** | **`requires_python = <3.14`，pip 在 Python 3.14.1 上直接裝不起來。** 專案本身健康（1.19.1 @ 2026-07-24），但要用它得另開 Python 3.13 環境。單人專案為一個驗證工具維護第二套環境不划算；且其治理型功能（Data Docs、跨團隊 Suite 複用）對一人專案無價值。 |
| **Soda Core** | **授權是 Elastic License 2.0（PyPI license 欄位寫 `Proprietary`），非開源，程式碼含 license key 機制且條款禁止規避。** 加上 README 明寫官方支援上限 Python 3.12（落後你兩版）、每週發版對單人維護是負擔。 |
| **dbt-duckdb**（連帶 dbt-core） | **adapter 落後 core 5 個月、2 個 minor 版本**（1.10.1 @ 2026-02-17 vs core 1.12.0 @ 2026-07-16），且 `dbt-core>=1.8.0` 無上限 pin，pip 會裝出未經驗證的組合。**dbt-core 2.0 已在 alpha**（`2.0.0a5` @ 2026-07-20），一年內要面對大版本遷移。要上框架就直接評估 SQLMesh（DuckDB 支援內建、同 repo 同版發布）。 |
| **Ibis** | **在你已定案「SQL 為介面」的前提下，Ibis 是淨增加的抽象層**——debug 對象從「我的 SQL」變成「我的 Ibis 表達式 → 生成的 SQL」。另外 **12.0.0 @ 2026-02-07 已 5.5 個月無新版，連 dev 版也停在 2 月**（repo 仍有 commit，原因不明，列入無法查證）。 |
| **Kedro** | 專案健康（1.5.0 @ 2026-06-29、LF AI & Data Foundation 治理），但**它的核心價值是「強制專案結構」，收益隨團隊人數增長**。一個人用，`conf/` + `src/pipelines/` + `settings.py` 的約定是純開銷。可借用其 Data Catalog 概念寫 30 行 YAML，不必引入框架。 |
| **Hamilton** | 概念優雅、侵入性低，但**正在經歷 Apache 改名遷移**（`sf-hamilton` → `apache-hamilton`），且**發版節奏慢**（1.90.0 @ 2026-04-25，前一版 1.89.0 @ 2025-10-12，中間隔 6 個月）。它的核心價值（DAG 編排）在單人專案可由 200 行 Python runner 取代。 |
| **Apache Iceberg（作為寫入路徑）** | **DuckDB 官方明述：無 catalog 時對 Iceberg 是唯讀的**（"This requires no catalog and **is read-only**"）；要寫入必須 attach 一個 Iceberg REST catalog 服務。**且 `pyiceberg 0.11.1` 沒有 cp314 wheel**，你的 Python 3.14.1 裝不了預編譯版。單機分析師架 REST catalog 服務，成本與 DuckLake 完全不成比例。**保留 `iceberg_scan` 唯讀能力**，未來要對接公司 lakehouse 時可用。 |
| **Polars `[rt64]`** | 官方文件明述 `rt64` = Big Index（2^64 列），且「Polars will be a bit slower... less cache efficient」。**你的事件資料上億列，遠低於預設的 2^32（43 億）上限**，不需要。 |
| **`APPEND` 作為日常載入方式** | 它是為累加設計的，**重跑必然重複**。日常載入一律 `OVERWRITE_OR_IGNORE` + 明確日期範圍。 |
| **`hour=` 分區** | 每小時 3-6MB，遠低於官方「至少 100 MB per partition」建議。 |
| **在明細資料上 `PIVOT`** | 官方明述 `PIVOT` 內部使用 `list()`，而 `list()` **不支援 spill to disk**，大表必 OOM。只在已聚合的小結果上 pivot。 |
| **`.duckdb` 放在 OneDrive / 網路磁碟機** | 官方明確建議避免（"avoid using DuckDB's native database format in read-write mode on network-attached storage"），會有檔案鎖衝突與 spurious errors。 |

---

## 13. 無法查證的事項

以下是我**確實嘗試但未能取得**的資訊，誠實列出，不以印象填補：

1. **DuckLake 的 git tag / release 歷史**：`duckdb/ducklake` 的 GitHub Releases 頁面明確顯示「There aren't any releases here」，且我嘗試抓 `/tags` 與 `/commits` 端點時**已耗盡 GitHub 匿名 API 額度（60 req/hr）而收到 403**。因此「DuckLake 1.0 於 2026 年 4 月發布」這個時間點，我的來源是 **DuckDB 官方文件頁的敘述**（"DuckLake 1.0 was released in April 2026"），**不是我直接看到的 git tag**。

2. **`duckdb/ducklake` 的 README**：`raw.githubusercontent.com/duckdb/ducklake/main/README.md` 回傳 404，該 repo 根目錄可能沒有 README.md 或使用其他檔名。repo 的檔案結構我**未能列出**（受同一 API 額度限制）。

3. **Ibis 發版停滯的原因**：`ibis-project/ibis` 的 `pushed_at` 是 2026-07-24（有活動），但正式版停在 12.0.0（2026-02-07）、連 dev 版也停在 2026-02-01。**我無法從抓到的資料判定這是發版流程調整、版本策略改變，還是專案動能下降。** 未讀取其 issue/discussion 或 roadmap。

4. **dbt-duckdb 對 dbt-core 1.12 的實際相容性**：我確認了版本落差與 `dbt-core>=1.8.0` 的無上限 pin，但**未查證是否有已知的 breaking issue**。我沒有讀 dbt-duckdb 的 issue tracker（API 額度耗盡）。「未經驗證的組合」是基於發版時間差的合理推論，**不等於「一定會壞」**。

5. **SQLMesh 與 Ibis 的 Python 3.14 實際相容性**：兩者的 PyPI metadata **完全沒有 Python classifier**（不是「沒有 3.14」，是一個都沒有），`requires_python` 也沒有上界。因此我**無法判斷它們是否支援 Python 3.14**——只能說「pip 不會擋」。**需要實際安裝測試才能確認。**

6. **Soda Core 在 Python 3.13/3.14 的實際行為**：README 寫「there are no known issues preventing use of Python 3.13+」，但這是**廠商自述**，我沒有獨立驗證，也沒有找到 3.14 的測試證據。

7. **第 9.3 節的資料量對照表是我的估算，不是量測值。** 壓縮率（我假設 CSV → Parquet+zstd 約 10:1）高度依賴實際資料的基數與欄位型別——高基數的 UUID 欄位壓縮率會差很多，低基數的類別欄位會好很多。**這張表用來抓數量級，不要當精確預測。** 建議你拿真實資料跑一次 `COPY ... TO ... (FORMAT parquet, COMPRESSION zstd)` 後量測實際大小。

8. **16GB/32GB 的「實務上限」（30-50 GB / 100-150 GB 掃描量）是我從官方的每執行緒記憶體規則推導的，不是官方數字，也不是我實測的。** 官方只給了「1-4 GB per thread」與 out-of-core 的限制清單，**沒有給任何「N GB RAM 能處理 M GB Parquet」的官方數字。** 實際極限高度依賴查詢形狀（單一 blocking operator vs 多個疊加）。

9. **DuckDB 在 Windows 上的中文路徑行為，我沒有實際測試。** 「專案根目錄可以有中文」是基於 DuckDB 內部使用 UTF-8 的推論；我**確實**在本次調研中踩到 cp950 的 console 編碼錯誤（那是實測），但**沒有實測 DuckDB 讀寫含中文字元路徑的 Parquet 檔**。建議你在正式建目錄前先跑一個 5 分鐘的小測試。

10. **防毒軟體拖慢 spill 的說法沒有量測數據支撐**，是基於 Windows Defender 即時掃描機制的一般性推論。

11. **各 repo 的 star 數是查證當下（2026-07-26）的快照**，且 star 數與專案品質無因果關係，僅作為社群規模的粗略指標。

12. **我沒有查證任何工具的商業支援、SLA、或安全漏洞（CVE）狀態。**

---

## 附錄：一頁速查

```sql
-- 開場設定（Windows / 16GB）
SET threads = 6;
SET memory_limit = '11GB';
SET temp_directory = 'E:/duckdb_tmp';
SET preserve_insertion_order = false;
INSTALL encodings; LOAD encodings;      -- Big5/CP950

-- raw 讀取（永遠加這兩個參數）
FROM read_parquet('10_raw/source=X/**/*.parquet',
                  union_by_name = true, hive_partitioning = true);

-- Big5 CSV
FROM read_csv('pos.csv', encoding = 'big5');

-- idempotent 分區覆寫
COPY (...) TO '10_raw/source=X'
(FORMAT parquet, COMPRESSION zstd, PARTITION_BY (event_date), OVERWRITE_OR_IGNORE);

-- mart 增量（DuckLake）
ATTACH 'ducklake:warehouse/marketing.ducklake' AS mart (DATA_PATH 'warehouse/mart_data/');
MERGE INTO mart.fct_orders AS t USING staged AS s ON (t.order_id = s.order_id)
WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT;

-- 稽核
FROM ducklake_snapshots('mart');
FROM ducklake_table_insertions('mart','main','fct_orders', 3, 4);

-- 維護（定期）
CALL mart.merge_adjacent_files();
CHECKPOINT;
```

**分區粒度**：至少 100 MB／分區。CRM 與廣告不分區；POS 用 `year=/month=`；事件用 `year=/month=/day=`。

**驗證**：raw/staging 用 SQL 斷言；出口 DataFrame 用 pandera。

**檔案鎖**：唯讀連線一律 `read_only=True`；遇到 lock 先關 Jupyter kernel 與 VS Code DB 外掛。
