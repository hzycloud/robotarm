# 文件作用：上位机（HMI）的 FastAPI 后端入口。
#
# 主要内容：
#   1. create_app：应用工厂，注入数据目录与 hmi 根目录，便于测试。
#   2. 路由：首页、/api/stats 统计、/api/state 状态、/video/front|wrist 视频流、/urdf 静态资源。
#   3. 所有外设读取均延迟到请求时进行，设备缺失时降级返回，不影响其他接口。
import json
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# 让 project 包可从任意 cwd 导入（app.py 位于 project/hmi/ 下，仓库根为 parents[2]）
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from project.hmi.cameras import mjpeg_frames, open_camera
from project.hmi.robot_state import read_robot_state
from project.hmi.stats import compute_stats, parse_grasp_log


def _camera_indices(cameras_json: Optional[Path]) -> dict:
    """读取 cameras.json 得到 front/wrist 的相机索引。

    输入：cameras.json 路径（可不存在）。
    输出：{"front": int, "wrist": int}；文件缺失或格式不符时用默认值 0/1。
    """
    default = {"front": 0, "wrist": 1}
    if cameras_json is None or not Path(cameras_json).exists():
        return default
    try:
        data = json.loads(Path(cameras_json).read_text(encoding="utf-8"))
        indices = {}
        for name in ("front", "wrist"):
            item = data.get(name, {})
            index = item.get("index_or_path", default[name])
            indices[name] = int(index) if isinstance(index, (int, float)) else default[name]
        return indices
    except (json.JSONDecodeError, ValueError, AttributeError):
        return default


def _mjpeg_response(index: int) -> StreamingResponse:
    """构造一路 MJPEG 流响应；相机不可用时返回 503 文本。

    输入：相机索引。
    输出：StreamingResponse（multipart/x-mixed-replace）或 503 降级响应。
    """
    if open_camera(index) is None:
        return PlainTextResponse("camera unavailable", status_code=503)

    def generate():
        for jpeg in mjpeg_frames(index):
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


def create_app(data_dir: Path, hmi_root: Path, cameras_json: Optional[Path] = None) -> FastAPI:
    """创建上位机应用。

    输入：数据目录（grasp_log.json/robot_state.json 所在）、hmi 根目录、可选 cameras.json 路径。
    输出：配置好的 FastAPI 实例。
    """
    data_dir = Path(data_dir)
    hmi_root = Path(hmi_root)
    static_dir = hmi_root / "static"
    urdf_dir = hmi_root / "urdf"
    static_dir.mkdir(parents=True, exist_ok=True)
    urdf_dir.mkdir(parents=True, exist_ok=True)
    cameras_json = cameras_json or (hmi_root.parent / "configs" / "cameras.json")

    app = FastAPI(title="Edge-Sort HMI")

    @app.get("/")
    def index():
        """返回上位机首页。"""
        return FileResponse(static_dir / "index.html")

    @app.get("/api/stats")
    def stats():
        """返回分拣统计；无日志时返回全零统计。"""
        records = parse_grasp_log(data_dir / "grasp_log.json")
        return compute_stats(records)

    @app.get("/api/state")
    def state():
        """返回机械臂关节状态与连接状态；文件缺失时返回离线。"""
        return read_robot_state(data_dir / "robot_state.json", now=time.time())

    @app.get("/video/{name}")
    def video(name: str):
        """返回 front/wrist 相机 MJPEG 流；相机不可用时 503 降级。"""
        if name not in ("front", "wrist"):
            return PlainTextResponse("unknown camera", status_code=404)
        index = _camera_indices(cameras_json)[name]
        return _mjpeg_response(index)

    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/urdf", StaticFiles(directory=urdf_dir), name="urdf")
    return app
