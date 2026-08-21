# 测试文件：上位机 FastAPI 后端（project/hmi/app.py）
#
# 覆盖：无日志时统计返回零值、无状态文件时返回离线、首页可访问。
from pathlib import Path

from fastapi.testclient import TestClient

from project.hmi.app import create_app


def _hmi_root() -> Path:
    return Path(__file__).resolve().parents[1] / "project" / "hmi"


def test_stats_offline_when_no_log(tmp_path: Path):
    app = create_app(data_dir=tmp_path, hmi_root=_hmi_root())
    resp = TestClient(app).get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_attempts"] == 0
    assert body["success_rate"] is None


def test_state_offline_when_missing(tmp_path: Path):
    app = create_app(data_dir=tmp_path, hmi_root=_hmi_root())
    resp = TestClient(app).get("/api/state")
    assert resp.status_code == 200
    assert resp.json()["connected"] is False


def test_index_page_served(tmp_path: Path):
    app = create_app(data_dir=tmp_path, hmi_root=_hmi_root())
    resp = TestClient(app).get("/")
    assert resp.status_code == 200
    assert "Edge-Sort" in resp.text
