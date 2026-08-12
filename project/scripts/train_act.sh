#!/bin/bash
# ============================================================================
# 文件作用：在 A100 上训练 ACT 教师策略（基线模型），供蒸馏与对比实验使用。
#
# 主要内容：
#   1. 读取 HF_USER 并组装 repo_id=${HF_USER}/so101_sort；
#   2. 调用 lerobot-train 训练标准 ACT（默认 ResNet18 骨干）；
#   3. 输出目录 outputs/train/act_so101_sort。
#
# 用法（在 A100 上执行）：
#   export HF_USER=<你的HuggingFace用户名>
#   bash ~/train_act.sh
#
# 提示：先加 --policy.num_steps=200 冒烟，再正式训练（50k-100k steps，约 2-7 小时）。
# ============================================================================

# 任一命令失败立即退出
set -e

# 1. 进入训练环境
conda activate lerobot

# 2. HF_USER 必填
export HF_USER=${HF_USER:?set HF_USER first}

# 3. 训练 ACT 教师
lerobot-train \
  --dataset.repo_id="${HF_USER}/so101_sort" \
  --policy.type=act \
  --output_dir=outputs/train/act_so101_sort \
  --policy.device=cuda \
  --policy.batch_size=8 \
  --policy.push_to_hub=false \
  --wandb.enable=false
