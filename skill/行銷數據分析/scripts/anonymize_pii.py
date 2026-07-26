#!/usr/bin/env python3
"""
把素材庫與文件裡的第三方個資（姓名、學號）統一換成代號。

設計原則：
  · 分析價值 100% 保留 —— digest 引用姓名只是當「證據錨點」，
    我們要的是「這個錯誤長什麼樣」，不是「誰犯的」。
  · 對照表存在本機且進 .gitignore，需要回查時查得到。
  · 冪等：重跑不會把代號再換一次。

用法：
    python anonymize_pii.py --dry-run          # 只看會改什麼，不動檔案
    python anonymize_pii.py                    # 實際執行
    python anonymize_pii.py --root <路徑>      # 指定掃描根目錄
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# Windows 主控台輸出中文用
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from paths import SKILL_ROOT
    DEFAULT_ROOT = SKILL_ROOT.parent.parent      # skill/<名稱>/ → skill/ → repo root
except ImportError:                              # 單獨複製這支腳本時的退路
    DEFAULT_ROOT = Path.cwd()

# --- 要匿名化的第三方 ---------------------------------------------------
# 依在素材庫出現的次數排序，代號一經指定就不要再改（否則舊文件對不上）
THIRD_PARTY_NAMES = [
    "陳依靜", "蔡函紜", "張翔駿", "吳宇翔", "游方慈", "陳秉翔", "吳逸寧",
    "賴怡帆", "楊翔宇", "宋美娜", "張雅喬", "蘇永逸", "賴亮宇", "蔡承翰",
    "李芝瑩", "李泰坤", "郭冠廷", "朱姵甄", "張澤群",
]

# 學號格式：b/r + 8~9 碼；以及跨校前綴
ID_PATTERNS = [
    re.compile(r"\b([br]1[0-9]{8})\b"),
    re.compile(r"\b(ntnu_[0-9A-Za-z]+)\b"),
    re.compile(r"\b(ntust_[0-9A-Za-z]+)\b"),
]

# 使用者本人，不匿名化（這是他自己的 repo）
OWNER_TOKENS = {"陳柏寰", "包子", "R13724054", "r13724054"}

SCAN_DIRS = ["00_source_archive", "skill", "10_blueprint"]
SCAN_SUFFIXES = {".md", ".py", ".sql", ".csv", ".json", ".yml", ".yaml"}

MAPPING_FILE = "_pii_mapping.json"   # 進 .gitignore


def build_name_map() -> dict[str, str]:
    """姓名 → 學生A / 學生B / …；超過 26 個用 學生AA 形式。"""
    out = {}
    for i, name in enumerate(THIRD_PARTY_NAMES):
        if i < 26:
            code = f"學生{chr(ord('A') + i)}"
        else:
            code = f"學生{chr(ord('A') + i // 26 - 1)}{chr(ord('A') + i % 26)}"
        out[name] = code
    return out


def collect_files(root: Path) -> list[Path]:
    """收集待掃描檔案。排除本腳本自己 —— 它的姓名清單會被自己換掉。"""
    self_path = Path(__file__).resolve()
    files = []
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if p.resolve() == self_path or p.name == MAPPING_FILE:
                continue
            files.append(p)
    return files


def anonymize_text(text: str, name_map: dict[str, str],
                   id_map: dict[str, str], id_counter: list[int]) -> tuple[str, int]:
    """回傳 (新內容, 替換次數)。id_map 會就地累積新發現的學號。"""
    hits = 0

    for name, code in name_map.items():
        if name in text:
            hits += text.count(name)
            text = text.replace(name, code)

    for pat in ID_PATTERNS:
        def _sub(m):
            nonlocal hits
            raw = m.group(1)
            if raw in OWNER_TOKENS:
                return raw
            if raw not in id_map:
                id_counter[0] += 1
                id_map[raw] = f"學號{id_counter[0]:03d}"
            hits += 1
            return id_map[raw]
        text = pat.sub(_sub, text)

    return text, hits


def main() -> int:
    ap = argparse.ArgumentParser(description="第三方個資匿名化")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="掃描根目錄")
    ap.add_argument("--dry-run", action="store_true", help="只報告，不改檔")
    args = ap.parse_args()

    root: Path = args.root
    if not root.exists():
        print(f"✗ 找不到根目錄：{root}")
        return 2

    name_map = build_name_map()
    id_map: dict[str, str] = {}
    id_counter = [0]

    files = collect_files(root)
    print("=" * 60)
    print(f"掃描根目錄：{root}")
    print(f"掃描檔案數：{len(files)}")
    print(f"匿名化對象：{len(name_map)} 個姓名 + 學號格式 {len(ID_PATTERNS)} 種")
    print(f"不匿名化（本人）：{'、'.join(sorted(OWNER_TOKENS))}")
    print("=" * 60)

    changed, total_hits = [], 0
    for p in files:
        try:
            original = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError) as e:
            print(f"⚠ 跳過（讀取失敗）：{p.name} — {e}")
            continue

        new_text, hits = anonymize_text(original, name_map, id_map, id_counter)
        if hits:
            total_hits += hits
            changed.append((p, hits))
            if not args.dry_run:
                p.write_text(new_text, encoding="utf-8")

    print()
    if changed:
        print(f"{'有異動的檔案':<48} 替換數")
        print("-" * 60)
        for p, hits in sorted(changed, key=lambda x: -x[1]):
            print(f"  {p.relative_to(root).as_posix():<46} {hits:>5}")
    else:
        print("沒有發現需要匿名化的內容（可能已經處理過）。")

    print("-" * 60)
    print(f"合計：{len(changed)} 個檔案、{total_hits} 處替換")

    if not args.dry_run and total_hits:
        mapping = {
            "generated_at": date.today().isoformat(),
            "note": "此檔含第三方個資對照，必須在 .gitignore 內，不得推上遠端。",
            "names": name_map,
            "student_ids": id_map,
        }
        mp = root / MAPPING_FILE
        mp.write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✓ 對照表已寫入：{mp}")
        print("  ⚠ 確認它在 .gitignore 裡再 commit。")

    if args.dry_run:
        print("\n（dry-run：未實際修改任何檔案）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
