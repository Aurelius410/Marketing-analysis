---
title: "Lecture 4 Clustering + Lecture 5 Sequence Tagging 完整萃取"
course: "NTU 大數據與商業分析（碩二課程）"
captured_at: 2026-07-26
sources:
  - type: notion
    title: "Lecture 4：Clustering"
    url: https://app.notion.com/p/33c2b4ffdf0b80bd808cc413a349d715
    id: 33c2b4ffdf0b80bd808cc413a349d715
  - type: notion
    title: "Lecture 4 / Part 1.（Clustering 概念與 K-means、評估）"
    url: https://app.notion.com/p/fc606a1d4b6e44e4b15998050e671a22
    id: fc606a1d4b6e44e4b15998050e671a22
  - type: notion
    title: "Lecture 4 / Part 2.（DBSCAN — 密度式分群）"
    url: https://app.notion.com/p/4f18c4508613407ca138a0cb1a23768e
    id: 4f18c4508613407ca138a0cb1a23768e
  - type: notion
    title: "Lecture 4 / Part 3.（階層分群與主題模型）"
    url: https://app.notion.com/p/d3ed79768e034253b6c4de27922d4959
    id: d3ed79768e034253b6c4de27922d4959
  - type: notion
    title: "Lecture 5：Sequence Tagging（施工中）"
    url: https://app.notion.com/p/33c2b4ffdf0b8006ae38c97340bf26bf
    id: 33c2b4ffdf0b8006ae38c97340bf26bf
  - type: local
    path: C:\Users\User\Desktop\大數據\Lecture4_Clustering_完整講義_Notion版.md
    size: 106806 bytes / 2737 lines
  - type: local
    path: C:\Users\User\Desktop\大數據\L4_Clustering_完整前置整理.md
    size: 47423 bytes / 2075 lines
  - type: local
    path: C:\Users\User\Desktop\大數據\Lecture5_SequenceTagging_完整講義_Notion版.md
    size: 24807 bytes / 600 lines
  - type: local
    path: C:\Users\User\Desktop\大數據\L5_Sequence_Tagging_完整前置整理.md
    size: 29018 bytes / 1164 lines
  - type: local_pdf
    path: C:\Users\User\Desktop\大數據\L4.pdf
    note: "80 頁原始投影片，未直接讀取；內容已由 L4_Clustering_完整前置整理.md 的『逐頁內容整理』（p.1–p.80）完整轉述"
  - type: local_pdf
    path: C:\Users\User\Desktop\大數據\L5.pdf
    note: "原始投影片，未直接讀取；內容已由 L5_Sequence_Tagging_完整前置整理.md 的『逐頁內容整理』轉述"
coverage: |
  【誠實說明】
  - Notion 五頁（Lecture 4 主頁 + Part 1/2/3、Lecture 5）：100% 全文讀完。
  - Lecture4_Clustering_完整講義_Notion版.md（2737 行）：讀完 1–2737 行中的
    1–1000、1000–1700、1700–2260、2260–2737，即 100% 讀完（分四段）。
  - Lecture5_SequenceTagging_完整講義_Notion版.md（600 行）：**未逐行讀完**。
    已用 grep 對照確認其章節結構與 Notion Lecture 5 頁面高度重疊（Notion 版更完整，
    含 HMM 三矩陣數值範例、LSTM 門控公式、四路線比較表），本 digest 的 L5 內容
    以 Notion 版為主體。本機版獨有的「§11 與 ARIMA 的比較」已透過 grep 與
    L5 前置整理 Part XIII 交叉補齊。估計 L5 講義覆蓋率 ~85%。
  - L4_Clustering_完整前置整理.md（2075 行）：讀完標題索引（全部 100+ 個標題）
    + 1400–2075 行（逐頁投影片對照 p.18–p.80 與模組建議）。前半（Part I–XI 的
    論述文字）**未逐行讀完**，但其內容與 Lecture4 完整講義 Notion 版重複度極高
    （已比對標題一一對應）。估計覆蓋率 ~70%，且未讀部分無獨有資訊。
  - L5_Sequence_Tagging_完整前置整理.md（1164 行）：僅讀標題索引（全部）。
    估計覆蓋率 ~25%。其 Part I–XIV 標題與 Notion Lecture 5 章節一一對應。
  - L4.pdf / L5.pdf：**未開啟**。改以前置整理的逐頁摘要（p.1–p.80）取得投影片
    層級事實（如 elbow 圖 K≈4、purity 例題數字、DBSCAN 互動網站等）。
  【最重要的覆蓋缺口】教材本身沒有的東西見文末「§13 教材未涵蓋（Gap）」。
---

# Lecture 4 Clustering + Lecture 5 Sequence Tagging

> **閱讀約定**
> 【材料原文】= 直接取自 Notion / 本機講義 / 前置整理的內容（含公式、表格、例題數字）。
> 【評註】= 萃取者（我）補充的判斷、行銷映射、與教材缺口提醒。**教材沒說的，一律標【評註】。**

---

## §0 這兩堂課在解什麼問題（定位）

【材料原文｜Notion Lecture 4 主頁「這個章節在解決什麼？」】

- 如果 Lecture 3 的核心問題是：「已經知道有哪些類別，如何讓機器把文件自動分到正確類別？」
- 那 Lecture 4 的核心問題就變成：**如果根本沒有預先標籤，機器能不能自己從資料中找出結構？**
- 分類（classification）與分群（clustering）最本質的差異：
  - **分類**：類別已經存在，模型要學會怎麼分。
  - **分群**：類別還未存在，模型要自己找出資料裡可能的群組結構。
- 換句話說，這堂課的本質是：**從「已知類別的監督式分類」轉向「未知結構的非監督式學習」。**

【材料原文｜同頁「在現實世界中，分群無處不在」】

- **新聞推薦系統**：自動把海量新聞組織成主題群組，方便使用者瀏覽。
- **客戶分群**：電商根據消費行為把使用者分成不同族群，做差異化行銷。
- **搜尋引擎**：把搜尋結果自動分類，提供更有結構的導覽。
- **生物資訊**：將基因或蛋白質按相似性分群，發現潛在功能類別。
- **金融風控**：將交易行為分群，識別異常群組或潛在欺詐模式。

【材料原文｜Notion Lecture 5「這個章節在解決什麼問題？」】

- 到 L3 為止，處理的是單一文件或單一樣本的分類問題（一個輸入 → 一個輸出標籤）。
- 聚類讓我們發現數據的內部結構，但仍然沒有「預測序列中每一步的決策」。
- **L5 定位**：現在面對的是「序列中的每一個位置都需要決策」的問題。不再是「一個輸入 → 一個輸出」，而是「序列輸入 → 序列輸出」。
- 白話：想像從「診斷一份病歷」（單一分類）升級到「診斷一個病人的整個治療過程」（每天都要決定治療方案）。前者是靜態決策，後者是動態決策。

【評註｜行銷映射】
- L4 = **顧客分群 / 消費者輪廓（segmentation & persona）** 的方法論基礎。
- L5 = **顧客旅程（customer journey）、生命週期階段標註、購買序列建模** 的方法論基礎。
  L4 回答「這批顧客可以分成哪幾種人」，L5 回答「同一個顧客在時間軸上正處於哪個階段、下一步會做什麼」。

---

## §1 Clustering 的正式定義與判準

### 1.1 定義

【材料原文｜本機講義 §1.1】

給定一個文件集合 $D = \{d_1, d_2, \ldots, d_n\}$，Clustering 是一種無監督學習任務，其目的是將 $D$ 分割成 $k$ 個不相交的子集（簇）$C = \{c_1, c_2, \ldots, c_k\}$，使得：

1. $\bigcup_{i=1}^{k} c_i = D$（覆蓋所有文件）
2. $c_i \cap c_j = \emptyset$ 當 $i \neq j$（子集互不重疊）
3. 同一簇內的文件具有高度相似性（intra-cluster similarity 高）
4. 不同簇之間的文件具有低度相似性（inter-cluster similarity 低）

視覺化 / 降維的形式化寫法：

$$\pi: D \rightarrow C = \{c_1, c_2, \ldots, c_k\}, \quad k \ll n$$

### 1.2 好分群的四個評價標準

【材料原文｜Notion Lecture 4 主頁「總結 > Clustering 的本質」】

- 不是預測既有類別，而是從無標籤資料中找出潛在結構。
- 評價標準：
  - 群內相似。
  - 群間相異。
  - **群數合理**。
  - **結果可解釋**。

【評註】這四條就是可以直接寫成 Skill 檢查清單的驗收條件——注意教材把「群數合理」和「可解釋」與統計指標並列，這正是行銷分群最常被忽略的兩項。

### 1.3 Classification vs Clustering

【材料原文｜Notion Part 1 表格】

| 特性 | Classification | Clustering |
|---|---|---|
| 學習方式 | Supervised Learning | Unsupervised Learning |
| 類別定義 | Human-defined，事先已知 | Inferred from data，事後推論 |
| 評估方式 | 與已知類別比對準確度 | 評估群內同質性與群間異質性 |
| 核心問題 | 這個東西屬於哪一個已知類別？ | 這些資料自然會形成哪些群？ |

【材料原文｜本機講義 §1.3 補充列】

| 面向 | Classification | Clustering |
|---|---|---|
| 訓練資料 | Labeled data $(x_i, y_i)$ | Unlabeled data $\{x_i\}$ |
| 目標 | 預測新文件的類別 | 發現文件的自然分組 |
| 輸出 | 預測類別標籤 | 簇的分配 |
| 例子 | 垃圾郵件偵測、情感分析 | **客戶分群**、主題探索 |
| 評估方式 | Accuracy、Precision、Recall | Silhouette Score、CH Index |

$$\text{Classification: Given } (d_1, y_1),\ldots,(d_n, y_n) \quad \text{Learn: } f(d) \rightarrow y$$
$$\text{Clustering: Given } d_1,\ldots,d_n \quad \text{Discover: } c_1,\ldots,c_k$$

【材料原文｜Notion Part 1「常見誤解」】

- 很多人會以為分群只是「沒有標籤版本的分類」，但其實不完全對。
- 分類中的類別通常有明確語意（spam / non-spam、positive / negative）。
- **分群出來的群，不一定一開始就有語意名稱。它只是先形成一批彼此相近的點，後面還要再做 labeling / interpretation。**
- 也就是說，分群之後常常還要再問一次：「這一群到底代表什麼主題？」

【評註｜行銷】這句話就是「分群 ≠ persona」的教材依據：K-means 給你 cluster 1~5，命名成「小資嘗鮮族 / 高頻補貨族」是**額外的 labeling 工作**，不是演算法輸出。

---

## §2 為什麼要做 Clustering（五大用途）—— 回答什麼商業問題

### 2.1 用途一：視覺化文件集合（Whole corpus analysis / navigation）

【材料原文】文件集合龐大時，直接展示所有文件不切實際。Clustering 提供「3D 地形圖式」的視覺化：先將高維文件空間聚類成數個簇 → 每個簇用代表點（重心）表示 → 在 2D/3D 呈現簇間關係。

範例（10,000 篇新聞 → 5 簇）：政治 1,200 / 運動 2,100 / 娛樂 3,500 / 科技 2,000 / 財經 1,200；在 2D 平面用 5 個圓點表示，圓大小 = 文件數，位置 = 相似度。

> **回答的商業問題**：「我手上這 50 萬筆評論/商品/顧客，整體長什麼樣子？」

### 2.2 用途二：改進搜尋召回率（Cluster Hypothesis）

【材料原文｜Cluster Hypothesis】

> 相似的文件往往被分配到同一簇中；相似的文件與查詢的相關性也相似。

$$\text{If } d_i, d_j \in c_k \text{ and } \text{sim}(d_i, q) \text{ is high, then } \text{sim}(d_j, q) \text{ is also likely high}$$

兩階段檢索：(1) 找出與查詢最相似的簇（通常 5～10 個簇中心）；(2) 在該簇內做精確搜尋；需要更多結果時逐步查看鄰近簇。

數據：100,000 份文件、查詢「機器學習」→ 直接掃描召回率 60%；聚成 100 簇後取 5 個最相關簇（~5,000 文件）+ 檢查相鄰簇 → 召回率 85%。

> **回答的商業問題**：「站內搜尋 / 推薦候選集怎麼擴大而不失準？」

### 2.3 用途三：搜尋結果導航（Faceted Search）

【材料原文】查詢「Python 教學」返回 50,000 結果，Clustering 後分成：初學者教程（8,000）、Web 開發（12,000）、資料科學（15,000）、遊戲開發（5,000）、性能優化（10,000）。

效率數據：未分組平均需瀏覽 100 個結果才找到想要的（成功率 50%）；分組後平均瀏覽 20 個（成功率 80%）→ **效率提升 4 倍**。

Amazon 搜尋「手機」的 Facets：品牌（Apple、Samsung…）、價格段（<100¥、100-300¥…）、容量（32GB、64GB…）。

> **回答的商業問題**：「電商/內容平台的分類導航要怎麼自動生成？」

### 2.4 用途四：加速向量空間檢索

【材料原文｜複雜度】

| 方法 | 時間複雜度 | 備註 |
|---|---|---|
| 直接向量搜尋 | $O(n \cdot m)$ | $n$ = 100M 時非常慢 |
| Clustering + 雙階段 | $O(k \cdot m + t \cdot \lvert c_i \rvert \cdot m)$ | $t \ll k \ll n$ |

聚類版總式：$O\!\left(m \cdot \left(K + \frac{t \cdot n}{K}\right)\right)$

數值例（本機講義版）：100 萬份文件、1,000 維、聚 100 簇、搜前 5 簇 → 直接法 $10^9$ 次運算 ≈ 1 秒；聚類法 ≈ 51 萬次 ≈ 0.05 秒，**加速 20 倍**。
數值例（Notion Part 1 版）：$n=1{,}000{,}000$、$K=1000$、簇大小 1000、$t=5$ → $O(m \cdot 6000)$ ≈ 理論 6 倍，**實際觀察 10～20 倍加速**。

> **回答的商業問題**：「即時推薦要在 50ms 內從千萬 SKU 撈出候選。」

### 2.5 用途五：更好地理解數據（★ 行銷最核心的一條）

【材料原文｜全局統計會騙人】

雞兔同籠：100 隻「四足動物」全局平均體重 45 kg、標準差 30 kg；但雞 2 kg、兔 3 kg、羊 60 kg、牛 500 kg。**全局平均 45 kg 對任何真實動物都不具代表性！**

聚類後：

| 簇 | 動物種類 | 數量 | 平均體重 | 標準差 |
|---|---|---|---|---|
| 1 | 雞、兔 | 30 | 2.5 kg | 0.8 kg |
| 2 | 羊 | 40 | 60 kg | 8 kg |
| 3 | 牛 | 30 | 500 kg | 50 kg |

【材料原文｜客戶購買行為分析 — 這段可直接搬進行銷 Skill】

**方法一（無聚類）**：全部客戶平均購買金額 \$500、平均購買頻率 10 次/年 → 無法指導行銷策略——有的客戶是「高消費、低頻率」，有的是「低消費、高頻率」。

**方法二（聚類後）**：

| 簇 | 名稱 | 客戶數 | 平均客單 | 購買頻率 | 策略 |
|---|---|---|---|---|---|
| 1 | VIP | 5% | \$3,000 | 2 次/年 | 個性化服務 |
| 2 | 常客 | 20% | \$200 | 20 次/年 | 會員優惠 |
| 3 | 偶買客 | 75% | \$100 | 2 次/年 | 促銷刺激 |

【材料原文｜Notion Part 1 版本】
- 問題：「平均客單價 500 元」並不意味著均勻分佈，可能是 80% 客戶消費 100 元、20% 客戶消費 2000 元。
- 解決：簇 1 高消費低頻（少數大客戶，年消費 10,000 元以上）；簇 2 低消費高頻（大量小客戶，月消費 10～50 元）。
- 應用（差異化營銷）：對簇 1 → VIP 服務、高端產品推薦；對簇 2 → 高頻優惠、薄利多銷。

【材料原文｜數學表述】

不聚類時的方差：$V_{\text{global}} = \frac{1}{n} \sum_{j=1}^{n} (x_j - \bar{x})^2$

聚類後簇內平均方差：$V_{\text{within}} = \frac{1}{k} \sum_{i=1}^{k} V_i$

通常 $V_{\text{within}} \ll V_{\text{global}}$，說明聚類後的子群更同質。

> **回答的商業問題**：「為什麼要做顧客分群？」—— 因為全局平均會掩蓋多樣性，一刀切的行銷策略對誰都不最優。這是教材給的**分群正當性論證**。

---

## §3 做分群前的四個核心決策

【材料原文｜Notion Part 1「核心問題與決策」四題】
問題一：如何表示文件？ 問題二：如何定義距離？ 問題三：決定 K 值（簇數）。 問題四：結果可解釋性。
教材直言：**「K 值決定是 Clustering 的最大問題！沒有絕對的『對』或『錯』，取決於業務目標和數據本身。」**

### 3.1 資料表示（Document Representation）

【材料原文｜三大方法比較表】

| 方法 | 維數 | 語義 | 速度 | 場景 |
|---|---|---|---|---|
| BoW | 詞彙大小（通常 10,000+） | 無 | 快 | 初探、簡單任務 |
| TF-IDF | 詞彙大小 | 弱（基於頻率） | 快 | 傳統信息檢索 |
| Embedding | $d \ll m$（100–1024） | 強 | 中 | 深度分析、現代應用 |

**BoW**：$\vec{d} = (x_1, \ldots, x_m)$，$x_i$ = 詞 $i$ 在文件 $d$ 中出現次數。
```
詞彙表：['python', 'java', 'clustering', 'learning']
文件1："Python clustering is great for learning"
向量：[1, 0, 1, 1]
```
優點：簡單、快速。缺點：詞序和語法資訊丟失、高維稀疏向量。

**TF-IDF**：
$$\text{TF-IDF}(i,d) = \text{TF}(i,d) \times \text{IDF}(i)$$
$$\text{TF}(i,d) = \frac{\text{詞}i\text{在}d\text{中出現次數}}{d\text{中的總詞數}}, \qquad \text{IDF}(i) = \log \frac{n}{\text{包含詞}i\text{的文件數}}$$
```
詞 'python' 出現在 100/1000 文件中：IDF = log(1000/100) = 1.0
詞 'the'    出現在 999/1000 文件中：IDF = log(1000/999) ≈ 0.001
```

**Word Embeddings**：$\vec{w} \in \mathbb{R}^{d}$（$d$ 通常 100–1000）；文件向量常取詞向量平均
$$\vec{d} = \frac{1}{|d|} \sum_{w \in d} \vec{w}$$

【評註｜行銷映射】BoW/TF-IDF ↔ 顧客的「品類購買次數矩陣 / RFM 原始值」；Embedding ↔ 商品或顧客的向量化表示（item2vec、顧客嵌入）。教材的訊息是：**表示越好，聚類效果越好**——分群失敗有一半是特徵沒做好，不是演算法問題。

### 3.2 距離度量怎麼選（★ 任務問題 3）

【材料原文｜Notion Part 1 四大距離度量表】

| 指標 | 公式 | 適用 |
|---|---|---|
| Euclidean | $\sqrt{\sum(x_i-y_i)^2}$ | 連續數值、小維數 |
| Manhattan | $\sum \lvert x_i-y_i \rvert$ | 離散數據、棋盤距離 |
| Cosine | $\frac{x \cdot y}{\lVert x\rVert \lVert y\rVert}$ | 文本、方向相似性 |
| Jaccard | $\frac{\lvert A \cap B\rvert}{\lvert A \cup B\rvert}$ | 集合、二值向量 |

【材料原文｜本機講義 §3.2 更詳細版】

**1. Euclidean Distance（歐幾里得距離）**
$$d_E(x, y) = \sqrt{\sum_{i=1}^{m} (x_i - y_i)^2}$$
- 幾何意義：直線距離（飛行距離）
- 適用：連續數值數據
- 問題：**對異常值敏感、在高維空間中失效（維度詛咒）**；在高維空間中，所有點到原點的距離趨近相等
- 例：$x=(0,0)$、$y=(3,4)$ → $d_E = \sqrt{3^2+4^2} = 5$

**2. Manhattan Distance（曼哈頓距離）**
$$d_M(x, y) = \sum_{i=1}^{m} |x_i - y_i|$$
- 幾何意義：棋盤距離（只能走直角路）
- 適用：城市街區、離散數據
- 優點：計算快、**對異常值相對不敏感、在稀疏數據上更穩健**
- 例：$x=(0,0)$、$y=(3,4)$ → $d_M = 3+4 = 7$

**3. Cosine Similarity（余弦相似度）**
$$\cos(x, y) = \frac{x \cdot y}{\lVert x\rVert \cdot \lVert y\rVert} = \frac{\sum_{i=1}^{m} x_i y_i}{\sqrt{\sum x_i^2} \cdot \sqrt{\sum y_i^2}}$$
- 範圍：$[-1, 1]$（1 = 完全相同方向，0 = 正交，-1 = 完全相反）
- 優點：**只考慮方向、不考慮大小**；對文本特別有效（忽略文件長短）
- 特性：與向量長度無關（(1,1) 和 (10,10) 的餘弦相似度都是 1）
- 轉距離：$d(x,y) = 1 - \cos(x,y)$
- 例：$x=(1,0)$、$y=(1,1)$ → $\cos = 1/\sqrt{2} \approx 0.707$

**4. Jaccard Similarity（杰卡德相似度）**
$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$
- 適用：集合型數據（如 tag、**購買清單**）
- 範圍：$[0, 1]$
- 例：
```
用戶A的購買：{蘋果, 香蕉, 橙子}
用戶B的購買：{香蕉, 橙子, 葡萄}
交集：{香蕉, 橙子}，聯集：{蘋果, 香蕉, 橙子, 葡萄}
J = 2/4 = 0.5
```

【材料原文｜比較表與互換公式】

| 指標 | 公式型別 | 應用場景 | 特點 |
|---|---|---|---|
| Euclidean | 距離 | 連續數值 | 直觀但高維失效 |
| Manhattan | 距離 | 離散/棋盤 | 快速、穩健 |
| Cosine | 相似度 | 文本、向量 | 方向一致性 |
| Jaccard | 相似度 | 集合數據 | 只看重疊 |

- 距離轉相似度：$\text{sim}(x,y) = \frac{1}{1 + d(x,y)}$
- 相似度轉距離：$d(x,y) = 1 - \text{sim}(x,y)$

【材料原文｜前置整理 p.（文字資料補充）】在文字資料裡，因為向量通常高維且稀疏，所以 **cosine similarity 特別常見**。

【材料原文｜學長的話】「距離定義就像『怎麼判定兩個人相似』。用身高？用興趣？用消費習慣？每個標尺衡量的『相似』都不同。文本聚類用余弦（只看方向），購物聚類用杰卡德（只看共通點），數值數據用歐幾里得（看整體距離）。選對度量，事半功倍。」

【評註｜行銷資料型態對照 → 直接可寫進 Skill 的決策規則】

| 顧客資料型態 | 選距離 | 教材依據 |
|---|---|---|
| RFM 標準化後的連續數值（低維，3–8 維） | **Euclidean** | 「連續數值、小維數」 |
| 含極端值的金額（未做 log、未 winsorize） | **Manhattan**（或先處理極端值再用 Euclidean） | 「對異常值相對不敏感、稀疏數據更穩健」 |
| 品類佔比 / 購買結構（在意**組合比例**而非消費規模） | **Cosine** | 「對向量大小不敏感」——可分出「買同樣品類組合但客單不同」的人 |
| 購買品項清單、標籤集合、是否買過 X 的 0/1 向量 | **Jaccard** | 「集合、二值向量」——教材的購買清單例子就是這個 |
| 高維（品類 100+、TF-IDF 文本評論） | **Cosine**，且務必先降維 | 「高維失效（維度詛咒）」 |

---

## §4 群數 K 怎麼決定（★ 任務問題 1）

### 4.1 教材的總體立場

【材料原文｜Notion Part 1】
- **K 值決定是 Clustering 的最大問題！**
- 沒有絕對的「對」或「錯」，取決於業務目標和數據本身。

【材料原文｜本機講義 §3.3 / §6.2】
- **Case 1: K 已知** — 某些應用中 K 先驗已知（分公司數量固定、預先定義的分類），直接用該 K 值。
- **Case 2: K 未知（更常見，更難）** — 大多數應用無法事先確定 K，需要用啟發式方法決定。

【材料原文｜前置整理 p.30「If K not specified in advance」】可自動建議 K：用 heuristics based on N；用 K vs. cluster-size diagram。**重點在於群太少與群太多之間的 tradeoff。**

### 4.2 方法一：Elbow Method（手肘法）

【材料原文｜完整步驟】

1. **定義指標**：群內平方和（WGSS = Within-Group Sum of Squares）
   $$\text{WGSS}(K) = \sum_{k=1}^{K} \sum_{x_i \in c_k} \lVert x_i - \mu_k \rVert^2$$
   這正是 K-means 的目標函數 $G$。
2. **計算曲線**：對 $K = 1, 2, \ldots, K_{\max}$（如 $K_{\max}=20$），$\text{WGSS}(K) = \min_{\text{partition}} G$
3. **改善率**：
   $$\text{Improvement Ratio}(K) = \frac{\text{WGSS}(K-1) - \text{WGSS}(K)}{\text{WGSS}(K-1)} \times 100\%$$
4. **尋找肘部**：找到改善率急劇下降的地方。

【材料原文｜視覺示例與判讀】
```
WGSS
   |
5000|●
   |  ╲
4000|    ●╲
   |      ╲╲
3000|        ●╲
   |          ╲╲
2000|            ●
   |              ╲
1500|                ●
   |                  ╲
1200|                    ● ← 肘部
   |                      ╲
1100|                        ●
   |                         ╲
1000|                          ●
   |________________________________
     1    3    5    7    9   11  13  K
```
- K=1-4：WGSS 快速下降（改善 50%-80%）
- K=5：開始減速
- **K=9-10：肘部**，改善率急劇下降（<5%）
- K>10：幾乎沒有改善
- **決策：選擇 K=10**

【材料原文｜直觀解釋】
- $K$ 越大，G 一定越小（極端情況下 $K=N$ 時 $G=0$）。
- 但某個 K 之後，繼續加 K 帶來的 G 下降很少 → 不值得。
- K 小時，增加一個簇減少 WGSS 很多（因為點確實分散）；K 達到真實簇數附近時，再增加 K 幫助不大（因為開始人為分裂）。**肘部正好是「自然簇數」的信號。**
- 白話：就像你切蛋糕，切越多片每片越整齊，但切到某個程度之後再切下去改善不大，反而更麻煩。

【材料原文｜投影片層級（前置整理 p.31）】
- x 軸：群數；**y 軸：解釋變異比例**；紅圈標出 elbow，**大約在 K=4**。
- 每加一群所帶來的邊際改善開始下降的前一點，就是合理 K 候選。

> **陷阱**：教材明說 Elbow **客觀性低（靠人眼）**、主觀性強。

### 4.3 方法二：Calinski-Harabasz Index（CH Index）

【材料原文｜定義（兩種等價寫法）】

$$\text{CH Index}(K) = \frac{\text{BGSS}/(K-1)}{\text{WGSS}/(N-K)} \qquad\Longleftrightarrow\qquad C = \frac{N-K}{K-1} \cdot \frac{\text{BGSS}}{\text{WGSS}}$$

其中
- $N$ = 總樣本數，$K$ = 群數
- **BGSS（Between-Group Sum of Squares）**：群間離散度
  $$\text{BGSS} = \sum_{k=1}^{K} |c_k| \cdot \lVert center_k - center_{global} \rVert^2$$
- **WGSS（Within-Group Sum of Squares）**：群內離散度（= K-means 目標函數）

【材料原文｜直觀含義】
$$\text{CH} = \frac{\text{簇之間差異大}}{\text{簇內差異小}}$$
好的分群 = 群間離得遠（BGSS 大）+ 群內很緊（WGSS 小）。**Calinski-Harabasz 越大越好。**

【材料原文｜範例計算】

假設 N=100，K=3：

| 指標 | 值 |
|---|---|
| WGSS | 500 |
| BGSS | 2000 |
| CH | $(2000/2) / (500/97) = 1000 / 5.15 \approx 194$ |

假設 K=5：

| 指標 | 值 |
|---|---|
| WGSS | 400 |
| BGSS | 2200 |
| CH | $(2200/4) / (400/95) = 550 / 4.21 \approx 131$ |

→ **K=3 的 CH Index 更高，說明 K=3 更好。**

【材料原文｜決策規則】
```
計算 CH Index 對所有候選 K 值
找 K* = arg max_K CH Index(K)
選擇 K*
```

### 4.4 方法三：先驗知識 / 領域專家

【材料原文｜方法比較表】

| 方法 | 客觀性 | 計算量 | 穩定性 | 推薦 |
|---|---|---|---|---|
| Elbow | 低（靠人眼） | 低 | 高 | 初步探索 |
| CH Index | 高（自動最大化） | 中等 | 中等 | 標準選擇 |
| 先驗知識 | 無需計算 | 低 | 高 | **最好（如果有）** |

### 4.5 教材給的 K 決策 SOP（★ 可直接寫成 Skill 步驟）

【材料原文｜本機講義「實務建議」】
```
Step 1: 用先驗知識縮小 K 範圍（如果有）
        例：市場調查提示客戶可能 3-5 類
Step 2: 計算 K = 2 到 10 的 CH Index
Step 3: 選擇 CH Index 最高的 K
Step 4: 驗證（用 Elbow 法視覺檢查，聽專家意見）
```

【材料原文｜Notion Part 1「實務建議」】
- 快速探索：先用 Elbow 法，粗略估計 K 範圍。
- 精確決定：在範圍內用 CH Index，找峰值。
- 驗證：**視覺檢查簇的大小和語義是否合理**。
- 專家意見：最後問領域專家，**K 要反映業務需求**。
- 總結：Elbow 法主觀性強，CH Index 是數學化、自動的。兩者結合使用最佳：讓 CH Index 給你候選，再用肘部法視覺驗證是否合理。**如果兩者意見不一，找領域專家問問，因為最終 K 要反映實際業務需求，不能純粹靠數學。**

【材料原文｜方法選擇決策樹（Notion Lecture 4 主頁「方法選擇建議」）】
```plain text
Start here:

資料特性？
├─ 群形狀？
│  ├─ 球形 / 均勻 → K-means（快速、預設首選）
│  └─ 不規則 / 細長 → DBSCAN 或 Single-link HAC
│
├─ 是否有噪音？
│  ├─ 大量噪音 → DBSCAN（自動識別 noise）
│  └─ 乾淨資料 → K-means 或 HAC
│
├─ 是否需要階層結構？
│  ├─ 需要 → HAC（得到 dendrogram）
│  └─ 不需要 → K-means 或 DBSCAN
│
├─ K 是否已知？
│  ├─ 已知 → K-means 直接用
│  └─ 未知 → DBSCAN 或先用 elbow method
│
└─ 文本是否多主題重疊？
   ├─ 是 → Topic Model（LDA）
   └─ 否 → Hard clustering
```

【評註｜K 決策的陷阱清單（教材明示 + 教材邏輯推論）】
1. **Elbow 的肘部常常不存在或有多個** —— 教材承認靠人眼、主觀性強；DBSCAN 的 k-distance 圖也明說「曲線可能有多個較明顯的肘部，需要領域知識判斷」，同一個病理。
2. **WGSS 對 K 單調遞減**（$K=N$ 時 $G=0$），所以不能拿 WGSS 本身當「越低越好」的選擇準則 —— 這是教材直接寫出的。
3. **Purity 也是隨 K 上升而上升**（見 §6.2），所以不能用 Purity 選 K。
4. **教材唯一給出「可自動最大化」的 K 選擇指標是 CH Index**；Silhouette 只在評估段被列名，沒有給公式（見 §13 Gap）。
5. **最終仲裁權在業務**：教材兩處都寫「K 要反映業務需求，不能純粹靠數學」。行銷分群請把「每群要有足夠人數可以下廣告」「群數不能多到行銷團隊做不出這麼多套素材」當成硬約束。

---

## §5 K-means（完整）

### 5.1 定位

【材料原文】
- K-means 可能是最知名的 clustering algorithm；簡單、很多情境下效果不錯、可作為 clustering 的 **default / baseline**。
- Official Full Name：K-means Clustering Algorithm；**First Proposed 1957（Stuart Lloyd）**；**Popularized 1967（MacQueen）**。
- **K** = 簇的個數（用戶指定）；**means** = 每個簇由其重心（mean）代表。
- 地位：不知道用什麼算法時先試 K-means；評估新算法的基準；Spark / TensorFlow 內置；教學入門首選。
- 白話：K-means 的角色很像分類問題裡的 baseline model —— 不一定永遠最好，但非常值得先做，而且能快速建立比較基準。

### 5.2 重心（Centroid）

$$\mu(c) = \frac{1}{|c|} \sum_{x \in c} x$$

例（2D）：簇 $c = \{(0,0), (2,0), (2,2), (0,2)\}$（正方形四角）→ 重心 $\mu(c) = (1,1)$（正方形中心）。

核心假設：
$$\boxed{\text{同簇的點應該聚集在其重心周圍}}$$

### 5.3 目標函數

【材料原文】WCSS（Within-Cluster Sum of Squares）/ RSS（Residual Sum of Squares）/ Inertia：

$$G = \sum_{k=1}^{K} \sum_{x_i \in c_k} \lVert x_i - \mu_k \rVert^2$$

分配矩陣寫法：$R \in \{0,1\}^{n \times K}$，$r_{ik}=1$ 若 $x_i$ 分配到簇 $k$，否則 0：

$$G = \sum_{i=1}^{n} \sum_{k=1}^{K} r_{ik} \lVert x_i - \mu_k \rVert^2$$

**為什麼用平方距離？**
1. 數學上便利：平方函數處處可微，易於優化（方便梯度下降）
2. 懲罰遠點：異常值（距簇心遠的點）被更重地懲罰
3. 凸函數：確保本地最小值的存在性

**K-means 作為 EM 的特例**：$G = \text{Negative Log-Likelihood of Gaussian Mixture}$；K-means 實際上是 EM 算法的特例（當高斯方差趨向 0 時）。

### 5.4 演算法流程

【材料原文｜四步】

- **Step 1 初始化**：隨機選 $K$ 個點作為初始重心 $\mu_1^{(0)}, \ldots, \mu_K^{(0)}$（從文件中隨機挑 $K$ 篇作為初始中心）
- **Step 2 分配（Assignment）**：$k^* = \arg\min_{k=1}^{K} \lVert x_i - \mu_k \rVert^2$，等價寫法 $\text{cluster}(d_i) = \arg\min_{j} \text{distance}(d_i, \mu_j)$
- **Step 3 更新（Update）**：$\mu_k^{(t+1)} = \frac{1}{|c_k|} \sum_{x_i \in c_k} x_i$
- **Step 4 收斂檢查**：滿足停止條件則終止，否則回 Step 2

【材料原文｜四種常見停止條件】
1. 固定迭代次數：$t > T_{\max}$（如 100 次）
2. 簇分配無變化：$c_k^{(t)} = c_k^{(t-1)}$ 對所有 $k$ 成立
3. 重心無變化：$\lVert \mu_k^{(t)} - \mu_k^{(t-1)} \rVert < \epsilon$
4. 目標函數變化足夠小：$\lvert G^{(t)} - G^{(t-1)} \rvert < \epsilon$

【材料原文｜偽碼】
```
Algorithm K-means(data D, number of clusters K, max iterations T_max)
  Input: 數據集 D = {x₁, x₂, ..., xₙ}，簇數 K，最大迭代次數 T_max
  Output: 簇分配 C = {c₁, c₂, ..., cₖ}，重心集 M = {μ₁, μ₂, ..., μₖ}

  1. 隨機初始化 K 個重心：μ₁⁽⁰⁾, μ₂⁽⁰⁾, ..., μₖ⁽⁰⁾
  2. t ← 0
  3. REPEAT
  4.   // Step 2: Assignment
  5.   FOR EACH point xᵢ in D:
  6.     k* ← arg min_k ||xᵢ - μₖ⁽ᵗ⁾||²
  7.     assign xᵢ to cluster cₖ*
  8.   END FOR
  9.
  10.  // Step 3: Update
  11.  FOR EACH cluster cₖ:
  12.    μₖ⁽ᵗ⁺¹⁾ ← (1/|cₖ|) * Σ(xᵢ ∈ cₖ) xᵢ
  13.  END FOR
  14.
  15.  // Step 4: Check convergence
  16.  IF (no assignment changed) OR (t > T_max):
  17.    BREAK
  18.  END IF
  19.
  20.  t ← t + 1
  21. UNTIL convergence
  22.
  23. RETURN C, M
```

### 5.5 收斂性證明

【材料原文】

**Theorem**：K-means 演算法必定收斂到局部最小值。

**Claim 1（Assignment 單調降低 $G$）**：每個點被重新分配給最近的重心 $k^* = \arg\min_k \lVert x_i - \mu_k \rVert^2$，確保 $x_i$ 的貢獻項小於等於前一輪，因此 $G^{(t+1)} \leq G^{(t)}$。

**Claim 2（Update 單調降低 $G$）**：給定簇成員固定，對每個簇最小化 $f_k(\mu) = \sum_{x_i \in c_k} \lVert x_i - \mu \rVert^2$，求導

$$\frac{\partial f_k}{\partial \mu} = -2 \sum_{x_i \in c_k} (x_i - \mu) = 0 \;\Longrightarrow\; \mu_k = \frac{1}{|c_k|} \sum_{x_i \in c_k} x_i$$

這正是 K-means 的更新公式，在此值下 $G$ 達到最小。

**Conclusion**：$G$ 有下界（$G \geq 0$）且單調遞減，必定收斂。

$$\boxed{\text{K-means 保證收斂，但只收斂到局部最小值，不保證全域最小值}}$$

【材料原文｜前置整理 p.25】K-means 是 EM 的特例；理論上會收斂；但可能迭代很多次；**一開始逼近快，後面變慢**。

### 5.6 時間複雜度

$$O(I \cdot K \cdot n \cdot m)$$

| 符號 | 含義 | 說明 |
|---|---|---|
| $I$ | 迭代次數 | 通常 10-100 次（實務 10–50） |
| $K$ | 簇的個數 | 通常 2-50 |
| $n$ | 數據點總數 | 文件數、樣本數 |
| $m$ | 特徵維數 | TF-IDF 維數、embedding 維數 |

拆解：Assignment $O(n \cdot K \cdot m)$；Update $O(n \cdot m)$；每輪合計 $O(n \cdot K \cdot m)$。

【材料原文｜降維效益的實例】
```
例1：n = 1,000,000；m = 5,000（TF-IDF）；K = 20；I = 20
     複雜度 = 2 × 10¹² 次操作 ≈ 30 分鐘（現代 CPU）

例2：同樣數據，降到 100 維 embedding
     m = 100 → 複雜度 = 4 × 10¹⁰ 次操作 ≈ 0.5 分鐘（快 60 倍！）
```

| 因素 | 影響程度 | 說明 |
|---|---|---|
| 數據量 $n$ | 線性 | 最主要成本 |
| 維數 $m$ | 線性 | **降維效果顯著** |
| 簇數 $K$ | 線性 | |
| 迭代次數 $I$ | 線性 | 大多實際應用中很小（5-50） |

**優化策略**：1. 降維（PCA、embedding）→ 效果最明顯；2. 增量 K-means；3. 迷你批次 K-means；4. 並行計算。

### 5.7 變種：Mini-batch K-means

【材料原文】
```
For each mini-batch B (size b, much smaller than n):
  1. 計算 B 中每點到 K 個重心的距離
  2. 分配 B 中每點到最近重心
  3. 更新各簇的重心（只基於 B 中的新分配）
```
- 每步複雜度 $O(K \cdot b \cdot m)$，$b \ll n$
- 需要多個 epoch，但單步更快；收斂速度稍慢但仍有保證；適合流式數據（online learning）
- Trade-off：收斂速度 vs. 單步計算時間

【材料原文｜前置整理 p.33 K-means variations】每加入一個點後就立刻重算 centroid，可能加快收斂速度。

### 5.8 Issue 1：Seed Choice（初始種子）

【材料原文｜問題描述】
- 現象：運行同一個 K-means 演算法 10 次，得到 10 個不同的結果。
- 原因：K-means 對初始化敏感，不同初始值導致不同局部最小值。
- 後果：某次可能陷入「差」的局部最小值，聚類品質差。

【材料原文｜1D 具體例子】
```
點位置：A(1), B(2), C(3), D(10), E(11), F(12)

「好」的初始重心選擇（μ₁=2, μ₂=11）：
  迭代 0：  簇1 = {A,B,C}, 簇2 = {D,E,F}
  迭代 1：  μ₁=2,  μ₂=11  （無變化）
  結果：   正確分組 ✓

「差」的初始重心選擇（μ₁=3, μ₂=4）：
  迭代 0：  簇1 = {A,B,C,D}, 簇2 = {E,F}
  迭代 1：  μ₁ = (1+2+3+10)/4 = 4,  μ₂ = (11+12)/2 = 11.5
  迭代 2：  簇1 = {A,B,C,D}, 簇2 = {E,F}
  結果：   不對稱，B、C 應和 D 分離 ✗
```

【材料原文｜方案 A：啟發式選擇】
- 方法 1（選統計量點）：$\mu_1^{(0)} = \frac{1}{n}\sum_{i=1}^{n} x_i$（全局重心），然後選遠離 $\mu_1^{(0)}$ 的點作為第 2–K 個初始中心。
- 方法 2（選相距最遠的點）：
```
1. 隨機選第一個點 p₁
2. 選距 p₁ 最遠的點 p₂
3. 選距 {p₁, p₂} 最遠的點 p₃
4. ...重複至 K 個點
```
- 優點：簡單，無參數。缺點：啟發式，無理論保證。
- 白話（開分店比喻）：第一間店開在市中心（全局重心），第二間刻意挑「離第一間最遠」的地方，第三間再挑「離前兩間都最遠」的地方。

【材料原文｜方案 B：K-means++（推薦）】
- 第一個中心：隨機選一個點 $\mu_1^{(0)}$
- 第 $j$ 個中心（$j = 2, \ldots, K$）：
  $$\mu_j^{(0)} = \text{按概率 } P(x_i) \propto D(x_i)^2 \text{ 選擇}, \quad D(x_i) = \min_{l < j} \lVert x_i - \mu_l^{(0)} \rVert$$
- 直觀：點到已選中心越遠，被選的概率越高，形成「散布」的初始中心。
- **理論保證：K-means++ 初始化的預期聚類成本 $\leq O(\log K)$ 倍最優解。**
- 實務：通常與 3-5 次重啟結合，能得到接近全域最優的結果。
- 白話：像發抽獎券——離現有分店越遠的地方，拿到的抽獎券就越多（中選機率越大）。

【材料原文｜方案 C：多次重啟（Random Restarts）】
$$\text{Best} = \arg\min_{r=1}^{R} G_r$$
```
Best_G ← ∞
FOR r = 1 to R:  // R 通常 = 10-100
  用隨機初始化執行 K-means
  得到結果 C_r 和目標函數值 G_r
  IF G_r < Best_G:
    Best_G ← G_r
    Best_C ← C_r
  END IF
END FOR
RETURN Best_C
```
- 推薦參數：$R = 10\text{–}100$（取決於計算預算）
- $R = 10$：覆蓋 99.99% 的情況；$R = 50$：幾乎找到全域最優
- 配合 K-means++：**K-means++ + 3 次重啟 通常足夠**
- 成本例：100 次重啟 × 每次 5 秒 = 500 秒 = 8 分鐘，但結果質量提升 50-80%

【材料原文｜三方案比較】

| 方案 | 成本 | 效果 | 推薦 |
|---|---|---|---|
| Heuristic | 低 | 中等 | 快速原型、實時系統 |
| K-means++ | 低-中 | 良好 | **生產系統（標準選擇）** |
| Random Restarts | 中-高 | 很好 | 離線分析、高質要求 |

---

## §6 分群品質評估（★ 任務問題 2）

### 6.1 兩大方向

【材料原文｜Notion Part 1 + 本機講義 §7.1】

**Internal Criterion（內部評估）**
- 定義：不需要外部真實標籤（ground truth），單純根據分群結果本身的特性進行評估。
- 衡量目標：群內相似度高（intra-cluster similarity），群間相似度低（inter-cluster similarity）。
- **代表指標：Silhouette coefficient、Davies-Bouldin Index、Calinski-Harabasz Index。**
- 優勢：無須人工標註，適合無監督情境，能快速評估不同參數下的分群效果。
- **侷限：高內聚的分群不一定符合業務需求。極端例子是把每個點都分成一群，內部評估分數完美但毫無意義。**

**External Criterion（外部評估）**
- 定義：存在預先標記好的真實類別標籤（gold standard），將分群結果與之比對。
- 衡量目標：分群結果是否能重現或逼近真實的類別結構。
- **代表指標：Purity、Rand Index、Adjusted Rand Index、Normalized Mutual Information。**
- 優勢：直接反映分群是否符合人類預期的分類概念。
- 侷限：需要大量人力標註，且真實標籤本身可能有歧義或不完善。

【材料原文｜投影片層級（前置整理 p.35–p.36）】
- p.35「What Is A Good Clustering?」內部準則：群內同質性高、群間差異大。同時提醒：**結果品質也依賴文件表示與相似度定義**。
- p.36「External criteria」若有 gold standard：可檢查 clustering 是否重現真實類別結構；可衡量是否找出 hidden patterns。

【材料原文｜白話說明】想像你在做電影分類。用 internal 評估，你只看你自己的分群邏輯是否合理；用 external 評估，你問朋友：「電影的真正類型應該是什麼？我分對了嗎？」**前者不需要標準答案但容易騙自己，後者麻煩但最真實。**

### 6.2 Purity（純度）— 外部指標

【材料原文｜定義】

設 $\Omega = \{\omega_1, \ldots, \omega_K\}$ 為分群產生的 $K$ 個 clusters，$C = \{c_1, \ldots, c_J\}$ 為真實的 $J$ 個 classes，樣本總數為 $N$：

$$purity(\Omega, C) = \frac{1}{N} \sum_{k=1}^{K} \max_{j \in \{1,\ldots,J\}} |\omega_k \cap c_j|$$

【材料原文｜計算步驟】
1. 統計每個 cluster 中各類別的樣本數，製作 $K \times J$ 的列聯表（contingency table）。
2. 每一行（每個 cluster）找出最大值。
3. 將最大值加總，再除以 $N$。

範圍：$0 \leq purity \leq 1$，1 表示完美純度。

【材料原文｜範例計算（講義版）】
```javascript
Cluster 1: 5個× + 2個o + 0個◇ = 7個樣本
Cluster 2: 0個× + 4個o + 3個◇ = 7個樣本
Cluster 3: 1個× + 0個o + 2個◇ = 3個樣本
```
- Cluster 1 最大值 = 5（`×` 類）；Cluster 2 最大值 = 4（`o` 類）；Cluster 3 最大值 = 2（`◇` 類）
$$purity = \frac{5 + 4 + 2}{17} = \frac{11}{17} \approx 0.647$$

【材料原文｜範例計算（投影片版，前置整理 p.38）】
- cluster 1 最多類別數 = 5；cluster 2 最多類別數 = 4；cluster 3 最多類別數 = 3
- $purity = (5+4+3)/17 \approx 0.71$

【評註｜數字不一致】兩份材料對同一張投影片給出不同的第三簇最大值（2 vs 3），因此 purity 分別為 0.647 與 0.71。**投影片原始版本應為 0.71（前置整理是逐頁對照原稿）**，講義版自己也註明「如果投影片的例子中數值不同，請用該數值代入」。寫 Skill 時用公式即可，不要引用這個例題數字。

【材料原文｜Purity 的三大限制與陷阱】
1. **偏好細碎分割**：若每個樣本都自成一群，purity = 1，但這樣的分群毫無意義。**Purity 會被極度細碎的分割人為拉高。**
2. **沒有懲罰機制**：不考慮 clusters 的個數；只要最多的類別佔多數就能獲得高分；不會因為 clusters 數量過多或過少而扣分。
3. **與 cluster 數量的依賴**：一般來說，cluster 數量越多，purity 越高。**必須搭配其他指標（如 Rand Index）綜合評估。**

【材料原文｜白話】如果我作弊，把每個學生單獨分一群，purity 當然是 100%，但這根本沒分出什麼東西。**所以 Purity 不能單獨用。**

### 6.3 Rand Index — 外部指標

【材料原文｜核心思想】從「兩兩樣本對」（pairwise perspective）的角度出發，看所有可能的樣本對在分群和真實類別上的「一致性」。

【材料原文｜四象限】給定 $N$ 個樣本，共有 $\binom{N}{2}$ 個樣本對：

| 樣本對類型 | 定義 | 說明 |
|---|---|---|
| A | 同類且同群 | 真實屬同一類，分群後也在同一群（True Positive） |
| B | 不同類但同群 | 真實屬不同類，分群後卻在同一群（False Positive） |
| C | 同類但不同群 | 真實屬同一類，分群後卻分到不同群（False Negative） |
| D | 不同類且不同群 | 真實屬不同類，分群後也分到不同群（True Negative） |

$$RI = \frac{A + D}{A + B + C + D} = \frac{A + D}{\binom{N}{2}}$$

【材料原文｜與 Precision/Recall 的對比】
$$P = \frac{A}{A+B}, \qquad R = \frac{A}{A+C}, \qquad F = \frac{2PR}{P+R}$$
而 Rand Index 同時考慮了正例和反例，**更全面但不夠敏感於特定錯誤類型**。

【材料原文｜範例計算】A=20, B=20, C=24, D=72：
$$RI = \frac{20 + 72}{20 + 20 + 24 + 72} = \frac{92}{136} \approx 0.676$$
$$P = \frac{20}{40} = 0.5, \qquad R = \frac{20}{44} \approx 0.455$$
（投影片版：前置整理 p.41 記錄最後算得 **RI = 0.68**，與 0.676 一致。）

範圍：$0 \leq RI \leq 1$，1 表示完美一致，**0.5 表示等於隨機猜測**。

【材料原文｜Purity vs Rand Index 比較表】

| 指標 | Purity | Rand Index |
|---|---|---|
| 評估角度 | 每個 cluster 的主導類別佔比 | 所有樣本對的判定一致性 |
| 計算方式 | 統計每個 cluster 最多的類別 | 比較所有樣本對在分群和真實類別上的一致 |
| 靈敏度 | 低；容易被大的主導類別拉高 | 高；考慮所有樣本對的關係 |
| **對碎片化的反應** | **會被細碎分割人為拉高** | **會降低（B 和 C 都會增加）** |
| 適用場景 | 快速評估 cluster 純度 | 綜合評估分群品質 |
| 範圍 | [0, 1] | [0, 1] |
| 理想值 | 1（每群完全純） | 1（所有樣本對一致） |

【材料原文｜白話】Purity 就像問「你每一隊裡的隊員背景是不是相近？」，但它不在乎你分了幾隊。Rand Index 則問「你把任意兩個人的分類都做對了嗎？」—— 本該在一隊卻分開（false negative）也是錯，不該在一隊卻混一起（false positive）也是錯。**所以 Rand Index 更嚴格。**

### 6.4 評估指標的使用時機（整合）

【評註｜教材只把 Silhouette / Davies-Bouldin 列名，沒給公式。以下時機表由教材原文邏輯整理，公式缺口見 §13】

| 情境 | 用哪一類 | 教材依據 |
|---|---|---|
| **沒有任何標籤**（一般顧客分群的真實情況） | Internal：CH Index（教材唯一給公式者）+ Elbow 視覺驗證 | 「不需要外部真實標籤，單純根據分群結果本身」 |
| **要選 K** | CH Index 取極大 | 「CH Index 是數學化、自動的」；Elbow 「靠人眼」 |
| **有既有分類可對照**（例如已有的會員等級、人工標的 persona、產品線） | External：Purity（快速）+ Rand Index（綜合） | 「存在預先標記好的真實類別標籤（gold standard）」 |
| **想確認分群沒有碎裂** | Rand Index（會因碎片化下降），**不要**用 Purity | Purity「會被細碎分割人為拉高」 |
| **想確認分群對業務有用** | 教材立場：內部指標高 ≠ 業務有用，必須加上可解釋性檢查與專家意見 | 「高內聚的分群不一定符合業務需求」 |

---

## §7 演算法分類座標系

### 7.1 維度一：Flat vs Hierarchical

【材料原文】

**Flat (Partitional) Clustering**：一次性將數據分成 $k$ 個互不重疊的簇。
- 輸出：$C = \{c_1, \ldots, c_k\}$；無層級關係；$c_i \cap c_j = \emptyset$；$\bigcup c_i = D$
- 代表算法：**K-means**（本課重點）、K-medoids、Fuzzy C-means、Expectation-Maximization (EM)
- 優點：算法簡單、計算快、易於並行化、適合大規模數據
- 缺點：必須預先指定 K；K 選擇困難

**Hierarchical Clustering**：遞迴地構建樹形結構（Dendrogram），呈現多個粒度的簇。
- 輸出：樹狀結構，不同高度對應不同 K 值；允許「簇的簇」存在
- 兩子型：
  1. **Agglomerative（凝聚）Bottom-up**：初始每點單獨成簇（$n$ 個簇）→ 每步合併最相似的兩個簇 → 全部合併成 1 個簇
  2. **Divisive（分裂）Top-down**：初始所有點在一個簇 → 每步選一個簇分裂成兩個 → 每點各自一簇
- 代表算法：Agglomerative Hierarchical Clustering、CURE、BIRCH
- 優點：無需預先指定 K（樹的任何高度都可切割）；樹狀結構提供豐富信息；可視化直觀
- 缺點：計算複雜度高（通常 $O(n^2)$ 以上）；**無法「反悔」（一旦合併就無法拆散）**；對大規模數據效率低

```
Flat：        所有點 → K-means → 簇1, 簇2, ..., 簇K

Hierarchical：樹根 ────┬──────┬─────┐
                      │      │     └─ 簇C
                      ├──┐   └─ 簇B
                      │  └─ 簇A
                   （可在任意高度切割）
```

### 7.2 維度二：Hard vs Soft Clustering（★ 任務問題 6）

【材料原文｜定義】

**Hard Clustering**：每個點明確屬於某一個簇，概率為 0 或 1。
$$c(d_i) \in \{1, 2, \ldots, k\} \quad \text{（唯一確定）}$$
- 代表：K-means、Hierarchical Clustering、DBSCAN（主要是 hard）
- 優點：結果清晰易解釋
- 缺點：**邊界點被迫分配到一個簇**

**Soft Clustering**：每個點以不同概率屬於多個簇。
$$P(c_j \mid d_i), \qquad \sum_{j=1}^{k} P(c_j \mid d_i) = 1$$
- 代表：**Gaussian Mixture Model (GMM)**、Fuzzy C-means、EM 算法
- 優點：更準確地表達不確定性、更細緻更現實
- 缺點：結果複雜，不易解釋；計算代價大（涉及概率優化）

【材料原文｜例子 1：學生】
```
Hard：John 屬於「文科生簇」（概率 100%）
Soft：John → 文科生簇 60% / 理科生簇 35% / 跨領域簇 5%
```
直覺：「John 主要是文科生，但有點理科天分，還有點跨領域興趣」——更細緻的描述。

【材料原文｜例子 2：Sneakers 運動鞋分類（投影片原例）】
```
鞋子 A：輕量級跑鞋、良好緩衝、可用於越野
Hard：要麼「跑步鞋」、要麼「越野鞋」——選哪個都不太對
Soft：跑步鞋 70% / 越野鞋 25% / 休閒鞋 5%
```
（前置整理 p.17 記：sneakers 可以同時屬於 sports apparel 與 shoes。）

【材料原文｜比較表】

| 特性 | Hard Clustering | Soft Clustering |
|---|---|---|
| 歸屬 | 唯一確定 | 概率分佈 |
| 公式 | $c(d) \in \{1,\ldots,k\}$ | $P(c_j \mid d)$ |
| 直覺 | 清晰、易理解 | 細緻、更現實 |
| 計算 | 快速 | 複雜（涉及概率優化） |
| 應用 | 初步分析、實時系統 | 深度分析、機率模型 |

【材料原文｜本課重點：Hard Clustering，四個理由】
1. 計算效率高：K-means 是實務中最常用的
2. 理論基礎扎實：容易推導、證明收斂性
3. 應用最廣：電商、新聞、推薦系統等多數用 K-means
4. 易於學習：Soft 聚類通常建立在 Hard 之上

【材料原文｜Topic Model 版的硬 vs 軟對照表（Notion Part 3）】

| 特徵 | 硬分群 | 軟分佈（Topic Model） |
|---|---|---|
| 歸屬 | 每篇文件屬於且僅屬於一個群 | 每篇文件以一定機率屬於多個主題 |
| 輸出 | 離散的群編號 | 連續的機率分佈 |
| 現實匹配度 | 較低（現實文件常多主題） | 較高（符合文件實際情況） |
| 可解釋性 | 直接（文件要嘛在群 A，要嘛在群 B） | 需要理解機率 |

【材料原文｜何時選用哪一種（Notion Part 3）】
- **選用 Hard Clustering**：需要快速部署、實時性要求高；分群結果易於溝通給非技術背景的人；資料確實分屬不同類別（如商品分類）。
- **選用 Topic Model / Soft**：追求語義深度與精細性；資料本質上是多主題混合（如文件）；計算資源充足，時間不緊；需要對每個資料的多維特性進行分析。
- 白話：硬分群像是「員工大會分組」——每個員工被分配到一個部門；Topic Model 像是「員工技能描述」——每個員工可能 30% 擅長市場行銷、50% 擅長產品開發、20% 擅長財務規劃。

【評註｜行銷選擇規則】
- 要**發廣告受眾包、做 A/B 測試分組、給業務團隊看的 persona** → Hard（K-means / Ward）。理由用教材原話：「分群結果易於溝通給非技術背景的人」。
- 要**建推薦模型特徵、算「這位顧客有多像 VIP」的傾向分數、處理跨品類重疊消費者** → Soft（GMM / LDA）。理由用教材原話：「邊界點被迫分配到一個簇」是硬分群的缺點。
- **教材只給 GMM 這個名字與「軟分群代表」的定位，沒有給 GMM 的公式、EM 步驟、共變異數矩陣型態（spherical/diagonal/full）或 BIC 選 K 的方法。**（見 §13 Gap）

### 7.3 維度三：密度聚類

【材料原文】
- 基於點的密度；算法：DBSCAN、OPTICS
- 特點：能識別任意形狀的簇，自動決定簇數
- 適用：點的分佈不規則，簇形狀複雜

---

## §8 DBSCAN（密度式分群）

### 8.1 核心思想

【材料原文】

DBSCAN（Density-Based Spatial Clustering of Applications with Noise）核心假設：

> **聚類是連通的高密度區域，不同聚類由低密度區域分隔開。**

- 「密度」通過兩個參數定義：半徑 $\varepsilon$（eps）和最小點數 $MinPts$。若半徑 $\varepsilon$ 內至少有 $MinPts$ 個點，該區域被視為「高密度」。
- 為什麼選 Density-Based？K-means 假設簇呈球形，對非凸（non-convex）形狀效果差；DBSCAN 不預設形狀，能發現任意形狀的聚類；能自然地識別和隔離噪音點。
- 代價：對 $\varepsilon$ 和 $MinPts$ 參數敏感。

【材料原文｜白話】想像一個很擁擠的人群。DBSCAN 的做法是：只要附近人夠多，我就認為這是一個「人群」；如果有人孤零零地站在一邊，那他就是「異常人士」（噪音）。K-means 則預先說「我要分成 5 群」，不管人群的實際密度如何都硬生生分割。

### 8.2 兩個參數

【材料原文】

**Eps-neighborhood（$\varepsilon$-鄰域）**：
$$N_\varepsilon(p) = \{q \in D \mid d(p, q) \leq \varepsilon\}$$

**MinPts**：一個正整數，表示判斷某區域為「高密度」的最低樣本數閾值。

- **Eps 太小**：大多數點會被判為噪音，很難形成大的簇。
- **Eps 太大**：多個簇會被錯誤地合併。
- **MinPts 太小（如 1）**：幾乎每個點都是 core，容易過度聚類。
- **MinPts 太大**：需要非常密集才能成為 core，容易產生過多噪音。
- 常見啟發式：$MinPts \geq \log(N)$ 或 $MinPts = 2 \times d$（$d$ 是數據維度）；也有 $MinPts \geq d + 1$。
- **兩參數需要聯動調整**：增大 Eps 通常也需要相應增大 MinPts，否則會過度聚類。

【材料原文｜白話】Eps 就是「我最多看周圍多遠的人」，MinPts 是「周圍至少要有多少人我才認為這裡很擁擠」。

### 8.3 三種點

【材料原文｜正式定義】

1. **Core Point（核心點）**：$|N_\varepsilon(p)| \geq MinPts$（$\varepsilon$-鄰域內至少 $MinPts$ 個點，包括自己）
2. **Border Point（邊界點）**：$|N_\varepsilon(q)| < MinPts$ 但 $\exists$ core point $p$ 使 $q \in N_\varepsilon(p)$
3. **Noise Point（噪音點）**：$|N_\varepsilon(r)| < MinPts$ 且不存在任何 core point $p$ 使 $r \in N_\varepsilon(p)$

【材料原文｜角色】
- Core points 是聚類的「骨幹」，通常位於簇的內部；DBSCAN 演算法主要圍繞 core points 展開。
- Border points 位於聚類的邊界，自己周圍不夠密集，但搭著某個 core point 的順風車進入聚類；**同一個 border point 可能鄰近多個不同簇的 core points（通常歸到先發現的那個簇）**。
- Noise points 是孤立或離群的點，不屬於任何簇。**DBSCAN 對噪音的魯棒性是相比 K-means 的重要優勢。**

```
        ××      ← core points（周圍多點）
       ×××
      ×××××
        × ←─  border point（周圍稀疏但靠近 core）

    ○ ←─────────  noise point（孤立）

       ◇◇
      ◇◇◇◇
       ◇◇
```

### 8.4 Density-Reachability 與 Density-Connectivity

【材料原文】

- **Directly Density-Reachable（直接密度可達）** $p \to q$ 當且僅當：(1) $p$ 是 core point；(2) $q \in N_\varepsilon(p)$
- **Density-Reachable（密度可達）**：存在序列 $p = p_0, p_1, \ldots, p_m = q$ 使得
  $$p_i \to p_{i+1}, \quad \forall i = 0, 1, \ldots, m-1$$
- **Density-Connected（密度連通）**：存在點 $o$ 使得 $p$ 和 $q$ 都相對於 $o$ 是 density-reachable。

**不對稱性（asymmetric）**：若 $p$ 是 core point、$q$ 在 $p$ 的 $\varepsilon$-鄰域內，則 $q$ directly reachable from $p$；但如果 $q$ 是 border point，$q$ 的 $\varepsilon$-鄰域內可能沒有足夠的點，所以 $p$ 可能 not directly reachable from $q$。

```javascript
p (core) ──直接可達───→ q (border)
         ← 不直接可達 ← (q不是core，不能進一步擴展)

p (core) ──→ m (core) ──→ q (border)
    └─────── 密度可達 ─────→
```

**簇被定義為 density-connected 的點的最大集合。**

【材料原文｜白話】直接密度可達是「我靠我的朋友圈直接認識你」；密度可達是「我靠朋友的朋友的朋友……最終能認識你」。**關鍵是中間必須經過夠密集的人圈（core points）才算，不能靠孤立的人（border or noise）傳遞。**

### 8.5 演算法流程

【材料原文｜偽碼】
```
Algorithm DBSCAN(D, ε, MinPts)
    Input: Dataset D, parameters ε and MinPts
    Output: A set of clusters and noise points

    C ← 0  // cluster counter

    for each point o in D:
        if o is already classified:
            continue

        N ← N_ε(o)  // ε-neighborhood of o

        if |N| < MinPts:
            mark o as NOISE
        else:
            C ← C + 1  // start a new cluster
            ExpandCluster(o, N, C, ε, MinPts)

Procedure ExpandCluster(o, N, C, ε, MinPts):
    assign o to cluster C

    for each point q in N:
        if q is NOISE:
            assign q to cluster C  // border point
        else if q is unclassified:
            assign q to cluster C
            N_q ← N_ε(q)
            if |N_q| ≥ MinPts:  // q is core point
                for each point p in N_q not yet classified:
                    add p to N  // expand the neighborhood
```

【材料原文｜關鍵設計】Core points 能互相連接形成連通的簇；**Border points 被納入但不進一步擴展（只有 core points 才能擴展）**；這樣自動決定了簇數，無需預先指定。

【材料原文｜範例計算（$\varepsilon=2$ cm，$MinPts=3$）】
```
初始狀態：
  A(0, 0)  B(0.5, 0)  C(1, 0)    ← 很靠近
  D(5, 5)  E(5.5, 5)  F(6, 5)    ← 很靠近
  G(10, 10)                       ← 孤立

Step 1：掃描 A → N_ε(A) = {A, B, C}，|N| = 3 ≥ MinPts
        A 是 core point → 開始 Cluster 1，將 A, B, C 加入
Step 2-3：B、C 已分類，skip
Step 4：掃描 D → N_ε(D) = {D, E, F}，|N| = 3 ≥ MinPts
        D 是 core point → 開始 Cluster 2，將 D, E, F 加入
Step 5-6：E、F 已分類，skip
Step 7：掃描 G → N_ε(G) = {G}，|N| = 1 < MinPts → 標記為 NOISE

結果：Cluster 1 = {A, B, C}，Cluster 2 = {D, E, F}，Noise = {G}
```

複雜度：最壞 $O(N^2)$；用空間索引（如 KD-tree）可優化至 $O(N \log N)$。

### 8.6 優缺點

【材料原文｜優點】
1. **不需要預先指定簇數**：避免了 K 的猜測和調參成本。
2. **能識別和隔離噪音**：自動標記孤立或離群的點為噪音，比 K-means 處理異常值時更魯棒。
3. **發現任意形狀的簇**：不限於球形簇，適應新月形、環形等複雜形狀。
4. **時間複雜度可接受**：用適當的空間索引可達 $O(N \log N)$。

【材料原文｜缺點】
1. **對參數敏感**：Eps 和 MinPts 的選擇直接影響結果；參數估計困難，需要多次嘗試或領域知識。
2. **密度不均時表現受限**：如果數據內部密度差異大，單一 Eps 和 MinPts 難以適應。
3. **高維數據上失效**：在高維空間中，距離度量的區分力下降（維度詛咒）；**Eps-鄰域的概念變得不清晰**。
4. **邊界點的歸屬模糊**：Border point 可能同時鄰近多個簇，歸屬不唯一；實現上通常按「先到先得」原則。

【材料原文｜投影片 p.51 When DBSCAN Works Well】兩大優勢：resistant to noise；can handle clusters of different shapes and sizes。

### 8.7 如何決定 Eps 與 MinPts：k-distance Graph

【材料原文｜方法步驟】
1. 對數據集中的每個點 $p$，找出距離它最近的 $k$ 個點（其中 $k = MinPts - 1$），記錄第 $k$ 個最近鄰點到 $p$ 的距離 $d_k(p)$。
2. 將所有 $d_k(p)$ 排序後繪圖（距離為縱軸，點的編號為橫軸）。
3. 尋找拐點（elbow）：簇內的點通常有較小的 k-近鄰距離；噪音或邊界的點會有明顯較大的 k-近鄰距離；**曲線從平緩上升突然陡峭上升的地方（肘部）就是 Eps 的候選值**。

```
距
離
 │         ╱╱╱╱╱ ← 噪音點（距離突增）
 │      ╱╱╱
 │    ╱╱        ← Eps 參考值（在肘部）
 │  ╱╱
 │╱╱   ← 簇內點（距離平緩）
 └─────────────────
   點的索引
```

【材料原文｜缺點與補救】曲線可能有多個較明顯的肘部，需要領域知識判斷；密度不均的數據難以找到理想的單一 Eps；補救：可嘗試多個 Eps 值，或使用自適應的密度估計方法。

【材料原文｜實作建議】
- 先用 $MinPts = 2 \times d$（$d$ 為維度）作為起點
- 繪製 k-近鄰距離圖，尋找肘部
- 在肘部前後多試幾個 Eps 值，觀察簇的變化
- **根據業務需求調整（寧願多噪音，也別強行合併不同簇）**

### 8.8 DBSCAN vs K-means（完整比較表）

【材料原文｜簡易版】

| 特性 | K-means | DBSCAN |
|---|---|---|
| 群的形狀 | 傾向凸形、球狀 | 任意形狀 |
| 群的數量 | 需事先指定 K | 自動決定 |
| 離群點處理 | 硬分配到某群 | 標記為 noise |
| 參數 | K（相對直觀） | Eps、MinPts（較難調） |
| 高維表現 | 中等 | 較差 |
| 計算複雜度 | $O(IKnm)$，迭代式 | $O(n^2)$，最簡實作 |
| 收斂性 | 保證收斂（局部最優） | 決定式完成 |

【材料原文｜詳細版】

| 維度 | K-means | DBSCAN |
|---|---|---|
| 核心思想 | 最小化類內方差；最近聚類中心 | 密度連通；高密度區域聚類 |
| 簇的假定 | 球形、大小相近、密度均勻 | 任意形狀、可不同密度 |
| 簇數決定方式 | 必須預先指定 K | 自動發現，無需指定 |
| 噪音處理 | 所有點必須歸到某個簇 | 自動識別和隔離噪音點 |
| 參數調整 | 只需調 K（通常用 Elbow 法或 Silhouette） | 需調 Eps 和 MinPts（k-近鄰距離圖） |
| 參數敏感度 | 中等（K 的選擇很重要） | 高（Eps 和 MinPts 都重要且聯動） |
| **高維數據表現** | **尚可（距離仍有區分力）** | **差（距離度量失效，維度詛咒）** |
| 時間複雜度 | $O(nkT)$ | $O(n^2)$ 或 $O(n \log n)$（有索引） |
| 空間複雜度 | $O(n + k)$ | $O(n)$（可能含索引結構） |
| 適用場景 | 數據分佈相對均勻、簇大小接近、K 已知 | 簇形狀複雜、存在噪音、K 未知 |
| 實現難度 | 簡單；易於並行化 | 中等；需要距離查詢優化 |
| 可解釋性 | 高；簇中心直觀 | 中等；密度概念需解釋 |
| 典型應用 | 圖像分割、**客戶分群**、初步探索 | 地理坐標聚類、**異常檢測**、複雜形狀發現 |

【材料原文｜思路對比】K-means 是「距離驅動」（distance-driven）；DBSCAN 是「密度驅動」（density-driven）。各有側重，不是絕對好壞。

【材料原文｜參數調整難度】K-means：K 的選擇影響大但邏輯清晰（更多聚類 vs 更少聚類）。DBSCAN：**Eps 和 MinPts 聯動，組合爆炸，調參更複雜。**

【評註｜行銷】DBSCAN 在顧客分群的真正用途通常不是「主分群方法」，而是**先找出離群顧客**（極端高消費、機器人帳號、批發轉售者），把 noise 撈掉之後再跑 K-means/Ward。理由取自教材：K-means「異常值敏感性高（會被吸入最近的群）」、「噪音點視為普通點，可能拉偏群心」。

---

## §9 階層式分群 HAC（含 Ward 的理論位置）

### 9.1 基本概念

【材料原文】

階層式分群透過建立樹狀結構（**dendrogram**），將資料點逐步組織成巢狀的群。不同於 K-means，**無需事先指定群數，可在樹的任意高度進行「橫切」**。

$$\text{Dendrogram} = \text{樹狀結構，記錄資料點與群的逐步合併或拆分過程}$$

三大優勢：
1. **樹狀結構**：整個分群過程完整記錄在一棵樹上，葉節點是原始資料點，每次合併時產生內部節點，高度反映相似度或距離。
2. **多層次選擇**：使用者可在任意高度取一條水平線，線下仍保持連通的部分自動形成分群結果。
3. **不需事先決定 K**：只需在事後根據 dendrogram 形狀選擇最適切的高度。

### 9.2 Agglomerative vs Divisive

【材料原文】

$$\text{Agglomerative: } n \text{ clusters} \to n-1 \to \cdots \to 1$$
$$\text{Divisive: } 1 \text{ cluster} \to 2 \to \cdots \to n$$

- **Agglomerative（凝聚 / Bottom-up）**：實作更簡單——只需重複計算最近的兩群並合併；每次合併時只需更新該兩群與其他群的距離，無須重新計算全局。實務上被廣泛採用。
- **Divisive（分割 / Top-down）**：計算更複雜——每次需決定如何最優地分割一個群；**第一次分割決定了樹的整體結構，若第一步就分得不好，後續很難補救**；學術上研究較少，實務應用較罕見。

本講義以 **HAC (Hierarchical Agglomerative Clustering)** 為主軸。

### 9.3 HAC 演算法

【材料原文｜正式演算法】
```
輸入：n 筆資料點，相似度/距離函數 sim(·,·) 或 dist(·,·)，連結方法 Linkage
輸出：dendrogram

步驟：
1. 初始化：令每筆資料點 x_i 各自成為一個單點群 c_i
2. 迴圈直到只剩 1 個群：
   (a) 在所有現存的群對 (c_i, c_j) 中，找出相似度最高的（或距離最小的）
   (b) 合併這兩個群：c_new = c_i ∪ c_j
   (c) 記錄合併事件到樹中，該節點高度代表 sim(c_i, c_j) 或 dist(c_i, c_j)
   (d) 刪除原 c_i 與 c_j，加入 c_new
   (e) 根據所選 Linkage 方法，更新 c_new 與其餘所有群的距離
```

關鍵：**貪心選擇**（在所有可能的群對中選擇「最接近」的一對，「最接近」的定義取決於 Linkage 方法）。

### 9.4 四種 Linkage 方法

【材料原文｜(a) Single-link（最近鄰法 / Min-link）】
$$\text{sim}(c_i, c_j) = \max_{x \in c_i, y \in c_j} \text{sim}(x, y) \qquad \text{dist}(c_i, c_j) = \min_{x \in c_i, y \in c_j} \text{dist}(x, y)$$
更新規則：
$$\text{sim}((c_i \cup c_j), c_k) = \max(\text{sim}(c_i, c_k), \text{sim}(c_j, c_k))$$
- 只看「最接近的橋樑」。
- **Chaining Effect（鏈條效應）**：即使 $c_i$ 的主體與 $c_j$ 的主體相距甚遠，只要邊緣點剛好接近，這兩個本應獨立的群就會被合併，導致形成長而鬆散的「鏈條狀」群。
- 白話：「只要能牽手，就認為你們是一群」。

【材料原文｜(b) Complete-link（最遠鄰法 / Max-link）】
$$\text{sim}(c_i, c_j) = \min_{x \in c_i, y \in c_j} \text{sim}(x, y) \qquad \text{dist}(c_i, c_j) = \max_{x \in c_i, y \in c_j} \text{dist}(x, y)$$
更新規則：
$$\text{sim}((c_i \cup c_j), c_k) = \min(\text{sim}(c_i, c_k), \text{sim}(c_j, c_k))$$
- 只看「最遠的橋樑」——即使是最遠的點對也要滿足相近的條件。
- **優點**：形成較緊密、較球狀、更符合人們直覺的群。
- **缺點**：計算成本較高，且對異常值敏感（一個遠離群心的異常點會大幅降低相似度評分）。
- 白話：「只有全部人都牽上手，才認為你們是一群」。

【材料原文｜(c) Centroid-link】
$$\text{dist}(c_i, c_j) = \text{dist}(\bar{x}_i, \bar{x}_j), \qquad \bar{x}_i = \frac{1}{|c_i|} \sum_{x \in c_i} x$$
合併後新質心：
$$\bar{x}_{\text{new}} = \frac{|c_i| \cdot \bar{x}_i + |c_j| \cdot \bar{x}_j}{|c_i| + |c_j|}$$
- 特點：群的「中心位置」是主要考量，邊緣點影響較小；質心可能不是實際存在的資料點（**虛擬點問題**）。
- **倒轉問題（Inversion）**：有時會出現新合併的群反而比先前的群更近，導致 dendrogram 在某處出現「V 形」的異常。
- 白話：這就像說「兩個班級的平均身高」反而比某個班級的身高更「高」，感覺不太對勁。

【材料原文｜(d) Average-link（平均鄰法 / UPGMA）】
$$\text{dist}(c_i, c_j) = \frac{1}{|c_i| \cdot |c_j|} \sum_{x \in c_i} \sum_{y \in c_j} \text{dist}(x, y)$$
更新規則：
$$\text{dist}((c_i \cup c_j), c_k) = \frac{|c_i| \cdot \text{dist}(c_i, c_k) + |c_j| \cdot \text{dist}(c_j, c_k)}{|c_i| + |c_j|}$$
- 在 Single-link 和 Complete-link 之間取得平衡：不像 Single-link 那麼容易出現鏈條效應；不像 Complete-link 那麼敏感於異常值。
- 對所有點對進行「民主投票」，較為穩健。
- 也稱為 **UPGMA (Unweighted Pair Group Method with Arithmetic Mean)**，在實務上應用廣泛。

【材料原文｜Single-link vs Complete-link 比較表】

| 面向 | Single-link | Complete-link |
|---|---|---|
| 距離定義 | $\min_{x,y} \text{dist}(x,y)$ | $\max_{x,y} \text{dist}(x,y)$ |
| 群形狀 | 易出現長鏈狀、不規則 | 傾向球狀、緊密 |
| Chaining Effect | 嚴重 | 不存在 |
| 對異常值敏感性 | 低（單點不影響大局） | 高（邊緣點決定距離） |
| 計算複雜度 | $O(n^2)$ | $O(n^2)$ |
| 實務偏好 | 不常用 | 常用於想要緊密球狀群的場景 |
| 適用情境 | 想要發現任意形狀的群結構；對鏈條無所謂 | 想要緊密、高品質的群；對形狀有偏好 |

【材料原文｜投影片 p.62】列出四種 linkage 定義：single-link（最近點）、complete-link（最遠點）、centroid（重心）、average-link（平均）。**這一頁是 HAC 最核心的設計選擇頁。**

### 9.5 Ward 在教材中的位置（★ 任務要求：HW8 的理論依據）

【材料原文｜這是教材對 Ward 的**全部**內容，出現在「推薦延伸閱讀」】

> **經典文獻**
> - Ward, J.H. (1963). "Hierarchical Grouping to Optimize an Objective Function"
> - Blei et al. (2003). "Latent Dirichlet Allocation"

【評註｜必須誠實標示】**教材（L4 講義、前置整理、Notion 三個 Part）沒有講 Ward linkage 的公式、目標函數或性質，只在延伸閱讀列出 Ward 1963 的原始論文標題。** 教材列的四種 linkage 是 single / complete / centroid / average，**不含 Ward**。

【評註｜可用教材推出的 Ward 理論依據（供 IB5082 HW8 論述，但要標明是推論不是教材原文）】
Ward 1963 論文標題本身即說明其方法論本質：「Hierarchical Grouping to **Optimize an Objective Function**」——即在階層合併的每一步，選擇讓某個目標函數增量最小的合併。當該目標函數取 K-means 的 WGSS（群內平方和 $\sum_k \sum_{x_i \in c_k}\lVert x_i - \mu_k\rVert^2$，見 §5.3、§4.2）時，Ward 就是「階層版的 K-means」。因此可以用教材已有的三塊材料串出 HW8 的理論依據：
1. **Ward 與 K-means 目標函數同源**：教材已把 WGSS/RSS/G 定義清楚（§5.3、§4.2），Ward 的目標函數即此式；所以「先用 Ward 定 K、再用 K-means 精修」在目標函數上是一致的，不是兩套互相矛盾的準則。
2. **Ward 產生的群形狀偏好**：教材說 Complete-link「形成較緊密、較球狀」；Ward 因為最小化群內變異，同樣屬於**球狀偏好**的 linkage，與 K-means 的球形假設相容。這也是 HW8 把 K-means 與 Ward 並列的原因。
3. **Ward 的階層優勢**：教材對 HAC 的三大優勢（樹狀結構、多層次選擇、不需事先決定 K）與「若資料點數不超過數千，HAC 的成本是可接受的，而且不需事先決定 K 的優勢往往值得付出的代價」直接適用於 Ward。

【評註｜Two-step clustering 的位置】**教材完全沒有提到 SPSS 的 Two-step / 2-step clustering。** 能從教材推出的最接近論證是：
- 教材的階層 vs 平面比較（§7.1）指出 HAC 的致命傷是 $O(n^2 \log n) \sim O(n^3)$ 時間與 $O(n^2)$ 空間，「無法直接擴展至超大規模」；而 K-means 是 $O(I K n m)$，可擴展。
- Two-step 的設計正是先用可擴展的預聚類（類似 K-means/BIRCH 式的 CF-tree 壓縮）把 $n$ 降成數百個 sub-cluster，再在 sub-cluster 上跑 HAC——**用教材的話說，就是「先用 flat 解決 scalability，再用 hierarchical 取得不需預設 K 與多粒度切割的好處」**。
- 教材另有 Mini-batch K-means（§5.7）與「增量 K-means：一次只處理數據子集」的優化策略，可作為「兩階段設計」思想的教材佐證。
- **請務必標註：這是從教材原理推出的合理化論證，不是教材原文。**

### 9.6 HAC 計算複雜度

【材料原文】
1. **初始距離矩陣計算**：$O(n^2 \cdot d)$（$d$ 是特徵維度）
2. **主迴圈**：外層執行 $n-1$ 次；每次找最近群對 $O(n^2)$；若採用適當的資料結構（如優先隊列）可優化至 $O(n^2 \log n)$
3. **總體複雜度**：$O(n^2 \log n)$ 或 $O(n^3)$（取決於實作細節）
4. **空間複雜度**：$O(n^2)$（存儲距離矩陣）

【材料原文｜實務尺度】若有 1000 個資料點，距離矩陣約 100 萬個元素；若有 10000 個點，就是 1 億個元素。**HAC 最適合處理「幾百到幾千」規模的資料。若資料太多（幾十萬級），可能得考慮採樣或其他更快的演算法。**

相比 K-means 的 $O(n \cdot K \cdot iter \cdot d)$，HAC 在高維度、大規模資料集上會更加耗時。**然而，若資料點數不超過數千，HAC 的成本是可接受的，而且不需事先決定 $K$ 的優勢往往值得付出的代價。**

### 9.7 Dendrogram 的解讀與切割

【材料原文】
- **縱軸**：代表合併時的距離。高度越低 = 兩群越相似，高度越高 = 較遠距離下的合併。
- **橫軸**：資料點的排列，通常依據樹的結構優化讓相近的點在視覺上也較靠近。

**如何切割 Dendrogram 決定群數？**
- 在某個高度用一條水平線切下去。
- 切線與樹相交的線段數，就是最終群數。
- **若想要 $K$ 群，就在第 $(n - K)$ 次合併的高度切。**
- 例：假設一次合併高度為 0.5，另一次為 0.8 → 在高度 0.6 切得到兩個群；在高度 0.9 切得到一個群。

【材料原文｜白話】Dendrogram 就像一份「分群歷史書」。你可以在任何一頁「翻書停止」，看那一刻對應的群結構。在合併很密集的地方切 → 多個小群；在合併很疏散的地方切 → 少數大群。

【評註｜行銷】Dendrogram 切割高度就是 K 的另一種決定方法（教材的第四種方法，但沒有被放進 §4 的 K 決策表）：**看「合併距離的跳躍」——在某次合併距離突然變大之前切**，邏輯與 Elbow 完全同構。

---

## §10 群代表、特徵篩選與標籤化（分群之後的工作）

### 10.1 Centroid 的侷限

【材料原文】

$$\bar{c} = \frac{1}{|c|} \sum_{x \in c} x$$

**問題 1：非真實點（Non-existent Point）**
- 質心通常是個向量，但不一定對應任何真實存在的資料點。
- 若資料是離散的（如文件、商品），質心可能無法在現實中找到對應物。

**問題 2：高維空間的密度問題（典型性問題 Typicality Problem）**
- 在高維空間中，質心往往落在數據的「主要濃聚區」，但個別資料點由於**維度詛咒**反而呈現 sparse（稀疏）分佈。
- 結果：質心周圍可能沒有真正的資料點聚集，是個「虛幻」的點。

**問題 3：異常值敏感性**
$$\bar{c}_{\text{old}} = \frac{1}{n} \sum_{i=1}^{n} x_i$$
$$\bar{c}_{\text{new}} = \frac{1}{n+1} \sum_{i=1}^{n+1} x_i = \frac{n}{n+1} \bar{c}_{\text{old}} + \frac{1}{n+1} x_{\text{outlier}}$$
當 $x_{\text{outlier}}$ 離 $\bar{c}_{\text{old}}$ 很遠時，新質心會被「拉」向異常點方向。

具體例子：若群是 100 篇討論「籃球」的文章，質心指向籃球議題的核心；突然加入 1 篇「核能安全」的文章 → 新質心會向「核能」方向偏移。

【材料原文｜投影片 p.70】可在計算 centroid 時忽略 outlier；outlier 可定義為距中心過遠之點。

### 10.2 Medoid：更好的群代表

【材料原文｜兩種定義】
$$\text{medoid}(c) = \arg\min_{x \in c} \lVert x - \bar{c} \rVert$$
或更直接地，是與其他群內所有點「距離和最小」的點：
$$\text{medoid}(c) = \arg\min_{x \in c} \sum_{y \in c} \text{dist}(x, y)$$

**優勢**：
1. **真實存在**：Medoid 必然是資料集中的某個真實點，可以被直接展示、引用、或用其特徵來標記群。
2. **更穩健**：相比質心，Medoid 對異常值敏感度較低。
3. **適合離散資料**：對於文件、商品、基因序列等本質上離散的資料，Medoid 比虛擬質心更有意義。
4. **適合使用者展示**：向業務人員或最終使用者說「第一群由這 50 篇文章代表，代表文章是這篇」遠比說「第一群由這個虛擬質心代表」更容易理解。

**劣勢**：計算更昂貴（需計算所有點到所有其他點的距離）；限定為資料集中的某個點，可能不如質心「最優」。

【評註｜行銷】這是「代表性顧客 / 典型客戶檔案」的方法論依據：不要用群平均值編一個不存在的假人（平均年齡 34.7 歲、平均客單 1,283 元），而要挑出**真實存在的 medoid 顧客**當 persona 的原型。教材原話：「向業務人員說『代表文章是這篇』遠比說『虛擬質心』更容易理解。」

### 10.3 Feature Selection

【材料原文｜四種方法】
1. **TF-IDF**：詞在某文件中的頻率乘以它在整個語料庫中的「稀有度」；「the」、「and」等停用詞的 IDF 極低，被自動降權。
2. **文檔頻率（Document Frequency）閾值**：若某詞只出現在 1 或 2 篇文件中，對分群的通用性太弱，可刪除；若某詞出現在 95% 的文件中，區辨性也很弱，也可刪除。**通常保留出現在 5% 至 95% 文件的詞。**
3. **互信息（Mutual Information）**：衡量詞與文件類別的依存關係。
4. **卡方檢驗（Chi-square Test）**：統計該詞的出現與類別標籤之間是否獨立。

**為什麼要做 Feature Selection？**
- **降低維度**：減少計算量，加快分群演算法
- **去除噪聲**：刪除不相關的詞，提升信號質量
- **提升可解釋性**：保留的詞更能直觀解釋群的含義

【材料原文｜投影片 p.73】IDF 可視為 feature selection；可只取較有鑑別力的詞，例如名詞 / 名詞片語。

### 10.4 Labeling（群命名）

【材料原文｜標籤來源】
1. **代表文件的標題或關鍵特徵**（用 Medoid 的標題片段）
2. **該群最顯著的詞/片語（Top Terms）**
3. **避免只看高頻詞的陷阱**：應改用**群特異詞（Cluster-specific Terms）**——只在這個群高頻，在其他群罕見的詞
4. **有區辨力的詞才是好標籤**：
   $$\text{salience}(\text{term}, \text{cluster}) = \frac{\text{freq}(\text{term}, \text{cluster})}{\text{freq}(\text{term}, \text{all})} \times \text{freq}(\text{term}, \text{cluster})$$
   高顯著性的詞就是好標籤。

【材料原文｜Computer 陷阱的完整例子】
```
群 A：{論文 1-50}   內容：深度學習、神經網絡、CNN、RNN、機器學習
                    高頻詞：computer, learning, network, deep, model
群 B：{論文 51-100} 內容：量子計算、算法複雜度、計算理論
                    高頻詞：computer, algorithm, complexity, quantum, theory
群 C：{論文 101-150}內容：作業系統、編譯器、進程管理
                    高頻詞：computer, system, process, kernel, memory

若三個群都標記為「Computer」，就沒有區辨性。應該用：
  群 A：「深度學習」（特異詞：learning, deep, neural）
  群 B：「量子計算」（特異詞：quantum, complexity）
  群 C：「系統軟體」（特異詞：system, kernel, OS）
```

【材料原文｜投影片 p.77 Labeling heuristics】常用 heuristic：列出 centroid vector 中最常見的 5-10 個詞；但若整體集合共享某些高頻詞，則要做 **differential labeling**；因此真正要挑的是鑑別力高的詞。

【評註｜行銷｜這是 persona 命名的黃金規則】「Computer 陷阱」直接對應行銷分群最常見的失敗：五個群的 top feature 都是「年齡 30-45」「都會區」——因為那是**整體樣本的共同特徵**，不是群的特徵。正確做法是算 **差異化指標**（群內佔比 ÷ 全體佔比 = index/lift），只挑 index 明顯偏離 100 的變數來命名。教材的 salience 公式就是這個 index 的一種寫法。

### 10.5 分群不是終點

【材料原文｜Notion Lecture 4 主頁「分群不是終點」】
真正的應用還要處理：
- **Feature selection**：選出有鑑別力的詞。
- **Cluster labeling**：給群命名，讓人能理解。
- **Representative documents**：找到典型文件作代表。
- **使用者可理解性**：確保分群結果能實際應用。

【材料原文｜可解釋性的正反例（本機講義 §3.4）】

無解釋性的結果：
```
簇1：30 篇文件   簇2：25 篇   簇3：45 篇   簇4：20 篇   簇5：80 篇
```
用戶會問：「這些簇分別是什麼主題？」無法回答。

有解釋性的結果：
```
簇1（政治）：30 篇 → 高頻詞：election, vote, parliament
簇2（運動）：25 篇 → 高頻詞：game, score, team
簇3（娛樂）：45 篇 → 高頻詞：movie, actor, celebrity
簇4（科技）：20 篇 → 高頻詞：AI, software, algorithm
簇5（財經）：80 篇 → 高頻詞：stock, profit, investment
```

【材料原文｜Notion Part 1 可解釋性的反面/正面例子】
- **反面例子**：聚類成 100 個大小為 1～10 的碎片 → 無法解釋。
- **正面例子**：聚類成 8 個簇，每個 50+ 篇文件，簇內詞彙高度相關 → 易於理解。

【材料原文｜達成可解釋性的四種方法】
1. 查看簇中心（對文本，分析簇中心的 Top-K 高權重詞）
2. 簇成員特徵分析（隨機檢視簇中的 5-10 個成員，找共同特徵）
3. 使用易解釋的算法（Hierarchical Clustering 有樹狀結構；K-means 簇中心具體）
4. 標注簇名稱（自動提取高頻詞作簇標籤）

---

## §11 主題模型（軟分群的延伸）

### 11.1 定義

【材料原文】

$$\text{Document} = \sum_{t=1}^{T} \theta_{d,t} \times \text{Topic}_t$$

- $T$ 是主題總數
- $\theta_{d,t}$ 是文件 $d$ 對主題 $t$ 的權重，$0 \leq \theta_{d,t} \leq 1$，$\sum_t \theta_{d,t} = 1$
- $\text{Topic}_t$ 由詞彙分佈 $P(\text{word} \mid \text{topic}_t)$ 描述

工作流程：1. 初始化（隨機設定 $T$ 個主題）→ 2. 反覆推理（調整 $\theta_{d,t}$ 與 $P(w|t)$）→ 3. 收斂 → 4. 解釋（對每個主題提取高概率詞彙）。

### 11.2 LSA / pLSA / LDA

【材料原文｜LSA】
- 原理：使用奇異值分解（SVD）對詞-文件矩陣進行降維
  $$\mathbf{A}_{m \times n} = \mathbf{U}_{m \times k} \Sigma_{k \times k} \mathbf{V}_{n \times k}^T$$
  （$m$ = 詞彙量，$n$ = 文件數，$k$ = 主題數/選定的低秩）
- 優點：計算快速（只需 SVD）；直接的線性代數方法
- 缺點：假設主題詞彙分佈遵循高斯分佈，與實際詞頻分佈（冪律分佈）不符；無法處理概率，**結果可能出現負值**
- 適用：快速進行初步的潛在語義探索

【材料原文｜pLSA】
- 生成過程：對於文件 $d$，從分佈 $P(z|d)$ 抽樣一個主題 $z$；從該主題的詞彙分佈 $P(w|z)$ 抽樣一個詞 $w$
- 學習方法：**EM 演算法**
- 優點：概率框架，結果有明確的概率解釋
- 缺點：**參數眾多（$K \times m + n \times K$ 個），易過擬合**；無法有效處理新文件（語料庫外的文件）
- 適用：中等規模語料，追求概率嚴謹性

【材料原文｜LDA】
- 生成過程：從狄利克雷分佈 $\text{Dir}(\alpha)$ 抽樣文件-主題分佈 $\theta_d$；對每個詞位置 $i$：從 $\theta_d$ 抽樣主題 $z_i$，從 $\text{Dir}(\beta)$ 得到的主題-詞分佈 $\phi_z$ 抽樣詞 $w_i$
- 參數：超參數 $\alpha, \beta$（控制分佈的稀疏性）；隱變數 $\theta_d, \phi_z$
- 學習方法：**吉布斯采樣（Gibbs Sampling）或變分推斷（Variational Inference）**
- 優點：貝葉斯框架不易過擬合；**能有效推導出新文件的主題分佈（外推性好）**；結果更穩定，更被業界接納
- 缺點：計算複雜；超參數選擇需經驗調試
- 適用：大規模語料，需要高品質與可靠推導，時間允許的情況

【材料原文｜LSA → pLSA → LDA 演進比較表】

| 面向 | LSA | pLSA | LDA |
|---|---|---|---|
| 框架 | 線性代數（SVD） | 機率（EM） | 貝氏機率（採樣/變分） |
| 過擬合風險 | 低 | 高（參數多） | 低（有先驗） |
| 外推性 | 無（只適用已知文件） | 弱 | 好 |
| 計算速度 | 快 | 中 | 慢（採樣） |
| 結果解釋 | 可含負值 | 機率分佈 | 機率分佈 |
| 主流度 | 已過時 | 已過時 | **目前標準方法** |

【材料原文｜Topic Model vs Hard Clustering】

| 維度 | Hard Clustering | Topic Model |
|---|---|---|
| 模型假設 | 每個資料點只屬於一個簇 | 每個資料點由多個隱藏變數混合組成 |
| 出力形式 | 離散的簇編號 | 連續的概率分佈 |
| 應用例 1 | 用戶興趣分類：每個用戶 → 一個興趣群體 | 用戶興趣分類：每個用戶 → 多個興趣的比例 |
| 應用例 2 | 新聞聚類：每篇新聞 → 一個主題 | 新聞分析：每篇新聞 → 多個主題的混合 |
| 可解釋性 | 直接易懂 | 需要概率背景 |
| 計算成本 | 快速 | 較慢 |
| 適用場景 | 簡化問題、快速得結果 | 需要更精細的語義分析 |

【評註｜行銷】LDA 在行銷的兩個直接用途：(1) **開放式問卷 / 評論 / 客服對話的主題萃取**，比 K-means 分文件更適合，因為一則評論常同時抱怨物流又稱讚商品；(2) **顧客的「品類偏好組合」建模**——把顧客當文件、品類當詞，LDA 給出的 $\theta_{d,t}$ 就是「這位顧客 40% 母嬰、30% 生鮮、30% 美妝」，比硬分群更適合當推薦系統的特徵。

---

## §12 三演算法總比較（教材最終版，直接可用）

【材料原文｜Notion Lecture 4 主頁「各方法適用場景」＋本機講義 §13，兩處內容一致】

| 比較項目 | K-means | DBSCAN | HAC |
|---|---|---|---|
| **分群思路** | 迭代最小化類內變異數，逐步移動群心 | 密度連通性：相鄰密集點自動成群，低密度點為噪音 | 由下而上逐步合併最近的兩群，形成樹狀結構 |
| **需要事先決定 K** | 是（必須） | 否（無需） | 否（可在樹狀圖上任意切割） |
| **群形狀偏好** | 傾向球狀 | 任意形狀 | 取決於 Linkage；Complete-link 傾向球狀 |
| **雜訊點處理** | 視為普通點，拉偏群心 | 標記為雜訊，不納入任何群 | 視為普通點，被強制分配 |
| **異常值敏感性** | 高 | 低 | 中（Complete-link 時較敏感） |
| **時間複雜度** | $O(n \cdot K \cdot \text{iter} \cdot d)$ | $O(n^2)$ 或 $O(n \log n)$ | $O(n^2 \log n)$ 至 $O(n^3)$ |
| **空間複雜度** | $O(n \cdot d + K)$ | $O(n)$ | $O(n^2)$ |
| **可視化結果** | 群心位置；需額外工具 | 散佈圖，雜訊點獨立標記 | Dendrogram，直觀展示合併過程 |
| **實作難度** | 簡單 | 中等 | 中等 |
| **參數調試** | 選 K（最難）；初值敏感 | 選 $\epsilon$ 與 MinPts | 選 Linkage 方法；無敏感超參數 |
| **優點** | 快速；簡單易實現；可擴展 | 無需預設 K；任意形狀；穩健 | 完整樹狀視圖；多粒度切割；無敏感參數 |
| **缺點** | 需預設 K；球形偏好；異常值敏感 | 參數敏感；大規模較慢；密度不均 | 計算昂貴；無法超大規模；Linkage 影響大 |
| **適用情境** | 大規模；已知或可估計 K；追求效率 | 探索性；群形狀未知；需識別雜訊 | 小至中規模；需多粒度視角；群數不確定 |
| **實際應用例** | 線上推薦（用戶分群）；**客戶細分** | 異常檢測；空間聚類；密度異質 | 文件聚類；生物系統樹；層級化組織 |
| **軟體/套件** | scikit-learn: `KMeans` | scikit-learn: `DBSCAN` | scikit-learn: `AgglomerativeClustering`；scipy: `linkage` |

【材料原文｜三演算法的角色定位（Notion Lecture 4 主頁）】

**K-means 的角色**
- 最常見 baseline。
- 依賴 centroid（重心）。
- 需要事先決定 $K$。
- 對 seed choice 敏感。
- 偏好球形群。
- 保證局部收斂。

**DBSCAN 的角色**
- 依賴密度。
- 不一定要先給 $K$。
- 可處理噪音與任意形狀群。
- 對 Eps / MinPts 敏感。
- 自然產生聚類結果。

**Hierarchical Clustering 的角色**
- 提供樹狀階層結構。
- 不必一開始決定 $K$。
- Linkage 選擇明顯影響結果。
- 計算成本較高（$O(n^2 \log n)$）。

【材料原文｜全課重點速記】
1. **K-means**：快速簡單，但需決定 $K$；迭代更新群心；球形偏好
2. **DBSCAN**：密度導向；無需 $K$；能識別噪音；參數 $(\epsilon, \text{MinPts})$ 需調優
3. **HAC**：樹狀結構直觀；Linkage 方法決定群形狀；計算昂貴但結果可視化能力強
4. **群代表選擇**：Medoid 優於 Centroid（避免虛擬點、對異常值穩健）
5. **特徵篩選**：用 TF-IDF、互信息等去除低區辨力詞彙
6. **群標籤**：使用群特異詞（不只是高頻詞），提升可解釋性
7. **Topic Model**：軟分佈，比硬分群更符合現實；LDA 是目前主流

---

## §13 高維詛咒與降維（★ 任務問題 5）

【評註｜先講結論】**這一節是教材相對最薄的一塊。** 教材對維度詛咒只有「零散提及」，沒有專章、沒有公式、沒有降維方法的比較。以下把教材散落在五處的原句全部集中，讓 Skill 至少有可引用的原文依據。

【材料原文｜出處 1：Euclidean 距離的缺點（§3.2）】
> 在高維空間（curse of dimensionality）中，**所有點到原點的距離趨近相等**。
> Euclidean 距離「對異常值敏感、在高維空間中失效（維度詛咒）」。
> 比較表註記：Euclidean「直觀但高維失效」。

【材料原文｜出處 2：文字資料的實務對策（前置整理）】
> 在文字資料裡，因為向量通常高維且稀疏，所以 **cosine similarity 特別常見**。

【材料原文｜出處 3：DBSCAN 在高維失效（§8.6 缺點 3）】
> **高維數據上失效**：在高維空間中，距離度量的區分力下降（維度詛咒）；**Eps-鄰域的概念變得不清晰**。

【材料原文｜出處 4：K-means vs DBSCAN 的高維表現對比（§8.8）】
> 高維數據表現：K-means「尚可（距離仍有區分力）」；DBSCAN「差（距離度量失效，維度詛咒）」。

【材料原文｜出處 5：Centroid 的典型性問題（§10.1）】
> 在高維空間中，質心往往落在數據的「主要濃聚區」，但個別資料點由於**維度詛咒**反而呈現 sparse（稀疏）分佈。結果：質心周圍可能沒有真正的資料點聚集，是個「虛幻」的點。這稱為**典型性問題（Typicality Problem）**。
> 你算出的「平均文件」可能是個很少見的詞彙組合，根本沒人這樣寫過，也不適合拿來代表整個群。

【材料原文｜降維在教材中出現的四處】
1. **無監督學習的三大任務之一**：Clustering、**Dimensionality Reduction（降維）**、Anomaly Detection。
2. **K-means 的第一優化策略**：「**降維**：用 PCA、embedding 等方法降低 $m$ → **效果最明顯**」（§5.6 優化策略清單第 1 項）。
3. **降維的效益量化**（§5.6 例 2）：$m$ 從 5,000 降到 100 → 從 30 分鐘變 0.5 分鐘，**快 60 倍**。
4. **Embedding 作為降維手段**（§3.1）：$\vec{d_i} \in \mathbb{R}^d$，$d$ 通常 100–1024，遠小於詞彙大小；優點「維數低，語義豐富」。
5. **LSA 作為降維手段**（§11.2）：用 SVD 對詞-文件矩陣降維到低秩 $k$。
6. **Feature Selection 作為降維手段**（§10.3）：「**降低維度**：減少計算量，加快分群演算法」。

【評註｜教材立場整理成可執行規則】
1. **維度詛咒的機制（教材原話）**：高維下「所有點到原點的距離趨近相等」→ 距離失去區分力 → 任何以距離為基礎的分群都會退化。
2. **受害程度排序（教材給的）**：DBSCAN（差） < K-means（尚可）。教材沒說 HAC，但 HAC 同樣建立在距離矩陣上，推論同受影響。
3. **教材給的三條對策**：
   - **換距離**：文本/高維稀疏用 **Cosine**（教材明確推薦）。
   - **Feature Selection**：DF 閾值（保留出現在 5%–95% 文件的詞）、TF-IDF、互信息、卡方。
   - **降維**：PCA / Embedding / SVD(LSA)，且教材說這是**效果最明顯**的優化。
4. **降維順序**：教材的 K-means 優化策略把「降維」列為第 1 項、優先於 mini-batch 與並行化。
5. **降維後的副作用（教材沒說，評註）**：PCA 之後的主成分沒有業務語義，會直接傷害 §10.4 的 labeling；行銷分群的實務折衷是「用原始變數命名群、用降維後空間算距離」，或乾脆用 Feature Selection（保留原變數）而非 PCA。

---

## §14 Lecture 5：Sequence Tagging（★ 任務問題 7）

### 14.1 定義

【材料原文】

給定長度為 $T$ 的序列 $X = (x_1, x_2, \ldots, x_T)$，輸出同等長度的標籤序列 $Y = (y_1, y_2, \ldots, y_T)$，其中每個 $y_t \in \mathcal{Y}$（標籤集合）。

- 輸入空間：$X \in \mathcal{X}^T$
- 輸出空間：$Y \in \mathcal{Y}^T$
- 任務：學習映射函數 $f: \mathcal{X}^T \to \mathcal{Y}^T$

| 維度 | Classification | Sequence Tagging |
|---|---|---|
| 輸入 | 單一樣本 $x$ | 序列 $(x_1, \ldots, x_T)$ |
| 輸出 | 單一標籤 $y$ | 標籤序列 $(y_1, \ldots, y_T)$ |
| 預測策略 | 獨立評估樣本 | **考慮位置間的依存性** |
| 複雜度 | $O(m)$ | $O(\lvert Y\rvert^T)$ 指數增長 |

### 14.2 應用領域

【材料原文｜NLP】
- **詞性標記（POS Tagging）**：$\mathcal{Y} = \{N, V, ADJ, ADV, P, \ldots\}$；例「大學生/N 應該/AD 努力/V 學習/V」；NLP 流水線中最前端的任務。
- **命名實體識別（NER）**：$\mathcal{Y} = \{PERSON, ORG, LOC, DATE, \ldots, O\}$；例「Tim Cook 是 Apple 的首席執行官」→「Tim Cook/PERSON Apple/ORG」；應用：知識圖譜抽取、搜索引擎、智能問答系統。
- **語音辨識**：輸入聲譜圖序列（每 10ms 一幀，3 秒音頻 = 300 幀）；輸出音素或字符序列。

【材料原文｜金融序列（★ 行銷/商業最相關）】
- 股票價量預測：編碼為「升/平/降」三分類。
- 交易信號：每天決策「買/持/賣」。
- 風險檢測：識別異常模式「正常/警告/風險」。

【材料原文｜生物資訊】DNA 區域標註、蛋白質結構預測（$\mathcal{Y} = \{\alpha\text{-螺旋}, \beta\text{-摺疊}, \text{圈}\}$）；人類基因組 ~32 億個鹼基對。

### 14.3 為什麼上下文有用

【材料原文｜上下文的力量】

| 上下文 | 候選字 | 候選數 |
|---|---|---|
| 「馬」 | 上、虎、腳、達、屁、克、尾、... | 很多（100+） |
| 「馬英」 | 九 | 只有一個 |
| 「馬英九」 | 是（99.9%） | 基本確定 |

$$P(\text{下一個字} \mid \text{很多上下文}) \ll P(\text{下一個字} \mid \text{少量上下文})$$

**這正是序列模型強大的根本原因。**

【材料原文｜獨立 vs 依存】
- 若視為獨立分類：$P(\text{馬}|ctx) \times P(\text{英}|ctx) \times P(\text{九}|ctx)$ → 大量競爭候選，預測精度低。
- 若按順序依次決策：「馬」之後限制「英」的候選；「馬英」之後只有「九」→ 精度大幅提升。

【材料原文｜資訊論觀點】
$$D_{KL}(P^* \parallel Q(\cdot \mid \text{context})) < D_{KL}(P^* \parallel Q(\cdot))$$

### 14.4 Sliding Window（三種方向）

【材料原文】

- **Forward Predicting**：只看到「當前及之前」的信息。適用：在線系統（online）、即時預測（語音輸入法邊說邊轉文字）。優點：可以實時給出結果。缺點：未來信息不可得，預測精度受限。
- **Backward Predicting**：只看「當前及之後」的信息。適用：離線系統、整句已知（文本校對、拼音輸入的候選詞排序）。優點：利用未來信息，精度較高。缺點：無法即時反應，延遲大。
- **Bidirectional Predicting**：同時利用前後信息。適用：整個序列已知且不需要實時反應。優點：最多上下文 → 最準確。缺點：需等待整個序列。
- **這正是 BERT、XLNet 等現代雙向模型有效的根本原因。**

【材料原文｜例子「美國是個自由的國家」，標記第 4 個字「自」】

| 方向 | 可見 | 推理 | 精度 |
|---|---|---|---|
| Forward | 「美國是個」 | 模糊 | 低 |
| Backward | 「由的國家」 | 較清楚 | 中 |
| Bidirectional | 「個自由的」 | 完全確定 | 高 |

### 14.5 語言模型與 n-gram

【材料原文｜鏈式法則】
$$P(w_1, w_2, \ldots, w_T) = \prod_{t=1}^{T} P(w_t \mid w_1, w_2, \ldots, w_{t-1})$$

bigram 例子：
$$\begin{align}
P(\text{美國是個自由的國家}) &= P(\text{美}) \times P(\text{國}|\text{美}) \\
&\quad \times P(\text{是}|\text{國}) \times P(\text{個}|\text{是}) \\
&\quad \times P(\text{自}|\text{個}) \times P(\text{由}|\text{自}) \\
&\quad \times P(\text{的}|\text{由}) \times P(\text{家}|\text{的})
\end{align}$$

其中 $P(\text{國}|\text{美})$ = (語料中「美國」的次數) / (「美」的總次數)。

【材料原文｜對數機率（實務技巧）】
$$\log P(w_1, \ldots, w_T) = \sum_{t=1}^{T} \log P(w_t \mid \text{history})$$
原因：避免 **underflow**（連續相乘許多 $<1$ 的機率會迅速趨近 0）；數值穩定性；計算效率。

【材料原文｜Markov 假設】
$$P(w_t \mid w_1, \ldots, w_{t-1}) \approx P(w_t \mid w_{t-n+1}, \ldots, w_{t-1})$$
- Unigram ($n=1$)：完全忽視上下文
- Bigram ($n=2$)：只看前一個詞
- Trigram ($n=3$)：看前兩個詞

| 視窗大小 | 優點 | 缺點 |
|---|---|---|
| n 小（如 2） | 資料豐富、統計準確；計算快速 | 上下文不完整、資訊遺失 |
| n 中（如 3） | 效能與速度平衡 | 仍有資訊遺失 |
| n 大（如 5,6） | 上下文完整、捕捉更多信號 | **資料稀疏、許多組合未出現；估計困難** |

**權衡**：實務上 bigram 或 trigram 是常用選擇。

| 單位 | 優點 | 缺點 | 適用場景 |
|---|---|---|---|
| Character | 詞彙大小小（~5000 中文字），稀疏性低；適合拼寫變化 | 序列長度長，計算成本高；需更多上下文 | 輸入法、音譯 |
| Word | 語言結構清晰；序列短；語意豐富 | 詞彙大小大，資料稀疏；未知詞問題 | NLP 標準做法 |
| N-gram | 混合特性 | 複雜度增長 | 語言模型、機器翻譯 |

【材料原文｜Firth 名句與分佈語義】
> **"You shall know a word by the company it keeps"** — *Firth, J. R. (1957)*

**詞的含義由其出現的上下文決定。** Word2vec、GloVe、BERT 等現代嵌入模型，本質上都在實現分佈語義學：相似的上下文 → 相似的詞義。

### 14.6 金融序列的兩種做法（★ 可直接類比顧客行為序列）

【材料原文｜序列編碼】

| 日期 | Day1 | Day2 | Day3 | Day4 | Day5 | Day6 | Day7 | Day8 |
|---|---|---|---|---|---|---|---|---|
| 價格 | 100 | 102 | 102 | 105 | 103 | 101 | 99 | 99 |
| 變化 | 升 | 升 | 平 | 升 | 降 | 降 | 降 | 平 |
| 成交量 | 1M | 1.2M | 800K | 900K | 1.1M | 950K | 850K | 800K |
| 變化 | 升 | 升 | 降 | 降 | 升 | 降 | 平 | 平 |

編碼規則：升（比前一天上升）/ 平（保持不變）/ 降（下降）。

【材料原文｜做法 A：Tabular Classification（展平成特徵向量）】

將滑動視窗中的所有特徵展平成一個向量，套用標準分類演算法（決策樹、SVM、隨機森林）。用前兩天的資料預測第三天的價格變化：

| 樣本 | Day(i-2)價 | Day(i-2)量 | Day(i-1)價 | Day(i-1)量 | 目標 |
|---|---|---|---|---|---|
| 1 | 升 | 升 | 升 | 升 | 平 |
| 2 | 升 | 升 | 平 | 降 | 升 |
| 3 | 平 | 降 | 升 | 降 | 降 |

**優點**：簡單、快速、易於理解。**缺點**：丟失序列的連續時間結構；各樣本間被視為獨立。

【材料原文｜做法 B：條件機率建模】
$$P(D_i^{\text{價}} = \text{升} \mid D_{i-1}^{\text{價}}, D_{i-1}^{\text{量}}, D_{i-2}^{\text{價}}, D_{i-2}^{\text{量}}, \ldots)$$
對所有可能的目標值（升、平、降）計算機率，選擇機率最高的。

**優點**：明確建模序列依存性；捕捉時間動態。**缺點**：機率估計困難（資料稀疏）；計算複雜度更高。

【材料原文｜兩種世界觀】

| 視角 | 本質 | 適用 | 代表方法 |
|---|---|---|---|
| 表格分類 | 特徵向量 → 分類 | 特徵無時序 | 決策樹、SVM |
| 序列建模 | 序列 → 機率/隱態 → 序列 | 時間依存強 | n-gram、HMM、RNN |

> **白話說明**：表格分類像是「看一張快照做決定」；序列建模像是「看連貫的電影做決定」。電影提供的信息更豐富，決策品質更高。

【評註｜行銷映射】把上表的「價格/成交量」換成「造訪/加購/下單/退貨」，「升平降」換成「活躍/沉睡/流失」，這一整套就是**顧客生命週期階段標註**。做法 A 就是常見的「用過去 3 期特徵預測下一期是否流失」的表格化 churn model；做法 B 就是 HMM 式的顧客狀態轉移模型。教材明確指出做法 A 的缺點是「丟失序列的連續時間結構；各樣本間被視為獨立」——這正是為什麼 churn 模型常常學不到「顧客正在逐步降溫」的模式。

### 14.7 HMM（Hidden Markov Model）

【材料原文｜基本結構】

- **隱藏狀態序列** $Y = (y_1, \ldots, y_T)$：真實但不可直接觀測的狀態
  - 例：詞性標記中的詞性；**金融中的「市場狀態」（牛市、熊市、振盪）**
- **觀測序列** $X = (x_1, \ldots, x_T)$：實際看到的數據
  - 例：詞性標記中的詞本身；**金融中的「股價變化」（升、平、降）**

```javascript
隱狀態：  y₁ ──→ y₂ ──→ y₃ ──→ ... ──→ yₜ
           ↓     ↓     ↓            ↓
觀  測：  x₁     x₂     x₃     ...  xₜ
```
- 隱狀態間有**轉移邊**（表示馬可夫依存）
- 隱狀態到觀測有**發射邊**（表示觀測依賴於隱狀態）

【材料原文｜現實類比】
- **POS 標記**：隱狀態=詞性（看不到），觀測=詞（看得到）
- **市場分析**：隱狀態=市場政權（牛/熊，看不到），觀測=價格變化（看得到）
- **天氣模型**：隱狀態=天氣真實狀態，觀測=人的主觀感受

【材料原文｜兩個關鍵假設】

**假設 1：Markov Property（馬可夫性質）**
$$P(y_t \mid y_1, y_2, \ldots, y_{t-1}) \approx P(y_t \mid y_{t-1})$$
含義：下一時刻的隱狀態只依賴於上一時刻的狀態，與更遠的歷史無關（「無記憶性」/「一階依存」）。
- 白話：股票明天的漲跌趨勢主要取決於今天的狀態，而不是 100 天前的狀態。
- 局限性：實際上，詞的詞性可能受到遠處詞的影響；股票的趨勢往往受到長期因素影響。但為了計算簡便，我們接受這個近似。

**假設 2：Observation Independence（觀測獨立性）**
$$P(x_t \mid y_1, \ldots, y_t, x_1, \ldots, x_{t-1}) \approx P(x_t \mid y_t)$$
含義：給定當前隱狀態後，當前觀測獨立於所有歷史觀測與隱狀態。
- 局限性：觀測間可能有直接相關性（例如連續幾天的交易量往往相近）。

| 假設 | 效果 | 代價 |
|---|---|---|
| Markov Property | 減少隱狀態間的依存複雜度 | 長期記憶喪失 |
| Observation Independence | 減少觀測間的依存複雜度 | 觀測細節喪失 |
| 兩者結合 | 模型極度簡化，計算高效 | 預測精度受限 |

【材料原文｜聯合機率分解】
$$P(Y, X) = \prod_{t=1}^{T} P(y_t \mid y_{t-1}) \cdot P(x_t \mid y_t)$$
（$y_0$ 通常設為特殊的「開始」狀態 START）

展開：
$$\begin{align}
P(Y, X) &= P(y_1 | y_0) \cdot P(x_1 | y_1) \\
&\quad \times P(y_2 | y_1) \cdot P(x_2 | y_2) \\
&\quad \times \cdots \\
&\quad \times P(y_T | y_{T-1}) \cdot P(x_T | y_T)
\end{align}$$

- 第一項 $P(y_t \mid y_{t-1})$：**轉移機率**，模型狀態如何變化
- 第二項 $P(x_t \mid y_t)$：**發射機率**，狀態如何產生觀測

【材料原文｜三個核心分佈】
- **初始分佈** $\pi = P(y_1)$：$\pi = [\pi_1, \ldots, \pi_K]$，$K$ 是狀態數
- **轉移機率** $A = P(y_t \mid y_{t-1})$：$A_{ij} = P(y_t = j \mid y_{t-1} = i)$，$K \times K$ 矩陣
- **觀測機率** $B = P(x_t \mid y_t)$：$B_j(k) = P(x_t = k \mid y_t = j)$，$K \times M$ 矩陣（$M$ 是觀測符號數）

【材料原文｜POS 標記的完整數值例】

$$\pi = [P(\text{N}), P(\text{V}), P(\text{A})] = [0.3, 0.5, 0.2]$$

轉移矩陣 $A$（行=前一狀態，列=當前狀態）：
$$A = \begin{bmatrix}
P(\text{N}|\text{N}) & P(\text{V}|\text{N}) & P(\text{A}|\text{N}) \\
P(\text{N}|\text{V}) & P(\text{V}|\text{V}) & P(\text{A}|\text{V}) \\
P(\text{N}|\text{A}) & P(\text{V}|\text{A}) & P(\text{A}|\text{A})
\end{bmatrix} = \begin{bmatrix}
0.1 & 0.7 & 0.2 \\
0.4 & 0.1 & 0.5 \\
0.8 & 0.1 & 0.1
\end{bmatrix}$$
直覺：名詞後多接動詞（0.7）；動詞後多接形容詞（0.5）或名詞（0.4）；形容詞後多接名詞（0.8）。

觀測機率 $B$（行=狀態，列=詞：「銀行」、「經營」、「大」）：
$$B = \begin{bmatrix}
P(\text{銀行}|\text{N}) & P(\text{經營}|\text{N}) & P(\text{大}|\text{N}) \\
P(\text{銀行}|\text{V}) & P(\text{經營}|\text{V}) & P(\text{大}|\text{V}) \\
P(\text{銀行}|\text{A}) & P(\text{經營}|\text{A}) & P(\text{大}|\text{A})
\end{bmatrix} = \begin{bmatrix}
0.6 & 0.1 & 0.3 \\
0.05 & 0.8 & 0.15 \\
0.1 & 0.05 & 0.85
\end{bmatrix}$$
直覺：「銀行」多為名詞（0.6）；「經營」多為動詞（0.8）；「大」多為形容詞（0.85）。

【材料原文｜HMM 的三大問題】

| 問題 | 任務 | 公式 | 演算法 | 複雜度 |
|---|---|---|---|---|
| **1. 評估（Evaluation）** | 給定模型 $\lambda$ 和觀測 $X$，計算 $P(X\mid\lambda)$ | — | **Forward 演算法** | $O(T \times K^2)$ |
| **2. 解碼（Decoding）** | 找最可能的隱狀態序列 | $Y^* = \arg\max_Y P(Y \mid X, \lambda)$ | **Viterbi 演算法** | $O(T \times K^2)$ |
| **3. 學習（Learning）** | 學習模型參數 $\lambda = (\pi, A, B)$ | $\lambda^* = \arg\max_\lambda P(X\mid\lambda)$ | **Baum-Welch (EM) 演算法** | 迭代優化 |

問題 2 的應用：給定句子，預測每個詞的詞性。

【材料原文｜HMM 優缺點】

**優點**
- **理論基礎扎實**：概率模型有清晰的數學定義
- **高效推理**：Viterbi、Forward 演算法都是多項式時間
- **可學習**：Baum-Welch EM 演算法可無監督或弱監督學習
- **可解釋**：狀態轉移、發射機率有直觀意義
- **經典演算法**：已有 40+ 年的工業應用

**缺點**
- **假設過強**：Markov 假設和觀測獨立假設在現實中往往不成立
- **特徵工程困難**：觀測必須符合生成模型框架，難以加入複雜特徵
- **預測精度有限**
- **相鄰預測無互動**：轉移機率只看單個位置，無法建模標籤間的複雜相互作用

【評註｜HMM 的行銷應用（教材給了金融版，行銷版是同構）】
- **隱狀態 = 顧客的生命週期階段**（新客 / 成長 / 忠誠 / 沉睡 / 流失）——這是**看不到的**，公司資料庫裡沒有這個欄位。
- **觀測 = 每期可觀察的行為**（有無下單、造訪次數分級、客單價分級、是否用折價券）。
- **轉移矩陣 $A$ = 生命週期轉移機率**，直接就是行銷最想要的東西：「忠誠 → 沉睡」的月轉移率是多少？哪個環節漏水最快？
- **發射矩陣 $B$ = 各階段的行為特徵**：「沉睡期的顧客有 80% 機率零造訪」。
- **Viterbi 解碼** = 給定某顧客過去 12 個月的行為，回推他每個月實際處於哪個階段（比用硬規則「90 天未購買 = 流失」細緻得多）。
- **Baum-Welch** = 在沒有人工標階段標籤的情況下，直接從交易記錄學出階段定義——**這正是 HMM 對行銷最大的價值：不需要先定義「什麼叫流失」。**
- 教材的 Markov 假設限制在行銷上要小心：「這個月的階段只由上個月決定」會忽略季節性與長期忠誠度，教材原話：「股票的趨勢往往受到長期因素影響。但為了計算簡便，我們接受這個近似。」

### 14.8 CRF（Conditional Random Field）

【材料原文｜為什麼需要 CRF】

HMM 作為生成模型，同時建模 $P(Y, X)$，因此受到強獨立假設束縛。但實務中，**我們其實只關心 $P(Y|X)$**（給定觀測，預測隱狀態），所以無須同時建模 $P(X)$。

例如在詞性標記中：我們已經有詞（觀測）了；只需預測詞性（隱狀態）；不需要反向生成詞。

**生成 vs 判別的經典對比**：
- **生成模型**：$P(Y, X)$ → 建模整個聯合分布 → 複雜但可從無監督數據學習
- **判別模型**：$P(Y|X)$ → 直接建模條件分布 → 簡單且通常精度更高

【材料原文｜線性鏈 CRF 的核心公式】
$$P(Y|X) = \frac{1}{Z(X)} \exp\left(\sum_{t=1}^{T} \sum_{k} \lambda_k f_k(y_t, y_{t-1}, x_t)\right)$$

其中：
- $f_k(y_t, y_{t-1}, x_t)$：**特徵函數**，可以任意設計
  - 例：$f_1 = \mathbb{1}[y_t = \text{N} \wedge x_t = \text{銀行}]$（詞是「銀行」且詞性是名詞）
  - 例：$f_2 = \mathbb{1}[y_t = \text{V} \wedge y_{t-1} = \text{N}]$（名詞後接動詞）
  - **可以是任意函數，不受獨立假設限制**
- $\lambda_k$：**權重**，通過訓練數據學習；重要的特徵對應高權重；學習過程類似於邏輯迴歸或 SVM
- $Z(X)$：**配分函數**（歸一化常數）
  $$Z(X) = \sum_Y \exp\left(\sum_{t=1}^{T} \sum_{k} \lambda_k f_k(y_t, y_{t-1}, x_t)\right)$$

【材料原文｜特徵函數的靈活性】CRF 相比 HMM 的核心優勢是**特徵空間沒有限制**。在 HMM 中，觀測機率 $P(x_t|y_t)$ 只能建模「狀態到單個觀測」的映射；但在 CRF 中，特徵函數可以：
- 跨越多個時刻：$f(y_{t-1}, y_t, y_{t+1}, x_t)$
- 包含原始特徵的複雜組合：詞的字符、詞的長度、是否大寫等
- **編碼領域知識**：如「含數字的詞往往是實體名」

【材料原文｜HMM vs CRF 詳細比較】

| 特性 | HMM | CRF |
|---|---|---|
| 建模目標 | $P(Y,X)$ 生成式 | $P(Y|X)$ 判別式 |
| 獨立假設 | 馬可夫性 + 觀測獨立 | 更靈活 |
| 特徵設計 | 受限於生成框架 | **任意特徵函數** |
| 訓練方法 | EM、MLE | 梯度下降、SGD |
| 解碼 | Viterbi | **Viterbi（相同）** |
| 計算複雜度 | 低 | 中等 |
| 預測精度 | 通常較低 | **通常較高 (15-25%)** |
| 應用 | POS、簡單 NER | 複雜 NER、分詞 |

> **直觀比喻**：HMM 像是「推導整個故事的物理過程」，必須明確假設每一步如何發生；CRF 像是「直接學習從觀測到答案的映射」，只需指定有用的特徵，無需完整的生成過程。

【材料原文｜實務工具】
- **CRFsuite**（http://www.chokkan.org/software/crfsuite/）：輕量級、快速、易用；Python 綁定支持
- **CRF++**（https://taku910.github.io/crfpp/）：日本開發，經典工具；廣泛應用於 NLP，尤其在日文處理
- **MALLET**（http://mallet.cs.umass.edu/）：Java 實現，功能豐富

【評註｜CRF 的行銷應用】CRF 對行銷比 HMM 更實用的原因就是教材說的「特徵空間沒有限制」：顧客在某期的階段標籤可以同時吃進「上一期階段」「本期是否雙 11」「本期是否收到 EDM」「顧客註冊年資」「是否使用 App」——這些在 HMM 的發射矩陣裡塞不進去，在 CRF 的特徵函數裡是自然的。教材給的精度提升幅度是 **15-25%**。

### 14.9 RNN / LSTM

【材料原文｜RNN 遞推公式】
$$h_t = \tanh(W_{hh} h_{t-1} + W_{xh} x_t + b_h)$$
$$\hat{y}_t = \text{softmax}(W_{hy} h_t + b_y)$$
- $x_t \in \mathbb{R}^{d_x}$：時刻 $t$ 的輸入
- $h_t \in \mathbb{R}^{d_h}$：隱態向量，包含到目前為止的序列信息
- $W_{hh} \in \mathbb{R}^{d_h \times d_h}$、$W_{xh} \in \mathbb{R}^{d_h \times d_x}$、$W_{hy} \in \mathbb{R}^{d_y \times d_h}$

```javascript
輸入：    x₁ ──→ x₂ ──→ x₃ ──→ ... ──→ xₜ
           ↓     ↓     ↓            ↓
隱態：    h₁     h₂     h₃    ...   hₜ (累積記憶)
           ↓     ↓     ↓            ↓
輸出：    ŷ₁     ŷ₂     ŷ₃    ...   ŷₜ
```

**優勢**：變長序列處理；參數共享（參數數量與序列長度無關）；可導性（BPTT 訓練）；理論上無限記憶。

**限制**：
- **梯度消失**：若 $\lVert W_{hh}\rVert < 1$，梯度呈指數衰減，$\frac{\partial L}{\partial h_0} \approx (\prod_{t=1}^T J_h^{(t)}) \cdot \frac{\partial L}{\partial h_T}$；遠處時刻的梯度接近 0
- **梯度爆炸**：若 $\lVert W_{hh}\rVert > 1$，梯度呈指數增長；損失函數出現 NaN 或 Inf
- **長序列訓練困難**：難以學習超過 50-100 時刻的依存

【材料原文｜LSTM 三個門】

**遺忘門**：$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$ —— 「這個舊信息還有用嗎？」
**輸入門**：$i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i)$，$\tilde{C}_t = \tanh(W_C \cdot [h_{t-1}, x_t] + b_C)$ —— 「這個新信息重要嗎？」
**輸出門**：$o_t = \sigma(W_o \cdot [h_{t-1}, x_t] + b_o)$，$h_t = o_t \odot \tanh(C_t)$ —— 「哪些記憶現在應該用上？」

【材料原文｜記憶細胞的加法更新（關鍵創新）】
$$C_t = f_t \odot C_{t-1} + i_t \odot \tilde{C}_t$$

梯度流動：
$$\frac{\partial L}{\partial C_t} = \frac{\partial L}{\partial C_{t+1}} \frac{\partial C_{t+1}}{\partial C_t} + \frac{\partial L}{\partial h_t} \frac{\partial h_t}{\partial C_t}, \qquad \frac{\partial C_{t+1}}{\partial C_t} = f_{t+1} + \text{其他項}$$

加法項為梯度流動提供了「高速公路」。即使 $f_{t+1}$ 很小，梯度也不會完全消失。對比 RNN 的純乘法：
$$\frac{\partial h_t}{\partial h_{t-1}} = W_{hh}^T \text{diag}(\tanh'(\ldots))$$

> **比喻**：RNN 每天重寫整本日記，用新日記「覆蓋」舊日記 → 舊信息容易遺忘；LSTM 保持長期日記本，每天只「修改」部分內容、「添加」新條目 → 長期記憶得以保留。

【材料原文｜LSTM 的金融序列應用】
- **市場狀態轉變**：LSTM 的遺忘門可以學習市場從「牛市」轉向「熊市」的臨界點（遺忘門降低，新輸入門提高）
- **長期趨勢與短期波動**：同時捕捉高頻波動（短期）與低頻趨勢（長期）
- 應用：股價預測、異常檢測、交易信號生成

### 14.10 與 ARIMA 的比較

【材料原文】
$$y_t = c + \sum_{i=1}^{p} \phi_i y_{t-i} + \sum_{j=1}^{q} \theta_j \epsilon_{t-j} + \epsilon_t$$
- **AR（自迴歸）**：$\sum_{i=1}^{p} \phi_i y_{t-i}$，過去 $p$ 個值的線性組合
- **I（差分）**：數據的 $d$ 階差分，使序列平穩
- **MA（移動平均）**：$\sum_{j=1}^{q} \theta_j \epsilon_{t-j}$，過去 $q$ 個誤差項的加權和

ARIMA(1,1,1)：$\Delta y_t = c + \phi_1 \Delta y_{t-1} + \theta_1 \epsilon_{t-1} + \epsilon_t$，含義「今天的變化受昨天的變化和昨天的誤差影響」。

特點：線性；連續數值；統計可解釋；**資料需求低（通常 50-100 個數據點足夠訓練）**。

| 維度 | ARIMA | HMM/CRF | RNN/LSTM |
|---|---|---|---|
| 模型類型 | 線性 | 非線性 | 高度非線性 |
| 輸入 | 連續數值 | 離散標籤 | 連續或離散 |
| 輸出 | 連續預測 | 序列標籤 | 序列標籤或連續 |
| 依存建模 | 線性自迴歸 | 馬可夫或特徵 | 隱態累積 |
| 長期記憶 | 差分處理 | 有限（HMM）或好 | 強（LSTM） |
| 可解釋性 | 高 | 中 | 低（黑箱） |
| 資料需求 | 低 | 中 | 高 |
| 訓練速度 | 快 | 中 | 慢 |
| 應用 | 股價、天氣預測 | POS、NER | 複雜 NLP、深度學習 |

【材料原文｜非替代關係】ARIMA、HMM/CRF、RNN 不是替代關係，而是處理不同問題設定的工具。**他們可以組合使用：先用 ARIMA 將連續股價轉換為「升/平/降」，再用 HMM 或 RNN 建模這個離散序列。**

### 14.11 四條路線總比較

【材料原文】

| 方法 | 核心思路 | 優點 | 缺點 | 適用 |
|---|---|---|---|---|
| 滑窗 + 分類 | 固定視窗 → 分類 | 簡單快速 | 丟失窗外信息 | 資源有限、快速 baseline |
| n-gram 機率 | 條件機率鏈 | 機率基礎、存儲高效 | 資料稀疏 | 輸入法、語音辨識 |
| HMM/CRF | 隱狀態機率 | 機率框架扎實 | 假設強或計算複雜 | POS、NER |
| RNN/LSTM | 隱態遞推 | 無需手工特徵、端到端 | 資料需大、黑箱 | 大規模深度學習 |

【材料原文｜進展路線與每一步解決的限制】
```javascript
Sliding Window (固定視窗)
     ↓
n-gram Language Model (統計機率)
     ↓
HMM (隱狀態 + 馬可夫假設)
     ↓
CRF (打破獨立假設)
     ↓
RNN (變長記憶)
     ↓
LSTM (可控記憶)
```
- Sliding Window → 視窗大小固定，無法捕捉長期依存
- n-gram → 資料稀疏，沒有建模序列結構的機制
- HMM → 假設過強，特徵空間受限
- CRF → 計算複雜度高，無法處理超長序列
- RNN → 梯度消失，難以學習長期依存
- LSTM → 解決梯度問題，實現高效的長期記憶

【材料原文｜場景推薦表】

| 場景 | 推薦方法 | 原因 | 範例 |
|---|---|---|---|
| 資源極限 | Sliding Window | 快速、簡單 | 手機拼音輸入 |
| 實時預測 | n-gram | 低延遲 | 語音辨識實時字幕 |
| 傳統 NLP | HMM/CRF | 精度可靠、可解釋 | 標註語料有限的 NER |
| 深度學習 | LSTM/Transformer | 大資料、高精度 | 機器翻譯、問答系統 |
| 超長序列 | Transformer | 無梯度消失、注意力機制 | 文檔分類、長文本摘要 |

【材料原文｜一句話總結】
> **序列標記將分類問題升級為結構化預測：不再是「一個輸入 → 一個輸出」，而是「利用上下文和序列結構，為序列中的每個位置做最優決策」。**
>
> **"You shall know a word by the company it keeps"** —— 序列中的每個元素的標籤，由其「夥伴」（上下文）決定。
> - Sliding Window：固定視窗看夥伴
> - n-gram：統計夥伴的出現機率
> - HMM：用隱狀態解釋夥伴關係
> - CRF：設計特徵捕捉夥伴的複雜相互作用
> - RNN/LSTM：無限視窗，記憶所有夥伴

---

## §15 教材未涵蓋（Gap）—— 寫 Skill 時必須另尋來源

【評註｜以下每一項都經過全文檢索確認教材**沒有**給出，Skill 若要用必須自行補充或標註外部來源】

| 主題 | 教材狀態 | 影響 |
|---|---|---|
| **Silhouette coefficient** | **只列名兩次**（「代表指標：Silhouette coefficient、Davies-Bouldin、CH」、「K-means 只需調 K（通常用 Elbow 法或 Silhouette）」）。**沒有公式、沒有 $a(i)$/$b(i)$ 定義、沒有解讀門檻。** | 任務問題 2 的核心指標之一在教材是空的。Skill 必須自行定義 $s(i) = \frac{b(i)-a(i)}{\max(a(i),b(i))}$ 與解讀規則。 |
| **Davies-Bouldin Index** | **只列名一次**，無公式、無「越小越好」的說明。 | 同上。 |
| **Adjusted Rand Index (ARI)** | **只列名一次**（外部指標清單）。無公式、無「校正隨機期望」的說明。 | 教材只完整教了未校正的 RI。ARI 的「隨機分群期望值為 0」性質完全缺席。 |
| **Normalized Mutual Information (NMI)** | **只列名一次**。無公式。 | 同上。 |
| **Ward linkage** | **只在「推薦延伸閱讀」列出 Ward 1963 論文標題**。四種 linkage 不含 Ward。 | IB5082 HW8 直接要求 Ward，理論依據需自行從 WGSS 目標函數推（見 §9.5 評註）。 |
| **Two-step / 2-step clustering** | **完全沒有提及**（含 BIRCH 只在 Hierarchical 代表算法清單裡出現名字、無說明；CF-tree、log-likelihood 距離、BIC 自動選 K 全無）。 | HW8 直接要求 2-step，教材零覆蓋。見 §9.5 的推論式論證。 |
| **GMM 的實質內容** | 只出現三次：軟分群代表算法名、「K-means 是 EM 的特例（高斯方差趨向 0 時）」、「$G$ = Negative Log-Likelihood of Gaussian Mixture」。**沒有 GMM 的機率密度式、EM 的 E-step/M-step、共變異數型態、BIC/AIC 選 K。** | 任務問題 6 的「軟分群」在教材只有概念層。 |
| **維度詛咒的量化/專章** | 只有五處零散提及（見 §13），**沒有「高維下距離比 $\frac{d_{max}-d_{min}}{d_{min}} \to 0$」之類的量化陳述，沒有降維方法比較（PCA vs t-SNE vs UMAP），沒有「先降維再分群」的完整流程。** | 任務問題 5 教材偏薄。 |
| **標準化 / 尺度處理** | **完全沒有提及**。教材沒有講「跑 K-means 前要不要 z-score / min-max」。 | 這是行銷分群最常見的踩雷點（RFM 的 M 尺度遠大於 F），教材零覆蓋，Skill 必須自己加。 |
| **類別型變數的分群** | 沒有 k-modes、k-prototypes、Gower distance。Jaccard 是唯一沾邊的。 | 行銷資料常有性別/區域/會員等級，教材無解。 |
| **Gap Statistic** | 完全沒有。 | K 選擇只有 Elbow + CH。 |
| **分群穩定性 / bootstrap 驗證** | 完全沒有。 | 「換個 seed 群就變了」教材只給 random restart，沒給穩定性度量。 |
| **Viterbi 演算法的 DP 遞推式** | **只給名稱與複雜度 $O(T\times K^2)$**，沒有 $\delta_t(j) = \max_i \delta_{t-1}(i) A_{ij} B_j(x_t)$ 的遞推式與回溯。 | HMM 解碼要實作需另補。 |
| **Baum-Welch 的 E/M step** | 只給名稱。 | 同上。 |
| **平滑（smoothing）** | n-gram 資料稀疏問題有講，但**沒有 Laplace / Kneser-Ney 等平滑方法**。 | |

---

## §16 可重用資產（可直接寫進新 Skill）

### 16.1 分群專案的九步檢查清單（全部有教材依據）

```
□ 1. 釐清商業問題與 K 的業務約束
     - 這次分群要餵給誰？（廣告受眾包 / 業務名單 / 產品線規劃）
     - 行銷團隊能執行幾套策略？→ K 的上界
     - 每群至少要多少人才值得投放？→ K 的上界
     教材依據：「K 要反映業務需求，不能純粹靠數學」

□ 2. 選定資料表示（特徵）
     - RFM？品類佔比？行為序列？
     教材依據：「表示越好，聚類效果越好」、三大表示方法比較表

□ 3. 做 Feature Selection，砍掉無區辨力的變數
     - DF 閾值類比：刪掉「幾乎所有人都有」與「幾乎沒人有」的欄位
       （教材原則：保留出現在 5%–95% 的詞）
     教材依據：「降低維度 / 去除噪聲 / 提升可解釋性」

□ 4. 選距離度量（見 16.3 決策規則）
     教材依據：四大距離度量表

□ 5. 檢查維度。高維就降維（PCA / embedding）或改用 Cosine
     教材依據：「降維：效果最明顯」；「高維空間中所有點到原點的距離趨近相等」

□ 6. 選演算法（見 16.2 決策樹）

□ 7. 決定 K（見 16.4 SOP）

□ 8. 評估
     - 無 gold standard → CH Index（+ Elbow 視覺驗證）
     - 有既有分類可對照 → Purity（快速）+ Rand Index（綜合，能抓碎片化）
     教材依據：internal / external 兩大方向

□ 9. 命名與代表化（★ 最常被跳過但教材強調）
     - 為每群挑 Medoid（真實存在的代表顧客），不要用平均值編假人
     - 用「群特異變數」命名，不要用全體共同的高頻變數（Computer 陷阱）
     - 檢查群大小是否合理（反面例子：100 個大小 1–10 的碎片）
     教材依據：「分群不是終點」四項；salience 公式；Medoid 優勢四點
```

### 16.2 演算法選擇決策樹（教材原文，可直接引用）

```plain text
Start here:

資料特性？
├─ 群形狀？
│  ├─ 球形 / 均勻 → K-means（快速、預設首選）
│  └─ 不規則 / 細長 → DBSCAN 或 Single-link HAC
│
├─ 是否有噪音？
│  ├─ 大量噪音 → DBSCAN（自動識別 noise）
│  └─ 乾淨資料 → K-means 或 HAC
│
├─ 是否需要階層結構？
│  ├─ 需要 → HAC（得到 dendrogram）
│  └─ 不需要 → K-means 或 DBSCAN
│
├─ K 是否已知？
│  ├─ 已知 → K-means 直接用
│  └─ 未知 → DBSCAN 或先用 elbow method
│
└─ 文本是否多主題重疊？
   ├─ 是 → Topic Model（LDA）
   └─ 否 → Hard clustering
```

補充規模規則（教材原文推得）：
- $n \lesssim$ 數千 → HAC 可行（「若資料點數不超過數千，HAC 的成本是可接受的」）
- $n \gtrsim$ 數十萬 → K-means / Mini-batch K-means（「HAC 無法直接擴展至超大規模」）

### 16.3 距離度量決策規則（if-then）

```
IF 特徵是標準化後的連續數值 AND 維度 ≤ ~10
   THEN Euclidean
IF 特徵含未處理的極端值 OR 資料稀疏
   THEN Manhattan（教材：對異常值相對不敏感、稀疏數據更穩健）
IF 在意「組合比例」而非「絕對規模」（品類佔比、文本 TF-IDF）
   THEN Cosine，距離用 d = 1 - cos
IF 特徵是集合 / 0-1 二值（買過哪些品項、有哪些標籤）
   THEN Jaccard
IF 維度很高（>50）
   THEN 先降維，或直接改用 Cosine（教材：高維下 Euclidean 失效）
```

### 16.4 K 決定 SOP（教材原文四步）

```
Step 1: 用先驗知識縮小 K 範圍（如果有）
        例：市場調查提示客戶可能 3-5 類
Step 2: 計算 K = 2 到 10 的 CH Index
Step 3: 選擇 CH Index 最高的 K
Step 4: 驗證（用 Elbow 法視覺檢查，聽專家意見）

若 CH 與 Elbow 意見不一 → 找領域專家，因為 K 要反映實際業務需求。
```

### 16.5 核心公式速查

```
群內平方和（K-means 目標 / WGSS / RSS / Inertia）
G = Σ_k Σ_{x_i ∈ c_k} ||x_i - μ_k||²

重心
μ(c) = (1/|c|) Σ_{x ∈ c} x

Elbow 改善率
Improvement(K) = [WGSS(K-1) - WGSS(K)] / WGSS(K-1) × 100%

Calinski-Harabasz Index（越大越好）
CH(K) = [BGSS/(K-1)] / [WGSS/(N-K)] = [(N-K)/(K-1)] × (BGSS/WGSS)
BGSS  = Σ_k |c_k| · ||center_k - center_global||²

Purity（越大越好，但會被碎片化拉高）
purity(Ω, C) = (1/N) Σ_k max_j |ω_k ∩ c_j|

Rand Index（越大越好，0.5 = 隨機）
RI = (A + D) / C(N,2)
Precision = A/(A+B)   Recall = A/(A+C)   F = 2PR/(P+R)

Medoid（群代表）
medoid(c) = argmin_{x ∈ c} Σ_{y ∈ c} dist(x, y)

Labeling salience（挑群特異變數）
salience(term, cluster) = [freq(term, cluster) / freq(term, all)] × freq(term, cluster)

Linkage 更新規則
single   : sim((c_i ∪ c_j), c_k) = max(sim(c_i,c_k), sim(c_j,c_k))
complete : sim((c_i ∪ c_j), c_k) = min(sim(c_i,c_k), sim(c_j,c_k))
average  : dist((c_i ∪ c_j), c_k) = [|c_i|·dist(c_i,c_k) + |c_j|·dist(c_j,c_k)] / (|c_i|+|c_j|)
centroid : x̄_new = (|c_i|·x̄_i + |c_j|·x̄_j) / (|c_i| + |c_j|)

Dendrogram 切割：要 K 群，就在第 (n - K) 次合併的高度切

K-means++ 選種
P(x_i) ∝ D(x_i)²,  D(x_i) = min_{l<j} ||x_i - μ_l||
理論保證：期望成本 ≤ O(log K) 倍最優解

DBSCAN
N_ε(p) = {q ∈ D | d(p,q) ≤ ε}
core   : |N_ε(p)| ≥ MinPts
啟發式 : MinPts = 2 × d  或  MinPts ≥ log(N)；k-distance graph 的肘部 = ε

HMM
P(Y, X) = Π_t P(y_t | y_{t-1}) · P(x_t | y_t)
三分佈：π = P(y₁)、A_{ij} = P(y_t=j | y_{t-1}=i)、B_j(k) = P(x_t=k | y_t=j)
三問題：Evaluation→Forward O(TK²)；Decoding→Viterbi O(TK²)；Learning→Baum-Welch(EM)

CRF（線性鏈）
P(Y|X) = (1/Z(X)) · exp( Σ_t Σ_k λ_k f_k(y_t, y_{t-1}, x_t) )
Z(X)   = Σ_Y exp( Σ_t Σ_k λ_k f_k(y_t, y_{t-1}, x_t) )

RNN / LSTM
h_t = tanh(W_hh h_{t-1} + W_xh x_t + b_h)
C_t = f_t ⊙ C_{t-1} + i_t ⊙ C̃_t     ← 加法更新，梯度高速公路
```

### 16.6 程式碼資產（教材點名的套件；R 對照為評註補充）

【材料原文｜教材點名】

| 演算法 | Python | R |
|---|---|---|
| K-means | `sklearn.cluster.KMeans` | 教材列 R 但未指名函式 |
| DBSCAN | `sklearn.cluster.DBSCAN` | 教材列 `density`（實務應為 `dbscan::dbscan`） |
| HAC | `sklearn.cluster.AgglomerativeClustering`；`scipy.linkage` | 教材列 `hclust` |
| Topic Model | — | 教材列 `lda`；Java: MALLET |
| CRF | CRFsuite（Python 綁定）、CRF++、MALLET | — |

【材料原文｜教材延伸閱讀列的 R 生態】「R: hclust (HAC), density (DBSCAN), lda (主題建模)」

【評註｜R → Python 遷移對照，供包子把 R 習慣搬到 Python】

```python
# ---- K-means（教材：K-means++ + 3 次重啟通常足夠）----
from sklearn.cluster import KMeans
km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
labels = km.fit_predict(X)
wgss = km.inertia_          # 教材的 G / WGSS / RSS

# ---- Elbow（教材 Step: K=2..10）----
wgss_curve = {k: KMeans(k, init="k-means++", n_init=10, random_state=42)
                 .fit(X).inertia_ for k in range(1, 11)}

# ---- CH Index（教材唯一給公式的自動 K 選擇指標）----
from sklearn.metrics import calinski_harabasz_score
ch = {k: calinski_harabasz_score(X, KMeans(k, n_init=10, random_state=42).fit_predict(X))
      for k in range(2, 11)}
best_k = max(ch, key=ch.get)          # 教材決策規則：K* = argmax CH

# ---- 外部評估（有 gold standard 時）----
from sklearn.metrics import rand_score
ri = rand_score(y_true, labels)       # 教材的 RI
# Purity 教材有公式但 sklearn 無內建：
import numpy as np
from scipy.stats import contingency
def purity(y_true, y_pred):
    cm = contingency.crosstab(y_pred, y_true)[1]   # K x J 列聯表
    return cm.max(axis=1).sum() / cm.sum()

# ---- HAC（教材四種 linkage；Ward 為 HW8 需求，教材未教）----
from sklearn.cluster import AgglomerativeClustering
hac = AgglomerativeClustering(n_clusters=k, linkage="ward")  # 'single'|'complete'|'average'|'ward'
# Dendrogram（教材：要 K 群就在第 n-K 次合併的高度切）
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
Z = linkage(X, method="ward")
labels = fcluster(Z, t=k, criterion="maxclust")

# ---- DBSCAN + k-distance graph（教材的 Eps 決定法）----
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN
min_pts = 2 * X.shape[1]                      # 教材啟發式 MinPts = 2 × 維度
nn = NearestNeighbors(n_neighbors=min_pts).fit(X)
d, _ = nn.kneighbors(X)
kdist = np.sort(d[:, -1])[::-1]               # 教材：由大到小排序後找肘部
db = DBSCAN(eps=chosen_eps, min_samples=min_pts).fit(X)
# db.labels_ == -1 即教材的 noise point

# ---- Medoid（教材：群代表要用真實存在的點）----
def medoid(Xc):                                # argmin_x Σ_y dist(x, y)
    from scipy.spatial.distance import cdist
    return Xc[cdist(Xc, Xc).sum(axis=1).argmin()]
```

R 對照（教材點名 hclust / dbscan / lda）：
```r
# HAC —— 教材的四種 linkage 對應 hclust 的 method
d  <- dist(X, method = "euclidean")          # "manhattan" 亦可
hc <- hclust(d, method = "ward.D2")          # "single" | "complete" | "average" | "centroid"
plot(hc)                                      # dendrogram
grp <- cutree(hc, k = 4)                      # 教材：第 (n-K) 次合併的高度切

# K-means
km <- kmeans(X, centers = 4, nstart = 25)     # nstart = 教材的 random restarts
km$tot.withinss                                # 教材的 WGSS / G

# DBSCAN
library(dbscan)
kNNdistplot(X, k = 2 * ncol(X)); abline(h = eps_guess, lty = 2)   # 教材的 k-distance graph
db <- dbscan(X, eps = eps_guess, minPts = 2 * ncol(X))
```

### 16.7 給行銷 Skill 的十條決策規則（濃縮）

```
R1  分群的正當性論證：全局平均會掩蓋多樣性（雞兔同籠 / 平均客單 500 元）。
    → 教材的客戶分群三簇表（VIP 5% / 常客 20% / 偶買客 75%）可直接當範本。

R2  K-means 是 baseline，不是答案。教材原話：「不一定永遠最好，但非常值得先做」。

R3  一定要用 K-means++ 而不是純隨機初始化；配 3 次以上重啟。
    純隨機的失敗案例教材有 1D 反例（A~F 六點）。

R4  K 的最終仲裁是業務不是數學。CH Index 給候選，Elbow 視覺驗證，專家拍板。

R5  不要用 Purity 或 WGSS 選 K —— 兩者都隨 K 單調變好，會誘導你切太碎。

R6  高維（品類 100+、文本）先降維或改 Cosine。降維是教材列的第一優化手段。

R7  異常顧客先撈掉再分群。K-means 對異常值敏感（centroid 會被拉偏，教材有公式）。
    可用 DBSCAN 的 noise 標記或直接 winsorize。

R8  Persona 用 Medoid（真實顧客），不用 centroid（虛擬平均人）。
    教材的 Typicality Problem 說明高維下 centroid 周圍可能沒有真實資料點。

R9  命名用「群特異變數 / index」，不用「群內高頻變數」。這是 Computer 陷阱。
    salience 公式 = 群內頻率 ÷ 全體頻率 × 群內頻率。

R10 顧客旅程 / 生命週期階段 → 不是分群問題，是序列標註問題（L5）。
    隱狀態 = 階段，觀測 = 行為，轉移矩陣 = 階段流失率，Viterbi = 回推每期階段。
    要塞入活動、季節、年資等外生變數 → 用 CRF 而非 HMM（教材：特徵空間無限制，精度 +15~25%）。
```

---

## §17 兩份材料的差異與可信度註記

【評註】

1. **Purity 例題數字不一致**：本機講義給 $(5+4+2)/17 \approx 0.647$；前置整理的逐頁對照（p.38）給 $(5+4+3)/17 \approx 0.71$。**前置整理是對照投影片逐頁謄寫，可信度較高**。講義自己也註明「如果投影片的例子中數值不同，請用該數值代入」。
2. **Elbow 的 y 軸**：本機講義畫成 WGSS（越低越好，找下降趨緩點）；前置整理 p.31 記投影片的 y 軸是「**解釋變異比例**」（越高越好，找上升趨緩點），elbow 在 K≈4。兩者是同一件事的倒數關係，Skill 裡要標明用的是哪一種。
3. **加速倍數不一致**：本機講義的雙階段檢索例子給 20 倍；Notion Part 1 給「理論 6 倍、實際觀察 10～20 倍」。取 Notion 版較保守。
4. **Notion Lecture 5 標題含「（施工中）」**，但內容已相當完整（含 HMM 三矩陣數值、LSTM 門控公式、四路線比較、ARIMA 比較）。本機 L5 講義較短（24KB），推測 Notion 版是後續擴充的版本。
5. **Notion Part 1/2/3 與本機講義高度重疊**，Notion 版多了 toggle/details 的層次與「白話說明」標註，本機講義多了「學長的話」與更多數值例子。兩者互補，本 digest 已合併。
6. **教材對 K-means 收斂的措辭有小出入**：Notion Part 1 說 assignment 與 update 使 $G$「不增」；本機講義說「單調降低」。嚴格說是「不增（non-increasing）」，Notion 版較精確。
