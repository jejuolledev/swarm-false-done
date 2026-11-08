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
    rows = [
        ("Qwen 1.5B \u00b7 wrong qty \u00b7 4 wordings", N["DISTALL|Qwen2.5-1.5B|wrong_qty|still_paid"]),
        ("Qwen 1.5B \u00b7 wrong qty \u00b7 multi-turn", N["DIST|multiturn|Qwen2.5-1.5B|wrong_qty|still_paid"]),
        ("Qwen 1.5B \u00b7 missing row \u00b7 main prompt", N["DIST|fresh|Qwen2.5-1.5B|missing|still_paid"]),
        ("Qwen 1.5B \u00b7 missing row \u00b7 other 3", N["DIST3|Qwen2.5-1.5B|missing|still_paid"]),
        ("Nemotron \u00b7 both mismatches \u00b7 4 wordings", N["DISTALL|Nemotron-30B-A3B|all|still_paid"]),
    ]
    if "SUBALL|Nemotron-30B-A3B|still_paid" in N:
        rows.append(("Nemotron \u00b7 qty\u22121, item, date", N["SUBALL|Nemotron-30B-A3B|still_paid"]))
    rows.append(("State check, no LLM \u00b7 3 models", N["GATE_ALL|bad_charge"]))
    return rows


def headline(path, big=False):
    rows = headline_rows()
    h = 0.205 * len(rows) + 0.47
    fig, ax = plt.subplots(figsize=(6.3, h) if not big else (16, 7.6))
    fs = 8 if not big else 17
    for i, (lab, v) in enumerate(rows):
        y = len(rows) - 1 - i
        col = RED if v["k"] > 0 else NAVY
        ax.barh(y, max(v["pct"], 0.0), color=col, height=0.72)
        ax.errorbar(v["pct"], y, xerr=[[v["pct"] - v["lo"]], [v["hi"] - v["pct"]]], color="black", capsize=3, lw=0.9)
        txt = f"{v['k']}/{v['n']}  ({v['pct']:.0f}%, CI {v['lo']:.0f}\u2013{v['hi']:.0f}%)"
        ax.text(v["hi"] + 2, y, txt, va="center", fontsize=fs, color=col, fontweight="bold")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=fs)
    ax.set_xlim(0, 188); ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("% of distinct post-lookup prompts in which the agent paid", fontsize=fs)
    ax.tick_params(axis="x", labelsize=fs)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Looked it up, then paid anyway", fontsize=fs + 2, fontweight="bold", color=NAVY, loc="left", pad=3)
    fig.tight_layout()
    fig.savefig(path, dpi=220 if not big else 120)
    plt.close(fig)


def box(ax, x, y, w, h, title, sub, fc, ec, tc="white", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h * 0.75, title, ha="center", va="center", fontsize=fs + 1.5, color=tc, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.33, sub, ha="center", va="center", fontsize=fs - 1, color=tc)


def arrow(ax, a, b, col=NAVY, ls="-", lw=1.6, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=col, lw=lw, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))


def pipeline(path, big=False):
    fig, ax = plt.subplots(figsize=(5.8, 2.75) if not big else (16, 7.4))
    s = 1.0 if not big else 2.45
    ax.set_xlim(0, 10); ax.set_ylim(0, 4.3); ax.axis("off")
    box(ax, 0.05, 2.5, 2.4, 1.25, "1  Reserve", "W1 (script)\nmay send\na false DONE", LIGHT, NAVY, tc=NAVY, fs=9 * s)
    box(ax, 3.8, 2.5, 2.4, 1.25, "2  Pay", "W2 (LLM)\nPROCEED, HALT\nor CHECK", NAVY, NAVY, fs=9 * s)
    box(ax, 7.55, 2.5, 2.4, 1.25, "3  Ship", "W3 (LLM)\nPROCEED, HALT\nor CHECK", NAVY, NAVY, fs=9 * s)
    ax.add_patch(FancyBboxPatch((3.55, 0.15), 2.9, 0.75, boxstyle="round,pad=0.02,rounding_size=0.2", fc="white", ec=GRAY, lw=1.2))
    ax.text(5.0, 0.52, "SQLite reservations\n(ground truth)", ha="center", va="center", fontsize=8 * s, color="#4A5260")
    arrow(ax, (2.5, 3.12), (3.75, 3.12), col=RED, lw=2.0)
    ax.text(3.12, 3.85, "false \u201cDONE\u201d\nin planted runs", ha="center", va="bottom", fontsize=8 * s, color=RED)
    arrow(ax, (6.25, 3.12), (7.5, 3.12))
    ax.text(6.87, 3.85, "\u201cDONE:\ncharged\u201d", ha="center", va="bottom", fontsize=8 * s, color=NAVY)
    ax.add_patch(FancyBboxPatch((2.55, 1.45), 1.15, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1", fc=GREEN, ec=GREEN))
    ax.text(3.12, 1.75, "state\ncheck", ha="center", va="center", fontsize=8 * s, color="white", fontweight="bold")
    arrow(ax, (3.12, 2.08), (3.12, 3.0), col=GREEN, lw=1.3)
    arrow(ax, (3.3, 1.43), (4.0, 0.92), col=GREEN, ls="--", lw=1.3)
    ax.text(1.25, 1.55, "compares claim with\ndatabase, asks W1 to\nredo (no LLM)", ha="center", va="center",
            fontsize=8 * s, color=GREEN)
    arrow(ax, (5.0, 2.47), (5.0, 0.95), col=ORANGE, ls="--", lw=1.3)
    arrow(ax, (8.75, 2.47), (6.5, 0.6), col=ORANGE, ls="--", lw=1.3, rad=-0.15)
    ax.text(5.15, 1.75, "CHECK:\nread the row", ha="left", va="center", fontsize=8 * s, color=ORANGE)
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
    fig, axes = plt.subplots(2, 1, figsize=(5.6, 3.1) if not big else (16, 7.6))
    s = 1.15 if not big else 2.6
    for ax, fault, ttl in ((axes[0], "missing", "Missing row"), (axes[1], "wrong_qty", "Wrong quantity")):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        recs = eps[fault]
        w1 = next(d for d in recs if d["agent"] == "W1")
        w2a = next(d for d in recs if d["agent"] == "W2" and "tool" not in d)
        w2b = next(d for d in recs if d["agent"] == "W2" and "tool" in d)
        order = w2a["prompt"].split("\n")[0]
        lines = [
            ("Order", order, NAVY),
            ("W1 says", w1["message"].split(", reservation")[0] + " \u2026", "#4A5260"),
            ("W2 replies", w2a["completion"], ORANGE),
            ("Database", w2b["result"], RED),
            ("W2 replies", w2b["completion"] + "   → customer charged", RED),
        ]
        ax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.0,rounding_size=0.03", fc="white", ec=GRAY, lw=1))
        ax.text(0.05, 0.93, f"{ttl}  ·  Qwen2.5-1.5B, tool, seed 0", fontsize=8 * s, fontweight="bold", color=NAVY, va="top")
        y = 0.74
        for lab, val, col in lines:
            ax.text(0.05, y, lab, fontsize=8 * s, color=GRAY, va="top")
            ax.text(0.21, y, val, fontsize=7.0 * s, color=col, va="top", family="DejaVu Sans Mono",
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
