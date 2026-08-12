"""
文件作用：离线动作蒸馏——用训练好的 ACT 教师策略为整个数据集生成动作标签，
         产出一个"蒸馏数据集"（动作被替换为教师输出），供 TinyACT 学生用标准训练器学习。

主要内容：
  1. 加载教师策略（--teacher 指向 pretrained_model 目录）；
  2. 逐 episode 读取源数据集（--src，例如 alice/so101_sort）；
  3. 对每个状态调用 teacher.select_action，取动作块第一步作为该帧的动作标签；
  4. 用 LeRobotDataset.create 创建新数据集（--dst，例如 alice/so101_sort_distill）；
  5. 保存新数据集，之后用 train_tinyact.sh 把 repo_id 换成蒸馏数据集即可训练学生。

为什么取动作块第一步：
  ACT 一次预测一段长度为 chunk_len 的未来动作；离线蒸馏采用最简形式——
  每帧只保留教师对"当前步"的动作，等价于把教师策略压成逐帧 BC 目标。

运行方式（A100，lerobot 环境内）：
  python offline_distill.py \
    --teacher outputs/train/act_so101_sort/checkpoints/last/pretrained_model \
    --src alice/so101_sort \
    --dst alice/so101_sort_distill

注意：
  LeRobot v0.4.x 的 API 可能与本脚本略有出入；若 LeRobotDataset.create /
  get_episode_data / add_episode 名称不符，按运行时报错修正：
  python -c "from lerobot.common.datasets.lerobot_dataset import LeRobotDataset as D; print([x for x in dir(D) if not x.startswith('_')])"
"""

import argparse  # 解析命令行参数

import torch  # 张量运算与 GPU 推理
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset  # 读写 LeRobot 数据集
from lerobot.common.policies.pretrained import PreTrainedPolicy  # 加载训练好的策略


def main():
    """主流程：教师推理 → 生成蒸馏数据集。"""
    # 1. 命令行参数：教师路径、源数据集、目标数据集、数据根目录
    ap = argparse.ArgumentParser(description="Offline action distillation from ACT teacher to dataset")
    ap.add_argument("--teacher", required=True, help="teacher pretrained_model directory")
    ap.add_argument("--src", required=True, help="source dataset repo_id, e.g. alice/so101_sort")
    ap.add_argument("--dst", required=True, help="distilled dataset repo_id, e.g. alice/so101_sort_distill")
    ap.add_argument("--root", default="~/.cache/huggingface/lerobot", help="dataset cache root")
    args = ap.parse_args()

    # 2. 加载教师策略并切换到评估/GPU 模式（不计算梯度，纯推理）
    teacher = PreTrainedPolicy.from_pretrained(args.teacher).to("cuda").eval()

    # 3. 打开源数据集；create() 按源数据集的 fps/features/机器人类型初始化目标数据集
    src = LeRobotDataset(args.src, root=args.root)
    dst = LeRobotDataset.create(
        args.dst,
        root=args.root,
        fps=src.fps,
        robot_type=src.robot_type,
        features=src.features,
        episodes=src.num_episodes,
    )

    # 4. 逐 episode 蒸馏：每个状态喂给教师，取动作块第一步作为动作标签
    for ep in range(src.num_episodes):
        ep_data = src.get_episode_data(ep)  # 该 episode 的观测/状态/动作数据
        states = ep_data["observation.state"]  # 形状 (T, state_dim)
        teacher_actions = []  # 收集教师逐帧动作
        for i in range(states.shape[0]):
            with torch.no_grad():  # 关闭梯度，省显存
                chunk = teacher.select_action(states[i : i + 1].to("cuda"))
            teacher_actions.append(chunk[0, 0])  # chunk: (1, chunk_len, action_dim) → 取第 0 帧
        actions = torch.stack(teacher_actions).cpu()  # 回 CPU，写入数据集
        dst.add_episode(ep_data, actions=actions)
        print(f"episode {ep}/{src.num_episodes} done")

    # 5. 保存蒸馏数据集（parquet + 视频帧信息）
    dst.save_episodes()
    print("distillation finished:", args.dst)


if __name__ == "__main__":
    main()
