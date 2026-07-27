#!/usr/bin/env python3
"""
全 skill 統一的退出碼 —— 規格見 references/00_通則與紀律.md §八。

    0   全部通過
    1   有 error 擋住（資料／設定的問題，不是腳本的問題）
    2   只有 warning，可以往下走
    64  用法錯誤（旗標打錯、缺必填參數、值不在 choices 裡）
    70  腳本自身異常（未預期的例外，修腳本）

64 / 70 沿用 BSD sysexits.h 的 EX_USAGE / EX_SOFTWARE。

為什麼要 64：argparse 預設把用法錯誤也吐成 exit 2，跟「只有 warning，可往下走」
撞在一起，驅動腳本分不出「跑完了但有警告」與「根本沒跑起來」。本模組的
GateArgumentParser 覆寫 error()，把用法錯誤改成 64。

用法：
    from exitcodes import EX_OK, EX_ERROR, EX_WARN, EX_USAGE, EX_SOFTWARE
    from exitcodes import GateArgumentParser

    ap = GateArgumentParser(description="…")     # 其餘用法與 ArgumentParser 相同
"""

from __future__ import annotations

import argparse
import sys

__all__ = [
    "EX_OK", "EX_ERROR", "EX_WARN", "EX_USAGE", "EX_SOFTWARE",
    "EXIT_CODE_TABLE", "GateArgumentParser",
]

EX_OK = 0
EX_ERROR = 1
EX_WARN = 2
EX_USAGE = 64
EX_SOFTWARE = 70

#: 給 docstring / --help / 報告尾巴共用的一行說明
EXIT_CODE_TABLE = (
    "0 全過｜1 有 error 擋住｜2 只有 warning 可往下｜"
    "64 用法錯誤｜70 腳本自身異常"
)


class GateArgumentParser(argparse.ArgumentParser):
    """argparse.ArgumentParser，但用法錯誤退 64 而不是 2。

    argparse 的 error() 預設走 self.exit(2, …)，會跟本 skill 的
    「2 = 只有 warning」語意衝突。只覆寫 error()，不動 exit()，
    因為 --help / --version 走的是 exit(0)，那個是對的。
    """

    def error(self, message: str):  # noqa: D102 - 覆寫 argparse 的介面
        self.print_usage(sys.stderr)
        self.exit(EX_USAGE, f"{self.prog}: 用法錯誤：{message}\n")
