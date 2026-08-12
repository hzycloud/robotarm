# SO-Sort 数据集

## 概述

SO-Sort 是 Edge-Sort 项目采集的桌面分拣模仿学习数据集，格式为 LeRobot 标准
（Parquet + 视频），可发布到 Hugging Face Hub 并直接用 `lerobot-train` 训练。

## 任务描述

桌面 3–4 类小物体随机位姿摆放，机械臂逐件抓取并按类别放入对应格口。

## 采集协议

- 演示条数：80–100
- 相机：front（外部 200W）+ wrist（腕部 30W），640x480@30（以 cameras.json 为准）
- 采样：关节角度 + 夹爪开合 + 双相机，约 30–50 Hz
- 物体清单：见 task_definition.md（以实际可抓取性为准）

## 数据格式

```text
~/.cache/huggingface/lerobot/${HF_USER}/so101_sort/
├── meta/
├── videos/
├── data/
└── info.json
```

## 复现命令

```bash
export HF_USER=<你的HuggingFace用户名>
# 训练教师
bash project/scripts/train_act.sh
# 蒸馏数据集（教师生成动作标签）
python project/scripts/offline_distill.py \
  --teacher outputs/train/act_so101_sort/checkpoints/last/pretrained_model \
  --src "${HF_USER}/so101_sort" --dst "${HF_USER}/so101_sort_distill"
# 训练学生
bash project/scripts/train_tinyact.sh   # 改 repo_id 为 so101_sort_distill
```

## 许可

Apache-2.0（与 LeRobot 上游一致）；发布时附 LICENSE。
