"""
文件作用：把训练好的 TinyACT PyTorch 策略导出为 ONNX 模型，供后续 int8 量化与
          Pi 5 上的 ONNX Runtime 部署使用。

主要内容：
  1. 用 PreTrainedPolicy 加载 checkpoint；
  2. 构造固定尺寸的 dummy 输入（front/wrist 图像 + state）；
  3. 用 torch.onnx.export 导出，输入名 front/wrist/state，输出名 action_chunk；
  4. 只对 state 的 batch 维度做动态轴，图像保持固定尺寸以简化量化。

运行方式（A100，lerobot 环境内）：
  python export_onnx.py \
    --policy outputs/train/tinyact_distill_so101_sort/checkpoints/last/pretrained_model \
    --out tinyact.onnx

注意：
  如果 select_action 的输入签名不是字典形式（不同 LeRobot 版本可能不同），
  按运行时报错调整 forward 包装函数即可。
"""

import argparse  # 解析命令行参数

import torch  # 模型加载与导出
from lerobot.common.policies.pretrained import PreTrainedPolicy  # 加载策略


def main():
    """主流程：加载策略 → 导出 ONNX。"""
    ap = argparse.ArgumentParser(description="Export TinyACT policy to ONNX")
    ap.add_argument("--policy", required=True, help="pretrained_model directory")
    ap.add_argument("--out", required=True, help="output .onnx path")
    ap.add_argument("--img", type=int, default=224, help="square input image size")
    args = ap.parse_args()

    # 1. 加载策略并切到评估模式
    policy = PreTrainedPolicy.from_pretrained(args.policy).eval()

    # 2. dummy 输入：batch=1，图像 3 通道；state 维度从策略配置读取
    front = torch.zeros(1, 3, args.img, args.img)
    wrist = torch.zeros(1, 3, args.img, args.img)
    state = torch.zeros(1, policy.config.state_dim)

    # 3. 包装 forward：把三个输入映射为策略期望的观测字典
    def forward(front, wrist, state):
        return policy.select_action(
            {
                "observation.images.front": front,
                "observation.images.wrist": wrist,
                "observation.state": state,
            }
        )

    # 4. 导出：固定图像尺寸，仅 state 的 batch 维度动态（方便真机按 1 帧调用）
    torch.onnx.export(
        policy,
        (front, wrist, state),
        args.out,
        input_names=["front", "wrist", "state"],
        output_names=["action_chunk"],
        opset_version=17,
        dynamic_axes={"state": {0: "batch"}},
    )
    print("exported", args.out)


if __name__ == "__main__":
    main()
