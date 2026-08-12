#!/bin/bash
# ============================================================================
# 文件作用：把 Pi 5 上采集的 LeRobot 数据集（so101_sort）增量同步到 A100 训练服务器。
#
# 主要内容：
#   1. 校验 HF_USER / A100_USER / A100_HOST 环境变量；
#   2. 用 rsync -av 增量同步数据集目录（断点续传、保留元数据）；
#   3. 同步目标是两台机器相同的目录：~/.cache/huggingface/lerobot/${HF_USER}/so101_sort。
#
# 用法（在 Pi 5 上执行）：
#   export HF_USER=<你的HuggingFace用户名>
#   export A100_USER=<A100登录用户名>
#   export A100_HOST=<A100的IP或主机名>
#   bash ~/sync_data.sh
#
# 注意：首次使用前在 Pi 5 与 A100 上互相配置 SSH 免密登录（ssh-copy-id），
#       否则 rsync 会交互式询问密码。
# ============================================================================

# 任一命令失败立即退出
set -e

# 1. 三个必要环境变量，缺一直接报错，避免同步到错误位置
export HF_USER=${HF_USER:?set HF_USER first}
export A100_USER=${A100_USER:?set A100_USER first}
export A100_HOST=${A100_HOST:?set A100_HOST first}

# 2. 本机数据集目录（LeRobot 默认缓存位置）
SRC="$HOME/.cache/huggingface/lerobot/${HF_USER}/so101_sort"

# 3. 远端目标目录（与本地保持同一相对路径）
DEST="${A100_USER}@${A100_HOST}:~/.cache/huggingface/lerobot/${HF_USER}/"

# 4. 检查本地数据集存在，避免 rsync 同步空目录后误以为成功
if [ ! -d "$SRC" ]; then
  echo "ERROR: dataset not found: $SRC" >&2
  exit 1
fi

# 5. 增量同步：-a 保留权限/时间戳，-v 显示进度
rsync -av "$SRC" "$DEST"

# 6. 提示下一步：到 A100 上 ls 确认文件完整
echo "sync done. On A100 run: ls ~/.cache/huggingface/lerobot/${HF_USER}/so101_sort"
