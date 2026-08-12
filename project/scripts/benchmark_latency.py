"""
文件作用：在 Pi 5 上测量 PyTorch 策略的原始推理延迟（FP32 基线），
         与 ONNX int8 部署（benchmark_onnx.py）对比，量化优化收益。

主要内容：
  1. 加载 PreTrainedPolicy（完整 checkpoint 目录）；
  2. 构造 dummy state 输入，连续推理 N 次；
  3. 输出平均延迟（ms）与等效 FPS。

运行方式（Pi 5，lerobot 环境内）：
  python benchmark_latency.py --policy ~/act_model/pretrained_model --n 100
"""

import argparse  # 解析命令行参数
import time  # 计时

import torch  # 推理
from lerobot.common.policies.pretrained import PreTrainedPolicy  # 加载策略


def main():
    """主流程：加载策略 → 测 N 次推理延迟 → 输出 ms/FPS。"""
    ap = argparse.ArgumentParser(description="Benchmark PyTorch policy latency")
    ap.add_argument("--policy", required=True, help="pretrained_model directory")
    ap.add_argument("--n", type=int, default=100, help="number of inferences")
    args = ap.parse_args()

    # 1. 加载策略并切换到评估模式
    policy = PreTrainedPolicy.from_pretrained(args.policy)
    policy.eval()

    # 2. dummy state（batch=1），state 维度从配置读取
    state = torch.zeros(1, policy.config.state_dim)

    # 3. 计时推理 N 次
    t0 = time.perf_counter()
    for _ in range(args.n):
        with torch.no_grad():
            policy.select_action(state)
    dt = (time.perf_counter() - t0) / args.n
    print(f"avg_ms={dt * 1000:.1f} fps={1 / dt:.2f}")


if __name__ == "__main__":
    main()
