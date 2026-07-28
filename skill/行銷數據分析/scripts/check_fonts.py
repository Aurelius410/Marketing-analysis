#!/usr/bin/env python3
"""
產圖前的字型 gate（19 §3.3）—— 退出碼非 0 就不准產圖。

為什麼需要一道專門的關卡：
  **缺字是靜默失敗。** PNG 路徑（vl-convert / matplotlib）的字型來自**產圖的
  這台機器**；字沒裝，圖照樣產出來、檔案大小正常、沒有 warning，只是中文全變
  豆腐字 □□□。等你看到成品時，圖已經進投影片了（19 §3.3 的三條渲染路徑表）。

  HTML 互動圖的失敗模式不同：字型來自**收件人的機器**，失敗是靜默 fallback ——
  版面跑掉、行高變、標籤重疊。所以對外一律 @font-face 內嵌 subset，
  不依賴收件人，而內嵌會踩到授權（見 --embed）。

檢查方式刻意不靠「渲染後數像素」：
  19 §3.3 的原始草稿寫「渲染 PROBE_TEXT、算墨水像素、方框比例異常 → exit 1」。
  那是啟發式的 —— 門檻要憑經驗訂，而且不同 DPI／不同 matplotlib 版本會漂。
  本腳本改成**直接讀字型檔的 cmap 表**：某個字有沒有字符，是二元事實，
  查得到就是查得到。fontTools 是 matplotlib 的相依套件，不必額外裝。
  渲染只留一項用途 —— 驗可變字型的字重 instancing（那件事 cmap 看不出來）。

五道檢查：
  1. 必要字型家族是否安裝（家族名，不是檔名 —— CSS / Vega-Lite 的 font
     屬性填的是家族名）
  2. 探針字串的每個字元在該字型的 cmap 裡是否都有字符（缺一個就是豆腐字）
  3. 可變字型的字重 instancing（19 §3.2 實測：matplotlib 不做 instancing）
  4. 數字是否等寬（19 §3.2 + 18-T10：tabular-nums 對 Noto／正黑體是無效宣告，
     幸好它們預設就等寬；Noto Serif TC 宣告了也救不回來）
  5. --embed 模式的授權白名單（內嵌散布會踩到 JhengHei / Times New Roman 的授權）

19 §715 明訂：**換字型／換機器／升 matplotlib 就要重跑這支腳本。**
§3.2 的兩條結論都是本機實測值，換環境就失效 —— 要重測，不是照抄。
本腳本第 3、4 項就是那個「重測」，每次跑都是現場量的。

用法：
    python check_fonts.py                    # 產 PNG 前的例行檢查
    python check_fonts.py --embed            # 要內嵌字型對外散布時
    python check_fonts.py --family "Noto Serif TC"   # 追加檢查某個家族
    python check_fonts.py --self-test

退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 全通過，可以產圖
    1  = 有 error，**不准產圖**（家族缺席、探針字缺字符）
    2  = 只有 warning（可變字型無法產生粗體、數字非等寬、授權需確認）
    64 = 用法錯誤
    70 = 腳本自身異常
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import cfg  # noqa: E402
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 19 §3.3 的必要家族。中文正文 + 對外散布備援 + 英文襯線。
REQUIRED_FAMILIES = ["Microsoft JhengHei", "Noto Sans TC", "Times New Roman"]

# 探針字串刻意混雜：中文、英數、全形標點、括號、半形減號與 Unicode 減號、
# 百分比。這些正是圖表標籤真的會用到的字，而缺字最常缺在標點與 −（U+2212）。
PROBE_TEXT = "會員回購率 vs 廣告 ROAS｜月份 (2026 Q1)｜變化 −12.5%"

# 對外散布時不可內嵌的字型（授權原因）。19 §3.3 的決策樹：
# 要對外 → 中文切 Noto Sans TC（OFL）、襯線需求切 Noto Serif / Source Serif 4。
NOT_REDISTRIBUTABLE = {
    "Microsoft JhengHei": "微軟正黑體隨 Windows 授權，不得單獨內嵌散布",
    "Microsoft JhengHei UI": "同上",
    "Times New Roman": "Monotype 商標字型，隨 Windows／Office 授權，不得內嵌散布",
    "PMingLiU": "隨 Windows 授權，不得內嵌散布",
    "DFKai-SB": "隨 Windows 授權，不得內嵌散布",
}
OFL_SAFE_PREFIX = ("Noto ", "Source ", "Open Sans", "Roboto", "Lato",
                   "IBM Plex", "Fira ", "Inter", "思源")

# 有安全替代字的字符。缺這些不是災難，但打下去就是一個豆腐字。
# U+2212 是排版上正確的減號（與加號等寬、與數字對齊），也是 19 的圖表標籤
# 範例用的字 —— 而**微軟正黑體全部字重都沒有它**（本機實測，見 §②）。
SAFE_SUBSTITUTE: dict[int, tuple[str, str]] = {
    0x2212: ("–", "真減號（U+2212）在中文字型裡很常缺；"),
    0x2013: ("-", "en dash；"),
    0x2014: ("-", "em dash；"),
    0xFF5C: ("|", "全形直線；"),
}

# CJK 統一漢字與常見中日韓區塊。用來判斷一個家族「管不管中文」。
_CJK_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
               (0x20000, 0x2FA1F), (0x3040, 0x30FF), (0xAC00, 0xD7AF))


def is_cjk(cp: int) -> bool:
    return any(lo <= cp <= hi for lo, hi in _CJK_RANGES)


_errors: list[str] = []
_warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def detail(msg: str) -> None:
    print(f"     · {msg}")


def warn(fact: str, todo: str) -> None:
    _warnings.append(f"{fact}｜{todo}")
    print(f"  ⚠ {fact}")
    print(f"     → {todo}")


def err(fact: str, todo: str) -> None:
    _errors.append(f"{fact}｜{todo}")
    print(f"  ⛔ {fact}")
    print(f"     → {todo}")


# ══════════════════════════════════════════════════════════════
#  字型定位
# ══════════════════════════════════════════════════════════════
def installed_families() -> dict[str, list[Path]]:
    """家族名 → 該家族的字型檔清單。

    用 matplotlib 的 font_manager 而不是讀 Windows 登錄檔：
      · 跨平台（同一支腳本要能在 macOS／Linux 容器跑）
      · 拿到的就是 matplotlib **實際會用**的那份清單 —— 登錄檔有、
        font_manager 沒收進來的字型，產圖時一樣用不到
    """
    from matplotlib import font_manager as fm
    out: dict[str, list[Path]] = {}
    for f in fm.fontManager.ttflist:
        out.setdefault(f.name, []).append(Path(f.fname))
    return out


def open_faces(path: Path) -> list[Any]:
    """打開字型檔的**所有** face。

    .ttc 一個檔裝多個 face（msjh.ttc 就同時有 Microsoft JhengHei 與
    Microsoft JhengHei UI），只取 fonts[0] 會漏掉其他 face。
    更糟的是 matplotlib 的 ttflist 排序不保證，同一個家族取「第一個檔」
    可能拿到 Light —— 而 Light 與 Regular 的數字度量完全不同（實測見 §④）。
    """
    from fontTools.ttLib import TTFont, TTCollection
    if path.suffix.lower() in (".ttc", ".otc"):
        return list(TTCollection(str(path)).fonts)
    return [TTFont(str(path), fontNumber=0, lazy=True)]


def face_label(font: Any, path: Path, idx: int) -> str:
    try:
        fam = font["name"].getDebugName(1) or path.stem
        sub = font["name"].getDebugName(2) or f"face{idx}"
        return f"{fam} {sub}"
    except Exception:  # noqa: BLE001
        return f"{path.name} face{idx}"


def cmap_codepoints(path: Path) -> set[int]:
    """字型檔實際涵蓋的碼位（聯集全部 face）。查 cmap 是二元事實，不用猜像素。"""
    cps: set[int] = set()
    for font in open_faces(path):
        try:
            for table in font["cmap"].tables:
                cps.update(table.cmap.keys())
        finally:
            font.close()
    return cps


# ══════════════════════════════════════════════════════════════
#  ① 家族安裝  ② 字符涵蓋
# ══════════════════════════════════════════════════════════════
def check_presence_and_coverage(families: list[str],
                                probe: str) -> dict[str, dict[str, Any]]:
    inst = installed_families()
    results: dict[str, dict[str, Any]] = {}
    print(f"\n① 必要字型家族是否安裝（本機共 {len(inst)} 個家族）")
    for fam in families:
        r: dict[str, Any] = {"家族": fam}
        if fam not in inst:
            near = [k for k in inst if fam.split()[0].lower() in k.lower()][:3]
            err(f"缺少字型家族「{fam}」",
                f"產 PNG 時中文會變豆腐字 □□□ 而且**不會有任何警告**。"
                f"裝上它，或改 config.yml 的 字型.中文／字型.英文。"
                + (f"本機有類似的：{'、'.join(near)}" if near else ""))
            r["安裝"] = False
            results[fam] = r
            continue
        r["安裝"] = True
        r["檔案"] = [str(p) for p in inst[fam]]
        ok(f"{fam}（{len(inst[fam])} 個字型檔）")
        results[fam] = r

    print(f"\n② 探針字串的字符涵蓋（缺一個字符就是一個豆腐字）")
    detail(f"探針：{probe}")
    need = sorted({ord(ch) for ch in probe if not ch.isspace()})
    cjk_need = [cp for cp in need if is_cjk(cp)]
    for fam in families:
        r = results[fam]
        if not r.get("安裝"):
            continue
        covered: set[int] = set()
        for p in inst[fam]:
            try:
                covered |= cmap_codepoints(p)
            except Exception as e:  # noqa: BLE001
                warn(f"{fam} 的 {p.name} 讀不開（{type(e).__name__}）",
                     "跳過這個檔，改用同家族的其他檔判斷。若整個家族都讀不開，"
                     "字型檔可能損毀，重裝")
        # 這個家族到底管不管中文？全部 CJK 都沒有 = 它是英數字型，
        # 缺中文是**設計本意**（19 §3.1：中文微軟正黑體、英文 Times New Roman），
        # 不是缺陷。有一半沒一半才是真的破洞。
        cjk_have = sum(1 for cp in cjk_need if cp in covered)
        latin_only = bool(cjk_need) and cjk_have == 0
        r["涵蓋範圍"] = "英數字型" if latin_only else "含中文"
        check_cps = [cp for cp in need if not is_cjk(cp)] if latin_only else need

        missing = [cp for cp in check_cps if cp not in covered]
        # 有安全替代字的（例如真減號 −）降級成 warning：它不會讓整份圖毀掉，
        # 但打下去就是一個豆腐字，必須讓人知道要換字。
        hard = [cp for cp in missing if cp not in SAFE_SUBSTITUTE]
        soft = [cp for cp in missing if cp in SAFE_SUBSTITUTE]
        r["缺字"] = [f"U+{cp:04X} {chr(cp)}" for cp in missing]

        if latin_only:
            detail(f"{fam} 不含中文 → 判定為英數字型，只驗非中文字符"
                   f"（19 §3.1：英文 Times New Roman、中文另指定家族）")
        if hard:
            shown = "、".join(f"U+{cp:04X}「{chr(cp)}」"
                              f"（{unicodedata.name(chr(cp), '?')}）"
                              for cp in hard[:6])
            err(f"{fam} 缺 {len(hard)} 個字符：{shown}"
                + ("…" if len(hard) > 6 else ""),
                "這些字在圖上會是 □，而且不會有任何警告。"
                "換一個涵蓋這些字的家族，或把 matplotlib 的 font.family 設成"
                "清單讓它逐一 fallback")
        if soft:
            for cp in soft:
                sub, why = SAFE_SUBSTITUTE[cp]
                warn(f"{fam} 沒有 U+{cp:04X}「{chr(cp)}」"
                     f"（{unicodedata.name(chr(cp), '?')}）",
                     f"打下去就是一個 □。{why}"
                     f"改用「{sub}」（U+{ord(sub):04X}），"
                     f"或該欄位改指定有這個字的家族")
        if not missing:
            ok(f"{fam} 涵蓋要驗的全部 {len(check_cps)} 個字符"
               + ("（英數部分）" if latin_only else ""))
    return results


# ══════════════════════════════════════════════════════════════
#  ③ 可變字型的字重 instancing（19 §3.2 的實測，每次現場重測）
# ══════════════════════════════════════════════════════════════
def _ink_pixels(text: str, family: str, weight: str) -> int:
    """把文字畫進離屏畫布，數非白像素。用來比 normal 與 bold 是否真的不同。"""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(4, 1), dpi=100)
    fig.text(0.02, 0.35, text, fontfamily=family, fontweight=weight, fontsize=22)
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[..., :3]
    plt.close(fig)
    return int((buf < 250).any(axis=2).sum())


def check_variable_font_weight(families: list[str]) -> list[dict[str, Any]]:
    """matplotlib 對可變字型不做 instancing —— normal 與 bold 會渲染成同一個東西。

    19 §3.2 的本機實測：NotoSansTC-VF.ttf 只被註冊為 weight=100 一筆，
    渲染「營收 2026」22pt 後 normal 與 bold 逐位元組完全相同（墨水像素都是
    2,121）。微軟正黑體有三個實體字重，bold/normal 墨水比 1.233。
    這一節每次跑都現場重量 —— 換機器、升 matplotlib 就會變。
    """
    print("\n③ 可變字型的字重 instancing（19 §3.2；本機實測值，不可照抄）")
    rows = []
    probe = "營收 2026"
    for fam in families:
        try:
            n_reg = _ink_pixels(probe, fam, "normal")
            n_bold = _ink_pixels(probe, fam, "bold")
        except Exception as e:  # noqa: BLE001
            warn(f"{fam} 的字重量測失敗（{type(e).__name__}: {e}）",
                 "跳過這一項。若要中文粗體，先確認該家族有實體粗體字重")
            continue
        ratio = (n_bold / n_reg) if n_reg else float("nan")
        same = n_reg == n_bold
        rows.append({"家族": fam, "normal墨水": n_reg, "bold墨水": n_bold,
                     "比值": round(ratio, 3),
                     "結論": "無法產生粗體" if same else "有實體粗體"})
        detail(f"{fam}：normal {n_reg:,} / bold {n_bold:,} 墨水像素"
               f"（比值 {ratio:.3f}）")
        if same:
            warn(f"{fam} 的 bold 與 normal 渲染結果完全相同 —— 產不出粗體",
                 "matplotlib 對可變字型不做 instancing，整個 VF 檔只會被註冊成"
                 "一筆字重。要中文粗體只有兩條路：裝該家族的靜態字重 OTF"
                 "（Noto Sans TC 有七字重），或本機產出改用微軟正黑體"
                 "（三個實體字重）。**不要靠 fontweight='bold' 當強調手段**，"
                 "改用顏色或大小")
        else:
            ok(f"{fam} 有實體粗體（墨水比 {ratio:.3f}）")
    return rows


# ══════════════════════════════════════════════════════════════
#  ④ 數字等寬（18-T10）
# ══════════════════════════════════════════════════════════════
def check_tabular_numerals(families: list[str]) -> list[dict[str, Any]]:
    """數字欄位要對齊，靠的是字型本身等寬，不是 CSS 宣告。

    18-T10：font-variant-numeric: tabular-nums 對 Noto 與正黑體是**無效宣告**
    —— 它們的 GSUB/GPOS 根本沒有 tnum feature。幸好兩者預設就等寬。
    但 Noto Serif TC 宣告了也救不回來，數字欄不能用它。
    """
    print("\n④ 數字是否等寬（18-T10：tabular-nums 對這些字型是無效宣告）")
    inst = installed_families()
    rows = []
    for fam in families:
        if fam not in inst:
            continue
        # **逐 face 量，不要挑第一個檔。** 同一個家族的不同字重可以有完全不同的
        # 數字度量：實測微軟正黑體 Regular 1187/2048=0.5796 em（等寬）、
        # Bold 1220/2048=0.5957 em（等寬但與 Regular 不同）、
        # Light 有 793/1105/1142/1178 四種寬度（根本不等寬）。
        # 取 inst[fam][0] 會拿到哪一個由 matplotlib 的排序決定 —— 那是碰運氣。
        faces_seen = []
        for path in inst[fam]:
            try:
                faces = open_faces(path)
            except Exception:  # noqa: BLE001
                continue
            for i, font in enumerate(faces):
                try:
                    label = face_label(font, path, i)
                    upem = font["head"].unitsPerEm
                    cmap = font.getBestCmap()
                    hmtx = font["hmtx"]
                    widths = [hmtx[cmap[ord(d)]][0] for d in "0123456789"
                              if ord(d) in cmap and cmap[ord(d)] in hmtx.metrics]
                    has_tnum = False
                    for tag in ("GSUB", "GPOS"):
                        if tag in font:
                            try:
                                feats = {fr.FeatureTag for fr in
                                         font[tag].table.FeatureList.FeatureRecord}
                                has_tnum = has_tnum or ("tnum" in feats)
                            except AttributeError:
                                pass
                finally:
                    font.close()
                if len(widths) < 10:
                    continue
                kinds = len(set(widths))
                faces_seen.append({
                    "家族": fam, "字面": label, "數字寬度種類": kinds,
                    "寬度em": round(widths[0] / upem, 4) if kinds == 1 else None,
                    "全部寬度em": sorted(round(w / upem, 4) for w in set(widths)),
                    "宣告tnum": has_tnum,
                    "結論": "等寬" if kinds == 1 else f"{kinds} 種寬度，不等寬"})

        if not faces_seen:
            warn(f"{fam} 取不齊 0–9 的寬度",
                 "這個家族可能不含完整數字，數字欄改用別的家族")
            continue
        rows += faces_seen
        for f in faces_seen:
            detail(f"{f['字面']}：{f['結論']}"
                   + (f"（{f['寬度em']:.4f} em）" if f["寬度em"] else
                      f"（{f['全部寬度em']} em）")
                   + f"｜{'有' if f['宣告tnum'] else '沒有'} tnum feature")
        bad = [f for f in faces_seen if f["數字寬度種類"] > 1]
        if not bad:
            ok(f"{fam} 各字重的數字都等寬 → 數字欄可用"
               f"（CSS 的 tabular-nums 加不加都一樣）")
        else:
            warn(f"{fam} 有 {len(bad)}/{len(faces_seen)} 個字重的數字不等寬："
                 + "、".join(f"{f['字面']}（{f['數字寬度種類']} 種）" for f in bad),
                 "數字欄不要用這幾個字重 —— 這些字型沒有 tnum feature，"
                 "宣告 font-variant-numeric: tabular-nums 也救不回來（18-T10）。"
                 "同家族換一個等寬的字重，或數字欄改用 Noto Sans TC")
        widths_by_face = {f["字面"]: f["寬度em"] for f in faces_seen if f["寬度em"]}
        if len(set(widths_by_face.values())) > 1:
            detail(f"注意：{fam} 各字重雖然各自等寬，但寬度彼此不同"
                   f"（{widths_by_face}）—— 同一張表混用字重，欄位仍然對不齊")
    return rows


# ══════════════════════════════════════════════════════════════
#  ⑤ 內嵌授權
# ══════════════════════════════════════════════════════════════
def check_embed_license(families: list[str]) -> list[dict[str, Any]]:
    print("\n⑤ 內嵌散布的授權白名單（--embed）")
    rows = []
    for fam in families:
        reason = NOT_REDISTRIBUTABLE.get(fam)
        safe = fam.startswith(OFL_SAFE_PREFIX)
        rows.append({"家族": fam,
                     "可內嵌": bool(safe and not reason),
                     "說明": reason or ("OFL 或同級開源授權" if safe else "授權未知")})
        if reason:
            warn(f"「{fam}」不可內嵌散布：{reason}",
                 "19 §3.3 決策樹：要對外 → 中文切 Noto Sans TC（OFL）、"
                 "襯線需求切 Noto Serif／Source Serif 4。切換時**主動告知對方**："
                 "「這份要對外，字型已從微軟正黑體換成 Noto Sans TC（授權原因），"
                 "版面寬度會有微幅變化」")
        elif safe:
            ok(f"{fam} 可內嵌（{rows[-1]['說明']}）")
        else:
            warn(f"「{fam}」的內嵌授權未知",
                 "查該字型的授權條款再決定。不確定就不要內嵌 —— "
                 "改成 HTML 用 web-safe fallback 清單")
    return rows


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    families = list(REQUIRED_FAMILIES)
    for f in args.family or []:
        if f not in families:
            families.append(f)
    # config.yml 指定的字型也一併驗 —— 那才是產圖時真的會用到的
    for key in ("字型.中文", "字型.英文", "字型.對外散布備援"):
        v = cfg(key)
        if v and v not in families:
            families.append(str(v))

    probe = args.probe or PROBE_TEXT

    print("=" * 72)
    print("行銷數據分析 Skill — 產圖前字型 gate（19 §3.3）")
    print(f"要驗的家族：{'、'.join(families)}")
    print(f"模式：{'內嵌散布（--embed）' if args.embed else '本機產圖'}")
    print("=" * 72)

    cov = check_presence_and_coverage(families, probe)
    present = [f for f in families if cov.get(f, {}).get("安裝")]
    wrows = check_variable_font_weight(present) if not args.skip_render else []
    trows = check_tabular_numerals(present)
    lrows = check_embed_license(families) if args.embed else []

    print("\n" + "=" * 72)
    n_err, n_warn = len(_errors), len(_warnings)
    print(f"error {n_err}、warning {n_warn}")
    if n_err:
        print("結果：⛔ **不准產圖**。缺字是靜默失敗 —— 圖會產出來、大小正常、")
        print("      沒有警告，只是中文全變 □。先把上面的 error 解掉。")
    elif n_warn:
        print("結果：⚠ 可以產圖，但上面的限制要記住（尤其粗體與數字欄那兩條）。")
    else:
        print("結果：✅ 可以產圖。")
    print("      19 §715：換字型／換機器／升 matplotlib 就要重跑這支腳本 ——")
    print("      ③④ 兩項是本機實測值，換環境就失效，要重測不是照抄。")

    if args.json:
        import json
        payload = {
            "families": families, "probe": probe, "embed": bool(args.embed),
            "coverage": cov, "weight": wrows, "numerals": trows,
            "license": lrows, "errors": _errors, "warnings": _warnings,
        }
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✓ 結果已寫入 {args.json}")

    if n_err:
        return EX_ERROR
    return EX_WARN if n_warn else EX_OK


def _selftest() -> int:
    print("=" * 72)
    print("check_fonts.py 自我測試")
    print("=" * 72)
    failed = []

    def check(name: str, cond: bool, got: str = "") -> None:
        print(("  ✓ " if cond else "  ✗ ") + name + (f"（{got}）" if got else ""))
        if not cond:
            failed.append(name)

    inst = installed_families()
    check("列得出本機字型家族", len(inst) > 0, f"{len(inst)} 個")

    # cmap 查詢對「一定沒有中文」的字型必須回缺字 —— 驗檢查器本身有效
    ascii_only = next((f for f in ("Times New Roman", "Arial", "Courier New")
                       if f in inst), None)
    if ascii_only:
        cps = cmap_codepoints(inst[ascii_only][0])
        check(f"{ascii_only} 有 ASCII 'A'", ord("A") in cps)
        check(f"{ascii_only} 沒有「會」（檢查器抓得到缺字）",
              ord("會") not in cps,
              "若這裡失敗，代表 cmap 查詢沒在真的查")
    if "Noto Sans TC" in inst:
        cps: set[int] = set()
        for p in inst["Noto Sans TC"]:
            cps |= cmap_codepoints(p)
        miss = [c for c in PROBE_TEXT if not c.isspace() and ord(c) not in cps]
        check("Noto Sans TC 涵蓋整條探針字串（含真減號）", not miss,
              f"缺 {''.join(miss)}" if miss else "全覆蓋")
    if "Microsoft JhengHei" in inst:
        cps = set()
        for p in inst["Microsoft JhengHei"]:
            cps |= cmap_codepoints(p)
        # 本機實測：微軟正黑體三個檔、六個 face 全都沒有 U+2212。
        # 這一項固定住那個事實 —— 哪天它變了（換 Windows 版本），要知道。
        check("偵測得到微軟正黑體缺 U+2212（真減號）", 0x2212 not in cps,
              "若這裡失敗代表本機的正黑體版本不同，19 §3.2 的那段實測要重寫")
    check("探針含 U+2212（真減號，中文字型最常缺的字）", "−" in PROBE_TEXT)
    check("U+2212 有登記安全替代字 → 判 warning 不判 error",
          0x2212 in SAFE_SUBSTITUTE)
    check("CJK 判定：「會」是中文、'A' 不是",
          is_cjk(ord("會")) and not is_cjk(ord("A")))

    # 數字等寬要**逐字重**驗。19 §3.2 只寫「JhengHei 也等寬（0.5796 em）」，
    # 那對 Regular 成立、對 Light 不成立 —— 只量一個檔會拿到隨機的答案。
    if "Microsoft JhengHei" in inst:
        rows = check_tabular_numerals(["Microsoft JhengHei"])
        reg = next((r for r in rows if r["字面"] == "Microsoft JhengHei Regular"), None)
        light = next((r for r in rows if "Light" in r["字面"]), None)
        if reg:
            check("正黑體 Regular 數字等寬且為 0.5796 em（19 §3.2 的數字）",
                  reg["數字寬度種類"] == 1 and abs(reg["寬度em"] - 0.5796) < 5e-4,
                  f"{reg['數字寬度種類']} 種、{reg['寬度em']} em")
        check("有量到 Light 字重（逐 face 才看得到）", light is not None)
        if light:
            check("正黑體 Light 數字**不**等寬 —— 只量一個檔會漏掉這件事",
                  light["數字寬度種類"] > 1,
                  f"{light['數字寬度種類']} 種寬度 {light['全部寬度em']}")
    if "Noto Sans TC" in inst:
        rows = check_tabular_numerals(["Noto Sans TC"])
        check("Noto Sans TC 數字等寬且為 0.521 em（19 §3.2 的數字）",
              bool(rows) and rows[0]["數字寬度種類"] == 1
              and abs(rows[0]["寬度em"] - 0.521) < 5e-4,
              f"{rows[0]['寬度em']} em" if rows else "量不到")

    # 授權判定
    lic = {r["家族"]: r for r in check_embed_license(
        ["Microsoft JhengHei", "Noto Sans TC", "Times New Roman"])}
    check("微軟正黑體判為不可內嵌", lic["Microsoft JhengHei"]["可內嵌"] is False)
    check("Times New Roman 判為不可內嵌", lic["Times New Roman"]["可內嵌"] is False)
    check("Noto Sans TC 判為可內嵌", lic["Noto Sans TC"]["可內嵌"] is True)

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="產圖前的字型 gate（19 §3.3）。退出碼非 0 就不准產圖。")
    ap.add_argument("--family", action="append",
                    help="追加要檢查的字型家族（可重複）")
    ap.add_argument("--probe", help="自訂探針字串（預設含中英數與全形標點）")
    ap.add_argument("--embed", action="store_true",
                    help="要內嵌字型對外散布 —— 追加授權白名單檢查")
    ap.add_argument("--skip-render", action="store_true",
                    help="跳過字重 instancing 檢查（無圖形後端的環境用）")
    ap.add_argument("--json", help="把結果另寫成 JSON")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    try:
        return run(args)
    except ImportError as e:
        print(f"\n⛔ 缺少必要套件：{e}", file=sys.stderr)
        print(f"   退出碼 {EX_ERROR} —— pip install -r requirements.txt（第 1 層）",
              file=sys.stderr)
        return EX_ERROR


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ check_fonts.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
