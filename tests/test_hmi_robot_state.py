# 测试文件：机械臂状态读取模块（project/hmi/robot_state.py）
#
# 覆盖：文件缺失返回离线、新鲜状态判定为在线、超过 5 秒未更新判定为离线。
import json
from pathlib import Path

from project.hmi.robot_state import read_robot_state
from project.hmi.robot_state import write_robot_state


def test_read_robot_state_missing_file_offline(tmp_path: Path):
    state = read_robot_state(tmp_path / "none.json", now=1_726_840_800.0)
    assert state["connected"] is False
    assert state["joints"] == [0.0] * 6


def test_read_robot_state_fresh_connected(tmp_path: Path):
    p = tmp_path / "robot_state.json"
    p.write_text(
        json.dumps(
            {
                "ts": "2026-08-21T10:00:00+08:00",
                "connected": True,
                "joints": [0.1, 0.2, -0.3, 0.4, 0.5, 0.6],
                "gripper": 0.8,
            }
        ),
        encoding="utf-8",
    )
    state = read_robot_state(p, now=1_787_277_600.0)
    assert state["connected"] is True
    assert state["joints"] == [0.1, 0.2, -0.3, 0.4, 0.5, 0.6]
    assert state["gripper"] == 0.8


def test_read_robot_state_stale_offline(tmp_path: Path):
    p = tmp_path / "robot_state.json"
    p.write_text(
        json.dumps({"ts": "2026-08-21T10:00:00+08:00", "connected": True, "joints": [0.0] * 6, "gripper": 0.0}),
        encoding="utf-8",
    )
    state = read_robot_state(p, now=1_787_277_700.0)
    assert state["connected"] is False


def test_write_robot_state_roundtrip(tmp_path: Path):
    p = tmp_path / "robot_state.json"
    write_robot_state(p, ts="2026-08-21T10:00:00+08:00", joints=[0.1, 0.2, -0.3, 0.4, 0.5, 0.6], gripper=0.8)
    state = read_robot_state(p, now=1_787_277_600.0)
    assert state["connected"] is True
    assert state["joints"] == [0.1, 0.2, -0.3, 0.4, 0.5, 0.6]
    assert state["gripper"] == 0.8
