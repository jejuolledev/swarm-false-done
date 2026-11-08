"""Generate narration audio per slide with ElevenLabs TTS.
The API key is read from the environment variable XI_KEY (set by the caller from a .env file); it is never printed.

Usage: XI_KEY=... .venv/bin/python -I tts.py results/narration.json results/narration_audio VOICE_ID
"""
import hashlib, json, os, sys, urllib.request, urllib.error

SRC, OUT, VOICE = sys.argv[1], sys.argv[2], sys.argv[3]
MODEL = os.environ.get("XI_MODEL", "eleven_multilingual_v2")
KEY = os.environ["XI_KEY"]
os.makedirs(OUT, exist_ok=True)
items = json.load(open(SRC))
total_chars = 0
mapping = {}
for it in items:
    text = it["text"]
    h = hashlib.sha1((VOICE + MODEL + text).encode()).hexdigest()[:10]
    path = os.path.join(OUT, f"s{it['slide']:02d}_{h}.mp3")
    mapping[str(it["slide"])] = path
    if os.path.exists(path):
        print("cached", os.path.basename(path)); continue
    body = json.dumps({"text": text, "model_id": MODEL,
                       "voice_settings": {"stability": 0.55, "similarity_boost": 0.75, "style": 0.0,
                                          "use_speaker_boost": True}}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
                                 body, {"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read()[:300].decode("utf8", "replace")); sys.exit(1)
    open(path, "wb").write(data)
    total_chars += len(text)
    print("made", os.path.basename(path), len(data), "bytes", len(text), "chars")
json.dump(mapping, open(os.path.join(OUT, "map.json"), "w"), indent=1)
print("characters sent this run:", total_chars, "| characters in script:", sum(len(i["text"]) for i in items))
