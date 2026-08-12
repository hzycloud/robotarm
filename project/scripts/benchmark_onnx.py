"""
文件作用：在 Pi 5 上测量 ONNX 模型的推理延迟（p50/p95 毫秒与等效 FPS），
         用于 TinyACT 部署的性能底数与论文的时延指标。

主要内容：
  1. 加载 ONNX Runtime CPU 会话；
  2. 构造 dummy 输入（front/wrist/state）；
  3. 连续推理 N 次，统计 p50/p95 延迟与 FPS。

运行方式（Pi 5）：
  python benchmark_onnx.py --model tinyact_int8.onnx --n 100
"""

import argparse  # 解析命令行参数
import time  # 计时

import numpy as np  # 构造输入数组
import onnxruntime as ort  # 推理引擎


def main():
    """主流程：加载模型 → 推理 N 次 → 输出延迟分位数。"""
    ap = argparse.ArgumentParser(description="Benchmark ONNX latency")
    ap.add_argument("--model", required=True, help="onnx model path")
    ap.add_argument("--n", type=int, default=100, help="number of inferences")
    ap.add_argument("--img", type=int, default=224, help="square input image size")
    args = ap.parse_args()

    # 1. CPU 会话（Pi 5 无 GPU，必须显式用 CPUExecutionProvider）
    sess = ort.InferenceSession(args.model, providers=["CPUExecutionProvider"])

    # 2. dummy 输入：图像 (1,3,img,img) float32，state (1,7)
    front = np.zeros((1, 3, args.img, args.img), dtype=np.float32)
    wrist = np.zeros_like(front)
    state = np.zeros((1, 7), dtype=np.float32)

    # 3. 连续推理并记录每次耗时（毫秒）
    lat = []
    for _ in range(args.n):
        t0 = time.perf_counter()
        sess.run(None, {"front": front, "wrist": wrist, "state": state})
        lat.append((time.perf_counter() - t0) * 1000)

    # 4. 排序后取 p50/p95；FPS 按 p50 计算
    lat.sort()
    p50 = lat[len(lat) // 2]
    p95 = lat[int(len(lat) * 0.95)]
    print(f"p50={p50:.1f}ms p95={p95:.1f}ms fps={1000 / p50:.1f}")


if __name__ == "__main__":
    main()
