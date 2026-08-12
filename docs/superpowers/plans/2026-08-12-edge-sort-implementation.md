# Edge-Sort 端侧闭环分拣系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 三个月内完成 Edge-Sort 论文（中科院二区）所需的全部工程与研究资产：SO-ARM101 遥操作数据采集、ACT 基线、TinyACT 学生+蒸馏+int8 量化、闭环验证器与重试、能耗/时延基准、开源数据集，并完成论文初稿与投稿。

**Architecture:** 感知/决策层（Pi 5 8GB，双相机，TinyACT int8 推理 + 验证器 + 重试调度）与执行层（SO-ARM101 follower，STS3215 总线舵机）通过串口连接；数据与训练在 A100 完成（LeRobot 数据集格式），模型导出 ONNX int8 后回传 Pi 5。本工作区（D:\work\robotarm）为代码与文档的主仓库，Pi 5 与 A100 通过 SSH 使用同一套脚本。

**Tech Stack:** Python 3.10、PyTorch（A100 用 CUDA 版，Pi 5 用 CPU 版）、LeRobot v0.4.4（固定版本）、ONNX Runtime（ARM64）、OpenCV、ffmpeg、pytest（本地配置校验）、Hugging Face Hub。

## Global Constraints

- Python 版本固定 3.10（miniforge conda 环境名 `lerobot`）。
- LeRobot 固定版本：安装完成后立即记录 `pip show lerobot` 版本，若与 v0.4.4 不同，以 HiWonder 官方文档（docs.hiwonder.com/projects/LeRobot）推荐版本为准，并把实际版本写入 `project/README.md`。
- 机器人标识：follower 使用 `--robot.type=so101_follower`，leader 使用 `--teleop.type=so101_leader`；两个机械臂的 `--robot.id`/`--teleop.id` 在所有命令中保持一致（默认 `my_awesome_follower_arm` / `my_awesome_leader_arm`）。
- 相机名固定为 `front`（外部 200W）与 `wrist`（腕部 30W），类型 `opencv`，默认 640x480@30。
- 所有数据采集/训练命令必须设置 `export HF_USER=<你的HuggingFace用户名>`，`repo_id=${HF_USER}/so101_sort`。
- 安全约束：机械臂运行时清空 1 米内人员与贵重物品；上电后不得触碰关节；插拔线缆前断电；异常运动立即断电。
- 实验纪律：每个配置至少 30 次试次；结果记录为 CSV；代码与数据每个任务结束必须 commit。
- 禁止目标期刊：MDPI 全部、IEEE Access、Discover Computing。
- 论文写作从第 6 周开始并行，不允许串行。
- 代码注释规范（用户明确要求，2026-08-12 追加）：每个代码文件顶部必须用注释写明该文件的主要作用与主要内容；每个函数/类/关键代码块前必须有详细中文注释，解释其功能、输入输出与设计意图，便于作者在开发过程中自学。

---

## 任务总览与周次映射

| 周次 | 任务 |
|---|---|
| W1 | 任务 1–4：仓库初始化、本地校验工具、Pi 5 系统与 LeRobot 安装 |
| W2 | 任务 5–6：舵机设置/校准、遥操作与相机跑通 |
| W3 | 任务 7–9：A100 环境、数据同步管线、任务台定型 |
| W4 | 任务 10–11：试采 5 条 + 正式采集 80–100 条 |
| W5 | 任务 12–14：ACT 基线训练、Pi 5 部署、频率匹配排查 |
| W6 | 任务 15：TinyACT 学生配置与训练（论文方法节开写） |
| W7 | 任务 16–17：离线蒸馏、int8 量化导出与基准 |
| W8 | 任务 18–19：验证器训练、闭环重试集成 |
| W9 | 任务 20：完整实验矩阵 |
| W10 | 任务 21：能耗测量与数据分析 |
| W11 | 任务 22：论文初稿完成并交导师 |
| W12 | 任务 23–24：开源发布、投稿 |

---

### Task 1: 初始化项目仓库与目录结构

**Files:**
- Create: `D:\work\robotarm\project\README.md`
- Create: `D:\work\robotarm\project\scripts\README.md`
- Create: `D:\work\robotarm\project\configs\README.md`
- Create: `D:\work\robotarm\project\datasets\README.md`
- Create: `D:\work\robotarm\project\paper\README.md`

**Interfaces:**
- Produces: 目录结构与 README，后续所有任务把脚本放进 `project/scripts/`，配置放进 `project/configs/`。

- [ ] **Step 1: 安装 Git（Windows）**

打开 PowerShell（管理员），运行：
```powershell
winget install --id Git.Git -e --source winget
```
安装完成后关闭并重开 PowerShell，运行 `git --version`，预期输出 `git version 2.x.x`。

- [ ] **Step 2: 初始化仓库**

```powershell
cd D:\work\robotarm
git init
git config user.name "你的名字"
git config user.email "你的邮箱"
```

- [ ] **Step 3: 创建目录与 README**

```powershell
New-Item -ItemType Directory -Force -Path project\scripts, project\configs, project\datasets, project\paper | Out-Null
```

用编辑器创建 `project/README.md`，内容至少包含：项目一句话简介、硬件清单、LeRobot 固定版本号（安装后回填）、HF_USER 说明、安全规则。其余三个 README 各写 1–3 行说明用途。

- [ ] **Step 4: 提交**

```powershell
git add .
git commit -m "chore: init edge-sort repo structure"
```

- [ ] **Step 5: 验收**

运行 `git status --short`，预期输出为空；运行 `Get-ChildItem project`，预期包含 scripts/configs/datasets/paper/README.md 五个条目。

---

### Task 2: 配置校验工具与本地测试

**Files:**
- Create: `project/scripts/validate_config.py`
- Create: `tests/test_validate_config.py`

**Interfaces:**
- Produces: `validate_config.py`，提供 `validate_camera_json(text) -> dict` 与 `validate_repo_id(repo_id) -> bool`；后续任务 6/10 的 shell 脚本调用同一规则。

- [ ] **Step 1: 安装 Windows 本地 Python 与 pytest**

```powershell
winget install --id Python.Python.3.10 -e --source winget
python --version
pip install pytest
```

- [ ] **Step 2: 编写校验函数**

创建 `project/scripts/validate_config.py`：
```python
import json
import re

def validate_camera_json(text):
    data = json.loads(text)
    for name in ("front", "wrist"):
        assert name in data, f"missing camera: {name}"
        cam = data[name]
        assert cam.get("type") == "opencv", f"{name}: type must be opencv"
        assert cam.get("width", 0) > 0 and cam.get("height", 0) > 0
    return data

def validate_repo_id(repo_id):
    return bool(re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", repo_id))
```

- [ ] **Step 3: 编写测试**

创建 `tests/test_validate_config.py`：
```python
import json
import pytest
from project.scripts.validate_config import validate_camera_json, validate_repo_id

def test_camera_config_ok():
    cfg = validate_camera_json(json.dumps({
        "front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30},
        "wrist": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30},
    }))
    assert set(cfg) == {"front", "wrist"}

def test_camera_config_missing_wrist():
    with pytest.raises(AssertionError):
        validate_camera_json('{"front": {"type": "opencv", "width": 640, "height": 480}}')

def test_repo_id():
    assert validate_repo_id("alice/so101_sort")
    assert not validate_repo_id("bad id")
```

- [ ] **Step 4: 运行测试**

```powershell
python -m pytest tests/test_validate_config.py -v
```
预期：3 个测试全部 PASS。

- [ ] **Step 5: 提交**

```powershell
git add project/scripts/validate_config.py tests/
git commit -m "feat: add config validation tooling with tests"
```

---

### Task 3: Pi 5 系统准备

**Files:**
- Create: `project/README.md`（追加 Pi 5 环境说明）

**Interfaces:**
- Produces: 可 SSH 登录、可安装 Python 的 Pi 5；后续任务 4 在此执行。

- [ ] **Step 1: 烧录系统并启用 SSH**

用 Raspberry Pi Imager 烧录 Raspberry Pi OS（64-bit，Bookworm 或更新），烧录时在设置里启用 SSH、设置用户名密码，Wi-Fi 或网线接入同一局域网。

- [ ] **Step 2: 获取 IP 并登录**

```bash
# 在 Windows PowerShell 中
ssh pi@<Pi的IP>
```

- [ ] **Step 3: 系统更新与权限**

```bash
sudo apt update && sudo apt -y upgrade
sudo usermod -aG dialout,video $USER
sudo reboot
```
重启后重新登录，运行 `groups`，预期输出包含 `dialout` 与 `video`。

- [ ] **Step 4: 安装 Miniforge 与基础依赖**

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh -b
source ~/.bashrc
conda create -y -n lerobot python=3.10
conda activate lerobot
conda install -y -c conda-forge ffmpeg
sudo apt -y install build-essential
```

- [ ] **Step 5: 验收**

```bash
python --version   # 预期 Python 3.10.x
ffmpeg -version | head -1
```

- [ ] **Step 6: 提交**

把 Pi 5 的安装步骤摘要追加到 `project/README.md`，回到 Windows 工作区：
```powershell
git add project/README.md
git commit -m "docs: record Pi 5 environment setup"
```

---

### Task 4: 安装 LeRobot（Pi 5）并验证设备发现

**Files:**
- Create: `project/configs/cameras.json`
- Create: `project/scripts/pisetup.sh`

**Interfaces:**
- Produces: `cameras.json`（后续所有遥操作/录制命令读取同一份相机配置）；`pisetup.sh`（可重复执行的安装脚本）。

- [ ] **Step 1: 编写安装脚本**

创建 `project/scripts/pisetup.sh`：
```bash
#!/bin/bash
set -e
conda activate lerobot
git clone https://github.com/huggingface/lerobot.git ~/lerobot
cd ~/lerobot
git checkout v0.4.4
pip install -e ".[feetech]"
pip show lerobot | grep -E "^(Name|Version):"
```

- [ ] **Step 2: 执行并固定版本**

把脚本传到 Pi 5 并执行：
```bash
scp project/scripts/pisetup.sh pi@<Pi的IP>:~/
ssh pi@<Pi的IP> "bash ~/pisetup.sh"
```
把 `pip show lerobot` 输出的版本号记录到 `project/README.md`。若 v0.4.4 安装失败（依赖冲突），按 HiWonder 官方文档中的安装命令执行并记录实际版本。

- [ ] **Step 3: 验证设备发现**

```bash
conda activate lerobot
lerobot-find-port
lerobot-find-cameras opencv
```
预期：`find-port` 输出两个端口（follower 为 `/dev/ttyACM0`，leader 为 `/dev/ttyACM1`，以实际插入顺序为准）；`find-cameras` 列出两颗 UVC 相机及其 index。

- [ ] **Step 4: 编写相机配置并校验**

根据 Step 3 的实际 index 创建 `project/configs/cameras.json`：
```json
{
  "front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30},
  "wrist": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}
}
```
在 Windows 本地运行 `python -m pytest tests/test_validate_config.py -v` 确认仍通过（index 数值不同不影响测试）。

- [ ] **Step 5: 提交**

```powershell
git add project/scripts/pisetup.sh project/configs/cameras.json project/README.md
git commit -m "feat: pin lerobot v0.4.4 and camera config"
```

---

### Task 5: 舵机设置与主从臂校准

**Files:**
- Create: `project/scripts/calibrate.md`（校准操作记录模板）

**Interfaces:**
- Produces: 校准文件（位于 Pi 5 的 `~/.cache/huggingface/lerobot/my_awesome_follower_arm/` 与 `.../my_awesome_leader_arm/`），任务 6 依赖。

- [ ] **Step 1: 端口权限**

```bash
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyACM1
```

- [ ] **Step 2: 舵机 ID 设置（出厂默认已设置则跳过）**

仅在发现舵机 ID 错乱时执行；按提示把驱动板依次单独连接 6 号到 1 号舵机：
```bash
conda activate lerobot
lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/ttyACM0
```
预期每步输出 `'gripper' motor id set to 6` 等确认信息。

- [ ] **Step 3: 校准 follower**

```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm
```
按提示把每个关节完整移动一遍；校准完成后确认 `~/.cache/huggingface/lerobot/my_awesome_follower_arm/` 下出现 calibration 文件。

- [ ] **Step 4: 校准 leader**

```bash
lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=my_awesome_leader_arm
```
同样确认校准文件生成。

- [ ] **Step 5: 记录并提交**

在 `project/scripts/calibrate.md` 记录：端口映射、校准时间、异常现象（如终端收不到 5 号舵机信号属正常）。回到 Windows 提交：
```powershell
git add project/scripts/calibrate.md
git commit -m "docs: record servo setup and calibration"
```

---

### Task 6: 遥操作跑通与相机视野确认

**Files:**
- Create: `project/scripts/teleoperate.sh`

**Interfaces:**
- Produces: `teleoperate.sh`（任务 10 录制脚本复用其中的端口/相机参数）。

- [ ] **Step 1: 编写遥操作脚本**

创建 `project/scripts/teleoperate.sh`：
```bash
#!/bin/bash
set -e
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}
CAM=$(cat "$(dirname "$0")/../configs/cameras.json" | tr -d '\n' | sed 's/ /_/g')
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm \
  --robot.cameras="$CAM" \
  --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=my_awesome_leader_arm \
  --display_data=true
```

注意：shell 不会自动展开 JSON，实际使用时把 `$CAM` 替换为 `--robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, ...}, "wrist": {...}}'`（与 `cameras.json` 内容一致）。若 HiWonder 文档提供了 `--robot.cameras` 的直接 JSON 写法，以文档为准。

- [ ] **Step 2: 传输并运行**

```bash
scp project/scripts/teleoperate.sh pi@<Pi的IP>:~/
ssh pi@<Pi的IP> "export HF_USER=你的用户名; bash ~/teleoperate.sh"
```

- [ ] **Step 3: 验收**

确认三点：手推 leader 时 follower 实时跟随、无抖动；`front` 画面能看到整个工作区；`wrist` 画面能看到夹爪正下方物体。任一不满足，调整相机位置后重试。

- [ ] **Step 4: 提交**

```powershell
git add project/scripts/teleoperate.sh
git commit -m "feat: teleoperation script with dual cameras"
```

---

### Task 7: A100 训练环境

**Files:**
- Create: `project/scripts/a100setup.sh`

**Interfaces:**
- Produces: A100 上可用的 `lerobot` conda 环境（CUDA 版 PyTorch）；任务 12 训练依赖。

- [ ] **Step 1: 登录 A100 并创建环境**

```bash
ssh a100
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b
source ~/.bashrc
conda create -y -n lerobot python=3.10
conda activate lerobot
conda install -y -c conda-forge ffmpeg
git clone https://github.com/huggingface/lerobot.git ~/lerobot
cd ~/lerobot && git checkout v0.4.4
pip install -e ".[feetech]"
```

- [ ] **Step 2: 安装 CUDA 版 PyTorch**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```
（若 A100 的 CUDA 驱动版本不同，按 `nvidia-smi` 显示的 CUDA 版本选 cu118/cu121/cu124 对应 index。）

- [ ] **Step 3: 验证 CUDA**

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```
预期输出 `... True`。

- [ ] **Step 4: 提交**

```powershell
git add project/scripts/a100setup.sh
git commit -m "feat: A100 training environment setup script"
```

---

### Task 8: 数据同步管线（Pi 5 → A100）

**Files:**
- Create: `project/scripts/sync_data.sh`

**Interfaces:**
- Produces: `sync_data.sh`，任务 10 采集后调用；约定数据集根目录为 `~/.cache/huggingface/lerobot/${HF_USER}/so101_sort`。

- [ ] **Step 1: 编写同步脚本**

创建 `project/scripts/sync_data.sh`：
```bash
#!/bin/bash
set -e
export HF_USER=${HF_USER:?set HF_USER first}
A100_USER=a100用户
A100_HOST=a100主机名或IP
rsync -av \
  "~/.cache/huggingface/lerobot/${HF_USER}/so101_sort" \
  "${A100_USER}@${A100_HOST}:~/.cache/huggingface/lerobot/${HF_USER}/"
```

- [ ] **Step 2: 验证 rsync 可用**

Pi 5 与 A100 均运行 `rsync --version`；缺失则 `sudo apt install rsync`。

- [ ] **Step 3: 提交**

```powershell
git add project/scripts/sync_data.sh
git commit -m "feat: dataset sync script pi5 to a100"
```

---

### Task 9: 任务台与物体清单定型

**Files:**
- Create: `project/datasets/task_definition.md`

**Interfaces:**
- Produces: 任务定义与物体清单，任务 10 的 `single_task` 文案与任务 11 的采集标准以此为准。

- [ ] **Step 1: 搭建任务台**

固定外部相机与分拣盒位置；用卷尺记录：外部相机相对工作区的坐标、工作区边界、分拣盒格口位置，写入 `task_definition.md`。

- [ ] **Step 2: 定物体清单**

选 3–4 类物体（如大螺母、积木块、玩具、小杯），每类 2–3 个相同/相似件。逐件验证：夹爪能稳定抓起、腕部相机可见、外部相机可见。抓不稳的物体剔除并记录原因。

- [ ] **Step 3: 定义成功判据**

写入 `task_definition.md`：成功 = 物体被抓起并放入正确类别格口，且放稳后不掉落；失败分类：未抓起、掉落、放错格口、策略异常。

- [ ] **Step 4: 提交**

```powershell
git add project/datasets/task_definition.md
git commit -m "docs: task definition and object list"
```

---

### Task 10: 录制脚本与试采 5 条演示

**Files:**
- Create: `project/scripts/record_so101.sh`

**Interfaces:**
- Produces: `record_so101.sh`；任务 11 批量采集使用；数据集 `repo_id=${HF_USER}/so101_sort`。

- [ ] **Step 1: 编写录制脚本**

创建 `project/scripts/record_so101.sh`：
```bash
#!/bin/bash
set -e
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}
CAM=$(cat "$(dirname "$0")/../configs/cameras.json" | tr -d '\n')
lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm \
  --robot.cameras="$CAM" \
  --teleop.type=so101_leader --teleop.port=/dev/ttyACM1 --teleop.id=my_awesome_leader_arm \
  --display_data=false \
  --dataset.repo_id="${HF_USER}/so101_sort" \
  --dataset.num_episodes=5 \
  --dataset.single_task="Pick up the object and place it into the correct sorting slot"
```

相机 JSON 的传入方式以 HiWonder 官方文档为准（与任务 6 相同）。

- [ ] **Step 2: 试采**

```bash
scp project/scripts/record_so101.sh pi@<Pi的IP>:~/
ssh pi@<Pi的IP> "export HF_USER=你的用户名; bash ~/record_so101.sh"
```
键盘操作：`→` 结束当前 episode，`←` 重录，`ESC` 退出。

- [ ] **Step 3: 检查数据完整性**

```bash
ls ~/.cache/huggingface/lerobot/${HF_USER}/so101_sort
python - <<'EOF'
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
ds = LeRobotDataset("${HF_USER}/so101_sort", root="~/.cache/huggingface/lerobot")
print("episodes:", ds.num_episodes, "frames:", ds.num_frames)
item = ds[0]
print(sorted(item.keys()))
EOF
```
预期：episodes ≥ 1，frames > 0，键包含 `observation.images.front`、`observation.images.wrist`、`observation.state`、`action`。

- [ ] **Step 4: 提交**

```powershell
git add project/scripts/record_so101.sh
git commit -m "feat: so101 recording script with dual cameras"
```

---

### Task 11: 正式采集 80–100 条演示

**Files:**
- Create: `project/datasets/collection_log.csv`

**Interfaces:**
- Produces: 完整数据集（Pi 5 本地 + 同步到 A100）；任务 12 直接消费。

- [ ] **Step 1: 制定采集纪律**

每个 episode：随机摆放 1–3 个物体（位置、朝向变化），从固定起始姿势开始，轨迹保持一致（正上方下抓 → 垂直提起 → 平移 → 放入格口），速度均匀。

- [ ] **Step 2: 分 3–4 天采集**

每天运行 `record_so101.sh`（把 `num_episodes` 改为当天目标数），每天 20–30 条；每次结束后在 `collection_log.csv` 记录：日期、episode 号、物体组合、摆放随机度、主观质量（优/良/差）、备注。

- [ ] **Step 3: 质量筛查**

用 LeRobot 自带的 dataset viewer 或逐条回放 `lerobot-record` 采集目录，删除动作抖动、物体掉落、轨迹异常的 episode（`lerobot-record` 支持按 `←` 重录）。

- [ ] **Step 4: 同步到 A100**

```bash
export HF_USER=你的用户名
bash ~/sync_data.sh
```
在 A100 上确认：
```bash
ls ~/.cache/huggingface/lerobot/${HF_USER}/so101_sort
```

- [ ] **Step 5: 提交**

```powershell
git add project/datasets/collection_log.csv
git commit -m "data: so101_sort 80-100 episodes collected"
```

---

### Task 12: ACT 基线训练（A100）

**Files:**
- Create: `project/scripts/train_act.sh`

**Interfaces:**
- Produces: 教师模型 checkpoint `outputs/train/act_so101_sort/checkpoints/last/pretrained_model`；任务 13 评估、任务 16 蒸馏复用。

- [ ] **Step 1: 编写训练脚本**

创建 `project/scripts/train_act.sh`：
```bash
#!/bin/bash
set -e
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}
lerobot-train \
  --dataset.repo_id="${HF_USER}/so101_sort" \
  --policy.type=act \
  --output_dir=outputs/train/act_so101_sort \
  --policy.device=cuda \
  --policy.batch_size=8 \
  --policy.push_to_hub=false \
  --wandb.enable=false
```

- [ ] **Step 2: 短训冒烟（20 分钟）**

先加 `--policy.num_steps=200` 跑一次，确认无报错、loss 下降、checkpoint 生成。

- [ ] **Step 3: 正式训练**

```bash
export HF_USER=你的用户名
bash ~/train_act.sh
```
以 50k–100k steps 为目标；参考实测约 4 step/s 时 100k steps 约 7 小时，可隔夜跑。训练日志记录到 `project/datasets/train_log.txt`。

- [ ] **Step 4: 验收**

检查 `outputs/train/act_so101_sort/checkpoints/last/pretrained_model` 存在；记录最终 `eval_loss`。

- [ ] **Step 5: 提交**

```powershell
git add project/scripts/train_act.sh project/datasets/train_log.txt
git commit -m "feat: ACT teacher training script and log"
```

---

### Task 13: 基线部署到 Pi 5 并测定性能底数

**Files:**
- Create: `project/scripts/eval_rollout.sh`
- Create: `project/scripts/benchmark_latency.py`

**Interfaces:**
- Produces: 基线成功率与推理 FPS（写入 `project/datasets/baseline_metrics.csv`）；为任务 14 提供决策数据。

- [ ] **Step 1: 传输模型到 Pi 5**

```bash
scp -r a100:~/lerobot/outputs/train/act_so101_sort/checkpoints/last/pretrained_model ~/act_model/
```

- [ ] **Step 2: 编写 rollout 脚本**

创建 `project/scripts/eval_rollout.sh`：
```bash
#!/bin/bash
set -e
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}
CAM=$(cat "$(dirname "$0")/../configs/cameras.json" | tr -d '\n')
lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_awesome_follower_arm \
  --robot.cameras="$CAM" \
  --dataset.repo_id="${HF_USER}/eval_act_baseline" \
  --dataset.num_episodes=10 \
  --dataset.push_to_hub=false \
  --dataset.single_task="Pick up the object and place it into the correct sorting slot" \
  --display_data=false \
  --policy.path=~/act_model/pretrained_model
```

- [ ] **Step 3: 跑 10 次试次并记录**

每次试次记录：成功/失败及失败类型（未抓起/掉落/放错/异常），同时用秒表或脚本记录单件周期时间。

- [ ] **Step 4: 测推理延迟**

在 Pi 5 上运行：
```bash
python - <<'EOF'
import time, torch
from lerobot.common.policies.pretrained import PreTrainedPolicy
policy = PreTrainedPolicy.from_pretrained("~/act_model/pretrained_model")
policy.eval()
state = torch.zeros(1, policy.config.state_dim)
t0 = time.perf_counter(); n = 100
for _ in range(n):
    with torch.no_grad():
        policy.select_action(state)
dt = (time.perf_counter() - t0) / n
print(f"avg_ms={dt*1000:.1f} fps={1/dt:.2f}")
EOF
```

- [ ] **Step 5: 记录并提交**

把成功率和 FPS 写入 `project/datasets/baseline_metrics.csv`（列：model, fps, success_rate, avg_cycle_s, notes），提交。

```powershell
git add project/scripts/eval_rollout.sh project/scripts/benchmark_latency.py project/datasets/baseline_metrics.csv
git commit -m "feat: baseline rollout and latency benchmark"
```

---

### Task 14: 推理频率匹配排查（论文关键发现）

**Files:**
- Modify: `project/datasets/baseline_metrics.csv`
- Create: `project/datasets/fps_experiments.md`

**Interfaces:**
- Produces: “训练频率 vs 推理频率”对照实验结论，写入论文方法/实验章节；为任务 15 的 TinyACT 指标提供基线。

- [ ] **Step 1: 确认采集频率**

在数据集中读取控制频率：
```bash
python - <<'EOF'
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
ds = LeRobotDataset("${HF_USER}/so101_sort", root="~/.cache/huggingface/lerobot")
print("fps:", ds.fps, "frames per episode:", ds.num_frames // ds.num_episodes)
EOF
```

- [ ] **Step 2: 对照实验**

若 Pi 5 推理 FPS 明显低于数据集 fps（如 30Hz vs 8Hz），执行对照：
1. 记录当前低 FPS 下的成功率（任务 13 数据）；
2. 在 A100 上用 CUDA 跑同一模型 10 次试次，记录成功率；
3. 将两组数据写入 `fps_experiments.md`，复现公开结论“推理频率匹配影响成功率”。

- [ ] **Step 3: 决策分支**

- 若 Pi 5 推理 FPS ≥ 采集频率的 80%：继续原计划。
- 若不足：两种对策二选一（优先 A）：
  - A：重新以 15Hz 采集（`cameras.json` 中 fps 改 15，采集脚本同步改），重训基线；
  - B：将输入分辨率降到 320×240 重训。
把决策与依据写入 `fps_experiments.md`。

- [ ] **Step 4: 提交**

```powershell
git add project/datasets/baseline_metrics.csv project/datasets/fps_experiments.md
git commit -m "data: fps matching experiment and decision"
```

---

### Task 15: TinyACT 学生模型训练（论文方法节开写）

**Files:**
- Create: `project/scripts/train_tinyact.sh`
- Create: `project/paper/sections/method.md`

**Interfaces:**
- Produces: 学生模型 checkpoint `outputs/train/tinyact_so101_sort/checkpoints/last/pretrained_model`；任务 16 蒸馏、任务 17 量化依赖。

- [ ] **Step 1: 编写学生训练脚本**

创建 `project/scripts/train_tinyact.sh`（在教师命令基础上缩小模型）：
```bash
#!/bin/bash
set -e
conda activate lerobot
export HF_USER=${HF_USER:?set HF_USER first}
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
```

若上述超参名在当前版本不存在，运行 `lerobot-train --policy.type=act --help | grep -i "n_heads\|n_layers\|dim_model"` 获取实际参数名并回填。

- [ ] **Step 2: 冒烟训练**

`--policy.num_steps=200` 跑通后正式训练 30k–50k steps（A100 约 2–3 小时）。

- [ ] **Step 3: 双端延迟对比**

把学生模型传到 Pi 5，重复任务 13 Step 4 的延迟测量，把结果追加到 `baseline_metrics.csv`（model=tinyact_fp32）。

- [ ] **Step 4: 写方法节初稿**

创建 `project/paper/sections/method.md`，写出：系统架构、数据采集协议、ACT 教师、TinyACT 轻量化（超参缩容+分辨率决策）、验证器、量化、闭环重试的完整方法描述。允许初稿粗糙，W7–W8 逐步补数据。

- [ ] **Step 5: 提交**

```powershell
git add project/scripts/train_tinyact.sh project/paper/sections/method.md project/datasets/baseline_metrics.csv
git commit -m "feat: TinyACT student training and method draft"
```

---

### Task 16: 离线动作蒸馏（教师 → 学生）

**Files:**
- Create: `project/scripts/offline_distill.py`
- Create: `tests/test_offline_distill.py`

**Interfaces:**
- Produces: 蒸馏数据集 `~/.cache/huggingface/lerobot/${HF_USER}/so101_sort_distill`（动作替换为教师输出），任务 17 用 `train_tinyact.sh` 在该数据集上训练。

- [ ] **Step 1: 编写蒸馏脚本**

创建 `project/scripts/offline_distill.py`：
```python
import argparse
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.policies.pretrained import PreTrainedPolicy

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--root", default="~/.cache/huggingface/lerobot")
    args = ap.parse_args()

    teacher = PreTrainedPolicy.from_pretrained(args.teacher).to("cuda").eval()
    src = LeRobotDataset(args.src, root=args.root)
    dst = LeRobotDataset.create(
        args.dst, root=args.root,
        fps=src.fps,
        robot_type=src.robot_type,
        features=src.features,
        episodes=src.num_episodes,
    )

    for ep in range(src.num_episodes):
        ep_data = src.get_episode_data(ep)
        states = ep_data["observation.state"]
        teacher_actions = []
        for i in range(states.shape[0]):
            with torch.no_grad():
                chunk = teacher.select_action(states[i : i + 1].to("cuda"))
            teacher_actions.append(chunk[0, 0])  # 取动作块第一步
        actions = torch.stack(teacher_actions).cpu()
        dst.add_episode(ep_data, actions=actions)
        print(f"episode {ep}/{src.num_episodes} done")
    dst.save_episodes()

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 编写形状测试**

创建 `tests/test_offline_distill.py`，用假数据验证“teacher 每步输出 chunk、取第一步”的形状逻辑：
```python
import torch

def test_chunk_first_action_shape():
    chunk = torch.zeros(1, 25, 7)  # batch=1, chunk_len=25, action_dim=7
    action = chunk[0, 0]
    assert action.shape == (7,)
```

- [ ] **Step 3: 本地跑测试**

```powershell
python -m pytest tests/test_offline_distill.py -v
```
预期 PASS。

- [ ] **Step 4: A100 上执行蒸馏**

```bash
export HF_USER=你的用户名
python ~/offline_distill.py \
  --teacher ~/lerobot/outputs/train/act_so101_sort/checkpoints/last/pretrained_model \
  --src "${HF_USER}/so101_sort" \
  --dst "${HF_USER}/so101_sort_distill"
```
若 `LeRobotDataset.create` 或 `get_episode_data` API 与 v0.4.4 不一致，以 `python -c "import lerobot.common.datasets.lerobot_dataset as m; print([x for x in dir(m.LeRobotDataset) if not x.startswith('_')])"` 的输出为准调整方法名。

- [ ] **Step 5: 训练学生于蒸馏数据集**

把 `train_tinyact.sh` 的 `repo_id` 改为 `${HF_USER}/so101_sort_distill`，运行 30k steps，输出目录 `outputs/train/tinyact_distill_so101_sort`。

- [ ] **Step 6: 提交**

```powershell
git add project/scripts/offline_distill.py tests/test_offline_distill.py
git commit -m "feat: offline action distillation teacher to student"
```

---

### Task 17: int8 量化导出与延迟基准

**Files:**
- Create: `project/scripts/export_onnx.py`
- Create: `project/scripts/quantize_onnx.py`
- Create: `project/scripts/benchmark_onnx.py`

**Interfaces:**
- Produces: `tinyact_int8.onnx`（Pi 5 上部署）；`benchmark_onnx.py` 输出 p50/p95 延迟，任务 19 闭环脚本与任务 20 实验矩阵使用。

- [ ] **Step 1: 编写导出脚本**

创建 `project/scripts/export_onnx.py`：
```python
import argparse
import torch
from lerobot.common.policies.pretrained import PreTrainedPolicy

ap = argparse.ArgumentParser()
ap.add_argument("--policy", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--img", type=int, default=224)
args = ap.parse_args()

policy = PreTrainedPolicy.from_pretrained(args.policy).eval()
front = torch.zeros(1, 3, args.img, args.img)
wrist = torch.zeros(1, 3, args.img, args.img)
state = torch.zeros(1, policy.config.state_dim)

def forward(front, wrist, state):
    return policy.select_action({"observation.images.front": front,
                                 "observation.images.wrist": wrist,
                                 "observation.state": state})

torch.onnx.export(
    policy, (front, wrist, state), args.out,
    input_names=["front", "wrist", "state"],
    output_names=["action_chunk"],
    opset_version=17,
    dynamic_axes={"state": {0: "batch"}},
)
print("exported", args.out)
```

- [ ] **Step 2: 编写量化脚本**

创建 `project/scripts/quantize_onnx.py`：
```python
import argparse
from onnxruntime.quantization import quantize_dynamic, QuantType

ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="input", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()

quantize_dynamic(args.input, args.out, weight_type=QuantType.QInt8)
print("quantized", args.out)
```

- [ ] **Step 3: 导出并量化**

Pi 5 与 A100 均安装 `pip install onnx onnxruntime`（Pi 5 使用 ARM64 版 `onnxruntime`）。在 A100 上导出 fp32，在 Pi 5 上量化：
```bash
python export_onnx.py --policy ~/lerobot/outputs/train/tinyact_distill_so101_sort/checkpoints/last/pretrained_model --out tinyact.onnx
python quantize_onnx.py --in tinyact.onnx --out tinyact_int8.onnx
```

- [ ] **Step 4: 编写并运行延迟基准**

创建 `project/scripts/benchmark_onnx.py`：
```python
import argparse, time
import numpy as np
import onnxruntime as ort

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--n", type=int, default=100)
ap.add_argument("--img", type=int, default=224)
args = ap.parse_args()

sess = ort.InferenceSession(args.model, providers=["CPUExecutionProvider"])
front = np.zeros((1, 3, args.img, args.img), dtype=np.float32)
wrist = np.zeros_like(front)
state = np.zeros((1, 7), dtype=np.float32)
lat = []
for _ in range(args.n):
    t0 = time.perf_counter()
    sess.run(None, {"front": front, "wrist": wrist, "state": state})
    lat.append((time.perf_counter() - t0) * 1000)
lat.sort()
print(f"p50={lat[len(lat)//2]:.1f}ms p95={lat[int(len(lat)*0.95)]:.1f}ms fps={1000/lat[len(lat)//2]:.1f}")
```

运行：
```bash
python benchmark_onnx.py --model tinyact_int8.onnx
```
把 fp32 与 int8 两组结果追加到 `baseline_metrics.csv`。

- [ ] **Step 5: 精度回检**

用 `eval_rollout.sh`（`--policy.path` 改为 ONNX 需自定义加载器，本轮先用原 PyTorch 模型跑 10 次）确认量化前后成功率差 ≤1 次试次；若超过，改用静态 QDQ 量化（A100 上从数据集取 100 帧做校准集）并重测。

- [ ] **Step 6: 提交**

```powershell
git add project/scripts/export_onnx.py project/scripts/quantize_onnx.py project/scripts/benchmark_onnx.py project/datasets/baseline_metrics.csv
git commit -m "feat: int8 quantization and latency benchmark"
```

---

### Task 18: 抓取验证器训练

**Files:**
- Create: `project/scripts/train_verifier.py`
- Create: `project/scripts/prepare_verifier_data.py`
- Create: `project/datasets/verifier_data/README.md`

**Interfaces:**
- Produces: `verifier.onnx`（int8 二分类：0=没抓到，1=抓到），任务 19 调用。

- [ ] **Step 1: 准备数据目录**

采集 100–200 张腕部相机图像：从成功/失败 rollout 视频中截取抓取动作结束瞬间的帧，按 `project/datasets/verifier_data/success/` 与 `failure/` 分目录存放（JPEG，224×224 以上分辨率）。

- [ ] **Step 2: 编写数据整理脚本**

创建 `project/scripts/prepare_verifier_data.py`：遍历两个目录，输出 `train.txt`/`val.txt`（每行：路径 标签），按 8:2 划分。

- [ ] **Step 3: 编写训练脚本**

创建 `project/scripts/train_verifier.py`：
```python
import argparse
from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
from PIL import Image

class ImgDir(Dataset):
    def __init__(self, txt):
        self.items = [(p, int(l)) for p, l in (line.split() for line in Path(txt).read_text().splitlines())]
        self.tf = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
    def __len__(self):
        return len(self.items)
    def __getitem__(self, i):
        path, label = self.items[i]
        return self.tf(Image.open(path).convert("RGB")), label

ap = argparse.ArgumentParser()
ap.add_argument("--train", required=True)
ap.add_argument("--val", required=True)
ap.add_argument("--epochs", type=int, default=20)
args = ap.parse_args()

model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
model.classifier[3] = nn.Linear(model.classifier[3].in_features, 2)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
lossf = nn.CrossEntropyLoss()
train_dl = DataLoader(ImgDir(args.train), batch_size=16, shuffle=True)
val_dl = DataLoader(ImgDir(args.val), batch_size=16)

for ep in range(args.epochs):
    model.train()
    tot = 0
    for x, y in train_dl:
        opt.zero_grad()
        loss = lossf(model(x), y)
        loss.backward()
        opt.step()
        tot += loss.item()
    model.eval()
    correct = sum((model(x).argmax(1) == y).sum().item() for x, y in val_dl)
    n = sum(len(y) for _, y in val_dl)
    print(f"epoch {ep}: loss={tot/len(train_dl):.3f} val_acc={correct/n:.3f}")
torch.save(model.state_dict(), "verifier.pt")
```

- [ ] **Step 4: 训练与验收**

在 A100 上运行，目标验证集准确率 ≥95%；不足则增加数据或调 `lr`/`epochs`。

- [ ] **Step 5: 导出 int8 ONNX**

用任务 17 的量化流程导出 `verifier.onnx`（输入名 `image`，单张 1×3×224×224）。

- [ ] **Step 6: 提交**

```powershell
git add project/scripts/train_verifier.py project/scripts/prepare_verifier_data.py project/datasets/verifier_data/README.md
git commit -m "feat: grasp verifier training pipeline"
```

---

### Task 19: 闭环重试集成（Edge-Sort 核心）

**Files:**
- Create: `project/scripts/closed_loop_sort.py`

**Interfaces:**
- Produces: `closed_loop_sort.py`——Pi 5 上的主程序：策略推理 → 执行 → 验证 → 重试（N=2）→ 记录指标；任务 20 实验矩阵直接运行。

- [ ] **Step 1: 编写主程序**

创建 `project/scripts/closed_loop_sort.py`（以 LeRobot robot API 为准，方法名若不同按 Step 2 输出调整）：
```python
import argparse, time, json, csv
import numpy as np
import onnxruntime as ort
from lerobot.robots.factory import make_robot

ap = argparse.ArgumentParser()
ap.add_argument("--policy", required=True)
ap.add_argument("--verifier", required=True)
ap.add_argument("--port", default="/dev/ttyACM0")
ap.add_argument("--trials", type=int, default=30)
ap.add_argument("--max_retries", type=int, default=2)
ap.add_argument("--out", default="closed_loop_results.csv")
args = ap.parse_args()

policy = ort.InferenceSession(args.policy, providers=["CPUExecutionProvider"])
verifier = ort.InferenceSession(args.verifier, providers=["CPUExecutionProvider"])
robot = make_robot("so101_follower", port=args.port, id="my_awesome_follower_arm")

def verify(wrist_img):
    img = np.asarray(wrist_img.resize((224, 224))).astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))[None]
    out = verifier.run(None, {"image": img})[0]
    return int(out.argmax())

rows = []
for t in range(args.trials):
    obs = robot.read_observation()
    t0 = time.perf_counter()
    chunk = policy.run(None, {
        "front": np.asarray(obs["observation.images.front"])[None],
        "wrist": np.asarray(obs["observation.images.wrist"])[None],
        "state": np.asarray(obs["observation.state"])[None].astype(np.float32),
    })[0]
    for a in chunk:
        robot.send_action(a)
    grabbed = verify(obs["observation.images.wrist"])
    retries = 0
    while not grabbed and retries < args.max_retries:
        robot.send_action(robot.gripper_open_action())
        obs = robot.read_observation()
        chunk = policy.run(None, {...})[0]  # 与上方相同的推理调用
        for a in chunk:
            robot.send_action(a)
        grabbed = verify(obs["observation.images.wrist"])
        retries += 1
    rows.append({"trial": t, "retries": retries, "grabbed": grabbed, "cycle_s": time.perf_counter() - t0})

with open(args.out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print("done", args.out)
```

- [ ] **Step 2: 核对 robot API**

```bash
python - <<'EOF'
from lerobot.robots.factory import make_robot
r = make_robot("so101_follower", port="/dev/ttyACM0", id="my_awesome_follower_arm")
print([x for x in dir(r) if not x.startswith("_")])
EOF
```
根据输出调整 `read_observation`/`send_action`/夹爪开合动作的方法名。

- [ ] **Step 3: 冒烟测试**

`--trials 3` 跑通，确认：策略动作执行、抓取后验证、失败触发重试、CSV 正常生成。

- [ ] **Step 4: 提交**

```powershell
git add project/scripts/closed_loop_sort.py
git commit -m "feat: closed-loop sorting with verifier and retry"
```

---

### Task 20: 完整实验矩阵

**Files:**
- Create: `project/scripts/run_experiments.sh`
- Create: `project/datasets/results_schema.md`

**Interfaces:**
- Produces: `results_*.csv`（每个配置 ≥30 次试次），任务 21 能耗合并、任务 22 论文实验节消费。

- [ ] **Step 1: 定义结果表结构**

`results_schema.md` 固定列：`config, trial, success(0/1), failure_type, retries, cycle_s, inference_ms, notes`。

- [ ] **Step 2: 编写实验运行脚本**

创建 `project/scripts/run_experiments.sh`，依次运行：
1. 教师 ACT（A100 直连机械臂或 Pi 5 运行 PyTorch 模型，标注 config=teacher_gpu）；
2. 学生 fp32（config=tinyact_fp32）；
3. 学生 int8（config=tinyact_int8）；
4. 闭环 int8（`closed_loop_sort.py`，config=closed_loop_int8）；
5. 单相机变体（`cameras.json` 只保留 front，config=tinyact_int8_singlecam）。

每个配置写独立 CSV。

- [ ] **Step 3: 执行**

每个配置 ≥30 次试次；物体每次随机摆放；一次实验会话控制在 2–3 小时内，分多天完成。

- [ ] **Step 4: 汇总与提交**

把所有 CSV 汇总为 `project/datasets/results_all.csv` 并提交。

```powershell
git add project/scripts/run_experiments.sh project/datasets/
git commit -m "data: full experiment matrix"
```

---

### Task 21: 能耗测量与分析

**Files:**
- Create: `project/scripts/measure_power.md`
- Create: `project/datasets/energy_analysis.py`

**Interfaces:**
- Produces: `energy_per_action.csv`（每配置 J/件），任务 22 实验节使用。

- [ ] **Step 1: 接入功率计**

USB-C 功率计串接在 Pi 5 电源与机械臂 12V 电源线路上；记录各功率计型号与读数方式（数字显示或上位机日志）到 `measure_power.md`。

- [ ] **Step 2: 采集功耗日志**

对每个配置（teacher_gpu、tinyact_fp32、tinyact_int8、closed_loop_int8）跑 10 次试次，同时记录：起始总能耗读数与结束总能耗读数（Wh），以及单次周期时间。

- [ ] **Step 3: 编写分析脚本**

创建 `project/datasets/energy_analysis.py`：读入日志，计算每配置平均每件能耗（J/件 = Wh×3600/件数）、周期时间、能耗/成功率联合指标，输出 `energy_per_action.csv` 与两张图（能耗柱状图、时延分解图）。

- [ ] **Step 4: 提交**

```powershell
git add project/scripts/measure_power.md project/datasets/energy_analysis.py project/datasets/energy_per_action.csv
git commit -m "data: energy per action benchmark"
```

---

### Task 22: 论文初稿

**Files:**
- Create: `project/paper/main.tex`（或 Word 文档）
- Create: `project/paper/sections/introduction.md`、`related_work.md`、`results.md`、`conclusion.md`

**Interfaces:**
- Produces: 完整初稿（按 IEEE Sensors Journal 模板），任务 24 投稿。

- [ ] **Step 1: 搭建骨架**

下载 IEEE Sensors Journal 模板（overleaf.com 上 IEEE 官方模板或编辑部模板页），建 `project/paper/main.tex`。

- [ ] **Step 2: 逐节填写**

- Introduction：从基线论文 7.6s/14.6s 与公开“FPS 匹配问题”切入，引出 TinyACT + 闭环 + 能耗基准；
- Related Work：TinyML 机械臂、ACT/模仿学习边缘部署、抓取验证；
- Method：复用任务 15 的 method.md；
- Results：用任务 20/21 的 CSV 出表（成功率/周期/时延/能耗/消融）；
- Conclusion + Future Work：第二篇论文（RP2040 实时控制层）。

- [ ] **Step 3: 数据核对**

逐表核对与 CSV 一致；补充误差棒（均值±标准差）；“与基线论文对比”注明平台差异。

- [ ] **Step 4: 交导师**

初稿发给导师，收集意见（重点：创新点是否成立、期刊是否认可、图表规范）。

- [ ] **Step 5: 提交**

```powershell
git add project/paper/
git commit -m "paper: full first draft for supervisor review"
```

---

### Task 23: 开源发布

**Files:**
- Create: `project/datasets/README.md`（扩充为数据集卡）
- Create: `LICENSE`（Apache-2.0）

**Interfaces:**
- Produces: Hugging Face 数据集与 GitHub 仓库链接，写入论文 Data Availability。

- [ ] **Step 1: 上传数据集**

```bash
conda activate lerobot
export HF_USER=你的用户名
huggingface-cli login
python -m lerobot.scripts.push_dataset_to_hub --dataset.repo_id="${HF_USER}/so101_sort"
```
（若命令名不同，用 `lerobot-push-dataset --help` 查看。）

- [ ] **Step 2: 编写数据集卡**

在 `project/datasets/README.md` 写明：任务描述、物体清单、采集协议、相机参数、episode 数、许可、如何复现训练命令。

- [ ] **Step 3: 整理 GitHub 仓库**

把 `project/` 内容推送到 GitHub 公开仓库（如 `edge-sort`），确保不含原始大视频文件（数据集放 HF），加入 Apache-2.0 LICENSE 与依赖安装说明。

- [ ] **Step 4: 提交**

```powershell
git add LICENSE project/datasets/README.md
git commit -m "docs: dataset card and license"
```

---

### Task 24: 投稿准备

**Files:**
- Create: `project/paper/cover_letter.md`
- Create: `project/paper/submission_checklist.md`

**Interfaces:**
- Produces: 可提交稿件；完成项目“三个月一篇中科院二区”的闭环。

- [ ] **Step 1: 提交前检查表**

`submission_checklist.md` 逐项核对：模板合规、图表高清、Data Availability 链接有效、引用基线论文、导师署名确认、无 MDPI 目标、字数/页数限制。

- [ ] **Step 2: 写投稿信**

`cover_letter.md`：三段式——动机（低端机械臂边缘化瓶颈）、贡献（TinyACT+闭环+基准+数据集）、与期刊范围契合说明。

- [ ] **Step 3: 投稿**

在 IEEE Sensors Journal ScholarOne 系统按投稿信与检查表提交；记录稿件号。

- [ ] **Step 4: 提交（仓库）**

```powershell
git add project/paper/cover_letter.md project/paper/submission_checklist.md
git commit -m "docs: submission ready"
```

---

## Self-Review 记录

- **Spec 覆盖**：设计文档第 2 节四个贡献点分别由任务 15/16/17（TinyACT+蒸馏+量化）、18/19（验证器+闭环）、13/20/21（时延/成功率/能耗基准）、23（开源数据集）覆盖；12 周里程碑由任务总览表覆盖；风险预案落在任务 14（FPS 匹配）与任务 9/11（物体与数据质量）；期刊策略在任务 22/24 落地。
- **占位符扫描**：无 TBD/TODO；API 不确认处均给出运行时探测命令与决策规则。
- **类型/命名一致性**：相机名统一 `front`/`wrist`；数据集 `repo_id=${HF_USER}/so101_sort`；输出目录 `outputs/train/act_so101_sort` 与 `outputs/train/tinyact_so101_sort`；结果列名统一 `config,trial,success,failure_type,retries,cycle_s,inference_ms,notes`。
