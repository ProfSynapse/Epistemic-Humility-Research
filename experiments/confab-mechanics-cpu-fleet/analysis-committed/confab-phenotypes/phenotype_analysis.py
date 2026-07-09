"""Confabulation phenotype taxonomy + internal-state coupling (arm A).

RQ: our model confabulates on questions it internally knows are unanswerable.
Do those confabulations have PHENOTYPES (hedged vs assertive, fabricated-specific
vs generic, premise-accepting vs premise-correcting), and does the PRE-GENERATION
internal state predict the phenotype? If high-doubt confabs come out hedged and
low-doubt ones come out confidently specific, the doubt reading leaks into the
texture of the hallucination even when it fails to trigger refusal.

Tier-1 lab-notebook. CPU only. Seed 20260704. One activation layer loaded at a time.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")

import json
import re
from pathlib import Path
import numpy as np
from collections import Counter, defaultdict
from scipy.stats import spearmanr, mannwhitneyu
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import joblib

SEED = 20260704
rng = np.random.default_rng(SEED)

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[4]
LEGACY_ANALYSIS = REPO / "experiment" / "phase1" / "probe" / "analysis"
AH = str(LEGACY_ANALYSIS / "ah_main")
CACHE = str(LEGACY_ANALYSIS / "mi_category_geometry_20260704" / "cache")
PROBES = str(LEGACY_ANALYSIS / "ah_stage0" / "probes")
OUT = BASE

PROBE_LAYERS = [20, 24, 28]
CV_LAYERS = [8, 16, 20, 24, 28, 34]
N_PERM = 1000

findings = {"seed": SEED}
log_lines = []
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


# ---------------------------------------------------------------- data loading
def load_rows(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def extract_answer(at):
    """Recover the 'answer' field from the JSON-ish answer_text, tolerating
    truncated generations (missing closing quote / brace)."""
    try:
        o = json.loads(at)
        if isinstance(o, dict) and "answer" in o:
            return _unescape(o["answer"])
    except Exception:
        pass
    m = re.search(r'"answer"\s*:\s*"(.*?)"\s*,\s*"response_confidence"', at, re.S)
    if m:
        return _unescape(m.group(1))
    m = re.search(r'"answer"\s*:\s*"(.*)$', at, re.S)
    if m:
        txt = m.group(1).rstrip()
        if txt.endswith('"'):
            txt = txt[:-1]
        return _unescape(txt)
    return at


def _unescape(s):
    # answer strings from the model may carry literal \n \" etc.
    return (s.replace('\\n', '\n').replace('\\"', '"')
             .replace('\\t', '\t').replace('\\\\', '\\'))


# ---------------------------------------------------------------- phenotype features
HEDGE_TERMS = [
    r"\bmight\b", r"\bmay\b", r"\bperhaps\b", r"\bpossibly\b", r"\bpotentially\b",
    r"\blikely\b", r"\bprobably\b", r"\bgenerally\b", r"\btypically\b", r"\boften\b",
    r"\bsome argue\b", r"\bsome believe\b", r"\bit depends\b", r"\buncertain\b",
    r"\bnot definitively\b", r"\bnot certain\b", r"\bdebated\b", r"\bdebatable\b",
    r"\bcould\b", r"\bcan vary\b", r"\bvaries\b", r"\bin some cases\b",
    r"\bit is unclear\b", r"\bunclear\b", r"\bnot clear\b", r"\bhard to say\b",
    r"\bno consensus\b", r"\bno definitive\b", r"\bwould depend\b", r"\bsuggests?\b",
    r"\bappears? to\b", r"\bseems? to\b", r"\btend to\b", r"\btends to\b",
    r"\bmore research\b", r"\bnot fully understood\b", r"\bcomplex\b",
    r"\bsubjective\b", r"\bopinions? (vary|differ)\b", r"\bdifferent perspectives\b",
]
HEDGE_RE = [re.compile(t, re.I) for t in HEDGE_TERMS]
HEDGE_OPENER_RE = re.compile(
    r"^\s*\W*(it depends|this depends|it is (difficult|hard|unclear|uncertain)|"
    r"there is no (single|definitive|clear|one)|opinions|perspectives (differ|vary)|"
    r"generally|typically|perhaps|it (may|might)|this is (a )?(complex|debated|subjective)|"
    r"the answer (depends|varies)|while|although)", re.I)

# premise handling (for false_assumption flavor)
CORRECT_PREMISE_RE = re.compile(
    r"(\bactually\b|\bthere is no\b|\bthere isn'?t\b|\bdoes not exist\b|\bdoesn'?t exist\b|"
    r"\bthis assumes\b|\bthe (premise|assumption|question) (is|assumes|presupposes)\b|"
    r"\bno (such|evidence)\b|\bnot (true|accurate|correct)\b|\bmisconception\b|"
    r"\bincorrect(ly)?\b|\bfalse\b|\bcontrary to\b|\bin fact\b)", re.I)
NO_OPENER_RE = re.compile(r"^\s*\W*no[,.\s]", re.I)

WORD_RE = re.compile(r"[A-Za-z']+")
NUM_RE = re.compile(r"\b\d[\d,]*\.?\d*\b")
YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
PCT_RE = re.compile(r"\b\d+(?:\.\d+)?\s?%")
# capitalized mid-sentence word = proper-noun proxy (skip sentence-initial)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
PROPER_RE = re.compile(r"\b[A-Z][a-zA-Z]+\b")


def phenotype_features(answer, flavor):
    a = answer.strip()
    words = WORD_RE.findall(a)
    nw = max(len(words), 1)
    hedge_hits = sum(len(r.findall(a)) for r in HEDGE_RE)
    # specificity: proper nouns mid-sentence
    proper = 0
    for sent in SENT_SPLIT_RE.split(a):
        toks = sent.split()
        for i, t in enumerate(toks):
            if i == 0:
                continue
            if PROPER_RE.fullmatch(t.strip(".,;:!?()\"'")):
                proper += 1
    nums = len(NUM_RE.findall(a))
    years = len(YEAR_RE.findall(a))
    pcts = len(PCT_RE.findall(a))
    feats = {
        "n_words": nw,
        "n_chars": len(a),
        "hedge_count": hedge_hits,
        "hedge_rate": hedge_hits / nw,
        "opens_with_hedge": int(bool(HEDGE_OPENER_RE.match(a))),
        "n_proper": proper,
        "proper_rate": proper / nw,
        "n_numerals": nums,
        "n_years": years,
        "n_pct": pcts,
        "specificity_raw": proper + nums,
        "specificity_rate": (proper + nums) / nw,
    }
    if flavor == "false_assumption":
        corrects = bool(CORRECT_PREMISE_RE.search(a)) or bool(NO_OPENER_RE.match(a))
        feats["corrects_premise"] = int(corrects)
    return feats


# ---------------------------------------------------------------- build corpora
log("=== loading gen arms ===")
A0 = load_rows(os.path.join(AH, "gen_A0", "rows.jsonl"))
ACERT = load_rows(os.path.join(AH, "gen_Acertain", "rows.jsonl"))
ADOUBT = load_rows(os.path.join(AH, "gen_Adoubt", "rows.jsonl"))


def clean(rows):
    return [r for r in rows if not r.get("degenerate") and not r.get("ungradeable")]


def confabs(rows):
    return [r for r in clean(rows) if r.get("confab_on_unanswerable")]


def attach_features(rows):
    out = []
    for r in rows:
        ans = extract_answer(r["answer_text"])
        flavor = r.get("category_canon") or "(none)"
        f = phenotype_features(ans, flavor)
        rec = dict(r)
        rec["_answer"] = ans
        rec["_flavor"] = flavor
        rec["_feats"] = f
        out.append(rec)
    return out


a0_confab = attach_features(confabs(A0))
acert_confab = attach_features(confabs(ACERT))
adoubt_confab = attach_features(confabs(ADOUBT))
# reference populations
a0_clean = clean(A0)
a0_correct_known = attach_features(
    [r for r in a0_clean if r.get("gold_class") == "answerable" and r.get("correct") is True])
a0_refuse_unk = [r for r in a0_clean if r.get("gold_class") == "unanswerable" and r.get("refused")]

findings["populations"] = {
    "A0_total": len(A0), "A0_clean": len(a0_clean),
    "A0_confab": len(a0_confab),
    "Acertain_total": len(ACERT), "Acertain_confab": len(acert_confab),
    "Adoubt_total": len(ADOUBT), "Adoubt_confab": len(adoubt_confab),
    "A0_correct_on_known": len(a0_correct_known),
    "A0_refusals_on_unknown": len(a0_refuse_unk),
}
log("populations:", json.dumps(findings["populations"]))


# ---------------------------------------------------------------- descriptives
def summarize(recs, keys):
    out = {}
    for k in keys:
        vals = np.array([r["_feats"].get(k, np.nan) for r in recs], float)
        vals = vals[~np.isnan(vals)]
        if len(vals):
            out[k] = {"mean": float(vals.mean()), "median": float(np.median(vals)),
                      "std": float(vals.std()), "n": int(len(vals))}
    return out


FEAT_KEYS = ["n_words", "hedge_count", "hedge_rate", "opens_with_hedge",
             "n_proper", "n_numerals", "n_years", "n_pct",
             "specificity_raw", "specificity_rate", "proper_rate"]

findings["descriptives"] = {
    "A0_confab": summarize(a0_confab, FEAT_KEYS),
    "Acertain_confab": summarize(acert_confab, FEAT_KEYS),
    "A0_correct_known": summarize(a0_correct_known, FEAT_KEYS),
}

# by flavor within A0 confabs
by_flavor = defaultdict(list)
for r in a0_confab:
    by_flavor[r["_flavor"]].append(r)
findings["A0_confab_by_flavor"] = {
    fl: {"n": len(rs), **summarize(rs, ["hedge_rate", "opens_with_hedge",
                                        "specificity_rate", "n_words"])}
    for fl, rs in sorted(by_flavor.items())
}

# premise handling on false_assumption
fa_a0 = [r for r in a0_confab if r["_flavor"] == "false_assumption"]
findings["false_assumption_premise"] = {
    "A0_confab_n": len(fa_a0),
    "A0_corrects_premise": int(sum(r["_feats"].get("corrects_premise", 0) for r in fa_a0)),
}


# ---------------------------------------------------------------- prime vs baseline
def compare_pop(a, b, keys):
    out = {}
    for k in keys:
        va = np.array([r["_feats"].get(k, np.nan) for r in a], float)
        vb = np.array([r["_feats"].get(k, np.nan) for r in b], float)
        va = va[~np.isnan(va)]; vb = vb[~np.isnan(vb)]
        if len(va) < 5 or len(vb) < 5:
            continue
        try:
            u, p = mannwhitneyu(va, vb, alternative="two-sided")
        except Exception:
            p = np.nan
        out[k] = {"A_mean": float(va.mean()), "B_mean": float(vb.mean()),
                  "diff": float(va.mean() - vb.mean()), "mwu_p": float(p)}
    return out


findings["prime_vs_baseline"] = {
    "Acertain_minus_A0_confab": compare_pop(acert_confab, a0_confab, FEAT_KEYS),
    "note": "A>0 means Acertain (certainty prime) higher than A0 baseline confab",
}
# contrast: confab hedging vs correct-on-known hedging
findings["confab_vs_correct_known"] = compare_pop(a0_confab, a0_correct_known,
                                                  ["hedge_rate", "specificity_rate", "n_words"])


# ---------------------------------------------------------------- internal-state readouts
log("\n=== attaching internal-state readouts (A0 confabs) ===")
# manifest join
manifest = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
key2idx = {m["row_key"]: i for i, m in enumerate(manifest)}
man_label = np.array([1 if m["label"] == "unknown" else 0 for m in manifest])
man_cat = np.array([m["category_canon"] for m in manifest])

a0_keys = [r["row_key"] for r in a0_confab]
join_hit = [k in key2idx for k in a0_keys]
findings["join_coverage"] = {"A0_confab_join": int(sum(join_hit)), "of": len(a0_keys)}
log("join coverage:", findings["join_coverage"])

# ready-made per-row readouts already on the rows
def col(recs, k):
    return np.array([r.get(k) if r.get(k) is not None else np.nan for r in recs], float)

caution_z = col(a0_confab, "caution_dist_z")
score_l24_row = col(a0_confab, "score_L24")

# doubt-trunk projection + frozen probe scores computed from cache, per layer
# doubt-trunk direction = mean(categorized unknown) - mean(known) at each layer
CATS = ["ambiguous", "controversial", "counterfactual",
        "false_assumption", "future_unknown", "unsolved_problem"]
known_idx = np.where(man_label == 0)[0]
cat_all_idx = np.where((man_label == 1) & np.isin(man_cat, CATS))[0]

idx_in_cache = np.array([key2idx[k] for k in a0_keys])  # all join (309/309 expected)

readouts = {"caution_dist_z": caution_z, "score_L24_row": score_l24_row}
for L in PROBE_LAYERS:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    mu_k = X[known_idx].mean(0)
    doubt_dir = X[cat_all_idx].mean(0) - mu_k
    doubt_dir /= (np.linalg.norm(doubt_dir) + 1e-12)
    proj = X[idx_in_cache] @ doubt_dir
    readouts[f"doubt_proj_L{L}"] = proj
    # frozen knowledge probe: class 1 == known -> use P(unknown) = 1 - P(known)
    pb = joblib.load(os.path.join(PROBES, f"probe_L{L}.joblib"))
    Xs = pb["scaler"].transform(X[idx_in_cache])
    p_known = pb["clf"].predict_proba(Xs)[:, 1]
    readouts[f"unknownness_probe_L{L}"] = 1.0 - p_known
    del X

# phenotype targets (continuous) for correlation
targets = {
    "hedge_rate": np.array([r["_feats"]["hedge_rate"] for r in a0_confab]),
    "specificity_rate": np.array([r["_feats"]["specificity_rate"] for r in a0_confab]),
    "n_words": np.array([r["_feats"]["n_words"] for r in a0_confab], float),
    "opens_with_hedge": np.array([r["_feats"]["opens_with_hedge"] for r in a0_confab], float),
}
flavor_arr = np.array([r["_flavor"] for r in a0_confab])


def perm_spearman(x, y, nperm=N_PERM):
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < 20:
        return np.nan, np.nan, len(x)
    rho, _ = spearmanr(x, y)
    cnt = 0
    for _ in range(nperm):
        if abs(spearmanr(x, rng.permutation(y))[0]) >= abs(rho):
            cnt += 1
    return float(rho), (cnt + 1) / (nperm + 1), int(len(x))


def partial_within_flavor_spearman(x, y, flav, nperm=N_PERM):
    """Spearman after removing flavor means (flavor-partialed), perm within flavor."""
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y, flav = x[ok], y[ok], flav[ok]
    if len(x) < 20:
        return np.nan, np.nan, len(x)
    def resid(v):
        out = v.astype(float).copy()
        for f in np.unique(flav):
            m = flav == f
            out[m] = out[m] - out[m].mean()
        return out
    xr, yr = resid(x), resid(y)
    rho, _ = spearmanr(xr, yr)
    cnt = 0
    for _ in range(nperm):
        yp = np.empty_like(y, float)
        for f in np.unique(flav):
            m = flav == f
            yp[m] = rng.permutation(y[m])
        if abs(spearmanr(xr, resid(yp))[0]) >= abs(rho):
            cnt += 1
    return float(rho), (cnt + 1) / (nperm + 1), int(len(x))


log("\n=== internal-state coupling (Spearman, perm p) ===")
coupling = {}
for tname, tvec in targets.items():
    coupling[tname] = {}
    for rname, rvec in readouts.items():
        rho, p, n = perm_spearman(rvec, tvec)
        rho_w, p_w, _ = partial_within_flavor_spearman(rvec, tvec, flavor_arr)
        coupling[tname][rname] = {
            "spearman_rho": rho, "perm_p": p, "n": n,
            "within_flavor_rho": rho_w, "within_flavor_perm_p": p_w}
        log(f"  {tname:16s} ~ {rname:22s} rho={rho:+.3f} p={p:.4f}  "
            f"within-flavor rho={rho_w:+.3f} p={p_w:.4f}")
findings["coupling_spearman"] = coupling


# ---------------------------------------------------------------- probe: predict hedged vs assertive
log("\n=== probe: pre-gen activations -> hedged(top tercile) vs assertive(bottom tercile) ===")
hr = targets["hedge_rate"]
q1, q2 = np.quantile(hr, [1/3, 2/3])
tercile_label = np.full(len(hr), -1)
tercile_label[hr <= q1] = 0  # assertive
tercile_label[hr >= q2] = 1  # hedged
sel = tercile_label >= 0
y = tercile_label[sel]
sel_cache_idx = idx_in_cache[sel]
sel_flavor = flavor_arr[sel]
log(f"tercile split: assertive={int((y==0).sum())} hedged={int((y==1).sum())} "
    f"(thresholds hedge_rate<= {q1:.4f} / >= {q2:.4f})")


def cv_auroc(Xr, y, seed):
    """PCA-128 (label-agnostic, fit on train fold) + LR, stratified 5-fold.
    LR is lbfgs on the 128-dim PCA features (converges fast at low dim; the
    'never full-dim lbfgs' rule targets the 2560-dim raw space, not PCA-128)."""
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    scores = []
    for tr, te in skf.split(Xr, y):
        p = PCA(n_components=min(128, Xr.shape[1], len(tr) - 1),
                svd_solver="randomized", random_state=seed)
        Xtr = p.fit_transform(Xr[tr]); Xte = p.transform(Xr[te])
        clf = LogisticRegression(solver="lbfgs", tol=1e-3, max_iter=1000, C=1.0)
        clf.fit(Xtr, y[tr])
        pr = clf.predict_proba(Xte)[:, 1]
        scores.append(roc_auc_score(y[te], pr))
    return float(np.mean(scores))


probe_res = {}
for L in CV_LAYERS:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    Xr = X[sel_cache_idx]
    del X
    aurocs = [cv_auroc(Xr, y, s) for s in (0, 1, 2)]
    obs = float(np.mean(aurocs))
    # permutation null (shuffle labels), few reps for speed
    null = []
    for _ in range(40):
        yp = rng.permutation(y)
        null.append(cv_auroc(Xr, yp, 0))
    null = np.array(null)
    pval = (np.sum(null >= obs) + 1) / (len(null) + 1)
    probe_res[f"L{L}"] = {"auroc_mean": obs, "auroc_seeds": aurocs,
                          "null_mean": float(null.mean()),
                          "null_p95": float(np.quantile(null, 0.95)),
                          "perm_p": float(pval), "n": int(len(y))}
    log(f"  L{L}: AUROC={obs:.3f}  null_mean={null.mean():.3f} "
        f"null_p95={np.quantile(null,0.95):.3f} perm_p={pval:.3f}")
findings["hedge_probe"] = probe_res


# ---------------------------------------------------------------- confound: TF-IDF on QUESTION text
log("\n=== confound guard: TF-IDF(question) -> hedged/assertive ===")
questions = np.array([r["question"] for r in a0_confab])[sel]
def tfidf_cv(qs, y, seed):
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    scores = []
    for tr, te in skf.split(qs, y):
        vec = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), stop_words="english")
        Xtr = vec.fit_transform(qs[tr]); Xte = vec.transform(qs[te])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000)
        clf.fit(Xtr, y[tr])
        pr = clf.predict_proba(Xte)[:, 1]
        scores.append(roc_auc_score(y[te], pr))
    return float(np.mean(scores))
tfidf_auroc = float(np.mean([tfidf_cv(questions, y, s) for s in (0, 1, 2)]))
log(f"  TF-IDF(question) AUROC={tfidf_auroc:.3f}")
findings["tfidf_question_baseline"] = {"auroc": tfidf_auroc, "n": int(len(y))}

# also: does flavor alone predict hedge tercile? (flavor is a coarse confound)
from sklearn.preprocessing import OneHotEncoder
def flavor_cv(fl, y, seed):
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    scores = []
    fl2 = fl.reshape(-1, 1)
    for tr, te in skf.split(fl2, y):
        enc = OneHotEncoder(handle_unknown="ignore")
        Xtr = enc.fit_transform(fl2[tr]); Xte = enc.transform(fl2[te])
        clf = LogisticRegression(max_iter=2000)
        clf.fit(Xtr, y[tr])
        pr = clf.predict_proba(Xte)[:, 1]
        scores.append(roc_auc_score(y[te], pr))
    return float(np.mean(scores))
flavor_auroc = float(np.mean([flavor_cv(sel_flavor, y, s) for s in (0, 1, 2)]))
log(f"  flavor-only AUROC={flavor_auroc:.3f}")
findings["flavor_only_baseline"] = {"auroc": flavor_auroc, "n": int(len(y))}


# ---------------------------------------------------------------- audited examples
log("\n=== 10 audited example classifications ===")
audit = []
# pick a spread: 3 high-hedge, 3 low-hedge/high-specificity, 2 false_assumption, 2 random
order = np.argsort([r["_feats"]["hedge_rate"] for r in a0_confab])
picks = list(order[-3:]) + list(order[:3])
fa_idx = [i for i, r in enumerate(a0_confab) if r["_flavor"] == "false_assumption"]
picks += fa_idx[:2]
picks += list(rng.choice(len(a0_confab), size=2, replace=False))
seen = set()
for i in picks:
    if i in seen:
        continue
    seen.add(i)
    r = a0_confab[i]
    f = r["_feats"]
    phen = "hedged" if f["hedge_rate"] >= q2 else ("assertive" if f["hedge_rate"] <= q1 else "mid")
    audit.append({
        "row_key": r["row_key"],
        "flavor": r["_flavor"],
        "question": r["question"][:160],
        "answer_snippet": r["_answer"][:220],
        "hedge_rate": round(f["hedge_rate"], 4),
        "hedge_count": f["hedge_count"],
        "opens_with_hedge": f["opens_with_hedge"],
        "specificity_rate": round(f["specificity_rate"], 4),
        "n_proper": f["n_proper"], "n_numerals": f["n_numerals"],
        "corrects_premise": f.get("corrects_premise"),
        "assigned_phenotype": phen,
        "caution_dist_z": r.get("caution_dist_z"),
    })
findings["audited_examples"] = audit


# ---------------------------------------------------------------- write outputs
with open(os.path.join(OUT, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2, default=float)
with open(os.path.join(OUT, "run.log"), "w") as f:
    f.write("\n".join(log_lines) + "\n")
log("\nDONE. findings.json + run.log written to", OUT)
