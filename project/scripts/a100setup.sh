#!/bin/bash
# ============================================================================
# 文件作用：在 A100 训练服务器上搭建 LeRobot 训练环境（CUDA 版 PyTorch + 固定版本 LeRobot）。
#
# 主要内容：
#   1. 安装 Miniforge（若未安装）并创建 Python 3.10 的 lerobot conda 环境；
#   2. 安装 ffmpeg（LeRobot 数据集视频编码依赖）；
#   3. 克隆 HuggingFace LeRobot 仓库并固定到 v0.4.4；
#   4. 安装 feetech 舵机依赖；
#   5. 按 nvidia-smi 显示的 CUDA 版本安装匹配的 PyTorch（脚本默认 cu121，需人工确认）。
#
# 用法（在 A100 上执行）：
#   bash ~/a100setup.sh
#
# 注意：
#   - 若服务器已存在 miniforge/conda，可跳过第 1 步，直接创建环境。
#   - PyTorch 的 CUDA index 必须与驱动匹配：cu118/cu121/cu124 选一个。
# ============================================================================

# 任一命令失败立即退出
set -e

# 1. 安装 Miniforge（仅当 conda 不存在时）
if ! command -v conda >/dev/null 2>&1; then
  wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
  bash Miniforge3-Linux-x86_64.sh -b
  source ~/.bashrc
fi

# 2. 创建并激活 Python 3.10 环境（重复运行前先 conda env remove -n lerobot 再重建）
conda create -y -n lerobot python=3.10
conda activate lerobot

# 3. ffmpeg：LeRobot 录制/回放视频必需
conda install -y -c conda-forge ffmpeg

# 4. 克隆 LeRobot 并固定版本（与 Pi 5 保持一致）
if [ ! -d "$HOME/lerobot" ]; then
  git clone https://github.com/huggingface/lerobot.git "$HOME/lerobot"
fi
cd "$HOME/lerobot"
git checkout v0.4.4

# 5. 安装 feetech 舵机依赖（-e 可编辑模式便于调试源码）
pip install -e ".[feetech]"

# 6. 安装 CUDA 版 PyTorch。
#    重要：先运行 nvidia-smi 查看驱动支持的 CUDA 版本，再选择 cu118/cu121/cu124。
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 7. 验证 CUDA 可用；输出必须为 True，否则训练时无法使用 GPU
python -c "import torch; print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available())"
