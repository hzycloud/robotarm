"""
文件作用：把 FP32 的 ONNX 策略模型动态量化为 INT8（权重 8bit），
         大幅减小模型体积并加速 Pi 5 CPU 推理。

主要内容：
  1. 读取 FP32 ONNX；
  2. 用 onnxruntime 的 quantize_dynamic 做动态量化（仅量化权重，无需校准集）；
  3. 输出 int8 ONNX。

运行方式（Pi 5 或 A100）：
  python quantize_onnx.py --in tinyact.onnx --out tinyact_int8.onnx

注意：
  - 动态量化最简单、零校准数据；若精度损失超过可接受范围（成功率下降 >1 次试次），
    改用静态 QDQ 量化（用数据集 100 帧做校准集）。
  - Pi 5 需要安装 ARM64 版 onnxruntime：pip install onnxruntime
"""

import argparse  # 解析命令行参数

from onnxruntime.quantization import quantize_dynamic, QuantType  # 动态量化工具


def main():
    """主流程：动态量化 FP32 ONNX → INT8 ONNX。"""
    ap = argparse.ArgumentParser(description="Quantize ONNX model to int8")
    ap.add_argument("--in", dest="input", required=True, help="input fp32 .onnx")
    ap.add_argument("--out", required=True, help="output int8 .onnx")
    args = ap.parse_args()

    # 动态量化：只量化权重（QInt8），激活仍按 float 计算，适合快速部署
    quantize_dynamic(args.input, args.out, weight_type=QuantType.QInt8)
    print("quantized", args.out)


if __name__ == "__main__":
    main()
