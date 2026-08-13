# 舵机设置与主从臂校准记录

## 1 环境信息

| 项目 | 值 |
|---|---|
| 日期 | |
| Pi 5 IP | |
| follower 端口 | /dev/ttyACM0，以 lerobot-find-port 实测为准 |
| leader 端口 | /dev/ttyACM1 |
| follower id | my_awesome_follower_arm |
| leader id | my_awesome_leader_arm |

## 2 舵机设置

使用 lerobot-setup-motors 为每个舵机设置 ID 与波特率，从 6 号夹爪舵机开始，依次到 1 号。

| 关节 | 舵机 ID | 校准状态 | 备注 |
|---|---|---|---|
| 1 shoulder_pan | 1 | | |
| 2 shoulder_lift | 2 | | |
| 3 elbow | 3 | | |
| 4 wrist_flex | 4 | | |
| 5 wrist_roll | 5 | | 终端收不到 5 号信号属正常 |
| 6 gripper | 6 | | |

## 3 校准记录

使用 lerobot-calibrate 分别校准 follower 与 leader，校准文件位于 ~/.cache/huggingface/lerobot/ 下对应 id 的目录。记录校准完成时间与异常现象。

## 4 验收

follower 与 leader 在相同物理位姿时读数一致，遥操作无抖动、无卡顿。
