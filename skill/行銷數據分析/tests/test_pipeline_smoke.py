#!/usr/bin/env python3
"""
串接冒煙測試 —— 測的是**介面**，不是單支腳本的邏輯。

問的問題只有一個：A 的產出，B 真的吃得下去嗎？

    profile_dataset  →  check_data_quality  →  build_features
                                                     ↓
                                              prep_cluster_matrix
                                                     ↓
                                              verify_outputs
    stats_utils.anova3  vs  裸 anova_lm(typ=3)（防呆是否真的有作用）

跑法：
    python -m pytest tests/test_pipeline_smoke.py -v

設計：
  · 全部走 subprocess，跟真人在命令列跑的路徑完全一樣（退出碼才有意義）。
  · 專案根目錄用 MKT_專案根目錄 環境變數導到 tmp，不污染 projects/。
  · session 級 fixture 只跑一次管線，後面各條測試讀它的產物。
  · **已知的介面缺陷一律用 xfail(strict=True) 標記**，不改別人的腳本。
    xfail 清單 = bug 清單；哪天缺陷被修好，strict=True 會讓它變 XPASS 而失敗，
    強迫回來把標記拿掉。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
REPO_ROOT = SKILL_ROOT.parent.parent
SAMPLE = (REPO_ROOT / "00_source_archive" / "local" / "資料集剖析" / "samples"
          / "ntu_creditcard__transactions.parquet")
DIM = SAMPLE.with_name("ntu_creditcard__customers.parquet")
DIRTY = Path(__file__).resolve().parent / "fixtures" / "dirty_mini.parquet"

AS_OF = "2012-12-01"
PROJ = "冒煙_乾淨"
PROJ_DIRTY = "冒煙_髒"
PROJ_CRI = "冒煙_CRI"
PROJ_BAD = "冒煙_壞交付"

pytestmark = pytest.mark.skipif(not SAMPLE.exists(),
                                reason=f"找不到樣本 parquet：{SAMPLE}")


# ══════════════════════════════════════════════════════════════
#  執行器
# ══════════════════════════════════════════════════════════════
class Run:
    def __init__(self, cp: subprocess.CompletedProcess):
        self.rc = cp.returncode
        self.out = cp.stdout or ""
        self.err = cp.stderr or ""

    @property
    def all(self) -> str:
        return self.out + self.err

    def __repr__(self) -> str:  # pytest -v 失敗時看得到
        return f"<rc={self.rc}>\n{self.all[-3000:]}"


def run(script: str, *args: str, root: Path) -> Run:
    env = dict(os.environ)
    env["MKT_專案根目錄"] = str(root)
    env["PYTHONIOENCODING"] = "utf-8"
    cp = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(SCRIPTS), timeout=900,
    )
    return Run(cp)


@pytest.fixture(scope="session")
def root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("projroot")


# ══════════════════════════════════════════════════════════════
#  管線各段（session 級，只跑一次）
# ══════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def r_profile(root):
    return run("profile_dataset.py", PROJ, str(SAMPLE), "--report-to", "stdout", root=root)


@pytest.fixture(scope="session")
def r_quality(root, r_profile):
    """不帶 --profile：驗證它會自己接上 profile_dataset 的落點。"""
    return run("check_data_quality.py", PROJ,
               "--file", f"transactions={SAMPLE}", "--as-of", AS_OF, root=root)


@pytest.fixture(scope="session")
def r_quality_dirty(root):
    return run("check_data_quality.py", PROJ_DIRTY,
               "--file", f"交易={DIRTY}", "--as-of", AS_OF, "--no-write", root=root)


@pytest.fixture(scope="session")
def r_features(root, r_quality):
    return run("build_features.py", PROJ, "--as-of", AS_OF,
               "--source", str(SAMPLE), "--benchmark", root=root)


@pytest.fixture(scope="session")
def feat_path(root, r_features) -> Path:
    return root / PROJ / "顧客特徵表" / f"feat_customer_asof{AS_OF}.parquet"


@pytest.fixture(scope="session")
def spec_path(root, r_features) -> Path:
    """把出貨範本原封不動放進專案 —— 這正是 SKILL 文件教的第一步。"""
    dst = root / PROJ / "模型輸出" / "cluster_spec.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text((SKILL_ROOT / "templates" / "cluster_spec.json").read_text(encoding="utf-8"),
                   encoding="utf-8")
    return dst


@pytest.fixture(scope="session")
def r_prep_template(root, feat_path, spec_path):
    """出貨範本 + build_features 的真實產出，直接串。"""
    return run("prep_cluster_matrix.py", PROJ, "--input", str(feat_path),
               "--dry-run", root=root)


@pytest.fixture(scope="session")
def r_prep(root, feat_path, spec_path, r_prep_template):
    """補上範本缺的 cri_prior_type、改成 build_features 真的有的欄名，再串一次。"""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["cri_prior_type"] = "behavioral"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return run("prep_cluster_matrix.py", PROJ, "--input", str(feat_path),
               "--vars", "r_days_since_last_sale,f_txn_cnt,m_net_twd,cai",
               "--no-spec-update", root=root)


# ══════════════════════════════════════════════════════════════
#  ① profile_dataset → check_data_quality
# ══════════════════════════════════════════════════════════════
def test_profile_runs_and_exit_is_2_for_warnings(r_profile):
    assert r_profile.rc == 2, r_profile
    assert "資料剖析" in r_profile.all


def test_profile_writes_column_inventory(root, r_profile):
    csv = root / PROJ / "開案與問題定義" / "欄位總表.csv"
    assert csv.exists(), f"profile_dataset 沒寫出 {csv}"


def test_column_inventory_has_the_schema_quality_reads(root, r_profile):
    """check_data_quality.load_profile 只吃這幾欄；欄名對不上就是斷線。"""
    import csv as _csv
    p = root / PROJ / "開案與問題定義" / "欄位總表.csv"
    with p.open(encoding="utf-8-sig", newline="") as fh:
        header = next(_csv.reader(fh))
    for need in ("source", "table", "column", "suspected_sentinel", "practical_use"):
        assert need in header, f"欄位總表少了 {need}；check_data_quality 讀不到"


def test_quality_autolinks_profile_output(r_quality):
    """不給 --profile 也要自己找到 開案與問題定義/欄位總表.csv。"""
    assert "欄位總表" in r_quality.all
    assert "自動接上 profile_dataset 的產出" in r_quality.all, r_quality


def test_quality_clean_data_exit_2(r_quality):
    assert r_quality.rc == 2, r_quality
    assert "error 0" in r_quality.all


def test_quality_writes_bucket_table(root, r_quality):
    assert (root / PROJ / "統計表" / "資料體檢" / "M1_品質檢查三桶.csv").exists()
    assert (root / PROJ / "統計表" / "資料體檢" / "M1_品質檢查三桶.json").exists()


# ══════════════════════════════════════════════════════════════
#  ② check_data_quality 的 error 真的擋得住
# ══════════════════════════════════════════════════════════════
def test_quality_dirty_exit_1(r_quality_dirty):
    assert r_quality_dirty.rc == 1, r_quality_dirty
    assert "擋住，不准進 M2" in r_quality_dirty.all


def test_quality_dirty_catches_the_expected_rules(r_quality_dirty):
    for q in ("Q1", "Q2", "Q17", "Q18", "Q20"):
        assert f"⛔ {q} " in r_quality_dirty.all, f"{q} 沒被抓到\n{r_quality_dirty}"


def test_quality_list_exits_0(root):
    r = run("check_data_quality.py", "--list", root=root)
    assert r.rc == 0, r


# ══════════════════════════════════════════════════════════════
#  ③ build_features —— 17 §八 的基準值
# ══════════════════════════════════════════════════════════════
def test_features_run_ok(r_features):
    assert r_features.rc == 2, r_features       # 只有 warning
    assert "error" not in r_features.all.split("結果：")[-1]


@pytest.mark.parametrize("cust,col,want,tol", [
    (89, "r_days_since_last_sale", 19, 0),
    (89, "f_txn_cnt", 85, 0),
    (89, "f_active_days", 69, 0),
    (89, "m_net_twd", 150681, 0),
    (89, "interval_cnt", 68, 0),
    (89, "mle", 10.279412, 5e-7),
    (89, "wmle", 11.570759, 5e-7),
    (89, "cai", -12.562460, 5e-7),
    (106, "r_days_since_last_sale", 8, 0),
    (106, "f_txn_cnt", 75, 0),
    (106, "m_net_twd", 90192, 0),
    (131, "r_days_since_last_sale", 401, 0),
    (131, "f_txn_cnt", 16, 0),
    (131, "m_net_twd", 69558, 0),
    (605, "mle", 2.296530, 5e-7),
])
def test_benchmark_17_section8(feat_path, cust, col, want, tol):
    """17 §八 逐位比對過的 ground truth。讀落檔，不讀 stdout。"""
    import pandas as pd
    df = pd.read_parquet(feat_path)
    got = float(df.loc[df["cust_id"] == cust, col].iloc[0])
    assert abs(got - want) <= tol, f"客戶 {cust} 的 {col}：得到 {got!r}，期望 {want!r}"


def test_benchmark_cai_range(feat_path):
    import pandas as pd
    cai = pd.read_parquet(feat_path)["cai"].dropna()
    assert abs(float(cai.min()) - (-43.665943)) <= 5e-7
    assert abs(float(cai.max()) - 54.590571) <= 5e-7


def test_benchmark_row_flow_7764_5294_5194(r_features):
    """17 §一：7,764 → 5,294 → 5,194。腳本只在 stdout 交代，落檔沒有這三個數。"""
    assert "原始交易 7,764 → 去重後 5,294 → 間隔數 5,194" in r_features.all, r_features


def test_benchmark_flag_reports_all_green(r_features):
    assert "基準值" in r_features.all
    assert "不符" not in r_features.all, r_features


def test_features_also_land_in_duckdb_as_feat_customer(root, r_features):
    """prep_cluster_matrix --table 的預設表名是 feat_customer。"""
    import duckdb
    con = duckdb.connect(str(root / PROJ / "warehouse.duckdb"), read_only=True)
    try:
        names = {r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='main'").fetchall()}
    finally:
        con.close()
    assert "feat_customer" in names, names


# ══════════════════════════════════════════════════════════════
#  ④ build_features → prep_cluster_matrix
# ══════════════════════════════════════════════════════════════
def test_prep_reads_build_features_parquet(r_prep):
    assert r_prep.rc == 2, r_prep                # warning-only
    assert "矩陣已產出" in r_prep.all


def test_prep_writes_matrix_and_scaler(root, r_prep):
    for rel in ("模型輸出/cluster_matrix.parquet", "模型輸出/scaler.json",
                "統計表/分群輪廓/wgss_contribution.csv",
                "統計表/轉換前後對照/cluster_matrix_transform.csv",
                "隔離區/cluster_matrix_dropped.csv"):
        assert (root / PROJ / rel).exists(), f"缺 {rel}"


def test_prep_can_read_from_duckdb_table(root, r_prep):
    r = run("prep_cluster_matrix.py", PROJ, "--table",
            "--vars", "r_days_since_last_sale,f_txn_cnt,m_net_twd,cai",
            "--dry-run", "--verbose", root=root)
    assert r.rc == 2, r
    assert "資料庫表 feat_customer" in r.all


def test_prep_whitelist_blocks_demographics(root, r_prep):
    r = run("prep_cluster_matrix.py", PROJ, "--input",
            str(root / PROJ / "顧客特徵表" / f"feat_customer_asof{AS_OF}.parquet"),
            "--vars", "r_days_since_last_sale,m_net_twd,性別",
            "--dry-run", root=root)
    assert r.rc == 1, r
    assert "18-E2" in r.all


def test_prep_cri_lineage_blocks_missing_declaration(r_prep_template):
    """CRI 血緣檢查本身有效：spec 沒宣告 cri_prior_type 就擋。"""
    assert r_prep_template.rc == 1, r_prep_template
    assert "cri_prior_type" in r_prep_template.all


@pytest.mark.xfail(strict=True, reason=(
    "介面缺陷：出貨範本 templates/cluster_spec.json 的 input_vars 帶 cri，"
    "卻沒有 cri_prior_type；照 SKILL 教的 cp 範本再跑 prep_cluster_matrix 直接 exit 1。"))
def test_shipped_template_works_out_of_the_box(r_prep_template):
    assert r_prep_template.rc in (0, 2), r_prep_template


@pytest.mark.xfail(strict=True, reason=(
    "介面缺陷：範本 input_vars 寫 ln_f / ln_m，build_features 產出的是 "
    "f_txn_cnt / m_net_twd，兩邊欄名對不上。"))
def test_template_input_vars_exist_in_build_features_output(feat_path, spec_path):
    import pandas as pd
    cols = set(pd.read_parquet(feat_path).columns)
    want = set(json.loads(spec_path.read_text(encoding="utf-8"))["input_vars"])
    assert want <= cols, f"範本要的欄不在特徵表：{sorted(want - cols)}"


@pytest.mark.xfail(strict=True, reason=(
    "介面缺陷：CRI 血緣只讀 spec 裡人工填的 cri_prior_type，不看 build_features "
    "留在同一張表 prior_group 欄的實際值。用 --prior-group-cols 性別 算出來的 CRI，"
    "只要 spec 打 behavioral 就一路綠燈。"))
def test_cri_lineage_detects_demographic_prior_group(root):
    import pandas as pd
    r = run("build_features.py", PROJ_CRI, "--as-of", AS_OF, "--source", str(SAMPLE),
            "--dim", str(DIM), "--prior-group-cols", "性別", root=root)
    assert r.rc == 2, r
    fp = root / PROJ_CRI / "顧客特徵表" / f"feat_customer_asof{AS_OF}.parquet"
    groups = set(pd.read_parquet(fp)["prior_group"].dropna().unique())
    assert groups, "沒有 prior_group 可查"

    spec = root / PROJ_CRI / "模型輸出" / "cluster_spec.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(json.dumps(
        {"input_vars": ["r_days_since_last_sale", "cri"], "cri_prior_type": "behavioral",
         "scaler": "zscore", "k": 4, "seed": 42}, ensure_ascii=False), encoding="utf-8")
    r2 = run("prep_cluster_matrix.py", PROJ_CRI, "--input", str(fp), "--dry-run",
             "--verbose", root=root)
    # 先驗群值長得像「1:男 / 2:女」，血緣檢查應該要擋下來。
    assert r2.rc == 1, f"prior_group={groups} 卻放行了\n{r2}"


# ══════════════════════════════════════════════════════════════
#  ⑤ stats_utils.anova3 vs 裸 anova_lm(typ=3)
# ══════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def factorial_df():
    """真資料、2×2、無空格。刻意不平衡（1751/7/1270/5）才驗得出 18-T3。"""
    import numpy as np
    import pandas as pd
    df = pd.read_parquet(SAMPLE)
    d = df[df["刷卡產品產業分類"].isin(["06_公用事業", "12_量販超市"])].copy()
    d = d.rename(columns={"刷卡產品產業分類": "a", "刷卡地點": "b", "刷卡金額": "y"})
    d["y"] = np.log1p(d["y"])
    return d[["a", "b", "y"]]


def test_anova3_differs_from_naive_anova_lm(factorial_df):
    """18-T3：直接 anova_lm(typ=3) 會靜默算錯主效果 SS。防呆有沒有作用，看這裡。"""
    sys.path.insert(0, str(SCRIPTS))
    import statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    from stats_utils import anova3

    naive = anova_lm(smf.ols("y ~ C(a)*C(b)", data=factorial_df).fit(), typ=3)
    good = anova3("y ~ C(a)*C(b)", data=factorial_df, verbose=False)

    ss_naive = float(naive.loc["C(a)", "sum_sq"])
    ss_good = float(good.loc["C(a, Sum)", "sum_sq"])
    assert ss_naive != pytest.approx(ss_good, rel=1e-6), (
        f"兩者相同（{ss_naive}）—— 防呆沒有作用，或這份資料驗不出 18-T3")
    assert ss_naive > ss_good * 10, f"naive={ss_naive}, anova3={ss_good}"
    # 交互作用項不受編碼影響，兩邊必須一致 —— 差異只該出現在主效果
    assert float(naive.loc["C(a):C(b)", "sum_sq"]) == pytest.approx(
        float(good.loc["C(a, Sum):C(b, Sum)", "sum_sq"]), rel=1e-9)


def test_anova3_rewrites_formula_and_records_it(factorial_df):
    sys.path.insert(0, str(SCRIPTS))
    from stats_utils import anova3
    tbl = anova3("y ~ C(a)*C(b)", data=factorial_df, verbose=False)
    assert tbl.attrs["formula_used"] == "y ~ C(a, Sum)*C(b, Sum)"
    assert tbl.attrs["rewrites"], "沒有記錄改寫過程"
    assert tbl.attrs["ss_check"]["passed"] is True


def test_stats_utils_selftest_exits_0(root):
    r = run("stats_utils.py", "--selftest", root=root)
    assert r.rc == 0, r


@pytest.mark.xfail(strict=True, reason=(
    "穩健性缺陷：設計矩陣有空格（15 類 × 國內/國外）時，sum-to-zero 編碼的 "
    "type-III 約束矩陣降秩，anova3 回傳的表所有項 F/p 完全相同（垃圾）。"
    "_ss_double_check 已判定 passed=False，但只在 verbose 時印 stderr，不 raise —— "
    "呼叫端不主動看 .attrs['ss_check'] 就拿到假結果。"))
def test_anova3_refuses_rank_deficient_design():
    sys.path.insert(0, str(SCRIPTS))
    import numpy as np
    import pandas as pd
    from stats_utils import anova3
    df = pd.read_parquet(SAMPLE).rename(
        columns={"刷卡產品產業分類": "a", "刷卡地點": "b", "刷卡金額": "y"})
    df["y"] = np.log1p(df["y"])
    tbl = anova3("y ~ C(a)*C(b)", data=df[["a", "b", "y"]], verbose=False)
    f = tbl["F"].dropna().to_numpy(dtype=float)
    degenerate = bool(np.allclose(f, f[0], rtol=1e-6))
    assert tbl.attrs["ss_check"]["passed"] and not degenerate, (
        f"SS 雙路徑驗算 passed={tbl.attrs['ss_check']['passed']}、"
        f"所有效果的 F 都等於 {f[0]:.6f}（主效果與交互作用一模一樣），"
        f"函式卻照樣把這張表回傳出去")


# ══════════════════════════════════════════════════════════════
#  ⑥ verify_outputs 擋不擋得住故意做壞的輸出
# ══════════════════════════════════════════════════════════════
@pytest.fixture(scope="session")
def broken_project(root) -> Path:
    """手工做一張壞掉的統計表：占比不到 100、r=1.000、最後一欄空白、#DIV/0!。"""
    p = root / PROJ_BAD / "統計表" / "行銷分析"
    p.mkdir(parents=True, exist_ok=True)
    (p / "群輪廓.csv").write_text(
        "群別,人數,占比,平均客單價,相關係數 r,結論\n"
        "A群,30,25.0,1200,0.42,高頻中額\n"
        "B群,25,20.5,3400,1.000,低頻高額\n"
        "C群,45,31.0,#DIV/0!,0.11,\n",
        encoding="utf-8-sig")
    return root / PROJ_BAD


@pytest.fixture(scope="session")
def r_verify_broken(root, broken_project):
    return run("verify_outputs.py", PROJ_BAD,
               "--only", "T03,T05,T06,C01,C02", root=root)


def test_verify_blocks_broken_output(r_verify_broken):
    assert r_verify_broken.rc == 1, r_verify_broken
    assert "不得輸出" in r_verify_broken.all


@pytest.mark.parametrize("check_id,why", [
    ("T03", "占比欄加總 76.5，不是 100"),
    ("T05", "r=1.000 沒標樣本不足"),
    ("C01", "最後一欄有空白格"),
    ("C02", "#DIV/0! 洩漏到交付檔"),
])
def test_verify_catches_each_defect(r_verify_broken, check_id, why):
    assert f"[{check_id}]" in r_verify_broken.all, f"{check_id} 沒抓到（{why}）\n{r_verify_broken}"


def test_verify_list_exits_0(root):
    r = run("verify_outputs.py", "--list", root=root)
    assert r.rc == 0, r


@pytest.mark.xfail(strict=True, reason=(
    "介面衝突：verify_outputs 的 C01/C02/T03 把 統計表/**/*.csv 全當交付檔掃，"
    "而 統計表/資料體檢/M1_品質檢查三桶.csv（check_data_quality 寫的）與 "
    "統計表/轉換前後對照/cluster_matrix_transform.csv（prep_cluster_matrix 寫的）"
    "本來就有空白格、'none' 字樣、以及 0–1 而非 0–100 的占比欄。"
    "照著 SKILL 跑完 M1→M6，M7 的驗收一定紅。"))
def test_verify_accepts_upstream_scripts_own_tables(root, r_quality, r_prep):
    r = run("verify_outputs.py", PROJ, "--only", "C01,C02,T03", root=root)
    assert r.rc == 0, r


@pytest.mark.xfail(strict=True, reason=(
    "介面缺陷：R01（無編號式英文目錄硬編路徑）掃的是 skill 自己的 references/，"
    "不是專案交付物。references/14_決策轉譯.md 有 12 處 交付物/ 沒改乾淨，"
    "於是**任何**專案跑 verify_outputs 都會被別人的檔案判 error。"))
def test_verify_r01_is_clean_on_the_skill_itself(root):
    r = run("verify_outputs.py", "--static-only", "--only", "R01", root=root)
    assert r.rc == 0, r


# ══════════════════════════════════════════════════════════════
#  ⑦ 跨檔約定：import、退出碼、路徑
# ══════════════════════════════════════════════════════════════
ALL_SCRIPTS = ["paths", "db", "anonymize_pii", "setup_check", "profile_dataset",
               "check_data_quality", "check_schema_contract", "build_features",
               "pick_transform", "prep_cluster_matrix", "retransform",
               "stats_utils", "verify_outputs", "write_transform_log"]


@pytest.mark.parametrize("mod", ALL_SCRIPTS)
def test_no_import_cycle(mod, root):
    """每支單獨 import 一次；有循環 import 這裡就會炸。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cp = subprocess.run([sys.executable, "-c", f"import {mod}"],
                        cwd=str(SCRIPTS), capture_output=True, text=True,
                        encoding="utf-8", errors="replace", env=env, timeout=300)
    assert cp.returncode == 0, cp.stderr[-2000:]


@pytest.mark.parametrize("script", ["profile_dataset.py", "check_data_quality.py",
                                    "check_schema_contract.py", "build_features.py",
                                    "prep_cluster_matrix.py", "verify_outputs.py",
                                    "setup_check.py"])
def test_help_exits_0(script, root):
    r = run(script, "--help", root=root)
    assert r.rc == 0, r


@pytest.mark.parametrize("script", ["profile_dataset.py", "check_data_quality.py",
                                    "build_features.py", "prep_cluster_matrix.py",
                                    "verify_outputs.py", "setup_check.py"])
@pytest.mark.xfail(strict=True, reason=(
    "退出碼語意衝突：全部腳本都宣告『2 = 只有 warning，可往下走』，"
    "但 argparse 的用法錯誤（打錯旗標、漏必填參數）也是 exit 2。"
    "驅動腳本分不出『有警告但跑完了』和『參數打錯，根本沒跑』。"))
def test_usage_error_is_not_exit_2(script, root):
    r = run(script, "--這個旗標不存在", root=root)
    assert r.rc != 2, r


@pytest.mark.xfail(strict=True, reason=(
    "介面不一致：自我測試旗標三種寫法並存 —— stats_utils.py 是 --selftest、"
    "pick_transform.py / write_transform_log.py 是 --self-test、"
    "retransform.py 是 --demo；而且後三者還強制要先給位置參數專案代號，"
    "stats_utils 不用。"))
def test_selftest_flag_is_uniform(root):
    bad = {}
    for script in ("stats_utils.py", "pick_transform.py", "write_transform_log.py",
                   "retransform.py"):
        r = run(script, "--selftest", root=root)
        if r.rc != 0:
            bad[script] = r.rc
    assert not bad, bad


@pytest.mark.xfail(strict=True, reason=(
    "介面不一致：verify_outputs.py / pick_transform.py / retransform.py 的位置參數叫 "
    "`專案代號`（中文），其餘叫 `project`。要寫統一的 orchestrator 就得開特例。"))
def test_positional_project_arg_is_named_consistently():
    import ast
    names = {}
    for f in ("profile_dataset.py", "check_data_quality.py", "build_features.py",
              "prep_cluster_matrix.py", "verify_outputs.py", "pick_transform.py",
              "retransform.py", "write_transform_log.py"):
        tree = ast.parse((SCRIPTS / f).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_argument"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and not str(node.args[0].value).startswith("-")):
                names.setdefault(f, str(node.args[0].value))
                break
    assert len(set(names.values())) == 1, names


def test_no_script_actually_bypasses_db_connect():
    """AST 認定的真實呼叫（不是註解、不是字串）。除了 db.py 自己與 setup_check
    用來探測 duckdb 是否可用的 in-memory 連線之外，不該有人自己開連線。"""
    import ast
    offenders = []
    for f in sorted(SCRIPTS.glob("*.py")):
        if f.name in {"db.py", "setup_check.py"}:
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "connect"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "duckdb"):
                offenders.append(f"{f.name}:{node.lineno}")
    assert not offenders, offenders


@pytest.mark.xfail(strict=True, reason=(
    "誤報：verify_outputs 的 R02 用逐行 regex 找 duckdb.connect()，會打到註解後半段"
    "與字串常數。實際回報的三處全是誤報 —— profile_dataset.py:1226 是 "
    "`from db import connect  # …不准自己 duckdb.connect()` 的行尾註解，"
    "setup_check.py:197 是 dict 裡的說明字串，setup_check.py:320 是探測 duckdb "
    "是否可用的 in-memory 連線。沒有任何腳本真的繞過 db.connect()。"))
def test_verify_r02_has_no_false_positives(root):
    r = run("verify_outputs.py", "--static-only", "--only", "R02", root=root)
    assert "duckdb.connect()" not in r.all, r


@pytest.mark.xfail(strict=True, reason=(
    "介面缺陷：Q16 只看有沒有 currency 欄，從不讀契約的 columns[].unit —— "
    "但它自己的修法就寫『在契約的 columns[].unit 明寫幣別』。照做也清不掉警告。"))
def test_q16_respects_contract_declared_unit(root):
    contract = REPO_ROOT / "skill" / "行銷數據分析" / "templates" / "contracts"
    src = next((p for p in contract.glob("*.yml")), None)
    if src is None:
        pytest.skip("找不到契約範本")
    dst = root / PROJ / "原始資料" / "contracts" / "ntu_creditcard.yml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    r = run("check_data_quality.py", PROJ, "--file", f"transactions={SAMPLE}",
            "--contract", str(dst), "--as-of", AS_OF, "--only", "Q16",
            "--no-write", root=root)
    assert "Q16" not in r.all, r
