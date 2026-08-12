#!/bin/bash
# ============================================================================
# 文件作用：在 A100 上训练 TinyACT 学生模型（缩容版 ACT：更少的注意力头/层数、更小的隐层维度）。
#
# 主要内容：
#   1. 读取 HF_USER 并组装数据集 repo_id=${HF_USER}/so101_sort；
#   2. 调用 lerobot-train 以 ACT 策略训练学生模型；
#   3. 通过 --policy.n_heads/n_layers/dim_model/dim_feedforward 缩小模型规模；
#   4. 输出目录统一为 outputs/train/tinyact_so101_sort，便于后续蒸馏/量化复用。
#
# 用法（在 A100 上执行）：
#   export HF_USER=<你的HuggingFace用户名>
#   bash ~/train_tinyact.sh
#
# 注意：
#   - 若 --policy.n_heads 等参数在当前 LeRobot 版本不存在，先运行
#     lerobot-train --policy.type=act --help | grep -i "n_heads\|n_layers\|dim_model"
#     获取实际参数名后回填。
#   - 冒烟测试：临时追加 --policy.num_steps=200 跑通后再正式训练。
# ============================================================================

# 任一命令失败立即退出
set -e

# 1. 进入 LeRobot 训练环境
conda activate lerobot

# 2. HF_USER 必填，缺失直接报错
export HF_USER=${HF_USER:?set HF_USER first}

# 3. 训练 TinyACT 学生：batch_size 比教师更大（模型更小，显存占用更低）
lerobot-train \
  --dataset.repo_id="${HF_USER}/so101_sort" \
  --policy.type=act \
  --output_dir=outputs/train/tinyact_so101_sort \
  --policy.device=cuda \
  --policy.batch_size=16 \
  --policy.push_to_hub=false \
  --wandb.enable=false \
  --policy.n_heads=4 \
  --policy.n_layers=3 \
  --policy.dim_model=256 \
  --policy.dim_feedforward=1024
