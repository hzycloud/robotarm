# 实验结果表结构

所有实验 CSV 统一使用以下列，便于后续汇总与论文制表。

| 列名 | 类型 | 说明 |
|---|---|---|
| config | str | 配置名，取值 teacher_gpu、tinyact_fp32、tinyact_int8、closed_loop_int8、tinyact_int8_singlecam |
| trial | int | 试次编号，从 0 开始 |
| success | int | 1 表示成功，0 表示失败 |
| failure_type | str | 失败分类，取值 none、not_grasped、dropped、wrong_slot、abnormal |
| retries | int | 重试次数，开环配置固定为 0 |
| cycle_s | float | 单件周期时间，单位秒 |
| inference_ms | float | 单次策略推理延迟，单位毫秒 |
| notes | str | 备注 |
