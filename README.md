# Looking It Up Is Not Stopping

Code and full logs for the Apart Research **Swarm Alignment Sprint 2026** report
*"Looking It Up Is Not Stopping: Measuring When Pipeline Agents Act on a Peer's False 'Done'"*
(Jungkil Bae, MoaHub). The report PDF is in `report/`.

A three-worker pipeline (reserve -> charge -> ship) runs on a fake in-memory SQLite database.
The first worker is a script that can plant a false "DONE" report (missing row, wrong quantity,
missing row plus a cover story). The two downstream workers are LLMs. We measure how often they
act on the false report under five conditions (`trust`, `tool`, `tool_busy`, `shown`, `gate`) and,
separately, how often they look the reservation up and still proceed after seeing a mismatch.

All data are synthetic. All code was written during the sprint (November 7-9, 2026, Korea time,
inside the November 6-8 Anywhere-on-Earth window). Nothing here calls a paid API.

## Files

| Path | What it is |
|---|---|
| `harness.py` | The pipeline, faults, conditions, backends (transformers CPU, MLX Apple GPU). Logs every prompt, completion and DB read as JSONL. |
| `run_main_1108.sh`, `run_excuse_1108.sh`, `run_robust_1109.sh`, `run_subtle_1109.sh` | The four experiment runs (one model at a time). |
| `analyze.py`, `figures.py` | Compute every number, figure and table from the logs -> `results/`. `make_video.py` builds the silent presentation video from them. |
| `build_report.py`, `docbuild.py` | Fill the official Apart report template (docx) with the text and numbers from `results/numbers.json`. |
| `check_report.py` | Checks that every count in the PDF matches `numbers.json`, section order, abstract length, page budget. |
| `runs/` | Raw logs: `log_*.jsonl` (every call) and `results_*.jsonl` (one line per episode). `pilot_1107` is the 72-episode pilot. |
| `results/` | Regenerated outputs (numbers.json, fig1.png, tables). |

## Reproduce

Needs Python 3.12 or newer.

```bash
python3 -m venv .venv
# analysis only (re-count every number and redraw the figures from the shipped logs; no model download)
.venv/bin/pip install matplotlib==3.11.2
.venv/bin/python -I analyze.py runs/main_1108 results runs/excuse_1108 runs/robust_1109 runs/subtle_1109
.venv/bin/python -I figures.py results runs/main_1108
# full install (to re-run episodes and rebuild the PDF)
.venv/bin/pip install -r requirements.txt
# re-run episodes, e.g. one model and condition set
HF_HUB_OFFLINE=0 .venv/bin/python -I harness.py --model Qwen/Qwen2.5-1.5B-Instruct --seeds 30 \
    --conds trust,tool,tool_busy,shown,gate --out runs/my_run
# Nemotron on Apple silicon (needs mlx-lm 0.31.3)
python -I harness.py --backend mlx --model mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit --seeds 30 --out runs/my_run
```

Decoding is greedy, so an episode is determined by (model, condition, fault, seed, prompt variant).
In the fresh and paraphrase variants the post-lookup prompt is the same in `tool` and `tool_busy`, so the report
counts each distinct post-lookup prompt once (`DIST|...` keys in `results/numbers.json`).
The run scripts use `.venv/bin/python` for the CPU runs and `$MLX_PYTHON` (default `python3`) for the Nemotron runs.
Building the PDF needs the official template from the sprint's Guidelines tab (set `SWARM_TEMPLATE=/path/to/template.docx`) and LibreOffice; `./reproduce.sh` does the rest.

## License

MIT (code). Model weights are under their own licenses (Qwen2.5: Apache-2.0; Nemotron: see its model card).
