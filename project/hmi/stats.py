# 文件作用：上位机（HMI）的分拣统计聚合模块。
#
# 主要内容：
#   1. parse_grasp_log：读取 grasp_log.json（JSONL 格式），跳过坏行，文件缺失时返回空列表。
#   2. compute_stats：把抓取记录聚合成统计字典（次数、成功率、平均用时、最近记录），供 /api/stats 使用。
import json
from pathlib import Path
from typing import Any, List


def parse_grasp_log(path: Path) -> List[dict]:
    """读取抓取日志（JSONL），返回记录列表。

    输入：日志文件路径；文件不存在时返回空列表。
    输出：每条记录为一个字典；无法解析的行直接跳过，不影响其余数据。
    """
    records: List[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    # 坏行跳过：单条记录损坏不应影响整体统计
                    continue
    except FileNotFoundError:
        return []
    return records


def compute_stats(records: List[dict]) -> dict:
    """把抓取记录聚合成上位机展示用的统计字典。

    输入：parse_grasp_log 的输出（字典列表）。
    输出：total_attempts/successes/failures/success_rate/avg_duration_s/recent。
    recent 为按记录顺序倒序的最近 20 条；无数据时 success_rate 为 None。
    """
    total = len(records)
    successes = sum(1 for r in records if r.get("success"))
    failures = total - successes
    durations = [r.get("duration_s") for r in records if isinstance(r.get("duration_s"), (int, float))]
    avg_duration = sum(durations) / len(durations) if durations else None
    recent = list(reversed(records[-20:]))
    return {
        "total_attempts": total,
        "successes": successes,
        "failures": failures,
        "success_rate": successes / total if total else None,
        "avg_duration_s": avg_duration,
        "recent": recent,
    }
