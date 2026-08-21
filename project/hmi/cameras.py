# 文件作用：上位机（HMI）的相机 MJPEG 流模块。
#
# 主要内容：
#   1. open_camera：打开指定索引的 UVC 相机，失败返回 None（降级处理）。
#   2. mjpeg_frames：把相机帧编码为 JPEG 并逐帧产出，供 FastAPI 以 MJPEG 流推送。
import time
from typing import Iterator, Optional

import cv2


def open_camera(index: int) -> Optional["cv2.VideoCapture"]:
    """打开指定索引的相机。

    输入：相机索引（与 project/configs/cameras.json 中的 index_or_path 一致）。
    输出：可用的 VideoCapture 对象；打开失败返回 None，供上层降级显示。
    """
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        return None
    return cap


def mjpeg_frames(index: int, fps: int = 15) -> Iterator[bytes]:
    """从相机读取帧并编码为 JPEG，逐帧产出字节。

    输入：相机索引与目标帧率上限。
    输出：JPEG 字节的迭代器；相机不可用或读取失败时结束迭代。
    帧率上限用于避免长时间推流占用过高 CPU，不影响统计与状态接口。
    """
    cap = open_camera(index)
    if cap is None:
        return
    interval = 1.0 / max(1, fps)
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                break
            yield jpeg.tobytes()
            time.sleep(interval)
    finally:
        cap.release()
