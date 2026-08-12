"""
文件作用：把抓取验证器的训练图片整理成 train.txt / val.txt 索引文件。

主要内容：
  1. 扫描 success/（抓到）与 failure/（没抓到）两个目录下的图片；
  2. 按 8:2 随机划分训练/验证集；
  3. 每行输出"图片路径 标签"（标签：success=1，failure=0）。

数据准备方法（人工操作）：
  从成功/失败的 rollout 视频中截取"抓取动作结束瞬间"的腕部相机帧，
  按类别放入 project/datasets/verifier_data/success/ 与 failure/。

运行方式（A100 或本地）：
  python prepare_verifier_data.py \
    --data project/datasets/verifier_data --out project/datasets/verifier_data
"""

import argparse  # 解析命令行参数
import random  # 随机划分
from pathlib import Path  # 跨平台路径处理


def main():
    """主流程：扫描图片目录 → 写 train.txt / val.txt。"""
    ap = argparse.ArgumentParser(description="Prepare verifier train/val split")
    ap.add_argument("--data", required=True, help="dir containing success/ and failure/")
    ap.add_argument("--out", required=True, help="output dir for train.txt/val.txt")
    ap.add_argument("--seed", type=int, default=42, help="random seed for reproducibility")
    args = ap.parse_args()

    data_dir = Path(args.data)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 收集 (路径, 标签)：success 目录标签 1，failure 目录标签 0
    items = []
    for label, sub in ((1, "success"), (0, "failure")):
        for img in (data_dir / sub).glob("*.jpg"):
            items.append((str(img), label))
    if len(items) < 20:
        raise SystemExit(f"too few images: {len(items)} (need >=20)")

    # 2. 固定随机种子，保证可复现的 8:2 划分
    random.seed(args.seed)
    random.shuffle(items)
    split = int(len(items) * 0.8)
    train_items, val_items = items[:split], items[split:]

    # 3. 写索引文件：每行 "路径 标签"
    for name, part in (("train.txt", train_items), ("val.txt", val_items)):
        (out_dir / name).write_text("\n".join(f"{p} {l}" for p, l in part) + "\n", encoding="utf-8")
        print(name, len(part), "samples")


if __name__ == "__main__":
    main()
