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
import re
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


def test_prep_cri_lineage_blocks_missing_declaration(root, feat_path, tmp_path):
    """CRI 血緣檢查本身有效：input_vars 有 cri、但血緣不是 behavioral 就擋。

    這批特徵表（PROJ）跑 build_features 時沒給 --dim／--prior-group-cols，
    所以資料側的血緣是 none —— 沒有先驗群就沒有 τ²_g，CRI 整欄 N/A，
    spec 不管怎麼宣告都不該放行。

    刻意自備一份 spec，不用出貨範本 —— 範本的 input_vars 已經不含 cri 了
    （含了就必須同時宣告血緣型別）。這裡要驗的是「檢查本身有效」，
    不是「範本剛好壞掉」。拿壞掉的範本當測試素材，範本修好那天這條就會誤報。
    """
    spec = tmp_path / "cluster_spec_無血緣宣告.json"
    spec.write_text(json.dumps(
        {"input_vars": ["r_days_since_last_sale", "f_txn_cnt", "cri"],
         "scaler": "zscore", "k": 4, "seed": 42}, ensure_ascii=False), encoding="utf-8")
    r = run("prep_cluster_matrix.py", PROJ, "--input", str(feat_path),
            "--spec", str(spec), "--dry-run", root=root)
    assert r.rc == 1, r
    assert "CRI" in r.all and "input_vars" in r.all


def test_shipped_template_works_out_of_the_box(r_prep_template):
    """cp 出貨範本 → 接 build_features 的產出跑 prep_cluster_matrix，不准 exit 1。

    範本的 input_vars 用 build_features 真的會產出的欄名（r_days_since_last_sale /
    f_txn_cnt / m_net_twd / cai），cri 預設不進矩陣、cri_prior_type 預設 null。
    """
    assert r_prep_template.rc in (0, 2), r_prep_template


def test_template_input_vars_exist_in_build_features_output(feat_path, spec_path):
    import pandas as pd
    cols = set(pd.read_parquet(feat_path).columns)
    want = set(json.loads(spec_path.read_text(encoding="utf-8"))["input_vars"])
    assert want <= cols, f"範本要的欄不在特徵表：{sorted(want - cols)}"


def test_cri_lineage_detects_demographic_prior_group(root):
    import pandas as pd
    # M1 閘門（04 §一 步驟⑤）：build_features 會先讀三桶 JSON，沒跑過品質檢查
    # 就直接擋掉並回 1。這一關必須先過，否則本測試量到的是閘門、不是血緣檢查。
    rq = run("check_data_quality.py", PROJ_CRI,
             "--file", f"transactions={SAMPLE}", "--as-of", AS_OF, root=root)
    assert rq.rc in (0, 2), f"品質檢查沒放行，後面的血緣檢查驗不到\n{rq}"

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
    r = run("stats_utils.py", "--self-test", root=root)
    assert r.rc == 0, r


@pytest.fixture(scope="session")
def rank_deficient_df():
    """15 類 × 國內/國外，其中 3 類沒有國外列 → 3 個空 cell、設計矩陣降秩。"""
    import numpy as np
    import pandas as pd
    df = pd.read_parquet(SAMPLE).rename(
        columns={"刷卡產品產業分類": "a", "刷卡地點": "b", "刷卡金額": "y"})
    df["y"] = np.log1p(df["y"])
    return df[["a", "b", "y"]]


def test_design_check_lists_empty_cells(rank_deficient_df):
    """跑 anova 之前就要抓到降秩，而且要點名是哪些組合。"""
    sys.path.insert(0, str(SCRIPTS))
    from stats_utils import design_check
    d = design_check("y ~ C(a)*C(b)", rank_deficient_df)
    assert d["rank_deficient"]
    assert (d["n_cols"], d["rank"], d["deficiency"]) == (30, 27, 3), d
    combos = {c for e in d["empty_cells"] for c in e["cells"]}
    assert combos == {("05_捐贈", "國外"), ("13_交通(含加值)", "國外"),
                      ("X2.中信錢加值", "國外")}, combos


def test_anova3_refuses_rank_deficient_design(rank_deficient_df):
    """降秩設計必須 raise，不是回一張所有 F/p 都相同的垃圾表。"""
    sys.path.insert(0, str(SCRIPTS))
    from stats_utils import RankDeficientDesignError, anova3
    with pytest.raises(RankDeficientDesignError) as ei:
        anova3("y ~ C(a)*C(b)", data=rank_deficient_df, verbose=False)
    msg = str(ei.value)
    # 訊息要講清楚：哪個設計、哪些空 cell、差多少、該怎麼辦
    assert "30 欄但秩只有 27" in msg, msg
    assert "13_交通(含加值) × 國外" in msg, msg
    assert "anova_degrade" in msg and "allow_rank_deficient" in msg, msg


def test_anova3_allow_rank_deficient_carries_visible_warning(rank_deficient_df):
    """顯式放行時，警告必須寫進回傳表的可見欄位，不是只印 stderr。"""
    sys.path.insert(0, str(SCRIPTS))
    import numpy as np
    from stats_utils import anova3
    tbl = anova3("y ~ C(a)*C(b)", data=rank_deficient_df,
                 verbose=False, allow_rank_deficient=True)
    f = tbl["F"].dropna().to_numpy(dtype=float)
    assert np.allclose(f, f[0], rtol=1e-6), "這份資料本來就該是退化的，fixture 變了"
    assert "警告" in tbl.columns, list(tbl.columns)
    assert tbl["警告"].notna().all() and (tbl["警告"] != "").all()
    assert tbl.attrs["可信"] is False
    assert tbl.attrs["ss_check"]["passed"] is False


def test_anova_degrade_gives_usable_fallback(rank_deficient_df):
    """00 §1.6：降級不留空 —— 要退到一個真的可信的結果，並交代四件事。"""
    sys.path.insert(0, str(SCRIPTS))
    import pandas as pd
    from stats_utils import anova_degrade
    r = anova_degrade("y ~ C(a)*C(b)", rank_deficient_df, verbose=False)
    assert r["階梯"] in (2, 3, 4), r["階梯"]
    assert isinstance(r["table"], pd.DataFrame)
    assert r["table"].attrs["可信"] is True
    for k in ("原方法", "失效證據", "實際採用", "結論弱在哪"):
        assert r[k], f"{k} 留空了（00 §1.6 不准）"

    # min_cell=1 時合併救不回來，必須再退一格到主效果模型 + Type II
    r3 = anova_degrade("y ~ C(a)*C(b)", rank_deficient_df, min_cell=1, verbose=False)
    assert r3["階梯"] == 3, r3["ladder_log"]
    assert r3["table"].attrs["typ"] == 2
    assert r3["table"].attrs["ss_check"]["passed"] is True
    assert "不能主張交互作用" in r3["結論弱在哪"]


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


# ── 反向題：gate 在**正常**專案上會不會放行 ────────────────
PROJ_CLEAN = "冒煙_乾淨交付"


@pytest.fixture(scope="session")
def clean_delivery(root):
    """按 verify_outputs 的輸入契約做一份完整交付物（fixtures/make_clean_delivery.py）。

    四份中繼檔的產生腳本（build_report / result_bundle / collect_figures /
    stamp_version）都還沒實作，沒有這份 fixture 就只驗得到「擋不擋得住壞的」，
    驗不到「好的放不放得過」—— 而後者才是 exit 0 存在的理由。
    """
    env = dict(os.environ, **{"MKT_專案根目錄": str(root), "PYTHONIOENCODING": "utf-8"})
    maker = Path(__file__).resolve().parent / "fixtures" / "make_clean_delivery.py"
    cp = subprocess.run([sys.executable, str(maker), PROJ_CLEAN],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=env, timeout=300)
    assert cp.returncode == 0, cp.stdout + cp.stderr
    return root / PROJ_CLEAN


def test_verify_exits_0_on_a_clean_project(root, clean_delivery):
    r = run("verify_outputs.py", PROJ_CLEAN, root=root)
    assert r.rc == 0, r
    assert "全綠" in r.all, r


def test_clean_project_stays_green_with_upstream_qa_tables(root, clean_delivery, r_prep):
    """把上游腳本真的寫出來的 QA 中繼產物搬進乾淨專案，仍然要 exit 0。

    ①（QA 中繼產物誤擋）的回歸鎖：手做的 fixture 不會有那些空白格與 0–1 占比欄，
    真檔案才會 —— 所以這裡搬的是 check_data_quality／prep_cluster_matrix 的實際產出。
    """
    import shutil
    src = root / PROJ / "統計表"
    moved = 0
    for p in src.rglob("*.csv"):
        rel = p.relative_to(src)
        if set(rel.parts[:-1]) & {"資料體檢", "轉換前後對照", "分群輪廓"}:
            dst = clean_delivery / "統計表" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            moved += 1
    assert moved >= 2, f"只搬到 {moved} 張 QA 中繼產物，這條測試是空的"
    r = run("verify_outputs.py", PROJ_CLEAN, root=root)
    assert r.rc == 0, r


def test_verify_accepts_upstream_scripts_own_tables(root, r_quality, r_prep):
    """19 §5.5：統計表/{資料體檢,轉換前後對照,分群輪廓}/ 是 QA 中繼產物不是交付表。

    這三類本來就有空白格（非比率型規則沒有母數）與 0–1 的比率欄，
    照 §5.1~§5.4 判一定紅。gate 不掃它們 —— 掃了等於擋下自己上游的正常產出。
    """
    r = run("verify_outputs.py", PROJ, "--only", "C01,C02,T03", root=root)
    assert r.rc == 0, r


def test_qa_tables_really_exist_so_the_previous_test_is_not_vacuous(root, r_quality, r_prep):
    """上一條若是因為根本沒表而過，等於什麼都沒驗。"""
    tables = root / PROJ / "統計表"
    qa = [p for p in tables.rglob("*.csv")
          if set(p.relative_to(tables).parts[:-1])
          & {"資料體檢", "轉換前後對照", "分群輪廓"}]
    assert qa, f"{tables} 底下沒有任何 QA 中繼產物，上一條測試是空的"


def test_qa_tables_are_still_scannable_on_demand(root, r_quality, r_prep):
    """--include-qa-tables 要能把它們掃回來 —— 排除是預設值，不是把規則刪掉。"""
    r = run("verify_outputs.py", PROJ, "--include-qa-tables",
            "--only", "C01,T03", root=root)
    assert r.rc == 1, r
    assert "資料體檢" in r.all, r


def test_verify_r01_is_clean_on_the_skill_itself(root):
    r = run("verify_outputs.py", "--self-check", "--only", "R01", root=root)
    assert r.rc == 0, r


def test_self_check_rules_do_not_judge_a_project(root, r_quality):
    """19 §5.6：R01/R02 檢查的是 skill 自身，不該出現在專案模式的判定裡。"""
    r = run("verify_outputs.py", PROJ, root=root)
    assert "[R01]" not in r.all and "[R02]" not in r.all, r
    assert "自檢規則不參與專案判定" in r.all, r


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
def test_usage_error_is_not_exit_2(script, root):
    """用法錯誤必須是 64，不能跟『2 = 只有 warning，可往下走』撞在一起。

    00 §八：驅動腳本靠退出碼決定要不要往下，2 和 64 混用會讓
    `if [ $? -le 2 ]` 這種 wrapper 在腳本一列資料都沒讀的情況下 fail open。
    """
    r = run(script, "--這個旗標不存在", root=root)
    assert r.rc == 64, r


def test_user_mistakes_do_not_become_exit_70(root):
    """使用者打錯不能被判成 70。

    70 的語意是「腳本自身異常，修腳本」。把「檔案路徑打錯」「日期格式打錯」
    也吐 70，會叫使用者去讀腳本原始碼找一個不存在的 bug。
    分界：值／路徑不合法 → 64（命令列打錯）；路徑合法但東西不在 → 1（資料側）。
    """
    r = run("check_data_quality.py", PROJ, "--file", f"transactions={SAMPLE}",
            "--as-of", "not-a-date", "--no-write", root=root)
    assert r.rc == 64, f"--as-of 格式錯應該是 64，不是腳本壞了\n{r}"

    missing = SAMPLE.with_name("這個檔案不存在.parquet")
    r2 = run("check_data_quality.py", PROJ, "--file", f"transactions={missing}",
             "--as-of", AS_OF, "--no-write", root=root)
    assert r2.rc == 1, f"檔案不存在應該是 1（資料側），不是 70\n{r2}"


def test_selftest_flag_is_uniform(root):
    """自我測試旗標全庫一律 --self-test，且都不需要先給專案代號（00 §八）。

    判準是「旗標被認得且自我測試真的跑完」= 退出碼落在三桶（0/1/2），
    不是「一定全綠」—— write_transform_log 的自我測試用真實樣本跑，
    課程資料的 Spearman 並列與偏度本來就會出 warning，那是 2 不是壞掉。
    """
    bad = {}
    for script in ("stats_utils.py", "pick_transform.py", "write_transform_log.py",
                   "retransform.py"):
        r = run(script, "--self-test", root=root)
        if r.rc not in (0, 1, 2):
            bad[script] = r.rc
    assert not bad, bad


def test_old_selftest_spellings_are_gone(root):
    """舊寫法 --selftest / --demo 必須退 64（用法錯誤），不准還能跑。"""
    for script, flag in (("stats_utils.py", "--selftest"),
                         ("retransform.py", "--demo")):
        r = run(script, flag, root=root)
        assert r.rc == 64, (script, flag, r)


def test_positional_project_arg_is_named_consistently():
    """位置參數的 dest 全庫一律 `project`（00 §八）。metavar 可以是中文。"""
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


def test_verify_r02_has_no_false_positives(root):
    """R02 改用 ast，不再打到行尾註解／字串常數／in-memory 探測。

    逐行 regex 版本回報的三處全是誤報：profile_dataset.py 的
    `from db import connect  # …不准自己 duckdb.connect()`（行尾註解）、
    setup_check.py 的 BLOCKING_SCRIPTS 說明字串、以及 setup_check.py 的
    `duckdb.connect()` 無參數 in-memory 探測。
    """
    r = run("verify_outputs.py", "--self-check", "--only", "R02", root=root)
    assert "duckdb.connect()" not in r.all, r
    assert r.rc == 0, r


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
    # 契約宣告了幣別 → Q16 要降到 info 桶並標「已解除」，不是消失。
    # 舊寫法斷言 "Q16" not in r.all，但 info 桶本來就會印出代號 —— 那樣
    # 只有「整條規則被拿掉」才會過，等於逼修法往錯的方向走。
    assert r.rc == 0, f"契約已宣告幣別卻沒全綠\n{r}"
    assert "error 0、warning 0" in r.all, f"Q16 沒降到 info 桶\n{r}"
    assert "已解除" in r.all, f"Q16 沒標記為已解除\n{r}"


# ══════════════════════════════════════════════════════════════
#  ⑨ kmeans_preflight —— 五道關，前三道事前、後兩道事後
# ══════════════════════════════════════════════════════════════
def test_kmeans_preflight_selftest(root):
    r = run("kmeans_preflight.py", "--self-test", root=root)
    assert r.rc == 0, r


def test_kmeans_preflight_pre_fit_does_not_claim_five_gates(root, r_prep):
    """只跑得到三道關時，不准輸出「五道全過」。

    07 §四：「前三道是事前可驗的，後兩道只能事後驗——這個區別要誠實寫在
    報告裡，不要假裝五道都在跑之前就過了。」這是本腳本存在的理由，
    真的退化成「跑三道印五道」的話，K-Means 對非球形簇給出的漂亮錯誤答案
    就會一路進報告。
    """
    r = run("kmeans_preflight.py", PROJ, "--no-write", root=root)
    assert r.rc in (0, 2), r
    assert "跑了 3／5 道關" in r.all, f"沒有誠實標明跑了幾道\n{r}"
    assert "報告不可寫「五道前提全部通過」" in r.all, r
    assert "五道關全過" not in r.all, f"只跑三道卻宣稱五道全過\n{r}"


def test_kmeans_preflight_gate1_reads_pre_standardization_sd(root, r_prep):
    """關卡 1 必須還原標準化前的尺度比，不能對著標準化後的矩陣算。

    cluster_matrix.parquet 每欄 sd 都是 1，直接算比值恆等於 1.00 —— 那是
    一道穩過的假關卡。真值要從 scaler.json 的 vars[].scale 還原，而且必須
    與 prep_cluster_matrix 自己報的數字對得上（兩支腳本各走各的路徑）。
    """
    r = run("kmeans_preflight.py", PROJ, "--no-write", root=root)
    assert "標準化前尺度比" in r.all, f"關卡 1 沒去讀 scaler.json\n{r}"
    m = re.search(r"標準化前尺度比 ([\d.]+)", r.all)
    assert m, r
    got = float(m.group(1))
    m2 = re.search(r"標準化前尺度比 max\(sd\)/min\(sd\) = ([\d.]+)", r_prep.all)
    assert m2, f"prep_cluster_matrix 沒報尺度比，對不了帳\n{r_prep}"
    assert abs(got - float(m2.group(1))) < 0.05, (
        f"兩支腳本算出的標準化前尺度比不一致："
        f"kmeans_preflight={got}、prep_cluster_matrix={m2.group(1)}")


def test_kmeans_preflight_no_scaler_refuses_to_pass_gate1(root, r_prep, tmp_path):
    """已標準化但拿不到 scaler.json → 必須報 warning 並明講「沒有真的驗到」。"""
    mtx = root / PROJ / "模型輸出" / "cluster_matrix.parquet"
    if not mtx.exists():
        pytest.skip("矩陣尚未產出")
    r = run("kmeans_preflight.py", PROJ, "--matrix", str(mtx),
            "--scaler", str(tmp_path / "不存在.json"), "--no-write", root=root)
    assert r.rc == 2, r
    assert "沒有真的驗到" in r.all, f"假關卡被當成通過\n{r}"


def test_kmeans_preflight_post_fit_writes_json(root, r_prep):
    """給了 --k 就要跑滿五道，並把結果寫成 JSON。

    JSON 那一步是真的炸過：群標籤來自 pd.unique()，是 numpy int32，
    json.dumps 丟 TypeError —— 而且是在五道關全跑完、CSV 都寫好之後才炸，
    退出碼 70 蓋掉前面全綠的結論。
    """
    r = run("kmeans_preflight.py", PROJ, "--k", "4", root=root)
    assert r.rc in (0, 2), r
    assert "跑了 5／5 道關" in r.all, r
    jp = root / PROJ / "模型輸出" / "kmeans_preflight.json"
    assert jp.exists(), f"沒寫出 JSON\n{r}"
    d = json.loads(jp.read_text(encoding="utf-8"))
    assert d["gates_run"] == 5 and d["後兩道已驗"] is True, d
    assert all(isinstance(x["群"], int) for x in d["gate4_detail"]), d["gate4_detail"]
    assert "本節的 K-Means 有兩道前提只能事後檢查" in r.all, "沒印誠實說明模板"


# ══════════════════════════════════════════════════════════════
#  ⑩ S1 循環推論 gate（07 §8.2）—— verify_outputs 的 T08 / T09
# ══════════════════════════════════════════════════════════════
def _objects(proj_root: Path) -> tuple[Path, dict]:
    op = proj_root / "模型輸出" / "analysis_objects.json"
    return op, json.loads(op.read_text(encoding="utf-8"))


def test_s1_gate_blocks_anova_on_cluster_input(root, clean_delivery):
    """對分群輸入變數跑 ANOVA 必須擋下來。

    07 §8.2 稱這是「整個 M6 最嚴重、也最沒有被任何既有規則攔住的問題」：
    F 正是 K-Means 被最佳化的量，純隨機噪音一樣得到 p<0.001。素材原文的代價是
    據此把 29 人定為 VIP，投入 14.5 萬元預算。
    """
    op, obj = _objects(clean_delivery)
    orig = op.read_text(encoding="utf-8")
    try:
        obj["anova"].append({"id": "anova_M_by_群", "posthoc_id": "posthoc_M_by_群"})
        obj["posthoc"].append({"id": "posthoc_M_by_群", "method": "Tukey HSD"})
        op.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        r = run("verify_outputs.py", PROJ_CLEAN, root=root)
        assert r.rc == 1, f"S1 違規沒被擋下來\n{r}"
        assert "T08" in r.all and "循環推論" in r.all, r
    finally:
        op.write_text(orig, encoding="utf-8")


def test_s1_gate_blocks_eta2_on_cluster_input(root, clean_delivery):
    """η² 一併禁：它與 F 是嚴格單調的一對一變換，報 η² 等同報 F。"""
    op, obj = _objects(clean_delivery)
    orig = op.read_text(encoding="utf-8")
    try:
        obj["報了η²的變數"] = ["CAI"]
        op.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        r = run("verify_outputs.py", PROJ_CLEAN, root=root)
        assert r.rc == 1, f"報 η² 沒被擋下來\n{r}"
        assert "嚴格單調" in r.all, r
    finally:
        op.write_text(orig, encoding="utf-8")


def test_s1_gate_blocks_chi2_on_upstream_var(root, clean_delivery):
    """血緣：拿分群輸入的上游人口變數跑卡方 = 用被污染的分群檢定污染源。"""
    op, obj = _objects(clean_delivery)
    orig = op.read_text(encoding="utf-8")
    try:
        obj["分群輸入上游變數"] = ["性別"]
        obj["卡方檢定變數"] = ["性別", "地區"]
        op.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        r = run("verify_outputs.py", PROJ_CLEAN, root=root)
        assert r.rc == 1, f"血緣違規沒被擋下來\n{r}"
        assert "T09" in r.all and "污染源" in r.all, r
    finally:
        op.write_text(orig, encoding="utf-8")


def test_s1_gate_catches_undeclared_violation_in_delivered_table(root, clean_delivery):
    """沒登錄在 analysis_objects.json 的違規也要擋。

    只驗自我宣告的欄位，等於只擋「有誠實登錄的人」—— 沒登錄的照樣交出去。
    這一條直接掃真的要交出去的統計表。
    """
    t = clean_delivery / "統計表" / "行銷分析" / "S1違規_群間比較.csv"
    t.parent.mkdir(parents=True, exist_ok=True)
    t.write_text("變數,群1,群2,F值,p值,結論\n"
                 "M,1200,3400,182.4,<0.001,四群在購買金額上存在極顯著差異\n",
                 encoding="utf-8-sig")
    try:
        r = run("verify_outputs.py", PROJ_CLEAN, root=root)
        assert r.rc == 1, f"未登錄的 S1 違規沒被擋下來\n{r}"
        assert "推論欄位" in r.all, r
    finally:
        t.unlink()


def test_s1_gate_says_so_when_it_cannot_verify(root, clean_delivery):
    """沒有分群輸入變數時，必須明說「這次沒有驗到」，不准靜默放行。"""
    op, obj = _objects(clean_delivery)
    orig = op.read_text(encoding="utf-8")
    try:
        obj.pop("分群輸入變數", None)
        op.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        r = run("verify_outputs.py", PROJ_CLEAN, root=root)
        assert "S1 gate 這次沒有驗到" in r.all, f"假關卡：沒資料卻靜默通過\n{r}"
    finally:
        op.write_text(orig, encoding="utf-8")
