"""
文件作用：训练抓取验证器——一个二分类模型，输入腕部相机抓取后画面，
         输出"抓到(1)/没抓到(0)"，用于闭环重试机制的自动判据。

主要内容：
  1. 从 train.txt/val.txt 读取图片与标签（prepare_verifier_data.py 生成）；
  2. 用 MobileNetV3-Small（ImageNet 预训练）替换分类头为 2 类；
  3. 训练 20 个 epoch，输出每轮验证集准确率；
  4. 保存 verifier.pt，后续用 export/quantize 流程转 int8 ONNX。

运行方式（A100）：
  python train_verifier.py --train train.txt --val val.txt --epochs 20

验收标准：验证集准确率 >= 95%；不足则增加数据或调学习率。
"""

import argparse  # 解析命令行参数
from pathlib import Path  # 读取索引文件

import torch  # 深度学习框架
from torch import nn  # 网络层与损失
from torch.utils.data import DataLoader, Dataset  # 数据加载
from torchvision import transforms  # 图像预处理
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights  # 轻量骨干
from PIL import Image  # 读图


class ImgDir(Dataset):
    """从索引文件读取图片与标签的数据集类。"""

    def __init__(self, txt):
        # 每行格式：路径 标签(0/1)
        self.items = [
            (p, int(l)) for p, l in (line.split() for line in Path(txt).read_text().splitlines())
        ]
        # 预处理：缩放到 224x224、归一化到 ImageNet 均值/方差（与预训练权重匹配）
        self.tf = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, label = self.items[i]
        return self.tf(Image.open(path).convert("RGB")), label


def main():
    """主流程：加载数据 → 微调 MobileNetV3-Small → 保存模型。"""
    ap = argparse.ArgumentParser(description="Train grasp verifier")
    ap.add_argument("--train", required=True, help="train.txt")
    ap.add_argument("--val", required=True, help="val.txt")
    ap.add_argument("--epochs", type=int, default=20)
    args = ap.parse_args()

    # 1. 模型：ImageNet 预训练 MobileNetV3-Small，只换最后一层分类头为 2 类
    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, 2)

    # 2. 优化器与损失：AdamW + 交叉熵
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    lossf = nn.CrossEntropyLoss()
    train_dl = DataLoader(ImgDir(args.train), batch_size=16, shuffle=True)
    val_dl = DataLoader(ImgDir(args.val), batch_size=16)

    # 3. 训练循环：每个 epoch 打印 loss 与验证集准确率
    for ep in range(args.epochs):
        model.train()
        tot = 0
        for x, y in train_dl:
            opt.zero_grad()
            loss = lossf(model(x), y)
            loss.backward()
            opt.step()
            tot += loss.item()
        model.eval()
        correct = sum((model(x).argmax(1) == y).sum().item() for x, y in val_dl)
        n = sum(len(y) for _, y in val_dl)
        print(f"epoch {ep}: loss={tot / len(train_dl):.3f} val_acc={correct / n:.3f}")

    # 4. 保存权重（完整模型转 ONNX 时用）
    torch.save(model.state_dict(), "verifier.pt")
    print("saved verifier.pt")


if __name__ == "__main__":
    main()
