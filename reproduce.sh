#!/bin/zsh
# ./reproduce.sh          -> re-analyse the shipped logs, redraw figures, check numbers
# ./reproduce.sh --rerun  -> re-run all episodes first (one model at a time; set MLX_PYTHON for the Nemotron runs)
set -e
cd "${0:A:h}"
if [[ "$1" == "--rerun" ]]; then ./run_main_1108.sh; ./run_excuse_1108.sh; ./run_robust_1109.sh; ./run_subtle_1109.sh; fi
.venv/bin/python -I analyze.py runs/main_1108 results runs/excuse_1108 runs/robust_1109 runs/subtle_1109
.venv/bin/python -I figures.py results runs/main_1108
# PDF build needs the official Apart template: SWARM_TEMPLATE=/path/to/template.docx
if [[ -n "$SWARM_TEMPLATE" ]]; then
  .venv/bin/python -I build_report.py results results/report.docx
  soffice --headless --norestore --convert-to pdf --outdir results results/report.docx
  .venv/bin/python -I check_report.py results
fi
