"""
文件作用：Edge-Sort 核心主程序——在 Pi 5 上把 TinyACT 策略推理、机械臂执行、
         抓取验证器与重试逻辑串成完整闭环分拣流程。

主要内容：
  1. 加载 int8 ONNX 策略（front/wrist/state → action_chunk）与验证器（wrist 图 → 抓到与否）；
  2. 用 LeRobot make_robot 连接 so101_follower；
  3. 每轮试次：读观测 → 策略推理 → 逐动作执行 → 腕部验证 → 失败重试（最多 N 次）；
  4. 结果写入 CSV：trial/retries/grabbed/cycle_s。

运行方式（Pi 5，lerobot 环境内）：
  python closed_loop_sort.py \
    --policy tinyact_int8.onnx --verifier verifier.onnx \
    --trials 30 --max_retries 2 --out closed_loop_results.csv

注意：
  LeRobot v0.4.x 的 robot API 方法名可能不同；先运行
  python -c "from lerobot.robots.factory import make_robot; r=make_robot('so101_follower',port='/dev/ttyACM0',id='my_awesome_follower_arm'); print([x for x in dir(r) if not x.startswith('_')])"
  按输出调整 read_observation / send_action / 夹爪开合动作的方法名。
"""

import argparse  # 解析命令行参数
import csv  # 写实验结果
import time  # 计时

import numpy as np  # 图像与张量处理
import onnxruntime as ort  # CPU 推理
from lerobot.robots.factory import make_robot  # 连接 SO-ARM101


def verify_grasp(verifier, wrist_img):
    """用验证器判断夹爪是否抓到物体。

    参数：
      verifier: ONNX Runtime 会话（输入 image，输出 2 类 logits）
      wrist_img: 腕部相机 PIL/array 图像
    返回：
      int：1=抓到，0=没抓到
    """
    img = np.asarray(wrist_img.resize((224, 224))).astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))[None]  # HWC→CHW 并加 batch 维
    out = verifier.run(None, {"image": img})[0]
    return int(out.argmax())


def main():
    """主流程：策略+验证器+机器人 → 逐试次闭环分拣 → 写 CSV。"""
    ap = argparse.ArgumentParser(description="Closed-loop sorting with verifier and retry")
    ap.add_argument("--policy", required=True, help="int8 onnx policy path")
    ap.add_argument("--verifier", required=True, help="int8 onnx verifier path")
    ap.add_argument("--port", default="/dev/ttyACM0", help="follower serial port")
    ap.add_argument("--trials", type=int, default=30, help="number of sorting trials")
    ap.add_argument("--max_retries", type=int, default=2, help="max regrasp attempts per trial")
    ap.add_argument("--out", default="closed_loop_results.csv")
    args = ap.parse_args()

    # 1. 加载两个 int8 ONNX 模型（CPU 推理）
    policy = ort.InferenceSession(args.policy, providers=["CPUExecutionProvider"])
    verifier = ort.InferenceSession(args.verifier, providers=["CPUExecutionProvider"])

    # 2. 连接机械臂（id 必须与校准/采集时一致）
    robot = make_robot("so101_follower", port=args.port, id="my_awesome_follower_arm")

    rows = []  # 结果行集合
    for t in range(args.trials):
        obs = robot.read_observation()  # 读取双相机与关节状态
        t0 = time.perf_counter()  # 单件周期计时起点

        # 3a. 策略推理：输出动作块，逐动作下发执行
        chunk = policy.run(
            None,
            {
                "front": np.asarray(obs["observation.images.front"])[None],
                "wrist": np.asarray(obs["observation.images.wrist"])[None],
                "state": np.asarray(obs["observation.state"])[None].astype(np.float32),
            },
        )[0]
        for a in chunk:
            robot.send_action(a)

        # 3b. 抓取后验证；失败则松开重抓，最多 max_retries 次
        grabbed = verify_grasp(verifier, obs["observation.images.wrist"])
        retries = 0
        while not grabbed and retries < args.max_retries:
            robot.send_action(robot.gripper_open_action())  # 松开夹爪
            obs = robot.read_observation()  # 重新观测
            chunk = policy.run(
                None,
                {
                    "front": np.asarray(obs["observation.images.front"])[None],
                    "wrist": np.asarray(obs["observation.images.wrist"])[None],
                    "state": np.asarray(obs["observation.state"])[None].astype(np.float32),
                },
            )[0]
            for a in chunk:
                robot.send_action(a)
            grabbed = verify_grasp(verifier, obs["observation.images.wrist"])
            retries += 1

        # 4. 记录本试次结果
        rows.append(
            {
                "trial": t,
                "retries": retries,
                "grabbed": grabbed,
                "cycle_s": time.perf_counter() - t0,
            }
        )
        print(f"trial {t}: grabbed={grabbed} retries={retries}")

    # 5. 写 CSV（实验矩阵后续统一汇总）
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("done", args.out)


if __name__ == "__main__":
    main()
