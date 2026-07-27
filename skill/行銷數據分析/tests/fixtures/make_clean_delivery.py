#!/usr/bin/env python3
"""
做一個「乾淨、正常跑完」的專案 —— 給 verify_outputs.py 當全綠基準。

為什麼要有它：
  verify_outputs.py 是交付 gate，但它讀的四份中繼檔（report_meta.json /
  bundle.json / analysis_objects.json / manifest.json）由 build_report.py、
  result_bundle.py、collect_figures.py、stamp_version.py 產生，**那四支還沒實作**。
  沒有這支 fixture，「gate 在正常專案上會不會放行」這件事永遠驗不到，
  只驗得到「gate 擋不擋得住壞東西」。

  這支腳本按 verify_outputs.py 開頭那張輸入契約表，把四份中繼檔與對應的交付物
  一次做齊。四支腳本實作時，產出要能取代這裡的每一段 —— 對不上就是契約破了。

用法：
    python make_clean_delivery.py [專案代號]
    MKT_專案根目錄=/tmp/xxx python make_clean_delivery.py 冒煙_乾淨交付
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from paths import project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_PROJECT = "冒煙_乾淨交付"
AS_OF = "2026-06-30"

# 版本三件套（20 §十）。刻意都做成「會被 D05 的雜訊遮罩吃掉」的形狀：
# 純十六進位字串 → 不會被當成內文統計數字。
RUN_ID = "a1b2c3d4e5f6"
SNAPSHOT_ID = "0000000000042"
GIT_COMMIT = "9f3c1a7b2d8e4f6a0c5b3d1e7f9a2c4b6d8e0f1a"

# 1×1 透明 PNG。圖的內容不是這支腳本要證明的事，非 0 bytes 才是（19 §6.2 第 4 條）。
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100fdff03fa0000000049454e44ae426082"
)

CHAPTERS = [
    "資料描述", "RFM 模型", "CAI 指標", "CRI 指標", "購物籃分析",
    "因素分析", "集群分析", "卡方檢定", "F 檢定／ANOVA",
    "事後檢定／獨立 t", "結論與管理者建議",
]
LAYOUT_ITEMS = ["封面", "摘要", "目錄", "表目錄", "圖目錄", "頁碼",
                "章節大小標", "表格自製", "跨頁續表頭"]

# 19 §1.8 的必出張數。topic 用中文、kind 取自 19 §6.1 詞彙表。
FIGURE_PLAN: dict[str, list[tuple[str, str]]] = {
    "M1": [("刷卡金額", "hist"), ("刷卡金額", "box"), ("刷卡金額", "qqplot"),
           ("缺失率", "heatmap"), ("刷卡地點", "bar"), ("交易日", "line")],
    "M2": [("金額與次數", "scatter"), ("特徵相關", "heatmap"),
           ("特徵分布", "box"), ("常態性", "qqplot")],
    "M4": [("複檢殘差", "scatter"), ("複檢相關", "heatmap"),
           ("複檢分布", "box"), ("複檢常態性", "qqplot")],
    "M3": [("轉換前", "hist"), ("轉換後", "hist"), ("偏態變化", "bar"),
           ("轉換前後排序", "scatter"), ("轉換方法比較", "line")],
    "M6": [("群數選擇", "elbow"), ("群內凝聚", "silhouette"), ("間隙統計", "gap"),
           ("群投影", "pca"), ("群指標", "heatmap"), ("群特徵", "parallel"),
           ("群規模", "barh"), ("穩定度", "bar")],
    "M7": [("係數", "coefplot"), ("殘差", "diag2x2"), ("鑑別度", "roc"),
           ("校準", "calibration"), ("學習曲線", "learning")],
    "M8-1": [("rfm 分數", "heatmap"), ("rfm 分布", "hist"), ("cai 累積", "cdf"),
             ("cai 三群", "bar"), ("cri 與回購", "scatter"),
             ("cri 與金額", "scatter"), ("clv 集中度", "pareto"),
             ("留存", "cohort"), ("群遷徙", "sankey"), ("存活", "km")],
    "M8-2": [("品類支持度", "bar"), ("品類提升度", "barh"),
             ("共現", "heatmap"), ("關聯", "network"),
             ("信賴度與提升度", "scatter"), ("品類貢獻", "waterfall"),
             ("品類排名", "lollipop")],
    "M8-3": [("月營收", "bar"), ("成長趨勢", "line"), ("成長分解", "waterfall"),
             ("轉換漏斗", "funnel"), ("成長與獲利", "quadrant"),
             ("期初期末", "dumbbell")],
    "M9": [("預測與實際", "line"), ("鑑別度", "roc"), ("精確召回", "pr"),
           ("增益", "lift"), ("校準", "calibration"), ("混淆", "confusion"),
           ("學習曲線", "learning"), ("季節分解", "stl")],
    "M10": [("詞頻", "bar"), ("主題強度", "barh"), ("主題相似", "heatmap"),
            ("共詞", "network"), ("情緒趨勢", "line")],
}

# 進報告的圖（collect_figures.py 的落點）。key = 檔名，value = 結果物件鍵
REPORT_FIGURES = {
    "M8-1_rfm 分數_heatmap.png": ("圖.rfm 熱圖", "近一年有效交易，退貨已扣除"),
    "M8-1_cai 三群_bar.png": ("圖.cai 三群", "CAI 以 as_of 當日回溯 365 天計算"),
    "M6_群規模_barh.png": ("圖.群規模", "分群母體＝當期有交易的會員"),
}

# 內文出現的每個數字 → Bundle 的 metric_id（20 §2.2：格式化只發生在 Bundle.fmt()）
NUM_SOURCES = {
    "3,210": "客單價.A群",
    "2.9": "倍數.A群對C群",
    "33.5%": "占比.A群",
}

BUNDLE = {
    "客單價.A群": {"value": 3210, "fmt": "整數千分位", "source": "統計表/行銷分析/rfm_群輪廓.csv",
                   "as_of": AS_OF, "evidence": "相關", "n": 412},
    "倍數.A群對C群": {"value": 2.866, "fmt": "一位小數", "source": "統計表/行銷分析/rfm_群輪廓.csv",
                      "as_of": AS_OF, "evidence": "相關", "n": 841},
    "占比.A群": {"value": 33.5, "fmt": "一位小數百分比", "source": "統計表/行銷分析/rfm_群輪廓.csv",
                 "as_of": AS_OF, "evidence": "相關", "n": 1229},
    "圖.rfm 熱圖": {"value": "M8-1_rfm 分數_heatmap.png", "fmt": "檔名",
                    "source": "模型輸出/rfm_score.parquet", "as_of": AS_OF,
                    "evidence": "相關", "n": 1229},
    "圖.cai 三群": {"value": "M8-1_cai 三群_bar.png", "fmt": "檔名",
                    "source": "模型輸出/cai.parquet", "as_of": AS_OF,
                    "evidence": "相關", "n": 1229},
    "圖.群規模": {"value": "M6_群規模_barh.png", "fmt": "檔名",
                  "source": "模型輸出/cluster_labels.parquet", "as_of": AS_OF,
                  "evidence": "相關", "n": 1229},
}

# 頁尾不寫 reference 章節號 —— 「20 §十」的那個 20 會被 D05 當成未登錄的內文數字，
# 而它本來就不是統計數字。交付物是給客戶看的，本來也不該引 skill 的內部編號。
FOOTER_MD = (f"\n\n---\n\n版本三件套：run_id {RUN_ID}｜"
             f"ducklake snapshot {SNAPSHOT_ID}｜git commit {GIT_COMMIT}\n")
FOOTER_HTML = (f'\n<footer><p>版本三件套：run_id {RUN_ID}｜'
               f'ducklake snapshot {SNAPSHOT_ID}｜git commit {GIT_COMMIT}</p></footer>\n')


def _summary(title: str) -> str:
    """每章小結 150–400 字、不以「本章分析了」開頭（18-E19）。"""
    s = (f"{title}這一章的主要發現是：A 群平均客單價 3,210 元，"
         "為 C 群的 2.9 倍，且該群人數只佔全體的 33.5%，"
         "營收貢獻卻超過半數，集中度明顯偏高。"
         "經營意涵是預算應該往這一群傾斜，但傾斜的前提是先把該群的回購間隔"
         "壓在四十二天以內，否則加碼只會把成本花在已經會回來的人身上。"
         "此處只到相關等級，不宣稱任何因果；要談增量效果必須先做實驗設計，"
         "在沒有對照組之前，任何「加碼就會成長」的說法都不成立。"
         "承接下一章，我們把同一批顧客改用行為分層重新切一次，"
         "檢查這個集中度是不是切法造成的假象。")
    n = len("".join(s.split()))
    assert 150 <= n <= 400, f"{title} 小結 {n} 字，超出 150–400"
    return s


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig" if path.suffix == ".csv" else "utf-8")


def build(code: str) -> Path:
    p = project_dir(code, create=True)

    # ── 圖表/（19 §1.8 各模組必出張數）──────────────────
    group_of = {"M1": "資料體檢", "M2": "特徵檢驗", "M4": "特徵檢驗",
                "M3": "轉換前後對照",
                "M6": "分群", "M7": "迴歸診斷", "M8-1": "行銷分析",
                "M8-2": "行銷分析", "M8-3": "行銷分析", "M9": "預測模型",
                "M10": "文本分析"}
    fig_src: dict[str, Path] = {}
    for mod, plan in FIGURE_PLAN.items():
        d = p.figures / group_of[mod]
        d.mkdir(parents=True, exist_ok=True)
        for topic, kind in plan:
            f = d / f"{mod}_{topic}_{kind}.png"
            f.write_bytes(PNG_1PX)
            fig_src[f.name] = f

    # 報告用/ 只准 copy 不准產圖（19 §6.2）
    dest = p.figures / "報告用"
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, (rid, caliber) in REPORT_FIGURES.items():
        src = fig_src[name]
        shutil.copy2(src, dest / name)
        manifest[name] = {
            "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "src": str(src),
            "result_object_id": rid,
            "口徑": caliber,
        }
    _write(dest / "manifest.json",
           json.dumps(manifest, ensure_ascii=False, indent=2))

    # ── 統計表/（交付用類；QA 中繼產物那三類不放這裡）────
    _write(p.tables / "行銷分析" / "rfm_群輪廓.csv",
           "群別,人數,占比,平均客單價,平均回購間隔天數,結論\n"
           "A群,412,33.5,3210,42,高頻高額，優先經營\n"
           "B群,388,31.6,1840,68,中頻中額，維持既有溝通\n"
           "C群,429,34.9,1120,95,低頻低額，只做低成本觸達\n")
    _write(p.tables / "行銷分析" / "cai_三群比較.csv",
           "群別,人數,占比,平均 CAI,結論\n"
           "高活躍,301,24.5,12.481,持續加碼，回購動能仍在\n"
           "中活躍,540,44.0,3.207,維持既有溝通頻率\n"
           "低活躍,388,31.5,-8.664,降低投放，改以低成本觸達\n")

    # ── 模型輸出/（result_bundle.py 與建模腳本的落點）──
    _write(p.models / "bundle.json",
           json.dumps(BUNDLE, ensure_ascii=False, indent=2))
    _write(p.models / "analysis_objects.json", json.dumps({
        "anova": [{"id": "anova_客單價_by_群", "posthoc_id": "posthoc_客單價_by_群"}],
        "posthoc": [{"id": "posthoc_客單價_by_群", "method": "Tukey HSD"}],
        "分群輸入變數": ["R", "F", "M", "CAI"],
        "分群先驗群依據": "行為分層（RFM 分數五分位）",
        "證據檢查物件": [],
    }, ensure_ascii=False, indent=2))

    # ── 專案記憶/（18-G10 指標字典）──────────────────
    _write(p.memory / "指標字典.csv",
           "metric_id,中文名,口徑,計算窗\n"
           "客單價,平均客單價,有效交易淨額除以交易筆數，退貨已扣除,近 365 天\n"
           "倍數,群間倍數,兩群同一指標相除,近 365 天\n"
           "占比,人數占比,該群人數除以分群母體,as_of 當日\n"
           "圖,圖檔結果物件,圖用的結果物件鍵,as_of 當日\n")

    # ── 執行紀錄/（20 §十 版本三件套）────────────────
    _write(p.log / "run_manifest.json", json.dumps({
        "run_id": RUN_ID,
        "ducklake_snapshot_id": SNAPSHOT_ID,
        "git_commit": GIT_COMMIT,
        "as_of": AS_OF,
    }, ensure_ascii=False, indent=2))

    # ── 交付物/ ─────────────────────────────────────
    d = p.deliverables
    _write(d / "完整報告.html",
           "<html><head><title>顧客價值分析</title></head><body>\n"
           "<h1>顧客價值與分群分析</h1>\n"
           + "".join(f"<h2>{ch}</h2><p>{_summary(ch)}</p>\n" for ch in CHAPTERS)
           + "<p>A 群平均客單價 3,210 元，為 C 群的 2.9 倍；該群人數佔全體 33.5%。</p>\n"
             "<p>本報告僅到相關等級，不宣稱因果；停止對低活躍群的無差別投放。</p>\n"
           + FOOTER_HTML + "</body></html>\n")

    _write(d / "決策摘要.html",
           "<html><head><title>決策摘要</title></head><body>\n"
           "<h1>決策摘要</h1>\n"
           "<p>A 群平均客單價 3,210 元，佔全體 33.5%，是本期唯一值得加碼的群。</p>\n"
           "<p>相對地，低活躍群應停止全通路推播，改走低成本觸達。</p>\n"
           + FOOTER_HTML + "</body></html>\n")

    _write(d / "insights.md",
           "## 洞察一：高價值群同時是高活躍群\n\n"
           "M6 的分群結果與 M8-1 的活躍度指標指向同一批人，兩者交集接近全部。\n"
           "這一群的回購間隔最短，且品類廣度最寬。\n\n"
           "## 洞察二：品類擴張與回購間隔同向\n\n"
           "M8-2 的品類共現網絡顯示，跨品類購買者在 M8-1 的留存曲線上明顯較平。\n"
           "此處只到相關等級，尚不可宣稱擴品類會延長生命週期。\n\n"
           "## 洞察三：低活躍群的營收貢獻與投放成本不成比例\n\n"
           "M8-3 的成長分解顯示低活躍群幾乎不貢獻增量，M7 的迴歸也未見其反應。\n"
           "建議停止對這一群的全通路推播。\n"
           + FOOTER_MD)

    _write(d / "decision_summary.md",
           "# 決策摘要\n\n"
           "| 決策 | 依據 | 證據等級 |\n"
           "|---|---|---|\n"
           "| 高價值群加碼 | 群輪廓與活躍度一致 | 相關 |\n"
           "| 低活躍群停止全通路推播 | 成長分解無增量跡象 | 相關 |\n\n"
           "## Key Insights\n\n"
           "- 高價值群與高活躍群高度重疊\n"
           "- 品類廣度與留存同向\n"
           "- 低活躍群投放產出不成比例，應停止\n"
           "- 所有結論止於相關等級，尚待實驗驗證\n"
           + FOOTER_MD)

    _write(d / "decision_tables.md",
           "# 各群決策表\n\n"
           "## 高價值群\n\n"
           "| 列 | 內容 |\n|---|---|\n"
           "| 現況 | 回購間隔最短、品類最寬 |\n"
           "| 動作 | 專屬顧問與早鳥檔期 |\n"
           "| 停止 | 停止與其他群共用的大量群發 |\n"
           + FOOTER_MD)

    _write(d / "action_brief_R1.md",
           "# R1：高價值群專屬經營\n\n"
           "## 對象\n\n名單見 audience_R1 檔，母體為分群後的高價值群。\n\n"
           "## 現況\n\n該群回購間隔與品類廣度都與活躍度指標同向變化（相關等級）。\n\n"
           "## 動作\n\n專屬顧問、早鳥檔期、生日回饋三選一測試。\n\n"
           "## 不做什麼\n\n停止對這一群沿用全體共用的群發素材。\n\n"
           "## 證據等級\n\n相關。尚未做對照試驗，不宣稱任何因果效果。\n"
           + FOOTER_MD)

    _write(d / "sizing.csv",
           "rec_id,建議,evidence_level,breakeven_response_rate,verdict,group_n,結論\n"
           "R1,高價值群專屬經營,相關,2.8%,先做,412,兩平門檻低於歷史反應水準\n")

    _write(d / "calibration_log.csv",
           "rec_id,校準來源,經驗值,模型值,calib_status,結論\n"
           "R1,去年同檔期,3.1%,2.8%,已校準,兩者差距在可接受範圍\n")

    _write(d / "excluded_options.csv",
           "option_id,已考慮方案,排除理由,結論\n"
           "X1,全站折扣,毛利無法支撐且會侵蝕高價值群單價,列入附錄備查\n")

    _write(d / f"audience_R1_{AS_OF}.csv",
           "顧客編號,群別,建議動作\n"
           "C0001,高價值群,專屬顧問\n"
           "C0002,高價值群,早鳥檔期\n"
           "C0003,高價值群,生日回饋\n")

    _write(d / "report_meta.json", json.dumps({
        "章節": [{"標題": ch, "狀態": "完成", "小結": _summary(ch)} for ch in CHAPTERS],
        "排版件": {k: True for k in LAYOUT_ITEMS},
        "頁數": 28,
        "圖表引用": list(REPORT_FIGURES),
        "數字來源": {
            "完整報告.html": NUM_SOURCES,
            "決策摘要.html": {"3,210": "客單價.A群", "33.5%": "占比.A群"},
            "insights.md": {},
            "decision_summary.md": {},
            "decision_tables.md": {},
            "action_brief_R1.md": {},
        },
        "名單人數": {f"audience_R1_{AS_OF}.csv": 3},
        "量測變更日": [],
        "含變更日的趨勢圖": [],
    }, ensure_ascii=False, indent=2))

    return p.root


def main() -> int:
    code = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROJECT
    root = build(code)
    print(f"✅ 已產生乾淨交付專案：{root}")
    print("   驗收：python scripts/verify_outputs.py " + code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
