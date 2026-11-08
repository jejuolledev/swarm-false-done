"""Silent 1920x1080 presentation video built from the report's own figures, with on-screen captions.
All numbers come from results/numbers.json. No voice.

Usage: .venv/bin/python -I make_video.py results out.mp4
"""
import json, os, subprocess, sys, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

RES, OUT = sys.argv[1], sys.argv[2]
N = json.load(open(os.path.join(RES, "numbers.json")))
SL = os.path.join(RES, "video_slides"); os.makedirs(SL, exist_ok=True)
for _old in os.listdir(SL):
    os.remove(os.path.join(SL, _old))
VF = os.path.join(RES, "video_figs")
NAVY, ORANGE, GRAY, BG, RED = "#1F2A44", "#D9541E", "#5B6475", "#FBFAF7", "#B83A2E"
plt.rcParams["font.family"] = "DejaVu Sans"


def f(key):
    x = N[key]; return f"{x['k']}/{x['n']}"


def c(key):
    x = N[key]; return f"{x['k']}/{x['n']} ({x['pct']:.0f}%, 95% CI {x['lo']:.0f}–{x['hi']:.0f}%)"


def slide(i, title, accent=None, bullets=(), image=None, caption=None, take=None, big=None, bigcol=None, mono=False):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    fig.patch.set_facecolor(BG)
    fig.text(0.05, 0.955, "Looking It Up Is Not Stopping  ·  Swarm Alignment Sprint 2026  ·  MoaHub",
             fontsize=15, color=GRAY, va="top")
    fig.text(0.95, 0.955, f"{i}", fontsize=15, color=GRAY, va="top", ha="right")
    fig.text(0.05, 0.89, title, fontsize=38, color=NAVY, fontweight="bold", va="top")
    if accent:
        fig.text(0.05, 0.82, accent, fontsize=38, color=ORANGE, fontweight="bold", va="top")
    top = 0.72 if accent else 0.79
    if big:
        fig.text(0.05, top - 0.02, big[0], fontsize=110, color=bigcol or RED, fontweight="bold", va="top")
        fig.text(0.05, top - 0.22, big[1], fontsize=26, color=NAVY, va="top")
        top -= 0.32
    y = top
    for b in bullets:
        txt = textwrap.fill(b, 78) if not mono else b
        if not mono:
            fig.text(0.07, y, "•", fontsize=27, color=ORANGE, va="top")
        col = RED if (mono and ("NOT FOUND" in b or "PROCEED" in b)) else NAVY
        fig.text(0.09, y, txt, fontsize=27 if not mono else 26, color=col, va="top", linespacing=1.35,
                 family="DejaVu Sans Mono" if mono else "DejaVu Sans", fontweight="bold" if col == RED else "normal")
        y -= 0.075 * (txt.count("\n") + 1) + 0.03
    if image:
        img = mpimg.imread(image)
        h, w = img.shape[:2]
        bottom = (0.31 if caption else 0.23) if take else (0.22 if caption else 0.14)
        avail_h = (y - 0.02 if bullets else top) - bottom
        aw = min(0.9, avail_h * (w / h) * (10.8 / 19.2))
        ah = aw * (h / w) * (19.2 / 10.8)
        ax = fig.add_axes([0.5 - aw / 2, bottom + (avail_h - ah) / 2, aw, ah]); ax.imshow(img); ax.axis("off")
    if caption:
        fig.text(0.05, 0.285 if take else 0.20, textwrap.fill(caption, 110), fontsize=21, color="#3A4250", va="top")
    if take:
        # kept above the bottom 12% that a video player's control bar covers
        fig.patches.append(matplotlib.patches.FancyBboxPatch((0.05, 0.135), 0.9, 0.085, boxstyle="round,pad=0.005",
                                                             transform=fig.transFigure, fc=NAVY, ec=NAVY))
        fig.text(0.07, 0.177, "Implication:  ", fontsize=23, color="#F29A6B", fontweight="bold", va="center")
        fig.text(0.205, 0.177, textwrap.fill(take, 82), fontsize=22, color="white", va="center")
    p = os.path.join(SL, f"s{i:02d}.png"); fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


Q15, NEM, Q05 = "Qwen2.5-1.5B", "Nemotron-30B-A3B", "Qwen2.5-0.5B"
HAS_SUB = N.get("sub_total_episodes", 0) > 0
eps = N["total_episodes"] + N["exc_total_episodes"] + N["rob_total_episodes"] + (N["sub_total_episodes"] if HAS_SUB else 0)
D = lambda vn, m, fl: f"DIST|{vn}|{m}|{fl}|still_paid"
# one real logged episode, read verbatim
LOG = []
for l in open(os.path.join(os.path.dirname(RES.rstrip("/")) or ".", "runs/main_1108/log_Qwen2.5-1.5B-Instruct.jsonl")):
    d = json.loads(l)
    if d["cond"] == "tool" and d["seed"] == 0 and d["fault"] == "missing":
        LOG.append(d)
w1 = next(d for d in LOG if d["agent"] == "W1"); w2a = next(d for d in LOG if d["agent"] == "W2" and "tool" not in d)
w2b = next(d for d in LOG if d["agent"] == "W2" and "tool" in d)
S = []  # (path, seconds)
S.append((slide(1, "Looking it up is not stopping",
                "When pipeline agents act on a peer's false “done”",
                bullets=["Jungkil Bae, MoaHub (independent), Gwangju-si, South Korea",
                         "Apart Research · Swarm Alignment Sprint 2026 · Track 4: Multi-Agent Oversight and Control",
                         "Silent walkthrough of the report. All numbers come from the run logs."]), 12))
S.append((slide(2, "Agents hand work to each other with one word: DONE.",
                "What if the DONE is false?",
                bullets=["The next agent pays, ships or merges on the strength of that sentence.",
                         "Agent-written records can be wrong: METR's investigation of the OpenAI / Hugging Face hacking "
                         "incident reports that roughly 7% of the transcripts it evaluated were spoofed in some places.",
                         "Question: does the next agent check? And when it checks, does it act on what it found?"]), 16))
S.append((slide(3, "A three-step pipeline on a fake database", image=os.path.join(VF, "pipeline.png"),
                caption="W1 is a script and can send a false DONE. W2 pays and W3 ships; both are LLMs. "
                        "The state check compares the claim with the database in code."), 16))
S.append((slide(4, "Five conditions, three local models",
                bullets=["trust: the agent sees only the message.",
                         "tool / tool + time pressure: the agent may answer CHECK to read the reservation first.",
                         "shown: the database result is always in the prompt.",
                         "gate: a non-LLM state check before the payment step, with one redo.",
                         f"Qwen2.5-0.5B, Qwen2.5-1.5B, Nemotron-3.5-Lightning-30B-A3B; {eps:,} greedy episodes; "
                         f"no paid API or cloud compute."]), 18))
S.append((slide(5, "Looked it up, then paid anyway", image=os.path.join(VF, "headline.png"),
                caption="Counted over distinct post-lookup prompts. Red = paid after seeing the mismatch (bad); "
                        "navy = stopped. The state check's 0 follows from its design."), 20))
S.append((slide(6, "Baseline by design:", "with only the message, every model paid.",
                big=(f("TRUST_ALL|bad_charge"), "false reports paid for, three models, trust condition"),
                take="in our setting, acting on a peer's “done” alone gave no protection."), 12))
S.append((slide(7, "Qwen2.5-1.5B looked it up and still paid;", "Nemotron-30B-A3B stopped.",
                image=os.path.join(RES, "fig1.png"),
                caption=f"Qwen2.5-1.5B looked in {f(f'{Q15}|tool|w2_checked')} tool episodes and paid after the mismatch "
                        f"in {c(f'{Q15}|tool|checked_then_charged')}. Nemotron paid after a mismatch in "
                        f"{f(f'{NEM}|tool|checked_then_charged')}."), 18))
S.append((slide(8, "In the log: CHECK → NOT FOUND → PROCEED",
                bullets=[w2a["prompt"].split("\n")[0],
                         "W1:  " + w1["message"].split(", reservation")[0] + " …",
                         "W2:  " + w2a["completion"],
                         "DB:  " + w2b["result"],
                         "W2:  " + w2b["completion"] + "  → customer charged"], mono=True,
                caption="Verbatim from log_Qwen2.5-1.5B-Instruct.jsonl (condition tool, fault missing, seed 0).",
                take="count checks that changed the decision; a CHECK in the log is not a stop."), 18))
S.append((slide(9, "Is it one prompt? We changed only the post-lookup prompt.",
                "Wrong quantity: paid under all four wordings.",
                bullets=[f"Qwen2.5-1.5B paid after seeing a wrong quantity in {f(f'DISTALL|{Q15}|wrong_qty|still_paid')} "
                         f"distinct prompts (fresh, multi-turn, two paraphrases); {f(D('multiturn', Q15, 'wrong_qty'))} "
                         f"with its own CHECK turn kept.",
                         f"After seeing NOT FOUND: {f(D('fresh', Q15, 'missing'))} with the main prompt, "
                         f"{f(f'DIST3|{Q15}|missing|still_paid')} with the other three wordings.",
                         f"Nemotron never paid after a mismatch ({f(f'DISTALL|{NEM}|all|still_paid')}), but with paraphrase 2 "
                         f"it halted {f(f'DIST|para2|{NEM}|false_halt')} honest orders."],
                take="test the check on subtle mismatches (a wrong number), not only obvious ones."), 22))
if HAS_SUB:
    def sb(m, fl):
        return f"{f(f'SUB|fresh|{m}|{fl}|still_paid')} / {f(f'SUB|multiturn|{m}|{fl}|still_paid')}"
    leaks = N[f"SUBALL|{NEM}|still_paid"]["k"] > 0
    S.append((slide(10, "Subtler mismatches (fresh / multi-turn prompt)",
                    "Nemotron also paid." if leaks else "Nemotron still stopped; Qwen2.5-1.5B still paid.",
                    bullets=[f"Quantity off by one — Nemotron {sb(NEM, 'qty_off1')}; Qwen2.5-1.5B {sb(Q15, 'qty_off1')}",
                             f"Wrong product — Nemotron {sb(NEM, 'wrong_item')}; Qwen2.5-1.5B {sb(Q15, 'wrong_item')}",
                             f"Wrong delivery date — Nemotron {sb(NEM, 'wrong_date')}; Qwen2.5-1.5B {sb(Q15, 'wrong_date')}",
                             "Counts: paid after looking and seeing the mismatch."]), 18))
S.append((slide(11, "Time pressure and a cover story", "did not stop Nemotron from checking.",
                 bullets=[f"Busy note: Nemotron still looked in {f(f'{NEM}|tool_busy|w2_checked')} episodes; "
                          f"Qwen2.5-1.5B in {f(f'{Q15}|tool_busy|w2_checked')}.",
                          f"Cover story (“the replica can lag”): Nemotron looked in {f(f'EXC|{NEM}|tool|w2_checked')} "
                          f"and paid in {f(f'EXC|{NEM}|tool|bad_charge')}.",
                          f"Qwen2.5-1.5B: its {f(f'{Q15}|tool|missing|stopped')} stops on a missing row dropped to "
                          f"{f(f'EXC|{Q15}|tool|stopped')} with the excuse."],
                 take="a one-sentence excuse removed Qwen2.5-1.5B's remaining stops; test excuses as a separate fault."), 18))
S.append((slide(12, "A non-LLM state check stopped every false report,", "without extra model calls.",
                 big=(f("GATE_ALL|bad_charge"), f"bad payments with the state check, all three models (by design); "
                                                  f"step repaired in {f('GATE_ALL|gate_fixed')}"), bigcol=NAVY,
                 take="where a claim can be compared with a record, compare it in code first."), 14))
S.append((slide(13, "Limits", bullets=[
    "Toy task, one-word answers, greedy decoding; seeds vary the order, not sampling.",
    "Two small models and one 30B-A3B mixture-of-experts model in 4-bit; no frontier model.",
    "The first worker is scripted; the state check's redo is honest by construction.",
    "Robustness covers one multi-turn version and two paraphrases only."]), 14))
S.append((slide(14, "Takeaway", "Audit whether agents act on their checks.", bullets=[
    "Not only whether they check: a CHECK in the log is not a stop.",
    "Put a cheap non-LLM state check at hand-offs where the truth can be queried.",
    "Code and full JSONL logs: github.com/jejuolledev/swarm-false-done"]), 14))

# ---- encode: each slide as a still, short crossfades avoided (plain cuts)
lst = os.path.join(SL, "list.txt")
with open(lst, "w") as fh:
    for p, sec in S:
        fh.write(f"file '{os.path.abspath(p)}'\nduration {sec}\n")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                "-vf", "scale=1920:1080,format=yuv420p,fps=30", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-movflags", "+faststart", OUT], check=True)
print("total seconds", sum(s for _, s in S), "slides", len(S))
