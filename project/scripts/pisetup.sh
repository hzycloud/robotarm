#!/bin/bash
# ============================================================================
# 文件作用：在 Raspberry Pi 5 上安装 LeRobot 固定版本 v0.4.4 的一键安装脚本。
#
# 主要内容：
#   1. 激活 miniforge 的 lerobot 环境（Python 3.10）
#   2. 克隆 HuggingFace LeRobot 仓库并切换到固定版本 v0.4.4
#   3. 以可编辑模式安装（含 feetech 舵机依赖）
#   4. 打印实际安装的 LeRobot 版本，供执行者回填到 project/README.md
#
# 前置条件（由 Task 3 完成）：
#   - Pi 5 已刷 Raspberry Pi OS 64-bit 并启用 SSH
#   - 已安装 Miniforge 并创建 lerobot 环境（conda create -n lerobot python=3.10）
#
# 用法（在 Pi 5 上执行）：
#   bash ~/pisetup.sh
#
# 若安装失败或版本冲突，以 HiWonder 官方文档为准：
#   docs.hiwonder.com/projects/LeRobot
# ============================================================================

# 非交互式 shell 不会加载 ~/.bashrc，conda 的 activate 函数不可用，
# 需要显式导入 conda 的 profile 脚本后才能执行 conda activate。
source "$HOME/miniforge3/etc/profile.d/conda.sh"

# 任一命令失败立即退出，避免在损坏的环境中继续安装
set -e

# 1. 进入 LeRobot 专用 conda 环境（由 Task 3 创建，Python 3.10）
conda activate lerobot

# 2. 克隆 LeRobot 官方仓库；已存在则跳过，避免重复下载
if [ ! -d "$HOME/lerobot" ]; then
  git clone https://github.com/huggingface/lerobot.git "$HOME/lerobot"
fi
cd "$HOME/lerobot"

# 先拉取远程 tags：本地克隆可能缺少 v0.4.4 等 tag（例如克隆早于 tag 创建），
# 直接 git checkout 会报 pathspec 不匹配错误。
git fetch --tags

# 3. 切换到与 HiWonder SO-ARM101 官方文档配套的固定版本 v0.4.4
git checkout v0.4.4

# 4. 可编辑安装：-e 便于后续调试源码；[feetech] 安装 STS3215 总线舵机依赖
pip install -e ".[feetech]"

# 5. 打印实际安装的版本号。执行者需把输出回填到 project/README.md 的
#    "LeRobot 版本" 一栏；若与 v0.4.4 不同，以 HiWonder 官方文档推荐版本为准
pip show lerobot | grep -E "^(Name|Version):"
