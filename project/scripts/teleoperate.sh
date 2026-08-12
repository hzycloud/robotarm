#!/bin/bash
# ============================================================================
# 文件作用：在 Pi 5 上启动 SO-ARM101 主从臂遥操作（leader 示教 → follower 跟随），
#           并挂载双相机（front 外部 200W + wrist 腕部 30W）实时显示画面。
#
# 主要内容：
#   1. 读取 project/configs/cameras.json 相机配置（由 Task 4 生成）；
#   2. 调用 lerobot-teleoperate 启动主从联动；
#   3. --display_data=true 用于确认相机视野，正式采集时改为 false（见 record_so101.sh）。
#
# 前置条件（由 Task 3-5 完成）：
#   - Pi 5 已装 miniforge 的 lerobot 环境（Python 3.10）；
#   - follower 与 leader 均已校准，端口通常为 /dev/ttyACM0 与 /dev/ttyACM1；
#   - 已执行 sudo chmod 666 /dev/ttyACM0 /dev/ttyACM1（或已加入 dialout 组）。
#
# 用法（在 Pi 5 上执行）：
#   export HF_USER=<你的HuggingFace用户名>
#   bash ~/teleoperate.sh
# ============================================================================

# 任一命令失败立即退出，避免在损坏环境下继续运行
set -e

# 1. 进入 LeRobot 专用 conda 环境（Task 3 创建）
conda activate lerobot

# 2. 检查 HF_USER 是否已设置；未设置直接报错，避免 repo_id 变成非法路径
export HF_USER=${HF_USER:?set HF_USER first}

# 3. 用 Python 读取相机配置并压缩成单行 JSON。
#    相比手写 JSON 字符串，这样保证与 cameras.json 永远一致，且无需手工转义引号。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAM=$(python -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" \
  "$SCRIPT_DIR/../configs/cameras.json")

# 4. 启动遥操作：follower 接 /dev/ttyACM0，leader 接 /dev/ttyACM1。
#    --robot.id / --teleop.id 必须与校准、录制时保持一致（默认 my_awesome_*_arm）。
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm \
  --robot.cameras="$CAM" \
  --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=my_awesome_leader_arm \
  --display_data=true
