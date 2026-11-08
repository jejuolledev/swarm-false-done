"""Check the narration audio against the script with local speech-to-text (faster-whisper base.en, CPU).
Compares normalised words and every number. Usage: .venv/bin/python -I stt_check.py results
"""
import difflib, json, os, re, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

RES = sys.argv[1]
script = {x["slide"]: x["text"] for x in json.load(open(os.path.join(RES, "narration.json")))}
TRIM = os.path.join(RES, "narration_audio", "trimmed")
model = WhisperModel("Systran/faster-whisper-base.en", device="cpu", compute_type="int8")

UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}


def norm(t):
    t = t.lower().replace(",", "").replace("-", " ")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return [w for w in t.split() if w]


def nums(t):
    """Digits, plus number words a recogniser may write out (zero..nine)."""
    t = t.replace(",", "")
    out = [int(x) for x in re.findall(r"\d+", t)]
    out += [UNITS[w] for w in re.findall(r"[a-z]+", t.lower()) if w in UNITS]
    return out


report, all_ok = [], True
for s in sorted(script):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(TRIM, f"s{s:02d}.wav"), "-f", "s16le",
                          "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    seg, _ = model.transcribe(audio, language="en", beam_size=5)
    heard = " ".join(x.text.strip() for x in seg)
    a, b = norm(script[s]), norm(heard)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    na, nb = nums(script[s]), nums(heard)
    num_ok = all(n in nb for n in na)
    ok = ratio >= 0.85 and num_ok   # names (Bae, Nemotron, jejuolledev) are often spelled differently by STT
    all_ok &= ok
    report.append({"slide": s, "word_match": round(ratio, 3), "numbers_script": na, "numbers_heard": nb,
                   "numbers_ok": num_ok, "heard": heard})
json.dump(report, open(os.path.join(RES, "narration_stt.json"), "w"), indent=1, ensure_ascii=False)
for r in report:
    print(r["slide"], r["word_match"], "numbers ok" if r["numbers_ok"] else f"NUMBERS {r['numbers_script']} vs {r['numbers_heard']}")
print("ALL OK" if all_ok else "CHECK FAILED")
