"""Independent checks on the built PDF: numbers vs numbers.json (which comes from the logs),
section order, abstract length, page budget. Exit code 1 on any failure.

Usage: .venv/bin/python -I check_report.py results_dir
"""
import json, os, re, sys
import pymupdf

RES = sys.argv[1]
N = json.load(open(os.path.join(RES, "numbers.json")))
doc = pymupdf.open(os.path.join(RES, "report.pdf"))
pages = [p.get_text() for p in doc]
text = re.sub(r"\s+", " ", " ".join(pages))
fail = []

# 1. every "k/n" in the text must be a count produced by analyze.py (or a summed pair of them)
counts = {(d["k"], d["n"]) for d in N.values() if isinstance(d, dict) and "k" in d}
ks = [d for d in N.values() if isinstance(d, dict) and "k" in d]
summed = set(counts)
# sums used in prose: over models for one metric/cond, or over tool+tool_busy for one model/metric
keys = [k for k, d in N.items() if isinstance(d, dict) and "k" in d]
by = {}
for k in keys:
    parts = k.split("|")
    if len(parts) == 3:
        m, c, met = parts
        by.setdefault(("cond", c, met), []).append(N[k])
        if c in ("tool", "tool_busy"):
            by.setdefault(("model", m, met), []).append(N[k])
    if len(parts) == 4 and parts[0] == "EXC":
        by.setdefault(("exc", parts[2], parts[3]), []).append(N[k])
for v in by.values():
    summed.add((sum(x["k"] for x in v), sum(x["n"] for x in v)))
ALLOWED_OTHER = {"11/7", "11/8"}  # dates in the Code and Data section
for m in re.finditer(r"(?<![\w/.])(\d+)/(\d+)(?![\w/])", text):
    s = m.group(0)
    if s in ALLOWED_OTHER:
        continue
    if (int(m.group(1)), int(m.group(2))) not in summed:
        fail.append(f"count {s} not derivable from numbers.json: ...{text[max(0, m.start()-60):m.end()+20]}...")

# 2. every "p% (95% CI lo–hi%)" must match a numbers.json entry
for m in re.finditer(r"(\d+)/(\d+) \((\d+)%, 95% CI (\d+)–(\d+)%\)", text):
    k, n, p, lo, hi = map(int, m.groups())
    ok = any(d["k"] == k and d["n"] == n and round(d["pct"]) == p and round(d["lo"]) == lo and round(d["hi"]) == hi
             for d in ks)
    if not ok:
        fail.append(f"CI mismatch: {m.group(0)}")

# 3. section order (official template)
order = ["Abstract", "1. Introduction", "2. Related Work", "3. Methods", "4. Results", "5. Discussion and Limitations",
         "6. Conclusion", "Code and Data", "References", "Appendix", "Limitations and Dual-Use", "LLM Usage Statement"]
pos, at = [], 0
for h in order:  # each heading must appear after the previous one (headings are searched in sequence)
    at = text.find(h, at); pos.append(at)
    if at == -1:
        break
if -1 in pos:
    fail.append(f"section order wrong: {list(zip(order, pos))}")

# 4. abstract length 150-250 words
a = text[text.find("Abstract") + 8: text.find("Figure 1.")]
wc = len(a.split())
if not 150 <= wc <= 250:
    fail.append(f"abstract has {wc} words")

# 5. page budget: pages up to (not incl.) References, excluding the title/abstract page
ref_page = next(i for i, p in enumerate(pages) if "\nReferences\n" in "\n" + p)
body_pages = ref_page  # pages 2..ref_page (title page is page 1)
if body_pages > 8:
    fail.append(f"body is {body_pages} pages (> 8)")

# 5b. pooled counts that double-count identical post-lookup prompts must not appear (QA2, 2026-11-09)
for bad in ("112/120", "232/240", "0/360", "44/60", "52/60"):
    if re.search(r"(?<![\d/])" + re.escape(bad) + r"(?![\d])", text):
        fail.append(f"double-counted figure in text: {bad}")

# 6. no leftover template guidance
for g in ("Summarize your project", "[Reference 1]", "How to use this template", "Author name", "[First contribution"):
    if g in text:
        fail.append(f"template guidance left: {g}")

print(json.dumps({"pages_total": len(pages), "body_pages_through_page_before_refs": body_pages,
                  "abstract_words": wc, "fractions_checked": len(re.findall(r"\d+/\d+", text)),
                  "failures": fail}, indent=1, ensure_ascii=False))
sys.exit(1 if fail else 0)
