# Edge-Sort 项目说明

Edge-Sort 是一个基于 LeRobot 的端侧闭环桌面分拣系统，研究轻量模仿学习策略（TinyACT）在低成本六轴机械臂上的部署，并完成抓取验证闭环与能耗时延基准。

## 1 硬件清单

- SO-ARM101 主从双臂，leader 示教臂与 follower 执行臂，六自由度，六组 STS3215 总线舵机
- 双相机，腕部 30W 手眼相机与外部 200W 全局相机
- Raspberry Pi 5 8GB，负责端侧推理与决策
- NVIDIA A100，负责策略训练

## 2 软件与版本

LeRobot 版本计划固定为 v0.4.4，实际版本以安装后 pip show lerobot 的输出为准并回填本节。Python 使用 3.10，运行环境为 miniforge 创建的 lerobot conda 环境。

## 3 环境变量

所有采集与训练命令需要先设置环境变量：

```bash
export HF_USER=<你的HuggingFace用户名>
```

数据集 repo_id 统一为 `${HF_USER}/so101_sort`。

## 4 安全规则

机械臂运行时清空一米内的人员与贵重物品；上电后不得触摸关节；插拔线缆前断电；出现异常运行立即断电。

## 5 代码注释规范

每个代码文件顶部必须用注释写明主要作用与主要内容；每个函数、类、关键代码块前必须有详细中文注释，解释功能、输入输出与设计意图。

## 6 文档写作规范

Markdown 文档采用论文版式：标题后使用编号章节，段落以平实文本为主，减少加粗、表情符号、勾选框与嵌套列表等装饰性符号；表格仅在需要对照数据时使用。

## 7 Pi 5 环境记录（附录）

- 系统：Raspberry Pi OS 64-bit（aarch64），2026-08 安装并启用 SSH。
- 包管理器：Miniforge（aarch64 版），conda 环境 lerobot（Python 3.10）。
- LeRobot：v0.4.4（2026-08-21 安装，pip show lerobot 确认；源码位于 ~/lerobot）。
- 安装方式：~/pisetup.sh（克隆 huggingface/lerobot 并固定 v0.4.4，可重复执行；非交互 shell 下会自动导入 conda profile）。
- SSH：用户 pi，地址以 <Pi的IP> 占位。实际地址只记录在本地台账，不写入仓库（仓库将开源）。
- 相机与端口：待机械臂接入后，用 lerobot-find-port 与 lerobot-find-cameras opencv 实测，写入 project/configs/cameras.json。
- 维护：安装确认后可用 conda clean --all 与 pip cache purge 清理缓存，不影响已装环境。
