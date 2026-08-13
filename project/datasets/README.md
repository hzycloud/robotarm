# SO-Sort 数据集说明

SO-Sort 是 Edge-Sort 项目采集的桌面分拣模仿学习数据集，采用 LeRobot 标准格式（Parquet 与视频），可发布到 Hugging Face Hub，并可直接用 lerobot-train 训练。

## 1 任务描述

桌面摆放三到四类小物体，位置与朝向随机，机械臂逐件抓取并按类别放入对应格口。

## 2 采集协议

演示条数 80 到 100。相机为 front（外部 200W）与 wrist（腕部 30W），分辨率 640×480，帧率 30，以 cameras.json 为准。采样内容包括关节角度、夹爪开合与双相机图像，频率约 30 到 50 Hz。物体清单见 task_definition.md。

## 3 数据格式

```text
~/.cache/huggingface/lerobot/${HF_USER}/so101_sort/
├── meta/
├── videos/
├── data/
└── info.json
```

## 4 复现命令

```bash
export HF_USER=<你的HuggingFace用户名>
bash project/scripts/train_act.sh
python project/scripts/offline_distill.py \
  --teacher outputs/train/act_so101_sort/checkpoints/last/pretrained_model \
  --src "${HF_USER}/so101_sort" --dst "${HF_USER}/so101_sort_distill"
bash project/scripts/train_tinyact.sh
```

训练学生前，把 train_tinyact.sh 中的 repo_id 改为 `${HF_USER}/so101_sort_distill`。

## 5 许可

Apache-2.0，与 LeRobot 上游一致，发布时附 LICENSE 文件。
