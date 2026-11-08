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
VF = os.path.join(RES, "video_figs")
NAVY, ORANGE, GRAY, BG = "#1F2A44", "#D9541E", "#5B6475", "#FBFAF7"
plt.rcParams["font.family"] = "DejaVu Sans"


def f(key):
    x = N[key]; return f"{x['k']}/{x['n']}"


def c(key):
    x = N[key]; return f"{x['k']}/{x['n']} ({x['pct']:.0f}%, 95% CI {x['lo']:.0f}–{x['hi']:.0f}%)"


def slide(i, title, accent=None, bullets=(), image=None, caption=None, take=None, big=None):
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
        fig.text(0.05, top - 0.02, big[0], fontsize=110, color=ORANGE, fontweight="bold", va="top")
        fig.text(0.05, top - 0.22, big[1], fontsize=26, color=NAVY, va="top")
        top -= 0.32
    y = top
    for b in bullets:
        txt = textwrap.fill(b, 78)
        fig.text(0.07, y, "•", fontsize=27, color=ORANGE, va="top")
        fig.text(0.09, y, txt, fontsize=27, color=NAVY, va="top", linespacing=1.35)
        y -= 0.075 * (txt.count("\n") + 1) + 0.03
    if image:
        img = mpimg.imread(image)
        h, w = img.shape[:2]
        bottom = 0.20 if take else 0.10
        avail_h = (y - 0.02 if bullets else top) - bottom
        aw = min(0.9, avail_h * (w / h) * (10.8 / 19.2))
        ah = aw * (h / w) * (19.2 / 10.8)
        ax = fig.add_axes([0.5 - aw / 2, bottom + (avail_h - ah) / 2, aw, ah]); ax.imshow(img); ax.axis("off")
    if caption:
        fig.text(0.05, 0.155 if take else 0.06, textwrap.fill(caption, 120), fontsize=19, color=GRAY, va="top")
    if take:
        fig.patches.append(matplotlib.patches.FancyBboxPatch((0.05, 0.03), 0.9, 0.075, boxstyle="round,pad=0.005",
                                                             transform=fig.transFigure, fc=NAVY, ec=NAVY))
        fig.text(0.07, 0.067, "What to do:  ", fontsize=24, color="#F29A6B", fontweight="bold", va="center")
        fig.text(0.2, 0.067, take, fontsize=24, color="white", va="center")
    p = os.path.join(SL, f"s{i:02d}.png"); fig.savefig(p, facecolor=BG); plt.close(fig)
    return p


Q15, NEM, Q05 = "Qwen2.5-1.5B", "Nemotron-30B-A3B", "Qwen2.5-0.5B"
eps = N["total_episodes"] + N["exc_total_episodes"] + N["rob_total_episodes"]
S = []  # (path, seconds)
S.append((slide(1, "Looking it up is not stopping",
                "When pipeline agents act on a peer's false “done”",
                bullets=["Jungkil Bae, MoaHub (independent), Gwangju-si, South Korea",
                         "Apart Research · Swarm Alignment Sprint 2026 · Track 4: Multi-Agent Oversight and Control",
                         "Silent walkthrough of the report. All numbers come from the run logs."]), 12))
S.append((slide(2, "Agents hand work to each other with one word: DONE.",
                "What if the DONE is false?",
                bullets=["The next agent pays, ships or merges on the strength of that sentence.",
                         "Records made by agents cannot simply be trusted: METR's investigation of the OpenAI / Hugging Face "
                         "hacking incident reports that roughly 7% of the transcripts it evaluated were spoofed in some places.",
                         "Question: does the next agent check? And when it checks, does it act on what it found?"]), 16))
S.append((slide(3, "A three-step pipeline on a fake database", image=os.path.join(VF, "pipeline.png"),
                caption="W1 is a script and can send a false DONE (missing row, wrong quantity, or a missing row with an excuse). "
                        "W2 pays and W3 ships; both are LLMs. The state gate compares the claim with the database in code."), 16))
S.append((slide(4, "Five conditions, three local models",
                bullets=["trust: the agent sees only the message.",
                         "tool / tool + time pressure: the agent may answer CHECK to read the reservation first.",
                         "shown: the database result is always in the prompt (can the model use evidence at all?).",
                         "gate: a non-LLM state check before the payment step, with one redo.",
                         f"Qwen2.5-0.5B, Qwen2.5-1.5B, Nemotron-3.5-Lightning-30B-A3B; {eps:,} greedy episodes; "
                         f"no paid API or cloud compute."]), 18))
S.append((slide(5, "With only the message,", "every model paid for every false report.",
                big=(f(f"TRUST_ALL|bad_charge"), "false reports paid for, three models, trust condition"),
                take="never let an agent act on a peer's “done” alone when the claim can be checked."), 13))
S.append((slide(6, "The 1.5B model looked it up and still paid;", "the larger model stopped.",
                image=os.path.join(RES, "fig1.png"),
                caption=f"Qwen2.5-1.5B looked in {f(f'{Q15}|tool|w2_checked')} tool episodes and paid after the mismatch in "
                        f"{c(f'{Q15}|tool|checked_then_charged')}. Nemotron paid after a mismatch in "
                        f"{f(f'{NEM}|tool|checked_then_charged')}."), 18))
S.append((slide(7, "In the log: CHECK \u2192 NOT FOUND \u2192 PROCEED", image=os.path.join(VF, "logrun.png"),
                caption="Two real episodes rendered verbatim from log_Qwen2.5-1.5B-Instruct.jsonl (Qwen2.5-1.5B, condition tool, seed 0).",
                take="count checks that changed the decision; a CHECK in the log is not a stop."), 18))
S.append((slide(8, "Headline", image=os.path.join(VF, "headline.png"),
                caption="Orange: episodes in which the agent first looked the reservation up and saw the mismatch. "
                        "The state check reads the database directly, so its 0 follows from the design."), 18))
S.append((slide(9, "Is it one prompt? We changed only the post-lookup prompt.",
                "Wrong quantity: robust. Missing row: wording-dependent.",
                bullets=[f"Qwen2.5-1.5B paid after seeing a wrong quantity in {f(f'ROBALL|{Q15}|wrong_qty|checked_then_charged')} "
                         f"cases across four wordings (fresh, multi-turn, two paraphrases).",
                         f"After seeing NOT FOUND: {f(f'ROB|fresh|{Q15}|pooled|missing|checked_then_charged')} with the main "
                         f"prompt, {f(f'ROB3|{Q15}|missing|checked_then_charged')} with the other three wordings.",
                         f"Nemotron never paid after a mismatch ({f(f'ROB3|{NEM}|checked_then_charged')} in the other wordings), "
                         f"but with paraphrase 2 it halted {f(f'ROB|para2|{NEM}|pooled|false_halt')} honest orders."],
                take="test the check on subtle mismatches (a wrong number), not only obvious ones."), 22))
S.append((slide(10, "Time pressure and a cover story", "did not stop the larger model from checking.",
                 bullets=[f"Busy note: Nemotron still looked in {f(f'{NEM}|tool_busy|w2_checked')} episodes; "
                          f"Qwen2.5-1.5B in {f(f'{Q15}|tool_busy|w2_checked')}.",
                          f"Cover story (“the replica can lag”): Nemotron looked in {f(f'EXC|{NEM}|tool|w2_checked')} "
                          f"and paid in {f(f'EXC|{NEM}|tool|bad_charge')}.",
                          f"Qwen2.5-1.5B with the excuse: {f(f'EXC|{Q15}|tool|bad_charge')} paid in tool "
                          f"(without it: {f(f'{Q15}|tool|missing|bad_charge')})."],
                 take="treat a peer's explanation for contrary evidence as a reason to stop."), 18))
S.append((slide(11, "A non-LLM state check stopped every false report,", "with fewer model calls.",
                 big=(f("GATE_ALL|bad_charge"), f"bad payments with the state check, all three models "
                                                  f"(by design); step repaired in {f('GATE_ALL|gate_fixed')}"),
                 take="where a claim can be compared with a record, compare it in code first."), 15))
S.append((slide(12, "Limits", bullets=[
    "Toy task, one-word answers, greedy decoding; seeds vary the order, not sampling.",
    "Two small models and one 30B-A3B mixture-of-experts model in 4-bit; no frontier model.",
    "The first worker is scripted; the state check's redo is honest by construction.",
    "Robustness covers one multi-turn version and two paraphrases only."]), 15))
S.append((slide(13, "Takeaway", "Audit whether agents act on their checks.", bullets=[
    "Not only whether they check: a CHECK in the log is not a stop.",
    "Put a cheap non-LLM state check at hand-offs where the truth can be queried.",
    "Code and full JSONL logs: github.com/jejuolledev/swarm-false-done"]), 15))

# ---- encode: each slide as a still, short crossfades avoided (plain cuts)
lst = os.path.join(SL, "list.txt")
with open(lst, "w") as fh:
    for p, sec in S:
        fh.write(f"file '{os.path.abspath(p)}'\nduration {sec}\n")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                "-vf", "scale=1920:1080,format=yuv420p,fps=30", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-movflags", "+faststart", OUT], check=True)
print("total seconds", sum(s for _, s in S), "slides", len(S))
