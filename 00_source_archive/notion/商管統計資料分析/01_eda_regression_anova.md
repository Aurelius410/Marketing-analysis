---
title: "商管統計資料分析 (MBA5045) — EDA / 迴歸 / 迴歸診斷 / ANOVA 方法論萃取"
course: "商管統計資料分析 (MBA5045)，台大工商管理學系 Dr. Jiun-Yu Yu（余俊賢）"
source_type: notion
source_parent: "https://app.notion.com/p/2692b4ffdf0b8060ac98f5535dda84a9"
sources:
  - { title: "0902",                    url: "https://app.notion.com/p/2692b4ffdf0b80a78dacd68453e1a9e7", size: "~4 KB（大量為圖片）" }
  - { title: "0909",                    url: "https://app.notion.com/p/26b2b4ffdf0b8040bea8e3327e2508b4", size: "69,548 chars（原始）/ 42 KB（去圖片 URL 後）" }
  - { title: "0916",                    url: "https://app.notion.com/p/2712b4ffdf0b801387c1cc677109b16c", size: "49 KB（去圖片 URL 後）" }
  - { title: "0923",                    url: "https://app.notion.com/p/27b2b4ffdf0b80838643cff845f92a36", size: "53 KB（去圖片 URL 後）" }
  - { title: "0930 In-class practical", url: "https://app.notion.com/p/27e2b4ffdf0b80b090ecdac81c787791", size: "~28 KB，幾乎純 R code" }
  - { title: "1007",                    url: "https://app.notion.com/p/2842b4ffdf0b80b8bcc9c81e527d1fa2", size: "43 KB（去圖片 URL 後）" }
  - { title: "1014",                    url: "https://app.notion.com/p/2842b4ffdf0b80fc936ef87fd93b93b1", size: "100 KB（去圖片 URL 後）" }
  - { title: "1021",                    url: "https://app.notion.com/p/2972b4ffdf0b805c976cdf227153500b", size: "35 KB（去圖片 URL 後）" }
  - { title: "變異數分析",               url: "https://app.notion.com/p/26a2b4ffdf0b8003b5aad43e4b9a07d8", size: "68 KB（去圖片 URL 後）" }
  - { title: "EDA Code",                url: "https://app.notion.com/p/26c2b4ffdf0b8097bff1e0fd80febc48", size: "~4 KB，純 R code" }
  - { title: "EDA Files",               url: "https://app.notion.com/p/26c2b4ffdf0b804cb2f2e6043dece41c", size: "僅一個 zip 附件 1-02-1_EDA.zip，無文字內容" }
  - { title: "SLR Code",                url: "https://app.notion.com/p/2712b4ffdf0b805e8bb2e9bfb05b483f", size: "~2.5 KB，純 R code" }
fetched: 2026-07-26
coverage: |
  12 個指定頁面全部取得。其中 0902 / 0930 / EDA Code / EDA Files / SLR Code 為本次直接 fetch；
  0909 / 0916 / 0923 / 1007 / 1014 / 1021 / 變異數分析 取自本機已快取的完整頁面 dump
  （已驗證每個檔案結尾均為完整的 </content></page>，非截斷）。
  文字內容 100% 讀完，R 程式碼 100% 逐字抄錄（含註解、空白行語意、變數命名）。
  **未涵蓋**：所有頁面內嵌的截圖（Notion S3 圖片），本 digest 以 `![圖片]` 標記位置並轉述其文字說明；
  EDA Files 的 zip 附件（1-02-1_EDA.zip，內含 HOMES.csv 等資料檔）未下載解壓。
  1014 / 1021 / 變異數分析 三頁 ANOVA 內容有大量重疊，本 digest 已合併去重但保留各自獨有的判讀規則。
---

# 商管統計資料分析 (MBA5045) — 方法論萃取

> **本文件的閱讀約定**
> - 【材料原文】= 直接來自 Notion 頁面的內容（中文講義筆記、R 程式碼、公式）。R 程式碼一律逐字抄錄。
> - 【評註】= 萃取者為了轉成 Python Skill 所加的說明、對應關係、實作提醒。**不是教材內容**。
> - 每個方法都標註「這回答什麼行銷/商業問題」。

---

## 0. 課程的分析觀（0902）

### 【材料原文】SIPOC 架構

- **S**：Suppliers
- **I**：Inputs
- **P**：Process Steps
- **O**：Outputs
- **C**：Customers

### 【材料原文】資料到行動的價值鏈

```
Uncertainty + Variability → Outcomes → Observations → Data
→ Information → Knowledge → Insight → Action
```

其餘為三張投影片截圖：`Business process`、`Level of Analytics`、`Summary`（本次未取得圖片內容）。

### 【評註】這回答什麼行銷/商業問題

這是整套方法論的「為什麼」：商業流程本身帶有**不確定性與變異**，所以我們才需要統計。
分析的終點不是模型，是 **Action**。任何 Skill 的輸出如果停在 p-value，就沒走完這條鏈。
SIPOC 則決定了「該蒐集哪些變數」——輸入端（供應商、原料）、流程端、輸出端、顧客端各自對應不同的 X。

---

## 1. EDA：拿到資料的標準動作序列

> 這是任務要求的第 1 項。以下順序直接來自 EDA Code 的程式排列順序與 0909 講義的敘述順序，
> 並以 0930 In-class practical 的實戰腳本交叉驗證（同一位老師、同一套流程套用到新資料集）。

### 1.1 【材料原文】EDA 的定位（0909）

- Overall task：Analyze data to inform a （business）decesion.
- Assume data relevant to the problem has collected.
- Intermediate task：Identify and summarize the data.
- Example：We've moved to a new city and wish to buy a home.
- Data：

$$y = \text{home price (in \$ thousands) for } n = 50 \text{ randomly sampled single-family homes}$$

### 1.2 【材料原文】標準動作序列（EDA Code 原始碼順序）

老師的 EDA 腳本嚴格照這個順序走：

| # | 動作 | R 指令 | 目的 |
|---|------|--------|------|
| 1 | 讀檔 | `read.csv(..., header=TRUE)` | 把資料進到 data frame |
| 2 | 展開欄位 | `attach(HOMES)` | 標題變成變數名稱 |
| 3 | 分布形狀（圖） | `hist()` + `boxplot()` | 先看單變數長相 |
| 4 | 集中趨勢 | `mean()`, `median()` | Measures of Location |
| 5 | 分散趨勢 | `sd()`, `var()`, `min()`, `max()`, `range()`, `quantile()`, `summary()`, `length()` | Measures of Spread / Dispersion |
| 6 | 形狀量數 | `skewness()`, `kurtosis()`（需 fBasics） | Measures of Shape |
| 7 | 版面設定 | `par(mfrow=)`, `par(pty="s")` | 排版 |
| 8 | 雙變數關係 | `plot()` 散佈圖 → `abline(lm())` 加迴歸線 | 看 X-Y 關係 |
| 9 | 整合圖 | `par(fig=)` 疊圖 | 散佈圖＋邊際直方圖＋盒鬚圖 |
| 10 | 全變數掃描 | `pairs()` 散佈圖矩陣 → 加迴歸線版本 | 初步變數篩選 |
| 11 | 分組比較 | Trellis plots（lattice：`dotplot`, `xyplot`） | 依類別切 panel 比較 |

【評註】0930 的實戰腳本在第 2 步的位置改用了更穩健的三件套（`str()` / `summary()` / `colSums(is.na())`）
而不是 `attach()`，並在第 10 步之後多加了 `cor()` 相關矩陣。**這是老師自己示範的「正式做法」**，
轉 Python 時應以 0930 版本為準。

### 1.3 【材料原文】EDA Code 完整原始碼（逐字抄錄）

```r
####-------------------------------------------------------####
####  Business Analytics
####  Dr. Jiun-Yu Yu
####  Department of Business Administration
####  National Taiwan University
####  Lecture 2-1: Exploratory Data Anaylsis (EDA)
####-------------------------------------------------------####


########  R Basics  ########

##  Value assign:
n <- 15

##  Case sensitive:
x <- 1
X <- 10

##  Value replace:
n <- 10 + rnorm(1)

##  Need some help?
help(rnorm)
?rnorm
help.start()

##  Change directory: Change manually on GUI, or
setwd("D:/R_work")

##  Load package:
library(MASS)

##  Install package: Install manually on GUI, or
install.packages(“fBasics")
	# You will be asked to highlight the mirror nearest to you for 
	# downloading (e.g. Taipei), then everything else is automatic.


##  Inspect packages currently loaded:
search()




########  Exploratory Data Anaylsis (EDA)  ########

## Read data
HOMES <- read.csv("HOMES.csv", header=TRUE)
attach(HOMES)
price

## Histogram + Boxplot
hist(price,ylab = "Frequency", xlab = "Home Price (in $ thousands)") 
boxplot(price, main="Boxplot of Home Price")

## Measures of Location
mean(price);  median(price)

## Measures of Spread / Dispersion
sd(price);  var(price)
min(price);  max(price);  range(price)
quantile(price, c(0.25,0.5,0.75));  summary(price)
length(price)

## Measures of Shape
library(fBasics)
skewness(price)	# works with package ��fBasics��
kurtosis(price)	# works with package ��fBasics��

## Setting plot area
par(mfrow=c(1,2))
par(pty="s")

## Scatter plot
plot(size, price, pch=1, lwd=1)
title("(a)", lwd=2)

## Scatter plot with regression line
plot(size, price, pch=1, lwd=1)
abline(lm(price~size), lwd=2)
title("(b)", lwd=2)

dev.off()

## Integrated plot
par(fig=c(0,0.7,0,0.7))
plot(size, price, lwd=1)
abline(lm(price~size), lwd=1)

par(fig=c(0,0.7,0.65,1), new=TRUE)
hist(size, lwd=1)

par(fig=c(0.65,1,0,0.7), new=TRUE)
boxplot(price, lwd=1)

## Scatterplot Matrix
pairs(HOMES)

pairs(HOMES, panel=function(x,y)
	{abline(lsfit(x,y)$coef, lwd=1); points(x,y)})




########  Trellis Plots  ########

library(lattice)

## Single month, 3 channels, 6 cities, 4 coffees
coffee1 <- read.csv("coffee_trellis1.csv", header=TRUE)
coffee1$county <- factor(coffee1$county, level=c("TCC","TNC","KHC","TPE","NTPC","TYC"))
coffee1$channel <- factor(coffee1$channel)

dotplot(name ~ revenue | county, data = coffee1, group = channel, 
key = list(space = "right", text = list(levels(coffee1$channel)), points = list(pch = 1:3)),
pch = 1:3, col = "black", xlab = "revenue")


## Single channel, 4 coffees, monthly 
coffee2 <- read.csv("coffee_trellis2.csv", header=TRUE)
coffee2$county <- factor(coffee2$county, level=c("TCC","TNC","KHC","TPE","NTPC","TYC"))
coffee2$month <- factor(coffee2$month)
coffee2$name <- factor(coffee2$name)

xyplot(revenue ~ month | county, data = coffee2, type = "o", groups = name, 
key = list(space = "right", text = list(levels(coffee2$name)), points = list(pch = 1:4)), 
pch = 1:4, col.line = "darkgrey", col.symbol = "black",
xlab = "month", ylab="revenue")


# Single channel, 4 coffees, weekly 
coffee3 <- read.csv("coffee_trellis3.csv", header=TRUE)
coffee3$county <- factor(coffee3$county, level=c("TCC","TNC","KHC","TPE","NTPC","TYC"))
coffee3$week <- factor(coffee3$week)
coffee3$name <- factor(coffee3$name)

xyplot(revenue ~ week | county, data = coffee3, type = "o", groups = name, 
key = list(space = "right", text = list(levels(coffee3$name)), points = list(pch = 1:4)), 
pch = 1:4, col.line = "darkgrey", col.symbol = "black",
xlab = "week", ylab="revenue")
```

> 【評註】`install.packages(“fBasics")` 的左引號是全形彎引號，是原始檔的錯字（R 會報錯）。
> `# works with package ??fBasics??` 的 `??` 是原檔的編碼損毀（原本應是彎引號）。逐字保留。

### 1.4 【材料原文】各步驟的判讀與操作要點（0909 講義）

**資料讀取**
- `HOMES <- read.csv("HOME.csv", header = True)`：`read.csv` 用來讀 excel 檔案中 csv 格式的儲存檔。`header = True` 代表讀取的檔案資料中，標題（第一列）是變數名稱。
- 到這一步，R 其實是還沒有對變數名稱進行指派，所以輸入 HOMES 只會有整個資料表回傳。
- `attach(HOMES)`：attach 會將整個資料集展開後，將標題指派為變數名稱，這一步之後，輸入對應的標題，就會回傳對應的列資料。
- attach 之後輸入 `Price`，就會回傳 Price 這一列含有的所有資料，會以 vector 的形式來呈現。
- 結束分析：`detach`

**畫直方圖**
- `hist(Price, ylab = "Frequency", xlab = "Home Price (in $ thousands)")`
- ylab 代表 y 軸的 label 是什麼，xlab 代表 x 軸的 label 是什麼。
- X 軸間距是可以自行設定的。

**Box plot**
- `boxplot(price, main = "Boxplot of Home Price")`；main 代表這張圖的標題名稱為何。

**Numerically description**
- Measure of location（集中趨勢量數）：平均數 `mean(Price)`、中位數 `median(Price)`
- Measure of Spread / Dispersion（分散趨勢量數）：
  - 標準差 `sd(Price)`、變異數 `var(Price)`
  - 最小值 `min(Price)`、最大值 `max(Price)`、最小值與最大值範圍 `range(Price)`
  - 全距 `max(Price) - min(Price)`
  - 四分位數 `quantile(price, c(0.25,0.5,0.75))`
  - 以上全部顯示 `summary(Price)`
  - 該 vector 中含有多少元素（element）`length(Price)`
- Measure of shape（形狀量數）：偏態係數 `skewness(Price)`、峰態係數 `kurtosis(Price)`；以上兩個要先裝 "fBasics" 這個 package。

**Scatter plot 版面**
- `par(mfrow=c(1,2))`：這張圖要分成左右 2 塊。`c(a,b)`，a 代表的是列（row）、b 代表的是行（column）。如果寫的是 `c(2,1)`，這張圖會分成上下 2 塊。
- `par(pty="s")`：s = square，表示要把圖形畫成「正方形」。如果沒有設定，default 會是橫或直的長方形（看資料決定）。
- `plot(size,price,pch=1,lwd=1)`：plot（x 軸資料, y軸資料, 資料點樣式, 直線寬度）。pch 代表資料點樣式，`pch = 1` 樣式是空心小圓。lwd 代表直線寬度。
- `title("(a)",lwd=2)`：可以用 `main = "標題"` 在一開始設定圖形標題，也可以用 `title("標題",lwd=2)` 來額外設定標題內容。
- `abline(lm(price~size),lwd=2)`：abline( ) 代表在圖形內加入一條線的意思；lm 表 linear model；波浪符名稱：tilde。`abline(lm( y軸資料~x軸資料),lwd=2)`。
- 圖形生成完後要使用，可以直接在圖上按右鍵：複製成 metafile／複製成 bitmap／儲存成 postscript。**以上都可以直接拿來使用，就是不要用螢幕截圖（很笨）**。
- 工作結束後：可以直接圖形右上角打叉關掉，或輸入 `dev.off()`（device off）。

**Integrated plots（疊圖）**
- 左下角散佈圖：`par(fig=c(0,0.7,0,0.7))`；`fig = c(x1,x2,y1,y2)`，the partial area for plot。
- 上方直方圖：`par(fig=c(0,0.7,0.65,1),new=TRUE)` + `hist(size,lwd=1)`
- 右方盒狀圖：`par(fig=c(0.65,1,0,0.7),new=TRUE)` + `boxplot(price,lwd=1)`
- 簡單來說，這邊就是在疊圖，將 scatter plot 畫出來後，x 軸同樣刻度對應往上畫出直方圖；y 軸同樣刻度對應往右畫出盒狀圖；可以進行較多層次的比對。
- 註：**Size 是右偏分配，Price 也是右偏分配，讓整個資料趨勢呈現左下右上。**

**Scatter plot matrix（散佈圖矩陣）— 判讀規則**
- 會有一個很大的矩陣，裡面每個位置都是散佈圖，可以知道兩兩變數間的散佈圖關係。
- `pairs(HOMES)`
- **類別變數不要拿來畫 scatter plot，沒意義（只會看到格點）。**
- 加迴歸線版本：`pairs(HOMES,panel=function(x,y) {abline(lsfit(x,y)$coef, lwd=1) ; points(x,y)})`
- 將所有 scatter plot 都加上迴歸線，每張圖都會有對應的迴歸線，有些迴歸線就可以看出沒有意義（例如：類別變數 v.s 類別變數）。
- **所以繪製 scatter plot matrix 的步驟在 EDA 時，可以算是一種初步的資料篩選過程。**

**Trellis plots**
- 要安裝 lattice 套件 → `library(lattice)`
- Trellis plot（格狀圖、格子圖）是一種將資料「依照某個或多個分類變數」切割成多個小圖 (panels) 的方式。
- 每個小圖顯示相同類型的圖形（例如散點圖、長條圖），但針對不同的類別組別分開呈現。
- 這種方式讓我們能夠一次比較多個群體的分布或關係。
- 資料量太多可以有以下操作：Windows：Ctrl+L → 直接把 Console 的內容清空。

**`$` 與 `attach()` 與 `factor()`**
- `coffee1` 是一個資料框 (data frame)，就像一張表格，裡面有很多欄位。當我們要使用資料框裡的某一個欄位時，可以用 `$` 來指定。
- 如果沒有使用 `attach(coffee1)`，R 不會直接認得 `county` 這個名字。
- 使用 `attach(coffee1)` 之後，你就可以直接打 `county` 而不用加 `$`。**但這樣可能會和其他變數名稱衝突（例如不同資料框中都有同名欄位）。因此在實務上，建議還是習慣用 `$` 來存取欄位，比較清楚也比較安全。**
- `factor(coffee1$county, levels = c("TCC","TNC","KHC","TPE","NTPC","TYC"))`
  - `factor()` 用於將變數轉換成類別 (categorical) 變數，並透過 `levels` 定義所有可能的類別名稱及其顯示順序。
  - 這樣會建立類別的順序，但**不代表類別之間具有數值上的大小關係**。
  - 在統計模型（例如迴歸或 ANOVA）中，`levels` 中的第一個類別通常會被視為**參考組 (reference level)**，這是一種**模型處理的慣例**，而不是 factor 本身具有的特性。

### 1.5 【材料原文】0930 實戰版 EDA 腳本（逐字抄錄）

```r
####-------------------------------------------------------####
####  Business Analytics
####  Lecture 2-1: Exploratory Data Analysis (EDA)
####  Dataset: steel_ind_energy_a.csv (absolute path)
####-------------------------------------------------------####

## 需要時才安裝（課堂有用到）
if (!requireNamespace("fBasics", quietly = TRUE)) install.packages("fBasics")
library(fBasics)

## 讀檔（用絕對路徑；將 \ 改為 / 以避免跳脫字元問題）
file_path <- "C:/Users/user/Desktop/商管統計資料分析/In-class pratical 1/steel_ind_energy_a.csv"
dat <- read.csv(file_path, header = TRUE)

## 快速檢視與缺漏
str(dat)
summary(dat)
colSums(is.na(dat))

## 直方圖 + 盒鬚圖（依講義做法，針對目標變數）
hist(dat$Usage_kWh, ylab = "Frequency", xlab = "Usage (kWh)", main = "Histogram of Usage_kWh")
boxplot(dat$Usage_kWh, main="Boxplot of Usage_kWh")

## 位置量數（講義）
mean(dat$Usage_kWh); median(dat$Usage_kWh)

## 分散趨勢量數（講義）
sd(dat$Usage_kWh); var(dat$Usage_kWh)
min(dat$Usage_kWh); max(dat$Usage_kWh); range(dat$Usage_kWh)
quantile(dat$Usage_kWh, c(0.25,0.5,0.75)); summary(dat$Usage_kWh)
length(dat$Usage_kWh)

## 形狀量數（講義：fBasics）
skewness(dat$Usage_kWh)   # 偏態
kurtosis(dat$Usage_kWh)   # 峰態

## 散佈圖（講義：含回歸線）
par(mfrow=c(1,2))
plot(dat$CO2, dat$Usage_kWh, pch=1, lwd=1, xlab="CO2 (dataset scale)", ylab="Usage (kWh)")
abline(lm(Usage_kWh ~ CO2, data = dat), lwd=2); title("(a)", lwd=2)

plot(dat$Lagging_Current, dat$Usage_kWh, pch=1, lwd=1, xlab="Lagging_Current", ylab="Usage (kWh)")
abline(lm(Usage_kWh ~ Lagging_Current, data = dat), lwd=2); title("(b)", lwd=2)

dev.off()

## 散佈圖矩陣（講義：pairs + 自訂 panel 畫回歸線）
vars <- c("Usage_kWh","Lagging_Current","Leading_Current","CO2",
          "Lagging_Current_Power_Factor","Leading_Current_Power_Factor","NSM")
pairs(dat[, vars])

pairs(dat[, vars],
     panel = function(x, y){
       abline(lsfit(x, y)$coef, lwd=1)
       points(x, y)
     })

## 相關矩陣（講義）
cor(dat[, vars])
```

### 【評註】這回答什麼行銷/商業問題

EDA 回答的是「**在建任何模型之前，我手上這批資料到底長什麼樣、能不能用**」。
具體到行銷場景：
- `hist` + `skewness`：客單價／回購間隔通常右偏 → 直接跑迴歸會違反常態假設，先在這裡就發現。
- `boxplot`：找出離群的大客戶（VIP）或異常訂單，決定要不要獨立處理。
- `pairs` + `cor`：在放進模型前先看哪些行銷變數（廣告費、曝光、點擊）彼此高度相關 → 預告後面會有共線性問題。
- Trellis plot：**通路 × 縣市 × 商品**的三維比較，是行銷最常見的切面分析（EDA Code 的 coffee 範例正是「6 縣市 × 3 通路 × 4 品項」的營收比較）。

---

## 2. Simple Linear Regression（SLR）（0909 + SLR Code）

### 2.1 【材料原文】變數定義

- $Y$：反應變數（response variable）
  - 又稱「依變數」、「結果變數」、「輸出變數」
  - Quantitative response variable
  - Dependent、Outcome、Output variable
- $X$：解釋變數（explanatory variable）
  - 又稱「自變數」、「輸入變數」、「預測變數」
  - Quantitative explanatory variable
  - Predictor、Independent variable、Input variable、Covariate
- $E(Y|X) = 90.38X + 3089.26$
  - Expected value of $Y$ given $X$
  - 條件期望值（Conditional expected value）
  - 表示給定 $X$ 在某值之下，$Y$ 的期望值是多少

### 2.2 【材料原文】模型

$$Y_i = \beta_0 + \beta_1 X_i + \varepsilon_i,\quad i=1,2,\dots,n$$

- $\beta_0$：直線在 $Y$ 軸上的截距，代表當 $X=0$ 時，$Y$ 的期望值。
- $\beta_1$：斜率，代表 $X$ 每增加 1，$Y$ 平均會增加多少。
- $\varepsilon_i$：誤差，代表「直線無法完全解釋的隨機部分」。用以解釋實際資料點與迴歸直線之間的差距。下標 $i$ 代表每個不同的資料點。
- 可以理解為：$Y_i = \text{deterministic part} + \text{random error}$

- **核心問題**：我們關心當 $X$ 改變 1 單位時，$Y$ 會改變多少。
- **注意！迴歸模型描述的是關聯，不是因果關係，觀察性資料不能直接推論因果關係。**

X 與 Y 可能的關係：
- 正相關（同向變動）：$X$ 增加時，$Y$ 也增加。
- 負相關（反向變動）：$X$ 增加時，$Y$ 減少。
- 無明顯關係：$X$ 的改變不影響 $Y$。

### 2.3 【材料原文】SLR 的模型假設（六項）

1. **線性關係（Linearity assumption）**
   - $E[Y|X] = \beta_0 + \beta_1 X$，即 $X$ 與 $Y$ 的期望值是線性關係。
   - 用意：我們假設「Y 跟 X 的關係大致像一條直線」，而不是彎來彎去。
2. **誤差期望為零**
   - $E[\varepsilon_i] = 0$；Mean zero（課堂上說的）。※ $\varepsilon$ 也是 Random variable
   - 用意：誤差只是隨機的雜訊，不會永遠高估或低估。
3. **同質變異性（Homoscedasticity）**
   - $\text{Var}(\varepsilon_i) = \sigma^2$；Constant variance（課堂上說的）。
   - 用意：不論 X 大還是小，誤差的大小應該差不多；就像散布在迴歸線上下的點，應該均勻分布。
   - 白話：誤差的變異數在不同 $X$ 水準下都是一樣的，不會隨 $X$ 大小而改變。
4. **獨立性（Independence）**
   - 誤差項彼此獨立。Independent variance。
   - 用意：一個人的誤差不會影響另一個人的誤差（例如不同受訪者之間的誤差不應該串連）。
5. **最小平方估計法下的迴歸係數**
   - $E(\hat{\beta}_1)=\beta_1$：$\hat{\beta}_1$ 是 $\beta_1$ 的不偏估計量。
   - $\text{Var}(\hat{\beta}_1)=\sigma^2\left(\dfrac{1}{\sum_{i=1}^n(X_i-\bar{X})^2}\right)$
     - 變異數與誤差大小 $\sigma^2$ 成正比，與 $X$ 的分散程度呈反比。
     - $X$ 分布很分散（$\sum(X_i-\bar{X})^2$ 會膨脹的很大），斜率會估得更準。
     - 如果所有 X 幾乎一樣（$\sum(X_i-\bar{X})^2\rightarrow 0$），整筆資料看不太出什麼變化，斜率就估不準。
   - $E(\hat{\beta}_0)=\beta_0$
   - $\text{Var}(\hat{\beta}_0)=\sigma^2\left(\dfrac{1}{n}+\dfrac{\bar{X}^2}{\sum_{i=1}^n(X_i-\bar{X})^2}\right)$
     - 截距的變異數，除了跟誤差大小、$X$ 的分散程度有關，還會受到「樣本平均 $\bar{X}$」的影響。
     - 樣本數 $n$ 很多，截距會估得更準；$X$ 分布很分散，截距會估得更準。
     - 如果所有 $X$ 都很集中或樣本太少，截距估計就會比較不準。
   - $\text{Cov}(\hat{\beta}_0,\hat{\beta}_1)=-\sigma^2\left(\dfrac{\bar{X}^2}{\sum_{i=1}^n(X_i-\bar{X})^2}\right)$
     - **截距項和係數呈現「負相關」。如果斜率估計變大，通常截距估計會相對變小，反之亦然。**
     - 直觀而言，因為迴歸線必須「繞過」數據的平均位置，一端調高就得在另一端調低，兩者有牽制關係。
6. **常態性（Normality）**
   - 2～4 項基礎假設成立後，就可以假設 $\varepsilon_i$ 服從常態分配：$\varepsilon_i \sim N(0,\sigma^2)$
   - 誤差的分布應該長得像「鐘形曲線」，這樣統計推論（t 檢定、信賴區間）才成立。

- **應用情境**：行銷數據分析中，若「廣告費用」與「銷售額」之間呈遞減報酬，可能違反線性關係假設，需要轉換模型。

### 2.4 【材料原文】最小平方估計（LSE）

母體（真實模型）：
$$Y_i=\beta_0+\beta_1X_i+\varepsilon_i,\ i=1,2,\dots,n$$
$$E(Y|X)= \mu(Y|X)=b_0+b_1X$$
（上面兩種寫法一樣意思。描述真實世界的發生過程，因此會存在誤差項。）

估計模型（變數上面掛帽子符號）：
$$\hat{Y}_i=\hat{\beta}_0+\hat{\beta}_1X_i,\ i=1,2,\dots,n$$
$$E(\hat{Y}|X)= \hat{\mu}(Y|X)=\hat{\beta}_0+\hat{\beta}_1X$$
我們用樣本資料估出係數，得到一條預測線，因此線上所得到的值就是正確估計的 $\hat{Y}$，本身不會再帶 $\varepsilon$。

**差異**：母體方程式裡要加誤差項，因為現實世界的 $Y$ 不會剛好落在迴歸線上。但當我們用估計值去算 $\hat{Y}$ 的時候，那就是「模型預測線」，它已經把誤差排除掉了，所以不用再加 $\varepsilon$。

殘差 $\hat{\varepsilon}_i = Y_i-\hat{Y}_i$，在**含截距的模型**下，有以下數學性質：
$$\sum_{i=1}^n\hat{\varepsilon}_i=0,\qquad \sum_{i=1}^nX_i\hat{\varepsilon}_i=0,\qquad \sum_{i=1}^nY_i\hat{\varepsilon}_i=0$$

$\varepsilon_i$ 的性質：
- $E(\varepsilon_i) = 0$ 或 $E(\varepsilon_i|X) = 0$
- $\text{Var}(\varepsilon_i) = \sigma^2$ 或 $\text{Var}(\varepsilon_i|X)$
- $\text{Cov}(\varepsilon_i,\varepsilon_j)=0,\ \forall i\neq j$
- $\Rightarrow E(Y_i)= \beta_0 +\beta_1X_i,\ \text{Var}(Y_i)=\sigma^2$

目標函數：
$$\min_{\beta_0, \beta_1} \sum_{i=1}^n \left( Y_i - \beta_0 - \beta_1 X_i \right)^2$$

估計結果：
$$\hat{\beta}_1=\frac{\sum(X_i-\bar{X})(Y_i-\bar{Y})}{\sum(X_i-\bar{X})^2},\qquad \hat{\beta_0} = \bar{Y} -\hat{\beta_1}\bar{X}$$

- **直觀解釋**：找到一條「最佳擬合線」，讓點到線的垂直距離平方和最小。
- **應用情境**：根據房屋坪數 (X) 來預測房價 (Y)，LSE 幫我們找到最合理的「價格—坪數」關係。

### 2.5 【材料原文】$R^2$ 與變異拆解

- **SST (Total Sum of Squares)**：總變異，衡量 $Y$ 相對於平均數 $\bar{Y}$ 的總變動量。
  $$SST=\sum_{i=1}^n(Y_i-\bar{Y})^2$$
  - 沒有模型時，唯一能用的估計就是樣本平均 $\bar{Y}$ ⇒ SST 的來源。因此 **SST 可以被視為「沒有模型時的總誤差」**。
  - 有模型時，用迴歸線估計值 $\hat{Y}$ 來進行估計 ⇒ SSE 的來源。因此 **SSE 可以被視為「有模型後剩下的誤差」**。
- **SSE (Sum of Squared Errors)**：殘差平方和，衡量模型未能解釋的誤差。
  $$SSE=\sum_{i=1}^n\hat{\varepsilon}_i^2=\sum_{i=1}^n(Y_i-\hat{Y}_i)^2=\sum_{i=1}^n(Y_i-\hat{\beta}_0-\hat{\beta}_1X_i)^2$$
  - $\varepsilon_i$：真實（母體）誤差，無法被觀測。$\hat{\varepsilon}_i$（有的會寫 $e_i$）代表誤差的「估計值」。
  - Residual Standard error：$\hat{\sigma}=\sqrt{\dfrac{SSE}{n-2}}=\sqrt{\dfrac{\sum_{i=1}^n\hat{\varepsilon}_i^2}{n-2}}$
- **SSR (Regression Sum of Squares)**：迴歸平方和，衡量模型所解釋的部分。$SSR=SST-SSE$

$R^2$：
$$R^2 =\frac{SSR}{SST}= 1 - \frac{SSE}{SST} = \frac{\text{解釋變異}}{\text{總變異}},\qquad 0 \le R^2 \le 1$$

- 衡量模型能解釋多少比例的資料變異。例如 $R^2 = 0.85$ → 模型解釋了 85% 的變異。
- **注意（三條使用戒律）**：
  1. $R^2$ 會因加入額外解釋變數而不降（**單調不減**），不代表模型一定更好。
  2. 在使用 $R^2$ 比較不同模型時，**應確保這些模型具有相同的 $Y$（應變數）**，否則這樣的比較沒有意義。
  3. 在單一解釋變數的迴歸（即 SLR）下，相關係數 $r = \pm\sqrt{R^2}$，相關係數不僅能指出關聯強度更能指出關聯「方向」。
- 應用情境：在財務分析中，用於評估股價與利率之間的解釋程度。

### 2.6 【材料原文】統計推論（t 檢定、CI、假說檢定）

因為真實的 $\sigma$ 很難知道，所以我們通常會使用估計值 $\hat{\sigma}$，因此原本的檢定統計量不再服從常態，而是服從 t 分配（自由度 $n-2$，因為估計了兩個參數）。

$$SE_{\hat{\beta}_1} = \sqrt{ \frac{ \hat{\sigma}^2 }{ \sum_{i=1}^n (X_i - \bar{X})^2 } }=\sqrt{ \frac{ \frac{SSE}{n-2} }{ \sum_{i=1}^n (X_i - \bar{X})^2 } }$$
$$T_{\hat{\beta}_1} = \frac{\hat{\beta}_1-\beta_1}{SE_{\hat{\beta}_1}} \sim t_{n-2}\quad\text{（檢定 X 對 Y 的影響是否顯著} \ne 0\text{）}$$
$$SE_{\hat{\beta}_0}= \sqrt{ \sigma^2\left(\frac{1}{n}+\frac{\bar{X}^2}{\sum_{i=1}^n(X_i-\bar{X})^2}\right)},\qquad T_{\hat{\beta}_0} = \frac{\hat{\beta}_0-\beta_0}{SE_{\hat{\beta}_0}} \sim t_{n-2}$$

**信賴區間的正確解讀**
- 統計學上的解釋：若我們重複多次抽樣，那麼這些信賴區間中，約有 95% 會包含真正的 $\beta_1$。或：我們有 95% 的信心，區間 $[\ ]$ 會包含真實的母體統計量。
- 白話解釋（投影片例子）：我們用樣本資料算了一個區間（$51.75$ 到 $129.01$）。解讀方式：我們有 95% 的信心，區間 $[51.75,129.01]$ 包含了真實的 $\beta_1$。
- **注意！不是說「$\beta_1$ 有 95% 機率落在這裡」，因為 $\beta_1$ 是固定值，沒有隨機性。真正具有隨機性的，是「我們抽取到的樣本」。**
- 公式：$\hat{\beta}_1 \pm t_{n,p_{0.975}}\cdot SE(\hat{\beta}_1)$
  - 投影片數字：$\hat{\beta}_1 = 90.38$、$SE(\hat{\beta}_1) = 12.14$、$t = 3.182$
  - $[90.38-3.182\times12.14,\ 90.38+3.182\times12.14]=[51.75,129.01]$

**假說檢定**
- 問題的核心：某個效果「是真的存在」還是「只是樣本隨機出來的結果」？**檢驗推論關係，而非因果關係！** 例如：廣告費增加 → 銷售額真的會增加嗎？
- 虛無假說 $H_0$：預設立場，通常會先假定情形「沒有發生」，或「統計量＝某數」。通常既定事實，或是需要被檢驗的立場之對立面會擺在這。例：$H_0:\beta_1=0 \rightarrow$ 廣告費對銷售額沒有影響。
- 對立假說 $H_1$：想驗證是否真實、需要被檢驗的會放對立假說。**若對立假說屬實，會「拒絕虛無」，而不是以「接受對立」來呈現。** 例：$H_1:\beta_1\neq0 \rightarrow$ 廣告費對銷售額有影響。

檢驗步驟：
1. 先假設 $H_0$ 成立
2. 計算樣本統計量（如 p-value 或 t-value），看看在選定的信心水準（通常採 95%）下，統計量是否包含於該水準下的信賴區間。
3. 若在區間內，選擇接受虛無假說，拒絕對立假說。
4. 若在區間外，選擇拒絕虛無假說，但不會說接受對立假說。
5. 一般會說，在統計上顯著拒絕虛無假說。
6. **假說檢定可以想像成是有固定流程的寫故事內容！**

p-value 的意義：
- 代表當 $H_0$ 為真時，觀察到一個像樣本結果一樣或更極端的機率。
- p-value 很小 → 「如果 $H_0$ 真的對，出現這樣的結果非常罕見」，所以我們懷疑 $H_0$ 不成立。
- p-value 很大 → 「這樣的結果在 $H_0$ 成立下並不稀奇」，所以沒理由拒絕 $H_0$。
- 常見標準：$p < 0.05 \rightarrow$ reject $H_0$，表在 95% 信心水準下效果顯著。
- 例子：假設你認為硬幣是公平的（$H_0$），結果連續拋出 10 次正面，這樣的結果機率只有 0.1%（p-value 很小），所以你會懷疑硬幣其實不公平。

t-value 的意義：
$$\text{t-value}=\frac{\text{估計值}-\text{假設值}}{\text{標準誤}}$$
- t-value 大 = 差距明顯大於隨機誤差的可能範圍；t-value 小 = 差距不大，可能只是隨機造成。
- 可以把 t-value 想成「差距的標準化分數（z-score）」，$t=3$ 就代表「估計值比假設值大了 3 個標準誤」。

完整檢定範例（投擲硬幣 50 次，35 正 15 反）：
1. 進行假設 $H_0: p=0.5$、$H_1: p\neq 0.5$
2. 決定信心水準 $\alpha = 0.05$（95% 信心水準）
3. 計算檢定統計量 $\hat{p} = \frac{35}{50} = 0.7$，$\hat{z} =\frac{\hat{p}-p_0}{\frac{p_0(1-p_0)}{n}}=\frac{0.7-0.5}{\frac{0.7(1-0.7)}{50}}=2.83$
4. p-value 計算或計算拒絕域（Reject Region），**推薦後者**。$RR= \{ |Z| \ge Z_{0.05} =1.96\}$
5. 判斷「p-value 與 $\alpha$ 之間的大小關係」，或「統計量是否在拒絕域」。$\hat{z} \in RR$
6. 寫結論 → 「拒絕虛無，接受對立」；「不拒絕虛無」。reject null hypothesis，故此硬幣在統計上顯著不公平。

### 2.7 【材料原文】Prediction：CI vs PI

給定新值 $X_0$：$\hat{Y_0}=\hat{\beta_0}+\hat{\beta_1}X_0$

現在給定一個新的資料點 $x_0$，考慮以下兩件事：
- $E(Y|X=x_0)$，平均趨勢大概落在哪？→ 以 **Confidence Interval（CI）** 判斷
- 未來若出現一筆新資料 $Y_{new}$，大概會落在哪？→ 以 **Prediction Interval（PI）** 判斷

**信賴區間（CI）— 用來估「平均」**
$$\hat{Y}(x_0) \pm t_{n-2,1-\frac{\alpha}{2}}\cdot SE_{\hat{Y}(x_0)},\qquad SE_{\hat{Y}(x_0)}=\hat{\sigma}\sqrt{\frac{1}{n}+\frac{(x_0-\bar{X})^2}{\sum_{i=1}^n(X_i-\bar{X})^2}}$$
其中 $\hat{\sigma}=\sqrt{\frac{SSE}{n-2}}$（因 $\hat{\beta}_0$ 和 $\hat{\beta}_1$ 已被估計，自由度少 2）
- 解釋：給定 $x_0$ 之下，趨勢線的平均位置（條件期望）之合理範圍。

**預測區間（PI）— 用來估「個體」**
$$\hat{Y}(x_0) \pm t_{n-2,1-\frac{\alpha}{2}}\cdot SE_{\hat{Y}(x_0)},\qquad SE_{\hat{Y}(x_0)}=\hat{\sigma}\sqrt{1+\frac{1}{n}+\frac{(x_0-\bar{X})^2}{\sum_{i=1}^n(X_i-\bar{X})^2}}$$
- 解釋：給定 $x_0$ 之下，**單一新觀測值**的合理範圍。

**使區間變窄的因素（CI 與 PI 共通）**
- $n \uparrow$（樣本數變多）→ $\frac{1}{n} \downarrow$ ⇒ 估計變得更準確。
- $x_k$ 接近平均數 $\bar{X}$ ⇒ 中心位置估計最穩定，**向外推時區間會變寬**。
- 殘差標準差 $\hat{\sigma} \downarrow$ ⇒ 模型誤差小，區間自然變窄（精確）。
- 信心水準低（例如 90% 而非 95%）⇒ 區間變窄。

**兩個區間的差異**
- 因包含個體誤差，因此 **PI 一定比 CI 寬**（多一筆數據）。
- 可以理解成：預測一個人（個體）永遠比估平均更難。
- 數學公式上可以明顯發現，預測區間在 SE 的根號中多了一個 1（新數據）。
- CI 看的是「迴歸線的平均位置」→ 我們對**趨勢**有多確定。
- PI 看的是「新來一點會落哪」→ 我們對**個體**有多確定。
- 圖例：紅色虛線＝信賴區間（**正常情況下，迴歸線理應要在區間內**）；藍色虛線＝預測區間。

### 2.8 【材料原文】SLR Code 完整原始碼（逐字抄錄）

```r
####-------------------------------------------------------####
####  Business Analytics
####  Dr. Jiun-Yu Yu
####  Department of Business Administration
####  National Taiwan University
####  Lecture 2-2: Simple Linear Regression (SLR)
####-------------------------------------------------------####


########  Simple Linear Regression (SLR)  ########

## Read data
HOMES1 <- read.csv("HOMES1.csv")
	attach(HOMES1)

## Summary
lm1 <- lm(price ~ size, data=HOMES1)
summary(lm1)

## Scatterplot +　Regression line
plot(HOMES1$size, HOMES1$price, ylab = "Home Price", xlab = "Floor Size")
abline(lm1)

## Confidence interval
confint(lm1)


########  Diagnostic Plots  ########

## Diagnostic Plots - Residual plot
plot(HOMES1$size, residuals(lm1), xlab="X", ylab="Residuals")
abline(h=0)

plot(fitted(lm1), residuals(lm1), xlab="Fitted", ylab="Residuals")
abline(h=0)

## Diagnostic Plots - Histogram on Residuals
hist(residuals(lm1))

## Diagnostic Plots - QQ-plot
lm1$fitted;		fitted(lm1)
lm1$residual;	residuals(lm1)
qqnorm(residuals(lm1), ylab="Residuals")
qqline(residuals(lm1))


########  Confidence Interval (CI) & Prediction Interval (PI)  ########

## Confidence Interval & Prediction Interval of Y given new observed x
xnew <- data.frame(size=200)
ci <- predict(lm1, xnew, interval="confidence", level=0.95)
pi <- predict(lm1, xnew, interval="prediction", level=0.95)


## Advanced Practice: CI & PI plots

## CI plot
xy <- data.frame(size=pretty(HOMES1$size))
yhat.ci <- predict(lm1, newdata=xy, interval="confidence")
ci <- data.frame(lower=yhat.ci[,"lwr"], upper=yhat.ci[,"upr"])

plot(HOMES1$size, HOMES1$price, main ="Confidence and Prediction Interval", ylab = "Home Price", xlab = "Floor Size")
abline(lm1)

lines(xy$size, ci$lower, lty=2, col="red")
lines(xy$size, ci$upper, lty=2, col="red")

## PI plot
yhat.pi <- predict(lm1, newdata=xy, interval="prediction")
pi <- data.frame(lower=yhat.pi[,"lwr"], upper=yhat.pi[,"upr"])

lines(xy$size, pi$lower, lty=2, col="blue")
lines(xy$size, pi$upper, lty=2, col="blue")
```

### 2.9 【材料原文】R 指令逐條說明（0909 R Code 段）

- `HOMES1 <- read.csv("HOMES1.csv")`：讀取資料
- `lm1 <- lm(price ~ size, data=HOMES1)`
  - `lm()` 是指 linear model；`~` 前面是 $Y$（被解釋變數），`~` 後面是 $X$（解釋變數）
  - 在尚未定義 price & size 時，`data=HOMES1` → 指定使用 HOMES 這個資料集中的 price & size 欄位
  - 呈現的結果：
    - **Call**：再次描述一遍現在的 function 是在執行什麼功能。
    - **Residuals（殘差）**：模型預測值與實際觀察值之間的「落差」。
    - **Coefficients**：各項變因的係數，其中 Intercept 指的是截距項。
- `confint(lm)`：找這個模型的 95% 信賴區間（2.5%～97.5% 資料範圍邊界）。**如果這個範圍不包含 0，就代表這個變數對 $Y$ 的影響大概率是真的。**
- `residuals(lm1)`：找你設定的 model 裡的殘差，跑出來會是對應的五十筆資料的 $\hat{\varepsilon}_i$
- `plot(HOMES1$size, residuals(lm1), xlab="X", ylab="Residuals")`：Residual plot，一樣前面是 X，後面是 Y。
- `abline(h=0)`：加上 0 點的線。$h = 0$ means $height = 0$
- `fitted(lm1)`：呈現模型所預估出來的 $\hat{Y}$；另一個呼叫方式 → `lm1$fitted`
- `qqnorm(residuals(lm1), ylab="Residuals")`：畫 Q-Q Plot
- `qqline(residuals(lm1))`：補上 Q-Q Plot 中的對角線
- `xnew <- data.frame(size=200)`：先定義 data frame
- `ci <- predict(lm1, xnew, interval="confidence", level=0.95)`：算 CI。lm1 ⇒ 選用的模型；xnew ⇒ 選用的 dataframe；`interval="confidence"` ⇒ 定義為信賴區間；`level=0.95` ⇒ 選用 95% 信心水準
- `pi <- predict(lm1, xnew, interval="prediction", level=0.95)`：算 PI

### 【評註】這回答什麼行銷/商業問題

SLR 回答「**單一行銷投入對單一績效指標的邊際效果有多大、確不確定**」。
- $\hat{\beta}_1$ = 廣告每多花 1 元，銷售額平均增加多少元（ROI 的直接估計）。
- `confint` 不含 0 → 這個效果在統計上站得住腳，可以拿去跟主管報告。
- CI vs PI 的分野在行銷極重要：CI 回答「這一群客人的**平均**回應」（用於預算配置），PI 回答「**下一個**客人會怎樣」（用於個別化行銷、庫存備貨）。

---

## 3. Multiple Linear Regression（MLR）（0916）

### 3.1 【材料原文】模型與係數解讀

$$E(Y\mid X_1,\dots,X_p)=\beta_0+\beta_1X_1+\dots+\beta_pX_p$$
$$Y_i=\beta_0+\beta_1X_{i1}+\dots+\beta_pX_{ip}+\varepsilon_i,\; i=1,2,\dots,n$$

- **注意！在這裡因為自變數很多，因此明確定義並且辨認變因是很重要的！**
- $\beta_0$：截距，代表在 $X_1=\cdots=X_p=0$ 時 $Y$ 的期望值。
  - 若 0 不具意義，可對各 $X_j$ **中心化**（令 $\bar X_j=0$），則 $\beta_0$ 表示「在平均的 $X$ 上的 $E(Y)$」。
  - 通常是以「樣本均值」中心化（令 $\bar X_j=0$）。此時估計量滿足 $\hat\beta_0=\bar Y-\sum_{j=1}^p \hat\beta_j \bar X_j=\bar Y$，所以**數值上** $\hat{\beta}_0=\bar{Y}$，解讀為「在樣本平均 $X$ 上的 $Y$ 之條件平均的估計」。
- $\beta_j$（$j=1,\dots,p$）：
  - **偏效應（partial effect）**，或稱在 $X_j$ 方向的斜率。
  - 解讀：在 ***holding others fixed***（其他 $X_k$ 固定）的條件下，$X_j$ 增加 1 單位，$Y$ 的條件期望**平均改變** $\beta_j$。
- $\varepsilon_i$：誤差項（線性無法完全解釋的隨機部分），反映測量誤差、遺漏變數、純隨機波動等。
- 可以理解為：$Y_i = \text{deterministic part} + \text{random error}$，deterministic part $=\beta_0+\sum_{j=1}^p\beta_jX_{ij}$。
- **核心問題**：我們關心當 $X_j$ 改變 1 單位時，$Y$ 會改變多少。

**注意事項（三條）**
1. 迴歸模型描述的是關聯性（association），不是因果（causation），觀察性資料不可直接推論因果。
2. 多重共線性（multicollinearity）：若 $X_j$ 彼此高度相關，**係數標準誤會膨脹、t 檢定不穩**。共線性可以透過 VIF 進行診斷。
3. 類別變數處理：$k$ 類需放 $k-1$ 個虛擬變數（dummy variable），且需指定參考組，避免產生虛擬變數陷阱。

**白話解釋（為什麼要「其他變因固定」）**
- 同時有很多變因在動，若只看單一變因，容易把別的因素的影響也算進去。
- MLR 讓你讀到的是「在其它因素不變下，某個變因本身的平均影響」。
- 例：$X_1=$ 參加派對時數、$X_2=$ 讀書時數、$X_3=$ 是否補習（0,1）、$X_4=$ 睡眠時數。在讀書時數與睡眠一樣的條件下，參加派對多 1 小時，期末分數平均少 2 分 $\Longrightarrow \beta_1=-2$。

### 3.2 【材料原文】虛擬變數（Dummy Variable）的建構與解讀 ★

> 這是任務要求的第 4 項（前半）。

以四季作為虛擬變數的例子：

$$D_1=\begin{cases}1, & \text{夏天} \\ 0, & \text{其他}\end{cases},\quad D_2=\begin{cases}1, & \text{秋天} \\ 0, & \text{其他}\end{cases},\quad D_3=\begin{cases}1, & \text{冬天} \\ 0, & \text{其他}\end{cases}$$

**當 $D_1=D_2=D_3=0$ 則代表春天。**

迴歸式：$Y_i=\beta_0+\beta_1D_{i1}+\beta_2D_{i2}+\beta_3D_{i3}+\varepsilon_i$

**係數如何解讀？**
- $\beta_0$：春天的平均。
- $\beta_1$：夏 − 春 的平均差。$>0$ 代表夏高於春；$<0$ 代表夏低於春。
- $\beta_2$：秋 − 春 的平均差。$>0$ 代表秋高於春；$<0$ 代表秋低於春。
- $\beta_3$：冬 − 春 的平均差。$>0$ 代表冬高於春；$<0$ 代表冬低於春。

$$\begin{cases}
E(Y_i\mid D_{i1}=0, D_{i2}=0, D_{i3}=0)=\beta_0 & \text{春季之平均}\\
E(Y_i\mid D_{i1}=1, D_{i2}=0, D_{i3}=0)=\beta_0+\beta_1 & \text{夏季之平均}\\
E(Y_i\mid D_{i1}=0, D_{i2}=1, D_{i3}=0)=\beta_0+\beta_2 & \text{秋季之平均}\\
E(Y_i\mid D_{i1}=0, D_{i2}=0, D_{i3}=1)=\beta_0+\beta_3 & \text{冬季之平均}
\end{cases}$$

**通俗的解釋（三條關鍵規則）**
1. **為什麼是 $k-1$ 個？** 因為模型裡有截距，若四季都各放一個 dummy，又留截距，解釋變數會完全共線（俗稱「**虛擬變數陷阱**」），模型無法估計。
2. **換基準組會不會改結果？** 係數值會換寫法，但**群組平均與預測不變**。選誰當基準，只是為了解讀方便。
3. **係數不是效果大小（effect size）的絕對比較**：不同變數的單位不同，跨變數的 $|\beta|$ 不可直接互比。若有連續變數想比較影響力，要看標準化係數或做對應的效果量。

**交互作用（初步提及）**
- 若懷疑 $X_1$ 的效果會隨 $X_2$ 改變，須加入 $X_1\times X_2$ 這樣的交互項，**將係數解讀回到條件式**。
- 有時候某個變因的影響力，**會因為另一個變因不同而改變**，這就是**交互作用**（interaction）。
- 例：讀書 1 小時對分數的幫助，可能在「派對參加時數很少的人」身上效果比較大，可能在「派對參加時數很多的人」身上效果比較小。
- 寫法上會加一個「$X_1\times X_2$ 的交叉項」。解讀：「讀書的效果，會隨著 party 程度而改變」。

### 3.3 【材料原文】估計：OLS / BLUE / 遺漏變數偏誤

$$SSE=\sum_{i=1}^n\hat{\varepsilon}_i^2=\sum_{i=1}^n(Y_i-\hat{Y_i})^2=\sum_{i=1}^n\left(Y_i-\hat{\beta}_0-\sum_{j=1}^k\hat{\beta}_jX_{ji}\right)^2$$

- 目的與 SLR 一樣，找一組 $\hat\beta$ 讓 SSE 最小；直覺上，就是讓「預測值」整體最貼近「觀察值」。
- 白話解釋：同時考慮所有變因，在其他變因固定下，選出每個變因的係數，讓整體誤差平方和最小。
- 參數個數：$p=k+1$（含截距）；自由度 $=n-p$
- 殘差的標準差（Residual standard error）：$\hat{\sigma}=\sqrt{\dfrac{SSE}{n-(k+1)}}$

**BLUE（最佳線性不偏估計量）** — 當一個估計量滿足 BLUE 性質時，有以下特性：線性／零均值／等變異／誤差獨立／$X$ 非隨機或已知。

**遺漏變數偏誤**：若有重要因素同時影響 $Y$ 又和 $X_1,X_2$ 關聯，卻被放進 $\varepsilon$，就可能讓 $\hat\beta$ 產生偏誤（違反 $E(\varepsilon\mid X)=0$）。

### 3.4 【材料原文】標準化迴歸係數（Beta coefficient）★

**為什麼需要？** 各解釋變數 $X_i$ 單位不同（小時、萬元、km 等），$\hat\beta_i$ 的數值大小不能直接互相比較。因此需要把 $Y$ 與所有 $X_i$ 標準化（standardize, z-score）再跑回歸，得到的係數稱 Beta coefficient，可用來比較「在控制其他變因下，誰的影響力相對大」。

$$Z_Y=\frac{Y-\bar{Y}}{S_Y},\quad S_Y=\sqrt{\frac{\sum_{i=1}^n(Y_i-\bar{Y})^2}{n-1}}$$
$$Z_{X_j}=\frac{X_j-\bar{X_j}}{S_{X_j}},\quad S_{X_j}=\sqrt{\frac{\sum_{j=1}^n(X_{ji}-\bar{X_j})^2}{n-1}}$$

**快速換算：**
$$\hat{\beta}_j^*=\frac{S_{X_j}}{S_Y}\hat{\beta}_j,\quad j=1,2,\dots,k$$

白話解釋：$X_j$ 增加一個標準差，$Y$ 的條件期望值改變 $\hat{\beta}_j^*$ 個標準差。

**使用限制（五條）**
1. 只有一個解釋變數時，退化成 SLR；此時 $\hat{\beta}_j^*$ 的數值等於樣本相關係數 $\pm r_{XY}$。
2. **多變量時的侷限**：$\hat{\beta}_j^*$ 會受**多重共線性**影響。兩個高度相關的變數彼此「分不清」貢獻，$|\hat{\beta}_j^*|$ 可能被稀釋、甚至導致影響方向不穩。比較時請先看 VIF 或相關結構。
3. **有虛擬變數時**：對 0/1 變數做標準化，數學上可行，但解讀不直覺。混合連續與 dummy 的模型中，**不建議**用 $\hat{\beta}_j^*$ 直接比較「誰比較重要」。
4. **含交互作用**：若有 $X_1\times X_2$，應**先將主效應標準化後再生成交互項**，否則尺度解讀會混亂。
5. **模型外比較**：$\hat{\beta}_j^*$ 只能在「同一模型」內比較不同變因的影響程度。不同樣本或不同模型的 $\hat{\beta}_j^*$ 最好不要直接比較。

### 3.5 【材料原文】$R^2$ 為何不能當單一指標 ★

- **$R^2$ 單調不遞減（monotonic non-decreasing）**：多放任一個解釋變數，在樣本內的 SSE 一定不會變大（維持或變小）$\Longrightarrow R^2=1-\frac{SSE}{SST}$ 一定上升或不變。結果而言，以 $R^2$ 進行比較，永遠都是「變數越多越好」，這就是所謂的**過度擬合（overfitting）**。
- **容易誤解成「好模型」**：
  - 高 $R^2$ 不代表好預測，它可能只是把雜訊也一併擬合了，這些訊息若是 in-sample 很好，但若 out-of-sample 就是讓模型變差。
  - **對極端值相當敏感，少數極端點就能把 $R^2$ 拉高。**
  - 不同資料集的 $R^2$ 不可直接比較，因 $R^2$ 受不同變異程度（SST）影響。
- **沒有複雜度懲罰**：$R^2$ 只獎勵「SSE 下降」，不會懲罰「參數變多」。理論上，只要放到「每個樣本一個虛擬變數」，$R^2$ 可以逼近 1，但模型沒有解釋力也無泛化能力。
- **實務替代方案**：
  - 部分 F 檢定（partial F test）：比較「舊模型」vs「加了一組變數的新模型」，檢定新增變數的邊際貢獻是否顯著。也可報告 partial $R^2$ 量化新增變數解釋到的額外變異比例。
  - Adjusted $R^2$（校正後判定係數）。

### 3.6 【材料原文】Adjusted $R^2$

$$\bar{R^2}=1-\left(\frac{n-1}{n-k-1}\right)(1-R^2) \Leftrightarrow \bar{R^2} =1- \frac{\frac{SSE}{n-p}}{\frac{SST}{n-1}}\quad\text{（兩者等價）}$$

其中 $n=$ 樣本數、$k=$ 解釋變數個數、$p=k+1=$ 參數總數（含截距）。

- 以殘差均方 $\frac{SSE}{n-p}$ 相對於總均方 $\frac{SST}{n-1}$ 的比例來定義，分母的自由度自然形成複雜度懲罰。
- **直觀解釋**：新增一個變數會使 SSE 降低，但同時把自由度從 $n-p$ 再減 1。只有當 SSE 的下降大於自由度減少帶來的懲罰時，$\bar R^2$ 才會上升，否則下降。
- 簡單來說，若新增變數後 $\bar R^2$ 沒上升，那麼它在告訴你：「這些變數帶來的誤差下降，不足以抵掉複雜度產生的代價。」
- 與 $R^2$ 的關係：$\bar R^2 \le R^2$；當 $k=0$（只有截距）時 $\bar R^2=0$；變數越多，越容易讓 $\bar R^2$ 下降。
- **注意！**
  - **$R^2$ 才是用來解釋 $Y$ 的變異比例。**
  - **Adjusted $R^2$ 是用來進行模型比較用的**，特別是巢狀模型間的比較。例如：當解釋變數增加時，Adjusted $R^2$ 卻減少了，代表模型已經開始出現過度擬合。
  - $\bar R^2$ 在不同資料集、不同反應變數或資料變異程度差異很大時，不適合直接對比。

### 3.7 【材料原文】Multiple Correlation Coefficient

$$R = \text{cor}(Y,\hat{Y})=\sqrt{\frac{SSR}{SST}}=\sqrt{R^2},\quad R\in[0,1]$$

- $R$ 越接近 1，代表 $\hat{Y}$ 與 $Y$ 越貼合；越接近 0，代表模型幾乎沒有解釋力。
- 與單變量的相關係數不同，**$R$ 沒有正負號，是純粹的強度指標**。
- 加入變數時 $R$（和 $R^2$ 一樣）只會上升或不變，因此**不能拿來做模型選擇**。

### 3.8 【材料原文】殘差標準誤

$$\hat{\sigma}=\sqrt{\frac{SSE}{n-k-1}}=\sqrt{\frac{\sum_{i=1}^n\hat{\varepsilon}_i^2}{n-k-1}}$$

- **OLS 本身並不需要常態假設。** 但要做標準誤、t 檢定、信賴區間等推論，通常會加上零均值／同質變異／獨立／常態四項誤差假設。
- **注意！常態性假設不是估計 $\hat\beta_{ij}$ 與 $\hat\sigma$ 的必要條件，它主要用在小樣本的 t 檢定／信賴區間。**
- 白話解釋：一筆資料在「控制其它變數後」相對於模型平均 $\hat Y$ 的典型誤差量。
- **$\hat{\sigma}$ 與 $R^2$ 互補**：$\hat{\sigma}$ 可以理解成有單位的「絕對誤差」；$R^2$ 可以理解成沒有單位的「相對解釋比例」。
- 註：時間序列或集群資料通常會違反獨立假設。

### 3.9 【材料原文】三個檢定：Global F / Partial F / Individual t ★

> 這是任務要求的第 5 項。以下為完整流程。

#### (A) 全體有用性檢定（Global Usefulness F-Test）

- **核心問題**：「整體來看，解釋變數有沒有用？」
- 假說：$H_0：\beta_0=\beta_1=\dots=\beta_k=0$；$H_1：\beta_j$ 不全為 0，$j=1,2,\dots,k$（或：至少存在一個 $\beta_j$ 不為 0）
- 白話解釋：想證明整體解釋變數有沒有用，那至少有一個變數有解釋力就可以。

$$\text{F-statistics} =\frac{\frac{SSR}{k}}{\frac{SSE}{n-k-1}} = \frac{\frac{(SST-SSE)}{k}}{\frac{SSE}{n-k-1}} =\frac{\frac{R^2}{k}}{\frac{1-R^2}{n-k-1}}$$

- 分子：**模型解釋的變異「平均」**（每個解釋變數分到一份）。
- 分母：**殘差變異的平均**（$\hat\sigma^2=\frac{SSE}{n-k-1}$）。
- 在（誤差零均、等變異、獨立、常態）成立下，$F\sim F_{k,\ n-k-1}$。
- **注意！$F$ 分配本身是一個右偏分配。**

**決策規則**：通常選定 $\alpha = 0.05$。
- critical value $= F_{0.95}(k,n-k-1)$
- p-value $=P(F_{k,\ n-k-1} \ge F_{obs})$
- 若 p-value $< \alpha$ 或落在拒絕域 $\Rightarrow$ Reject $H_0$ $\Longrightarrow$ 整體上「至少有一個」解釋變數有線性效果。

**如何解讀（三條）**
- 較大的 $F$：代表「模型多解釋了一塊變異，且相對噪音不小」，整體有用。
- **$F$ 顯著並不保證每個 $\beta_j$ 都顯著，個別要看 t-Test。**
- **$F$ 顯著 $\ne$ 模型就一定好用。** 還需要進行其他模型診斷：殘差圖、共線性、外點、$\hat\sigma$、交叉驗證誤差等等。

**完整數值範例**：$X_1$（坪數）、$X_2$（屋齡）解釋房價 $Y$，$n=30$，$SST=2000$、$SSE=1200$、$SSR=800$、$k=2$
1. $H_0:\beta_1=\beta_2=0$；$H_1:\beta_1、\beta_2$ 不全為 0
2. $\alpha = 0.05$
3. $F =\frac{800/2}{1200/(30-2-1)}=\frac{400}{1200/27}=\frac{400}{44.444}\approx 9$；$df_1=k=2$、$df_2=30-2-1=27$
4. $RR= \{ F \ge F_{0.95}(2,27) \approx 3.35\}$；p-value $=P(F_{(2,27)}\ge 9.00)\approx 0.001$
5. $F \in RR$，reject $H_0$
6. 結論：在 5% 顯著水準下，整體模型具有統計上顯著的解釋力。／兩個解釋變數中至少有一個對房價 $Y$ 的條件期望值有線性影響。
- 後續可以看各別 t-Test 與信賴區間，判斷哪些 $\beta_j$ 顯著，以及效果大小方向。

#### (B) 巢狀結構下的部分 F 檢定（Nested model Partial F-Test）★★

- **核心問題**：實務上，常會懷疑：是不是考量了太多變數而造成「過度擬合」？例如：在 $k$ 個候選解釋變數裡，是否其實只需要其中 $r<k$ 個就夠了？

**模型設定**
- 縮減模型（reduced model）：$r$ 個變數，$E(Y)=\beta_0+\beta_1X_1+\dots+\beta_rX_r$
- 完整模型（complete model）：$k$ 個變數，$E(Y)=\beta_0+\beta_1X_1+\dots+\beta_rX_r+\beta_{r+1}X_{r+1}+\dots+\beta_kX_k$
- **巢狀關係：縮減模型就是把完整模型中某些係數鎖成 0 的特例，兩者必須是巢狀關係，否則不能做 Partial F-test。**

**假說**
- $H_0：\beta_{r+1}=\beta_{r+2}=\dots=\beta_k=0$（多加的 $k-r$ 個變數對解釋力沒有幫助）
- $H_1：\beta_j$ 不全為 0，$j=r+1,\dots,k$（多加的那一批變數裡，至少有一個真的有用）

**檢定統計量**
$$\text{Partial F}=\frac{\frac{SSE_R-SSE_C}{k-r}}{\frac{SSE_C}{n-k-1}} \sim F_{k-r,\;n-k-1}$$
- $SSE_C$：完整模型（含 $k$ 個變數）之殘差平方和
- $SSE_R$：縮減模型（只用 $r$ 個變數）之殘差平方和
- $df_1=k-r$：分子自由度，代表新增變數個數
- $df_2=n-k-1$：分母自由度，完整模型的殘差自由度（含截距故 $-1$）
- 直觀解釋：若加了變數**真的有效**，則 $SSE_C$ 應該**明顯**小於 $SSE_R$，使得分子 $SSE_R-SSE_C$ 夠大，$F$ 就會大。
- **若只增加一個變數（$k-r=1$），此 $F$ 值其實就是該變數 t 檢定統計量的平方（$F=t^2$）。**

**決策規則**：critical value $= F_{0.95}(k-r,n-k-1)$；若 p-value $<\alpha \Rightarrow$ Reject $H_0$ $\Longrightarrow$ 新增的那堆變數「整體而言顯著的提升了模型解釋力」。

**如何解讀**
- 想像先用一個「簡易模型（縮減模型）」進行預測，接著把「一坨你懷疑可能只是湊熱鬧的變數」丟進去變成完整模型。
- 如果這些新增變數真的有料，模型誤差會明顯下降（$SSE$ 明顯降低）$\Longrightarrow$ 這些變數會把 $F$ 值推大，使檢定容易通過。
- 如果這些新增變數只是增加噪音，$SSE$ 則幾乎不降，$F$ 不會變大、p-value 不會變小 $\Longrightarrow$ 這些變數不值得保留。

**與「是否過度擬合」的關聯性 — 三角驗證法則 ★**
- 哪個 $SSE$ 大？**一定是 $SSE_R \ge SSE_C$**，因為新增變數不會讓 $SSE$ 變大。
- 若 $SSE_R - SSE_C$ 非常大：新增變數帶來顯著改善 $\Longrightarrow$ 效果顯著，應保留。
- 若 $SSE_R - SSE_C$ 非常小：改善幅度很小，考慮模型簡潔與泛化能力 $\Longrightarrow$ 傾向刪除新增的變數（偏好縮減模型）。
- **可搭配兩個量綜合判斷**：
  - Adjusted $R^2$：會對多放變數做懲罰。加了「無效」的變數，Adjusted $R^2$ 可能下降。
  - 殘差標準誤 $\hat\sigma=\sqrt{\frac{SSE}{n-k-1}}$：好的模型會讓 $\hat\sigma$ 下降。
- **三者一致的情況下**：Nested Partial F-Test 不顯著 + Adjusted $R^2$ 較高的是縮減模型 + $\hat\sigma$ 也較低 $\Longrightarrow$ 高機率是縮減模型比較理想。

**簡易結論**
| Partial F-Test | 決策 | 通常伴隨 |
|---|---|---|
| 顯著 | 保留那批變數（完整模型） | Adjusted $R^2 \uparrow$、$\hat\sigma \downarrow$（但若沒有同向也不違反理論） |
| 不顯著 | 移除那批變數（縮減模型） | Adjusted $R^2 \downarrow$ 或幾乎不變、$\hat\sigma$ 不降 |

**注意！（四條陷阱）**
1. **務必留意巢狀的特性**：縮減模型一定要是完整模型把某些係數設 0 的特例，否則不能用 Partial F-Test。
2. **多重共線性**：會讓新增變數在「邊際上」看起來不顯著（彼此搶解釋力）。**在單一 t-Test 可能不顯著，但 Partial F-Test 仍可能顯著。**
3. **單一新增變數**：Partial F-Test 與該新增變數的 t-Test 為等價檢定（$F=t^2$）。
4. **量測單位差異**：係數大小不能直接互比，必要時看標準化係數。

#### (C) 個別參數 t-Test（Individual parameter t-test）

- **核心問題**：檢定「在已控制其他 $k-1$ 個變數後，某一變數 $X_p$ 是否還有額外解釋力？」
  - 評估單一候選變數是否保留/移除。
  - **先用 t-Test 挑出「疑似多餘」的變數，再透過 Nested model partial F-test 進行成組（$>1$ 個）的確認。**
- 假說：$H_0：\beta_p=0$（$X_p$ 在控制其他變數後沒有線性效果）；$H_1：\beta_p \ne 0$

$$\text{t-statistics} = \frac{\hat{\beta}_p-\beta_p}{S_{\hat{\beta}_p}}\sim t_{n-k-1}$$
- 分子是「估計的效果大小」，分母是「不確定度」。
- 白話：估計值距離 0 有多遠（效果），相對於不確定度（標準誤）$\Rightarrow$ 距離越遠、證據越強。

**決策規則**
- 雙尾檢定 critical value $= \pm t_{\frac{\alpha}{2}}(n-k-1)$
- 單尾：右尾 $t_{\alpha}(n-k-1)$；左尾 $-t_{\alpha}(n-k-1)$
- **注意！課堂與 R 的預設多半用雙尾。**

**如何解讀**
- 顯著 $\Longrightarrow$ 先將變數視為保留候選。
- 不顯著 $\Longrightarrow$ 將變數列為移除候選。
- **值得注意的是，結論是「在目前模型」下得到的。變數進出後，其他係數與 p-value 可能因「共線性」或「遮蔽效應」而改變。**

**注意！**
- **高 p-value $\ne$ 一定要刪**：可能是樣本少或共線性讓標準誤變大（t 變小）。
- **估計顯著 $\ne$ 效果大**：效果大小還是要看單位、標準化係數。

**t-test 與 Partial F-test 的關係（決策規則）**
- 想一次檢驗**一個**變數 $\longrightarrow$ Individual t-test
- 想一次檢驗**多個**變數（降低多重比較錯誤）$\longrightarrow$ Nested Partial F-test
- 實務步驟：先以 Individual t-tests 找可能冗餘的變數（一次只看一個），再以 Nested Partial F-tests 同時檢定一組候選變數（$>1$ 個）是否能一起刪除。

### 3.10 【材料原文】MLR R Code 完整原始碼（逐字抄錄）

```r
####-------------------------------------------------------####
####  Business Analytics
####  Dr. Jiun-Yu Yu
####  Department of Business Administration
####  National Taiwan University
####  Lecture 3: Multiple Linear Regression (MLR)
####-------------------------------------------------------####


########  Multiple Linear Regression (MLR)  ########

## Read data
HOMES2 <- read.csv("HOMES2.csv", header=TRUE)
attach(HOMES2)

## Scatterplot matrix
plot(HOMES2[,c("price","size","room")])
pairs(HOMES2)


## SLR
	lm2.1 <- lm(price ~ size, data=HOMES2)
	summary(lm2.1)

## MLR
lm2.2 <- lm(price ~ size + room, data=HOMES2)
summary(lm2.2)


## Beta coefficients
beta.X1 <- lm2.2$coef["size"]*sd(size)/sd(price)
beta.X2 <- lm2.2$coef["room"]*sd(room)/sd(price)
beta.X1
beta.X2


## Complete model
lm2.3 <- lm(price ~ size + room + hall + bathroom + parking + age, data=HOMES2)
summary(lm2.3)

## Reduced model
lm2.4 <- lm(price ~ size + room + parking + age, data=HOMES2)
summary(lm2.4)


## Multiple Correlation Coefficient
sqrt(summary(lm2.4)$r.squared)


## Global Usefulness Test
anova(lm2.4)				# ANOVA table 

summary(lm2.4)$fstatistic	
(qf(0.95, 4, 145))			# critical value
(1-pf(61.92893, 4, 145))		# p-value


## Nested F-test
anova(lm2.4, lm2.3) 

	(qf(0.95, 2, 145))		# critical value
	(1-pf(0.4563, 2, 145))		# p-value


	## Question: What does this mean?
	anova(lm2.1, lm2.4)


## Individual t-test
summary(lm2.3)

	(qt(0.95, 143))			# critical value
	(1-pt(11.688, 143))*2		# p-value, for the coefficient of 'size'


####  Diagnostic Plots 				####
####  Residual plot, Histogram, QQ-plot	####

	par(mfrow=c(1,3))

plot(fitted(lm2.4), residuals(lm2.4), xlab="Fitted", ylab="Residuals"); abline(h=0)
hist(residuals(lm2.4),breaks=10)
qqnorm(residuals(lm2.4), ylab="Residuals"); qqline(residuals(lm2.4))



## Summary and Confidence interval
summary(lm2.4);	confint(lm2.4)


## Confidence interval, Prediction interval 
xnew <- data.frame(size=100, room=2, parking=20, age=10)

predict(lm2.4, xnew, interval="confidence", level=0.95)
predict(lm2.4, xnew, interval="prediction", level=0.95)
```

### 3.11 【材料原文】R 語法要點（0916 R code 段）

- 在這裡指定參數如下：$Y=\text{Price}$、$X_1=\text{size}$（floor size）、$X_2=\text{room}$（number of rooms）
- `lm2.2 <- lm(price ~ size + room, data=HOMES2)`
  - 和 SLR 的 lm 語法類似，但在 $X_i$ 的變數指定上略有不同。要新增變因 $X_i$，是在 `~` 後面的第一個變數命名後，以「+」做指派。
  - **`data =` 指定資料集，這部分盡量別省略**，未來可能讀的檔案多了，會依不同的模型需求對資料集進行刪減或編輯，為了避免讀錯檔案，在指定新模型的時候，還是建議每次都要明確指定使用資料集。
- `beta.X1 <- lm2.2$coef["size"]*sd(size)/sd(price)`：指定需要的是 lm2.2 此模型中的 size 這個 coefficient；透過 $\hat{\beta}_j^*=\frac{S_{X_j}}{S_Y}\hat{\beta}_j$ 此公式，直接轉換成 size 的 beta coefficient。
- `beta.X2 <- lm2.2$coef["room"]*sd(room)/sd(price)`：同理，room 的 beta coefficient。
- Complete model vs. reduce model
  - `lm2.3 <- lm(price ~ size + room + hall + bathroom + parking + age, data=HOMES2)` $\Longrightarrow$ complete model
  - `lm2.4 <- lm(price ~ size + room + parking + age, data=HOMES2)` $\Longrightarrow$ reduce model
  - **lm2.4 所使用的四個解釋變數 lm2.3 都有，這就是一個巢狀結構的典型。**
- 診斷三圖可以分開畫三次，也可以一次完成：`par(mfrow=c(1,n))` 代表如果我要把 n 張圖放在一起。

```r
par(mfrow=c(1,3))

plot(fitted(lm2.4), residuals(lm2.4), xlab="Fitted", ylab="Residuals"); abline(h=0)
hist(residuals(lm2.4),breaks=10)
qqnorm(residuals(lm2.4), ylab="Residuals"); qqline(residuals(lm2.4))
```

### 【評註】這回答什麼行銷/商業問題

- **偏效應**回答「在控制通路、季節、價格之後，廣告本身還有多少獨立貢獻」——這是行銷歸因（attribution）的統計版本。
- **Beta coefficient** 回答「電視、數位、促銷三個管道，誰的邊際影響最大」——預算重分配的直接依據。
- **Nested F-test** 回答「這一整組新加的變數（例如：整批 CRM 行為變數）值不值得繼續蒐集」——資料採購決策。
- **Global F 不顯著**：整套行銷變數都解釋不了績效，該回頭檢查資料或重新定義 Y。

---

## 4. 迴歸診斷（0909 + 0916 + 0923）★★★

> 這是任務要求的第 2、3 項。**教科書通常不寫的判讀規則，全部在這一節。**

### 4.0 【評註】診斷的執行順序

材料沒有用一句話寫出「順序」，但順序可以從三處交叉推導出來，且三處完全一致：

1. **0923「實務上的快速流程」**（材料原文，唯一明說順序的地方）：
   > 1. 用 Global Usefulness F-Test 確認模型有訊號。
   > 2. 針對候選區塊做 Nested model Partial F-Test（例如加入 $X^2$ 項、交互項）。
   > 3. 在通過 (2) 後，再看 Individual parameter t-test 與信賴區間，決定保留的欄位。
   > 4. **以殘差圖、診斷（槓桿 / Cook's）檢查穩健性，最後下結論。**
2. **0923「影響點」章節的敘述順序**：Outliers（Y 方向）→ High Leverage（X 方向）→ Cook's distance（兩者綜合）。
3. **R 程式碼的實際排列順序**（0923 R code 段）：`rstandard()` → `hatvalues()` → `cooks.distance()`；且 0930 實戰腳本是先做殘差三圖比較 Y 的轉換，再做 Cook's distance，最後才做 VIF。

因此，可寫成新 Skill 的**診斷順序**是：

```
Step 0  模型整體有沒有訊號        → Global F test
Step 1  殘差三圖（假設檢查）      → Residual plot → Histogram → Q-Q plot
          ├ 殘差圖：檢查 零均值 / 同質變異 / 獨立性
          ├ Histogram：檢查 常態性
          └ Q-Q plot：檢查 常態性（比 Histogram 敏感）
Step 2  離群值（Y 方向異常）      → rstandard()，|studentized residual| > 3
Step 3  槓桿點（X 方向異常）      → hatvalues()，h > 3(k+1)/n
Step 4  影響點（綜合）            → cooks.distance()，D >= 1 或 0.5 <= D < 1
Step 5  共線性                    → 成對散佈矩陣 / 相關係數 → VIF > 10（寬鬆 5）
Step 6  變數選擇                  → Testing-based（backward/forward/stepwise）
                                     → Criterion-based（AIC / Adjusted R²）驗證收尾
Step 7  敏感度分析                → 移除可疑點重估，看係數、標準誤、R² 是否實質改變
```

【評註】**Step 1 一定在 Step 2-4 之前**，因為 Step 2 的 studentized residual 「在迴歸四大假設成立下才近似 $\mathcal N(0,1)$」——假設沒過，$|r|>3$ 這條線本身就沒有意義。
**Step 5（共線性）可以更早做**（在 EDA 的 `pairs`/`cor` 階段就會看到端倪），但正式的 VIF 要在模型配適後才能算。

---

### 4.1 【材料原文】殘差圖（Residual plot）判讀規則 ★

- 橫軸為：$\hat{Y}$ 或 $X$
- 縱軸為：$\hat{\varepsilon}$

**用來檢驗三個假設：**

| 檢驗的假設 | 理想狀況 | 問題訊號 | 可能的解決方式 |
|---|---|---|---|
| **零均值（Mean zero）** | 點雲上下分布大致對稱，平均接近 0 | 若整體殘差偏上或偏下 → 模型有系統性偏差 | （材料未列） |
| **同質變異（Constant variance）** | 點的散布寬度**從左到右差不多** | ① 圖形呈現**漏斗形**（左窄右寬或相反）→ 異質變異<br>② 圖形**弓形** → 誤差隨 $X$ 改變而增減 | ① 變數轉換（**對數、平方根**）<br>② 加權最小平方法（WLS）<br>③ robust SE |
| **獨立性（Independence）** | 殘差像**隨機雜訊**，沒有固定模式 | 呈現「**波浪狀**」或「**週期性**」→ 誤差存在自我相關（常見於時間序列） | ① 檢查 **Durbin-Watson**<br>② **Newey-West SE** |

有問題的例子（材料附圖，文字說明逐字保留）：
- 「$X$ 愈小變異數愈小，$X$ 愈大變異數愈大，違反 Constant variance。」
- 「以下都是違反 Constant variance 假設。」
- 「殘差圖出現系統性規律，而不是『隨機雜訊』，違反 scattered。」

### 4.2 【材料原文】Histogram（殘差直方圖）判讀規則

- 常用來檢驗**常態性假設（Normality）**

| | 內容 |
|---|---|
| 理想狀況 | 圖形分佈呈現**鐘形、對稱、中心在 0** |
| 問題訊號 | ① **偏斜**（左長尾／右長尾）→ 誤差分布偏斜<br>② **扁平或尖峰** → 分布與常態差異明顯 |
| 解決方式 | ① 轉換（**log、Box-Cox**）<br>② 穩健迴歸<br>③ 用非參數方法 / **bootstrap（拔靴法）** |

### 4.3 【材料原文】Q-Q plot 判讀規則

- 常用來檢驗**常態性假設（Normality）**

| | 內容 |
|---|---|
| 理想狀況 | 點大致落在 **45 度對角線**上 |
| 問題訊號 | ① **尾端翹起／下垂** → 肥尾或瘦尾分布<br>② **整體彎曲** → 殘差存在偏態 |

- **Durbin-Watson test：檢查誤差獨立性。**

### 4.4 【材料原文】影響點：三個面向 ★★

**少數幾個資料點，就可能透過槓桿效應把整體結論帶偏：**
- 使迴歸線被少數點「拉走」，從而誤判關聯強度。
- 以少數支配性樣本為主的證據，容易導致誤導性結論。

**個別資料點「影響力」的兩個面向 + 一個綜合指標：**

| 概念 | 英文定義 | 影響的方向 | R 指令 |
|---|---|---|---|
| **離群值（Outliers）** | Unusual $Y$ values relative to $\hat Y$ | 相對於模型預測值 $\hat Y$，$Y$ 值異常（殘差很大）。**事實上，離群值影響的是 $Y$ 方向上的數值！** | `rstandard()` |
| **高槓桿點（High leverage points）** | Unusual $X$ values relative to general dataset pattern | **高槓桿點所影響的則是 $X$ 方向上的數值！** 某筆資料的 $X$ 值跑到其他點很少散佈的角落，或說 $X$ 的組合很罕見。 | `hatvalues()` |
| **庫克距離（Cook's distance）** | 把「殘差大小」與「槓桿高低」綜合起來衡量影響力 | 綜合 | `cooks.distance()` |

**★ 關鍵判讀原則（材料原文）**
> - 殘差大 $\ne$ 影響一定大；槓桿高 $\ne$ 影響一定大。
> - **殘差大 $+$ 槓桿高 $=$ 最危險，但仍需視庫克距離而定。**

### 4.5 【材料原文】Outliers 的判讀與處理 ★

**用詞注意**
- 這裡用的是 **studentize** 而非 standardize。
- 其實是指 t 分配的標準化，因提出者是 student's t 的作者 Gossett，故以此用。
- 基本上，邏輯跟 standardize 是一樣的概念。

**定義**：對於模型的預測值 $\hat Y$，這筆資料的 $Y$「偏得特別多」。例如：殘差很大的觀察值。

**前提**：在迴歸四大假設（零均值／同質變異／獨立／常態）成立下，studentized residual 近似 $\mathcal N(0,1)$。

**判準（rule of thumb）**
$$|\text{studentized residual}| > 3 \Longrightarrow \text{離群值}$$
- studentized residual $> 3$，或 studentized residual $< -3$
- **兩尾機率約 $< 0.002$**

**如何處理 Outliers？找到離群點後，先檢查原因（四類）★**

| 原因 | 處理方式 |
|---|---|
| **資料輸入錯誤（最常見）** | 更正後重跑分析 |
| **重要變數遺漏（解釋變數不足）** | 找回可能有用的變數納入後重估 |
| **回歸假設失真**（異質變異、非常態、交互項未檢驗） | 透過變數轉換、加入交互或非線性項，再重新評估模型 |
| **族群本質差異**（潛在次族群，與多數樣本機制不同） | 先把疑似離群樣本獨立處理，其餘資料單獨重估，**進行分開分析** |

**評估離群點的影響力（敏感度分析）**
1. 先找出最大 $|\text{studentized residual}|$ 的觀測值。
2. 先排除該點，以剩餘資料重估模型，觀察**係數、標準誤、$R^2$** 是否有實質改變。
3. 統計檢驗：
   - **顯著影響** → 該點具實質影響，需回到上面四類原因處理。
   - **未顯著影響** → **紀錄即可，通常保留。**

**投影片範例 1（HOMES4，模型 $E(Y) = \beta_0+\beta_1X_1+\beta_2X_2+\beta_5X_5+\beta_6X_6+\beta_7X_6^2$）**
- 由直方圖可看到有 2 個 $|\text{studentized residual}| \approx -4$ 的資料點。
- 移除後 → HOMES4a，由直方圖可看到已無其他 Outliers。
- **模型變動**：資料點刪除後，迴歸參數估計與 p-value **沒有明顯變動**。該離群點原本可能對結果造成強烈影響，但在此範例中並未發生。

$$\begin{array}{lrr}
\text{Model} & \text{HOMES4} & \text{HOMES4a} \\
\hline
\text{degrees of freedom} & 144 & 142 \\
\text{Residual standard error} & 4422 & 4192 \\
\text{Multiple R-squared} & 0.6602 & 0.6808 \\
\text{Adjusted R-squared} & 0.6484 & 0.6696 \\
\text{F-statistic} & 55.94 & 60.57 \\
\text{p-value} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16}
\end{array}$$

**投影片範例 2（CARS4，模型 $E(Y)=\beta_0+\beta_1 \frac{1}{X_1}+\beta_2 \frac{1}{X_2}+ \beta_3X_3$）**
- 由直方圖可以發現，此資料集中並沒有 Outliers。

**Coding 的注意事項**
- studentized residual 的指令：`rstandard( )`
- 第 57 及 117 筆資料需要被移除，指令如下：`HOMES4a <- HOMES4[-c(54,117),]`
  - 指定 HOMES4a 為 HOMES4 資料集變動後的資料集。
  - `-` 是移除的意思。`c` 是 combination，也就是要移除的數據筆數組合。
  - **注意，c 後面還有一個逗號以及空白。R 的 Index 中，第一列是代表位置橫軸，第二列是代表縱軸位置。因此 `c(54,117),` 指的就是第 54 列及第 117 列。**

### 4.6 【材料原文】High Leverage Points 的判讀與處理 ★

**定義**
- 某筆資料的 $X$ 值落在其餘資料點相對稀少的區域 → 迴歸線容易被它拉過去。
- 若存在一點遠離多數樣本，它會把擬合線往自己的 $Y$ 值拉，可能偏斜整體結論。
- **Leverage 衡量「某點是否有潛力對模型產生過度影響」。** 0＝低，1＝高。

**經驗法則（rule of thumb）** — 令 $n$ = 樣本數，$k$ = 解釋變數個數，$h$ 表槓桿（leverage）：

$$h>\frac{3(k+1)}{n} \longrightarrow \text{需進一步檢查}$$
$$h<\frac{2(k+1)}{n} \longrightarrow \text{該點很孤立，也需進一步檢查}$$
$$\frac{2(k+1)}{n} \le h \le \frac{3(k+1)}{n} \longrightarrow \text{暫無過度影響的明確證據}$$

> 【評註】材料第三條原文寫作 `h>3(k+1)/n ≥ h ≤ 2(k+1)/n`，是筆記的排版錯誤；依前兩條的邏輯，
> 中間帶（$2(k+1)/n \le h \le 3(k+1)/n$）才是「暫無明確證據」的區間。第二條「$h$ 小於下界也要檢查」
> 是這份筆記獨有的說法（一般教科書只講上界），轉 Python 時建議兩條門檻線都畫。

**評估高槓桿點的影響力（敏感度分析）**
1. 找出 $h$ 最大的點。
2. 排除該點，以剩餘資料重估模型，觀察係數、標準誤、$R^2$ 是否有實質改變。
3. 顯著影響 → 該點具實質影響，需回到資料審查及模型建構進行處理；未顯著影響 → 紀錄即可，通常保留。

**投影片範例 1（HOMES4a，$k=5$、$n=148$）**
- $\frac{3(k+1)}{n}=\frac{3(5+1)}{148}=0.12$
- $\frac{2(k+1)}{n}=\frac{2(5+1)}{148}=0.08$
- 圖中「有三個點在上方虛線以上，那三個點即是 high leverage points！」
- 移除後 → HOMES4b。**模型變動：資料點刪除後，迴歸參數估計與 p-value 沒有明顯變動。**

$$\begin{array}{lrrr}
\text{Model} & \text{HOMES4} & \text{HOMES4a} & \text{HOMES4b} \\
\hline
\text{degrees of freedom} & 144 & 142 & 139 \\
\text{Residual standard error} & 4422 & 4192 & 4229 \\
\text{Multiple R-squared} & 0.6602 & 0.6808 & 0.6757 \\
\text{Adjusted R-squared} & 0.6484 & 0.6696 & 0.664 \\
\text{F-statistic} & 55.94 & 60.57 & 57.92 \\
\text{p-value} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16}
\end{array}$$

**投影片範例 2（CARS4，$k=3$、$n=300$）**
- $\frac{3(k+1)}{n}=\frac{3(3+1)}{300}=0.040$
- $\frac{2(k+1)}{n}=\frac{2(3+1)}{300}=0.0267$

$$\begin{array}{lrr}
\text{Model} & \text{CARS4} & \text{CARS4a} \\
\hline
\text{degrees of freedom} & 296 & 289 \\
\text{Residual standard error} & 1.205 & 1.207 \\
\text{Multiple R-squared} & 0.8215 & 0.8122 \\
\text{Adjusted R-squared} & 0.8197 & 0.8102 \\
\text{F-statistic} & 454 & 416.5 \\
\text{p-value} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16}
\end{array}$$

**Coding 的注意事項**
- 計算 leverage values 的指令：`hatvalues( )`
- 找尋比臨界值還要高的 high leverage points 有哪些點：`levlm4.1[levlm4.1 > thr3]`（此時會回傳資料點）

### 4.7 【材料原文】Cook's distance 的判讀與處理 ★

**定義**
- Cook's distance 是把「殘差大小」與「槓桿高低」綜合成一個影響力指標。
- Cook's distance 值越大，對模型的參數估計越可能有**過度影響**。
- **僅作為模型警訊使用！**

**經驗法則（rule of thumb）**
- $\text{Cook's distance} \ge 1$
- $0.5 \le \text{Cook's distance} < 1$
- 否則，通常沒有過度影響的明確證據。

【評註】0930 實戰腳本另外加了業界常用的 $4/n$ 門檻（`thr_4n <- 4 / n`），材料註記為「常見經驗法則」／「常用判準」，
但講義正文只列 1.0 與 0.5 兩條。轉 Python 時三條都畫，但**主判準用 1.0 / 0.5**。

**評估影響力（敏感度分析）**
1. 找出 $\text{Cook's distance} \ge 1$ 的點。
2. 排除該點，以剩餘資料重估模型，觀察係數、標準誤、$R^2$ 是否有實質改變。
3. 顯著影響 → 回到資料審查及模型建構處理；未顯著影響 → 紀錄即可，通常保留。

**投影片範例**
- HOMES4：此模型之 Cook's distance 最高也就 0.35，完全沒有超出任何臨界值。
- CARS4：此模型之 Cook's distance 最高僅有 0.05 多一些，完全沒有超出任何臨界值。

**Coding 的注意事項**：取得 Cook's distance 的指令 `cooks.distance( )`

### 4.8 【材料原文】診斷相關 R Code（0923，逐字抄錄）

**Outliers — HOMES4**
```r
## Read data
HOMES4 <- read.csv("HOMES4.csv", header=TRUE)
attach(HOMES4)

lm4.1 <- lm(price ~ size + room + parking + age + agesq, data=HOMES4)
summary(lm4.1)
```

**Outliers — HOMES4a（識別、移除、重估）**
```r
## Outlier (studentized residuals), on histogram
reslm4.1 <- rstandard(lm4.1)		# studentized residuals
hist(reslm4.1, breaks=20)

	## identify the outliers, remove them, and get HOMES4a dataset

	reslm4.1[reslm4.1<(-3) | reslm4.1>3]
	HOMES4a <- HOMES4[-c(54,117),]	# datset HOMES4a
	
	## Refit the MLR with new dataset HOMES4a
lm4.1a <- lm(price ~ size + parking + room + age + agesq, data=HOMES4a)
summary(lm4.1a)
```

**Outliers — 更新後的直方圖**
```r
## histogram for studentized residuals of the updated MLR
reslm4.1a <- rstandard(lm4.1a)
hist(reslm4.1a, breaks=10)
```

**Outliers — CARS4**
```r
## Read data
CARS4 <- read.csv("CARS4.csv", header=TRUE)
attach(CARS4)

lm4.1 <- lm(fuel ~ recipweight + recipdisplacement + door, data=CARS4)
summary(lm4.1)

## Outlier (studentized residuals)
reslm4.1 <- rstandard(lm4.1)	
hist(reslm4.1, breaks=20)

reslm4.1[reslm4.1<(-3) | reslm4.1>3]
```

**High Leverage Points — Leverage values**
```r
####  Leverage : hatvalues  ####
levlm4.1 <- hatvalues(lm4.1a)		# leverage values
k <- 5; n <- nrow(HOMES4a)
( thr3 <- 3*(k+1)/n )
( thr2 <- 2*(k+1)/n )
plot(levlm4.1, xlab="ID Number", ylab="Leverage") 
	abline(h=thr3, lty=2); abline(h=thr2,lty=3)
```

**High Leverage Points — HOMES4b**
```r
## identify high leverage points in 'levlm4.1', 
	## and then remove them to get HOMES4b dataset

	levlm4.1[levlm4.1 > thr3]
	HOMES4b <- HOMES4a[-c(80,104,119),]		# dataset HOMES4b

## Refit the MLR with new dataset HOMES4b
lm4.1b <- lm(price ~ size + room + parking + age + agesq, data=HOMES4b)
summary(lm4.1b)
```

**High Leverage Points — CARS4**
```r
## Leverage 
levlm4.1 <- hatvalues(lm4.1)

k <- 3; n <- nrow(CARS4)
( thr3 <- 3*(k+1)/n )
( thr2 <- 2*(k+1)/n )

plot(levlm4.1, xlab="ID Number", ylab="Leverage");	abline(h=thr3, lty=2); abline(h=thr2,lty=3)

levlm4.1[levlm4.1 > thr3]				# identify high leverage points
```

**Cook's distance — HOMES4**
```r
####  Cook's Distance : cooks.distance  ####
cooklm4.1 <- cooks.distance(lm4.1)		# cook's distance of the FIRST model, all data points!

plot(cooklm4.1, xlab="ID number")

cooklm4.1[cooklm4.1 > 1.0] 
cooklm4.1[cooklm4.1 > 0.5]
```

**Cook's distance — CARS4**
```r
CARS4b <- CARS4[-c(58,68,87,250,271,275,291),]	# dataset CARS4b

lm4.1b <- lm(fuel ~ recipweight + recipdisplacement + door, data=CARS4b)
summary(lm4.1b)

## Cook's Distance 
cooklm4.1 <- cooks.distance(lm4.1)

plot(cooklm4.1, xlab="ID number")

cooklm4.1[cooklm4.1 > 1.0]
cooklm4.1[cooklm4.1 > 0.5]
```

### 4.9 【材料原文】0930 實戰版 Cook's distance 與 VIF（逐字抄錄）

```r
####-------------------------------------------------------####
####  Cook's Distance — Best model (Y = 1/Usage, X 全處理 + NSM)
####-------------------------------------------------------####

## 若尚未讀檔與轉換
file_path <- "C:/Users/user/Desktop/商管統計資料分析/In-class pratical 1/steel_ind_energy_a.csv"
dat <- read.csv(file_path, header = TRUE)

## 轉換（與前面一致）
eps_y  <- 0.001; eps_x <- 0.001; eps_pf <- 1e-6
dat$Y_inv <- 1 / (dat$Usage_kWh + eps_y)

dat$log_CO2             <- log(dat$CO2 + eps_x)
dat$log_Lagging_Current <- log(dat$Lagging_Current + eps_x)
dat$log_Leading_Current <- log(dat$Leading_Current + eps_x)
dat$log_inv_LagPF       <- log(1 / (dat$Lagging_Current_Power_Factor  + eps_pf))
dat$log_inv_LeadPF      <- log(1 / (dat$Leading_Current_Power_Factor + eps_pf))

## 擬合：Y=1/Usage；X 全處理 + NSM
lm_best <- lm(
  Y_inv ~ log_CO2 + log_Lagging_Current + log_Leading_Current +
    log_inv_LagPF + log_inv_LeadPF + NSM,
  data = dat
)
summary(lm_best)  # 可看一下整體與係數

## Cook's distance（沿用講義風格）
cook_best <- cooks.distance(lm_best)

## 繪圖（講義用法）
plot(cook_best, xlab = "ID number", ylab = "Cook's distance")
n <- nrow(dat)
thr_4n <- 4 / n
abline(h = thr_4n, lty = 2)  # 參考線：4/n（常見經驗法則）
abline(h = 0.5, lty = 3)     # 參考線：0.5
abline(h = 1.0, lty = 3)     # 參考線：1.0

## 列出影響較大的觀測（講義範例是 >1 與 >0.5）
cook_best[cook_best > 1.0]
cook_best[cook_best > 0.5]

## 也一併回報 > 4/n（常用判準）
cook_best[cook_best > thr_4n]

##（選用）若資料有 ID 欄，對照出「哪幾個 ID」
idx_1   <- which(cook_best > 1.0)
idx_05  <- which(cook_best > 0.5)
idx_4n  <- which(cook_best > thr_4n)

if ("ID" %in% names(dat)) {
  data.frame(
    Row = idx_4n,
    ID  = dat$ID[idx_4n],
    CooksD = round(cook_best[idx_4n], 6),
    row.names = NULL
  )
}

##（選用）檢視前 10 名影響點
ord <- order(cook_best, decreasing = TRUE)
head(data.frame(
  Row = ord, 
  CooksD = round(cook_best[ord], 6),
  ID = if ("ID" %in% names(dat)) dat$ID[ord] else ord
), 10)
```

```r
#### VIF for 3B model (Y = 1/Usage; X = log(CO2,Currents) + log(1/PFs) + NSM)

# 套件
if (!requireNamespace("car", quietly = TRUE)) install.packages("car")
library(car)

## --- Full（含 NSM）---
v_full <- vif(m3B_full)
vif_full_tbl <- data.frame(
  Variable  = names(v_full),
  VIF       = as.numeric(v_full),
  Tolerance = 1/as.numeric(v_full),
  sqrt_VIF  = sqrt(as.numeric(v_full)),
  Flag_gt5  = as.numeric(v_full) > 5,
  Flag_gt10 = as.numeric(v_full) > 10,
  row.names = NULL
)
vif_full_tbl[order(vif_full_tbl$VIF, decreasing = TRUE), ]   # 由大到小檢視

## --- Reduced（不含 NSM）— 供參考 ---
v_red <- vif(m3B_red)
vif_red_tbl <- data.frame(
  Variable  = names(v_red),
  VIF       = as.numeric(v_red),
  Tolerance = 1/as.numeric(v_red),
  sqrt_VIF  = sqrt(as.numeric(v_red)),
  Flag_gt5  = as.numeric(v_red) > 5,
  Flag_gt10 = as.numeric(v_red) > 10,
  row.names = NULL
)
vif_red_tbl[order(vif_red_tbl$VIF, decreasing = TRUE), ]
```

### 【評註】這回答什麼行銷/商業問題

- **離群值**：一筆金額異常的訂單，是打錯 key、是 B2B 大單（次族群）、還是真的有異常客群？處理方式完全不同，材料的「四類原因」正是決策樹。
- **高槓桿點**：某個超大預算的檔期（$X$ 極端），會不會一檔活動就決定了整條 ROI 曲線？
- **Cook's distance**：把上面兩件事合起來，回答「刪掉這筆，我的行銷結論會不會翻盤」。
- **敏感度分析（移除後重估）** 是給主管的答案：「就算把這個異常客戶拿掉，結論還是一樣」——這比 p-value 更有說服力。

---

## 5. 共線性與五大迴歸陷阱（0923）★

### 5.1 【材料原文】Regression Pitfalls 概述（六項）

| 陷阱 | 定義 |
|---|---|
| **多重共線性（Multicollinearity）** | 解釋變數間彼此存在高度線性相關。會使迴歸模型產生預期之外的不良結果。 |
| **遺漏重要解釋變數（Excluding important predictor variables）** | 殘差值很高，即未解釋變異很高的情形，可能是有部分解釋變數未被考慮。 |
| **過度擬合（Overfitting）** | 使用了過多的解釋變數，造成過度解釋。 |
| **外差（Extrapolation）** | 拿模型去預測樣本範圍外的 $X$ 值。 |
| **自我相關（autocorrelation）** | 殘差彼此之間相關，在時間序列模型中是很常見的問題。 |
| **缺失資料（missing data）** | 若非隨機缺失，會導致樣本縮小與偏誤。 |

### 5.2 【材料原文】多重共線性 ★

**定義**：解釋變數彼此太相似，彼此高度相關，導致以下結果：
- 係數不穩。
- **標準誤膨脹。**
- **個別 $t$ 不顯著但整體 $F$ 可能仍顯著。**
- 係數方向也容易在正負之間「反覆變動」。
- **整個模型的結果可能很顯著，但到底是哪個變數顯著找不出來。**

**舉例**：$X_1$ 與 $X_2$ 存在線性關係，$X_1$ 對 $Y$ 的影響與 $X_2$ 對 $Y$ 的影響要算在哪個變數上？
- 有可能 $X_1$ 對 $X_2$ 產生影響，進一步影響 $Y$。
- 有可能 $X_2$ 對 $X_1$ 產生影響，進一步影響 $Y$。
- 有可能 $X_1$ 與 $X_2$ 會同時對 $Y$ 產生影響。

**判斷方式（兩步）**
1. 看**成對散佈矩陣或相關係數**。
2. 計算 **VIF（Variance Inflation Factor）**
   - 一般而言 **$\text{VIF} > 10$ 視為高度共線性**。
   - 有些領域（如：金融業）會採行較寬鬆的門檻 → **$\text{VIF} > 5$**。

**如何處理（下述方法皆可交替或組合使用）★**
1. **收集更多彼此相關性較低的資料**，實務上能做到是最理想的。
2. **合成變數**，將高度相關的指標做成組合指標。
3. **轉換變數**，將高度相關的變數重塑成其他更細緻的變數，需要專業知識輔助。
4. **在理論允許下，移除高度重疊的其中一個解釋變數。**
5. **對多項式或交互項所造成的共線性，將資料標準化可明顯緩解。**
6. **注意！對「兩個量測幾乎等價」的相關，標準化是沒有用的。**

**投影片範例（AUTO 資料）**

設定：$Y=$ price，$X_1=$ horsepower，$\frac{1}{X_2}=$ city mpg 的倒數，$\frac{1}{X_3}=$ highway mpg 的倒數

$$E(\ln{Y})=\beta_0+\beta_1X_1+\beta_2 \frac{1}{X_2}+\beta_3 \frac{1}{X_3}$$

- 此處可以發現 $R^2$ 高達 0.7005，相當顯著（代表整體模型的 SSE 小）。
- **但 $\frac{1}{X_2}$ 的係數 $\beta_2$ 及 $\frac{1}{X_3}$ 的係數 $\beta_3$ 都不顯著。相當於整體 F 檢定顯著，但個別 t 檢定不顯著的結論。**
- 其中，$\frac{1}{X_2}$ 及 $\frac{1}{X_3}$ 的散佈圖呈現高度相關。

解法（合併後取倒數）：
$$E(\ln{Y})=\beta_0+\beta_1X_1+\beta_2 \frac{1}{\frac{X_2+X_3}{2}}$$

- 此數可以發現 $R^2$ 幾乎沒有太大的變化，仍舊相當顯著。
- **但進行轉換後的 $\frac{1}{\frac{X_2+X_3}{2}}$ 項係數 $\beta_2$ 變得顯著了。**
- **注意！**
  - **合併在這邊算是特殊情況，有合理原因所以才可以合併。**
  - **合併是需要有情境意義的，沒有合理解釋時，不要硬合。**
  - **更常見、也很實務的做法，是直接刪掉其一個高度相關的預測變數，保留較有理論意義或較容易量測的那個。**

$$\begin{array}{lrr}
\text{Model} & \text{with multicollinearity} & \text{without multicollinearity} \\
\hline
\text{degrees of freedom} & 146 & 147 \\
\text{Residual standard error} & 0.2365 & 0.2358 \\
\text{Multiple R-squared} & 0.7005 & 0.7003 \\
\text{Adjusted R-squared} & 0.6944 & 0.6962 \\
\text{F-statistic} & 113.8 & 171.7 \\
\text{p-value} & < 2.2\times 10^{-16} & < 2.2\times 10^{-16}
\end{array}$$

係數比較：
$$\begin{array}{lrrrrrr}
\text{Variable} & \text{Coef (M1)} & \text{p (M1)} & \text{Coef (M2)} & \text{p (M2)} & \Delta\text{Coef} & \Delta p \\
\hline
\text{Intercept} & 7.814705 & <2\times10^{-16} & 7.820097 & <2\times10^{-16} & +0.005392 & \text{—} \\
\text{horsepower} & 0.004170 & 0.00151 & 0.004104 & 0.00133 & -0.000066 & -0.00018 \\
\text{recip.city\_mpg} & 10.150792 & 0.19655 & \text{—} & \text{—} & \text{—} & \text{—} \\
\text{recip.highway\_mpg} & 19.296590 & 0.05253 & \text{—} & \text{—} & \text{—} & \text{—} \\
\text{recip.avgX2X3} & \text{—} & \text{—} & 28.874179 & 1.95\times10^{-8} & \text{—} & \text{—} \\
\end{array}$$
（M1 = Model 1 with multicollinearity；M2 = Model 2 without multicollinearity）

> **不要太執著於模型不能出現共線性，不要太高就好，畢竟在真實世界中要找到完全沒有任何正交的資料幾乎是不可能的事情。**

**R Code（逐字抄錄）**
```r
#### Automobile ------
####------------------

AUTO4 <- read.csv("AUTO.csv", header=TRUE)

AUTO4$log.price <- log(AUTO4$price)
AUTO4$recip.city_mpg <- 1 / AUTO4$city_mpg
AUTO4$recip.highway_mpg <- 1 / AUTO4$highway_mpg

attach(AUTO4)

lm4.1 <- lm(log.price ~ horsepower + recip.city_mpg + recip.highway_mpg, data=AUTO4)
summary(lm4.1)

plot(AUTO4[c("log.price","horsepower","recip.city_mpg","recip.highway_mpg")])
```

```r
	library(car)
	vif(lm4.1)

AUTO4$avgX2X3 <- (AUTO4$city_mpg + AUTO4$highway_mpg)/2
AUTO4$recip.avgX2X3 <- 1/AUTO4$avgX2X3

lm4.3 <- lm(log(price) ~ horsepower + recip.avgX2X3, data=AUTO4)
summary(lm4.3)
```

### 5.3 【材料原文】遺漏重要解釋變數 ★

遺漏重要的解釋變數，將使其他係數被扭曲，造成**遺漏變數偏誤**，進而對「已納入的變數」下出偏差結論，**可能導致結論比實際上更強、更弱、甚至方向錯誤。**

**容易發生遺漏變數的情境（三種）**
1. 只看單變數結果，就把某些理論上重要的變數忽略。
2. 以為 p-value 不小就可以拿掉，但其實和關鍵解釋變數有高度關聯。
3. 受限於資料蒐集成本，量測不到或觀測得很差的變數被省略。

**投影片範例（房價）**：$Y=$ price、$X_1=$ floor size、$X_2=$ number of rooms

SLR 模型 $E(Y)=\beta_0+\beta_1X_1$ 的結論：
- $R^2=0.0102$，幾乎沒有解釋能力。
- 房價 $Y$ 與房間數 $X_2$ 呈現正向關係。直觀來說，房間數增加，價格上升，表面看起來是這樣。
- **但這樣的說法忽略了「坪數」的影響。** 考量現實情境，房間變多常伴隨坪數變大，若沒把坪數一起納入，容易把坪數的效果錯算到房間數上。

MLR 模型 $E(Y)=\beta_0+\beta_1X_1+\beta_2X_2$ 的結論：
- 在房間數固定下，房價與坪數呈正向。
- 在坪數固定下，房價與房間數也呈正向。
- 直觀來說：同樣房間數，坪數越大，價格越高；同樣坪數，房間越多，價格越高。
- 試想，若把坪數加大、同時把房間數變少（大空間、少隔間），只要「坪數變大帶來的正向效果」大於「房間數變少的負向效果」，總價仍可能上升。
- 散佈圖：不同顏色代表不同的資料 level。**在不同的狀況之下，不同的分布型態其實是有負的相關性（圖中的線幾乎都是負斜率）。**

> 可以說，如果資料本身很分散，在單維度的情況下可能看不出個所以然，但在高維度的情況下就會產生影響。
> **因此領域知識相當重要，能否找到足夠好的變數來進行解釋並收集資料很重要。**

> 【評註】這正是統計上的 **Simpson's paradox / 辛普森悖論** 情境：分層看是負相關，合併看是正相關。
> 材料沒有用這個名詞，但描述的就是它。

### 5.4 【材料原文】過度擬合

- 當模型設計得過於**複雜**，試圖將資料集中的每種可能性都描繪出來時，就會形成過度擬合，從而導致模型在母體上的泛用性**變差**。
- **Sanity check：從領域常識看要說得通，結論也要有資料支撐。**
- 圖例說明：左邊的圖形雖存在誤差，但一條乾淨簡潔的直線易呈現，也容易用於預測。右邊的圖形雖通過每個資料點，但結構過於複雜，難以用於預測。
- **在實務上，除非有特殊的理由或理論佐證資料應進行何種處理，否則會希望盡可能地將解釋變數的數量縮減。**

### 5.5 【材料原文】外差（Extrapolation）

**定義**
- 迴歸模型去估計或預測一個觀測值，但它的 $X$ 值遠超出樣本範圍。
- **在建構模型的時候，必須要知道所有解釋變數 $X_1、X_2、\dots、X_n$ 的範圍在哪裡，模型的有效性僅止於這個範圍之內，對範圍外是沒有解釋力或預測能力的。**
- 我們在沒有資料支撐的區域做決策，關係可能早就變形，推論結果並不可靠。

**圖例說明**
- $X$ 的範圍在 $2 \sim 8$。
- 圖中的線性模型或曲線模型都可以擬合這些資料點，此兩個模型的 $R^2$ 差不多，對於資料集的解釋力不分軒輊。
- **若以 $X=12$ 進行預測，兩模型所回應的 $E(Y)$ 將有極大的落差。**
- 因為模型是使用 $2\sim 8$ 的資料建立起來的，並未包含 $X=12$ 的情形，因此無法進行有意義的推論或預測。

### 【評註】這回答什麼行銷/商業問題

- **共線性**：電視廣告與數位廣告常同期投放（高度相關），模型會說「兩個都不顯著」，但整體 F 顯著。此時若直接砍掉數位預算，是嚴重誤判。材料的解法（合成指標／砍一個／標準化）就是行銷歸因的標準處方。
- **遺漏變數**：只看「發折價券 → 銷售上升」，沒控制「同期也在打廣告」，會把廣告效果算到折價券頭上。
- **外差**：歷史行銷預算落在 100 萬～500 萬，模型不能拿來回答「花 2000 萬會怎樣」。這是行銷預算規劃最常見的誤用。

---

## 6. 變數轉換的決策原則（0909 + 0916 + 0923 + 1007）★

> 這是任務要求的第 7 項。材料把轉換的「觸發條件」與「處方」拆在三個地方，這裡合併整理。

### 6.1 【材料原文】轉換的觸發條件 → 處方對照表

| 觸發條件（在哪裡看到） | 症狀 | 材料指定的處方 | 出處 |
|---|---|---|---|
| **殘差圖**：漏斗形（左窄右寬或相反） | 異質變異 | **變數轉換（對數、平方根）**／加權最小平方法（WLS）／robust SE | 0909、0916 |
| **殘差圖**：弓形 | 誤差隨 $X$ 改變而增減 | 同上 | 0909、0916 |
| **殘差直方圖**：偏斜（左長尾／右長尾）、扁平或尖峰 | 常態性違反 | **轉換（log、Box-Cox）**／穩健迴歸／非參數方法 / bootstrap | 0909、0916 |
| **Q-Q plot**：尾端翹起／下垂、整體彎曲 | 肥尾／瘦尾／偏態 | 同上 | 0909、0916 |
| **EDA 直方圖**：高度偏態的變數 | — | **常先取自然對數再分析** | 1007 |
| **EDA**：應變數 $Y$ 右偏很嚴重 | — | **考慮用 $\ln(Y)$** | 1007 |
| **散佈圖**：非線性（曲線） | 線性假設違反 | 加上**平方項 $X_i^2$**；或把 $X_i$ 換成 $\ln(X_i)$ 或 $\frac{1}{X_i}$ | 1007 |
| **離群值成因診斷**：回歸假設失真 | — | 透過**變數轉換、加入交互或非線性項**，再重新評估模型 | 0923 |
| **共線性**：多項式或交互項造成 | VIF 高 | **將資料標準化可明顯緩解**（但對「兩個量測幾乎等價」的相關無效） | 0923 |
| **共線性**：兩個高相關指標 | VIF 高 | **合成變數**（例：取平均後再取倒數）／移除其一 | 0923 |

### 6.2 【材料原文】1007 的「由簡到繁」加法順序 ★★

> 這是全部材料裡最接近「決策流程」的一段，逐字保留。

**Step 1. 建立初始模型**
- 用量化自變數與類別指示變數先擬合一個起始的多元線性模型。
- **應變數 $Y$ 先用原始尺度；除非 EDA 明確建議轉換。** 例如：右偏很嚴重就考慮用 $\ln(Y)$。

**Step 2. 檢查四個基本假設（看殘差圖）**
- 線性、常態、等變異、獨立性。
- 若有明顯違反 → 進 Step 3（調整模型）。
- **若都過關 → 直接跳 Step 4（簡化模型）。**

**Step 3. 加入「交互項」或進行「變數轉換」，讓假設變合理（由簡到繁）**
1. **先試「類別 $\times$ 連續」的交互項**（最常見，通常也最容易有意義）。例：$DX_1, DX_2$（組別 $\times$ 共變數）。
2. **若模型解釋力仍不足，再試變數轉換**
   - 加上平方項 $X_i^2$。
   - 或把 $X_i$ 換成 $\ln(X_i)$ 或 $\frac{1}{X_i}$ 等能改善線性與等變異的形式。
3. **若模型解釋力還是不夠，再嘗試「連續 $\times$ 連續」的交互項。** 例：$X_1X_2$。

> **原則：一步一步加，每加一種就重新檢查殘差，確認假設是否改善。**

**Step 4. 評估每個候選模型，要留誰、刪誰**
1. 常用指標：$R^2$、Adjusted $R^2$、迴歸標準誤 $s$（整體殘差大小）、係數假設檢定（① Global usefulness F-test ② Nested model partial F-test ③ Individual t-test）
2. 移除冗餘的自變數、交互、轉換
   - **維持階層性（hierarchy）：若保留交互項，通常也保留其對應的主效應。**
   - **一次只動少數幾個預測變數，逐步檢視影響，不要整包一起砍。**

> **目標：得到足夠簡潔、且能抓住母體重要關聯性的模型。**

### 6.3 【材料原文】1007 的 EDA 前置流程

**拿到模型前先做 EDA**
1. **先把問題問清楚**：你要回答什麼？需要哪些資料才能回答？先列清單。
2. **收集並整理資料**：這通常是最花時間的一段。
3. **把資料整理成可分析的樣子**
   - 檢查錯誤：缺漏、離群、單位、編碼、時間序…
   - 把類別變數轉成指標變數（dummy variable, indicator variable）。
4. **把資料畫出來（graph the data）**
   - 用散佈矩陣看變數之間的關係。
   - 先算摘要統計（平均、標準差、分位數）抓感覺。
   - **圖和數字會提示你可能的錯誤，也可能提醒你要做轉換。** 例如：高度偏態的變數，常先取自然對數再分析。

### 6.4 【材料原文】五種轉換的 R Code（0923，逐字抄錄）

**(1) 對數轉換 — 解釋變數（Natural log transformation for explanatory variables）**

圖形比較：
```r
## Read data
AUTO3 <- read.csv("AUTO.csv", header=TRUE)
attach(AUTO3)

par(mfrow=c(1,2))
plot(AUTO3$price, AUTO3$horsepower, ylab = "Y = horsepower", xlab = "X = price")
abline(lm(horsepower~price, data=AUTO3))

plot(log(AUTO3$price), AUTO3$horsepower, ylab = "Y = horsepower", xlab = "X = log(price)")
abline(lm(horsepower~log(price), data=AUTO3))
```

模型比較：
```r
## Summary of two SLR models
lm3.1 <- lm(horsepower ~ price, data=AUTO3)
summary(lm3.1)

lm3.2 <- lm(horsepower ~ log(price), data=AUTO3)
summary(lm3.2)
```

直方圖比較：
```r
## histograms show the difference of distributions
hist(AUTO3$price)
hist(log(AUTO3$price))
```

**(2) 多項式轉換（Polynomial transformation for explanatory variables）**

圖形比較：
```r
## Read data
HOMES3 <- read.csv("HOMES3.csv", header=TRUE)
attach(HOMES3)

## Transformations for X - Polynomial

plot(HOMES3$age, HOMES3$price, ylab = "Y = home price (in $ thousands)", xlab = "X = age (years)")
abline(lm(price ~ age, data=HOMES3))

HOMES3$agesq <- HOMES3$age^2
newX <- seq(min(age), max(age))
newXsq <- newX^2
lines(newX, predict(lm(price ~ age + agesq, data=HOMES3), 
	newdata=data.frame(age=newX,agesq=newXsq)), col=2)
```

模型比較：
```r
## Summary of two MLR models
lm3.1 <- lm(price ~ size + room + parking + age, data=HOMES3)
summary(lm3.1)

lm3.2 <- lm(price ~ size + room + parking + age + agesq, data=HOMES3)
summary(lm3.2)
```

Nested model partial F-test：
```r
## Nested-model F-test
anova(lm3.1, lm3.2)
```

**(3) 倒數轉換（Reciprocal transformation for explanatory variables）**

圖形比較：
```r
## Read data
CARS3 <- read.csv("CARS3.csv", header=TRUE)
attach(CARS3)

## Transformations for X - Reciprocal
CARS3$recipdisplacement <- 1/CARS3$displacement
CARS3$recipweight <- 1/CARS3$weight


par(mfrow=c(1,2))
plot(CARS3$weight, CARS3$fuel, ylab = "Y = fuel efficiency (km/L)", xlab = "X = weight (kg)")
abline(lm(fuel~weight, data=CARS3))
plot(CARS3$recipweight, CARS3$fuel, ylab = "Y = fuel efficiency (km/L)", xlab = "recipX = weight (kg)")
abline(lm(fuel~recipweight, data=CARS3))
```

模型比較：
```r
## Summary of two MLR models
lm3.1 <- lm(fuel ~ weight + displacement + door, data=CARS3)
summary(lm3.1)

lm3.2 <- lm(fuel ~ recipweight + displacement + door, data=CARS3)
summary(lm3.2)
```

模型診斷（轉換前後並排比較，2×3 面板）：
```r
#### [Extra: Diagnostic Plots]
## Residual plot, Histogram, QQ-plot

par(mfrow=c(2,3))

plot(fitted(lm3.1), residuals(lm3.1), xlab="Fitted", ylab="Residuals"); abline(h=0)
hist(residuals(lm3.1))
qqnorm(residuals(lm3.1), ylab="Residuals"); qqline(residuals(lm3.1))

plot(fitted(lm3.2), residuals(lm3.2), xlab="Fitted", ylab="Residuals"); abline(h=0)
hist(residuals(lm3.2))
qqnorm(residuals(lm3.2), ylab="Residuals"); qqline(residuals(lm3.2))
```

**(4) $Y$ 的對數轉換（Natural log transformation for the response variable）**

圖形比較：
```r
## Read data
AIR3 <- read.csv("AIR.csv", header=TRUE)
attach(AIR3)

	## Log Transformation on Y
	## EDA
	hist(AIR3$spm)
	hist(log(AIR3$spm))
	hist(AIR3$o3)

## scatter plot with regression line
par(mfrow=c(1,2))

plot(AIR3$o3, AIR3$spm, ylab="Y = SPM concentration (ppb)", xlab="X = O3 concentration (ppb)")
abline(lm(spm~o3,data=AIR3))

plot(AIR3$o3, log(AIR3$spm), ylab="Y = SPM concentration (ppb)", xlab="X = O3 concentration (ppb)")
abline(lm(log(spm)~o3,data=AIR3))
```

模型比較：
```r
## Summary of two SLR models
lm3.1 <- lm(spm ~ o3, data=AIR3)
summary(lm3.1)

lm3.2 <- lm(log(spm) ~ o3, data=AIR3)
summary(lm3.2)
```

模型診斷：
```r
#### [Extra: diagnostic plots]
## Residual plot, Histogram, QQ-plot

par(mfrow=c(2,3))

plot(fitted(lm3.1), residuals(lm3.1), xlab="Fitted", ylab="Residuals");abline(h=0)
hist(residuals(lm3.2))
qqnorm(residuals(lm3.2), ylab="Residuals");qqline(residuals(lm3.2))

plot(fitted(lm3.2), residuals(lm3.2), xlab="Fitted", ylab="Residuals");abline(h=0)
hist(residuals(lm3.2))
qqnorm(residuals(lm3.2), ylab="Residuals");qqline(residuals(lm3.2))
```

> 【評註】上面這段診斷程式碼的第一組（lm3.1）在 hist 與 qqnorm 誤用了 `residuals(lm3.2)`，
> 是原始講義的複製貼上錯誤。**逐字保留**，但轉 Python 時必須修正為 `residuals(lm3.1)`。

**(5) $X$ 與 $Y$ 的同時轉換（Transformations for the response and explanatory variables）**

圖形比較：
```r
## Read data
BILL3 <- read.csv("BILL.csv", header=TRUE)
attach(BILL3)

	## Log Transformation on X and Y
	## EDA
	par(mfrow=c(2,2))
	hist(BILL3$Aug)
	hist(log(BILL3$Aug))
	hist(BILL3$Sep)
	hist(log(BILL3$Sep))

## scatter plot with regression line
par(mfrow=c(1,2))

plot(BILL3$Aug, BILL3$Sep, ylab = "Y = amount of bill statement in September", xlab = "X = amount of bill statement in August")
abline(lm(Sep ~ Aug, data=BILL3))

plot(log(BILL3$Aug), log(BILL3$Sep), ylab = "Y = amount of bill statement in September", xlab = "X = amount of bill statement in August")
abline(lm(log(Sep) ~ log(Aug), data=BILL3))
```

模型比較：
```r
# Summary of two SLR models
lm3.bill.1 <- lm(Sep ~ Aug, data=BILL3)
summary(lm3.bill.1)

lm3.bill.2 <- lm(log(Sep) ~ log(Aug), data=BILL3)
summary(lm3.bill.2)
```

### 6.5 【材料原文】0930 的轉換實戰：$\varepsilon$（epsilon）保護與六模型比較 ★

0930 的腳本示範了**避免 $\log(0)$ 與 $1/0$** 的標準做法，以及「三組 X 轉換 × 兩種 Y 形式」的系統性比較。

```r
####-------------------------------------------------------####
####  Six Models: (Three X-transform sets) × (Two Y forms)
####  Dataset already in `dat`; if not, run your EDA block to read file.
####  Y1 = log(Usage_kWh + eps_y) ; Y2 = 1/(Usage_kWh + eps_y_inv)
####  X-set A: log(CO2+0.001), log(Lag+0.001), log(Lead+0.001)
####  X-set B: log(1/LagPF), log(1/LeadPF)
####  X-set C: A + B
####-------------------------------------------------------####

## --- Universal transforms (avoid log(0)/1/0) ---
eps_y     <- 0.001
eps_y_inv <- 1e-6
eps_x     <- 0.001        # for log of CO2, currents
eps_pf    <- 1e-6         # for PF inverse in case of zeros

dat$Y_log <- log(dat$Usage_kWh + eps_y)
dat$Y_inv <- 1 / (dat$Usage_kWh + eps_y_inv)

dat$log_CO2             <- log(dat$CO2 + eps_x)
dat$log_Lagging_Current <- log(dat$Lagging_Current + eps_x)
dat$log_Leading_Current <- log(dat$Leading_Current + eps_x)

dat$log_inv_LagPF  <- log(1 / (dat$Lagging_Current_Power_Factor  + eps_pf))
dat$log_inv_LeadPF <- log(1 / (dat$Leading_Current_Power_Factor + eps_pf))

## --- helper: concise report for a (full, reduced) pair ---
report_pair <- function(full_fit, red_fit, label){
  cat("\n==================== ", label, " ====================\n", sep="")
  cat("\n[Full model] formula:\n"); print(formula(full_fit))
  cat("\nSummary (Full):\n"); print(summary(full_fit))
  cat("\nConfint (Full):\n"); print(confint(full_fit))
  cat("\nSummary (Reduced):\n"); print(summary(red_fit))

  cat("\nNested F (Reduced -> Full):\n")
  a <- anova(red_fit, full_fit); print(a)
  Fv <- a$F[2]; pv <- a$`Pr(>F)`[2]
  cat(sprintf("Partial F (NSM) = %.6f, p = %.6f\n", Fv, pv))

  cat("\nModel fit metrics:\n")
  cat(sprintf("Full:   R2=%.6f, AdjR2=%.6f, AIC=%.3f, BIC=%.3f\n",
              summary(full_fit)$r.squared, summary(full_fit)$adj.r.squared, AIC(full_fit), BIC(full_fit)))
  cat(sprintf("Reduced:R2=%.6f, AdjR2=%.6f, AIC=%.3f, BIC=%.3f\n",
              summary(red_fit)$r.squared, summary(red_fit)$adj.r.squared, AIC(red_fit), BIC(red_fit)))

  cat("\nGlobal F (Full):\n"); print(summary(full_fit)$fstatistic)
  cat("\nGlobal F (Reduced):\n"); print(summary(red_fit)$fstatistic)

  co <- summary(full_fit)$coefficients
  coef_table <- data.frame(
    Term      = rownames(co),
    Estimate  = sprintf("%.6f", co[,1]),
    Std_Error = sprintf("%.6f", co[,2]),
    t_value   = sprintf("%.6f", co[,3]),
    p_value   = sprintf("%.6f", co[,4]),
    row.names = NULL
  )
  cat("\nCoefficients (Full, 6dp):\n"); print(coef_table)
  invisible(list(nested= a, coef_table=coef_table))
}

####========================================================
####  1A) Y = log(Usage)  |  X-set A (log currents & log CO2)
####========================================================
m1A_full <- lm(
  Y_log ~ log_CO2 + log_Lagging_Current + log_Leading_Current +
    Lagging_Current_Power_Factor + Leading_Current_Power_Factor + NSM,
  data = dat
)
m1A_red  <- update(m1A_full, . ~ . - NSM)
report_pair(m1A_full, m1A_red, "1A: Y=log(Usage); X=log(CO2,Lag,Lead)+PFs(+NSM)")

####========================================================
####  1B) Y = 1/Usage     |  X-set A (log currents & log CO2)
####========================================================
m1B_full <- lm(
  Y_inv ~ log_CO2 + log_Lagging_Current + log_Leading_Current +
    Lagging_Current_Power_Factor + Leading_Current_Power_Factor + NSM,
  data = dat
)
m1B_red  <- update(m1B_full, . ~ . - NSM)
report_pair(m1B_full, m1B_red, "1B: Y=1/Usage; X=log(CO2,Lag,Lead)+PFs(+NSM)")

####========================================================
####  2A) Y = log(Usage)  |  X-set B (log inverse PFs)
####========================================================
m2A_full <- lm(
  Y_log ~ CO2 + Lagging_Current + Leading_Current +
    log_inv_LagPF + log_inv_LeadPF + NSM,
  data = dat
)
m2A_red  <- update(m2A_full, . ~ . - NSM)
report_pair(m2A_full, m2A_red, "2A: Y=log(Usage); X=CO2,Currents + log(1/PFs)(+NSM)")

####========================================================
####  2B) Y = 1/Usage     |  X-set B (log inverse PFs)
####========================================================
m2B_full <- lm(
  Y_inv ~ CO2 + Lagging_Current + Leading_Current +
    log_inv_LagPF + log_inv_LeadPF + NSM,
  data = dat
)
m2B_red  <- update(m2B_full, . ~ . - NSM)
report_pair(m2B_full, m2B_red, "2B: Y=1/Usage; X=CO2,Currents + log(1/PFs)(+NSM)")

####========================================================
####  3A) Y = log(Usage)  |  X-set C (A + B)
####========================================================
m3A_full <- lm(
  Y_log ~ log_CO2 + log_Lagging_Current + log_Leading_Current +
    log_inv_LagPF + log_inv_LeadPF + NSM,
  data = dat
)
m3A_red  <- update(m3A_full, . ~ . - NSM)
report_pair(m3A_full, m3A_red, "3A: Y=log(Usage); X=log(CO2,Currents) + log(1/PFs)(+NSM)")

####========================================================
####  3B) Y = 1/Usage     |  X-set C (A + B)
####========================================================
m3B_full <- lm(
  Y_inv ~ log_CO2 + log_Lagging_Current + log_Leading_Current +
    log_inv_LagPF + log_inv_LeadPF + NSM,
  data = dat
)
m3B_red  <- update(m3B_full, . ~ . - NSM)
report_pair(m3B_full, m3B_red, "3B: Y=1/Usage; X=log(CO2,Currents) + log(1/PFs)(+NSM)")
```

**選 Y 形式的方法：把三種 Y 的診斷三圖排成 3×3 面板直接比對**

```r
####-------------------------------------------------------####
####  Compare Y forms via diagnostics (Residual, Hist, QQ)
####  固定一組 X 規格（可切換），比較 Y_raw / Y_log / Y_inv 三者
####-------------------------------------------------------####

## 1) 讀檔（若已讀可略過）
file_path <- "C:/Users/user/Desktop/商管統計資料分析/In-class pratical 1/steel_ind_energy_a.csv"
dat <- read.csv(file_path, header = TRUE)

## 2) 準備轉換欄位（避免 log(0) 與 1/0）
eps_y  <- 0.001
eps_x  <- 0.001
eps_pf <- 1e-6

dat$Y_raw <- dat$Usage_kWh
dat$Y_log <- log(dat$Usage_kWh + eps_y)
dat$Y_inv <- 1 / (dat$Usage_kWh + eps_y)   # 你偏好的倒數處理

dat$log_CO2             <- log(dat$CO2 + eps_x)
dat$log_Lagging_Current <- log(dat$Lagging_Current + eps_x)
dat$log_Leading_Current <- log(dat$Leading_Current + eps_x)

dat$log_inv_LagPF  <- log(1 / (dat$Lagging_Current_Power_Factor  + eps_pf))
dat$log_inv_LeadPF <- log(1 / (dat$Leading_Current_Power_Factor + eps_pf))

## 3) 這裡選擇「X 的規格」與「是否包含 NSM」
##    x_spec 可選： "raw" | "logA" | "invPF" | "all"
##      - raw  : CO2, Lag, Lead, LagPF, LeadPF
##      - logA : log_CO2, log_Lag, log_Lead + (原始)PF
##      - invPF: (原始)CO2, Lag, Lead + log_inv_*PF
##      - all  : log_CO2, log_Lag, log_Lead + log_inv_*PF
x_spec      <- "raw"   # << 想改成「對數處理」就用 "logA"，或 "invPF"/"all"
include_nsm <- TRUE    # << 若要固定不含 NSM，改成 FALSE

get_predictors <- function(spec, include_nsm = TRUE){
  base <- switch(spec,
    "raw"   = c("CO2","Lagging_Current","Leading_Current",
                "Lagging_Current_Power_Factor","Leading_Current_Power_Factor"),
    "logA"  = c("log_CO2","log_Lagging_Current","log_Leading_Current",
                "Lagging_Current_Power_Factor","Leading_Current_Power_Factor"),
    "invPF" = c("CO2","Lagging_Current","Leading_Current",
                "log_inv_LagPF","log_inv_LeadPF"),
    "all"   = c("log_CO2","log_Lagging_Current","log_Leading_Current",
                "log_inv_LagPF","log_inv_LeadPF")
  )
  if (include_nsm) base <- c(base, "NSM")
  base
}

Xvars <- get_predictors(x_spec, include_nsm)

## 4) 拟合三個模型（僅改 Y；X 固定）
mk_form <- function(y, Xvars){
  as.formula(paste(y, "~", paste(Xvars, collapse = " + ")))
}

fit_raw <- lm(mk_form("Y_raw", Xvars), data = dat)
fit_log <- lm(mk_form("Y_log", Xvars), data = dat)
fit_inv <- lm(mk_form("Y_inv", Xvars), data = dat)

## 5) 畫 3×3 診斷面板：每列是一種 Y（Residual plot / Histogram / QQ）
op <- par(mfrow = c(3,3), mar = c(4,4,2.5,1))

## ---- Row 1: Y_raw ----
plot(fitted(fit_raw), residuals(fit_raw),
     xlab = "Fitted", ylab = "Residuals",
     main = "Residuals vs Fitted | Y = Usage")
abline(h = 0)
hist(residuals(fit_raw), main = "Histogram of Residuals | Y = Usage", xlab = "Residuals")
qqnorm(residuals(fit_raw), main = "QQ-plot | Y = Usage"); qqline(residuals(fit_raw))

## ---- Row 2: Y_log ----
plot(fitted(fit_log), residuals(fit_log),
     xlab = "Fitted", ylab = "Residuals",
     main = "Residuals vs Fitted | Y = log(Usage)")
abline(h = 0)
hist(residuals(fit_log), main = "Histogram | Y = log(Usage)", xlab = "Residuals")
qqnorm(residuals(fit_log), main = "QQ-plot | Y = log(Usage)"); qqline(residuals(fit_log))

## ---- Row 3: Y_inv ----
plot(fitted(fit_inv), residuals(fit_inv),
     xlab = "Fitted", ylab = "Residuals",
     main = "Residuals vs Fitted | Y = 1/Usage")
abline(h = 0)
hist(residuals(fit_inv), main = "Histogram | Y = 1/Usage", xlab = "Residuals")
qqnorm(residuals(fit_inv), main = "QQ-plot | Y = 1/Usage"); qqline(residuals(fit_inv))

par(op)  # 還原畫布
```

### 【評註】這回答什麼行銷/商業問題

- **$\log(Y)$**：銷售額、客單價、LTV 幾乎都右偏 → 取 log 後係數變成「**百分比效果**」，正好是行銷人習慣的「提升 X% 」語言。
- **$\log(X)$**：廣告投入的**遞減報酬**（0909 明說：「若『廣告費用』與『銷售額』之間呈遞減報酬，可能違反線性關係假設，需要轉換模型」）。
- **$1/X$**：0923 用在「重量 → 油耗」，行銷對應的是「距離 → 到店率」這類反比關係。
- **$X^2$**：價格 → 銷量的倒 U 型（有最適價格點）。

---

## 7. 迴歸式的分類地圖（1007）

### 【材料原文】Reminder — 依 Y / X 的型態決定用哪個模型 ★

| $Y$ 的型態 | $X$ 的型態 | 對應模型 |
|---|---|---|
| 連續變數 | 連續變數 | **線性模型（Linear Model，LM）** |
| 連續變數 | 連續變數 ＋ 類別變數 | **共變異數分析（Analysis of Covariance，ANCOVA）** |
| 連續變數 | 類別變數 | **變異數分析（Analysis of Variance，ANOVA）**／**實驗設計（Experimental Design）** |
| 類別變數 | 連續變數或類別變數 | **廣義線性模型（Generalized Linear Model，GLM）** |

---

## 8. ANCOVA：連續 + 類別的混合模型（1007）★

### 8.1 【材料原文】模型目的與直覺

- **模型目的**：在比較「類別變數（不同處理、組別）」對被解釋變數 $Y$ 的影響時，同時用「連續共變數」$X$ 做線性校正，以降低雜訊、提高檢定力。
- **直覺**：先用共變數解釋掉一部分 $Y$ 的系統性變異，再比較各組「在相同共變數水準下」的**調整後平均**。
- **與 ANOVA 的差別**：ANOVA 僅比較各組類別變數間的「原始平均」；ANCOVA 是先「校正」共變數後，再比較「調整後平均」。
- **與迴歸的差異**：ANCOVA 就是廣義線性模型（GLM）的特例——將組別以虛擬變數表示，將共變數當成連續解釋變數。
- **經典使用案例**：實驗前測分數作為共變數，並檢驗不同教學方法（組）對後測分數（$Y$）的影響。

### 8.2 【材料原文】兩個模型層級

**(A) 斜率平行（無交互作用）**
- 直覺：各組類別間有不同「截距」，但對 $X$ 的斜率都相同。線彼此平行。
- **處理上建議先把 $X$ 做中心化以利數值穩定與解讀。**

$$X_i^{c}=X_i-\bar{X}$$
$$Y_i = \mu + \tau_{g(i)} + \beta X_i^{c} + \varepsilon_i,\qquad \varepsilon_i \sim \mathcal{N}(0,\sigma^2)$$

- $Y_i$：第 $i$ 筆觀測的反應變數（連續）
- $g(i)$：第 $i$ 筆資料所屬組別（因子水準），共有 $a$ 組
- $X_i$：第 $i$ 筆共變數（連續）；$\bar{X}$：全樣本 $X$ 的平均
- $\mu$：全體基準截距
- $\tau_{g(i)}$：組別效果，常用限制為 $\sum_{g=1}^a\tau_g=0$
- $\beta$：共變數斜率
- $\varepsilon_i$：隨機誤差，期望 0、變異 $\sigma^2$

**(B) 斜率不同（有交互作用）**
- 直覺：不同組類別間對 $X$ 的影響強弱不同。**需先檢定交互作用是否顯著，再決定如何報告。**
- 要先進行斜率是否同質的假說檢定：$H_0: \gamma_{1}=\gamma_{2}=\cdots=\gamma_{a}=0$

$$Y_i = \mu + \tau_{g(i)} + \beta X_i^{c} + \gamma_{g(i)} X_i^{c} + \varepsilon_i$$

- $\gamma_{g(i)}$：組別 $g$ 與 $X$ 的交互作用係數（代表每組相對共同斜率的加成）

### 8.3 【材料原文】調整後平均（Adjusted mean）

把每一組的原始組均數，沿著共同斜率 $\hat\beta$「平移」到同一個 $X$ 基準（常取全體 $\bar X$），再進行比較。

以全體 $\bar{X}$ 為基準的調整後平均：
$$\hat{\mu}_{g}^{\,\text{adj}} = \bar{Y}_{g\cdot} - \hat{\beta}\bigl(\bar{X}_{g\cdot}-\bar{X}_{\cdot\cdot}\bigr)$$

在任意基準 $c$ 的調整後平均：
$$\hat{\mu}_{g}(c) = \hat{\alpha}_{g} + \hat{\beta}(c-\bar{X}_{\cdot\cdot}),\qquad \hat{\alpha}_{g}= \bar{Y}_{g\cdot}-\hat{\beta}(\bar{X}_{g\cdot}-\bar{X}_{\cdot\cdot})$$

調整後平均之信賴區間：
$$\hat{\mu}_{g}(c)\ \pm\ t_{1-\alpha/2,\ \mathrm{df}_{\text{error}}}\;\mathrm{SE}\!\left[\hat{\mu}_{g}(c)\right],\qquad \mathrm{SE}\!\left[\hat{\mu}_{g}(c)\right]= \sqrt{\mathbf{l}_g(c)^\top \widehat{\mathrm{Var}}(\hat{\boldsymbol{\beta}}) \mathbf{l}_g(c)}$$

### 8.4 【材料原文】ANCOVA 的檢定順序 ★★

**Step 1. 檢定交互作用是否存在（斜率是否同質）**
- 比較以下兩個模型：
  - Reduced（無交互作用）：$Y \sim G+X$
  - Full（有交互作用）：$Y \sim G+X+G{:}X$
- $H_0: \gamma_{1}=\gamma_{2}=\cdots=\gamma_{a}=0$

$$F_{\text{int}} = \frac{\bigl(\mathrm{SSE}_{\text{reduced}}-\mathrm{SSE}_{\text{full}}\bigr)/df_{\text{int}}}{\mathrm{SSE}_{\text{full}}/df_{\text{err,full}}} \sim F\bigl(df_{\text{int}},\,df_{\text{err,full}}\bigr)$$

- $df_{\text{int}}$：交互作用自由度（例：兩組時為 1）
- $df_{\text{err,full}}$：full model 誤差自由度
- **上述檢定其實就是 Partial F-Test。**
- **若顯著 → 報告交互作用並改以「在特定 $X$ 水準」下進行比較。**
- **若不顯著 → 可採「平行斜率」模型繼續檢定組別主效應。**

**Step 2. 檢定在 $X$ 下的組別主效應（僅在交互作用不顯著時進行）**
- 比較 $Y\sim X$ 與 $Y\sim X+G$，即「控制 $X$ 後，組別是否仍有差異」

$$F_{\text{group}\mid X} = \frac{\bigl(\mathrm{SSE}_{X}-\mathrm{SSE}_{X+G}\bigr)/(a-1)}{\mathrm{SSE}_{X+G}/(N-a-1)} \sim F(a-1,\,N-a-1)$$

- $a$：組別數；$N$：樣本數
- 分子自由度 $a-1$：組別主效應之自由度
- 分母自由度 $N-a-1$：誤差自由度（截距：1、共變數：1、組別：$a-1$）

**自由度判斷**：$\mathrm{df}_{\text{group}}=a-1$；$\mathrm{df}_{X}=1$；$\mathrm{df}_{\text{error}}=N-a-1$

**若斜率顯著不同，則應依條件報告結果**
- 線不平行就像「不同斜度的坡」。在坡的不同位置（不同 $X$），兩組差距會改變。
- **此時應選幾個代表性的 $X$（例如分位數或平均）逐一進行比較。**

### 8.5 【材料原文】指示變數（Indicator）與 baseline ★

- 跟虛擬變數（dummy variable）是一樣的概念，只是命名方式不同。
- baseline 的概念相當於是虛擬變數中設定的基準值，**他是一個相對的參考值，提供判斷類別使用，而非一項具有實質意義的絕對數值。**
- **更換 baseline，只會把「截距」和「組別係數」重新命名、數值重分配，但預測值、殘差、$R^2$ 都不變。**
- 例如：當 baseline = 0 代表春天，則 1 = 夏、2 = 秋、3 = 冬；當 baseline = 0 代表夏天，則 1 = 秋、2 = 冬、3 = 春。上述兩組僅是基準點不同，並不影響資料判讀。
- 把 $X$ 做中心化（減去全樣本平均），之後「截距」就能被解釋成「**在典型 $X$ 水準（$\bar X$）時的平均 $Y$**」。

**兩個 SLR 的 $R^2$ 無法直接進行比較 ★**
- $R^2$ 的概念是「這條線把自己的那一群資料解釋得有多好」。
- 兩群資料的「分散程度」與「平均值」不同，算出來的 $R^2$ 基準不同，拿來比較就像用兩把不同刻度的尺量身高再比誰高，有失公允。
- **更重要的是，兩個 SLR 不是在同一筆資料上、也不是巢狀模型，所以無法透過 Partial F-test 來比較孰優孰劣。**

**重點提醒！★★**
> 要分析同一資料集中的不同類別資料時，**不可以直接拿各類別的 SLR 來比**，應該放在同一個模型中，並檢驗交互項的顯著性，進而比較各類別變數對被解釋變數的影響性。
>
> 舉例：要檢驗管院與非管院的學生的學習效果，不可以拿管院做一份 SLR，再拿非管院做一份 SLR 後進行比較，這樣沒有意義，應該要將管院與非管院資料放在同一模型中，並檢驗管院與非管院的交互作用是否顯著後，才能檢驗各類別對被解釋變數的影響顯著性。

### 8.6 【材料原文】類別變數超過兩個 levels ★

- 如同前述 dummy variables 的觀念，當某一類別變數中，其分類有 $n$ 項（$n$ levels）時，我們就會需要 **$n-1$ 個 indicator variables**。
- 其中被設為基準的項目稱為 **baseline category** 或 **reference category**。
- **在 R 的邏輯中，通常是依類別名稱的首個字母來排序（A～Z），越靠前的越容易被設定為 baseline category**，但若有需要可以視需求進行 baseline 的設定。

六都的例子（台北、新北、桃園、台中、台南、高雄，以台北為基準）：
- 台北：截距項 $=0.3453+0\times D_{新北}+0\times D_{桃園}+0\times D_{台中}+0\times D_{台南}+0\times D_{高雄}$
- 新北：截距項 $=0.3453+1\times D_{新北}+0\times D_{桃園}+0\times D_{台中}+0\times D_{台南}+0\times D_{高雄}$
- 桃園：截距項 $=0.3453+0\times D_{新北}+1\times D_{桃園}+0\times D_{台中}+0\times D_{台南}+0\times D_{高雄}$
- （其餘同理）
- **可理解成，考慮某項時，除他之外每一項係數都會是 0，而在他本身係數不會是 0。**

### 8.7 【材料原文】reference level 的選擇規則 ★★（教科書罕見）

以 CARS5 的 brand（6 個 levels，基準為 Audi）為例：

- 從資料中可以發現，品牌中的 Porsche 與品牌基準項的 Audi 是存在顯著差異的，且引入 brand 也使 $R^2$ 提升約 3%，解釋力也顯著上升。
- 在所有品牌中，只有 BMW 的截距差為正（代表 BMW 的排序比 Audi 靠前），而挑選在排名靠中間的 Audi，向上或向下比較，其實落差不會到太大，可能就不會出現「顯著差異」的結果。
- **也就是說，若基準項挑在排序正中間的，可能會出現全部「不顯著」的結果。**
- **反過來說，如果作為基準項的是排序最高或最低的，位於排序另一側的類別變數反而比較容易出現「顯著差異」的結果，本來不顯著的也有可能會變得顯著。**

**看係數判斷基準項位置的三條規則 ★**
| 觀察到的現象 | 推論 |
|---|---|
| 其餘類別的係數**都是正的** | 代表挑到**排序最低項**作為基準項 |
| 其餘類別的係數**都是負的** | 代表挑到**排序最高項**作為基準項 |
| 其餘類別的係數**有正有負** | 代表挑到**中間項**作為基準項，**可能要重挑** |

> **因此在統計上而言，進行 ANCOVA 的時候，reference level 的選定非常重要。**

**relevel 的用法**
```r
## relevel
brand <- relevel(as.factor(brand), ref="BMW")
```
- **relevel 在解讀上應該要理解成 reference level 而不是 re-level。**
- `as.factor` 是指定某一字串為變數，而非字元（character），確保 R 有將指定的字串認定為類別順序。
- `ref` 則是指定某一項為 reference level。
- 白話來說，這串就是指定，現在想要指定 brand 作為類別變數，並且選擇 BMW 為基準項。

改為 BMW 後的觀察：
- 會發現以 BMW 為 reference level 後，其餘各項係數皆轉變為負。
- **值得注意的是 TOYOTA 的 p-value $=0.0884>0.05$，但不代表他不重要，雖然在不顯著的範疇但其 p-value 很接近 0.05，是值得關注的一項。**
- 因此 ANCOVA 的核心概念就是，當迴歸式引入「類別變數」後，比較類別變數間不同的 levels 所能呈現的訊息。

### 8.8 【材料原文】ANCOVA 的完整 R Code（CARS5，逐字抄錄）

```r
## Read data
CARS5 <- read.csv("CARS5.csv", header=TRUE)
attach(CARS5)

summary(CARS5)
```

```r
  table(production); table(type); table(brand)
```

```r
plot(CARS5$recipweight, CARS5$fuel, xlab="1/Weight", ylab="Fuel Efficiency")
cor(CARS5$recipweight, CARS5$fuel)
```

分類後模型的 Scatter plot（兩條各自的 SLR）：
```r
CARS5$group1[which(CARS5$production == "imported")] <- 2
CARS5$group1[which(CARS5$production == "domestic")] <- 4

## Plots of two separate SLRs
plot(CARS5$recipweight, CARS5$fuel, type="n", xlab="1/Weight", ylab="Fuel Efficiency")
for (i in 1:nrow(CARS5)) 
	points(CARS5$recipweight[i], CARS5$fuel[i], pch=substr(CARS5$production[i],1,1), col=CARS5$group1[i])
abline(lm(fuel~recipweight, data=subset(CARS5, production=="imported")), col=2)
abline(lm(fuel~recipweight, data=subset(CARS5, production=="domestic")), col=4)
```

```r
summary(lm(fuel ~ recipweight, data=subset(CARS5, production=="imported")))
summary(lm(fuel ~ recipweight, data=subset(CARS5, production=="domestic")))

##上面是各類別下的 summary
## Basic model for one single dataset:
lm5.0 <- lm(fuel ~ recipweight + production, data=CARS5)
summary(lm5.0)
```

```r
## Plot of lm5.0:
plot(CARS5$recipweight, CARS5$fuel, type="n", xlab="1/Weight", ylab="Fuel Efficiency")
for (i in 1:nrow(CARS5)) 
	points(CARS5$recipweight[i], CARS5$fuel[i], pch=substr(CARS5$production[i],1,1), col=CARS5$group1[i])
for (i in 0:1) 
	lines(sort(CARS5$recipweight[CARS5$group1==(i+1)*2]), sort(fitted(lm5.0)[CARS5$group1==(i+1)*2]), col=(i+1)*2 )
```

```r
## Since 'production' is not significant...
lm5 <- lm(fuel ~ recipweight, data=CARS5)
summary(lm5)

anova(lm5, lm5.0)
```

```r
## Consider more explanatory variables:
lm5.1 <- lm(fuel ~ recipweight + recipdisplacement + door, data=CARS5)
summary(lm5.1)
```

```r
## See if 'production' is a good predictor:
lm5.2 <- lm(fuel ~ recipweight + recipdisplacement + door + production, data=CARS5)
summary(lm5.2)
```
> 這裡直觀的解釋是：當考量到「重量」、「排氣量」、「車門數」後，國產車與進口車在燃油效率的表現上沒有顯著差異。

```r
## Nested model test:
anova(lm5.1,lm5.2)
```

```r
## Replace 'production' with 'type':
lm5.3 <- lm(fuel ~ recipweight + recipdisplacement + door + type, data=CARS5)
summary(lm5.3)

anova(lm5.1,lm5.3)
```
> 簡單來說，在這裡 Car 是 baseline，因為字母 C 排序比字母 T 靠前，係數 $-9.532e{-}01 \approx -0.95$，代表 Truck 平均而言比 Car 的燃油效率差 0.95，且這個差距是顯著的。而這個模型對於燃油效率的解釋力也比前述的模型再更高一些。$R^2:0.8342>0.8229$

**如何解釋迴歸結果（依類別列出子迴歸式）★**
- Baseline（Car）：
$$\text{Estimated Fuel Efficiency(Km/L)}=0.9532+9918\times \frac{1}{\text{weight}}+10070\times \frac{1}{\text{displacement}}+0.3181\times \text{door}$$
- Truck：
$$\text{Estimated Fuel Efficiency(Km/L)}=(0.9532-0.9532)+9918\times \frac{1}{\text{weight}}+10070\times \frac{1}{\text{displacement}}+0.3181\times \text{door}$$
- **會發現在 type 這個類別變數下，後續三項係數都一樣，唯一不同的是截距項。**
- 透過檢定後的結果，我們可以知道這個截距是有顯著意義的，且能夠提高模型的解釋力。

**檢驗同質變異數（分組殘差比較）**
```r
# Comparing the Variances of Residuals

	CARS5$group2[which(CARS5$type == "truck")] <- 2
	CARS5$group2[which(CARS5$type == "car")] <- 4

par(mfrow=c(1,2))

plot(fitted(lm5.3), residuals(lm5.3), type="n", xlab="Estimated Fuel", ylab="Residual Fuel")
for (i in 1:nrow(CARS5))
	points(fitted(lm5.3)[i], residuals(lm5.3)[i], pch=substr(CARS5$type[i],1,1), col=CARS5$group2[i])
abline(h=0, lty=3)

boxplot(lm5.3$residual ~ CARS5$type)
```
- 左邊是 residual plots，只是可以發現引入類別後，藍色的 C 代表 Car，紅色的 t 代表 Truck。
- 右邊是 side by side box plot。
- **兩者中位數一樣，只是 Car 資料比較多，上下 range 就也比較寬。但我們可以得知其實 Car 跟 Truck 的 residual 表現上沒有顯著差異，畢竟兩者資料量本也有落差。**

**診斷三圖**
```r
# Diagnostic plots:Residual plot, Histogram, QQ-plot
par(mfrow=c(1,3))
plot(fitted(lm5.3), residuals(lm5.3), xlab="Fitted", ylab="Residuals"); abline(h=0)
hist(residuals(lm5.3))
qqnorm(residuals(lm5.3), ylab="Residuals"); qqline(residuals(lm5.3))
```

**多 levels 類別（brand）與 relevel**
```r
## Replace 'type' with 'brand', which has 6 levels:
lm5.4 <- lm(fuel ~ recipweight + recipdisplacement + door + brand)
summary(lm5.4)

anova(lm5.1,lm5.4)
```

```r
## relevel
brand <- relevel(as.factor(brand), ref="BMW")
```

```r
lm5.4 <- lm(fuel ~ recipweight + recipdisplacement + door + brand)
summary(lm5.4)
```

---

## 9. 交互作用（Interaction）（1007）★★

> 這是任務要求的第 4 項（後半）。

### 9.1 【材料原文】為什麼需要交互項

- 到目前為止，課堂中教到的迴歸式中，各個解釋變數間對被解釋變數的影響都是分開的，**各項變因對 $Y$ 的影響具有相加性**。
- 實際上，不同變數之間對被解釋變數的影響會存在著「連動關係」，例如：$X_2$ 對 $Y$ 的影響上升時，$X_1$ 對 $Y$ 的影響可能上升或下降（未必等比例）。
- **若只考慮相加性，相當於是忽略了交互作用帶來的影響，在估計時容易失真。**
- 因此交互作用便是將「兩項解釋變數相乘」形成一項新變數，並賦予該「交乘項」係數，用以表示兩變數間的關聯性。
- **交乘項也可以是三項或是四項以上的交乘，但除非有非常明確的理論依據，否則三項以上的交乘項就已經不太必要。**

### 9.2 【材料原文】完整交互模型的建構與拆解 ★★

假設台北、台中、高雄三個城市之指標變數如下表示：

$$\begin{array}{|l|c|c|}\hline\text{City} & \text{D1} & \text{D2} \\\hline\text{CT} & 0 & 0 \\\text{KH} & 1 & 0 \\\text{TP} & 0 & 1 \\\hline\end{array}$$

想知道 Cost 與 Revenue 之間的關係是否會隨城市不同而改變。

**Full interaction model**
$$\text{E(revenue)}=\beta_0+\beta_1\times\text{cost}+\beta_2\times D_1+\beta_3 \times D_2+\beta_4\times \text{cost}\times D_1 +\beta_5 \times \text{cost} \times D_2$$

在這裡 $D_1,D_2$ 所指的類別變數都是城市，只是拆分成兩個「指標變數」來代指不同城市，和二進位制有類似的概念：
- $(D_2,D_1)=(0,0)$ 是基準項（台中）
- $(D_2,D_1)=(0,1)$ 是高雄
- $(D_2,D_1)=(1,0)$ 是台北
- **簡單來說當以類別為變數時，$D$ 這項僅具有「分類」功能，並不是代表很多「不同的變數」。**

整個方程式可以理解成：
- 被解釋變數：$\text{E(revenue)}$
- 解釋變數：$\text{cost}$、$\text{城市}$、$\text{cost}\times \text{城市}$
- 指標變數：$D_1,D_2$

**各城市模型的代入拆解 ★**

台中市（$D_1=0,D_2=0$）：
$$\mu_{\text{revenue}\mid \text{cost,CT}}=\beta_0+\beta_1\times\text{cost}$$

高雄市（$D_1=1,D_2=0$）：
$$\mu_{\text{revenue}\mid \text{cost,KH}}=(\beta_0 +\beta_2) +(\beta_1+\beta_4) \times \text{cost}$$
- $\beta_2$ 指的是台中市與高雄市的「**截距差**」。
- $\beta_4$ 指的是台中市與高雄市的「**斜率差**」。

台北市（$D_1=0,D_2=1$）：
$$\mu_{\text{revenue}\mid \text{cost,TP}}=(\beta_0 +\beta_3) +(\beta_1+\beta_5) \times \text{cost}$$
- $\beta_3$ 指的是台中市與台北市的「**截距差**」。
- $\beta_5$ 指的是台中市與台北市的「**斜率差**」。

### 9.3 【材料原文】交互項的 R 寫法與報表判讀 ★

```r
RC <- read.table("revcost.txt", header=T)
attach(RC)

fitRC <- lm(revenue ~ cost*(D1+D2), data=RC)

summary(fitRC)
```

- **`cost*(D1+D2)` 表示 cost 是一項變數、$D_1,D_2$ 是一項變數，會判定為 $\text{cost}\times D_1$ 與 $\text{cost}\times D_2$ 兩項，在報表中則以 `cost:D1` 及 `cost:D2` 來表示這兩個交乘項。**

報表逐項判讀（材料原文）：
- $D_1$ 係數 $-0.6207$ 指的是「高雄相對於台中的截距少 $0.6207$」。p-value $=0.54 \longrightarrow$ 不顯著。
- $D_2$ 係數 $-2.0557$ 指的是「台北相對於台中的截距少 $2.0557$」。p-value $=0.0699 \longrightarrow$ 顯著。
- `cost:D1` 係數 $-0.1663$ 指的是「高雄相對於台中的斜率少 $0.1663$」。p-value $=0.8295 \longrightarrow$ 不顯著。
- `cost:D2` 係數 $2.0377$ 指的是「台北相對於台中的斜率多 $2.0377$」。p-value $=0.0282 \longrightarrow$ 顯著。

> 【評註】原文對 $D_2$（p=0.0699）標為「顯著」，而 8.7 節對 TOYOTA（p=0.0884）標為「不顯著但值得關注」。
> 這是筆記內部的用語不一致。轉 Python 時應以 $\alpha=0.05$ 為準，並把 $0.05<p<0.10$ 標為「邊際顯著／值得關注」。

**進階寫法：直接用 factor，R 自動展開**
```r
lm.RC <- lm(revenue ~ cost * city)
summary(lm.RC)		# Note the reference level of 'city'
```

**換 baseline 後的重新判讀**
```r
city <- relevel(as.factor(city), ref="TP")
lm.RC <- lm(revenue ~ cost * city)
summary(lm.RC)
```
- `cityCT` 係數 $2.0557$：「台中相對於台北的截距多 $2.0557$」。p-value $=0.0699 \longrightarrow$ 接近顯著。
- `cityKH` 係數 $1.4350$：「高雄相對於台北的截距多 $1.4350$」。p-value $=0.1573 \longrightarrow$ 不顯著。
- `cost:cityCT` 係數 $-2.0377$：「台中相對於台北的斜率少 $2.0377$」。p-value $=0.0190 \longrightarrow$ 顯著。
- `cost:cityKH` 係數 $-2.2039$：「高雄相對於台北的斜率少 $2.2039$」。p-value $=0.0282 \longrightarrow$ 顯著。

**檢定交互項是否該留（Nested F）**
```r
lm5.3i <- lm(fuel ~ recipweight + door + recipdisplacement * type, data=CARS5)
summary(lm5.3i)

	anova(lm5.3, lm5.3i)
```

### 9.4 【材料原文】階層性原則（Preserving hierarchy）★

- 若 $X_1$ 的係數 $\beta_1$ 及 $X_2$ 的係數 $\beta_2$ 皆不顯著，但 $X_1 \times X_2$ 的係數 $\beta_3$ 顯著，則在完整模型中**傾向同時保留 $X_1$ 與 $X_2$ 兩項變因**，如同在 MLR 中提到的階層性一樣。
- **這個原則挺小眾的，參考就好。**
- 可以理解成解釋變數 $X_1$ 對 $Y$ 的解釋力除了 $X_1$ 自己本身，還有其交互項。
- **極端情況下，如 $X_1$ 的 p-value $\approx1$，且 $X_1$ 交互項的 p-value $\approx0$，則可以考慮直接拿掉 $X_1$，僅留下交互項。**

### 9.5 【材料原文】交互作用的三種型態 ★★

**核心口訣（材料原文）**
> - **指標變數的係數所代表的是「不同解釋變數間的截距差」。**
> - **交互項的係數所代表的是「不同解釋變數間的斜率差」。**

| 交互型態 | 主要由哪個方法檢定 | 說明 | 例子 |
|---|---|---|---|
| **類別 vs. 類別** | **ANOVA 主要在檢定的** | $X_1$ 因子的效果會因 $X_2$ 因子的效果而改變，不同類別的組合可能會產生不一樣的效果。**若無交互效果，則兩變因 $X_1,X_2$ 具相加性。** | $X_1=$ 教材（實體、數位）、$X_2=$ 年級（高、低）：數位教材在高年級比低年級更有效。 |
| **類別 vs. 連續** | **ANCOVA 主要在檢定的** | 不同組別對連續變數 $X$ 的影響強度（斜率）可能不同。**若斜率同質，則交互效果僅影響「截距項」；若斜率異質，則交互效果還會影響「斜率」。** | 飲食方式 × 每週運動時數 → 減重公斤數。類別因子 $D$：飲食法（0＝正常，1＝低醣）；連續共變數 $X$：每週運動時數；反應 $Y$：8 週後減重公斤數。若沒有交互作用（斜率同質），兩種飲食的「運動 → 減重」關係是平行線，差別只在截距（整體平均差）。**若有交互作用，代表運動每多 1 小時帶來的平均減重在兩種飲食下不同**——例如低醣組的線更陡，表示運動越多，低醣的優勢越明顯。 |
| **連續 vs. 連續** | （迴歸） | $X_1$ 因子的效果會受 $X_2$ 因子的效果而改變。 | 運動時間對健康分數的提升幅度，會隨睡眠時數而增減。 |

**三條操作守則**
- 交乘項一樣可以做變數轉換。
- **交乘項若顯著，要考慮階層性並保留。**
- **交乘項若不顯著，則可以拿掉，整體模型會更簡單。**

### 9.6 【材料原文】交互作用與共線性：VIF 的原理 ★

**基礎概念**
- 用來檢驗模型是否存在共線性問題的指數。
- 一般來說若 $\mathrm{VIF}>10$，就代表模型存在顯著共線性問題。
- **對於少部分監管比較嚴格的產業（例如電力、通訊、金融），$\mathrm{VIF}>5$，就代表模型存在顯著共線性問題。**
- 想解決的問題：某個解釋變數 $X_i$ 和**其他解釋變數**高度相關時，$\hat\beta_i$ 的不確定性會被「**放大**」。
- $\mathrm{VIF}$ 就是在量化「放大了幾倍」——相對於 $X_i$ 與其他變數完全不相關時的理想狀況。
- 在「連續變數 vs. 類別變數」的組合下：$\beta_1$（連續變數本身）、$\beta_2$（連續變數 $\times$ 0）、$\beta_3$（連續變數 $\times$ 1）。**上述三個係數間必然存在共線性，高或低的問題而已。**

**$\mathrm{VIF}$ 的運行方式（三步驟）★**
1. 將想檢驗的解釋變數 $X_i$ 拿來替換被解釋變數 $Y$。例如：$X_1 \sim X_2,X_3,\dots,X_n$
2. 計算得到 $R^2_i$。**如果解釋變數 $X_i$ 跟其他解釋變數幾乎不存在共線性問題，其 $R_i^2 \approx 0$。**
3. 將 $R_i^2$ 套用至下列公式：

$$\mathrm{VIF}(\hat\beta_i)=\frac{1}{1-R_i^2}$$
$$\mathrm{Var}(\hat\beta_i)= \frac{\sigma^2}{\mathrm{SST}_{X_i}(1-R_i^2)}\quad\Rightarrow\quad\text{放大因子}=\frac{1}{1-R_i^2}=\mathrm{VIF}(\hat\beta_i)$$
$$\mathrm{Tolerance}(\hat\beta_i)=\frac{1}{\mathrm{VIF}}=1-R_i^2\quad(\text{越小越糟糕})$$

**可行的補救策略**
- **收集更多「彼此較不相關」的資料**：讓解釋變數的變動更獨立，降低一起同升同降的比例。
- **把高度相關的變數「合併」成較穩定的指標**：在有足夠理論支持下，可以將具高度相關性的解釋變數「打包」起來，進行有意義的「轉換」，形成新的指標。
- **移除其中一個高度相關的自變數。**

**R Code**
```r
library(car)
```
```r
vif(lm5.3i)
```
```r
vif(lm5.3)
```
- 會發現沒有考慮交乘項時，原本的模型是沒有共線性問題的。
- **但沒有交乘項的模型在解釋上卻會有缺陷，因此 $\mathrm{VIF}$ 僅是告知此模型的解釋變數間具有高度線性相關的問題，但不代表此模型就不能使用，不應據此就推翻該模型。**

**重點提醒！★★**
> - $\mathrm{VIF}$ 僅是提醒模型中的解釋變數存在高度線性相關的問題，**並非等價於模型不可使用**。
> - 模型的首要目標是在避免過度擬合的情況下，盡量提升對被解釋變數的解釋力，**而共線性是否會造成嚴重影響，則需要根據領域知識進行判斷，並小心解釋**。

### 9.7 【材料原文】Regression with several groups — 零售店銷售範例

**Store Sales Estimation**
- 被解釋變數：Sales in dollars per square foot（單位面積營業額）
- 連續解釋變數：
  - median household income in surrounding community（該店周遭社區的家戶收入中位數 → 可了解居民型態）
  - size of the local population（當地有多少居民會往來）
- 類別解釋變數：market (urban, suburban, rural)

```r
ss <- read.table("retail_sales.txt", header=T, sep="\t")

summary(ss)
```

```r
cor(ss[,1:3])
```
> 兩兩變數間的關聯性其實不高。

```r
ss$code <- as.integer(factor(ss$Market))

pairs(ss[,1:3], col=ss[,5]+1, pch=ss[,5]+1,
	main="Rural:Red, Suburban:Green, Urban:Blue")
```
（紅色 = Rural、綠色 = Suburban、藍色 = Urban）

```r
levels(factor(ss[,4]))
```

```r
attach(ss)
ss.lm <- lm(Sales ~ Income * Market + Population)
summary(ss.lm)
```
> 全部都顯著。

**模型解釋（材料原文）**
- Suburban 的截距項比 Rural 高 $525.7$。p-value $=0.006952$，表示此差距是顯著的。
- Suburban 的 Income 斜率比 Rural 的低 $0.007823$。看的是表中的交乘項 `Income:MarketSuburban`。p-value $=0.005518$，表示此差距是顯著的。
- Urban 的截距項比 Rural 高 $522.4$。p-value $=0.002797$，表示此差距是顯著的。
- Urban 的 Income 斜率比 Rural 的低 $0.005849$。看的是表中的交乘項 `Income:MarketUrban`。p-value $=0.026564$，表示此差距是顯著的。

**三個區域的子模型**
- Rural：$\text{Estimated Sales}=-300.4+0.0086\times \text{Income}+0.1766\times \text{Population(K)}$
- Suburban：$\text{Estimated Sales}=225.3+0.0008\times \text{Income}+0.1766\times \text{Population(K)}$
- Urban：$\text{Estimated Sales}=222.0+0.0028\times \text{Income}+0.1766\times \text{Population(K)}$

### 9.8 【材料原文】Model building guidelines — Best practice ★★

**Best practice（現行較好的分析做法）**
- 盡可能蒐集「認為」對被解釋變數有解釋力的（變數）。**判斷一個模型時不能僅用單一指標來看。**
- **考慮交乘項。**
- **挑選適當的類別作為基準（baseline）。**
- **需將以類別區分後的迴歸式列出來。**
- **注意解釋不同指標變數所造成的「截距差」及「斜率差」。**
- **檢查各組的變異數是否同質（繪圖）。**
- **圖表應分色或分符號標示子群。**

**Some remarks on ANCOVA**
- 在 R 中基準組的判定通常是以字母先後順序來判斷。可用 `xx <- relevel(as.factor(brand), ref="123")` 來進行指定。
- **類別變數的效果會使子迴歸式的「截距項」不同。**
- **類別變數與連續變數的交互效果會使子迴歸式的「斜率項」不同。**
- **想要校正所有偏誤是不可能的，可以接受就好。**
- **不同類別下同變數的斜率不要混為一談。**
- **任何模型都記得要檢驗 3 + 1 假設。**

> 【評註】「3 + 1 假設」= 線性／等變異／獨立（3 個結構假設）+ 常態（1 個推論假設）。
> 呼應 0916 的說法：「OLS 本身並不需要常態假設」，所以常態被單獨列為「+1」。

### 【評註】這回答什麼行銷/商業問題

- **ANCOVA**：A/B test 的正確做法。單純比兩組轉換率會被「兩組本來就不一樣」污染；把前測、客群特徵當共變數校正後再比，才是「調整後平均」。
- **交互項 = 分眾行銷的統計語言**：`cost:cityTP` 顯著，代表「同樣多花 1 元廣告，台北的營收回報跟台中不同」——這就是預算要不要按城市差異化配置的直接證據。
- **reference level 選擇**：報表要給主管看時，基準組選錯會讓所有品牌看起來都「沒差異」。材料的三條係數正負規則是實用的自檢法。
- **零售店範例**：Rural / Suburban / Urban 的截距差 + 斜率差，正好對應「開店選址 × 客群收入」的雙因子決策。

---

## 10. 變異數分析（ANOVA）（變異數分析 + 1014 + 1021）★★

> 這是任務要求的第 6 項。三個頁面內容高度重疊：`變異數分析` 與 `1014` 的前 970 行完全相同（同一份理論筆記），
> `1021` 是 RBD 與 Two-way 的重講 + 實作。本節以理論頁為骨幹，R code 與範例整併自 1014 / 1021。

### 10.1 【材料原文】ANOVA 概論

**目的**：用於比較兩組或以上樣本的平均數是否相同的統計檢定方法。
- 從實驗設計（experimental design）的角度來看，ANOVA 雖名為「分解變異」，但在應用上，是用以處理**母體平均數是否相等**的多組比較問題。
- **比較兩組樣本時，ANOVA 會退化成獨立 t 檢定。**

**多個獨立母體期望值之檢定**
- 費雪（Ronald Fisher）在 1925 年出版《Statistical Methods for Research Workers》，系統性提出檢定 $k$ 個獨立母體期望值是否相等的方法：

$$\begin{aligned}&\mathrm{H}_0:\ \mu_1=\mu_2=\cdots=\mu_k \\&\mathrm{H}_1:\ \mu_1,\mu_2,\ldots,\mu_k\ \text{不完全相等}\end{aligned}$$

- **若不採用一次性比較，而將 $k$ 組均值拆成多次的兩兩比較會有以下問題：**
  1. $k$ 大時，兩兩比較次數增多，流程龐雜且累積誤差。
  2. **多次檢定會導致整體型一錯誤率上升（experimentwise error rate, EER），不同於每次比較的個別錯誤率（per-comparison error rate, PCER）。**

### 10.2 【材料原文】實驗設計（DOE）概論

- 費雪 1935 年在《The Design of Experiments》中，發展出 ANOVA 的實驗設計觀點，**核心精神是「控制與隨機化」**，以建立因果推論的可信度。
- **實驗設計（Design of Experiments, DOE）**：主要目的在於，如何有系統地設計出一系列的實驗，以期在統計上，釐清「自變數（independent variable）或稱因子（factor）」是否對實驗中的「依變數（dependent variable）或稱反應變數（response variable）」存在影響效果。即：**研究自變數與依變數之間的因果關係**。

**重要名詞**

| 名詞 | 定義 |
|---|---|
| **實驗單位（experimental unit）** | 被分派處理（treatment）的最小觀測單位 |
| **反應變數（response variable / dependent variable）** | 實驗中，研究者感興趣的結果變數 |
| **因子（factor）** | 能影響反應變數實驗結果的控制變數，在 ANOVA 的模型架構下，是一種「**類別型態**」自變數（categorical independent variable） |
| **水準（level）** | 由於因子是「類別型態」自變數，因子內的「每一類別稱為一個水準」，例如因子「血型」的水準 A、B、O、AB |
| **處理（treatment）** | 在**單因子（one-way）**下，「處理」即該因子的水準；在**多因子（multi-factor）**下，處理＝不同因子之間各個水準所產生的組合 |

- **實驗設計最大的挑戰，在於隔離或控制干擾變數（nuisance variable / nuisance factor）對實驗結果的影響**，通常有以下兩種方式來處理：
  - **隨機化（randomization）**：應對**未知且不可控制**的干擾。
  - **區集化（blocking）**：對**已知且可控制**的干擾進行分組控制。

**實驗設計的 3 個基本原則 ★**

| 原則 | 內容 |
|---|---|
| **重複（replication）** | 同一處理的重複實驗，在統計上可降低極端觀察值發生的機率，避免錯誤結論。不可控的干擾變數效應，也可以在重複實驗的過程中被平均掉（averaging out）。 |
| **隨機化（randomization）** | 每個實驗單位在實驗中接受何種「處理」，應採取隨機指派。若有受試順序，也應隨機決定。如此可避免干擾變數在實驗的過程中，對反應變數產生「系統性」的影響。**滿足隨機化原則的實驗設計，在數學模型上，才可假設干擾變數造成的誤差是相互獨立的。** |
| **區集化（blocking）** | 我們將「可控的」干擾因子透過區集化的實驗設計方法控制住，干擾因子的每個水準可設定為一個區集（block）。**在同一個區集內的干擾因子將會有同質性，使得我們回頭在處理之間比較時，得以移除此一干擾因子產生的效應。** |

**核心等價關係**

$$\left\{\begin{aligned}&\mathrm{H}_0:\ \text{因子不影響實驗反應變數} \\&\mathrm{H}_1:\ \text{因子會影響實驗反應變數}\end{aligned}\right. \Longleftrightarrow \left\{\begin{aligned}&\mathrm{H}_0:\ \mu_1=\mu_2=\cdots=\mu_k \\&\mathrm{H}_1:\ \mu_1,\mu_2,\ldots,\mu_k\ \text{不完全相等}\end{aligned}\right.$$

**行銷範例（材料原文）**
- 反應變數：飲料銷售量
- 實驗單位：全台灣選取 $n$ 個銷售據點

$$\begin{array}{r|l|l|l}
\text{因子} & \text{口味} & \text{品牌} & \text{包裝} \\
\hline
 & \text{蘋果} & \text{統一} & \text{紙盒} \\
\text{水準} & \text{柳橙} & \text{味全} & \text{鋁罐} \\
 & \text{芒果} & \text{光泉} & \text{鋁箔包}
\end{array}$$

- 此實驗有 3 個因子，故可稱為三因子變異數分析（three-way ANOVA），共有 $3 \times 3\times 3=27$ 種不同組合的處理，例如：「統一鋁箔包柳橙汁」就是其一。
- 當我們只考慮「口味」一個因子時，即成為單因子變異數分析，有 $k=3$ 個水準（處理），可視為有 3 個獨立母體。
- 若三種口味（3 個獨立母體）飲料的母體平均銷售量相同，即表示「口味這個因子不會影響飲料銷量」，反之就代表「口味這個因子確實會影響飲料銷售量」。

**研究兩個因子或多個因子時**
- 我們採用「**要因設計（factorial designs）**」方法，也就是每一個因子的不同水準之間的全部組合（處理），我們都在實驗中操作它們，並在每一個處理中重複實驗。
- 如此一來，**不但可以檢驗各因子的主要效果（main effect），也能檢驗各因子之間的交互作用效果（interaction effect）。**

### 10.3 【材料原文】One-way ANOVA CRD（完全隨機化設計）

**完全隨機化設計（Completely Randomized Design, CRD）**：一因子實驗設計中，隨機分配 $n$ 個實驗單位到 $k$ 個不同的處理，各處理的樣本數記為 $n_1,n_2,\dots,n_k$，我們有 $n=\sum_{i=1}^kn_i$。

**模型**
$$Y_{ij} = \mu + \alpha_i + \varepsilon_{ij}=\mu_{ij}+\varepsilon_{ij},\qquad i=1,\dots,k,\ j=1,\dots,n_i$$
- $Y_{ij}$ 表第 $i$ 個處理中第 $j$ 個樣本的反應變數觀察值
- $\mu$ 為 $k$ 個獨立處理的混合總平均
- $\mu_i$ 為第 $i$ 個處理的母體平均數
- $\alpha_i=\mu_i-\mu$ 稱為第 $i$ 個處理的**處理效應（treatment effect）**
- $\varepsilon_{ij}$ 稱為個別**誤差效應（error effect）**

**模型假設（四項）★**
$$\varepsilon_{ij}\ \overset{\text{iid}}{\sim}\ \mathcal{N}(0,\ \sigma^2)$$

1. **零均值定理（mean zero）**：$\mathrm{E}(\varepsilon_{ij})=0$。個別誤差效應正負相消，使得其平均為 0。進一步推得 $\mathrm{E}(Y_{ij})=\mu_i$。
2. **同質變異數假設（homoscedasticity）**：$\mathrm{VAR}(\varepsilon_{ij})=\sigma^2$，即 $\sigma_1^2=\sigma_2^2=\dots=\sigma_k^2=\sigma^2$。代表 $k$ 個處理內部之變異數皆相等。
3. **獨立性假設（independence）**：$\varepsilon_{ij}$ 相互獨立。指在不同處理間相互獨立（這使得 $Y_{ij}$ 亦互相獨立，此即 $k$ 個處理間相互獨立的假設），也要求在第 $i$ 個母體內部獨立。
4. **常態性假設（normality）**：$\varepsilon_{i1},\dots,\varepsilon_{in}\overset{\text{iid}}{\sim} \mathcal{N}(0,\sigma^2)\Longrightarrow Y_{i1},\dots,Y_{in_i}\overset{\text{iid}}{\sim} \mathcal{N}(\mu_i,\sigma^2)$

**固定效果 vs 隨機效果**
- 模型中 $n_1=n_2=\dots=n_k$ 時，我們應設定 $\sum_{i=1}^k\alpha_i=0$，也就是所有的處理效應會完全正負相抵消，故 $\mu=\frac{\sum_{i=1}^k\mu_i}{k}$。
- $\varepsilon_{ij}$ 為隨機變數，$Y_{ij}$ 亦為隨機變數，而 $\mu,\alpha_i,\mu_i$ 均為母體參數（常數）——這樣的模型設定方式稱為**固定效果模式（fixed effect model）**。
- 另一種設定：視 $\mu_i$ 為與 $\varepsilon_{ij}$ 獨立之隨機變數，進一步假設 $\mu_i \overset{\text{iid}}{\sim} \mathcal{N}(\mu,\sigma^2)$——稱為**隨機效果模式（random effect model）**。此模型進一步假設每一個因子實際有無窮多種可能水準，實驗中所取的 $k$ 個水準期望值由該常態分配抽出。

**點估計量**
| 效應 | 估計量 |
|---|---|
| 處理平均 | $\hat{\mu_i}=\bar{Y}_{i\cdot} \longrightarrow \mu_i$ |
| 總平均 | $\hat{\mu}=\bar{Y}_{\cdot\cdot} \longrightarrow \mu$ |
| 處理效應 | $\hat{\alpha_i}=\bar{Y}_{i\cdot}-\bar{Y}_{\cdot\cdot} \longrightarrow \alpha_i=\mu_i-\mu$ |
| 誤差效應 | $e_{ij}=Y_{ij}-\bar{Y}_{i\cdot} \longrightarrow \varepsilon_{ij}=Y_{ij}-\mu_i$ |

**三種平方和 ★**

$$\mathrm{SSTO}=\sum_{i=1}^k\sum_{j=1}^{n_i}\left(Y_{ij}-\bar Y_{\cdot\cdot}\right)^2 \quad\text{（總平方和 total sum of squares）}$$
$$\mathrm{SSTR}=\sum_{i=1}^k n_i\left(\bar Y_{i\cdot}-\bar Y_{\cdot\cdot}\right)^2 \quad\text{（處理平方和 / 組間平方和 SSB）}$$
$$\mathrm{SSE}=\sum_{i=1}^k\sum_{j=1}^{n_i}\left(Y_{ij}-\bar Y_{i\cdot}\right)^2 \quad\text{（誤差平方和 / 組內平方和 SSW）}$$

$$\mathrm{SSTO}=\mathrm{SSTR}+\mathrm{SSE}$$

- 總平方和即為「總變異平方和」的概念，把全體的每一個樣本 $Y_{ij}$ 都減去總樣本平均，算出他們的變異，再將這些變異平方做總和。
- 處理平方和反應所有的樣本當中，**因為處理的不同**，所造成的變異總和。
- 誤差平方和反應所有的樣本當中，**因為個體的差異**，所造成的變異總和，非關處理的部分。
- **當 $\mathrm{SSTR}$ 相對 $\mathrm{SSE}$ 較大時，表示處理效應顯著。**
- **當 $\mathrm{SSE}$ 相對 $\mathrm{SSTR}$ 較大時，表示大部分的變異來自個體誤差，此時處理效應不顯著。**

**平均平方**
$$\mathrm{MSTR}=\frac{\mathrm{SSTR}}{k-1},\qquad \mathrm{MSE}=\frac{\mathrm{SSE}}{n-k},\qquad \text{F-statistic}=\frac{\mathrm{MSTR}}{\mathrm{MSE}}$$

**抽樣分配**
1. $\dfrac{\mathrm{SSTR}}{\sigma^2}=\dfrac{(k-1)\mathrm{MSTR}}{\sigma^2}\overset{H_0}{\sim} \chi^2(k-1)$ — **只有在 $H_0$ 為真之下才服從**
2. $\dfrac{\mathrm{SSE}}{\sigma^2}=\dfrac{(n-k)\mathrm{MSE}}{\sigma^2}\sim \chi^2(n-k)$ — **在任何狀況下均服從**
3. $\mathrm{F}=\dfrac{\mathrm{MSTR}}{\mathrm{MSE}}\overset{H_0}{\sim} \mathcal{F}(k-1,n-k)$

**檢定步驟（六步）★**
1. 假說：$H_0$：因子不影響反應變數／處理效應不存在（$\alpha_1=\dots=\alpha_k=0$）／$\mu_1=\dots=\mu_k$；$H_1$：反之
2. 顯著水準：$\alpha$
3. 檢定統計量：$\mathrm{F}=\frac{\mathrm{MSTR}}{\mathrm{MSE}}\overset{H_0}{\sim}\mathcal{F}(k-1,n-k)$
4. 拒絕域：$\mathrm{RR}=\{F\ge\mathcal{F}_{\alpha}(k-1,n-k)\}$（**右尾檢定**）
5. 計算檢定統計量之樣本觀察值 $\mathrm{F}_o$
6. 決策法則：若 $\mathrm{F}_o \in \mathrm{RR}$ 則拒絕 $H_0$；否則不拒絕

**ANOVA table（one-way ANOVA CRD）**
$$\begin{array}{|c|c|c|c|c|}
\hline
\text{變異來源} & \text{SS} & \text{df} & \text{MS} & F \\
\hline
\text{處理} & \mathrm{SSTR} & k-1 & \mathrm{MSTR}=\dfrac{\mathrm{SSTR}}{k-1} & \dfrac{\mathrm{MSTR}}{\mathrm{MSE}} \\
\hline
\text{誤差} & \mathrm{SSE} & n-k & \mathrm{MSE}=\dfrac{\mathrm{SSE}}{n-k} & {} \\
\hline
\text{總和} & \mathrm{SSTO} & n-1 & {} & {} \\
\hline
\end{array}$$

### 10.4 【材料原文】One-way ANOVA RBD（隨機區集化設計）

**設計**
- 考慮因子有 $k$ 個不同的處理（treatment）
- 考慮另一影響實驗反應變數的可能因素，稱之為**區集（block）**，並設有 $b$ 個不同的設定
- **每一個處理當中，都分成這 $b$ 個區集來實驗，每一個區集在處理內部「都只實驗一次」。**
- 共實驗 $n=k \times b$ 次，這 $n$ 個實驗單位，採隨機的方式分配到各個處理和區集。

**模型**
$$Y_{ij} = \mu + \alpha_i + \beta_j + \varepsilon_{ij},\quad i=1,\dots,k,\ j=1,\dots,b$$
- $\alpha_i$：第 $i$ 個處理的**處理效應**
- $\beta_j$：第 $j$ 個區集的**區集效應（block effect）**

**模型假設**：與 CRD 相同四項（零均值／同質變異／獨立／常態），$\varepsilon_{ij}\overset{\text{iid}}{\sim}\mathcal{N}(0,\sigma^2)$

**模型其餘解釋 ★★（很重要！）**
- RBD 實驗設計中，每一個處理被區分為 $b$ 個區集，也就是每一個處理取了 $b$ 個樣本，如此可視為 $n_1=n_2=\dots=n_k=b$。
- $\sum_{i=1}^k\alpha_i=0$：在任意「區集」內部，「處理效應」會完全正負相抵銷。
- $\sum_{j=1}^b\beta_j=0$：在任意「處理」內部，「區集效應」會完全正負相抵消。
- 定義 $\mu_{i\cdot}=\mu+\alpha_i$ 為不同處理的母體平均數；$\mu_{\cdot j}=\mu+\beta_j$ 為不同區集的母體平均數。
- **很重要！！！**
  - **One-way ANOVA RBD 可視為雙因子變異數分析（two-way ANOVA）「不重複實驗」的特例。也就是將區集進一步視為第二個因子！**
  - 獨立性假設指的是「誤差效應 $\varepsilon_{ij}$ 之間相互獨立」，但在 RBD 中，因為有區集效應 $\beta_j$ 的存在，因此我們可以把 one-way ANOVA RBD 視為「**$k$ 個相依母體期望值 $\mu_{i\cdot}$ 是否相等**」之假說檢定。

**點估計量**
| 效應 | 估計量 |
|---|---|
| 處理平均 | $\hat{\mu}_{i\cdot}=\bar{Y}_{i\cdot}$ |
| 區集平均 | $\hat{\mu}_{\cdot j}=\bar{Y}_{\cdot j}$ |
| 總平均 | $\hat{\mu}=\bar{Y}_{\cdot\cdot}$ |
| 處理效應 | $\hat{\alpha_i}=\bar{Y}_{i\cdot}-\bar{Y}_{\cdot\cdot}$ |
| 區集效應 | $\hat{\beta_j}=\bar{Y}_{\cdot j}-\bar{Y}_{\cdot\cdot}$ |
| 誤差效應 | $e_{ij}=Y_{ij}-\bar{Y}_{i\cdot}-\bar{Y}_{\cdot j}+\bar{Y}_{\cdot\cdot}$ |

**四種平方和**
$$\mathrm{SSTO}= \sum_{i=1}^{k}\sum_{j=1}^{b}\left(Y_{ij}-\bar Y_{\cdot\cdot}\right)^{2}$$
$$\mathrm{SSTR}= \sum_{i=1}^{k}\sum_{j=1}^{b}\hat{\alpha}_{i}^{2}= \sum_{i=1}^{k}\sum_{j=1}^{b}\left(\bar Y_{i\cdot}-\bar Y_{\cdot\cdot}\right)^{2}$$
$$\mathrm{SSB}= \sum_{i=1}^{k}\sum_{j=1}^{b}\hat{\beta}_{j}^{2}= \sum_{i=1}^{k}\sum_{j=1}^{b}\left(\bar Y_{\cdot j}-\bar Y_{\cdot\cdot}\right)^{2}$$
$$\mathrm{SSE}= \sum_{i=1}^{k}\sum_{j=1}^{b} e_{ij}^{2}= \sum_{i=1}^{k}\sum_{j=1}^{b}\left(Y_{ij}-\bar Y_{i\cdot}-\bar Y_{\cdot j}+\bar Y_{\cdot\cdot}\right)^{2}$$

$$\mathrm{SSTO}=\mathrm{SSTR}+\mathrm{SSB}+\mathrm{SSE}$$

**判讀規則**
- 當 $\mathrm{SSTR}$ 相對 $\mathrm{SSE}$ 較大時，表示**處理效應顯著**。
- 當 $\mathrm{SSB}$ 相對 $\mathrm{SSE}$ 較大時，表示**區集效應顯著**。
- 當 $\mathrm{SSE}$ 相對 $\mathrm{SSTR}$ 或 $\mathrm{SSB}$ 較大時，表示大部分的變異來自個體誤差，此時處理效應或區集效應不顯著。

**平均平方與檢定統計量**
$$\mathrm{MSTR}=\frac{\mathrm{SSTR}}{k-1},\quad \mathrm{MSB}=\frac{\mathrm{SSB}}{b-1},\quad \mathrm{MSE}=\frac{\mathrm{SSE}}{(k-1)(b-1)}$$
$$\text{F}_1=\frac{\mathrm{MSTR}}{\mathrm{MSE}}\overset{H_0}{\sim}\mathcal{F}(k-1,(k-1)(b-1)),\qquad \text{F}_2=\frac{\mathrm{MSB}}{\mathrm{MSE}}\overset{H_0}{\sim}\mathcal{F}(b-1,(k-1)(b-1))$$

**ANOVA table（one-way ANOVA RBD）**
$$\begin{array}{|c|c|c|c|c|}
\hline
\text{變異來源} & \text{SS} & \text{df} & \text{MS} & F \\
\hline
\text{處理} & \mathrm{SSTR} & k-1 & \dfrac{\mathrm{SSTR}}{k-1} & \text{F}_1=\dfrac{\mathrm{MSTR}}{\mathrm{MSE}} \\
\hline
\text{區集} & \mathrm{SSB} & b-1 & \dfrac{\mathrm{SSB}}{b-1} & \text{F}_2=\dfrac{\mathrm{MSB}}{\mathrm{MSE}} \\
\hline
\text{誤差} & \mathrm{SSE} & (k-1)(b-1) & \dfrac{\mathrm{SSE}}{(k-1)(b-1)} & {} \\
\hline
\text{總和} & \mathrm{SSTO} & n-1 & {} & {} \\
\hline
\end{array}$$

**檢定步驟**：分「檢定處理效應」（用 $F_1$，$H_0:\mu_{1\cdot}=\dots=\mu_{k\cdot}$）與「檢定區集效應」（用 $F_2$，$H_0:\mu_{\cdot 1}=\dots=\mu_{\cdot b}$）兩套，各自六步。

**檢定注意事項 ★**
> 在整個模型和檢定過程中，可以發現，「**處理和區集完全對稱**」，也就是我們可以很自由地把處理和區集的設定互相對調。
> 例如：我們可以設口味為因子，品牌為區集；也可以反過來設品牌為因子，口味為區集。

### 10.5 【材料原文】One-way ANOVA LSD（拉丁方格設計，可略）

**設計**
- 考慮因子有 $p$ 個不同的處理
- 考慮另外兩個影響反應變數的可能因素：列區集（$p$ 個水準）、行區集（$p$ 個水準）
- **只進行 $p^2$ 次實驗**，再以拉丁方格的方式，均衡地配置「處理、列區集與行區集」的實驗組合。

**模型**
$$Y_{ijk}=\mu+\alpha_i+\beta_j+\gamma_k+\varepsilon_{ijk},\quad i,j,k=1,\dots,p$$
- $\beta_j$：列區集效應（row block effect）；$\gamma_k$：行區集效應（column block effect）

**模型其餘解釋**
- 若把列區集與行區集進一步視為第二個與第三個因子，則 one-way ANOVA LSD 可以視為**三因子變異數分析（three-way ANOVA）的特例**。
- 因子有 $p$ 個處理，列/行區集也各有 $p$ 個水準，如果每一種組合都要實驗一輪，則至少需要 $p^3$ 次實驗。**而 LSD 就是試圖以 $n=p^2$ 次實驗完成統計檢驗，故可節省實驗操作與蒐集資料的成本。**
- **缺點在於無法研究因子與干擾變數（區集）之間的交互作用**，當然實驗次數減少，也會使得樣本數減少從而降低檢定力。
- 配置範例（類似「數獨」）：

$$\begin{array}{|c|c|c|c|c|}\hline\text{區集} & \text{I} & \text{II} & \text{III} & \text{IV} \\\hline1 & A & B & C & D \\\hline2 & B & C & D & A \\\hline3 & C & D & A & B \\\hline4 & D & A & B & C \\\hline\end{array}$$

- 橫向來看，列區集的每一水準均可對應到因子 $A,B,C,D$ 4 種處理；縱向來看亦然。
- **事實上，LSD 的處理配置，在滿足前述橫向列區集與縱向行區集的基本配置要件下，同時也要求滿足隨機配置。**

**五種平方和**
$$\mathrm{SSTO}=\sum\sum\sum\bigl(Y_{ijk}-\bar Y_{\cdot\cdot\cdot}\bigr)^2=\sum\sum\sum Y_{ijk}^{2}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n}$$
$$\mathrm{SSTR}=\sum_{i=1}^{p}\frac{Y_{i\cdot\cdot}^{2}}{p}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n},\quad \mathrm{SSR}=\sum_{j=1}^{p}\frac{Y_{\cdot j \cdot}^{2}}{p}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n},\quad \mathrm{SSC}=\sum_{k=1}^{p}\frac{Y_{\cdot\cdot k}^{2}}{p}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n}$$
$$\mathrm{SSE}=\mathrm{SSTO}-\mathrm{SSTR}-\mathrm{SSR}-\mathrm{SSC},\qquad \mathrm{SSTO}=\mathrm{SSTR}+\mathrm{SSR}+\mathrm{SSC}+\mathrm{SSE}$$
（注意，總樣本數 $n=p^2$）

**one-way ANOVA LSD table**
$$\begin{array}{|c|c|c|c|c|}\hline\text{變異來源} & \text{SS} & \text{df} & \text{MS} & F \\\hline\text{處理} & \mathrm{SSTR} & p-1 & \dfrac{\mathrm{SSTR}}{p-1} & \dfrac{\mathrm{MSTR}}{\mathrm{MSE}} \\\hline\text{列區集} & \mathrm{SSR} & p-1 & \dfrac{\mathrm{SSR}}{p-1} & \dfrac{\mathrm{MSR}}{\mathrm{MSE}} \\\hline\text{行區集} & \mathrm{SSC} & p-1 & \dfrac{\mathrm{SSC}}{p-1} & \dfrac{\mathrm{MSC}}{\mathrm{MSE}} \\\hline\text{誤差} & \mathrm{SSE} & (p-1)(p-2) & \dfrac{\mathrm{SSE}}{(p-1)(p-2)} & {} \\\hline\text{總和} & \mathrm{SSTO} & p^{2}-1 & {} & {} \\\hline\end{array}$$

### 10.6 【材料原文】Two-way ANOVA（雙因子變異數分析）★★

**因子設計**：當我們考慮兩個因子以上的實驗設計時，因子設計（factorial design）是最有效率的實驗設計方式。$A$ 因子有 $a$ 個水準，$B$ 因子有 $b$ 個水準，**兩因子之間所有的 $a \times b$ 個「組合」都需要進行實驗與研究**，故我們有 $a \times b$ 個處理。

**模型**
$$Y_{ijk}=\mu+\alpha_i+\beta_j+(\alpha\beta)_{ij}+\varepsilon_{ijk},\quad i=1,\dots,a,\ j=1,\dots,b,\ k=1,\dots,r$$
- $\alpha_i$：$A$ 因子第 $i$ 個水準的 $A$ 因子效應
- $\beta_j$：$B$ 因子第 $j$ 個水準的 $B$ 因子效應
- $(\alpha\beta)_{ij}$：**交互作用效應**
- $\alpha_i+\beta_j+(\alpha\beta)_{ij}$ 合併稱為**處理效應**
- $\mu_{ij}$ 表 $A$ 因子第 $i$ 個水準與 $B$ 因子第 $j$ 個水準所組合的處理平均
- **總樣本數 $n=abr$**

**模型假設**：四項（零均值／同質變異／獨立／常態），$\varepsilon_{ijk}\overset{\text{iid}}{\sim}\mathcal{N}(0,\sigma^2)$

**模型其餘解釋**
- **在二因子變異數分析中，處理與水準已非等義名詞**，$A$ 因子第 $i$ 個水準與 $B$ 因子第 $j$ 個水準的組合，稱之為一種處理。
- 限制式：
  - $\sum_{i=1}^a\alpha_i=0$：在 $A$ 因子內部，水準效應會完全正負相抵消
  - $\sum_{j=1}^b\beta_j=0$：在 $B$ 因子內部，水準效應會完全正負相抵消
  - $\sum_{j=1}^b(\alpha\beta)_{ij}=0$、$\sum_{i=1}^a(\alpha\beta)_{ij}=0$
- 定義：$\mu_{i\cdot}=\mu+\alpha_i$、$\mu_{\cdot j}=\mu+\beta_j$、$\mu_{ij}=\mu+\alpha_i+\beta_j+(\alpha\beta)_{ij}$

**點估計量**
| 效應 | 估計量 |
|---|---|
| $A$ 因子水準平均 | $\hat{\mu}_{i\cdot}=\bar{Y}_{i\cdot\cdot}$ |
| $B$ 因子水準平均 | $\hat{\mu}_{\cdot j}=\bar{Y}_{\cdot j\cdot}$ |
| 處理平均 | $\hat{\mu}_{ij}=\bar{Y}_{ij\cdot}$ |
| 總平均 | $\hat{\mu}=\bar{Y}_{\cdot\cdot\cdot}$ |
| $A$ 因子效應 | $\hat{\alpha_i}=\bar{Y}_{i\cdot\cdot}-\bar{Y}_{\cdot\cdot\cdot}$ |
| $B$ 因子效應 | $\hat{\beta_j}=\bar{Y}_{\cdot j\cdot}-\bar{Y}_{\cdot\cdot\cdot}$ |
| **交互作用效應** | $\widehat{(\alpha\beta)_{ij}}=\bar{Y}_{ij\cdot}-\bar{Y}_{i\cdot\cdot}-\bar{Y}_{\cdot j\cdot}+\bar{Y}_{\cdot\cdot\cdot}$ |
| 誤差效應 | $e_{ijk}=Y_{ijk}-\bar{Y}_{ij\cdot}$ |

**五種平方和**
$$\mathrm{SSTO}=\sum_{i=1}^{a}\sum_{j=1}^{b}\sum_{k=1}^{r}\left(Y_{ijk}-\bar Y_{\cdot\cdot\cdot}\right)^{2}=\sum\sum\sum Y_{ijk}^{2}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n}$$
$$\mathrm{SSA}=\sum_{i=1}^{a}\frac{Y_{i\cdot\cdot}^{2}}{br}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n},\qquad \mathrm{SSB}=\sum_{j=1}^{b}\frac{Y_{\cdot j \cdot}^{2}}{ar}-\frac{Y_{\cdot\cdot\cdot}^{2}}{n}$$
$$\mathrm{SSAB}\ (\mathrm{SSI})=\sum_{i=1}^{a}\sum_{j=1}^{b}\sum_{k=1}^{r}\left(\bar Y_{ij\cdot}-\bar Y_{i\cdot\cdot}-\bar Y_{\cdot j \cdot}+\bar Y_{\cdot\cdot\cdot}\right)^{2}$$
$$\mathrm{SSE}=\sum_{i=1}^{a}\sum_{j=1}^{b}\sum_{k=1}^{r}\left(Y_{ijk}-\bar Y_{ij\cdot}\right)^{2}$$
$$\mathrm{SSTO}=\mathrm{SSA}+\mathrm{SSB}+\mathrm{SSAB}+\mathrm{SSE}$$

**平均平方**
$$\mathrm{MSA}=\frac{\mathrm{SSA}}{a-1},\quad \mathrm{MSB}=\frac{\mathrm{SSB}}{b-1},\quad \mathrm{MSAB}=\frac{\mathrm{SSAB}}{(a-1)(b-1)},\quad \mathrm{MSE}=\frac{\mathrm{SSE}}{ab(r-1)}$$

**三個 F 統計量**
$$\mathrm{F}_1=\frac{\mathrm{MSA}}{\mathrm{MSE}}\overset{H_0}{\sim}\mathcal{F}(a-1,\,ab(r-1))\qquad\text{（A 因子主效應）}$$
$$\mathrm{F}_2=\frac{\mathrm{MSB}}{\mathrm{MSE}}\overset{H_0}{\sim}\mathcal{F}(b-1,\,ab(r-1))\qquad\text{（B 因子主效應）}$$
$$\mathrm{F}_3=\frac{\mathrm{MSAB}}{\mathrm{MSE}}\overset{H_0}{\sim}\mathcal{F}((a-1)(b-1),\,ab(r-1))\qquad\text{（交互作用）}$$

**檢定注意事項 ★★（最重要的三條）**
1. **檢定 $A$ 因子效應、$B$ 因子效應與交互作用效應是三個不同的檢定，三者沒有必然關聯。**
2. **$A$ 因子和 $B$ 因子完全對稱**，可以自由對調，必然會得到等價的檢定結論。
3. **Two-way ANOVA 模型進行統計分析時，都應先檢定交互作用效應是否顯著。**
   - **若存在顯著交互作用效應時，會使得「主效應」的內涵變得複雜，此時不能單單比較 $\bar{Y}_{i\cdot\cdot}$ 之間的 $A$ 因子效應，或 $\bar{Y}_{\cdot j\cdot}$ 之間的 $B$ 因子效應。**
   - **此時應分析處理平均 $\bar{Y}_{ij\cdot}$ 之間的處理效應，涵蓋交互作用效應與兩因子主效應的合併效應。**

### 10.7 【材料原文】ANOVA 中的區間估計

**單一信賴區間（one-at-a-time confidence interval）**：單單只求一組 $\mu_i-\mu_j$ 的信賴區間，其中 $i \ne j$。

**(1) $\sigma^2$ 的 $(1-\alpha)100\%$ 信賴區間**
- 點估計量：$\mathrm{MSE} \longrightarrow \sigma^2$
- 樞紐量：$\dfrac{(n-k)\mathrm{MSE}}{\sigma^2}\sim \chi^2(n-k)$

$$\left[\ \frac{(n-k)\mathrm{MSE}}{\chi^2_{\frac{\alpha}{2}}(n-k)},\ \frac{(n-k)\mathrm{MSE}}{\chi^2_{1-\frac{\alpha}{2}}(n-k)}\ \right]$$

**(2) $\mu_i$ 的 $(1-\alpha)100\%$ 單一信賴區間**
- 點估計量：$\bar Y_{i\cdot} \longrightarrow \mu_i$
- 樞紐量：$\dfrac{\bar Y_{i\cdot}-\mu_i}{\sqrt{\mathrm{MSE}/n_i}}\sim t(n-k)$

$$\left[\ \bar Y_{i\cdot}\pm t_{\frac{\alpha}2}(n-k)\sqrt{\frac{\mathrm{MSE}}{n_i}}\ \right]$$

**(3) $\mu_i-\mu_j$ 的 $(1-\alpha)100\%$ 單一信賴區間（同質變異假設）**
- 樞紐量：$\dfrac{(\bar Y_{i\cdot}-\bar Y_{j\cdot})-(\mu_i-\mu_j)}{\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}}\sim t(n-k)$

$$\left[\ \bar Y_{i\cdot}-\bar Y_{j\cdot}\ \pm\ t_{\frac\alpha2}(n-k)\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}\ \right]$$

### 10.8 【材料原文】聯立信賴區間與型一錯誤膨脹 ★★

**聯立信賴區間（simultaneous confidence intervals）的意義**
- 同時求出所有兩兩母體期望值比較的 $\mu_i-\mu_j$ 之 $(1-\alpha)100\%$ 聯立信賴區間，一共有 $\binom{k}{2}$ 組。
- **問題**：想在 $(1-\alpha)100\%$ 聯立信心水準之下同時求出所有 $\binom{k}{2}$ 組信賴區間時，**我們不能在各組信賴區間中個別選取 $(1-\alpha)100\%$ 的信心水準**。因此這樣做出的聯立信心水準只有：

$$[(1-\alpha)100\%]^{\binom{k}{2}}<(1-\alpha)100\%$$

- **例如：設 $k=3$ 個母體時，同時要做出 $\binom{3}{2}=3$ 組比較，當個別信賴區間均選取 95% 信心水準時，聯立的整體信心水準只有 $(95\%)^3=85.74\%$。**

**三種聯立信賴區間方法 ★**

| 方法 | 公式 | 說明 |
|---|---|---|
| **邦弗洛尼修正（Bonferroni correction）** | $\bar Y_{i\cdot}-\bar Y_{j\cdot} \pm t_{\frac{\alpha}{2\binom{k}{2}}}(n-k)\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}$ | 在個別的信賴區間中，先選取「較大」的信心水準 $\left(\frac{1-\alpha}{\binom{k}{2}}\right)100\%$。**問題在於當處理個數 $k$ 較大時，所選取的個別信心水準會太大，以致於個別的信賴區間的長度過長，失去了意義。** |
| **薛費法（Scheffé's method）** | $\bar Y_{i\cdot}-\bar Y_{j\cdot} \pm \sqrt{(k-1)F_{\alpha}(k-1,n-k)}\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}$ | **$F_{\alpha}(k-1,n-k)$ 其實是 ANOVA 拒絕域的臨界點！** |
| **杜奇法（Tukey's method）** | $\bar Y_{i\cdot}-\bar Y_{j\cdot} \pm q_{\alpha}(k,n-k)\sqrt{\frac{\mathrm{MSE}}{m}}=\bar Y_{i\cdot}-\bar Y_{j\cdot} \pm \frac{q_{\alpha}(k,n-k)}{\sqrt2}\sqrt{\mathrm{MSE}\left(\frac{1}{m}+\frac{1}{m}\right)}$ | **需設定 $k$ 個母體之樣本數相同**（$n_1=\dots=n_k=m$）。$q_{\alpha}(k,n-k)$ 須查詢司徒頓化全距分配表（studentized range distribution table），或稱 Tukey's q 表。 |

**Tukey-Kramer 程序**
> 統計學家 Kramer 於 1956 年的研究指出，雖然 Tukey 推導此一方法時用到樣本數相同之假設，但是當樣本數不同時，仍採用 Tukey 法，並不會有太大的問題，此種方法在文獻上稱為 Tukey-Kramer 程序。

$$\bar Y_{i\cdot}-\bar Y_{j\cdot} \pm \frac{q_{\alpha}(k,n-k)}{\sqrt2}\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}$$

**Bonferroni 的數值示範（材料原文）**
> 設 $k=3$ 個母體時，在信心水準 $94\%$（$\alpha=0.06$）下，欲求出全部 $\binom{3}{2}=3$ 組比較的信賴區間，我們在個別的信賴區間中，先選取較大的 $\left(\frac{1-0.06}{\binom{3}{2}}\right)100\% =98\%$ 信心水準，此時聯立的整體信心水準為 $(98\%)^3=94.12\% \approx 94\%$。

### 10.9 【材料原文】多重比較（事後檢定）★★

**多重比較的意義**
- 當我們拒絕 $\mathrm{H}_0:\mu_1=\dots=\mu_k$ 時，如果想進一步了解他們之間的**相對大小順序**，我們就有必要把 $k$ 個母體兩兩進行比較，這個過程稱之為多重比較。
- 個別單一檢定的型一錯誤率稱為**單一配對錯誤率**（comparisonwise / pairwise error rate），記為 $\alpha_{pc}$；整體 $\binom{k}{2}$ 次兩兩比較時，**聯立顯著水準**（joint significant level）為：

$$\alpha_{ew}=1-(1-\alpha_{pc})^{\binom{k}{2}} \gg \alpha$$

- **這使得整個多重比較的聯立型一錯誤發生率膨脹。因此我們不適宜直接操作兩獨立母體檢定法來進行多重比較。**
- **「聯立信心水準縮小」與「多重比較聯立型一錯誤率膨脹」為對偶問題。**
- 故一個簡單的多重比較方法是：**先同時求出所有 $\binom{k}{2}$ 組兩兩母體 $\mu_i-\mu_j$ 的信賴區間（用任何一種方法皆可），再以信賴區間法來進行檢定（比較）。**

**決策法則（以 $[\mathrm{L},\mathrm{U}]$ 為 $\mu_i-\mu_j$ 的聯立信賴區間）**
- 若 $0 \in [\mathrm{L},\mathrm{U}]$，則拒絕 $\mathrm{H}_0$，認定 $\mu_i$ 與 $\mu_j$ 有顯著差異。
- 若 $0 \notin [\mathrm{L},\mathrm{U}]$，則不拒絕 $\mathrm{H}_0$，不認為 $\mu_i$ 與 $\mu_j$ 有顯著差異。

> 【評註】**此處材料的兩條決策法則寫反了。** 正確為：區間**不含 0** → 拒絕 $H_0$（有顯著差異）；
> 區間**含 0** → 不拒絕 $H_0$。這一點與 0909「`confint` 範圍不包含 0，就代表這個變數對 $Y$ 的影響大概率是真的」
> 的說法自相矛盾，可確認是筆記的筆誤。**轉 Python 時務必用正確版本。**

**四種事後檢定法 ★**

| 方法 | 臨界值公式 | 判準 | 材料評價 |
|---|---|---|---|
| **費雪最小顯著差異（Fisher's LSD）** | $\mathrm{LSD}=t_{\frac{\alpha}2}(n-k)\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}$ | 若 $\lvert\bar Y_{i\cdot}-\bar Y_{j\cdot}\rvert\ge \mathrm{LSD}$，則拒絕 $H_0:\mu_i=\mu_j$ | **「其實就是直接以單一信賴區間進行兩兩比較，並沒有解決型一誤差率膨脹的問題，可以說是什麼都沒做。」** |
| **邦弗洛尼修正法** | 用 Bonferroni 聯立信賴區間 | 信賴區間法檢定 | 先以 Bonferroni 法求出 $\binom{k}{2}$ 組聯立信賴區間，再一一檢定比較 |
| **薛費法（Scheffé's method）** | 用 Scheffé 聯立信賴區間 | 信賴區間法檢定 | 同上 |
| **杜奇真實顯著性差異（Tukey's HSD）** | $\mathrm{HSD} = \frac{q_{\alpha}(k,n-k)}{\sqrt{2}}\sqrt{\mathrm{MSE}\left(\frac{1}{n_i}+\frac{1}{n_j}\right)}$ | 若 $\lvert\bar Y_{i\cdot}-\bar Y_{j\cdot}\rvert\ge \mathrm{HSD}$，則拒絕 $H_0$ | **等價於先以 Tukey-Kramer 程序求出聯立信賴區間，再以信賴區間法一一檢定比較** |

- LSD 的補充：**LSD 即為 $\mu_i-\mu_j$ 之 $(1-\alpha)100\%$ 信賴區間中的誤差邊際 $\mathrm{E}$**，因此我們也可以運用區間估計與假說檢定的對偶關係。

### 10.10 【材料原文】ANOVA 的模型診斷 ★★

**模型診斷意義（model adequacy checking）**
> ANOVA 模型中，我們加入了幾個重要假設，讓後續的分析得以順利地進行，如果我們面對的真實問題中，與這些前提假設不太符合，則後面硬套 ANOVA 的統計方法，其導出的結論顯然會有大問題。**因此在進行 ANOVA 前，先做模型診斷是相當重要的。**

**同質變異數假設之診斷（homoscedasticity）— 三種檢定**

**(1) 巴特雷檢定（Bartlett test）**
- **假設 $k$ 個獨立母體服從常態分配**
1. $H_0: \sigma_1^2=\sigma_2^2=\dots=\sigma_k^2$；$H_1$：不完全相等
2. 顯著水準：$\alpha$
3. 檢定統計量：
$$\chi^{2}=2.3026\frac{q}{c}\overset{H_0}{\sim} \chi^2(k-1)$$
$$q=(n-k)\log_{10}(\mathrm{MSE})-\sum_{i=1}^{k}(n_i-1)\log_{10}(S_i^{2})$$
$$c=1+\frac{1}{3(k-1)}\left(\sum_{i=1}^{k}\frac{1}{n_i-1}-\frac{1}{n-k}\right)$$
4. 拒絕域：$\mathrm{RR}=\{\chi^{2}\ge\chi_{\alpha}^{2}(k-1)\}$
5. 計算樣本觀察值；6. 決策法則

**(2) 哈特利檢定（Hartley test）**
- **假設 $k$ 個獨立母體服從常態分配，並有相同的樣本數** $n_1=n_2=\dots=n_k=m$
- 檢定統計量：
$$\mathrm{H}=\frac{\max S_i^2}{\min S_i^2}$$
- 拒絕域：$\mathrm{RR}=\{\mathrm{H}\ge \mathrm{H}_{\alpha}(k,m-1)\}$

**(3) 修正雷文檢定（Modified Levene test）★**
- **前述 Bartlett 檢定與 Hartley 檢定，都相當依賴母體常態假設，而修正 Levene 檢定則對於母體偏離常態分配的狀況下，仍有相當好的檢定力。**
- 修正 Levene 檢定透過檢定 $k$ 個獨立母體（處理）**平均絕對離差（mean absolute deviation, MAD）** 是否相等來診斷同質變異數假設。
- 步驟：先算出每一個處理的中位數 $\tilde{Y}_{i\cdot}$，再將所有 $n$ 筆資料均轉換為絕對離差型式：
$$D_{ij}=\bigl|Y_{ij}-\tilde{Y}_{i}\bigr|,\qquad i=1,\dots,k,\ j=1,\dots,n_i$$
- **後續再使用正規的 one-way ANOVA CRD 方法，以 $\mathrm{F}=\frac{\mathrm{MSTR}}{\mathrm{MSE}}$ 檢定統計量檢定 $k$ 個獨立母體（處理）絕對離差的期望值是否相等即可。**

> 【評註】三者的選擇規則可歸納為：**資料接近常態 → Bartlett（各組樣本數可不同）或 Hartley（樣本數須相同、計算最簡單）；
> 資料偏離常態 → Modified Levene（最穩健，也是實務首選）。**

### 【評註】這回答什麼行銷/商業問題

- **One-way ANOVA CRD**：三種包裝／三種價格帶／三個廣告版本，哪一個平均銷量最高？（隨機分派門市）
- **RBD（區集）**：不同門市規模本來就會影響銷量（已知且可控的干擾）→ 把門市規模設為區集，就能把它的變異扣掉再比廣告版本。**這是行銷實驗最容易被忽略、卻最能提升檢定力的一步。**
- **Two-way ANOVA + 交互作用**：折扣幅度 × 通路，折扣在電商比實體更有效嗎？——交互作用顯著就代表要分通路訂折扣策略。
- **多重比較**：ANOVA 只告訴你「至少有一組不一樣」，**主管真正要問的是「哪一個最好」——那要靠 Tukey HSD**。
- **型一錯誤膨脹**：同時比 5 個廣告版本＝10 組兩兩比較，用 95% 逐一比，整體錯誤率會膨脹到接近 40%。這是「A/B/n test 亂比一通」的統計代價。

---

## 11. ANOVA 的迴歸觀點與實作流程（1014 課堂內容）★★

### 11.1 【材料原文】Traditional ANOVA view

- ANOVA 用於比較兩個以上相互獨立母體的平均數。
- **核心是在「樣本變異」裡找線索，檢查各母體平均數是否有差異。**

**單因子 ANOVA**：$\mathrm{SSTO}=\mathrm{SST}+\mathrm{SSE}$，$\mathrm{F}=\frac{\mathrm{MST}}{\mathrm{MSE}}$

$$\begin{array}{l|c|c|c|c}\text{Source of Variation} & \text{DF} & \text{Sum of Squares} & \text{Mean Square} & F\text{-stat}\\\hline\text{Treatments} & k-1 & \mathrm{SST} & \mathrm{MST}=\frac{\mathrm{SST}}{k-1} & \frac{\mathrm{MST}}{\mathrm{MSE}}\\\text{Error} & n-k & \mathrm{SSE} & \mathrm{MSE}=\frac{\mathrm{SSE}}{n-k} & \\\text{Total} & n-1 & \mathrm{SSTO} & & \\\end{array}$$

**雙因子 ANOVA**
- 兩因子 ANOVA 可分「有重複」與「無重複」。
  - **隨機區組設計（RBD）屬於無重複的典型。**
  - 無重複可視為等同於 one-way ANOVA RBD 的特例。
  - 若每次實驗只有 1 次觀測：總樣本 $n=kb$；誤差自由度 $(k-1)(b-1)=n-k-b+1$。
- RBD 的總平方和：$\mathrm{SSTO}=\mathrm{SST}+\mathrm{SSB}+\mathrm{SSE}$

$$\begin{array}{l|c|c|c|c}\text{Source} & \text{DF} & \text{SS} & \text{MS} & F\\ \hline\text{Treatments} & k-1 & \mathrm{SST} & \dfrac{\mathrm{SST}}{k-1} & \dfrac{\mathrm{MST}}{\mathrm{MSE}}\\\text{Blocks} & b-1 & \mathrm{SSB} & \dfrac{\mathrm{SSB}}{b-1} & \dfrac{\mathrm{MSB}}{\mathrm{MSE}}\\\text{Error} & n-k-b+1\ (= (k-1)(b-1)) & \mathrm{SSE} & \dfrac{\mathrm{SSE}}{(k-1)(b-1)} & \\\text{Total} & n-1 & \mathrm{SSTO} & &\end{array}$$

> **注意！傳統 ANOVA 可以判斷「是否有顯著差異」，但差異幅度有多大並無法得知。**

### 11.2 【材料原文】ANOVA – Regression Perspective ★★

- 模型：$Y_{ij}=\mu+\alpha_i+\varepsilon_{ij}$
- **參數不可識別**：$\mu$ 與 $\alpha_i$ 可同加減常數，模型不變，因此需進行限制。
  - 因為可以把一個常數 $c$ 加到 $\mu$，同時從每個 $\alpha_i$ 減掉 $c$，預測不會改變：$(\mu + c) + (\alpha_i - c) \equiv \mu + \alpha_i$
  - 因此若不先定規矩，$\mu$ 和 $\alpha_i$ 沒有唯一答案。

**三種編碼做法 ★**

| 編碼方式 | 限制 | $\mu$ 的意義 | $\alpha_i$ 的意義 |
|---|---|---|---|
| **基準組（reference / treatment coding）** | $\alpha_1=0$ | 第一組的平均 | 第 $i$ 組 − 第 1 組 的差 |
| **零和限制（sum-to-zero）** | $\sum_{i=1}^{I}\alpha_i=0$ | 全部組的整體平均 | 第 $i$ 組 − 整體平均 的偏離（正的代表高於整體、負的代表低於整體） |
| **$\mu=0$ ＋ $I$ 個虛擬變數（no-intercept）** | 不用截距 | — | 直接用 $I$ 個 0/1 變數各自代表「第 $i$ 組的平均」 |

> **重點：選哪個做法都不會改變配適值與殘差，只會改變係數的解讀方式。**

**傳統模型的三項分解**
$$Y_{ij} = \mu+\alpha_i+\varepsilon_{ij}= \hat{\mu}+\hat{\alpha}_i+\hat{\varepsilon}_{ij}= \bar{Y}_{..}+(\bar{Y}_{i.}-\bar{Y}_{..})+(Y_{ij}-\bar{Y}_{i.})$$
- 整體平均：$\bar Y_{..}$
- 組間差異：$\bar Y_{i.}-\bar Y_{..}$
- 組內差異：$Y_{ij}-\bar Y_{i.}$

$$N = \sum_{i=1}^{I} J_i,\qquad \bar{y}_{..} = \frac{1}{N}\sum_{i=1}^{I}\sum_{j=1}^{J_i} Y_{ij},\qquad \bar{y}_{i.} = \frac{1}{J_i}\sum_{j=1}^{J_i} Y_{ij}$$

$$\begin{array}{l|c|l}\text{Source} & \text{DF} & \text{Sum of Squares} \\\hline\text{Treatment / Level} & I-1 & \displaystyle \sum_{i=1}^{I} J_i\left(\bar Y_{i.}-\bar Y_{..}\right)^{2} \\\text{Residual} & N-I & \displaystyle \sum_{i=1}^{I}\sum_{j=1}^{J_i}\left(Y_{ij}-\bar Y_{i.}\right)^{2} \\\text{Total} & N-1 & \displaystyle \sum_{i=1}^{I}\sum_{j=1}^{J_i}\left(Y_{ij}-\bar Y_{..}\right)^{2} \\\end{array}$$

### 11.3 【材料原文】ANOVA Procedure — 圖形檢查的三件事 ★★★

> **在配 ANOVA 之前，先看圖是必要步驟。**

**用什麼圖**
- 通常用「**並排箱型圖**」（side-by-side boxplot）快速比較各組的中位數、散佈與可能的離群值。
- **若每組樣本很少（例如 $< 10$），條狀點圖（strip plot）更能看清每一個觀測點**，避免箱型圖在小樣本下資訊不夠。

**圖上要檢查的三件事（What to look for）**

| # | 檢查項目 | 怎麼看 | 看到問題怎麼辦 |
|---|---|---|---|
| 1 | **等變異（equality of variance）** | 各組箱體的高度（IQR）與鬚長度是否大致相近；點圖看各組點的垂直散開幅度是否相當。**若某些組明顯更「高或鬆散」，代表變異可能不等。** | 後續 F 檢定中等變異假設需要加強檢查：**Levene test**、**Bartlett test** |
| 2 | **是否需要轉換** | — | **① 若分佈右偏很明顯，可考慮對 $Y$ 做對數轉換。**<br>**② 若平均越大變異越大（扇形擴張），可考慮對 $Y$ 做根號轉換。**<br>**③ 做完轉換後，建議再畫一次圖確認偏態與變異是否趨於穩定，再進行 ANOVA。** |
| 3 | **離群值（outliers）** | 箱型圖的「圓點/星號」或 strip plot 上遠離主體的點要特別留意 | **① 需先確認是否為輸入錯誤。**<br>**② 若為真實極端值，需評估其對結果的影響（是否應採用穩健方法或敏感度分析）。** |

> 【評註】**第 2 項是整份材料裡唯一明確區分「何時取 log、何時開根號」的地方**，直接回答任務要求的第 7 項：
> **右偏 → log(Y)；變異隨平均放大（扇形）→ sqrt(Y)。**

**後續流程**
- 模型可以用 R 的 `lm()` 來配適，**但要記得該解釋變數是類別變數，而非連續數值。**
- 一旦模型配適完成並取得各水準的效果估計，下一步就是檢驗該因子各水準之間是否存在差異：
  - **此檢驗以整體 F 檢定為起點。**
  - **若拒絕虛無假設，再進一步比較哪些水準彼此不同。**
- **ANOVA 的 F 檢定前提：隨機變數需服從常態分布，且各母體（各組別）的變異數相等。**
  - **常態性檢查**：針對每個樣本（每一組）繪製直方圖進行圖形化檢查（也可搭配 Q-Q plot 做輔助）。
  - **等變異檢查**：列出並比較各組的樣本標準差或變異數。若彼此相近，即可合理假設母體變異數相等。實務上亦常以 **Levene 或 Bartlett 檢定**作為量化佐證。

### 11.4 【材料原文】範例一：Movie-Goer（單因子 ANOVA）

將學生依年齡分成三組：14～16 歲、17～19 歲、20～23 歲。從每一組隨機抽樣，記錄每位學生去年看過的電影數量。
**這些資料是否足以讓電影公司的行銷經理推論三個年齡族群之間存在差異？**

$$\begin{array}{c|ccc}\text{Age group} & 14\sim16 & 17 \sim 19 & 20\sim23 \\\hline\text{Obs 1} & 10 & 23 & 16 \\\text{Obs 2} & 36 & 3  & 48 \\\text{Obs 3} & 14 & 12 & 50 \\\text{Obs 4} & 48 & 25 & 7  \\\end{array}$$

假說：$\mathrm{H}_0: \mu_{14\sim16}=\mu_{17\sim19}=\mu_{20\sim23}$；$\mathrm{H}_1$: not all means are equal.

$$\begin{array}{l|c|c|c|c}\text{Groups} & \text{Count} & \text{Sum} & \text{Average} & \text{Variance}\\\hline14\text{ to }16 & 73 & 1348 & 18.47 & 157.84\\17\text{ to }19 & 99 & 1978 & 19.98 & 161.84\\20\text{ to }23 & 109 & 2332 & 21.39 & 290.11\\\end{array}$$

$$\begin{array}{l|c|c|c|c|c}\text{Source of Variation} & \text{SS} & \text{df} & \text{MS} & F & \text{p-value}\\\hline\text{Between Groups} & 378.70 & 2 & 189.3503 & 0.8990 & 0.4082\\\text{Within Groups} & 58556.16 & 278 & 210.6337 &  &  \\\text{Total} & 58934.86 & 280 &  &  &  \\\end{array}$$
$$\mathrm{F}_{0.05}(2,278)=3.0282$$

**R Code（逐字抄錄）**
```r
## Read Data
movie <- read.csv("Movie_R.csv")
	head(movie)
	attach(movie)

## Model Building
m1 <- lm(movie ~ group, data=movie)
summary(m1)
anova(m1)
```

```r
## EDA: plots
par(mfrow=c(1,2))
boxplot(movie ~ group, data=movie)
stripchart(movie ~ as.factor(group), data=movie, vertical=TRUE, method="stack",
     ylab="No. of Movies", xlab="Group")
```
- **script plot 橫著看其實就是直方圖。**
- **注意！`as.factor(group)` → 把 ( ) 內的物件視為 factor。**

### 11.5 【材料原文】範例二：Bakery Revenue Analysis（行銷市場區隔）★

**此範例把 ANOVA 用在烘焙門市行銷，特別是市場區隔：**
- 我們想檢視「行政區」是否與「營收」有關，藉此**辨識目標市場**。
- 此處的營收定義為「同一行政區內所有門市的一日總營收」。
- 行政區分成五組：北投（TPE_Beitou）、萬華（TPE_Wanhua）、信義（TPE_Xinyi）、中山（TPE_Zhongshan）、中正（TPE_Zhongzheng）
- **研究目標：檢查行政區是否是好的市場區隔變數。也就是，不同行政區的平均營收是否有差。**

**R Code（逐字抄錄）**
```r
## Read data
bakery <- read.csv("bakery.csv", header=TRUE)
	head(bakery)
summary(bakery)
table(bakery$county_district);	table(bakery$week)
```

```r
par(mfrow=c(1,2))
hist(bakery$revenue);	hist(log(bakery$revenue))
```

```r
par(mfrow=c(1,2))
plot(bakery$revenue ~ factor(bakery$county_district), ylab="", xlab="")
with(bakery, stripchart(bakery$revenue ~ factor(bakery$county_district), 
	vertical=TRUE, method="stack", ylab="", xlab=""))
```

```r
plot(log(bakery$revenue) ~ factor(bakery$county_district), las=2, ylab="", xlab="")
with(bakery, stripchart(log(bakery$revenue) ~ factor(bakery$county_district), 
	las=2, vertical=TRUE, method="stack", ylab="", xlab=""))
```
- `mar=c(8,4,4,2)+0.1` 圖表呈現的版型設定。
- **`las=2` 表示將橫軸座標以直式呈現。**

```r
## Linear Model
bakery$county_district <- relevel(factor(bakery$county_district), ref="TPE_Wanhua")

bakery.lm <- lm(log(revenue) ~ county_district, data=bakery)
summary(bakery.lm)
	anova(bakery.lm)
```

> 【評註】注意這裡 **$Y$ 取了 log**——正是 11.3 第 2 項規則（右偏 → 取對數）的實際套用，
> 因為門市營收典型右偏。這是行銷資料最常見的情境。

### 11.6 【材料原文】多重比較的三種方法（1014 課堂版）★★

**為什麼需要**
- 在前面的分析中，我們已知道基準組與其他各組之間的差異，並做了相對應的 t 檢定。
- **但若想比較不是基準組的那兩組（例如第 3 組與第 5 組），能不能利用摘要報表中的估計值來檢驗？**
  - 例如摘要顯示：第 3 組與第 5 組分別比第 1 組高 1.913 與 2.174。由於兩者彼此很接近，我們想檢驗「第 3 組 vs 第 5 組是否不同？」
- **這就凸顯了多重比較的重要性，常見有三種做法。**

**共同的 t 統計量**
$$t_{ij}=\frac{\hat{\alpha}_i-\hat{\alpha}_j}{\hat{\sigma}\sqrt{\frac{1}{J_i}+\frac{1}{J_j}}},\qquad \hat{\sigma}=\sqrt{\mathrm{MSE}},\qquad \text{df}=n-I$$

假說：$\mathrm{H}_0: \alpha_i-\alpha_j=0$；$\mathrm{H}_1: \alpha_i \ne \alpha_j$

| 方法 | 拒絕域 | 材料評價 |
|---|---|---|
| **Fisher's LSD** | $\lvert t_{ij}\rvert>t_{n-I,\frac{\alpha}2}$ | **本質上等於兩獨立樣本 t 檢定，只適合單一（或極少數）事先規劃的比較。是三者之中最寬鬆的方法。** 也可以等價於「用信賴區間判斷是否含 0」。 |
| **Bonferroni correction** | $\lvert t_{ij}\rvert>t_{n-I,\frac{\alpha}{2k}}$，其中 $k=\binom{I}{2}=\frac{I(I-1)}{2}$ | **是三者之中最嚴謹的方法。** 若只檢定部分配對，$k$ 就改成實際的配對數。 |
| **Tukey's HSD** | $\lvert t_{ij}\rvert>\frac{q_{I,\mathrm{df},\alpha}}{\sqrt{2}}$ | **針對「所有成對比較」且等變異及常態假設合理時最推薦。樣本數不相等時，自動選擇 Tukey–Kramer procedure。是三者中較適中的做法。** |

**Bonferroni 的信賴區間版**
$$\hat{\alpha}_i-\hat{\alpha}_j \pm t_{n-I,\frac{\alpha}{2k}}\hat{\sigma}\sqrt{\frac{1}{J_i}+\frac{1}{J_j}}$$

**Bonferroni 補充（材料原文）**
- **為什麼要做 Bonferroni 修正？** 同時做很多成對檢定會讓「整體型一錯誤率」膨脹。Bonferroni 透過「把 $\alpha$ 平均分給每個檢定」來保證整體誤拒 $\mathrm{H}_0$ 的機率 $\le \alpha$。
- **適用時機**：同時檢定多組成對比較，想嚴格控制「整體型一錯誤」。
- **優點**：簡單穩健、對多種依賴結構都成立（保守上界不需獨立）。
- **缺點**：當 $k$ 大或樣本小會偏保守、檢定力下降。

**Tukey HSD 補充（材料原文）**
- 使用 *studentized range* 分配的上分位數 $q_{I,\mathrm{df},\alpha}$ 來做**所有成對平均的同時檢定**。$I$：組數；$\mathrm{df}$：ANOVA 的誤差自由度；$\alpha$：整體顯著水準。
- **直覺：$\frac{q}{\sqrt{2}}$ 是把多組同時比較的門檻折算到 t 尺度上的「臨界值」。**
- 聯立信賴區間版：
$$(\bar Y_{i.}-\bar Y_{j.}) \pm \frac{q_{I,\mathrm{df},\alpha}}{\sqrt{2}}\hat{\sigma}\sqrt{\tfrac{1}{J_i}+\tfrac{1}{J_j}}\quad(\text{不含 0} \Rightarrow \text{顯著})$$
- 等樣本數（每組 $J_i=n$）的常見門檻：
$$\mathrm{HSD}=q_{I,\mathrm{df},\alpha}\sqrt{\frac{\mathrm{MSE}}{n}},\quad |\bar Y_{i.}-\bar Y_{j.}|>\mathrm{HSD}\ \Rightarrow\ \text{顯著不同}$$
- p-value 可以直接由 studentized range 分配求得：
$$\Pr\left(Q\ge |t_{ij}|\sqrt{2}\right) = 1-\mathrm{PTukey}\left(|t_{ij}|\sqrt{2};\, I,\, \mathrm{df}\right)$$
其中 $\mathrm{PTukey}$ 是 Tukey 分配的 CDF，可直接使用 R 中的 `ptukey()`。
- **`TukeyHSD()` 可一口氣輸出所有成對比較與同時信賴區間。**

**三種方法的數值對照（同一組資料，第 3 組 vs 第 5 組）★**

| 方法 | 檢定統計量 | 臨界值 | p-value | 結論 |
|---|---|---|---|---|
| Fisher's LSD | $t=3.052$ | $t_{n-I,0.975}=1.966$ | 雙尾 $0.00243$ | 顯著 |
| Bonferroni | $t=3.051935$ | $2.823878$ | $0.02437$（未調整 p 乘上 $k$） | **顯著性相較未校正下降** |
| Tukey HSD | $t=3.051935$ | $q/\sqrt2 \approx 2.741205$ | $1-\mathrm{ptukey}(3.052\sqrt2,I,\mathrm{df})\approx 0.0205$ | $3.052>2.741$，拒絕 $H_0$ |

**R Code（逐字抄錄）**

確認每一個 county 究竟有多少資料：
```r
	# table(bakery$county_district)

(n <- nrow(bakery))
(I <- length(table(bakery$county_district)))
(n1 <- table(bakery$county_district)[[1]])
(n2 <- table(bakery$county_district)[[2]])
(n3 <- table(bakery$county_district)[[3]])
(n4 <- table(bakery$county_district)[[4]])
(n5 <- table(bakery$county_district)[[5]])
```

Fisher's LSD：
```r
#### Compare Group 3 and 5
## Multiple Comparison - Fisher's LSD ##

(sigma_hat <- summary(bakery.lm)$sigma)	# sigma hat = residual standard error
(t35 <- (2.17434-1.91337)/(sigma_hat*sqrt(1/n3+1/n5)))
(tc.lsd <- qt(0.975, n-I))				# critival value
(1-pt(t35, n))*2 
```

Bonferroni correction：
```r
## Multiple Comparison - Bonferroni correction ##

(t35 <- (2.17434-1.91337)/(sigma_hat*sqrt(1/n3+1/n5)))
(tc.bon <- qt(1-0.05/(2*(I*(I-1)/2)), n-I))	# critival value
(1-pt(t35, n-I))*2*(I*(I-1)/2)	
	# now Groups 3 & 5 are less significantly different
```

Tukey's HSD：
```r
## Multiple Comparison - Tukey's HSD ##

(t35 <- (2.17434-1.91337)/(sigma_hat*sqrt(1/n3+1/n5)))
(tc.hsd <- qtukey(0.95, I, n-I)/sqrt(2))		# critival value
1-ptukey(t35*sqrt(2), I, n-I)

hsd <- TukeyHSD(aov(lm(log(revenue) ~ county_district, data=bakery)))
par(fig=c(0.15,1,0,1)); plot(hsd, las=1, cex.axis=0.7)
hsd # 呈現兩兩比較表
```
- **信賴區間若有包含到 $0$，代表兩者差距其實不顯著，等價於不拒絕虛無。**

Diagnostics：
```r
## Diagnostics ##
par(mfrow=c(1,2))
qqnorm(residuals(bakery.lm));	qqline(residuals(bakery.lm))
plot(fitted(bakery.lm), residuals(bakery.lm), xlab="Fitted", ylab="Residuals");
abline(h=0, lty=2, col='grey')
```

### 11.7 【材料原文】範例三：Diet Restriction & Longevity（事先規劃的對比）★

本研究將雌性小鼠隨機分派到六種飲食處理之一，探討「飲食限制」與壽命（月）的關係：
- **NP**：非純化飼料，全程標準飲食
- **N/N85**（control）：斷奶前正常飲食，之後 85 kcal/週
- **N/R50**：斷奶前正常飲食，之後 50 kcal/週
- **R/R50**：全程 50 kcal/週
- **N/R50 lopro**：斷奶前正常飲食，之後 50 kcal，但蛋白質逐步降低
- **N/R40**：斷奶前正常飲食，之後 40 kcal/週

**五個「事先規劃」的研究問題 → 對應假設 ★**

| # | 研究問題 | $H_0$ | $H_1$ | 尾數 |
|---|---|---|---|---|
| 1 | 85 → 50 是否延長壽命？（post-weaning 限制的效果） | $\mu_{\mathrm{N/N85}}=\mu_{\mathrm{N/R50}}$ | $\mu_{\mathrm{N/R50}}>\mu_{\mathrm{N/N85}}$ | **單尾**，因問題問 "increase" |
| 2 | 斷奶前的限制是否有影響？（pre-weaning effect） | $\mu_{\mathrm{R/R50}}=\mu_{\mathrm{N/R50}}$ | $\mu_{\mathrm{R/R50}}\ne \mu_{\mathrm{N/R50}}$ | 雙尾 |
| 3 | 50 → 40 是否「更進一步」延長壽命？ | $\mu_{\mathrm{N/R50}}=\mu_{\mathrm{N/R40}}$ | $\mu_{\mathrm{N/R40}}>\mu_{\mathrm{N/R50}}$ | **單尾** |
| 4 | 同熱量下「降蛋白」是否改變壽命？ | $\mu_{\mathrm{N/R50}}=\mu_{\mathrm{N/R50\;lopro}}$ | $\ne$ | 雙尾 |
| 5 | 實驗室小鼠（NP）與對照組（N/N85）壽命是否相同？ | $\mu_{\mathrm{NP}}=\mu_{\mathrm{N/N85}}$ | $\ne$ | 雙尾 |

> 【評註】這個範例示範了一個重要技巧：**用 `relevel()` 依序把每個「想比較的基準」設為 reference，
> 就能直接從 `summary()` 的係數表與 `confint()` 讀出對應的對比檢定**——不需要另外算。
> 這是把「事先規劃的對比（planned contrasts）」用 `lm` 做出來的實務做法。

**R Code（逐字抄錄）**
```r
install.packages("Sleuth2")
```

```r
library(Sleuth2)
summary(case0501)
attach(case0501)
```

```r
## Data structuring
Dn <- summary(Diet)
Dm <- tapply(Lifetime, Diet, mean)
Ds <- tapply(Lifetime, Diet, sd)
Dx <- tapply(Lifetime, Diet, max)
Dy <- tapply(Lifetime, Diet, min)
	# tapply(Lifetime, Diet, quantile)
Dsum <- cbind(Dn, Dm, Ds, Dx, Dy)
colnames(Dsum) <- c("n", "Mean", "SD", "Max", "Min")
Dsum
```

```r
## EDA
par(mfrow=c(1,2))
boxplot(Lifetime ~ Diet)
stripchart(Lifetime ~ Diet, vertical=T, method="stack")
```

```r
## First model
c501.lm <- lm(Lifetime ~ Diet)
summary(c501.lm)
confint(c501.lm)		# (e)
```

```r
Diet <- relevel(Diet, ref="N/N85")
c501.lm2 <- lm(Lifetime~Diet)
summary(c501.lm2)
confint(c501.lm2)		# (a)
```

```r
Diet <- relevel(Diet, ref="N/R50")
c501.lm3 <- lm(Lifetime~Diet)
summary(c501.lm3)
confint(c501.lm3)		# (b), (c), (d), (a)
```

```r
( c501hsd <- TukeyHSD(aov(Lifetime~Diet)) )
par(fig=c(0.1,1,0,1))
plot(c501hsd, las=1)
```

```r
## Residual plot
plot(fitted(c501.lm), residuals(c501.lm))
abline(h=0, lty=2, col='grey')
```

### 11.8 【材料原文】實驗設計的系統性流程（7 步）★★

**Systematic Approach to Experimental Planning and Implementation**
1. 明確陳述目標（State objective）
2. 選定被解釋變數（Choose response）
3. 選擇因子與水準（Choose factors and levels）
4. 選擇實驗計畫（Choose an experimental plan）
5. 執行實驗（Perform the experiment）
6. 分析資料（Analyze the data）
7. 下結論並提出建議（Draw conclusions and make recommendations）

**逐步展開（材料原文）**
1. **目標**：用一句可驗證的話。例：「比較三種配方的平均拉伸強度是否不同」。
2. **反應變數**：連續／計數／比例。**量測方法、單位、量測次序、誰量、盲測與否。**
3. **因子**：
   - 可控：例如，配方、溫度。
   - 不可控但可量：例如，環溫。
   - 干擾因子：例如，人員、機台、天。
   - 水準範圍：基於可行性與安全。**先做試驗找「合理區間」。**
4. **實驗設計**：決定重複數、隨機化、是否分區、樣本量。
   - CRD（完全隨機）／RBD（隨機區集）／Factorial（因子設計）
5. **執行**：照隨機表、記錄偏差、處理遺失值（**事前規則**）。
6. **分析**：先畫圖（箱型/點圖），檢查常態與等變異 → 做 ANOVA/對比 → 多重比較 → **效果量**
7. **建議**

---

## 12. RBD 與 Factorial Design 實作（1021）★★

### 12.1 【材料原文】範例：Blood Sugar-Lowering Drugs（RBD）

- 許多北美民眾血糖偏高，嚴重可能導致糖尿病。對於血糖非常高（>126 mg/dL）者，醫師會開立藥物降血糖。
- 某藥廠開發了 **4 種降血糖藥**，設計實驗以判斷藥效是否有差異。
- 公司挑選 **25 組（每組 4 人）** 的男性受試者，**各組內依年齡與體重進行匹配**。服藥 2 個月後，記錄血糖下降量。
- 假說：$\mathrm{H}_0:\mu_1=\mu_2=\mu_3=\mu_4$；$\mathrm{H}_1$：至少兩個平均不同
- **四種藥視為「四個處理」。依年齡與體重配對的一組人視為一個「區集」。**
- **這樣的設計可排除由年齡/體重組合帶來的變異，因此更容易偵測到真正在於藥物差異的效果。**

**★★ 關鍵對照：忽略區集 vs 納入區集**

不納入區集（誤把 RBD 當 CRD 分析）：
$$\begin{array}{c|c|c|c|c|c|c}\textbf{Source of Variation} & \textbf{SS} & \textbf{df} & \textbf{MS} & \textbf{F} & \textbf{P-value} & \textbf{F crit} \\\hline\text{Between Groups} & 319.103 & 3 & 106.368 & 1.434 & 0.238 & 2.699 \\\text{Within Groups} & 7119.80 & 96 & 74.165 & - & - & - \\\text{Total} & 7438.91 & 99 & - & - & - & -\end{array}$$

納入區集（正確的 RBD / two-way）：
$$\begin{array}{c|c|c|c|c|c|c}\textbf{Source of Variation} & \textbf{SS} & \textbf{df} & \textbf{MS} & \textbf{F} & \textbf{P-value} & \textbf{F crit} \\\hline\text{Rows（區集）} & 5365.12 & 24 & 223.547 & 9.1728 & 1.0848\times 10^{-13} & 1.6695 \\\text{Columns（藥物）} & 319.103 & 3 & 106.368 & 4.3646 & 0.0070 & 2.7318 \\\text{Error} & 1754.68 & 72 & 24.3706 & - & - & - \\\text{Total} & 7438.91 & 99 & - & - & - & -\end{array}$$

> 【評註】**這是整份材料裡最有說服力的一組數字。** 同一批資料：
> - 不分區集：藥物 $F=1.434$、$p=0.238$ → **不顯著**，結論「四種藥沒差」。
> - 分區集後：藥物 $F=4.3646$、$p=0.0070$ → **顯著**，結論「四種藥有差」。
>
> 關鍵在於 SSE 從 7119.80 降到 1754.68（把 5365.12 的區集變異抽走了），MSE 從 74.165 降到 24.3706。
> **處理平方和 319.103 完全沒變，變的只是分母。** 這就是「區集化能提升檢定力」的完整數值證明，
> 也是行銷實驗設計最該學的一課：**把已知的干擾（門市規模、季節、客群）設為區集，不要讓它留在誤差裡。**

$$\begin{array}{c|c|c|c|c}\textbf{Groups} & \textbf{Count} & \textbf{Sum} & \textbf{Average} & \textbf{Variance} \\\hline\text{Drug 1} & 25 & 543.85 & 21.75 & 45.23 \\\text{Drug 2} & 25 & 557.49 & 22.30 & 101.53 \\\text{Drug 3} & 25 & 470.21 & 18.81 & 100.01 \\\text{Drug 4} & 25 & 592.83 & 23.71 & 49.89\end{array}$$

**R Code（逐字抄錄）**
```r
## Read Data
drug <- read.csv("Drug_R.csv")
	# summary(drug)
	# head(drug)

## Model Building
drug.lm1 <- lm(Reduction ~ Drug, data=drug)
summary(drug.lm1)
anova(drug.lm1)
```

```r
drug.lm2 <- lm(Reduction ~ Drug + factor(Group), data=drug)
summary(drug.lm2)
anova(drug.lm2)
```

```r
boxplot(Reduction ~ Drug, data=drug)

boxplot(Reduction ~ factor(Group), data=drug)
```

```r
par(mfrow=c(1,2))
qqnorm(residuals(drug.lm2));	qqline(residuals(drug.lm2))
plot(fitted(drug.lm2), residuals(drug.lm2), pch=1)
abline(h=0, lty=2, col='grey')
```

> 【評註】`lm(Reduction ~ Drug + factor(Group))` 這一行就是 RBD 的全部——**把區集用 `factor()` 包起來加進模型即可。**

### 12.2 【材料原文】Factorial Design 基本概念

- 因子設計：有若干個因子、各有若干水準。**全因子設計是把各因子水準的所有組合都至少做一次。**
- 二因子 ANOVA（有重複數 $n_{ij}$）：因子 $\alpha$ 有 $I$ 個水準，因子 $\beta$ 有 $J$ 個水準。$n_{ij}$ 表示在 $\alpha=i$、$\beta=j$ 這個「儲存格（cell）」中的觀測數，$Y_{ijk}$ 是第 $k$ 筆觀測。
- **完整設計**：所有 cell 都有資料（$n_{ij}\ge 1$）。**若所有 cell 的樣本數都相同（$n_{ij}=n$），稱為平衡設計。**
- 模型：$Y_{ijk}=\mu+\alpha_i+\beta_j+(\alpha\beta)_{ij}+\varepsilon_{ijk}$

**交互作用的定義與解讀（材料原文）**
> - **交互作用：平均反應中那一部分，不是單純由 $\alpha$ 與 $\beta$ 的加總效果解釋的差異。**
> - **若交互作用顯著，主效果的解讀必須「條件化」：$\alpha$ 的比較需在特定 $\beta$ 水準下討論（反之亦然）。**

### 12.3 【材料原文】無重複 vs 有重複的關鍵差異 ★★

**Wastewater data（每個 cell 只有 1 筆）**
- one $Y$ per cell。
- **只能先配適只有主效果的模型。**
- **交互作用無法正式檢定，只能透過交互作用圖做視覺檢查。**
- 註：
  - **每格 1 筆 → 交互作用的自由度 = 誤差自由度，所以無法同時估計「交互作用」與「純誤差」。**
  - **若硬要做檢定，等於假設沒有交互作用。**

**若每個 cell 都有相同的重複數 $n>1$，則是正交/平衡設計**
- $>1$ $Y$s per cell。
- 行列 cell 數成比例時，也可能達到正交。
- **有重複數即可直接用模型 $Y_{ijk}=m+a_i+b_j+(ab)_{ij}+e_{ijk}$ 來檢定交互作用。**
- **正交**：
  - **直覺：A、B 兩因子的資訊「零干擾、彼此不搶變異」。**
  - **好處：平方和可加、各來源的 F 檢定不受順序影響，解釋更單純。**

### 12.4 【材料原文】範例：Detergent Effectiveness（有重複的二因子）★

**情境（行銷／消費者測試）**
- 洗衣精廠商常宣稱自家產品的效果。**消費者保護單位決定測試銷量前五名的洗衣精。**
- 各家都聲稱「在各種水溫下都能洗出**最白**的白色」。
- 實驗設計：準備 150 片白布並平均弄髒。對於每一個品牌，清洗 30 片——其中 10 片用冷水、10 片用溫水、10 片用熱水。
- 清洗後，使用雷射儀器量測每片布的「白度分數」。

**額外說明**
- 這是二因子 ANOVA（有重複）：因子 A＝品牌（5 個水準）；因子 B＝水溫（3 個水準：冷/溫/熱）。
- **每個 cell 的重複數 $n=10$ ⟹ 平衡設計，可同時檢定主效果與交互作用。**
- 反應變數：白度分數（越高越白）。
- 後續問題：品牌是否有差異？水溫是否有差異？**品牌×水溫是否有交互作用？**

**ANOVA table（two-factor ANOVA with Replication）**
$$\begin{array}{c|c|c|c|c|c|c}\text{Source of Variation} & \text{SS} & \text{df} & \text{MS} & \text{F} & \text{P-value} & \text{F crit} \\\hline\text{Sample（水溫）} & 5706.84 & 2 & 2853.42 & 17.9133 & 1.259\times 10^{-7} & 3.0632 \\\text{Columns（品牌）} & 4084.09 & 4 & 1021.0233 & 6.4098 & 9.4068\times 10^{-5} & 2.4387 \\\text{Interaction} & 3579.03 & 8 & 447.3783 & 2.8086 & 0.0065 & 2.0076 \\\text{Within} & 21504.20& 135 & 159.2904 & - & - & - \\\text{Total} & 34874.16& 149 & - & - & - & -\end{array}$$

> 【評註】三個檢定都顯著（水溫 $p<10^{-7}$、品牌 $p<10^{-4}$、**交互作用 $p=0.0065$**）。
> 依 10.6 的規則，**交互作用顯著 ⟹ 不能單獨比品牌主效應**，必須說「在冷水下哪個品牌最好、在熱水下哪個品牌最好」。
> 這直接推翻了廠商「在各種水溫下都最白」的宣稱。

**原始資料（逐字保留）**

$$\begin{array}{c|c|c|c}\text{Temperature} & \text{Detergent A} & \text{Detergent B} & \text{Detergent C} \\\hline\text{Cold} &57, 84, 45, 28, 60, 37, 42, 47, 59, 52 &78, 51, 51, 80, 70, 71, 61, 56, 90, 76 &63, 68, 53, 60, 65, 90, 62, 63, 69, 75 \\\text{Warm} &72, 55, 59, 67, 45, 38, 79, 61, 45, 72 &55, 35, 83, 65, 64, 63, 65, 60, 73, 60 &65, 83, 88, 82, 74, 62, 52, 73, 52, 84 \\\text{Hot} &98, 83, 46, 80, 88, 55, 84, 82, 54, 78 &77, 81, 65, 62, 65, 71, 68, 84, 68, 71 &94, 97, 73, 52, 79, 48, 72, 83, 88, 69 \end{array}$$

$$\begin{array}{c|c|c}\text{Temperature} & \text{Detergent D} & \text{Detergent E} \\\hline\text{Cold} &30, 48, 34, 50, 71, 52, 64, 53, 62, 74 &78, 58, 96, 80, 65, 66, 68, 77, 73, 71\\\text{Warm} &62, 76, 74, 64, 64, 69, 99, 75, 85, 76 &84, 98, 79, 76, 91, 69, 82, 68, 62, 73\\\text{Hot} &79, 79, 92, 84, 69, 99, 88, 100, 88, 80 &78, 93, 77, 67, 95, 81, 74, 69, 88, 91\end{array}$$

### 12.5 【材料原文】Factorial Design R Code（逐字抄錄）★

**WITHOUT Replication（Wastewater pH data）**

```r
## Read Data
ph <- read.csv("pH_R.csv") 
ph
```

```r
## Model Building
ph.m1 <- lm(pH ~ factor(Temperature) + Lightwave, data=ph)
summary(ph.m1)
anova(ph.m1)
```

```r
	par(mfrow=c(1,2))
with(ph, interaction.plot(Temperature, Lightwave, pH, legend=T))
with(ph, interaction.plot(Lightwave, Temperature, pH, legend=T))
```
- **`with(ph, …)`**：`ph` 這個資料物件的內文中，執行後面的程式碼（鎖定範圍）。
- **`interaction.plot(x.factor, trace.factor, response, …)`**：
  - 在圖上把 `x.factor` 放橫軸。
  - **不同的 `trace.factor` 水準畫成不同的線/顏色，用來視覺檢查交互作用（線條是否平行）。**
- **`legend = TRUE`**：要求在圖上顯示圖例（各 `Lightwave` 水準對應的線型/顏色）。

**WITH Replication（Detergent data）**

```r
## Read Data
detergent <- read.csv("Detergent_R.csv")
	# head(detergent)
```

```r
# Model Building
dt.lm1 <- lm(Score ~ Detergent + Temperature, data=detergent)
summary(dt.lm1)
anova(dt.lm1)
```

```r
detergent$Temperature <- factor(detergent$Temperature, c("Cold","Warm","Hot"))
	hist(detergent$Score)
```

```r
	# par(mfrow=c(1,2))
with(detergent, interaction.plot(Temperature,Detergent,Score,legend=T))
	# with(detergent, interaction.plot(Detergent,Temperature,Score,legend=F))
```

```r
dt.lm2 <- lm(Score ~ Detergent * Temperature, data=detergent)
summary(dt.lm2)
anova(dt.lm2)
```

```r
anova(dt.lm1, dt.lm2)
```

```r
boxplot(Score ~ Detergent, data=detergent)
```
> 單因子（Detergent）的 box plot → 「品牌主效果」的邊際分布。

```r
boxplot(Score ~ Temperature, data=detergent)
```
> 單因子（Temperature）的 box plot → 「水溫主效果」的邊際分布。

```r
boxplot(Score ~ Detergent + Temperature, data=detergent)
```
> **把 Detergent 及 Temperature 兩因子組合成 cell 來畫 box plot → 主要用來觀察交互作用與各 cell 的分布。**

> 【評註】注意 `factor(detergent$Temperature, c("Cold","Warm","Hot"))` 這一行——**手動指定 level 順序**，
> 因為字母序會變成 Cold / Hot / Warm，圖形與係數解讀都會亂掉。轉 Python 時對應 `pd.Categorical(..., categories=[...], ordered=True)`。

### 【評註】這回答什麼行銷/商業問題

- **RBD 數值對照**：告訴行銷分析師「你的 A/B test 沒跑出顯著，可能不是效果不存在，而是你沒把門市/客群的差異當區集扣掉」。
- **interaction.plot 線條平行與否**：這是**最直觀的分眾判讀工具**——線平行 ⟹ 全客群一致策略；線交叉 ⟹ 必須分眾。
- **Detergent 範例**：品牌 × 水溫 = 產品 × 使用情境。交互作用顯著 ⟹ 廣告不能說「全情境最好」，只能說「在某情境最好」。
- **無重複設計的限制**：每個 cell 只跑一次的行銷實驗（例如每個通路每檔期只做一次）**根本無法檢定交互作用**，只能畫圖目視。這是實驗規劃階段就要決定的事。

---

## 13. 可重用資產（直接寫進新 Skill）

> 本節是【評註】性質的整理，但**每一條規則都可回溯到上文的材料原文**。
> 標註 `[出處]` 方便查核。

### 13.1 檢查清單 A：EDA 標準動作序列（L4 規格）

```
□ 1. 先把問題問清楚：你要回答什麼？需要哪些資料才能回答？先列清單        [1007]
□ 2. 讀檔 read.csv(..., header=TRUE)                                    [EDA Code]
□ 3. 結構檢視三件套：str() / summary() / colSums(is.na())               [0930]
□ 4. 檢查錯誤：缺漏、離群、單位、編碼、時間序                            [1007]
□ 5. 類別變數轉指標變數（dummy / indicator）                             [1007]
□ 6. 單變數分布：hist() + boxplot()（先看目標變數 Y）                    [EDA Code]
□ 7. 位置量數：mean() / median()                                         [EDA Code]
□ 8. 分散量數：sd() var() min() max() range() quantile() summary() length() [EDA Code]
□ 9. 形狀量數：skewness() / kurtosis()（fBasics）                        [EDA Code]
□10. 雙變數：plot() 散佈圖 + abline(lm()) 迴歸線                          [EDA Code]
□11. 整合圖：par(fig=) 疊散佈圖 + 邊際 hist + boxplot                    [EDA Code]
□12. 全變數掃描：pairs() 散佈圖矩陣（+ panel 加迴歸線）                   [EDA Code]
      ※ 類別變數不要拿來畫 scatter plot，沒意義（只會看到格點）
      ※ 這一步算是一種初步的資料篩選過程
□13. 相關矩陣：cor()                                                     [0930]
□14. 分組比較：Trellis plot（lattice: dotplot / xyplot）                 [EDA Code]
□15. 圖和數字提示你可能的錯誤，也提醒你要不要做轉換                       [1007]
      ※ 高度偏態的變數，常先取自然對數再分析
```

### 13.2 檢查清單 B：迴歸診斷順序（L4/L5 規格）★★

```
Step 0  Global F test        模型整體有沒有訊號？                        [0916]
        └ 不顯著 → 回頭檢查資料或重新定義 Y
        └ 顯著 ≠ 模型好用，還要往下走

Step 1  殘差三圖（假設檢查）  必須先做，因為 Step 2 的判準依賴四大假設   [0909/0916]
        ├ Residual plot (fitted vs residual) → 零均值 / 同質變異 / 獨立性
        ├ Histogram of residuals            → 常態性
        └ Q-Q plot + qqline                 → 常態性
        R: par(mfrow=c(1,3)); plot(fitted(m),resid(m)); abline(h=0)
           hist(resid(m),breaks=10); qqnorm(resid(m)); qqline(resid(m))

Step 2  Outliers（Y 方向）    rstandard()，|studentized residual| > 3     [0923]
Step 3  Leverage（X 方向）    hatvalues()，h > 3(k+1)/n（也看 h < 2(k+1)/n）[0923]
Step 4  Cook's distance      cooks.distance()，D≥1 或 0.5≤D<1            [0923]
        ※ 殘差大 ≠ 影響一定大；槓桿高 ≠ 影響一定大
        ※ 殘差大 + 槓桿高 = 最危險，但仍需視庫克距離而定

Step 5  共線性               成對散佈矩陣 / cor() → vif()                [0923/1007]
        ※ VIF > 10 高度共線；嚴管產業（電力/通訊/金融）VIF > 5

Step 6  變數選擇             Testing-based（backward/forward/stepwise）  [0923]
                             → Criterion-based（AIC / Adjusted R²）收尾

Step 7  敏感度分析           移除可疑點重估，看係數/標準誤/R² 是否實質改變 [0923]
        ※ 顯著影響 → 回到成因處理；未顯著影響 → 紀錄即可，通常保留
```

### 13.3 判讀規則表：每張診斷圖看什麼 ★★★

| 圖 | 理想狀況 | 問題訊號 | 對應違反的假設 | 處方 |
|---|---|---|---|---|
| **Residual plot** | 點雲上下對稱、平均近 0 | 整體偏上或偏下 | 零均值 | 模型有系統性偏差 |
| **Residual plot** | 散布寬度從左到右差不多 | **漏斗形**（左窄右寬或反）／**弓形** | 同質變異 | 變數轉換（**對數、平方根**）／WLS／robust SE |
| **Residual plot** | 像隨機雜訊、無固定模式 | **波浪狀**／**週期性** | 獨立性（自我相關） | Durbin-Watson 檢查／Newey-West SE |
| **Histogram of residuals** | 鐘形、對稱、中心在 0 | 偏斜（左/右長尾）／扁平／尖峰 | 常態性 | 轉換（**log、Box-Cox**）／穩健迴歸／非參數 / bootstrap |
| **Q-Q plot** | 點落在 **45 度對角線** | 尾端翹起/下垂（肥尾瘦尾）／整體彎曲（偏態） | 常態性 | 同上 |
| **studentized residual hist** | 集中在 ±3 內 | $\lvert r\rvert>3$（兩尾機率 < 0.002） | — 離群值 | 查四類成因（見 13.4） |
| **Leverage plot** | 多數點在 $2(k+1)/n$ 與 $3(k+1)/n$ 之間 | $h>3(k+1)/n$（或 $h<2(k+1)/n$ 極孤立） | — 高槓桿 | 敏感度分析 |
| **Cook's distance plot** | 全部遠低於 0.5 | $D\ge1$（強警訊）；$0.5\le D<1$（留意） | — 影響點 | 僅作為模型警訊使用！ |
| **VIF 表** | VIF 接近 1 | VIF > 10（寬鬆 5）；Tolerance 越小越糟 | — 共線性 | 見 13.5 |
| **並排箱型圖（ANOVA）** | 各組 IQR 與鬚長相近 | 某組明顯更高/更鬆散 | 等變異 | Levene / Bartlett 檢定佐證 |
| **並排箱型圖（ANOVA）** | 分布對稱 | **右偏明顯 → log(Y)**；**平均越大變異越大（扇形）→ sqrt(Y)** | — | 轉換後再畫一次圖確認 |
| **interaction.plot** | 線條**平行** | 線條**不平行/交叉** | — 交互作用 | 主效果解讀必須條件化 |

### 13.4 決策規則：離群值的四類成因 → 處方 ★

| 成因 | 處方 |
|---|---|
| 資料輸入錯誤（**最常見**） | 更正後重跑分析 |
| 重要變數遺漏 | 找回可能有用的變數納入後重估 |
| 回歸假設失真（異質變異、非常態、交互項未檢驗） | 變數轉換、加入交互或非線性項，再重新評估模型 |
| 族群本質差異（潛在次族群） | 先把疑似離群樣本獨立處理，其餘資料單獨重估，**分開分析** |

### 13.5 決策規則：共線性的處理階梯 ★

```
1. 收集更多彼此相關性較低的資料（最理想，但實務常做不到）
2. 合成變數：把高度相關的指標做成組合指標
   ※ 需要有情境意義，沒有合理解釋時不要硬合
3. 轉換變數：重塑成更細緻的變數（需專業知識輔助）
4. 移除高度重疊的其中一個（最常見、也很實務）
   ※ 保留較有理論意義或較容易量測的那個
5. 多項式/交互項造成的共線性 → 標準化可明顯緩解
   ※ 但對「兩個量測幾乎等價」的相關，標準化沒有用
--------------------------------------------------
不要太執著於模型不能出現共線性，不要太高就好。
VIF 高 ≠ 模型不可使用，需根據領域知識判斷並小心解釋。
```

### 13.6 決策規則：變數轉換 ★★

| 觸發訊號 | 轉換 | 出處 |
|---|---|---|
| $Y$ 右偏很嚴重（EDA hist / 箱型圖） | $\ln(Y)$ | 1007 / 1014 |
| 各組平均越大變異越大（扇形擴張） | $\sqrt{Y}$ | 1014 |
| 殘差圖漏斗形（異質變異） | 對數或平方根轉換 | 0909/0916 |
| 殘差 Histogram / Q-Q 偏斜 | log、Box-Cox | 0909/0916 |
| 散佈圖呈曲線（非線性） | 加 $X^2$；或 $\ln(X)$、$1/X$ | 1007 |
| $X$ 高度偏態 | $\ln(X)$ | 1007 |
| 遞減報酬（廣告費 → 銷售額） | $\ln(X)$ | 0909 |
| 兩個高相關的比率型變數 | 取平均後再取倒數 | 0923 |
| 資料含 0，需取 log 或倒數 | 加 epsilon：`log(x + 1e-3)`、`1/(x + 1e-6)` | 0930 |

**加法順序鐵則（1007）**
```
1. Y 先用原始尺度，除非 EDA 明確建議轉換
2. 檢查四個基本假設（線性/常態/等變異/獨立）
   ├ 都過關 → 直接跳到「簡化模型」
   └ 有違反 → 往下
3. 由簡到繁：
   (a) 先試「類別 × 連續」的交互項（最常見、最容易有意義）
   (b) 再試變數轉換（X², ln(X), 1/X）
   (c) 最後才試「連續 × 連續」的交互項
   ※ 一步一步加，每加一種就重新檢查殘差
4. 簡化：維持階層性（保留交互項就保留主效應）；一次只動少數幾個變數
```

### 13.7 完整流程範本：Full vs Reduced 巢狀 F test ★★

**前置條件檢查**
```
□ 縮減模型必須是完整模型把某些係數設 0 的特例（巢狀關係），否則不能做
□ 兩個模型必須用同一個 Y（同一尺度）與同一筆資料
□ 一定有 SSE_R ≥ SSE_C
```

**公式**
$$\text{Partial F}=\frac{(SSE_R-SSE_C)/(k-r)}{SSE_C/(n-k-1)} \sim F_{k-r,\;n-k-1}$$

**R 範本（順序很重要：reduced 在前）**
```r
m_full <- lm(Y ~ X1 + X2 + X3 + X4, data=dat)
m_red  <- update(m_full, . ~ . - X3 - X4)     # 或直接寫 lm(...)
a <- anova(m_red, m_full)                      # reduced 在前！
a
F_val <- a$F[2]; p_val <- a$`Pr(>F)`[2]
```

**判讀與三角驗證**
| Partial F | 決策 | 應同時看到 |
|---|---|---|
| 顯著 | 保留那批變數（完整模型） | Adjusted $R^2 \uparrow$、$\hat\sigma \downarrow$ |
| 不顯著 | 移除那批變數（縮減模型） | Adjusted $R^2 \downarrow$ 或幾乎不變、$\hat\sigma$ 不降 |

> 三者一致（F 不顯著 + 縮減模型 AdjR² 較高 + $\hat\sigma$ 較低）⟹ 高機率縮減模型較理想。

**陷阱**
- 單一新增變數時 $F=t^2$（與該變數 t 檢定等價）
- 共線性會讓個別 t 不顯著但 Partial F 仍可能顯著 → **先 t 挑候選，再 F 成組確認**
- 「被移除」只能解讀為「**在目前已納入的變數之上，該變數沒有『額外』解釋力**」，不等於它不重要

### 13.8 完整流程範本：ANOVA ★★

```
【設計階段】
□ 1. 明確陳述目標（一句可驗證的話）
□ 2. 選定反應變數（量測方法、單位、次序、誰量、盲測與否）
□ 3. 選擇因子與水準（可控 / 不可控但可量 / 干擾因子；先試驗找合理區間）
□ 4. 選擇實驗計畫：CRD / RBD / Factorial
      ※ 已知且可控的干擾 → blocking
      ※ 未知且不可控的干擾 → randomization
      ※ 三原則：重複 replication / 隨機化 randomization / 區集化 blocking
□ 5. 執行：照隨機表、記錄偏差、事前定好遺失值規則

【分析階段】
□ 6. 先畫圖：side-by-side boxplot（每組 n<10 改用 stripchart）
      ├ 等變異？ 各組 IQR 與鬚長是否相近
      ├ 要轉換？ 右偏 → log(Y)；扇形 → sqrt(Y)；轉換後再畫一次
      └ 離群值？ 先確認是否輸入錯誤
□ 7. 常態性：各組 histogram（+ Q-Q plot 輔助）
□ 8. 等變異量化佐證：Bartlett / Hartley / Modified Levene
      ├ 資料接近常態 → Bartlett（樣本數可不同）/ Hartley（樣本數須相同）
      └ 資料偏離常態 → Modified Levene（最穩健，實務首選）
□ 9. 配適模型 lm()，記得解釋變數是 factor 不是連續數值
□10. 整體 F 檢定（右尾）
      └ 不拒絕 H0 → 停，結論「各組平均無顯著差異」
□11. 拒絕 H0 → 多重比較找出「哪些水準彼此不同」
      ├ 只比 1~2 組事先規劃的 → Fisher's LSD（最寬鬆）
      ├ 嚴格控制整體型一錯誤 → Bonferroni（最嚴謹，k 大時保守）
      └ 所有成對比較、等變異常態合理 → Tukey HSD（最推薦、最適中）
□12. 殘差診斷：qqnorm/qqline + fitted vs residuals
□13. 報告效果量（傳統 ANOVA 只說有無差異，說不出差異幅度）

【two-way 專屬】
□14. 一定先檢定交互作用！
      ├ 顯著 → 主效果解讀必須條件化，改看處理平均 Ybar_ij
      └ 不顯著 → 才可以分別解讀 A、B 主效應
□15. 每個 cell 只有 1 筆 → 交互作用無法檢定，只能用 interaction.plot 目視
```

**R 範本速查**
```r
# one-way CRD
m <- lm(Y ~ factor(G), data=dat);  summary(m);  anova(m)

# one-way RBD（把區集用 factor 加進去）
m <- lm(Y ~ Treat + factor(Block), data=dat);  summary(m);  anova(m)

# two-way 主效果 vs 含交互作用
m1 <- lm(Y ~ A + B, data=dat)
m2 <- lm(Y ~ A * B, data=dat)
anova(m1, m2)                 # 檢定交互作用是否該留

# 交互作用圖
with(dat, interaction.plot(A, B, Y, legend=T))

# 事後檢定
TukeyHSD(aov(lm(Y ~ factor(G), data=dat)))

# 手算三種臨界值
qt(0.975, n-I)                              # Fisher LSD
qt(1-0.05/(2*(I*(I-1)/2)), n-I)             # Bonferroni
qtukey(0.95, I, n-I)/sqrt(2)                # Tukey HSD

# 改 reference level
dat$G <- relevel(factor(dat$G), ref="Baseline")

# 指定 level 順序（避免字母序亂掉）
dat$Temp <- factor(dat$Temp, c("Cold","Warm","Hot"))
```

### 13.9 公式速查卡

**迴歸**
$$R^2=\frac{SSR}{SST}=1-\frac{SSE}{SST}\qquad \bar{R^2}=1-\frac{n-1}{n-k-1}(1-R^2)$$
$$\hat\sigma=\sqrt{\frac{SSE}{n-k-1}}\qquad \hat{\beta}_j^*=\frac{S_{X_j}}{S_Y}\hat{\beta}_j\quad(\text{Beta coefficient})$$
$$F_{\text{global}}=\frac{SSR/k}{SSE/(n-k-1)}=\frac{R^2/k}{(1-R^2)/(n-k-1)}$$
$$F_{\text{partial}}=\frac{(SSE_R-SSE_C)/(k-r)}{SSE_C/(n-k-1)}\qquad t=\frac{\hat\beta_p}{S_{\hat\beta_p}}\sim t_{n-k-1}$$
$$\mathrm{VIF}_i=\frac{1}{1-R_i^2}\qquad \mathrm{Tolerance}_i=1-R_i^2$$
$$\text{CI: } \hat Y(x_0)\pm t\,\hat\sigma\sqrt{\tfrac1n+\tfrac{(x_0-\bar X)^2}{\sum(X_i-\bar X)^2}}\qquad \text{PI: 根號內多一個 } 1$$

**診斷門檻**
$$|\text{studentized residual}|>3\qquad h>\frac{3(k+1)}{n}\ \text{（或}\ h<\frac{2(k+1)}{n}\text{）}\qquad D\ge1\ \text{或}\ 0.5\le D<1$$
$$\mathrm{VIF}>10\ \text{（嚴管產業 }>5\text{）}\qquad \Delta\mathrm{AIC}\le2\text{（難分軒輊）},\ 4\text{–}7\text{（弱優勢）},\ \ge10\text{（明顯）}$$

**ANOVA**
$$\text{CRD: } SSTO=SSTR+SSE,\quad F=\frac{MSTR}{MSE}\sim F(k-1,\,n-k)$$
$$\text{RBD: } SSTO=SSTR+SSB+SSE,\quad F_1=\frac{MSTR}{MSE}\sim F(k-1,(k-1)(b-1))$$
$$\text{Two-way: } SSTO=SSA+SSB+SSAB+SSE,\quad F_3=\frac{MSAB}{MSE}\sim F((a-1)(b-1),\,ab(r-1))$$
$$\text{LSD}=t_{\frac{\alpha}2}(n-k)\sqrt{MSE\left(\tfrac{1}{n_i}+\tfrac{1}{n_j}\right)}\qquad \text{HSD}=\frac{q_{\alpha}(k,n-k)}{\sqrt2}\sqrt{MSE\left(\tfrac{1}{n_i}+\tfrac{1}{n_j}\right)}$$
$$\text{Bonferroni: } t_{\frac{\alpha}{2\binom{k}{2}}}(n-k)\qquad \text{Scheffé: } \sqrt{(k-1)F_{\alpha}(k-1,n-k)}$$
$$\alpha_{ew}=1-(1-\alpha_{pc})^{\binom{k}{2}}\gg\alpha \quad\text{（型一錯誤膨脹）}$$

### 13.10 R → Python 對照表（翻譯用）

| R | Python（pandas / statsmodels / scipy） |
|---|---|
| `read.csv(f, header=TRUE)` | `pd.read_csv(f)` |
| `str(dat)` / `summary(dat)` | `dat.info()` / `dat.describe(include='all')` |
| `colSums(is.na(dat))` | `dat.isna().sum()` |
| `skewness()` / `kurtosis()` (fBasics) | `dat[c].skew()` / `dat[c].kurt()`（注意 kurtosis 定義差異：R fBasics 預設為 excess） |
| `quantile(x, c(.25,.5,.75))` | `x.quantile([.25,.5,.75])` |
| `pairs(df)` | `pd.plotting.scatter_matrix(df)` 或 seaborn `pairplot` |
| `cor(df)` | `df.corr()` |
| `lm(y ~ x1 + x2, data=d)` | `smf.ols('y ~ x1 + x2', data=d).fit()` |
| `summary(m)` | `m.summary()` |
| `confint(m)` | `m.conf_int()` |
| `fitted(m)` / `residuals(m)` | `m.fittedvalues` / `m.resid` |
| `anova(m)` | `sm.stats.anova_lm(m, typ=2)` |
| `anova(m_red, m_full)` | `sm.stats.anova_lm(m_red, m_full)` |
| `update(m, . ~ . - X)` | 重建 formula 字串後重跑 `smf.ols` |
| `rstandard(m)` | `m.get_influence().resid_studentized_internal` |
| `hatvalues(m)` | `m.get_influence().hat_matrix_diag` |
| `cooks.distance(m)` | `m.get_influence().cooks_distance[0]` |
| `vif(m)` (car) | `statsmodels.stats.outliers_influence.variance_inflation_factor` |
| `step(m)` | 無內建；需自寫 AIC 逐步搜尋（`m.aic`） |
| `AIC(m)` / `BIC(m)` | `m.aic` / `m.bic` |
| `qqnorm()` + `qqline()` | `scipy.stats.probplot(resid, plot=ax)` 或 `sm.qqplot(resid, line='45')` |
| `predict(m, newd, interval="confidence")` | `m.get_prediction(newd).conf_int()` |
| `predict(m, newd, interval="prediction")` | `m.get_prediction(newd).conf_int(obs=True)` |
| `relevel(factor(x), ref="A")` | `C(x, Treatment(reference="A"))` 於 formula 中 |
| `factor(x, c("Cold","Warm","Hot"))` | `pd.Categorical(x, categories=[...], ordered=True)` |
| `TukeyHSD(aov(...))` | `statsmodels.stats.multicomp.pairwise_tukeyhsd` |
| `qtukey()` / `ptukey()` | `scipy.stats.studentized_range.ppf` / `.cdf` |
| `bartlett.test()` | `scipy.stats.bartlett` |
| Modified Levene | `scipy.stats.levene(..., center='median')` |
| `interaction.plot(A, B, Y)` | `statsmodels.graphics.factorplots.interaction_plot` |
| `boxplot(Y ~ G)` | `df.boxplot(column='Y', by='G')` 或 seaborn `boxplot` |
| `stripchart(..., method="stack")` | seaborn `stripplot` / `swarmplot` |
| `par(mfrow=c(1,3))` | `fig, axes = plt.subplots(1,3)` |
| `dat[-c(54,117),]` | `dat.drop(dat.index[[53,116]])`（**R 是 1-based，Python 0-based**） |
| `log(x + 1e-3)` | `np.log(x + 1e-3)` |

### 13.11 翻譯時必須修正的材料錯誤（重要）★

| 位置 | 材料原文 | 正確版本 |
|---|---|---|
| EDA Code | `install.packages(“fBasics")` | 全形彎引號，R 會報錯 → `install.packages("fBasics")` |
| EDA Code | `# works with package ??fBasics??` | 編碼損毀，原為彎引號 |
| 0923 Y 對數轉換診斷 | 第一組診斷誤用 `residuals(lm3.2)` | 應為 `residuals(lm3.1)` |
| 0923 Leverage 第三條 | `h>3(k+1)/n ≥ h ≤ 2(k+1)/n` | 排版錯誤，應為 $2(k+1)/n \le h \le 3(k+1)/n$ 才是「暫無明確證據」 |
| 變異數分析 多重比較 | 「若 $0 \in [L,U]$ 則拒絕 $H_0$」 | **寫反了**。正確：$0 \notin [L,U]$ → 拒絕 $H_0$（有顯著差異） |
| 1007 revcost 判讀 | $D_2$ 的 p=0.0699 標為「顯著」 | 與同頁 TOYOTA（p=0.0884 標「不顯著」）不一致。以 $\alpha=0.05$ 為準，0.05<p<0.10 標「邊際顯著」 |
| 0923 遺漏變數範例 | 「$R^2=0.0102$…房價 $Y$ 與房間數 $X_2$ 呈現正向關係」 | 模型寫的是 $E(Y)=\beta_0+\beta_1X_1$（$X_1$=坪數），敘述卻談 $X_2$（房間數）。以敘述邏輯判斷，該 SLR 實際跑的是「房價 ~ 房間數」 |
| 1014 Tukey df | `df = n-I×n-I n-I` | 排版損毀，正確為 $\mathrm{df}=n-I$ |

### 13.12 給行銷分析師的「這回答什麼問題」對照表

| 方法 | 行銷/商業問題 |
|---|---|
| EDA hist + skewness | 客單價／回購間隔是否右偏？要不要取 log 才能建模 |
| EDA boxplot | 誰是離群的大客戶（VIP）／異常訂單 |
| EDA pairs + cor | 哪些行銷變數彼此高度相關（預告共線性） |
| Trellis plot | 通路 × 縣市 × 商品的三維切面比較 |
| SLR 斜率 | 廣告每多花 1 元，銷售額平均增加多少（ROI 直接估計） |
| CI vs PI | CI：這群客人的**平均**回應（預算配置）；PI：**下一個**客人會怎樣（個別化行銷、備貨） |
| MLR 偏效應 | 控制通路/季節/價格後，廣告本身的獨立貢獻（行銷歸因） |
| Beta coefficient | 電視/數位/促銷三管道誰的邊際影響最大（預算重分配） |
| Nested F test | 這整組新變數（如 CRM 行為資料）值不值得繼續蒐集（資料採購決策） |
| Outlier 四類成因 | 異常大單是打錯 key、B2B 次族群、還是真異常？處理方式完全不同 |
| Cook's distance | 刪掉這筆，我的行銷結論會不會翻盤 |
| 敏感度分析 | 給主管的答案：「就算把異常客戶拿掉，結論還是一樣」 |
| VIF / 共線性處理 | 電視與數位同期投放 → 模型說兩個都不顯著，但不能因此砍數位預算 |
| 遺漏變數偏誤 | 只看「發折價券→銷售上升」，沒控制同期廣告，會把廣告效果算到折價券頭上 |
| 外差（Extrapolation） | 歷史預算 100–500 萬的模型，不能拿來回答「花 2000 萬會怎樣」 |
| ANCOVA 調整後平均 | A/B test 的正確做法：把前測/客群特徵當共變數校正後再比 |
| 交互項（類別×連續） | 「同樣多花 1 元廣告，台北的回報跟台中不同」→ 預算要不要按城市差異化 |
| reference level 選擇 | 基準組選錯會讓所有品牌看起來都「沒差異」，報表給主管前要自檢 |
| One-way ANOVA | 三種包裝／價格帶／廣告版本，哪一個平均銷量最高 |
| RBD 區集化 | A/B test 沒跑出顯著，可能是沒把門市規模/客群差異當區集扣掉 |
| Two-way + 交互 | 折扣 × 通路：折扣在電商比實體更有效嗎 → 要不要分通路訂折扣 |
| interaction.plot | 線平行 ⟹ 全客群一致策略；線交叉 ⟹ 必須分眾 |
| Tukey HSD | ANOVA 只說「至少有一組不一樣」，主管要問的是「**哪一個最好**」 |
| 型一錯誤膨脹 | 同時比 5 個廣告版本＝10 組比較，逐一用 95%，整體錯誤率膨脹到近 40% |
| Bakery 範例 | 「行政區」是不是好的市場區隔變數 |
| Detergent 範例 | 交互作用顯著 ⟹ 推翻「在各種水溫下都最白」的廣告宣稱 |

---

## 14. 尚未涵蓋 / 待補

1. **所有 Notion 內嵌截圖**（每頁大量 `![圖片]`）：包含模型 summary 報表、殘差圖範例、Q-Q plot 正常/異常對照、AIC step 逐步輸出、TukeyHSD 圖等。本 digest 已保留其文字說明與數值表，但圖本身未取得。
2. **EDA Files 的附件 `1-02-1_EDA.zip`**：內含 HOMES.csv、coffee_trellis1~3.csv 等實際資料檔，未下載解壓。同理未取得 SLR Files、MLR Files 的附件。
3. **0902 的三張投影片圖**：`Business process`、`Level of Analytics`、`Summary`——0902 頁面文字極少，主要內容在圖裡。
4. **F-Test 在 0909「Model diagnosis」下標註「（略）」**：SLR 的 F 檢定細節材料本身跳過。
5. **ANCOVA 調整後平均的 SE 完整推導**：材料標註「（略）」，只給了矩陣形式 $\sqrt{\mathbf{l}_g(c)^\top \widehat{\mathrm{Var}}(\hat{\boldsymbol{\beta}}) \mathbf{l}_g(c)}$。
6. **平方和之抽樣分配的推導**：材料多處標註「（可略）」，只給結論。
7. **One-way ANOVA LSD（拉丁方格）的檢定步驟與 R 實作**：材料標註「（可略）」，只給模型與 ANOVA table，無 R code。
8. **Criterion-based 只講了 AIC**：BIC、Mallows' $C_p$、交叉驗證在材料中僅被提及名稱（「比較 CV、比較 RMSE」），無展開。
9. **1021 的 Two-way ANOVA 理論段（lines 237–405）**與 `變異數分析` 完全重複，本 digest 未重覆抄錄。
10. **Durbin-Watson、Newey-West、WLS、robust SE、Box-Cox、穩健迴歸、bootstrap**：材料只列為「可能的解決方式」，無公式與實作。
