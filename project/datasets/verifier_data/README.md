# 抓取验证器数据集说明

## 目录结构

- `success/`：抓取成功瞬间的腕部相机图片（标签 1）
- `failure/`：抓取失败（未抓到/掉落）瞬间的腕部相机图片（标签 0）

## 采集方法

1. 运行 rollout（`eval_rollout.sh`）并录像；
2. 从视频中截取"夹爪闭合动作结束"那一帧；
3. 按结果分别放入 success/ 与 failure/；
4. 目标：总数 100–200 张，两类尽量均衡。

## 生成索引

```bash
python project/scripts/prepare_verifier_data.py \
  --data project/datasets/verifier_data --out project/datasets/verifier_data
```

## 训练

```bash
python project/scripts/train_verifier.py \
  --train project/datasets/verifier_data/train.txt \
  --val project/datasets/verifier_data/val.txt \
  --epochs 20
```

验收标准：验证集准确率 ≥ 95%，否则补数据或调参。
