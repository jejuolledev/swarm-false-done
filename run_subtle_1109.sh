#!/bin/zsh
# Subtle-mismatch run, 2026-11-09: orders carry a delivery date; faults none, qty_off1, wrong_item, wrong_date;
# condition tool; post-lookup prompt fresh and multiturn. One model at a time.
set -e
cd "${0:A:h}"
export HF_HUB_OFFLINE=1
F=none,qty_off1,wrong_item,wrong_date
for V in fresh multiturn; do
  OUT=runs/subtle_1109/$V; mkdir -p $OUT
  ${MLX_PYTHON:-python3} -I harness.py --backend mlx --model mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit --seeds 30 --conds tool --faults $F --with-date --variant $V --out $OUT > $OUT.nemo.out 2>&1
done
for V in fresh multiturn; do
  OUT=runs/subtle_1109/$V
  .venv/bin/python -I harness.py --model Qwen/Qwen2.5-1.5B-Instruct --seeds 30 --conds tool --faults $F --with-date --variant $V --out $OUT > $OUT.q15.out 2>&1
done
echo ALLDONE > runs/subtle_1109.done
