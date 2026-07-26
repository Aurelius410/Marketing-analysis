# 可用性審查：照著 SKILL.md 從 M0 走到 M4，真的做得出來嗎

審查日期：2026-07-27
審查對象：`skill/行銷數據分析/SKILL.md`、`CLAUDE.md`、`references/00`–`20`（21 份，920 KB）、`scripts/`、`templates/`
審查方法：假裝第一次使用者，手上一份交易明細，從 SKILL.md 進入，逐步照做到 M4；每個「見 xx」「產出 X」「跑 script Y」都實際去查它存不存在、規格夠不夠寫得出來
對照素材：`00_source_archive/`（25 份 .md digest，2.6 MB）

**總結論**：方法論本身寫得極好（門檻有出處、降級有階梯、每條規則有實證代價）。**擋住使用的不是方法論，是三件事：(1) 專案資料夾結構有三套互相矛盾的方案，其中程式碼自動建的那一套沒有任何 reference 在用；(2) 36 支被當成硬規則引用的 script 有 34 支不存在，其中 5 支是「沒有它就走不下去」；(3) M1 的品質關卡要求「在 contracts/<source>.yml 宣告處理方式才能解除 error」，但整套文件沒有任何一處寫這個檔長什麼樣。**

---

## Critical

### C1. 專案資料夾結構有三套互斥方案，程式自動建的那一套沒有任何 reference 在用

**檔案／位置**
- `scripts/paths.py:61-85`（`PROJECT_SUBDIRS` / `FIGURE_SUBDIRS` / `TABLE_SUBDIRS`）
- `references/03_倉儲與檔案結構.md:29-69`（§1.2 完整結構）
- `references/00_通則與紀律.md:48-59`（§1.2 三段式留檔）
- 另有 18 份 reference 使用編號式路徑（見下方清單）

**原文引述**

`references/03_倉儲與檔案結構.md:32-68`：
```
├── 專案記憶/                ← 專案核心.md、進度與異狀.md、指標字典.csv、決策紀錄.md
├── 開案與問題定義/          ← 問題定義.md、假說登錄表.csv、checklist.md、指標樹.md
├── 原始資料/                ← raw 層。唯讀，落地即凍結…
...
└── 執行紀錄/                ← run_manifest.json、cleaning_log.md、lineage.md、時間記錄.md
```

`references/00_通則與紀律.md:49-58`（同一件事，完全不同的名字）：
```
projects/<代號>/
├── 01_raw/        交易記錄檔.xlsx              ← 原名不動、唯讀
├── 02_staging/    s2_01_typed.parquet
├── 03_mart/       fact_transaction.parquet
├── 04_features/   customer_features__as_of_2026-06-30.parquet
├── _quarantine/   bot_and_test_txn.parquet
└── _log/          cleaning_log.md
```

**錯在哪**

`CLAUDE.md:16-24` 叫使用者用 `project_dir()` 開專案，`paths.py:209-220` 會自動建立 13 個**中文名**目錄。但走進 M0 之後，18 份 reference 一路叫你把檔案寫到編號式目錄：

| reference | 要求寫到哪 | paths.py 有建嗎 |
|---|---|---|
| 01 §3.4:162 | `00_intake/hypothesis_register.csv` | ❌ |
| 01 §四:198 | `00_intake/checklist_matrix.md` | ❌ |
| 01 §五:233 | `templates/metric_tree.yaml` → 存 `00_intake/` | ❌ |
| 04 §一:39,41 | `00_intake/檔案盤點.md`、`00_intake/欄位總表.csv` | ❌ |
| 04 §五:273,303 | `06_figures/` | ❌ |
| 04 §八:316 | `07_report/M1_體檢報告.md` | ❌ |
| 05 §二:331 | `04_features/feature_check_M2.parquet` | ❌ |
| 06 §六:299,467 | `04_features/transform_log.csv` | ❌ |
| 06 §4.1:334,390 | `04_features/transform_spec.json` | ❌ |
| 06 §5.2:443,445 | `05_models/scaler.json`、`ts_spec.json` | ❌ |
| 07 §3.3:163,170 | `05_models/scaler.json`、`cluster_spec.json` | ❌ |
| 07:304,616 | `06_figures/04_分群/` | ❌ |
| 09 §（產出清單）:420-436 | `02_staging/`、`03_mart/`、`04_features/`、`05_models/`、`07_report/` 共 17 個路徑 | ❌ |
| 00 §1.5:193 | `05_models/`（證據等級的檢查物件必須在這） | ❌ |
| 00 §1.3:117、§1.6:230 等 15 處 | `_log/`、`_log/degradation_log.md` | ❌ |
| 10:360、12:530、13:94、14:183、15:356,444、16:312、18:124、19:553,627 | 同上編號式 | ❌ |

只有 `references/03` 與 `references/02` 用中文名目錄。**M0 第一個要交的檔（假說登錄表）就已經沒有地方放。**

**怎麼確認它是錯的**：實際執行 `python -c "import paths; paths.project_dir(...)"` 讀出 `PROJECT_SUBDIRS`，逐一與各 reference 的路徑字串比對；並用 `grep -noE '0[0-9]_(intake|raw|staging|mart|features|models|figures|report)/'` 掃全部 21 份 reference，得到 18/21 使用編號式、2/21 使用中文式的分布（`02` 不涉及檔案路徑）。

**修法**：二選一，不能兩套並存。
- (a) 若定案中文式：改 `00 §1.2`、`01`、`04`–`16`、`18`、`19` 共 18 份的路徑字串；`00 §1.2` 的三段式圖要改成 `原始資料/ → 清理後資料/ → 分析資料表/ → 顧客特徵表/`，`_log/` → `執行紀錄/`，`_quarantine/` → `隔離區/`，`05_models/` → `模型輸出/`，`06_figures/` → `圖表/`，`07_report/` → `交付物/`，`00_intake/` → `開案與問題定義/`。
- (b) 若定案編號式：改 `paths.py` 的三個常數、`references/03 §1.2`、`CLAUDE.md:26`。
建議 (a)，因為 `03 §1.2` 對「數字編號在檔案總管裡讓你記不住 05 是模型還是圖表」有明確論證（`03:27`），而中文式已寫進 `paths.py` 與 `config.example.yml`。改完後在 `03 §八 維護條款` 加一條「新增子目錄必須同時改 `paths.py` 的 `PROJECT_SUBDIRS`」。

---

### C2. `圖表/` 與 `統計表/` 的子目錄有三套命名，交集只有 1–2 個

**檔案／位置**：`scripts/paths.py:77-85`、`references/03_倉儲與檔案結構.md:52-60`、`references/19_圖表與統計表規格.md:555-559`

**原文引述**

`paths.py:77-85`：
```python
FIGURE_SUBDIRS = ["資料體檢", "特徵檢驗", "轉換前後對照", "分群",
                  "迴歸診斷", "行銷分析", "預測模型", "文本分析", "報告用"]
TABLE_SUBDIRS  = ["資料體檢", "特徵檢驗", "轉換前後對照", "分群輪廓",
                  "迴歸與診斷", "行銷分析", "預測模型"]
```

`references/03:53-60`：`分布/ 關係/ 時間趨勢/ 組成占比/ 排行比較/ 分群/ 模型診斷/ 行銷專用/ 報告用`（分類軸是**圖種**）
`references/19:555-558`：`01_體檢/ 02_檢驗/ 03_轉換/ 04_分群/ 05_迴歸/ 06_行銷/ 07_預測/ 08_文本/ 報告用`（分類軸是**模組**，且帶編號）

**錯在哪**：`paths.py` 建的 9 個圖表子目錄，與 `03` 只有 `分群`、`報告用` 兩個重疊，與 `19` 只有 `報告用` 一個重疊。統計表 7 個子目錄與 `03` 只有 `特徵檢驗` 重疊。三份文件的分類軸根本不同（圖種 vs 模組），不是拼字差異。使用者跑完 M1 要存圖時，會發現 `03` 說存 `圖表/分布/`（不存在）、`19` 說存 `06_figures/01_體檢/`（不存在）、實際被建好的是 `圖表/資料體檢/`。

**怎麼確認它是錯的**：實際 import `paths` 印出兩個常數，用 Python 對三組清單取交集，結果為 `圖表: {分群, 報告用}`（vs 03）、`{報告用}`（vs 19）、`統計表: {特徵檢驗}`（vs 03）。

**修法**：以 `paths.py` 的模組軸命名為準（它與 `19` 的分類軸一致，只差編號前綴），改 `03 §1.2` 的九類圖表與七類統計表清單、改 `19 §6.2` 去掉數字前綴。`03 §1.2` 原本按圖種分類的清單價值在於「哪些圖種存在」，可移到 `19 §4.1 主決策表` 當附註，不要當目錄結構。

---

### C3. M1 的 error 關卡要求寫 `contracts/<source>.yml`，但全套文件沒有這個檔的規格

**檔案／位置**：`references/04_資料體檢.md:19, 40, 42, 184, 215, 258, 529`；`references/03_倉儲與檔案結構.md:36`

**原文引述**

`04:215`：
> | `2` | **有 error** | **擋住。不准進 M2。** 必須在 `contracts/<source>.yml` 明確宣告處理方式後重跑 |

`04:184`：
> `-- <grain_cols> 從 contracts/<source>.yml 的 grain: 欄位讀出來，不准寫死在這裡`

`03:36`（全套文件對這個檔唯一的「規格」）：
> `│   └── contracts/           ← <source>.yml：欄位契約、renames、sentinels、unit、source_tz`

**錯在哪**：這是典型的「說產出 X 但沒說 X 長什麼樣」。契約檔是 M1 的第 ② 步輸入、第 ④ 步輸出、第 ⑤ 步解除 error 的唯一途徑，`04 §八` 的範本裡甚至寫「已生成 `contracts/ntu_creditcard.yml` 草稿」（`04:416`）。但：
- 沒有 `templates/` 底下的契約範本檔
- 沒有任何一節列出完整欄位（只知道有 `grain:`、`sentinels:`、`renames:`、`unit`、`source_tz` 五個鍵，其中三個只在散落的句子裡出現過一次）
- 沒有一個完整的 YAML 範例
- `02_資料模型規格.md` 九個小節（`02:11-746`）沒有任何一節談契約檔

使用者跑到 M1 步驟 ⑤ 拿到 exit code 2，被告知「必須在 contracts/ntu_creditcard.yml 宣告處理方式後重跑」，此時無法動作。

**怎麼確認它是錯的**：`grep -rn "contracts/" references/` 得到 9 處引用；`grep -rn "sentinels:\|grain:\|renames:" references/` 得到 4 處，全部是散句而非規格；`ls templates/` 確認無契約範本；逐一檢查 `02` 的九個 `##` 標題確認沒有契約章節。

**修法**：在 `references/02_資料模型規格.md` 新增 `§十 資料契約檔規格`，或新增 `templates/contract.yml`，至少要含：`source`、`grain`（list，對應 `checks/<table>__grain_unique.sql`）、`columns`（每欄的 `name` / `dtype` / `unit`（`ratio|percent|TWD|days`，對應 `03 §3.3`）/ `nullable` / `practical_use`（`04 §二` 的七種標籤））、`renames`（append-only，對應 `03` W5）、`sentinels`（值 → 處理方式 `to_null|keep|exclude`，對應 `04` Q2）、`source_tz`、`encoding`（Big5/CP950，對應 `03` W1）、`quality_overrides`（哪一條 error 已被宣告處理、理由、日期）。並在 `04 §一` 步驟表的第 ② 列指到它。

---

### C4. 36 支被引用的 script 有 34 支不存在，其中 5 支「沒有它就走不下去」

**檔案／位置**：`scripts/`（實有 `paths.py`、`setup_check.py`、`anonymize_pii.py`）

**完整缺失清單**（以 `scripts/` 前綴引用者 34 支 + 裸名引用者 2 支）

| # | script | 首次被要求 | 引用位置 | 沒有它會怎樣 |
|---:|---|:--:|---|---|
| 1 | `check_schema_contract.py` | **M1 步驟②** | `04:40,62`；`00:356` | 硬卡點回報範本第一行就寫「跑完 check_schema_contract」 |
| 2 | `profile_dataset.py` | **M1 步驟①③** | `04:56` | 逐欄剖析（22 個統計量 × 全欄）與 `欄位總表.csv` 產不出來 |
| 3 | **`check_data_quality.py`** | **M1 步驟⑤** | `04:249`；`18-G11:115` | ⛔ **走不下去**：三桶 + exit code 是 M1→M2 的唯一放行機制 |
| 4 | **`db.py`** | 任何 SQL | `03:495` | ⛔ **走不下去**：`03:495` 明訂「所有腳本一律從這裡拿連線，**禁止各自 duckdb.connect()**」 |
| 5 | **`stats_utils.py`** | M2 起 | `SKILL.md:195`；`05:107`；`08:121,161,212,452`；`16:60,245,473`；`18-T3:135` | ⛔ **走不下去**：`SKILL.md` 負面清單明訂「直接呼叫 `anova_lm(typ=3)` 會靜默算錯，用 `stats_utils.py` 的 `anova3()`」——沒有它就沒有合法的 type-III ANOVA 途徑 |
| 6 | `pick_transform.py` | M3 | `06:96` | 情境路由（文件有完整程式碼，可直接抄出來） |
| 7 | `retransform.py` | M3 | `06:192` | Duan smearing（文件有程式碼） |
| 8 | `write_transform_log.py` | M3 | `06:494` | 六欄轉換紀錄（文件有 SCHEMA） |
| 9 | **`build_features.py`** | M8 起 | `03:97`；`17:5` | ⛔ **走不下去**：`18-G4` 明訂「`build_features(as_of)` 是唯一介面」；`03:97` 明訂顧客特徵表由它產生 |
| 10 | **`verify_outputs.py`** | 交付 | `20:357`；`SKILL.md:247`；`18 §八:146`；`00:193,458`；`06:505`；`01:334` | ⛔ **走不下去**：SKILL.md 品質清單最後一項、六份 reference 的匯流點 |
| 11 | `prep_cluster_matrix.py` | M6 | `07:159` | `07:159` 寫「**必經**」 |
| 12 | `kmeans_preflight.py` | M6 | `07:200` | 五道關（文件有程式碼骨架） |
| 13 | `cluster_validity.py` | M6 | `07:416` | — |
| 14 | `basket_gates.py` | M8-2 | `10:141` | — |
| 15 | `split_time.py` | M9 | `12:136` | out-of-time 切分 |
| 16 | `calibrate.py` | M9 | `12:186` | — |
| 17 | `explain_model.py` | M9 | `12:343` | — |
| 18 | `scan_columns.py` | M9 | `12:394` | — |
| 19 | `model_monitor.py` | M9 | `12:530` | — |
| 20 | `text_prep.py` | M10 | `13:75` | — |
| 21 | `size_recommendation.py` | M11 | `14:484` | — |
| 22 | `result_bundle.py` | 交付 | `20:62` | `Result`/`Bundle`：`20:62` 稱「所有交付物取數字的唯一介面」 |
| 23 | `build_report.py` | 交付 | `20:130,138` | — |
| 24 | `build_slides.py` | 交付 | `20:347`（裸名） | — |
| 25 | `check_fonts.py` | 交付 | `19:361`；`20:345` | `20:347` 寫「build_slides.py 與 build_report.py 的**第一行**」 |
| 26 | `collect_figures.py` | 報告用圖 | `19:562` | 見 I2（與 #27 打架） |
| 27 | `collect_report_figures.py` | 報告用圖 | `03:78` | 見 I2 |
| 28 | `palette_lab.py` | 圖表 | `19:245`；`18-G14:123` | — |
| 29 | `robustness.py` | 穩健性 | `16:311` | — |
| 30 | `experiment_power.py` | M12 | `15:189` | — |
| 31 | `export_for_causal.py` | 因果 | `03:540` | — |
| 32 | `causal/did_analysis.py` | 因果 | `03:544` | — |
| 33 | `maintain_ducklake.py` | 倉儲維運 | `03:473,476`；`20:423` | `03:473` 寫「不要靠人記得」 |
| 34 | `build_lineage.py` | 血緣 | `03:314` | `03:314` 寫「檔頭的 depends_on 是唯一的血緣來源，且是它掃描的對象」 |
| 35 | `diff_runs.py` | 可重現 | `03:462` | — |
| 36 | `stamp_version.py` | 交付 | `20:410` | — |

另有 5 個測試檔被引用而不存在：`tests/test_metrics.py`（`17:7,281`；`09:488`）、`tests/test_quality_gates.py`（`17:282`）、`tests/test_invariants.py`（`09:174`）、`tests/test_palette.py`（`19:270`）、`tests/fixtures/dirty_mini.parquet`（`02:560`；`04:547`；`17:285`）。`04:547` 對最後一個寫得很硬：「Q1/Q6/Q7/Q8/Q10/Q11/Q12 這七條在課程資料集上永遠不可能變紅，**必須用 `tests/fixtures/dirty_mini.parquet` 驗證檢查器本身**」。

**怎麼確認它是錯的**：`ls scripts/` 對照 `grep -noE 'scripts/[A-Za-z0-9_/]+\.py'` 掃全部文件的去重結果（36 筆），扣掉 `paths.py`、`setup_check.py`；再 `grep -noE '\b[a-z_]+\.py\b'` 補抓裸名引用（`check_schema_contract.py`、`build_slides.py`）。

**修法**：優先補上表中 5 支標 ⛔ 的（`check_data_quality.py`、`db.py`、`stats_utils.py`、`build_features.py`、`verify_outputs.py`）——它們是 gate 或「唯一合法介面」，其他 script 缺了頂多手寫一次，這 5 支缺了整條紀律鏈斷掉。第二批補 #1/#2/#6-#8/#11（M1–M6 主線）。文件裡已有完整程式碼骨架的（#6 `06:95-129`、#12 `07:196-212`、#26 `19:560-582`、#33 `03:475-483`）只是搬出來成檔。**在補完之前，`setup_check.py` 應加一節列出「缺哪幾支 script → 哪些模組不可用」**（見 I5）。

---

## Important

### I1. `references/19` 要求的 `baozi_viz/` 套件不存在，也不在 SKILL.md 的檔案地圖裡

**檔案／位置**：`references/19_圖表與統計表規格.md:605, 633, 646`；`SKILL.md:35-68`

**原文引述**（`19:600-606`）：
> ### 7.2 `build_chart(df) -> alt.Chart` 純函式規則
> 這是整個視覺層的**單一真相**。四種交付物全部從它衍生，**不准各寫一套**。
> ```python
> """baozi_viz/charts.py —— 唯一的 chart 建構層。
```
另有 `19:633` `# baozi_viz/altair_theme.py`、`19:646` `# baozi_viz/theme.py`。

**錯在哪**：`build_chart()` 在 `19` 與 `20` 各被引用 5 次，是四種交付物（HTML 報告／pptx／marimo／落地 PNG）的共同入口。但 `baozi_viz/` 這個位置：(a) 不存在；(b) 不在 `SKILL.md:63-67` 的檔案地圖裡（地圖只有 `scripts/`、`sql/`、`templates/`、`assets/`、`tests/`）；(c) 與同一份文件裡的 `scripts/palette_lab.py`（`19:245`）、`scripts/check_fonts.py`（`19:361`）分屬兩個位置，看不出憑什麼分。使用者第一次要畫圖時，不知道該建 `scripts/charts.py` 還是 `baozi_viz/charts.py`。

**怎麼確認它是錯的**：`find . -name "baozi_viz*"` 無結果；`grep -rn "baozi_viz" .` 只在 `19` 出現 3 次，`SKILL.md`、`CLAUDE.md` 皆無。

**修法**：統一到 `scripts/viz/`（charts.py / theme.py / altair_theme.py），改 `19 §7.2/§7.3` 的三個路徑註解，並在 `SKILL.md:63` 的檔案地圖補上 `scripts/viz/ ← chart 建構層與主題`。

---

### I2. 「報告用圖只准複製」有兩支不同的 script、兩種 manifest 格式、兩種目標檔名，各自宣稱是唯一途徑

**檔案／位置**：`references/03_倉儲與檔案結構.md:77-86` vs `references/19_圖表與統計表規格.md:560-586`

**原文引述**

`03:78-84`：
```python
# scripts/collect_report_figures.py 的核心，就這麼簡單
MANIFEST = "交付物/報告圖清單.csv"   # 兩欄：來源相對路徑, 報告中的圖編號
for src, fig_no in read_manifest(MANIFEST):
    shutil.copy2(src, pathlib.Path("圖表/報告用") / f"fig{fig_no}_{src.name}")
```

`19:560-576`：
```python
# scripts/collect_figures.py —— 唯一允許把圖放進「報告用/」的方式
def collect(fig_paths: list[Path], dest: Path, manifest: Path) -> None:
    shutil.copy2(p, dest / p.name)      # copy2 保留 mtime，方便比對
    rec[p.name] = {"src": ..., "sha256": ..., "bytes": ...}
    manifest.write_text(json.dumps(rec, ...))
```

**錯在哪**：script 名稱不同（`collect_report_figures.py` vs `collect_figures.py`）、manifest 格式不同（兩欄 CSV vs JSON dict）、輸出檔名不同（`fig{編號}_{原名}` vs 保持原名）、verify_outputs 的檢查也不同（`03:85` 檢查「同 hash 的原檔」vs `19:578-582` 檢查「sha256 等於 manifest 記錄」）。`19:560` 的註解明寫「**唯一**允許把圖放進報告用/的方式」，兩邊都自稱唯一。

**怎麼確認它是錯的**：兩段程式碼並排逐行比對；`grep -rn "collect_figures\|collect_report_figures" references/` 確認兩者各只在一份文件出現、彼此不互相引用。

**修法**：保留 `19` 的版本（有 sha256、有 manifest、`verify_outputs` 檢查更完整），把 `03 §1.3` 改成引用 `19 §6.2`，只留「複製不重畫」的規則與 18-E7 的理由。`03 §八 維護條款` 第 3 條本來就寫「同一件事只在一邊寫完整，另一邊用『見 18-Txx』指過去」——這條規則沒有套用到自己身上。

---

### I3. M1 該出哪些圖表，`04` 與 `19` 給了兩份不相容的清單與兩套檔名規約

**檔案／位置**：`references/04_資料體檢.md:271-317` vs `references/19_圖表與統計表規格.md:15-28, 536-542`

**原文引述**

`04:275-289` 列 F1–F11：直方圖＋密度／箱型圖／類別次數長條／**缺失值熱圖**／**缺失模式矩陣**／**相關矩陣熱圖**／**散點圖矩陣 pairs**／時間序列折線／每月每週長條／**類別×數值分組箱型**／**類別×類別堆疊長條**

`19:19` 列 M1 圖：直方圖 small multiples／箱型圖＋jitter／缺值矩陣熱圖／類別水平長條／日週交易量折線／**六域完整度熱圖**

`04:303-314` 檔名：
```
M1_F01_hist_<table>_<column>.png
M1_F02_box_<table>_<column>.png
```
`19:538` 檔名：
> 格式 `{模組}_{主題}_{圖種}.png`。…底線分隔，**不加版號**

**錯在哪**：
- 圖種：`04` 有 6 種 `19` 沒有（缺失模式矩陣、相關矩陣熱圖、pairs、分組箱型、堆疊長條、每月每週）；`19` 有 1 種 `04` 沒有（六域完整度熱圖）。`19:13` 寫「下表列的是**預設必出**；不出要在《進度與異狀.md》寫理由」——那麼 `04` 的 F4/F5/F6/F7/F10/F11 到底算不算必出？
- 表：`04:293-300` 是 T1–T6（欄位總表／敘述統計／類別次數／缺失值總表／重複值總表／異常值總表）；`19:21-28` 是 1.1–1.6（資料檔清單／欄位字典／敘述統計／類別次數／缺值三桶／六域缺口）。只有兩張重疊，`04` 的重複值總表與異常值總表在 `19` 消失，`19` 的六域缺口盤點在 `04` 的表清單裡消失（雖然 `04 §六` 有講內容）。
- 檔名：`04` 的 `M1_F01_hist_…` 多了一個 F 編號槽，`19` 的三段式格式沒有這個槽。同一張圖兩種合法檔名，`collect_figures` 的 manifest 就對不起來。
- `04:273` 自己寫「用色、字型、尺寸一律照 `19_圖表與統計表規格.md`」，但沒說清單本身以誰為準。

**怎麼確認它是錯的**：逐項比對 `04:275-300` 與 `19:15-28` 兩張表；比對 `04:303-314` 的命名範例與 `19:538` 的格式定義（`F01` 不屬於 `{模組}`、`{主題}`、`{圖種}` 任一槽）。

**修法**：`19` 是「圖表規格」的權威（SKILL.md:60 這樣定位），把清單統一收在 `19 §1.1`，`04 §五` 改成「M1 該出的圖表清單見 `19 §1.1`；本節只補 M1 專屬的判讀重點與實測案例」。同時刪掉 `04:302-316` 的命名區塊，或把 F 編號改成 `19` 認得的形式（例如放進 `{主題}` 槽）。

---

### I4. 覆蓋率門檻有 30% / 60% / 80% 三套，30–60% 區間的行動互相矛盾

**檔案／位置**：`references/04_資料體檢.md:362-368`、`references/00_通則與紀律.md:500`、`references/01_商業框架與提問.md:191`

**原文引述**

`04:364-366`：
> | ≥ 80% | 正常使用 |
> | 30% – 80% | **可用，但報告中該指標旁必須標覆蓋率** |
> | **< 30%** | **不准進報告。** |

`00:500`：
> | 覆蓋率過低 | 算得出來的顧客占比 < **30%** | 執行脈絡 §S2。低於門檻不准進報告 |

`01:191`：
> | 第 5 列覆蓋率 < 60% | 指標不可靠 | **不得作為分群輸入變數，也不得作為建議依據**，只能當描述性補充 |

**錯在哪**：CAI 覆蓋率算出來是 45% 時，`04` 說「可用，標覆蓋率就好」、`00` 說「過門檻，可用」、`01` 說「不得作為分群輸入變數，也不得作為建議依據」。M6 分群的白名單裡有 CAI（`00:502`），所以這不是假想情境。三處互不交叉引用，使用者讀到哪份就照哪份做。

**怎麼確認它是錯的**：查素材 `00_source_archive/research/gap-business-translation.md` BT-07 第 2 點原文：「**硬規則**：覆蓋率 < 60% 的指標，**不得作為分群輸入變數，也不得作為建議依據**」，且同節的門檻表對 λ/MLE、CAI/WMLE、CRI 都標「覆蓋率門檻 ≥ 60%」、CLV 標「≥ 70%」。也就是 `01` 抄的是 BT-07（指標層、分用途），`04`/`00` 抄的是藍圖 §S2（單一門檻）。兩個來源都真實存在，但沒有人做過整併。

**修法**：在 `04 §七` 的覆蓋率表加第三軸「用途」，把兩套門檻合成一張：
- `< 30%`：不准進報告（任何用途）
- `30–60%`：可進報告但必須標覆蓋率；**不得作為分群輸入、不得作為建議依據**（`01:191`）；CLV 另加 70% 門檻
- `60–80%`：可用於分群與建議，圖表標覆蓋率
- `≥ 80%`：正常使用
並把 BT-07 的逐指標最低資料需求表（λ/CAI/CRI/CLV/購物籃/因素分析/分群/卡方）搬進 `17_指標公式庫.md` 每支公式旁邊——BT-07 原文的修補動作 1 就是這樣要求的，目前沒有落地。

---

### I5. 新機器第一件事 `setup_check.py` 會回報「不能開工」，原因是一個文件自己說可以沒有的套件

**檔案／位置**：`scripts/setup_check.py:64-70`；`scripts/paths.py:100-118`；`CLAUDE.md:32-38`

**原文引述**

`setup_check.py:69`：
```python
    "yaml": "讀 config.yml（套件名 pyyaml）",     # ← 放在 CORE
```
`CLAUDE.md:38`：
> 退出碼 0 = 全通過、1 = 有 error **不能開工**、2 = 可開工但部分模組不可用。

`paths.py:8`（設計原則）：
> · 沒有 config.yml 也要能跑 —— 每一項都有合理預設值。

`paths.py:109-113`：
```python
            import yaml  # 只有真的有 config.yml 時才需要 PyYAML
        except ImportError:
            print("⚠ 找到 config.yml 但沒有 PyYAML，改用預設值。…")
```

**錯在哪**：`paths.py` 明確把 PyYAML 當成「只有存在 config.yml 才需要」的選用相依，而且缺了會 graceful degrade。但 `setup_check.py` 把 `yaml` 列在 `CORE`（註解寫「沒有它整條管線不能跑」），因此在**沒有 config.yml 的預設情況**下也會 error。實測本機執行結果：

```
⛔ 缺少核心套件：yaml — 跑 pip install -r requirements.txt
結果：1 個 error、18 個 warning → 不能開工
```

使用者照 `CLAUDE.md` 跑第一個指令就被擋住，而實際上 `paths.py`、`project_dir()`、DuckDB 全都能正常運作。

**怎麼確認它是錯的**：實際執行 `python scripts/setup_check.py`（退出碼 1）；再執行 `python -c "import paths; print(paths.projects_root())"` 確認在沒有 PyYAML 的情況下路徑解析完全正常。

**修法**：把 `yaml` 從 `CORE` 移到 `OPTIONAL`，理由改成「讀 config.yml（沒有 config.yml 時不需要）」；或改成條件式：`CONFIG_FILE.exists() and not has("yaml")` 才 error。

---

### I6. `setup_check.py` 的檢查範圍漏了三類東西，導致「全綠」不代表能開工

**檔案／位置**：`scripts/setup_check.py:76-98, 163-187, 275-276`

**原文引述**（`setup_check.py:275-276`）：
```python
    for fn in (check_python, check_packages, check_paths, check_references,
               check_causal_env, check_tools, check_duckdb_smoke, check_fonts):
```

**錯在哪**：三個缺口。
1. **不檢查 `scripts/`**。34 支被硬性引用的 script 缺席（C4），`setup_check` 一句話都不會說。`check_references()` 有逐份比對 `EXPECTED_REFS`，同樣的做法沒套用到 script。
2. **`OPTIONAL` 清單漏了 `requirements.txt` 裡的 5 個套件**：`marimo`（`20 §五` 的 L2/L3 儀表板）、`vl_convert`（`19:667`、`20:54` 產 pptx PNG 的唯一途徑）、`seaborn`、`scikit-survival`、`tea_tasting`。使用者會在 M11 交付當下才發現 `import marimo` 失敗。
3. **`python-pptx` 只驗 import**，而 `20:346-348` 明確要求：
   > `# scripts/setup_check.py 對 python-pptx 不能只驗 import 成功，要 smoke test：`
   > `#   實際產一頁含中文標題的 .pptx → 重新開啟 → 讀回標題字串比對 → 非 0 退出碼`

   這條要求寫在 reference 裡，`setup_check.py` 沒有實作。

**怎麼確認它是錯的**：讀 `setup_check.py:275-276` 的函式列表確認無 script 檢查；把 `OPTIONAL` 的 21 個 key 與 `requirements.txt` 的套件清單逐一對照（`marimo>=0.10`、`vl-convert-python>=1.7`、`seaborn>=0.13`、`scikit-survival>=0.23`、`tea-tasting>=0.6` 不在 OPTIONAL）；`grep -n "pptx" setup_check.py` 只有一行 import 檢查。

**修法**：加一個 `check_scripts()`，用 `EXPECTED_SCRIPTS = {檔名: "缺了哪些模組不可用"}` 的形式比對（把 C4 的表直接搬進來），缺 5 支 ⛔ 的算 error、其餘算 warning；補齊 `OPTIONAL` 的 5 個套件；依 `20:346-348` 實作 pptx smoke test。

---

### I7. `templates/` 缺 6 個被指名的範本檔，其中 2 個被寫成「M0 硬卡點必填」與「勿另建」

**檔案／位置**：`templates/`；`references/01:233`、`references/11:629`、`references/17:295`、`references/14:355`、`references/20:165-170`

**原文引述**

`01:233`：
> `# templates/metric_tree.yaml —— M0 硬卡點必填，存 00_intake/`

`20:165`：
> `├── exec_onepager.html.j2     ← 決策摘要（§四；檔名由 14 §六指定，勿另建）`

**缺失清單**

| 範本 | 被誰要求 | 現況 |
|---|---|---|
| `templates/metric_tree.yaml` | `01:233`（M0 硬卡點必填）、`14:53`（環 2 的修補件） | ❌ 不存在。`01:234-252` 有完整 YAML 內容可直接抄，屬「壞指標」而非「無規格」 |
| `templates/metric_definitions.csv` | `11:629`、`17:295` | ❌ 不存在。對應 `dim_metric_definition`（18-G10），`00:504` 把「指標不在 `dim_metric_definition`」列為跨模組否決條件 |
| `templates/exec_onepager.html.j2` | `14:355`、`20:165`（「勿另建」） | ❌ 不存在 |
| `templates/報告骨架.html.j2` | `20:164` | ❌ 不存在。11 章 + 9 個排版件的骨架，`verify_outputs` 的「9 個排版件齊備」直接依賴它 |
| `templates/_tokens.css.j2` | `20:166` | ❌ 不存在 |
| `templates/_macros.j2` | `20:167` | ❌ 不存在 |

另：`templates/py/` 是空目錄，沒有任何 reference 指向它。

**怎麼確認它是錯的**：`ls -R templates/` 對照 `grep -noE 'templates/[^ `）)、，,。]+' references/*.md` 的 26 筆引用去重結果，逐一勾稽。

**修法**：`metric_tree.yaml` 與 `metric_definitions.csv` 優先（前者是 M0 硬卡點交付物、後者是跨模組否決條件的依據），內容 `01 §五` 與 `17 §九` 已寫好可直接落檔。四個 Jinja2 範本屬 M11 交付階段，可與 `build_report.py` 一起補。順手刪掉空的 `templates/py/`，或在 `SKILL.md` 檔案地圖說明它放什麼。

---

### I8. `references/19` 沒有 M11 與 M12 的圖表規格，但 SKILL.md 說它涵蓋「每模組」

**檔案／位置**：`SKILL.md:60, 245`；`references/19:15-172`；`references/14`、`references/15`

**原文引述**

`SKILL.md:60`：
> `│   ├── 19_圖表與統計表規格.md          ← 每模組該出什麼圖什麼表、用色、字型`

`SKILL.md:245`（品質檢查清單）：
> `- [ ] 該出的圖都出了（見 ref 19），報告用圖從既有圖複製而非重畫`

`20:171`（決策摘要的第 ④ 版位）：
> | ④ 一張圖 | — | **只放一張**，標題是結論句；從 `圖表/報告用/` 複製，禁重畫（19 §6.2） |

**錯在哪**：`19 §一` 只有 1.1（M1）、1.2（M2/M4）、1.3（M3）、1.4（M6）、1.5（M7）、1.6（M8）、1.7（M9）、1.8（M10）。**M0、M5、M11、M12 完全沒有**。M11 是四個硬卡點的最後一個、M12 是獨立模組，兩者都會產出對外圖表（`15` 的功效曲線、MDE 曲線、平行趨勢圖是 DiD 證據等級的必要條件，`00:180-184` 明訂「事前趨勢平行圖」是準實驗的判定要件之一）。而 `14` 與 `15` 兩份文件裡 `grep "19 §\|ref 19\|圖表"` 皆為 0 筆——它們也沒有自己寫。使用者跑到 M11 要做決策摘要，`20` 說「只放一張圖，從報告用/複製」，但沒有任何地方說該是哪一張。

**怎麼確認它是錯的**：`grep -n '^### ' references/19_圖表與統計表規格.md` 列出 §一 的八個子節，確認缺 M0/M5/M11/M12；`grep -n "19 §\|ref 19\|圖表" references/14_決策轉譯.md references/15_實驗設計.md` 皆無輸出。

**修法**：`19 §一` 補 `1.9 M11 決策轉譯`（sizing 瀑布圖、損益兩平反應率 vs 歷史兌換率的區間圖、優先序 2×2）與 `1.10 M12 實驗設計`（功效／MDE 曲線、事前平行趨勢圖、分流平衡圖）。M0 與 M5 若確定不出圖，在 `19 §一` 開頭明寫「M0、M5 不出圖」，不要靠讀者推斷。

---

### I9. `CLAUDE.md` 的「開工前必讀」六個檔名有三個不存在

**檔案／位置**：`CLAUDE.md:5-12`

**原文引述**（`CLAUDE.md:7-12`）：
```
1. **`SKILL.md`** — 完整流程總覽（八階段、四個硬卡點、觸發條件、檔案地圖）
2. **`references/04_資料品質與踩雷庫.md`** — 進場檢核與失敗案例（必讀，資料錯了後面全錯）
3. **`references/07_分析陷阱清單.md`** — E1–E22 實證防呆規則（必讀，每條都有樣本實證）
4. **`references/02_資料模型規格.md`** — 六域模型完整 DDL，所有分析的地基
5. **`references/05_指標公式庫.md`** — RFM/CAI/CRI/CLV 公式與已驗證的基準值
6. **`references/01_商業框架與提問.md`** — 七問倒推鏈與 Check List 矩陣
```

**錯在哪**：`CLAUDE.md` 是**被自動載入**的檔（`SKILL.md:38` 自己這樣說），是使用者看到的第一份指引，但六個指名檔案有三個不存在：

| CLAUDE.md 寫的 | 實際檔名 |
|---|---|
| `04_資料品質與踩雷庫.md` | 實際 04 是 `04_資料體檢.md`；「踩雷庫」的內容在 `18_分析陷阱清單.md` |
| `07_分析陷阱清單.md` | 實際 07 是 `07_標籤與分群.md`；陷阱清單是 `18` |
| `05_指標公式庫.md` | 實際 05 是 `05_資料特徵檢驗.md`；公式庫是 `17` |

同一段還有兩個內容錯誤：`SKILL.md` 是**十三個模組**不是「八階段」（`SKILL.md:95`）；`01` 是**開案五問**不是「七問」（`01:11` 標題「一、開案五問」）。而 `CLAUDE.md` 完全沒提 `00_通則與紀律.md`——`SKILL.md:97` 把它列為「開工前必讀」的第一份，`00:3` 也自稱「其他 20 份 reference 都假設你已經讀過它」。

同樣的舊編號殘留也在 `references/18:53`：
> | **E8** | 公式抄錯 | … | 公式庫集中管理於 `05_指標公式庫.md`，不逐份手寫 |

**怎麼確認它是錯的**：`ls references/` 逐檔比對；`head -1 references/0[1457].md` 確認實際標題；`grep -n "^## 一" references/01_商業框架與提問.md` 得「一、開案五問」。

**修法**：`CLAUDE.md:7-12` 改成 `SKILL.md` → `00_通則與紀律.md` → `18_分析陷阱清單.md` → `02_資料模型規格.md` → `17_指標公式庫.md` → `01_商業框架與提問.md`，「八階段」改「十三個模組」、「七問」改「五問」。`18:53` 的 `05_指標公式庫.md` 改成 `17_指標公式庫.md`。

---

### I10. `SKILL.md` 的檔案地圖列了三個不存在的目錄，其中兩個被品質檢查清單當成驗收依據

**檔案／位置**：`SKILL.md:63-67, 238, 247`

**原文引述**（`SKILL.md:63-67`）：
```
├── scripts/                          ← 可重複使用的 Python 工具
├── sql/                              ← 建倉與指標 SQL
├── templates/                        ← 記憶檔、報告、指標字典範本
├── assets/                           ← 主題、調色盤、字型設定
└── tests/                            ← 對已知基準值的迴歸測試
```

**錯在哪**：`sql/`、`assets/`、`tests/` 三個目錄都不存在。而且：
- `SKILL.md:238` 品質檢查清單：「指標對得上 `tests/` 的基準值」——無從勾選
- `references/18-G14:123`：圖表設計規範的修補動作是 `assets/tokens.json` + `palette_lab.py`；`19:372,379,380` 需要 `assets/marimo_theme.css`
- `sql/` 在整套 reference 裡沒有任何一處被引用（reference 談的是**專案層**的 `SQL/models/`、`SQL/checks/`，見 `03 §5.1`；skill 層的 SQL 範本實際在 `templates/sql/`）

**怎麼確認它是錯的**：`ls skill/行銷數據分析/` 顯示只有 `references/ scripts/ templates/` 三個目錄；`grep -rnoE '(^|[^/])sql/' references/` 只命中 `02:83,643` 的 `sql/checks/`（專案層）；`grep -rn "assets/" references/` 命中 4 處全在 `18`/`19`。

**修法**：`SKILL.md:64` 的 `sql/` 刪掉或改成 `templates/sql/`（實際位置）；`assets/` 與 `tests/` 要嘛建起來、要嘛從地圖移除並同步改 `SKILL.md:238` 與 `18-G14`、`19 §3.3` 的路徑。地圖列了不存在的目錄，比不列更糟——使用者會以為自己拿到的是殘缺版。

---

## Minor

### M1. `SKILL.md` 說素材庫有 30 份 digest，實際 25 份

`SKILL.md:12`：
> 原始素材全部保存在 `00_source_archive/`（30 份 digest，約 2.5 MB）

確認方式：`find 00_source_archive -name "*.md" | wc -l` = 25；`find … -exec wc -c {} + | tail -1` = 2,615,363 bytes（2.6 MB，大小對得上，份數不對）。`setup_check.py:155-156` 會實算並印出真實份數，所以使用者第一天就會看到兩個數字打架。
修法：`SKILL.md:12` 改「25 份 digest，約 2.6 MB」，或改成不寫死份數。

### M2. `00 §四` 描述 `18-E17` 的內容，與 `18-E17` 現在的寫法不符（互指成環）

`00:450`：
> **與 18-E17 的口徑統一**：18-E17 寫「不顯著標『—』」。本 skill 把「不顯著」統一寫成 `n.s.`…

`18:85`（實際內容）：
> | E17 | 只挑顯著的組別秀 | 所有群 × 所有人口變數都要出現在表中，**不顯著標 `n.s.`**（見 00_通則 §四 的五符號表）|

`18` 已經改成 `n.s.` 並反過來指向 `00 §四`，但 `00:450` 仍在描述舊版的 `—`，形成「A 說 B 寫 X，B 說見 A」的循環。內容上沒有實質風險（兩邊最終口徑都是 `n.s.`），但讀者會以為兩份文件仍有分歧。
修法：`00:450` 改成「本 skill 對『不顯著』統一寫 `n.s.`（`18-E17` 已同步）」，刪掉對舊寫法的描述。

### M3. `SKILL.md` 給的 setup_check 指令從 repo 根目錄跑不起來

`SKILL.md:93`：
> **新機器先跑 `python scripts/setup_check.py`**

實際位置是 `skill/行銷數據分析/scripts/setup_check.py`。`CLAUDE.md:34-36` 同樣寫相對路徑，但 `CLAUDE.md` 明說「這個資料夾」所以還算成立；`SKILL.md` 是總覽文件，讀者可能在 repo 根目錄。
修法：`SKILL.md:93` 改成「`cd skill/行銷數據分析 && python scripts/setup_check.py`」。

---

## 對「references 平均 44 KB，agent 走到某一步要讀整份嗎」的評估

**結論：不需要再切，但需要在每份開頭加「本模組執行清單」。**

理由：
1. **這 21 份不是參考手冊，是「一次一個模組」的執行規格**。`SKILL.md:97` 已經明訂「進入某模組前再讀該模組的 reference」，`00:514` 也寫「走到哪讀哪」。以最大的 `11_行銷_成長與促銷.md`（697 行、56 KB，約 15–18k tokens）而論，agent 走到 M8-3 時把它整份讀進來是合理的——那正好是它要執行的全部內容。
2. **每份的 `##` 節數 7–13，切分粒度已經健康**（唯一偏多的 `04` 有 13 節，但其中 §八 硬卡點範本佔 130 行、§九 維護條款佔 15 行，實質節數是 7）。
3. **真正該切的不是大小，是「同一模組要讀兩份」**。目前 M1 要同時讀 `04`（46 KB）+ `19 §1.1`；M2/M4 要讀 `05`（50 KB）+ `19 §1.2` + `16`；M6 要讀 `07`（55 KB）+ `19 §1.4` + `16`。修掉 I3（把圖表清單統一收在 19）之後，這個問題會自然縮小。

**具體建議（成本低、效益高）：**
- 每份 reference 開頭加一個 8–12 行的「本模組執行清單」區塊：輸入什麼（哪個檔）→ 依序做哪幾步 → 產出哪幾個檔（含路徑）→ 卡點與門檻。agent 讀完這一段就能決定要不要往下讀全文，也能在只讀清單的情況下正確接上上下游。`04 §一` 的七步表（`04:37-45`）已經是這個形態，可以當範本推廣到其餘 20 份。
- **兩份維護條款可以獨立成檔**：每份 reference 末尾的「維護條款」合計約 60 KB（21 份 × 平均 2.8 KB），對執行期的 agent 完全無用，只在改文件時才需要。抽成 `references/_maintenance.md` 可以讓每份平均降到 41 KB，且不損失任何執行資訊。
- **唯一建議實質拆分的是 `19_圖表與統計表規格.md`（685 行）**：它同時是「每模組出什麼圖表」（§一，172 行，執行期要查）與「色彩/字型/選型/排版/命名/主題檔規格」（§二–§八，513 行，設定期讀一次）。前者每個模組都會回來查，後者只在建 `scripts/viz/` 時讀。建議拆成 `19_圖表清單.md` 與 `19b_視覺規格.md`。

---

## 明確查過、沒有問題的地方

1. **SKILL.md 的模組表與 references 的實際內容完全對得上**。逐一比對 21 份的第一行標題與 `SKILL.md:99-113` 的模組表：M0→01、M1→04、M2/M4→05、M3→06、M5/M6→07、M7→08、M8-1/2/3→09/10/11、M9→12、M10→13、M11→14、M12→15，全數相符（`04_資料體檢.md` 標題「資料體檢（M1）」、`05` 標題「資料特徵檢驗（M2／M4）」…）。
2. **所有 `18-Exx / 18-Gxx / 18-Txx` 交叉引用都解析得到**。用 `grep -ohE '18[-_ ]?[EGT][0-9]+'` 掃全部文件，得到 E1–E22（無 E5 以外的跳號問題）、G1–G16、T1–T10 共 48 個唯一代號，全部能在 `18` 找到對應條目（E1–E5 §二、E6–E12 §三、E13–E22 §五、G1–G16 §六、T1–T10 §七）。無懸空引用。
3. **`ref NN §X.Y` 形式的節次交叉引用都存在**。抽查 `00→17 §3.1/§4.2/§6.1/§6.2`、`09→17 §3.4/§6.2/§八`、`08→05 §1.1/§1.3/§1.4/§1.7/§1.9/§7.1/§7.2`、`07→19 §1.4/§4/§6.2`、`12→19 §1.7`，全部命中真實的 `###` 標題。
4. **四個硬卡點的定義在三處一致**。`SKILL.md:117`（M0/M1/M4/M11）、`00 §三:341`、`05:16`（「M2 不卡、M4 是硬卡點」）、`14:8`（「M11 是四個硬卡點的最後一個」）互相吻合。
5. **回報四段格式在四處一致**，且 `00 §三:352-432` 給了三份完整範例（M1/M4/M11），每份的「需要你決定什麼」都附了具體選項＋後果＋**我的預設值**（`00:379` 「直接排除（我的預設）／視為真值／你來確認來源？」）。這一項我特別找過「問了問題卻沒給預設」的案例，在 M0–M4 主線上沒找到。
6. **順序矛盾**：特別查了三組容易打架的順序規則——(a)「先轉換再 winsorize」（`SKILL.md:192` 負面清單 vs `06 §三:219` 鐵則 vs `07:—` 關卡 3）三處一致；(b)「標準化不在 M3 做」（`SKILL.md:138` vs `06 §五:426` vs `05 §1.5:178` vs `07 §3.3:163`）四處一致；(c)「ANOVA→事後檢定綁定」（`SKILL.md:185` vs `18-E1` vs `05 §1.2:107` vs `00 §1.6:246`）四處一致。沒有找到順序矛盾。
7. **降級階梯的方向性一致**：`00 §1.6:242-251` 的六條階梯與各模組 reference 內的階梯（`05 §六`、`07 §五`、`08 §—`、`09`）方向都是「前提由多到少」，沒有出現平移式的假降級。
8. **M0 的處境分流器在缺資訊時有明確預設**：`01 §二:58-76` 的決策樹對每一個分支都給了落點，Q3/Q4 答不出來分別落到處境 7/6，且 `01:87` 明訂這兩格的正確產出與禁止事項。這是全套文件裡「決策點有預設」做得最好的一段。
9. **`config.example.yml` 與 `paths.py` 的 `_DEFAULTS` 鍵完全對得上**（專案根目錄／素材庫／python.次環境路徑／次環境版本／duckdb.檔名/執行緒/記憶體上限/暫存目錄／字型四項／工具三項），且 `paths.py:100-118` 在缺 config.yml、缺 PyYAML、YAML 解析失敗三種情況下都能 graceful degrade。
10. **`anonymize_pii.py` 存在且對應 `18-G13`**，是三支現存 script 中唯一沒被 reference 硬性引用卻已經寫好的——沒有問題，只是順帶記錄。
