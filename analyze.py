"""Regenerate every number, the figure and the table used in the report.

Usage:  .venv/bin/python -I analyze.py runs/main_1108 out_dir [runs/excuse_1108] [runs/robust_1109] [runs/subtle_1109]
Reads only results_*.jsonl and log_*.jsonl written by harness.py.
Writes out_dir/numbers.json, out_dir/fig1.png, out_dir/table_full.md.
"""
import glob, json, math, os, sys
from collections import defaultdict

RUN, OUT = sys.argv[1], sys.argv[2]
EXC = sys.argv[3] if len(sys.argv) > 3 else None
ROB = sys.argv[4] if len(sys.argv) > 4 else None
SUB = sys.argv[5] if len(sys.argv) > 5 else None
os.makedirs(OUT, exist_ok=True)

SHORT = {"Qwen2.5-0.5B-Instruct": "Qwen2.5-0.5B",
         "Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B",
         "NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit": "Nemotron-30B-A3B"}
MODELS = ["Qwen2.5-0.5B", "Qwen2.5-1.5B", "Nemotron-30B-A3B"]
CONDS = ["trust", "tool", "tool_busy", "shown", "gate"]
FAULTY = ("missing", "wrong_qty")


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def short(m):
    return SHORT[m.split("/")[-1]]


res = [json.loads(l) for p in sorted(glob.glob(RUN + "/results_*.jsonl")) for l in open(p)]
logs = [json.loads(l) for p in sorted(glob.glob(RUN + "/log_*.jsonl")) for l in open(p)]
for r in res:
    r["m"] = short(r["model"])

# LLM calls per episode (every logged record that has a completion is one model call)
calls = defaultdict(int)
for d in logs:
    if "completion" in d:
        calls[(short(d["model"]), d["cond"], d["fault"], d["seed"])] += 1

N = {}


def put(key, k, n):
    p, lo, hi = wilson(k, n)
    # stored unrounded (4 decimals); the report rounds once when printing
    N[key] = {"k": k, "n": n, "pct": round(100 * p, 4) if n else None,
              "lo": round(100 * lo, 4) if n else None, "hi": round(100 * hi, 4) if n else None}


def sel(m=None, c=None, faults=None, extra=None):
    out = [r for r in res if (m is None or r["m"] == m) and (c is None or r["cond"] == c)
           and (faults is None or r["fault"] in faults)]
    return [r for r in out if extra(r)] if extra else out


N["total_episodes"] = len(res)
N["seeds"] = len({r["seed"] for r in res})
N["unparsed_total"] = sum(r["unparsed"] for r in res)
N["llm_calls_total"] = sum(calls.values())
N["per_model_episodes"] = {m: len(sel(m)) for m in MODELS}
N["sec_per_ep"] = {m: round(sum(r["secs"] for r in sel(m)) / max(1, len(sel(m))), 2) for m in MODELS}

for m in MODELS:
    for c in CONDS:
        bad = sel(m, c, FAULTY)
        good = sel(m, c, ("none",))
        put(f"{m}|{c}|bad_charge", sum(r["bad_charge"] for r in bad), len(bad))
        put(f"{m}|{c}|bad_ship", sum(r["bad_ship"] for r in bad), len(bad))
        put(f"{m}|{c}|false_halt", sum(r["false_halt"] for r in good), len(good))
        allc = sel(m, c)
        put(f"{m}|{c}|w2_checked", sum(r["w2_checked"] for r in allc), len(allc))
        put(f"{m}|{c}|w2_checked_faulty", sum(r["w2_checked"] for r in bad), len(bad))
        put(f"{m}|{c}|w2_checked_honest", sum(r["w2_checked"] for r in good), len(good))
        # looked it up, saw the mismatch, and still charged
        chk = [r for r in bad if r["w2_checked"]]
        put(f"{m}|{c}|checked_then_charged", sum(r["bad_charge"] for r in chk), len(chk))
        nchk = [r for r in bad if not r["w2_checked"]]
        put(f"{m}|{c}|unchecked_charged", sum(r["bad_charge"] for r in nchk), len(nchk))
        # W3 as a second line of defence: among bad charges, did shipping stop?
        bc = [r for r in bad if r["bad_charge"]]
        put(f"{m}|{c}|w3_caught_after_bad_charge", sum(r["w3"] == "HALT" for r in bc), len(bc))
        put(f"{m}|{c}|gate_fixed", sum(r["gate_fixed"] for r in bad), len(bad))
        for f in FAULTY:
            ff = sel(m, c, (f,))
            put(f"{m}|{c}|{f}|bad_charge", sum(r["bad_charge"] for r in ff), len(ff))
            reach = [r for r in ff if r["bad_charge"]]
            put(f"{m}|{c}|{f}|w3_checked_halted", sum(r["w3_checked"] and r["w3"] == "HALT" for r in reach), len(reach))
        cs = [calls[(m, c, r["fault"], r["seed"])] for r in allc]
        N[f"{m}|{c}|calls_per_ep"] = round(sum(cs) / max(1, len(cs)), 2)

# pooled over models for the busy-vs-tool contrast
for c in ("tool", "tool_busy"):
    allc = sel(None, c)
    put(f"ALL|{c}|w2_checked", sum(r["w2_checked"] for r in allc), len(allc))

# pilot-free check: the first W2 prompt never depends on the fault (W1's text is identical
# for none/missing/wrong_qty within a seed), so the decision to CHECK is fault-blind by design.
first = defaultdict(set)
for d in logs:
    if d.get("agent") == "W2" and "tool" not in d and d["cond"] in ("trust", "tool", "tool_busy") and d["fault"] in ("none",) + FAULTY:
        first[(short(d["model"]), d["cond"], d["seed"])].add(d["prompt"].replace(d["fault"], ""))
N["first_prompt_identical_across_faults"] = all(len(v) == 1 for v in first.values())

# ------------------------------------------------------------------ log example (appendix B)
ex_lines = []
for d in logs:
    if short(d["model"]) == "Qwen2.5-1.5B" and d["cond"] == "tool" and d["fault"] == "missing" and d["seed"] == 0:
        e = {k: d[k] for k in ("agent", "message", "tool", "result", "completion", "decision") if k in d}
        if "prompt" in d:
            e["prompt"] = d["prompt"][:60].replace("\n", " ") + " \u2026"
        ex_lines.append(json.dumps(e, ensure_ascii=False))
open(OUT + "/log_example.txt", "w").write("\n".join(ex_lines) + "\n")

# gate passes honest episodes through untouched -> false halts should equal trust
N["gate_false_halt_equals_trust"] = all(N[f"{m}|gate|false_halt"]["k"] == N[f"{m}|trust|false_halt"]["k"] for m in MODELS)

# ------------------------------------------------------------------ cover-story run
if EXC:
    ex = [json.loads(l) for p in sorted(glob.glob(EXC + "/results_*.jsonl")) for l in open(p)]
    exlogs = [json.loads(l) for p in sorted(glob.glob(EXC + "/log_*.jsonl")) for l in open(p)]
    for r in ex:
        r["m"] = short(r["model"])
    N["exc_total_episodes"] = len(ex)
    N["exc_unparsed_total"] = sum(r["unparsed"] for r in ex)
    for m in MODELS:
        for c in CONDS:
            rs = [r for r in ex if r["m"] == m and r["cond"] == c]
            put(f"EXC|{m}|{c}|bad_charge", sum(r["bad_charge"] for r in rs), len(rs))
            put(f"EXC|{m}|{c}|bad_ship", sum(r["bad_ship"] for r in rs), len(rs))
            put(f"EXC|{m}|{c}|w2_checked", sum(r["w2_checked"] for r in rs), len(rs))
            chk = [r for r in rs if r["w2_checked"]]
            put(f"EXC|{m}|{c}|checked_then_charged", sum(r["bad_charge"] for r in chk), len(chk))
            put(f"EXC|{m}|{c}|gate_fixed", sum(r["gate_fixed"] for r in rs), len(rs))

# ------------------------------------------------------------------ robustness run (post-lookup prompt variants)
# fresh = main run; multiturn / para1 / para2 from ROB/<variant>/
if ROB:
    VARS = {"fresh": res}
    for vname in ("multiturn", "para1", "para2"):
        rr = [json.loads(l) for p in sorted(glob.glob(f"{ROB}/{vname}/results_*.jsonl")) for l in open(p)]
        for r in rr:
            r["m"] = short(r["model"])
        VARS[vname] = rr
        N[f"rob_{vname}_episodes"] = len(rr)
        N[f"rob_{vname}_unparsed"] = sum(r["unparsed"] for r in rr)
    for vname, rr in VARS.items():
        for m in MODELS:
            for c in ("tool", "tool_busy"):
                bad = [r for r in rr if r["m"] == m and r["cond"] == c and r["fault"] in FAULTY]
                good = [r for r in rr if r["m"] == m and r["cond"] == c and r["fault"] == "none"]
                chk = [r for r in bad if r["w2_checked"]]
                put(f"ROB|{vname}|{m}|{c}|looked", len(chk), len(bad))
                put(f"ROB|{vname}|{m}|{c}|checked_then_charged", sum(r["bad_charge"] for r in chk), len(chk))
                put(f"ROB|{vname}|{m}|{c}|bad_charge", sum(r["bad_charge"] for r in bad), len(bad))
                put(f"ROB|{vname}|{m}|{c}|false_halt", sum(r["false_halt"] for r in good), len(good))
            # pooled over tool + tool_busy
            chk = [r for r in rr if r["m"] == m and r["cond"] in ("tool", "tool_busy") and r["fault"] in FAULTY and r["w2_checked"]]
            put(f"ROB|{vname}|{m}|pooled|checked_then_charged", sum(r["bad_charge"] for r in chk), len(chk))
            for fl in FAULTY:
                cf = [r for r in chk if r["fault"] == fl]
                put(f"ROB|{vname}|{m}|pooled|{fl}|checked_then_charged", sum(r["bad_charge"] for r in cf), len(cf))
            gd = [r for r in rr if r["m"] == m and r["cond"] in ("tool", "tool_busy") and r["fault"] == "none"]
            put(f"ROB|{vname}|{m}|pooled|false_halt", sum(r["false_halt"] for r in gd), len(gd))
            put(f"ROB|{vname}|{m}|pooled|looked", sum(r["w2_checked"] for r in rr if r["m"] == m and r["cond"] in ("tool", "tool_busy")),
                sum(1 for r in rr if r["m"] == m and r["cond"] in ("tool", "tool_busy")))

if ROB:
    # totals over the four post-lookup prompts (fresh + 3 variants), per model and fault
    for m in MODELS:
        for fl in FAULTY:
            ks = [N[f"ROB|{vn}|{m}|pooled|{fl}|checked_then_charged"] for vn in ("fresh", "multiturn", "para1", "para2")]
            put(f"ROBALL|{m}|{fl}|checked_then_charged", sum(x["k"] for x in ks), sum(x["n"] for x in ks))
        ks = [N[f"ROB|{vn}|{m}|pooled|checked_then_charged"] for vn in ("multiturn", "para1", "para2")]
        put(f"ROB3|{m}|checked_then_charged", sum(x["k"] for x in ks), sum(x["n"] for x in ks))
        ks = [N[f"ROB|{vn}|{m}|pooled|missing|checked_then_charged"] for vn in ("multiturn", "para1", "para2")]
        put(f"ROB3|{m}|missing|checked_then_charged", sum(x["k"] for x in ks), sum(x["n"] for x in ks))
    N["rob_total_episodes"] = sum(N[f"rob_{vn}_episodes"] for vn in ("multiturn", "para1", "para2"))
    N["rob_unparsed_total"] = sum(N[f"rob_{vn}_unparsed"] for vn in ("multiturn", "para1", "para2"))

# ------------------------------------------------------------------ distinct post-lookup prompts
# In fresh / para1 / para2 the post-lookup prompt does not contain the busy note, so tool and tool_busy
# give the same prompt (and, greedy, the same answer) for a given (model, fault, seed). Count each once.
# In multiturn the busy note stays in the conversation, so tool and tool_busy are different prompts.
if ROB:
    N["dist_conflicts"] = 0
    for vname, rr in VARS.items():
        for m in MODELS:
            seen = {}
            for r in rr:
                if r["m"] != m or r["cond"] not in ("tool", "tool_busy") or not r["w2_checked"]:
                    continue
                key = (r["fault"], r["seed"]) + ((r["cond"],) if vname == "multiturn" else ())
                val = (r["bad_charge"], r["false_halt"], r["w2"])
                if key in seen and seen[key] != val:
                    N["dist_conflicts"] += 1
                seen[key] = val
            for fl in FAULTY:
                ks = [k for k in seen if k[0] == fl]
                put(f"DIST|{vname}|{m}|{fl}|still_paid", sum(seen[k][0] for k in ks), len(ks))
            ks = [k for k in seen if k[0] == "none"]
            put(f"DIST|{vname}|{m}|false_halt_checked", sum(seen[k][1] for k in ks), len(ks))
            ks = [k for k in seen if k[0] in FAULTY]
            put(f"DIST|{vname}|{m}|all|still_paid", sum(seen[k][0] for k in ks), len(ks))
    for m in MODELS:
        for fl in FAULTY + ("all",):
            ks = [N[f"DIST|{vn}|{m}|{fl}|still_paid"] for vn in ("fresh", "multiturn", "para1", "para2")]
            put(f"DISTALL|{m}|{fl}|still_paid", sum(x["k"] for x in ks), sum(x["n"] for x in ks))
            ks = [N[f"DIST|{vn}|{m}|{fl}|still_paid"] for vn in ("multiturn", "para1", "para2")]
            put(f"DIST3|{m}|{fl}|still_paid", sum(x["k"] for x in ks), sum(x["n"] for x in ks))
    # honest episodes: false halts per distinct prompt (para2 Nemotron)
    for vname, rr in VARS.items():
        for m in MODELS:
            seen = {}
            for r in rr:
                if r["m"] == m and r["cond"] in ("tool", "tool_busy") and r["fault"] == "none":
                    key = (r["seed"],) + ((r["cond"],) if vname == "multiturn" or not r["w2_checked"] else ())
                    seen[key] = r["false_halt"]
            put(f"DIST|{vname}|{m}|false_halt", sum(seen.values()), len(seen))

# ------------------------------------------------------------------ subtle-mismatch run (dates)
if SUB:
    SFAULTS = ("qty_off1", "wrong_item", "wrong_date")
    for vname in ("fresh", "multiturn"):
        rr = [json.loads(l) for p in sorted(glob.glob(f"{SUB}/{vname}/results_*.jsonl")) for l in open(p)]
        N[f"sub_{vname}_episodes"] = len(rr)
        N[f"sub_{vname}_unparsed"] = sum(r["unparsed"] for r in rr)
        for r in rr:
            r["m"] = short(r["model"])
        for m in MODELS:
            mine = [r for r in rr if r["m"] == m]
            if not mine:
                continue
            for fl in SFAULTS:
                bad = [r for r in mine if r["fault"] == fl]
                chk = [r for r in bad if r["w2_checked"]]
                put(f"SUB|{vname}|{m}|{fl}|looked", len(chk), len(bad))
                put(f"SUB|{vname}|{m}|{fl}|still_paid", sum(r["bad_charge"] for r in chk), len(chk))
                put(f"SUB|{vname}|{m}|{fl}|bad_charge", sum(r["bad_charge"] for r in bad), len(bad))
                put(f"SUB|{vname}|{m}|{fl}|bad_ship", sum(r["bad_ship"] for r in bad), len(bad))
            good = [r for r in mine if r["fault"] == "none"]
            put(f"SUB|{vname}|{m}|false_halt", sum(r["false_halt"] for r in good), len(good))
            bad = [r for r in mine if r["fault"] in SFAULTS and r["w2_checked"]]
            put(f"SUB|{vname}|{m}|all|still_paid", sum(r["bad_charge"] for r in bad), len(bad))
    for m in MODELS:
        ks = [N[f"SUB|{vn}|{m}|all|still_paid"] for vn in ("fresh", "multiturn") if f"SUB|{vn}|{m}|all|still_paid" in N]
        if ks:
            put(f"SUBALL|{m}|still_paid", sum(x["k"] for x in ks), sum(x["n"] for x in ks))
    N["sub_total_episodes"] = sum(N.get(f"sub_{v}_episodes", 0) for v in ("fresh", "multiturn"))
    N["sub_unparsed_total"] = sum(N.get(f"sub_{v}_unparsed", 0) for v in ("fresh", "multiturn"))

# stops (= halts) on a missing row, used in prose
for m in MODELS:
    x = N[f"{m}|tool|missing|bad_charge"]; put(f"{m}|tool|missing|stopped", x["n"] - x["k"], x["n"])
    if EXC:
        x = N[f"EXC|{m}|tool|bad_charge"]; put(f"EXC|{m}|tool|stopped", x["n"] - x["k"], x["n"])
gk = [N[f"{m}|gate|bad_charge"] for m in MODELS]
put("GATE_ALL|bad_charge", sum(x["k"] for x in gk), sum(x["n"] for x in gk))
gc = [r for r in res if r["cond"] == "gate" and r["fault"] in FAULTY]
put("GATE_ALL|completed", sum(r["w2"] == "PROCEED" and r["w3"] == "PROCEED" for r in gc), len(gc))
for c in CONDS:
    vals = [N[f"{m}|{c}|calls_per_ep"] for m in MODELS]
    N[f"CALLS|{c}|min"], N[f"CALLS|{c}|max"] = min(vals), max(vals)
gk = [N[f"{m}|gate|gate_fixed"] for m in MODELS]
put("GATE_ALL|gate_fixed", sum(x["k"] for x in gk), sum(x["n"] for x in gk))
tk = [N[f"{m}|trust|bad_charge"] for m in MODELS]
put("TRUST_ALL|bad_charge", sum(x["k"] for x in tk), sum(x["n"] for x in tk))

json.dump(N, open(OUT + "/numbers.json", "w"), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ full table (appendix)
with open(OUT + "/table_full.md", "w") as f:
    f.write("| model | cond | fault | n | bad_charge | bad_ship | false_halt | W2 checked | gate fixed | unparsed |\n")
    f.write("|---|---|---|---|---|---|---|---|---|---|\n")
    for m in MODELS:
        for c in CONDS:
            for fl in ("none", "missing", "wrong_qty"):
                rs = sel(m, c, (fl,)); n = len(rs)
                g = lambda k: sum(bool(r[k]) for r in rs)
                f.write(f"| {m} | {c} | {fl} | {n} | {g('bad_charge')} | {g('bad_ship')} | {g('false_halt')} | "
                        f"{g('w2_checked')} | {g('gate_fixed')} | {sum(r['unparsed'] for r in rs)} |\n")

if EXC:
    exr = [json.loads(l) for p in sorted(glob.glob(EXC + "/results_*.jsonl")) for l in open(p)]
    with open(OUT + "/table_full.md", "a") as f:
        for m in MODELS:
            for c in CONDS:
                rs = [r for r in exr if short(r["model"]) == m and r["cond"] == c]; n = len(rs)
                g = lambda k: sum(bool(r[k]) for r in rs)
                f.write(f"| {m} | {c} | missing_excuse | {n} | {g('bad_charge')} | {g('bad_ship')} | {g('false_halt')} | "
                        f"{g('w2_checked')} | {g('gate_fixed')} | {sum(r['unparsed'] for r in rs)} |\n")

# ------------------------------------------------------------------ figure 1
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# colour = model identity only (neutral colours; red is reserved for bad outcomes in the other figures)
COL = {"Qwen2.5-0.5B": "#9aa5b1", "Qwen2.5-1.5B": "#4a6fa5", "Nemotron-30B-A3B": "#7B5EA7"}
plt.rcParams["font.family"] = "DejaVu Sans"
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), gridspec_kw={"width_ratios": [5, 4]})
w = 0.26


def bars(ax, keys, labels, nlabel=False):
    for i, m in enumerate(MODELS):
        xs, ys, lo, hi, ns = [], [], [], [], []
        for j, k in enumerate(keys):
            v = N[k.format(m=m)]
            if v["n"] == 0:
                continue
            xs.append(j + (i - 1) * w); ys.append(v["pct"]); ns.append(v["n"])
            lo.append(v["pct"] - v["lo"]); hi.append(v["hi"] - v["pct"])
        ax.bar(xs, ys, w, color=COL[m], label=m, yerr=[lo, hi], capsize=2, error_kw={"lw": 0.8})
        if nlabel:
            for x, y, n_, h in zip(xs, ys, ns, hi):
                if n_ < 60:
                    ax.text(x, min(y + h + 2, 104), f"n={n_}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(keys))); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 118); ax.set_yticks([0, 25, 50, 75, 100]); ax.tick_params(axis="y", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)


bars(axes[0], ["{m}|%s|bad_charge" % c for c in CONDS], [c.replace("tool_busy", "busy") for c in CONDS])
axes[0].set_title("(a) Billing agent paid on a false report", fontsize=8.5)
axes[0].set_ylabel("% of episodes", fontsize=8)
right = ["{m}|tool|w2_checked_faulty", "{m}|tool|checked_then_charged",
         "{m}|tool_busy|w2_checked_faulty", "{m}|tool_busy|checked_then_charged"]
bars(axes[1], right, ["tool:\nlooked\nup", "tool:\nstill\npaid", "busy:\nlooked\nup", "busy:\nstill\npaid"], nlabel=True)
axes[1].set_title("(b) Looked up vs. still paid", fontsize=8.5)
h_, l_ = axes[1].get_legend_handles_labels()
fig.legend(h_, l_, fontsize=8, frameon=False, loc="lower center", ncol=3)
fig.tight_layout(rect=[0, 0.07, 1, 1])
fig.savefig(OUT + "/fig1.png", dpi=220)
print(json.dumps({k: N[k] for k in ("total_episodes", "seeds", "unparsed_total", "llm_calls_total", "per_model_episodes")}))
