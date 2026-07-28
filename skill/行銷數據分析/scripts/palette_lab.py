#!/usr/bin/env python3
"""
色盤驗證器 —— 把美感變成可跑的測試（18-G14、19 §2.3）。

**改任何色值前先跑這支，CI 也跑。**

為什麼需要它：
  「這兩個顏色看起來夠不夠不一樣」不是可以憑感覺回答的問題。19 §2.2 的深色
  第 5 槽灰試過 `#C7CFDA` / `#9AA5B4` / `#B9C2CE`，肉眼看都跟玫瑰紫差很多，
  但在 deuteranopia 模擬下 ΔE 只有 2.2–6.2（等於同色）；只有 `#8A94A3`
  拉得開。這種事必須量，不能看。

實作四件事（19 §2.3、04_design_system.md §936–940）：
  · sRGB ↔ linear、OKLab / OKLCH
  · WCAG 2.x 相對亮度與對比
  · Machado et al. (2009) 色覺缺陷模擬矩陣，severity 1.0
  · CIEDE2000 色差（D65/2°）

取捨（照抄 04_design_system.md §940，不要在使用時忘記）：
  Machado 矩陣是**線性近似**，不如 Brettel/Viénot 精確；CIEDE2000 用 D65/2°。
  對「排除明顯撞色」這個目的足夠，**不宜當作醫學級結論**。

門檻的出處（19 §2.3）：
  MIN_CONTRAST_MARK = 3.0   WCAG 1.4.11 非文字對比
  MIN_CONTRAST_TEXT = 4.5   WCAG AA 正文
  MIN_DELTA_E = 12.0        淺色主題。「ΔE > 10 為明顯不同色」是常見經驗值，
                            取 12 當安全邊際。**04_design_system.md §1212 自己
                            標註這是全文最重要的主觀參數 —— 沒有查到針對「資料
                            視覺化類別色最小色差」的正式標準。** 日後找到權威
                            依據要據以修正。
  MIN_DELTA_E_DARK = 9.0    深色主題。04_design_system.md §1.4 的深色表把 n=7
                            標成「✅（放寬至 ≥9）」—— 深色盤的 protan 9.7、
                            tritan 9.5 本來就過不了 12。**這個放寬原本只寫在
                            研究稿裡，沒進出貨的 reference 19 也沒進 tokens.json**，
                            所以拿 12 去驗深色盤的人會得到假警報。本檔把它補上。

用法：
    python palette_lab.py --validate            # 驗 assets/tokens.json（CI 跑這個）
    python palette_lab.py --contrast "#0072B2" "#FFFFFF"
    python palette_lab.py --simulate "#009E73"
    python palette_lab.py --delta-e "#F5E96B" "#FFC757"
    python palette_lab.py --fix "#E69F00" --on "#FFFFFF" --target 3.0
    python palette_lab.py --self-test

退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 全通過
    1  = 有 error（色盤不合格、tokens.json 的宣稱與實算對不上）
    2  = 只有 warning
    64 = 用法錯誤
    70 = 腳本自身異常
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SKILL_ROOT  # noqa: E402
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

MIN_CONTRAST_MARK = 3.0
MIN_CONTRAST_TEXT = 4.5
MIN_DELTA_E = 12.0          # 淺色主題
MIN_DELTA_E_DARK = 9.0      # 深色主題（見下方「為什麼深色放寬」）

# 色覺模擬要在哪個空間做 —— 這個選擇會動到每一個 ΔE 判定，所以講清楚。
#
# Machado et al. (2009) 的模型**定義在 linear RGB**，照理該先解 gamma。
# 但本 skill 全套色盤與門檻（19 §2.2 的淺色表、04_design_system.md §1.4 的
# 深色表、以及所有逐對 ΔE）都是在 **gamma 編碼的 sRGB** 上量出來的。實測比對：
#
#   配對                      文件記載   sRGB空間   linear空間
#   淺色盤 n=5 protan/deutan/tritan  12.9/13.2/13.0  12.89/13.20/13.01  12.26/16.11/12.07
#   深色盤 n=7 protan/deutan/tritan   9.7/11.6/9.5    9.66/11.56/9.48    9.84/9.64/8.83
#   深色 檸黃 vs 琥珀（deutan）        5.2            5.24              4.28
#   深色 灰 vs 玫瑰紫（deutan）       11.6           11.56             13.04
#
# sRGB 全部對上（誤差 ≤0.05），linear 差到 1.5。**門檻 12/9 是照 sRGB 的數字
# 校準的** —— 改空間等於讓每一個門檻失去意義（例如深色灰 vs 玫瑰紫會從
# 11.56「不過 12」變成 13.04「過 12」，結論翻轉）。
#
# 所以預設 srgb，保持與校準一致；要理論純度就用 --cvd-space linear，
# 但那時門檻要重新校準，不能沿用。
CVD_SPACE_DEFAULT = "srgb"
_cvd_space = CVD_SPACE_DEFAULT

# Machado, Oliveira & Fernandes (2009) 的 CVD 模擬矩陣，severity = 1.0。
# 原文定義在 linear RGB；本檔預設套在 sRGB —— 理由見上方 CVD_SPACE_DEFAULT。
CVD_MATRICES: dict[str, np.ndarray] = {
    "protan": np.array([[0.152286, 1.052583, -0.204868],
                        [0.114503, 0.786281, 0.099216],
                        [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968],
                        [0.280085, 0.672501, 0.047413],
                        [-0.011820, 0.042940, 0.968881]]),
    "tritan": np.array([[1.255528, -0.076749, -0.178779],
                        [-0.078411, 0.930809, 0.147602],
                        [0.004733, 0.691367, 0.303900]]),
}
CVD_NAMES = {"protan": "紅色盲", "deutan": "綠色盲", "tritan": "藍色盲"}

# sRGB → XYZ（D65 白點），CIE Lab 要用
_M_RGB2XYZ = np.array([[0.4123907992659595, 0.3575843393838780, 0.1804807884018343],
                       [0.2126390058715104, 0.7151686787677559, 0.0721923153607337],
                       [0.0193308187155918, 0.1191947797946259, 0.9505321522496608]])
_D65 = np.array([0.9504559270516716, 1.0, 1.0890577507598784])

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
#  色彩空間
# ══════════════════════════════════════════════════════════════
def hex_to_rgb(h: str) -> np.ndarray:
    s = h.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"色值格式不對：{h!r}（要 #RRGGBB 或 #RGB）")
    try:
        return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255.0
    except ValueError as e:
        raise ValueError(f"色值格式不對：{h!r}") from e


def rgb_to_hex(rgb: Iterable[float]) -> str:
    v = np.clip(np.asarray(list(rgb), dtype=float), 0, 1)
    return "#" + "".join(f"{int(round(c * 255)):02X}" for c in v)


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(np.asarray(c, dtype=float), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def relative_luminance(h: str) -> float:
    """WCAG 2.x 相對亮度。係數 0.2126/0.7152/0.0722 是規範明訂的。"""
    lin = srgb_to_linear(hex_to_rgb(h))
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def contrast(fg: str, bg: str) -> float:
    """WCAG 對比。(L1+0.05)/(L2+0.05)，亮的當分子。白對黑恰為 21.0。"""
    a, b = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def simulate(h: str, kind: str, space: str | None = None) -> str:
    """Machado (2009) severity 1.0 的色覺缺陷模擬。

    space 預設 'srgb'（與本 skill 全套門檻的校準空間一致，見 CVD_SPACE_DEFAULT
    上方的長註解）。'linear' 是 Machado 原文定義的空間，但門檻要重新校準。
    """
    if kind not in CVD_MATRICES:
        raise ValueError(f"不認得的色覺類型：{kind!r}（要 protan／deutan／tritan）")
    sp = space or _cvd_space
    if sp == "linear":
        sim = CVD_MATRICES[kind] @ srgb_to_linear(hex_to_rgb(h))
        return rgb_to_hex(linear_to_srgb(np.clip(sim, 0.0, 1.0)))
    if sp != "srgb":
        raise ValueError(f"不認得的色彩空間：{sp!r}（要 srgb／linear）")
    return rgb_to_hex(np.clip(CVD_MATRICES[kind] @ hex_to_rgb(h), 0.0, 1.0))


def hex_to_lab(h: str) -> np.ndarray:
    """sRGB → CIE Lab（D65/2°）。CIEDE2000 吃的是這個，不是 OKLab。"""
    xyz = _M_RGB2XYZ @ srgb_to_linear(hex_to_rgb(h))
    t = xyz / _D65
    d = 6.0 / 29.0
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d ** 2) + 4.0 / 29.0)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def hex_to_oklab(h: str) -> np.ndarray:
    """Björn Ottosson 的 OKLab。做明度排序用（順序型色階要嚴格單調）。"""
    lin = srgb_to_linear(hex_to_rgb(h))
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(m1 @ lin)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return m2 @ lms


def hex_to_oklch(h: str) -> np.ndarray:
    L, a, b = hex_to_oklab(h)
    return np.array([L, float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a)) % 360)])


def ciede2000(h1: str, h2: str) -> float:
    """CIEDE2000 色差（Sharma, Wu & Dalal 2005 的實作形式）。

    參數 kL = kC = kH = 1。這是本檔唯一有標準測試資料可對的函式，
    自我測試用 Sharma 的表逐筆驗。
    """
    L1, a1, b1 = hex_to_lab(h1)
    L2, a2, b2 = hex_to_lab(h2)
    return _ciede2000_lab(L1, a1, b1, L2, a2, b2)


def _ciede2000_lab(L1: float, a1: float, b1: float,
                   L2: float, a2: float, b2: float) -> float:
    kL = kC = kH = 1.0
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cbar = (C1 + C2) / 2.0
    G = 0.5 * (1 - np.sqrt(Cbar ** 7 / (Cbar ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360 if (a2p or b2) else 0.0

    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp) / 2)

    Lbp = (L1 + L2) / 2.0
    Cbp = (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2.0
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2.0
    else:
        hbp = (h1p + h2p - 360) / 2.0

    T = (1 - 0.17 * np.cos(np.radians(hbp - 30))
         + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6))
         - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dtheta = 30 * np.exp(-(((hbp - 275) / 25.0) ** 2))
    RC = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    SL = 1 + (0.015 * (Lbp - 50) ** 2) / np.sqrt(20 + (Lbp - 50) ** 2)
    SC = 1 + 0.045 * Cbp
    SH = 1 + 0.015 * Cbp * T
    RT = -np.sin(np.radians(2 * dtheta)) * RC

    return float(np.sqrt((dLp / (kL * SL)) ** 2 + (dCp / (kC * SC)) ** 2
                         + (dHp / (kH * SH)) ** 2
                         + RT * (dCp / (kC * SC)) * (dHp / (kH * SH))))


# ══════════════════════════════════════════════════════════════
#  調整到目標對比
# ══════════════════════════════════════════════════════════════
def _shift_to_contrast(h: str, bg: str, target: float, direction: int) -> str | None:
    """在 OKLab 明度上二分搜尋，找到剛好達標的顏色。色相與彩度盡量保留。

    direction: -1 變暗、+1 變亮。到極端仍達不到就回 None（誠實回答做不到，
    不要回一個看起來像答案但沒達標的顏色）。
    """
    lo, hi = (0.0, hex_to_oklch(h)[0]) if direction < 0 else (hex_to_oklch(h)[0], 1.0)
    L0, C0, H0 = hex_to_oklch(h)

    def at(L: float) -> str:
        a = C0 * np.cos(np.radians(H0))
        b = C0 * np.sin(np.radians(H0))
        lab = np.array([L, a, b])
        m2i = np.linalg.inv(np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                                      [1.9779984951, -2.4285922050, 0.4505937099],
                                      [0.0259040371, 0.7827717662, -0.8086757660]]))
        lms = (m2i @ lab) ** 3
        m1i = np.linalg.inv(np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                                      [0.2119034982, 0.6806995451, 0.1073969566],
                                      [0.0883024619, 0.2817188376, 0.6299787005]]))
        return rgb_to_hex(linear_to_srgb(np.clip(m1i @ lms, 0.0, 1.0)))

    end = at(lo if direction < 0 else hi)
    if contrast(end, bg) < target:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if contrast(at(mid), bg) >= target:
            lo, hi = (mid, hi) if direction < 0 else (lo, mid)
        else:
            lo, hi = (lo, mid) if direction < 0 else (mid, hi)
    cand = at(lo if direction < 0 else hi)
    return cand if contrast(cand, bg) >= target else end


def darken_to_contrast(h: str, bg: str, target: float = MIN_CONTRAST_MARK) -> str | None:
    return _shift_to_contrast(h, bg, target, -1)


def lighten_to_contrast(h: str, bg: str, target: float = MIN_CONTRAST_MARK) -> str | None:
    return _shift_to_contrast(h, bg, target, +1)


# ══════════════════════════════════════════════════════════════
#  色盤報告
# ══════════════════════════════════════════════════════════════
def report(name: str, palette: list[str], bg: str,
           min_contrast: float = MIN_CONTRAST_MARK,
           min_delta_e: float = MIN_DELTA_E) -> dict[str, Any]:
    """一個色盤的完整體檢：對比 + 三種色覺缺陷下的兩兩最小色差。"""
    contrasts = {h: contrast(h, bg) for h in palette}
    worst_c = min(contrasts.values()) if contrasts else float("nan")

    de: dict[str, dict[str, Any]] = {}
    for kind in ("normal", "protan", "deutan", "tritan"):
        pairs = []
        for x, y in itertools.combinations(palette, 2):
            sx = x if kind == "normal" else simulate(x, kind)
            sy = y if kind == "normal" else simulate(y, kind)
            pairs.append((ciede2000(sx, sy), x, y))
        if pairs:
            pairs.sort()
            de[kind] = {"最小ΔE": round(pairs[0][0], 2),
                        "最接近的一對": (pairs[0][1], pairs[0][2])}

    passed = (worst_c >= min_contrast
              and all(v["最小ΔE"] >= min_delta_e for v in de.values()))
    return {"名稱": name, "背景": bg, "n": len(palette),
            "對比": {h: round(c, 2) for h, c in contrasts.items()},
            "最低對比": round(worst_c, 2), "色差": de, "通過": bool(passed)}


def print_report(r: dict[str, Any], min_contrast: float, min_delta_e: float) -> None:
    print(f"\n{r['名稱']}（n={r['n']}，背景 {r['背景']}）")
    for h, c in r["對比"].items():
        mark = "✓" if c >= min_contrast else "✗"
        detail(f"{mark} {h}  對比 {c:>6.2f}")
    for kind, v in r["色差"].items():
        mark = "✓" if v["最小ΔE"] >= min_delta_e else "✗"
        label = "正常視覺" if kind == "normal" else CVD_NAMES[kind]
        detail(f"{mark} {label:<6} 最小 ΔE {v['最小ΔE']:>6.2f}"
               f"（{v['最接近的一對'][0]} vs {v['最接近的一對'][1]}）")


# ══════════════════════════════════════════════════════════════
#  驗 assets/tokens.json
# ══════════════════════════════════════════════════════════════
def load_tokens() -> dict[str, Any]:
    p = SKILL_ROOT / "assets" / "tokens.json"
    if not p.exists():
        raise FileNotFoundError(
            f"找不到 {p} —— 它是圖表用色的單一來源（18-G14）。"
            f"沒有它就沒有東西可驗。")
    return json.loads(p.read_text(encoding="utf-8"))


def validate_tokens(tok: dict[str, Any]) -> None:
    thr = tok.get("驗證門檻", {})
    min_c = float(thr.get("MIN_CONTRAST_MARK", MIN_CONTRAST_MARK))
    min_de = float(thr.get("MIN_DELTA_E_LIGHT", MIN_DELTA_E))
    min_de_dark = float(thr.get("MIN_DELTA_E_DARK", MIN_DELTA_E_DARK))

    def de_for(theme_key: str) -> float:
        """深色盤的門檻本來就比較鬆（04_design_system.md §1.4 標「放寬至 ≥9」）。
        一律用 12 去驗會把出貨中的深色盤判成不合格 —— 那是假警報，不是發現。"""
        return min_de_dark if "深" in theme_key else min_de

    print("=" * 72)
    print("assets/tokens.json 色盤驗證（18-G14、19 §2.2）")
    print(f"門檻：非文字對比 ≥ {min_c}、CIEDE2000 最小色差 ≥ {min_de}")
    print("=" * 72)

    # ① 宣稱的對比值 vs 實算 —— tokens.json 裡的每個數字都要對得上
    print("\n① 宣稱的對比值與實算是否一致")
    mismatch = 0
    for theme_key, theme in tok["類別型色盤"].items():
        if not isinstance(theme, dict) or "背景" not in theme:
            continue
        bg = theme["背景"]
        for group in ("線條可用", "僅大面積填色"):
            for slot in theme.get(group, []):
                got = contrast(slot["hex"], bg)
                want = float(slot["對比"])
                if abs(got - want) > 0.02:
                    mismatch += 1
                    err(f"{theme_key} 第 {slot['槽']} 槽 {slot['名']} {slot['hex']}："
                        f"tokens.json 寫 {want}，實算 {got:.2f}",
                        "把 tokens.json 的數字改成實算值。宣稱與實算對不上時，"
                        "沒有人知道該信哪一個 —— 而後面所有配色決策都建立在這些數字上")
    for name, arr in (("順序型_品牌藍_淺色", ("品牌藍_淺色", "白底對比", "#FFFFFF")),
                      ("順序型_品牌藍_深色", ("品牌藍_深色", "深底對比", "#14181F"))):
        key, field, bg = arr
        blk = tok["順序型色盤"].get(key, {})
        for h, want in zip(blk.get("色階", []), blk.get(field, [])):
            got = contrast(h, bg)
            if abs(got - float(want)) > 0.02:
                mismatch += 1
                err(f"{name} {h}：tokens.json 寫 {want}，實算 {got:.2f}",
                    "同上，改成實算值")
    if not mismatch:
        ok("tokens.json 裡宣稱的每一個對比值都與實算相符")

    # ② 線條色盤要過門檻
    print("\n② 線條用色盤是否過門檻")
    for theme_key, theme in tok["類別型色盤"].items():
        if not isinstance(theme, dict) or "背景" not in theme:
            continue
        pal = [s["hex"] for s in theme.get("線條可用", [])]
        if not pal:
            continue
        thr_de = de_for(theme_key)
        r = report(f"類別型・{theme_key}・線條", pal, theme["背景"], min_c, thr_de)
        print_report(r, min_c, thr_de)
        detail(f"本盤色差門檻 ΔE ≥ {thr_de}"
               + ("（深色主題放寬，04_design_system.md §1.4）" if thr_de != min_de else ""))
        if not r["通過"]:
            bad_c = [h for h, c in r["對比"].items() if c < min_c]
            bad_e = [k for k, v in r["色差"].items() if v["最小ΔE"] < thr_de]
            err(f"{r['名稱']} 不合格"
                + (f"｜對比不足：{'、'.join(bad_c)}" if bad_c else "")
                + (f"｜色差不足：{'、'.join(CVD_NAMES.get(k, k) for k in bad_e)}" if bad_e else ""),
                "拿掉最後一槽再驗一次，或用 --fix 把該色調到達標。"
                f"19 §2.2 實測 n=5 是淺色主題全綠燈的最大槽數"
                f"（本盤門檻 ΔE ≥ {thr_de}）")
        else:
            ok(f"{r['名稱']} 全部過關（最低對比 {r['最低對比']}）")

    # ③ 順序型色階的明度必須嚴格單調 —— 不單調的色階讀者排不出大小
    print("\n③ 順序型色階的 OKLab 明度是否嚴格單調")
    for key, blk in tok["順序型色盤"].items():
        steps = blk.get("色階", [])
        if len(steps) < 3:
            continue
        Ls = [hex_to_oklab(h)[0] for h in steps]
        inc = all(b > a for a, b in zip(Ls, Ls[1:]))
        dec = all(b < a for a, b in zip(Ls, Ls[1:]))
        if inc or dec:
            ok(f"{key}：{'遞增' if inc else '遞減'}單調"
               f"（L {Ls[0]:.3f} → {Ls[-1]:.3f}）")
        else:
            bad = [i for i, (a, b) in enumerate(zip(Ls, Ls[1:]))
                   if (b - a) * (Ls[1] - Ls[0]) <= 0]
            err(f"{key} 的明度不是嚴格單調（第 {bad} 個間隔反向）",
                "順序型色階的用途就是讓讀者排出大小 —— 明度反轉的地方，"
                "讀者會把它讀成兩個方向。重新取色或改用內建色階")

    # ④ 紅綠語意色的色覺風險 —— tokens.json 自己宣告的數字要對得上
    print("\n④ 紅綠語意色在色覺缺陷下的色差（必須加第二編碼的實證）")
    claim = tok.get("紅綠必須加第二編碼", {}).get("實測ΔE_deuteranopia", {})
    for theme_key, sem in tok["語意與中性"].items():
        g, b = sem["good"], sem["bad"]
        d = ciede2000(simulate(g, "deutan"), simulate(b, "deutan"))
        detail(f"{theme_key}：good {g} vs bad {b} 在綠色盲下 ΔE = {d:.1f}")
        if d < min_de:
            warn(f"{theme_key} 的 good/bad 在綠色盲下 ΔE 僅 {d:.1f} < {min_de}",
                 "這不是要改色 —— 紅綠語意有商業慣例。"
                 "但**極值上色一律要配 +/− 或 ▲/▼**，不可只靠顏色。"
                 "對約 8% 男性讀者，只靠顏色的「綠好紅壞」是失效的（19 §2.2）")
        for k, want in claim.items():
            if g in k and b in k and abs(d - float(want)) > 0.6:
                err(f"tokens.json 宣稱 {k} 的 ΔE 是 {want}，實算 {d:.1f}",
                    "把宣稱改成實算值")

    # ⑤ 深色第 8 槽檸黃的已知撞色，tokens.json 有記，這裡確認它還成立
    dark = tok["類別型色盤"].get("深色", {})
    fill = dark.get("僅大面積填色", [])
    lines = {s["名"]: s["hex"] for s in dark.get("線條可用", [])}
    if fill and "琥珀" in lines:
        d = ciede2000(simulate(fill[0]["hex"], "deutan"),
                      simulate(lines["琥珀"], "deutan"))
        print("\n⑤ 深色第 8 槽檸黃與第 6 槽琥珀的已知撞色")
        detail(f"綠色盲下 ΔE = {d:.1f}（tokens.json 記 5.2）")
        if d >= min_de:
            warn(f"實算 ΔE {d:.1f} 已達門檻，與 tokens.json 記的撞色不符",
                 "確認是不是色值被改過。若確實不再撞色，更新 tokens.json 的警告")
        else:
            ok(f"撞色仍然成立（ΔE {d:.1f} < {min_de}）—— "
               f"這兩槽不要同時出現在同一張圖")


# ══════════════════════════════════════════════════════════════
def _selftest() -> int:
    print("=" * 72)
    print("palette_lab.py 自我測試")
    print("=" * 72)
    failed = []

    def check(name: str, cond: bool, got: str = "") -> None:
        print(("  ✓ " if cond else "  ✗ ") + name + (f"（{got}）" if got else ""))
        if not cond:
            failed.append(name)

    # ① WCAG 對比：白對黑恰為 21.0，這是規範的定義值
    c = contrast("#FFFFFF", "#000000")
    check("白對黑對比 = 21.00（WCAG 定義值）", abs(c - 21.0) < 1e-9, f"{c:.10f}")
    check("同色對比 = 1.00", abs(contrast("#0072B2", "#0072B2") - 1.0) < 1e-12)
    check("對比對稱（fg/bg 互換不變）",
          abs(contrast("#0072B2", "#FFF") - contrast("#FFF", "#0072B2")) < 1e-12)

    # ② 對上 19 §2.2 的實測對比值 —— 這是最強的交叉驗證：
    #    reference 的數字是別人量的，我的實作是獨立寫的，對得上才算兩邊都對。
    for h, want in (("#0072B2", 5.19), ("#D55E00", 3.87), ("#009E73", 3.42),
                    ("#CC79A7", 3.06), ("#4D4D4D", 8.45), ("#E69F00", 2.25),
                    ("#56B4E9", 2.31), ("#F0E442", 1.32)):
        got = contrast(h, "#FFFFFF")
        check(f"19 §2.2 淺色 {h} 白底對比 = {want}", abs(got - want) < 0.01, f"{got:.2f}")
    for h, want in (("#4597D4", 5.62), ("#FB8747", 7.34), ("#54C399", 8.17),
                    ("#F0A1CC", 9.05), ("#8A94A3", 5.80), ("#FFC757", 11.49),
                    ("#87DAFF", 11.44), ("#F5E96B", 14.19)):
        got = contrast(h, "#14181F")
        check(f"19 §2.2 深色 {h} 深底對比 = {want}", abs(got - want) < 0.01, f"{got:.2f}")

    # ③ CIEDE2000 對 Sharma, Wu & Dalal (2005) 的標準測試資料
    sharma = [
        ((50.0000, 2.6772, -79.7751), (50.0000, 0.0000, -82.7485), 2.0425),
        ((50.0000, 3.1571, -77.2803), (50.0000, 0.0000, -82.7485), 2.8615),
        ((50.0000, -1.3802, -84.2814), (50.0000, 0.0000, -82.7485), 1.0000),
        ((50.0000, 0.0000, 0.0000), (50.0000, -1.0000, 2.0000), 2.3669),
        ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0009), 7.1792),
        ((50.0000, 2.5000, 0.0000), (73.0000, 25.0000, -18.0000), 27.1492),
        ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ]
    worst = 0.0
    for lab1, lab2, want in sharma:
        got = _ciede2000_lab(*lab1, *lab2)
        worst = max(worst, abs(got - want))
    check(f"CIEDE2000 對上 Sharma 標準測試資料 {len(sharma)} 筆",
          worst < 1e-4, f"最大偏差 {worst:.2e}")

    # ④ 色覺模擬：灰在任何色覺缺陷下都應該幾乎不變（無色相可失）
    grey_shift = max(ciede2000("#808080", simulate("#808080", k))
                     for k in CVD_MATRICES)
    check("灰色在三種色覺缺陷下幾乎不變", grey_shift < 3.0, f"最大 ΔE {grey_shift:.2f}")
    # 紅綠在綠色盲下必須靠攏 —— 模擬若沒作用，這裡會維持很大的 ΔE
    rg_normal = ciede2000("#00A000", "#D00000")
    rg_deutan = ciede2000(simulate("#00A000", "deutan"), simulate("#D00000", "deutan"))
    check("純紅與純綠在綠色盲下明顯靠攏",
          rg_deutan < rg_normal * 0.5,
          f"正常 ΔE {rg_normal:.1f} → 綠色盲 {rg_deutan:.1f}")

    # ⑤ 對上文件記載的 ΔE 實測。sRGB 空間應該逐筆對上（誤差 ≤0.06）——
    #    這同時證明兩件事：我的實作是對的，以及文件的數字是在 sRGB 空間量的。
    for a, b, want, label in (
            ("#F5E96B", "#FFC757", 5.2, "深色檸黃 vs 琥珀"),
            ("#8A94A3", "#F0A1CC", 11.6, "深色第5槽灰 vs 玫瑰紫"),
            ("#1B7F4B", "#C0392B", 10.3, "淺色 good vs bad"),
            ("#4ADE80", "#F87171", 7.5, "深色 good vs bad")):
        got = ciede2000(simulate(a, "deutan", "srgb"), simulate(b, "deutan", "srgb"))
        check(f"{label} 綠色盲 ΔE = {want}（19 §2.2）", abs(got - want) < 0.06, f"{got:.2f}")
    d = ciede2000(simulate("#0072B2", "deutan", "srgb"),
                  simulate("#D55E00", "deutan", "srgb"))
    check("對照組 藍/橘 綠色盲 ΔE = 57.7（19 §2.2）", abs(d - 57.7) < 0.6, f"{d:.2f}")

    # ⑥ 對上 04_design_system.md §1.4 的兩張 prefix 表（逐 n 的最小 ΔE）
    CAT_L = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#4D4D4D"]
    CAT_D = ["#4597D4", "#FB8747", "#54C399", "#F0A1CC",
             "#8A94A3", "#FFC757", "#87DAFF"]

    def min_de(pal, kind, space):
        return min(ciede2000(simulate(x, kind, space), simulate(y, kind, space))
                   for x, y in itertools.combinations(pal, 2))

    for kind, want in (("deutan", 13.2), ("protan", 12.9), ("tritan", 13.0)):
        got = min_de(CAT_L, kind, "srgb")
        check(f"淺色盤 n=5 的 {CVD_NAMES[kind]} 最小 ΔE = {want}（文件表）",
              abs(got - want) < 0.06, f"{got:.2f}")
    for kind, want in (("deutan", 11.6), ("protan", 9.7), ("tritan", 9.5)):
        got = min_de(CAT_D, kind, "srgb")
        check(f"深色盤 n=7 的 {CVD_NAMES[kind]} 最小 ΔE = {want}（文件表）",
              abs(got - want) < 0.06, f"{got:.2f}")

    # ⑦ 換成 linear 空間會偏離文件 —— 固定住這個差異，別哪天有人「順手改成
    #    理論上正確的空間」而讓所有門檻悄悄失效。
    lin_l = min_de(CAT_L, "deutan", "linear")
    check("linear 空間下淺色盤 deutan 明顯偏離文件的 13.2（差異要留痕）",
          abs(lin_l - 13.2) > 1.0, f"linear {lin_l:.2f} vs 文件 13.2")
    lin_grey = ciede2000(simulate("#8A94A3", "deutan", "linear"),
                         simulate("#F0A1CC", "deutan", "linear"))
    srgb_grey = ciede2000(simulate("#8A94A3", "deutan", "srgb"),
                          simulate("#F0A1CC", "deutan", "srgb"))
    check("換空間會翻轉 ΔE≥12 的判定（深色灰 vs 玫瑰紫）",
          (srgb_grey < 12.0) and (lin_grey >= 12.0),
          f"sRGB {srgb_grey:.2f} 不過、linear {lin_grey:.2f} 過")
    check("預設空間是 srgb（門檻的校準空間）", CVD_SPACE_DEFAULT == "srgb")

    # ⑧ 深色盤用 12 驗會假警報，用 9 驗才對（04_design_system.md §1.4 放寬）
    r_dark12 = report("深色 n=7 @12", CAT_D, "#14181F", MIN_CONTRAST_MARK, 12.0)
    r_dark9 = report("深色 n=7 @9", CAT_D, "#14181F", MIN_CONTRAST_MARK,
                     MIN_DELTA_E_DARK)
    check("深色盤在 ΔE≥12 下不合格（所以門檻要分主題）", not r_dark12["通過"])
    check("深色盤在放寬後的 ΔE≥9 下合格", r_dark9["通過"],
          f"最小 ΔE " + "/".join(f"{v['最小ΔE']}" for v in r_dark9["色差"].values()))

    # ⑥ 淺色線條盤 n=5 全綠、n=6 不合格（19 §2.2 的核心結論）
    CAT5 = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#4D4D4D"]
    r5 = report("n=5", CAT5, "#FFFFFF")
    check("淺色線條盤 n=5 通過", r5["通過"],
          f"最低對比 {r5['最低對比']}、最小 ΔE "
          + "/".join(f"{v['最小ΔE']}" for v in r5["色差"].values()))
    r6 = report("n=6", CAT5 + ["#E69F00"], "#FFFFFF")
    check("加第 6 槽琥珀後不合格（19 §2.2：n=6 起最低對比掉到 2.25）",
          not r6["通過"], f"最低對比 {r6['最低對比']}")

    # ⑦ OKLab 明度單調（順序型色階的判準）
    seq = ["#E9F3FF", "#C0D3EB", "#98B3D7", "#7195C3", "#4A76AE", "#225899", "#003984"]
    Ls = [hex_to_oklab(h)[0] for h in seq]
    check("品牌藍淺色色階的 OKLab 明度嚴格遞減",
          all(b < a for a, b in zip(Ls, Ls[1:])), f"L {Ls[0]:.3f} → {Ls[-1]:.3f}")
    check("OKLab 白色 L ≈ 1.0", abs(hex_to_oklab("#FFFFFF")[0] - 1.0) < 1e-3,
          f"{hex_to_oklab('#FFFFFF')[0]:.6f}")
    check("OKLab 黑色 L ≈ 0.0", abs(hex_to_oklab("#000000")[0]) < 1e-6)

    # ⑧ 調整到目標對比：調完必須真的達標，做不到要回 None
    fixed = darken_to_contrast("#E69F00", "#FFFFFF", 3.0)
    check("琥珀調暗到白底對比 ≥ 3.0",
          fixed is not None and contrast(fixed, "#FFFFFF") >= 3.0,
          f"{fixed} → {contrast(fixed, '#FFFFFF'):.2f}" if fixed else "回 None")
    check("做不到時誠實回 None（白色在白底上不可能達到 3.0）",
          darken_to_contrast("#FFFFFF", "#FFFFFF", 21.0) is None
          or contrast(darken_to_contrast("#FFFFFF", "#FFFFFF", 21.0) or "#FFF",
                      "#FFFFFF") >= 21.0)

    # ⑨ 輸入驗證
    for bad in ("not-a-color", "#12345", ""):
        try:
            hex_to_rgb(bad)
            check(f"拒絕不合法色值 {bad!r}", False, "沒有丟例外")
        except ValueError:
            check(f"拒絕不合法色值 {bad!r}", True)
    check("色值往返一致（#RRGGBB → rgb → hex）",
          rgb_to_hex(hex_to_rgb("#0072B2")) == "#0072B2")
    check("三碼縮寫展開正確", rgb_to_hex(hex_to_rgb("#FFF")) == "#FFFFFF")

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="色盤驗證器（18-G14、19 §2.3）。改色值前先跑，CI 也跑。")
    ap.add_argument("--validate", action="store_true",
                    help="驗 assets/tokens.json 的全部色盤")
    ap.add_argument("--contrast", nargs=2, metavar=("前景", "背景"),
                    help="算 WCAG 對比")
    ap.add_argument("--simulate", metavar="色值",
                    help="三種色覺缺陷下的模擬色")
    ap.add_argument("--delta-e", nargs=2, metavar=("色1", "色2"),
                    help="CIEDE2000 色差（含三種色覺缺陷下的值）")
    ap.add_argument("--fix", metavar="色值", help="調到達標對比")
    ap.add_argument("--on", metavar="背景", default="#FFFFFF", help="--fix 的背景色")
    ap.add_argument("--target", type=float, default=MIN_CONTRAST_MARK,
                    help=f"--fix 的目標對比（預設 {MIN_CONTRAST_MARK}）")
    ap.add_argument("--cvd-space", choices=("srgb", "linear"),
                    default=CVD_SPACE_DEFAULT,
                    help="色覺模擬在哪個空間做。預設 srgb（全套門檻的校準空間）；"
                         "linear 是 Machado 原文定義的空間，但門檻要重新校準")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    global _cvd_space
    _cvd_space = args.cvd_space
    if args.cvd_space != CVD_SPACE_DEFAULT:
        print(f"⚠ 色覺模擬空間已切成 {args.cvd_space}。"
              f"門檻 {MIN_DELTA_E}/{MIN_DELTA_E_DARK} 是在 {CVD_SPACE_DEFAULT} "
              f"空間校準的，換空間後不可沿用（差距可達 1.5，足以翻轉結論）。",
              file=sys.stderr)

    if args.self_test:
        return _selftest()

    try:
        if args.contrast:
            fg, bg = args.contrast
            c = contrast(fg, bg)
            print(f"{fg} on {bg}：對比 {c:.2f}")
            print(f"  非文字（WCAG 1.4.11 ≥ {MIN_CONTRAST_MARK}）："
                  f"{'通過' if c >= MIN_CONTRAST_MARK else '不通過'}")
            print(f"  正文（WCAG AA ≥ {MIN_CONTRAST_TEXT}）："
                  f"{'通過' if c >= MIN_CONTRAST_TEXT else '不通過'}")
            return EX_OK if c >= MIN_CONTRAST_MARK else EX_WARN

        if args.simulate:
            h = args.simulate
            print(f"{h} 的色覺缺陷模擬（Machado 2009，severity 1.0）")
            for k, label in CVD_NAMES.items():
                s = simulate(h, k)
                print(f"  {label}（{k}）：{s}  與原色 ΔE {ciede2000(h, s):.2f}")
            return EX_OK

        if args.delta_e:
            a, b = args.delta_e
            print(f"{a} vs {b}")
            print(f"  正常視覺  ΔE {ciede2000(a, b):>6.2f}")
            worst = ciede2000(a, b)
            for k, label in CVD_NAMES.items():
                d = ciede2000(simulate(a, k), simulate(b, k))
                worst = min(worst, d)
                print(f"  {label}（{k}）ΔE {d:>6.2f}")
            print(f"  最弱環節 ΔE {worst:.2f}"
                  f"（門檻 {MIN_DELTA_E}）→ "
                  f"{'可辨' if worst >= MIN_DELTA_E else '有撞色風險'}")
            return EX_OK if worst >= MIN_DELTA_E else EX_WARN

        if args.fix:
            h, bg, t = args.fix, args.on, args.target
            cur = contrast(h, bg)
            print(f"{h} on {bg}：目前對比 {cur:.2f}，目標 {t}")
            if cur >= t:
                print("  已達標，不需調整")
                return EX_OK
            for label, fn in (("調暗", darken_to_contrast), ("調亮", lighten_to_contrast)):
                res = fn(h, bg, t)
                if res:
                    print(f"  {label}：{res}  對比 {contrast(res, bg):.2f}"
                          f"  與原色 ΔE {ciede2000(h, res):.2f}")
                else:
                    print(f"  {label}：做不到（到極端仍達不到 {t}）")
            return EX_OK

        # 預設就是驗 tokens.json
        validate_tokens(load_tokens())
        print("\n" + "=" * 72)
        print(f"error {len(_errors)}、warning {len(_warnings)}")
        if _errors:
            print("結果：⛔ 色盤不合格或宣稱與實算對不上 → 修完再改圖表程式。")
            return EX_ERROR
        if _warnings:
            print("結果：⚠ 可用，但上面的限制要記住（尤其紅綠要加第二編碼）。")
            return EX_WARN
        print("結果：✅ 全部通過。")
        return EX_OK

    except FileNotFoundError as e:
        print(f"\n⛔ {e}", file=sys.stderr)
        return EX_ERROR
    except ValueError as e:
        # 色值格式錯是命令列打錯 → 64，不是資料側問題
        print(f"\n⛔ {e}", file=sys.stderr)
        print(f"   退出碼 {64} —— 檢查你給的色值格式。", file=sys.stderr)
        return 64


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ palette_lab.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
