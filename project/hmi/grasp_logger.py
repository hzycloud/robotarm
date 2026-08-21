# 文件作用：上位机（HMI）的抓取日志写入模块。
#
# 主要内容：
#   1. append_grasp_record：把一条抓取记录以 JSONL 形式追加到 grasp_log.json。
#   2. 文件不存在时自动创建父目录与文件，供 closed_loop_sort.py 集成调用。
import json
from pathlib import Path
from typing import Any


def append_grasp_record(path: Path, record: dict) -> None:
    """把抓取记录追加到 JSONL 日志文件。

    输入：日志文件路径与记录字典（ts/object/success/duration_s/retries）。
    输出：无；文件不存在时创建父目录并新建文件，追加一行 UTF-8 JSON。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
