# Edge-Sort 上位机网页实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Pi 5 上提供浏览器访问的上位机页面：分拣统计、双相机实时画面、URDF 3D 机械臂姿态。

**Architecture:** FastAPI 后端（端口 8000）提供统计/状态 API、MJPEG 视频流与 URDF 静态资源；前端为原生 HTML/CSS/JS 单页，three.js + URDFLoader 渲染 3D 机械臂；数据来自 grasp_log.json 与 robot_state.json。

**Tech Stack:** Python 3.10、FastAPI、uvicorn、OpenCV、three.js 0.160.0、urdf-loader 0.11.0、pytest。

## Global Constraints

- Python 3.10；后端代码遵守项目注释规范（文件头 + 函数/类详细中文注释）。
- 相机名固定 `front`/`wrist`，索引读 `project/configs/cameras.json`。
- 页面为中文；文档遵循论文版式（编号章节、平实文本）。
- 机械臂/相机未接入时必须降级显示，不崩溃。
- 每个任务结束提交到 edge-sort-impl 分支。
- 3D 模型本期使用简化几何 URDF（官方网格暂不可下载），标注"近似模型"。

---

### Task 1: 统计聚合模块（TDD）

**Files:**
- Create: `project/hmi/stats.py`
- Test: `tests/test_hmi_stats.py`

**Interfaces:**
- Produces: `parse_grasp_log(path: str|Path) -> list[dict]`；`compute_stats(records: list[dict]) -> dict`。后续 Task 4 的 `/api/stats` 使用。

- [ ] **Step 1: 写失败测试**

`tests/test_hmi_stats.py`：

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `D:\work\robotarm\.tools\python310\python.exe -m pytest tests\test_hmi_stats.py -q -p no:cacheprovider`
Expected: FAIL（ModuleNotFoundError: project.hmi.stats）

- [ ] **Step 3: 最小实现**

`project/hmi/stats.py`：文件头注释说明作用；实现 `parse_grasp_log`（文件不存在返回 []，逐行 json.loads，坏行跳过）与 `compute_stats`（总次数、成功、失败、成功率、平均时长、最近 20 条倒序）。成功率无数据时为 None。

- [ ] **Step 4: 运行确认通过**

同上命令，Expected: 3 passed。

- [ ] **Step 5: 提交**

`git -C D:\work\robotarm\.worktrees\edge-sort-impl add project/hmi/stats.py tests/test_hmi_stats.py`，commit `feat: add grasp stats aggregation module (hmi)`。

---

### Task 2: 关节状态读取模块（TDD）

**Files:**
- Create: `project/hmi/robot_state.py`
- Test: `tests/test_hmi_robot_state.py`

**Interfaces:**
- Produces: `read_robot_state(path: str|Path, now: float) -> dict`，返回 `{"connected": bool, "joints": list[float], "gripper": float, "ts": str}`。

- [ ] **Step 1: 写失败测试**

```python
import json
from pathlib import Path

from project.hmi.robot_state import read_robot_state


def test_read_robot_state_missing_file_offline(tmp_path: Path):
    state = read_robot_state(tmp_path / "none.json", now=1_000_000.0)
    assert state["connected"] is False
    assert state["joints"] == [0.0] * 6


def test_read_robot_state_fresh_connected(tmp_path: Path):
    p = tmp_path / "robot_state.json"
    p.write_text(json.dumps({"ts": "2026-08-21T10:00:00+08:00", "connected": True,
                             "joints": [0.1, 0.2, -0.3, 0.4, 0.5, 0.6], "gripper": 0.8}), encoding="utf-8")
    state = read_robot_state(p, now=1_726_840_800.0)
    assert state["connected"] is True
    assert state["joints"] == [0.1, 0.2, -0.3, 0.4, 0.5, 0.6]
    assert state["gripper"] == 0.8


def test_read_robot_state_stale_offline(tmp_path: Path):
    p = tmp_path / "robot_state.json"
    p.write_text(json.dumps({"ts": "2026-08-21T10:00:00+08:00", "connected": True,
                             "joints": [0.0] * 6, "gripper": 0.0}), encoding="utf-8")
    state = read_robot_state(p, now=1_726_840_900.0)
    assert state["connected"] is False
```

- [ ] **Step 2: 运行确认失败**

Expected: FAIL（模块不存在）。

- [ ] **Step 3: 最小实现**

`project/hmi/robot_state.py`：读取 JSON；时间戳用 ISO8601 解析为 epoch；与 `now` 相差超过 5 秒视为离线；文件缺失返回全零离线；joints 长度不足 6 时补零。

- [ ] **Step 4: 运行确认通过**（同上，3 passed）

- [ ] **Step 5: 提交**

commit `feat: add robot state reader module (hmi)`。

---

### Task 3: 抓取日志写入模块（TDD）

**Files:**
- Create: `project/hmi/grasp_logger.py`
- Test: `tests/test_hmi_grasp_logger.py`

**Interfaces:**
- Produces: `append_grasp_record(path: str|Path, record: dict) -> None`（追加一行 JSON）；Task 8 集成到 closed_loop_sort.py。

- [ ] **Step 1: 写失败测试**

```python
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
```

- [ ] **Step 2/3/4**: 失败确认 → 实现（文件不存在则创建父目录与文件；ensure_ascii=False、utf-8 追加）→ 通过。

- [ ] **Step 5: 提交** `feat: add grasp log writer module (hmi)`。

---

### Task 4: FastAPI 后端

**Files:**
- Create: `project/hmi/app.py`
- Test: `tests/test_hmi_app.py`

**Interfaces:**
- Consumes: Task 1 `compute_stats`/`parse_grasp_log`；Task 2 `read_robot_state`；Task 5 的 `mjpeg_frames`/`open_camera`；Task 6 的静态文件；Task 7 的 URDF 目录。
- Produces: 路由 `/`、`/api/stats`、`/api/state`、`/video/front`、`/video/wrist`、`/urdf/*`（StaticFiles）。

- [ ] **Step 1: 写失败测试**

`tests/test_hmi_app.py`（TestClient；路径通过 app 配置注入，便于测试用 tmp 目录）：

```python
from pathlib import Path

from fastapi.testclient import TestClient

from project.hmi.app import create_app


def test_stats_offline_when_no_log(tmp_path: Path, monkeypatch):
    app = create_app(data_dir=tmp_path, hmi_root=Path(__file__).parents[1] / "project" / "hmi")
    client = TestClient(app)
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert resp.json()["total_attempts"] == 0


def test_state_offline_when_missing(tmp_path: Path, monkeypatch):
    app = create_app(data_dir=tmp_path, hmi_root=Path(__file__).parents[1] / "project" / "hmi")
    client = TestClient(app)
    resp = client.get("/api/state")
    assert resp.status_code == 200
    assert resp.json()["connected"] is False


def test_index_page_served(tmp_path: Path):
    hmi_root = Path(__file__).parents[1] / "project" / "hmi"
    app = create_app(data_dir=tmp_path, hmi_root=hmi_root)
    resp = TestClient(app).get("/")
    assert resp.status_code == 200
    assert "Edge-Sort" in resp.text
```

- [ ] **Step 2: 确认失败**（模块不存在）。

- [ ] **Step 3: 实现**

`project/hmi/app.py`：`create_app(data_dir, hmi_root)` 工厂函数；`/api/stats` 读 `data_dir/grasp_log.json` 聚合；`/api/state` 读 `data_dir/robot_state.json`；`/` 返回 `hmi_root/static/index.html`；`/urdf` 挂载 `hmi_root/urdf` 静态目录；`/video/*` 用受保护导入调用 Task 5 的 `open_camera`/`mjpeg_frames`（模块不存在或相机不可用时返回 503 文本）。全部带文件头与函数注释。

- [ ] **Step 4: 通过**（3 passed；若缺 httpx 先 `pip install httpx`）。

- [ ] **Step 5: 提交** `feat: add hmi fastapi backend`。

---

### Task 5: 相机 MJPEG 模块

**Files:**
- Create: `project/hmi/cameras.py`

**Interfaces:**
- Produces: `mjpeg_frames(index: int) -> Iterator[bytes]`（OpenCV 抓帧转 JPEG，逐帧 yield）；`open_camera(index) -> cv2.VideoCapture|None`。

- [ ] **Step 1: 实现**（注释规范；打开失败返回 None；读取失败退出生成器；帧率上限约 15 FPS，避免占用过高）。
- [ ] **Step 2: 冒烟验证**：`python -c "from project.hmi.cameras import open_camera; print(open_camera(999))"` 输出 None（无相机降级）。
- [ ] **Step 3: 提交** `feat: add camera mjpeg module (hmi)`。

---

### Task 6: 前端页面（统计 + 视频 + 状态）

**Files:**
- Create: `project/hmi/static/index.html`
- Create: `project/hmi/static/css/style.css`
- Create: `project/hmi/static/js/app.js`

- [ ] **Step 1: 页面结构**

`index.html`：中文页面；页头（标题 + 连接状态徽标）；统计卡片区（抓取次数、成功率、平均周期、最近用时）；视频区（front/wrist 两个 `<img src="/video/front">`）；3D 容器 `<div id="viewer3d">`；最近记录表（时间/物体/结果/用时/重试）。引用本地 css、js 与 vendor。

- [ ] **Step 2: 样式**

`style.css`：深色主题，卡片网格，离线状态用灰/红标识，窄屏自适应（flex/grid 换行）。

- [ ] **Step 3: 交互逻辑**

`app.js`：每 2 秒轮询 `/api/stats` 更新卡片与记录表；每 200ms 轮询 `/api/state` 更新状态徽标并调用 `window.updateArmJoints(joints, gripper)`（供 Task 7 使用）；fetch 失败时显示"离线"，不抛错。

- [ ] **Step 4: 验证**

`uvicorn` 起服务（或 TestClient 请求 `/`），curl 确认 200 与关键元素；`node --check` 若可用则校验 JS 语法（不可用则人工复查）。

- [ ] **Step 5: 提交** `feat: add hmi frontend dashboard`。

---

### Task 7: 3D URDF 视图

**Files:**
- Create: `project/hmi/urdf/so101_simplified.urdf`
- Create: `project/hmi/static/js/viewer3d.js`
- Create: `project/hmi/static/vendor/three.module.js`、`OrbitControls.js`、`urdf-loader.js`（从 jsdelivr 下载，版本固定）

- [ ] **Step 1: 本地化依赖**

下载（jsdelivr 已验证可访问）：
- `https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js`
- `https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js`
- `https://cdn.jsdelivr.net/npm/urdf-loader@0.11.0/build/urdf-loader.js`
存入 `static/vendor/`；下载后校验文件头（three.module.js 以 `import` 或 `/* three */` 开头；若某文件 404 则调整版本并记录）。

- [ ] **Step 2: 简化 URDF**

`so101_simplified.urdf`：6 个转动关节（joint1..joint6）+ 夹爪（gripper 连续关节），链接用圆柱/立方体近似；文件头 XML 注释标注"近似模型，官方网格可后续替换"；关节轴向参考 SO-101（底座 yaw、肩 pitch、肘 pitch、腕 pitch、腕 roll、末端 pitch，夹爪平移）。

- [ ] **Step 3: 视图脚本**

`viewer3d.js`：importmap 指向本地 vendor；初始化 three 场景、相机、OrbitControls；URDFLoader 加载 `/urdf/so101_simplified.urdf`；暴露 `window.updateArmJoints(joints, gripper)`，按 joint1..joint6 设置关节角、gripper 设夹爪；加载失败显示"3D 模型加载失败"。

- [ ] **Step 4: 验证**

`python -c "import xml.etree.ElementTree as ET; ET.parse(r'project/hmi/urdf/so101_simplified.urdf'); print('urdf ok')"`；vendor 文件存在且非空；JS 语法人工复查。

- [ ] **Step 5: 提交** `feat: add urdf 3d viewer (hmi)`。

---

### Task 8: closed_loop_sort.py 集成抓取日志

**Files:**
- Modify: `project/scripts/closed_loop_sort.py`

**Interfaces:**
- Consumes: Task 3 `append_grasp_record`。

- [ ] **Step 1: 集成**：每次抓取试次结束后（无论成功失败）调用 `append_grasp_record`，写入 `project/datasets/grasp_log.json`（object、success、duration_s、retries、ts）。只增加日志写入，不改变控制逻辑。
- [ ] **Step 2: 语法/导入验证**：`py_compile` 通过；`python -c "from project.scripts.closed_loop_sort import *"` 不报错（该脚本若入口设计不允许则改为仅 py_compile）。
- [ ] **Step 3: 提交** `feat: log grasp records for hmi (task integration)`。

---

### Task 9: README 与全量验证

**Files:**
- Create: `project/hmi/requirements-hmi.txt`
- Create: `project/hmi/README.md`

- [ ] **Step 1: 依赖清单**：`fastapi`、`uvicorn`、`opencv-python`（Pi 用完整版，本地测试可用 headless）。
- [ ] **Step 2: README**：启动命令（`conda activate lerobot && uvicorn app:app --host 0.0.0.0 --port 8000`，cwd=project/hmi）、浏览器访问 `http://<Pi的IP>:8000`、数据文件说明、降级行为、3D 模型近似说明。
- [ ] **Step 3: 全量测试**：`python -m pytest tests -q -p no:cacheprovider` 全部通过（含既有测试）。
- [ ] **Step 4: 提交** `docs: add hmi readme and requirements`。
