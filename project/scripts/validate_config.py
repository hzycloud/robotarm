import json
import re


def validate_camera_json(text):
    data = json.loads(text)
    for name in ("front", "wrist"):
        assert name in data, f"missing camera: {name}"
        cam = data[name]
        assert cam.get("type") == "opencv", f"{name}: type must be opencv"
        assert cam.get("width", 0) > 0 and cam.get("height", 0) > 0
    return data


def validate_repo_id(repo_id):
    return bool(re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", repo_id))
