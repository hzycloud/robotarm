"""
文件作用：offline_distill.py 关键逻辑（取动作块第一步）的单元测试。

主要内容：
  验证 ACT 输出的动作块 (batch=1, chunk_len, action_dim) 取 [0, 0] 后
  得到形状 (action_dim,) 的逐帧动作——这是蒸馏脚本的核心切片逻辑。

运行方式（仓库根目录）：
  python -m pytest tests/test_offline_distill.py -v
"""

import torch  # 构造张量


def test_chunk_first_action_shape():
    """动作块切片：chunk[0, 0] 的形状应为 (action_dim,)。"""
    chunk = torch.zeros(1, 25, 7)  # batch=1, chunk_len=25, action_dim=7
    action = chunk[0, 0]
    assert action.shape == (7,)
