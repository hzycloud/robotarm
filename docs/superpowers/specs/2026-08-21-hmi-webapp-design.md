# Edge-Sort 上位机网页：设计文档

- 日期：2026-08-21
- 状态：已获用户确认（方案 A：Python FastAPI + 原生 JS + three.js）
- 目标：为 Edge-Sort 项目提供一个浏览器访问的上位机页面，用于实时监控分拣统计、双相机画面与机械臂 3D 姿态。

## 1 背景与目标

项目目前只有命令行脚本，缺少一个可视化的运行监控界面。用户需要一个上位机网页，能够：

1. 显示抓取统计：抓取次数、抓取物体、抓取时间、抓取成功率。
2. 实时查看机械臂摄像头画面（腕部相机与外部相机）。
3. 通过 URDF 模型实时展示机械臂姿态。

约束：界面为中文；服务部署在 Pi 5 上，浏览器从局域网任意设备访问；机械臂与相机尚未接入时页面必须可正常打开并显示离线状态。

## 2 系统架构

三层结构：

- 浏览器前端：单页应用（原生 HTML/CSS/JS），展示统计卡片、相机视频、3D 机械臂。
- 后端服务：Python FastAPI + uvicorn，运行在 Pi 5 的 lerobot 环境，端口 8000，监听 0.0.0.0。
- 数据源：分拣日志 grasp_log.json（由 closed_loop_sort.py 追加写入）与关节状态 robot_state.json（由控制循环周期写入）；相机由 OpenCV 直接读取。

数据流：

1. closed_loop_sort.py 每次抓取后向 `project/datasets/grasp_log.json` 追加一行 JSON。
2. 后端读取并聚合该日志，通过 `/api/stats` 返回统计结果。
3. 控制循环周期（约 10 Hz）把当前关节角度写入 `project/datasets/robot_state.json`；后端以 5–10 Hz 轮询并通过 `/api/state` 返回。
4. 相机画面由后端 OpenCV 抓帧，以 MJPEG 流（multipart/x-mixed-replace）推送给前端。
5. 前端定时刷新统计与状态，3D 视图由 three.js + URDFLoader 渲染官方 SO-101 URDF。

## 3 组件与接口

### 3.1 后端 API

| 接口 | 方法 | 说明 |
|---|---|---|
| `/` | GET | 返回前端页面 |
| `/api/stats` | GET | 分拣统计：总次数、成功数、失败数、成功率、平均周期、最近记录 |
| `/api/state` | GET | 机械臂状态：是否连接、关节角度数组、夹爪开合、更新时间 |
| `/video/front` | GET | 外部相机 MJPEG 流 |
| `/video/wrist` | GET | 腕部相机 MJPEG 流 |
| `/urdf/...` | GET | URDF 文件与 STL 资产（静态资源） |

### 3.2 数据格式

grasp_log.json（JSONL，每行一条抓取记录）：

```json
{"ts": "2026-08-21T10:00:00+08:00", "object": "screw", "success": true, "duration_s": 12.3, "retries": 0}
```

robot_state.json：

```json
{"ts": "2026-08-21T10:00:01+08:00", "connected": true, "joints": [0, 0.5, -0.3, 0, 0.2, 0], "gripper": 0.8}
```

关节角度单位为弧度，顺序与 URDF 中 6 个旋转关节一致；夹爪为 0–1 的开合比例。

### 3.3 前端页面结构

- 页头：项目名称、当前连接状态（在线/离线）。
- 统计区：抓取次数、成功率、平均周期、最近一次用时四个卡片。
- 相机区：外部相机与腕部相机两路画面并排显示。
- 3D 区：three.js 渲染机械臂，支持鼠标旋转缩放（OrbitControls），显示当前关节角度。
- 记录区：最近抓取记录表格（时间、物体、结果、用时、重试次数）。
- 刷新策略：统计每 2 秒轮询，状态每 200 毫秒轮询，视频流由浏览器原生持续播放。

## 4 关键实现决策

1. 后端采用 FastAPI + uvicorn，Python 3.10，新增依赖 fastapi、uvicorn、opencv-python（项目已有 OpenCV 依赖则复用）。
2. 前端使用原生 JS 与 three.js（含 OrbitControls 与 URDFLoader），通过 CDN importmap 加载；局域网浏览器需能访问互联网。若离线部署需求明确，后续将 three.js 与 URDFLoader 本地化。
3. 相机索引从 project/configs/cameras.json 读取；相机不可用时返回占位画面，不导致页面崩溃。
4. 机械臂未接入或 robot_state.json 不存在时，/api/state 返回 connected=false 与零关节角，页面显示离线并停止 3D 姿态跟随（仍显示静止模型）。
5. URDF 资产：从 Hugging Face lerobot/robot-urdfs 仓库获取 so101 的 URDF 与 STL 网格，存放于 project/hmi/urdf/；若官方资产不可用，退化为简化几何体并标注"近似模型"。
6. 统计接口读不到 grasp_log.json 时返回全零统计，前端显示"暂无数据"，不报错。

## 5 目录结构

```text
project/hmi/
  app.py                 # FastAPI 后端（页面、API、MJPEG、URDF 静态资源）
  requirements-hmi.txt   # fastapi / uvicorn / opencv-python
  static/
    index.html           # 页面结构
    css/style.css        # 样式
    js/app.js            # 统计与状态轮询、记录表渲染
    js/viewer3d.js       # three.js URDF 机械臂渲染
  urdf/
    so100.urdf           # 官方 SO-101 URDF
    assets/*.stl         # 网格资产
  README.md              # 启动方法（uvicorn 命令、端口、访问方式）
```

## 6 错误处理与降级

- 相机打开失败：视频区显示"无信号"占位，统计与 3D 不受影响。
- grasp_log.json 损坏：跳过坏行，统计仍可计算；文件不存在时按空数据处理。
- robot_state.json 过期（超过 5 秒未更新）：视为离线。
- 后端启动时不因设备缺失而失败；所有外设读取均延迟到请求时进行。

## 7 验收标准

1. 在 Pi 5 上按 README 启动后，局域网浏览器可打开页面，界面为中文。
2. 无机械臂、无相机时页面正常显示离线状态，无报错。
3. 写入示例 grasp_log.json 后，统计卡片与记录表正确显示。
4. 相机接入后，两路视频流实时显示。
5. 机械臂接入且控制循环写 robot_state.json 后，3D 模型关节角度跟随真实姿态。
6. 代码遵守项目注释规范（文件头 + 关键函数中文注释）与文档版式规范。

## 8 非目标（本期不做）

- 不做机器人控制指令下发（仅监控）。
- 不做用户鉴权（局域网使用，后续需要再加）。
- 不做视频录制与回放。
- 不做多用户会话管理。
