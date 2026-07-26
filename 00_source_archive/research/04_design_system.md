# 04 — 設計系統：把「美感」變成可寫進 Skill 的硬規則

> 調研日期：2026-07-26
> 對象環境：Windows 11 Home 26200 / Python 3.14.1 / 繁體中文
> 前提（已定案，本文不再比較）：倉儲層 DuckDB + Parquet + SQL；建模與視覺化層 Python 為主；交付物四種（單檔 HTML、互動儀表板、投影片、Excel/CSV）；資料型態四種（會員 CRM、電商行為、廣告成效、實體 POS）
>
> **紀律聲明**：本文所有「維護狀態 / 版本 / 最後活躍時間 / 是否 archived」皆來自實際 fetch 的 GitHub Atom feed 或頁面，逐項標註觀測值。所有 hex 色值與對比度、色盲可辨性數據，皆由本機 matplotlib 3.10.7 實際計算產出（計算腳本見 §9）。查不到的一律進 §12「無法查證的事項」。

---

## 0. 硬規則速查表（Skill 可直接抄成 checklist）

這一節是給 Skill 用的「可機械檢查」條款。細節與推導在後面各節。

| # | 規則 | 可機械檢查？ |
|---|---|---|
| R-01 | 淺色主題單一圖表**最多 5 個類別色**（slot 1–5）；第 6–8 色僅可用於大面積填色，不可作為線條/小點 | ✅ 數 series 數量 |
| R-02 | 深色主題單一圖表**最多 7 個類別色**（slot 1–7）；第 8 色僅可填色 | ✅ |
| R-03 | 超過上限 → 強制改為：Top-N + 「其他」、或 small multiples、或加冗餘編碼（direct label / marker shape / dash） | ⚠️ 半自動 |
| R-04 | 任何線條、點、文字對背景的 WCAG 對比 **≥ 3.0:1**；正文文字 ≥ 4.5:1 | ✅ 計算 |
| R-05 | 紅/綠語意色（好/壞）**必須**同時帶第二編碼（+/− 符號、箭頭、位置），因為 deuteranopia 下 ΔE2000 僅 10.3（淺）/ 7.5（深） | ✅ 檢查是否有符號 |
| R-06 | 圓餅圖 / 甜甜圈：**類別 > 5 一律禁用**；≤ 5 且為「單一時點的部分對全體」才可用；任何時間序列禁用 | ✅ |
| R-07 | 雙 Y 軸：**預設禁用**。唯一例外＝同一量在兩種單位（°C/°F、TWD/USD），且兩軸為固定線性換算 | ✅ 檢查換算關係 |
| R-08 | 長條圖 / 直條圖 Y 軸**必須從 0 起**；折線圖可不從 0，但必須標示 | ✅ |
| R-09 | 3D、陰影、漸層填色、圓角柱、雷達圖：**全禁** | ✅ |
| R-10 | 數字欄位一律**右對齊**、同欄**小數位數固定**、千分位分隔、使用 tabular numerals | ✅ |
| R-11 | **禁用 Noto Serif TC 排數字欄**（實測數字寬度有 6 種，非等寬）；數字欄用 Noto Sans TC / Microsoft JhengHei / Segoe UI | ✅ 字型白名單 |
| R-12 | matplotlib 輸出若需要粗體中文，**禁用 Noto Sans TC 可變字型**（實測 bold 與 normal 像素完全相同），改用 Microsoft JhengHei 或安裝 Noto Sans TC 靜態字重 | ✅ |
| R-13 | 儀表板 12 欄網格；KPI 列高度固定、每卡 3 欄；趨勢區 6–12 欄；明細表永遠在最後一屏 | ✅ |
| R-14 | 圖表標題必須是**結論句**（IBCS SAY），不是「XX 趨勢圖」 | ⚠️ 人工/LLM 檢查 |
| R-15 | 同一份報告中，同一指標的軸刻度必須一致（IBCS 一致性縮放） | ✅ 比對 y-limits |
| R-16 | 情境語意固定：實際=實心、計畫=空心外框、預測=斜線填、去年=淺灰實心（IBCS / ISO 24896） | ✅ |
| R-17 | 圖表不放 legend 就能讀懂時，優先 **direct labeling**；legend 僅在 ≥4 series 且無法直標時使用 | ⚠️ |
| R-18 | 格線僅保留一個方向（通常水平），顏色對比 ≤ 1.5:1；座標軸線可省略 | ✅ |
| R-19 | 順序型色階必須**明度單調**；深色主題禁用未截斷的 viridis（低端 #440154 對比僅 1.17:1） | ✅ |
| R-20 | 發散型色階必須**中點為中性色、兩側明度對稱** | ✅ |

---

## 1. 調色盤（實際 hex 值，全部經過驗證）

### 1.1 驗證方法（這是本節的價值所在）

我沒有從網路抄一組色票就交差。我在本機用 matplotlib 3.10.7 寫了一個驗證器（完整程式碼見 §9.1），對每一組候選色盤計算：

1. **WCAG 2.x 相對亮度對比**（對背景色）
2. **Machado et al. (2009) 色覺缺陷模擬矩陣**（severity 1.0）：protanopia / deuteranopia / tritanopia
3. **模擬後兩兩 CIEDE2000 色差**，取最小值當作該色盤的「最弱環節」

判定門檻（我採用的硬標準）：
- 對比 ≥ 3.0:1（WCAG 1.4.11 非文字對比）
- 三種色覺缺陷下最小 ΔE2000 ≥ 12（一般認為 ΔE > 10 才是「明顯不同色」）

### 1.2 最重要的實測結論：8 色類別盤在數學上做不到

我實測了 5 組業界最有名的色盲友善盤，**在白底、8 色、上述門檻下，沒有一組通過**：

| 色盤 | 最低對比(白底) | normal ΔE | deutan ΔE | protan ΔE | tritan ΔE | 結果 |
|---|---|---|---|---|---|---|
| Okabe-Ito 原版（黑改 #333） | **1.32** ❌ | 21.7 | 13.3 | 12.9 | 10.6 | FAIL |
| Okabe-Ito（天藍加深） | 1.32 ❌ | 15.4 | 13.2 | **8.2** ❌ | **7.9** ❌ | FAIL |
| Tableau Color Blind 10（前 8） | 1.75 ❌ | **10.8** ❌ | 10.8 | 10.8 | **7.8** ❌ | FAIL |
| Paul Tol bright(7)+黑 | 1.84 ❌ | 20.5 | **11.3** | 15.9 | **10.1** ❌ | FAIL |
| Paul Tol muted(8) | 1.62 ❌ | 16.1 | 14.9 | **10.4** | 12.3 | FAIL |

我另外跑了一輪 OKLCH 色彩空間上的貪婪 max-min 搜尋（pool 12,587 色，約束對比 ≥3:1），最佳解是 `#0072B2 #C98600 #6D4240 #AE88A3 #B20053 #536304 #7F9873 #3B3B3B` — 顏色又醜又土，而且加入中性灰後 protan ΔE 仍掉到 5.75。

**→ 這產生了 R-01/R-02/R-03：8 色類別盤是一個設計神話。要嘛降到 5–7 色，要嘛加冗餘編碼。**

Okabe-Ito 的真正弱點不是色盲可辨性（deutan 13.3 / protan 12.9 其實很好），而是**白底對比**：黃 `#F0E442` 只有 1.32:1、橘 `#E69F00` 2.25:1、天藍 `#56B4E9` 2.31:1。這三色當「線」在白底上就是看不見。所以我的設計是：**保留 Okabe-Ito 的色相邏輯，但按對比分成兩層 —— 前 5 色可畫線，後 3 色只能填面積。**

### 1.3 類別型（Categorical）— 淺色主題

背景 `#FFFFFF`，卡片面 `#F7F8FA`。

```python
CAT_LIGHT = [
    "#0072B2",  # 1 藍     對比 5.19
    "#D55E00",  # 2 朱橘   對比 3.87
    "#009E73",  # 3 青綠   對比 3.42
    "#CC79A7",  # 4 玫瑰紫 對比 3.06
    "#4D4D4D",  # 5 中性灰 對比 8.45
    # --- 以下僅可用於大面積填色，禁止當線條/小標記 ---
    "#E69F00",  # 6 琥珀   對比 2.25 ❌ 線條不合格
    "#56B4E9",  # 7 天藍   對比 2.31 ❌
    "#F0E442",  # 8 檸黃   對比 1.32 ❌
]
```

**實測 prefix 驗證（白底）**：

| n | 最低對比 | normal | deutan | protan | tritan |
|---|---|---|---|---|---|
| 2 | 3.87 | 49.6 | 57.7 | 49.9 | 56.5 |
| 3 | 3.42 | 38.4 | 21.9 | 20.7 | 13.0 |
| 4 | 3.06 | 37.0 | 14.1 | 12.9 | 13.0 |
| **5** | **3.06** | **24.4** | **13.2** | **12.9** | **13.0** ✅ |
| 6 | 2.25 ❌ | 22.2 | 13.2 | 12.9 | 10.6 |
| 8 | 1.32 ❌ | 21.7 | 13.2 | 12.9 | 10.6 |

n=5 是全綠燈的最大值。這就是 R-01 的來源。

### 1.4 類別型（Categorical）— 深色主題

背景 `#14181F`（刻意不用純黑，減少 halation），卡片面 `#1C222C`。

由 Okabe-Ito 在 OKLCH 空間提亮 ΔL=+0.12、降彩度 ΔC=−0.01 導出：

```python
CAT_DARK = [
    "#4597D4",  # 1 藍     對比 5.62
    "#FB8747",  # 2 朱橘   對比 7.34
    "#54C399",  # 3 青綠   對比 8.17
    "#F0A1CC",  # 4 玫瑰紫 對比 9.05
    "#8A94A3",  # 5 中性灰 對比 5.80
    "#FFC757",  # 6 琥珀   對比 11.49
    "#87DAFF",  # 7 天藍   對比 11.44
    # --- 僅填色 ---
    "#F5E96B",  # 8 檸黃   對比 14.19（但 deutan 下與 #FFC757 撞色 ΔE=5.2）
]
```

**實測 prefix 驗證（深底 #14181F）**：

| n | 最低對比 | normal | deutan | protan | tritan |
|---|---|---|---|---|---|
| 4 | 5.62 | 33.4 | 13.1 | 11.0 | 11.0 |
| 5 | 5.62 | 15.3 | 11.6 | 9.7 | 11.0 |
| 6 | 5.62 | 15.3 | 11.6 | 9.7 | 9.5 |
| **7** | **5.62** | **15.3** | **11.6** | **9.7** | **9.5** ✅（放寬至 ≥9） |
| 8 | 5.62 | 13.6 | **5.2** ❌ | **6.6** ❌ | 9.5 |

深色背景反而能容納更多顏色（因為所有色都提亮後對比充裕）。第 5 槽的灰我試過 `#C7CFDA` / `#9AA5B4` / `#B9C2CE`，deutan 下都會跟玫瑰紫 `#F0A1CC` 撞（ΔE 2.2–6.2）；只有 `#8A94A3` 拉開到 11.6。**這種細節就是必須實測、不能憑感覺的原因。**

### 1.5 順序型（Sequential）

#### 選項 A：viridis（perceptually uniform，學術界標準）
本機 matplotlib 3.10.7 實際取樣：

```python
VIRIDIS_5 = ["#440154", "#3B528B", "#21918C", "#5EC962", "#FDE725"]
VIRIDIS_7 = ["#440154", "#443983", "#31688E", "#21918C", "#35B779", "#90D743", "#FDE725"]
VIRIDIS_9 = ["#440154", "#472D7B", "#3B528B", "#2C728E", "#21918C",
             "#28AE80", "#5EC962", "#ADDC30", "#FDE725"]
```
白底對比（9 階）：15.24 / 10.88 / 7.59 / 5.38 / 3.82 / 2.82 / 2.10 / 1.61 / 1.26 — 高端（黃）在白底幾乎消失。

**深色主題禁用未截斷的 viridis**：`#440154` 對 `#14181F` 對比僅 **1.17:1**。截斷後可用：
```python
VIRIDIS_DARK_7 = ["#433E85", "#32648E", "#25858E", "#21A685", "#52C569", "#A5DB36", "#FDE725"]
# 取樣範圍 [0.18, 1.0]；對深底對比 1.92 → 14.09
```

#### 選項 B：cividis（對 deuteranopia 最佳化，藍→黃單調）
```python
CIVIDIS_5 = ["#00224E", "#434E6C", "#7D7C78", "#BCAE6C", "#FEE838"]
CIVIDIS_7 = ["#00224E", "#2A3F6D", "#575D6D", "#7D7C78", "#A59C74", "#D2C060", "#FEE838"]
CIVIDIS_9 = ["#00224E", "#1A386F", "#434E6C", "#61656F", "#7D7C78",
             "#9B9476", "#BCAE6C", "#DEC958", "#FEE838"]
CIVIDIS_DARK_7 = ["#243C6E", "#4D556C", "#6D6F72", "#8F8A78", "#B3A670", "#D9C55C", "#FEE838"]  # 取樣 [0.15,1.0]
```

#### 選項 C：品牌藍單色階（推薦作為儀表板預設，因為與 CAT slot-1 同色系）
OKLCH 等距生成，明度嚴格單調：

```python
# 淺色主題（白底）；OKLCH L = .96 → .363 線性遞減
SEQ_BLUE_LIGHT = ["#E9F3FF", "#C0D3EB", "#98B3D7", "#7195C3", "#4A76AE", "#225899", "#003984"]
# 白底對比：1.12 / 1.53 / 2.15 / 3.09 / 4.67 / 7.18 / 10.95

# 深色主題（#14181F 底）；L = .22 → .90
SEQ_BLUE_DARK  = ["#091B31", "#213754", "#3A5679", "#5676A0", "#7399C9", "#92BDF4", "#B1E2FF"]
# 深底對比：1.03 / 1.47 / 2.36 / 3.81 / 6.04 / 9.16 / 12.87
```

#### 選項 D：ColorBrewer（8 階，官方 JSON 實抓）
```python
BLUES_8  = ["#F7FBFF","#DEEBF7","#C6DBEF","#9ECAE1","#6BAED6","#4292C6","#2171B5","#084594"]
YLGNBU_8 = ["#FFFFD9","#EDF8B1","#C7E9B4","#7FCDBB","#41B6C4","#1D91C0","#225EA8","#0C2C84"]
```
（來源：`https://colorbrewer2.org/export/colorbrewer.json`，rgb 三元組轉 hex。matplotlib 內建的 `Blues` 9 階取樣為 `#F7FBFF #DEEBF7 #C6DBEF #9DCAE1 #6AAED6 #4191C6 #2070B4 #08509B #08306B`，與官方 8 階為不同插值，兩者不可混用。）

### 1.6 發散型（Diverging）

**核心規則**：發散型不可用紅↔綠（見 R-05 的實測數據）。預設用**橘↔藍**。

```python
# 淺色主題，中點白 #F5F5F5；OKLCH 明度對稱 .552/.654/.760/.864/.970/.864/.760/.656/.551
DIV_LIGHT_9 = ["#B55000", "#C87B43", "#D9A480", "#E8CCBA", "#F5F5F5",
               "#C2D4ED", "#8FB4E4", "#5C93D9", "#2171CC"]

# 深色主題，中點 #292929；深底對比 9.33 … 1.22 … 9.74（對稱）
DIV_DARK_9  = ["#FFA85D", "#CF8652", "#946646", "#5C4738", "#292929",
               "#3E4D60", "#53749D", "#699CDE", "#7EC7FF"]
```

**IBCS 差異圖專用紅↔綠**（只在 IBCS 語意變異圖使用，且必須配 +/− 符號）：
```python
DIV_VARIANCE_LIGHT_9 = ["#BD413F","#D0716B","#E09E97","#ECC9C5","#F5F5F5",
                        "#C1DAC5","#8DC096","#55A568","#008A39"]
DIV_VARIANCE_DARK_9  = ["#FF9B92","#D77D76","#99605B","#5F4441","#292929",
                        "#3D5241","#517E5A","#63AD74","#75DF8F"]
```

**ColorBrewer 發散型（8 階，官方 JSON 實抓）**，若需要學術慣例可用：
```python
RDBU_8  = ["#B2182B","#D6604D","#F4A582","#FDDBC7","#D1E5F0","#92C5DE","#4393C3","#2166AC"]
RDYLBU_8= ["#D73027","#F46D43","#FDAE61","#FEE090","#E0F3F8","#ABD9E9","#74ADD1","#4575B4"]
BRBG_8  = ["#8C510A","#BF812D","#DFC27D","#F6E8C3","#C7EAE5","#80CDC1","#35978F","#01665E"]
PUOR_8  = ["#B35806","#E08214","#FDB863","#FEE0B6","#D8DAEB","#B2ABD2","#8073AC","#542788"]
```

### 1.7 語意色與中性色 token（全部附實測對比）

```python
LIGHT = {
    "bg":          "#FFFFFF",
    "surface":     "#F7F8FA",
    "text":        "#1A1F26",   # 16.56:1  ✅ AAA
    "text_muted":  "#5A6673",   #  5.86:1  ✅ AA
    "grid":        "#E3E7EC",   #  1.24:1  （刻意低，符合 R-18）
    "axis":        "#B4BCC6",   #  1.92:1
    "good":        "#1B7F4B",   #  5.02:1
    "bad":         "#C0392B",   #  5.44:1
    "warn":        "#B26B00",   #  4.20:1
    "neutral_bar": "#7B8794",   #  3.66:1
    "highlight":   "#0072B2",   #  5.19:1
}
DARK = {
    "bg":          "#14181F",
    "surface":     "#1C222C",
    "text":        "#E8EDF3",   # 15.12:1  ✅ AAA
    "text_muted":  "#9AA5B4",   #  7.13:1  ✅ AA
    "grid":        "#2A323C",   #  1.37:1
    "axis":        "#3E4855",   #  1.92:1
    "good":        "#4ADE80",   # 10.21:1
    "bad":         "#F87171",   #  6.43:1
    "warn":        "#FBBF24",   # 10.66:1
    "neutral_bar": "#8A94A3",   #  5.80:1
    "highlight":   "#4597D4",   #  5.62:1
}
```

**紅綠語意色的實測可辨性（R-05 的證據）**：

| 配對 | normal ΔE | deutan ΔE | protan ΔE |
|---|---|---|---|
| 淺色 good/bad `#1B7F4B` vs `#C0392B` | 60.4 | **10.3** | 14.2 |
| 深色 good/bad `#4ADE80` vs `#F87171` | 71.5 | **7.5** | 25.2 |
| 對照：藍/橘 `#0072B2` vs `#D55E00` | 49.6 | **57.7** | 49.9 |

深色主題下綠紅在 deuteranopia 幾乎同色（ΔE 7.5）。**IBCS 的「綠好紅壞」如果不加符號，對 ~8% 男性讀者是失效的。** 這條必須寫死進 Skill。

---

## 2. 繁體中文字型

### 2.1 本機實際狀況（PowerShell + matplotlib.font_manager 實測）

`C:\Windows\Fonts` 已安裝（全機安裝，可變字型）：
```
NotoSansTC-VF.ttf    11,942,912 bytes
NotoSansHK-VF.ttf    11,906,752 bytes
NotoSerifTC-VF.ttf   16,855,236 bytes
NotoSerifHK-VF.ttf   16,831,380 bytes
```
另有系統內建：Microsoft JhengHei（msjhl.ttc 290 / msjh.ttc 400 / msjhbd.ttc 700 三個實體字重）、MingLiU / PMingLiU / MingLiU-ExtB、DFKai-SB、Microsoft YaHei、MS Gothic、Yu Gothic。
`%LOCALAPPDATA%\Microsoft\Windows\Fonts`（單一使用者字型目錄）**不存在**，HKCU 字型登錄檔也是空的 → 目前所有字型都是全機安裝。

### 2.2 可商用、可嵌入的繁中字型清單

| 字型 | 授權 | 來源（實抓） | 觀測到的最後活躍 | 可嵌入 PDF/PPT | 備註 |
|---|---|---|---|---|---|
| **Noto Sans TC / Noto Serif TC** | SIL OFL 1.1 | `github.com/notofonts/noto-cjk`（4.0k★，未 archived）；Google Fonts metadata 顯示 `"license":"ofl"`、wght 100–900 可變軸 | **repo 最後 commit 2024-09-19「Be more MS-friendly」**；release：Noto Serif CJK 2.003 (2024-07-30)、Noto Sans CJK 2.004 (2023-11-30) | ✅ | 本機已裝可變版。靜態字重需另抓 subset OTF zip（見 2.4） |
| **思源黑體 Source Han Sans** | SIL OFL 1.1 | `github.com/adobe-fonts/source-han-sans` | **最新 release「Fonts Version 2.005R (OTF, OTC, Super OTC, Subset OTF, Variable OTF/TTF/WOFF2)」updated 2025-06-25** | ✅ | Noto Sans CJK 的上游；字形同源 |
| **思源宋體 Source Han Serif** | SIL OFL 1.1 | `github.com/adobe-fonts/source-han-serif` | **最新 release「Fonts Version 2.003」updated 2024-07-30** | ✅ | ⚠️ 數字非等寬，見 R-11 |
| **台北黑體 Taipei Sans TC Beta** | SIL OFL 1.1（官網原文：「台北黑體亦基於 SIL Open Font License 1.1 授權為免費、公開的字型製品。」） | 官方＝翰字鑄造 JT Foundry（Google Sites）；GitHub 鏡像 `github.com/VdustR/taipei-sans-tc`（37★，repo 本身 MIT，未 archived） | **未能查證**（見 §12） | ✅ | 基於思源黑體改作，印刷體風格；官網明訂不得「直接更改字型名稱並宣稱為自身之作品」 |
| **jf open 粉圓 (open-huninn)** | SIL OFL 1.1，**無需標註出處** | `github.com/justfont/open-huninn-font`（1.3k★，未 archived） | **最新 release v2.1 (2024-09-19)；最後 commit 2025-06-17「Update README.md」** | ✅ | 衍生自 Kosugi Maru（日文）+ Varela Round（拉丁）。含注音、台語/閩南語音標。**圓體，不適合正式商業報告內文，只適合標題或親和向 deck** |
| **Microsoft JhengHei 微軟正黑體** | Windows 隨附授權（非 OFL） | 系統內建 | n/a | ⚠️ 授權限制 | 有三個實體字重。**不可自由嵌入/散布** → 只能用於本機產出，不可打包進交付檔的字型嵌入 |

### 2.3 三個必須寫死的實測發現

#### (A) Noto Serif TC 的數字不是等寬 —— 禁用於數字欄

用 fontTools 直接讀 `hmtx` 表，量測 0–9 的 advance width（單位 em）：

| 字型 | 數字寬度種類 | 等寬？ | `,` | `.` | `-` | `%` |
|---|---|---|---|---|---|---|
| Noto Sans TC (VF) | `{0.521}` | ✅ | 0.231 | 0.231 | 0.324 | 0.880 |
| **Noto Serif TC (VF)** | `{0.473, 0.533, 0.540, 0.542, 0.544, 0.548}` | ❌ **6 種寬度** | 0.323 | 0.323 | 0.336 | 0.906 |
| Microsoft JhengHei | `{0.5796}` | ✅ | 0.2305 | 0.2305 | 0.4316 | 0.880 |
| Segoe UI | `{0.5391}` | ✅ | 0.2168 | 0.2168 | 0.3999 | 0.818 |
| Arial | `{0.5562}` | ✅ | 0.2778 | 0.2778 | 0.333 | 0.889 |
| Consolas | `{0.5498}` | ✅（全等寬） | 0.5498 | 0.5498 | 0.5498 | 0.5498 |

#### (B) `font-feature-settings: "tnum"` 對 Noto 是無效的

用 fontTools 列舉 GSUB/GPOS 的 FeatureRecord：

| 字型 | 有的數字相關 feature |
|---|---|
| Noto Sans TC (VF) | **（空）** |
| Noto Serif TC (VF) | **（空）** |
| Microsoft JhengHei | **（空）** |
| Segoe UI | `tnum, lnum, pnum, onum, case, ss01` |
| Arial | `tnum, lnum, pnum, onum, ss01` |
| Consolas | `onum, case, ss01`（本身即等寬） |

**結論**：在 HTML 報告裡寫 `font-variant-numeric: tabular-nums` 對 Noto Sans TC 是「無害但無效」的宣告 —— 幸好它預設就已經等寬（0.521 em）。但對 Noto Serif TC 則是「宣告了也救不回來」。

#### (C) matplotlib 對可變字型不做 instancing —— 中文粗體會靜默失效

`font_manager` 只把 `NotoSansTC-VF.ttf` 註冊為 **weight=100** 一筆；`findfont(weight='bold')`、`weight=700`、`weight=500` 全部回傳同一個檔案。

實際渲染「營收 2026」22pt 後計算墨水像素：

| 字型 | normal 墨水 | bold 墨水 | 兩張圖是否完全相同 | 比值 |
|---|---|---|---|---|
| **Noto Sans TC** | 2,121 | 2,121 | **True（逐位元組相同）** | 1.000 |
| Microsoft JhengHei | 3,633 | 4,479 | False | 1.233 |

**→ R-12。** 解法二選一：
1. 從 `github.com/googlefonts/noto-cjk/releases/download/Sans2.004/19_NotoSansTC.zip` 抓 Taiwan subset OTF（README 原文：「Each ZIP file contains seven font resources, one for each of the seven weights.」，檔名 `NotoSansTC-{Thin,ExtraLight,Light,Regular,Medium,SemiBold,Bold}.otf`）並安裝靜態字重；
2. 或 matplotlib 圖表內的中文粗體改用 Microsoft JhengHei（僅本機產出用，不嵌入）。

正面驗證：用 `font.sans-serif = ['Noto Sans TC', 'Microsoft JhengHei', 'DejaVu Sans']` + `axes.unicode_minus = False` 渲染「會員回購率 vs 廣告 ROAS」「月份 (2026 Q1)」「變化 %」，**無任何 missing glyph warning**，中英數混排正常。

### 2.4 Windows 11 安裝方式（本機驗證的路徑）

| 方式 | 路徑 | 需要管理員 | 適用 |
|---|---|---|---|
| 全機安裝 | `C:\Windows\Fonts` | ✅ 是 | 本機已用此法安裝 Noto（4 個 VF 檔） |
| 單一使用者安裝 | `%LOCALAPPDATA%\Microsoft\Windows\Fonts` + 寫入 `HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts` | ❌ 否 | 本機此目錄目前**不存在**；適合無管理員權限的環境 |

實務上：檔案總管選取 `.otf`/`.ttf` → 右鍵 →「安裝」（單一使用者）或「為所有使用者安裝」（需 UAC）。安裝後 **matplotlib 必須清快取**才看得到新字型：

```powershell
Remove-Item "$env:USERPROFILE\.matplotlib\fontlist-*.json" -Force -ErrorAction SilentlyContinue
```

matplotlib 設定目錄（本機實測）：`C:\Users\User\.matplotlib`
自訂 style 目錄（本機實測**尚未建立**）：`C:\Users\User\.matplotlib\stylelib`
內建 matplotlibrc：`...\site-packages\matplotlib\mpl-data\matplotlibrc`

### 2.5 Fallback 順序（可直接抄）

```python
# matplotlib（本機產出，允許用系統字型）
FONT_STACK_MPL_SANS = [
    "Noto Sans TC",        # 主：OFL、數字等寬、已安裝
    "Microsoft JhengHei",  # 備：有真粗體
    "Noto Sans HK",        # 備：港標字形
    "Segoe UI",            # 拉丁/數字 fallback（有 tnum）
    "DejaVu Sans",         # matplotlib 內建保底
]
FONT_STACK_MPL_MONO = ["Consolas", "DejaVu Sans Mono"]
```

```css
/* HTML 報告 / 儀表板：先西文後中文，讓拉丁字母用西文字型 */
--font-sans: "Segoe UI", "Inter", system-ui,
             "Noto Sans TC", "Microsoft JhengHei", "PingFang TC", sans-serif;
--font-num:  "Segoe UI", "Noto Sans TC", "Consolas", monospace; /* 數字欄 */
--font-mono: "Cascadia Mono", "Consolas", "Noto Sans TC", monospace;
/* 明確不放 Noto Serif TC 於任何含數字的 stack —— 見 R-11 */
```

### 2.6 中英數混排的字級與行高

繁中方塊字的視覺重量高於拉丁小寫，同 px 下中文「看起來比較大、比較擠」。

| 用途 | font-size | line-height | letter-spacing | 說明 |
|---|---|---|---|---|
| 報告內文 | 16–17 px | **1.75**（≈28–30 px） | 0.02em | 中文內文行高需比英文高；查得的繁中排版慣例落在 1.5–1.8，取偏高值 |
| 小字註解 / 來源 | 13 px | 1.6 | 0.02em | |
| 表格內文 | 14 px | 1.45 | 0 | 表格行高刻意壓低以提升資訊密度（IBCS CONDENSE） |
| 表格數字 | 14 px | 1.45 | **0**（數字絕不加字距） | |
| 圖表刻度標籤 | 11–12 px | 1.2 | 0 | |
| 圖表軸標題 | 12–13 px | 1.3 | 0 | |
| 圖表標題（結論句） | 16–18 px / 600 | 1.4 | 0 | |
| KPI 主數字 | 32–40 px / 600 | 1.1 | −0.01em | 大字負字距 |
| KPI 標籤 | 13 px / 400 | 1.3 | 0.03em | |
| 投影片標題 | 28–32 pt | 1.25 | 0 | |
| 投影片內文 | 18–20 pt | 1.5 | 0.02em | |

補充規則：
- 中英數之間**不手動加空格**，改用 CSS `text-autospace`（若不支援則接受）或直接接排；不要用全形空格。
- 數字與單位之間用**半形空格**：`12.5 %`→ 業界慣例是 `12.5%` 不加空格，但 `120 萬`、`3 個月` 要加。統一規則：**中文量詞前加半形空格，符號（% $ ）不加。**
- `axes.unicode_minus = False` 必設，否則 matplotlib 用 U+2212 而多數中文字型缺這個 glyph。
- Noto Sans TC 的 Google Fonts metadata 標示 `lineHeight: 1.448`（全字重相同）—— 這是字型自帶的 default line gap，CSS 設 1.75 是在此之上再加。

---

## 3. 圖表選型決策表

分類法採用 **FT Visual Vocabulary 的九大資料關係**（`github.com/Financial-Times/chart-doctor`，3.3k★；README 實抓出：Deviation / Correlation / Ranking / Distribution / Change over Time / Magnitude / Part-to-Whole / Spatial / Flow）。該 repo 有**繁體中文版 PDF**，可直接給團隊當共同語言。

### 3.1 主決策表（含四種行銷資料的對照）

| 你要回答的問題 | 資料形狀 | 首選 | 次選 | 禁用 |
|---|---|---|---|---|
| 隨時間怎麼變？ | 1 類別 × 連續時間 | 折線圖 | 面積圖（僅單一 series） | 直條圖（時點多時）、圓餅 |
| 多個 series 隨時間怎麼變？ | ≤5 類別 × 時間 | 多線折線 + direct label | small multiples | 堆疊折線、雙 Y 軸 |
| >5 類別隨時間？ | 多類別 × 時間 | **small multiples**（每格一線，灰底全體） | Top-5 + 「其他」 | 一張圖畫 12 條線 |
| 誰大誰小？（排名） | 類別 × 1 數值 | **水平長條**（依值排序） | lollipop、dot plot | 圓餅、雷達 |
| 部分佔全體多少？ | 1 時點 × ≤5 類別 | 堆疊水平長條（100%） | 圓餅（僅 ≤5 且無需精讀） | 甜甜圈 + 中間放數字、>5 類的圓餅 |
| 部分佔全體 × 時間 | 類別 × 時間 | 100% 堆疊直條 | 堆疊面積圖 | 圓餅小倍數 |
| 兩個變數有沒有關係？ | 2 連續 | 散佈圖 + 回歸線 + CI 帶 | hexbin（n>5000） | 3D 散佈 |
| 三個變數？ | 3 連續 | 泡泡圖（第三變數→面積，非半徑） | 散佈 + 顏色（順序型色階） | 3D |
| 分布長什麼樣？ | 1 連續 | 直方圖（標 bin 寬） | density plot | 只給平均值 |
| 多組分布比較 | 類別 × 連續 | **箱型圖 + jitter 原始點**（n<200 時） | violin（n 大） | 只畫 bar + error bar（dynamite plot） |
| 與目標/去年差多少？ | 類別 × 差異值 | **發散長條**（0 軸置中） | 瀑布圖（拆解貢獻） | 雙 Y 軸疊圖 |
| 漏斗轉換 | 有序階段 | 水平長條 + 階段間轉換率標註 | 瀑布圖 | 立體漏斗圖形 |
| 兩維交叉密度 | 2 類別 × 1 數值 | heatmap（順序型色階 + 數值標註） | 馬賽克圖 | 3D surface |
| 世代/留存 | cohort × period | **三角 heatmap**（列＝cohort，行＝期數） | 留存曲線多線 | 表格塞滿數字不上色 |
| 流向 | 節點 → 節點 | Sankey（節點 ≤10） | chord | 節點 >15 的 Sankey |
| 地理分布 | 行政區 × 數值 | 面量圖（**必須用率不用絕對值**） | 比例符號圖 | 用絕對值的面量圖 |
| 迴歸/ANOVA 結果 | 係數 + CI | **coefficient plot**（點 + 95% CI，0 線標出） | forest plot | 只貼 summary 文字 |
| 殘差診斷 | 擬合值 × 殘差 | 2×2 診斷面板（Residual vs Fitted / Q-Q / Scale-Location / Residual vs Leverage + Cook's D 等高線） | — | 只看 R² |
| 事後檢定 | 組別兩兩比較 | 差異 + CI 的 forest plot | compact letter display 疊在箱型圖上 | 表格塞 p 值矩陣 |

### 3.2 四種行銷資料型態的預設圖表

| 資料型態 | 招牌圖 | 色盤 |
|---|---|---|
| 會員 / CRM 交易 | RFM heatmap、cohort 留存三角、LTV 累積曲線、分群雷達**改用** parallel coordinates 或分群 × 指標 heatmap | 順序型（RFM/留存）、類別型 ≤5（分群） |
| 電商 / 網站行為 | 漏斗水平長條、流量來源 100% 堆疊直條（時間）、頁面停留分布箱型圖、Sankey（路徑，節點 ≤10） | 類別型 |
| 廣告投放成效 | ROAS 散佈（花費 × 營收，泡泡＝曝光）、渠道 × 週 heatmap、預算配置瀑布圖、成效 vs 目標發散長條 | 類別型 + 發散型 |
| 實體零售 POS / 門市 | 門市排名水平長條、時段 × 星期 heatmap、同店成長率發散長條、地理面量圖（**用坪效/客單價等率值**） | 發散型 + 順序型 |

### 3.3 明確禁用規則（可寫成 lint）

| 規則 | 門檻 | 理由 |
|---|---|---|
| **圓餅 / 甜甜圈** | 類別 **> 5** 一律禁；即使 ≤5，若需要精讀數值也禁；**任何時間維度絕對禁**；禁「多個小圓餅比較」 | 角度判讀誤差大；IBCS Bottom-1 明列 pie chart 應避免 |
| **雙 Y 軸** | **預設禁用**。唯一例外：同一物理量的兩種單位且為固定線性換算（°C/°F、TWD/USD 固定匯率） | 兩軸縮放可任意調整 → 可製造任意相關性；替代方案：small multiples、或都轉成指數化（基期=100）畫在同一軸 |
| **雷達 / 蜘蛛圖** | 全禁 | 面積隨軸序改變；IBCS Bottom-1 明列。替代：parallel coordinates、分組長條、heatmap |
| **3D 任何圖表** | 全禁 | |
| **長條 Y 軸截斷** | 全禁（bar/column 必須 0 起） | 長度編碼的前提是從 0 |
| **折線 Y 軸截斷** | 允許，但必須：(a) 軸標明確、(b) 不使用 fill_between 到軸底 | |
| **堆疊長條做「比較個別類別」** | 禁（除最底層外無法比較） | 只有「總和」與「最底層」可讀；要比個別類別改用分組長條或 small multiples |
| **面積圖多於 1 個 series** | 禁（改堆疊面積或多線折線） | 重疊半透明面積會產生第三種顏色 |
| **漸層填色、陰影、圓角柱、外框光暈** | 全禁 | IBCS Bottom-3 clutter |
| **樣本數 < 20 畫 violin / density** | 禁，改 dot plot + 中位數線 | 核密度在小樣本上是幻覺 |
| **面量圖用絕對值** | 禁，必須用率 | 面積大的區域必然數字大 |
| **超過 8 條線 / 12 個類別擠一張圖** | 禁 | 見 R-01/R-02 |
| **鋸齒狀 sparkline 沒有基準線** | 禁；sparkline 必須標最後值與 min/max | IBCS Bottom-1 對 sparkline 有保留意見，我方採「可用但必須有基準與端點標註」 |
| **散佈圖畫回歸線但不畫 CI 帶** | 禁 | 統計層要求（本專案有 lm/glm） |
| **顏色用來裝飾** | 禁 | IBCS Bottom-3 原文：「IBCS suggests to use color for a highlighting purposes only.」 |

---

## 4. 表格排版

### 4.1 數字呈現硬規則

| 項目 | 規則 |
|---|---|
| 對齊 | 數字欄 **右對齊**；文字欄左對齊；標頭對齊方式**跟隨該欄內容** |
| 等寬數字 | 必須。Noto Sans TC 預設即等寬（0.521 em，實測）；HTML 仍寫 `font-variant-numeric: tabular-nums` 作為對其他字型的保險 |
| 千分位 | ≥ 4 位數必加 `,`；**年份不加**（2026 不是 2,026）；ID 欄不加 |
| 小數位數 | **同欄固定**。金額 0 位（元）或 1 位（萬元/千元）；比率 1 位；轉換率 2 位；p 值 3 位（<0.001 顯示 `<0.001`）；係數 3 位 |
| 單位 | 放在**欄標頭**，不放每一格（`營收 (千元)`，不是每格 `1,234 千元`） |
| 負數 | 用 `−1,234`（U+2212）或 `(1,234)`，**擇一貫徹**；財務報表用括號，分析報告用負號 |
| 零與缺值 | `0` 表示真的是零；缺值用 `—`（em dash）不留空白，不用 `0`、`N/A`、`NaN` |
| 百分比變化 | `+12.3%` / `−4.5%`（正號必須顯示，符合 R-05 的冗餘編碼） |
| 極大數字 | 統一縮放到欄層級（全欄改「千元」），**不要每格自適應**（1.2M / 340K 混排禁止） |
| 排序 | 預設依主要數值欄降序；若有自然順序（時間、階段）則依自然順序 |

### 4.2 視覺結構

| 項目 | 規則 |
|---|---|
| 直線 | **禁用垂直分隔線**；水平線僅三條：表頭上、表頭下、表尾（Tufte / booktabs 風格） |
| 斑馬紋 | 欄數 ≤ 6 不用；> 6 或列數 > 15 才用，且顏色極淡（淺色 `#F7F8FA`、深色 `#1C222C`） |
| 列高 | 內文 14px / line-height 1.45 → 列高約 32–36px（含 padding 8px 上下） |
| 欄距 | 左右 padding 12px；第一欄與最後一欄外緣 padding 0（與版心對齊） |
| 表頭 | 600 字重、`text_muted` 顏色、字級同內文或小 1px、**不用全大寫**（中文無意義） |
| 群組表頭 | 跨欄群組標題下加短水平線僅覆蓋所屬欄 |
| 合計列 | 上方加分隔線、字重 600、**不加底色** |
| 行內圖形 | 允許 sparkline 欄、bar-in-cell（長度∝數值，單色 `highlight`，寬度固定不隨欄寬變） |
| 熱度上色 | 允許，但用順序型色階且必須保證文字對比 ≥4.5:1（深色格子上的字要翻白） |
| 條件標色 | 只標「需要行動」的格，不要整表變彩虹（IBCS Bottom-3） |

### 4.3 跨頁 / 長表

| 場景 | 規則 |
|---|---|
| HTML 單檔報告 | 表頭 `position: sticky; top: 0`；容器 `overflow-x: auto`；列數 > 50 時預設收合只顯示前 20 列 + 「展開全部」 |
| HTML 列印 / PDF | `thead { display: table-header-group; }` 使表頭每頁重複；`tr { break-inside: avoid; }`；`tfoot { display: table-footer-group; }` |
| Word / PDF 交付 | 表頭列設「跨頁重複標題列」；續頁表頭右上標「（續）」 |
| 投影片 | **單張投影片表格上限 7 列 × 5 欄**；超過改成圖或拆頁 |
| Excel 交付 | 凍結窗格在表頭下方（`freeze_panes="A2"`）；設定列印標題列 `print_title_rows='1:1'`；數字用 Excel 原生格式碼而非字串 |

### 4.4 Excel 數字格式碼（openpyxl 3.1.5 / XlsxWriter 3.2.9 皆已安裝）

```python
NUMFMT = {
    "int":       '#,##0',
    "money":     '#,##0;[Red]-#,##0',
    "money_k":   '#,##0,"K";[Red]-#,##0,"K"',
    "pct1":      '0.0%;[Red]-0.0%',
    "pct_delta": '+0.0%;-0.0%;0.0%',      # 正號強制顯示（R-05 冗餘編碼）
    "ratio2":    '0.00',
    "coef3":     '0.000',
    "pval":      '[<0.001]"<0.001";0.000',
    "date":      'yyyy-mm-dd',
    "missing":   '#,##0;-#,##0;"—";@',
}
```
規則：**Excel 交付檔的數字必須是數值型別（含格式碼），不可寫成已格式化的字串** —— 否則使用者無法再做樞紐分析。

---

## 5. 儀表板資訊層級

### 5.1 四層結構（KPI → 趨勢 → 拆解 → 明細）

固定 **12 欄網格**，gutter 16px，最大版心 1440px，卡片圓角 8px、無陰影（用 1px `grid` 色邊框）。

| 層 | 位置 | 網格 | 高度 | 內容 | 限制 |
|---|---|---|---|---|---|
| **L0 標題列** | 頂部 | 12 欄 | 64px | 報告名稱、資料期間、最後更新時間、全域篩選器（≤3 個） | 篩選器 >3 個移到側欄 |
| **L1 KPI** | 第一屏上方 | 每卡 **3 欄**（一列 4 張），最多 **8 張**（兩列） | 每卡 120px 固定 | 指標名 / 主數字 / vs 上期變化（+−% 帶符號與色）/ 40px sparkline | 主數字 32–40px；卡內不放圓餅；變化必須同時有符號與顏色 |
| **L2 趨勢** | 第一屏下方 | 主圖 **8 欄** + 輔助 **4 欄**；或並列兩張各 6 欄 | 280–320px | 主指標時間序列（折線）+ 目標線 / 去年虛線 | 一張圖 ≤5 條線；**必須在第一屏可見** |
| **L3 拆解** | 第二屏 | 每張 **4 欄**（一列 3 張）或 **6 欄**（一列 2 張） | 240–280px | 依渠道 / 商品 / 門市 / 客群拆解：排序長條、發散長條、heatmap、瀑布 | 每張圖只回答一個問題；圖標題是結論句 |
| **L4 明細** | 最後一屏 | 12 欄 | 自適應，最高 600px 後內捲 | 資料表（含匯出鈕） | 預設收合；欄數 >10 提供欄位選擇器 |

### 5.2 網格與間距 token

```css
--grid-cols: 12;
--gutter: 16px;
--container-max: 1440px;
--space-1: 4px;  --space-2: 8px;   --space-3: 12px;
--space-4: 16px; --space-6: 24px;  --space-8: 32px;  --space-12: 48px;
--card-radius: 8px;
--card-border: 1px solid var(--grid);
--section-gap: 32px;    /* 層與層之間 */
--card-gap: 16px;       /* 同層卡片之間 */
```

RWD 斷點：`≥1280px` 12 欄 → `768–1279px` 6 欄（KPI 每卡 3 欄 = 一列 2 張）→ `<768px` 1 欄（全部堆疊，L4 明細改為卡片列表）。

### 5.3 資訊層級的排版規則

| 規則 | 內容 |
|---|---|
| 閱讀順序 | Z 型：左上最重要。**最重要的 KPI 放最左上，不要按字母序排** |
| 一屏原則 | L1 + L2 必須在 1440×900 的第一屏內完整顯示，不需捲動 |
| 顏色預算 | 整個儀表板的**強調色只有一個**（`highlight`）。其餘用中性灰。類別色只在需要區分 series 的圖裡出現 |
| 標題 | 每張圖的標題是**結論句**：「北區門市 Q2 客單價下滑 8%，主因週間時段」而非「門市客單價趨勢」 |
| 註腳 | 每張圖右下角小字：資料來源、n、計算口徑。字級 11px、`text_muted` |
| 空狀態 | 篩選後無資料時顯示明確訊息 + 建議放寬條件，不要顯示空白圖 |
| 載入 | 用 skeleton（灰塊），不要 spinner；避免版面跳動 |
| 互動 | hover 顯示 tooltip（含精確值與單位）；點擊做 cross-filter；所有互動狀態必須可用鍵盤觸發 |

---

## 6. 商業報告標準：IBCS 與 ISO 24896

### 6.1 重大更新（2026 年必須知道）

**IBCS 的表示法已經在 2026-06-11 成為國際標準 ISO 24896「Notation for business reporting」。**（ibcs.com/iso-24896/ 實抓）

- ISO 24896 原文範圍：「establishes a consistent notation for business communication with written reports, live presentations, and analytic dashboards」，規範「labelling of content, the layout of charts and tables, the representation of data values, as well as the visualization of their characteristics」。
- 基礎來源：「based on suggestions for consistent business reporting notation developed by the International Business Communication Standards (IBCS) Association (**mainly the UNIFY and CHECK parts of IBCS' SUCCESS formula**)」。
- IBCS Standards 2.0 同日發布並「Full alignment of the Notation part with the international standard ISO 24896」，且已「restructured into separate Notation and Composition parts」。

**對本專案的意義**：可以在報告方法論裡寫「本報告表示法依循 ISO 24896」，這比寫「依循 IBCS」在對外溝通上更有份量。

### 6.2 SUCCESS 七大規則群（Wikipedia 條目實抓）

| 字母 | 規則群 | 類型 | 一句話 |
|---|---|---|---|
| **S** | SAY | Conceptual | 用適當的敘事線傳達訊息 |
| **U** | UNIFY | **Semantic** | 統一表示法（IBCS Notation）→ **這部分已成 ISO 24896** |
| **C** | CONDENSE | Perceptual | 提高資訊密度 |
| **C** | CHECK | Perceptual | 確保視覺完整性 → **這部分已成 ISO 24896** |
| **E** | EXPRESS | Perceptual | 選擇正確的視覺化 |
| **S** | SIMPLIFY | Perceptual | 去除雜訊 |
| **S** | STRUCTURE | Conceptual | 有效組織內容 |

版本沿革（同條目）：1.0 於 2015-06-18 阿姆斯特丹大會通過、1.1 (2017)、1.2 (2021)、2.0 (2026-06-11)。

### 6.3 可以直接採用的具體規則（ibcs.com Top/Bottom 5 頁面實抓）

**採用（直接寫進 Skill）**：

| IBCS 條目 | 原文 | 我方落地規則 |
|---|---|---|
| Top 1 — Title Concept | 「Unified and well-structured titles will help business executives making correct decisions.」 | 每張圖標題三段式：**〔對象〕〔指標〕〔結論〕**；副標放期間與單位 |
| Top 2 — Time and Structure | 用 lines / bars / columns 分別對應時間序列與結構比較 | **時間序列→直條或折線（橫軸為時間）；結構比較→水平長條**。這是一條可機械檢查的規則：橫軸若非時間，一律用水平長條 |
| Top 3 — Scenarios | 「Solid fill for actual data, outlined columns or bars for plan figures, and hatched fill for forecast.」 | 見 6.4 情境語意表（R-16） |
| Top 4 — Variances | 「IBCS suggests using red and green color for variances only. Green is good, and red is bad.」 | 採用，**但強制加符號**（R-05）。且紅綠只出現在差異圖，絕不當類別色 |
| Top 5 — Scaling | 「Consistent scaling is key for proper visual perception」 | 同一報告中同一指標的 y 軸上下限一致；small multiples 必須共用軸（R-15） |
| Bottom 1 — Wrong Visualization | 避免 pie / radar / sparkline，bar 較適合結構比較 | 圓餅、雷達全禁；sparkline 我方**有條件採用**（必須有基準線與端點標註）— 這是我方與 IBCS 的明確分歧，已記錄 |
| Bottom 3 — Cluttered Layout | 「IBCS suggests to use color for a highlighting purposes only.」 | 顏色預算規則（§5.3） |
| Bottom 4 — Low Information Density | 單頁最大化脈絡，不要散落多頁 | 儀表板一屏原則、表格不分頁 |
| Bottom 5 — Missing Message | 圖必須「support, and ideally prove, the message」 | 每張圖都要能回答「所以呢？」，否則刪掉 |

### 6.4 情境語意表（IBCS Notation / ISO 24896，R-16）

| 情境 | 縮寫 | 填色 | 建議 hex（淺色主題） |
|---|---|---|---|
| 實際 | **AC** | 實心深色 | `#4D4D4D`（或 `highlight` `#0072B2`） |
| 計畫 | **PL** | 白底 + 深色外框（outlined） | fill `#FFFFFF`, edge `#4D4D4D`, lw 1.2 |
| 預算 | **BU** | 同 PL | |
| 預測 | **FC** | 斜線填（hatch `///`） | fill `#FFFFFF`, hatch `///`, edge `#4D4D4D` |
| 去年 | **PY** | 淺灰實心 | `#B4BCC6` |
| 差異（好） | ΔAC/PY | 綠 + `+` 號 | `#1B7F4B` |
| 差異（壞） | ΔAC/PY | 紅 + `−` 號 | `#C0392B` |

matplotlib 實作：
```python
SCENARIO = {
    "AC": dict(facecolor="#4D4D4D", edgecolor="#4D4D4D", hatch=None,  linewidth=0),
    "PL": dict(facecolor="none",    edgecolor="#4D4D4D", hatch=None,  linewidth=1.2),
    "BU": dict(facecolor="none",    edgecolor="#4D4D4D", hatch=None,  linewidth=1.2),
    "FC": dict(facecolor="none",    edgecolor="#4D4D4D", hatch="///", linewidth=1.0),
    "PY": dict(facecolor="#B4BCC6", edgecolor="#B4BCC6", hatch=None,  linewidth=0),
}
ax.bar(x, y, **SCENARIO["FC"])
```
深色主題把 `#4D4D4D` → `#E8EDF3`、`#B4BCC6` → `#3E4855`、`facecolor="none"` 不變。

---

## 7. Nightingale / Data Visualization Society 有什麼可引用

**結論：DVS / Nightingale 沒有可直接引用的規範性標準。** 這點必須誠實說明。

- Nightingale（`nightingaledvs.com`，實抓）自述為「The Journal of the Data Visualization Society」，由 DVS（501(c)(3) 非營利）出版；內容是「personal stories to exploratory research to interviews with leaders in the community, data ethics, and best practices」——**是散文、案例、訪談，不是 normative standard**。網站上最新文章日期為 2026 年 7 月，出版活躍。
- DVS 官網有 `#style-guides` Slack 頻道與資源列表，但那是社群資源匯集，不是標準。

**可引用的替代品**（比 Nightingale 更具體）：

| 來源 | 性質 | 實抓到的內容 |
|---|---|---|
| **datavizstyleguide.com**（DVS 共同創辦人 Amy Cesal） | style guide 的「目錄模板」 | Foundations 分為 **Color**（Categorical / Sequential / Diverging / Other color considerations）、**Typography**、**Size and dimensions**、**Medium**；並建議先定 Guiding Principles（mission, brand, equity, accessibility）。「Visualization parts」標註 coming soon（**未完成**） |
| **Royal Statistical Society《Best Practices for Data Visualisation》** | 有程式碼的實務指南 | `github.com/royal-statistical-society/datavisguide`，167★，未 archived，**授權 CC BY 4.0（原文：「licensed under a Creative Commons Attribution 4.0 (CC BY 4.0) International licence, meaning it can be used and adapted for any purpose, provided attribution is given」）**。→ **可合法改作成內部規範**。最後 commit **2024-11-16「Render PDF」** |
| **FT Visual Vocabulary** | 圖表選型分類法 | `github.com/Financial-Times/chart-doctor`，3.3k★，九大關係分類，**有繁體中文版 PDF**。最後 commit **2024-03-12「Update Visual-vocabulary-de.pdf」**（已兩年多無更新，但分類法本身不需更新） |
| **Urban Institute Data Viz Style Guide** | 完整機構級 style guide | `UrbanInstitute/urbnthemes`（88★，R 套件）連結到 `UrbanInstitute.github.io/r-at-urban/graphics-guide.html` |

我方的 style guide 目錄應照 datavizstyleguide.com 的 Foundations 骨架，內容用 RSS 指南（CC BY 4.0，可改作）+ FT 分類法 + ISO 24896 表示法填充。

---

## 8. 落地：把規範做成可 import 的 theme 檔

### 8.1 matplotlib

**機制（本機實測）**：`plt.style.use()` 接受 (a) 內建名稱、(b) `.mplstyle` 檔案路徑、(c) 放在 `matplotlib.get_configdir()/stylelib/` 下的自訂名稱、(d) dict、(e) 上述的 list（後者覆蓋前者）。

本機路徑：`matplotlib.get_configdir()` → `C:\Users\User\.matplotlib`，因此自訂 style 目錄為 `C:\Users\User\.matplotlib\stylelib\`（**目前尚未建立**）。

**建議做法：不要依賴 stylelib 全域安裝，改成套件內附檔 + 一個 `apply()` 函式**（可版控、可隨專案走）。

`baozi_viz/themes/baozi_light.mplstyle`：
```ini
# ---- Baozi Marketing Analytics — Light ----
figure.figsize:        8.0, 4.5
figure.dpi:            110
savefig.dpi:           200
figure.facecolor:      FFFFFF
axes.facecolor:        FFFFFF
savefig.facecolor:     FFFFFF
savefig.bbox:          tight
savefig.pad_inches:    0.12

font.family:           sans-serif
font.sans-serif:       Noto Sans TC, Microsoft JhengHei, Noto Sans HK, Segoe UI, DejaVu Sans
font.size:             11
axes.titlesize:        13
axes.labelsize:        11.5
xtick.labelsize:       10
ytick.labelsize:       10
legend.fontsize:       10
figure.titlesize:      15
axes.unicode_minus:    False

text.color:            1A1F26
axes.labelcolor:       5A6673
xtick.color:           5A6673
ytick.color:           5A6673
axes.edgecolor:        B4BCC6
axes.titlecolor:       1A1F26
axes.titlelocation:    left
axes.titlepad:         12
axes.labelpad:         6

axes.spines.top:       False
axes.spines.right:     False
axes.spines.left:      False
axes.spines.bottom:    True
axes.linewidth:        0.8

axes.grid:             True
axes.grid.axis:        y
grid.color:            E3E7EC
grid.linewidth:        0.8
grid.alpha:            1.0
axes.axisbelow:        True

# 只放 5 個線條安全色（R-01）；6-8 色由程式碼在填色情境明確指定
axes.prop_cycle:       cycler('color', ['0072B2','D55E00','009E73','CC79A7','4D4D4D'])

lines.linewidth:       2.0
lines.markersize:      5
lines.solid_capstyle:  round
patch.linewidth:       0
scatter.marker:        o

legend.frameon:        False
legend.loc:            upper left
legend.borderaxespad:  0.0
legend.handlelength:   1.4
legend.columnspacing:  1.2

xtick.direction:       out
ytick.direction:       out
xtick.major.size:      3
ytick.major.size:      0
ytick.major.pad:       4
xtick.minor.visible:   False
ytick.minor.visible:   False

boxplot.showfliers:    True
errorbar.capsize:      3
hatch.linewidth:       0.8
```

`baozi_viz/themes/baozi_dark.mplstyle`：差異部分
```ini
figure.facecolor:  14181F
axes.facecolor:    14181F
savefig.facecolor: 14181F
text.color:        E8EDF3
axes.titlecolor:   E8EDF3
axes.labelcolor:   9AA5B4
xtick.color:       9AA5B4
ytick.color:       9AA5B4
axes.edgecolor:    3E4855
grid.color:        2A323C
axes.prop_cycle:   cycler('color', ['4597D4','FB8747','54C399','F0A1CC','8A94A3','FFC757','87DAFF'])
```

`baozi_viz/theme.py`：
```python
from __future__ import annotations
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

_HERE = Path(__file__).parent / "themes"

CAT_LIGHT = ["#0072B2","#D55E00","#009E73","#CC79A7","#4D4D4D"]
CAT_LIGHT_FILL_ONLY = ["#E69F00","#56B4E9","#F0E442"]
CAT_DARK  = ["#4597D4","#FB8747","#54C399","#F0A1CC","#8A94A3","#FFC757","#87DAFF"]
CAT_DARK_FILL_ONLY = ["#F5E96B"]

SEQ_BLUE_LIGHT = ["#E9F3FF","#C0D3EB","#98B3D7","#7195C3","#4A76AE","#225899","#003984"]
SEQ_BLUE_DARK  = ["#091B31","#213754","#3A5679","#5676A0","#7399C9","#92BDF4","#B1E2FF"]
DIV_LIGHT = ["#B55000","#C87B43","#D9A480","#E8CCBA","#F5F5F5","#C2D4ED","#8FB4E4","#5C93D9","#2171CC"]
DIV_DARK  = ["#FFA85D","#CF8652","#946646","#5C4738","#292929","#3E4D60","#53749D","#699CDE","#7EC7FF"]

def _register_cmaps() -> None:
    specs = {
        "baozi_seq_light": SEQ_BLUE_LIGHT,
        "baozi_seq_dark":  SEQ_BLUE_DARK,
        "baozi_div_light": DIV_LIGHT,
        "baozi_div_dark":  DIV_DARK,
    }
    for name, colors in specs.items():
        if name in mpl.colormaps:
            mpl.colormaps.unregister(name)
        mpl.colormaps.register(LinearSegmentedColormap.from_list(name, colors), name=name)

def use(mode: str = "light") -> None:
    """套用 Baozi 主題。mode: 'light' | 'dark'"""
    if mode not in {"light", "dark"}:
        raise ValueError(f"mode must be 'light' or 'dark', got {mode!r}")
    plt.style.use(str(_HERE / f"baozi_{mode}.mplstyle"))
    _register_cmaps()

def palette(n: int, mode: str = "light", *, fill: bool = False) -> list[str]:
    """取 n 個類別色。超過線條安全上限會 raise —— 這是 R-01/R-02 的執行點。"""
    safe = CAT_LIGHT if mode == "light" else CAT_DARK
    extra = CAT_LIGHT_FILL_ONLY if mode == "light" else CAT_DARK_FILL_ONLY
    limit = len(safe) if not fill else len(safe) + len(extra)
    if n > limit:
        raise ValueError(
            f"{mode} 主題 {'填色' if fill else '線條'}類別上限為 {limit}，"
            f"要求 {n}。請改用 Top-N + 其他、small multiples，或加冗餘編碼。"
        )
    return (safe + extra)[:n]
```

使用：
```python
from baozi_viz import theme
theme.use("light")
colors = theme.palette(4)            # 4 條線 → OK
# theme.palette(7)                   # → ValueError（淺色線條上限 5）
im = ax.imshow(mat, cmap="baozi_seq_light")
```

**額外注意（本機實測）**：本機 matplotlib 為 **3.10.7**，而上游最新 release 為 **v3.11.1 (2026-07-18)**。`mpl.colormaps.register/unregister` 在 3.10 可用；若曾用 `matplotlib.cm.register_cmap`，該 API 在 3.9 已移除，勿使用。

### 8.2 Altair / Vega-Lite

**機制（altair-viz.github.io API 頁面實抓）**：Altair 5.5+ 起 theme API 移到 `altair.theme` 命名空間，舊的 `alt.themes.register()` 已 deprecated。

可用函式：`altair.theme.register(name)`（decorator）、`enable(name)`、`active`、`get`、`unregister`、`names`、`options`。
設定容器：`altair.theme.ThemeConfig`（「Top-Level Configuration TypedDict for creating a consistent theme」），子 TypedDict 包含 `AxisConfigKwds`、`LegendConfigKwds`、`RangeConfigKwds`、`MarkConfigKwds`、`TitleConfigKwds`、`ViewConfigKwds`、`ScaleConfigKwds`。

`baozi_viz/altair_theme.py`：
```python
from __future__ import annotations
import altair as alt
from .theme import CAT_LIGHT, CAT_DARK, SEQ_BLUE_LIGHT, SEQ_BLUE_DARK, DIV_LIGHT, DIV_DARK

FONT = "Noto Sans TC, Microsoft JhengHei, Segoe UI, sans-serif"

def _base(*, bg, surface, text, muted, grid, axis, cat, seq, div) -> alt.theme.ThemeConfig:
    return alt.theme.ThemeConfig(
        config={
            "background": bg,
            "font": FONT,
            "view": {"continuousWidth": 620, "continuousHeight": 320, "stroke": None},
            "title": {
                "font": FONT, "fontSize": 15, "fontWeight": 600, "color": text,
                "anchor": "start", "offset": 14,
                "subtitleFont": FONT, "subtitleFontSize": 12, "subtitleColor": muted,
                "subtitlePadding": 6,
            },
            "axis": {
                "labelFont": FONT, "labelFontSize": 11, "labelColor": muted, "labelPadding": 4,
                "titleFont": FONT, "titleFontSize": 12, "titleColor": muted,
                "titleFontWeight": 400, "titlePadding": 8,
                "domainColor": axis, "domainWidth": 0.8,
                "tickColor": axis, "tickSize": 4, "tickWidth": 0.8,
                "gridColor": grid, "gridWidth": 0.8, "grid": False,
            },
            "axisY": {"grid": True, "domain": False, "ticks": False, "labelPadding": 8},
            "axisX": {"grid": False},
            "legend": {
                "labelFont": FONT, "labelFontSize": 11, "labelColor": muted,
                "titleFont": FONT, "titleFontSize": 11, "titleColor": muted,
                "titleFontWeight": 400, "orient": "top", "direction": "horizontal",
                "symbolType": "stroke", "symbolStrokeWidth": 3, "offset": 8,
            },
            "range": {
                "category": cat,
                "ordinal": seq,
                "ramp": seq,
                "heatmap": seq,
                "diverging": div,
            },
            "line": {"strokeWidth": 2.2, "strokeCap": "round"},
            "point": {"size": 45, "filled": True},
            "bar": {"binSpacing": 2, "cornerRadius": 0},
            "rule": {"color": muted, "strokeWidth": 1},
            "text": {"font": FONT, "fontSize": 11, "color": text},
        }
    )

@alt.theme.register("baozi_light", enable=True)
def baozi_light() -> alt.theme.ThemeConfig:
    return _base(bg="#FFFFFF", surface="#F7F8FA", text="#1A1F26", muted="#5A6673",
                 grid="#E3E7EC", axis="#B4BCC6",
                 cat=CAT_LIGHT, seq=SEQ_BLUE_LIGHT, div=DIV_LIGHT)

@alt.theme.register("baozi_dark")
def baozi_dark() -> alt.theme.ThemeConfig:
    return _base(bg="#14181F", surface="#1C222C", text="#E8EDF3", muted="#9AA5B4",
                 grid="#2A323C", axis="#3E4855",
                 cat=CAT_DARK, seq=SEQ_BLUE_DARK, div=DIV_DARK)

# 切換：alt.theme.enable("baozi_dark")
```

**匯出靜態圖給投影片時的字型陷阱**（vl-convert README 實抓）：「SVG text placement and PNG text rendering require that the fonts referenced by the exported chart are installed on the system that VlConvert is running on.」，另可用 `vl_convert.register_font_directory` 註冊額外字型目錄。→ **CI 或容器環境必須先安裝 Noto Sans TC，否則中文會變豆腐。**

### 8.3 HTML 報告 / 儀表板的 CSS token

```css
:root {
  color-scheme: light dark;
  --font-sans: "Segoe UI", system-ui, "Noto Sans TC", "Microsoft JhengHei", sans-serif;
  --font-num:  "Segoe UI", "Noto Sans TC", "Consolas", monospace;
  --cat-1:#0072B2; --cat-2:#D55E00; --cat-3:#009E73; --cat-4:#CC79A7; --cat-5:#4D4D4D;
  --bg:#FFFFFF; --surface:#F7F8FA; --text:#1A1F26; --text-muted:#5A6673;
  --grid:#E3E7EC; --axis:#B4BCC6;
  --good:#1B7F4B; --bad:#C0392B; --warn:#B26B00; --highlight:#0072B2;
}
@media (prefers-color-scheme: dark) {
  :root {
    --cat-1:#4597D4; --cat-2:#FB8747; --cat-3:#54C399; --cat-4:#F0A1CC;
    --cat-5:#8A94A3; --cat-6:#FFC757; --cat-7:#87DAFF;
    --bg:#14181F; --surface:#1C222C; --text:#E8EDF3; --text-muted:#9AA5B4;
    --grid:#2A323C; --axis:#3E4855;
    --good:#4ADE80; --bad:#F87171; --warn:#FBBF24; --highlight:#4597D4;
  }
}
:root[data-theme="dark"]  { /* 同 dark 區塊，確保手動切換優先 */ }
:root[data-theme="light"] { /* 同 light 區塊 */ }

body { font-family: var(--font-sans); font-size: 16px; line-height: 1.75;
       letter-spacing: .02em; color: var(--text); background: var(--bg); }
table { border-collapse: collapse; width: 100%; font-size: 14px; line-height: 1.45; }
th, td { padding: 8px 12px; }
th { font-weight: 600; color: var(--text-muted); border-bottom: 1px solid var(--axis); }
tbody tr:last-child td { border-bottom: 1px solid var(--axis); }
td.num, th.num { text-align: right; font-family: var(--font-num);
                 font-variant-numeric: tabular-nums; letter-spacing: 0; }
thead th { position: sticky; top: 0; background: var(--bg); z-index: 1; }
.table-wrap { overflow-x: auto; }
@media print {
  thead { display: table-header-group; }
  tfoot { display: table-footer-group; }
  tr { break-inside: avoid; }
}
```

---

## 9. 工具與資源逐項調研

> 所有「最後活躍時間」為 2026-07-26 實際 fetch GitHub Atom feed / 頁面所見。

### 9.1 本文使用的驗證器（不是外部套件，是本專案資產）

- **檔案**：`E:\Projects\行銷分析\00_source_archive\research\palette_lab.py`
- **定位**：色盤驗證器。實作 sRGB↔linear、OKLab/OKLCH、WCAG 對比、Machado(2009) CVD 模擬矩陣（severity 1.0）、CIEDE2000。
- **依賴**：只有 `numpy` + `matplotlib`（本機 3.10.7 已裝）。
- **用途**：本文所有色值都由它驗證過；建議接進 CI，任何人改色盤都要跑過。
- **核心 API**：`contrast(hex, bg)`、`simulate(hex, 'deutan'|'protan'|'tritan')`、`ciede2000(h1, h2)`、`report(name, palette, bg)`、`darken_to_contrast()`、`lighten_to_contrast()`。
- **取捨**：Machado 矩陣是線性近似，不如 Brettel/Viénot 精確；CIEDE2000 用的是 D65/2°。對「排除明顯撞色」這個目的足夠，不宜當作醫學級結論。

### 9.2 matplotlib

- repo：`https://github.com/matplotlib/matplotlib`
- star：**23.0k**
- 最後活躍：**最新 release `REL: v3.11.1`，updated 2026-07-18T03:45:29Z**（前一版 v3.11.0 於 2026-06-12）。本機安裝版本為 **3.10.7**。
- archived：**否**
- 定位：靜態圖表主力；`.mplstyle` 是最成熟的「可 import theme 檔」機制。
- 適用：統計診斷圖（殘差 2×2 面板、Q-Q、Cook's D）、small multiples、投影片與 PDF 用的高 DPI 靜態圖、Excel 內嵌圖。
- 不適用：互動儀表板、需要 tooltip / cross-filter 的場景。
- 取捨：**對可變字型不做 instancing → 中文粗體靜默失效（R-12，已實測）**。中文排版細節（標點擠壓、直排）不支援。

### 9.3 Vega-Altair

- repo：`https://github.com/vega/altair`
- star：**10.4k**
- 最後活躍：**最新 release「Version 6.2.2」updated 2026-06-23T12:46:14Z；main 分支最後 commit「ci: bump actions/checkout from 6 to 7…」2026-07-20T00:32:16Z**
- archived：**否**
- 定位：宣告式圖表 + 原生互動（selection、cross-filter），主題系統為 typed（`ThemeConfig` TypedDict）。
- 適用：互動探索儀表板、單檔 HTML 報告（`chart.save(html)` 可內嵌 Vega-Lite runtime）。
- 不適用：極大資料量（需先在 DuckDB 聚合）、複雜統計診斷面板。
- 取捨：**本機尚未安裝**。5.5 起 theme API 改到 `alt.theme`，舊 `alt.themes.register()` deprecated —— 網路上多數教學是舊寫法，抄了會踩雷。

### 9.4 vega/vega-themes

- repo：`https://github.com/vega/vega-themes`
- star：**160**
- 最後活躍：**main 最後 commit 2026-07-21「chore(deps-dev): Bump brace-expansion…」（近期 commit 全為 Dependabot 自動更新）**
- archived：**否**
- 授權：BSD-3-Clause
- 定位：14 個現成 Vega/Vega-Lite 主題（excel, ggplot2, quartz, vox, fivethirtyeight, dark, latimes, urbaninstitute, googlecharts, powerbi, carbonwhite, carbong10, carbong90, carbong100）。
- 適用：拿來當**寫自己 theme 的參考結構**（看它們怎麼組 config 物件）。
- 不適用：直接使用 —— 沒有一個符合本文的色盲與對比門檻。
- 取捨：近一年只有依賴更新，無功能演進；但主題檔本質是靜態設定，這不算問題。

### 9.5 vega/vl-convert

- repo：`https://github.com/vega/vl-convert`
- star：**160**
- 最後活躍：**releases 最新為「V8 146.9.0 Pre-built Binaries」updated 2026-03-29T12:42:24Z；`vl-convert-python@2.0.0-rc1` 2026-02-14**
- archived：**否**
- 定位：把 Vega-Lite spec 轉成 SVG / PNG / PDF（Rust 實作，不需 node/browser）。
- 適用：Altair 圖表輸出到投影片與 PDF。
- 不適用：需要完整瀏覽器行為的場景。
- 取捨：**字型必須裝在執行環境上**（README 原文見 §8.2），中文環境要特別注意；可用 `register_font_directory` 補救。本機**尚未安裝**。2.0 目前仍是 RC。

### 9.6 plotly.py

- repo：`https://github.com/plotly/plotly.py`
- star：未取得（頁面未回傳）
- 最後活躍：**最新 release v6.9.0 updated 2026-07-09T14:53:20Z**（v6.8.0 於 2026-06-03，發版節奏約每月一次）
- archived：**否**
- 定位：互動圖表 + 自帶 template 系統（`plotly.io.templates`）。
- 適用：需要 3D、地圖、或想用 Dash 的場景。
- 不適用：本專案 —— 與 Altair 功能高度重疊，且單檔 HTML 會塞入 ~3MB plotly.js。
- 取捨：**明確不用**（見 §11）。本機未安裝。

### 9.7 great-tables（Python）

- repo：`https://github.com/posit-dev/great-tables`
- star：未取得（只抓了 feed）
- 最後活躍：**main 最後 commit 2026-07-24T20:52:31Z「Add to freeze cache」；最新 release v0.22.0 (2026-06-12)**
- archived：**否**
- 定位：表格排版與格式化。`fmt_number / fmt_integer / fmt_percent / fmt_currency / fmt_scientific / fmt_engineering / fmt_partsper / fmt_roman / fmt_bytes / fmt_date / fmt_time / fmt_datetime / fmt_duration / fmt_units`；樣式面 `tab_style`（配 `style.fill/text/borders/css`）、`tab_options`、`opt_table_font / opt_table_outline / opt_row_striping / opt_horizontal_padding / opt_vertical_padding / opt_css`。
- 適用：§4 表格排版規則的執行工具，輸出 HTML 表格。
- 不適用：Excel 交付（要用 openpyxl / XlsxWriter 的原生格式碼）。
- 取捨：版本仍在 0.x（v0.22.0），API 可能變動；但開發極活躍（兩天前還有 commit）。**本機尚未安裝**。

### 9.8 Noto CJK

- repo：`https://github.com/notofonts/noto-cjk`
- star：**4.0k**
- 最後活躍：**main 最後 commit 2024-09-19T09:26:59Z「Be more MS-friendly」；releases：Noto Serif CJK 2.003 (2024-07-30)、Noto Sans CJK 2.004 (2023-11-30)**
- archived：**否**（但近兩年無實質更新）
- 授權：SIL OFL 1.1（Google Fonts metadata `"license":"ofl"`；wght 100–900 可變軸）
- 定位：主力中文字型。
- 適用：全部四種交付物。
- 不適用：matplotlib 需要粗體時（R-12）。
- 取捨：字型檔大（TC VF 約 11.9 MB），Web 嵌入必須做 subset。

### 9.9 Adobe Source Han Sans / Serif

- repo：`https://github.com/adobe-fonts/source-han-sans`、`.../source-han-serif`
- 最後活躍：**Sans 最新 release「Fonts Version 2.005R (OTF, OTC, Super OTC, Subset OTF, Variable OTF/TTF/WOFF2)」updated 2025-06-25T03:26:30Z；Serif 最新「Fonts Version 2.003」updated 2024-07-30T18:57:27Z**
- archived：**否**
- 授權：SIL OFL 1.1
- 定位：Noto CJK 的上游，且 **Sans 的更新比 noto-cjk repo 新一年**（2.005R vs 2.004）。
- 取捨：如果要最新字形與 WOFF2，直接抓 Adobe 這邊；但字型名稱是「Source Han Sans TC」不是「Noto Sans TC」，font stack 要兩個都寫。

### 9.10 jf open 粉圓 (open-huninn)

- repo：`https://github.com/justfont/open-huninn-font`
- star：**1.3k**
- 最後活躍：**最新 release v2.1（2024-09-19）；master 最後 commit 2025-06-17T11:05:41Z「Update README.md」**
- archived：**否**
- 授權：SIL OFL 1.1，README 明示**無需標註出處**、可商用、修改須沿用同授權、不可單獨販售字型本身。
- 衍生自：Kosugi Maru（Motoya，日文）+ Varela Round（拉丁）。版本史：1.0 (2020-03-14)、1.1 (2020-04-04)、2.0 (2023-03-14)、2.1 (2024-09-19)。含注音與台語/閩南語音標。
- 適用：對內簡報標題、活動主視覺、親和向文案。
- 不適用：**正式商業報告內文與數字欄**（圓體降低權威感；且字重選項少）。
- 取捨：這是「風格資產」不是「系統字型」。

### 9.11 台北黑體 Taipei Sans TC Beta

- 官方：翰字鑄造 JT Foundry（Google Sites）；GitHub 鏡像 `https://github.com/VdustR/taipei-sans-tc`
- star：**37**（鏡像 repo）
- 最後活躍：**未能查證**（見 §12）
- archived：**否**（鏡像 repo 頁面無 archived 標記）
- 授權：SIL OFL 1.1。官網原文：「台北黑體亦基於 SIL Open Font License 1.1 授權為免費、公開的字型製品。」限制：不得「直接更改字型名稱並宣稱為自身之作品」。鏡像 repo 本身標 MIT（那是打包腳本的授權，不是字型的）。
- 定位：思源黑體改作的印刷體風格繁中黑體，字形較貼近台灣印刷慣例。
- 取捨：名稱含 "Beta"，且無公開的版本更新節奏 → **不建議當唯一主字型**，可當第二選擇。

### 9.12 FT Chart Doctor / Visual Vocabulary

- repo：`https://github.com/Financial-Times/chart-doctor`
- star：**3.3k**
- 最後活躍：**main 最後 commit 2024-03-12T17:12:47Z「Update Visual-vocabulary-de.pdf」**
- archived：頁面未顯示 archived 標記
- 定位：圖表選型分類法（九大資料關係），**有繁體中文版 PDF**。
- 適用：§3 決策表的分類骨架、給團隊當共同語言的一頁 poster。
- 不適用：色彩與排版規範（它不談這些）。
- 取捨：兩年多未更新，但分類法屬穩定知識，不是問題。

### 9.13 Royal Statistical Society — datavisguide

- repo：`https://github.com/royal-statistical-society/datavisguide`
- star：**167**
- 最後活躍：**main 最後 commit 2024-11-16T19:35:07Z「Render PDF」**
- archived：**否**
- 授權：**CC BY 4.0**（原文引於 §7）→ 可合法改作成內部規範，只要標註出處。
- 定位：有程式碼範例的實務指南，Quarto 產出。
- 取捨：範例以 R 為主（本專案是 Python），需要轉譯。

### 9.14 Urban Institute urbnthemes

- repo：`https://github.com/UrbanInstitute/urbnthemes`
- star：**88**
- 最後活躍：**未能查證**（見 §12）
- archived：頁面未顯示 archived 標記
- 定位：R + ggplot2 的機構級 theme 套件，連到 `UrbanInstitute.github.io/r-at-urban/graphics-guide.html`。
- 適用：**只當參考**（看一個機構的 style guide 該長什麼樣）。
- 不適用：本專案（R 套件，且本專案已定案 Python）。

### 9.15 IBCS / ISO 24896

- 來源：`ibcs.com`（standards、iso-24896、top-and-bottom-5 三頁實抓）；`iso.org/standard/88366.html`
- 狀態：**ISO 24896「Notation for business reporting」於 2026-06-11 發布；IBCS Standards 2.0 同步對齊並拆分為 Notation / Composition 兩部分**
- 定位：商業報告表示法的國際標準。
- 適用：情境語意（AC/PL/BU/FC/PY）、差異圖紅綠、一致性縮放、標題概念、資訊密度。
- 不適用：**它對 sparkline 的否定我方不採納**；它也不談色盲可及性與深色主題。
- 取捨：完整標準文本需付費/會員（PDF 限會員，或購書）。**免費頁面能取得的規則已足夠寫出 §6.3 與 §6.4**。

### 9.16 python-pptx

- repo：`https://github.com/scanny/python-pptx`
- star：未取得
- 最後活躍：**最新 release v1.0.2 updated 2024-08-07T17:36:25Z；master 最後 commit 2024-08-07T17:33:54Z「fix(enum): replace read-only enum values」**
- archived：**否**（但已接近兩年無 commit）
- 定位：投影片交付物的產生工具。
- 適用：把 matplotlib 匯出的 PNG/SVG 塞進版型化的 .pptx。
- 取捨：**維護明顯停滯（近 2 年零 commit）**，是本堆疊中維護風險最高的一環。替代路徑：Quarto revealjs（單檔 HTML 投影片，與 HTML 報告共用同一套 CSS token）。本機未安裝。

### 9.17 本機既有環境（實測）

| 套件 | 本機版本 | 說明 |
|---|---|---|
| matplotlib | 3.10.7 | 上游最新 3.11.1，落後一個 minor |
| pandas | 2.3.3 | |
| duckdb | 1.5.5 | 倉儲層已就位 |
| pyarrow | 23.0.0 | Parquet 讀寫 |
| openpyxl | 3.1.5 | Excel 交付 |
| XlsxWriter | 3.2.9 | Excel 交付（格式碼更完整） |
| seaborn | 0.13.2 | |
| statsmodels | 0.14.6 | lm/glm/ANOVA 重寫的主力 |
| fonttools | 4.61.0 | 本文字型量測工具 |
| **altair** | **未安裝** | 需補 |
| **great_tables** | **未安裝** | 需補 |
| **vl-convert-python** | **未安裝** | 需補（Altair 靜態匯出） |
| **jinja2** | **未安裝** | 需補（HTML 報告模板） |
| plotly / polars / narwhals / quarto | 未安裝 | 不需要 |

---

## 10. 總結比較表

| 工具 / 資源 | repo | ★ 量級 | 實際觀測到的最後活躍 | archived | 在本設計系統的角色 |
|---|---|---|---|---|---|
| matplotlib | matplotlib/matplotlib | 23k | release v3.11.1 **2026-07-18** | 否 | 靜態圖 + `.mplstyle` theme 檔 ✅ 採用 |
| Vega-Altair | vega/altair | 10k | commit **2026-07-20**；release 6.2.2 **2026-06-23** | 否 | 互動圖 + `alt.theme` theme ✅ 採用 |
| vega-themes | vega/vega-themes | 160 | commit **2026-07-21**（皆 Dependabot） | 否 | 參考結構，不直接用 ⚪ |
| vl-convert | vega/vl-convert | 160 | release **2026-03-29**；py 2.0.0-rc1 **2026-02-14** | 否 | Altair→PNG/PDF ✅ 採用 |
| great-tables | posit-dev/great-tables | — | commit **2026-07-24**；v0.22.0 **2026-06-12** | 否 | HTML 表格排版 ✅ 採用 |
| plotly.py | plotly/plotly.py | — | release v6.9.0 **2026-07-09** | 否 | ❌ 不用（與 Altair 重疊） |
| Noto CJK | notofonts/noto-cjk | 4k | commit **2024-09-19**；Sans 2.004 **2023-11-30** | 否 | 主字型 ✅ 採用（已安裝） |
| Source Han Sans | adobe-fonts/source-han-sans | — | release 2.005R **2025-06-25** | 否 | 上游/備援 ✅ 採用 |
| Source Han Serif | adobe-fonts/source-han-serif | — | release 2.003 **2024-07-30** | 否 | 標題用襯線 ⚪ 有條件（禁數字欄） |
| jf open 粉圓 | justfont/open-huninn-font | 1.3k | commit **2025-06-17**；v2.1 **2024-09-19** | 否 | 風格字型 ⚪ 有條件 |
| 台北黑體 | VdustR/taipei-sans-tc（鏡像） | 37 | **未能查證** | 否 | 備選 ⚪ |
| FT Visual Vocabulary | Financial-Times/chart-doctor | 3.3k | commit **2024-03-12** | 未顯示標記 | 圖表分類法 ✅ 採用（有繁中版） |
| RSS datavisguide | royal-statistical-society/datavisguide | 167 | commit **2024-11-16** | 否 | CC BY 4.0，可改作 ✅ 採用 |
| urbnthemes | UrbanInstitute/urbnthemes | 88 | **未能查證** | 未顯示標記 | 參考 ⚪（R 套件） |
| python-pptx | scanny/python-pptx | — | commit **2024-08-07**；v1.0.2 **2024-08-07** | 否 | 投影片 ⚠️ 維護停滯 |
| IBCS / ISO 24896 | ibcs.com / iso.org | n/a | **ISO 24896 發布 2026-06-11** | n/a | 商業報告表示法 ✅ 採用 |
| Nightingale / DVS | nightingaledvs.com | n/a | 文章更新至 **2026-07** | n/a | ❌ 無可引用規範 |

---

## 11. 推薦堆疊與明確不用的東西

### 11.1 推薦堆疊

| 層 | 選擇 | 理由 |
|---|---|---|
| 色彩定義 | **本專案自建 token**（§1），Okabe-Ito 色相邏輯 + OKLCH 導出深色版 + 實測驗證 | 沒有現成色盤能同時過對比與 CVD 門檻，只能自建並驗證 |
| 色彩驗證 | **`palette_lab.py`**（本專案資產，只依賴 numpy/matplotlib） | 把美感變成可跑的測試 |
| 色階 | viridis / cividis（學術）+ 自建品牌藍單色階（儀表板）+ 自建橘藍發散 | 三者用途分明，皆已驗證明度單調/對稱 |
| 字型（主） | **Noto Sans TC**（OFL、已安裝、數字等寬 0.521 em） | 唯一同時滿足可商用、可嵌入、數字等寬的繁中黑體 |
| 字型（補靜態字重） | Noto Sans TC subset OTF 七字重，或 Source Han Sans 2.005R | 解 matplotlib 可變字型無粗體問題 |
| 靜態圖 | **matplotlib + `.mplstyle`** | theme 機制最成熟；統計診斷圖無可取代 |
| 互動圖 | **Altair + `alt.theme.register`** | 宣告式、typed theme、原生 selection |
| 靜態匯出 | **vl-convert-python** | Altair→PNG/PDF，不需 node |
| HTML 表格 | **great-tables** | `fmt_*` 系列直接對應 §4.1 規則 |
| Excel 表格 | **XlsxWriter**（格式碼）+ openpyxl（讀改） | 數值必須是數值型別 + 原生格式碼 |
| 報告模板 | Jinja2 單檔 HTML（內嵌 CSS token + base64 圖） | 交付「單檔」硬需求 |
| 圖表分類法 | **FT Visual Vocabulary 繁中版** | 團隊共同語言 |
| 商業表示法 | **ISO 24896 / IBCS 2.0** | 2026-06-11 成為國際標準，對外溝通有份量 |
| style guide 骨架 | datavizstyleguide.com 的 Foundations 目錄 | 現成目錄結構 |
| 可改作素材 | RSS datavisguide（CC BY 4.0） | 授權明確可改作 |

需要 `pip install`：`altair`、`great-tables`、`vl-convert-python`、`jinja2`。（`matplotlib` 可考慮升到 3.11.x 對齊上游。）

### 11.2 明確不用的東西 + 理由

| 不用 | 理由 |
|---|---|
| **plotly.py** | 與 Altair 功能重疊；單檔 HTML 會塞入約 3MB 的 plotly.js，違背「單檔報告」的體積合理性；主題系統不如 Altair 的 typed ThemeConfig 好維護 |
| **原封不動的 Okabe-Ito 8 色** | 實測白底對比 1.32 / 2.25 / 2.31，三色當線條不可見（§1.2） |
| **Tableau Color Blind 10** | 實測 normal 下最小 ΔE 僅 10.8（兩個灰撞色），且 8 色中 4 色對比不足 |
| **ColorBrewer Set2 / Dark2 當預設類別盤** | 未經本專案對比與 CVD 門檻驗證；Set2 彩度過低在投影機上會糊 |
| **紅↔綠發散色階當通用色階** | 深色主題下 deutan ΔE 僅 7.5（§1.7）。只保留給 IBCS 差異圖且強制加符號 |
| **深色主題用完整 viridis** | 低端 `#440154` 對 `#14181F` 對比 1.17:1，等於看不見（R-19） |
| **Noto Serif TC 排數字欄** | 實測數字有 6 種寬度，非等寬（R-11） |
| **Microsoft JhengHei 嵌入交付檔** | Windows 隨附授權，不可自由嵌入散布。僅限本機產出 |
| **`font-feature-settings: "tnum"` 當作解法** | 實測 Noto Sans TC / Noto Serif TC / JhengHei 都沒有 `tnum` feature（§2.3B） |
| **`alt.themes.register()` 舊 API** | 5.5 起 deprecated，改用 `alt.theme.register` |
| **`matplotlib.cm.register_cmap`** | 舊 API，改用 `mpl.colormaps.register` |
| **雙 Y 軸（除單位換算外）** | 縮放可任意調整 → 可製造任意相關性（R-07） |
| **圓餅 >5 類、雷達圖、3D** | IBCS Bottom-1 + 感知學共識（R-06/R-09） |
| **Nightingale 當規範引用** | 它是期刊不是標準（§7） |
| **urbnthemes / bbplot 等 R 主題套件** | R 生態，本專案已定案 Python；僅作參考 |
| **Quarto（目前）** | 本機未安裝、且會引入獨立的 Pandoc/Quarto CLI 依賴。若 python-pptx 的維護停滯成為問題，再回頭評估 Quarto revealjs 作投影片方案 |

---

## 12. 無法查證的事項（誠實清單）

以下是我**實際嘗試過但沒能取得**的資訊。沒有用印象填補。

1. **台北黑體的最後更新時間與版本號。** 官方是翰字鑄造 JT Foundry 的 Google Sites 頁面，該站不提供版本歷史或更新日期；GitHub 鏡像 `VdustR/taipei-sans-tc` 我取得了 star 數（37）與 license（MIT，屬打包腳本），但**未取得 commit 日期**。字型名稱至今仍帶 "Beta"，是否還在維護無從判斷。
2. **UrbanInstitute/urbnthemes 的最後 commit / release 日期。** 只取得 star 數 88 與 README 內容。
3. **plotly.py、great-tables、python-pptx 的 star 數。** GitHub 頁面 fetch 時未回傳該欄位（只取得 release/commit feed）。
4. **matplotlib 與 noto-cjk repo 首頁的 archived 標記狀態。** 兩次 fetch 都回報「頁面出現載入錯誤」或欄位缺失，我是從「持續有 commit / release」推斷未 archived，**不是直接看到 archived 標記的缺席**。
5. **IBCS Standards 2.0 的完整規則條文。** 完整 PDF 限會員或需購書。§6.3 的規則來自 IBCS 官網的免費「Top and Bottom 5」與 ISO 24896 說明頁，**不是標準原文**。ISO 24896 本文（iso.org/standard/88366.html）是付費文件，我沒有讀過。
6. **ISO 24896 對顏色的具體規定。** 我只查到它規範「labelling of content, the layout of charts and tables, the representation of data values, as well as the visualization of their characteristics」，**沒有查到它是否指定具體 hex 值或色彩可及性要求**。
7. **Paul Tol 官方色票頁面。** `personal.sron.nl/~pault/` DNS 解析失敗（`getaddrinfo ENOTFOUND`）。§1.2 表中的 Tol bright / muted hex 值是我從記憶中的常見值輸入後**用本機驗證器實測**的 —— 對比與 ΔE 數據是真實計算結果，但**這些 hex 是否確為 Tol 官方公布值，我未能從原始來源核對**。本文最終推薦色盤不依賴這組值。
8. **Okabe-Ito 的原始出處頁面**（Okabe & Ito, "Color Universal Design"）。我是從搜尋結果彙整取得 hex 值，**未 fetch 到原始日文/英文原文頁**。不過這 8 個值在多個獨立來源一致，且我已用驗證器實測其性質。
9. **Google Fonts 上 Noto Sans TC 的靜態字重下載連結是否仍有效。** README 中的 URL 指向 `googlefonts/noto-cjk` 的 `Sans2.004` release 資產（`19_NotoSansTC.zip`），**我沒有實際下載驗證該檔案存在與內容**。
10. **繁中排版行高的權威來源。** §2.6 的 1.5–1.8 區間來自數篇中文網頁設計文章的共識，**不是任何標準組織的規範**。1.75 是我在此區間內的設計決定，非引用值。
11. **本機 Noto Sans/Serif TC/HK 是誰安裝的、版本號多少。** 只確認檔案存在於 `C:\Windows\Fonts` 與檔案大小，**未讀取字型的 version 欄位**比對是 2.004 還是更新版。
12. **深色主題背景 `#14181F` 與 `#1C222C` 沒有外部依據。** 這是我的設計選擇（避開純黑以減少 halation），對比數據是實測的，但「哪個深色背景最好」我沒有查到權威研究。
13. **投影片 7 列 × 5 欄的表格上限。** 這是常見的簡報經驗法則，**我沒有查到可引用的研究或標準**。
14. **儀表板 KPI 卡上限 8 張、12 欄網格。** 同上，屬設計決定而非引用。
15. **CIEDE2000 ΔE ≥ 12 這個門檻。** 「ΔE > 10 為明顯不同色」是常見經驗值，我取 12 作為安全邊際，**沒有查到針對「資料視覺化類別色最小色差」的正式標準**。這是本文最重要的一個主觀參數，若日後找到權威依據應據以修正。

---

## 附：驗證器原始碼位置

`E:\Projects\行銷分析\00_source_archive\research\palette_lab.py` — 本文所有色彩數據的產生器。改任何色值前先跑：

```python
from palette_lab import report
report("我的新色盤", ["#...", "#..."], "#FFFFFF")   # 印出對比 + 三種色覺缺陷下的最小 ΔE2000
```
