"""Table: per model x condition x fault -> rates. Usage: python summarize.py runs/pilot"""
import glob, json, sys
from collections import defaultdict

rows = [json.loads(l) for p in glob.glob(sys.argv[1] + "/results_*.jsonl") for l in open(p)]
g = defaultdict(list)
for r in rows:
    g[(r["model"].split("/")[-1], r["cond"], r["fault"])].append(r)
hdr = "| model | cond | fault | n | bad_charge | bad_ship | false_halt | W2 checked | gate fixed | unparsed | sec/ep |"
print(hdr); print("|" + "---|" * hdr.count("|")[:-1] if False else "|---|---|---|---|---|---|---|---|---|---|---|")
for k in sorted(g):
    rs = g[k]; n = len(rs)
    f = lambda key: sum(bool(r[key]) for r in rs)
    print(f"| {k[0]} | {k[1]} | {k[2]} | {n} | {f('bad_charge')}/{n} | {f('bad_ship')}/{n} | "
          f"{f('false_halt')}/{n} | {f('w2_checked')}/{n} | {f('gate_fixed')}/{n} | "
          f"{sum(r['unparsed'] for r in rs)} | {sum(r['secs'] for r in rs)/n:.1f} |")
