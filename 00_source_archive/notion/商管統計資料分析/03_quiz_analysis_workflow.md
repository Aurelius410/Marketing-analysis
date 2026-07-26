---
source: Notion
workspace_parent:
  title: "商管統計資料分析 (MBA5045)"
  url: "https://app.notion.com/p/2692b4ffdf0b8060ac98f5535dda84a9"
pages:
  - title: "Quiz 1"
    url: "https://app.notion.com/p/2732b4ffdf0b80fd92b9c6d00352ea95"
    notion_last_view: "2025-09-22T08:40:57Z"
    topic: "簡單線性迴歸 (SLR)：假設、SSE/R^2/RSE、SE 與樣本數"
    datasets: ["car accident.txt", "OACs.txt"]
  - title: "Quiz 2"
    url: "https://app.notion.com/p/2772b4ffdf0b805abd5ee9a54bad5fe6"
    notion_last_view: "2025-10-11T19:10:03Z"
    topic: "多元迴歸：共線性、Adjusted R^2、變數轉換、多項式與交乘、巢狀 F 檢定、Cook's D"
    datasets: ["COLLGPA.txt"]
  - title: "Quiz 3"
    url: "https://app.notion.com/p/28f2b4ffdf0b80a99fc4e442e25d1baf"
    notion_last_view: "2025-10-31T10:09:39Z"
    topic: "變數選擇 (backward/step/AIC)、dummy 與交互作用、log 轉換；★行銷資料主案例"
    datasets: ["O2O_spending.csv"]
  - title: "Quiz 4"
    url: "https://app.notion.com/p/29f2b4ffdf0b80508c4af6922c61b8e1"
    notion_last_view: "2025-11-02T09:37:04Z"
    topic: "ANOVA：單因子/雙因子、reference coding、Tukey HSD vs Bonferroni、交互作用"
    datasets: ["Detergent_R.csv", "icecream.csv"]
  - title: "Quiz 5"
    url: "https://app.notion.com/p/2a82b4ffdf0b8075890fc4d1420a07f5"
    notion_last_view: "2025-11-30T13:07:02Z"
    topic: "類別資料：列聯表、卡方獨立性/適合度、odds 與 odds ratio、抽樣設計"
    datasets: ["Drinking & Breast Cancer（手動輸入之 2x2 表）"]
  - title: "Quiz 6"
    url: "https://app.notion.com/p/2c12b4ffdf0b80cdb928eff080785bcc"
    notion_last_view: "2025-12-08T04:00:35Z"
    topic: "GLM：三成分、MLE、Wald vs LRT、Deviance 適合度、Poisson log-linear、Overdispersion 與 quasi-likelihood"
    datasets: ["ILdirectorates.txt"]
capture_scope: "Quiz 1~6 六個頁面之全文（含全部是非題解析、全部 R 程式碼區塊、全部填答數值）。所有 toggle/details 區塊皆已展開抓取。頁內嵌入的圖片為 Notion 簽章短效 URL，無法長期保存，僅以文字說明其內容。"
captured_at: "2026-07-25"
fidelity_note: "本檔以「忠實轉錄 + 結構化」為原則：所有數學式、程式碼、答案數值均來自上列 Notion 頁面原文。任何非原文的推論、疑點與補充判斷，一律集中放在標示為「評註」的段落，或段落內明確標示【評註】。"
---

# Quiz 1~6 完整分析工作流程 digest（商管統計資料分析 MBA5045）

這批材料的價值不在「統計課本知識」，而在於它是**六個完整的「拿到資料 → 選方法 → 跑 R → 讀報表 → 寫成一句結論」的實例**，而且每個實例都有：

1. 一段觀念判讀（是非題解析）＝告訴你「這個方法的常見誤用在哪」；
2. 一份可執行的 R 程式碼＝告訴你「實際敲什麼指令」；
3. 一組填答數值＝告訴你「報表要讀出哪個數字才算完成分析」。

以下逐份完整記錄，最後一節整理成可重用資產。

---

## 0. 六份 Quiz 全景對照表

| Quiz | 核心方法 | 資料集 | 反應變數 | 主要解釋變數型態 | 這回答什麼行銷／商業問題 |
|---|---|---|---|---|---|
| 1 | 簡單線性迴歸 (SLR)、SSE/R²/RSE、SE 與 n 的關係 | `car accident.txt`、`OACs.txt` | Accidents；GPA | 單一連續變數 | 「單一驅動因子（速限／入學成績）能不能解釋結果？解釋力有多少？哪一個指標更有預測力？」＝單變數篩選與 KPI 選擇 |
| 2 | 多元迴歸、共線性、多項式與交乘、巢狀 F 檢定、Cook's D | `COLLGPA.txt` | Y (大學 GPA) | 兩個連續變數 + 二次項 + 交乘 | 「兩個投入變數之間有沒有交互作用／報酬遞減？加了非線性項是否真的值得？哪幾筆樣本在主導結論？」＝投入組合與異常客戶診斷 |
| 3 ★ | 變數選擇 (最大 p 值淘汰、`step()`/AIC)、dummy、交互作用、log 轉換 | `O2O_spending.csv` | `log(store.spend)` | 連續（age、距離、交易數、線上行為）＋類別（gender、email） | 「線上行為與 email 訂閱如何影響線下（到店）消費？email 訂戶到店花得更少嗎？效果是否因性別而異？」＝O2O 通道互相蠶食 / 名單價值 / 分眾差異 |
| 4 | 單因子與雙因子 ANOVA、Tukey HSD、Bonferroni、交互作用 | `Detergent_R.csv`、`icecream.csv` | Score；Amount | 純類別因子（品牌×溫度；碗大小×勺大小） | 「五個品牌／三種水溫哪幾組真的有差？包裝或器具尺寸會不會改變消費者取用量？兩個因子會不會互相影響？」＝A/B/n 測試、包裝設計實驗 |
| 5 | 列聯表、卡方（獨立性／適合度）、odds、odds ratio 與其 CI | Drinking & Breast Cancer 2×2 表（程式內手動輸入） | 是否為 Case | 二元分組（4+ / <4 drinks） | 「暴露（行為）與結果之間有沒有關聯？關聯有多強（幾倍勝算）？回溯性樣本能不能算比例？」＝行為分群 vs 轉換的關聯強度、觀察性資料的因果界線 |
| 6 | GLM 架構、MLE、Wald vs LRT、Deviance、Poisson log-linear、Overdispersion、quasi-likelihood | `ILdirectorates.txt` | `interlocks`（計數） | `log2(assets)` ＋ sector、nation 兩個 factor | 「規模每翻倍，事件次數增加幾 %？不同產業／國家的水準差幾倍？計數資料變異被低估時該怎麼修正結論？」＝次數型 KPI（點擊、購買次數、客訴數）建模與規模彈性 |

---

## 1. Quiz 1 — 簡單線性迴歸：假設優先、指標互相牽動

**頁面**：Quiz 1 — https://app.notion.com/p/2732b4ffdf0b80fd92b9c6d00352ea95
**頁內開頭寫法**：以「快速整理：」開場，每題以「$Q_k$：正確／錯誤」加一到兩行機制說明。這是這批材料反覆出現的**答案體例：先給判斷，再給一行「為什麼」，不寫廢話**。

### 1.1 觀念判讀（Q1–Q10 原文解析）

- **Q1：正確**
  - 符合假設比單純拉高 $R^2$ 更重要；否則推論（$\text{t}$、$\text{CI}$、$\text{p-value}$）不可靠。
- **Q2：錯誤**
  - 異質變異不會讓平均預測系統性偏高/偏低；OLS 仍無偏，主要影響標準誤與檢定。
- **Q3：正確**
  - 定義上 $Y_i=\hat Y_i+\hat\varepsilon_i$。
- **Q4：正確**
  - 斜率 $\text{SE}\propto \dfrac{1}{\sqrt{n}}$；$n$ 倍增 → $\text{SE}$ 乘上 $\dfrac{1}{\sqrt{2}}\approx 0.7071$ → 約降 30%。
- **Q5：錯誤**
  - 迴歸 $Y$ on $X$ 與 $X$ on $Y$ 的 $\text{OLS}$ 斜率不同（分母分別是 $\mathrm{Var}(X)$、$\mathrm{Var}(Y)$）。
- **Q6：錯誤**
  - 計算 $\text{SSE}=\sum_{i=1}^n(Y_i-\hat{Y}_i)^2$ 不需常態，常態只影響推論分布。
- **Q7：錯誤**
  - $R^2=1-\dfrac{SSE}{SST}$；若 $SSE=0$，則 $R^2=1$。
- **Q8：錯誤**
  - $\hat\sigma=\sqrt{\dfrac{SSE}{n-2}}=20$、$n=10 \Rightarrow SSE=20^2\times 8=3200$（非 3600）。
- **Q9：正確**
  - 好模型常見訊號：$\text{SSE}$ 小、$\text{RSE}$ 小、$R^2$ 高、整體 $\text{F}$ 大（在假設大致成立下）。
- **Q10：正確**
  - $\text{SSE}$ 衡量觀測值與擬合值的**差距平方和**。

**這回答什麼商業問題**：Q1、Q2、Q9 合起來就是一條**匯報紀律**——不要拿 $R^2$ 當唯一賣點；假設壞掉時，$p$ 值與信賴區間（也就是你要拿去說服人的「顯著」）才是先失效的東西。Q4 是**樣本量投資報酬**的算式：想把估計精度提高一倍（SE 減半），樣本要 4 倍，不是 2 倍。

### 1.2 Coding Q11：車禍數 vs 速限（SLR）

**資料集特徵**：`car accident.txt`，`read.table(header = TRUE)` 可讀，欄位含 `Accidents`（反應）、`Speed`（解釋）。空白分隔文字檔。

**提問**：速限對車禍數的估計係數、$p$ 值、$R^2$ 各為多少？關係顯著嗎？

**答案（原文）**
- Estimated coefficient：**0.2508**
- $\text{p-value}$：**0.2693**
- $R^2$：**0.0210**（關係不顯著）

**R 程式碼（原文照錄）**

```r
########  指定絕對路徑   ########
fp <- "C:/Users/user/Desktop/商管統計資料分析/Quiz/car accident/car accident.txt"

## Read data
caraccident <- read.table(fp, header = TRUE)
    attach(caraccident)欣
    
## Summary
lm1 <- lm(Accidents ~ Speed, data=caraccident)
summary(lm1)
```

【評註】上面 `attach(caraccident)欣` 的「欣」是原文誤打的中文字，實際執行會報錯，需刪除。此處保留原樣以維持忠實轉錄。

**結論寫法**：三個數字並列（係數、$p$、$R^2$），最後用括號一句定調「（關係不顯著）」。注意它**沒有**因為係數是正的就說「速限越高車禍越多」——$p=0.2693$ 就停在「不顯著」。

### 1.3 Coding Q12：OACs — 兩個候選預測變數比 $R^2$

**資料集特徵**：`OACs.txt`，欄位含 `GPA`（反應）、`Best-6`、`B4+E+C`。**關鍵資料清理細節（原文註解）**：欄名含 `-`、`+` 時 R 會改寫，`Best-6` 要打成 `Best.6`、`B4+E+C` 要打成 `B4.E.C` 才讀得到。

**提問**：兩個模型（GPA~Best-6 與 GPA~B4+E+C）哪個 $R^2$ 較高？

**答案（原文）**：較高的 $R^2$ 為 **0.3509**（B4+E+C 模型較佳）。

**R 程式碼（原文照錄，兩個區塊）**

```r
########  GPA 對 Best-6   ########
########  指定絕對路徑   ########
fp <- "C:/Users/user/Desktop/商管統計資料分析/Quiz/OACs/OACs.txt"

## Read data
OACs <- read.table(fp, header = TRUE)
    attach(OACs)
## Summary （ Best-6　改　Best.6 才讀的到）
lmOACs1 <- lm(GPA ~ `Best-6`, data = OACs)
summary(lmOACs1)
```

```r
########  GPA 對 Best-6   ########
########  指定絕對路徑   ########
fp <- "C:/Users/user/Desktop/商管統計資料分析/Quiz/OACs/OACs.txt"

## Read data
OACs <- read.table(fp, header = TRUE)
    attach(OACs)
## Summary （ B4+E+C　改　B4.E.C 才讀的到）
lmOACs2 <- lm(GPA ~ B4.E.C, data = OACs)
summary(lmOACs2)
```

【評註】第一個區塊註解說「改 `Best.6` 才讀得到」，但公式仍寫 `` `Best-6` ``（反引號寫法）；兩種寫法擇一即可，註解與程式碼在原文中不一致。

**這回答什麼行銷/商業問題**：這是最小型的**指標擇一**分析——兩個候選預測分數，哪一個對結果的解釋力高？流程是「同一反應變數、同一資料、換一個單變數、比 $R^2$」，等同於行銷上比較兩個候選 lead score / 傾向分數哪個更能預測成效。

---

## 2. Quiz 2 — 多元迴歸：共線性、轉換原則、巢狀比較、影響點

**頁面**：Quiz 2 — https://app.notion.com/p/2772b4ffdf0b805abd5ee9a54bad5fe6
**體例**：每題先抄英文題幹，接著 `Sol. 正確/錯誤`，再用 2–4 個縮排子點交代「現象 → 機制 → 判讀」。

### 2.1 觀念判讀（10 題，原文完整）

1. **題**：A high value of the coefficient of determination significantly above 0 in multiple regression, accompanied by insignificant *t*-statistics on all parameter estimates, very often indicates a high correlation between independent variables in the model.
   - **Sol. 正確**
     - 現象：$R^2$ 高、各係數 t-statistics 不顯著。
     - 機制：共線性 $\uparrow \Longrightarrow s_{\hat b_j} \uparrow \Longrightarrow t_j=\dfrac{\hat b_j}{s_{\hat b_j}} \downarrow$
     - 判讀：整體好、個別差的情形常見於多重共線性，需用 VIF 確認。
2. **題**：When an explanatory variable is dropped from a multiple regression model, the coefficient of determination can increase.
   - **Sol. 錯誤**
     - 刪變數只會讓 SSE 不降 ⇒ $R^2=1-\dfrac{SSE}{SST}$ 不會上升（維持或下降）。
     - 易混淆的點：Adjusted $R^2$ 可能上升，但題目問的是 $R^2$。
3. **題**：The main use for a residual plot is finding nonlinear effects in multiple regression.
   - **Sol. 錯誤**
     - 殘差圖主要用來檢：Mean zero／Constant variance／Independence
     - 非線性只是可能顯示的型態之一，非主要用途。
4. **題**：In testing the significance of a multiple regression model with three independent variables, the null hypothesis for the global usefulness test is $H_0: b_1 = b_2 = b_3$.
   - **Sol. 錯誤**
     - 全體有用性檢定正確的假說建立：
       $H_0：\beta_1=\beta_2=\beta_3=0$
       $H_1：\beta_1,\beta_2,\beta_3\ 不全為\ 0$
5. **題**：In multiple regression analysis, the adjusted coefficient of determination is adjusted for the number of independent variables and the sample size.
   - **Sol. 正確**
     - $\bar{R}^2=1-\dfrac{n-1}{n-k-1}(1-R^2)$。
     - 同時調整樣本數 $n$ 與變數數量 $k$（含截距）。
6. **題**：When using polynomial transformations in models, lower powers can be removed according to their significance.
   - **Sol. 錯誤**
     - 階層原則：有 $X^2, X^3$ 時，低次項（$X, X^2$）應保留，即使 t-statistics 不顯著。
     - 原因：解釋性與共線性。
     - 可先中心化 $X$，成組後以 partial F-test 檢定整段多項式。
7. **題**：Natural logarithm transformation works well for negatively skewed variables.
   - **Sol. 錯誤**
     - ln 主要矯正右偏分配。
     - 左偏分配以次方轉換（如平方）或反射＋log。
8. **題**：Transformations often suggested by theories about economics, consumer psychology, worker behavior, business decision-making, physical laws, and so on.
   - **Sol. 正確**
     - 轉換常由理論建議：經濟（log–log、log–linear）／行為（對數效應）／物理（冪律、反比、平方根）。
     - 原則：**先理論、後統計**。
9. **題**：If it is suggested from experience that there is an inverse relationship between response and explanatory variables, it is suitable to apply reciprocal transformation for the response.
   - **Sol. 錯誤**
     - 反向關係 $\ne$ 一定對 Y 取倒數。
     - 若 $Y \approx a+b\left(\dfrac{1}{X}\right)$：對 $\dfrac{1}{X}$ 做迴歸。
     - 只有在 $Y \approx a+b\left(\dfrac{1}{X}\right)$ 時，才對 $Y$ 取倒數（資料需 > 0）。
10. **題**：Taking logarithm transformation for the response *Y* means we are fitting a multiplicative model such as $Y = \exp(b_0)\exp(b_1X_1)\exp(b_2X_2)\exp(e)$。
    - **Sol. 正確**
      - $\ln Y=b_0+b_1X_1+b_2X_2+e \Rightarrow Y=\exp(b_0)\times\exp(b_1X_1)\times\exp(b_2X_2)\times\exp(e)$

**這回答什麼行銷/商業問題**
- 第 1 題＝「為什麼我的模型整體很準，但每個渠道的貢獻都不顯著？」→ 渠道投放量高度同動（共線），要看 VIF，不能下「渠道沒用」的結論。
- 第 2 題＝「刪掉一個變數 $R^2$ 會不會變好？」→ 不會；要用 Adjusted $R^2$ 或 AIC 才是公平比較。
- 第 6 題＝**階層原則**，做報酬遞減曲線（$X, X^2$）時不能因為一次項不顯著就砍掉。
- 第 10 題＝log 反應變數等於在配**乘法（彈性）模型**，係數要用百分比語言解讀，這是行銷 ROI 常見設定。

### 2.2 Coding：COLLGPA 四題（線性 → 完整二次 → 巢狀 F → Cook's D）

**資料集特徵**：`COLLGPA.txt`，`read.table(header = TRUE)`；欄位 `Y`（反應，大學 GPA）、`X1`、`X2`（兩個連續解釋變數）。樣本內至少有 ID 28 以上的觀測（Cook's D 答案指到 ID 28）。

**四個提問（依原文答案反推的題序）**
1. 線性模型 $Y \sim X_1+X_2$ 的 $\beta_1, \beta_2, R^2$？
2. 加入 $X_1X_2, X_1^2, X_2^2$ 的完整二次模型中，這三個新變數的係數與模型 $R^2$？
3. 線性 vs 完整二次的巢狀比較 F 統計量？
4. Cook's distance 最高與第二高的觀測 ID？

**答案（原文）**
1. $\beta_1=0.0280$；$\beta_2=0.0261$；$R^2=0.5545$
2. $\beta_{x_1x_2}=0.0009$；$\beta_{x_1^2}=-0.0011$；$\beta_{x_2^2}=-0.0011$；$R^2=0.9305$
3. $\text{F-statistics}=61.3536$
4. the highest Cook's distance $=9$；the second Cook's distance $=28$
   （即：Cook's D 最高的觀測 ID 為 9，第二高為 28）

**R 程式碼（原文照錄，含 `>` 提示符與分段註記）**

```r
########  指定絕對路徑   ########
fp <- "C:/Users/user/Desktop/商管統計資料分析/Quiz2/COLLGPA.txt"

## Read data
GPA <- read.table(fp, header = TRUE)
    attach(GPA)
## Summary
lm1 <- lm( Y ~ X1+X2, data=GPA)
summary(lm1)

########  第一題完成   ########

## 產生三個新解釋變數
GPA$X1X2 <- GPA$X1 * GPA$X2
GPA$X1sq <- GPA$X1^2
GPA$X2sq <- GPA$X2^2

## 配適完整二次模型：Y ~ X1 + X2 + X1X2 + X1^2 + X2^2
lm.q2 <- lm(Y ~ X1 + X2 + X1X2 + X1sq + X2sq, data = GPA)
summary(lm.q2)

> ## 抽出三個「新加入」變數的係數與 R^2 (比較方便看)
> b_X1X2  <- coef(lm.q2)[["X1X2"]]
> b_X1sq  <- coef(lm.q2)[["X1sq"]]
> b_X2sq  <- coef(lm.q2)[["X2sq"]]
> R2_full <- summary(lm.q2)$r.squared

########  第二題完成   ########

## 簡化模型（線性）
lm_lin  <- lm(Y ~ X1 + X2, data = GPA)

## 完整二次模型（平方用 I()，交乘用 :）
lm_full <- lm(Y ~ X1 + X2 + I(X1^2) + I(X2^2) + X1:X2, data = GPA)

## 巢狀模型比較，F 值在第二列
anova_lin_full <- anova(lm_lin, lm_full)
anova_lin_full    

# 顯示要填寫的 F-statistic  
F_value <- anova_lin_full$F[2]
F_value             

########  第三題完成   ########

cook_full <- cooks.distance(lm_full)

## 圖：縱軸 Cook's D，橫軸為 ID
plot(cook_full, xlab="ID number", ylab="Cook's distance")

## 最高的 Cook's D 與其 ID
max1 <- max(cook_full)
cook_full[cook_full == max1]

## 第二高：先排除等於第一高的值，再取最大
max2 <- max(cook_full[cook_full < max1])
cook_full[cook_full == max2]

########  第四題完成   ########
```

**可直接複製的三個 R 慣用法**
1. **兩種等價寫法並存**：手動造欄（`GPA$X1sq <- GPA$X1^2`）與公式內寫法（`I(X1^2)`、`X1:X2`）。手動造欄的好處是 `coef()[["X1sq"]]` 取值方便。
2. **巢狀比較固定套路**：`anova(reduced, full)`，F 值在**第二列**（`anova_lin_full$F[2]`）。
3. **找第二大值的慣用法**：`max(x[x < max(x)])`，避開 `sort()` 後還要回頭找 ID 的麻煩。

**結論寫法**：四題各自只回報「要填的那幾個數字」，$R^2$ 從 0.5545 → 0.9305 的躍升與 $F=61.35$ 兩者互相印證（大幅解釋力提升＋巢狀檢定顯著），但原文**沒有**額外寫論述句。這是一種「數字自證」的極簡結論體。

---

## 3. Quiz 3 ★ — O2O_spending：完整的行銷迴歸建模五步階梯

**頁面**：Quiz 3 — https://app.notion.com/p/28f2b4ffdf0b80a99fc4e442e25d1baf
這是本批材料**唯一的真行銷資料集**，也是最完整的一條「EDA → 轉換 → 全模型 → 共線性 → 淘汰 → 交互作用 → 自動選模 → 精簡 → 巢狀比較」流水線。以下加倍詳述。

### 3.1 觀念判讀（是非題，8 題原文）

1. **題**：In the testing-based procedures, the removal of less significant predictors has no impact on the significance of the remaining predictors.
   - **錯誤**
   - 拿掉變數會改變其他係數/標準誤與 $\text{p-value}$。
     - 係數與其標準誤是**模型相依**的。
     - 移除變數會改變其他變數與「其餘自變數」的相關（$R_j^2$），進而改變
       $\mathrm{Var}(\hat\beta_j)=\dfrac{\sigma^2}{\mathrm{SST}_{X_j}(1-R_j^2)}$ 與 $\text{p-value}$
     - 在共線時甚至會出現符號翻轉。
2. **題**：To check the constant variance assumption in models with a dummy variable, use comparison boxplots of *y* versus the categorical variable.
   - **正確**
   - 有 dummy（類別變數）時，畫 $Y$ 對組別的箱型圖來比較兩組變異是否相當（等變異）。
     - 分組箱型圖能先抓到組間變異量差異
     - 建模後再看「**分組殘差**的箱型圖／殘差 vs. 預測值」更貼近假設檢查。
3. **題**：The simplest of all variable selection procedures and can be easily implemented without special software is backward elimination.
   - **正確**
   - Backward elimination 用 $\text{Partial F}$／最大 $\text{p-value}$ 逐步刪除，邏輯簡單、手動也做得起來。
4. **題**：The variables dropped from the model may still be related to the response.
   - **正確**
   - 被刪掉的不顯著變數仍可能與 y 有關（例如與其他自變數高度相關或樣本力不足）。
     - 不顯著可能是因樣本力不足或與其他自變數高度相關（訊息被分攤），不是「完全無關」的同義詞。
5. **題**：AIC is a criterion-based variable selection procedure, and it can be easily carried out in R using `AIC(fit)`, where fit is an lm object.
   - **正確**
   - AIC 是典型的準則式選模法；在 R 用 `AIC(fit)` / `AIC(model1, model2, …)` 就能比。
6. **題**：Adjusted $R^2$ is one type of criterion-based variable selection procedures.
   - **正確**
   - Adjusted $R^2$ 也是一種準則式比較指標（懲罰變數數量）。
     - 它對 $R^2$ 加上參數數量的懲罰，常用來在同一資料上比較巢狀或近似巢狀模型。
7. **題**：If the multiple regression implies parallel fits, the slope of the dummy variable is the difference between the two fitted lines.
   - **錯誤**
   - 平行斜率模型裡，dummy variable 的係數＝**截距差**，不是斜率差（斜率相同）。
8. **題**：The purpose of an interaction is to force fits in the groups to be parallel.
   - **錯誤**
   - 交互作用是**允許斜率不同**（不平行），不是要把各組強迫成平行。

**這回答什麼行銷問題**
- 第 1、4 題＝「這個變數不顯著，是不是就可以從行銷模型裡刪掉、宣告它沒用？」→ 不行，尤其在渠道變數彼此相關時。
- 第 7、8 題＝**分眾建模的兩種假設**：只放 dummy（例：email 訂戶）＝假設兩群「水準不同、斜率相同」（平行線，截距差＝群體基線差）；加交互作用＝允許「同一驅動因子對兩群的邊際效果不同」。這正是「效果是否因分眾而異」的統計語言。

### 3.2 資料集特徵：`O2O_spending.csv`

由程式碼可完整還原的欄位清單（原文所使用者）：

| 欄位 | 型態 | 在分析中的角色 | 處理方式 |
|---|---|---|---|
| `store.spend` | 連續（金額，>0 才有意義） | **反應變數** | 取 `log(store.spend)`；先以 `store.trans > 0` 篩選 |
| `store.trans` | 連續／計數（線下交易次數） | 解釋變數，同時是**樣本篩選條件** | `log(store.trans)`；`subset(O2O, store.trans > 0)` |
| `online.spend` | 連續（金額，含 0） | 解釋變數 | `log(online.spend + 1)`（EDA 段用 `log1p()`） |
| `online.trans` | 計數（含 0） | 解釋變數 | `log(online.trans + 1)` |
| `online.visits` | 計數（含 0） | 解釋變數 | `log(online.visits + 1)` |
| `age` | 連續 | 解釋變數 | 原尺度不轉換 |
| `distance.to.store` | 連續（距離） | 解釋變數 | `log(distance.to.store)` |
| `gender` | 類別（Female / Male） | dummy | `relevel(as.factor(gender), ref="Female")` |
| `email` | 類別（no / yes） | dummy | `relevel(as.factor(email), ref="no")` |

**資料規模**：篩選後 `nrow(O2O.off)` = **475**（有線下成功交易的客戶數）。

**關鍵資料處理決策（原文註解可見的三個判斷）**
1. **樣本範圍**：`subset(O2O, store.trans > 0)`，原註解寫「只保留『有線下成功交易』的客戶（與 `store.spend > 0` 等價）」。理由是反應變數要取 log，0 不能取 log。
2. **含 0 的自變數用 `+1`**：`log(x+1)` / `log1p(x)`，因為線上行為變數存在 0。
3. **基準組明示**：gender 基準 Female、email 基準 no，讓係數解讀方向固定（`emailyes` 就是「訂閱者 − 未訂閱者」）。

### 3.3 Coding 1：EDA 與轉換決策（答案 a–d）

**答案（原文）**
- (a) **475**
- (b) **Natural log transformation**
- (c) **log(store.spend)**
- (d) **gender**

**頁內附圖**：一張 side-by-side 箱型圖（`log(store.spend)` 分別對 gender 與 email 作圖）。圖片以 Notion 簽章 URL 嵌入、無法長期保存；答案 (d) 為 `gender`，對應「兩張箱型圖中哪一個類別變數看起來對 log 消費有（較明顯的／該題所問的）效果」。

**R 程式碼（Coding 1，原文照錄）**

```r
## Read data（自己改路徑）
O2O <- read.csv("C:/Users/user/Desktop/商管統計資料分析/Quiz3/O2O_spending.csv", header=TRUE)
attach(O2O)

summary(O2O)
table(gender); table(email)

## 只保留「有線下成功交易」的客戶（與 store.spend > 0 等價）
O2O.off <- subset(O2O, store.trans > 0)
nrow(O2O.off)     # ==> (a) 475

## EDA：檢視反應變數分布與對數後的改善
par(mfrow=c(1,2))
hist(O2O.off$store.spend, main="store.spend", xlab="store.spend")
hist(log(O2O.off$store.spend), main="log(store.spend)", xlab="log(store.spend)")

## 建議的轉換（後續建模可直接使用）
O2O.off$log_store      <- log(O2O.off$store.spend)        # 反應變數
O2O.off$log_ospend     <- log1p(O2O.off$online.spend)     # 自變數（含0）
O2O.off$log_otrans     <- log1p(O2O.off$online.trans)
O2O.off$log_ovisits    <- log1p(O2O.off$online.visits)

## 兩張 side-by-side 箱型圖（觀察兩個類別自變數的潛在效果）
par(mfrow=c(1,2))
boxplot(log_store ~ gender, data=O2O.off,
        ylab="log(Store spending)", xlab="gender", col="gray90")
boxplot(log_store ~ email,  data=O2O.off,
        ylab="log(Store spending)", xlab="email",  col="gray90")

## （若要延伸到 ANCOVA/回歸）
# lm.o2o <- lm(log_store ~ log_ospend + log_otrans + log_ovisits + gender + email, data=O2O.off)
# summary(lm.o2o)
# par(mfrow=c(2,2)); plot(lm.o2o)
```

**EDA 的四個固定動作（可直接抄成 checklist）**
1. `summary(資料)` 看全部欄位的分布與 NA；
2. `table(類別變數)` 逐一看類別水準與各水準樣本數（確認沒有極小組）；
3. `hist(y)` 與 `hist(log(y))` **並排**，用圖決定要不要取 log（原文答案 (b)(c) 就是這一步的產出）；
4. `boxplot(y ~ 類別變數)` 每個 dummy 各一張，同時做兩件事：看效果、順便檢查等變異假設（呼應是非題第 2 題）。

### 3.4 Coding 2：五個模型的階梯式選模（答案 e–l）

**答案（原文）**
- (e) **10**
- (f) **8**
- (g) **5**
- (h) **3**
- (i) **8**
- (j) **log(online.visits + 1)**
- (k) **Yes**
- (l) **4**

**模型階梯（依程式碼還原）**

| 步驟 | 模型 | 規格 | 決策依據 / 產出 |
|---|---|---|---|
| M1 | 全變數主效果 | `log(store.spend) ~ age + log(distance.to.store) + log(store.trans) + log(online.trans+1) + log(online.visits+1) + log(online.spend+1) + email + gender` | 起點模型；跑 `vif(model1)`，註解寫「threshold ~ 10」；(k) 也在此模型讀 `emailyes` 的符號與 $p$ 值 |
| M2 | 淘汰最大 $p$ 值 | M1 減去 `log(online.spend+1)` | 原註解：「Highest p-value is log(online.spend+1)」→ testing-based backward 的一步 |
| M3 | 加 8 個交互項 | 4 個連續變數（age、log 距離、log store.trans、log(online.visits+1)）× {email, gender} | `k_inter_m3 <- sum(grepl(":", names(coef(model3))))` → **8**（對應 (f)） |
| M4 | `step()` 自動選模 | `model4 <- step(model3, trace=0)` | `removed_by_step` → **5**（對應 (g)）；`g_inter_m4`（含 gender 的交互項數）→ **3**（對應 (h)） |
| M5 | 最終模型 | `update(model4, . ~ . - gender)`：移除 $p$ 值接近 1 的 `gender` 主效果、保留其交互項 | `summary(model5)` 讀顯著變數個數（(i)）與線上主效果誰顯著（(j)） |
| 比較 | 巢狀 ANOVA | `anova(model5, model4)`、`anova(model5, model3)`、`anova(model4, model1)` | 前兩個合法（巢狀），第三個 R 會警告 "Models are not nested"；(l)=4 |

**R 程式碼（Coding 2，原文照錄，含全部註解）**

```r
## Read data
O2O <- read.csv("C:/Users/user/Desktop/商管統計資料分析/Quiz3/O2O_spending.csv",
                header=TRUE, stringsAsFactors=FALSE)

## Factors (set baselines: Female / no)
O2O$gender <- relevel(as.factor(O2O$gender), ref="Female")
O2O$email  <- relevel(as.factor(O2O$email),  ref="no")

## Keep customers who had offline transactions
O2O.off <- subset(O2O, store.trans > 0)
attach(O2O.off)

####---------------------------####
####  (a) Count & EDA           ####
####---------------------------####
n_offline <- nrow(O2O.off); n_offline      # 475

par(mfrow=c(1,2))
boxplot(log(store.spend) ~ gender, xlab="gender", ylab="log(store.spend)")
boxplot(log(store.spend) ~ email,  xlab="email",  ylab="log(store.spend)")
par(mfrow=c(1,1))


####---------------------------####
####  Model 1: Full MLR         ####
####---------------------------####
model1 <- lm(
  log(store.spend) ~ age +
    log(distance.to.store) + log(store.trans) +
    log(online.trans + 1) + log(online.visits + 1) + log(online.spend + 1) +
    email + gender
)
summary(model1)

## VIF (threshold ~ 10)
library(car)
vif(model1)


####---------------------------####
####  Model 2: Drop largest p   ####
####---------------------------####
## Highest p-value is log(online.spend+1)
model2 <- lm(
  log(store.spend) ~ age +
    log(distance.to.store) + log(store.trans) +
    log(online.trans + 1) + log(online.visits + 1) +
    email + gender
)
summary(model2)

####  Model 3: Add 8 interaction terms         ####
####  (continuous) × {email, gender}           ####
model3 <- lm(
  log(store.spend) ~
    age + log(distance.to.store) + log(store.trans) + log(online.visits + 1) +
    email + gender +
    age:email + age:gender +
    log(distance.to.store):email + log(distance.to.store):gender +
    log(store.trans):email + log(store.trans):gender +
    log(online.visits + 1):email + log(online.visits + 1):gender
)
summary(model3)
k_inter_m3 <- sum(grepl(":", names(coef(model3)))); k_inter_m3   # 8


####  Model 4: step() selection ####
model4 <- step(model3, trace=0)
summary(model4)

removed_by_step <- (length(coef(model3)) - 1) - (length(coef(model4)) - 1)
removed_by_step    # 5

g_inter_m4 <- sum(grepl(":", names(coef(model4))) & grepl("gender", names(coef(model4))))
g_inter_m4          # 3

####  Model 5 (Final): drop near-1 p main effect    ####
####  remove 'gender' main effect, keep interactions ####
if (any(grepl("^gender", names(coef(model4))))) {
  model5 <- update(model4, . ~ . - gender)
} else {
  model5 <- model4
}
summary(model5)

sig_in_final <- sum(summary(model5)$coef[-1,4] < 0.05); sig_in_final  # 7


##  SHOW outputs for (i)(j)(k)(l) — 用看的（老師風格）  ##

## (i) 顯著變數數量：看下面這份最終模型摘要
summary(model5)

## (j) 三個線上相關主效果誰顯著？在最終模型中的主效果：
##     log(online.trans+1) / log(online.visits+1) / log(online.spend+1)
##     直接從 summary(model5) 的 Coefficients 區塊判讀。
## （輔助：印出名稱交叉檢視）
interested <- c("log(online.trans + 1)", "log(online.visits + 1)", "log(online.spend + 1)")
intersect(rownames(summary(model5)$coef), interested)

## (k) email 是否讓到店消費較低？用只有主效果的 Model 1 直接閱讀係數與 p 值
summary(model1)      # 看 emailyes 的 Estimate（負）與 p-value（顯著）

## (l) 巢狀模型比較（ANOVA 表）
anova(model5, model4)    # 有巢狀，合法比較（縮減：移除 gender 主效果）
anova(model5, model3)    # 有巢狀，合法比較（M5 是 M3 的縮減）
anova(model4, model1)    # 非巢狀，R 會警告 "Models are not nested"

detach(O2O.off)


model8 <- lm(
  log(store.spend) ~ age +
    log(distance.to.store) + log(store.trans) +
    log(online.trans + 1) + online.visits ) + log(online.spend + 1) +
    email + gender
)
```

**頁尾補充（原文）**
- 「(i),(j),(k) 可以直接用 summary 後看著報表回答」
- 修正版 model8 公式：`model8 <- lm(log(store.spend) ~ age + log(distance.to.store) + log(store.trans) + log(online.trans + 1) + online.visits + log(online.spend + 1) + email + gender)`
  （即：把 `online.visits` 以**原尺度**放入，其餘維持 log 轉換，用來對照「該不該對 visits 取 log」。）

【評註】上面 code block 最後那段 `model8` 在原文中括號放錯（`online.visits ) +`），無法執行；頁尾那行文字才是正確版本。轉錄時兩者都保留。

### 3.5 這一份的行銷結論寫法（重點）

原文的結論表現形式是**填空式答案 + 「看報表回答」的指示**，可歸納出三種結論句型：

1. **規模型結論**：「(a) 475」——先講清楚分析母體是誰（有線下交易的 475 位客戶），這是所有後續百分比與係數的適用範圍。
2. **方法型結論**：「(b) Natural log transformation／(c) log(store.spend)」——明確交代反應變數做了什麼轉換，因為這決定後續係數要用**百分比／彈性**語言解讀（呼應 Quiz 2 第 10 題的乘法模型）。
3. **方向型結論**：「(k) Yes」＋程式註解「看 `emailyes` 的 Estimate（負）與 p-value（顯著）」——**先看符號、再看顯著性、最後才下 Yes/No**。這句對應的商業結論是：**email 訂閱者的到店消費顯著較低**（在只含主效果的 Model 1 中）。
4. **哪個變數在最終模型仍站得住**：「(j) log(online.visits + 1)」——三個線上行為變數（spend / trans / visits）互相高度相關，最後留下且顯著的是**造訪次數**，不是線上金額。這是典型的「共線變數群裡只留一個代表」結果。

**這回答什麼行銷問題（整份 Quiz 3）**
- **通道互蠶食 / O2O 交互**：線上行為（造訪、交易、金額）與到店消費是正相關還是替代？→ 最終模型保留 `log(online.visits+1)`。
- **名單（email 訂閱）的價值方向**：訂閱者到店消費更低（顯著），提醒「訂閱 ≠ 高價值」，且這是觀察性關聯，不能直接說 email 造成消費下降（呼應 Quiz 5 的因果警告）。
- **分眾異質性**：`step()` 後仍留下 3 個含 gender 的交互項，代表**某些驅動因子的效果對男女不同**；而 gender 主效果 $p\approx 1$ 被移除，意思是「基線水準沒差、但反應斜率有差」。
- **地理與忠誠度**：`log(distance.to.store)`（到店距離）與 `log(store.trans)`（到店次數）是模型骨幹變數，對應「門市可及性」與「消費頻次」兩個行銷槓桿。

---

## 4. Quiz 4 — ANOVA 與實驗設計：多重比較與交互作用

**頁面**：Quiz 4 — https://app.notion.com/p/29f2b4ffdf0b80508c4af6922c61b8e1

### 4.1 觀念判讀（10 題，原文完整）

1. **題**：The intercept in a regression of Y on a dummy variable X is the difference between the mean of Y for observations with x=0 and the mean of Y for observations with x=1.
   - **False**
     - 在 ANOVA 的迴歸模型觀點中，若採用 reference coding，設 $\alpha_1=0$，截距代表基準組（即虛擬變數 $X=0$ 的那一組）的母體平均數期望值。
     - 截距本身並非差異。
     - 差異（即 $X=1$ 的平均數減去 $X=0$ 的平均數）是由與虛擬變數 $X=1$ 相關聯的係數所表示。
2. **題**：The one-way ANOVA requires balanced data, with an equal number of observations in each group.
   - **False**
     - One-way ANOVA 的模型架構允許每個處理（水準）的樣本數 $n_i$ 不相等。
     - 若所有處理的樣本數皆相同，則稱為平衡設計（balanced design），平衡設計雖然有助於分析的效率，但並非執行 ANOVA F 檢定的必要條件。
     - 需要相同樣本數（$n_1=n_2=\cdots=n_k$）的假設主要用於特定的多重比較方法，例如杜奇法（Tukey's method）的原始推導。
3. **題**：Suppose an ANOVA meets the required conditions and the F-test rejects the null hypothesis. If the Bonferroni confidence interval for $\mu_1-\mu_2$ does not include zero, then the Tukey confidence interval for $\mu_1-\mu_2$ does not include zero too.
   - **True**
     - Bonferroni correction 在多重比較方法中通常是最保守、最嚴格的方法。當處理（母體）個數 $k$ 較大時，Bonferroni 的聯立信賴區間會比 Tukey HSD 的信賴區間更長（更寬）。
     - 如果較寬鬆或保守的 Bonferroni 信賴區間已經不包含零，表示 $\mu_1$ 和 $\mu_2$ 之間存在顯著差異，則代表該差異足夠大，因此通常更為緊縮的 Tukey 信賴區間也必然會不包含零，因此差異也會被認定為顯著。
4. **題**：The F-statistic depends upon which dummy variable defined as the reference level in the regression model.
   - **False**
     - 無論在迴歸模型中選擇哪一個水準作為基準組（reference level），模型最終計算出來的配適值與殘差都不會改變。
     - F 統計量是基於總平方和（SST）、處理平方和（SSTR）和誤差均方（MSE）計算出來的，這些平方和的值都只取決於殘差和配適值。因此，F 統計量的值與基準水準的選擇無關。
5. **題**：A balanced experiment does not benefit from the use of randomization to assign treatments to the subjects.
   - **False**
     - 隨機化（Randomization）是實驗設計的核心原則之一，目的是將已知或未知的干擾因子的影響平均分散到各處理組中，從而避免系統性偏差。
     - 只有在滿足隨機化原則下，才能在數學模型上假設干擾變數造成的誤差是相互獨立的。
     - 因此，即使是平衡實驗（各組樣本數相等），隨機化對於確保推論的效度和誤差的獨立性仍然是不可或缺的。
6. **題**：A fitted value in a one-way ANOVA is the mean for some group defined by the explanatory dummy variables.
   - **True**
     - 在 One-way ANOVA 模型中，某一樣本觀測值 $Y_{ij}$ 的配適值（$\hat{Y}_{ij}$）是該觀測值所屬的第 $i$ 組的樣本平均數（$\bar{Y}_{i\cdot}$）。
     - 這是因為 ANOVA 假設同一組內的所有觀測值都應該具有相同的期望值 $\mu_i$，而 $\bar{Y}_{i\cdot}$ 是這個期望值的點估計量。
7. **題**：The average of the residuals within a category used in an ANOVA is zero.
   - **True**
     - 在 ANOVA 中，第 $i$ 組的殘差定義為 $e_{ij}=Y_{ij}-\bar{Y}_{i\cdot}$。
     - 由於 $\bar{Y}_{i\cdot}$ 是該組的樣本平均數，根據樣本平均數的定義，該組內所有殘差的總和 $\sum_j e_{ij}$ 必然為零。因此，殘差在該組內的平均數也必須為零。
8. **題**：Suppose that the subjects in an experiment are reused. For example, each person in a taste test samples every product. These data are suitable for a one-way ANOVA.
   - **False**
     - 當實驗中的受試者被重複使用或配對時（例如：每個人都品嚐所有產品），觀測值之間存在相依性。
     - 標準的單因數 ANOVA（完全隨機化設計，CRD）假設各組樣本是相互獨立的，因此不適用於此類相依數據。
     - 這種設計（受試者重複使用，受試者作為區集）應使用隨機區集化設計（Randomized Block Design, RBD），這可視為對 $k$ 個相依母體期望值進行檢定。
9. **題**：The F-test in an ANOVA tests the null hypothesis that all the groups have equal variance.
   - **False**
     - ANOVA 中的 F 檢定所測試的虛無假設是所有組別的母體平均數相等（$\mathrm{H}_0:\mu_1=\mu_2=\cdots=\mu_k$）。
     - 所有組別具有同質變異數（homoscedasticity）是執行 ANOVA F 檢定所需的前提條件，而不是檢定本身的目的。
10. **題**：Bonferroni confidence intervals adjust for all the effect of multiple comparisons.
    - **True**
      - 多重比較程序的目的正是為了調整在進行多組兩兩比較時，整體型一錯誤率（experimentwise error rate, EER）膨脹的問題。
      - Bonferroni 修正法正是透過調整個別比較所使用的 $\alpha$ 水準，以確保所有比較的聯立信賴區間能夠控制住整體型一錯誤率 $\alpha$。

**這回答什麼行銷問題**：第 5、8 題直指**行銷實驗的設計效度**——受試者重複試吃所有產品（同一批用戶看所有創意）不能用 one-way ANOVA，要用區集設計；即使各組人數一樣，隨機分派仍不可省。第 3、10 題是**多重比較的紀律**：比較 5 個品牌就有 10 組配對，不修正 $\alpha$ 會製造假的「顯著差異」。

### 4.2 R-1：Detergent 洗劑 × 水溫（雙因子 + Tukey HSD）

**資料集特徵**：`Detergent_R.csv`（路徑在講義資料夾 `2-03_ANOVA-2`），欄位 `Score`（反應，清洗分數）、`Detergent`（因子，5 水準 A–E）、`Temperature`（因子，3 水準 Cold/Warm/Hot）。因子水準順序**依講義刻意指定**。

**提問**：在不含交互作用的模型下，指定的 10 組品牌配對與 3 組溫度配對，哪些在 $\alpha=0.05$ 下顯著？加入交互作用後，輸出會多出幾組配對比較？

**答案（原文）**

| 配對 | 結果 |
|---|---|
| B − A | No |
| C − A | Significant |
| D − A | Significant |
| E − A | Significant |
| C − B | No |
| D − B | No |
| E − B | Significant |
| D − C | No |
| E − C | No |
| E − D | No |
| Warm − Cold | Significant |
| Hot − Cold | Significant |
| Hot − Warm | Significant |

- 「How many additional pairs of comparisons do you see in the output?」→ $\binom{15}{2}=105$
  （含交互作用時，對 15 個 cell（Detergent:Temperature）做成對比較）

**R 程式碼（原文照錄）**

```r
## 讀資料（自己改路徑）
detergent <- read.csv("C:/Users/user/Desktop/商管統計資料分析/2-03_ANOVA-2/2-03_ANOVA-2/Detergent_R.csv",
                      header=TRUE)

## 因子設定（依講義的順序）
detergent$Detergent  <- factor(detergent$Detergent,  levels=c("A","B","C","D","E"))
detergent$Temperature <- factor(detergent$Temperature, levels=c("Cold","Warm","Hot"))

##  Tukey HSD（不含交互作用）   ##
##  模型：Score ~ Detergent + Temperature

dt.lm1 <- lm(Score ~ Detergent + Temperature, data=detergent)
summary(dt.lm1)
anova(dt.lm1)

## TukeyHSD：會針對每一個主因子各自列出全部兩兩比較
hsd1 <- TukeyHSD(aov(dt.lm1))
hsd1
# ↑ 到這邊為止，區間有包含 0 就是不顯著，未包含 0 就是顯著，可以用看的就好（下面可略）

# 視覺化
par(fig=c(0.12,1,0,1)); plot(hsd1, las=1, cex.axis=0.8)

## ↓這邊是懶人做法，可以直接顯示每個是否顯著↓ ##

## ——依題目指定的配對，輸出是否顯著（alpha=0.05）——
alpha <- 0.05
pick_sig <- function(hsd_table, a, b, alpha=0.05){
  # TukeyHSD 的 rowname 可能是 "B-A" 或 "A-B"，兩者擇一
  k1 <- paste0(b,"-",a)
  k2 <- paste0(a,"-",b)
  rn <- rownames(hsd_table)
  idx <- which(rn %in% c(k1, k2))
  if(length(idx)==0) return(NA)
  if(hsd_table[idx, "p adj"] < alpha) "significant" else "no"
}

## 10 組品牌比較
cat("\n== Detergent pairs (Tukey, no interaction) ==\n")
cat("B - A :", pick_sig(hsd1$Detergent, "A","B", alpha), "\n")
cat("C - A :", pick_sig(hsd1$Detergent, "A","C", alpha), "\n")
cat("D - A :", pick_sig(hsd1$Detergent, "A","D", alpha), "\n")
cat("E - A :", pick_sig(hsd1$Detergent, "A","E", alpha), "\n")
cat("C - B :", pick_sig(hsd1$Detergent, "B","C", alpha), "\n")
cat("D - B :", pick_sig(hsd1$Detergent, "B","D", alpha), "\n")
cat("E - B :", pick_sig(hsd1$Detergent, "B","E", alpha), "\n")
cat("D - C :", pick_sig(hsd1$Detergent, "C","D", alpha), "\n")
cat("E - C :", pick_sig(hsd1$Detergent, "C","E", alpha), "\n")
cat("E - D :", pick_sig(hsd1$Detergent, "D","E", alpha), "\n")

## 3 組溫度比較
cat("\n== Temperature pairs (Tukey, no interaction) ==\n")
cat("Warm - Cold :", pick_sig(hsd1$Temperature, "Cold","Warm", alpha), "\n")
cat("Hot  - Cold :", pick_sig(hsd1$Temperature, "Cold","Hot",  alpha), "\n")
cat("Hot  - Warm :", pick_sig(hsd1$Temperature, "Warm","Hot",  alpha), "\n")

## ↑這邊是懶人做法，可以直接顯示每個是否顯著↑ ##

##  Tukey HSD（含交互作用）                     ##
##  模型：Score ~ Detergent * Temperature       ##

dt.lm2 <- lm(Score ~ Detergent * Temperature, data=detergent)
summary(dt.lm2)
anova(dt.lm2)            # 可看到交互作用顯著

hsd2 <- TukeyHSD(aov(dt.lm2))  
# 會對 15 個 cell（Detergent:Temperature）做成對比較 (因此有 C15取2 = 105 組)
# 慢慢數就是 105 個 #

## ↓這邊也是方便看到結果，上一個步驟其實就可以看出答案了↓ ##

# 檢視總列數（pair 數量）
num_pairs_interaction <- nrow(hsd2[["Detergent:Temperature"]])
cat("\n== Number of pairwise comparisons with interaction ==\n")
cat("Pairs =", num_pairs_interaction, "\n")   # 應為 105

## ↑這邊也是方便看到結果，上一個步驟其實就可以看出答案了↑ ##

# 可視覺化（很多，圖會很長）
par(fig=c(0.12,1,0,1)); plot(hsd2, las=1, cex.axis=0.7)
```

**兩個可重用的分析習慣**
1. **「用看的」優先，程式輔助其次**：原文明白標示「到這邊為止，區間有包含 0 就是不顯著，未包含 0 就是顯著，可以用看的就好（下面可略）」，把自動化判定標為「懶人做法」。判讀規則本身就是結論規則：**Tukey CI 是否跨 0**。
2. **`pick_sig()` 這個小工具**：解決 `TukeyHSD` rowname 方向不定（"B-A" 或 "A-B"）的實務痛點，值得保留成 snippet。

**這回答什麼行銷問題**：五個洗劑品牌×三種水溫＝典型的**產品配方 × 使用情境**測試。結論的商業讀法是：C、D、E 都顯著優於 A；E 也優於 B；但 C、D、E 之間彼此無顯著差異（換句話說「前段班內部打成平手，選最便宜的即可」）；水溫三個水準**兩兩皆顯著**，代表使用情境的影響穩定且強。

### 4.3 R-2：icecream 碗大小 × 勺大小（2×2 因子實驗，$\alpha=0.01$）

**資料集特徵**：`icecream.csv`，**寬表格式**：第 1 欄是 `Scoop`（"2 ounce scoop" / "4 ounce scoop"），第 2–3 欄是兩種碗（17 / 34 盎司）下的取用量。需轉成長表才能建模。`read.csv(..., check.names=FALSE)`。

**提問**：在 $\alpha=0.01$ 下，碗大小、勺大小、以及兩者交互作用是否顯著？

**答案（原文）**
- the bowl size：**Significant**
- the scoop size：**Significant**
- the interaction：**No**
- 原文特別提醒：「注意！這邊設定的顯著水準 $\alpha=0.01$」

頁內另附一張圖（ANOVA/模型報表或交互作用圖；圖片為 Notion 簽章 URL，無法長期保存）。

**R 程式碼（原文照錄）**

```r
## 讀資料（自己改路徑）
ice0 <- read.csv("C:/Users/user/Desktop/商管統計資料分析/Quiz4/icecream.csv",
                 header=TRUE, check.names=FALSE)

## 這份檔案是寬表：第1欄是 Scoop（2/4 ounce），第2~3欄是 Bowl（17/34）
## 僅取需要的三欄並重新命名，便於之後引用
ice <- ice0[, 1:3]
colnames(ice) <- c("Scoop", "Bowl17", "Bowl34")

## 寬表轉長表
s1 <- data.frame(Scoop = ice$Scoop, Bowl = "17", Amount = ice$Bowl17)
s2 <- data.frame(Scoop = ice$Scoop, Bowl = "34", Amount = ice$Bowl34)
ice_long <- rbind(s1, s2)

## 因子化與層級順序設定
ice_long$Scoop <- factor(ice_long$Scoop,
                         levels = c("2 ounce scoop","4 ounce scoop"))
ice_long$Bowl  <- factor(ice_long$Bowl, levels = c("17","34"))

## ↓這邊模型報表出來就可以看出答案了↓ ##

## 模型（含交互作用）：Amount ~ Bowl * Scoop
ice.lm2 <- lm(Amount ~ Bowl * Scoop, data = ice_long)
summary(ice.lm2)
anova(ice.lm2)

## ↑這邊模型報表出來就可以看出答案了↑ ##

## ↓額外做的模型檢驗，可以不做↓ ##

## 交互作用圖
par(mfrow=c(1,2))
with(ice_long, interaction.plot(Bowl,  Scoop, Amount, legend=TRUE))
with(ice_long, interaction.plot(Scoop, Bowl,  Amount, legend=TRUE))

## 盒鬚圖（各主因子）
par(mfrow=c(1,2))
boxplot(Amount ~ Bowl,  data=ice_long, ylab="Amount", xlab="Bowl size")
boxplot(Amount ~ Scoop, data=ice_long, ylab="Amount", xlab="Scoop size")

## 診斷圖
par(mfrow=c(1,2))
qqnorm(residuals(ice.lm2)); qqline(residuals(ice.lm2))
plot(fitted(ice.lm2), residuals(ice.lm2), xlab="Fitted", ylab="Residuals"); abline(h=0, lty=2, col="grey")

## ↑額外做的模型檢驗，可以不做↑ ##

## ↓用 α=0.01 自動判定顯著與否 （懶人做法）↓ ##
alpha <- 0.01
aov_tab <- anova(ice.lm2)
p_bowl <- aov_tab["Bowl", "Pr(>F)"]
p_scoop <- aov_tab["Scoop", "Pr(>F)"]
p_int   <- aov_tab["Bowl:Scoop", "Pr(>F)"]

cat("\nDecision at alpha = 0.01\n")
cat("Bowl size     :", ifelse(p_bowl  < alpha, "significant", "not significant"), "(p =", signif(p_bowl,3), ")\n")
cat("Scoop size    :", ifelse(p_scoop < alpha, "significant", "not significant"), "(p =", signif(p_scoop,3), ")\n")
cat("Interaction   :", ifelse(p_int   < alpha, "significant", "not significant"), "(p =", signif(p_int,3), ")\n")

## ↑用 α=0.01 自動判定顯著與否 （懶人做法）↑ ##
```

**這回答什麼行銷問題**：這是經典的**器具尺寸 → 消費量**行為實驗（碗越大、勺越大，人取用越多？）。結論寫法是三行判定：兩個主效果都顯著、交互作用不顯著 → **兩個設計槓桿各自獨立生效、可以加法式套用**（放大碗與放大勺的效果不互相放大或抵銷）。對包裝／份量設計來說，「交互作用不顯著」本身就是可行動的結論。

**流程亮點（可重用）**：寬表 → 長表（`rbind` 兩個 `data.frame`）→ `factor()` 定序 → `lm(y ~ A*B)` → `anova()` 讀三列 → 交互作用圖 + 分組盒鬚圖 + QQ 圖與殘差圖做假設檢查。原文把後者標為「額外做的模型檢驗，可以不做」，但流程完整保留。

---

## 5. Quiz 5 — 類別資料：列聯表、odds ratio、抽樣設計的限制

**頁面**：Quiz 5 — https://app.notion.com/p/2a82b4ffdf0b8075890fc4d1420a07f5
**體例特色**：這一份的是非題**先抄英文題幹、再翻成中文、再判 True/False、再展開機制**。是六份中論述最完整、最像「小論文」的一份。

### 5.1 觀念判讀（10 題，原文完整）

1. **The chi-squared test of goodness-of-fit finds the expected cell counts based on the distribution of a random variable.**（卡方適合度檢定是根據隨機變數的分佈來計算預期單元格計數）
   - **True.**
     - 在 Goodness-of-fit 下，我們處理的是一個類別型隨機變數 $\mathrm{Y}$，在虛無假設 $\mathrm{H}_0$ 下，假設 $P(Y=j)=\pi_j$（例如某個「已知分配」）。
     - 在這個假設下，樣本大小為 $n$ 時，每個 cell 的期望次數為 $\mu_j = n\pi_j$ 的確是「根據隨機變數的機率分佈」來決定 expected cell counts。
     - 卡方統計量就是用觀察次數 $n_j$ 和這些 $\mu_j$ 的差異來衡量「觀察分佈」與「假設分佈」是否偏離。
2. **If variable X is associated with variable Y, then Y is caused by X.**
   - **False.**
     - 在列聯表與卡方檢定的框架下，我們檢驗的是「統計獨立性 (statistical independence)」，也就是 $P(Y\mid X)=P(Y)$ 是否成立，只要條件分配不同，就稱為兩者具有關聯性。
     - 但這種「關聯性」只是機率分配的差異，並不保證存在因果關係 (causation)。尤其在觀察性資料下，還可能有混雜變數（confounders）介入。
     - 因此，就算卡方檢定顯著（$\text{p-value}$ 很小），頂多只能說「X 與 Y 在統計上有關聯」，不能直接宣稱「X 導致 Y」。
3. **We can use odds and odds ratio to analyze categorical data regardless of the sampling scheme adopted to collect the data.**（原文以紅底標示此題，答案以紅字標 False）
   - **False.**
     - 在 **prospective / cross-sectional / Poisson / multinomial** 等設計下，我們可以估計 $\pi_1,\pi_2$ 等「母體比例」，進而得到 odds $\omega_1,\omega_2$，以及 odds ratio $\phi$。
     - 但是在回溯性抽樣（例如固定「有病 / 沒病」個數，再往回問是否吸菸），樣本設計是「條件在結果上抽樣」，此時：
       - $\pi_1,\pi_2$（母體比例）不可識別。
       - 對應的單一 odds $\omega_1,\omega_2$ 也無法直接從這種抽樣估計出來。
       - **只有 odds ratio $\phi$ 可以被一致估計。**
     - 所以「odds ratio」的確相對穩健、不太受抽樣方案限制，且並非所有的 odds 指標都能用於所有抽樣方案。
4. **The value of chi-squared depends on which variable defines the rows and which variable defines the columns of the contingency table.**
   - **False.**
     - 不論是 Pearson chi-squared $\chi^2$ 還是 likelihood-ratio chi-squared $\mathrm{G}^2$，統計量都是把所有 cell 的 $\dfrac{(n_{ij}-\hat\mu_{ij})^2}{\hat\mu_{ij}}$ 或 $\log(n_{ij}/\hat\mu_{ij})$ 類似的項目加總。
     - 把變數從 row 換去當 column，只是把整張表「轉置」，cell 的集合沒有改變，$\hat\mu_{ij}$ 也只是位置互換，整體加總出來的 $\chi^2$ 會完全一樣。
     - 因此，$\chi^2$ 的值與「誰當 row／誰當 column」無關。
5. **If the percentage of defective items produced by a manufacturing process is about the same on Monday…Friday, then the days of the week is associated with defective items.**
   - **False.**
     - 若反應變數（有缺陷的物品）的比例在解釋變數（星期幾）的每個水準上都相同，則這兩個變數被稱為統計獨立的。
     - 若每一天的缺陷率都差不多，代表 $P(Y=\text{defect} \mid X=\text{Mon}) \approx \cdots \approx P(Y=\text{defect} \mid X=\text{Fri})$
     - 這代表「條件分配在各個 $\mathrm{X}$ 水準上都一樣」的情況，符合統計獨立的定義。
     - 若兩變數獨立，就不會說它們是具有關聯性的；題目方向完全相反，因此是 False。
6. **The chi-squared test of independence requires at least 5 observations in each cell of the contingency table.**
   - **False.**
     - 卡方檢定依賴的是「大樣本下，檢定統計量的抽樣分佈接近 chi-squared」這個漸近結果，實務上常見的經驗法則是：每一 cell 的**預期次數** $\hat\mu_{ij}$ 最好不要太小，常見門檻是 $\hat\mu_{ij} \ge 5$。
     - 題目說「observations ≥ 5」，而且用「requires」，講得像嚴格必要條件，理論上不精確：
       - 有些情況下，就算有少數 cell 的 expected 小於 5，只要整體樣本夠大，卡方近似仍可接受。
       - 真的 expected 很小，可以改用 exact test（例如 Fisher's exact test）或合併類別，而不是說檢定「無法使用」。
7. **Small p-values of the chi-squared test of independence indicate that the data have small amounts of dependence.**
   - **False.**
     - 在獨立性檢定中，$\mathrm{H}_0$ 是「row 與 column 變數獨立」。
     - $\text{p-value}$ 小（例如 $p=0.01$）代表：在 $\mathrm{H}_0$ 成立時觀察到這麼極端或更極端的 $\chi^2$ 值的機率很低，因此有強烈證據拒絕獨立性假設。
     - 「關聯程度強或弱」，是由 odds ratio $\phi$、Cramér's V 等統計量來描述；$\text{p-value}$ 只是告訴你「有沒有足夠證據說不獨立」，並不等於「關聯性有多大」。
8. **Categorical data whose column percentages vary from column to column in the contingency table are associated.**
   - **True.**
     - 獨立性條件可以寫成：$P(Y=j\mid X=i)$ 在所有 $i$ 上相同，也就是對同一個變數 $\mathrm{Y}$，在不同 $\mathrm{X}$ 水準下的條件分配（百分比）一樣。
     - 實務上常用 row percentages 或 column percentages 檢查條件分配是否相同：看「各欄中，row percentage 是否都差不多」、看「各列中，column percentage 是否都差不多」。
     - 「column percentages vary from column to column」表示條件分配已經改變，違反獨立性定義，故為 True。
9. **One difference between hypotheses of homogeneity and of independence lies in whether one thinks of I populations, each with J categories of response, or of a single population with IJ categories of response.**
   - **True.**
     - Hypothesis of homogeneity（同質性）：思考架構是「有多個母體或族群」，每個族群都有相同的一組 $\mathrm{J}$ 類別反應，檢定這些族群的 response distribution 是否相同。
     - Hypothesis of independence（獨立性）：思考架構是「有一個母體」，每個個體同時有兩個分類變數（row factor 與 column factor），共 $\mathrm{I}\times\mathrm{J}$ 個 cell，檢定這兩個變數是否獨立。
     - 雖然數學上兩種檢定都導向類似的列聯表與卡方統計量，但在「抽樣設計」與「概念上的母體想像」上確實是這個差異。
10. **A large chi-squared value tells us that there is strong association between two categorical variables.**
    - **False.**
      - $\chi^2$ 的大小會受樣本量 $n$ 很大影響：當 $n$ 很大時，就算兩變數之間只有非常小的差異，$\dfrac{(n_{ij}-\hat\mu_{ij})^2}{\hat\mu_{ij}}$ 加起來也可能變得很大，導致 $\chi^2$ 大、$\text{p-value}$ 很小。這只代表「有非常強的證據拒絕獨立性」，不代表效應一定很強。
      - 真正描述「關聯性強弱」的，通常是 odds ratio、Cramér's V 等強度指標；$\chi^2$ 本身只是檢定統計量，不是標準化的「強度指標」。
      - 較嚴謹的說法是「A large chi-squared value provides strong evidence against independence」，不能等同於「strong association」。

**這回答什麼行銷問題（極重要的三條界線）**
- **關聯 ≠ 因果**（第 2 題）：卡方顯著只能說「這群人與那群人的轉換率分配不同」，不能說「做了 X 導致 Y」。
- **顯著 ≠ 效果大**（第 7、10 題）：大樣本（行銷資料常態）幾乎必然顯著，所以**必須同時報 effect size（odds ratio）**，否則結論會被 $n$ 綁架。
- **抽樣設計決定你能算什麼**（第 3 題）：如果樣本是「先固定成功/失敗人數再回頭看行為」（回溯抽樣，如流失者 vs 留存者各抽 500 人），**單邊 odds 與母體比例都不可識別，只有 odds ratio 能一致估計**。

### 5.2 R-Code：Drinking & Breast Cancer（2×2 表 → OR → CI → 檢定）

**資料集特徵**：不是讀檔，而是**在程式內手動輸入 2×2 次數**，並用 `gl()` 造因子、`xtabs()` 組表。

| 列（drinking group） | Case | Control |
|---|---|---|
| 4+Drinks（每週 4 杯以上） | 204 | 386 |
| <4Drinks（每週少於 4 杯） | 330 | 658 |

**提問（a)–(i)）與答案（原文）**

| 題 | 問題 | 答案 |
|---|---|---|
| (a) | Response variable | **Breast cancer** |
| (b) | Study type | **retrospective** |
| (c) | Study design | **observational study** |
| (d) | Odds ratio（4+ vs <4） | **1.0538** |
| (e) | ASE for CI | **0.1097** |
| (f) | SE0 for testing | **0.11** |
| (g) | 95% CI for odds ratio | **[0.8498546, 1.3066672]**；填四捨五入版 **[0.8499, 1.3067]** |
| (h) | p-value for $H_0:\text{OR}=1$ | **0.3169** |
| (i) | Association between drinking and breast cancer? | **No** |

**公式對照（由程式碼還原）**

- 比例與 odds：$\hat\pi_i$ 由 `prop.test()$estimate` 取得；$\hat\omega_i=\dfrac{\hat\pi_i}{1-\hat\pi_i}$
- Odds ratio：$\hat\phi=\dfrac{\hat\omega_1}{\hat\omega_2}$；並看 $\log\hat\phi$
- **檢定用的虛無標準誤**（pooled，$H_0:\phi=1$ 下）：
  $\hat\pi_c=\dfrac{n_{\cdot \text{Case}}}{n}$，
  $\text{SE}_0=\sqrt{\sum_i \dfrac{1}{\hat\pi_c(1-\hat\pi_c)\,n_{i\cdot}}}$
- **信賴區間用的 ASE**：$\text{ASE}=\sqrt{\sum_{i,j}\dfrac{1}{n_{ij}}}$
- 95% CI：$\log\hat\phi \pm z_{0.975}\times \text{ASE}$，再取 $\exp(\cdot)$
- 單尾 p 值：$p=1-\Phi\!\left(\dfrac{\log\hat\phi}{\text{SE}_0}\right)$

**R 程式碼（原文照錄）**

```r
####  Case: Drinking & Breast Cancer
####-------------------------------------------------------####

#### Contingency Table --------------------------------------------------------

## 列順序刻意設為：
##   4+Drinks    : 每週喝 4 杯以上
##   <4Drinks    : 每週少於 4 杯
## 行變數是 drinking group，欄變數是是否為乳癌病例 (Case / Control)

y <- c(204,386,      # 4 or more drinks per week: Cases, Controls
       330,658)      # Fewer than 4 drinks per week: Cases, Controls   # listed by row

drink <- gl(2,2,4, c("4+Drinks","<4Drinks"))   # row names
bc     <- gl(2,1,4, c("Case","Control"))       # col names

( case <- xtabs(y ~ drink + bc) )


#### Odds Ratio ---------------------------------------------------------------

ptest <- prop.test(case)
( pi   <- ptest$estimate )                     # pi1.hat, pi2.hat
( odds <- pi/(1 - pi) )                        # odds: omega1.hat, omega2.hat
( phi  <- odds[1]/odds[2] )                    # odds ratio (phi: 4+ vs <4)
log(phi)                                       # log odds ratio


#### Standard Error for Testing Equality (SE0) --------------------------------

nY  <- sum(case[,1]); n <- sum(case)
( pic <- nY / n )                              # pic.hat
( n.r <- apply(case,1,sum) )                   # n1, n2

( se0 <- sqrt( sum( 1 / (pic * (1 - pic) * n.r) ) ) )  # se0, test version

## one-sided p-value for H0: phi = 1 (跟老師講義 Smoking & Lung Cancer 一樣)
( p.value <- 1 - pnorm( log(phi) / se0 ) )


#### ASE for Confidence Interval ----------------------------------------------

( ase <- sqrt( sum(1 / case) ) )               # ASE for CI

( logphi.ci <- log(phi) + c(-1,1) * qnorm(0.975) * ase )
( phi.ci    <- exp(logphi.ci) )                # 95% CI for odds ratio


#### Answers (rounded to 4 decimal places) ------------------------------------

cat("\n(a) Response variable                : Breast cancer\n")
cat(  "(b) Study type                      : retrospective\n")
cat(  "(c) Study design                    : observational study\n\n")

cat(  "(d) Odds ratio (4+ vs <4)           =",
     round(phi, 4), "\n")
cat(  "(e) ASE for CI                      =",
     round(ase, 4), "\n")
cat(  "(f) SE0 for testing                 =",
     round(se0, 4), "\n")
cat(  "(g) 95% CI for odds ratio           =",
     round(phi.ci[1], 4), "to", round(phi.ci[2], 4), "\n")
cat(  "(h) p-value for H0: OR = 1          =",
     round(p.value, 4), "\n")
cat(  "(i) Association between drinking and breast cancer?  : No\n\n")
```

**結論寫法（這份最值得模仿）**
1. **先交代研究性質**：response variable 是什麼、是 retrospective 還是 prospective、是 observational 還是 experimental。這三行決定後面所有數字能講到什麼程度（能不能談因果、能不能算比例）。
2. **再給效果量與不確定性**：OR = 1.0538，95% CI = [0.8499, 1.3067]。
3. **最後判定**：CI **包含 1** → $p=0.3169$ 不顯著 → 「(i) No，無關聯」。
4. **兩種標準誤分工明確**：檢定用 pooled `se0`、信賴區間用 `ase`，兩者**不可混用**。這是這份材料最精細的技術點。

**這回答什麼行銷/商業問題**：這就是「某個行為分群（重度使用 vs 輕度使用）與某個結果（轉換／流失／申訴）之間有沒有關聯、幾倍勝算」的標準做法。CI 是否跨 1 就是決策線；OR ≈ 1.05 這種「方向對但區間跨 1」的結果，商業上要寫成「目前資料不支持兩群有差異」，而不是「重度族群風險高 5%」。

---

## 6. Quiz 6 — GLM 與 Poisson 對數線性模型：計數型 KPI 的建模

**頁面**：Quiz 6 — https://app.notion.com/p/2c12b4ffdf0b80cdb928eff080785bcc

### 6.1 觀念判讀（10 題，原文完整）

1. **An ordinary regression model that treats the response Y as normally distributed is a special case of a GLM, with normal random component and identity link function.**
   - **True.**
     - 這是 GLM 的基礎定義。當隨機成分（Random Component）為 Normal Distribution，且連結函數為 Identity Link，$g(\mu)=\mu$ 時，GLM 就退化回普通最小平方法（OLS）線性迴歸。
     - 此時預測方程式為 $\mu=\beta_0+\beta_1 X$，完全符合線性迴歸的形式。
2. **The three main components of GLM are random component, systematic component, and link function.**
   - **True.**
     - 隨機成分（Random Component）：定義反應變數 $\mathrm{Y}$ 的機率分佈（如：Normal、Binomial、Poisson）。
     - 系統成分（Systematic Component）：定義解釋變數的線性組合 Linear Predictor $\eta=\beta_0+\beta_1X$。
     - 連結函數（Link Function）：連結 $\mathrm{Y}$ 的期望值 $\mu$ 與系統成分的橋樑 $g(\mu)=\eta$。
3. **Two methods for performing significance tests of hypothesis $H_0: b=0$ about parameters in GLMs are Wald's test and likelihood-ratio test.**
   - **True.**
     - Wald's Test：利用 MLE 的大樣本常態性質，計算 $\text{z}=\dfrac{\hat\beta}{SE}$。適合檢定單一係數，報表中的 $\text{z-value}$ 即為此。
     - Likelihood-Ratio Test（LRT）：又稱 Drop-in-Deviance Test。比較完整模型（Full）與限制模型（Reduced）的 Deviance 差異。適合比較巢狀模型或檢定變數整體的貢獻，通常比 Wald Test 更準確。
4. **The MLE of the unknown parameter is defined to be the parameter value for which the probability of the observed data takes its greatest value.**
   - **True.**
     - 我們尋找一組參數 $\beta$，使得在該組參數下，觀察到目前這組數據的機率（Likelihood）最大化。
     - GLM 的配適過程（Fitting Process）就是在解這個最佳化問題。
5. **With a GLM, Y does not need to be normally distributed… But in order to get maximum likelihood estimates, the variance of Y must be constant at all values of predictors.**
   - **False.**
     - 前半段關於 GLM 的描述是對的，但後半段關於「變異數固定（Constant Variance）」是錯的。
     - 同質變異數（Homoscedasticity）是傳統線性迴歸（OLS）的假設。
     - 在 GLM 中（如 Poisson 或 Logistic），變異數通常會隨著平均數改變：例如 Poisson 的 $\mathrm{Var}(Y)=\mu$，Binomial 的 $\mathrm{Var}(Y)=\pi(1-\pi)$。GLM 允許並處理這種變異數不固定的特性。
6. **For most GLMs for categorical responses, the parameters are usually estimated using least squared method.**
   - **False.**
     - GLM 使用的是最大概似法（MLE）。最小平方法（LS）專門用於常態分佈的線性模型。
     - 對於類別資料（二元或計數），誤差不服從常態且變異數不固定，因此 LS 不適用。
7. **While applying the drop-in-deviance test to compare the reduced model with the complete model, we have to specify in R to use F.**
   - **False.**
     - 在標準的 GLM（如 Logistic 或 Poisson）且沒有超額變異（Overdispersion）的情況下，LRT（Drop-in-deviance test）應使用**卡方檢定**。
     - 只有在處理超額變異時會使用 Quasi-likelihood 方法，或是線性迴歸模型時，我們才會改用 F 檢定。
     - 題目未提及超額變異，故預設應為 Chi-square。
8. **When conducting deviance goodness-of-fit test, we are unable to know the likelihood-ratio statistic $G^2$ directly from R output.**
   - **False.**
     - R 輸出報表底部的 "Residual Deviance" 數值，就是概似比統計量 $G^2$，也就是 Deviance 統計量。
     - 我們可以很輕易地從 `summary(model)` 中讀取該數值，並拿它跟自由度比較，或計算 $\text{p-value}$。
9. **Although the maximum likelihood estimators are essentially unbiased, the shapes of the sampling distributions are unknown.**
   - **False.**
     - 根據 MLE 的漸近性質（Asymptotic Properties），當樣本數夠大時，估計量的抽樣分佈會近似常態分佈。
     - 這正是為什麼我們可以計算標準誤（ASE），並使用 Z 分配（Wald Test）來建立信賴區間的原因。
10. **Using Poisson log-linear regression when overdispersion is present, we may apply the quasi-likelihood approach to extend the model by estimating the dispersion parameter.**
    - **True.**
      - 這是處理 Overdispersion 的標準作法。
      - 透過估計離散參數 $\hat{\psi}=\dfrac{\text{Deviance}}{df}$，我們可以校正標準誤 $SE_{quasi}=SE_{MLE}\times\sqrt{\hat{\psi}}$，使推論結果更保守、更誠實，避免因變異數被低估而產生過度顯著的結論。

### 6.2 R-Code：ILdirectorates（Poisson log-linear 完整八問）

**資料集特徵**：`ILdirectorates.txt`，`read.table(header=TRUE)`。欄位：`interlocks`（反應，**計數**：連結董事席次數）、`assets`（連續，資產規模）、`sector`（類別，含 AGR/BNK/FIN/TRN 等）、`nation`（類別，含 CAN/US/UK 等）。
**題目要求的處理**：用 `log2(assets)` 取代 `assets`；`sector`、`nation` 轉 factor（R 預設字母序決定基準組，原文註記 CAN 與 AGR 通常是基準）。

**八個提問與答案（原文）**

| 題 | 問題 | 答案 |
|---|---|---|
| (a) | Model 1（`interlocks ~ log2assets`）的 Null deviance / Residual deviance | Null deviance **3737**；Residual deviance **1904.7** |
| (b) | Model 2（全變數 `log2assets + sector + nation`）的 Residual deviance | **1547.1** |
| (c) | $\alpha=0.05$ 下顯著係數個數 | nation：**2**（US & UK 顯著）；sector：**3**（BNK, FIN, TRN 顯著） |
| (d) | Drop in deviance（Model 1 vs Model 2） | **357.6** |
| (e) | 離散參數 $\hat\psi$ | **6.6115**（> 1 ⇒ 存在超額變異） |
| (f) | 考慮 extra-Poisson variation 後，sector 顯著係數個數 | **1** |
| (g) | `log2(assets)` 增加 1 時 interlocks 增加百分比 | **36.74 %** |
| (h) | US 公司維持的 interlocks 是加拿大公司的百分之幾 | **46.19 %** |

**關鍵公式（由程式碼與註解還原）**
- Drop in deviance：$\Delta D = D_{\text{reduced}} - D_{\text{full}}$，在標準 Poisson 下以卡方分布判讀
- 離散參數：$\hat\psi=\dfrac{\text{Residual Deviance}}{df_{\text{residual}}}$
- Quasi 校正：`summary(glm2, dispersion = psi)`，效果等於把 SE 乘上 $\sqrt{\hat\psi}$
- log-link 係數解讀：倍數 $=\exp(\beta)$；百分比增加 $=(\exp(\beta)-1)\times 100\%$；「percent as many」$=\exp(\beta)\times 100\%$

**R 程式碼（原文照錄）**

```r
####---------------------------------------------------------------####
####  GLM Case Study: Interlocking Directorates (ILdirectorates)
####---------------------------------------------------------------####

# 1. 資料讀取

IL <- read.table("ILdirectorates.txt", header = TRUE)

# 檢查資料結構
# str(IL)

# 題目要求：使用 log2(assets) 代替 assets
IL$log2assets <- log2(IL$assets)

# 確保類別變數是 factor (R 預設會以字母順序決定基準組，CAN 和 AGR 通常是基準)
IL$sector <- as.factor(IL$sector)
IL$nation <- as.factor(IL$nation)

# 2. 回答問題 (a): First Model ----------------------------------------------
# 題目：Fit model using interlocks and log2(assets)

glm1 <- glm(interlocks ~ log2assets, data = IL, family = poisson)
sum_glm1 <- summary(glm1)

cat("==== 問題 (a) ====\n")
cat("Null deviance:", round(sum_glm1$null.deviance, 1), "\n")
cat("Residual deviance:", round(sum_glm1$deviance, 1), "\n\n")


# 3. 回答問題 (b): Second Model (Full Model) --------------------------------
# 題目：Fit model using all possible explanatory variables (log2assets + sector + nation)

glm2 <- glm(interlocks ~ log2assets + sector + nation, data = IL, family = poisson)
sum_glm2 <- summary(glm2)

cat("==== 問題 (b) ====\n")
cat("Residual deviance for model 2:", round(sum_glm2$deviance, 1), "\n\n")


# 4. 回答問題 (c): Standard Significance (Poisson) --------------------------
# 題目：How many coefficients are significant (alpha = 0.05)?

# 提取係數表
coef_table_2 <- coef(sum_glm2)

# 找出 nation 相關的係數 (排除 intercept)
nation_coeffs <- coef_table_2[grep("^nation", rownames(coef_table_2)), ]
# 計算 p-value < 0.05 的個數
sig_nation_count <- sum(nation_coeffs[, 4] < 0.05)

# 找出 sector 相關的係數
sector_coeffs <- coef_table_2[grep("^sector", rownames(coef_table_2)), ]
# 計算 p-value < 0.05 的個數
sig_sector_count <- sum(sector_coeffs[, 4] < 0.05)

cat("==== 問題 (c) ====\n")
cat("Significant coefficients for nation:", sig_nation_count, "\n")
cat("Significant coefficients for sector:", sig_sector_count, "\n\n")


# 5. 回答問題 (d): Drop-in-Deviance Test ------------------------------------
# 題目：Test hypothesis that model 2 is better than model 1 (Drop in Deviance)

# Drop in deviance = Deviance(Reduced) - Deviance(Full)
drop_deviance <- deviance(glm1) - deviance(glm2)

cat("==== 問題 (d) ====\n")
cat("Drop in deviance:", round(drop_deviance, 1), "\n\n")


# 6. 回答問題 (e): Overdispersion / Extra-Poisson Variation -----------------
# 題目：Estimate dispersion parameter (psi)

# 計算方式：Residual Deviance / Residual Degrees of Freedom
psi <- deviance(glm2) / df.residual(glm2)

cat("==== 問題 (e) ====\n")
cat("Estimated dispersion parameter (psi):", round(psi, 4), "\n")
if(psi > 1) cat("結論: 存在超額變異 (Overdispersion)\n\n") else cat("結論: 無明顯超額變異\n\n")


# 7. 回答問題 (f): Significance with Quasi-Likelihood -----------------------
# 題目：After considering extra-Poisson variation, how many sector coefficients are significant?

# 使用準概似法更新模型 (Quasi-Poisson)
# R 的做法是直接在 summary 中加入 dispersion 參數，這會放大標準誤
sum_quasi <- summary(glm2, dispersion = psi)
coef_table_quasi <- coef(sum_quasi)

# 再次檢查 sector 的顯著性 (注意：這時通常是用 t 檢定)
sector_coeffs_quasi <- coef_table_quasi[grep("^sector", rownames(coef_table_quasi)), ]
sig_sector_quasi_count <- sum(sector_coeffs_quasi[, 4] < 0.05)

cat("==== 問題 (f) ====\n")
cat("Significant coefficients for sector (Quasi):", sig_sector_quasi_count, "\n\n")


# 8. 回答問題 (g): Interpretation of log2(assets) ---------------------------
# 題目：Increasing log2(assets) by 1, increase in interlocks is ... percent?

# 係數 (beta) 代表 log(y) 的變化量
# Y 的倍數變化 = exp(beta)
# 增加百分比 = (exp(beta) - 1) * 100
beta_assets <- coef(glm2)["log2assets"]
percent_increase <- (exp(beta_assets) - 1) * 100

cat("==== 問題 (g) ====\n")
cat("Coefficient for log2(assets):", beta_assets, "\n")
cat("Increase in interlocks:", round(percent_increase, 2), "%\n\n")


# 9. 回答問題 (h): Interpretation of Nation (US vs CAN) ---------------------
# 題目：US firm maintains "how many percent as many" interlocks as Canadian firm?

# 基準組 (Reference Level) 是 CAN (因為 nationCAN 不在係數表中)
# US 的係數 beta_US 代表 log(US) - log(CAN)
# US / CAN 的倍數 = exp(beta_US)
# "Percent as many" = exp(beta_US) * 100
beta_US <- coef(glm2)["nationUS"]
percent_as_many <- exp(beta_US) * 100

cat("==== 問題 (h) ====\n")
cat("Coefficient for nationUS:", beta_US, "\n")
cat("US firm maintains:", round(percent_as_many, 2), "% as many interlocks as a Canadian firm.\n")
```

**這回答什麼行銷/商業問題**
- **規模彈性**：`log2(assets)` 每增加 1（＝資產**翻倍**）→ 事件次數增加 **36.74%**。這是最漂亮的「翻倍語言」：把連續變數取 $\log_2$，係數就能直接說成「每翻一倍，Y 增加 X%」，非常適合對業務端溝通（例如「廣告預算翻倍，曝光次數增加 36.7%」）。
- **分眾水準比較**：`exp(nationUS)*100 = 46.19%` → 美國公司只維持加拿大公司 **46.19%** 的席次數。log-link 的 dummy 係數＝**倍率**，不是差額。
- **超額變異的誠實性**：$\hat\psi=6.61$（遠大於 1）→ 用 quasi 校正後，sector 的顯著係數從 **3 個掉到 1 個**。這是本批材料裡最強的一課：**變異被低估時，會憑空生出一堆「顯著」的行銷發現**。任何計數型 KPI（點擊數、購買次數、客訴數）都應先檢查 $\hat\psi$。

---

## 7. 跨 Quiz 綜合：這批材料的分析文體與流程模板

### 7.1 通用分析流水線（六份合起來的最大公約數）

```
1. 讀檔      read.table(fp, header=TRUE) / read.csv(fp, header=TRUE)
             ├─ 路徑一律寫成 fp <- "絕對路徑"，並在註解寫「自己改路徑」
             ├─ 欄名含 - + 空白 → R 會改成 . ，要用改寫後的名字（Quiz 1 的教訓）
             └─ 寬表 → 長表（Quiz 4 icecream）
2. 型態整理  as.factor() → relevel(..., ref="基準組")  或  factor(x, levels=c(...)) 定序
3. 樣本界定  subset(...)，並記錄剩下 n（Quiz 3：store.trans > 0 → n=475）
4. EDA       summary() / table() / hist(y) 與 hist(log(y)) 並排 / boxplot(y ~ 類別)
5. 轉換決策  y 右偏 → log(y)；含 0 的自變數 → log(x+1) 或 log1p(x)
             取 log2 → 係數可講「每翻倍增加 x%」
6. 起點模型  全變數主效果模型 → summary()
7. 共線性    library(car); vif(model)，門檻約 10
8. 精簡      最大 p 值逐步刪除（testing-based）或 step()（AIC, criterion-based）
9. 交互作用  連續 × 類別 全套加入 → 允許分眾斜率不同
10. 比較     anova(reduced, full)（F 在第 2 列）；GLM 用 drop-in-deviance（卡方）
11. 診斷     plot(model) 四張圖 / qqnorm+qqline / fitted vs residuals / cooks.distance()
12. 讀報表   把要回答的數字圈出來（係數、p、R²、F、deviance、psi）
13. 寫結論   數字 + 方向 + 顯著與否 + 適用範圍
```

### 7.2 「結論寫法」的五種句型（從六份中歸納，皆有原文對應）

| 句型 | 原文例 | 使用時機 |
|---|---|---|
| 三數並列 + 括號定調 | 「Estimated coefficient 0.2508；p-value 0.2693；R² 0.0210（關係不顯著）」 | 單變數迴歸 |
| 比較擇優 | 「較高的 R² 為 0.3509（B4+E+C 模型較佳）」 | 兩個候選模型／指標 |
| 先符號後顯著 | 「看 emailyes 的 Estimate（負）與 p-value（顯著）」→ 答 Yes | 方向型商業問題 |
| 區間是否跨基準值 | 「95% CI [0.8499, 1.3067]」→ 含 1 → 「(i) No」 | odds ratio、Tukey 配對 |
| 條件式判定並附 p | 「Bowl size : significant (p = …)」「結論: 存在超額變異 (Overdispersion)」 | 多因子 ANOVA、GLM 診斷 |

### 7.3 三個「顯著性判讀」的等價路徑（材料中都出現過）

1. **看 p 值 vs $\alpha$**：`summary()` 報表，注意 $\alpha$ 不一定是 0.05（Quiz 4 R-2 是 **0.01**）。
2. **看信賴區間是否跨臨界值**：Tukey CI 跨 0＝不顯著；odds ratio CI 跨 1＝無關聯。原文明言「可以用看的就好」。
3. **看巢狀模型的整體檢定**：`anova()` 的 F（線性模型）或 drop-in-deviance 的卡方（GLM）。

---

## 8. 可重用資產（Checklists / 決策規則 / 診斷順序）

以下規則**全部有材料出處**，可直接寫進未來的 Skill。

### 8.1 資料載入與清理檢查清單

- [ ] 路徑用變數 `fp <- "..."` 存起來，方便換機器（六份皆此體例）
- [ ] `header = TRUE`；csv 視需要 `check.names=FALSE`（要保留原欄名）或 `stringsAsFactors=FALSE`
- [ ] **欄名有 `-`、`+`、空白** → R 會轉成 `.`，公式要用轉換後的名字（`Best-6`→`Best.6`，`B4+E+C`→`B4.E.C`）
- [ ] 寬表要先轉長表才能建模（`rbind` 兩個 `data.frame`）
- [ ] 類別變數 `as.factor()`；**明示基準組** `relevel(..., ref="…")` 或 `factor(x, levels=c(...))`
- [ ] 樣本篩選條件要寫成一行程式並記錄剩餘 n（可審計）
- [ ] `summary(資料)` + 每個類別變數 `table()`

### 8.2 反應變數／自變數轉換決策規則

| 情況 | 做法 | 出處 |
|---|---|---|
| y 右偏（金額類） | 取 `log(y)`；先用 `hist(y)` 與 `hist(log(y))` 並排確認 | Quiz 3 (b)(c) |
| y 左偏（負偏） | **不要用 log**；用次方轉換（如平方）或反射＋log | Quiz 2 第 7 題 |
| 自變數含 0 | `log(x+1)` / `log1p(x)` | Quiz 3 |
| y 必須 > 0 才能取 log | 用篩選條件界定母體（`store.trans > 0`）並說明 | Quiz 3 (a) |
| 想講「每翻倍增加 x%」 | 自變數取 `log2()`，係數用 $(\exp\beta-1)\times100\%$ | Quiz 6 (g) |
| 反應變數取 log | 等於配乘法模型 $Y=e^{b_0}e^{b_1X_1}\cdots$，係數要用彈性／百分比語言 | Quiz 2 第 10 題 |
| 理論指出反比 $Y\approx a+b/X$ | 對 $1/X$ 迴歸，**不是**對 Y 取倒數 | Quiz 2 第 9 題 |
| 轉換的優先順序 | **先理論、後統計**（經濟／行為／物理理論建議形式） | Quiz 2 第 8 題 |

### 8.3 建模與變數選擇決策規則

1. **起點**：全變數主效果模型。
2. **共線性**：`vif(model)`，門檻約 **10**。若「$R^2$ 高但所有 t 都不顯著」→ 幾乎確定是共線性，須用 VIF 確認，不可下「變數沒用」的結論。
3. **淘汰**：testing-based（每次刪**最大 p 值**那一個）或 criterion-based（`step()`/AIC/Adjusted $R^2$）。
4. **每刪一次就要重看其餘係數**：係數與 SE 是模型相依的，$\mathrm{Var}(\hat\beta_j)=\dfrac{\sigma^2}{\mathrm{SST}_{X_j}(1-R_j^2)}$ 會變，共線時甚至符號翻轉。
5. **階層原則**：有 $X^2$、$X^3$ 就保留 $X$、$X^2$，即使不顯著；必要時中心化 $X$ 後用 partial F 整段檢定。
6. **交互作用**：dummy 主效果＝**截距差**（平行線）；交互項＝**斜率差**（不平行）。要檢驗分眾異質性就加交互項。
7. **主效果 vs 交互項的去留**：材料的做法是「主效果 p 接近 1 → 移除主效果、保留其交互項」（Quiz 3 Model 5）。【評註】這違反一般的階層原則慣例（含交互項時通常保留主效果），屬本材料的特定作法，套用前要意識到爭議。
8. **模型比較必須巢狀**：`anova(reduced, full)`；非巢狀時 R 會警告 "Models are not nested"，該比較無效。
9. **刪變數不會讓 $R^2$ 上升**（只有 Adjusted $R^2$ 可能上升）——用來檢查自己有沒有記錯報表。
10. **被刪掉 ≠ 與 y 無關**：可能只是樣本力不足或訊息被共線變數分攤。

### 8.4 假設檢查與診斷順序（固定五步）

1. `plot(model)` 四張圖（或分開做）：
2. **殘差 vs 配適值** → 檢查 mean zero、constant variance、independence（殘差圖的**主要**用途；找非線性只是附帶）；
3. **QQ 圖**（`qqnorm` + `qqline`）→ 常態性（只影響推論分布，不影響 SSE 的計算）；
4. **有 dummy 時**：`boxplot(y ~ 類別)` 看組間變異是否相當；建模後再看**分組殘差**箱型圖更貼近假設；
5. **影響點**：`cooks.distance(model)` → `plot(cook, xlab="ID number", ylab="Cook's distance")`，找最高與第二高的 ID（第二高用 `max(x[x < max(x)])`）。

### 8.5 ANOVA／實驗設計檢查清單

- [ ] 反應變數連續、因子已 `factor()` 並定序
- [ ] **樣本數不必平衡**才能做 F 檢定；但 Tukey 的原始推導假設各組等 n
- [ ] **受試者被重複使用／配對** → 不能用 one-way ANOVA，要用 Randomized Block Design
- [ ] 即使平衡設計，**隨機分派仍不可省**（否則誤差獨立性不成立）
- [ ] F 檢定的 $H_0$ 是「各組**平均數**相等」；等變異是**前提**不是被檢定的對象
- [ ] 多重比較必修正：`TukeyHSD(aov(model))`；判讀規則＝**CI 是否包含 0**
- [ ] 保守度排序：Bonferroni 比 Tukey 寬（更保守）→ Bonferroni CI 不含 0 ⇒ Tukey CI 也不含 0
- [ ] 配對數量：主效果模型下 $k$ 水準有 $\binom{k}{2}$ 組；含交互作用時對 **cell** 兩兩比較，$I\times J$ 個 cell → $\binom{IJ}{2}$ 組（例：$5\times3=15$ → $\binom{15}{2}=105$）
- [ ] F 統計量**不受基準組選擇影響**（配適值與殘差不變）
- [ ] 交互作用不顯著 ⇒ 兩個設計槓桿可各自獨立套用（可行動的結論）
- [ ] **確認題目的 $\alpha$**（材料中出現過 0.01）

### 8.6 類別資料（列聯表）檢查清單與決策順序

1. **先問三件事**：反應變數是誰？prospective 還是 **retrospective**？observational 還是 experimental？
2. **抽樣設計決定可估參數**：回溯性抽樣下 $\pi_1,\pi_2$ 與單邊 odds $\omega_1,\omega_2$ **不可識別**，只有 **odds ratio $\phi$** 可一致估計。
3. **獨立性的判讀**：條件分配（row% 或 col%）在各水準是否相同；相同＝獨立＝**無**關聯。
4. **卡方值與行列無關**（轉置不變）。
5. **樣本量門檻**：經驗法則是**期望次數** $\hat\mu_{ij}\ge5$（不是觀察次數）；少數 cell 略小仍可接受，真的太小改用 Fisher's exact test 或合併類別。
6. **檢定與強度分開報**：
   - 檢定（是否獨立）→ $\chi^2$、$G^2$、p 值；
   - 強度（關聯多大）→ odds ratio、Cramér's V。
   - 大 $\chi^2$ / 小 p 只代表「強證據拒絕獨立」，**不等於**強關聯（p 值受 $n$ 影響）。
7. **兩種標準誤不可混用**：檢定 $H_0:\phi=1$ 用 pooled $\text{SE}_0=\sqrt{\sum_i \frac{1}{\hat\pi_c(1-\hat\pi_c)n_{i\cdot}}}$；建 CI 用 $\text{ASE}=\sqrt{\sum_{i,j}1/n_{ij}}$。
8. **CI 在 log 尺度做，再取 exp**：$\exp\left(\log\hat\phi \pm z_{0.975}\text{ASE}\right)$。
9. **最終判定**：CI 是否包含 1。
10. **顯著也不能講因果**（觀察性資料 + 混雜變數）。

### 8.7 GLM／計數資料檢查清單

- [ ] 三成分先講清楚：random component（分布）、systematic component（$\eta=\beta_0+\beta_1X$）、link function（$g(\mu)=\eta$）
- [ ] OLS = normal random component + identity link 的特例
- [ ] 參數用 **MLE**，不是最小平方；MLE 大樣本下**近似常態**（所以能做 Wald 檢定與 CI）
- [ ] GLM **不要求**等變異；Poisson $\mathrm{Var}(Y)=\mu$、Binomial $\mathrm{Var}(Y)=\pi(1-\pi)$
- [ ] 單一係數 → Wald（報表的 z 值）；整組變數／巢狀比較 → **LRT = drop-in-deviance**（更準確）
- [ ] Drop-in-deviance 在標準 Poisson/Logistic 下用**卡方**；只有 overdispersion（quasi）或線性模型才用 F
- [ ] `summary()` 底部的 **Residual Deviance 就是 $G^2$**，可直接與 df 比較做適合度檢定
- [ ] **必查 overdispersion**：$\hat\psi = \dfrac{\text{Residual Deviance}}{df_{\text{residual}}}$；$\hat\psi>1$ ⇒ 有超額變異
- [ ] 修正方式：`summary(model, dispersion = psi)`（等同 $SE_{quasi}=SE_{MLE}\sqrt{\hat\psi}$），並**重跑顯著性判定**
- [ ] log-link 係數解讀三句：倍數 $=\exp\beta$；增加百分比 $=(\exp\beta-1)\times100\%$；「percent as many」$=\exp\beta\times100\%$
- [ ] 用 `log2(x)` 讓係數變成「每翻倍」的語言

### 8.8 可直接複製的 R snippets（材料原生）

```r
# 1) 巢狀模型 F 值取值（F 在第二列）
anova_out <- anova(lm_reduced, lm_full); anova_out$F[2]

# 2) 找第二大值及其 ID
cook <- cooks.distance(model)
max1 <- max(cook);            cook[cook == max1]
max2 <- max(cook[cook < max1]); cook[cook == max2]

# 3) 數交互項個數 / 特定變數的交互項個數
sum(grepl(":", names(coef(model))))
sum(grepl(":", names(coef(model))) & grepl("gender", names(coef(model))))

# 4) step() 刪掉幾個變數
(length(coef(model_before)) - 1) - (length(coef(model_after)) - 1)

# 5) 最終模型中顯著的（非截距）係數個數
sum(summary(model)$coef[-1, 4] < 0.05)

# 6) 依名稱前綴抓一群 dummy 的係數並數顯著個數
ct <- coef(summary(glm_model))
sum(ct[grep("^sector", rownames(ct)), 4] < 0.05)

# 7) Tukey 配對顯著性查詢（處理 rowname 方向不定）
pick_sig <- function(hsd_table, a, b, alpha=0.05){
  rn <- rownames(hsd_table)
  idx <- which(rn %in% c(paste0(b,"-",a), paste0(a,"-",b)))
  if(length(idx)==0) return(NA)
  if(hsd_table[idx, "p adj"] < alpha) "significant" else "no"
}

# 8) 以指定 alpha 自動判定雙因子 ANOVA 三列
aov_tab <- anova(lm(y ~ A*B, data=d)); alpha <- 0.01
ifelse(aov_tab["A","Pr(>F)"] < alpha, "significant", "not significant")

# 9) 手動輸入列聯表
y <- c(204,386, 330,658)                        # by row
r <- gl(2,2,4, c("4+Drinks","<4Drinks"))
c_ <- gl(2,1,4, c("Case","Control"))
tab <- xtabs(y ~ r + c_)

# 10) 離散參數與 quasi 校正
psi <- deviance(glm_full) / df.residual(glm_full)
summary(glm_full, dispersion = psi)
```

### 8.9 「一份分析要交出哪些數字」對照表（依方法）

| 方法 | 必報數字 | 判定規則 |
|---|---|---|
| SLR / MLR | 各係數 Estimate、p-value、$R^2$（必要時 Adjusted $R^2$、RSE、整體 F） | p < α 才談方向 |
| 巢狀模型比較 | F 值（`anova()` 第 2 列）與其 p | 顯著 ⇒ 複雜模型值得 |
| 影響點診斷 | Cook's D 最高／第二高的觀測 ID | 圖上離群者要回頭查資料 |
| 共線性 | 每個變數的 VIF | 門檻約 10 |
| ANOVA | 各因子與交互作用的 F 與 p；配對比較的 CI 與 p adj | CI 跨 0 ⇒ 不顯著 |
| 列聯表 | odds、odds ratio、$\text{SE}_0$、ASE、95% CI、p | CI 跨 1 ⇒ 無關聯 |
| Poisson GLM | Null / Residual deviance、drop-in-deviance、各係數 p、$\hat\psi$、$(\exp\beta-1)\times100\%$ | $\hat\psi>1$ ⇒ 先 quasi 再談顯著 |

---

## 9. 評註（本節為 digest 撰寫者的判斷，非 Notion 原文內容）

1. **Quiz 3 (e)=10 的題目文字未被記錄**。頁面只有答案 (e) 10，而該位置在程式碼中緊接 `## VIF (threshold ~ 10)`，故 (e) 很可能是問「VIF 的判定門檻」。這是推論，非原文明示。同理 (l)=4 的題幹也缺失，只能從三行 `anova()` 比較推測與「巢狀比較的合法/自由度/模型數」有關。若未來要重製這份分析，需回頭補題目原文。
2. **Quiz 3 內部有一處數字不一致**：程式註解寫 `sig_in_final ... # 7`，但答案 (i) 填 **8**。兩者其中之一有誤，材料未交代。
3. **Quiz 3 有兩段語法錯誤的程式碼**：`attach(caraccident)欣`（Quiz 1）與最後的 `model8`（括號放錯）。頁尾以文字給了 model8 的正確式子。轉錄時全部保留原樣。
4. **`attach()` 的使用風險**：材料大量使用 `attach()`（甚至在 `lm()` 中省略 `data=`，如 Quiz 3 的 model1–model5）。這在多資料框環境下容易取錯欄位；Quiz 3 有寫 `detach(O2O.off)` 是好習慣，但 Quiz 1、2 沒有。若做成 Skill，建議改成一律用 `data=` 參數。
5. **Quiz 3 Model 5「刪主效果保留交互項」與階層原則相衝**（Quiz 2 第 6 題自己主張多項式要守階層原則）。材料在多項式上守階層、在交互作用上不守，這個不一致值得在 Skill 中明確表態。
6. **Quiz 5 的 p 值是單尾**（`1 - pnorm(log(phi)/se0)`），原文註明「跟老師講義 Smoking & Lung Cancer 一樣」。單尾/雙尾的選擇會直接改變 p 值（0.3169 vs 約 0.63），使用時務必說明方向性假設。
7. **缺少的環節（若要做成完整 Skill，需自行補足）**：
   - 全流程都沒有做**樣本外驗證／交叉驗證**，模型好壞完全以同一份資料的 $R^2$、AIC、deviance 判定；
   - `step()` 之後**沒有做選模後推論的修正**（p 值會過度樂觀），材料直接讀 `summary()` 的 p 值；
   - Quiz 3 沒有處理**選擇偏誤**：只留 `store.trans > 0` 的客戶等於剖掉「從未到店」的族群，這對「email 是否降低到店消費」的結論是實質限制，原文未討論；
   - 沒有**遺漏值處理**（`na.rm`、`complete.cases`）的任何步驟；
   - Quiz 4/5 幾乎沒有 effect size（除 odds ratio 外），ANOVA 沒有報 $\eta^2$ 或組平均差的實務大小；
   - 除 Quiz 2 的 Cook's D 外，**發現影響點之後要怎麼處置**（保留/剔除/穩健迴歸）沒有任何後續動作。
8. **文體上最值得複製的三點**：(i) 每個結論都先給「要填的數字」再給一句判定，不寫冗餘鋪陳；(ii) 程式碼用 `####  第 n 題完成   ####` 分段，讓程式與問題一一對應，可審計；(iii) 明確區分「用看的就好」與「懶人自動判定」兩層，前者訓練判讀能力、後者保證不手誤。
