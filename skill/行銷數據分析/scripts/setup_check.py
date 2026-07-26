#!/usr/bin/env python3
"""
新機器開工前的環境檢查 —— 在別台電腦第一次用這個 Skill 時先跑這支。

三桶輸出 + 退出碼（沿用既有 skill 的慣例）：
    0 = 全通過
    1 = 有 error，不能開工
    2 = 只有 warning，能開工但某些模組不可用

用法：
    python setup_check.py
    python setup_check.py --verbose      # 連通過項也列出來
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (  # noqa: E402
    SKILL_ROOT, CONFIG_FILE, CONFIG_EXAMPLE,
    projects_root, archive_root, causal_venv_python, cfg,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

errors: list[str] = []
warnings: list[str] = []
infos: list[str] = []


def ok(msg: str) -> None:
    infos.append(msg)


def warn(msg: str, why: str) -> None:
    warnings.append(f"{msg} — {why}")


def err(msg: str, why: str) -> None:
    errors.append(f"{msg} — {why}")


# ── 1. Python 版本 ───────────────────────────────────────
def check_python() -> None:
    v = sys.version_info
    s = f"{v.major}.{v.minor}.{v.micro}"
    if v < (3, 11):
        err(f"Python {s}", "太舊。需要 3.11 以上，建議 3.13 或 3.14")
    elif v >= (3, 14):
        ok(f"Python {s}（主環境）")
        infos.append("  └ 3.14 無法裝 dowhy/EconML/meridian，那些要用 3.12 次環境")
    else:
        ok(f"Python {s}")


# ── 2. 套件 ──────────────────────────────────────────────
CORE = {
    "duckdb": "倉儲引擎，沒有它整條管線不能跑",
    "pyarrow": "Parquet 讀寫",
    "pandas": "資料處理",
    "numpy": "數值運算",
    "yaml": "讀 config.yml（套件名 pyyaml）",
}
STATS = {
    "scipy": "統計檢定",
    "statsmodels": "迴歸與 GLM，M7 的核心",
    "sklearn": "分群與預測，M6/M9 的核心",
}
OPTIONAL = {
    "polars": "大檔整形（M1/M3 遇到大資料時）",
    "pandera": "出口資料驗證",
    "pingouin": "事後檢定與效果量（M6 分群後檢定）",
    "scikit_posthocs": "無母數事後檢定",
    "xgboost": "M9 預測建模",
    "lightgbm": "M9 大資料預測",
    "catboost": "M9 高基數類別特徵",
    "shap": "M9 模型解釋（不要用 tree importance）",
    "mlxtend": "M8-2 購物籃關聯規則",
    "factor_analyzer": "M8-2 因素分析",
    "lifelines": "M8-1 存活分析",
    "statsforecast": "時間序列預測",
    "pymc_marketing": "M8-1 CLV 與 M8-3 MMM",
    "altair": "所有圖表的基礎",
    "matplotlib": "統計診斷圖",
    "great_tables": "統計表排版",
    "jinja2": "單檔 HTML 報告",
    "xlsxwriter": "Excel 交付物",
    "pptx": "投影片（套件名 python-pptx）",
    "jieba": "M10 中文斷詞",
    "openpyxl": "讀 Excel 原始檔",
}


def has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def check_packages() -> None:
    missing_core = [m for m in CORE if not has(m)]
    if missing_core:
        err(f"缺少核心套件：{', '.join(missing_core)}",
            "跑 pip install -r requirements.txt")
    else:
        ok(f"核心套件齊全（{len(CORE)} 個）")

    missing_stats = [m for m in STATS if not has(m)]
    if missing_stats:
        err(f"缺少統計套件：{', '.join(missing_stats)}",
            "M6/M7/M9 不能跑。pip install -r requirements.txt")
    else:
        ok(f"統計套件齊全（{len(STATS)} 個）")

    missing_opt = {m: why for m, why in OPTIONAL.items() if not has(m)}
    if missing_opt:
        warn(f"缺少 {len(missing_opt)} 個選用套件", "對應模組不可用：")
        for m, why in missing_opt.items():
            warnings.append(f"    · {m:<18} {why}")
    else:
        ok(f"選用套件齊全（{len(OPTIONAL)} 個）")


# ── 3. 路徑 ──────────────────────────────────────────────
def check_paths() -> None:
    if not CONFIG_FILE.exists():
        if CONFIG_EXAMPLE.exists():
            ok("config.yml 不存在，使用預設值（多數情況沒問題）")
            infos.append(f"  └ 要自訂：cp {CONFIG_EXAMPLE.name} config.yml")
        else:
            warn("config.example.yml 也不見了", "skill 資料夾可能不完整")
    else:
        ok(f"config.yml 已設定：{CONFIG_FILE}")

    pr = projects_root()
    try:
        pr.mkdir(parents=True, exist_ok=True)
        probe = pr / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        ok(f"專案根目錄可寫入：{pr}")
    except OSError as e:
        err(f"專案根目錄不可寫入：{pr}", str(e))

    ar = archive_root()
    if ar:
        n = len(list(ar.rglob("*.md")))
        ok(f"素材庫：{ar}（{n} 份 digest）")
    else:
        warn("找不到素材庫 00_source_archive",
             "不影響分析，但查不到「這條規則的出處」")


# ── 4. references 完整性 ─────────────────────────────────
EXPECTED_REFS = [
    "00_通則與紀律", "01_商業框架與提問", "02_資料模型規格",
    "03_倉儲與檔案結構", "04_資料體檢", "05_資料特徵檢驗",
    "06_前處理與轉換", "07_標籤與分群", "08_迴歸建模",
    "09_行銷_顧客價值", "10_行銷_購物籃與品類", "11_行銷_成長與促銷",
    "12_預測建模", "13_文本分析", "14_決策轉譯", "15_實驗設計",
    "16_統計推論紀律", "17_指標公式庫", "18_分析陷阱清單",
    "19_圖表與統計表規格", "20_交付物產製",
]


def check_references() -> None:
    ref_dir = SKILL_ROOT / "references"
    if not ref_dir.exists():
        err("references/ 不存在", "skill 資料夾不完整，重新取得完整版")
        return
    present = {p.stem for p in ref_dir.glob("*.md")}
    missing = [r for r in EXPECTED_REFS if r not in present]
    if missing:
        warn(f"references 缺 {len(missing)}/{len(EXPECTED_REFS)} 份",
             "對應模組會讀不到規格：")
        for m in missing:
            warnings.append(f"    · {m}.md")
    else:
        ok(f"references 齊全（{len(EXPECTED_REFS)} 份）")


# ── 5. 次環境與外部工具 ──────────────────────────────────
def check_causal_env() -> None:
    p = causal_venv_python()
    if p:
        ok(f"因果推論次環境：{p}")
    else:
        warn("因果推論次環境未建立",
             "M12 與 uplift 級 2 不可用。建立方式："
             "py -3.12 -m venv .venv-causal 後 pip install -r requirements-causal.txt")

    if has("dowhy"):
        try:
            import dowhy  # noqa: PLC0415
            ver = getattr(dowhy, "__version__", "?")
            if ver.startswith("0.8") or ver.startswith("0.7"):
                err(f"主環境的 dowhy 是 {ver}（2022 年版）",
                    "這是 Python 3.14 靜默降版造成的。解除安裝，改用 3.12 次環境")
            else:
                warn(f"主環境有 dowhy {ver}",
                     "建議仍走次環境，避免相依衝突")
        except Exception:  # noqa: BLE001
            pass


def check_tools() -> None:
    for name, why in [("pandoc", "讀 .docx 評分標準／需求文件"),
                      ("git", "版本控制與可重現性")]:
        if shutil.which(name):
            ok(f"{name} 可用")
        else:
            warn(f"找不到 {name}", why)


# ── 6. DuckDB 冒煙測試 ───────────────────────────────────
def check_duckdb_smoke() -> None:
    if not has("duckdb"):
        return
    try:
        import duckdb  # noqa: PLC0415
        con = duckdb.connect()
        con.execute("SELECT 1").fetchone()
        try:
            con.execute("INSTALL encodings; LOAD encodings;")
            ok(f"DuckDB {duckdb.__version__} 可用，encodings 擴充已載入（Big5/CP950）")
        except Exception:  # noqa: BLE001
            warn(f"DuckDB {duckdb.__version__} 可用，但 encodings 擴充載入失敗",
                 "讀 Big5/CP950 檔案時會亂碼。需要網路才能首次下載擴充")
        con.close()
    except Exception as e:  # noqa: BLE001
        err("DuckDB 無法連線", str(e))


# ── 7. 字型 ──────────────────────────────────────────────
def check_fonts() -> None:
    if not has("matplotlib"):
        return
    try:
        from matplotlib import font_manager  # noqa: PLC0415
        names = {f.name for f in font_manager.fontManager.ttflist}
        for key in ("字型.中文", "字型.英文"):
            want = cfg(key)
            if want in names:
                ok(f"字型可用：{want}")
            else:
                warn(f"找不到字型：{want}",
                     f"圖表會出現豆腐字。改 config.yml 的 {key}，"
                     f"或安裝該字型")
        fallback = cfg("字型.對外散布備援")
        if fallback not in names:
            warn(f"找不到對外散布備援字型：{fallback}",
                 "對外交付且需嵌入字型時會退回系統字型（授權問題）")
    except Exception as e:  # noqa: BLE001
        warn("字型檢查失敗", str(e))


def main() -> int:
    ap = argparse.ArgumentParser(description="新機器環境檢查")
    ap.add_argument("--verbose", action="store_true", help="連通過項也列出")
    args = ap.parse_args()

    print("=" * 64)
    print("行銷數據分析 Skill — 環境檢查")
    print(f"skill 位置：{SKILL_ROOT}")
    print("=" * 64)

    for fn in (check_python, check_packages, check_paths, check_references,
               check_causal_env, check_tools, check_duckdb_smoke, check_fonts):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            err(f"檢查 {fn.__name__} 時異常", repr(e))

    if args.verbose and infos:
        print("\n通過")
        print("-" * 64)
        for m in infos:
            print(f"  ✅ {m}" if not m.startswith("  ") else m)

    if warnings:
        print("\n⚠ 可以開工，但這些功能不可用")
        print("-" * 64)
        for m in warnings:
            print(f"  {m}" if m.startswith("    ") else f"  ⚠ {m}")

    if errors:
        print("\n⛔ 不能開工，必須先處理")
        print("-" * 64)
        for m in errors:
            print(f"  ⛔ {m}")

    print("\n" + "=" * 64)
    if errors:
        print(f"結果：{len(errors)} 個 error、{len(warnings)} 個 warning → 不能開工")
        return 1
    if warnings:
        print(f"結果：{len(warnings)} 個 warning → 可以開工，部分模組不可用")
        return 2
    print(f"結果：全部通過（{len(infos)} 項）→ 可以開工")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
