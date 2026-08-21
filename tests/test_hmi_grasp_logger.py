# 测试文件：抓取日志写入模块（project/hmi/grasp_logger.py）
#
# 覆盖：追加 JSONL 记录、文件不存在时自动创建。
import json
from pathlib import Path

from project.hmi.grasp_logger import append_grasp_record


def test_append_grasp_record_appends_jsonl(tmp_path: Path):
    p = tmp_path / "grasp_log.json"
    append_grasp_record(p, {"ts": "t1", "object": "screw", "success": True, "duration_s": 1.0, "retries": 0})
    append_grasp_record(p, {"ts": "t2", "object": "nut", "success": False, "duration_s": 2.0, "retries": 1})
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["object"] == "screw"
    assert json.loads(lines[1])["success"] is False
