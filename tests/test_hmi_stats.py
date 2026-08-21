# 测试文件：grasp 统计聚合模块（project/hmi/stats.py）
#
# 覆盖：解析 grasp_log.json（跳过坏行、文件缺失）、统计聚合（次数/成功率/平均时长/最近记录）。
import json
from pathlib import Path

from project.hmi.stats import compute_stats, parse_grasp_log


def test_parse_grasp_log_skips_bad_lines_and_missing_file(tmp_path: Path):
    log = tmp_path / "grasp_log.json"
    log.write_text(
        '{"ts": "2026-08-21T10:00:00+08:00", "object": "screw", "success": true, "duration_s": 12.3, "retries": 0}\n'
        "not json\n"
        '{"ts": "2026-08-21T10:01:00+08:00", "object": "nut", "success": false, "duration_s": 9.0, "retries": 2}\n',
        encoding="utf-8",
    )
    records = parse_grasp_log(log)
    assert len(records) == 2
    assert parse_grasp_log(tmp_path / "missing.json") == []


def test_compute_stats_counts_and_rate():
    records = [
        {"ts": "2026-08-21T10:00:00+08:00", "object": "screw", "success": True, "duration_s": 12.3, "retries": 0},
        {"ts": "2026-08-21T10:01:00+08:00", "object": "nut", "success": False, "duration_s": 9.0, "retries": 2},
        {"ts": "2026-08-21T10:02:00+08:00", "object": "screw", "success": True, "duration_s": 11.1, "retries": 1},
    ]
    stats = compute_stats(records)
    assert stats["total_attempts"] == 3
    assert stats["successes"] == 2
    assert stats["failures"] == 1
    assert stats["success_rate"] == 2 / 3
    assert abs(stats["avg_duration_s"] - 10.8) < 1e-9
    assert stats["recent"][0]["object"] == "screw"


def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats["total_attempts"] == 0
    assert stats["success_rate"] is None
