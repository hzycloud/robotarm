#!/bin/bash
# ============================================================================
# 文件作用：按顺序运行完整实验矩阵，产出各配置的 results_*.csv。
#
# 实验矩阵：
#   1. teacher_gpu          —— 教师 ACT（A100 直连机械臂或 Pi 5 跑 PyTorch）
#   2. tinyact_fp32         —— 学生 FP32（Pi 5）
#   3. tinyact_int8         —— 学生 INT8（Pi 5，benchmark_onnx 部署）
#   4. closed_loop_int8     —— 闭环 int8（closed_loop_sort.py，含验证器+重试）
#   5. tinyact_int8_singlecam —— 单相机变体（只保留 front，消融）
#
# 用法（在 Pi 5 上执行，逐个配置运行）：
#   bash ~/run_experiments.sh
#
## 说明：本脚本只负责编排与提示，具体每个配置的执行命令见各步骤注释；
##       机械臂实验需人工监督，禁止无人值守运行。
# ============================================================================

set -e

# 1. teacher_gpu：在 A100 上直连机械臂跑教师模型（见 eval_rollout.sh，改 --policy.path）
echo "STEP 1/5: teacher_gpu —— 在 A100 上运行，记录到 results_teacher_gpu.csv"
echo "  参考：bash eval_rollout.sh（修改 --policy.path 指向 ACT 教师 checkpoint）"

# 2. tinyact_fp32：Pi 5 上 PyTorch 跑学生模型
echo "STEP 2/5: tinyact_fp32 —— Pi 5 上 PyTorch 学生模型 rollout"

# 3. tinyact_int8：Pi 5 上 ONNX int8 学生模型
echo "STEP 3/5: tinyact_int8 —— Pi 5 上 ONNX int8 学生模型 rollout"

# 4. closed_loop_int8：闭环主程序（验证器 + 重试）
echo "STEP 4/5: closed_loop_int8 —— 运行 closed_loop_sort.py"
python closed_loop_sort.py \
  --policy tinyact_int8.onnx --verifier verifier.onnx \
  --trials 30 --max_retries 2 --out results_closed_loop_int8.csv

# 5. 单相机消融：临时用单相机配置运行（同 STEP 3，但 cameras.json 只留 front）
echo "STEP 5/5: tinyact_int8_singlecam —— 临时单相机配置 rollout"
