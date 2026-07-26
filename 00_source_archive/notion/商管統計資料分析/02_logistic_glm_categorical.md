---
title: "商管統計資料分析 (MBA5045) — 類別資料分析 / Logistic Regression / GLM 全文萃取"
source_type: notion
source_parent:
  title: "商管統計資料分析 (MBA5045)"
  url: "https://app.notion.com/p/2692b4ffdf0b8060ac98f5535dda84a9"
source_pages:
  - title: "1028"
    url: "https://app.notion.com/p/2972b4ffdf0b80f49acad0528bad3aaf"
    id: "2972b4ffdf0b80f49acad0528bad3aaf"
    raw_chars: 12800
    topic: "MLR 收尾：類別變數編碼（指標變數 vs factor）、巢狀模型檢定、step()、殘差/槓桿/Cook's D"
  - title: "1111"
    url: "https://app.notion.com/p/2a82b4ffdf0b802880c6dbce6396b34d"
    id: "2a82b4ffdf0b802880c6dbce6396b34d"
    raw_chars: 86993
    topic: "類別資料分析：比例檢定、odds、odds ratio、列聯表、卡方、獨立性 vs 同質性、McNemar、前瞻 vs 回溯、抽樣設計"
  - title: "1118"
    url: "https://app.notion.com/p/2a82b4ffdf0b80019450f5507cb63e8a"
    id: "2a82b4ffdf0b80019450f5507cb63e8a"
    raw_chars: 231815
    topic: "變數選擇/交互作用回顧 + GLM 三大構件 + Binary Logistic Regression + MLE + 殘差 + Deviance GOF"
  - title: "1125"
    url: "https://app.notion.com/p/2b52b4ffdf0b8005ba93dee6ed8a15ff"
    id: "2b52b4ffdf0b8005ba93dee6ed8a15ff"
    raw_chars: 63953
    topic: "Binomial（分組資料）Logistic Regression、Empirical Logit、Deviance 適合度檢定、Overdispersion 與 Quasi-likelihood"
  - title: "1202"
    url: "https://app.notion.com/p/2b52b4ffdf0b80a1b80bdb3daaac63e3"
    id: "2b52b4ffdf0b80a1b80bdb3daaac63e3"
    raw_chars: 39000
    topic: "Poisson 分配、Log-Linear Model、計數資料模型評估、Extra-Poisson Variation、MLR vs GLM 總對照表"
  - title: "1209"
    url: "https://app.notion.com/p/2c42b4ffdf0b80459f92f26ed089e529"
    id: "2c42b4ffdf0b80459f92f26ed089e529"
    raw_chars: 420
    topic: "空頁（僅有 In-class practical 1 / 2 兩個空 toggle）"
source_pages_not_found:
  - requested_title: "1208"
    requested_id: "2c32b4ffdf0b8011b338c437b3d1033d"
    actual_parent: "作業管理 → 碩二課程 → NTU"
    note: "該 ID 實際上不屬於本課程，內容為『剩食處理 / 台大鬆餅屋 獲利模式發想』的作業管理課筆記，與 logistic/GLM 無關。本課程頁面清單中亦不存在 1208。已在文末『來源盤點』記錄。"
fetched_date: 2026-07-26
fetched_by: "Claude (notion-fetch MCP)"
coverage:
  - "類別資料分析：樣本比例、母體比例、勝算 odds、勝算比 odds ratio、log(OR) 的 ASE 與信賴區間"
  - "兩獨立樣本比例檢定（合併 vs 未合併標準誤）— 行銷 A/B 比較原型"
  - "列聯表、Pearson 卡方、概似比卡方 G²、自由度推導、期望次數"
  - "獨立性檢定 vs 同質性檢定的數學等價與詮釋差異"
  - "McNemar 配對比例檢定"
  - "前瞻性 vs 回溯性研究、五種抽樣設計與各自可估參數"
  - "GLM 三大構件（隨機成份 / 系統成份 / 連結函數）與家族對照"
  - "Binary vs Binomial（未分組 vs 分組）Logistic Regression 的差異 ★重點"
  - "MLE、Wald 檢定、LRT / Drop-in-Deviance 檢定"
  - "Deviance 定義、Deviance 適合度檢定與其適用邊界（分組才能用）"
  - "Deviance 殘差 / Pearson 殘差（binary、binomial、Poisson 三版公式）"
  - "Overdispersion 診斷三步驟與 Quasi-likelihood 校正、Drop-in-Deviance F-test"
  - "Poisson / Log-Linear Model 與 Extra-Poisson Variation"
  - "推論界線：觀察型資料只能談關聯不能談因果、變數被移除的正確說法、回溯性資料只能估 OR"
notation_note: "Notion 使用 $`...`$ 包裹 LaTeX，本檔統一正規化為標準 $...$ / $$...$$，公式內容一字未改。圖片（AWS S3 簽名網址，會過期）以 [圖片] 標記其存在位置，不保留失效網址。"
convention: "【材料原文】= 課程頁面內容（含作者本人的白話註解，皆屬材料）；【評註】= 本次萃取者為了建立行銷 Skill 所加的判斷，非教材內容。"
---

# 商管統計資料分析 (MBA5045) — 類別資料 / Logistic / GLM 完整 digest

> 本檔是**永久本地知識庫**，不是摘要。所有公式、R 程式碼、比較表格、欄位名稱皆逐字保留。
> 閱讀順序建議：Part 1（類別資料，含廣告 A/B 原型）→ Part 2（GLM + binary logistic）→ Part 3（binomial logistic + Deviance + Overdispersion）→ Part 5（可重用資產）。

---

## 目錄

- [Part 0 — 1028：MLR 收尾（類別變數編碼與巢狀檢定）](#part-0)
- [Part 1 — 1111：類別資料分析（比例 / odds / OR / 卡方 / 抽樣設計）](#part-1)
  - [★ 1.4 兩獨立樣本比例比較：「看過廣告 vs 沒看廣告」完整分析（行銷 A/B 原型）](#part-1-4)
- [Part 2 — 1118：GLM 家族與 Binary Logistic Regression](#part-2)
- [Part 3 — 1125：Binomial Logistic（分組資料）、Deviance 適合度、Overdispersion](#part-3)
- [Part 4 — 1202：Poisson / Log-Linear Model 與 MLR vs GLM 總對照](#part-4)
- [Part 5 — 推論界線總整理（作者反覆強調的部分）](#part-5)
- [Part 6 — 可重用資產（可直接寫進新 Skill）](#part-6)
- [Part 7 — 來源盤點與缺漏](#part-7)

---

<a id="part-0"></a>
## Part 0 — 1028：MLR 收尾（類別變數編碼與巢狀檢定）

【評註】這一頁是**線性迴歸**，不是 logistic。但它是 logistic 的直接前置：類別解釋變數如何進模型（指標變數 D1…Dk vs 直接丟 `factor()`）、參考組（reference level）如何選、巢狀模型如何比較——這三件事在 logistic regression 裡完全照搬，只是把 `lm()` 換成 `glm(..., family=binomial)`、把 `anova()` 換成 `anova(..., test="Chisq")`。故完整保留。

### 0.1 Example 1: New HOMES Data

#### 【材料原文】變數定義

- $\mathrm{Y}= \text{sales price of the property}$
- $\mathrm{X}_1=\text{ floor size (thousands of square feet)}$
- $\mathrm{X}_2=\text{ lot size category (from 1 small to 11 large)}$
- $\mathrm{X}_3=\text{ number of bathrooms (half-bathroom counting as 0.2)}$
- $\mathrm{X}_4=\text{ number of bedrooms (between 2 and 6)}$
- $\mathrm{X}_5=\text{ age (standardized:} \frac{(\text{year built} – 1970)}{10}$）
- $\mathrm{Status} = \mathrm{status\ of\ the\ property: “active”, “sold”, “pending”}$
- $\mathrm{D}_7=\text{ indicator for Status of “active listing”}$
- $\mathrm{School} = \mathrm{six\ neighboring\ schools: Fred, Elon, Beck, Aqua, Cloe, and Dior}$
- $\mathrm{D}_8 \;\text{to}\; \mathrm{D}_{12}=\text{indicators for School Elon, Beck, Aqua, Cloe, and Dior, respectively}$

#### 【材料原文】原始解 — 讀檔案

```r
## Read Data ##
HOMES.new <- read.csv("HOMES_new.csv", header=TRUE)
	# colnames(HOMES.new)
	# head(HOMES.new)
```

#### 【材料原文】原始解 — EDA

```r
## EDA ##
attach(HOMES.new)
pairs(HOMES.new[,c(2,3,4,5,6,8)])
	# levels(factor(Status));  levels(factor(School))
	# table(D7);	table(Status);	table(School);	table(X2)

par(mfrow=c(1,2))
boxplot(Y ~ D7, ylab= "Y = sale price in $thousands", xlab= "D7 = indicator for active status")
boxplot(Y ~ School, ylab= "Y = sale price in $thousands", xlab= "nearest school")
```

#### 【材料原文】原始解 — 迴歸模型建立並輸出報表

- Model 1（no transformations or interactions）
- Model 2（with transformation and interaction）

```r
## Model Building ##
mod1 <- lm(Y ~ X1+X2+X3+X4+X5+D7+D8+D9+D10+D11+D12)
summary(mod1)

plot(X5,residuals(mod1),xlab="X5",ylab="Residuals")
abline(h=0, lty=2)

mod2 <- lm(Y ~ X1+X2+X3*X4+X5+X5sq+D7+D8+D9+D10+D11+D12)
summary(mod2)
```

#### 【材料原文】原始解 — 巢狀模型檢驗

```r
## Nested model test ##
anova(mod1, mod2)

plot(X5,residuals(mod2), main="mod2", xlab="X5", ylab="Residuals")
abline(h=0, lty=2)

mod3 <- update(mod2, .~. -D10-D11-D12)	
	# Q: What is the implication of this step?
  	# mod3 <- lm(Y ~ X1+X2+X3*X4+X5+X5sq+X6+D7+D8+D9)
summary(mod3)

anova(mod3, mod2)
```

#### 【材料原文】原始解 — 最終模型

```r
## Final model ##
confint(mod3)

plot(X5, residuals(mod3), main="mod3", xlab="X5", ylab="Residuals")
abline(h=0, lty=2)
```

#### 【材料原文】替代解（較佳解）— 模型設定

```r
mh1 <- lm(Y ~ X1+X2+X3*X4+X5+X5sq+Status+School)
summary(mh1)
```

#### 【材料原文】替代解 — 更改 status 水準

```r
HOMES.new$Status.n <- factor(HOMES.new$Status)
levels(HOMES.new$Status.n) <- list(act="act", nac="pen", nac="sld")
HOMES.new$Status.n <- relevel(HOMES.new$Status.n, ref="nac")

	# detach()
	# attach(HOMES.new)
```

#### 【材料原文】替代解 — 模型 2 建立並摘要

```r
mh2 <- lm(Y ~ X1+X2+X3*X4+X5+X5sq+Status.n+School, data=HOMES.new)
summary(mh2)
```

#### 【材料原文】替代解 — 更改 School 水準後摘要

```r
School <- relevel(factor(School), ref="fred")
mh2.1 <- lm(Y ~ X1+X2+X3*X4+X5+X5sq+Status.n+School, data=HOMES.new)
summary(mh2.1)	#-> the same as mod2
```

#### 【材料原文】替代解 — 將 $\mathrm{X}_2$ 設定為類別變數後建模摘要

```r
mh3 <- lm(Y ~ X1+factor(X2)+X3*X4+X5+X5sq+Status.n+School, data=HOMES.new)
summary(mh3)
```

**這回答什麼行銷/商業問題**：多個門市/通路/學區（類別）在控制其他條件後，對成交價（連續 KPI）是否有系統性差異？哪一個當基準組（reference）會讓報表最好講給老闆聽？

**【評註】** 「原始解」用手刻 D7…D12 指標變數，「較佳解」直接丟 `factor()` + `relevel(ref=)`。兩者數學等價（`mh2.1` 註解寫 `#-> the same as mod2`），但後者可讀性高、不易搞錯水準數。行銷分析上這件事的意義是：**參考組的選擇不改變模型，只改變「係數怎麼被讀出來」**——把「沒投放廣告」設為 ref，所有係數就自動變成「相對於未投放的提升」，簡報就不用再換算。

### 0.2 Example 2: Vehicle Fuel Efficiency Data

#### 【材料原文】變數定義

- $\mathrm{Y}= \text{city miles per gallon (MPG)}$
- $\mathrm{X}_1=\text{ weight (thousands of pounds)}$
- $\mathrm{X}_2=\text{ horsepower (hundreds)}$
- $\mathrm{X}_3=\text{ engine size (liters)}$
- $\mathrm{X}_4=\text{ number of cylinders}$
- $\mathrm{X}_5=\text{ wheelbase (hundreds of inches)}$
- $\mathrm{D}_6=\text{ indicator for sports car (ref: sedan)}$
- $\mathrm{D}_7=\text{ indicator for SUV (ref: sedan)}$
- $\mathrm{D}_8=\text{ indicator for Wagon (ref: sedan)}$
- $\mathrm{D}_9=\text{ indicator for minivan (ref: sedan)}$
- $\mathrm{D}_{10}=\text{ indicator for pick-up truck (ref: sedan)}$
- $\mathrm{D}_{11}=\text{ indicator for all-wheel drive (ref: front-wheel drive)}$
- $\mathrm{D}_{12}=\text{ indicator for rear-wheel drive (ref: front-wheel drive)}$

#### 【材料原文】原始解 — 讀檔案

```r
## Read Data ##
fuel.eff <- read.table("Fuel_eff.txt", header=TRUE, sep="\t")
	colnames(fuel.eff);   summary(fuel.eff)
```

#### 【材料原文】原始解 — EDA

```r
## EDA: scatterplot ##
attach(fuel.eff)
pairs(fuel.eff[,c(5,7,8,9,10,11)])

	which(X4 > 10)		# id: 220 & 259

	table(type);  table(drive)

## boxplot ## 
par(mfrow=c(1,2))
plot(Y ~ factor(type), ylab="Y=city MPG", xlab="type of vehicle")
plot(Y ~ factor(drive), ylab="Y=city MPG", xlab="drive type")
```

#### 【材料原文】原始解 — 建立原始模型，並輸出直方圖後進行摘要

```r
## Model 1 ##
  fuel.mod1 <- lm(Y ~ X1+X2+X3+X4+X5+D6+D7+D8+D9+D10+D11+D12)
  summary(fuel.mod1)

  resfuel.mod1 <- rstandard(fuel.mod1)
  hist(resfuel.mod1)

  resfuel.mod1[resfuel.mod1<(-3)|resfuel.mod1>3]	# two outliers: id: 13 & 88
```

#### 【材料原文】Model 2：倒數轉換後摘要並進行 EDA

```r
## Model 2: reciprocal transformation ##
  fuel.eff$recipX1 <- 1/X1
  fuel.eff$recipX2 <- 1/X2
  fuel.eff$recipX3 <- 1/X3
  fuel.eff$recipX4 <- 1/X4
  fuel.eff$recipX5 <- 1/X5

  fuel.mod2 <- lm(Y ~ recipX1+recipX2+recipX3+recipX4+recipX5+D6+D7+D8+D9+D10+D11+D12, fuel.eff)
  summary(fuel.mod2)

  resfuel.mod2 <- rstandard(fuel.mod2)
  hist(resfuel.mod2)
  qqnorm(resfuel.mod2);  qqline(resfuel.mod2)
	  plot(resfuel.mod2)
  plot(fitted(fuel.mod2), resfuel.mod2, xlab="fitted values", ylab="residuals")

  resfuel.mod2[resfuel.mod2<(-3)|resfuel.mod2>3]		# two outliers: id: 88 & 13 & 64
```

#### 【材料原文】Model 3：移除離群值後摘要並進行 EDA

```r
## Model 3: remove outliers ##
  fuel.effa <- fuel.eff[-c(88,13),]

  fuel.mod3 <- lm(Y ~ recipX1+recipX2+recipX3+recipX4+recipX5+D6+D7+D8+D9+D10+D11+D12, fuel.effa)
  summary(fuel.mod3)

  resfuel.mod3 <- rstandard(fuel.mod3)
  hist(resfuel.mod3)
  qqnorm(resfuel.mod3);  qqline(resfuel.mod3)
	  plot(resfuel.mod3)
  plot(fitted(fuel.mod3), resfuel.mod3, xlab="fitted values", ylab="residuals")
  abline(h=0, lty=2)

  levfuel.mod3 <- hatvalues(fuel.mod3)
  plot(levfuel.mod3, xlab="id",ylab="Leverage")

  cookfuel.mod3 <- cooks.distance(fuel.mod3)
  plot(cookfuel.mod3, xlab="id",ylab="Cook's distance")
```

#### 【材料原文】Model 3 再額外刪減不顯著的指標變數後摘要

```r
## Model 3-reduced: remove insignificant indicators... ##

  fuel.mod3r <- update(fuel.mod3, .~.-D8-D9)
  anova(fuel.mod3r, fuel.mod3)
  summary(fuel.mod3r)
```

#### 【材料原文】最終模型：考慮交乘項

```r
 ## Final model - Interaction considered  ##
	  fuel.eff$recipX1<-1/X1
	  fuel.eff$recipX2<-1/X2
	  fuel.eff$recipX3<-1/X3
	  fuel.eff$recipX4<-1/X4
	  fuel.eff$recipX5<-1/X5
	  fuel.effa<-fuel.eff[-c(88,13),]	# remove outliers...

  fuel.modf <- lm(Y ~ (recipX1+recipX2+recipX3+recipX4+recipX5)*(D6+D7+D8+D9+D10+D11+D12),fuel.effa)
  summary(fuel.modf)

  fuel.mods <- step(fuel.modf)
  summary(fuel.mods)
```

#### 【材料原文】替代解（較佳解）— 倒數轉換 + 移除離群值 + 是否有交乘項的兩模型

```r
fuel.eff <- read.table("Fuel_eff.txt", header=TRUE, sep="\t")
	colnames(fuel.eff)

fuel.eff$type <- relevel(factor(fuel.eff$type), ref="sedan")
fuel.eff$drive <- relevel(factor(fuel.eff$drive), ref="fwd")
fuel.eff$recipX1<-1/X1
fuel.eff$recipX2<-1/X2
fuel.eff$recipX3<-1/X3
fuel.eff$recipX4<-1/X4
fuel.eff$recipX5<-1/X5
fuel.effa <- fuel.eff[-c(88,13),]	# remove outliers...

fuel.mh1 <- lm(Y ~ recipX1+recipX2+recipX3+recipX4+recipX5+type+drive, data=fuel.effa)
summary(fuel.mh1)

fuel.mh2 <- lm(Y ~ (recipX1+recipX2+recipX3+recipX4+recipX5)*(type+drive), data=fuel.effa)
summary(fuel.mh2)

fuel.mh3 <- step(fuel.mh2)
summary(fuel.mh3)

anova(fuel.mh2, fuel.mh3)
```

#### 【材料原文】模型檢驗

```r
## Residual Disgnostics ##

	plot(residuals(fuel.mh3), ylab="Residuals")
	abline(h=0, lty=3)

	qqnorm(resfuel.mh3);  qqline(resfuel.mh3)
```

#### 【材料原文】離群值檢驗

```r
# Outlier
	  resfuel.mh3 <- rstandard(fuel.mh3)
	  hist(resfuel.mh3)
	  resfuel.mh3[resfuel.mh3<(-3)|resfuel.mh3>3]
```

#### 【材料原文】槓桿（leverage）計算

```r
# Leverage
	  levfuel.mh3 <- hatvalues(fuel.mh3)
	  plot(levfuel.mh3, xlab="id",ylab="Leverage")
	  identify(levfuel.mh3, labels=fuel.effa$id)
```

#### 【材料原文】庫克距離（Cook's distance 計算）

```r
	  # Cook's distance
	  cookfuel.mh3 <- cooks.distance(fuel.mh3)
	  plot(cookfuel.mh3, xlab="id", ylab="Cook's distance")
	  identify(cookfuel.mh3, labels=fuel.effa$id)
```

### 0.3 Example 3: Block Cost data

#### 【材料原文】變數

[圖片：變數說明表]

#### 【材料原文】讀檔案

```r
## Read Data ##
cost <- read.csv("block_cost.csv")
	dim(cost);  names(cost)
	summary(cost);  head(cost)
```

#### 【材料原文】清理資料（衍生變數）

```r
## Derived Data ##
cost$recipUnits <- 1/cost$Units
cost$Breakdown.Unit <- cost$Breakdowns/cost$Units
cost$Total.Metal.Cost <- (cost$Weight.Final+cost$Weight.Rem)*cost$Cost.Metal.Kg
cost$SqTempDev <- (cost$Room.Temp-mean(cost$Room.Temp))^2
head(cost)
```

#### 【材料原文】EDA

```r
## EDA ##
table(cost[,13:14])
table(cost[,c(18,15)]);  table(cost[,c(15,18)])

pairs(cost[,c(1:7)])
pairs(cost[,c(1,8:12)])
cor(cost[,4:9])
```

#### 【材料原文】移除離群值

```r
## Remove Outliers ##
plot(cost$Labor.Hours, cost$Average.Cost)
identify(cost$Labor.Hours, cost$Average.Cost)	
costa <- cost[-c(19, 94),]	
	cor(costa[,4:9])
```

#### 【材料原文】建立模型

```r
## Build Model ##
cost.0 <- lm(Average.Cost ~ ., data=costa)
summary(cost.0)
```

#### 【材料原文】以 backward-elimination 進行巢狀模型檢驗

```r
### (1): backward elimination
cost.1 <- update(cost.0, .~. - Manager)
summary(cost.1)
cost.2 <- update(cost.1, .~. - Music - Shift)
summary(cost.2)
anova(cost.2, cost.1)		# Nested-model test

cost.3 <- update(cost.2, .~. - Stamp.Ops)
summary(cost.3)
anova(cost.3, cost.2)

cost.4 <- step(cost.3, data=df_newa)
summary(cost.4)

drop1(cost.4, test="F")		# Drop all possible single terms to a model
```

#### 【材料原文】以 Step 來排序篩選

```r
### (2): start step from full model
cost.01 <- step(cost.0)
summary(cost.01)
drop1(cost.01, test="F")

cost.02 <- update(cost.01, .~. - Manager + Plant)
summary(cost.02)			# same result as summary(cost.4)
```

#### 【材料原文】殘差檢驗

```r
## Residual Disgnostics ##

	par(mfrow=c(1,3))
	plot(fitted(cost.4), residuals(cost.4), xlab="Fitted", ylab="Residuals");abline(h=0)
	hist(residuals(cost.4))
	qqnorm(residuals(cost.4), ylab="Residuals");qqline(residuals(cost.4))
```

**這回答什麼行銷/商業問題**：一整包候選驅動因子（人員、班別、材料成本、溫度…）裡，哪些真的在解釋單位成本？`.~.` 更新語法 + `anova()` 巢狀檢定 + `step()` + `drop1()` 是「一次砍一組變數並留下證據」的標準操作，在行銷歸因模型（media mix、通路貢獻）裡完全可以照抄。

---

<a id="part-1"></a>
## Part 1 — 1111：類別資料分析（比例 / odds / OR / 卡方 / 抽樣設計）

【評註】這一頁分成兩大塊：**「概述」**（作者本人為了自學而寫的白話重構，行銷例子最多、最貼近包子要的東西）與 **「投影片內容」**（課堂投影片的正式版本，含 R code 與 4 個 Case）。兩塊都是材料原文，以下分節保留。

### 1.1 概述 — 二元比較的整體架構

#### 【材料原文】這個章節要講得基本上涵蓋大部分「二元比較」的內容。

**二元比較（Binary comparison）：**

- True or False 的判別，試驗結果非黑即白，或說答案只有 0 or 1 兩種。
- 即是「成敗試驗」，我們關心的總是 $\mathrm{P(Y=1) }$ 或 $\mathrm{P(Y=0) }$ 到底是多少？

**我們定義二元回應（Binary response）如下：**

- 當回應變數 $\mathrm{Y}$ 只有兩種可能：
- $\mathrm{Y = 1}$：事件「有發生」（例如：購買、罹病、死亡）。
- $\mathrm{Y = 0}$：事件「沒有發生」（未購買、未罹病、存活）。

**商業分析裡很常見的例子：**

- 客戶是否完成交易（Yes / No）
- 使用者是否流失（Churn / No churn）
- 折價券是否被兌換（Redeem / Not redeem）

補：後續若有教到邏輯迴歸（Logistic regression）也是根據此概念去延伸。

**這回答什麼行銷/商業問題**：任何「有沒有做某件事」的 KPI——轉換、流失、續約、開信、點擊、兌換——都是二元回應，這一整章就是這類 KPI 的比較工具箱。

#### 【材料原文】母體比例（Population proportion）

對每一個群組，我們都可以定義一個「**發生機率**」：

- 若關心事件「購買」，並定義 $\mathrm{P(Y=1)}$ 表購買機率，則母體比例 $p = \mathrm{P(Y=1)}$ 代表「購買的比例」。

在統計上，我們在意的是兩邊的發生機率差多少？

- 或兩種結果的比例差距在統計上是否顯著？

實務上我們只能看到樣本數據，所以會用樣本比例 $\hat{p}$ 來估計 $p$：

- 例如：
  - 在 100 個看過廣告的人中，有 30 人購買 $\longrightarrow$ $\hat{p}_1 = \frac{30}{100} = 0.30$ 。
  - 在 100 個沒看廣告的人中，有 15 人購買 $\longrightarrow$ $\hat{p}_0 = \frac{15}{100} = 0.15$ 。

#### 【材料原文】母體勝算（Population odds）

**「勝算」可以理解成**另一種描述機率的方式：

- 勝算表示的是「發生」次數**與**「不發生」次數**之間的**比例。
  - $\text{Odds} > 1$**：** 表示事件發生的可能性**大於**不發生的可能性。
  - $\text{Odds} < 1$**：** 表示事件發生的可能性**小於**不發生的可能性。
  - $\text{Odds} = 1$**：** 表示事件發生的可能性**等於**不發生的可能性，即 $p=0.5$。
  - $\text{Odds}$ 的範圍： $[0, \infty)$。
- 舉例：
  - 若 $p = \mathrm{P(Y=1)}$，則 $\text{odds} = \frac{p}{1-p}$ 。
  - 直覺：
    - 若 $p = 0.2 \longrightarrow \text{odds} = \frac{0.2}{0.8}=0.25$ 。
      - 「發生」1 次，約等於「不發生」4 次。
    - 若 $p = 0.8 \rightarrow \text{odds} = \frac{0.8}{0.2} = 4$ 。
      - 「發生」4 次，約等於「不發生」1 次。

**為什麼要用勝算？**

- 在某些實驗設計中，特別是回溯性研究裡，我們很難直接估計機率 $p$，但可以很自然地得到「有事件」與「無事件」的人數，進而算出勝算與勝算比。
- 未來在 logistic regression 中，我們預測的其實是 $log(\text{odds})$，所以需要在這裡先把 odds 的概念建立起來。

$$\text{odds}=\frac{p}{1-p} \Longleftrightarrow p=\frac{\text{odds}}{1+\text{odds}}$$

#### 【材料原文】勝算比（Odds ratio）

有兩個群體時，常用**勝算比（Odds ratio, OR）** 來比較：

- 設第 0 組的勝算為 $\text{O}_0$，第 1 組的勝算為 $\text{O}_1$ 。
- 勝算比：$\text{OR} = \frac{\text{O}_1}{\text{O}_0}$
  - 解讀：
    - $\text{OR} = 1$：兩組在發生機率上的「相對關係」一樣。
    - $\text{OR} > 1$：第 1 組的事件「更常發生」。
      - 例如：$\text{OR} = 2$ $\longrightarrow$ 第 1 組的勝算是第 0 組的兩倍
    - $\text{OR} < 1$：第 1 組的事件「較不容易發生」。
      - 例如 $\text{OR} = 0.5$ $\longrightarrow$ 第 1 組的勝算只有第 0 組的一半。

#### 【材料原文】列聯表（Contingency table）

處理這類二元回應＋兩個群組，最標準的整理方式就是做一個 $2 \times 2$ 的列聯表：

- 以有沒有看廣告為例。

$$\begin{array}{c|cc|c}
  & \text{事件發生 } Y=1 & \text{事件未發生 } Y=0 & \text{總計} \\
  \hline
  \text{第 1 組（有看廣告）} & a & b & a+b \\
  \text{第 0 組（沒看廣告）} & c & d & c+d \\
  \hline
  \text{總計} & a+c & b+d & n
\end{array}$$

從這張表可以：

- 算出每一組的樣本比例：
  - $\hat{p}_1 = \frac{a}{(a+b)}$
  - $\hat{p}_0 = \frac{c}{ (c+d)}$
- 算出每一組的樣本勝算：
  - $\widehat{\text{O}}_1 = \frac ab$
  - $\widehat{\text{O}}_0 = \frac cd$
- 算出勝算比的估計值：
  - $\widehat{\text{OR}} = \dfrac{\frac ab}{\frac cd} = \dfrac{ad}{bc}$

#### 【材料原文】前瞻性（Prospective）與回溯性（Retrospective）研究

**前瞻性（Prospective Study）**

- 先按照「有沒有某個條件／處理」把人分組，再往後追蹤看結果會怎樣。
  - 可以理解成：
    - 有沒有某個因素
    - 有沒有接受某種處理
    - A 組 vs 非 A 組
  - 例如：
    - 找 100 個有抽菸的人、100 個不抽菸的人，追蹤未來 10 年，看誰會得某種疾病。
- 優點：可以直接估計「發生機率」與「風險」。
- 這種設計下，比例、勝算、勝算比都可以直接解釋。

**回溯性（Retrospective / Case-Control Study）**

- 先從「已經發生的結果」開始分組，再回頭去看他們過去有沒有某個條件或處理。
  - 例如：
    - 先找 100 個已經得病的人（cases）
    - 再找 100 個沒得病的人（controls）
    - 回頭問他們過去是否有抽菸。
  - 在這種設計裡，樣本裡的「有病比例」是刻意設計的，不能拿來當母體機率。
  - 但我們仍然可以估計勝算比 (odds ratio)，而且在很多情況下，OR 仍然有很好的解釋力（尤其當疾病很罕見時）。

### 1.2 基礎分配：Bernoulli → Binomial → 樣本比例

#### 【材料原文】伯努力試驗（Bernoulli trials）

- 一次實驗只有兩種可能結果：
  - 成功 （Success）
  - 失敗 （Failure）
- 每次實驗的成功機率相同，記為 $p$。
- 例子：
  - 丟一枚公平硬幣：正面 = 成功；反面 = 失敗。
  - 客戶是否購買：購買 = 成功；沒購買 = 失敗。
  - 病人是否康復：康復 = 成功；未康復 = 失敗。
- 注意！
  - 所謂「成功」只是我們感興趣的那一類，不一定是好事。
  - 在流失分析中，也可以把「流失」定義成 Success，因為我們想研究的是「流失的機率」。

#### 【材料原文】伯努力分配（Bernoulli distribution）

- 伯努力分配是「一次成敗」的機率。
- 定義一個隨機變數 $\mathrm{X}$：
  - $\mathrm{X} = 1$：代表成功發生。
  - $\mathrm{X}=0$：代表成功沒有發生（失敗）。
  - 若 $\mathrm{P(X = 1)} = p$，則我們定義 $\mathrm{P(X = 0)} = 1-p$，我們說：
    - $\mathrm{X} \sim \text{Bernoulli}(p)$
- 「一次成敗試驗的結果」就是一個 $\mathrm{Bernoulli}(p)$ 隨機變數。

#### 【材料原文】二項分配（Binomial distribution）

- 二項分配則是做很多次一樣的成敗試驗，計算「成功了幾次」的機率。
- 假設：
  - 每一次試驗都是獨立的 $\mathrm{Bernoulli}(p)$。
  - 一共做了 $n$ 次。
- 定義 $\mathrm{X}$ 表這 $n$ 次鍾「成功的次數」，我們說：
  - $\mathrm{X} \sim \text{Binomial}(n, p)$ 。
- 例子：
  - 抽樣 100 位顧客，記錄其中有幾個人使用折價券。
    - 使用折價券的人數 $\mathrm{X}$ 服從 $\mathrm{Binomial}(100,p)$。
  - 抽樣 200 個病人，看一年內有幾個人復發。
    - 復發人數 $\mathrm{X}$ 服從 $\mathrm{Binomial}(200,p)$。

#### 【材料原文】樣本比例（sample proportion）

在資料分析中，我們更常看的不是絕對的「次數」而是相對的「比例」：

$$\hat{p} = \frac{X}{n}$$

- $\mathrm{X}$：這次樣本中觀察到的成功人數。
- $n$：樣本大小。
- $\hat{p}$：樣本成功比例（Sample proportion），用來估計母體成功機率 $p$。

直覺上：抽樣越多（$n$ 越大），$\hat{p}$ 通常就會越靠近真正的 $p$，而且波動會變小。
這個 $\hat{p}$ 是後面我們進行所有「比例檢定」的核心參數。

### 1.3 單一母體比例的估計與檢定（One-sample proportion）

#### 【材料原文】典型問題

- 「該族群中，成功的比例是不是等於某個已知或目標值？」。
  - 這是這類假說設計的核心概念。

**例子 1：去年某產品轉換率是 $5\%$。今年做新活動後，抽樣 200 人，有 18 人購買：**

- $\hat{p} = \frac{18}{200} = 0.09$
- 假說設計：
  - 問題：現在的轉換率是否已經「顯著高於」 5%？
    - $\mathrm{H}_0:p\le0.05 \;\;\;vs.\;\;\; \mathrm{H}_1:p>0.05$
    - 以 $\hat{p}=0.09$ 進行後續檢定步驟（此處略）。

**例子 2：某電商宣稱「退貨率不超過 10%」。抽樣 400 筆訂單，發現有 60 筆退貨：**

- $\hat{p} = \frac{60}{400} = 0.15$
- 假說設計：
  - 問題：這個樣本結果和「10%」這個說法相容嗎？
    - $\mathrm{H}_0:p\le0.1 \;\;\;vs.\;\;\; \mathrm{H}_1:p>0.1$
    - 以 $\hat{p}=0.15$ 進行後續檢定步驟（此處略）。

#### 【材料原文】概念性的檢定流程（省略數理推導）

1. 先有一個基準比例 $p_0$。
   - 可能是「過去的歷史比例」、「官方資訊」、「自行設定的 KPI」。
2. 從樣本算出 $\hat{p}$，嘗試與 $p_0$ 比較大小。
3. 假說檢定想呈現的問題：
   - 假定 $p_0$ 為真，然後問：在這個前提下，抽出像現在這麼極端（或更極端）的樣本比例 $\hat{p}$，機率到底有多大？
     - 如果這個機率很大（$\text{p-value}$ 很大），代表「這種結果在 $p_0$ 的世界裡很常見」，那就沒有理由懷疑 $p_0$ 的真實性。
     - 如果這個機率小到很誇張（$\text{p-value}$ 很小），就會傾向覺得：「這應該不只是抽樣運氣，是母體比例本來就跟 $p_0$ 不一樣。」。
4. 推理過程中需觀察的統計量：
   - 樣本比例的標準誤（standard error）：$\text{SE}(\hat{p}) \approx \sqrt{\frac{p_0(1-p_0)}{n}}$
   - 檢定使用的 Z 分數：$\mathrm{Z-Score}=\frac{\hat{p}-p_0}{\mathrm{SE}(\hat{p})}$。

重點：

- 想比較「樣本比例」和「假設中的比例」。
- 用機率去判斷：這個差距只是這次樣本剛好抽得比較極端，還是背後的比例本來就不一樣。

**這回答什麼行銷/商業問題**：「這檔活動的轉換率有沒有真的超過去年基準／KPI？」——單組 vs 基準值，注意 $\text{SE}$ 用的是 $p_0$（虛無假設下的值），不是 $\hat p$。

<a id="part-1-4"></a>
### ★ 1.4 兩獨立樣本比例比較：「看過廣告 vs 沒看廣告」完整分析（行銷 A/B 原型）

【評註】**這是整份材料裡最接近行銷 A/B 測試的段落，也是新 Skill「廣告成效分析」的直接起點。** 以下逐字保留全部原文，包含情境設定、假說、合併 vs 未合併的完整優缺點對照。

#### 【材料原文】從一個比例擴展成兩個

焦點從「一個比例 vs. 一個基準」擴展成「兩個群體的比例有沒有差」。

#### 【材料原文】典型問題

「兩個不同群組的成功比例，有沒有系統性的差異？」

- 這是很多 A / B test、行銷實驗、醫療比較研究的核心問題。

例子：

- **有看廣告 vs 沒看廣告**
- 現在想知道：「看過廣告的顧客，購買比例是否**高於**沒看廣告的顧客？」

**情境設定：**

- 第 0 組（沒看廣告）：
  - 樣本大小 $n_0 = 100$。
  - 其中有 $\mathrm{X}_0 = 15$ 人完成購買。
  - $\hat{p}_0 = \frac{15}{100} = 0.15$。
- 第 1 組（有看廣告）：
  - 樣本大小 $n_1 = 100$。
  - 其中有 $\mathrm{X}_1 = 30$ 人完成購買。
  - $\hat{p}_1 = \frac{30}{100} = 0.30$。

**假說設計**

- 問題：這樣的樣本結果（$15\%$ vs $30\%$），是否足以支持「看過廣告的購買率真的比較高」？
- $$\mathrm{H}_0: p_1 \leq p_0 \quad \text{vs.} \quad \mathrm{H}_1: p_1 > p_0$$
- 後續就會以 $\hat{p}_0 = 0.15$ 及 $\hat{p}_1 = 0.30$ 進行檢定步驟（此處略）。

#### 【材料原文】概念性的檢定流程（省略數理推導）

**1. 先釐清兩個群組與關注事件**

例子：

- 群組：
  - 有看廣告 vs. 沒看廣告
  - 新療法 vs. 舊療法
  - 會員 vs. 非會員。
- 事件：
  - 購買、存活、使用折價券、流失……等。
  - 全部都是 0 / 1 或 True & False 型態的結果。

對每一組，我們都有：

- 樣本大小：$n_1$, $n_2$
- 成功人數：$\mathrm{X}_1$, $\mathrm{X}_2$
- 樣本比例：
  - $\hat{p}_1 = \frac{\mathrm{X}_1}{n_1}$
  - $\hat{p}_1 = \frac{\mathrm{X}_2}{n_2}$
  （原文如此；第二式應為 $\hat p_2$，材料中為筆誤，此處照錄不改）

**2. 把研究問題轉換成「母體比例」的概念**

例子：

- $p_0$：在「沒看廣告」的母體中，真正購買的比例。
- $p_1$：在「看過廣告」的母體中，真正購買的比例。
- 問題就變成：「$p_1$ 是否顯著大於 $p_0$？」。

**3. 假說檢定想呈現的問題：**

- 假定「兩個母體比例其實一樣」，也就是虛無假說： $p_1$ = $p_2$。
- 然後問：「在這個前提下，抽出像現在看到這麼大的差距 $\hat{p}_1 - \hat{p}_2$（或更極端）的機率，到底有多高？」
- 如果這個機率很高（$\text{p-value}$ 很大），代表：
  - 這種程度的差距，在「兩邊其實一樣」的世界裡很常見，那我們就沒有太大理由懷疑 $p_1 = p_2$ 這件事。
- 如果這個機率小到有點誇張（$\text{p-value}$ 很小），代表：
  - 在「$p_1 = p_2$」的前提下，要看到這麼大的差距非常罕見，比較合理的解釋就會是：「兩個族群的母體比例，本來就不一樣。」。

**4. 推理過程中需觀察的統計值**

#### 【材料原文】★ 合併與未合併的差異（Pooled vs Unpooled）

**未合併（Unpooled）：**

- 假設兩個母體比例不相等。
- 分別使用各自的樣本比例來估計各自母體的比例。
- 使用情境：當目標是估計「差異的範圍」時。
- 核心價值：著重於不偏性，不預設立場，真實反映差異。
- 優點：
  - 不需假設 $p_1=p_2$，能更真實地反映當兩個母體比例**確實不同**時的變異程度。
- 缺點：
  - 效率較低。
  - 當 $\mathrm{H}_0: p_1=p_2$ 成立時，沒有利用共同比例的資訊，導致標準誤估計不如合併法精確。

**合併（Pooled）：**

- 假設兩個母體比例相等（虛無假設成立）。
- 將兩個樣本的成功數和樣本大小合併起來，得到一個更精確的共同比例估計值。
- 使用情境：當目標是檢定兩個比例是否相等時。
- 核心價值：著重於效率性（利用 $\mathrm{H}_0$ 資訊，使標準誤估計更優）。
- 優點：
  - 效率高 / 檢定力強。
  - 在 $\mathrm{H}_0: p_1=p_2$，成立的假設下，提供了對標準誤最佳、最精確的估計，使假設檢定更具檢定力。
- 缺點：
  - 適用性受限。
  - 只能用於檢定相等性，例如：$\mathrm{H}_0: p_1=p_2$。
  - 不能用於建構信賴區間，因為信賴區間不預設 $p_1=p_2$。

#### 【材料原文】合併後樣本比例（Pooled sample proportion）

在 $\mathrm{H}_0: p_1 = p_2$ 的前提下，我們可以把兩組資料合併，用一個共同比例 $p$ 來描述：

$$\hat{p} = \frac{\mathrm{X}_1 + \mathrm{X}_2}{n_1 + n_2}$$

**差異的標準誤：**

$$\text{SE}(\hat{p}_1 - \hat{p}_2)
\;\approx\;
\sqrt{ \hat{p}(1-\hat{p})\left(\frac{1}{n_1} + \frac{1}{n_2}\right) }$$

- 直覺上：
  - 樣本越大：$\frac{1}{n_1}$, $\frac{1}{n_2}$ 越小 $\longrightarrow$ 差異的波動越小。
  - $\hat{p}(1-\hat{p})$ 則反映事件本身的變異程度。

**檢定統計量 Z-score**

- 以「假設兩邊一樣」為基準，衡量現在的差異有多「大」：

$$\mathrm{Z-Score} = \frac{(\hat{p}_1 - \hat{p}_2) - 0}{\text{SE}(\hat{p}_1 - \hat{p}_2)}$$

- 在這樣的 $\mathrm{H}_0$ 下，理論上的差異是 $0$。

#### 【材料原文】未合併樣本比例（Unpooled sample proportion）

若是要做「$p_1 - p_2$ 的信賴區間」，或不希望假設 $p_1=p_2$ 來估變異，則可使用：

$$\text{SE}_{\text{unpooled}}(\hat{p}_1 - \hat{p}_2)
\approx
\sqrt{
  \frac{\hat{p}_1(1-\hat{p}_1)}{n_1}
  +
  \frac{\hat{p}_2(1-\hat{p}_2)}{n_2}
}$$

- 讓每一組各自負責自己的變異。

例子：

- 看過廣告 vs. 沒看過廣告，購買比例是否不同？
- 新療法 vs. 傳統療法，病人存活率是否不同？
- 會員 vs. 非會員，折價券使用率是否不同？

對每一組，我們都有：

- 第 1 組：
  - 樣本大小：$n_1$
  - 成功人數：$\mathrm{X}_1$
  - 樣本比例：$\hat{p}_1 = \frac{X_1}{n_1}$
- 第 2 組：
  - 樣本大小：$n_2$
  - 成功人數：$\mathrm{X}_2$
  - 樣本比例：$\hat{p}_2 = \frac{\mathrm{X}_2}{n_2}$
- 我們關注的：
  - 樣本差異：$\hat{p}_1 - \hat{p}_2$
  - 母體差異：$p_1 - p_2$ 是否為 0

#### 【評註】把 1.4 直接翻成可執行的廣告 A/B 分析

材料只給到「此處略」，沒有把 15% vs 30% 算完。用材料給的公式補完（**這是評註，不是教材內容**）：

- $\hat p_c = \frac{30+15}{100+100} = 0.225$
- $\text{SE}_0 = \sqrt{0.225 \times 0.775 \times (\frac1{100}+\frac1{100})} = 0.05903$
- $Z = \frac{0.30-0.15}{0.05903} = 2.541$，單尾 $\text{p-value} \approx 0.0055$ → 在 $\alpha=0.05$ 下拒絕 $\mathrm{H}_0$。
- 效果量：$\widehat{\text{OR}} = \frac{30/70}{15/85} = \frac{0.4286}{0.1765} = 2.43$；$\log \widehat{\text{OR}} = 0.888$；
  $\text{ASE} = \sqrt{\frac1{30}+\frac1{70}+\frac1{15}+\frac1{85}} = 0.3547$；
  95% CI for log OR $= 0.888 \pm 1.96 \times 0.3547 = (0.193, 1.583)$ → OR 的 95% CI $= (1.21, 4.87)$。

對應 R（用材料 Case 3 的同一套語法改寫）：

```r
## 廣告 A/B：看過廣告 vs 沒看廣告，購買比例是否較高
y   <- c(30, 70, 15, 85)                    # listed by row: 有廣告(買,不買), 無廣告(買,不買)
ad  <- gl(2, 2, 4, c("Exposed","Control"))  # row names
buy <- gl(2, 1, 4, c("Buy","NoBuy"))        # col names
( case <- xtabs(y ~ ad + buy) )

## 比例檢定（合併標準誤；單尾）
prop.test(c(30,15), c(100,100), alternative="greater", correct=FALSE)

## Odds ratio 與 CI（照材料 Case 3 流程）
ptest <- prop.test(case)
( pi    <- ptest$estimate )
( odds  <- ptest$estimate/(1-ptest$estimate) )
( phi   <- odds[1]/odds[2] )
log(phi)
( ase        <- sqrt(sum(1/case)) )
( logphi.ci  <- log(phi) + c(-1,1)*qnorm(0.975)*ase )
( exp(logphi.ci) )
```

**這回答什麼行銷/商業問題**：廣告曝光組與對照組的購買率差異是否只是抽樣雜訊？差多少（用 OR 而非百分點差）？——這正是投放後成效報告的標準句型：「曝光組購買勝算約為對照組的 2.4 倍（95% CI 1.2–4.9），單尾 p = 0.006」。

**【評註】推論界線提醒**：材料在同一頁的 Case 3 明確寫「本分析是基於觀察型資料，僅能提供統計關聯的證據，不能直接作為因果推論」。若廣告曝光不是隨機分派（例如是平台演算法挑出「本來就比較會買」的人看到廣告），這個 2.43 倍只能講「關聯」，不能講「廣告造成的增量」。要講因果，材料指的是本頁「隨機化二元實驗設計（Randomized Binomial Experiment）」那一段。

### 1.5 列聯表與卡方檢定（Contingency table & Chi-square test）— 概述版

#### 【材料原文】典型問題

「兩個類別變數之間，到底有沒有關聯？」

- 例子：
  - 是否看過廣告 (Yes / No) $\times$ 是否購買 (Buy / Not buy)。
  - 資費 A / B / C $\times$ 是否續約 (Renew/Not renew)。
  - 治療方式 (新療法 / 舊療法) $\times$ 結果 (痊癒 / 未痊癒)。
- 特殊情形，例如：
  - 一個變數是「群組」（例如：有看廣告 / 沒看廣告）
  - 另一個變數是「0 / 1 結果」（例如：購買 / 未購買）
  - 此時的問題就會「**退化」成「兩個比例是否相等」。**
  - 因此卡方檢定（Chi-square test）可以看成是「兩比例檢定」的推廣。

#### 【材料原文】列聯表（Contingency table）的表示方式

以「是否看過廣告」×「是否購買」為例（2×2 列聯表）：

$$\begin{array}{c|cc|c}
  & \text{購買 }(Y=1) & \text{未購買 }(Y=0) & \text{列合計} \\
  \hline
  \text{看過廣告}   & a & b & a+b \\
  \text{沒看廣告}   & c & d & c+d \\
  \hline
  \text{欄合計} & a+c & b+d & n
\end{array}$$

- 每一格的數字， $a,b,c,d$ 是**觀察到的次數**，記為 $O_{ij}$（Observed count）。
- 最右一欄、最下面一列是**列合計、欄合計**，整體樣本數為 $n$。

針對更一般性的情境，我們可以使用推廣出去的 $\mathrm{R} \times \mathrm{C}$ 列聯表：

$$\begin{array}{c|ccc|c}
  & \text{類別 1} & \cdots & \text{類別 C} & \text{列合計} \\
  \hline
  \text{群組 1} & O_{11} & \cdots & O_{1C} & n_{1\cdot} \\
  \vdots        & \vdots &        & \vdots & \vdots     \\
  \text{群組 R} & O_{R1} & \cdots & O_{RC} & n_{R\cdot} \\
  \hline
  \text{欄合計} & n_{\cdot 1} & \cdots & n_{\cdot C} & n
\end{array}$$

- $O_{ij}$：第 $i$ 列、第 $j$ 欄的「**觀察次數**」。
- $n_{i\cdot}$：第 $i$ 列的總數（列合計）。
- $n_{\cdot j}$：第 $j$ 欄的總數（欄合計）。
- $n$：總樣本數。

#### 【材料原文】卡方檢定想問的是什麼？（概念性的檢定流程）

1. 先整理出列聯表（整理資料）
   - 兩個變數都是**類別變數**（「名目變數」或「順序變數」）
   - 我們會把資料整理成上面的 $R \times C$ 表格，得到所有 $O_{ij}$
2. 將問題轉換成假說檢定
   - $\mathrm{H}_0$：兩個變數「彼此獨立、沒有關聯」。
   - $\mathrm{H}_1$：兩個變數「有關聯」。
3. 例子：
   - 以廣告為例：
     - $\mathrm{H}_0$：「是否看過廣告」**和「**是否購買」是沒有關係的。
     - $\mathrm{H}_1$：兩者之間存在某種關連。
       - 看過廣告的人購買率較高或較低，只要是「關聯性」就可以算。
4. 在「沒有關聯」的前提下，推算出「期望次數」 $\mathrm{E}_{ij}$。
   - 期望次數（Expected count）公式：$E_{ij} = \frac{n_{i\cdot} \cdot n_{\cdot j}}{n}$
   - 直覺：
     - 如果兩個變數真的完全沒關係，那每個 cell 裡的人數，應當只是「列合計 $\times$ 欄合計」按比例拆出來而已。
     - 也就是說：先看第 $i$ 列總共有多少人、第 $j$ 欄總共有多少人。在獨立假設下，落在這一格的「理想人數」就會是 $\mathrm{E}_{ij}$。
5. 透過卡方統計量（Chi-square statistics） 比較「觀察次數」和「期望次數」
   - 定義：

$$\chi^2
=
\sum_{i=1}^{\mathrm{R}} \sum_{j=1}^{\mathrm{C}}
  \frac{(\mathrm{O}_{ij} - \mathrm{E}_{ij})^2}{\mathrm{E}_{ij}}$$

   - 直覺解讀：
     - 利用列聯表中的每一格算「觀察值 − 期望值」的偏離程度。
     - 平方後再除以 $\mathrm{E}_{ij}$ 來標準化，
     - 再將所有格子的偏離程度加總。
     - 偏離總和越大，代表實際列聯表和『獨立情況下的理想表』差距越大。
6. 利用卡方分配（Chi-square distribution）決定 $\text{p-value}$
   - 在 $\mathrm{H}_0$ 成立且樣本數夠大的情況下，$\text{d}_\text{f} = (\mathrm{R} - 1)(\mathrm{C} - 1)$
   - $\chi^2$ 統計量大致服從自由度為 $\text{d}_\text{f} = (\mathrm{R} - 1)(\mathrm{C} - 1)$ 的卡方分配。
7. 假說檢定想呈現的問題：
   - 在 $\mathrm{H}_0$ 為真的世界裡，看到像現在這麼大的 $\chi^2$（或更大）的機率有多小？」
     - 若這個機率（$\text{p-value}$）非常小，就會傾向拒絕 $\mathrm{H}_0$。
     - 可以解讀為：「兩個變數之間存在某種關聯」。
8. 與「兩獨立樣本比例檢定」的關係（補）
   - 在 $2 \times 2$ 列聯表 的特例下（兩群 $\times$ 0 / 1 ）
     - 用 Chi-square 檢定「兩變數是否獨立」等價於用「兩獨立樣本比例檢定」來檢定 $\mathrm{H}_0: p_1 = p_2$ 。
   - Why？
     - 以兩樣本比例檢定的 Z-score 為：$\mathrm{Z} = \frac{\hat{p}_1 - \hat{p}_2}{\text{SE}(\hat{p}_1 - \hat{p}_2)}$
     - 對應的 Chi-square 統計量其實就是：$\chi^2 = Z^2$
     - 因此在 $2 \times 2$ 的情況下，用「兩樣本比例的 $\mathrm{Z}$ 檢定」與用「Chi-square 檢定」，雙尾檢定的 $\text{p-value}$ 會是一樣的。
     - 簡單結論：
       - 在 $2 \times 2$ 時：
         - 兩樣本比例檢定 = 列聯表 Chi-square 檢定的特例。
         - Chi-square 只是把這個概念推廣到「更多列、更多欄」的情境。
9. 實務上的注意事項
   - 樣本數與期望次數的大小
     - 一般教科書建議：每一格的期望次數 $\mathrm{E}_{ij}$ 不宜太小，
       - 常見規則是「大部分格子 $\mathrm{E}_{ij} \ge 5$」。
     - 若有太多格子的期望次數很小，Chi-square 近似會變差，此時會考慮：
       - 合併某些類別。
       - 改用其他精確檢定（略）。
       - 變數必須是類別型。
   - Chi-square 檢定是設計來處理「類別 × 類別」的資料，
     - 若變數本質是連續型（例如收入、年齡），通常會先切成類別區間後再做列聯表，但這樣會犧牲一些資訊。

**這回答什麼行銷/商業問題**：多水準的行銷變數（三種資費、五個渠道、四段年齡層）對二元 KPI 有沒有整體關聯？注意這只回答「有沒有」，不回答「哪一組贏、贏多少」（見 1.11 卡方限制）。

### 1.6 配對樣本的二元資料（Paired binary data）

#### 【材料原文】典型問題

想回答的問題大多長這樣：

- 「同一批人，在兩個時間點下，成功比例有沒有改變？」
- 「同一批人，在兩種處理下，成功比例有沒有改變？」

常見情境：

- 前後比較（Before vs. After）
  - 例如：「同一位」顧客，「活動前」及「活動後」是否完成購買？結果都以 0 / 1 （有買 / 沒買）來記錄。
- 兩方案比較（A vs B）但在同一個對象上
  - 例如：「同一位」使用者同時看「版面 A」、「版面 B」，對每個版面各自作出「喜歡 / 不喜歡」的 0 / 1 回應。
  - 「同一位」病人左右眼分別採用「治療 A」、「治療 B」，結果為「成功 / 失敗」。
- 成對觀測（Matched pairs）
  - 例如：雙胞胎兄弟分別接受不同教學法，是否「通過考試」。
  - 夫妻分別收到不同版本 EDM，是否「點擊連結」。

白話來說：

- 不是「兩群互不相干的人」，而是一對一綁在一起的觀測值。
- 每一對（pair）要嘛是同一個人測兩次，要嘛是兩個高度相關的個體。

#### 【材料原文】資料型態：每一組配對中裡有兩個 0 / 1

對第 $i$ 個受試者（或第 $i$ 對），我們會有兩個二元結果：

- $Y_{i1} \in \{0,1\}$：在「情況 1」的結果。
- $Y_{i2} \in \{0,1\}$：在「情況 2」的結果。

每個 $Y_{ij}$ 單看都是「一次伯努力試驗」，但 $(Y_{i1}, Y_{i2})$ 這一對是**高度相關**的：

- 同一個人的兩次結果，通常會受同一組特質影響。例如習慣、健康狀況、收入。
- 所以不能假裝 $Y_{i1}$ 跟另一個人 $Y_{k2}$「完全獨立」。

白話來說：一個人自己前後兩次的結果，一定比「兩個不同人」更像一組，所以在分析時也要把他們當作「配對」，而不是兩群獨立樣本。

#### 【材料原文】用 $2 \times 2$ 表呈現配對結果

$$\begin{array}{c|cc|c}
  & \text{後：成功 }(Y_2=1) & \text{後：失敗 }(Y_2=0) & \text{合計} \\
  \hline
  \text{前：成功 }(Y_1=1) & n_{11} & n_{10} & n_{1\cdot} \\
  \text{前：失敗 }(Y_1=0) & n_{01} & n_{00} & n_{0\cdot} \\
  \hline
  \text{合計} & n_{\cdot 1} & n_{\cdot 0} & n
\end{array}$$

- $n_{11}$：前後都成功的人數（1 → 1）。
- $n_{00}$：前後都失敗的人數（0 → 0）。
- $n_{10}$：前成功、後失敗（1 → 0），可以理解為「變糟」。
- $n_{01}$：前失敗、後成功（0 → 1），可以理解為「變好」。
- 列、欄合計：
  - $n_{1\cdot} = n_{11} + n_{10}$：前面成功（不管後面如何）的人數。
  - $n_{0\cdot} = n_{01} + n_{00}$：前面失敗的人數。
  - $n_{\cdot 1} = n_{11} + n_{01}$：後來成功的人數。
  - $n_{\cdot 0} = n_{10} + n_{00}$：後來失敗的人數。
  - $n = n_{11} + n_{10} + n_{01} + n_{00}$：總樣本數。

#### 【材料原文】與「兩獨立樣本」的差異：關鍵不在「組別」，而在「成對」！

**兩組樣本「不是互不相干的兩群人」**

- 獨立樣本比例：群組 1 和 群組 2 的人是分開抽的，可以視為互不影響。
- 配對樣本：每一列（每一對）都是「自己對自己」、「A / B 一人各一份」或「高度配對的兩個人」。

**資訊主要來自「前後不一樣」的同一人**

- 對「前後比例有沒有差」這個問題：
  - 前後都成功（1 $\rightarrow$ 1）的那群人，其實對差異沒有太多貢獻，因為本來就兩邊都一樣。
  - 前後都失敗（0 $\rightarrow$ 0）也是。
- 真正告訴我們「前後哪邊比較高」的是：
  - 從成功變失敗的：$n_{10}$（變糟）。
  - 從失敗變成功的：$n_{01}$（變好）。

這也是為什麼，在後續提到的 McNemar test 中，檢驗核心會只盯著 $n_{10}$ 及 $n_{01}$ 的差異來看。

### 1.7 McNemar 檢定（配對樣本比例的檢定）

#### 【材料原文】典型問題

「同一批人，在『前 vs 後』或『方案 A vs 方案 B』之間，成功比例有沒有系統性的差異？」

搭配前段的配對情境，常見例子如下：

- 「介面 A」 與「介面 B」 的喜好測試
  - 同一位使用者，先後看兩種介面版本：A、B。
  - 對每個版本都回答「喜歡 / 不喜歡」（1 / 0）。
  - 問題：喜歡 A 的比例和喜歡 B 的比例，對這一批人來說有沒有差？
- 治療前後的改善率
  - 同一位病人。治療前：是否症狀嚴重（1 = 嚴重、0 = 不嚴重）。治療後：是否仍嚴重。
  - 問題：治療前後「嚴重」的比例，有沒有顯著下降？
- 問卷意見的改變
  - 同一批受試者，在政策宣導前後，分別回答「支持 / 不支持」。
  - 問：宣導前後的支持率是否有改變？

#### 【材料原文】McNemar 檢定的關鍵

- **真正能夠提供有用資訊的是「前後不一致」的兩格**：$n_{10}$ 和 $n_{01}$。
- 其他兩格只是告訴我們「沒變」，對「誰比較高」的問題其實幫助有限。

#### 【材料原文】檢定想問的是什麼？（概念性的檢定流程）

1. 設定要比較的兩個比例
   - $p_1$：在這一批人中，「前」為成功的母體比例。
   - $p_2$：在同一批人中，「後」為成功的母體比例。
2. 想檢定的問題通常是：
   - $\mathrm{H}_0: p_1 = p_2 \quad \text{vs.} \quad \mathrm{H}_1: p_1 \neq p_2$
   - $\mathrm{H}_0: p_1 \le p_2 \quad \text{vs.} \quad \mathrm{H}_1: p_1 > p_2$
3. 在 $2 \times2$ 的世界中，相當於只看「有改變」的人
   - $n_{11}$、$n_{00}$：前後都一樣 $\longrightarrow$ 對「前後誰比較高」沒有直接資訊。
   - $n_{10}$、$n_{01}$：前後不一樣 $\longrightarrow$ 直接反映「往哪個方向改變」。
4. 因此 McNemar 檢定的核心邏輯是：
   - 先把所有「前後不同」的樣本集中起來看，再比較其中有多少人是「從成功變失敗」（1 $\rightarrow$ 0），有多少人是「從失敗變成功」（0 $\rightarrow$ 1）。
5. 白話來說：
   - 在虛無假設下，對「不成對」的直覺
     - 如果前後成功比例其實一樣（$p_1 = p_2$），直覺上，「變好」和「變糟」的機會應該差不多。
     - 也就是說，在「總共有 $b+c$ 個人發生改變」的前提下：變成 1 $\rightarrow$ 0 的人數 $n_{10}$ 和 變成 0 $\rightarrow$ 1 的人數 $n_{01}$ 像是把這 $b+c$ 個人像丟銅板分組，落到左右兩邊的機率各半。
     - 因此在 $\mathrm{H}_0$ 下，可以把「不成對樣本裡屬於某一邊的人數」視為 $\mathrm{Binomial}(b+c, 0.5)$ 的二項分配問題。（這是 McNemar 的「精確檢定」版本）
   - 檢定想回答的關鍵問題：
     - 「在假設『前後成功率沒差』的前提下，只看那些有改變的人，要看到像現在這樣 $n_{10}$ 和 $n_{01}$ 差這麼多的情況，機率到底多大？」
       - 若這個機率（p-value）很小，就覺表示：「要在前後沒有差的世界裡看到這麼不平衡的改變數實在太誇張」。
       - 因此較為合理的解釋就是「前後比例真的不一樣」。

#### 【材料原文】推理過程中會看到的統計量

**二項檢定（精確版）**

- 定義 $b = n_{10},\ c = n_{01}$，總不一致人數 $m=b+c$。
- 在 $\mathrm{H}_0$ 下，可以視：$\mathrm{B}=\min(b,c)$ 或 $\mathrm{B}=b$ 為 $\text{Binomial}(m, 0.5)$ 的觀測結果。
- $\text{p-}value$ 由二項分配算出「至少像現在這麼極端」的機率。
- 這是概念上最乾淨的版本，但手算不太方便，通常丟給電腦算。

**卡方檢定（近似版）**

- 當 $b+c$ 足夠大時，可以用 Chi-square 近似：
  - 沒有連續校正的版本：$\chi^2 = \frac{(b - c)^2}{b + c}$
  - 有連續校正的版本：$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$
- 在 $\mathrm{H}_0$ 下，$\chi^2$ 大致服從自由度為 $1$ 的卡方分配。
- $\text{p-value}$ 在這裡的意義就是「在 $\text{d}_\text{f}=1$ 的卡方分配下，看到這麼大（或更大）的 $\chi^2$ 的機率。
- 提醒！
  - 公式不用記。
  - 要知道 McNemar 檢定是在關注 $b$ 和 $c$ 這兩類的「不平衡程度」！

#### 【材料原文】重點！什麼時候用 McNemar 而不是兩比例檢定？

**一定要用 McNemar 的條件：**

- 同一個人（或成對樣本）有兩次 0 / 1 的試驗。
- 我們在乎的是「前 vs 後」或「方案 A vs 方案 B」中的成功比例是否相同。
- 每一對資料是「綁定」的，不能當成兩組獨立樣本。

**為什麼不能用一般「兩獨立樣本比例檢定」？**

- 因為兩次觀測是在「同一個人」身上（或高度相關的配對單位），彼此之間有相關性：
  - 例如：習慣、個人偏好、體質，會同時影響前後兩次結果。
- 若硬把這兩組當成獨立樣本，會有以下狀況：
  - 會低估變異，誤以為證據比較強。
  - 得到的 $\text{p-value}$ 會太樂觀。

**McNemar 檢定的核心思想**：

- 「先只看那些『有改變』的人，在假設前後一樣的前提下，評估『變好』和『變糟』這兩類不一致的比例是否差太多。」

在 R 中，若要使用的話，語法為 `mcnemar.test()` 。

**這回答什麼行銷/商業問題**：同一批人前後測（活動前/後、改版前/後、A/B 版面 within-subject）。**行銷上最容易踩的雷**：拿「同一群人活動前 vs 活動後」去跑 `prop.test()` 是錯的，會低估變異、p-value 過度樂觀。

### 1.8 獨立性檢定（Test of Independence）

#### 【材料原文】

- 問題核心：「在這個母體裡，變數 A 和變數 B 之間有沒有關聯？」
- 母體與抽樣設計（省略數理計算）
  - 只從一個單一母體抽樣。
  - 對每一個受試者，同時記錄兩個類別變數的狀態（例如：性別 × 政黨傾向、吸菸 × 飲酒）。
  - 抽完後，把資料整理成一個 $\mathrm{I} \times \mathrm{J}$ 的列聯表。
- 虛無假說（$\mathrm{H}_0$）
  - 假說概念：知道其中一個變數的類別，不會幫助我們預測另一個變數。
    - 也就是說：「兩個變數在統計上是『獨立』的。」
  - 假說寫法（以列因子為 $\mathrm{X}$，欄因子為 $\mathrm{Y}$）：

$$H_0:\ X \perp \!\!\! \perp Y
\quad\Longleftrightarrow\quad
P(X=i, Y=j) = P(X=i)\,P(Y=j)\;\;\forall\;i,j$$

- 情境範例：
  - 想知道某城市居民的：吸菸習慣（變數 A：吸菸 / 不吸菸）、飲酒習慣（變數 B：飲酒 / 不飲酒）是否有關聯？
- 實際做法：
  - 從這個城市中抽出一批居民。
  - 對每個人，同時問：有沒有吸菸？有沒有飲酒？
  - 將結果整理成 $2\times2$ 列聯表，做獨立性檢定。

### 1.9 同質性檢定（Test of Homogeneity）

#### 【材料原文】

- 問題核心：好幾個不同母體（族群），在同一個類別變數的分配上，是不是長得一樣？
- 母體與抽樣設計
  - 有兩個或多個不同的母體（族群或預先定義的組別）。
  - 從每一個母體中，各自抽出一個樣本。
  - 對每個樣本中的個體，只觀察一個類別變數的狀態（例如：對某政策的態度）。
  - 最後把所有樣本放在一起，整理成「母體（列） × 回應類別（欄）」的列聯表。
- 虛無假說（$\mathrm{H}_0$）
  - 假說概念：所有被比較的母體（或組別），在這個類別變數上的分佈是一樣的。
    - 也就是各母體的「機率分布」相同。
  - 假說寫法：
    - 以第 $k$ 個母體在 $J$ 種回應類別上的機率 $(\pi_{k1},\dots,\pi_{kJ})$ 為例，則

$$\mathrm{H}_0:\ (\pi_{1\cdot}) = (\pi_{2\cdot}) = \dots = (\pi_{K\cdot})$$

- 情境範例：
  - 想知道三個不同國家（A 國、B 國、C 國）的國民，在「是否支持某一新政策」上的分佈是否相同：
    - 變數：政策支持度（支持／中立／反對）。
    - 母體：A 國、B 國、C 國，各是一個母體。
- 實際做法：
  - 分別從三個國家抽樣。
  - 對每一位受訪者，只記錄「支持／中立／反對」。
  - 把三國資料合併成 $3\times3$ 或 $3\times4$ 列聯表（視選項多少而定）。
  - 對「三國的分布是否相同」做同質性檢定。

#### 【材料原文】獨立性與同質性（Independence and Homogeneity）— 兩者的關係

在 $2\times 2$ 或更一般化的列聯表中，「同質性假設」跟「獨立性假設」在數學上的計算與檢定過程是一樣的，只是詮釋角度不同。

**相同的虛無假設（Identical hypotheses）— 以兩群體、二元反應為例**

**同質性假設（Hypotheses of Homogeneity）：**

- 若以「兩母體的成功比例相同」來表達：$\mathrm{H}_0: \pi_2 - \pi_1 = 0$
- 若以「兩母體的 odds ratio 相同」來表達：$H_0: \frac{\omega_2}{\omega_1} = 1$
  - 其中 $\omega_k = \dfrac{\pi_k}{1-\pi_k}$ 是第 $k$ 組的 odds。
- 這兩個寫法在 2×2 的情境下是等價的，只是換一種參數化方式。
- 關注的是：「某個二元反應在不同母體（或不同族群）中，分配是否一樣？」
- 白話來說：
  - 概念上是，將二元反應視為「兩組不同的母體」，檢驗他們的比例值是否相同。
  - 一樣的話就是具有同質性，畢竟具有一樣的機率分佈情形。

**獨立性假設（Hypotheses of independence）：**

- 另一種常見的說法，是把列、欄都看成「因素（factors）」：
  - 我們有一個 row factor 和一個 column factor，想知道「兩者之間有沒有關聯？」。
  - 不一定要指定哪一方是反應變數。
- 虛無假說：
  - $\mathrm{H}_0:$ The row categorization is independent of the column categorization.
  - 指的是「列的分類方式與欄的分類方式在統計上獨立」。
- 在數學上，這個 $\mathrm{H}_0$ 等價於剛剛提到的「各群分布相同」，只是敘述上更中性，沒有先指定誰是 explanatory、誰是 response。
- 白話來說：
  - 給定不同的 $\mathrm{X}$，我的每個 $\mathrm{X}$ 中，$\mathrm{Y}$ 所佔的比例都一樣，可以稱做獨立。
  - 或說不同列的 $\mathrm{X}$ ，裡面所占的不同 $\mathrm{Y}$ 的比例要一樣，稱作獨立。
  - 兩者之間並沒有出現特別多，或是哪個地方特別少的狀況。
  - 選 $\mathrm{Y}$ 的狀況不會因為選 $\mathrm{X}$ 的狀況不同而不同。

**同質性 vs 獨立性：概念上差在哪？**

兩者的差異是「你用什麼角度來看那張列聯表」。

- 同質性（homogeneity）視角：
  - 可以想像你有「好幾個母體（幾個族群）」，每個母體都有一樣的一組反應類別（例如：四種回應）。
    - 問題是：這些母體的反應分布是不是「同質」的一樣？
- 獨立性（independence）視角：
  - 可以想像成你有「同一個大母體」，個體同時被兩種方式分類：
    - 例如：列是「年齡層」（三種）、欄是「滿意度等級」（四種）。
    - 問題是：這兩種分類彼此有沒有關聯？
- 在數學上，兩種檢定在 $2 \times 2$ 或一般 $\mathrm{I} \times \mathrm{J}$ 列聯表下，用的都是同一個 Chi-square 統計量，只是解讀的語言不同而已。

白話來說：

- 看「多個母體的反應分布是否一樣」 $\longrightarrow$ 同質性檢定。
- 看「列因子與欄因子之間是否獨立」 $\longrightarrow$ 獨立性檢定。
- 實務上我們做的都是同一個 Chi-square test，只是研究問題的方向不一樣。

**這回答什麼行銷/商業問題**：同一個 `chisq.test()` 輸出，在報告裡要寫成「渠道與轉換有關聯」（獨立性、單一母體同時量兩個變數）還是「三個渠道的轉換分布不同」（同質性、各渠道各自抽樣）——**取決於你怎麼抽的樣，不是取決於你算什麼**。

### 1.10 投影片版：比例的抽樣分配與兩比例推論

#### 【材料原文】Outlines

**比較兩組樣本**，其中反應測量（Response measurement）是**二元**的（0 或 1）。

- 例如：死亡或存活。患病或未患病。購買不購買。

對二元回應進行統計分析，可以得出以下結論：

- 兩個母體比例（Population proportions）
- 機率（Probabilities）
- 勝算（Odds）
- 勝算比（Odds ratio）

此類相關的研究方法有以下兩種：

- 前瞻性（Prospective）
- 回溯性（Retrospective）

#### 【材料原文】比例（Proportion）— 注意！

- 我們一般都是假設母體參數為未知固定值（真實值），不管是先前的 mean variance 或這裡的 proportion 都一樣，也就是 " fixed but unknown "。
- 我們是透過樣本進行「抽樣」來「推論」母體，所以估計值才會相對應的分配。

#### 【材料原文】樣本比例的抽樣分佈（Sampling Distribution of a Sample Proportion）

**二元反應變數：是 / 否 （Yes / No），1 / 0 。**

- 群體中二元反應變數的平均值，即是被歸類為「是」的成員比例。
- 此比例用 $\pi$ 表示，稱為母體比例（population proportion）或可視為是機率 （probability）。

**二元反應變數的變異數（Variance of Binary Response Variable）**

- 若 $\mathrm{Y}$ 是一個母體平均數為 $π$ 的二元反應變數，則母體變異數 $\mathrm{Var(Y)}=\pi\times(1-\pi)$ 。
- 可以發現，若 $\pi$ 是已知的話，$\mathrm{Var}$ 就相當於是已知了，因為不需要另外一個參數來對 $\mathrm{Var}$ 進行描述或估計。
- 因此 $\mathrm{Var}$ 可以視為是 $\mathrm{Mean}$ 的函數。

【評註】**這一句是整個 GLM 章節的伏筆**：`variance is a function of the mean`。它直接導出後面 logistic / Poisson 不需要（也不能）額外估一個 $\sigma^2$、以及 overdispersion 為什麼是個問題。

**樣本總數與二項分配（Sample Total and Binomial Distribution）**

- 假設 ${\mathrm{Y}_1,\mathrm{Y}_2,…,\mathrm{Y}_n}$ 是從二元反映應變數群體中提取的 $n$ 個隨機樣本。
- 這些二元反應的總和 $\mathrm{S}=\mathrm{Y}_1+\mathrm{Y}_2+…+\mathrm{Y}_n$ 是 $\mathrm{Y}=1$ 的試驗數量計數。
- 變數 $\mathrm{S}$ 具有二項分配（Binomial distribution）的特性。
- 機率：

$$\Pr(\mathrm{S}=k)=\binom{n}{k}\pi^k(1-\pi)^{n−k}=\frac{n!}{k!(n−k)!}\pi^k(1-\pi)^{n−k}$$

- $\mathrm{S}$ 的 $\mathrm{Mean} = n\pi$。
- $\mathrm{S}$ 的 $\mathrm{Var}=n\pi\times(1-\pi)$
- 可理解成：
  - $n$ 次隨機試驗中有 $k$ 次被判定為成功的機率。
  - 試驗成功的機率為 $\pi$；試驗失敗的機率為 $1-\pi$ 。
- 當 $nπ$ 和 $nπ(1–π)$ 這兩項值都大於 $5$ 時：
  - 我們會說此二項分配可以用常態分配來逼近。
  - 或說可以用常態分配來近似此二項分配。
  - 就是過往提過的「常態近似」，在滿足各種分配的樣本條件下，多數分配都可以「近似常態」。
  - 數學描述：

$$\mathrm{Bin}(n,\pi)\; \xrightarrow[n\pi\;>\;5\; \& \; n\pi(1-\pi)\;>\;5]{}\;\mathcal{N}(n\pi,n\pi(1-\pi))$$

**樣本比例的抽樣分佈**

- **樣本比例：** $\hat{\pi}$
  - 在 Case 1 中，$2,050$ 名肥胖婦女中有 $18$ 人在 $6$ 年研究期間死於 CVD，因此樣本比例為 $\frac{18}{2050}=0.00878$。
- 樣本比例的抽樣分佈
  - 平均數 $\mathrm{E}(\hat{\pi})=\pi$
  - 變異數 $\mathrm{Var}(\pi)=\frac{\pi(1−\pi)}{n}$。
  - 若 $n$ 足夠大，根據中央極限定理，$\hat{\pi}$ 的抽樣分佈近似於常態分佈。

#### 【材料原文】兩樣本比例差異的抽樣分佈（Sampling Distribution for Difference between Two Sample Proportions）

若 $\hat{\pi}_1$ 和 $\hat{\pi}_2$ 是從獨立的隨機樣本計算出來的，則它們差異的抽樣分佈有以下特性：

- 平均數 $\mathrm{E}(\hat{\pi}_1−\hat{\pi}_2)={\pi}_1−{\pi}_2$ 。
- 變異數 $\mathrm{Var}(\hat{\pi}_1−\hat{\pi}_2)=\frac{\pi_1(1−\pi_1)}{n_1}+\frac{\pi_2(1−\pi_2)}{n_2}$。
- 若 $n_1$ 及 $n_2$ 足夠大，根據中央極限定理 ${\pi}_1-{\pi}_2$ 的抽樣分布將會近似於常態分佈。

**$\hat{\pi}_1−\hat{\pi}_2$ 的兩種標準誤（Standard Errors）**

- 用於信賴區間：

$$\text{SE}(\hat{\pi}_1 - \hat{\pi}_2)
\approx
\sqrt{
  \frac{\hat{\pi}_1(1-\hat{\pi}_1)}{n_1}
  +
  \frac{\hat{\pi}_2(1-\hat{\pi}_2)}{n_2}
}$$

- 用於檢定是否相等（$\mathrm{H}_0:\hat{\pi}_1 - \hat{\pi}_2$）：

$$\text{SE}(\hat{\pi}_1 - \hat{\pi}_2)
\;\approx\;
\sqrt{ \hat{\pi}(1-\hat{\pi})\left(\frac{1}{n_1} + \frac{1}{n_2}\right) }=\sqrt{
  \frac{\hat{\pi_c}(1-\hat{\pi_c})}{n_1}
  +
  \frac{\hat{\pi_c}(1-\hat{\pi_c})}{n_2}
}$$

其中 $\pi_c$ 是將兩個樣本合併為一個樣本時的樣本比例：$\pi_c=\frac{y_1+y_2}{n_1+n_2}$。

- 此處由於是檢定兩比例是否相同，故以下三種表示方式均等價：
  - $\hat{\pi}_1 - \hat{\pi}_2=0$
  - $\hat{\pi}_2 - \hat{\pi}_1=0$
  - $\hat{\pi}_1 = \hat{\pi}_2$

**兩母體比例差異的推論（Inference about Difference between Two Population Proportions）**

- 相等比例的近似檢定 （Approximate Test for Equal Proportions）
  - 假設常態分佈能夠充分描述 $\hat{\pi}_1−\hat{\pi}_2$ 的抽樣分佈，則以下表達式具有標準常態分佈：

$$\text{Z-ratio}=\frac{(\hat{\pi}_1−\hat{\pi}_2)-({\pi}_1−{\pi}_2)}{\mathrm{SE}(\hat{\pi}_1−\hat{\pi}_2)}$$

  - 為了檢定虛無假說 $\mathrm{H_0}:{\pi}_1−{\pi}_2=0$，使用以下統計量：

$$\text{Z-statistic}=\frac{(\hat{\pi}_1−\hat{\pi}_2)-0}{\mathrm{SE}_0({\hat{\pi}_1−\hat{\pi}_2})}$$

  - **兩比例差異的近似信賴區間：**（Approximate Confidence Interval for Difference between Two Proportions）

$$(\hat{\pi}_1−\hat{\pi})\pm \mathrm{Z}_{1-\frac{\alpha}{2}}  \times \mathrm{SE}[(\hat{\pi}_1−\hat{\pi})]$$

### 1.11 四個 Case（含完整 R code）

#### 【材料原文】Case 1 - Obesity & Heart Disease

[圖片：2×2 列聯表，obese × CVDdeath]

- 上表顯示了 1975 年至 1980 年間，被歸類為「肥胖或非肥胖」的非洲婦女中，因心血管疾病 (CVD) 「死亡和未死亡」的人數。
- 想知道的事情是，這些婦女群體中，CVD 死亡是否與肥胖有關？
- $2 \times 2$ 表格分類：
  - CVD 死亡：Yes、No
  - Obese、Not obese

```r
#### Case1: Obesity & Heart Disease
y <- c(18,2032,8,1101)                      	# listed by row
obese <- gl(2,2,4, c("Yes","No"))           	# row names
CVDdeath <- gl(2,1,4, c("Yes","No"))        	# col names
( case <- xtabs(y ~ obese + CVDdeath) )
```

**假說檢定：**

- 肥胖婦女中 CVD 死亡的比例 $\frac{18}{2050}=0.00878$ 略高於非肥胖婦女中相對應的比例 $\frac{8}{1109}=0.00721$。
- 但估計差異 $0.00157$ 相對於其標準誤 $SE[\hat{\pi}_1-\hat{\pi}_2]=0.00327$ 而言很小。
- 因此，這些資料指出，肥胖和非肥胖非洲婦女群體中 CVD 死亡比例顯著相等。

#### 【材料原文】Case 2 - Vitamin C & Common cold

[圖片：2×2 列聯表，take × cold]

- 想知道吃安慰劑 （Placebo）及吃維他命 C（Vitamin C）的兩類人，得到感冒的比例有沒有顯著差異。
- $2 \times 2$ 表格分類：
  - 服用藥品：Placebo、Vitamin C
  - Cold、Not Cold
- 使用維生素 C 能否降低感冒的風險？
  - 這個問題光看表是回答不了的。
  - 所以才需要透過統計分析（Contingency table）的概念來回答。

```r
#### Case2: Vitamin C & Common Cold
y <- c(321,72,298,96)                       	# listed by row
take <- gl(2,2,4, c("Placebo","VC"))        	# row names
cold <- gl(2,1,4, c("Yes","No"))		      	# col names
( case <- xtabs(y ~ take + cold) )
```

#### 【材料原文】Case 3 - Smoking & Lung Cancer

[圖片：2×2 列聯表，smoker × patient]

- 在對吸菸與肺癌關聯性的調查中，採訪了 83 名肺癌患者和 83 名對照組對象，詢問他們的吸菸習慣。
  - 吸菸者的肺癌勝算與非吸菸者相比是否不同？不同多少？
  - 想知道抽菸對肺癌有沒有顯著關聯性。
    - **注意這邊找的結果通常是「關聯性」。**
- $2 \times 2$ 表格分類：
  - Cancer、Control
  - Smokers、Nonsmokers

```r
#### Case3: Smoking & Lung Cancer
y <- c(79,70,4,13)                          	# listed by row
smoker <- gl(2,2,4, c("Yes","No"))			# row names
patient <- gl(2,1,4, c("Cancer","Control"))	# col names
( case <- xtabs(y ~ smoker + patient) )
```

### 1.12 勝算（Odds）與勝算比（Odds ratio）— 投影片版

#### 【材料原文】兩個母體比例之間的差異可能不是比較它們的最佳方式

- 例如：
  - 0.50 對 0.45
    - 0.5 與 0.45 的絕對差距（數值差）為 5%。
    - 對比整體，0.5 比 0.45 高出 10%
  - 0.10 對 0.05
    - 0.10 與 0.05 的絕對差距（數值差）也為 5%。
    - 對比整體，0.10 卻比 0.05 高出 100%。
  - 兩者的比例尺有明顯的落差，若直接比較，說服力明顯不足。

**比較比例的替代方法是比較它們相對應的 Odds**

- 若 $\pi$ 是「Yes」結果的母體比例，則群體中「Yes」結果的相對應 Odds 為 $\omega=\frac{\pi}{1-\pi}$。
- 樣本 Odds：$\hat{\omega}=\frac{\hat{\pi}}{1-\hat{\pi}}$
- 習慣上在表示 Odds 時先引用較大的數字：
  - 機率為 0.95 的事件，其 Odds 是 19 比 1 「有利於」它。
  - 機率為 0.05 的事件，其 Odds 是 19 比 1 「不利於」它。

**這回答什麼行銷/商業問題**：為什麼報告裡不能只寫「轉換率從 5% 拉到 10%，只增加 5 個百分點」——同樣 5 個百分點，在低基期是翻倍、在高基期只是小幅。**這是 odds / OR 存在的商業理由**。

#### 【材料原文】勝算比（Odds ratio）

給定兩個具有比例 $\pi_1$ 和 $\pi_2$ 的群體，其相對應的 Odds 為 $\omega_1$ 和 $\omega_2$，則 Odds ratio 為 $\phi=\frac{\omega_2}{\omega_1}$。

- 若 $\omega_2>\omega_1$ ，則 $\text{Odds ratio}>1$ 。
  - 例如：$\phi=3 \Longleftrightarrow \omega_2=3\omega_1$。
    - 第 2 組中「Yes」結果的 Odds 是第 1 組中「Yes」結果的 Odds 的三倍。
    - 若第 1 組每 2 個「No」的結果有 5 個「Yes」的結果 $\Longrightarrow$ $\omega_1=2.5$。則當 $\phi=3$ 時，第 2 組每 2 個「No」的結果會有 15 個「Yes」的結果。
- 以 Case 3 為例：
  - 估計的 Odds ratio：$\hat{\phi}=\frac{\hat{\omega_2}}{\hat{\omega_1}}$
  - $\hat{\phi}=\frac{\hat{\omega_2}}{\hat{\omega_1}}=\frac{\frac{79}{70}}{\frac{4}{13}}=\frac{1.129}{0.308}=3.67$
  - 估計吸菸者患肺癌的勝算是非吸菸者患肺癌 Odds 的 3.67 倍。

#### 【材料原文】Odds ratio 的特性（Properties of the Odds Ratio）

- $0<ϕ<∞$
- 當兩個變數，或說兩個因子獨立時，$\phi=1$。
  - 當第 2 組的「成功」機率「低於」第 1 組時，$0<\phi<1$，即 $\pi_2<\pi_1$。
  - 當第 2 組的「成功」機率「高於」第 1 組時，$1<\phi<\infty$，即 $\pi_1<\pi_2$。
- 當 $\phi$ 的值離 1 越遠，表示在給定方向上的關聯性越強。
  - 例如：
    - $ϕ=4$ 時，第 2 組「成功」的 Odds 是第 1 組「成功」的 Odds 的四倍。
    - $\phi=0.25$ 時，第 2 組「成功」的 Odds 是第 1 組「成功」 Odds 的 $\frac14$ 倍。
    - $\phi$ 的兩種值（ $4$ 和 $0.25$）代表相同的關聯程度，但方向相反，反映了列和欄的順序。
- 在實務應用中，與其他衡量方式相比，Odds ratio 往往在不同層次（level）的混淆變數下（Confounding variable），表現得比較接近「常數」
  - 也就是說，跨越各個混淆因子分層時，其數值通常較為穩定。
  - 混淆變數（Confounding variable）：讓你「以為」$\mathrm{X}$ 影響 $\mathrm{Y}$，但其實是第三個因素在搞事的那個變數。
- **Odds ratio 是唯一可用於比較回溯性研究 (retrospective study) 中兩組二元反應的參數。**
- Odds 的比較可以很好地延伸到迴歸分析（後續會提到）。

#### 【材料原文】對數估計 Odds ratio 的抽樣分配（Sampling Distribution of Log Estimated Odds Ratio）

對於「樣本數偏小到中等」的情況，Odds ratio 的抽樣分配往往高度偏斜（highly skewed），不太適合直接拿來做常態近似。

若兩組母體的 Odds 分別為 $\omega_1$ 與 $\omega_2$，從兩個相互獨立的隨機樣本估計出的 Odds $\hat\omega_1$ 與 $\hat\omega_2$，所得到的估計 Odds ratio 記為 $\hat{\phi} = \frac{\hat{\omega}_2}{\hat{\omega}_1}$，則「自然對數勝算比」$\log(\hat{\phi})$ 的抽樣分配，大致具有下列性質：

- 期望值：

$$E\big[\log(\hat{\phi})\big]
\approx
\log(\phi)
= \log\!\left(\frac{\omega_2}{\omega_1}\right)$$

- 變異數：設母體成功機率為 $\pi_1$, $\pi_2$，對應樣本大小為 $n_1$, $n_2$，則

$$\operatorname{Var}\big[\log(\hat{\phi})\big]
\approx
\frac{1}{n_1 \pi_1 (1-\pi_1)}
+ \frac{1}{n_2 \pi_2 (1-\pi_2)}$$

- 當 $n_1$ 與 $n_2$ 皆足夠大時 $\log(\hat{\phi})$ 的抽樣分配可以近似為常態分配：

$$\log(\hat{\phi})
\approx
\mathcal{N}\big(\log(\phi),\ \text{ASE}^2\big)$$

其中 ASE（Asymptotic Standard Error，漸近標準誤）為

$$\text{ASE}\big[\log(\hat{\phi})\big]
=
\sqrt{
  \frac{1}{n_{11}}
  + \frac{1}{n_{12}}
  + \frac{1}{n_{21}}
  + \frac{1}{n_{22}}
}.$$

其中，

$$n_{11} = n_1 \pi_1,\quad
n_{12} = n_1 (1-\pi_1),\quad
n_{21} = n_2 \pi_2,\quad
n_{22} = n_2 (1-\pi_2)$$

分別代表 $2\times2$ 列聯表中四個 cell 的期望樣本數（成功 / 失敗 $\times$ 兩組）。

#### 【材料原文】$\log\!\left(\frac{\hat{\omega}_2}{\hat{\omega}_1}\right)$ 常用的兩種標準誤

**1. 用於信賴區間（For confidence interval）**

C.I. 用：直接反映各組自己的變異（$\hat{\pi}_1,\hat{\pi}_2$）

$$SE\big[\log(\hat{\phi})\big]
=
SE\!\left[\log\!\left(\frac{\hat{\omega}_2}{\hat{\omega}_1}\right)\right]
=
\sqrt{
  \frac{1}{n_1 \hat{\pi}_1 (1-\hat{\pi}_1)}
  +
  \frac{1}{n_2 \hat{\pi}_2 (1-\hat{\pi}_2)}
}
=
\sqrt{
  \frac{1}{n_{11}}
  + \frac{1}{n_{12}}
  + \frac{1}{n_{21}}
  + \frac{1}{n_{22}}
}$$

- 其中
  - $\hat{\pi}_1$, $\hat{\pi}_2$ 為兩組樣本中成功機率的估計值。
  - $n_{11}, n_{12}, n_{21}, n_{22}$ 為 $2 \times 2$ 列聯表四個 cell 的樣本數。

**2. 用於檢定「兩者相等」（For testing equality）**

在檢定兩組比例是否相等時，常在虛無假設 $\mathrm{H}_0: \pi_1 = \pi_2$ 之下，使用「合併後」的比例估計 $\hat{\pi}_c$ 來計算標準誤：

$$SE_{0}\!\left[\log\!\left(\frac{\hat{\omega}_2}{\hat{\omega}_1}\right)\right]
=
\sqrt{
  \frac{1}{n_1 \hat{\pi}_c (1-\hat{\pi}_c)}
  +
  \frac{1}{n_2 \hat{\pi}_c (1-\hat{\pi}_c)}
}$$

- 其中
  - $\hat{\pi}_c$ 通常為在 $\mathrm{H}_0$ 前提下的「合併樣本比例」估計值。
    - 例如：$\hat{\pi}_c = \frac{n_{11} + n_{21}}{n_1 + n_2}$
    - 代表在兩組合併後，整體的成功比例。

#### 【材料原文】R：Test for Equality of Two Population Odds

```r
## Case3: Smoking & Lung Cancer

y <- c(79,70,4,13) # listed by row
smoker <- gl(2,2,4, c("Yes","No")) # row names
patient <- gl(2,1,4, c("Cancer","Control")) # col names
( case <- xtabs(y ~ smoker + patient) )
## Odds Ratio
ptest <- prop.test(case)
( pi <- ptest$estimate ) # pi1.hat, pi2.hat
( odds <- ptest$estimate/(1-ptest$estimate) ) # odds
( phi <- odds[1]/odds[2] ) # odds ratio (phi)
log(phi) # log odds ratio
nY <- sum(case[,1]); n <- sum(case)
( pic <- nY/n ) # pic.hat
( n.r <- apply(case,1,sum) ) # n1, n2
( se0 <- sqrt(sum(1/(pic*(1-pic)*n.r))) ) # se0, test version
1-pnorm(log(phi)/se0) # p-value
```

逐段說明（材料原文）：

- 這段是在設定列聯表（Contingency table）

```r
y <- c(79,70,4,13) # listed by row
smoker <- gl(2,2,4, c("Yes","No")) # row names
patient <- gl(2,1,4, c("Cancer","Control")) # col names
( case <- xtabs(y ~ smoker + patient) )
```

- 這段是計算 Probability

```r
ptest <- prop.test(case)
```

- 這段是在設定 factor，拿來當「吸菸與否」兩組的群組變數。

```r
smoker <- gl(2,2,4, c("Yes","No"))
```

- 第一個 2 代表有 2 個層級（level），也就是吸菸與不吸菸。
- 第二個 2 代表每個層級重複 2 次。
- 第三個值 4 代表總長度為 4 筆資料。
- 第四個位置代表 labels，將 level 1 命名為 Yes，level 2 命名為 No。

#### 【材料原文】R：C.I. for Odds Ratio

```r
## C.I. for Odds Ratio
( ase <- sqrt(sum(1/case)) ) # se, CI version
( logphi.ci <- log(phi)+c(-1,1)*qnorm(0.975)*ase )
( exp(logphi.ci) ) # CI
```

#### 【材料原文】Case 3 的一些結果

吸菸與肺癌案例（Smoking and Lung Cancer Case）：

- 估計 Odds ratio（estimated odds ratio）：$\hat{\phi} = 3.668$
- 估計 Odds ratio 的自然對數：$\log(\hat{\phi}) = 1.300$
- 估計勝算比的漸近標準誤（ASE, Asymptotic Standard Error）：$\text{ASE}(\log(\hat{\phi})) = 0.595$
- 對數 Odds ratio 的 $95\%$ 信賴區間：$95\%\ \text{C.I. for } \log(\text{odds ratio}) = (0.134,\ 2.466)$
- 將上述區間指數化後得到 Odds ratio 的信賴區間：$\exp(\text{C.I.}) = (1.143,\ 11.770)$

**解讀：**

- 對於此觀察資料，吸菸者罹患肺癌的 Odds，估計約為非吸菸者的 $3.67$ 倍。
- 相對應的 $95\%$ 近似信賴區間為 $1.14$ 到 $11.77$，也就是說，在統計誤差考量下，合理的 Odds ratio 範圍 $[1.14,11.77]$。

（R code：Odds ratio）

```r
## Odds Ratio
ptest <- prop.test(case)
( pi <- ptest$estimate	)					# pi1.hat, pi2.hat
( odds <- ptest$estimate/(1-ptest$estimate) )	# odds: omega1.hat, omega2.hat
( phi <- odds[1]/odds[2] )					# odds ratio (phi)
log(phi)									# log odds ratio

nY <- sum(case[,1]); n <- sum(case)
( pic <- nY/n )							# pic.hat

( n.r <- apply(case,1,sum) )  				# n1, n2

( se0 <- sqrt(sum(1/(pic*(1-pic)*n.r))) )	    	# se0, test version
1-pnorm(log(phi)/se0)						# p-value
```

（R code：C.I. for odds ratio）

```r
## C.I. for Odds Ratio
( ase <- sqrt(sum(1/case)) )					# se, CI version
( logphi.ci <- log(phi)+c(-1,1)*qnorm(0.975)*ase )
( exp(logphi.ci) )  
```

#### ★【材料原文】注意！（推論界線）

> - **本分析是基於觀察型資料，僅能提供統計關聯的證據，不能直接作為因果推論。**
> - **「吸菸導致肺癌」仍需仰賴更嚴謹的研究設計與其他證據共同支持。**

**原始問題：**

- 在一項探討吸菸與肺癌關聯的研究中，研究者訪談了 83 位肺癌病人與 83 位對照組個體，紀錄他們的吸菸習慣。
- 研究問題：吸菸者與未吸菸者的肺癌 Odds 是否不同？若不同，大約差多少？
  - 分析結果顯示：吸菸者罹患肺癌的 Odds 顯著高於未吸菸者（約略單尾 $\text{p-value}=0.005$）。
  - 進一步估計：吸菸者罹患肺癌的勝算約為未吸菸者的 $3.67$ 倍，其近似 $95\%$ 信賴區間為 $1.14$ 倍至 $11.77$ 倍。

### 1.13 回溯性研究（Retrospective Studies）

#### 【材料原文】三個案例的共同結構

前述三個案例的設計概念、結構其實都一樣：

- 都有一個解釋變因（explanatory factor），而且只有兩個水準（level）（例如：有服用／沒服用、有肥胖／沒肥胖、吸菸／不吸菸）。
- 都有一個反應變數（response variable），且同樣都是二元。（例如：是否得病、是否存活、是否改善）。

具體來看：

- Case 1 - Obesity & Heart Disease
  - 從「解釋變因」的兩個等級中，各自隨機抽樣受試者。
  - 也就是說：先決定他屬於哪一群（例如：肥胖 vs. 非肥胖），再觀察後續的健康結果。
- Case 2 - Vitamin C & Common cold
  - 受試者被**隨機指派**到不同的解釋變因等級（例如：安慰劑、維他命 C）。
  - 一樣是先設定「處理／條件」，再往後看反應。

> 這兩種設計，都屬於 prospective sampling（前瞻性取樣）：先設定或觀察解釋變因的狀態，接著「往未來」追蹤反應結果。

- Case 3 - Smoking & Lung Cancer
  - 這裡的作法剛好相反：
    - 先固定「反應變數」的兩個等級來取樣：83 位肺癌病人（cases）、83 位沒有肺癌的對照組（controls）
    - 接著再去回頭訪問他們的「吸菸史」。

> 這種是 retrospective sampling（回溯性取樣）：先依照結果（有病 vs. 沒病）抽樣，再「往過去」回頭看暴露或群組。

#### 【材料原文】為什麼要做回溯性研究？

兩個主要理由：

1. 不用長時間追蹤受試者
   - 前瞻性研究常常要「等事件發生」。例如：追蹤 10 年看誰會得某種疾病。
   - 回溯性研究則是「病人已經存在」，我們直接從醫院或資料庫裡找病人與對照，再去回頭問他們過去的暴露情況（例如吸菸史）。在時間與成本上都能夠節省很多。
2. 當「正向反應機率很小」時，前瞻性研究非常「費樣本數」
   - 若某疾病本來就很罕見，在前瞻性設計裡：你可能得追蹤幾千、幾萬人，才會看到足夠多的「Yes（發病）」案例。
   - 回溯性設計可以直接：固定招募一批「已發病」的人（cases）、再招募一批「沒發病」的人當對照（controls）、然後比較兩組過去的暴露比例（例如：吸菸比率）。

- 簡單說：
  - 當事件很少見、又不想花多年追蹤時，回溯性研究是一個更實際的選項。
  - **但代價是：設計上比較容易遇到選樣偏誤、回憶偏誤等問題，因此在「因果解釋」上必須更小心。**

#### 【材料原文】前瞻式 vs 回溯式研究的取樣

- Prospective study：先看解釋變因，再往未來看結果
  - 在 前瞻性研究 中，研究者會先依照預先設定好的「解釋變因等級」來抽樣或分派受試者（例如：有服用 / 沒服用、處理組 / 對照組）。
  - 之後再隨時間發展，觀察並記錄他們的反應結果。
- Retrospective study：先看結果，再回頭追暴露
  - 在回溯性研究中，研究者會先依照「反應變數的狀態」來抽樣受試者（例如：先找已罹病者 vs 未罹病的對照組）。
  - 接著再回頭去調查、重建他們過去的解釋變因或暴露情形（例如：過去是否吸菸、是否接觸某種風險因子）。

#### 【材料原文】Odds ratio 與回溯性取樣（Odds ratio & Retrospective Sampling）

**為什麼在回溯性資料裡，幾乎只考慮 odds ratio？**

在回溯性研究中，是先依照「結果」分成 case / control，再回頭看暴露情形。

- 在這種設計下，樣本中各組的人數是我們「刻意控制」出來的（例如：硬是抓 83 個肺癌、83 個對照），
- 所以無法從樣本裡，直接估計「真實族群裡」吸菸者和未吸菸者罹癌的母體比例或其差異。
- 在這種情況下，真正還可以被穩健估計的，就是 Odds ratio。

以投影片的方式說，就是：

- 對於「不同暴露族群的二元結果」，在回溯性資料裡，odds ratio 幾乎是唯一一個可以好好被估計的效果指標。
- 例如：Case 3 - Smoking & Lung Cancer
  - 你不能從這個樣本直接說「吸菸者罹癌率是幾 ％」、「未吸菸者罹癌率是幾 ％」，因為 case / control 的人數是研究者自己設的。
  - 但你可以估計：「在這個族群裡，吸菸 vs 不吸菸的罹癌的 odds ratio 大約是多少」。

**Odds ratio 不會因為「誰當 response」而改變**

考慮下面這種 $2×2$ 的真實分布的例子（不是那個 83 vs 83 的樣本，而是假設在母體中）：

$$\begin{array}{c|cc}
  & \text{Lung Cancer} & \text{No Cancer} \\
  \hline
  \text{Smokers}     & 1{,}000 & 2{,}000{,}000 \\
  \text{Non-Smokers} & 4{,}000 & 16{,}000{,}000
\end{array}$$

1. 把「是否肺癌」當成反應變數，計算「在吸菸與否下的罹癌 odds ratio」：
   - 吸菸者罹癌的 odds：$\text{odds}(\text{Cancer} \mid \text{Smoker}) = \frac{1{,}000}{2{,}000{,}000}$
   - 未吸菸者罹癌的 odds：$\text{odds}(\text{Cancer} \mid \text{Non-Smoker}) = \frac{4{,}000}{16{,}000{,}000}$
   - Odds ratio（癌症在吸菸 vs 未吸菸）：

$$\text{OR}
=
\frac{\text{odds}(\text{Cancer} \mid \text{Smoker})}
     {\text{odds}(\text{Cancer} \mid \text{Non-Smoker})}
=
\frac{1{,}000/2{,}000{,}000}{4{,}000/16{,}000{,}000}
= 2$$

2. 把「是否吸菸」當成反應變數，計算「在癌症與否下的吸菸 odds ratio」：
   - 在肺癌病人中是吸菸者的 odds：$\text{odds}(\text{Smoker} \mid \text{Cancer}) = \frac{1{,}000}{4{,}000}$
   - 在非肺癌者中是吸菸者的 odds：$\text{odds}(\text{Smoker} \mid \text{No Cancer}) = \frac{2{,}000{,}000}{16{,}000{,}000}$
   - Odds ratio（吸菸在癌症 vs. 非癌症）：

$$\text{OR}
=
\frac{\text{odds}(\text{Smoker} \mid \text{Cancer})}
     {\text{odds}(\text{Smoker} \mid \text{No Cancer})}
=
\frac{1{,}000/4{,}000}{2{,}000{,}000/16{,}000{,}000}
= 2$$

3. 可以看到：不管把「肺癌」當反應、還是把「吸菸」當反應，算出來的 odds ratio 都是一樣是 2。
   - 呼應了投影片中「The odds ratio is the same regardless of which factor is considered the response.」
   - 因此 odds ratio 在 $2×2$ 表裡有一個很重要的性質：
     - 只要底層 2×2 的 cell 次數一樣，不管你怎麼切「誰是解釋、誰是反應」，odds ratio 本身是不變的。

4. ★ 要特別注意的：**「在肺癌病人與對照組中，吸菸者所佔的比例」並不能告訴我們「在整體吸菸者與非吸菸者族群中，肺癌患者所佔的比例」。**

   白話來說：
   - 我們可以算出：「在肺癌病人裡有幾成是吸菸者」、「在對照組裡有幾成是吸菸者」。
   - 但這些數字無法直接推回：「吸菸者族群中罹癌率是多少」、「非吸菸者族群中罹癌率是多少」。
   - 即便如此，odds ratio 的數值卻不會因為你把哪一個變數當作反應變數而改變。
     - 若從「肺癌病人 vs 對照組」的角度看，在肺癌患者中是吸菸者的 odds，是在對照組中是吸菸者 odds 的 2 倍。
     - 若從「吸菸者 vs 非吸菸者」的角度看，在吸菸者中罹患肺癌的 odds，是在非吸菸者中罹患肺癌 odds 的 2 倍。

   同一個 odds ratio 可以用兩種取樣設計來估計：
   - 前瞻式設計：對「吸菸者」與「非吸菸者」各自抽樣，直接觀察這兩組的肺癌發生率。
   - 回溯式設計：對「肺癌病人」與「對照組」各自抽樣，只觀察這兩組裡「吸菸者所佔的比例」。

   簡易結論：
   - Odds ratio 是在回溯性研究中，唯一一個仍然可以連結回「前瞻式」的效果量。
   - Odds ratio 是唯一能從回溯性資料中，被合理估計出來、並用來描述原始族群關聯程度的指標。

**這回答什麼行銷/商業問題**：行銷資料常常是「回溯式」的——先撈出已購買名單和未購買名單，再回頭看誰接觸過哪些觸點。**這種資料算出來的「轉換率」是假的（因為兩群人數是你自己撈的），但 OR 是真的**。這條規則決定了歸因報告能寫什麼、不能寫什麼。

### 1.14 列聯表（Contingency Table）— 投影片版

#### 【材料原文】

- 類別資料（categorical data）
  - 我們只關心每一種「類別」出現了幾次，而不是連續數值本身。
  - 資料是由各個反應類別的次數統計（frequency counts）所組成。
- 兩個類別變數的設定：
  - 設 $\mathrm{X}$ 與 $\mathrm{Y}$ 為兩個類別型變數：
    - $\mathrm{X}$：共有 $\mathrm{I}$ 個類別（levels）。
    - $\mathrm{Y}$：共有 $\mathrm{J}$ 個類別（levels）。
- 列聯表的基本概念 $\mathrm{I} \times \mathrm{J}$
  - 我們會把 $\mathrm{X}$ 與 $\mathrm{Y}$ 所有可能的組合，整理成一個有 $\mathrm{I} \times \mathrm{J}$ 個格子（cells）的表格，每一格放的是「落在該組合的觀測次數」。
- 表格的結構：一個列聯表會：
  - 以 $\mathrm{I}$ 個列（rows） 對應 $\mathrm{X}$ 的各個類別。
  - 以 $\mathrm{J}$ 個欄（columns） 對應 $\mathrm{Y}$ 的各個類別。
- 白話小結：
  - 列聯表就是把「兩個類別變數」所有可能的組合一一列出來，每一格放上「這種組合在樣本中出現了幾次」，方便後續以 Chi-square test 做關聯性分析。

### 1.15 卡方檢定（Chi-squared test）— 投影片版（含自由度推導）

#### 【材料原文】卡方獨立性檢定（Chi-squared test of independence）

我們的目標是檢定虛無假說：

- $\mathrm{H}_0:$ 每一個 cell 的機率 $π_{ij}$ 等於某一組「指定好的」固定值 $\{π_{ij}\}$
- 對一個樣本大小為 $n$ 的列聯表，我們在每個 cell 觀察到的次數記為 $\{n_{ij}\}$。
- 在 $\mathrm{H}_0$ 為真時，對應的期望次數（Expected frequencies） 定義為 $\mu_{ij} = n\pi_{ij}$。
  - 這些 $\{\mu_{ij}\}$ 就是 $E(n_{ij})$ 的理論值。

檢定的基本想法是：

- 把樣本中實際觀察到的 cell 次數 $\{n_{ij}\}$，和理論上的期望次數 $\{\mu_{ij}\}$ 做比較，來判斷資料是否「明顯偏離」虛無假設 $\mathrm{H}_0$。

若在一個二維列聯表中，$\mathrm{H}_0$ 確實不被拒絕，則每一格的觀察值 $n_{ij}$ 應該會靠近對應的期望值 $\mu_{ij}$。

- $|n_{ij} - \mu_{ij}|$ 的差距越大、整體偏離越明顯，就代表反對 $\mathrm{H}_0$ 的證據越強。
- 下一個步驟將會把這些差距代入卡方統計量 $\chi^2 = \sum \frac{(n_{ij}-\mu_{ij})^2}{\mu_{ij}}$ 做正式檢定。

**在「獨立性」的虛無假說下：**

我們假定：

$$H_0:\ \pi_{ij} = \pi_{i+}\,\pi_{+j} \quad \text{for all } i,j$$

- 其中
  - $\pi_{ij} = P(X=i, Y=j)$：第 $i$ 列、第 $j$ 欄的聯合機率
  - $\pi_{i+} = P(X=i)$：第 $i$ 列的列邊際機率
  - $\pi_{+j} = P(Y=j)$：第 $j$ 欄的欄邊際機率。
- 也就是說，在獨立性假設下，邊際機率就可以決定聯合機率。

要在樣本中檢定 $\mathrm{H}_0$，我們先把每一格在 $\mathrm{H}_0$ 為真時的「理論期望次數」寫成：

$$\mu_{ij} = n\pi_{ij} = n\pi_{i+}\pi_{+j}$$

- 此處 $\mu_{ij}$ 代表：若 $\mathrm{X}$ 與 $\mathrm{Y}$ 真的是獨立的，樣本大小為 $n$ 時，第 $i,j$ 格的期望值 $\mathrm{E}(n_{ij})$。

真實情況下，$\pi_{i+}$ 和 $\pi_{+j}$ 都是未知的，因此我們用樣本比例來取代它們：

- 列方向的樣本比例：$p_{i+} = \frac{n_{i+}}{n}$，其中 $n_{i+}$ 是第 $i$ 列的合計。
- 欄方向的樣本比例：$p_{+j} = \frac{n_{+j}}{n}$，其中 $n_{+j}$ 是第 $j$ 欄的合計。
- 把這兩個代入，就得到「期望次數的估計值」：

$$\widehat{\mu}_{ij}
= n p_{i+} p_{+j}
= n \left(\frac{n_{i+}}{n}\right)\left(\frac{n_{+j}}{n}\right)
= \frac{n_{i+} n_{+j}}{n}$$

- 這個公式是實作卡方檢定時最重要的一步：
  - 在獨立性假設下，第 $i,j$ 格的期望次數 =（該列總數 × 該欄總數）÷ 總樣本數。

#### 【材料原文】卡方統計量

**Pearson 卡方統計量（用來檢定 $\mathrm{H}_0$）**

$$\chi^2 = \sum_{i}\sum_{j} \frac{(n_{ij}-\hat{\mu}_{ij})^2}{\hat{\mu}_{ij}}$$

- $n_{ij}$：第 $i$ 列、第 $j$ 欄的實際觀察次數。
- $\hat{\mu}_{ij}$：在獨立性假設 $\mathrm{H}_0$ 底下，對應 cell 的期望次數估計值 $\hat{\mu}_{ij} = \frac{n_{i+}n_{+j}}{n}$
- 直覺：觀察每一格的「觀察值 − 期望值」的差距有多大、多嚴重，差距越大，整體的 $\chi^2$ 就越大，反對 $\mathrm{H}_0$ 的證據越強。

**對數概似比卡方統計量（Likelihood-Ratio Chi-Squared）**

$$\mathrm{G}^2 = 2\sum_{i}\sum_{j} n_{ij} \log\!\left(\frac{n_{ij}}{\hat{\mu}_{ij}}\right)$$

- 這個統計量來自「最大概似（Maximum-likelihood）」的想法：
  - 比較下列兩模型的概似差異
    - 在 $\mathrm{H}_0$ 限制下的模型
    - 不受限制（最一般）的模型
- 在樣本數夠大時，$\mathrm{G}^2$ 也近似服從卡方分配，自由度與 $\chi^2$ 相同。
- 實務上，R 裡的 `chisq.test()` 會給你 Pearson 統計量，某些教科書或軟體也會一併報告 $\mathrm{G}^2$。兩者在大樣本時結論通常很接近。

【評註】$\mathrm{G}^2$ 就是後面 logistic regression 的 **Deviance** 的同一個東西——現在先在列聯表脈絡下建立起來，1118 / 1125 會直接沿用。

**最大概似的概念與例子（材料原文）**

- 結論先行：找一個模型參數，使當前觀測的資料集合發生的可能性達最高。
- 例子：假設在路上撿到一枚硬幣，想知道它是公平的（正反面機率 $p=0.5$）還是不公平的（如 $p=0.8$）。
  1. 進行實驗： 拋了 10 次硬幣，結果出現了 7 次正面（H） 和 3 次反面（T）。
  2. 定義「概似性（Likelihood）」：
     - 概似性不是數據的機率，而是「參數在給定數據下」的「可信度」。
     - 假設硬幣正面機率為 $p$。觀察到 $\{7\mathrm{H}, 3\mathrm{T}\}$ 的機率是：

$$\mathrm{L}(p) = \mathrm{P}(\text{7H, 3T} | p) = \binom{10}{7} p^7 (1-p)^3$$

  3. 計算不同參數的「概似性」：
     - 假設 1（公平）： 若 $p=0.5$，出現 $\{\text{7H, 3T}\}$ 的概似性 $\mathrm{L}(0.5)$ 是某個值。
     - 假設 2（不公平）： 若 $p=0.8$，出現 $\{\text{7H, 3T}\}$ 的概似性 $\mathrm{L}(0.8)$ 是另一個值。
     - 假設 3（其他 $p$ 值）： 可以計算所有 $p$ 值（從 0 到 1）的概似性。
     - 最大化： 會發現，當 $p=0.7$ 時，這個概似函數 $\mathrm{L}(p)$ 達到最大值。
  4. 最大概似估計值 (Maximum Likelihood Estimate, MLE)
     - 在此例中，最大概似估計值（MLE）就是 $\hat{p} = 0.7$。
     - 這個 $p=0.7$ 的參數，是最能解釋觀測到「$7$ 次正面，$3$ 次反面」這個結果的參數。
     - 最大概似法就是找到一個 $\mathrm{\theta}$ 參數，使 $P(\text{數據} | \theta)$ 達到最大！

#### 【材料原文】自由度（degree of freedom, $\mathrm{d}_\mathrm{f}$）

- 對一個 $\mathrm{I} \times \mathrm{J}$ 的列聯表，兩種統計量 $\chi^2$、$\mathrm{G}^2$ 在 $\mathrm{H}_0$ 底下都近似服從 $\chi^2_{(I-1)(J-1)}$
- $\mathrm{d}_\mathrm{f}=(\mathrm{I}−1)(\mathrm{J}−1)$

**為什麼自由度是 $(\mathrm{I}−1)(\mathrm{J}−1)$？**

- 在虛無假說 $\mathrm{H}_0:\text{獨立}$ 下，我們假設：
  - $\pi_{ij} = \pi_{i+}\pi_{+j}$
  - 亦即只要知道列邊際機率 $\{\pi_{i+}\}$ 和欄邊際機率 $\{\pi_{+j}\}$，就能決定每一格的機率 $\pi_{ij}$。
  - 列邊際機率有 $\mathrm{I}$ 個，但因為要滿足 $\sum_{i=1}^{I} \pi_{i+} = 1$，所以只有 $\mathrm{I}−1$ 個是「真正獨立」的參數（最後一個可由前面推得）。
  - 欄邊際機率有 $\mathrm{J}$ 個，但因為 $\sum_{j=1}^{J} \pi_{+j} = 1$ ，所以也只有 $\mathrm{J}−1$ 個是獨立的。
- 因此，在 $\mathrm{H}_0$ 模型底下，**需要估計的參數總數是** $(\mathrm{I}−1)+(\mathrm{J}−1)$

在對立假說 $\mathrm{H}_1$ 下

- 對立假說 $\mathrm{H}_1$ 並沒有指定任何獨立結構，只是要求 $\sum_{i=1}^{I}\sum_{j=1}^{J} \pi_{ij} = 1$
- 共有 $\mathrm{I}\times \mathrm{J}$ 個 cell 機率 $\pi_{ij}$，但因為總和必須是 1，所以真正獨立的參數數量是：$\mathrm{I}\times\mathrm{J}-1$

自由度 = 兩個模型「參數數量的差」

- 卡方檢定的自由度，可以理解成以下兩模型的「參數數量差」：
  - **「沒有約束的模型」**
  - **「有約束的 $\mathrm{H}_0$ 模型」**
- 在 $\mathrm{H}_A$ 下：$\mathrm{I}\times\mathrm{J}-1$ 個參數。
- 在 $\mathrm{H}_0$ 下：$(\mathrm{I}−1)+(\mathrm{J}−1)$ 個參數。
- 差值就是自由度：

$$df
=(\mathrm{IJ}−1)−[(\mathrm{I}−1)+(\mathrm{J}−1)]
=\mathrm{IJ}−1−\mathrm{I}−\mathrm{J}+2
=\mathrm{IJ}-\mathrm{I}-\mathrm{J}+1
=(\mathrm{I}−1)(\mathrm{J}−1)$$

- 這就是為什麼對任何 $\mathrm{I} \times \mathrm{J}$ 列聯表，我們在做卡方獨立性檢定或同質性檢定時，最後查表或算 $\text{p-value}$ 時用的自由度，通通都是 $(\mathrm{I}−1)(\mathrm{J}−1)$。

【評註】**「自由度 = 兩個模型參數數量的差」這個框架要記牢**——1118 / 1125 的 Drop-in-Deviance 檢定用的是完全一樣的邏輯，只是把「列聯表模型」換成「GLM」。

#### 【材料原文】Case 4（happyliving.csv）完整 R code

```r
#### Contingency Tables --------------------------------------------------------

# Read csv
df <- read.csv("happyliving.csv", header=TRUE, sep=",", fileEncoding="UTF-8-BOM")
( case <- xtabs(cbind(df[,2],df[,3],df[,4],df[,5],df[,6])~df[,1]) )

# Pearson chi-squared
chisq.test(case, correct=F)

( Xsq <- chisq.test(case, correct=F)$statistic )
pchisq(Xsq, df=4*8, lower.tail=F)

( pij <- prop.table(case) )
( mpr.r <- apply(pij,1,sum) )		# marginal probability by row
( mpr.c <- apply(pij,2,sum) )		# marginal probability by column

( mu.hat <- outer(mpr.r, mpr.c)*sum(cbind(df[,2],df[,3],df[,4],df[,5],df[,6])) )

# Likelihood-Ratio chi-squared
( Gsq <- 2*sum(case*log(case/mu.hat)) )
pchisq(Gsq, df=4*8, lower.tail=F)
```

分段說明（材料原文）：

- 把原始表格整理成「列聯表」

```r
( case <- xtabs(cbind(df[,2],df[,3],df[,4],df[,5],df[,6])~df[,1]) )
```

- 進行卡方檢定

```r
chisq.test(case, correct = FALSE)
```

- 手動抓出 $\chi^2$ 、計算 $\text{p-value}$，並自算 $\mathrm{G}^2$

```r
## 提卡方 ##
( Xsq <- chisq.test(case, correct=F)$statistic )

## 算卡方 p-value ##
pchisq(Xsq, df=4*8, lower.tail=F)

## 提對數卡方 ##
( Gsq <- 2*sum(case*log(case/mu.hat)) )

## 算對數卡方 p-value ##
pchisq(Gsq, df=4*8, lower.tail=F)
```

- 從列聯表計算「邊際機率」

```r
## 算每一個 cell 的機率 ##
( pij <- prop.table(case) )

## 算欄機率 ##
( mpr.r <- apply(pij,1,sum) )		# marginal probability by row

## 算列機率 ##
( mpr.c <- apply(pij,2,sum) )		# marginal probability by column

## 透過邊際機率的乘積 × 總樣本數得到「期望次數」 ##
( mu.hat <- outer(mpr.r, mpr.c)*sum(cbind(df[,2],df[,3],df[,4],df[,5],df[,6])) )
```

[圖片：列聯表輸出、chisq.test 輸出、列機率、欄機率、期望次數表]

**結果解讀（材料原文）：**

- $\alpha=0.05$
- 檢定統計量：$\chi^2 = 46$
- 自由度：$\mathrm{d}_\mathrm{f} =(\mathrm{I}-1)(\mathrm{J}-1)= 32$
  - 其中 $\mathrm{I}=9$ ，題目數。$\mathrm{J}=5$ ，回應選項數。
- $\text{p-value} = 0.052$
- 解讀：
  - 若以 $\alpha = 0.05$ 當作顯著水準：
  - $\text{p-value} = 0.052 \approx 0.05$，略大於 0.05，嚴格來說「尚不足以拒絕 $\mathrm{H}_0$」。
  - 資料並沒有提供很強的證據，去主張「不同題目的回應分布差很多」。

#### 【材料原文】卡方檢定的建議

**需要足夠大的樣本（Large samples）**

- 不論是 Pearson 卡方統計量 $\chi^2$，或 Likelihood-Ratio 卡方統計量 $\mathrm{G}^2$，它們「在虛無假設下服從 $\chi^2$ 分配」這件事，都是一種大樣本近似。
- 白話的說：
  - 樣本數 $n$ 要相對於 cell 數 $\mathrm{IJ}$ 夠大，$\chi^2$ 和 $\mathrm{G}^2$ 的抽樣分配才會真的「像一個 $\chi^2$」。
  - 若每一格的期望次數太小，卡方的近似會變差，此時就要小心解讀，或改用合併類別等作法。

**把變數視為名目尺度（Nominal），不利用順序資訊**

- 在計算 $\chi^2$、$\mathrm{G}^2$ 時，用到的期望次數估計值為 $\hat{\mu}_{ij} = \frac{n_{i+}n_{+j}}{n}$
  - 這個公式完全不會用到「列與欄的排列順序」：
    - 就算把第 1、2 列互換，或把類別順序顛倒，得到的 $\hat{\mu}_{ij}$、$\chi^2$、$\mathrm{G}^2$ 數值都一樣。
- 白話的說：
  - 卡方檢定把兩個變數都當成 nominal（名目變數），只在意「是哪一格」與「多少人」，不會利用到任何「大小／順序」的資訊。

如果類別本身就具有自然順序，例如 1 ~ 5 分的滿意度，但仍然只用一般卡方檢定進行檢驗，其實就隱含著「刻意不用順序資訊」前提，這種情況在設計分析稍微注意。

#### ★【材料原文】卡方檢定的限制

**只給你 $\text{p-value}$，沒有「效果量」的參數**

- 一般的列聯表的卡方檢定，輸出最重要的就是一個：$\text{p-value}$
- 它回答到的其實只有一句話：
  - 「在 $\mathrm{H}_0$（獨立或同質）為真的前提下，看到這麼極端或更極端的資料機率大不大？」
- 但沒有提供一個明確的「關聯強度」參數。
  - 例如：我們不知道「兩變數關係是弱關聯、還是超級強」。
  - 這時才會需要另外看 odds ratio、Cramér's V 等效果量指標。
  - 卡方本身並不負責描述「有多強」，只負責說「顯不顯著」。

**對立假說太「籠統」**

- 只說「不獨立」，但不會告訴你「為什麼不獨立」。
  - 卡方檢定的對立假設通常只是：「列與欄不獨立。」
  - 這是一個非常空泛的說法，因為它沒辦法：
    - 告訴你是哪幾個 cell 貢獻最多的差距。
    - 告訴你關聯大致是線性、階層式，還是只在某幾個類別上特別強。
  - 尤其是以下狀況時更嚴重：
    - 列數、欄數都大於 2，例如 $4×5$ 的列聯表。
    - 資料裡可能存在某種「更具體的結構」：例如隨年齡層單調遞增、某幾個類別組合特別突出時。
    - 單純一個卡方檢定，只會告訴你「整體上有關聯」，但不會說「關聯長什麼樣子」。
- 這時通常會往更進階的模型走，例如：
  - 一般化線性模型（Generalized Linear Model, GLM）
  - Logistic regression（邏輯斯迴歸）
  - Log-linear model（對數線性模型）
- 這些方法可以把「哪一個變數、哪一種交互作用」寫成參數，更精細地描述、解釋類別變數間的關係。

【評註】**這一段就是整份材料從「檢定」跨到「模型」的轉折點**，也是新 Skill 應該內建的決策規則：卡方顯著 → 只證明有關聯 → 要講「誰貢獻多少、控制其他因素後還在不在」就必須進 logistic regression。

### 1.16 抽樣方法（Sampling Schemes）— 五種設計與各自可估參數

#### 【材料原文】卜瓦松抽樣（Poisson Sampling）

- 情境：
  - 先設定好要觀察哪些特徵、哪些項目、哪些變數，以及相對應的類別。
  - 在一段固定的時間或空間範圍內，觀察事件發生的次數，然後依照列聯表的 cell（格子）把每一筆觀測歸類進去。
  - 例子：
    - 想知道公館舟山路上，一段時間內有多少人流量、車流量的問題。
      - 可以設定觀察時間一小時。
      - 觀察內容可以是：車種、人流量、有無違規行為…等。
  - 在這種情況下，可以使用 Poisson sampling model。
- Poisson 取樣模型的想法是：
  - 列聯表中每一個 cell 的次數，都可以視為一個互相獨立的 Poisson 隨機變數。
- 例子：
  - 統計某醫院一年內不同科別 $\times$ 不同疾病類型的門診人次；
  - 每一格「科別 $\times$ 疾病」的看診次數，就當作一個 Poisson random variable。

#### 【材料原文】多項式分配抽樣（Multinomial Sampling）

- Multinomial 抽樣跟 Poisson 抽樣很像，但有一個關鍵差異：
  - 在 multinomial sampling 中，總樣本數 $n$ 會先被研究者固定住，而不是讓每一列或每一欄的總數自由生成。
  - 白話來說：
    - 與 Poisson 的差異是，Multinomial 是直接設定好要觀察的總數。
      - 例如：要觀察到 500 個樣本，那到達這個數量就會停止觀察。
- 常見設定：
  - 欄（Columns）：反應類別
  - 欄（Rows）：解釋變因或族群（原文如此）
- multinomial 的意義是：
  - 我們從樣本中一次一次抽個體，每個個體會被歸類到「多個可能 cell 之一」，而所有 cell 的次數和，加起來就是事先固定好的總樣本數 $n$。
- 直覺例子：
  - 抽 500 位顧客，記錄他們的「性別 $\times$ 是否滿意服務」。
  - 500 這總人數是先決定的，然後看看這 500 人分別落在 4 個 cell 各有多少人：男滿意、男不滿意、女滿意、女不滿意

#### 【材料原文】前瞻式 product binomial 抽樣（Prospective Product Binomial Sampling）

- 做法是先依照解釋變因的水準，切出兩個或多個母體，例如：
  - 吸菸者 vs. 非吸菸者。
  - 暴露 vs. 未暴露。
- 接著從每一個母體中各自抽樣，每一列（每個 explanatory level）的樣本數是研究者事先決定好的。
- 這種設計就是我們前面說的 prospective sampling：
  - 先看「暴露／群組」，再往後觀察二元反應：有病 vs. 沒病、購買 vs. 未購買

#### 【材料原文】回溯式 product binomial 抽樣（Retrospective Product Binomial Sampling）

- 相對於前瞻式，此方法的順序相反：
  - 先依照反應變數的水準切出子母體，例如：有病 vs 沒病（case vs control）。
  - 接著從每一個「反應類別」的子母體中，各自抽樣，每一欄的樣本數，是研究者事先固定的。
- 這與先前提及的 retrospective sampling / case–control 設計相同：
  - 先找一定數量的肺癌病人 & 一定數量的對照，再回頭問他們過去是否吸菸、是否暴露等等。

#### 【材料原文】隨機化二元實驗設計（Randomized Binomial Experiment）

- 此處的重點是「隨機分派（randomization）」：
  - 受試者被隨機分配到解釋變因的兩個等級，例如：新藥組 vs. 安慰劑組。介面 A vs. 介面 B。
  - 可以這樣記：
    - Randomized binomial experiment $=$ 「研究者先決定每一組的人數」$＋$「受試者是隨機被分配進去」的前瞻式 product binomial。
- 除了「分派方式是隨機」以外，整體架構其實跟 prospective product binomial sampling 幾乎一樣：
  - 一樣是先決定每一組要收多少人，再從每組去觀察二元結果：有無改善、有無購買。
- **這種設計的好處是：因為有隨機化，理論上可以平衡已知與未知的混淆變數，所以在談處理效果（treatment effect）時，比觀察性設計更有說服力。**

#### ★【材料原文】總結比較（五種抽樣設計）

- **Poisson sampling**
  - 沒有在事先設定好任何值，僅有要求要觀察「多久」，因此在列聯表的呈現中，沒有任何值的限定，根據樣本結果照單全收。
  - 可以做同質性檢驗。
  - 可以做獨立性檢驗。
  - Proportion & odds 都可以被估計。
- **Multinomial sampling**
  - 會事先決定觀察樣本的總量（Grand total or Capital total）。
  - 可以做同質性檢驗。
  - 可以做獨立性檢驗。
  - Proportion & odds 都可以被估計。
- **Prospective product binomial sampling**
  - 會事先決定列資料的總量（Row total）。
  - 只能做同質性檢驗。
  - Proportion & odds 都可以被估計。
- **Retrospective product binomial sampling**
  - 會事先決定欄資料的總量（Column total）。
  - 只能做同質性檢驗。
  - **且只能用 odds ratio 檢驗，proportion 無法被估計。**
- **Randomized binomial experiment**
  - 會事先決定列資料的總量（Row total）。
  - 只能做同質性檢驗。
- 但上述的所有抽樣，在數學檢驗上都一樣採卡方檢定。

[圖片：不同取樣設計下，可以檢定什麼？能估哪些參數？（對照表）]

- $\pi_1,\pi_2$ 群體 1 及 2 的「Yes」機率。
- $\omega_1,\omega_2$ 群體 1 及 2 中「Yes」的 odds。

**【評註】整理成決策表（依材料內容重排，非新增資訊）：**

| 抽樣設計 | 事先固定 | 同質性檢定 | 獨立性檢定 | 可估 proportion | 可估 odds / OR |
|---|---|---|---|---|---|
| Poisson | 只固定觀察時間 | ✔ | ✔ | ✔ | ✔ |
| Multinomial | 總樣本數 $n$ | ✔ | ✔ | ✔ | ✔ |
| Prospective product binomial | 列總和 (row total) | ✔ | ✘ | ✔ | ✔ |
| Retrospective product binomial | 欄總和 (col total) | ✔ | ✘ | **✘** | ✔（**只有 OR**） |
| Randomized binomial experiment | 列總和 (row total) | ✔ | ✘ | ✔ | ✔ |

**這回答什麼行銷/商業問題**：拿到一份行銷資料的第一件事就是問「這是怎麼撈出來的？」——是固定時段全撈（Poisson）、固定樣本數（Multinomial）、先分曝光/未曝光再看買不買（Prospective）、先撈買/沒買再回頭看觸點（Retrospective）、還是真的做了隨機分流（Randomized）。**這一步決定了報告能寫什麼指標，寫錯就是方法論錯誤，不是解讀角度問題。**

---

<a id="part-2"></a>
## Part 2 — 1118：GLM 家族與 Binary Logistic Regression

【評註】1118 分成三大塊：(a)「回顧」——把先前 MLR 的變數選擇、交互作用、影響點診斷等 synced block 整包搬過來；(b)「GLM - Logistic - Binary」——GLM 三大構件 + binary logistic + 模型推論 + 兩個 Case；(c)「GLM - MLE - Model - Assessment」——概似函數 / MLE / 殘差 / Deviance 適合度檢定。以下依序保留。

### 2.0 回顧區（MLR 的變數選擇 / 交互作用 / 影響點）

【評註】這一整區是 Notion 的 synced block（同步區塊），內容來自前面幾週的 MLR 章節。**它之所以被放在 logistic 這一頁的最前面，是因為這些工具在 logistic regression 裡完全照搬**：`step()`、`anova()` 巢狀檢定、階層性原則（preserving hierarchy）、交互作用的截距差 / 斜率差解讀、outlier / leverage / Cook's D。以下保留其中與 logistic 直接相關的部分（完整 MLR 診斷細節屬於前一章材料）。

#### 【材料原文】變數選擇：三種檢定的定位

- **全體有用性檢定（Global Usefulness F-Test）**
  - 用來檢定是否存在至少一個 $\beta$ 不為 0 。
  - $\beta_0=\beta_1=…=\beta_k=0$
  - 統計量：$\text{F-statistics} = \frac{\frac{SSR}{k}}{\frac{SSE}{n-k-1}} = \frac{\frac{(SST-SSE)}{k}}{\frac{SSE}{n-k-1}} =\frac{\frac{R^2}{k}}{\frac{1-R^2}{n-k-1}}$
- **巢狀結構下的部分 F 檢定（Nested model Partial F-Test）**
  - 用來檢定新增的一組變數是否存在至少一個 $\beta$ 不為 0。
  - $H_0：\beta_{r+1}=\beta_{r+2}=…=\beta_k=0$
  - 統計量：$\text{Partial F-statistics}=\frac{\frac{SSE_R-SSE_C}{k-r}}{\frac{SSE_C}{n-k-1}} \sim F_{k-r,n-k-1}$
- **個別參數 t-Test（Individual parameter t-test）**
  - 用來檢定新增的一個變數，其 $\beta$ 是否不為 0。
  - $H_0：\beta_p=0$（$X_p$ 在控制其他變數後沒有線性效果）

【評註】這三層在 logistic 裡的對應物：Global F → Null Deviance vs Residual Deviance 的 LRT；Partial F → **Drop-in-Deviance test**（`anova(m1, m2, test="Chisq")`）；individual t → **Wald test**（`summary()` 的 z value）。

#### 【材料原文】使用原則

- 先有理論支撐 ，再做檢定。
- 減少不必要的多重檢定。
- 若大量比對，可輔以交叉驗證做模型取捨。
- 效果大小與解讀要一併呈現（彈性、變化率、邊際效果），不能只報 $\text{p-value}$。
- 變數轉換或交互項的引入要能改善殘差型態與假設，而不是只讓 $\text{p-value}$ 變小。

#### 【材料原文】實務上的快速流程

1. 用 Global Usefulness F-Test 確認模型有訊號。
2. 針對候選區塊做 Nested model Partial F-Test（例如加入 $X^2$ 項、交互項）。
3. 在通過 (2) 後，再看 Individual parameter t-test 與信賴區間，決定保留的欄位。
4. 以殘差圖、診斷（槓桿 / Cook's）檢查穩健性，最後下結論。

#### 【材料原文】Testing-based procedures（逐步檢定程序）

**Backward elimination**

1. 先以所有的資料建構一個完整模型（complete model）。
2. 觀察哪些解釋變數的 $\text{p-value}>\alpha_{\text{remove}}$ ，逐步將其淘汰。
3. 若所有變數之 $\text{p-value}<\alpha_{\text{remove}}$ 則停止。
4. 重新估計後，重複步驟 2，直到無變數可移除為止，得到最終變數子集。

此處的 $\alpha$ 又被稱為 p-to-remove。

- $\alpha$ 不一定要是 0.05。
- 若以預測表現為主，常用 0.15 ~ 0.20 會更穩健。

一些值得留意的事項：

- 保留層級：有高次項或交互，需連同低次項一起留。
- 小心多重共線性會讓個別 $t$ 不顯著但整體仍有用，必要時需先進行標準化。
- 這是檢定式篩選，容易有多重檢定與選後 $\text{p-value}$ 偏樂觀的問題。
- 若遇到來回震盪，則可以考慮適度降低 $\alpha_{\text{remove}}$。

**Forward selection**

1. 由空模型（僅有截距項）開始建構。
2. 針對所有尚未進入模型的解釋變數，個別計算其加入後的 $\text{p-value}$。
3. 選擇 $\text{p-value}$ 最小且 $\text{p-value} \le \alpha_{\text{enter}}$ 的變數加入，形成下一階模型。
4. 若所有變數之 $\text{p-value}>\alpha_{\text{enter}}$ 則停止。
5. 重新估計後，重複步驟 2 ~ 3，直到無變數可進入為止，得到最終變數子集。

**Stepwise regression**

- 概念：
  - 同時結合 **backward elimination** 與 **forward selection**。
  - 每次**加入**一個符合門檻的變數後，**立即檢查**目前模型裡是否有變數應該**移除。**
  - 反覆將加入變數與移除變數交替進行，直到獲得穩定模型。
- 執行流程：
  1. 由空模型（僅有截距項）或指定初始模型開始。
  2. 依據 forward selection 的原則，在待選變數中，加入 $\text{p-value}$ 最小且 $\text{p-value}\le \alpha_{\text{enter}}$ 的一個變數。
  3. 依據 backward selection 的原則，檢查現有變數，若該變數之 $\text{p-value}>\alpha_{\text{remove}}$ 則移除，逐一進行檢驗。
  4. 重複步驟 2~3，直到無變數可進入或移除，得到最終變數子集。
- 白話理解：
  - 變數 $A$ 之所以顯著，可能是跟 變數 $B, D$ 一起才顯著，若少了其中一個都不行的變數組合，但一開始我們並不會知道這樣的情形，所以必須逐一加入、移除進行檢驗，才能測試出最理想的模型。

#### ★【材料原文】逐步檢定程序的一些缺陷

**核心問題：路徑依賴**

- 變數一次只「加或減」一個，容易錯過真正的最佳組合，也容易把**局部最佳**誤當全域最佳。
- 變數間高度相關時，誰先進或先出會影響結果，同樣資料做不同起點或不同抽樣，可能得到不一樣的最終模型。

**$\text{p-value}$ 不是唯一標準**

- 先選變數後再看 $\text{p-value}$ 值，會有「選後 $\text{p-value}$ 偏樂觀」的問題，容易形成過度解讀。
- 刪掉不顯著的變數，通常會讓留下的變數看起來更顯著，因「標準誤變小」、「共線性下降」，容易高估其重要性。

**與最終目標集合無直接關聯**

- 逐步檢定流程沒有直接對準「預測目標」或「被解釋目標」，而只是依 $\text{p-value}$ 做變數的局部調整。
- 被刪掉的變數未必與 $Y$ 無關，可能只是關聯性較弱而已。
- 常見情況是「在目前已納入的變數之上，沒有額外解釋力」，因此很難斷言哪一個變數是真正的「完全無關」。

**對預測的影響（常見陷阱）**

- Stepwise regression 傾向選出太小的模型，對預測未必理想。
- 單一解釋變數斜率剛好不顯著，仍可能對預測有幫助。
- 只用 $\text{p-value} <0.05$ 當門檻，這種一刀切的標準會過度嚴格，忽略許多變數的可解釋性。

#### ★★【材料原文】「變數被移除」的正確說法（推論界線之一）

> - **注意！在任一方法中，某變數被「移除或不在模型中」，只能解讀為「在目前已納入的變數之上，該變數沒有『額外』解釋力」。**
> - 若把 room 換成 bathroom（或加入 bathroom），模型配適度會更好，但這不代表像 Parking 這類變數就「不重要」。
> - **結論上而言，可以說「解釋變數在過程中被拿掉，是因為其他變數都在，而不是他本身沒有影響力。」**
> - **正確說法是：在已包含的變數條件下，Parking 沒有額外貢獻或提供的額外解釋力不足。**

材料的 Parking 案例（原文）：

- Parking 這筆資料要不要刪其實取決於個人，因其 $\text{p-value}=0.08$ 已經具有意義，且拿掉後，$R^2$ 由 0.6602 下降至 0.6530，是有影響的。
- Parking 資料在拿掉 land 前是具有顯著影響力的；拿掉 land 後影響力顯著下降。
- 因此要不要拿掉 Parking 是具有討論空間的，沒有唯一標準。
- 被拿掉的解釋變數分別是：size、bathroom、age、agesq。
- 此四個解釋變數單獨建立模型，也具有一定的解釋力，此處可得知，這些變數之間並非彼此完全獨立，是具有一定關聯性的。

材料的模型比較表（原文）：

$$\begin{array}{lrrr}
\text{Model} & \text{HOMES4} & \text{Backward (with Parking)} & \text{Backward (without Parking)} \\
\hline
\text{degrees of freedom} & 140 & 144 & 145 \\
\text{Residual standard error} & 4435 & 4422 & 4452 \\
\text{Multiple R-squared} & 0.6675 & 0.6602 & 0.6530 \\
\text{Adjusted R-squared} & 0.6462 & 0.6484 & 0.6435 \\
\text{F-statistic} & 31.23 & 55.94 & 68.23 \\
\text{p-value} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16}
\end{array}$$

$$\begin{array}{lrr}
\text{Model} & \text{room} & \text{bathroom} \\
\hline
\text{degrees of freedom} & 145 & 145 \\
\text{Residual standard error} & 4452 & 4457 \\
\text{Multiple R-squared} & 0.6530 & 0.6365 \\
\text{Adjusted R-squared} & 0.6435 & 0.6265 \\
\text{F-statistic} & 68.23 & 63.47 \\
\text{p-value} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16}
\end{array}$$

**這回答什麼行銷/商業問題**：媒體歸因模型跑完，某個渠道係數不顯著被 `step()` 砍掉——**不能寫成「這個渠道沒效果」**，只能寫成「在已納入的其他渠道之上，這個渠道沒有額外解釋力」。這是行銷報告裡最常被誤寫的一句話。

#### 【材料原文】Coding 的注意事項

- `lm4.2a <- lm(price ~ ., data=HOMES4)`
  - 其中 `price ~ .` 的 `.` 代表除了 price 以外的所有變數，皆列入 $X$ 做使用。
- `update(lm4.2a, . ~ . - hall)`
  - 用法：`lm4.2a <- update(lm4.2a, . ~ . - hall)`
  - update 代表更新指定變數所指定內容
    - 在 update 裡面所指定的是原先的 lm4.2a。
    - `. ~ .` 代表指定模型中的所有變數。
    - `-hall` 代表將 hall 這類變數直接刪掉。

#### 【材料原文】Criterion-based procedures（準則式程序）

- $R^2 =\frac{SSR}{SST}= 1 - \frac{SSE}{SST} = \frac{\text{解釋變異}}{\text{總變異}}$
- $\text{Adujusted }R^2=\bar{R}^2=1−\frac{\frac{SST}{(n−1)}}{\frac{SSE}{(n−k−1)}}=1−\frac{(n-1)}{(n−k−1)}(1−R^2)$，其中 n：樣本數、k：解釋變數個數

**Akaike Information Criterion (AIC)**

- Akaike 是一位日本學者。
- $\text{AIC}=−2\text{max log-likelihood}+2(k+1)$
  - $2(k+1)$ 為參數個數的懲罰項。
- 可理解為：
  - 模型放越多變數，對數概似會提高，即擬合程度會提高，但也會被懲罰
  - AIC 是在「擬合 與 模型大小」間尋找平衡。
- 如何判讀？
  - 只看差值，即 $\Delta\text{AIC}$，絕對值沒有意義。
  - 經驗法則：
    - $\Delta\text{AIC} \le2$，兩個模型幾乎一樣好，難分軒輊 $\longrightarrow$ 通常選較簡單的那個。
    - $4 \le \Delta\text{AIC} \le 7$，較小 AIC 的模型具有弱優勢 $\longrightarrow$ 暫時偏向它。但若差異不大，仍可選模型較簡單者。
    - $\Delta\text{AIC} \ge 10$，差距很明顯 $\longrightarrow$ 幾乎可以肯定選 AIC 較小的模型。
- 投影片範例的觀察（原文）：
  - 這一欄的意義是，如果拿掉 hall 這個變數，AIC 會降至 2526.9。
  - Step 會將所有單一變數拿掉對 AIC 造成的影響，一一檢驗並列表。
  - AIC 要選最低的，代表與原始 AIC 相比下 $\Delta\text{AIC}$ 最大，該變數則可拿掉。
  - 到這裡為止，會發現什麼都不做，AIC 才是最小的，拿掉任何一個變數都會使 AIC 上升，因此 step 進行至此就會停下了。
  - **注意！相較於 Testing-based procedures，以 AIC 做為標準，Parking 這個變數會被留下。**
- Coding：`step()` 包含了 AIC 計算。

【評註】AIC 定義裡的 $-2\,\text{max log-likelihood}$ 就是 Deviance 的骨架——`AIC = Deviance + 2(k+1) + const`。所以 `step()` 在 `glm()` 上照樣可用，只是它比的是 Deviance 而不是 SSE。

#### 【材料原文】變數選擇的結論

**變數選擇的目的**

- 建立一個能解釋清楚或穩定預測的模型。
- **變數選擇程序只是參考用，不保證與最終目標（解釋或預測）完全一致。**
- **僅供參考，不當作結論本身。**

**不同程序的差異**

- Testing-based procedures：在受限的模型空間裡做一次一個的加入或移除，依 $\text{p-value}$ 做局部決策。
- Criterion-based procedures：通常做較廣的搜尋，用 AIC 或調整後 $R^2$ 等可比較的準則來選擇模型。
- 思路：可以 Testing-based procedures 作為初步篩選，再以 Criterion-based procedures 進行驗證收尾。

**若遇到多個模型都差不多，則可依以下方式判斷：**

- 定性結論是否一致？變動方向、關鍵變因、是否存在交互作用。
- 預測是否相近？比較 CV、比較 RMSE。
- 量測成本差多少？選資料較便宜者、選資料較易取得者。
- 誰的模型診斷較好？殘差比較、常態性檢定、是否為同質變異數、槓桿點、Cook's distance。

**★ 看起來一樣好的模型，結論可能差很多**

- 代表有可能資料本身不足以給出單一答案，需額外補充資料，或進一步約束情境。
- 可以考慮同時呈現多模型的敏感度分析。
- **需警覺「可能存在與暫定結論相矛盾、但配適也不差的替代模型。」**

#### 【材料原文】交互作用（Interaction）

**有交互作用的迴歸式**

- 到目前為止，課堂中教到的迴歸式中，各個解釋變數間對被解釋變數的影響都是分開的，各項變因對 $Y$ 的影響具有相加性。
- 實際上，不同變數之間對被解釋變數的影響會存在著「連動關係」，例如：$X_2$ 對 $Y$ 的影響上升時，$X_1$ 對 $Y$ 的影響可能上升或下降（未必等比例）。
- 若只考慮相加性，相當於是忽略了交互作用帶來的影響，在估計時容易失真。
- 因此交互作用便是將「兩項解釋變數相乘」形成一項新變數，並賦予該「交乘項」係數，用以表示兩變數間的關聯性。
- 交乘項也可以是三項或是四項以上的交乘，但除非有非常明確的理論依據，否則三項以上的交乘項就已經不太必要。

**城市 × 成本的完整交互模型（Full interaction model）**

指標變數設定：

$$\begin{array}{|l|c|c|}\hline\text{City} & \text{D1} & \text{D2} \\\hline\text{CT} & 0 & 0 \\\text{KH} & 1 & 0 \\\text{TP} & 0 & 1 \\\hline\end{array}$$

$$\text{E(revenue)}=
\beta_0
+\beta_1\times\text{cost}
+\beta_2\times D_1
+\beta_3 \times D_2
+\beta_4\times \text{cost}\times D_1 +\beta_5 \times \text{cost} \times D_2$$

- $(D_2,D_1)=(0,0)$ 是基準項（台中）。
- $(D_2,D_1)=(0,1)$ 是高雄。
- $(D_2,D_1)=(1,0)$ 是台北。
- 簡單來說當以類別為變數時， $D$ 這項僅具有「分類」功能，並不是代表很多「不同的變數」。

各城市模型簡述：

- 台中市（$D_1=0,D_2=0$）：$\mu = \beta_0 + \beta_1 \times \text{cost}$
- 高雄市（$D_1=1,D_2=0$）：$\mu = (\beta_0 +\beta_2) +(\beta_1+\beta_4) \times \text{cost}$
  - $\beta_2$ 指的是台中市與高雄市的「截距差」。
  - $\beta_4$ 指的是台中市與高雄市的「斜率差」。
- 台北市（$D_1=0,D_2=1$）：$\mu = (\beta_0 +\beta_3) +(\beta_1+\beta_5) \times \text{cost}$
  - $\beta_3$ 指的是台中市與台北市的「截距差」。
  - $\beta_5$ 指的是台中市與台北市的「斜率差」。

```r
RC <- read.table("revcost.txt", header=T)
attach(RC)

fitRC <- lm(revenue ~ cost*(D1+D2), data=RC)

summary(fitRC)
```

- `cost*(D1+D2)` 表示 cost 是一項變數、$D_1,D_2$ 是一項變數，會判定為 $\text{cost}\times D_1$ 與 $\text{cost}\times D_2$ 兩項，在報表中則以 `cost:D1` 及 `cost:D2` 來表示這兩個交乘項。

報表解讀（材料原文）：

- $D_1$ 係數 $-0.6207$ 指的是「高雄相對於台中的截距少 $0.6207$」。$\text{p-value}=0.54 \longrightarrow$ 不顯著。
- $D_2$ 係數 $-2.0557$ 指的是「台北相對於台中的截距少 $2.0557$」。$\text{p-value}=0.0699 \longrightarrow$ 顯著。
- `cost:D1` 係數 $-0.1663$ 指的是「高雄相對於台中的斜率少 $0.1663$」。$\text{p-value}=0.8295 \longrightarrow$ 不顯著。
- `cost:D2` 係數 $2.0377$ 指的是「台北相對於台中的斜率多 $2.0377$」。$\text{p-value}=0.0282 \longrightarrow$ 顯著。

**Advanced technique in R**

```r
lm.RC <- lm(revenue ~ cost * city)
summary(lm.RC)		# Note the reference level of 'city'
```

透過 relevel 將台北市設為新的 baseline：

```r
city <- relevel(as.factor(city), ref="TP")
lm.RC <- lm(revenue ~ cost * city)
summary(lm.RC)
```

- `cityCT` 係數 $2.0557$ 指的是「台中相對於台北的截距多 $2.0557$」。$\text{p-value}=0.0699$
- `cityKH` 係數 $1.4350$ 指的是「高雄相對於台北的截距多 $1.4350$」。$\text{p-value}=0.1573$
- `cost:cityCT` 係數 $-2.0377$ 指的是「台中相對於台北的斜率少 $2.0377$」。$\text{p-value}=0.0190$
- `cost:cityKH` 係數 $-2.2039$ 指的是「高雄相對於台北的斜率少 $2.2039$」。$\text{p-value}=0.0282$

**★ Preserving hierarchy（階層性原則）**

- 若 $X_1$ 的係數 $\beta_1$ 及 $X_2$ 的係數 $\beta_2$ 皆不顯著，但 $X_1 \times X_2$ 的係數 $\beta_3$ 顯著，則在完整模型中傾向同時保留 $X_1$ 與 $X_2$ 兩項變因，如同在 MLR 中提到的階層性一樣。
- 這個原則挺小眾的，參考就好。
- 可以理解成解釋變數 $X_1$ 對 $Y$ 的解釋力除了 $X_1$ 自己本身，還有其交互項。
- 極端情況下，如 $X_1$ 的 $\text{p-value}\approx1$，且 $X_1$ 交互項的 $\text{p-value}\approx0$，則可以考慮直接拿掉 $X_1$，僅留下交互項。

```r
lm5.3i <- lm(fuel ~ recipweight + door + recipdisplacement * type, data=CARS5)
summary(lm5.3i)

	anova(lm5.3, lm5.3i)
```

**★ 重點提醒！**

- 指標變數的係數所代表的是「不同解釋變數間的截距差」。
- 交互項的係數所代表的是「不同解釋變數間的斜率差」。

不同變數下的交互效果：

- **類別變數 vs. 類別變數的交互效果**（ANOVA 主要在檢定的）
  - $X_1$ 因子的效果會因 $X_2$ 因子的效果而改變，不同類別的組合可能會產生不一樣的效果。
  - 若無交互效果，則兩變因 $X_1,X_2$ 具相加性。
  - 例如：$X_1=\text{教材(實體、數位)}$、$X_2=年級(高、低)$；$X_1\times X_2$ 數位教材在高年級比低年級更有效。
- **類別變數 vs. 連續變數的交互效果**（ANCOVA 主要在檢定的）
  - 不同組別對連續變數 $X$ 的影響強度（斜率）可能不同。
    - 若斜率同質，則交互效果僅影響「截距項」。
    - 若斜率異質，則交互效果還會影響「斜率」。
  - 例如：飲食方式 × 每週運動時數 → 減重公斤數
    - 類別因子 $D$：飲食法（0＝正常，1＝低醣）。連續共變數 $X$：每週運動時數。反應 $Y$：8 週後減重公斤數。
    - 若沒有交互作用（斜率同質），兩種飲食的「運動 $\longrightarrow$ 減重」關係是平行線，差別只在截距（整體平均差）。
    - 若有交互作用，**代表運動每多 1 小時帶來的平均減重在兩種飲食下不同**。例如低醣組的線更陡，表示運動越多，低醣的優勢越明顯。
- **連續變數 vs. 連續變數的交互效果**
  - $X_1$ 因子的效果會受 $X_2$ 因子的效果而改變。
  - 例如：運動時間對健康分數的提升幅度，會隨睡眠時數而增減。

- 交乘項一樣可以做變數轉換。
- 交乘項若顯著，要考慮階層性並保留。
- 交乘項若不顯著，則可以拿掉，整體模型會更簡單。

**這回答什麼行銷/商業問題**：「同一筆廣告預算，在不同城市 / 不同客群 / 不同裝置上的邊際效益是不是一樣？」——不顯著的交互項代表「效果一致、可以合併講」；顯著的交互項代表「必須分眾報告，講一個平均數會誤導」。

#### 【材料原文】影響點（Influential points）— 三個診斷指標

**個別資料點「影響力」的兩個面向：**

- Outliers（離群值）
  - Unusual $Y$ values relative to $\hat Y$.
  - 相對於模型預測值 $\hat Y$，$Y$ 值異常（殘差很大）。
  - 事實上，離群值影響的是 $Y$ 方向上的數值！
- High leverage points（高槓桿點）
  - Unusual $X$ values relative to general dataset pattern.
  - 高槓桿點所影響的則是 $X$ 方向上的數值！
  - 某筆資料的 $X$ 值跑到其他點很少散佈的角落，或說 $X$ 的組合很罕見。
- 庫克距離（Cook's distance）：
  - 把「殘差大小」與「槓桿高低」綜合起來衡量影響力。
  - 殘差大 $\ne$ 影響一定大；槓桿高 $\ne$ 影響一定大。
  - 殘差大 $+$ 槓桿高 $=$ 最危險，但仍需視庫克距離而定。

**Outliers 判準**

- 一般來說，我們定義 $\text{| studentized residual |} >3$ ，即是離群值。兩尾機率約 $< 0.002$。
- R 指令：`rstandard()`；移除：`HOMES4a <- HOMES4[-c(54,117),]`

**如何處理 Outliers？先檢查原因（材料原文）**

- 資料輸入錯誤（最常見） $\longrightarrow$ 更正後重跑分析。
- 重要變數遺漏（解釋變數不足） $\longrightarrow$ 找回可能有用的變數納入後重估。
- 回歸假設失真（異質變異、非常態、交互項未檢驗）$\longrightarrow$ 透過變數轉換、加入交互或非線性項，再重新評估模型。
- 族群本質差異，即潛在次族群，與多數樣本機制不同 $\longrightarrow$ 先把疑似離群樣本獨立處理，其餘資料單獨重估，進行分開分析。

評估離群點的影響力（敏感度分析）：

- 先找出最大 $|\text{studentized residual}|$ 的觀測值。
- 先排除該點，以剩餘資料重估模型，觀察係數、標準誤、$R^2$ 是否有實質改變。
- 顯著影響 $\longrightarrow$ 該點具實質影響，需回到上面四類原因處理。
- 未顯著影響 $\longrightarrow$ 紀錄即可，通常保留。

**High Leverage Points 經驗法則（rule of thumb）**

令 n = 樣本數，k = 解釋變數個數，h 表槓桿(leverage)，則：

- $h>\frac{3(k+1)}{n}\;\longrightarrow\;$ 需進一步檢查。
- $h<\frac{2(k+1)}{n}\;\longrightarrow\;$ 該點很孤立，也需進一步檢查。（原文如此）
- 介於兩者之間 $\longrightarrow$ 暫無過度影響的明確證據。
- R 指令：`hatvalues()`；篩選：`levlm4.1[levlm4.1 > thr3]`

**Cook's distance 經驗法則**

- $\text{Cook's distance} \ge 1$
- $0.5 \le \text{Cook's distance} <1$
- 否則，通常沒有過度影響的明確證據。
- **僅作為模型警訊使用！**
- R 指令：`cooks.distance()`

【評註】回顧區後半（個別 t 檢定、Partial F、Global F、$R^2$、Adjusted $R^2$、殘差圖 / Histogram / Q-Q plot 的假設檢查、CI / PI）都是前一章 MLR 內容的完整重貼，與本 digest 的 logistic / GLM 主軸關係較遠，此處不逐字重錄；核心公式已在上方「三種檢定的定位」保留。

---

### 2.1 前言：為什麼卡方不夠，要進 GLM

#### ★【材料原文】前言（要看！）

- 卡方獨立性或同質性檢定主要提供的是整體性的判斷，主要是告訴我們「變數之間是否存在關聯」，卻無法在同一個架構下，同時量化效果大小、控制其他共變數並進行預測，因此我們會需要進一步透過廣義線性模型（例如 logistic regression 或 log-linear model），把這些關聯結構化、參數化地呈現出來。
- GLM 可以視為在多元線性迴歸架構上的推廣：
  - 保留「線性預測」的結構，並允許反應變數服從非常態的分配，同時透過適當的 link function（例如：二元資料中的 logit，也就是 log-odds）把 $\mathrm{E}(\mathrm{Y})$ 與線性關係連結起來。
    - Logistic regression 則是 GLM 在二元反應下的一個重要特例。
- **注意！Linear regression 的假設是針對誤差項，在實務診斷裡則是透過 residuals 來檢查，而不是直接假設原始的 $\mathrm{Y}$ 本身要常態、等變異。**

**這回答什麼行銷/商業問題**：卡方只能說「渠道與轉換有關聯」；要說「控制客單價、年齡、既有會員狀態後，這個渠道還讓購買勝算多 X 倍」，就必須用 logistic regression。這是從「描述性報告」升級到「歸因報告」的分水嶺。

### 2.2 廣義線性模型（GLM）

#### 【材料原文】Introduction — 什麼時候該用 GLM

以前學的是「反應變數為連續型」時的線性迴歸模型，那如果反應變數是以下種類則可以考慮使用 GLM：

- 二元（binary）
- 計數（counts）
- 有序類別（ordinal）
- 多類別（multinomial）

當反應變數屬於下列型態時，可以考慮使用 GLM：

- 二元反應（Binary response variables），例如：Yes / No。
- 以比例呈現的計數資料，例如：logistic regression 中的成功 / 失敗比例。
- 不以比例呈現的一般計數資料，例如：log-linear 模型。
- 存活時間（time to death）等資料，其變異數會以快於「線性」的速度隨平均數增加（如 survival analysis 存活分析）。

#### ★【材料原文】不同資料類型中平均值（mean）與變異數（variance）之間的關係

- 在一般線性模型中，我們的核心假設之一是：**變異數為常數**。[圖片]
- 在「計數資料」中，反應變數通常是整數，而且資料中常出現很多 0。
  - 在這種情況下，**變異數會隨平均數大致線性上升**。[圖片]
- 對於「比例資料」，我們同時觀察某事件成功（或失敗）的次數與總試驗次數。
  - 在此情況下，**變異數會隨平均數呈現倒 U 型關係**。[圖片]
- 當反應變數服從 gamma 分配（例如存活資料）時：
  - **變異數會以快於線性的速度隨平均數增加**。[圖片]

**【評註】這一段就是「連結函數 / 家族怎麼選」的判準來源**——不是看 Y 長什麼樣，而是看 **Var 與 Mean 的關係長什麼樣**：常數 → Normal；線性上升 → Poisson；倒 U → Binomial；超線性 → Gamma。

#### ★【材料原文】為什麼不能直接用一般線性模型？

- 如果直接套用普通迴歸，得到的是所謂的「線性機率模型」（linear probability model）：$\pi(x) = \alpha + \beta x$
  - 其中 $\pi(x)$ 是成功機率。
  - 這代表成功機率會隨 $x$ 呈線性變化，而 $\beta$ 則是「$x$ 每增加一單位，機率改變多少」的係數。
- 這個模型有一個結構上的大問題：
  - 機率必須介於 0 與 1 之間；
  - 但線性函數可以取任何實數值。
  - 因此，對於極端的 $x$ 值，預測的 $\pi(x)$ 可能 < 0 或 > 1。
- 因此，我們需要對模型做修改，這就引出 Generalized Linear Models（GLM）的想法。

#### ★★【材料原文】GLM 的三大構成要素

$$g(\mathrm{E}(\mathrm{Y})) = \beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k$$

**隨機成份（Random component）：**

- 指定反應變數 $\mathrm{Y}$，並選擇一個適合 $\mathrm{Y}$ 的機率分配。
- **常見應用**：
  - 一般迴歸：$Y$ 是連續的 $\longrightarrow$ 常態分配（Normal distribution）。
  - 二元分類：每一筆觀測是「成功 / 失敗」$\longrightarrow$ 二項式分配（Binomial distribution）。
  - 計數資料：非負整數（例如：來客數）$\longrightarrow$ 選卜松分配（Poisson distribution）。
- 白話：
  - 這是在決定「資料的長相」。
  - 以前我們只處理長得像鐘形曲線的資料，現在 GLM 允許我們處理長得像「硬幣（0 / 1）」或「計數器（0, 1, 2...）」的資料。

**系統成份（Systematic component）**

- 指定解釋變數：$\beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k$
- 這個自變數線性組合稱為線性預測子（linear predictor）。通常記為 $\eta$ 。

**連結函數（Link function）**

- 指定平均數 $\mu = \mathrm{E}(\mathrm{Y})$ 與線性預測子之間如何透過連結函數 $g(\cdot)$ 相連。
- 模型形式為 $g(\mu) = \beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k$。

#### ★【材料原文】Properties

**GLM 對「一般線性迴歸模型」做了兩個方向的推廣：**

- 解放 $\mathrm{Y}$：
  - 允許隨機成份採用非常態分配。
  - 不再被常態假設綁死。
- 解放平均數：
  - 允許把「平均數」做某種函數轉換後再建模。
  - 也就是使用 link function（連結函數）。
- $\Longrightarrow$ 這兩點讓 GLM 能夠完美處理類別資料。

**GLM 的配適過程（fitting process）：**

- 使用的是最大概似法（Maximum Likelihood, ML）。
- 而不是最小平方法（Least Squares, LS）。
- 原因：
  - LS 是用「距離」算誤差，適合常態分配。
  - ML 是用「機率」算可能性，適合二項式這種離散分配。

> **在 GLM 中，「選擇何種連結函數」與「選擇何種隨機成分」是兩件相互獨立的事情。**

【評註】最後這句是**連結函數選擇規則的關鍵前提**：family 決定 Var–Mean 關係，link 決定尺度轉換，兩者可以自由組合（R 的 `family=binomial(link="probit")`、`family=poisson(link="identity")` 都合法）。實務上大多用各 family 的 canonical link（binomial → logit、poisson → log、gaussian → identity），因為它讓 MLE 數值最穩、係數解讀最自然（logit → log odds ratio、log → 倍數效果）。

#### 【材料原文】Normal GLM：MLR（GLM 如何退回線性迴歸）

以常態分配為例的 GLM：多元線性迴歸

- 隨機成份（Random component）：選擇常態分配作為 $\mathrm{Y}$ 的機率分配。
- 系統成份（Systematic component）：指定解釋變數。
- 連結函數（Link function）：
  - 若 $g(\mathrm{E}(\mathrm{Y})) = \mathrm{E}(\mathrm{Y})$，則 $\mathrm{E}(\mathrm{Y}) = \beta_0 + \beta_1 x_1 + \cdots + \beta_k x_k$。
  - 即 $g(\mu) = \mu$，稱為恆等連結函數（identity link）。
    - Identity Link 的意思就是「什麼都不做」（Input = Output）。
    - 因為 $\mathrm{Y}$ 是常態，範圍為 $(-\infty,\infty)$，跟另一邊的 $\mathrm{X}$ 線性組合，範圍也是 $(-\infty,\infty)$ 剛好能夠對上，可以直接連起來就好！

**【評註】連結函數的選擇邏輯（依材料推導，非新增資訊）**：link function 的工作就是把 $\mu$ 的**值域**拉到 $(-\infty,\infty)$，好跟線性預測子對齊。

| Y 的型態 | $\mu$ 的值域 | 需要的 link | family |
|---|---|---|---|
| 連續 | $(-\infty,\infty)$ | identity（什麼都不做） | gaussian |
| 二元 / 比例 | $(0,1)$ | logit $\log\frac{\pi}{1-\pi}$ | binomial |
| 計數 | $(0,\infty)$ | log $\log\mu$ | poisson |
| 正值連續（存活） | $(0,\infty)$ | log / inverse | gamma |

### 2.3 二元資料的 GLM：邏輯斯迴歸（Logistic Regression）

> 又稱羅吉斯迴歸、邏輯回歸、對數機率迴歸

#### ★【材料原文】用於二元資料的 GLM

- 許多類別反應變數只有兩個類別。
- 對於二元反應，分配可寫成：
  - 成功機率：$\Pr(\mathrm{Y} = 1) = \pi$。
  - 失敗機率：$\Pr(\mathrm{Y} = 0) = 1 - \pi$。
  - 平均數：$\mathrm{E}(\mathrm{Y}) = \pi$。
  - 變異數：$\mathrm{Var}(\mathrm{Y}) = \pi(1 - \pi)$。
    - **變異數的大小取決於平均數 $\pi$。**
      - 當 $\pi = 0.5$ 時，變異數最大（$0.5 \times 0.5 = 0.25$），代表最不確定。
      - 當 $\pi$ 接近 $0$ 或 $1$ 時，變異數變小，代表結果很確定。
      - 這代表二元資料的變異數是**不固定（Non-constant）的，且**呈現倒 U 型分佈。
      - **這直接違反了傳統線性迴歸的「同質變異數」假設，所以我們絕對不能直接拿 $\mathrm{Y}$ 去跑一般線性迴歸（OLS），必須改用 GLM。**
- 若對同一個二元反應做 $n$ 次獨立觀測，且每次成功機率皆為 $\pi$，則成功的次數服從以 $n$ 和 $\pi$ 為參數的二項分配（binomial）。
- 在迴歸情境下，$\pi$ 會隨自變數 $x$ 改變，因此記為 $\pi(x)$。

#### 【材料原文】$\pi(x)$ 與 $x$ 的關係通常是非線性但單調的

- 當 $\pi(x)$ 接近 0 或 1 時，同樣的 $x$ 變化量，對機率的影響往往比較小。
- 當 $\pi(x)$ 在中間區域時，影響則較大。
- 不過，這種非線性關係通常仍是單調遞增（monotonic increasing）或遞減（monotonic decreasing）。

單調（monotonic）的概念：

- 數學上的意義：方向固定。
  - 單調遞增（Monotonic Increasing）：隨著 $x$ 增加，機率 $\pi(x)$ 一直上升（或持平），絕對不會下降。
  - 單調遞減（Monotonic Decreasing）：隨著 $x$ 增加，機率 $\pi(x)$ 一直下降（或持平），絕對不會上升。
- 實務上的意義：因果關係的一致性。
  - 在商業或醫學研究中，許多現象都符合「單調性」假設，這也是為什麼 Logistic Regression 這麼好用的原因：
  - 案例 1（Donner Party）：年齡越大，體力越差，生存機率就越低。這是一個「單調遞減」的關係。
  - 案例 2（Birdkeeping）：抽菸年數越長，肺部受損越嚴重，罹癌機率就越高。這是一個「單調遞增」的關係。

#### ★【材料原文】邏輯斯迴歸模型

$$\eta = \log \frac{\pi(x)}{1 - \pi(x)} = \alpha + \beta x$$

- 其中 $\eta$ 是 logit，也就是對數 odds。

**S 型曲線的「變速」與「單調」的區別：**

- 單調性（Monotonic）：講的是方向。方向是永遠不變的，永遠往上或永遠往下。
- 非線性（Nonlinear / S-shape）：講的是速度（斜率）。雖然方向不變，但速度會變。
- 在機率很低（接近 0）或很高（接近 1）時，改變 $x$ 對機率的影響很小，曲線平緩。
- 在機率接近 0.5 時，改變 $x$ 對機率的影響最大，曲線最陡峭。

#### 【材料原文】Logistic Function

- 標準 logistic 函數
  - 在 $\alpha = 0, \beta = 1$ 的情況下，標準 logistic 函數為 $\pi(x) = \frac{e^{\eta}}{1 + e^{\eta}}$
  - 而 $\eta = \alpha + \beta$。
- 當 $\alpha = 0, \beta = 1$ 時：
  - $\pi = 0.5$ 時，$\eta = 0$。
  - $\eta$ 每增加 1 單位：
    - 機率 $\pi$ 在不同區段增加量不同（例如：在下圖中間區段約增加 0.244），但 **odds 會乘上 $e^1 = 2.718$**。

#### ★【材料原文】Logistic 迴歸模型是 GLM 的一個特例

- (success, failure) 的隨機成分為二項（Binomial）。
- 連結函數是 $\pi$ 的 logit 轉換 $\log[\frac{\pi}{(1 - \pi)}]$：
  - 使用 logit 連結可以很好地刻畫 $\pi(x)$ 與 $x$ 之間的 S 型關係。
- 若 $\text{logit}(\pi) = \eta$，則 $\pi = \frac{\exp(\eta)}{1 + \exp(\eta)}$
- 因此 logistic 迴歸模型常被稱為 logit model。
- 雖然 $\pi$ 必須介於 $(0, 1)$，但 logit 可以取任何實數，這與線性預測子 $\eta$ 的取值範圍相容。
- 因為線性預測子也是任意實數，所以模型 $\frac{\pi(x)}{1 - \pi(x)} = \alpha + \beta x$ 不會有「線性機率模型」那種機率超出 $(0,1)$ 範圍的結構性問題。（原文如此，此處應為 $\log$ 的筆誤）
- 參數 $\beta$ 控制曲線上升（或下降）的速度：
  - 當 $\beta > 0$ 時，$\pi(x)$ 隨 $x$ 增加而增加。
  - $|\beta|$ 越大，曲線越陡。
  - 當 $\beta = 0$ 時，曲線變成一條水平直線。

#### 【材料原文】Logistic 迴歸的詮釋

- 對二元反應 $\mathrm{Y}$ 與一個連續解釋變數 $\mathrm{X}$ 而言，令 $\pi(x)$ 為在 $\mathrm{X}=x$ 時「成功」的機率，這個機率同時也是二項分配的參數。
- Logistic 迴歸模型寫成：

$$\text{logit}\{\pi(x)\}
= \log \frac{\pi(x)}{1 - \pi(x)}
= \alpha + \beta x$$

  - 這個公式表示：$\pi(x)$ 是 $x$ 的 S 型函數，隨 $x$ 單調上升或下降。
- 另一種常用寫法，直接寫成成功機率：

$$\pi(x) = \frac{e^{(\alpha + \beta x)}}{1 + e^{(\alpha + \beta x)}}$$

#### ★【材料原文】線性近似的解釋（切線斜率與 $EL_{50}$）

- 參數 $\beta$ 決定了 S 型函數 $\pi(x)$ 上升或下降的速度。
- 在某個特定的 $x$ 值附近，可以用一條切線來描述曲線在該點附近的變化率。
- 對 logistic 迴歸而言，該切線的斜率是 $\beta \, \pi(x)\,[1 - \pi(x)]$。
- 曲線最陡的地方是 $\pi(x) = 0.5$ 處，對應的 $x$ 值為 $x = \frac{-\alpha}{\beta}$。
- 這個 $x$ 值有時稱為 mean effective level，記作 $EL_{50}$，代表在此水準時，兩種結果各有 50% 的機會發生。

#### ★★【材料原文】以 odds ratio 解釋（最重要的商業解讀）

改用「勝算（odds）」與「勝算比（odds ratio）」的角度來詮釋 logistic 迴歸：

$$\frac{\pi(x)}{1 - \pi(x)} = \text{odds}
= e^{\alpha + \beta x} = e^{\alpha} \, e^{\beta x}$$

這個指數關係提供了 $\beta$ 的另一個解讀：

- **當 $x$ 每增加 $1$ 單位，odds 會乘上 $e^{\beta}$。**
- 若 $\beta = 0$，則 $e^{\beta} = 1$，odds 不會隨 $x$ 改變。

**這回答什麼行銷/商業問題**：報告裡的標準句型「每多接觸一次廣告，購買勝算乘上 $e^{\hat\beta}$ 倍」。這是 logistic 係數唯一能直接講給非統計背景聽眾的方式——**不要講 log odds，永遠 exp() 後再講**。

### 2.4 模型推論（Model Inference）：Wald vs LRT

#### 【材料原文】參數估計：最大概似法（MLE）

- 核心方法：對多數 GLM 而言，參數都是用最大概似法（ML）估計。
- 統計性質：最大概似估計值（MLE）在樣本數夠大時，近似服從常態分配。
- 信賴區間：
  - 基於常態性，參數 $\beta$ 的 $(1-\alpha)\%$ 信賴區間可寫為：$\hat{\beta} \pm z_{\alpha/2} \cdot \text{ASE}$
  - 其中 $\text{ASE}$ 為 $\hat{\beta}$ 的漸近標準誤（Asymptotic Standard Error）。

#### 【材料原文】假設檢定

我們有兩種方法可以對 GLM 中的參數做顯著性檢定，用來檢驗假設 $\mathrm{H}_0: \beta = 0$。

- 注意：$\mathrm{H}_0: \beta = 0$ 表示成功機率與 $\mathrm{X}$ 無關（兩者獨立）。

**Wald 檢定（Wald's Test）**

- 這是最簡單、最快速的作法（電腦報表 `summary()` 預設跑出來的就是這個）。
- 原理：利用 MLE 在大樣本下的常態性質 。
- 統計量：$\mathrm{Z} = \frac{\hat{\beta}}{\text{ASE}}$
  - 這其實就是我們熟悉的 Z-score。
- 分配：在 $\mathrm{H}_0:\beta=0$ 下，近似服從標準常態分配 $\mathcal{N}(0,1)$。
- 有些軟體會輸出 $\mathrm{Z}^2$，此時它服從自由度為 $1$ 的卡方分配 $\chi^2_1$。

**概似比檢定（Likelihood-Ratio Test, LRT）**

- 這是更可靠、更有力的作法，雖然計算稍微麻煩一點，需要跑兩個模型。
- **套用在 GLM 上時，通常稱為 Drop-in-Deviance Test（偏差下降檢定）。**
- 原理：比較「限制模型（Null）」與「完整模型（Full）」的 Likelihood 差異。
- 定義符號：
  - $l_0$：在虛無假設 $\mathrm{H}_0: \beta=0$ 下，即限制模型下，概似函數的最大值。
    - 換句話說，$\mathrm{l}_0$ 是在 $\beta = 0$ 下，將 $\alpha$ 估到最好的概似值。
  - $l_1$：在不加限制下，$\beta$ 不必 $=0$，即完整模型下，概似函數的最大值。
- 統計量：

$$-2 \log\left(\frac{l_0}{l_1}\right) = -2(\log l_0 - \log l_1) = -2(L_0 - L_1)$$

  - 其中 $L$ 代表 Log-Likelihood。
  - 因為 $l_0 < l_1$ ，限制越多，配適越差，所以 $\log(\frac{l_0}{l_1})$ 是負數，乘上 $-2$ 變正數 。
- 分配：在 $\mathrm{H}_0:\beta=0$ 下，約服從自由度為 $1$ 的卡方分配 $\chi^2_1$。

#### ★【材料原文】白話解釋

**Wald Test 就像站在山頂用猜測的：**

- 想法：你站在山頂（MLE 最佳解），看著腳下的坡度（曲率）。
- 思考路徑：因為坡度很陡，你推測：「如果我離開這個山頂，分數應該會掉很多吧？」。這是一個基於現況的估計值。
- 優點：快，跑一次模型就全都有了。
- 缺點：
  - 如果這座山的形狀長得很奇怪（不對稱、非常態），你用坡度去推測高度差，可能會猜錯。
  - 如果樣本數不夠大，或是 Log-Likelihood 的形狀很不對稱，它的估計會失準。

**LRT 就像「實際走兩趟來比」：**

- 想法：不想用猜的，你想知道這個變數到底重不重要。
- 思考路徑：
  - 先算一次「有這個變數」的分數（Full model）。
  - 再算一次「把這個變數拿掉」的分數（Reduced model）。
  - 直接相減，看分數到底差多少。
- 優點：最老實、最穩的方法。因為是直接算出來的差距，不是推測的，所以結果非常可靠。
- 缺點：要跑兩次模型（Full model vs. Reduced model），比較麻煩。

**★ 結論：**

- 看報表快速掃瞄時 $\longrightarrow$ 看 Wald Test（$\text{Z-value}$）。
- **要做正式決策或變數篩選時 $\longrightarrow$ 請務必使用 LRT（ANOVA）。**

**這回答什麼行銷/商業問題**：`summary(glm)` 的 z / Pr(>|z|) 只能拿來掃視；要對老闆說「這個渠道有沒有額外貢獻」的正式結論，一定要跑 `anova(reduced, full, test="Chisq")`。

### 2.5 Case 1：Survival in Donner Party（連續 + 類別 + 交互作用）

#### 【材料原文】案例背景

- 表格顯示：Donner Party 中，成年生還者與未生還者的年齡與性別資料。
- 一位人類學家利用這組資料，來檢驗一個結論：**女性在惡劣環境下，比男性更能撐得住**。
- 研究問題：在給定「相同年齡」的情況下，女性的生存機率（或說 Odds）是否高於男性？

#### 【材料原文】R-Code 全流程

從 Sleuth2 資料集中提取 case：

```r
library(Sleuth2)

attach(case2001)
case2001
	# summary(case2001)
```

只看年齡（Age），建立第一個 GLM：

```r
## First model, consider Age only:
case2001.lg1 <- glm(Status~Age, binomial)
summary(case2001.lg1)
```

- 探討年齡是否影響生存狀態，會發現年齡係數為負且顯著。

加入性別（Age + Sex），建立第二個 GLM：

```r
## Second model, add Sex:
case2001.lg2 <- glm(Status~Age+Sex, binomial)
summary(case2001.lg2)
```

- 假設年齡對生存的影響在男女之間是相同的（斜率相同）。
- 但男女原本的生存率不同（截距不同）。
- 發現女性（SexFemale）係數顯著為正。

考慮交互作用（Age * Sex），建立第三個 GLM：

```r
## Third model, consider interaction:
case2001.lg3 <- glm(Status~Age*Sex, binomial)
summary(case2001.lg3)
```

- 在問：「年齡對生存的影響力，是否會因性別而不同？」
- 此時會看到交互作用項的 $\text{p-value}$ 約為 $0.0865$。

模型比較（Likelihood Ratio Test）：

```r
anova(case2001.lg2, case2001.lg3, test="Chisq")
```

- `test="Chisq"` 代表採用卡方檢定。
- 目的：比較「模型二 (無交互作用)」和「模型三 (有交互作用)」。
- 這個指令會計算 Deviance 的下降量。
- `Pr(>Chi)` 也就是 $\text{p-value}$。
  - 結果顯示 $\text{p-value}=0.048<0.05$，表示交互作用項是顯著的，模型三比模型二好，應該保留交互作用。

【評註】**注意這裡的教學重點**：同一個交互項，Wald 檢定給 p = 0.0865（不顯著），LRT 給 p = 0.048（顯著），**結論相反**。這正是材料前面說「正式決策請用 LRT」的實證。

模型推論（信賴區間）：

```r
confint.default(case2001.lg3)
confint.default(case2001.lg2)
exp(confint.default(case2001.lg2)[3,])
```

- `confint.default(...)`：計算係數的信賴區間。
- 這裡加上 `.default` 是指基於標準誤 (Wald) 的算法，也就是 $\hat{\beta} \pm 1.96 \times \text{SE}$。
- `exp(...)`：這個是關鍵！
  - Logistic Regression 的係數 $\beta$ 是 Log-Odds。
  - 加上 `exp()` 後，將其轉換為 Odds Ratio。
  - `[3,]` 是指取出第三列，也就是 `SexFemale` 的係數來算。
    - 可以告訴你「女性生存 odds 相對於男性的倍數區間」。

無交互作用模型的視覺化（繪製 S 型曲線）：

```r
## Display, with case2001.lg2
SF <- subset(case2001, Sex=="Female")
SM <- subset(case2001, Sex=="Male")
sq <- seq(14,66,1)
respF <- predict(case2001.lg2, type="response", newdata=data.frame(Age=sq, Sex="Female"))
respM <- predict(case2001.lg2, type="response", newdata=data.frame(Age=sq, Sex="Male"))

plot(sq, respF, type="l", col=2, ylim=c(0,1), ylab="Predicted Probability", 
     xlab="Age (years)", main="Logistic regression without interaction")	# bty="L",
lines(sq, respM, col=4)
text(x=50, y=0.4, "Females", adj=c(0,0))
text(x=40, y=0.2, "Males", adj=c(0,0))

case2001$SP <- ifelse(case2001$Status=="Survived", 1, 0)	# survived or died
points(SF$Age, jitter(SF$SP, factor=0.2), pch=17)
points(SM$Age, jitter(SM$SP, factor=0.2), pch=1)
legend(50,1, legend=c("Female","Male"), pch=c(17,1))
```

- `predict(..., type="response")`：關鍵參數。
  - 若不加這個，R 會給你 Logit 值（比方說 1.5）。
  - 加了這個，R 會透過 $\frac{e^x}{1+e^x}$ 轉回機率（0～1之間）。
- `jitter(..., factor=0.2)`：抖動處理。
  - 因為原始資料 $\mathrm{Y}$ 只有 $0$ 和 $1$，如果直接畫，很多點會重疊在一起看不清楚。
  - `jitter` 會加一點點隨機雜訊，讓點稍微錯開，這樣才看得到那邊「堆」了多少人。

有交互作用模型的視覺化（繪製 S 型曲線）：

```r
respF <- predict(case2001.lg3, type="response", newdata=data.frame(Age=sq, Sex="Female"))
respM <- predict(case2001.lg3, type="response", newdata=data.frame(Age=sq, Sex="Male"))

plot(SF$Age, jitter(SF$SP, factor=0.2), pch=17, 
     ylim=c(0,1), xlim=c(14,66), ylab="Predicted Probability",  
     xlab="Age (years)", main="Logistic regression with interaction")
points(SM$Age, jitter(SM$SP, factor=0.2), pch=1)
legend(50,1, legend=c("Female","Male"), pch=c(17,1))
lines(sq, respF, col=2)
lines(sq, respM, col=4)
text(x=40, y=0.4, "Females", adj=c(0,0))
text(x=60, y=0.2, "Males", adj=c(0,0))
```

#### 【材料原文】結果解讀

**初始模型**

- 此 logistic 迴歸模型為 $\text{logit}\{\hat{\pi}(x)\} = 1.819 - 0.066 \,\text{Age}$ 。
- 預測的存活機率為

$$\hat{\pi} =
\frac{\exp(1.819 - 0.066 \,\text{Age})}
     {1 + \exp(1.819 - 0.066 \,\text{Age})}$$

- 因為 $\hat{\beta} < 0$，所以年紀越大，預測的存活機率越低。
- median effective level：
  - 讓預測機率 $\hat{\pi} = 0.5$ 時的年齡：$\text{Age} = \mathrm{EL}_{50} = -\frac{\hat{\alpha}}{\hat{\beta}} =\frac{1.819}{0.066} \approx 27.6$
  - 也就是大約 $27.6$ 歲時，存活與死亡的機率各半。

**第二模型**

- 此 logistic 迴歸模型為：

$$\text{logit}\{\hat{\pi}(x)\}
= 1.633 - 0.078\,\text{Age} + 1.597\,\text{Sex}$$

$$\text{SexFemale} =\begin{cases}0, & \text{男性} \\1, & \text{女性}\end{cases}$$

- 雙尾 $\text{p-value}=2 \times \Pr(Z > 2.114) = 0.0345$。
- 解讀：
  - 比較同年齡的女性與男性：
    - 估計的 odds ratio 為 $\exp(1.60) \approx 4.95$。
    - 換句話說，在同年齡下，女性的存活勝算約為男性的 $5$ 倍。
  - 再比較 $20$ 歲女性與 $50$ 歲女性：
    - 年齡差 $30$ 歲，odds ratio：$\exp[-0.078 \times 30] \approx 0.10$。
    - 也就是說，$20$ 歲女性的存活勝算約為 $50$ 歲女性的 $10$ 倍。

【評註】**「差 k 單位 → odds ratio = $e^{k\hat\beta}$」這個算法是行銷分析最常用的手法**：例如「接觸 5 次 vs 接觸 1 次」的勝算比 = $e^{4\hat\beta}$。

**第三模型**

- 此 logistic 迴歸模型為：

$$\text{logit}\{\hat{\pi}(x)\}
= 0.318 - 0.032\,\text{Age} + 6.928\,\text{Sex}−0.162(\text{Age}\times \text{Sex})$$

- 交互作用項 Age:SexFemale 的雙尾 $\text{p-value}:2 \times \Pr(Z > 1.714) = 0.0865$。

**以 SexFemale 的 95% 信賴區間為例：**

$$1.597 \pm 1.96 \times 0.755 = [0.117,  3.077]$$

**勝算比的解讀：**

- 女性相對於同齡男性的存活勝算比估計為 $\exp(1.597) \approx 4.94$。
- 其 $95\%$ 信賴區間為 $\exp(0.117) \text{ 到 }\exp(3.077) \approx [1.12,21.69]$。

**這回答什麼行銷/商業問題**：「控制年齡（或客單價、既有黏著度）後，某一分群的轉換勝算是不是真的比較高？」——這是分群成效比較的完整範本：先只放連續變數 → 加類別變數（分群）→ 加交互作用 → LRT 決定要不要留。

### 2.6 Case 2：Birdkeeping & Lung Cancer（Drop-in-Deviance 的標準範例）

#### 【材料原文】案例概要

**背景**

- 1972～1981 年，在荷蘭海牙進行的健康調查，發現養寵物鳥與肺癌風險增加之間存在關聯。

**變數欄位**

- LC：是否肺癌（LungCancer / NoCancer）
- FM：性別
- AG：年齡
- SS：社經地位
- YR：抽菸年數
- CD：每天抽菸支數
- BK：是否飼養寵物鳥

**研究問題**

- **在控制年齡、社經地位與抽菸行為之後，飼養寵物鳥是否仍與肺癌風險增加有關？**

#### 【材料原文】R-Code

讀檔：

```r
attach(case2002)
# summary(case2002)
```

建立 Full & Reduced model：

```r
## Logistic Regression Models
full <- glm(LC ~ FM + SS + AG + YR + BK, family = "binomial")
reduced <- glm(LC ~ FM + SS + AG + YR, family = "binomial")

summary(full)
summary(reduced)
```

- 完整模型：包含所有變數。
- 簡化模型：包含養鳥（BK）以外的所有變數 。

★ 手動計算 LRT（Likelihood Ratio Test）：

```r
( dvr <- deviance(reduced) )
( dvf <- deviance(full) )
( dfr <- df.residual(reduced) )
( dff <- df.residual(full) )
1 - pchisq(dvr-dvf, dfr-dff)
```

- `deviance(...)`：取出模型的 Deviance（偏差）。
  - 可以把 Deviance 想像成「錯誤值」，模型越準，Deviance 越小。
  - 理論上，`reduced`（變數少）的錯誤一定比 `full`（變數多）來得大。
- `dvr - dvf`：計算 Drop-in-Deviance（偏差下降量）。
  - 這在問：加上「養鳥」這個變數後，模型的錯誤減少了多少？
- `dfr - dff`：計算自由度差 (Difference in degrees of freedom)。
  - 因為只差一個變數（BK），所以這裡是 1。
- `1 - pchisq(...)`：計算 $\text{p-value}$。
  - 透過卡方分配，算出在這個自由度下，Deviance 下降這麼多是「隨機發生」的機率有多少。

透過 ANOVA 自動計算 LRT：

```r
anova(reduced, full, test="Chisq")
```

- `test="Chisq"`：指定使用卡方檢定
  - 因為這是 GLM，傳統 ANOVA 會使用 F-test。
  - 也就是說如果要改成用其他檢定就把等號後面改掉。
- 會看到 Deviance 減少了 $11.29$，$\text{p-value}=0.0007786$ 非常小。
- 結論：
  - 因為 $\text{p-value} < 0.05$，我們拒絕虛無假說。
  - 這證實了養鳥 (BK) 對於解釋肺癌有顯著的額外貢獻。

視覺化（EDA）：

```r
BC <- subset(case2002, (BK=="Bird" & LC=="LungCancer"))
BN <- subset(case2002, (BK=="Bird" & LC=="NoCancer"))
NC <- subset(case2002, (BK=="NoBird" & LC=="LungCancer"))
NN <- subset(case2002, (BK=="NoBird" & LC=="NoCancer"))

plot(YR~AG, type="n", ylab="Years of Smoking", xlab="Age")
points(BC$AG, BC$YR, pch=17)
points(BN$AG, BN$YR, pch=2)
points(NC$AG, NC$YR, pch=19)
points(NN$AG, NN$YR, pch=1)

legend(37,50, legend=c("BC","BN","NC","NN"), pch=c(17,2,19,1))
```

抽菸效果的觀察（材料原文）：

- 垂直方向
  - 在圖上，頂端比底端有更多「深色符號」（表示肺癌個案）。
  - 這顯示：在同一個年齡範圍內，肺癌病患往往抽菸年數較長。
- 水平方向
  - 比較抽菸年數類似的個體，看在這些人當中，三角形（代表 birdkeeper）填滿（黑色，肺癌）的比例是否比空心（白色，非肺癌）高。
  - 注意：圖右下角有兩個「實心三角形」，表示長期抽菸且養鳥的肺癌個案。
- 整體來看：在肺癌病人中，養鳥的比例似乎比對照組高。

#### 【材料原文】結果解讀

- **Birdkeeping 的效果**：
  - 最後一步把 BK 指標變數加入模型。
  - 偏差下降量為 $155.24 − 166.53=−11.29$，自由度 $1$，對應的 $\text{p-value}$ 非常小，顯示 BK 與肺癌之間有強烈關聯，即使已經把其他變數（性別、社經地位、年齡、抽菸年數）納入模型。
- BK 係數的估計值為 $1.3349$：
  - 代表在控制其他變數後，養鳥者的肺癌 odds 約是未養鳥者的 $\exp(1.3349) \approx 3.80$ 倍。

**這回答什麼行銷/商業問題**：**這是「新增一個候選驅動因子是否值得放進歸因模型」的黃金範本**——full vs reduced 兩個模型、Drop-in-Deviance、`anova(..., test="Chisq")`、係數 `exp()` 後講倍數。行銷版本：「在控制年齡、既有消費、其他渠道後，是否曝光過本檔廣告」對購買勝算是否還有額外貢獻。

**【評註】推論界線提醒**：材料標題就寫「發現養寵物鳥與肺癌風險增加之間**存在關聯**」、研究問題寫「是否仍**與**肺癌風險增加**有關**」——全程用「關聯」而非「造成」。這份資料是觀察型調查（1972–1981 海牙健康調查），即使控制了四個共變數、即使 p = 0.0008，材料也沒有寫「養鳥導致肺癌」。**這個措辭紀律要原封不動搬進行銷 Skill**。

### 2.7 概似函數與 MLE

#### 【材料原文】概似函數（Likelihood Function）

- 對於一個給定的抽樣模型，我們可以把「樣本資料」帶入對應的機率函數，接著把這個機率，視為「未知參數的函數」。
- 例如，在 $N=10$ 次試驗中，若二項分配的成功次數為 $y=1$。
- 根據二項分配公式（$\pi$ 為成功機率）：

$$\Pr(Y = y) = \frac{N!}{y!(N-y)!}\,\pi^y (1-\pi)^{N-y},\quad y = 0,1,\ldots,N$$

- 在 $N=10,y=1$ 的情況下：$\Pr(1) = \frac{10!}{1!\,9!}\,\pi^1 (1-\pi)^9 = 10\pi(1-\pi)^9$
- 這個機率對所有可能的 $\pi$ 值都定義良好，也就是一個「以 $\pi$ 為自變數」的函數。
- 把「觀察到這筆資料的機率」，寫成「未知參數的函數」，就稱為 likelihood function（概似函數）。
- 在前述的例子中，當 $y=1$ 且 $N=10$ 時，$l(\pi) = 10\pi(1-\pi)^9$ 就是 $\pi$ 的概似函數。

#### 【材料原文】最大概似估計（Maximum Likelihood Estimate）

- **最大概似估計（MLE）** 的定義：使「觀察到這筆資料的機率」最大化的那個參數值。
  - 換句話說，就是讓概似函數取得最大值時的參數。
- 在前述例子中，$y=1,N=10$ 時，$l(\pi) = 10\pi(1-\pi)^9$ 在 $\pi = 0.1$ 取得最大值。
- 因此，當 $10$ 次試驗中有 $1$ 次成功時，$\pi$ 的 MLE 就是 $\hat{\pi} = 0.1$。
- 一般來說，二項分配在 $N$ 次試驗中出現 $y$ 次成功，其成功機率 $\pi$ 的 MLE 為 $\hat{\pi} = \frac{y}{N}$。
- 對 Poisson 分配而言，其平均參數 $\mu$ 的 MLE 則是樣本平均數。

#### 【材料原文】Logistic 模型中的 MLE（MLE in Logistic Model）

- 一旦給定參數的數值，logistic 迴歸模型就會指定：任何一組結果，例如：$y_1=1,y_2=0,y_3=1,\ldots$ ，出現的機率要如何計算。
- 對單一二元反應變數 $\mathrm{Y}$，其機率模型可寫為：
  - $\Pr(Y = y) = \pi^y(1-\pi)^{1-y}$
    - 代入 $y = 1$ 時，得到 $\pi$。
    - 代入 $y=0$ 時，得到 $1-\pi$。
- 假設現在有 $n$ 個這樣的反應值，且第 $i$ 個反應的參數是 $\pi_i$（$i = 1,\ldots,n$）。
- 若這些反應彼此獨立，它們的機率可相乘得到：

$$\Pr(Y_1 = y_1,\ldots,Y_n = y_n)
= \prod_{i=1}^{n} \pi_i^{\,y_i}(1-\pi_i)^{\,1-y_i}$$

這就是觀察到這一整組結果 $(y_1,\ldots,y_n)$ 的機率。

#### 【材料原文】MLE：Case Donner Party 的逐步示範

假設第 $i$ 位成員存活的機率為 $\pi_i$，再假設 logistic 迴歸模型正確，且參數取某一組「假設值」：

$$\text{logit}(\pi_i) = 1.50 - 0.08\,\text{Age}_i + 1.25\,\text{Sex}_i$$

對於第一位成員，一位 23 歲男性（Sex = 0），我們有：

- $\text{logit}(\pi_1) = 1.50 - 0.08\times 23 + 1.25\times 0 = -0.340$
- 因此 $\pi_1 = \frac{\exp(-0.340)}{1 + \exp(-0.340)} = 0.416$
- $\longrightarrow$ 第一位成員的存活機率約為 $0.416$。

重複這樣的推算，我們可以得到：

- $40$ 歲女性的存活機率約為 $0.389$。
- $40$ 歲男性的存活機率約為 $0.154$。

對於任何一組「獨立結果的組合」，都可以透過乘上各自的機率來計算整體機率：

- 所有人都活下來（$y_i = 1\;\forall \;i=1,2,...,n$）的機率是 $0.416 \times 0.389 \times 0.154 \times \cdots \times 0.679 = \exp(-53.3631)$
- 所有人都死亡（$y_i = 0\;\forall \;i=1,2,...,n$）的機率是 $(1-0.416)\times(1-0.389)\times(1-0.154)\times\cdots\times(1-0.679) = \exp(-25.1331)$
- 而「實際觀察到的結果」（哪幾位生存、哪幾位死亡）其機率則是 $(1-0.416)\times(0.389)\times(0.154)\times\cdots\times(0.679) = \exp(-26.1531)$

我們真正關心的是「實際發生的那一組結果」。

- 在這裡，剛剛那個機率公式就不只是「機率」，而是扮演了概似函數的角色。

同一個公式，可以用在不同的參數組合（不同的 $\beta$ 值）上，用來計算「觀察到這組實際結果」的機率。

- 對於某一組參數值，例如 $\beta_0 = 1.50, \beta_1 = -0.08, \beta_2 = 1.25$，用這組值算出來的 $\exp(-26.153)$ 就是該組參數的 likelihood：也就是「在這組 $\beta$ 之下，這個 outcome 出現的機率」。
- 一般而言：若某一組參數值，算出來的 likelihood 比另一組大，就說「在觀察到這組資料的前提下，前者比後者更為 plausible 或 more likely」。

**最大概似估計法**就是：從所有可能的參數組合裡，選出讓「實際 outcome 的機率」（likelihood）最大的那一組 $\beta$。

回顧一下在上一段 Case 1 跑出來的結果，以下都是透過最大概似法獲得的估計值（MLE）：

- $\hat{\beta}_0 = 1.6331$
- $\hat{\beta}_1 = -0.0782$
- $\hat{\beta}_2 = 1.5973$

#### 【材料原文】也可以透過 Excel 來手動求解 MLE

第一步是「設定需要計算的欄位」，包括：

- 輸入年齡、性別、存活狀態等原始資料。
- 建立 Intercept、Age 的欄位。
- 根據目前猜測的參數值，計算 logit、預測機率 $\hat{\pi}$、以及 log likelihood。
- 最後把所有 log likelihood 加總。

第二步是「啟用並設定 Excel 的 Solver（規劃求解）」：

- 把「log likelihood 的總和」當作目標儲存格。
- 設定為「最大化」。
- 允許變動的儲存格是 $\beta_0,\beta_1$（或再加 $\beta_2$）。
- Solver 會透過反覆運算，找到「讓 log likelihood 最大」的參數值。

只包含 Age 的 logistic 模型：

- 使用 Solver 求出的 $\beta_0, \beta_1$ 的 MLE，可以拿來和 R 的 `summary(case2001.lg1)` 輸出作比較。
- 在 Excel 手動求解出來的參數估計值：$\beta_0=1.81852$、$\beta_1=-0.06647$

「把 Sex 也放入模型」之後的 logistic 模型：

- 使用 Solver 求出的 $\beta_0, \beta_1, \beta_2$ 的 MLE，可以拿來和 R 的 `summary(case2001.lg2)` 輸出作比較。
- 在 Excel 手動求解出來的參數估計值：$\beta_0=1.50000$、$\beta_1=-0.08000$、$\beta_2=1.25000$
- 會看到 Excel 手動規劃求解的結果與 R 的結果相當接近。

#### 【材料原文】MLE 計算的一些補充說明

- 與最小平方法相同，我們原則上可以用微積分來找出「最大化」或「最小化」的參數值。

但跟「線性迴歸的最小平方法」不同的是：

- 在 logistic 這種 GLM 下面，用微積分通常無法得到封閉解（closed form）。
  - 白話來說，封閉解就是一套可以直接帶數字進去算出答案的「公式」。
    - 只要你的方程式能透過有限次的標準數學運算（加減乘除、開根號、指數、對數等）整理成 $x = \dots$ 的形式，那個解就叫做封閉解。
    - 也就是說，$\hat{\beta}$ 很難直接用一個簡單公式寫出來。
  - 沒有封閉解（No Closed Form）$\longrightarrow$ 需用數值解（Numerical Solution）
    - 很多複雜的方程式是導不出這種公式的。
    - 也就是說，無法把 $\beta$ 孤立在等號的一邊，寫不出 $\beta = \dots$。
    - 我們會改用「數值方法（Numerical Methods）」，也就是「逼近法」
      - 作法：
        1. 電腦先隨便猜一個答案。
        2. 看看這個答案跟真實數據差多遠。
        3. 根據誤差調整一點點，再猜一次。
        4. 重複幾千次，直到誤差小到可以忽略為止。

因此需要用一些反覆運算（iterative）的數值方法。統計軟體（例如 R）裡面的 `glm()` 函數就是這樣做的。

常見的數值方法的白話解釋：

**最大概似估計法：**

- 核心邏輯：「爬山法」。
- 運作方式：
  1. 電腦站在山腰（隨便猜一組參數）。
  2. 看看腳下的坡度（計算微分 / 梯度）。
  3. 往「上」走一步（修正參數）。
  4. 重複這動作，直到走到山頂（概似函數最大值）停下來。
- 特性：
  - 通常是確定性（Deterministic）的。
  - 只要起始點一樣，演算法每次走的路徑和算出來的答案要是一樣的。

**蒙地卡羅模擬（補）：**

- 蒙地卡羅方法通常用來處理「積分」或「機率」這種很難算的面積問題，或者是更複雜的系統模擬。
- 核心邏輯：「擲飛鏢法」。
- 運作方式：
  1. 假設你有一個形狀怪異的靶（這就是那個難算的數學問題）。
  2. 你閉著眼睛隨機對靶亂丟一萬次飛鏢（隨機抽樣）。
  3. 算出有多少支飛鏢射在靶內，除以總支數。
  4. 用這個比例來推算靶的面積。
- 特性：
  - 它是隨機性（Stochastic）的。
  - 依賴「大數法則」，丟越多次越準。每次跑出來的結果可能會有一點點微小的誤差。

#### ★【材料原文】最大概似估計的性質（射箭比喻）

當模型設定正確，而且樣本數夠大時，最大概似估計具有幾個重要性質：

**1. MLE 基本上是不偏的（essentially unbiased）：**

- 白話來說：這位射手不會亂瞄。雖然他每一箭可能不會剛好正中紅心，但如果你讓他射一萬次，這一萬支箭的「平均落點」，會不偏不倚剛好在靶心。
- 意義：保證了只要數據夠多，我們算出來的答案就會無限逼近真理，不會被系統性地算高或算低。

**2. 在所有「合理的不偏估計量」當中，MLE 的精準度通常是最好的或非常接近最好，即 MLE 是最有效率的（efficiency）**

- 白話解釋：（假設要聘請一位射手來幫你測試靶心在哪裡）
  - 普通射手：效率低。雖然平均來說瞄得準，但箭射得散散的（變異數大）。你要他射 100 支箭，取平均位置，才敢確定靶心大概在哪。
  - 菁英射手：效率高（即 MLE）。他的箭著點非常密集（變異數小）。每一支箭都緊咬著靶心不放。
- 意義：關係到荷包！
  - 誤差最小：若你只能負擔 10 支箭的錢（固定樣本數），MLE 射出來的結果最密集，讓你對結果最有信心。
  - 樣本最省：反過來說，若要求誤差不能超過 1 公分，普通射手可能要 50 箭才能靠平均值消除誤差，但 MLE 可能只要 10 箭就能達到同樣的精準度。
  - 在真實世界裡，每一支箭都是錢（樣本成本），MLE 能幫你用最少的成本找到真相。

**3. 估計量的抽樣分配形狀大致上是常態（Normality of Sampling Distribution）。**

- 白話解釋：不管原始資料長得多抽象（像是二元資料只是一堆 0 和 1），只要經過 MLE 處理算出係數，這些係數的誤差分佈看起來就會像一個完美的鐘形曲線（常態分佈）。
- 意義：
  - 可以用熟悉的 z-value 或 t-test 來檢定顯著性 。
  - 如果它不是常態，我們以前學的檢定方法就全廢了。

**4. 可以推導出公式來估計各估計量的標準差（也就是 sampling distribution 的標準差）**

- 也可以說，我們算得出誤差大小（Derivation of Standard Error）
- 白話解釋：MLE 不只給我們答案（係數），還可以同時帶出一套公式讓我們直接算出**標準誤（Standard Error）**
- 意義：有了這個，我們才能算出信賴區間（$\hat{\beta} \pm 1.96 \times SE$），打個比方，可以告訴老闆：「雖然我算出影響是 5 倍，但我有 95% 的信心它會落在 4 到 6 倍之間」。

**★ 若樣本數不大，實務上通常會在信賴區間與檢定結論上，加註「approximate（近似）」來提醒。**

- 如果樣本只有 10 個、20 個，MLE 就會像是一個還沒熱身的選手，可能會有偏差，射箭也不準，誤差也不常態。
- **可以說一切的結論都是在「樣本數足夠大」的前提下。**
- **小樣本時要小心使用，結果僅供參考！**

### 2.8 邏輯斯迴歸的模型評估（Model Assessment）

#### 【材料原文】二元反應的經驗值 vs 某個解釋變數的散佈圖

呼叫資料集（前面已經做過）：

```r
#### Case1 [Donner Party] ---------------------------------------------
library(Sleuth2)

attach(case2001)
case2001
	# summary(case2001)

## First model, consider Age only:
case2001.lg1 <- glm(Status~Age, binomial)
summary(case2001.lg1)
```

繪製 scatterplot 與模型預測曲線做比較：

```r
##  Scatterplot for case2001.lg1 
sq <- seq(14,66,1)
case2001$SP <- ifelse(case2001$Status=="Survived", 1, 0)	# survived or died

resp1 <- predict(case2001.lg1, type="response", newdata=data.frame(Age=sq))

plot(sq, resp1, type="l", col=2, ylim=c(0,1), ylab="Predicted Probability", 
     xlab="Age (years)", main="Logistic model: Status ~ Age")
points(Age, case2001$SP, pch=16)
```

### 2.9 殘差檢查（Examination of Residuals）— 三種殘差

#### 【材料原文】原始殘差（Raw Residuals）

- 定義為「觀察到的二元結果」減去「模型預測的成功機率」：

$$R.\text{res}_i = y_i - \hat{\pi}_i$$

- 由於這種殘差本身沒有什麼好用的統計性質，一般不太會直接拿 raw residuals 來做診斷。

白話解釋：

- 跟 Raw data 有類似的概念，沒經過任何前處理會存在過多雜訊。
- 在線性迴歸中，不管預測值是多少，因「同質變異數假設」，誤差的標準差都一樣。但在 Logistic 中，根據二項式分佈，變異數是 $\pi(1-\pi)$
  - 如果預測機率是 $0.5$，變異數最大，不確定性最高。
  - 如果預測機率是 $0.99$，變異數很小，相對很穩定。
  - 這樣子的比較並不具「可比性」，也因此才會有後續進行標準化的動作。
- 直接拿原始殘差來比，就好比「拿小學考卷跟大學考卷直接比分數」，忽略了題目的難易度（變異數）不同，所以是不公平的。

#### ★【材料原文】Deviance 殘差（Deviance Residuals）

Deviance 殘差衡量的是：

- 在每一筆觀測上，「模型配適」對整體 likelihood 造成的差異。
- **它是 GLM 中最常用的殘差形式，因為將所有點的 Deviance 殘差平方加總，就會得到模型的 Deviance 統計量（類似線性迴歸的 SSE）。**

在二元 logistic 模型中，第 $i$ 筆的 Deviance 殘差為：

$$D.\text{res}_i
= \operatorname{sign}(R.\text{res}_i)\,
  \sqrt{-2\Big[y_i\log(\hat{\pi}_i)
  + (1-y_i)\log(1-\hat{\pi}_i)\Big]}$$

**數學式解釋（材料原文）：**

- 為什麼括號內是「加號 (+)」？
  - 這是來自對數律 (Logarithm Rules)。
  - 在 Bernoulli trials 中，機率原本是相乘的：$\text{Likelihood} = \pi^y \times (1-\pi)^{1-y}$
  - 當我們取 Log (對數) 後，乘號就會變成加號：$\log(\text{Likelihood}) = y \log(\pi) + (1-y) \log(1-\pi)$
  - 這就是公式中那兩項相加的由來，分別代表「成功部分的貢獻」與「失敗部分的貢獻」。
- 為什麼要乘上 -2 並開根號？
  - 因為機率介於 0～1 之間，取對數後必然為負，換言之，$\log(\hat{\pi})$ 必定是負數。
  - 因此我們乘上 $-2$ 讓它變成正數，這也是 Deviance 的標準定義，這樣才能開根號，因為不考慮虛數下，根號裡面必須為正。
  - 開根號是為了讓殘差的尺度（Scale）回到跟一般殘差類似的水準。
- $\operatorname{sign}(\dots)$ 的作用：
  - 因為開根號出來一定是正的，我們會丟失該筆資料的方向性。
  - 因此加上 $\operatorname{sign}(y_i - \hat{\pi}_i)$ 是為了把「原始殘差的正負號」補回來，讓我們知道預測是高估了還是低估了。

白話解釋：

- 貢獻度的概念：Deviance 殘差就是在問：「這一個點 $i$，對整個模型『配適度變差 (Badness of Fit)』這件事，到底貢獻了多少？」
- 判讀：
  - 若是 0：代表這個點被完美預測，沒有增加模型的負擔。
  - 若數值很大：代表這個點正在「拖累」整個模型，讓模型配適度變差。

#### ★【材料原文】Pearson 殘差（Pearson Residuals）

- Pearson 殘差是「觀察值與預測值的差」，再除以預測值的標準差（所以有 scaling 的效果）。
- 在二元 logistic 模型中，第 $i$ 筆的 Pearson 殘差為：

$$P.\text{res}_i
= \frac{Y_i - \hat{\pi}_i}
       {\sqrt{\hat{\pi}_i(1-\hat{\pi}_i)}}$$

白話解釋：

- 這其實就是標準化**概念**：$\frac{x - \mu}{\sigma}$。
  - 分子是誤差，即觀察值 $Y_i$ 減掉預測發生機率 $\hat{\pi_i}$
    - 注意，在這裡 $Y_i$ 不是 0 就是 1，$\hat{\pi_i}$ 一定介於 0 到 1。
  - 分母是標準差，即 $\sqrt{\hat{\pi_i}(1-\hat{\pi_i})}$，要記得這是成敗試驗的標準差。
- 這是在做「校正」，把剛剛說的「題目難易度」考慮進去，讓每個觀測值的殘差站在同一個基準線上比較。這樣絕對值大於 2 就真的代表「異常」了。

#### ★【材料原文】殘差診斷的判準與注意事項

- 在樣本數夠大的情況下，若模型設定正確，不論是 Deviance residuals 還是 Pearson residuals，都會「看起來像」來自一個標準常態分配。
  - 因此可以特別留意**絕對值大於 2 的殘差**，這些點通常被視為可能的 outliers 或 model misfit 指標。
  - 實務上可以用 `qqnorm()` 搭配 `qqline()`，畫出殘差的 Q-Q plot 來檢查常態性與模型適配情況。
    - **注意！圖畫出來是不會看到線性迴歸那樣雲狀或散點狀的隨機分佈的。**
    - 因為 $Y$ 只有 0 和 1：
      - 當 $Y=1$，殘差是正的。
      - 當 $Y=0$，殘差是負的。
    - **會在圖上看到兩條奇怪的曲線是正常的，因為這就是二元資料的特性。**

#### 【材料原文】R-Code：計算三種 residuals

```r
R.res.1 <- fitted(case2001.lg1)-case2001$SP
D.res.1 <- residuals(case2001.lg1, type="deviance")	# deviance residuals
P.res.1 <- residuals(case2001.lg1, type="pearson")	# perason residuals

	cbind(case2001$SP, fitted(case2001.lg1), R.res.1, D.res.1, P.res.1)
```

畫出 Deviance residuals 的 Q-Q plot：

```r
qqnorm(D.res.1)
```

畫出 Pearson residuals 的 Q-Q plot：

```r
qqnorm(P.res.1)
```

**這回答什麼行銷/商業問題**：找出「模型死都預測不對」的顧客——高 |deviance residual| 的個案往往是新的細分市場、資料錯誤、或是模型漏掉的重要變數（材料在 MLR 那段列的四大原因同樣適用）。

### 2.10 ★★ The Deviance Goodness-of-Fit Test（Deviance 適合度檢定）

#### 【材料原文】Deviance 是什麼

Deviance 是 logistic 迴歸中的一個關鍵概念。

- 直觀來說，Deviance 是衡量模型「壞」的程度（Badness-of-Fit）。
  - 它量測我們目前的模型，距離一個完美的「飽和模型（Saturated Model）」還有多遠。
  - **飽和模型（$\text{M}_s$）**：這是一個想像中的模型，它有足夠多的參數可以完美預測每一個樣本點，甚至連雜訊都預測進去了（Likelihood = 1）。

#### 【材料原文】Deviance 的精確定義

$$\text{Deviance}
= -2\Big[\log L(M_f) - \log L(M_s)\Big]$$

- $M_f$：目前的模型（Current / Fitted Model）。
- $M_s$：飽和模型（Saturated Model）。
- 因為 $\log L(M_s) = 0$（完美配適），所以公式常簡化為 $-2 \log L(M_f)$。
- 特性：$\text{Deviance} \ge 0$。
  - 數值越小，代表模型越接近完美（越好）。

#### 【材料原文】評估基準：Null Deviance（$M_0$）

- 定義：這是「最陽春」的模型，只包含截距（Intercept only），不放入任何解釋變數。
- 數學式：$\text{Deviance}_0 = -2\log L(\hat{\beta}_0)$
- 直觀解釋：這就像是「瞎猜」的基準線，只用平均機率來猜。
- 用途：作為比較的起點。
  - 我們會計算（Null Deviance − Current Deviance）：
    - 這代表加入解釋變數後，模型在配適度上改善了多少（進步幅度）。
      - 這也是計算 Logistic Regression 中 $R^2$ 的基礎。
    - 這其實就是我們前面做的 LRT（Likelihood-Ratio Test）比較 。

#### ★★★【材料原文】Deviance 適合度檢定（Deviance Goodness-of-Fit Test）

- **核心目的**：正式檢驗目前的模型與完美的「飽和模型」是否有顯著差異。
- **檢定假設**：
  - $\mathrm{H}_0$：目前模型是合理的好模型（跟飽和模型無顯著差異）。
  - $\mathrm{H}_1$：目前模型配適不佳（Lack of fit）。
- **統計性質**：
  - 若模型配適良好且樣本數夠大，Deviance 統計量會「近似」服從自由度 $\mathrm{d}_\mathrm{f} = n - p$ 的卡方分配。
- **判決規則**：
  - $\text{p-value}$ 很大：不拒絕 $\mathrm{H}_0$。代表模型還不錯，Deviance 沒有大到「值得擔心」。
  - $\text{p-value}$ 很小：拒絕 $\mathrm{H}_0$。代表 Deviance 太大了，模型配適不良。
- **可以用的情況**：
  - 當資料是**分組資料（Grouped Data）**，例如：
    - 同一組 $\mathrm{X}$ 有多個觀測值，像 $n_i > 1$ 的二項式迴歸
    - Poisson 迴歸時這個卡方近似性質才成立。
- **★ 不能直接用的情況（最常見陷阱）**：
  - 當資料是**未分組二元資料（Ungrouped Binary Data）**，就是我們最常見的 0 / 1 資料，每筆都是獨立的 $n_i=1$ 時。
    - **此時 Deviance 並不服從卡方分配，直接做適配度檢定算出的 $\text{p-value}$ 不準確。**
    - **替代方案：對於二元資料，我們通常專注於模型間的比較（LRT），看 Null Deviance 降了多少，而不是看絕對數值。**

#### 【材料原文】整個概念上的白話解釋（先看）

考試的比喻（三種模型）：

- **飽和模型（Saturated）**：就像作弊的學生。拿著標準答案卷全抄，考了 100 分。這是天花板，但沒意義。
- **Null 模型（Null）**：就像完全沒唸書的學生。每一題都用猜的，考出全班最低分。這是地板。
- **目前模型（Current）**：我們訓練的模型。目標是離「作弊學生」越近越好（Deviance 小），離「亂猜學生」越遠越好。

扣分的概念（Deviance）：

- Deviance 就是 "Deviation"（偏離）。
  - 可以把它想成是「被扣了多少分」。
  - 飽和模型是 0 扣分。
  - 數值越大，代表被扣越多分，模型越不像樣。
  - 我們的目標是 Minimize Deviance（最小化扣分）。

**這回答什麼行銷/商業問題**：「我的購買預測模型到底配適得好不好？」——**但只有分組資料能問這個問題**。行銷資料多半是「一列一個顧客、Y = 買/沒買」的未分組資料，此時 `summary(glm)` 印出的 Residual Deviance 與 df 不能拿去查卡方表，唯一能做的是模型間比較（LRT / AIC）。

**【評註】★ 分組 vs 未分組 —— 這是 1118→1125 的核心分水嶺，先在此建立完整對照：**

| | 未分組（Ungrouped / Binary） | 分組（Grouped / Binomial） |
|---|---|---|
| 資料一列代表 | 1 個個體，$Y_i \in \{0,1\}$ | 1 個 covariate pattern，$y_i$ 成功 / $n_i$ 試驗 |
| $n_i$ | $n_i = 1$ | $n_i > 1$ |
| R 語法 | `glm(Y ~ X, family=binomial)` | `glm(cbind(succ, fail) ~ X, family=binomial)` |
| 係數估計 | 相同（同一組 $\hat\beta$） | 相同 |
| Deviance 絕對值 | **不服從 $\chi^2$**，不可做 GOF | 服從 $\chi^2_{n-p}$，**可做 GOF** |
| Deviance 差（LRT） | **可用**（Drop-in-Deviance） | 可用 |
| Overdispersion 診斷 | 做不了（無 GOF 基準） | 可以（見 Part 3） |

---

<a id="part-3"></a>
## Part 3 — 1125：Binomial Logistic（分組資料）、Deviance 適合度、Overdispersion

### 3.1 ★★ 二項反應（Binomial responses）：分組資料的定義

#### 【材料原文】二項反應的概念

**核心定義：**

- 一個「二項次數（Binomial Count）」其實就是多個獨立的「二元反應（0/1）」的總和。
- 假設這些反應都具有相同的成功機率 $\pi$。

**符號：**

- 若有 $m$ 個二元反應（樣本），母體成功比例為 $\pi$。
- 它們的總和 $\mathrm{Y}$（整數）服從二項分佈：$\mathrm{Y} \sim \text{binomial}(m, \pi)$

**名詞解釋：**

- $m$：稱為**二項分母（Binomial Denominator）**，也就是試驗的總次數。
- $\frac{Y}{m}$：稱為**二項比例（Binomial Proportion）**。

**迴歸情境：**

- 我們通常有多組觀測值，寫成 $\mathrm{Y}_i \sim \text{binomial}(m_i, \pi_i)$。
- 每個 $m_i$（每組的總數）不必相同，但**必須是已知的**。

#### ★★【材料原文】注意：不是所有的「比例」都能用二項式迴歸

> **這是最容易犯錯的地方！不是所有的「比例」都能用二項式迴歸。**

- **Counted Proportion**（由計數得來的比例），例如：
  - 21 個人裡面有 15 個人買 iPhone，比例是 $\frac{15}{21}$。
  - 分子（$\mathrm{Y}$）和分母（$m$）都是整數。
  - $\Longrightarrow$ **這是 GLM（Binomial）要處理的對象。**
- **Continuous Proportion**（連續型比例），例如：
  - 化學溶液濃度是 0.732、GDP 成長率。
  - 這種數字不是由「幾個成功 / 幾個總數」算出來的。
  - $\Longrightarrow$ **這不能用 Binomial GLM**（可能要用 Beta Regression 或轉換後用 Normal）。

**這回答什麼行銷/商業問題**：行銷報表滿滿都是「比例」——CTR、CVR、開信率、退貨率。**能不能丟進 binomial GLM，取決於你手上有沒有分母的整數次數**。有 impressions / clicks 兩欄 → 可以；只有一個 0.032 的 CTR 欄位、沒有曝光數 → 不可以（資訊已經被丟掉了，且每一列的可信度差異無法反映）。

### 3.2 ★★ 二項邏輯斯迴歸模型（Binomial Logistic Regression Model）

#### 【材料原文】模型公式

- 假設 $\mathrm{Y} \sim \text{binomial}(m, \pi)$

$$\text{logit}(\pi) = \beta_0 + \beta_1 x_1 + \beta_2 x_2$$

- 這個模型的解讀方式，與 11/28 中提到的「Binary logistic regression」相同。（原文如此，應指 11/18 那一頁）
- 係數解釋、Odds Ratio 的算法都一樣。
- 差別在於：
  - **Binary logistic regression 是 Binomial logistic model 的特例：也就是所有的 $m_i = 1$（每一筆只有一個 $0/1$）。**

#### ★★★【材料原文】白話解釋 Binary 與 Binomial 的差異

> **這兩個模型其實只是資料整理的方式不同。**

**Binary（二元分配）：**

- 資料長相：
  - 原始資料 (Raw Data)。
  - 每一列就是一個人，$\mathrm{Y}$ 是 0 或 1。
- 特例：
  - Binary 其實就是 Binomial 的特例。
  - 也就是所有的 $m_i = 1$，每組只有 1 個人。

**Binomial（二項分配）：**

- 資料長相：
  - 彙總資料（Aggregated / Grouped Data）。
  - 每一列是一個「群組」，例如：按年級分組。
  - $\mathrm{Y}$ 是「這組有幾個人成功」。
  - $m$ 是「這組總共有幾個人」。
- 結論：
  - **不管你餵給 R 吃哪種格式，背後的數學原理和算出來的 $\beta$ 係數是一模一樣的。**

**【評註】分組 vs 未分組的完整差異對照（合併 1118 + 1125 的材料）：**

| 面向 | Binary（未分組 / Ungrouped） | Binomial（分組 / Grouped） |
|---|---|---|
| 一列代表 | 1 個個體 | 1 個 covariate pattern（群組） |
| 反應變數 | $Y_i \in \{0,1\}$ | $Y_i$ = 成功數，$m_i$ = 該組總數 |
| $m_i$ | 恆為 1 | $>1$，且**必須已知** |
| R 語法 | `glm(Y ~ X, family=binomial)` | `glm(cbind(succ, fail) ~ X, family=binomial)` |
| $\hat\beta$、OR 解讀 | **完全相同** | **完全相同** |
| EDA 圖 | 0/1 散佈圖 + jitter + 預測曲線 | **Empirical logit plot**（可看線性） |
| 殘差近似常態 | 不成立（會看到兩條曲線） | $m_i$ 夠大時成立（可看 Q-Q plot） |
| Deviance GOF 檢定 | **不可用**（Deviance 不服從 $\chi^2$） | **可用**（$\chi^2_{n-p}$） |
| LRT / Drop-in-Deviance | 可用 | 可用 |
| Overdispersion 診斷 | 做不了 | **可以**（$\hat\psi = \text{Dev}/df$） |
| 模型評估手段 | 少（只能比模型） | **豐富很多**（材料原話） |

### 3.3 CASE：Survey iPhone / Survey Mac 資料集

#### 【材料原文】來自修習統計課學生的問卷資料

- student：undergrad or grad
- grade：目前就讀系所之年級
  - B1：大學部一年級
  - B2, B3, B4, B5
  - R1：碩士班一年級
  - R2, R3
  - D：博士班
- gender：F 或 M
- fb：臉書好友人數平均有多少位
- cash：平常大概會帶多少現金在身上
- shopping：每個月網路購物的平均次數
- iphone：手機是否為 iPhone（Yes or No）
- mac：電腦是否為 Mac（Yes or No）

想探討：

- **CASE iPhone**：持有 iPhone 筆電的學生比例，與其他變數（性別、年級、fb 數、現金額度、網購次數…）之間，是否存在關聯性。
- **CASE Mac**：持有 Mac 筆電的學生比例，與其他變數（性別、年級、fb 數、現金額度、網購次數…）之間，是否存在關聯性。
- 兩個 CASE 資料集一樣，就是探討的變數不同而已。

【評註】這個案例的行銷等價物幾乎是 1:1 的：**「持有 iPhone」= 高價品持有 / 品牌偏好；「fb 好友數」= 社群影響力分數；「cash」= 可支配所得代理變數；「shopping」= 購物頻次**。而且資料被彙總成分組資料（`survey_sum.csv`），正是行銷部門 dashboard 常見的形式（一列一個分眾、兩欄成功/失敗數）。

### 3.4 模型評估（Model Assessment）— 分組資料的優勢

> **【材料原文】現在處理的是分組資料（Binomial Data），評估模型的手段就會比單純的二元資料 (0/1) 豐富很多。**

#### ★【材料原文】實證對數比與解釋變數的散佈圖（Logit Plot）

- 目的：**在還沒跑模型前，先用肉眼檢查 $\mathrm{X}$ 跟 $\mathrm{Y (Logit)}$ 之間是不是線性關係。**
- 定義：
  - 第 $i$ 筆資料的反應比例：$\hat{\pi}_i = \frac{\mathrm{Y}_i}{ m_i}$。
  - 實證 Logit（Empirical Logit）：直接拿觀察數據算的 Logit 值。

$$\log\left(\frac{\hat{\pi}_i}{1-\hat{\pi}_i}\right) = \log\left(\frac{\mathrm{Y}_i}{m_i - \mathrm{Y}_i}\right)$$

- 實務問題與解法：
  - 問題：
    - 如果某一組全部成功（$\mathrm{Y}_i=m_i$）或全部失敗（$\mathrm{Y}_i=0$），比例是 1 或 0。這時候 Logit 會碰到 $\log(0)$ 或除以 $0$，導致沒有意義。
  - 解法：
    - 在分子分母都偷加一個小常數（例如 0.5）。

$$\text{Adjusted Logit} = \log\frac{\mathrm{Y}_i + 0.5}{m_i - \mathrm{Y}_i + 0.5}$$

    - 其實就跟 In-class practical 時，發現變數變換時，原資料可能存在 0 值做的處理一樣，目的就是要避免 log 或分數出現 0 的情況。

**Logit Plots of Survey：iPhone（材料原文）**

- 把「iPhone 使用比例」的經驗 logit 對 fb 好友數作圖。
- 散佈圖顯示：
  - iPhone 機率的 logit 跟 fb 好友數之間，看起來可以用一條近似線性的關係來描述。
  - 符合模型假設：$\text{logit}(\pi_{\text{iphone}}) \sim \text{fb}$。

**這回答什麼行銷/商業問題**：「這個連續驅動因子（曝光次數、瀏覽秒數、社群分數）跟轉換的關係，真的可以用一條直線在 logit 尺度上描述嗎？」——**Empirical logit plot 是 logistic 版的散佈圖**，也是判斷「要不要加平方項 / 要不要分箱」的第一手證據。未分組資料做不到這件事，這是實務上把資料先彙總成分組的主要理由之一。

#### ★【材料原文】殘差檢查（Examination of Residuals）— 分組版公式

> 這裡的殘差診斷比 Binary Data 更有意義，當分組大小 $m_i$ 夠大時，殘差會近似常態分佈。

**Deviance 殘差（Deviance Residuals）**

- 定義方式：
  - 讓所有 $n$ 筆 deviance 殘差的平方和剛好等於整體 deviance 統計量。
  - 用以衡量每一筆觀測對「整體模型配適度變差」的貢獻。
  - 對於第 $i$ 筆二項反應，二項分母為 $m_i$ 時：

$$D.\text{res}_i
= \operatorname{sign}(Y_i- m_i\hat{\pi}_i)
  \sqrt{2\Bigg\{
  Y_i \log\left(\frac{Y_i}{m_i\hat{\pi}_i}\right)
  + (m_i - Y_i)\log\left(\frac{m_i - Y_i}{m_i - m_i\hat{\pi}_i}\right)
  \Bigg\}}$$

- 優點：
  - 與 LRT / Drop-in-deviance test 的數學結構一致，理論性質較佳 。
  - 若模型正確且 $m_i$ 夠大，殘差應近似標準常態分佈。

**Pearson 殘差（Pearson Residuals）**

- 定義方式：
  - 「觀察到的 binomial 次數」減去「預測的期望值」，再除以「預測值的標準差」。
  - 也就是「標準化」後的誤差：

$$P.\text{res}_i
= \frac{Y_i - m_i\hat{\pi}_i}
       {\sqrt{m_i\hat{\pi}_i(1 - \hat{\pi}_i)}}$$

  - 分子是觀測誤差。
  - 分母是二項分佈的標準差。
- 優點：
  - 直觀好懂，做初步檢查最常用 。
  - 若模型正確且 $m_i$ 夠大，殘差應近似標準常態分佈。
- 診斷標準：
  - 離群值 (Outliers)：**特別注意絕對值 > 2 的點。**
  - 圖形檢查：可以用 `qqnorm()` 畫 Q-Q Plot。若點都在直線上，代表模型配適良好。

### 3.5 ★★★ Deviance 適合度檢定（The Deviance Goodness-of-Fit Test）— 分組版

> 【材料原文】這是正式的統計檢定，用來回答：「模型是否足夠好？」

#### 【材料原文】三個模型的定位

**感興趣的模型（fitted model, $\mathrm{M}_f$）：**

- 也就是我們目前討論的模型。

$$\text{logit}(\pi_i)
= \beta_0 + \beta_1 x_{i1} + \cdots + \beta_p x_{ip}$$

- **參數個數**：$p$ 個（包含截距）。

**飽和模型（saturated model, $\mathrm{M}_s$）：**

- 這是一個理論上的「作弊模型」。
- 它對每一筆分組資料（$i=1 \dots n$）都單獨估計一個參數，完全貼合數據。

$$\text{logit}(\pi_i) = \hat{\pi}_i = \text{logit}\left(\frac{y_i}{m_i}\right)$$

- 參數個數：$n$ 個，跟資料筆數一樣多。
- Likelihood：因為完美作弊，Likelihood = 1，Log-Likelihood = 0。

**評分標準：Deviance（偏差）**

- 定義：
  - 衡量目前模型 $\mathrm{M}_f$ 與完美模型 $\mathrm{M}_s$ 在 Log-Likelihood 上的差距。

$$\text{Deviance} = -2 \Big[ \log L(M_f) - \log L(M_s) \Big] = -2 \log L(M_f)$$

- **性質**：
  - $\text{Deviance} \ge 0$。
  - 數值越小，代表離完美越近（配適越好）。
  - 只有在「完美配適」時才會等於 0。

#### 【材料原文】檢定方法

**假說：**

- $\mathrm{H}_0$：（以下都行）
  - 目前的 Logistic GLM 是合適的。
  - Good Fit。
  - 與飽和模型無顯著差異。
- $\mathrm{H}_1$：（以下都行）
  - 目前的模型配適不佳
  - Lack of Fit。

**檢定統計量：**

若以 $y_i$ 表示觀察到的計數，$\hat{\mu}_i = m_i \hat{\pi}_i$ 表示預測的期望值，我們有兩種檢定方式可以測：

- **Likelihood-Ratio 統計量（$\mathrm{G}^2$ 即 Deviance）：**

$$\mathrm{G}^2 = 2 \sum y_i \log\left(\frac{y_i}{\hat{\mu}_i}\right) + 2 \sum (m_i - y_i) \log\left(\frac{m_i - y_i}{m_i - \hat{\mu}_i}\right)$$

  - 註：這就是 Deviance 的展開式，考慮了成功與失敗兩部分。

- **Pearson $\chi^2$ 統計量：**

$$\chi^2 = \sum \frac{(y_i - \hat{\mu}_i)^2}{\hat{\mu}_i (1 - \hat{\pi}_i)}$$

  - 註：這是標準化殘差的平方和。

**判讀規則：**

- 若二項分母 $m_i$ 都夠大，這兩個統計量都會近似服從卡方分佈 $\chi^2_{(n-p)}$。
- 若 $\text{p-value}$ 很小，例如 $\text{p-value}< 0.05$，則拒絕 $\mathrm{H}_0$，可以推論模型有問題（配適不良）。

#### ★★【材料原文】速算法（老師提的快速判斷法）

每次都要查表算 p-value 很麻煩，所以老師提了一個快速判斷法：利用卡方分佈的統計特性，可以直接「估算」模型好不好。

**原理：**

- 一個自由度為 $\mathrm{d}_\mathrm{f}$ 的卡方隨機變數 $\chi^2_{\mathrm{d}_\mathrm{f}}$，它的：
  - **期望值：剛好等於 $\mathrm{d}_\mathrm{f}$。**
  - **標準差：約為 $\sqrt{2\mathrm{d}_\mathrm{f}}$。**
  - 這代表，若模型是正確的，Deviance 的數值應該會落在 $\mathrm{d}_\mathrm{f}$ 附近跳動。

**實際操作：**

直接把算出來的 Deviance 與自由度 $\mathrm{d}_\mathrm{f}$ 拿來比大小：

- $\text{Deviance} \approx \mathrm{d}_\mathrm{f}$
  - 判定：模型及格，不拒絕 $\mathrm{H}_0$。
  - 解釋：Deviance 沒有偏離期望值太遠，在合理誤差範圍內。
- $\text{Deviance} \gg \mathrm{d}_\mathrm{f}$（遠大於的情形）
  - 判定：模型不及格，可能拒絕 $\mathrm{H}_0$。
  - 解釋：Deviance 大到超過了合理的隨機波動範圍。

**注意：**

- 所謂的「遠大於」，通常是指超過好幾個標準差 $\sqrt{2\mathrm{d}_\mathrm{f}}$，不是只大一點點 。

**結論：**

- 只要看到 Residual Deviance 的數字比 Degrees of Freedom 大非常多，基本上就可以猜測：「這個模型有問題！」
- 可能是變數沒設好，或是發生了 Overdispersion。

**這回答什麼行銷/商業問題**：`summary(glm)` 一印出來，第一眼就掃 `Residual deviance: 20.195 on 15 degrees of freedom`——20 vs 15 沒事；如果看到 `320 on 15`，模型就有嚴重問題，不要急著解讀係數。**這是最便宜的模型體檢。**

#### ★★★【材料原文】檢定失敗通常是以下三個原因

當得到一個「很小的 $\text{p-value}$」或「Deviance 遠大於 $\mathrm{d}_\mathrm{f}$」時，通常是以下三個原因造成的：

**1. 系統成份錯誤（Systematic Component Issue）：**

- 也可以說是模型形式錯誤。
- 變數漏了：重要的解釋變數沒放進去。
- 形式錯了：變數雖有放，但可能要平方項 $\mathrm{X}^2$ 或交互作用項 $X_1 \times X_2$。
- 解決方法：
  - 畫 Logit Plot 檢查線性關係。
  - 加變數。

**2. 異常值作祟（Outliers）：**

- 少數幾個極端點貢獻了巨大的 Deviance。
- 解決方法：
  - 檢查 Residuals，找出那些殘差絕對值 > 2 的點。

**3. 隨機成份錯誤（Random Component Issue）**

- **最常見的問題！**
- 超額變異（Overdispersion）：
  - 二項分配假設樣本是獨立且機率固定的，但資料可能存在「群聚效應」或「異質性」。
  - **這會導致 Deviance 異常的大，但係數估計其實沒錯，只是標準誤 (SE) 被低估了。**
- 解決方法：
  - 使用 Quasi-likelihood 方法來校正。

【評註】**這三條就是一張現成的除錯決策樹**：Deviance 太大 → (1) 先看 logit plot 是否非線性、有沒有漏變數 → (2) 再看有沒有幾筆殘差 > 2 撐大整體 → (3) 都排除後才歸因 overdispersion，改用 quasibinomial。**順序不能顛倒**（見 3.8）。

### 3.6 Logistic 迴歸係數的推論（分組資料版）

#### 【材料原文】Wald 檢定與信賴區間（Wald's Tests & Confidence Intervals）

- 理論基礎：在邏輯斯迴歸中，只要整體樣本數 $n$ 夠大，或各筆觀測的二項分母（$m_i$）都足夠大，則迴歸係數的估計值（$\hat{\beta}$）會近似服從常態分配。
- 以 iPhone 個案為例：
  - 我們想知道「FB 好友數 (fb)」是否影響「使用 iPhone」的機率。
  - 從 R 的 `summary` 輸出可以看到，`fb` 係數的雙尾 $\text{p-value}$ 非常小（0.0107）。
  - 結論：這證實了前面在散佈圖（Logit Plot）中看到的視覺證據：使用 iPhone 的機率與 FB 好友數有顯著的正相關。
- 信賴區間的驗證：
  - 我們也可以從信賴區間得到類似的訊息。
  - 使用 `confint.default(iphone.lg1)` 可以算出基於常態假設的區間：
    - `fb` 的 $95\%$ 信賴區間是 $[0.00046, 0.0035]$。
  - 判讀：
    - 因為整個區間不含 0（都是正數），所以我們有 95% 的信心拒絕虛無假說。
    - 確認 FB 好友數越多，用 iPhone 的機率越高。

#### 【材料原文】概似比／Drop-in-Deviance 檢定

- 理論優勢：
  - 相關研究指出，就算樣本數或二項分母不是很大，LRT (Likelihood-Ratio Test) 通常仍有不錯的表現。
  - 不過在這種小樣本情況下，我們還是習慣把推論標記為「近似（Approximate）」以示謹慎。
- 以 Case：iPhone 為例，LRT 是用 Null 模型 $\to$ 現在模型之間 Deviance 的下降量，作為卡方檢定的統計量。
  - R：
    - Null Deviance（只有截距）：26.934（$\mathrm{d}_\mathrm{f} = 16$）
    - Residual Deviance（加入 fb）：20.195（$\mathrm{d}_\mathrm{f} = 15$）
  - Drop-in-Deviance 計算：$26.934 - 20.195 = 6.739$
  - 自由度差異：$16 - 15 = 1$
  - 結論：
    - $\text{p-value}$ 約為 0.0094。
    - 這與 Wald Test 的結果（0.0107）非常接近，同樣都顯示極高度的顯著性。
    - **但在嚴謹的分析中，我們更傾向相信 LRT 的結果。**

### 3.7 個案分析 R-code 全流程（分組資料的完整模板）

#### 【材料原文】讀取資料

```r
	survey.s <- read.csv("survey_sum.csv")
	attach(survey.s)
```

#### ★【材料原文】建立模型

```r
iphone.lg1 <- glm(cbind(iphone, notiphone) ~ fb, family=binomial)
summary(iphone.lg1)
```

- **`cbind(iphone, notiphone)`**：
  - 因為我們的資料是 **Grouped Data**，每一列代表一群人。
  - R 的 `glm` 要求 Binomial 模型的 $\mathrm{Y}$ 必須是兩欄：
    - 第一欄是「成功次數」。
    - 第二欄是「失敗次數」。
    - **這與之前 Binary（$\mathrm{Y}=0/1$）的寫法不同。**
- **`family=binomial`**：指定使用二項式分佈與 Logit 連結函數。

#### 【材料原文】Logit Plot

```r
( proportion <- iphone/total )           # 算出每一組的 iPhone 使用比例
logit1 <- log(proportion/(1-proportion)) # 手動計算 Empirical Logit

plot(fb, logit1, pch=20, ylab="logit (iphone)") # 畫散佈圖
abline(coef=iphone.lg1$coef, lty=2, col=2)      # 加上模型預測的直線
```

- **目的**：檢查 `logit(iphone)` 跟 `fb`（好友數）是否呈現直線關係。

#### 【材料原文】確認 `fb` 這個變數是否顯著

```r
## (1) Wald's Test & C.I.
confint.default(iphone.lg1)
```

- **Wald Test**：`confint.default` 給出信賴區間，若區間不包含 0，代表顯著 。

```r
## (2) LRT / Drop-in-Deviance Test
1 - pchisq(iphone.lg1$null.deviance - deviance(iphone.lg1), 1)
```

- **LRT（Drop-in-Deviance）**：
  - 計算（Null Deviance - Residual Deviance）。
  - `pchisq(..., 1)`：查自由度為 1 的卡方表。
  - `1 - ...`：算出 $\text{p-value}$。
    - 這裡算出 $0.0094$，非常顯著。

#### 【材料原文】殘差分析

```r
( pihat <- fitted(iphone.lg1) )    # 模型預測的機率 (Predicted Probability)
( rawres <- proportion - pihat )   # 原始殘差 (不好用)

( respea <- residuals(iphone.lg1, type="pearson") )  # Pearson 殘差 (標準化後)
( resdev <- residuals(iphone.lg1, type="deviance") ) # Deviance 殘差 (貢獻度)

cbind(proportion, pihat, rawres, respea, resdev) # 把大家排在一起比較

## 畫 Q-Q Plot
qqnorm(respea); qqline(respea)
qqnorm(resdev, pch=16); qqline(resdev)
```

- 重點：因為這是分組資料且分母夠大，理論上殘差應該要近似常態分佈。

#### ★【材料原文】適合度檢定

```r
## (1) Deviance Goodness-of-Fit (Gsq)
deviance(iphone.lg1)     # 算出 Residual Deviance (約 20.195)
iphone.lg1$df.residual   # 算出 自由度 df (15)
1 - pchisq(deviance(iphone.lg1), iphone.lg1$df.residual)
```

```r
## (2) Pearson Goodness-of-Fit (Xsq)
( Xsq <- sum(respea^2) ) # 手動算 Pearson Chi-square 統計量
1 - pchisq(Xsq, df=iphone.lg1$df.residual)
```

- 速算法檢驗：
  - $\text{Deviance}=20.195$ vs. $\mathrm{d}_\mathrm{f}=15$。
    - 雖然 20 比 15 大一點，但沒有「大非常多」。
  - 正規檢定：
    - 算出來的 $\text{p-value}=0.164$。
  - 結論：
    - $\text{p-value} > 0.05$，不拒絕虛無假說。
    - 代表模型配適良好，沒有證據顯示模型有問題。

#### 【材料原文】CASE：Survey Mac — 加入性別與交互作用

與前段內容基本上完全一樣，只跑不同的地方。

```r
mac.lg2 <- glm(cbind(mac, notmac) ~ fb * gender, family=binomial)
summary(mac.lg2)
# -> 'gender' not significant
```

- 結果發現不顯著，所以後面的分析又退回去用只含 `fb` 的 `mac.lg1` 模型。
- 最後的配適度檢定（$\text{p-value} = 0.16$）也顯示 `mac.lg1` 模型配適良好 。

### 3.8 ★★★ GLM - Overdispersion（超額變異）

#### 【材料原文】白話解釋什麼是超額變異（先看！）

超額變異（Overdispersion），根本原因是：**真實世界的資料，通常比理論模型預期的還要『亂』。**

**打個比方：模範生 vs. 真實班級**

- 理論模型眼中的世界（二項式分佈）：
  - 假設資料是「一群互不認識的模範生」。
  - 大家都很乖，每個人考試及格的機率都一樣，而且絕對不會互相偷看（獨立）。
  - 預期結果：全班成績的波動（變異數）應該是很穩定的，完全在掌控之中。
- 真實世界的狀況（存在 Overdispersion）：
  - 現實的資料通常是「一群會互相影響的屁孩」。
    - 不獨立：好朋友會互相偷看答案（群聚效應）。
    - 不同質：有些學生其實是資優生，有些完全沒唸書（機率其實不一樣）。
  - 實際結果：
    - 會發現全班成績大起大落，波動比理論預期的還要大很多！
    - 實際上，就是「變異數」超標了。

**為什麼要在乎超額變異？**

- 如果你的模型忽略了這一點，強行用標準理論去分析，它就會變成一個「自我感覺良好」的分析，忽略了真實世界所帶來的偏差。
- 產生錯覺：模型會以為資料很集中、很穩定。
- 後果：**它會嚴重低估風險（標準誤 SE 算得太小）。**
- 不良影響：它會把明明是雜訊的波動，誤認為是重要的訊號。
- 舉個情境：
  - 分析結果會告訴你：這個變數超顯著，$\text{p-value} < 0.05$！
  - **實際上根本不顯著，只是因為模型太有自信（誤差抓太窄），所以誤判了。**

**這個小節要告訴你的事情**

- 診斷：怎麼看穿模型是不是在「自我感覺良好」？透過檢查 Deviance。
- 治療：怎麼幫模型「打預防針」，讓它謙虛一點，把低估的風險校正回來？透過 Quasi-likelihood 方法論。

**這回答什麼行銷/商業問題**：**行銷資料幾乎注定有 overdispersion**——同一個廣告組內的使用者互相影響（社群擴散）、同一分眾內個體轉換機率其實天差地遠（重度 vs 輕度用戶）、模型永遠漏了變數（競品活動、季節）。**不校正就等於系統性地宣稱「這個渠道顯著有效」，其實只是誤差抓太窄。**

#### 【材料原文】額外的「超出二項分配」的變異（Extra-Binomial Variation）

要記得：一個標準的二項計數（Binomial Count）是由許多個「獨立（Independent）且成功機率相同（Identical $\pi$）」的二元反應相加而成的。

**如果發生以下任一情況，反應次數的分配就不再是真正的 Binomial：**

- **不獨立**：這些二元試驗其實有牽連。例如：傳染病擴散、或是受試者互相討論。
- **機率不同**：雖然都在同一組，但每個個體的成功機率 $\pi$ 其實不一樣。例如：體質差異。
- **模型不足**：在建立 $\pi$ 的模型時，漏掉了重要的解釋變數，導致變異跑到殘差裡去了。
- 這些「模型不夠好」所造成的情況，統稱為
  - Overdispersion（超額變異）
  - Extra-binomial Variation（額外二項變異）。

#### ★★【材料原文】若發生 Overdispersion 會如何？

若「實際的反應變異數 $>$ 理論上的二項變異數」，模型就會產生以下連鎖反應：

- **係數估計（$\hat{\beta}$）**
  - 估計出來的迴歸係數本身通常**不會有嚴重的偏誤（Not seriously biased）**。
  - 也就是說，趨勢的方向（正相關 / 負相關）大致還是對的。
- **標準誤（SE）**
  - 係數的標準誤（Standard Error）會**被嚴重低估**。
  - 模型會誤以為自己算得很準。
- **統計推論**：
  - 產生過度自信的結論。
  - 因為 SE 變小了，導致計算出來的統計量（$z = \frac{\hat{\beta}}{SE}$）虛胖變大。
  - $\longrightarrow$ $\text{p-value}$ 變得太小。
  - $\longrightarrow$ 信賴區間變得太窄。
  - 結果：
    - 模型解讀過度樂觀，很容易把根本不顯著的變數，誤判為顯著影響。
    - **型一錯誤增加。**

> **實務上，寧可假設有 Overdispersion，去檢查與修正，也不要完全忽略它的可能性。**

#### ★★★【材料原文】如何檢查是否存在超額變異？三個主要步驟

> 只要這三個問題中有任一個答案偏向「是」，分析者在使用「標準二項模型」時就應該保持謹慎。

**步驟 1：先用「研究設計與情境」思考——這類反應是否合理地可能存在 extra-binomial variation？**

如何判斷 Overdispersion 是否有可能存在，可以由以下幾個關於資料來源的問題出發：

- **獨立性存疑？**
  - 每一個 Count（計數）裡面聚合的那些二元反應，是否其實不太可能獨立？
  - 例如：同一窩老鼠的實驗結果、同一家人的傳染病狀態，彼此肯定有牽連。
- **機率不同質？**
  - 對於「解釋變數 $\mathrm{X}$ 完全相同」的觀測單元，它們的真實成功機率 $\pi$ 是否很可能其實不一樣？
  - 例如：雖然都是大三男生，但有些是運動員、有些是書生，體能上完全不同。
- **模型太簡陋？**
  - 目前對 $\pi$ 的模型，是不是過於 Naive（天真）、過於簡化？
  - 例如：只放了一個變數，但明顯漏掉了其他重要的關鍵因素。

**步驟 2：配適一個「比較完整（rich）」的模型之後，檢查 deviance 適合度檢定的結果。**

- 這是最強力的數據證據，我們直接檢查 Deviance 統計量是否大得不合理。

檢查 Goodness-of-Fit 檢定（配適度檢定）應考慮的事情：

- 判讀邏輯：
  - 如果 Deviance 適合度檢定的統計量非常大，將導致 $\text{p-value}$ 很小。
    - 代表以目前的解釋變數組合而言，資料不支持這個 Binomial 模型。
- 排除法：
  - 若已經「反覆檢查並確定解釋變數集合是合理的」，該放的都放了，但 Deviance 還是很大，這時候就很可能是「超額變異 (Overdispersion)」在搞事了。
- 因此實務上通常建議：
  - **先跑 Rich Model**：
    - 在分析的早期階段，應該先配適一個「比較豐富的模型」，把所有可能重要的項（主效果、交互作用等）都暫時放進來。
  - **目的**：
    - 先盡全力解釋變異。
    - 如果連「詳細版模型」的 Deviance 都仍然偏大，那就可以更有信心地說：「不是變數不夠，而是真的有 Overdispersion！」

**步驟 3：檢查殘差，尤其是 deviance residuals——看看 Deviance 變大，是不是其實只被一兩個極端值主導，而不是整體 Overdispersion。**

- 原理：因為 Deviance 統計量本質上就是「各筆 Deviance 殘差的平方和」。
- 執行過程：
  - 直接檢查 Deviance Residuals。
  - 這可以幫助我們判斷：是不是只有「少數幾筆非常極端的觀測值」在撐高整體的 Deviance？
- 判斷方式：
  - 如果發現 Deviance 變大主要是由一兩個 Outliers 造成的，應該先處理 Outliers 的問題，而不是直接把整個情況歸因於超額變異，例如：
    - 檢查資料是否登錄錯誤。
    - 移除極端值。
  - 如果殘差普遍都偏大，沒有明顯的單一極端值，就代表真的存在超額變異 。

### 3.9 存在超額變異時的邏輯斯迴歸：準概似法（Quasi-likelihood）

#### 【材料原文】準概似法（Quasi-likelihood Approach）

當我們確認資料有 Overdispersion 時，我們不需要把整個二項式模型丟掉，而是使用「準概似法」來進行修正。

這個方法的優點是：

- **不需要把反應變數的分配完全具體寫出來。**
- **只需要指定它的「平均數」與「變異數」形式即可。**

**如何進行修正？**

- 在「二項分配 $＋$ 超額變異」情境下：
  - 我們讓「平均數」與「連結函數」保持不變，延續 Binomial 模型的結構。
  - 在變異數前面多乘了一個離散係數（Dispersion parameter）。
- 離散係數 $\psi$（Dispersion Parameter）：
  - 若 $\psi > 1$，代表實際變異大於理論上在二項分配下的變異數。
  - 注意：
    - **$\psi$ 本身不是一個變異數。**
    - 而是一個「相對於 Binomial variation 的乘數（Multiplier）」。

#### ★【材料原文】Quasi-likelihood 形式下的數學結構（Model Structure）

以包含兩個解釋變數的情況為例：

- 反應變數條件期望值：

$$\mu_i = E(Y_i \mid X_{1i}, X_{2i}) = m_i \pi_i$$

  - 這跟標準模型一模一樣。
- Logistic link（跟一般邏輯斯迴歸一樣）：

$$\text{logit}(\pi_i)
= \log\left(\frac{\pi_i}{1-\pi_i}\right)
= \beta_0 + \beta_1 X_{1i} + \beta_2 X_{2i}$$

  - 這也跟標準模型一模一樣，代表預測的趨勢線不變。
- 變異數結構：

$$\operatorname{Var}(Y_i \mid X_{1i}, X_{2i})
= \psi \, m_i \pi_i(1 - \pi_i)$$

  - **這裡不一樣！**
  - 跟 standard binomial 比起來，唯一的差別就是前面多了一個「$\psi$ 倍」。

#### ★★【材料原文】準概似推論（Quasi-Likelihood Inference）

**核心思路：維持估計，調整誤差**

- 參數估計值（$\hat{\beta}$）：
  - 準概似法被設計得很巧妙，**它的參數估計值跟標準 Binomial Logistic Regression 的 MLE 是一模一樣的。**
- 標準誤（SE）：
  - **唯一的差別在於：標準誤會被放大。**
- 白話來說：
  - 這相當於：維持原本的預測趨勢（估計值），但是把信心水準調得保守一點（SE 變大）。
  - 某種程度上，就是承認我們對資料的掌握度沒有原本以為的那麼高。

**關鍵參數：離散係數估計量（$\hat{\psi}$）**

- 我們需要一個數值來告訴我們「標準誤該放大多少倍」。
- 估計量：我們使用 Pearson $\chi^2$ 或 Deviance 統計量除以自由度來進行估計：

$$\hat{\psi} = \frac{\text{Deviance}}{\text{degrees of freedom}}$$

- 判讀方式：
  - 若 $\hat{\psi} \approx 1$：資料符合 Binomial 模型，沒有超額變異。
  - 若 $\hat{\psi} > 1$：資料的實際變異 > Binomial 預期變異，存在超額變異。

**推論方法的調整**

有了 $\hat{\psi}$ 之後，我們就可以修正推論：

- **基於漸近常態性的推論（Standard Normality）**
  - 方法：仍然可以使用原本的 Z-test 形式：$\text{Estimate} \pm Z_{\alpha/2} \times \text{Adjusted SE}$
  - 前提：適用於整體樣本數 $n$ 夠大，且二項分母 $m_i$ 也夠大的情況 。
- **使用 t 分配的推論：**
  - 現象：有些統計學家（以及 R 的 `quasibinomial` 預設）偏好將檢定統計量與自由度為 $n-p$ 的 t 分配比較。
  - 原因：
    - 雖然理論上 GLM 是大樣本性質（Z），但因為我們這裡「估計」了一個未知的離散參數 $\hat{\psi}$，使用了 $n-p$ 個自由度。
    - 這跟一般線性迴歸（OLS）中我們要估計未知變異數 $\sigma^2$ 的情況非常相似。
  - 結論：使用 t-test 雖然沒有完美的理論保證，但在實務上是比較保守且合理的作法。

**★ 舉個簡單的例子：**

- 調整公式：

$$\text{Adjusted SE} \approx \text{Original SE} \times \sqrt{\hat{\psi}}$$

- 說明：
  - 如果原先算出來 $\hat{\psi} = 4$，超額變異很嚴重。
  - 調整後標準誤就會變成原本的 $\sqrt{4} = 2$ 倍。
- 結果：
  - $\text{t-value}$ 會直接除以 2。
  - 原本顯著的變數，例如 $\text{t-value}=3$，修正後變成 $\text{t-value}=1.5$，可能就不顯著了。
  - **這就是為什麼我們說這個方法能避免「過度自信」。**

#### ★★【材料原文】Drop-in-Deviance F-Tests

當超額變異存在，也就是 $\psi > 1$ 時，**標準的卡方檢定（LRT）會太樂觀。**

**為什麼要看 F-stat？**

- 我們仍然關心同一個問題：「加入某些變數後，模型 Deviance 有沒有明顯下降？」。
- 在有超額變異、且透過 $\hat{\psi}$ 做調整的情況下，卡方分配已經不準了。
- 因此我們改用 F-test 來做檢定。

**F-statistic 的建構**

我們將 Full model 與 Reduced model 之間的 Deviance 差距視為一種 Sum of Squares（SS），建立出一個 F-statistic：

$$\text{F-stat} = \frac{\frac{\text{Drop in Deviance}}{d}}{\hat{\psi}}$$

- 分子（訊號）：
  - Drop in Deviance：Deviance 減少量，代表了模型進步了多少。
  - $d$：代表參數數目差 $n_{full} - n_{reduced}$ 。也就是多放了幾個變數進去 。
  - 白話解釋：平均每個新變數帶來了多少 Deviance 的下降。
- 分母（雜訊）
  - $\hat{\psi}$：估計出來的離散係數，**來自 Full model**。
  - 用途：用來進行「標準化」。把原本虛胖的 Deviance Drop 除以 $\hat{\psi}$，還原真實的進步幅度。
- 檢定方法：將算出來的 F-stat 與 F 分配進行比較 。
- 一些解釋：
  - 這個做法在理論上其實沒有完全嚴謹的「數學定理」背書（不像 OLS 那樣完美導出 F 分配）。
  - 但因為它在直覺與形式上，跟一般線性迴歸（Ordinary Linear Regression）的 F-test 非常類似：
    - 在 OLS 中，分母是 MSE（誤差變異）。
    - 在這裡，分母是 $\hat{\psi}$（超額變異）。
  - 因此實務上，這被認為是合理可用的近似方法（Sensible Approach）。

#### ★【材料原文】Case：iPhone 的 Overdispersion 完整 R 流程

我們想知道除了 `fb` 之外，`gender` 是否也影響使用 iPhone 的機率。但我們懷疑資料可能有 Overdispersion，所以我們要先檢查並計算 $\hat{\psi}$。

讀取資料並建立兩個模型：

```r
survey.s <- read.csv("survey_sum.csv")

attach(survey.s)

iphone.lg1 <- glm(cbind(iphone, notiphone) ~ fb, family=binomial)
iphone.lg2 <- glm(cbind(iphone, notiphone) ~ fb + gender, family=binomial)
```

計算兩個模型的離散係數並以準概似法重新 summary：

```r
# 計算模型 1 的離散係數 (psi1)
( psi1 <- deviance(iphone.lg1)/df.residual(iphone.lg1) ) 
# 假設結果是 1.346 (大於 1，代表有輕微超額變異)

# 使用準概似法更新 Summary
summary(iphone.lg1, dispersion=psi1) 
# 注意：這裡的 SE 會變大，z-value 變小，p-value 變大 (更保守)
```

```r
# 計算模型 2 (Full Model) 的離散係數 (psi2)
( psi2 <- deviance(iphone.lg2)/df.residual(iphone.lg2) ) 
# 假設結果是 1.011 (接近 1，代表加了性別後變異有被解釋掉一些)

summary(iphone.lg2, dispersion=psi2)
```

- `deviance(...) / df.residual(...)`：這個就是我們講義公式 $\hat{\psi} = \frac{\text{Deviance}}{df}$ 的實作 。
- `summary(..., dispersion=psi)`：
  - 一般 `summary` 預設 `dispersion=1`。
  - 當你手動指定 `dispersion` 後，R 會自動幫你把標準誤放大 $\sqrt{\psi}$ 倍，重新計算 $\text{z-value}$ 和 $\text{p-value}$。這就是我們說的「保守一點的推論」。

處理超額變異的模型比較（F-test）：

- 想比較 `iphone.lg1`（只有 fb）和 `iphone.lg2`（加了 gender），看看 `gender` 是否顯著。
- **因為有 Overdispersion，不能用卡方檢定（LRT），要改用 F-test。**

```r
#### Inference with Overdispersion: F-statistic 

##  計算訊號 (Drop in Deviance / d)
( drop <- deviance(iphone.lg1) - deviance(iphone.lg2) )  
# Deviance 減少量

( ddf <- df.residual(iphone.lg1) - df.residual(iphone.lg2) ) 
# 自由度差 (這裡是 1)

##  計算 F 統計量 (標準化)
( fstat <- (drop/ddf)/psi2 )  
# 關鍵！分母要除以 Full Model 的 psi
# fstat = (Deviance Drop / 1) / 1.011

##  計算 p-value (查 F 分配表)
1 - pf(fstat, ddf, df.residual(iphone.lg2))
```

- **`(drop/ddf) / psi2`**：對應講義的 F-stat 公式 。
- **`pf(...)`**：查 F 分配的累積機率，算出 $\text{p-value}$。

【評註】材料用的是 `summary(model, dispersion=psi)` 手動指定；R 另有 `family=quasibinomial` 可一次完成（$\hat\beta$ 相同、SE 自動放大、報表改用 t 值）。兩條路等價，材料選手動是為了讓 $\hat\psi$ 的來源可見。

#### ★★【材料原文】Overdispersion 結論

- Overdispersion 是在配適邏輯斯迴歸或其他 binomial 型 GLM 時必須認真考慮的議題。
- 老師建議了三項檢查步驟與注意事項：
  - **先用研究設計與經驗判斷：**
    - 研究設計是否存在「群聚」導致不獨立？
    - 受試者之間是否存在異質性，$\pi$ 其實不同？
    - 模型是否太陽春，漏了重要變數？
  - **再看「數據」佐證：**
    - 在配適「足夠豐富的模型（Rich Model）」後，檢查 Deviance 適合度檢定。
  - **排除「極端值」：**
    - 檢查殘差，釐清 deviance 偏大是來自 outliers 還是整體超額變異。
- 準概似法（Quasi-likelihood Approach）
  - 導入離散係數（Dispersion parameter）$\psi$，並提出 Quasi-likelihood approach：
    - 估計值（$\hat{\beta}$）：維持不變，趨勢線不動。
    - 標準誤（SE）：依據 $\hat{\psi}$ 進行調整，通常會變大。
    - 推論結果：檢定與信賴區間跟著被修正得更保守、更誠實。
- 準概似推論可以在 R 中透過一些延伸的程式碼來實作：
  - 計算 $\hat{\psi}$：利用公式 `deviance(model) / df.residual(model)` 算出估計值。
  - 更新 Summary：使用 `summary(model, dispersion = psi)`。R 會自動幫你把標準誤放大，算出修正後的 $\text{p-value}$。
  - 執行 F-test：若要比較模型，不能直接用卡方。要使用調整後的 Deviance Drop 建立 F 檢定統計量。

---

<a id="part-4"></a>
## Part 4 — 1202：Poisson / Log-Linear Model 與 MLR vs GLM 總對照

### 4.1 卜松分配（Poisson distribution）— 回顧初統

#### 【材料原文】卜松過程（Poisson process）

一個卜松過程（Poisson process）滿足下列假定：

1. 事件發生的機率與區間的長度有關，而與區間的起點無關。
2. 在不同的區間內發生一次或二次以上偶發事件的機率近乎零。
3. 在不重疊的區間內，發生事件的次數互相獨立。
4. 單位時間發生偶發事件的期望次數與區間的長度成正比（比例伸縮性）。

指數函數之 Maclaurin 級數展開：

$$e^{x}=1+\frac{x}{1!}+\frac{x^{2}}{2!}+\frac{x^{3}}{3!}+\cdots=\sum_{i=0}^{\infty}\frac{x^{i}}{i!}$$

#### 【材料原文】卜松分配的數學定義

1. 在單位時間（或單位線段、單位平面、單位空間等）內部，連續地操作 Poisson 過程，定義隨機變數 $X$ 表示其中特定偶發事件（rare event）發生的次數。
2. 值域：$R_X=\{0,1,2,\ldots\,\infty \}$
3. 定義母數：$\lambda$ ，單位時間內，偶發事件發生之期望次數；$\lambda>0$
4. 機率質量函數：$X\sim Poi(\lambda)$

$$f_X(x)=\frac{e^{-\lambda}\lambda^{x}}{x!},\quad x=0,1,\ldots,\infty
\qquad
\sum_{x=0}^{\infty}\frac{e^{-\lambda}\lambda^{x}}{x!}=1$$

5. $E(X)=\lambda,\quad Var(X)=\lambda,\quad M_X(t)=e^{\lambda(e^{t}-1)}$

證（材料原文，可略）：

- $E(X)=\sum_{x=1}^{\infty}x\frac{e^{-\lambda}\lambda^{x}}{x!}=e^{-\lambda}\sum_{y=0}^{\infty}\frac{\lambda^{y+1}}{y!}=\lambda$
- $Var(X)=E(X^{2})-[E(X)]^{2}=E[(X-1)X]+E(X)-[E(X)]^{2}=\lambda^{2}+\lambda-\lambda^{2}=\lambda$
- $M_X(t)=E(e^{tX})=\sum_{x=0}^{\infty}\frac{e^{tx}e^{-\lambda}\lambda^{x}}{x!}=e^{-\lambda}\sum_{x=0}^{\infty}\frac{(\lambda e^{t})^{x}}{x!}=e^{\lambda(e^{t}-1)}$

其他數學性質（材料原文，可略）：

- Poisson 分配之可加性（再生性）：設 $X\sim \text{Poi}(\lambda_{1}),\ Y\sim \text{Poi}(\lambda_{2})$ 且 $X\perp\!\!\!\perp Y$，則 $U=X+Y\sim \text{Poi}(\lambda_{1}+\lambda_{2})$。
  - 證：$M_U(t)=M_X(t)M_Y(t)=e^{\lambda_{1}(e^{t}-1)}e^{\lambda_{2}(e^{t}-1)}=e^{(\lambda_{1}+\lambda_{2})}$，由 mgf 唯一性可知。
- 用 Poisson 分配計算二項式分配之近似值：當 $n\to\infty,\ p\to 0,\ np\to\lambda$ 時，$B(n,p)\xrightarrow{d}\operatorname{Poi}(\lambda)$

### 4.2 【材料原文】Poisson 機率分配在此處的意義（投影片內容）

- 在前述個案中，反應變數是「計數」（每月網購次數）。
  - 在特定時間區間或特定空間範圍內，事件或物件的計數，與前面二項分配的「成功次數」不同。
- Poisson 機率分配：
  - 可以視為「在試驗次數很大」且「單次成功機率很小」的二項分配極限近似。
  - 若 $\mathrm{Y}$ 表示事件次數，其機率為

$$\Pr(Y = y) = \frac{e^{(-\mu)}\,\mu^y}{y!},\quad y = 0,1,2,\ldots$$

    - 其中 $\mu$ 是該 Poisson 分布的平均數，**也是變異數**。

**Poisson 分配最適合用來描述：**

- 在時間或空間中「隨機且稀有」事件的計數。
- 特性：
  - $\mathrm{Var(X)}$ 等於 $\mu$。
  - 分配通常向右偏（skew to the right）。
  - 當 $\mu$ 變大，偏態會降低。
  - 當 $\mu$ 很大時，Poisson 分配可以被常態分配良好近似。

### 4.3 ★【材料原文】核心：從「比例」到「計數」

- 前一節（Binomial）：我們關心的是「成功次數 / 總嘗試次數（$n$）」。
  - 例如：10 個人裡面有幾個買 iPhone。這裡有一個明確的天花板（$n$）。
- 此章節（Poisson）：我們關心的是「每月網購次數」。
  - 這種資料是在特定時間或空間內發生的次數。
  - **關鍵差異：它沒有固定的天花板（理論上可以買無限多次），且我們不知道「沒買的次數」是多少。**

【評註】**這一句是 binomial vs poisson 的唯一判準**：有沒有一個已知的分母（試驗次數）。有 → binomial；沒有 → poisson。行銷上：「500 次曝光中 30 次點擊」→ binomial；「這個月下單 3 次」→ poisson。

### 4.4 ★★【材料原文】Log-Linear Model（對數線性模型）

**模型設定：**

- 設反應變數 $\mathrm{Y}$ 服從 Poisson 分配，且其平均數 $\mu$ 與解釋變數 $X_1$ 有關。
- 連結函數（Link Function）：使用 Log。

$$\log(\mu) = \beta_0 + \beta_1 X_1$$

- 還原回平均數：

$$\mu = \exp(\beta_0 + \beta_1 X_1) = e^{\beta_0} \cdot e^{\beta_1 X_1}$$

**為什麼要取 Log？**

- 避免預測出負數：
  - 如果你直接用 $\mu = \beta_0 + \beta_1 X$（線性），當 $X$ 很小時，算出來的購買次數可能是負的（例如 -3 次）。這在物理上是不可能的。
  - 取了 $\log(\mu)$ 之後，等號左邊可以是負無窮大，代表 $\mu$ 無限接近 0，卻可以使 $\mu$ 本身永遠保持正數。

**指數成長（Exponential Growth）：**

- 注意公式：$\mu = e^{\beta_0 + \beta_1 X_1}$
- **這代表 $X_1$ 每增加 1 單位，平均次數 $\mu$ 不是「增加」一個固定量，而是「乘上」一個倍數（$e^{\beta_1}$）。**
- 結論：Log-Linear 模型描述的是一種爆發式（或衰退式）的非線性關係，而不是平緩的直線。

**變異數的連鎖反應：**

- 因為 Poisson 的特性是 $\text{Var} = \text{Mean} = \mu$。
- 所以當你的預測值（$\mu$）越大，例如網購大戶，他的行為波動，也就是 $\text{Var}$ 會自動變得越大。
- 這跟一般線性迴歸假設「波動固定」完全不同。

投影片範例（材料原文）：

- 假設反應變數 $\mathrm{Y}$ 的分布，在給定單一解釋變數 $\mathrm{X}_1$ 下是 Poisson。
- 令 $\mu = \mu\{Y \mid X_1\}$ 表示條件平均數，則 log-linear model 為 $\log(\mu) = -1.7 + 0.20 \mathrm{X}_1$
- 注意：
  - 迴歸在 $\mathrm{X}_1$ 上是「非線性」的，因為 $\mu\{Y\mid X_1\} = e^{(-1.7 + 0.20 X_1)}$ 對 $\mathrm{X}_1$ 是指數型增加。
  - 因為 Poisson 分配的特性，平均數越大時，對應的變異數也就越大。

**這回答什麼行銷/商業問題**：「每多帶 100 元現金 / 每多接觸一次廣告，這個顧客一個月的下單次數會變成幾倍？」——**logit 講勝算倍數，log 講次數倍數**。兩者的商業語言都是「乘上 $e^{\hat\beta}$ 倍」，這使得 GLM 報告的句型高度一致。

### 4.5 Poisson 的模型評估

#### 【材料原文】散佈圖檢查（Scatterplot）

- **操作**：畫出計數 $\mathrm{Y}$（例如網購次數）對解釋變數 $\mathrm{X}$（例如現金 Cash）的散佈圖。
- **目的**：
  - 用肉眼觀察是否存在明顯的趨勢模式。
  - 檢查是否符合我們假設的非線性關係（例如指數成長）。

#### 【材料原文】殘差檢查（Poisson 版公式）

**Deviance 殘差（Deviance Residuals）**

- 定義：基於 Log-Likelihood 的貢獻度計算出的殘差。

$$D.\text{res}_i = \operatorname{sign}(Y_i - \hat{\mu}_i) \sqrt{2\Big[ Y_i \log\Big(\frac{Y_i}{\hat{\mu}_i}\Big) - (Y_i - \hat{\mu}_i) \Big]}$$

- 註：當 $Y_i=0$ 時，第一項定為 0 。

**Pearson 殘差（Pearson Residuals）**

- 定義：標準化的誤差。

$$P.\text{res}_i = \frac{Y_i - \hat{\mu}_i}{\sqrt{\hat{\mu}_i}}$$

- 白話解釋：
  - 分子是「觀測值 - 期望值」。
  - 分母為什麼是 $\sqrt{\hat{\mu}_i}$？
    - Poisson 的特性是 $\text{Var}=\text{mean}=\mu$。
    - 所以 $\text{SD} = \sqrt{\mu}$。
  - 這其實就是 Z-score 的概念！

#### ★【材料原文】診斷標準與限制

- 大樣本性質：
  - 若 Poisson 平均數夠大（$\hat{\mu} > 5$）且模型合理，這兩種殘差的分佈都會接近標準常態。
- **小樣本陷阱：**
  - 若平均數偏小（$\hat{\mu} < 5$），也就是事件很罕見，殘差分佈會嚴重偏離常態。
  - **這時候看 Q-Q Plot 會覺得模型很爛，但其實只是因為資料太稀疏，這是正常現象，沒必要誤殺模型。**

**實務檢查方式：**

- 畫 Residuals vs. Fitted Plot：
  - 檢查是否有系統性 Pattern。
    - 例如：特別大的喇叭狀開口，暗示變異數不對。
    - **注意，Poisson 分配本來就會隨著平均變大而使變異變大，因此本身圖形就會呈現喇叭狀。**
- 畫 Q-Q Plot：檢查是否有極端 Outliers。

#### 【材料原文】Deviance 適合度檢定（Poisson 版）

- $\mathrm{H}_0$：所選的 Log-Linear GLM 是合適的。
- 統計量：
  - Likelihood-ratio：$G^2$，即 Deviance 統計量，殘差平方和。
  - Pearson statistic：$X^2$
- 判讀：兩者都可透過卡方分配 $\chi^2_{n-p}$ 來檢定。
- 如果 $\text{p-value}$ 很小，即檢定失敗，代表模型配適不良，通常是以下三種原因：
  - **平均數模型錯誤**：解釋變數選錯了，或是可能需要加平方項 / 交互作用項。
  - **異常值（Outliers）**：有幾個買東西買到瘋掉的極端值扭曲了整體 Deviance。
  - **分配錯誤（Distribution Issue）**：
    - 超額卜松變異（Extra-Poisson Variation），**這是最常見的。**
      - 正常的 Poisson 會是喇叭狀開口的圖形，但若存在超額變異，那個喇叭開口就會開得特別大，特別浮誇。
    - 也就是變異數比 $\mu$ 還大很多。

**★ 實務上而言（材料原文）：**

- 檢定力的限制：
  - **講義有特別提到，其實在 Log-Linear 模型中，Deviance 檢定本身對模型不適合的偵測能力並不是很強。**
  - 此時不能只看 $\text{p-value}$ 就下定論。
  - **必須搭配殘差圖與個別係數檢定一起看。**
- 指標選擇：
  - 雖然理論上 $G^2$（Deviance）比較好，但 Pearson $X^2$ 因為歷史悠久、在列聯表分析很好用，所以實務上還是很常看它。

### 4.6 Poisson 的模型推論

#### 【材料原文】Wald 檢定與信賴區間

- 適用情境：想快速檢查「單一變數 $\mathrm{X}$」是否顯著影響 $\mathrm{Y}$。
- 理論基礎：
  - Log-linear 模型的係數是透過最大概似法（MLE）求得的 。
  - 大樣本性質：若樣本數 $n$ 足夠大，或 Poisson 平均數 $\mu$ 足夠大，這些係數估計值的抽樣分配可以近似看成常態分配。
- 操作方式：
  - 直接看 R `summary()` 報表中的 `z value` 和 `Pr(>|z|)`。
  - 也可以計算對應的信賴區間（Confidence Interval）。如果區間不包含 0，代表顯著。

#### 【材料原文】概似比／Drop-in-Deviance 檢定（LRT）

- 適用情境：這是一個更嚴謹的方法，特別是用來比較兩個模型。例如：想確認「加入一整組變數」是否有幫助。
- 比較對象：
  - 完整模型（Full Model）：變數比較多、配適度通常較好、但較複雜。
  - 簡化模型（Reduced Model）：變數比較少、是 Full 的子集、模型結構較簡單。
- 檢定 $\mathrm{H}_0$：那些多出來的變數係數都是 0。$\mathrm{H}_0:$ 不需要那些變數，簡化模型就夠好了。
- 檢定統計量：

$$\text{Drop} = \text{Deviance}_{\text{reduced}} - \text{Deviance}_{\text{full}}$$

- **白話解釋：其實就是 GLM 版的 ANOVA**
  - 在以前的線性迴歸（OLS）中，我們看的是解釋了多少變異（Sum of Squares, SS）。
  - 在 GLM 中，Deviance 的下降量（Drop）就是「兩模型之間額外的剩餘平方和」。
  - 意義：這個 Drop 代表了 Full Model 比 Reduced Model 多解釋了多少資訊。
  - 判讀：如果 Drop 很大，超過卡方分佈的臨界值，代表這組變數很有貢獻，不能丟掉！

#### ★【材料原文】總結：推論流程

- **先看 Wald**：做初步篩選，看看誰是顯著的關鍵變數。
- **再做 LRT（ANOVA）**：如果你想移除某個變數，或是想確認某個變數是否真的不可或缺，需跑一次 LRT。這是更穩健的確認方式。

### 4.7 超額 Poisson 變異（Extra-Poisson Variation）

> 【材料原文】前面在 Binomial 章節學過這個概念，現在換到 Poisson，**邏輯其實完全一樣，只是衡量基準變了。**

#### 【材料原文】核心問題：變異數失控

- Poisson 的公設：標準 Poisson 模型假設 Mean = Variance = $\mu$。
- 現實狀況：有些「未被測量的效果」可能會讓反應變數的波動，比 Poisson 預測的還要大。
- 定義：當實際變異 $>$ 平均數時，我們稱之為 Extra-Poisson Variation。

#### 【材料原文】硬跑模型的代價

若在存在 Extra-Poisson variation 的情況下，仍硬用標準 Poisson log-linear 模型，會有以下三個大問題：

- 係數估計值（$\hat{\beta}$）：仍然大致不偏（Unbiased）。代表趨勢線沒畫錯。
- 標準誤（SE）：**會被嚴重低估**。以為自己很準。
- 檢定結果：$\text{p-value}$ 會比真正合理的值還要小。導致檢定結果呈現過度樂觀（Overly Optimistic）。

#### 【材料原文】解方：準概似法（Quasi-Likelihood Approach）

我們不需要換一個全新的複雜模型，只需要對原本的模型做一點「擴充」。

**模型設定**

- 核心概念：只需要指定反應變數的「平均數」與「變異數」形式，不必完整寫出整個機率分布。
- Log-Linear with Overdispersion：我們維持 Poisson 式的平均數結構，但允許變異數前面多一個離散參數（$\psi$）。

$$\begin{aligned}
&\mu_i = E(Y_i \mid X_{i}) \\
&\operatorname{Var}(Y_i \mid X_{i}) = \psi \times \mu_i \\
&\log(\mu_i) = \beta_0 + \beta_1 X_{1i} + \dots
\end{aligned}$$

- 離散參數 $\psi$（Dispersion Parameter）
  - $\psi = 1$：標準 Poisson 模型成立，也就是無超額變異。
  - $\psi > 1$：存在超額變異。代表實際變異是 Poisson 預期值的 $\psi$ 倍。

#### ★【材料原文】檢查超額變異（Checking for Overdispersion）— 四個方向

- **常識判斷**：這類計數資料是否合理地可能有額外變異？例如：是否有群聚效應？
- **數據檢驗**：比較「同一組 $X$」下的樣本變異數與樣本平均數。**若 $S^2 \gg \bar{X}$，可能有內鬼。**
- **Rich Model 測試**：配適一個「足夠豐富的模型」，檢查 Deviance 適合度檢定。如果 $\text{p-value}$ 還是很小，大概就是 Overdispersion 了。
- **殘差檢查**：看看 Deviance 偏大是否主要來自少數 Outliers。

【評註】Poisson 版比 Binomial 版多了一個**現成的快篩**：直接比 `mean(Y)` 與 `var(Y)`。Binomial 沒有這麼便宜的檢查（因為 $m_i$ 不同），只能靠 $\hat\psi = \text{Dev}/df$。

#### 【材料原文】超額變異的統計推論（Inference with Overdispersion）

一旦確認 $\psi > 1$，我們就要動手修正：

1. **估計 $\psi$**：使用 Deviance 統計量除以自由度：

$$\hat{\psi} = \frac{G^2}{n - p}$$

2. **校正標準誤（SE）**：

$$\text{Quasi SE} = \text{MLE SE} \times \sqrt{\hat{\psi}}$$

   - 這個步驟，通常可以由軟體自動完成。
3. **係數檢定（t-test）**：以調整後的 SE 為基礎，對係數做檢定或建構信賴區間。注意：此時參考的是 t 分配，自由度為 $n-p$。
4. **模型比較（F-test）**：如果要比較 Full vs. Reduced 模型，不能用卡方，要改用 F 統計量：

$$\text{F-stat} = \frac{\frac{\text{Drop in Deviance}}{d}}{\hat{\psi}}$$

#### ★★【材料原文】白話總結 Binomial vs. Poisson 的超額變異

- **Binomial**：變異數應該要是 $n\pi(1-\pi)$。如果超過，就是存在 Overdispersion。
- **Poisson**：變異數應該是 $\mu$。如果超過，就是存在 Overdispersion。
- **處理方法：完全一樣！**
  - 算出 $\hat{\psi}$，把 SE 放大，把檢定變保守。
  - **這就是 GLM 處理這類問題的統一處理思路。**

### 4.8 CASE: Online Shopping（Poisson 完整 R 流程）

#### 【材料原文】資料集

這個個案資料來自修習統計課同學的問卷調查（與 1125 同一份資料）：

- **student**：身分（undergrad / grad）
- **grade**：目前就讀年級（B1…B5, R1…R3, D）
- **gender**：性別（F 或 M）
- **fb**：平均 Facebook 好友人數
- **cash**：平常身上大約會帶多少現金
- **shopping**：每個月網路購物的平均次數
- **iphone**：手機是否為 iPhone（Yes / No）
- **mac**：電腦是否為 Mac（Yes / No）

研究問題：想探討每月網路購物次數（shopping），與其他變數之間是否存在關聯。

#### 【材料原文】讀資料

```r
survey <- read.csv("survey.csv")
head(survey[,c(4,6)],10)

attach(survey)
```

#### ★【材料原文】EDA：檢查資料是否有 Poisson 的特徵

```r
## EDA: shopping
table(shopping)
barplot(table(shopping), xlab="Shopping times", ylab="Frequency", col="lightblue")

mean(survey$shopping);var(survey$shopping)
```

- $\text{mean}=1.643103$
- $\text{variance}=2.001939$
- 一些解釋：
  - 會看到一個明顯右偏的圖形。
  - 大部分人網購次數是 0 或 1，很少人買很多次。
  - 這就很符合 Poisson 的特徵。
  - $\text{mean}=1.643103<2.001939=\text{variance}$
    - **這暗示資料可能有 Overdispersion。**
    - **或者我們漏了重要的解釋變數。**

#### 【材料原文】建立 Simple Model

- $\mathrm{Y}$：online shopping frequency
- $\mathrm{X}$：cash on hand

```r
## Y: online shopping frequency, X: cash on hand
glm1 <- glm(shopping ~ cash, data=survey, family=poisson)
summary(glm1)

plot(jitter(survey$cash), jitter(survey$shopping))
```

- **`glm(..., family=poisson)`**：
  - 告訴 R $\mathrm{Y}$ 是計數資料，要用 Log 連結函數。
  - 模型結果：`cash` 的係數是正的且顯著，$p < 0.001$。代表錢帶越多，網購次數越多。
- **`jitter`**：
  - 因為 $\mathrm{Y}$（次數）都是整數，直接畫散佈圖點會疊在一起。
  - `jitter` 加一點隨機擾動，讓我們看清楚數據的密度。

#### 【材料原文】模型評估 — Scatter plot

```r
## Model Assessment(1): Sactterplot
Y <- shopping; X <- cash
new <- seq(min(cash), max(cash), by=12.5)

plot(jitter(cash), jitter(shopping))
lines(new, exp(predict(glm(Y ~ X, family=poisson), newdata=data.frame(X=new))), col=2, lty=2)
```

- 這條曲線確實呈現指數成長趨勢 。

#### 【材料原文】模型評估 — Residual plot

```r
## Model Assessment(2): Residual plot
plot(fitted(glm1), residuals(glm1), xlab="Fitted Values", ylab="Deviance Residuals")
	# default: deviance residuals
abline(h = 0, lty = 2)
abline(h = c(2, -2), lty = 3, col = 4)
title("Deviance Residual Plot")
```

- 判讀：我們希望點均勻分佈在 0 上下，且大部分在 $\pm 2$ 之間。

#### 【材料原文】模型評估 — Q-Q plot

```r
qqnorm(residuals(glm1), pch=16);	qqline(residuals(glm1))
```

- 檢查殘差是否接近常態。
- 因為 Poisson 平均數偏小（1.643103），這裡的 Q-Q Plot 可能不會太漂亮，是很正常的。

#### 【材料原文】模型評估 — Goodness-of-fit

Deviance / Likelihood-Ratio：

```r
## Model Assessment(3.1): Goodness-of-fit (Deviance/Likelihood-Ratio)
( Gsq <- glm1$deviance)
1-pchisq(Gsq, df = glm1$df.residual)
# ↑ 這個是在算 p-value
```

- $\mathrm{G}^2=639.9238$
- $\text{p-value}=0.03758127$
- 一些解釋：
  - `pchisq(分數, df)` 是 R 的卡方累積機率函數（CDF）。
  - 它的意思是：在自由度為 `df` 的情況下，出現小於等於該分數的機率有多少？（也就是曲線左邊的面積）。

Pearson：

```r
## Model Assessment(3.2): Goodness-of-fit(Pearson)
glm1.res <- residuals(glm1, type="pearson")
( Xsq <- sum(glm1.res^2) )
1-pchisq(Xsq, df = glm1$df.residual)
# ↑ 這個是在算 p-value
```

- $\mathrm{X}^2=632.3772$
- $\text{p-value}=0.0580657$

#### 【材料原文】模型推論

```r
## Model Inference (1): Wald's test & C.I.
confint.default(glm1)
```

```r
## Model Inference (2): LRT / Drop-in-Deviance Test
1-pchisq(glm1$null.deviance-deviance(glm1), 1)
```

#### ★【材料原文】考慮加入更多變數

```r
## [Model 2] consider "gender, iphone or not, student(undergrad or graduate)"
glm2 <- glm(shopping ~ student + gender + iphone + cash, data=survey, family=poisson)
summary(glm2)
```

Drop-in-Deviance 檢定（LRT）：

```r
## LRT/Drop-in-Deviance test for removed some terms
anova(glm1, glm2, test="Chisq")
```

- 結果顯示 Deviance 下降了 37.136，$\text{p-value}=4.3 \times 10^{-8}$ 非常小。
- 結論：加入這組變數後，模型顯著進步，這些變數很有用 。

#### 【材料原文】對新模型進行評估

```r
## Model Assessment(2): Residual plot
plot(fitted(glm2), residuals(glm2), xlab="Fitted Values", ylab="Deviance Residuals")

abline(h = 0, lty = 2)
abline(h = c(2, -2), lty = 3, col = 4)
title("Deviance Residual Plot for glm2")
```

```r
qqnorm(residuals(glm2), pch=16);	qqline(residuals(glm2))
```

```r
# Model Assessment(3.1): Goodness-of-fitb(Deviance/Likelihood-Ratio)
( Gsq <- glm2$deviance )
1-pchisq(Gsq, glm2$df.residual)
```

- $\mathrm{G}^2=602.7875$
- $\text{p-value}=0.2043589$

```r
# Model Assessment(3.2): Goodness-of-fit(Pearson)
glm2.res <- residuals(glm2, type="pearson")
( Xsq <- sum(glm2.res^2) )
1-pchisq(Xsq, glm2$df.residual)
```

- $\mathrm{X}^2=595.2159$
- $\text{p-value}=0.2712981$

#### ★★★【材料原文】關鍵結論

- $\text{Deviance p-value} = 0.204 > 0.05$。
- 不拒絕 $\mathrm{H}_0$。
  - 代表新模型配適良好（Good Fit）。
  - **代表原先模型其實沒有存在 Overdispersion，只是因為我們遺漏了部分關鍵變數。**

【評註】**這是整份材料最有教學價值的一個轉折**：一開始 `mean < var` + GOF p = 0.038，看起來像 overdispersion；但加入 student / gender / iphone 三個變數後，GOF p 變成 0.204，問題消失。**證明了 3.8「三步驟必須按順序」的必要性——先排除系統成份錯誤（漏變數），最後才歸因隨機成份（overdispersion）。行銷分析上這代表：先把能拿到的顧客屬性都放進模型，再談要不要用 quasi 校正。**

### 4.9 ★★★【材料原文】Final Discussion – MLR vs. GLM 總對照表

| | **MLR** | **GLM** |
|---|---|---|
| **估計方法** | 最小平方法（Least Squares） | 最大概似法（Maximum Likelihood） |
| **殘差種類** | Raw residuals<br>Studentized residuals | Raw residuals<br>Deviance residuals<br>Pearson residuals |
| **模型評估** | Sum of Squared Errors (SSE) | Deviance |

| 類別 | **MLR** | **GLM** |
|---|---|---|
| **整體模型（Whole model）** | Global Usefulness F-test：<br>$\mathrm{H}_0: \text{全部 } \beta_i = 0$<br>F 統計量，**希望 p-value 小**。<br>指令：`summary()` | Deviance Goodness-of-Fit Test：<br>$\mathrm{H}_0:$ 目前這個模型適合。<br>統計量：$\mathrm{G}^2$ 或 $\mathrm{X}^2$<br>**希望 p-value 大**。<br>指令：`summary()` |
| **個別係數（Individual coefficient）** | 個別 t 檢定：<br>$\mathrm{H}_0: \beta_i = 0$<br>t 統計量，希望 p-value 小。 | Wald's test：<br>$H_0: \beta_i = 0$<br>z 統計量，希望 p-value 小。 |
| **模型比較（Nested models）** | 巢狀模型 F-test：<br>$H_0: \beta_{r+1} = \cdots = \beta_k = 0$<br>F 統計量，希望 p-value 小。<br>指令：`anova(model.R, model.C)` | Drop-in-Deviance / Likelihood Ratio Test：<br>$H_0: \beta_{r+1} = \cdots = \beta_k = 0$<br>統計量：$\chi^2$<br>希望 p-value 小。<br>指令：`anova(model.R, model.C, test="Chisq")` |

【評註】**這張表裡最容易搞錯、也最該印出來貼在螢幕旁的是「希望 p-value 大 vs 小」的方向**：GLM 的整體模型檢定（GOF）**希望 p 大**（模型沒問題），但個別係數與模型比較**希望 p 小**（變數有用）。MLR 的 Global F 是「希望 p 小」，方向剛好相反——因為兩者的 $\mathrm{H}_0$ 定義不同（MLR 的 $\mathrm{H}_0$ 是「模型沒用」，GLM GOF 的 $\mathrm{H}_0$ 是「模型夠好」）。

---

<a id="part-5"></a>
## Part 5 — 推論界線總整理（作者反覆強調的部分）

【評註】本節把散落在四頁材料裡「只能談關聯、不能談因果」與相關的推論界線，**依原文措辭逐條收攏**，並標明出處位置。這是新 Skill 最該內建的紀律章節——它決定了同一份數字能寫成什麼句子。

### 5.1 觀察型資料只能談關聯，不能談因果

| # | 出處 | 材料原文措辭（逐字） |
|---|---|---|
| A1 | 1111 · Case 3 「注意！」區塊 | 「**本分析是基於觀察型資料，僅能提供統計關聯的證據，不能直接作為因果推論。**」 |
| A2 | 1111 · Case 3 「注意！」區塊 | 「**『吸菸導致肺癌』仍需仰賴更嚴謹的研究設計與其他證據共同支持。**」 |
| A3 | 1111 · Case 3 案例敘述 | 「想知道抽菸對肺癌有沒有顯著**關聯性**。**注意這邊找的結果通常是「關聯性」。**」 |
| A4 | 1111 · Case 3 結果解讀 | 「**對於此觀察資料**，吸菸者罹患肺癌的 Odds，估計約為非吸菸者的 3.67 倍。」（先標明資料型態，再講數字） |
| A5 | 1111 · 卡方檢定假說 | $\mathrm{H}_1$ 的措辭一律是「兩者之間存在某種**關連**」「兩個變數之間存在某種**關聯**」，從不寫「造成」 |
| A6 | 1111 · 卡方檢定假說（廣告例） | 「$\mathrm{H}_1$：兩者之間存在某種關連。**看過廣告的人購買率較高或較低，只要是「關聯性」就可以算。**」（提醒卡方連方向都不指定） |
| A7 | 1111 · Odds ratio 特性 | 「混淆變數（Confounding variable）：**讓你「以為」$\mathrm{X}$ 影響 $\mathrm{Y}$，但其實是第三個因素在搞事的那個變數。**」 |
| A8 | 1118 · Case 2 背景 | 「1972～1981 年，在荷蘭海牙進行的健康調查，**發現養寵物鳥與肺癌風險增加之間存在關聯**。」 |
| A9 | 1118 · Case 2 研究問題 | 「在控制年齡、社經地位與抽菸行為之後，飼養寵物鳥是否**仍與**肺癌風險增加**有關**？」（即使控制了四個共變數，仍寫「有關」） |
| A10 | 1118 · Case 2 結果解讀 | 「顯示 BK 與肺癌之間**有強烈關聯**，即使已經把其他變數（性別、社經地位、年齡、抽菸年數）納入模型。」 |

**【評註】措辭模板（可直接搬進行銷報告）**：

- ✔ 「在控制 A、B、C 後，曝光組的購買勝算約為對照組的 X 倍（95% CI ...）」
- ✔ 「本分析基於觀察型資料，僅能提供統計關聯的證據，不能直接作為因果推論。」
- ✘ 「廣告使購買率提升 X%」「這檔活動帶來了 X 筆增量訂單」——除非是隨機分派實驗。

### 5.2 什麼設計才能談「處理效果」

| # | 出處 | 材料原文措辭 |
|---|---|---|
| B1 | 1111 · 隨機化二元實驗設計 | 「這種設計的好處是：**因為有隨機化，理論上可以平衡已知與未知的混淆變數，所以在談處理效果（treatment effect）時，比觀察性設計更有說服力。**」 |
| B2 | 1111 · 前瞻性研究 | 「優點：可以直接估計「發生機率」與「風險」。**這種設計下，比例、勝算、勝算比都可以直接解釋。**」 |
| B3 | 1111 · 回溯性研究代價 | 「**但代價是：設計上比較容易遇到選樣偏誤、回憶偏誤等問題，因此在「因果解釋」上必須更小心。**」 |

### 5.3 回溯性資料的估計界線（能算什麼、不能算什麼）

| # | 出處 | 材料原文措辭 |
|---|---|---|
| C1 | 1111 · Odds ratio 特性 | 「**Odds ratio 是唯一可用於比較回溯性研究 (retrospective study) 中兩組二元反應的參數。**」 |
| C2 | 1111 · 回溯性取樣 | 「樣本中各組的人數是我們「刻意控制」出來的（例如：硬是抓 83 個肺癌、83 個對照），**所以無法從樣本裡，直接估計「真實族群裡」吸菸者和未吸菸者罹癌的母體比例或其差異。**」 |
| C3 | 1111 · 回溯性取樣 | 「**你不能從這個樣本直接說「吸菸者罹癌率是幾 ％」、「未吸菸者罹癌率是幾 ％」，因為 case / control 的人數是研究者自己設的。**」 |
| C4 | 1111 · OR 不變性 | 「**「在肺癌病人與對照組中，吸菸者所佔的比例」並不能告訴我們「在整體吸菸者與非吸菸者族群中，肺癌患者所佔的比例」。**」 |
| C5 | 1111 · 抽樣總結比較 | 「Retrospective product binomial sampling ⋯ **只能做同質性檢驗。且只能用 odds ratio 檢驗，proportion 無法被估計。**」 |
| C6 | 1111 · 回溯性研究 | 「在這種設計裡，**樣本裡的「有病比例」是刻意設計的，不能拿來當母體機率。**」 |
| C7 | 1111 · 前瞻 product binomial | 「Prospective product binomial sampling ⋯ **只能做同質性檢驗。**」（列總和被固定，就不能談獨立性） |

**【評註】行銷版翻譯**：先撈「已購買名單 vs 未購買名單」再回頭比對觸點紀錄 = 回溯式抽樣。**這種資料算出來的「曝光組轉換率」是研究者自己設的比例，不是真實轉換率；只有 OR 是可信的。**

### 5.4 「變數被移除」的正確說法

| # | 出處 | 材料原文措辭 |
|---|---|---|
| D1 | 1118 · 變數選擇 | 「**注意！在任一方法中，某變數被「移除或不在模型中」，只能解讀為「在目前已納入的變數之上，該變數沒有『額外』解釋力」。**」 |
| D2 | 1118 · 變數選擇 | 「**正確說法是：在已包含的變數條件下，Parking 沒有額外貢獻或提供的額外解釋力不足。**」 |
| D3 | 1118 · 變數選擇 | 「**結論上而言，可以說「解釋變數在過程中被拿掉，是因為其他變數都在，而不是他本身沒有影響力。」**」 |
| D4 | 1118 · 逐步程序缺陷 | 「**被刪掉的變數未必與 $Y$ 無關，可能只是關聯性較弱而已。常見情況是「在目前已納入的變數之上，沒有額外解釋力」，因此很難斷言哪一個變數是真正的「完全無關」。**」 |
| D5 | 1118 · 變數選擇結論 | 「**變數選擇程序只是參考用，不保證與最終目標（解釋或預測）完全一致。僅供參考，不當作結論本身。**」 |
| D6 | 1118 · 變數選擇結論 | 「**需警覺「可能存在與暫定結論相矛盾、但配適也不差的替代模型。」**」 |
| D7 | 1118 · 逐步程序缺陷 | 「先選變數後再看 $\text{p-value}$ 值，會有「**選後 p-value 偏樂觀**」的問題，容易形成過度解讀。」 |
| D8 | 1118 · 逐步程序缺陷 | 「刪掉不顯著的變數，通常會讓留下的變數看起來更顯著，因「標準誤變小」、「共線性下降」，**容易高估其重要性**。」 |

### 5.5 統計顯著 ≠ 效果量；卡方 ≠ 關聯強度

| # | 出處 | 材料原文措辭 |
|---|---|---|
| E1 | 1111 · 卡方限制 | 「（卡方）**沒有提供一個明確的「關聯強度」參數。例如：我們不知道「兩變數關係是弱關聯、還是超級強」。⋯ 卡方本身並不負責描述「有多強」，只負責說「顯不顯著」。**」 |
| E2 | 1111 · 卡方限制 | 「（對立假說）**只說「不獨立」，但不會告訴你「為什麼不獨立」。⋯ 只會告訴你「整體上有關聯」，但不會說「關聯長什麼樣子」。**」 |
| E3 | 1118 · 變數選擇原則 | 「**效果大小與解讀要一併呈現（彈性、變化率、邊際效果），不能只報 p-value。**」 |
| E4 | 1111 · odds 的動機 | 「0.50 對 0.45 ⋯ 0.10 對 0.05 ⋯ **兩者的比例尺有明顯的落差，若直接比較，說服力明顯不足。**」（百分點差會誤導） |
| E5 | 1202 · Poisson GOF | 「**其實在 Log-Linear 模型中，Deviance 檢定本身對模型不適合的偵測能力並不是很強。此時不能只看 p-value 就下定論。必須搭配殘差圖與個別係數檢定一起看。**」 |

### 5.6 大樣本 / 近似的前提

| # | 出處 | 材料原文措辭 |
|---|---|---|
| F1 | 1118 · MLE 性質 | 「**若樣本數不大，實務上通常會在信賴區間與檢定結論上，加註「approximate（近似）」來提醒。⋯ 可以說一切的結論都是在「樣本數足夠大」的前提下。小樣本時要小心使用，結果僅供參考！**」 |
| F2 | 1111 · 卡方建議 | 「（$\chi^2$ 與 $\mathrm{G}^2$）**它們「在虛無假設下服從 $\chi^2$ 分配」這件事，都是一種大樣本近似。**」「常見規則是「大部分格子 $\mathrm{E}_{ij} \ge 5$」。」 |
| F3 | 1118 · Deviance GOF | 「（未分組二元資料）**此時 Deviance 並不服從卡方分配，直接做適配度檢定算出的 p-value 不準確。**」 |
| F4 | 1125 · LRT | 「不過在這種小樣本情況下，我們還是**習慣把推論標記為「近似（Approximate）」以示謹慎。**」 |
| F5 | 1202 · Poisson 殘差 | 「若平均數偏小（$\hat{\mu} < 5$）⋯ **這時候看 Q-Q Plot 會覺得模型很爛，但其實只是因為資料太稀疏，這是正常現象，沒必要誤殺模型。**」 |
| F6 | 1125 · Overdispersion | 「**實務上，寧可假設有 Overdispersion，去檢查與修正，也不要完全忽略它的可能性。**」 |
| F7 | 1125 · Overdispersion 後果 | 「模型解讀過度樂觀，**很容易把根本不顯著的變數，誤判為顯著影響。型一錯誤增加。**」 |

### 5.7 配對資料不能當獨立樣本

| # | 出處 | 材料原文措辭 |
|---|---|---|
| G1 | 1111 · McNemar | 「若硬把這兩組當成獨立樣本，會有以下狀況：**會低估變異，誤以為證據比較強。得到的 p-value 會太樂觀。**」 |
| G2 | 1111 · 配對資料 | 「**所以不能假裝 $Y_{i1}$ 跟另一個人 $Y_{k2}$「完全獨立」。**」 |

### 5.8 「比例」不等於「比例」

| # | 出處 | 材料原文措辭 |
|---|---|---|
| H1 | 1125 · 二項反應 | 「**這是最容易犯錯的地方！不是所有的「比例」都能用二項式迴歸。**」 |
| H2 | 1125 · 二項反應 | 「Continuous Proportion（連續型比例）⋯ **這不能用 Binomial GLM**（可能要用 Beta Regression 或轉換後用 Normal）。」 |
| H3 | 1111 · 卡方注意事項 | 「若變數本質是連續型（例如收入、年齡），**通常會先切成類別區間後再做列聯表，但這樣會犧牲一些資訊。**」 |
| H4 | 1111 · 卡方建議 | 「**卡方檢定把兩個變數都當成 nominal（名目變數）**，只在意「是哪一格」與「多少人」，不會利用到任何「大小／順序」的資訊。」 |

---

<a id="part-6"></a>
## Part 6 — 可重用資產（可直接寫進新 Skill）

【評註】以下全部是為了「廣告成效分析 Skill」而整理的可執行資產。**規則的來源全部指回材料，公式一字未改；標註「衍生」者為本次萃取者依材料推導的操作化版本。**

### 6.1 方法選擇決策樹（依材料規則整理）

```
Y 是什麼型態？
├─ 二元 0/1（買 / 沒買、點 / 沒點、流失 / 留存）
│   ├─ 只比兩組、無其他共變數
│   │   ├─ 兩群互相獨立 ────────→ 兩獨立樣本比例檢定（合併 SE）＋ OR 與 CI   [1111 §1.4]
│   │   └─ 同一批人前後 / A-B ──→ McNemar test（mcnemar.test）              [1111 §1.7]
│   ├─ 多水準類別 × 二元結果，只想知道「有沒有關聯」→ chisq.test()          [1111 §1.5]
│   └─ 要控制其他變數 / 要量化效果 / 要預測 → logistic regression           [1118 §2.1]
│       ├─ 一列一個個體（m_i = 1）→ glm(Y ~ X, binomial)     【未分組】
│       └─ 一列一個群組（m_i > 1）→ glm(cbind(s,f) ~ X, binomial) 【分組】
├─ 計數（次數、訂單數、來店數），無固定分母 → Poisson log-linear            [1202 §4.3]
│       glm(Y ~ X, family=poisson)
├─ 比例，且有整數分子/分母 → binomial GLM（同上分組版）                     [1125 §3.1]
├─ 比例，但是連續型（濃度、成長率）→ 不可用 binomial GLM                    [1125 §3.1]
└─ 連續 → MLR（gaussian + identity link）                                   [1118 §2.2]
```

### 6.2 家族與連結函數選擇規則（依材料的 Var–Mean 關係）

| 觀察到的 Var 與 Mean 關係 | 資料型態 | family | canonical link | 係數 $e^{\hat\beta}$ 的意思 |
|---|---|---|---|---|
| Var 為常數 | 連續 | `gaussian` | identity（$\mu$） | 加法效果（每單位 +$\hat\beta$） |
| Var 隨 Mean **線性上升** | 計數 | `poisson` | log（$\log\mu$） | **次數乘 $e^{\hat\beta}$ 倍** |
| Var 隨 Mean **倒 U 型** | 二元 / 比例 | `binomial` | logit（$\log\frac{\pi}{1-\pi}$） | **勝算乘 $e^{\hat\beta}$ 倍** |
| Var 隨 Mean **超線性上升** | 正值連續 / 存活 | `gamma` | log / inverse | 乘法效果 |
| 上述任一 + 實際 Var 又更大 | — | `quasibinomial` / `quasipoisson` | 同上 | 同上，但 SE × $\sqrt{\hat\psi}$ |

依據（材料原文）：1118「不同資料類型中平均值（mean）與變異數（variance）之間的關係」四張圖 + 「在 GLM 中，「選擇何種連結函數」與「選擇何種隨機成分」是兩件相互獨立的事情。」

### 6.3 廣告 A/B 成效分析檢查清單（1111 §1.4 的操作化，衍生）

**Step 0 — 先問資料是怎麼來的**（決定能寫什麼指標）

- [ ] 這是哪一種抽樣設計？（Poisson / Multinomial / Prospective / Retrospective / Randomized）
- [ ] 若是 **Retrospective**（先撈買/沒買名單再回頭看觸點）→ **只能報 OR，禁止報轉換率**
- [ ] 若是 **Randomized**（真正隨機分流）→ 才可以用「處理效果」的語言
- [ ] 其餘 → 全程使用「關聯」措辭

**Step 1 — 建列聯表與描述**

- [ ] 兩組（曝光 / 對照）× 兩結果（買 / 沒買）→ 2×2 表，四格 $a,b,c,d$
- [ ] $\hat p_1 = \frac{a}{a+b}$、$\hat p_0 = \frac{c}{c+d}$
- [ ] $\widehat{\text{OR}} = \frac{ad}{bc}$
- [ ] 檢查每格期望次數是否 $\ge 5$

**Step 2 — 顯著性**

- [ ] 單尾或雙尾？（「是否較高」→ 單尾 $\mathrm{H}_1: p_1 > p_0$）
- [ ] 檢定用**合併** SE：$\hat p_c = \frac{X_1+X_0}{n_1+n_0}$，$\text{SE}_0 = \sqrt{\hat p_c(1-\hat p_c)(\frac1{n_1}+\frac1{n_0})}$
- [ ] $Z = \frac{\hat p_1 - \hat p_0}{\text{SE}_0}$
- [ ] 等價作法：`chisq.test()`（2×2 時 $\chi^2 = Z^2$）

**Step 3 — 效果量（不能只給 p-value）**

- [ ] 差異的 CI 用**未合併** SE：$\sqrt{\frac{\hat p_1(1-\hat p_1)}{n_1}+\frac{\hat p_0(1-\hat p_0)}{n_0}}$
- [ ] OR 的 CI：先算 $\log\widehat{\text{OR}}$，$\text{ASE} = \sqrt{\frac1a+\frac1b+\frac1c+\frac1d}$，$\log\widehat{\text{OR}} \pm 1.96\,\text{ASE}$，最後 `exp()`
- [ ] 報告時**永遠 exp() 後再講**，不要講 log odds

**Step 4 — 控制共變數（升級成 logistic）**

- [ ] `full <- glm(buy ~ 客群 + 既有消費 + 其他渠道 + exposed, family=binomial)`
- [ ] `reduced <- glm(buy ~ 客群 + 既有消費 + 其他渠道, family=binomial)`
- [ ] `anova(reduced, full, test="Chisq")` ← **正式結論用這個，不是 summary 的 z**
- [ ] `exp(coef(full)["exposed"])`、`exp(confint.default(full)["exposed",])`

**Step 5 — 模型體檢**

- [ ] 掃 `Residual deviance` vs `df`：差很多 → 有問題
- [ ] （分組資料才做）GOF：`1 - pchisq(deviance(m), df.residual(m))`
- [ ] 殘差 |> 2| 的點是誰？
- [ ] 若 GOF 不過 → 依序查：(1) 漏變數 / 非線性 → (2) outlier → (3) overdispersion

**Step 6 — 寫報告**

- [ ] 主句：「在控制 ⋯ 後，曝光組的購買勝算約為對照組的 X 倍（95% CI a–b，p = ⋯）」
- [ ] 附註：「本分析基於觀察型資料，僅能提供統計關聯的證據，不能直接作為因果推論。」
- [ ] 若有變數被砍：「在已納入的其他變數之上，該變數沒有額外解釋力」（**不是**「沒有影響」）

### 6.4 GLM 模型體檢清單（1118 + 1125 + 1202 綜合）

| 檢查項 | 未分組 binary | 分組 binomial | Poisson | 指令 |
|---|---|---|---|---|
| EDA：X 與 logit 是否線性 | ✘（做不了） | ✔ Empirical logit plot | ✔ 散佈圖 + exp 曲線 | `plot(x, log(p/(1-p)))` |
| 預測曲線疊圖 | ✔（jitter） | ✔ | ✔（jitter） | `predict(m, type="response")` |
| Deviance 殘差 | ✔（但不常態） | ✔ | ✔ | `residuals(m, type="deviance")` |
| Pearson 殘差 | ✔（但不常態） | ✔ | ✔ | `residuals(m, type="pearson")` |
| Q-Q plot 有意義？ | ✘（會出現兩條曲線） | ✔（$m_i$ 夠大） | ✔（$\hat\mu>5$ 才有意義） | `qqnorm(); qqline()` |
| Deviance GOF 檢定 | **✘ 不可用** | ✔ | ✔（但檢定力弱） | `1-pchisq(deviance(m), df.residual(m))` |
| 速算法 Dev vs df | ✘ | ✔ | ✔ | 看 `summary()` 最後兩行 |
| Overdispersion $\hat\psi$ | ✘ | ✔ | ✔ | `deviance(m)/df.residual(m)` |
| 快篩 mean vs var | ✘ | ✘ | ✔ | `mean(Y); var(Y)` |
| 模型比較 | LRT | LRT（無 OD）/ F（有 OD） | LRT / F | `anova(r, f, test="Chisq")` |

### 6.5 Overdispersion 處理流程（1125 §3.8 + 1202 §4.7，順序不可顛倒）

```
Deviance >> df ?
  │
  ├─ Step 1 情境判斷：獨立性存疑？機率不同質？模型太簡陋？
  │
  ├─ Step 2 先跑 Rich Model（把所有主效果 + 交互作用都放進去）
  │     └─ 若 GOF 就此通過 → 原來只是漏變數，不是 overdispersion（1202 案例實證）
  │
  ├─ Step 3 檢查 deviance residuals
  │     ├─ 只有一兩個 |res| 很大 → 是 outlier，先處理資料
  │     └─ 普遍偏大 → 真的是 overdispersion
  │
  └─ Step 4 校正（Quasi-likelihood）
        psi <- deviance(m_full)/df.residual(m_full)
        summary(m, dispersion=psi)          # SE × sqrt(psi)，z 變小、p 變大
        # 模型比較改用 F-test，不能用卡方：
        F = ((dev_reduced - dev_full)/d) / psi
        1 - pf(F, d, df.residual(m_full))
```

### 6.6 R 程式碼資產（可直接改寫成 Python 前的原型）

**A. 從四格數字建 2×2 列聯表 + OR + CI（1111 Case 3 模板）**

```r
y   <- c(a, b, c, d)                        # listed by row
g   <- gl(2, 2, 4, c("Group1","Group0"))    # row names
o   <- gl(2, 1, 4, c("Yes","No"))           # col names
( case <- xtabs(y ~ g + o) )

## Odds Ratio & test
ptest <- prop.test(case)
( pi    <- ptest$estimate )                       # pi1.hat, pi2.hat
( odds  <- ptest$estimate/(1-ptest$estimate) )    # omega1.hat, omega2.hat
( phi   <- odds[1]/odds[2] )                      # odds ratio
log(phi)
nY <- sum(case[,1]); n <- sum(case)
( pic  <- nY/n )                                  # pooled proportion
( n.r  <- apply(case,1,sum) )
( se0  <- sqrt(sum(1/(pic*(1-pic)*n.r))) )        # test version SE
1-pnorm(log(phi)/se0)                             # one-sided p-value

## C.I. for Odds Ratio
( ase       <- sqrt(sum(1/case)) )                # CI version SE (ASE)
( logphi.ci <- log(phi)+c(-1,1)*qnorm(0.975)*ase )
( exp(logphi.ci) )
```

**B. 卡方 + 期望次數 + $G^2$ 手算（1111 Case 4 模板）**

```r
chisq.test(case, correct=F)
( Xsq <- chisq.test(case, correct=F)$statistic )
pchisq(Xsq, df=(I-1)*(J-1), lower.tail=F)

( pij   <- prop.table(case) )
( mpr.r <- apply(pij,1,sum) )        # marginal probability by row
( mpr.c <- apply(pij,2,sum) )        # marginal probability by column
( mu.hat <- outer(mpr.r, mpr.c)*sum(case) )

( Gsq <- 2*sum(case*log(case/mu.hat)) )
pchisq(Gsq, df=(I-1)*(J-1), lower.tail=F)
```

**C. 未分組 binary logistic 完整流程（1118 Case 1 / Case 2 模板）**

```r
m1 <- glm(Status ~ Age, family=binomial)
m2 <- glm(Status ~ Age + Sex, family=binomial)
m3 <- glm(Status ~ Age * Sex, family=binomial)
summary(m2)

## 正式決策：LRT，不是 Wald
anova(m2, m3, test="Chisq")

## 手動 LRT
( dvr <- deviance(reduced) ); ( dvf <- deviance(full) )
( dfr <- df.residual(reduced) ); ( dff <- df.residual(full) )
1 - pchisq(dvr-dvf, dfr-dff)

## 係數 → Odds Ratio
confint.default(m2)
exp(confint.default(m2)[3,])

## 預測曲線
sq <- seq(14,66,1)
resp <- predict(m2, type="response", newdata=data.frame(Age=sq, Sex="Female"))
plot(sq, resp, type="l", ylim=c(0,1))
points(Age, jitter(SP, factor=0.2), pch=16)

## 殘差
R.res <- fitted(m1) - SP
D.res <- residuals(m1, type="deviance")
P.res <- residuals(m1, type="pearson")
qqnorm(D.res); qqnorm(P.res)
```

**D. 分組 binomial logistic 完整流程（1125 iPhone 模板）**

```r
survey.s <- read.csv("survey_sum.csv"); attach(survey.s)

## 注意 Y 的寫法：cbind(成功, 失敗)
lg1 <- glm(cbind(iphone, notiphone) ~ fb, family=binomial)
summary(lg1)

## Empirical logit plot（未分組做不到）
( proportion <- iphone/total )
logit1 <- log(proportion/(1-proportion))
plot(fb, logit1, pch=20, ylab="logit (iphone)")
abline(coef=lg1$coef, lty=2, col=2)
# 若有 0 或 1：log((Y+0.5)/(m-Y+0.5))

## 顯著性
confint.default(lg1)                                        # Wald
1 - pchisq(lg1$null.deviance - deviance(lg1), 1)            # LRT

## 殘差
respea <- residuals(lg1, type="pearson")
resdev <- residuals(lg1, type="deviance")
qqnorm(respea); qqline(respea)
qqnorm(resdev, pch=16); qqline(resdev)

## Goodness-of-Fit（分組才可用）
deviance(lg1); lg1$df.residual
1 - pchisq(deviance(lg1), lg1$df.residual)
( Xsq <- sum(respea^2) )
1 - pchisq(Xsq, df=lg1$df.residual)
```

**E. Overdispersion 校正 + F-test（1125 模板）**

```r
lg1 <- glm(cbind(iphone, notiphone) ~ fb,          family=binomial)
lg2 <- glm(cbind(iphone, notiphone) ~ fb + gender, family=binomial)

( psi1 <- deviance(lg1)/df.residual(lg1) )
summary(lg1, dispersion=psi1)      # SE 放大 sqrt(psi) 倍
( psi2 <- deviance(lg2)/df.residual(lg2) )
summary(lg2, dispersion=psi2)

## 有 OD 時模型比較改用 F-test
( drop  <- deviance(lg1) - deviance(lg2) )
( ddf   <- df.residual(lg1) - df.residual(lg2) )
( fstat <- (drop/ddf)/psi2 )       # 分母用 Full model 的 psi
1 - pf(fstat, ddf, df.residual(lg2))
```

**F. Poisson log-linear 完整流程（1202 模板）**

```r
## EDA：Poisson 快篩
table(shopping)
barplot(table(shopping))
mean(survey$shopping); var(survey$shopping)   # var >> mean → 疑似 OD 或漏變數

glm1 <- glm(shopping ~ cash, data=survey, family=poisson)
summary(glm1)
plot(jitter(survey$cash), jitter(survey$shopping))

## 疊指數曲線
new <- seq(min(cash), max(cash), by=12.5)
lines(new, exp(predict(glm1, newdata=data.frame(cash=new))), col=2, lty=2)

## 殘差圖（Poisson 本來就會喇叭狀）
plot(fitted(glm1), residuals(glm1)); abline(h=0, lty=2); abline(h=c(2,-2), lty=3, col=4)
qqnorm(residuals(glm1), pch=16); qqline(residuals(glm1))

## GOF
( Gsq <- glm1$deviance ); 1-pchisq(Gsq, df=glm1$df.residual)
res <- residuals(glm1, type="pearson"); ( Xsq <- sum(res^2) )
1-pchisq(Xsq, df=glm1$df.residual)

## 加變數後再驗一次（1202 的關鍵教訓）
glm2 <- glm(shopping ~ student + gender + iphone + cash, data=survey, family=poisson)
anova(glm1, glm2, test="Chisq")
1-pchisq(glm2$deviance, glm2$df.residual)     # 0.204 → 原來不是 OD，是漏變數
```

**G. 類別變數編碼與參考組（1028 模板，logistic 完全照搬）**

```r
## 手刻指標變數（不建議）
mod <- lm(Y ~ X1 + D7 + D8 + D9)

## 直接用 factor + relevel（建議）
df$Status.n <- factor(df$Status)
levels(df$Status.n) <- list(act="act", nac="pen", nac="sld")   # 合併水準
df$Status.n <- relevel(df$Status.n, ref="nac")                 # 指定參考組
School <- relevel(factor(School), ref="fred")

## 交互作用
lm(revenue ~ cost * city)          # 主效果 + 交乘項
glm(Y ~ X * group, family=binomial)

## 巢狀比較與逐步
anova(mod3, mod2)                  # lm
anova(m2, m3, test="Chisq")        # glm
step(full)                         # AIC
drop1(m, test="F")
update(m, . ~ . - varname)
```

### 6.7 公式速查卡

| 名稱 | 公式 | 出處 |
|---|---|---|
| odds ↔ p | $\text{odds}=\frac{p}{1-p} \Longleftrightarrow p=\frac{\text{odds}}{1+\text{odds}}$ | 1111 |
| 樣本 OR（2×2） | $\widehat{\text{OR}} = \frac{ad}{bc}$ | 1111 |
| $\log \widehat{\text{OR}}$ 的 ASE | $\sqrt{\frac1{n_{11}}+\frac1{n_{12}}+\frac1{n_{21}}+\frac1{n_{22}}}$ | 1111 |
| 兩比例差 SE（檢定，合併） | $\sqrt{\hat p_c(1-\hat p_c)\left(\frac1{n_1}+\frac1{n_2}\right)}$ | 1111 |
| 兩比例差 SE（CI，未合併） | $\sqrt{\frac{\hat p_1(1-\hat p_1)}{n_1}+\frac{\hat p_2(1-\hat p_2)}{n_2}}$ | 1111 |
| 期望次數 | $\hat\mu_{ij} = \frac{n_{i+}n_{+j}}{n}$ | 1111 |
| Pearson $\chi^2$ | $\sum\sum\frac{(n_{ij}-\hat\mu_{ij})^2}{\hat\mu_{ij}}$ | 1111 |
| $G^2$（LR 卡方） | $2\sum\sum n_{ij}\log\frac{n_{ij}}{\hat\mu_{ij}}$ | 1111 |
| 列聯表自由度 | $(\mathrm{I}-1)(\mathrm{J}-1)$ | 1111 |
| McNemar $\chi^2$ | $\frac{(b-c)^2}{b+c}$（校正版 $\frac{(|b-c|-1)^2}{b+c}$），$df=1$ | 1111 |
| logit 模型 | $\log\frac{\pi(x)}{1-\pi(x)}=\alpha+\beta x$ | 1118 |
| 反解機率 | $\pi(x)=\frac{e^{\alpha+\beta x}}{1+e^{\alpha+\beta x}}$ | 1118 |
| 切線斜率 | $\beta\,\pi(x)[1-\pi(x)]$ | 1118 |
| $EL_{50}$ | $x = -\frac{\alpha}{\beta}$ | 1118 |
| 差 k 單位的 OR | $e^{k\hat\beta}$ | 1118 |
| Wald Z | $Z=\frac{\hat\beta}{\text{ASE}}$ | 1118 |
| LRT | $-2(L_0-L_1) \sim \chi^2_1$ | 1118 |
| Deviance | $-2[\log L(M_f)-\log L(M_s)] = -2\log L(M_f)$ | 1118 |
| Deviance 殘差（binary） | $\operatorname{sign}(r_i)\sqrt{-2[y_i\log\hat\pi_i+(1-y_i)\log(1-\hat\pi_i)]}$ | 1118 |
| Pearson 殘差（binary） | $\frac{Y_i-\hat\pi_i}{\sqrt{\hat\pi_i(1-\hat\pi_i)}}$ | 1118 |
| Deviance 殘差（binomial） | $\operatorname{sign}(\cdot)\sqrt{2\{Y_i\log\frac{Y_i}{m_i\hat\pi_i}+(m_i-Y_i)\log\frac{m_i-Y_i}{m_i-m_i\hat\pi_i}\}}$ | 1125 |
| Pearson 殘差（binomial） | $\frac{Y_i-m_i\hat\pi_i}{\sqrt{m_i\hat\pi_i(1-\hat\pi_i)}}$ | 1125 |
| Empirical logit | $\log\frac{Y_i}{m_i-Y_i}$（調整版 $\log\frac{Y_i+0.5}{m_i-Y_i+0.5}$） | 1125 |
| $G^2$（binomial GOF） | $2\sum y_i\log\frac{y_i}{\hat\mu_i}+2\sum(m_i-y_i)\log\frac{m_i-y_i}{m_i-\hat\mu_i}$ | 1125 |
| 離散係數 | $\hat\psi = \frac{\text{Deviance}}{df}$ | 1125 / 1202 |
| 校正後 SE | $\text{SE}\times\sqrt{\hat\psi}$ | 1125 |
| Drop-in-Deviance F | $\frac{(\text{Drop in Deviance})/d}{\hat\psi}$ | 1125 / 1202 |
| Poisson pmf | $\Pr(Y=y)=\frac{e^{-\mu}\mu^y}{y!}$，$E=Var=\mu$ | 1202 |
| Log-linear | $\log\mu=\beta_0+\beta_1X_1$，$\mu=e^{\beta_0}e^{\beta_1X_1}$ | 1202 |
| Deviance 殘差（Poisson） | $\operatorname{sign}(Y_i-\hat\mu_i)\sqrt{2[Y_i\log\frac{Y_i}{\hat\mu_i}-(Y_i-\hat\mu_i)]}$ | 1202 |
| Pearson 殘差（Poisson） | $\frac{Y_i-\hat\mu_i}{\sqrt{\hat\mu_i}}$ | 1202 |
| 卡方速算法 | 若模型對，$\text{Deviance}\approx df$，SD $\approx\sqrt{2\,df}$ | 1125 |

### 6.8 報告措辭範本（Part 5 的正面表述）

| 情境 | ✔ 可以寫 | ✘ 不可以寫 |
|---|---|---|
| 觀察型資料、有顯著關聯 | 「曝光組的購買勝算約為對照組的 2.4 倍（95% CI 1.2–4.9）。本分析基於觀察型資料，僅能提供統計關聯的證據。」 | 「廣告使購買率提高了 15 個百分點」 |
| 隨機分流實驗 | 「隨機分派下，處理組的購買勝算為對照組的 X 倍，可視為處理效果。」 | — |
| 回溯式抽樣（先撈名單） | 「曝光與購買之勝算比為 X（95% CI ⋯）。」 | 「曝光組轉換率 30%、未曝光 15%」 |
| 變數被 step() 砍掉 | 「在已納入的其他渠道之上，該渠道沒有額外解釋力。」 | 「該渠道對轉換沒有影響」 |
| 卡方顯著 | 「渠道與轉換之間存在關聯（$\chi^2$ = ⋯, df = ⋯, p = ⋯）。」 | 「渠道 A 顯著優於渠道 B」（卡方不指定方向） |
| 小樣本 | 「以下信賴區間與檢定結果為近似（approximate），小樣本下請謹慎解讀。」 | 直接報精確數字 |
| GOF 不過 | 「模型配適不佳，可能來自漏變數、離群值或超額變異，已依序檢查。」 | 直接解讀係數 |
| 有 overdispersion | 「已用準概似法校正，標準誤放大 $\sqrt{\hat\psi}$ 倍後，該變數（不）顯著。」 | 用未校正的 p-value |

### 6.9 給新 Skill 的「常見錯誤」清單（全部有材料出處）

1. 拿 0/1 顧客資料跑 OLS（線性機率模型會預測出 <0 或 >1 的機率）— 1118
2. 拿同一批人的活動前/後跑 `prop.test()`（該用 McNemar，否則 p-value 過度樂觀）— 1111
3. 未分組資料拿 Residual Deviance 去查卡方表做 GOF — 1118 / 1125
4. 沒有分母的 CTR 欄位丟進 `family=binomial` — 1125
5. 用 `summary(glm)` 的 z 值當正式決策依據（該用 `anova(..., test="Chisq")`）— 1118
6. 報告 log odds 而非 `exp()` 後的倍數 — 1118
7. 回溯式資料報「轉換率」— 1111
8. 只報 p-value 不報效果量與 CI — 1118 / 1111
9. 把「變數被移除」講成「沒有影響」— 1118
10. 有 overdispersion 還用卡方比模型（該用 F-test）— 1125
11. 一看到 Deviance 大就宣稱 overdispersion（先查漏變數與 outlier）— 1125 / 1202 實證
12. Poisson 小平均數下看 Q-Q plot 醜就否定模型 — 1202
13. 把 GLM 的 GOF「希望 p 大」與係數檢定「希望 p 小」搞混 — 1202 對照表
14. 順序型類別（滿意度 1–5）直接跑卡方，浪費順序資訊而不自知 — 1111

---

<a id="part-7"></a>
## Part 7 — 來源盤點與缺漏

### 7.1 逐頁盤點

| 要求的頁面 | ID | 實際狀態 | 本 digest 對應 | 原始字元數（含圖片 URL） |
|---|---|---|---|---|
| 1028 | `2972b4ffdf0b80f49acad0528bad3aaf` | ✔ 完整讀取 | Part 0 | ~12,800 |
| 1111 | `2a82b4ffdf0b802880c6dbce6396b34d` | ✔ 完整讀取 | Part 1（含 ★1.4 廣告 A/B） | 87,193 |
| 1118 | `2a82b4ffdf0b80019450f5507cb63e8a` | ✔ 完整讀取 | Part 2 | 231,025（去圖後 86,784） |
| 1125 | `2b52b4ffdf0b8005ba93dee6ed8a15ff` | ✔ 完整讀取 | Part 3 | 64,233（去圖後 27,342） |
| 1202 | `2b52b4ffdf0b80a1b80bdb3daaac63e3` | ✔ 完整讀取 | Part 4 | 50,174（去圖後 20,012） |
| 1208 | `2c32b4ffdf0b8011b338c437b3d1033d` | ⚠ **不屬於本課程** | 未收錄 | ~2,000 |
| 1209 | `2c42b4ffdf0b80459f92f26ed089e529` | ⚠ **空頁** | 未收錄 | 420 |

### 7.2 1208 的實際內容（已核對）

- 該 ID 的 ancestor-path 為：`作業管理` → `碩二課程` → `NTU`，**不是**「商管統計資料分析 (MBA5045)」。
- 內容為「剩食處理」與「台大鬆餅屋 獲利模式發想」的作業管理課筆記（處理成本 / 機會成本 / 惜食平台 / 廣告費 / 加盟金 / 訂閱費…），**與 logistic / GLM / 類別資料完全無關**。
- 結論：本課程頁面清單中不存在 1208，該 ID 為誤植。**本 digest 不收錄。**

### 7.3 1209 的實際內容（已核對）

- 頁面只有兩個空 toggle：`In-class practical 1`、`In-class practical 2`，無任何內容。
- 結論：課堂實作題當時未留下筆記。**無資料可萃取。**

### 7.4 本 digest 未逐字收錄的部分（誠實說明）

1. **1118「回顧」區的後半段**（約原始檔第 850–1325 行）：個別參數 t-test、Nested Partial F-test、Global Usefulness F-test 的完整假說 / 決策規則 / 範例，以及 $R^2$、Adjusted $R^2$、殘差圖 / Histogram / Q-Q plot 的假設檢查、信賴區間 vs 預測區間。
   - 原因：這是**前一章 MLR 的 synced block 完整重貼**，與本 digest 的 logistic / GLM 主軸關係較遠；核心公式（三種檢定的統計量、$R^2$、Adjusted $R^2$、AIC）已在 Part 2 §2.0 保留。
   - 若日後需要，可回到 `1118` 頁的「回顧（整理先前的 MLR）」toggle 取用，或參考本專案中 MLR 章節的 digest。
2. **所有圖片**：Notion 圖片為 AWS S3 簽名網址（含到期時間），數小時後即失效，故一律以 `[圖片]` 標記位置，不保留失效網址。受影響的內容主要是：R 報表截圖（係數表、Deviance 數值）、EDA 圖、Q-Q plot、Excel Solver 截圖、抽樣設計對照表圖。
   - **材料文字中已敘述的關鍵數值（係數、Deviance、p-value、CI）都已逐字保留在正文**，故圖片遺失不影響方法論的可用性。
3. **1111 的兩張空圖片標記** `![]()`（原始檔第 836–837 行）：Notion 中即為空，無內容。

### 7.5 材料本身的筆誤（照錄不改，此處標注）

- 1111 §1.4「兩獨立樣本比例」中，樣本比例列出兩次 $\hat{p}_1$（第二個應為 $\hat{p}_2$）。
- 1111 McNemar 卡方近似段落出現 `$b+cb + cb+c$` 的重複貼上痕跡，應為 $b+c$。
- 1118「Logistic 迴歸模型是 GLM 的一個特例」段末寫 $\frac{\pi(x)}{1-\pi(x)} = \alpha+\beta x$，依上下文應為 $\log\frac{\pi(x)}{1-\pi(x)} = \alpha+\beta x$。
- 1111 Multinomial Sampling 段落「欄（Columns）：反應類別 / 欄（Rows）：解釋變因」，第二個「欄」應為「列」。
- 1125「這個模型的解讀方式，與 11/28 中提到的 Binary logistic regression 相同」，依課程進度應指 11/18。
- 1111 高槓桿點經驗法則第二條「$h<\frac{2(k+1)}{n} \longrightarrow$ 該點很孤立，也需進一步檢查」與一般教科書慣例（$h$ 小代表不孤立）方向相反，材料原文如此。

### 7.6 建議的後續補充來源

- 課程頁面清單中若有 1028 之前的 MLR 章節（EDA、SLR、MLR 假設、變數轉換），可補成完整的「迴歸方法論」本地庫。
- `survey.csv` / `survey_sum.csv` / `happyliving.csv` / `HOMES_new.csv` / `Fuel_eff.txt` / `block_cost.csv` 等資料檔未在 Notion 中，若能取得可讓 Part 6 的 R 模板直接可跑（並用於 Python 移植的對拍驗證）。
- `Sleuth2` 套件的 `case2001`（Donner Party）與 `case2002`（Birdkeeping）在 R 中可直接取得，**這兩個資料集可以當作新 Skill 的內建測試案例**（`install.packages("Sleuth2")`）。

---

## 附錄：全文結構速覽

- **Part 0（1028）**：類別變數編碼、`factor()` + `relevel()`、巢狀檢定、`step()`、殘差 / 槓桿 / Cook's D
- **Part 1（1111）**：比例 → odds → OR → 列聯表 → 卡方 → 獨立性 vs 同質性 → McNemar → 前瞻 vs 回溯 → 五種抽樣設計
  - **★ §1.4 是廣告 A/B 分析的原型**
- **Part 2（1118）**：MLR 回顧 → GLM 三大構件 → binary logistic → Wald vs LRT → Donner / Birdkeeping → MLE → 殘差 → Deviance GOF
- **Part 3（1125）**：binomial（分組）logistic → Empirical logit → 分組版殘差 → **Deviance GOF 只有分組能用** → Overdispersion 三步驟 → Quasi-likelihood → Drop-in-Deviance F-test
- **Part 4（1202）**：Poisson → Log-Linear → Extra-Poisson Variation → **「漏變數 vs overdispersion」的實證案例** → MLR vs GLM 總對照表
- **Part 5**：推論界線（8 個主題、35 條逐字引文，全部標明出處）
- **Part 6**：可重用資產（決策樹 / 家族與 link 選擇表 / A-B 檢查清單 / 體檢清單 / OD 流程 / 7 段 R 模板 / 公式速查卡 / 措辭範本 / 14 條常見錯誤）
- **Part 7**：來源盤點與缺漏
