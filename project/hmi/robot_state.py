# 文件作用：上位机（HMI）的机械臂状态读取模块。
#
# 主要内容：
#   1. 读取控制循环写入的 robot_state.json（关节角度、夹爪、时间戳）。
#   2. 判定连接状态：文件缺失或时间戳超过 5 秒未更新视为离线。
import json
from datetime import datetime
from pathlib import Path


def _parse_ts(ts: str) -> float:
    """把 ISO8601 时间字符串转成 epoch 秒。

    输入：形如 2026-08-21T10:00:00+08:00 的时间字符串。
    输出：浮点 epoch 秒；解析失败返回 0（视为陈旧数据）。
    """
    try:
        # 'Z' 结尾是 UTC 简写，Python 3.10 的 fromisoformat 不识别，先替换
        normalized = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return 0.0


def read_robot_state(path: Path, now: float) -> dict:
    """读取机械臂状态文件并判定连接状态。

    输入：状态文件路径与当前时间（epoch 秒）。
    输出：{"connected": bool, "joints": [6 个弧度], "gripper": 0-1, "ts": 原始时间戳}。
    文件缺失返回离线全零；时间戳距今超过 5 秒返回离线；关节数不足 6 补零。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"connected": False, "joints": [0.0] * 6, "gripper": 0.0, "ts": ""}

    ts_epoch = _parse_ts(data.get("ts", ""))
    joints = list(data.get("joints", []))
    while len(joints) < 6:
        joints.append(0.0)
    joints = joints[:6]
    gripper = float(data.get("gripper", 0.0))
    connected = bool(data.get("connected", False)) and (now - ts_epoch) <= 5.0
    return {"connected": connected, "joints": joints, "gripper": gripper, "ts": data.get("ts", "")}
