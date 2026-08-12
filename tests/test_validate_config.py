import json

import pytest

from project.scripts.validate_config import validate_camera_json, validate_repo_id


def test_camera_config_ok():
    cfg = validate_camera_json(json.dumps({
        "front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30},
        "wrist": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30},
    }))
    assert set(cfg) == {"front", "wrist"}


def test_camera_config_missing_wrist():
    with pytest.raises(AssertionError):
        validate_camera_json('{"front": {"type": "opencv", "width": 640, "height": 480}}')


def test_repo_id():
    assert validate_repo_id("alice/so101_sort")
    assert not validate_repo_id("bad id")
