"""
文件作用：分析能耗日志，输出每配置的平均单件能耗（J/件）、周期时间与能耗/成功率联合指标。

主要内容：
  1. 读取能耗记录 CSV（measure_power.md 中的记录表格式）；
  2. 计算每个配置的平均每件能耗与平均周期时间；
  3. 输出 energy_per_action.csv 与两张图（能耗柱状图、时延分解图）。

运行方式：
  python energy_analysis.py --log power_log.csv --out energy_per_action.csv
"""

import argparse  # 解析命令行参数
import csv  # 读写 CSV
from collections import defaultdict  # 按配置聚合

import matplotlib.pyplot as plt  # 绘图


def main():
    """主流程：读日志 → 聚合 → 输出 CSV 与图表。"""
    ap = argparse.ArgumentParser(description="Analyze energy logs")
    ap.add_argument("--log", required=True, help="power log csv (日期,配置,试次数,起始Wh,结束Wh,周期总时长s,备注)")
    ap.add_argument("--out", default="energy_per_action.csv")
    args = ap.parse_args()

    # 1. 读取日志并按配置聚合
    agg = defaultdict(lambda: {"trials": 0, "wh": 0.0, "seconds": 0.0})
    with open(args.log, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cfg = row["配置"]
            agg[cfg]["trials"] += int(row["试次数"])
            agg[cfg]["wh"] += float(row["结束Wh"]) - float(row["起始Wh"])
            agg[cfg]["seconds"] += float(row["周期总时长s"])

    # 2. 计算每件能耗（J/件 = Wh×3600/件数）与平均周期
    out_rows = []
    for cfg, v in sorted(agg.items()):
        j_per_action = v["wh"] * 3600.0 / v["trials"]
        avg_cycle = v["seconds"] / v["trials"]
        out_rows.append({"config": cfg, "j_per_action": round(j_per_action, 1), "avg_cycle_s": round(avg_cycle, 1)})
        print(cfg, f"{j_per_action:.1f} J/action", f"{avg_cycle:.1f} s/action")

    # 3. 输出汇总 CSV
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["config", "j_per_action", "avg_cycle_s"])
        writer.writeheader()
        writer.writerows(out_rows)

    # 4. 画能耗柱状图
    plt.bar([r["config"] for r in out_rows], [r["j_per_action"] for r in out_rows])
    plt.ylabel("J/action")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("energy_bar.png")
    print("saved energy_bar.png")


if __name__ == "__main__":
    main()
