#!/bin/zsh
# Supplementary run, 2026-11-08: false report + cover story (missing_excuse). One model at a time.
set -e
cd "${0:A:h}"
OUT=runs/excuse_1108
mkdir -p $OUT
C=trust,tool,tool_busy,shown,gate
export HF_HUB_OFFLINE=1
${MLX_PYTHON:-python3} -I harness.py --backend mlx --model mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit --seeds 30 --conds $C --faults missing_excuse --out $OUT > $OUT.nemo.out 2>&1
.venv/bin/python -I harness.py --model Qwen/Qwen2.5-0.5B-Instruct --seeds 30 --conds $C --faults missing_excuse --out $OUT > $OUT.q05.out 2>&1
.venv/bin/python -I harness.py --model Qwen/Qwen2.5-1.5B-Instruct --seeds 30 --conds $C --faults missing_excuse --out $OUT > $OUT.q15.out 2>&1
echo ALLDONE > $OUT.done
