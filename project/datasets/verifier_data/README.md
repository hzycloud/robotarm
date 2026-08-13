# 抓取验证器数据集说明

## 1 目录结构

success 目录存放抓取成功瞬间的腕部相机图片，标签为 1；failure 目录存放抓取失败瞬间的腕部相机图片，标签为 0。

## 2 采集方法

运行 rollout 并录像，从视频中截取夹爪闭合动作结束的那一帧，按结果分别放入 success 与 failure 目录。目标总量 100 到 200 张，两类尽量均衡。

## 3 生成索引

```bash
python project/scripts/prepare_verifier_data.py \
  --data project/datasets/verifier_data --out project/datasets/verifier_data
```

## 4 训练

```bash
python project/scripts/train_verifier.py \
  --train project/datasets/verifier_data/train.txt \
  --val project/datasets/verifier_data/val.txt \
  --epochs 20
```

验收标准为验证集准确率不低于 95%，不足时补充数据或调整参数。
