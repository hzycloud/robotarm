#!/bin/bash
# ============================================================================
# 文件作用：在 Pi 5 上运行已训练策略的自主 rollout（无人工干预），用于统计成功率。
#
# 主要内容：
#   1. 读取相机配置；
#   2. 用 lerobot-record 以 --policy.path 加载模型并自主执行；
#   3. 结果录制为 eval_ 数据集，人工逐条判定成功/失败。
#
# 用法（在 Pi 5 上执行）：
#   export HF_USER=<你的HuggingFace用户名>
#   bash ~/eval_rollout.sh
#
# 注意：
#   - --policy.path 必须指向含 pretrained_model 的完整目录（带预处理配置）；
#   - 每次评估前用 lerobot-find-port / lerobot-find-cameras 确认端口与相机 index。
# ============================================================================

# 任一命令失败立即退出
set -e

# 1. 进入环境并校验 HF_USER
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}

# 2. 读取相机配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAM=$(python -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" \
  "$SCRIPT_DIR/../configs/cameras.json")

# 3. 自主 rollout 10 条（模型路径按实际位置修改）
lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm \
  --robot.cameras="$CAM" \
  --dataset.repo_id="${HF_USER}/eval_act_baseline" \
  --dataset.num_episodes=10 \
  --dataset.push_to_hub=false \
  --dataset.single_task="Pick up the object and place it into the correct sorting slot" \
  --display_data=false \
  --policy.path="$HOME/act_model/pretrained_model"
