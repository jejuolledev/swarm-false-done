#!/bin/zsh
# Robustness run, 2026-11-09: post-lookup prompt variants (multiturn, para1, para2) in tool and tool_busy.
# "fresh" is the main run (runs/main_1108). One model at a time.
set -e
cd "${0:A:h}"
export HF_HUB_OFFLINE=1
C=tool,tool_busy
for V in multiturn para1 para2; do
  OUT=runs/robust_1109/$V; mkdir -p $OUT
  ${MLX_PYTHON:-python3} -I harness.py --backend mlx --model mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit --seeds 30 --conds $C --variant $V --out $OUT > $OUT.nemo.out 2>&1
done
for V in multiturn para1 para2; do
  OUT=runs/robust_1109/$V
  .venv/bin/python -I harness.py --model Qwen/Qwen2.5-0.5B-Instruct --seeds 30 --conds $C --variant $V --out $OUT > $OUT.q05.out 2>&1
done
for V in multiturn para1 para2; do
  OUT=runs/robust_1109/$V
  .venv/bin/python -I harness.py --model Qwen/Qwen2.5-1.5B-Instruct --seeds 30 --conds $C --variant $V --out $OUT > $OUT.q15.out 2>&1
done
echo ALLDONE > runs/robust_1109.done
