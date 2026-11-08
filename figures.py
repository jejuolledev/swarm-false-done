"""Extra figures for the report and the video: headline, pipeline diagram, one real logged run.
Every number is read from results/numbers.json; the logged run is read verbatim from the JSONL log.

Usage: .venv/bin/python -I figures.py results runs/main_1108
"""
import json, os, sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RES, RUN = sys.argv[1], sys.argv[2]
N = json.load(open(os.path.join(RES, "numbers.json")))
NAVY, ORANGE, GRAY, LIGHT, RED, GREEN = "#1F2A44", "#D9541E", "#8A93A3", "#F3F1EC", "#B83A2E", "#2E7D5B"
plt.rcParams["font.family"] = "DejaVu Sans"


def headline_rows():
    return [
        ("Qwen2.5-1.5B looked it up and still paid\n(main prompt, missing row + wrong quantity)",
         N["ROB|fresh|Qwen2.5-1.5B|pooled|checked_then_charged"], ORANGE),
        ("Qwen2.5-1.5B looked it up and still paid\n(wrong quantity, all 4 prompt wordings)",
         N["ROBALL|Qwen2.5-1.5B|wrong_qty|checked_then_charged"], ORANGE),
        ("Nemotron-30B-A3B looked it up and still paid\n(main prompt)",
         N["ROB|fresh|Nemotron-30B-A3B|pooled|checked_then_charged"], GRAY),
        ("Non-LLM state check, all three models\n(bad payments; by design)", N["GATE_ALL|bad_charge"], NAVY),
    ]


def headline(path, big=False):
    rows = headline_rows()
    fig, ax = plt.subplots(figsize=(7.0, 1.95) if not big else (16, 7.2))
    fs = 7.2 if not big else 17
    for i, (lab, v, col) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, v["pct"], color=col, height=0.62)
        ax.errorbar(v["pct"], y, xerr=[[v["pct"] - v["lo"]], [v["hi"] - v["pct"]]], color="black", capsize=3, lw=0.9)
        txt = f"{v['k']}/{v['n']}  ({v['pct']:.0f}%, 95% CI {v['lo']:.0f}–{v['hi']:.0f}%)"
        x = v["hi"] + 2
        ax.text(x, y, txt, va="center", fontsize=fs, color=col if col != GRAY else "#4A5260", fontweight="bold")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=fs - 0.5)
    ax.set_xlim(0, 172); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("% of false-report episodes in which the billing agent paid", fontsize=fs - 0.5)
    ax.tick_params(axis="x", labelsize=fs - 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=220 if not big else 120)
    plt.close(fig)


def box(ax, x, y, w, h, title, sub, fc, ec, tc="white", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=fs + 1.5, color=tc, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=fs - 1, color=tc)


def arrow(ax, a, b, col=NAVY, ls="-", lw=1.6, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=col, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))


def pipeline(path, big=False):
    fig, ax = plt.subplots(figsize=(7.0, 2.7) if not big else (16, 6.2))
    s = 1 if not big else 2.0
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    box(ax, 0.2, 2.3, 2.0, 1.2, "1  Reserve", "W1, script\nmay send a false DONE", LIGHT, NAVY, tc=NAVY, fs=8 * s)
    box(ax, 4.0, 2.3, 2.0, 1.2, "2  Pay", "W2, LLM\nPROCEED / HALT / CHECK", NAVY, NAVY, fs=8 * s)
    box(ax, 7.8, 2.3, 2.0, 1.2, "3  Ship", "W3, LLM\nPROCEED / HALT / CHECK", NAVY, NAVY, fs=8 * s)
    # database
    ax.add_patch(FancyBboxPatch((3.6, 0.2), 2.8, 0.85, boxstyle="round,pad=0.02,rounding_size=0.2", fc="white", ec=GRAY, lw=1.2))
    ax.text(5.0, 0.62, "SQLite: reservations (ground truth)", ha="center", va="center", fontsize=7.5 * s, color="#4A5260")
    # false done
    arrow(ax, (2.25, 3.05), (3.95, 3.05), col=RED, lw=2.0)
    ax.text(3.1, 3.35, "“DONE: reserved 4 x …”\n(false in planted runs)", ha="center", va="bottom", fontsize=6.8 * s, color=RED)
    arrow(ax, (6.05, 3.05), (7.75, 3.05))
    ax.text(6.9, 3.35, "“DONE: charged …”", ha="center", va="bottom", fontsize=6.8 * s, color=NAVY)
    # gate
    ax.add_patch(FancyBboxPatch((2.45, 1.5), 1.3, 0.55, boxstyle="round,pad=0.02,rounding_size=0.1", fc=GREEN, ec=GREEN))
    ax.text(3.1, 1.77, "state gate", ha="center", va="center", fontsize=7.5 * s, color="white", fontweight="bold")
    arrow(ax, (3.1, 1.48), (4.2, 1.08), col=GREEN, ls="--", lw=1.3)
    ax.text(1.95, 1.2, "gate: compare claim\nwith DB, redo if wrong\n(no LLM)", ha="center", va="center", fontsize=6.5 * s, color=GREEN)
    arrow(ax, (3.1, 2.06), (3.1, 2.95), col=GREEN, lw=1.3)
    # lookups
    arrow(ax, (5.0, 2.28), (5.0, 1.1), col=ORANGE, ls="--", lw=1.3)
    arrow(ax, (8.8, 2.28), (6.45, 0.95), col=ORANGE, ls="--", lw=1.3, rad=-0.15)
    ax.text(6.75, 0.4, "optional lookup (tool):\nCHECK → database result → decide", ha="left", va="center",
            fontsize=6.5 * s, color=ORANGE)
    fig.tight_layout()
    fig.savefig(path, dpi=220 if not big else 120)
    plt.close(fig)


def logged_run(path, big=False):
    """Two real episodes, read from the log: Qwen2.5-1.5B, condition tool, seed 0."""
    log = os.path.join(RUN, "log_Qwen2.5-1.5B-Instruct.jsonl")
    eps = {"missing": [], "wrong_qty": []}
    for l in open(log):
        d = json.loads(l)
        if d["cond"] == "tool" and d["seed"] == 0 and d["fault"] in eps:
            eps[d["fault"]].append(d)
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 4.3) if not big else (16, 7.6))
    s = 1 if not big else 2.35
    for ax, fault, ttl in ((axes[0], "missing", "Missing row"), (axes[1], "wrong_qty", "Wrong quantity")):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        recs = eps[fault]
        w1 = next(d for d in recs if d["agent"] == "W1")
        w2a = next(d for d in recs if d["agent"] == "W2" and "tool" not in d)
        w2b = next(d for d in recs if d["agent"] == "W2" and "tool" in d)
        order = w2a["prompt"].split("\n")[0]
        lines = [
            ("Order", order, NAVY),
            ("W1 says", w1["message"], "#4A5260"),
            ("W2 replies", w2a["completion"], ORANGE),
            ("Database", w2b["result"], RED),
            ("W2 replies", w2b["completion"] + "   → customer charged", RED),
        ]
        ax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.0,rounding_size=0.03", fc="white", ec=GRAY, lw=1))
        ax.text(0.05, 0.93, f"{ttl}  ·  Qwen2.5-1.5B, tool, seed 0", fontsize=8 * s, fontweight="bold", color=NAVY, va="top")
        y = 0.76
        for lab, val, col in lines:
            ax.text(0.05, y, lab, fontsize=6.8 * s, color=GRAY, va="top")
            ax.text(0.17, y, val, fontsize=7.0 * s, color=col, va="top", family="DejaVu Sans Mono",
                    fontweight="bold" if col in (ORANGE, RED) else "normal")
            y -= 0.15
    fig.tight_layout()
    fig.savefig(path, dpi=220 if not big else 120)
    plt.close(fig)


if __name__ == "__main__":
    headline(os.path.join(RES, "fig_headline.png"))
    pipeline(os.path.join(RES, "fig_pipeline.png"))
    logged_run(os.path.join(RES, "fig_logrun.png"))
    big = os.path.join(RES, "video_figs"); os.makedirs(big, exist_ok=True)
    headline(os.path.join(big, "headline.png"), big=True)
    pipeline(os.path.join(big, "pipeline.png"), big=True)
    logged_run(os.path.join(big, "logrun.png"), big=True)
    print("ok")
