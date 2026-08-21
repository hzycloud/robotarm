# 推理频率匹配排查实验（Task 14）

## 1 目的

验证 Pi 5 端侧推理频率与数据采集频率的匹配程度对分拣成功率的影响，为 TinyACT 学生模型（任务 15）提供基线，并作为论文方法节与实验节的对照实验结论。

## 2 前置数据

- 任务 13 的 Pi 5 低 FPS 成功率：取自 project/datasets/baseline_metrics.csv（开环基线，每配置至少 30 次试次）。
- A100 CUDA 同模型成功率：本实验第 4 节产出（10 次试次）。

## 3 步骤一：确认采集频率

在 A100 或 Pi 5 的 lerobot 环境中读取数据集控制频率：

```bash
python - <<'EOF'
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
ds = LeRobotDataset("${HF_USER}/so101_sort", root="~/.cache/huggingface/lerobot")
print("fps:", ds.fps, "frames per episode:", ds.num_frames // ds.num_episodes)
EOF
```

记录项：数据集 fps、每集帧数、Pi 5 实测策略推理频率（任务 13 输出）。

## 4 步骤二：对照实验

1. 在 Pi 5 上部署模型，运行 project/scripts/eval_rollout.sh，记录低 FPS 下的分拣成功率（至少 30 次试次，写入 baseline_metrics.csv）。
2. 在 A100 上用 CUDA 运行同一模型 10 次试次，记录成功率。
3. 将两组结果填入下表。

| 配置 | 平台 | 推理 FPS | 试次 | 成功率 |
|---|---|---|---|---|
| 基线（待回填） | Pi 5 CPU | | | |
| 基线（待回填） | A100 CUDA | | 10 | |

## 5 步骤三：决策

规则：

- 若 Pi 5 推理 FPS 达到采集频率的 80% 及以上，继续原计划。
- 若不足，二选一（优先 A）：
  - A：重新以 15Hz 采集（cameras.json 的 fps 改为 15，record_so101.sh 同步修改），重训基线；
  - B：输入分辨率降到 320×240 重训。

决策记录（执行时填写）：选择、依据、影响范围。

## 6 输出

- 结论写入 project/paper/sections/method.md 与 results.md。
- 与 baseline_metrics.csv 一并提交：

```bash
git add project/datasets/baseline_metrics.csv project/datasets/fps_experiments.md
git commit -m "data: fps matching experiment and decision"
```
