#!/usr/bin/env python3
"""
交付 gate —— 產出前的機械化驗收，任一項 error 即不得輸出。

為什麼需要它：
  這支腳本是六份 reference 的匯流點（18 §八、19 §1.8/§5.4/§6.2、20 §八/§九、
  00 §四/§1.5、14 §九、03 §1.2），**不是提醒清單，是退出碼會擋住實作的 gate**。
  沒有它會發生什麼，每一條都有實證：
    · 27 人（全班最大扣分群）只漏了「ANOVA 後的事後檢定」，A+ 掉到 A（18-E1）
    · 學生E 圖例標「女 75.20%」、內文寫「女性佔 24.8%」，兩個數字來源必然對不上（18-E7）
    · 學生E 購物籃 Top 12 相關係數全部 = 1，因為共現只有 1 次（18-E10）
    · 學生K ANOVA 表某格 3217.258、同欄其他值都在 3.2~3.5，沒人發現（18-E9）
    · 學生J 把 CAI 寫成 Category Expansion Index（18-E6）
  這些都是「人眼看得到但沒人會每次看」的錯誤 —— 正是該交給機器的那一類。

退出碼（沿用 20 §九）：
    0 = 全綠，可交付
    1 = 有 error，**不得輸出**。回去修，不要用「先寄一版」繞過
    2 = 僅 warning，可交付，但每一條都要在《進度與異狀.md》登錄並配一條處理

用法：
    python verify_outputs.py 2026Q3_電商
    python verify_outputs.py 2026Q3_電商 --list           # 列出所有檢查代號
    python verify_outputs.py 2026Q3_電商 --only T01,T05   # 只跑這幾條
    python verify_outputs.py 2026Q3_電商 --skip D05,F01   # 跳過這幾條
    python verify_outputs.py 2026Q3_電商 --only R         # 跑整個 R 分類
    python verify_outputs.py 2026Q3_電商 --verbose        # 連通過項也列出
    python verify_outputs.py 2026Q3_電商 --json 結果.json # 另存機器可讀結果
    python verify_outputs.py --static-only                # 只跑不需要專案的靜態檢查

── 這支腳本讀什麼（交付物層的輸入契約）────────────────────────────
    交付物/完整報告.html            11 章骨架、排版件、數字 token
    交付物/決策摘要.html            14 §六
    交付物/report_meta.json         build_report.py 產出的章節／排版／頁數／數字來源
    交付物/sizing.csv               14 §三，每條建議一列
    交付物/action_brief_<rec>.md    14 §五，一頁一策略
    圖表/報告用/manifest.json       collect_figures.py 產出（含 sha256、口徑）
    統計表/**/*.csv                 utf-8-sig，最後一欄中文結論
    模型輸出/bundle.json            result_bundle.py 匯出的 Result 表
    模型輸出/analysis_objects.json  ANOVA／事後檢定／分群輸入／證據檢查物件索引
    專案記憶/指標字典.csv           dim_metric_definition（18-G10）
    執行紀錄/run_manifest.json      版本三件套（20 §十）
    執行紀錄/degradation_log.md     N/A 的來由（00 §四）

【此處為實作判斷】references 只規定了「要檢查什麼」，沒有規定這些中繼檔的檔名與
schema（result_bundle.py / collect_figures.py / stamp_version.py 都還沒實作）。
上表的檔名與欄位是本腳本訂的契約，那三支腳本實作時要對齊；schema 不合會報成
「缺檔／欄位不符」而不是靜默跳過。

【此處為實作判斷】14 §九 的 M11_ARTIFACTS 用了編號式英文目錄，與 03 §1.2
「這份 skill 裡不存在編號式英文目錄」直接衝突。本腳本一律走 `交付物/`，
並由 R01 把 14 §九 那 12 處硬編路徑掃出來報成 error —— 不默默吞掉。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SKILL_ROOT, ProjectPaths, projects_root  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ══════════════════════════════════════════════════════════════════
# 一、規格常數（全部抄自 references，改動要回去改 reference 再同步）
# ══════════════════════════════════════════════════════════════════

# 19 §1.8 —— verify_outputs.py 直接讀這張表
REQUIRED_FIGURES: dict[str, int] = {
    "M1": 6, "M2": 4, "M3": 5, "M4": 4, "M7": 5,
    "M6": 8,      # elbow/silhouette/gap/PCA/指標熱圖/parallel/bootstrapARI/KMeans×HDBSCAN
                  # 群大小水平長條為選配，不計入（同 07 §十）
    "M8-1": 10,   # RFM熱圖/RFM分布/CAI-CDF/CAI三群/CRI散點×2/CLV帕累托/cohort/桑基/KM
    "M8-2": 7, "M8-3": 6, "M9": 8, "M10": 5,
}
FORBIDDEN: list[str] = ["wordcloud", "radar", "pie_gt5", "chart3d", "dual_axis"]

# 19 §4.3 的禁用規則落成 lint：檔名圖種 → 為什麼禁
FORBIDDEN_FIGURE_KINDS: dict[str, str] = {
    "wordcloud": "字級對應詞頻但面積非線性、排版隨機、兩張圖無法比較（19 §4.3、13）",
    "radar": "面積隨軸的排列順序改變，換個軸序就換個結論（19 §4.3）",
    "spider": "同雷達圖（19 §4.3）",
    "chart3d": "透視造成遮蔽與面積失真（19 §4.3）",
    "3d": "透視造成遮蔽與面積失真（19 §4.3）",
    "dual_axis": "兩軸縮放可任意調整，同一組資料可做出兩種相反結論（19 §4.3）",
    "dualaxis": "同雙 Y 軸（19 §4.3）",
    "pie_gt5": "類別 >5 的圓餅全禁（19 §4.3）",
}
# 圓餅要看類別數才判得了，manifest 沒給類別數就當它超標
PIE_KINDS = {"pie", "donut", "doughnut"}
PIE_MAX_CATEGORIES = 5

# 產圖程式碼層的禁用寫法（19 §4.3）：(regex, 桶, 為什麼)
FORBIDDEN_CODE_PATTERNS: list[tuple[str, str, str]] = [
    (r"\.twinx\s*\(", "error",
     "matplotlib twinx() = 雙 Y 軸，除固定線性單位換算外全禁（19 §4.3）"),
    (r"secondary_y\s*=\s*True", "error", "pandas/plotly 雙 Y 軸，同上（19 §4.3）"),
    (r"\bwordcloud\b", "error", "文字雲全面禁用（19 §1.8、19 §4.3）"),
    (r"projection\s*=\s*['\"]3d['\"]", "error", "3D 圖表全禁（19 §4.3）"),
    (r"polar\s*=\s*True", "error", "極座標＝雷達圖的實作，全禁（19 §4.3）"),
    (r"mark_arc\s*\(|\bplt\.pie\s*\(|\.plot\.pie\s*\(", "warning",
     "圓餅／甜甜圈：類別 >5 全禁、任何時間維度絕對禁、≤5 且需精讀數值也禁（19 §4.3）"),
]

# 19 §6.1 圖種固定詞彙表（新增要先進這張表）
FIGURE_KIND_VOCAB = {
    "hist", "box", "qqplot", "scatter", "line", "barh", "bar", "heatmap",
    "sankey", "waterfall", "pareto", "network", "parallel", "elbow",
    "silhouette", "gap", "pca", "coefplot", "diag2x2", "roc", "pr", "lift",
    "calibration", "shap_summary", "shap_dep", "confusion", "learning",
    "cohort", "km", "stl", "elasticity", "funnel", "quadrant", "dumbbell",
    "lollipop", "cdf",
}

# 18 §四 術語對照表（E6 的自動驗證來源）
GLOSSARY: dict[str, tuple[str, list[str]]] = {
    "CAI": ("Customer Activity Index",
            ["Category Expansion Index", "Customer Acquisition Index",
             "Customer Engagement Index"]),
    "CRI": ("Customer Reliability Index",
            ["Customer Retention Index", "Customer Relationship Index"]),
    "RFM": ("Recency / Frequency / Monetary", ["Regency"]),
    "ARFM": ("Activity / Recency / Frequency / Monetary", []),
    "MLE": ("Mean interpurchase time", []),
    "WMLE": ("Weighted Mean interpurchase time", []),
    "CLV": ("Customer Lifetime Value", ["Customer Reliability Index"]),
}

# 18-E2 分群輸入變數白名單
CLUSTER_INPUT_WHITELIST = {
    "R", "F", "M", "RFM", "RFM_SCORE", "RFMSCORE", "CAI", "CRI",
    "LN_F", "LN_M", "FACTOR", "因素分數",
}
CLUSTER_INPUT_PREFIX_OK = ("FACTOR", "因素")   # 因素分數 1/2/3…

# 00 §1.5 證據等級四級 + 措辭白名單
EVIDENCE_LEVELS = ["相關", "預測", "準實驗", "實驗"]
EVIDENCE_NEEDS_OBJECT = {"準實驗", "實驗"}
FORBIDDEN_VERBS: dict[str, list[str]] = {
    "相關": ["造成", "帶動", "驅動", "導致", "提升了", "貢獻了", "增量",
             "因為", "所以能"],
    "預測": ["造成", "帶來", "只要做", "就會"],
    "準實驗": ["證實", "確定", "必然", "就是"],
    "實驗": [],
}
# 沒有實驗時絕對不能說的三句話（00 §1.5）
ABSOLUTE_BANNED = [
    (r"廣告.{0,8}使.{0,10}提升", "「廣告使購買率提升 X%」沒有實驗不能說（00 §1.5）"),
    (r"帶來.{0,6}增量訂單", "「這檔活動帶來 X 筆增量訂單」沒有實驗不能說（00 §1.5）"),
    (r"ROAS.{0,20}加碼", "「ROAS = 6.0 所以應該加碼」沒有實驗不能說（00 §1.5）"),
]

# 20 §3.1 十一章骨架（缺一章就掉級）
CHAPTERS: list[str] = [
    "資料描述", "RFM 模型", "CAI 指標", "CRI 指標", "購物籃分析",
    "因素分析", "集群分析", "卡方檢定", "F 檢定／ANOVA",
    "事後檢定／獨立 t", "結論與管理者建議",
]
# 20 §3.1 排版側 9 個 Check 項，模板固定件，不可關閉（18-E4）
LAYOUT_ITEMS: list[str] = [
    "封面", "摘要", "目錄", "表目錄", "圖目錄", "頁碼",
    "章節大小標", "表格自製", "跨頁續表頭",
]
SUMMARY_MIN_CHARS, SUMMARY_MAX_CHARS = 150, 400      # 18-E19
SUMMARY_BANNED_OPENING = "本章分析了"                  # 18-E19
PAGES_ERROR_BELOW, PAGES_WARN_BELOW = 15, 20         # 18-E5
SIZE_LIMIT_MB = 10                                    # 20 §3.2

# 00 §四 / 18 §八：不得洩漏到交付檔的字串
LEAK_TOKENS = ["nan", "inf", "-inf", "+inf", "#div/0!", "#name?", "#value!",
               "#ref!", "#n/a", "#null!", "none", "nat"]
LEAK_TOKENS_EXACT = {t for t in LEAK_TOKENS}

# 19 §5.4：百分比加總誤差門檻、數量級離群門檻
PCT_SUM_TOL = 0.5
MAGNITUDE_RATIO = 100.0
SHARE_HEADER_HINTS = ("佔比", "占比", "比重", "組成", "構成", "share", "構面比")
PCT_HEADER_HINTS = ("%", "百分比", "比例", "pct")
PCT_HEADER_EXCLUDE = ("累積", "累计", "cum", "變化", "增減", "成長", "差異",
                      "反應率", "轉換率", "留存率", "命中率", "誤差")

# 03 §1.2：references 與腳本裡不得出現的編號式英文目錄
NUMBERED_DIR_RE = re.compile(r"\b(\d{2}_[A-Za-z][A-Za-z0-9_\-]*)/")
# 03 §1.2 管的是「專案樹」的目錄命名。repo 自己的頂層資料夾（00_source_archive、
# 10_blueprint、20_skill、90_scratch…）是既存的專有名詞，不在管轄範圍內 ——
# 所以白名單是「repo 根目錄實際存在的資料夾名」，不用手維護一張表。
NUMBERED_DIR_ALLOW: set[str] = {"00_source_archive"}


def _repo_dir_allowlist() -> set[str]:
    allow = set(NUMBERED_DIR_ALLOW)
    repo = SKILL_ROOT.parent.parent
    try:
        allow |= {d.name for d in repo.iterdir() if d.is_dir()}
    except OSError:
        pass
    return allow


# 反例行：文件正在「宣告這種寫法是錯的」，不算違規
NEGATIVE_EXAMPLE_MARKERS = ("不存在", "筆誤", "禁止出現", "不得出現",
                            "verify-outputs:allow")
STATIC_SCAN_SUFFIXES = {".md", ".py", ".sql", ".yml", ".yaml", ".j2"}

FIG_NAME_RE = re.compile(
    # topic 非貪婪：kind 要吃到最長的英文尾段（shap_summary 不能被拆成 summary）
    r"^(?P<module>M\d+(?:-\d+)?)_(?P<topic>.+?)_(?P<kind>[a-z0-9]+(?:_[a-z0-9]+)*)"
    r"\.(?:png|svg|jpg|jpeg)$", re.IGNORECASE
)
NUM_TOKEN_RE = re.compile(r"(?<![\w.])[−\-]?\d[\d,]*(?:\.\d+)?\s?%?")
HTML_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", re.S | re.I)
NS_RE = re.compile(r"(?<![A-Za-z.])n\.?s\.?(?![A-Za-z])", re.I)


# ══════════════════════════════════════════════════════════════════
# 二、結果容器
# ══════════════════════════════════════════════════════════════════

LEVEL_ICON = {"error": "⛔", "warning": "⚠", "info": "✅"}


@dataclass
class Finding:
    """一條檢查結果。三個欄位對應「哪一條、在哪個檔、怎麼修」。"""
    check_id: str
    level: str          # error / warning / info
    fact: str           # 事實
    fix: str            # 該怎麼辦
    where: str = ""     # 在哪個檔（專案相對路徑或絕對路徑）


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    ran: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def add(self, check_id: str, level: str, fact: str, fix: str,
            where: str | Path = "") -> None:
        self.findings.append(
            Finding(check_id, level, fact, fix, str(where))
        )

    def by_level(self, level: str) -> list[Finding]:
        return [f for f in self.findings if f.level == level]


# ══════════════════════════════════════════════════════════════════
# 三、輸入載入（惰性；缺檔不 crash，回報成 error 並說怎麼修）
# ══════════════════════════════════════════════════════════════════

@dataclass
class Ctx:
    """一次驗收所需的全部輸入。缺什麼由各檢查自己抱怨。"""
    project: str
    p: ProjectPaths | None
    scan_root: Path
    rep: Report
    _cache: dict[str, Any] = field(default_factory=dict)

    # ── 小工具 ────────────────────────────────────────────
    def rel(self, path: Path) -> str:
        if self.p is None:
            return str(path)
        try:
            return str(path.relative_to(self.p.root))
        except ValueError:
            return str(path)

    def need_json(self, check_id: str, path: Path, produced_by: str) -> Any | None:
        """讀一份必要的 JSON。缺檔／壞檔都報 error 並回 None。"""
        key = f"json:{path}"
        if key in self._cache:
            return self._cache[key]
        val: Any | None = None
        if not path.exists():
            self.rep.add(check_id, "error",
                         f"找不到 {self.rel(path)}",
                         f"跑 {produced_by} 產生它；沒有它這條檢查等於沒做過",
                         self.rel(path))
        else:
            try:
                val = json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                self.rep.add(check_id, "error",
                             f"{self.rel(path)} 不是合法 JSON（{e}）",
                             f"重跑 {produced_by} 重新產生，不要手動編輯這個檔",
                             self.rel(path))
        self._cache[key] = val
        return val

    # ── 各輸入 ────────────────────────────────────────────
    def meta(self, check_id: str) -> dict | None:
        return self.need_json(check_id, self.p.deliverables / "report_meta.json",
                              "build_report.py（20 §3.2）")

    def bundle(self, check_id: str) -> dict | None:
        return self.need_json(check_id, self.p.models / "bundle.json",
                              "result_bundle.py（20 §2.2）")

    def objects(self, check_id: str) -> dict | None:
        return self.need_json(check_id, self.p.models / "analysis_objects.json",
                              "建模腳本收斂輸出（08／16／07）")

    def manifest(self, check_id: str) -> dict | None:
        return self.need_json(check_id, self.p.figures / "報告用" / "manifest.json",
                              "collect_figures.py（19 §6.2）")

    def run_manifest(self, check_id: str) -> dict | None:
        return self.need_json(check_id, self.p.log / "run_manifest.json",
                              "stamp_version.py（20 §十）")

    def stat_tables(self) -> list[Path]:
        if "tables" not in self._cache:
            self._cache["tables"] = sorted(self.p.tables.rglob("*.csv"))
        return self._cache["tables"]

    def text_deliverables(self) -> list[Path]:
        """可讀成純文字的交付檔。"""
        if "textdeliv" not in self._cache:
            out = []
            if self.p.deliverables.exists():
                for pat in ("*.html", "*.md", "*.htm", "*.csv", "*.txt"):
                    out += sorted(self.p.deliverables.rglob(pat))
            self._cache["textdeliv"] = out
        return self._cache["textdeliv"]

    def figures(self) -> list[Path]:
        """圖表/ 底下所有圖檔（含 報告用/）。"""
        if "figs" not in self._cache:
            out = []
            if self.p.figures.exists():
                for pat in ("*.png", "*.svg", "*.jpg", "*.jpeg"):
                    out += sorted(self.p.figures.rglob(pat))
            self._cache["figs"] = out
        return self._cache["figs"]


# ══════════════════════════════════════════════════════════════════
# 四、共用小函式
# ══════════════════════════════════════════════════════════════════

def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp950"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", HTML_TAG_RE.sub(" ", s))


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """回 (表頭, 每列的原始字串)。刻意不轉型 —— 空白格與 'N/A' 都要看得見。"""
    raw = read_text(path)
    rdr = csv.reader(io.StringIO(raw))
    rows = [r for r in rdr]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def to_num(s: str) -> float | None:
    """把表格裡的字串轉數字。處理千分位、U+2212 負號、百分比、括號負數。"""
    if s is None:
        return None
    t = s.strip().replace(",", "").replace("−", "-").replace("　", "")
    if not t:
        return None
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    if t.endswith("%"):
        t = t[:-1]
    if t.startswith("+"):
        t = t[1:]
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_total_row(cells: list[str]) -> bool:
    head = (cells[0] if cells else "").strip().lower()
    return head in {"合計", "總計", "小計", "total", "sum", "全體", "全部"}


def find_col(header: list[str], *hints: str) -> int:
    for i, h in enumerate(header):
        low = h.strip().lower()
        for hint in hints:
            if hint.lower() in low:
                return i
    return -1


# ══════════════════════════════════════════════════════════════════
# 五、檢查實作
#     每一支簽名固定 (ctx) -> None，自己往 ctx.rep 丟 Finding。
# ══════════════════════════════════════════════════════════════════

# ── 結構（20 §九「結構」桶）──────────────────────────────

def chk_S01_chapters(c: Ctx) -> None:
    """11 章 checklist 全綠（缺章即 error，不得以「資料不足」略過，18-E3）"""
    meta = c.meta("S01")
    if meta is None:
        return
    got = {str(ch.get("標題", "")).strip(): ch for ch in meta.get("章節", [])}
    for i, name in enumerate(CHAPTERS, 1):
        ch = got.get(name)
        if ch is None:
            c.rep.add("S01", "error",
                      f"第 {i} 章「{name}」不在 report_meta.json 的章節清單裡",
                      "把這章補進 templates/報告骨架.html.j2 並重跑 build_report.py；"
                      "適配不佳要保留章節+說明替代方案（18-E11），不准刪章",
                      "交付物/report_meta.json")
        elif str(ch.get("狀態", "")).strip() not in {"完成", "綠", "ok", "OK"}:
            c.rep.add("S01", "error",
                      f"第 {i} 章「{name}」狀態是「{ch.get('狀態')}」不是完成",
                      "把該章跑完；「資料不足」要降級輸出替代分析並寫理由（00 §1.6），不是留空",
                      "交付物/report_meta.json")


def chk_S02_layout(c: Ctx) -> None:
    """9 個排版件齊備，模板固定件不可關閉（18-E4）"""
    meta = c.meta("S02")
    if meta is None:
        return
    lay = meta.get("排版件", {})
    for item in LAYOUT_ITEMS:
        if not lay.get(item):
            c.rep.add("S02", "error",
                      f"排版件「{item}」未標記完成",
                      "這 9 項是模板固定件不可關閉（18-E4；學生J 缺封面/目錄/頁碼拿 C+）。"
                      "回去補 templates/報告骨架.html.j2",
                      "交付物/report_meta.json")


def chk_S03_summaries(c: Ctx) -> None:
    """每章都有小結，150–400 字，且不以「本章分析了」開頭（18-E19）"""
    meta = c.meta("S03")
    if meta is None:
        return
    for ch in meta.get("章節", []):
        title = str(ch.get("標題", "?"))
        s = str(ch.get("小結", "") or "").strip()
        if not s:
            c.rep.add("S03", "error",
                      f"「{title}」沒有小結",
                      "小結公式＝發現（帶數字）+ 經營意涵 +（可選）承接下一章，"
                      "模板見 00 §2.3",
                      "交付物/report_meta.json")
            continue
        if s.startswith(SUMMARY_BANNED_OPENING):
            c.rep.add("S03", "error",
                      f"「{title}」的小結以「{SUMMARY_BANNED_OPENING}」開頭",
                      "改成帶數字的發現句（18-E19）：「A 群客單價 3,210 元、是 B 群的 2.4 倍，"
                      "因此…」",
                      "交付物/report_meta.json")
        n = len(re.sub(r"\s", "", s))
        if not (SUMMARY_MIN_CHARS <= n <= SUMMARY_MAX_CHARS):
            c.rep.add("S03", "warning",
                      f"「{title}」的小結 {n} 字，不在 {SUMMARY_MIN_CHARS}–{SUMMARY_MAX_CHARS} 字之間",
                      "太短補經營意涵、太長把細節搬回內文（20 §3.1【實測】）",
                      "交付物/report_meta.json")


def chk_S04_pages(c: Ctx) -> None:
    """頁數 ≥15（<15 error、<20 warning、目標 25–35）（18-E5）"""
    meta = c.meta("S04")
    if meta is None:
        return
    pages = meta.get("頁數")
    if not isinstance(pages, int):
        c.rep.add("S04", "error",
                  "report_meta.json 沒有整數的「頁數」欄",
                  "build_report.py 渲染後要把頁數寫回 meta；沒有頁數就驗不了 18-E5",
                  "交付物/report_meta.json")
        return
    if pages < PAGES_ERROR_BELOW:
        c.rep.add("S04", "error", f"報告只有 {pages} 頁",
                  f"<{PAGES_ERROR_BELOW} 頁不得輸出（18-E5：5 份 <10 頁的報告全部拿不到 A+）。"
                  "目標 25–35 頁", "交付物/report_meta.json")
    elif pages < PAGES_WARN_BELOW:
        c.rep.add("S04", "warning", f"報告 {pages} 頁",
                  f"<{PAGES_WARN_BELOW} 頁觸發警告（18-E5），目標 25–35 頁",
                  "交付物/report_meta.json")


# ── 統計（20 §九「統計」桶）──────────────────────────────

def chk_T01_anova_posthoc(c: Ctx) -> None:
    """每個 ANOVA 都有對應的事後檢定結果物件（18-E1，27 人掉級的那一條）"""
    obj = c.objects("T01")
    if obj is None:
        return
    anovas = obj.get("anova", [])
    posthoc_ids = {str(p.get("id")) for p in obj.get("posthoc", [])}
    if not anovas:
        c.rep.add("T01", "warning", "analysis_objects.json 裡沒有任何 ANOVA 物件",
                  "若真的沒跑 ANOVA 可忽略；若跑了沒登錄，補 stats_utils 的輸出（08 §121）",
                  "模型輸出/analysis_objects.json")
    for a in anovas:
        aid = str(a.get("id", "?"))
        ph = str(a.get("posthoc_id", "") or "")
        if not ph:
            c.rep.add("T01", "error", f"ANOVA 物件「{aid}」沒有 posthoc_id",
                      "ANOVA→事後檢定是綁定的不可分離；跑不出來要沿階梯降級"
                      "（Tukey HSD → Games-Howell → Dunn(BH) → 獨立 t(BH) → 敘述統計）"
                      "並寫降級理由，不准留空（18-E1、00 §1.6）",
                      "模型輸出/analysis_objects.json")
        elif ph not in posthoc_ids:
            c.rep.add("T01", "error",
                      f"ANOVA 物件「{aid}」指向的 posthoc「{ph}」不存在",
                      "把事後檢定結果物件實際寫進 模型輸出/，不要只在 ANOVA 上掛一個 id",
                      "模型輸出/analysis_objects.json")


def chk_T02_cluster_inputs(c: Ctx) -> None:
    """分群輸入變數全在白名單內（18-E2）"""
    obj = c.objects("T02")
    if obj is None:
        return
    inputs = obj.get("分群輸入變數")
    if inputs is None:
        c.rep.add("T02", "error", "analysis_objects.json 沒有「分群輸入變數」",
                  "M6 收斂時要把實際進矩陣的欄位寫進來，否則 18-E2 驗不了",
                  "模型輸出/analysis_objects.json")
        return
    for v in inputs:
        key = str(v).strip().upper().replace(" ", "_")
        okay = (key in CLUSTER_INPUT_WHITELIST
                or key.startswith(CLUSTER_INPUT_PREFIX_OK)
                or str(v).startswith("因素"))
        if not okay:
            c.rep.add("T02", "error", f"分群輸入變數「{v}」不在白名單內",
                      "白名單只有 R／F／M／RFM Score／CAI／CRI（有條件）／因素分數／LN_F／LN_M。"
                      "人口變數只能出現在卡方那一章（18-E2：學生H 用性別×婚姻分群拿 B+）",
                      "模型輸出/analysis_objects.json")
    # CRI 的附加條件：先驗群必須以行為分層（18-E2 ⚠）
    if any(str(v).strip().upper() == "CRI" for v in inputs):
        basis = str(obj.get("分群先驗群依據", "") or "")
        if "行為" not in basis:
            c.rep.add("T02", "error",
                      f"分群輸入含 CRI，但先驗群依據是「{basis or '未填'}」不是行為分層",
                      "CRI≡W2×100，W2 的分母含先驗群的群內變異數；先驗群若用人口變數分，"
                      "交易紀錄完全相同的兩人會拿到不同 CRI（實測 21.4 vs 79.1）。"
                      "改用行為分層，或把 CRI 移出分群輸入（18-E2、07 §3.1）",
                      "模型輸出/analysis_objects.json")


def chk_T03_pct_sum(c: Ctx) -> None:
    """百分比欄加總 ≈100（誤差 <0.5）（18-E9 同段、19 §5.4）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not header:
            continue
        body = [r for r in rows if not is_total_row(r)]
        for i, h in enumerate(header):
            low = h.strip().lower()
            is_share = any(k.lower() in low for k in SHARE_HEADER_HINTS)
            is_pct = any(k.lower() in low for k in PCT_HEADER_HINTS)
            if any(k.lower() in low for k in PCT_HEADER_EXCLUDE):
                continue
            if not (is_share or is_pct):
                continue
            vals = [to_num(r[i]) for r in body if i < len(r)]
            vals = [v for v in vals if v is not None]
            if len(vals) < 2:
                continue
            s = sum(vals)
            off = abs(s - 100.0)
            # 【此處為實作判斷】明確的組成欄一律驗；只是掛 % 的欄，僅當總和落在
            # 90–110 帶（明顯想湊 100 卻沒湊到）才報，避免把「反應率」這種
            # 逐列比率欄誤判成組成欄。
            if is_share:
                if off > PCT_SUM_TOL:
                    c.rep.add("T03", "error",
                              f"「{h}」欄加總 {s:.2f}%，偏離 100 達 {off:.2f}",
                              "回去看是不是漏了「其他」列、或四捨五入沒做最大餘額法；"
                              f"誤差上限 {PCT_SUM_TOL}（19 §5.4）", c.rel(path))
            elif 90.0 <= s <= 110.0 and off > PCT_SUM_TOL:
                c.rep.add("T03", "error",
                          f"「{h}」欄加總 {s:.2f}%，偏離 100 達 {off:.2f}",
                          "這欄看起來是組成欄卻湊不到 100。補「其他」列或改用最大餘額法；"
                          "若它本來就不是組成欄，把欄名改清楚（如「反應率」）避免誤判",
                          c.rel(path))


def chk_T04_magnitude(c: Ctx) -> None:
    """同欄數值無數量級差 >100 倍的離群（18-E9）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not header:
            continue
        body = [r for r in rows if not is_total_row(r)]
        for i, h in enumerate(header):
            if any(k in h for k in ("n", "N", "人數", "筆數", "樣本")):
                continue          # 樣本數天生跨數量級，不適用
            vals = [(to_num(r[i]), r[0] if r else "?", r[i].strip())
                    for r in body if i < len(r)]
            pairs = [(abs(v), lbl, raw) for v, lbl, raw in vals
                     if v is not None and v != 0]
            if len(pairs) < 3:
                continue
            # 【此處為實作判斷】上界 ≤1 的欄（p 值、r、效果量、比率）天生跨數量級：
            # p=0.002 與 p=0.471 差 235 倍是正常的，不是打錯位數。18-E9 抓的是
            # 3217.258 混在 3.2~3.5 裡那種無界量，所以只驗有值 >1 的欄。
            if max(v for v, _, _ in pairs) <= 1.0:
                continue
            lo = min(pairs)
            hi = max(pairs)
            if hi[0] / lo[0] > MAGNITUDE_RATIO:
                c.rep.add("T04", "warning",
                          f"「{h}」欄最大 {hi[2]}（列「{hi[1]}」）是最小 {lo[2]}"
                          f"（列「{lo[1]}」）的 {hi[0]/lo[0]:.0f} 倍",
                          "先確認不是打錯位數（18-E9：學生K 的 ANOVA 表某格 3217.258、"
                          "同欄其他值都在 3.2~3.5，A+ 報告也沒人發現）。"
                          "確認是真值就在結論欄說明，別讓讀者自己嚇到", c.rel(path))


def chk_T05_r_equals_one(c: Ctx) -> None:
    """|r|=1 的格子都已標「樣本不足，不可解讀」（18-E10）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not header:
            continue
        is_corr_table = ("相關" in path.stem or "corr" in path.stem.lower())
        corr_cols = [i for i, h in enumerate(header)
                     if h.strip().lower() in {"r", "corr"} or "相關係數" in h]
        if not is_corr_table and not corr_cols:
            continue
        cols = corr_cols if corr_cols else list(range(1, len(header)))
        for r in rows:
            row_label = (r[0] if r else "").strip()
            flagged = any("樣本不足" in cell for cell in r)
            for i in cols:
                if i >= len(r):
                    continue
                if is_corr_table and not corr_cols and header[i].strip() == row_label:
                    continue                      # 矩陣對角線，自己對自己本來就是 1
                v = to_num(r[i])
                if v is None or abs(abs(v) - 1.0) > 1e-9:
                    continue
                if not flagged:
                    c.rep.add("T05", "error",
                              f"列「{row_label}」欄「{header[i]}」的 r = {r[i].strip()}，"
                              "同列沒有「樣本不足」標記",
                              "相關矩陣要設最低共現門檻 n≥5，r=±1 一律標"
                              "「樣本不足，不可解讀」（18-E10：學生E 的 Top 12 購物籃組合"
                              "相關係數全部 =1，因為兩商品只被同一人買過）", c.rel(path))
                    break


def chk_T06_conclusion_col(c: Ctx) -> None:
    """每張統計表最後一欄非空且非純數字（18-E15）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not header:
            c.rep.add("T06", "error", f"{path.name} 是空檔",
                      "空的統計表不要交；不做就從 統計表/ 移走並在《進度與異狀.md》寫理由",
                      c.rel(path))
            continue
        last = len(header) - 1
        head_ok = any(k in header[last] for k in ("結論", "解讀", "判定", "意涵", "說明"))
        if not head_ok:
            c.rep.add("T06", "warning",
                      f"最後一欄欄名是「{header[last]}」，看不出是中文結論欄",
                      "每張統計表最後一欄必須是中文結論 —— 這一欄是統計章存在的唯一理由"
                      "（18-E15）", c.rel(path))
        for n, r in enumerate(rows, 2):
            cell = (r[last] if last < len(r) else "").strip()
            if not cell:
                c.rep.add("T06", "error", f"第 {n} 列的結論欄是空的",
                          "空白格有「沒算」與「算出來是零」兩種讀法（00 §四）。"
                          "寫一句中文結論，不顯著也要寫（18-E16）", c.rel(path))
            elif to_num(cell) is not None:
                c.rep.add("T06", "error",
                          f"第 {n} 列的結論欄是純數字「{cell}」",
                          "結論欄要寫商業意涵不是再放一個統計量（18-E15）", c.rel(path))


def chk_T07_ns_needs_mde(c: Ctx) -> None:
    """標 n.s. 的列必須有同列的 mde 欄且非空（00 §四、18-E17）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not header:
            continue
        mde_i = find_col(header, "mde", "最小可偵測")
        for n, r in enumerate(rows, 2):
            # n.s. 可能單獨成格，也可能寫在結論句裡（「n.s.；這個樣本量看不出…」）
            if not any(NS_RE.search(cell) for cell in r):
                continue
            if mde_i < 0:
                c.rep.add("T07", "error",
                          f"第 {n} 列標了 n.s.，但這張表沒有 mde 欄",
                          "「沒差異」與「看不出差異」是兩件事。加一欄 MDE："
                          "(z_{1-α/2}+z_{1-β})·s·√(1/n1+1/n2)，"
                          "結論寫「這個樣本量看不出 X 以內的差異」（00 §四）",
                          c.rel(path))
                break
            if mde_i >= len(r) or not r[mde_i].strip():
                c.rep.add("T07", "error",
                          f"第 {n} 列標了 n.s.，但 mde 欄是空的",
                          "補上 MDE 數值；算不出來要寫 N/A 並在 degradation_log.md 記原因"
                          "（00 §四）", c.rel(path))


# ── 儲存格符號紀律（00 §四 CELL_RULES）──────────────────

def chk_C01_blank_cells(c: Ctx) -> None:
    """交付檔中不存在空白格（None / '' / 純空白字串）（00 §四）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not header:
            continue
        for n, r in enumerate(rows, 2):
            for i in range(len(header)):
                cell = (r[i] if i < len(r) else "")
                if cell.strip() == "":
                    c.rep.add("C01", "error",
                              f"第 {n} 列「{header[i]}」欄是空白格",
                              "三選一填滿：算得出來且為零填 0；有樣本算不出來填 N/A；"
                              "根本沒樣本填 -。任何情況都不准留白（00 §四）", c.rel(path))


def chk_C02_leak_tokens(c: Ctx) -> None:
    """無 NaN / inf / #DIV/0! / #NAME? 洩漏到交付檔（18 §八、00 §四）"""
    targets: list[tuple[Path, list[str]]] = []
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        cells = [cell for r in rows for cell in r]
        targets.append((path, cells))
    for path in c.text_deliverables():
        txt = strip_html(read_text(path))
        # 交付文字用 token 切，避免把 "Nancy" 這種字誤判
        targets.append((path, re.findall(r"[#A-Za-z/0-9!?\.\-]+", txt)))
    for path, cells in targets:
        seen: set[str] = set()
        for cell in cells:
            t = cell.strip().lower()
            if t in LEAK_TOKENS_EXACT and t not in seen:
                seen.add(t)
                c.rep.add("C02", "error", f"出現 {cell.strip()!r}",
                          "數值層的 NaN/inf 要在產表時轉成 N/A（有樣本算不出來）或 -（無樣本），"
                          "Excel 錯誤值要回去修公式，不是留在交付檔（00 §四）", c.rel(path))


def chk_C03_na_needs_log(c: Ctx) -> None:
    """凡出現 'N/A' 的表，degradation_log.md 中必有對應紀錄（00 §四）"""
    log = c.p.log / "degradation_log.md"
    log_txt = read_text(log) if log.exists() else ""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        if not any(cell.strip().upper() == "N/A" for r in rows for cell in r):
            continue
        if not log.exists():
            c.rep.add("C03", "error",
                      f"{path.name} 有 N/A，但 執行紀錄/degradation_log.md 不存在",
                      "N/A ＝有樣本但算不出來，讀者會去 degradation_log.md 找原因。"
                      "把降級紀錄寫出來（00 §1.6）", c.rel(path))
            return
        if path.stem not in log_txt:
            c.rep.add("C03", "warning",
                      f"{path.name} 有 N/A，但 degradation_log.md 沒提到這張表",
                      f"在 degradation_log.md 加一段「{path.stem}：哪一格算不出來、為什麼、"
                      "用什麼替代」（00 §1.6）", c.rel(path))


def chk_C04_dash_and_zero(c: Ctx) -> None:
    """'-' 只出現在 n=0 或缺席的列；'0' 不得出現在 n=0 的格（00 §四）"""
    for path in c.stat_tables():
        header, rows = read_csv_rows(path)
        n_i = find_col(header, "人數", "筆數", "樣本數")
        if n_i < 0:
            for i, h in enumerate(header):
                if h.strip().lower() == "n":
                    n_i = i
                    break
        if n_i < 0:
            continue
        for ln, r in enumerate(rows, 2):
            n_val = to_num(r[n_i]) if n_i < len(r) else None
            has_dash = any(cell.strip() in {"-", "−", "—"} for cell in r)
            if has_dash and n_val is not None and n_val > 0:
                c.rep.add("C04", "warning",
                          f"第 {ln} 列 n={n_val:g} 卻用了 '-'",
                          "'-' 是「無樣本」專用。有樣本但算不出來要用 N/A，"
                          "兩個符號代表兩種情況不可混用（00 §四）", c.rel(path))
            if n_val == 0:
                for i, cell in enumerate(r):
                    if i != n_i and cell.strip() == "0":
                        c.rep.add("C04", "error",
                                  f"第 {ln} 列 n=0，「{header[i] if i < len(header) else i}」"
                                  "欄卻填 0",
                                  "沒有樣本要填 '-'，填 0 會被讀成「算出來是零」，"
                                  "兩者導向完全不同的行動（00 §四）", c.rel(path))


# ── 交付物（20 §九「交付物」桶）──────────────────────────

def chk_D01_figures_exist(c: Ctx) -> None:
    """圖檔全部存在且非 0 bytes（18 §八、19 §6.2 第 4 條）"""
    figs = c.figures()
    if not figs:
        c.rep.add("D01", "error", "圖表/ 底下一張圖都沒有",
                  "圖是分析當下就存的（19 §6.2）。先跑各模組的產圖，再談交付", "圖表/")
        return
    for f in figs:
        if f.stat().st_size == 0:
            c.rep.add("D01", "error", f"{f.name} 是 0 bytes",
                      "0 bytes 通常是 savefig 前就 close 了，或 vl-convert 靜默失敗。"
                      "重跑產圖並肉眼抽驗一張（20 §八）", c.rel(f))


def chk_D02_figure_hash(c: Ctx) -> None:
    """報告用/ 每張圖的 sha256 必須等於 manifest 中來源圖的 sha256（19 §6.2 第 1 條）"""
    man = c.manifest("D02")
    if man is None:
        return
    dest = c.p.figures / "報告用"
    for name, rec in man.items():
        want = str(rec.get("sha256", ""))
        copied = dest / name
        if not copied.exists():
            c.rep.add("D02", "error", f"manifest 有 {name} 但 報告用/ 沒有這個檔",
                      "重跑 collect_figures.py；不要手動搬檔（19 §6.2）", c.rel(dest))
            continue
        got = sha256_of(copied)
        if got != want:
            c.rep.add("D02", "error",
                      f"報告用/{name} 的 sha256 與 manifest 不符",
                      "有人在 報告用/ 重畫或改過圖。刪掉重跑 collect_figures.py —— "
                      "報告用/ 只准 copy 不准產圖，重畫就是製造第二個數字來源（18-E7）",
                      c.rel(copied))
        src = Path(str(rec.get("src", "")))
        if src and src.exists() and sha256_of(src) != want:
            c.rep.add("D02", "error",
                      f"來源圖 {src.name} 已被重新產生，與 manifest 記錄的版本不同",
                      "分析重跑過就要重跑 collect_figures.py 再重新 build_report.py，"
                      "否則報告裡的圖是舊資料畫的（19 §6.2）", c.rel(src))


def chk_D03_report_refs(c: Ctx) -> None:
    """報告引用的每個檔名都存在於 manifest（19 §6.2 第 2 條）"""
    man = c.manifest("D03")
    meta = c.meta("D03")
    if man is None or meta is None:
        return
    for name in meta.get("圖表引用", []):
        if name not in man:
            c.rep.add("D03", "error",
                      f"報告引用了 {name}，但它不在 報告用/manifest.json 裡",
                      "所有進報告的圖都要經 collect_figures.py 收進來；"
                      "直接引用 圖表/xxx/ 的原圖會繞過雜湊驗證（19 §6.2）",
                      "交付物/report_meta.json")


def chk_D04_figure_has_result(c: Ctx) -> None:
    """manifest 中每張圖都有對應的計算結果物件（19 §6.2 第 3 條，防手打數字 18-E7）"""
    man = c.manifest("D04")
    bundle = c.bundle("D04")
    if man is None:
        return
    if not any("result_object_id" in (rec or {}) for rec in man.values()):
        c.rep.add("D04", "warning",
                  "manifest 的每一筆都沒有 result_object_id 欄",
                  "collect_figures.py 收圖時要一併記下這張圖用的結果物件鍵，"
                  "否則「圖的數字從哪來」無法回答（19 §6.2 第 3 條）",
                  "圖表/報告用/manifest.json")
        return
    keys = set(bundle or {})
    for name, rec in man.items():
        rid = str((rec or {}).get("result_object_id", "") or "")
        if not rid:
            c.rep.add("D04", "warning", f"{name} 沒有 result_object_id",
                      "補上它在 bundle.json 的鍵；圖與內文必須同源（18-E7）",
                      "圖表/報告用/manifest.json")
        elif keys and rid not in keys and not any(k.startswith(rid) for k in keys):
            c.rep.add("D04", "error",
                      f"{name} 指向的結果物件「{rid}」不在 bundle.json 裡",
                      "重跑產出這張圖的分析並把結果寫進 Bundle，或修正鍵名",
                      "圖表/報告用/manifest.json")


def chk_D05_numbers_from_bundle(c: Ctx) -> None:
    """報告中每個數字 token 都能在 Bundle 找到對應鍵（18-E7、20 §2.2）"""
    meta = c.meta("D05")
    bundle = c.bundle("D05")
    if meta is None or bundle is None:
        return
    src_map: dict[str, dict[str, str]] = meta.get("數字來源", {}) or {}
    if not src_map:
        c.rep.add("D05", "error", "report_meta.json 沒有「數字來源」對照",
                  "build_report.py 渲染時要把每個 {{ R.fmt(key) }} 產生的字串記下來："
                  "{交付檔名: {字串: metric_id}}。沒有它就無法證明內文數字不是手打的",
                  "交付物/report_meta.json")
        return
    for path in c.text_deliverables():
        if path.suffix.lower() not in {".html", ".htm", ".md"}:
            continue
        known = src_map.get(path.name)
        if known is None:
            c.rep.add("D05", "error", f"{path.name} 沒有登錄在「數字來源」裡",
                      "四種交付物都要從同一份 Bundle 取數（20 §二）。"
                      "把這份也接上 R.fmt()，或從 交付物/ 移走", c.rel(path))
            continue
        txt = _mask_noise(strip_html(read_text(path)))
        for m in NUM_TOKEN_RE.finditer(txt):
            tok = m.group(0).strip()
            if _token_is_exempt(tok, txt, m.start()):
                continue
            if tok in known:
                mid = known[tok]
                if mid not in bundle:
                    c.rep.add("D05", "error",
                              f"「{tok}」宣稱來自 metric_id「{mid}」，但 bundle.json 沒這個鍵",
                              "重跑 result_bundle.py，或修正模板裡的鍵名（KeyError = 你手打了）",
                              c.rel(path))
                continue
            c.rep.add("D05", "error", f"內文出現數字「{tok}」但不在數字來源對照裡",
                      "內文數字一律 {{ R.fmt(\"metric_id\") }}，不准手打 —— "
                      "18-E7 的實證是圖例寫「女 75.20%」、內文寫「女性佔 24.8%」，"
                      "兩個來源遲早不一致", c.rel(path))


# 日期／時間／雜湊／版本號不是統計數字，掃 token 前先遮掉。
# 不遮的話「2012 年 12 月 1 日」會被拆成 12、12、1 三個「未登錄的數字」，
# D05 就會在每一份真實報告上噴滿假警報。
NOISE_PATTERNS = [
    r"民國\s*\d{1,3}\s*年(\s*\d{1,2}\s*月)?(\s*\d{1,2}\s*日)?",
    r"\d{4}\s*年(\s*\d{1,2}\s*月)?(\s*\d{1,2}\s*日)?",
    r"\d{1,2}\s*月\s*\d{1,2}\s*日",
    r"\d{4}[-/.]\d{1,2}([-/.]\d{1,2})?",
    r"\d{1,2}:\d{2}(:\d{2})?",
    r"\b[0-9a-f]{7,40}\b",
    r"\bv?\d+\.\d+\.\d+\b",
    r"\b\d{4}\s*Q[1-4]\b",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.I)


def _mask_noise(txt: str) -> str:
    return NOISE_RE.sub(lambda m: " " * len(m.group(0)), txt)


def _token_is_exempt(tok: str, txt: str, pos: int) -> bool:
    """排除章節號、表號、圖號、年份、單純序號 —— 這些不是統計數字。"""
    before = txt[max(0, pos - 6):pos]
    if re.search(r"[表圖章節第頁§#]\s*$", before):
        return True
    if re.search(r"[表圖]\s*\d*\.?$", before):
        return True
    plain = tok.replace(",", "").replace("%", "").strip()
    if re.fullmatch(r"\d{4}", plain) and 1900 <= int(plain) <= 2100:
        return True
    if re.fullmatch(r"\d", plain):          # 個位數序號
        return True
    if re.fullmatch(r"\d+\.\d+", plain) and pos > 0 and txt[pos - 1] in "表圖":
        return True
    return False


def chk_D06_cross_deliverable(c: Ctx) -> None:
    """同一個 metric_id 在四種交付物中格式化後的字串完全一致（20 §2.2）"""
    meta = c.meta("D06")
    if meta is None:
        return
    src_map: dict[str, dict[str, str]] = meta.get("數字來源", {}) or {}
    seen: dict[str, dict[str, str]] = {}       # metric_id → {字串: 交付檔}
    for deliv, mapping in src_map.items():
        for token, mid in (mapping or {}).items():
            seen.setdefault(mid, {}).setdefault(token, deliv)
    for mid, variants in seen.items():
        if len(variants) > 1:
            detail = "、".join(f"{t}（{d}）" for t, d in variants.items())
            c.rep.add("D06", "error",
                      f"metric_id「{mid}」在不同交付物長得不一樣：{detail}",
                      "格式化只能發生在 Bundle.fmt() 一個地方（20 §2.2）。"
                      "會議上主管同時看到兩份、問哪個對，你答不出來就是這樣來的",
                      "交付物/report_meta.json")


def chk_D07_glossary(c: Ctx) -> None:
    """術語表驗證通過（18-E6：CAI = Customer Activity Index）"""
    for path in c.text_deliverables():
        txt = strip_html(read_text(path))
        for abbr, (right, wrongs) in GLOSSARY.items():
            for w in wrongs:
                if re.search(re.escape(w), txt, re.I):
                    c.rep.add("D07", "error",
                              f"出現錯誤術語「{w}」",
                              f"{abbr} 的正確全名是 {right}（18 §四）。"
                              "學生J 把 CAI 寫成 Category Expansion Index，C+",
                              c.rel(path))
            # 抓「CAI（...英文...）」形式的自訂展開
            for m in re.finditer(
                    rf"\b{re.escape(abbr)}\b\s*[（(：:\-—]\s*"
                    rf"([A-Za-z][A-Za-z \-/]{{5,60}})", txt):
                got = re.sub(r"\s+", " ", m.group(1)).strip(" -/")
                if _norm_term(got) != _norm_term(right) and not _norm_term(right).startswith(_norm_term(got)):
                    c.rep.add("D07", "error",
                              f"{abbr} 被展開成「{got}」",
                              f"正確全名是「{right}」（18 §四術語對照表）", c.rel(path))


def _norm_term(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def chk_D08_evidence_level(c: Ctx) -> None:
    """每條建議都帶證據等級，且措辭在該等級的白名單內（00 §1.5、18-G6）"""
    sizing = c.p.deliverables / "sizing.csv"
    if not sizing.exists():
        c.rep.add("D08", "error", "找不到 交付物/sizing.csv",
                  "14 §三：每條建議一列，欄位含 rec_id / evidence_level / "
                  "breakeven_response_rate / verdict / group_n。沒有它建議層驗不了",
                  "交付物/sizing.csv")
        return
    header, rows = read_csv_rows(sizing)
    rid_i = find_col(header, "rec_id", "建議編號")
    ev_i = find_col(header, "evidence_level", "證據等級")
    be_i = find_col(header, "breakeven", "損益兩平")
    if ev_i < 0:
        c.rep.add("D08", "error", "sizing.csv 沒有 evidence_level 欄",
                  "四級：相關／預測／準實驗／實驗，判定樹在 00 §1.5", "交付物/sizing.csv")
        return
    obj = c.objects("D08") or {}
    have_objs = {str(x) for x in obj.get("證據檢查物件", [])}
    for n, r in enumerate(rows, 2):
        rid = (r[rid_i].strip() if 0 <= rid_i < len(r) else f"第{n}列")
        lvl = (r[ev_i].strip() if ev_i < len(r) else "")
        if not lvl:
            c.rep.add("D08", "error", f"建議 {rid} 沒有證據等級",
                      "相關／預測／準實驗／實驗四選一，判定樹在 00 §1.5。"
                      "相關性直接寫成行銷建議是 18-G6", "交付物/sizing.csv")
            continue
        if lvl not in EVIDENCE_LEVELS:
            c.rep.add("D08", "error", f"建議 {rid} 的證據等級「{lvl}」不在四級白名單內",
                      f"只能是 {' / '.join(EVIDENCE_LEVELS)}（00 §1.5）", "交付物/sizing.csv")
            continue
        if lvl in EVIDENCE_NEEDS_OBJECT and not have_objs:
            c.rep.add("D08", "error",
                      f"建議 {rid} 標「{lvl}」，但 analysis_objects.json 的證據檢查物件是空的",
                      "標準實驗／實驗時對應檢查結果物件必須實際存在於 模型輸出/；"
                      "不存在就自動降級為「相關」並在報告顯示降級原因（00 §1.5）",
                      "模型輸出/analysis_objects.json")
        if be_i >= 0 and (be_i >= len(r) or not r[be_i].strip()):
            c.rep.add("D08", "error", f"建議 {rid} 的損益兩平反應率是空的",
                      "這一欄是整份提案的斷路器（14 §3.1）。算不出來寫 N/A，不准留空",
                      "交付物/sizing.csv")
        brief = c.p.deliverables / f"action_brief_{rid}.md"
        if not brief.exists():
            c.rep.add("D08", "warning", f"建議 {rid} 沒有 action_brief_{rid}.md",
                      "14 §五：一建議一頁策略書。沒有它，措辭白名單無從驗起",
                      c.rel(c.p.deliverables))
            continue
        btxt = read_text(brief)
        for verb in FORBIDDEN_VERBS.get(lvl, []):
            if verb in btxt:
                c.rep.add("D08", "error",
                          f"建議 {rid} 是「{lvl}」等級，卻用了禁用詞「{verb}」",
                          "相關級只能寫「同時／伴隨／與…相關（r=）」。"
                          "MBA5045 的養鳥／肺癌案例控制了四個共變數、p=0.0008、odds 3.80，"
                          "全篇仍然只寫「存在關聯」（00 §1.5）", c.rel(brief))


def chk_D09_absolute_bans(c: Ctx) -> None:
    """沒有實驗時絕對不能說的三句話（00 §1.5）"""
    for path in c.text_deliverables():
        txt = strip_html(read_text(path))
        for pat, why in ABSOLUTE_BANNED:
            m = re.search(pat, txt)
            if m:
                c.rep.add("D09", "error", f"出現「{m.group(0)}」", why, c.rel(path))


def chk_D10_metric_dict(c: Ctx) -> None:
    """指標口徑已標註（18-G10：dim_metric_definition + 圖表底下自動標口徑）"""
    dic = c.p.memory / "指標字典.csv"
    if not dic.exists():
        c.rep.add("D10", "error", "找不到 專案記憶/指標字典.csv",
                  "18-G10：指標口徑要有單一真相。建 dim_metric_definition，"
                  "欄位至少 metric_id / 中文名 / 口徑 / 計算窗", "專案記憶/指標字典.csv")
        return
    header, rows = read_csv_rows(dic)
    mid_i = find_col(header, "metric_id", "指標代號")
    def_i = find_col(header, "口徑", "定義")
    if mid_i < 0 or def_i < 0:
        c.rep.add("D10", "error", "指標字典.csv 缺 metric_id 或 口徑 欄",
                  "沒有這兩欄就對不上 Bundle 的鍵（18-G10）", "專案記憶/指標字典.csv")
        return
    defined = {r[mid_i].strip() for r in rows if mid_i < len(r) and
               def_i < len(r) and r[def_i].strip()}
    bundle = c.bundle("D10") or {}
    for key in bundle:
        root = key.split(".")[0]
        if key not in defined and root not in defined:
            c.rep.add("D10", "error",
                      f"Bundle 的 metric_id「{key}」在指標字典裡沒有口徑",
                      "每個進交付物的數字都要說得出「這個口徑是什麼」"
                      "（18-G2 的實證：M 用毛額還是淨額，決定一個退了 48 萬的人算不算 VIP）",
                      "專案記憶/指標字典.csv")
    man = c.manifest("D10") or {}
    missing = [n for n, rec in man.items() if not str((rec or {}).get("口徑", "")).strip()]
    if missing:
        c.rep.add("D10", "warning",
                  f"{len(missing)} 張圖的 manifest 沒有口徑註腳（例：{missing[0]}）",
                  "19 §一：所有圖表自動帶口徑註腳。collect_figures.py 收圖時一併寫入",
                  "圖表/報告用/manifest.json")


def chk_D11_measurement_break(c: Ctx) -> None:
    """跨越量測變更日的趨勢圖有斷線標記（20 §九）"""
    meta = c.meta("D11")
    if meta is None:
        return
    days = meta.get("量測變更日", []) or []
    charts = meta.get("含變更日的趨勢圖", []) or []
    if days and not charts:
        c.rep.add("D11", "warning",
                  f"登錄了量測變更日 {days}，但沒有任何趨勢圖標記為含變更日",
                  "確認趨勢圖是否真的沒跨過那幾天；跨過就要斷線 + 灰色垂直參考線 + "
                  "圖註標明變更日（20 §九）", "交付物/report_meta.json")
    for ch in charts:
        if not ch.get("有斷線標記"):
            c.rep.add("D11", "error",
                      f"{ch.get('檔名', '?')} 跨越量測變更日卻沒有斷線標記",
                      "折線直接連過去，圖上看到的是「7 月轉換率跳升 40%」，"
                      "實際上是量測口徑換了。斷線 + 灰色垂直參考線 + 圖註（20 §九）",
                      "交付物/report_meta.json")


def chk_D12_version_triplet(c: Ctx) -> None:
    """版本三件套三個欄位都非空，且埋進每份文字交付物（20 §十）"""
    rm = c.run_manifest("D12")
    if rm is None:
        return
    triplet = {}
    for k in ("run_id", "ducklake_snapshot_id", "git_commit"):
        v = str(rm.get(k, "") or "").strip()
        triplet[k] = v
        if not v:
            c.rep.add("D12", "error", f"run_manifest.json 的 {k} 是空的",
                      "三件套是 stamp_version.py 的唯一產生點；缺任一個，"
                      "「半年後能重跑出同一份數字」就是空話（20 §十、03 §6.3 D20）",
                      "執行紀錄/run_manifest.json")
    if not all(triplet.values()):
        return
    for path in c.text_deliverables():
        if path.suffix.lower() not in {".html", ".htm", ".md"}:
            continue
        txt = read_text(path)
        for k, v in triplet.items():
            if v not in txt:
                c.rep.add("D12", "error", f"{path.name} 沒有埋入 {k}={v}",
                          "每一份交付物都要埋三件套，位置固定（20 §十）。"
                          "模板加一段 footer，不要靠人記得", c.rel(path))
                break


def chk_D13_size_limit(c: Ctx) -> None:
    """單檔 HTML 報告 ≤ 10 MB（20 §3.2）"""
    for path in c.p.deliverables.glob("*.html") if c.p.deliverables.exists() else []:
        mb = path.stat().st_size / 1024 ** 2
        if mb >= SIZE_LIMIT_MB:
            c.rep.add("D13", "error", f"{path.name} 有 {mb:.1f} MB，超過 {SIZE_LIMIT_MB} MB",
                      "處置順序：① 互動圖降 PNG ② 明細表改前 20 列 + 附 CSV ③ 拆附件 —— "
                      "不要壓縮圖質（20 §3.2）", c.rel(path))


def chk_D14_bundle_evidence(c: Ctx) -> None:
    """Bundle 中每個 Result 的 evidence 欄非空且在四級白名單內（00 §1.5）"""
    bundle = c.bundle("D14")
    if bundle is None:
        return
    for key, rec in bundle.items():
        if not isinstance(rec, dict):
            c.rep.add("D14", "error", f"bundle.json 的「{key}」不是物件",
                      "每個值都要是 Result：value / fmt / source / as_of / evidence / n"
                      "（20 §2.2）", "模型輸出/bundle.json")
            continue
        ev = str(rec.get("evidence", "") or "").strip()
        if not ev:
            c.rep.add("D14", "error", f"「{key}」的 evidence 欄是空的",
                      "Result 的 evidence 是必填，判定樹在 00 §1.5", "模型輸出/bundle.json")
        elif ev not in EVIDENCE_LEVELS:
            c.rep.add("D14", "error", f"「{key}」的 evidence 是「{ev}」",
                      f"只能是 {' / '.join(EVIDENCE_LEVELS)}（00 §1.5）",
                      "模型輸出/bundle.json")
        for fld in ("source", "as_of", "fmt"):
            if not str(rec.get(fld, "") or "").strip():
                c.rep.add("D14", "warning", f"「{key}」的 {fld} 欄是空的",
                          "source 用來回答「這數字哪來的」、as_of 是特徵基準日（18-G4）、"
                          "fmt 對應 19 §5.3 的格式代號", "模型輸出/bundle.json")


# ── 圖表（19 §1.8 / §4.3 / §6.1）─────────────────────────

def chk_F01_required_figures(c: Ctx) -> None:
    """REQUIRED_FIGURES：每個模組的必出張數（19 §1.8）"""
    counts: dict[str, int] = {}
    for f in c.figures():
        if "報告用" in f.parts:
            continue
        m = FIG_NAME_RE.match(f.name)
        if m:
            counts[m.group("module").upper()] = counts.get(m.group("module").upper(), 0) + 1
    progress = c.p.progress_log
    ptxt = read_text(progress) if progress.exists() else ""
    for mod, need in REQUIRED_FIGURES.items():
        got = counts.get(mod.upper(), 0)
        if got >= need:
            continue
        if got == 0:
            lvl = "warning" if mod in ptxt else "error"
            c.rep.add("F01", lvl, f"{mod} 一張圖都沒有（應 {need} 張）",
                      f"預設必出；真的不做要在《進度與異狀.md》寫理由並點名 {mod}"
                      "（19 §一）" if lvl == "error"
                      else f"《進度與異狀.md》已記錄 {mod}，確認理由寫得夠具體（19 §一）",
                      "圖表/")
        else:
            c.rep.add("F01", "error", f"{mod} 只有 {got} 張圖，應 {need} 張",
                      "缺的那幾張回去補；同一組圖缺一張就報告不完整（19 §1.7 原文）",
                      "圖表/")


def chk_F02_forbidden_figures(c: Ctx) -> None:
    """禁用圖種靜態掃描：wordcloud / radar / pie>5 / 3D / 雙 Y 軸（19 §1.8、§4.3）"""
    man = c.manifest("F02") or {}
    for f in c.figures():
        m = FIG_NAME_RE.match(f.name)
        kind = (m.group("kind").lower() if m else f.stem.lower().rsplit("_", 1)[-1])
        for bad, why in FORBIDDEN_FIGURE_KINDS.items():
            if kind == bad or bad in kind:
                c.rep.add("F02", "error", f"{f.name} 是禁用圖種「{bad}」", why, c.rel(f))
                break
        else:
            if kind in PIE_KINDS:
                rec = man.get(f.name, {}) or {}
                n_cat = rec.get("類別數")
                if not isinstance(n_cat, int):
                    c.rep.add("F02", "error",
                              f"{f.name} 是圓餅／甜甜圈，manifest 沒有「類別數」",
                              f"類別 >{PIE_MAX_CATEGORIES} 全禁、任何時間維度絕對禁"
                              "（19 §4.3）。沒有類別數就無法判定，一律當超標處理",
                              c.rel(f))
                elif n_cat > PIE_MAX_CATEGORIES:
                    c.rep.add("F02", "error",
                              f"{f.name} 是 {n_cat} 類的圓餅",
                              f"類別 >{PIE_MAX_CATEGORIES} 全禁；角度判讀誤差遠大於長度，"
                              "改水平長條（19 §4.3）", c.rel(f))


def chk_F03_figure_naming(c: Ctx) -> None:
    """圖檔命名合規：{模組}_{主題}_{圖種}.png，圖種取自固定詞彙表（19 §6.1）"""
    for f in c.figures():
        if "報告用" in f.parts:
            continue
        m = FIG_NAME_RE.match(f.name)
        if not m:
            c.rep.add("F03", "warning", f"{f.name} 不符合命名規則",
                      "格式 {模組}_{主題}_{圖種}.png，模組＝M1…M12（M8 用 M8-1/2/3），"
                      "主題用資料原生的欄位名不要美化，不加版號（19 §6.1）", c.rel(f))
            continue
        kind = m.group("kind").lower()
        if kind not in FIGURE_KIND_VOCAB and kind not in FORBIDDEN_FIGURE_KINDS:
            c.rep.add("F03", "warning", f"{f.name} 的圖種「{kind}」不在固定詞彙表裡",
                      "新增圖種要先進 19 §6.1 的詞彙表，不要就地發明", c.rel(f))


def chk_F04_forbidden_code(c: Ctx) -> None:
    """產圖程式碼層的禁用寫法（雙 Y 軸／圓餅／3D／雷達／文字雲）（19 §4.3）"""
    roots = [c.scan_root]
    if c.p is not None and c.p.root.exists():
        roots.append(c.p.root)
    seen: set[tuple[str, int]] = set()
    for root in roots:
        for f in root.rglob("*.py"):
            if "__pycache__" in f.parts or f.name == Path(__file__).name:
                continue
            for ln, line in enumerate(read_text(f).splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                for pat, level, why in FORBIDDEN_CODE_PATTERNS:
                    m = re.search(pat, line)
                    if m and (str(f), ln) not in seen:
                        seen.add((str(f), ln))
                        c.rep.add("F04", level,
                                  f"{f.name}:{ln} 用了 `{m.group(0)}`",
                                  why + "。替代：small multiples，或都指數化"
                                        "（基期=100）畫同一軸；圓餅改水平長條",
                                  str(f))


# ── 靜態規範（03 §1.2）─────────────────────────────────

def chk_R01_numbered_dirs(c: Ctx) -> None:
    """references 與腳本裡不得出現 `0N_英文名/` 形式的硬編路徑（03 §1.2）"""
    root = c.scan_root
    allow = _repo_dir_allowlist()
    seen: set[tuple[str, int, str]] = set()
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in STATIC_SCAN_SUFFIXES:
            continue
        if "__pycache__" in f.parts or ".git" in f.parts:
            continue
        for ln, line in enumerate(read_text(f).splitlines(), 1):
            if any(mark in line for mark in NEGATIVE_EXAMPLE_MARKERS):
                continue
            for m in NUMBERED_DIR_RE.finditer(line):
                name = m.group(1)
                if name in allow or (f.name, ln, name) in seen:
                    continue
                seen.add((f.name, ln, name))
                c.rep.add("R01", "error",
                          f"{f.name}:{ln} 出現編號式英文目錄 `{name}/`",
                          "資料夾名稱不帶數字編號、用完整中文名（03 §1.2）。"
                          "對照：raw→原始資料/、features→顧客特徵表/、figures→圖表/、"
                          "delivery/report→交付物/。路徑一律走 "
                          "`from paths import project_dir`",
                          str(f))


def chk_R02_hardcoded_paths(c: Ctx) -> None:
    """腳本不得寫死絕對路徑，也不得自己 duckdb.connect()（03 §1.2、§7.1）"""
    for f in sorted((c.scan_root / "scripts").rglob("*.py")) if (c.scan_root / "scripts").exists() else []:
        if "__pycache__" in f.parts or f.name in {"paths.py", "db.py", Path(__file__).name}:
            continue
        for ln, line in enumerate(read_text(f).splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if re.search(r"['\"][A-Za-z]:[\\/]", line):
                c.rep.add("R02", "warning", f"{f.name}:{ln} 寫死了絕對路徑",
                          "改用 `from paths import project_dir, cfg`；"
                          "寫死路徑的 skill 換一台機器就不能用（03 §1.2）", str(f))
            if re.search(r"\bduckdb\.connect\s*\(", line):
                c.rep.add("R02", "warning", f"{f.name}:{ln} 直接呼叫 duckdb.connect()",
                          "一律走 `from db import connect` —— encodings 擴充、記憶體上限、"
                          "唯讀旗標都在那一層（03 §7.1、18-T9）", str(f))


# ── M11 建議層（14 §九）─────────────────────────────────

def chk_M01_artifacts(c: Ctx) -> None:
    """M11 必須產出的檔案齊備（14 §九，路徑改對齊 03 §1.2 的中文目錄）"""
    d = c.p.deliverables
    required = ["insights.md", "sizing.csv", "calibration_log.csv",
                "decision_summary.md", "excluded_options.csv", "decision_tables.md"]
    for name in required:
        if not (d / name).exists():
            lvl = "warning" if name == "excluded_options.csv" else "error"
            c.rep.add("M01", lvl, f"缺少 交付物/{name}",
                      "14 §九：缺一即 M11 不得標記完成"
                      "（excluded_options.csv 為空只是警告）", c.rel(d))
    if not list(d.glob("audience_*.csv")) and d.exists():
        c.rep.add("M01", "error", "沒有任何 audience_*.csv 名單檔",
                  "14 §五：一建議一份名單，檔名 audience_{rec_id}_{as_of}.csv，"
                  "含排除與未評估分頁", c.rel(d))


def chk_M02_insights(c: Ctx) -> None:
    """每條跨章洞察引用 ≥2 個不同章節的結果物件；洞察條數 3–5（14 §二）"""
    path = c.p.deliverables / "insights.md"
    if not path.exists():
        return
    txt = read_text(path)
    blocks = [b for b in re.split(r"\n(?=##+\s)", txt) if re.match(r"##+\s", b)]
    if not 3 <= len(blocks) <= 5:
        c.rep.add("M02", "error", f"insights.md 有 {len(blocks)} 條洞察",
                  "14 §二：跨章洞察 3–5 條。用 `## ` 標題分條", c.rel(path))
    for b in blocks:
        ids = set(re.findall(r"\b(M\d+(?:-\d+)?)\b", b))
        if len(ids) < 2:
            title = b.splitlines()[0].strip()
            c.rep.add("M02", "error", f"洞察「{title}」只引用了 {len(ids)} 個章節",
                      "跨章洞察要引用 ≥2 個不同章節的結果物件 id（14 §二），"
                      "否則它只是某一章的小結", c.rel(path))


def chk_M03_stop_doing(c: Ctx) -> None:
    """全報告至少一處明說「應停止做什麼」（18-E21）"""
    hits = []
    for path in c.text_deliverables():
        txt = strip_html(read_text(path))
        if re.search(r"停止|不要再|應退出|停投|不建議繼續|收掉", txt):
            hits.append(path.name)
    if not hits:
        c.rep.add("M03", "error", "全部交付物都沒有一處說「該停止做什麼」",
                  "A+ 報告都有負面建議（18-E21，如「停止全台無差別促銷」）。"
                  "只加碼不喊停的建議書，讀者無法據以重分配預算",
                  "交付物/")


def chk_M04_audience_conservation(c: Ctx) -> None:
    """名單列數 == 報告內文引用人數（14 §九，名單守恆）"""
    meta = c.meta("M04")
    if meta is None:
        return
    declared: dict[str, int] = meta.get("名單人數", {}) or {}
    if not declared:
        c.rep.add("M04", "warning", "report_meta.json 沒有「名單人數」對照",
                  "把報告內文引用的每份名單人數寫進來，才驗得了"
                  "「名單列數 == 內文人數 == segment SQL 回傳列數」（14 §九）",
                  "交付物/report_meta.json")
        return
    for name, n_declared in declared.items():
        f = c.p.deliverables / name
        if not f.exists():
            c.rep.add("M04", "error", f"報告引用了名單 {name}，但檔案不存在",
                      "產出名單檔，或修正報告引用（14 §五是最後一哩）", c.rel(c.p.deliverables))
            continue
        _, rows = read_csv_rows(f)
        n_real = len([r for r in rows if any(x.strip() for x in r)])
        if n_real != n_declared:
            c.rep.add("M04", "error",
                      f"{name} 實際 {n_real} 列，報告內文寫 {n_declared} 人",
                      "名單列數 == 內文人數 == segment SQL 回傳列數，三者必須守恆（14 §九）。"
                      "差額通常來自去重或排除名單沒交代（18-E22）", c.rel(f))


# ══════════════════════════════════════════════════════════════════
# 六、檢查登記表
# ══════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Check:
    id: str
    category: str
    title: str
    source: str
    fn: Callable[[Ctx], None]
    needs_project: bool = True


CHECKS: list[Check] = [
    Check("S01", "結構", "11 章 checklist 全綠", "20 §3.1、18-E3", chk_S01_chapters),
    Check("S02", "結構", "9 個排版件齊備", "20 §3.1、18-E4", chk_S02_layout),
    Check("S03", "結構", "每章小結 150–400 字且不以「本章分析了」開頭", "18-E19", chk_S03_summaries),
    Check("S04", "結構", "頁數 ≥15", "18-E5", chk_S04_pages),

    Check("T01", "統計", "每個 ANOVA 都有對應的事後檢定物件", "18-E1", chk_T01_anova_posthoc),
    Check("T02", "統計", "分群輸入變數全在白名單內", "18-E2", chk_T02_cluster_inputs),
    Check("T03", "統計", "百分比欄加總 ≈100（誤差 <0.5）", "19 §5.4", chk_T03_pct_sum),
    Check("T04", "統計", "同欄無數量級差 >100 倍的離群", "18-E9", chk_T04_magnitude),
    Check("T05", "統計", "|r|=1 的格子已標樣本不足", "18-E10", chk_T05_r_equals_one),
    Check("T06", "統計", "每張統計表最後一欄非空且非純數字", "18-E15", chk_T06_conclusion_col),
    Check("T07", "統計", "標 n.s. 的列有 mde 欄", "00 §四", chk_T07_ns_needs_mde),

    Check("C01", "符號", "交付檔中不存在空白格", "00 §四", chk_C01_blank_cells),
    Check("C02", "符號", "無 NaN / inf / #DIV/0! 洩漏", "18 §八、00 §四", chk_C02_leak_tokens),
    Check("C03", "符號", "出現 N/A 的表在 degradation_log 有紀錄", "00 §四", chk_C03_na_needs_log),
    Check("C04", "符號", "'-' 與 '0' 的使用符合樣本數", "00 §四", chk_C04_dash_and_zero),

    Check("D01", "交付物", "圖檔全部存在且非 0 bytes", "18 §八、19 §6.2", chk_D01_figures_exist),
    Check("D02", "交付物", "報告用/ 的 sha256 等於來源圖", "19 §6.2", chk_D02_figure_hash),
    Check("D03", "交付物", "報告引用的圖都在 manifest 裡", "19 §6.2", chk_D03_report_refs),
    Check("D04", "交付物", "manifest 每張圖都有對應結果物件", "19 §6.2、18-E7", chk_D04_figure_has_result),
    Check("D05", "交付物", "報告每個數字都能在 Bundle 找到", "18-E7、20 §2.2", chk_D05_numbers_from_bundle),
    Check("D06", "交付物", "同一 metric_id 在四種交付物字串一致", "20 §2.2", chk_D06_cross_deliverable),
    Check("D07", "交付物", "術語表驗證通過", "18-E6", chk_D07_glossary),
    Check("D08", "交付物", "每條建議帶證據等級且措辭合規", "00 §1.5、18-G6", chk_D08_evidence_level),
    Check("D09", "交付物", "沒有實驗時的三句禁語未出現", "00 §1.5", chk_D09_absolute_bans),
    Check("D10", "交付物", "指標口徑已標註", "18-G10", chk_D10_metric_dict),
    Check("D11", "交付物", "跨量測變更日的趨勢圖有斷線標記", "20 §九", chk_D11_measurement_break),
    Check("D12", "交付物", "版本三件套三欄非空且已埋入", "20 §十", chk_D12_version_triplet),
    Check("D13", "交付物", "單檔 HTML ≤ 10 MB", "20 §3.2", chk_D13_size_limit),
    Check("D14", "交付物", "Bundle 每個 Result 的 evidence 合規", "00 §1.5", chk_D14_bundle_evidence),

    Check("F01", "圖表", "REQUIRED_FIGURES 各模組張數達標", "19 §1.8", chk_F01_required_figures),
    Check("F02", "圖表", "禁用圖種（wordcloud/radar/pie>5/3D/雙Y軸）", "19 §1.8、§4.3", chk_F02_forbidden_figures),
    Check("F03", "圖表", "圖檔命名與圖種詞彙表合規", "19 §6.1", chk_F03_figure_naming),
    Check("F04", "圖表", "產圖程式碼無禁用寫法", "19 §4.3", chk_F04_forbidden_code, False),

    Check("R01", "靜態", "無編號式英文目錄硬編路徑", "03 §1.2", chk_R01_numbered_dirs, False),
    Check("R02", "靜態", "腳本無寫死絕對路徑／自建 duckdb 連線", "03 §1.2、§7.1", chk_R02_hardcoded_paths, False),

    Check("M01", "建議", "M11 產出物齊備", "14 §九", chk_M01_artifacts),
    Check("M02", "建議", "跨章洞察 3–5 條且各引用 ≥2 章", "14 §二", chk_M02_insights),
    Check("M03", "建議", "至少一處明說「應停止做什麼」", "18-E21", chk_M03_stop_doing),
    Check("M04", "建議", "名單列數與內文人數守恆", "14 §九", chk_M04_audience_conservation),
]

CHECK_BY_ID = {c.id: c for c in CHECKS}


# ══════════════════════════════════════════════════════════════════
# 七、主程式
# ══════════════════════════════════════════════════════════════════

def select_checks(only: str | None, skip: str | None) -> list[Check]:
    def match(spec: str, chk: Check) -> bool:
        s = spec.strip().upper()
        return (s == chk.id.upper() or s == chk.category
                or (len(s) == 1 and chk.id.upper().startswith(s)))

    picked = CHECKS
    if only:
        specs = [s for s in only.split(",") if s.strip()]
        picked = [c for c in picked if any(match(s, c) for s in specs)]
    if skip:
        specs = [s for s in skip.split(",") if s.strip()]
        picked = [c for c in picked if not any(match(s, c) for s in specs)]
    return picked


def print_list() -> int:
    print("=" * 72)
    print("verify_outputs.py — 檢查清單（--only / --skip 可用代號、分類或首字母）")
    print("=" * 72)
    cat = ""
    for c in CHECKS:
        if c.category != cat:
            cat = c.category
            print(f"\n[{cat}]")
        star = "" if c.needs_project else "  （不需專案，可用 --static-only）"
        print(f"  {c.id}  {c.title}")
        print(f"        出處：{c.source}{star}")
    print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="交付 gate：產出前的機械化驗收（0 可交付／1 不得輸出／2 有警告）")
    ap.add_argument("專案代號", nargs="?", help="要驗收的專案代號")
    ap.add_argument("--only", help="只跑這幾條，逗號分隔（代號／分類／首字母）")
    ap.add_argument("--skip", help="跳過這幾條，逗號分隔")
    ap.add_argument("--list", action="store_true", help="列出所有檢查後結束")
    ap.add_argument("--static-only", action="store_true",
                    help="只跑不需要專案的靜態檢查（R01/R02/F04）")
    ap.add_argument("--scan-root", type=Path, default=SKILL_ROOT,
                    help=f"靜態掃描的根目錄，預設 {SKILL_ROOT}")
    ap.add_argument("--verbose", action="store_true", help="連通過的檢查也列出")
    ap.add_argument("--json", type=Path, help="把結果另存成 JSON")
    args = ap.parse_args()

    if args.list:
        return print_list()

    project = getattr(args, "專案代號")
    if not project and not args.static_only:
        ap.error("要指定專案代號，或用 --static-only 只跑靜態檢查")

    picked = select_checks(args.only, args.skip)
    if args.static_only:
        picked = [c for c in picked if not c.needs_project]
    if not picked:
        print("⛔ --only / --skip 的組合把所有檢查都篩掉了 — "
              "用 --list 看有哪些代號")
        return 1

    rep = Report()
    pp: ProjectPaths | None = None
    if project:
        root = projects_root() / project
        if not root.exists():
            print(f"⛔ 找不到專案目錄：{root}")
            print(f"   — 確認專案代號是否打錯，或先跑過建倉流程（M3）建立它")
            return 1
        pp = ProjectPaths(root)

    ctx = Ctx(project=project or "(靜態)", p=pp, scan_root=args.scan_root, rep=rep)

    print("=" * 72)
    print("行銷數據分析 Skill — 交付 gate")
    print(f"專案：{ctx.project}")
    if pp:
        print(f"路徑：{pp.root}")
    print(f"靜態掃描根目錄：{args.scan_root}")
    print(f"本次執行 {len(picked)} / {len(CHECKS)} 條檢查")
    print("=" * 72)

    for chk in picked:
        if chk.needs_project and pp is None:
            rep.skipped.append(chk.id)
            continue
        before = len(rep.findings)
        try:
            chk.fn(ctx)
        except Exception as e:  # noqa: BLE001
            rep.add(chk.id, "error", f"檢查本身執行失敗（{e!r}）",
                    "這是 verify_outputs.py 的 bug 或輸入檔格式不符契約，"
                    "把這段訊息連同輸入檔回報")
        rep.ran.append(chk.id)
        if args.verbose and len(rep.findings) == before:
            print(f"  ✅ [{chk.id}] {chk.title}")

    # ── 輸出 ────────────────────────────────────────────
    for level, header in (("warning", "⚠ 可交付，但每一條都要在《進度與異狀.md》登錄並配一條處理"),
                          ("error", "⛔ 不得輸出，必須先修")):
        items = rep.by_level(level)
        if not items:
            continue
        print(f"\n{header}")
        print("-" * 72)
        for f in items:
            chk = CHECK_BY_ID.get(f.check_id)
            title = chk.title if chk else ""
            print(f"  {LEVEL_ICON[f.level]} [{f.check_id}] {title}")
            print(f"      {f.fact} — {f.fix}")
            if f.where:
                print(f"      · 檔案：{f.where}")

    n_err = len(rep.by_level("error"))
    n_warn = len(rep.by_level("warning"))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "專案": ctx.project,
            "執行": rep.ran,
            "跳過": rep.skipped + [c.id for c in CHECKS if c not in picked],
            "error": n_err, "warning": n_warn,
            "findings": [f.__dict__ for f in rep.findings],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n· 結果已寫入 {args.json}")

    print("\n" + "=" * 72)
    if n_err:
        print(f"結果：{n_err} 個 error、{n_warn} 個 warning → ⛔ 不得輸出")
        print("      回去修，不要用「先寄一版」繞過（20 §九）")
        return 1
    if n_warn:
        print(f"結果：{n_warn} 個 warning → ⚠ 可交付，但要登錄《進度與異狀.md》")
        return 2
    print(f"結果：{len(rep.ran)} 條檢查全綠 → ✅ 可交付")
    print("      交付時用 [View 檔名](computer://…) 給連結（00 §六）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
