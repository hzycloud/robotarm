#!/bin/bash
# ============================================================================
# 文件作用：在 Pi 5 上通过主从臂遥操作录制演示数据（双相机 + 关节角度 + 夹爪）。
#
# 主要内容：
#   1. 从 cameras.json 读取相机配置；
#   2. 调用 lerobot-record 录制到 ${HF_USER}/so101_sort；
#   3. 键盘控制：→ 结束当前 episode，← 重录，ESC 退出。
#
# 用法（在 Pi 5 上执行）：
#   export HF_USER=<你的HuggingFace用户名>
#   bash ~/record_so101.sh
#
# 注意：
#   - 正式采集时 display_data=false，避免 rerun 渲染拖慢帧率；
#   - num_episodes 是"目标条数"，可改成当天采集量（如 30）。
# ============================================================================

# 任一命令失败立即退出
set -e

# 1. 进入 LeRobot 环境并校验 HF_USER
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}

# 2. 读取相机配置（与遥操作脚本同一来源）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAM=$(python -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" \
  "$SCRIPT_DIR/../configs/cameras.json")

# 3. 录制演示数据到标准 repo_id
lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm \
  --robot.cameras="$CAM" \
  --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=my_awesome_leader_arm \
  --display_data=false \
  --dataset.repo_id="${HF_USER}/so101_sort" \
  --dataset.num_episodes=5 \
  --dataset.single_task="Pick up the object and place it into the correct sorting slot"
