#!/bin/zsh
# Main experiment, 2026-11-08. Models run one after another (never two at once).
set -e
cd "${0:A:h}"
OUT=runs/main_1108
C=trust,tool,tool_busy,shown,gate
export HF_HUB_OFFLINE=1
${MLX_PYTHON:-python3} -I harness.py --backend mlx --model mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit --seeds 30 --conds $C --out $OUT > $OUT.nemo.out 2>&1
.venv/bin/python -I harness.py --model Qwen/Qwen2.5-0.5B-Instruct --seeds 30 --conds $C --out $OUT > $OUT.q05.out 2>&1
.venv/bin/python -I harness.py --model Qwen/Qwen2.5-1.5B-Instruct --seeds 30 --conds $C --out $OUT > $OUT.q15.out 2>&1
echo ALLDONE > $OUT.done
