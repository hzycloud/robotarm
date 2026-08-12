# Related Work（初稿，投稿前按最新文献扩充）

## TinyML 与边缘计算机械臂

- 基线：Hu et al., Eng. Proc. 2025——Edge Impulse 黑盒、开环、7.6s 识别。
- TinyML 综述与低功耗 MCU 部署（Warden & Situnayake, O'Reilly 2019）。
- 边缘设备上的实时识别与机械臂控制工作（检索后按 2023-2026 最新文献扩充）。

## 模仿学习与 ACT

- ACT：Action Chunking with Transformers（Zhao et al., CoRL 2023）。
- LeRobot：开源端到端机器人学习库（Cadene et al., ICLR 2026）。
- SO-ARM101 是 LeRobot 官方 reference hardware。

## 策略压缩与边缘部署

- 知识蒸馏（Hinton et al.）、量化（PTQ/QAT）、ONNX Runtime int8。
- 相关公开实验表明：推理频率与训练频率不匹配会显著降低 ACT 成功率
  （SO-ARM101 + ACT 实测：30Hz→15Hz 时成功率从 90% 降至 40%）。
- 本文 TinyACT 与该证据直接相关：边缘部署必须保持时序一致性。

## 抓取验证与闭环纠错

- 视觉抓取结果验证（成功检测）、重试策略的相关工作（检索后补充）。

## 差距

现有工作要么在强硬件（UR5 + 工作站）上做演示级系统，要么在仿真中验证算法；
缺少"低成本臂 + 端侧闭环 + 能耗/时延可量化 + 开源数据"的组合。
