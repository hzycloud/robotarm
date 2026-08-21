# Edge-Sort 上位机（HMI）

## 1 简介

上位机网页运行在 Pi 5 上，浏览器访问后可以实时查看分拣统计、双相机画面与机械臂 3D 姿态。数据来自控制程序写入的两个文件：`project/datasets/grasp_log.json`（抓取记录）与 `project/datasets/robot_state.json`（关节状态）。

## 2 安装

在 Pi 5 的 lerobot 环境中安装依赖：

```bash
conda activate lerobot
pip install -r project/hmi/requirements-hmi.txt
```

## 3 启动

```bash
cd project/hmi
uvicorn app:app --host 0.0.0.0 --port 8000
```

浏览器访问 `http://<Pi的IP>:8000`。

## 4 数据来源

- `grasp_log.json`：由 `project/scripts/closed_loop_sort.py` 每次抓取后追加一行 JSON（时间、物体、成功与否、用时、重试次数）。
- `robot_state.json`：由 `closed_loop_sort.py` 每轮写入关节角度（弧度，顺序为 shoulder_pan、shoulder_lift、elbow_flex、wrist_flex、wrist_roll、gripper）与夹爪比例，供 3D 视图实时跟随。
- 相机：索引从 `project/configs/cameras.json` 读取（front/wrist），未配置时默认 0/1。

## 5 降级行为

- 机械臂未接入或状态文件过期超过 5 秒：页面显示"离线"，3D 模型保持静止。
- 相机不可用：视频区显示无信号（503 占位），不影响其他功能。
- 无抓取记录：统计卡片显示 0/--，记录表显示"暂无数据"。

## 6 说明

- 3D 模型为 SO-101 官方 URDF（so101_new_calib.urdf）与 STL 网格，来源 TheRobotStudio/SO-ARM100 仓库（Apache-2.0 兼容的社区资产），已随仓库提交；前端 three.js 依赖已本地化，页面不依赖外网。
- 3D 关节角与真实机械臂的零点/方向可能不一致，接入真机后如姿态异常，需按实测校准关节偏置与方向。
