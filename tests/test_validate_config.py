"""
文件作用：validate_config.py 配置校验工具的单元测试。

本文件用 pytest 覆盖三个场景：
- test_camera_config_ok：合法配置应通过校验并原样返回。
- test_camera_config_missing_wrist：缺少 wrist 相机时应抛 AssertionError。
- test_repo_id：合法的数据集 ID 返回 True，非法格式返回 False。

运行方式（在仓库根目录执行）：
    python -m pytest tests/test_validate_config.py -v
"""

import json  # 构造合法的相机配置 JSON

import pytest  # 使用 pytest.raises 断言函数抛异常

# 导入被测模块：本项目约定测试在仓库根目录运行，
# 因此可以直接用 project.scripts.validate_config 的形式导入
from project.scripts.validate_config import validate_camera_json, validate_repo_id


def test_camera_config_ok():
    """正常情况：front + wrist 双相机配置应校验通过，且原样返回。"""
    cfg = validate_camera_json(json.dumps({
        "front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30},
        "wrist": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30},
    }))
    # 校验函数应返回解析后的字典，且包含且仅包含 front/wrist 两个相机
    assert set(cfg) == {"front", "wrist"}


def test_camera_config_missing_wrist():
    """异常情况：只有 front 相机、缺少 wrist 时，应抛出 AssertionError。"""
    with pytest.raises(AssertionError):
        validate_camera_json('{"front": {"type": "opencv", "width": 640, "height": 480}}')


def test_repo_id():
    """ID 格式：合法 ID（用户名/数据集名）应通过，带空格的非法 ID 应被拒绝。"""
    assert validate_repo_id("alice/so101_sort")
    assert not validate_repo_id("bad id")
