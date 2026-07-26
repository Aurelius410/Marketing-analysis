#!/usr/bin/env python3
"""
DuckDB 連線 —— 所有 SQL 都從這裡進出。

為什麼要有這一層（而不是每次 duckdb.connect()）：
  · encodings 擴充必須載入，否則讀 Big5/CP950 檔案會亂碼（見 18-T9）
  · 記憶體與暫存目錄要設對，不然大表 spill 到系統碟會爆
  · .duckdb 不可放網路磁碟／OneDrive（見 18-T8），這裡集中檢查
  · 唯讀連線要能一行取得，避免分析腳本誤寫

用法：
    from db import connect, q

    with connect("2026Q3_電商") as con:
        con.execute("CREATE OR REPLACE TABLE ... AS SELECT ...")

    df = q("2026Q3_電商", "SELECT * FROM fact_transaction LIMIT 10")

自我檢查：
    python db.py <專案代號>
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import cfg, project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 這些路徑片段代表雲端同步或網路磁碟，DuckDB 官方明確建議避免
_RISKY_PATH_MARKERS = ("onedrive", "dropbox", "google drive", "icloud", "\\\\")


def _check_db_location(db_path: Path) -> list[str]:
    """回傳警告清單。不阻擋，但要讓使用者知道。"""
    warns = []
    low = str(db_path).lower()
    for m in _RISKY_PATH_MARKERS:
        if m in low:
            warns.append(
                f"資料庫位於疑似雲端同步或網路路徑（比對到 '{m.strip()}'）：{db_path}\n"
                f"  DuckDB 官方建議避免 —— 會有檔案鎖衝突與難以診斷的錯誤。"
                f"請改放本機實體磁碟（見 18-T8）。"
            )
            break
    return warns


@contextmanager
def connect(
    project: str,
    read_only: bool = False,
    threads: int | None = None,
    memory_limit: str | None = None,
) -> Iterator[Any]:
    """開一個設定好的 DuckDB 連線。用 with 確保關閉。

    project     專案代號，資料庫位置由 paths.project_dir 決定
    read_only   分析腳本一律傳 True，避免誤寫
    """
    try:
        import duckdb
    except ImportError as e:
        raise RuntimeError(
            "duckdb 未安裝。跑 pip install -r requirements.txt（第 1 層）"
        ) from e

    p = project_dir(project, create=not read_only)
    db_path = p.db

    if read_only and not db_path.exists():
        raise FileNotFoundError(
            f"唯讀模式但資料庫不存在：{db_path}\n"
            f"  先跑建倉流程（M3），或確認專案代號是否打錯。"
        )

    for w in _check_db_location(db_path):
        print(f"⚠ {w}", file=sys.stderr)

    con = duckdb.connect(str(db_path), read_only=read_only)
    try:
        if not read_only:
            con.execute(f"SET threads = {threads or cfg('duckdb.執行緒', 6)}")
            con.execute(f"SET memory_limit = '{memory_limit or cfg('duckdb.記憶體上限', '11GB')}'")
            tmp = cfg("duckdb.暫存目錄")
            if tmp:
                Path(tmp).mkdir(parents=True, exist_ok=True)
                con.execute(f"SET temp_directory = '{tmp}'")
            # 大表寫入時不保序，換取記憶體與速度
            con.execute("SET preserve_insertion_order = false")

        # Big5/CP950 —— 台灣資料的日常，不載入就是亂碼
        try:
            con.execute("INSTALL encodings; LOAD encodings;")
        except Exception as e:  # noqa: BLE001
            print(
                f"⚠ encodings 擴充載入失敗（{e}）。\n"
                f"  讀 Big5/CP950 檔案會亂碼。首次載入需要網路。",
                file=sys.stderr,
            )
        yield con
    finally:
        con.close()


def q(project: str, sql: str, **params: Any):
    """跑一句唯讀查詢，回 DataFrame。給探索與檢查用。"""
    with connect(project, read_only=True) as con:
        return con.execute(sql, params).df() if params else con.execute(sql).df()


def tables(project: str) -> list[str]:
    """列出專案資料庫裡的所有表。"""
    with connect(project, read_only=True) as con:
        rows = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchall()
    return [r[0] for r in rows]


def _main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        print("用法：python db.py <專案代號>")
        return 2

    project = sys.argv[1]
    p = project_dir(project, create=False)
    print("=" * 60)
    print(f"專案：{project}")
    print(f"資料庫：{p.db}")
    print(f"存在：{'是' if p.db.exists() else '否（第一次連線會建立）'}")
    print("=" * 60)

    try:
        with connect(project) as con:
            ver = con.execute("SELECT version()").fetchone()[0]
            print(f"DuckDB {ver} 連線成功")
            settings = con.execute(
                "SELECT name, value FROM duckdb_settings() "
                "WHERE name IN ('threads','memory_limit','temp_directory',"
                "'preserve_insertion_order') ORDER BY name"
            ).fetchall()
            for name, value in settings:
                print(f"  {name:<26} {value}")
            # 用同一條連線查，不要再開一條 —— DuckDB 不允許同檔不同設定的並存連線
            ts = [
                r[0]
                for r in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'main' ORDER BY table_name"
                ).fetchall()
            ]
            print(f"\n現有表：{len(ts)} 張")
            for t in ts[:20]:
                print(f"  {t}")
            if len(ts) > 20:
                print(f"  …另有 {len(ts) - 20} 張")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"⛔ 連線失敗：{e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
