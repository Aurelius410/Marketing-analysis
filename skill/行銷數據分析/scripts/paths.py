#!/usr/bin/env python3
"""
路徑與設定解析 —— 讓這個 Skill 丟到任何一台電腦都能直接用。

設計原則：
  · **skill 根目錄從 __file__ 推導**，不寫死。整個資料夾搬到哪都能跑。
  · 機器相依的設定放 config.yml（不進版控），範本是 config.example.yml。
  · 沒有 config.yml 也要能跑 —— 每一項都有合理預設值。
  · 環境變數優先於 config.yml，方便 CI 或臨時切換。

用法：
    from paths import SKILL_ROOT, project_dir, cfg

    p = project_dir("2026Q3_電商")        # 專案根目錄，不存在會自動建
    p.raw, p.staging, p.mart, p.figures    # 各子目錄
    cfg("字型.中文")                        # 讀設定，支援點號路徑

命令列自我檢查：
    python paths.py

退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 全通過
    1  = 有 error 擋住（本腳本目前沒有這種情況，路徑解析永遠有預設值）
    2  = 只有 warning，可往下（同上，本腳本不產生）
    64 = 用法錯誤（本腳本不吃任何參數，給了就是 64）
    70 = 腳本自身異常
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── skill 根目錄：從本檔位置推導，不寫死 ──────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = SKILL_ROOT / "config.yml"
CONFIG_EXAMPLE = SKILL_ROOT / "config.example.yml"

# 環境變數前綴。例：MKT_專案根目錄 會覆蓋 config.yml 的同名設定
ENV_PREFIX = "MKT_"

_DEFAULTS: dict[str, Any] = {
    "專案根目錄": None,          # None → SKILL_ROOT.parent.parent / "projects"
    "素材庫": None,              # None → 自動往上找 00_source_archive
    "python": {"次環境路徑": ".venv-causal", "次環境版本": "3.12"},
    "duckdb": {
        "檔名": "warehouse.duckdb",
        "執行緒": 6,
        "記憶體上限": "11GB",
        "暫存目錄": None,
    },
    "字型": {
        "中文": "Microsoft JhengHei",
        "英文": "Times New Roman",
        "對外散布備援": "Noto Sans TC",
        "最小字級": 12,
    },
    "工具": {"R路徑": None, "pandoc": None, "quarto": None},
}

# 專案的標準子目錄。名稱刻意用中文完整描述，與 references/03 一致。
PROJECT_SUBDIRS = [
    "專案記憶",
    "開案與問題定義",
    "原始資料",
    "清理後資料",
    "分析資料表",
    "顧客特徵表",
    "模型輸出",
    "統計表",
    "圖表",
    "交付物",
    "隔離區",
    "SQL",
    "執行紀錄",
]

FIGURE_SUBDIRS = [
    "資料體檢", "特徵檢驗", "轉換前後對照", "分群",
    "迴歸診斷", "行銷分析", "預測模型", "文本分析", "報告用",
]

TABLE_SUBDIRS = [
    "資料體檢", "特徵檢驗", "轉換前後對照", "分群輪廓",
    "迴歸與診斷", "行銷分析", "預測模型",
]

_config_cache: dict[str, Any] | None = None


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def load_config(reload: bool = False) -> dict[str, Any]:
    """讀 config.yml（沒有就用預設）。PyYAML 缺席時退化成純預設。"""
    global _config_cache
    if _config_cache is not None and not reload:
        return _config_cache

    user_cfg: dict[str, Any] = {}
    if CONFIG_FILE.exists():
        try:
            import yaml  # 只有真的有 config.yml 時才需要 PyYAML
            user_cfg = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
        except ImportError:
            print("⚠ 找到 config.yml 但沒有 PyYAML，改用預設值。"
                  "要讀設定請 pip install pyyaml", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"⚠ config.yml 解析失敗（{e}），改用預設值。", file=sys.stderr)

    _config_cache = _deep_merge(_DEFAULTS, user_cfg)
    return _config_cache


def cfg(dotted: str, default: Any = None) -> Any:
    """用點號路徑讀設定，環境變數優先。cfg('字型.中文')"""
    env_key = ENV_PREFIX + dotted.replace(".", "_")
    if env_key in os.environ:
        return os.environ[env_key]

    node: Any = load_config()
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node if node is not None else default


def _expand(p: str | Path) -> Path:
    return Path(os.path.expandvars(str(p))).expanduser().resolve()


def projects_root() -> Path:
    """分析專案的根目錄。預設是 skill 所在 repo 旁的 projects/。"""
    v = cfg("專案根目錄")
    if v:
        return _expand(v)
    # skill/行銷數據分析/scripts → skill/行銷數據分析 → skill → repo root
    return SKILL_ROOT.parent.parent / "projects"


def archive_root() -> Path | None:
    """素材庫位置。找不到回 None —— 它只影響「查出處」，不影響運作。"""
    v = cfg("素材庫")
    if v:
        p = _expand(v)
        return p if p.exists() else None
    for base in (SKILL_ROOT, SKILL_ROOT.parent, SKILL_ROOT.parent.parent):
        cand = base / "00_source_archive"
        if cand.exists():
            return cand
    return None


@dataclass(frozen=True)
class ProjectPaths:
    """一個分析專案的所有標準路徑。"""
    root: Path

    @property
    def memory(self) -> Path: return self.root / "專案記憶"
    @property
    def intake(self) -> Path: return self.root / "開案與問題定義"
    @property
    def raw(self) -> Path: return self.root / "原始資料"
    @property
    def staging(self) -> Path: return self.root / "清理後資料"
    @property
    def mart(self) -> Path: return self.root / "分析資料表"
    @property
    def features(self) -> Path: return self.root / "顧客特徵表"
    @property
    def models(self) -> Path: return self.root / "模型輸出"
    @property
    def tables(self) -> Path: return self.root / "統計表"
    @property
    def figures(self) -> Path: return self.root / "圖表"
    @property
    def deliverables(self) -> Path: return self.root / "交付物"
    @property
    def quarantine(self) -> Path: return self.root / "隔離區"
    @property
    def sql(self) -> Path: return self.root / "SQL"
    @property
    def log(self) -> Path: return self.root / "執行紀錄"

    @property
    def core_memory(self) -> Path: return self.memory / "專案核心.md"
    @property
    def progress_log(self) -> Path: return self.memory / "進度與異狀.md"

    @property
    def db(self) -> Path:
        return self.root / str(cfg("duckdb.檔名", "warehouse.duckdb"))

    def figure(self, group: str, name: str) -> Path:
        return self.figures / group / name

    def table(self, group: str, name: str) -> Path:
        return self.tables / group / name


def project_dir(code: str, create: bool = True) -> ProjectPaths:
    """取得專案路徑物件。create=True 時自動建立標準目錄結構。"""
    root = projects_root() / code
    pp = ProjectPaths(root)
    if create:
        for d in PROJECT_SUBDIRS:
            (root / d).mkdir(parents=True, exist_ok=True)
        for d in FIGURE_SUBDIRS:
            (root / "圖表" / d).mkdir(parents=True, exist_ok=True)
        for d in TABLE_SUBDIRS:
            (root / "統計表" / d).mkdir(parents=True, exist_ok=True)
    return pp


def causal_venv_python() -> Path | None:
    """次環境（因果推論）的 python 執行檔。找不到回 None。"""
    v = cfg("python.次環境路徑", ".venv-causal")
    base = _expand(v) if Path(v).is_absolute() else (SKILL_ROOT.parent.parent / v)
    exe = base / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return exe if exe.exists() else None


def _main() -> int:
    # 在函式內 import：paths.py 是所有腳本的最底層，模組層不吃額外相依
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from exitcodes import EX_OK, GateArgumentParser

    ap = GateArgumentParser(
        description="路徑解析自我檢查（不吃參數）")
    ap.parse_args()

    print("=" * 62)
    print("行銷數據分析 Skill — 路徑解析")
    print("=" * 62)
    print(f"skill 根目錄      : {SKILL_ROOT}")
    print(f"config.yml        : {CONFIG_FILE}"
          f"{'' if CONFIG_FILE.exists() else '  (不存在，使用預設值)'}")
    print(f"專案根目錄        : {projects_root()}")
    ar = archive_root()
    print(f"素材庫            : {ar or '(找不到，不影響運作)'}")
    cv = causal_venv_python()
    print(f"因果推論次環境    : {cv or '(未建立，需要時見 README)'}")
    print()
    print(f"中文字型          : {cfg('字型.中文')}")
    print(f"英文字型          : {cfg('字型.英文')}")
    print(f"對外散布備援字型  : {cfg('字型.對外散布備援')}")
    print(f"最小字級          : {cfg('字型.最小字級')} pt")
    print()
    print("範例：project_dir('示範專案') 會建立")
    pp = ProjectPaths(projects_root() / "示範專案")
    for d in PROJECT_SUBDIRS:
        print(f"    {d}/")
    print(f"  資料庫檔：{pp.db.name}")
    return EX_OK


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from exitcodes import EX_SOFTWARE
    try:
        raise SystemExit(_main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ paths.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
