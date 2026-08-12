"""
文件作用：Edge-Sort 项目的配置校验工具。

本文件提供两个纯函数，供所有需要读取相机配置 / 数据集 ID 的脚本复用：
- validate_camera_json(text)：解析相机配置 JSON 字符串，校验其中必须包含
  "front"（外部 200W 相机）与 "wrist"（腕部 30W 相机）两个相机，且每个
  相机都满足 LeRobot 的 opencv 相机约定（类型 opencv、分辨率 > 0）。
- validate_repo_id(repo_id)：校验 Hugging Face 数据集 ID 是否形如
  "用户名/数据集名"（例如 alice/so101_sort）。

后续 Task 6/10 的 shell 脚本（遥操作、录制数据）会调用这里的同一套规则，
保证相机配置和数据集 ID 在任何环节都不会出现拼写或格式不一致的问题。
"""

import json  # 解析相机配置的 JSON 文本
import re  # 用正则表达式校验数据集 ID 的格式


def validate_camera_json(text):
    """校验相机配置 JSON，返回解析后的字典。

    参数：
        text (str)：JSON 字符串，形如 {"front": {...}, "wrist": {...}}。
    返回：
        dict：解析后的相机配置字典。
    抛出：
        AssertionError：缺少 front/wrist 相机，或相机配置不满足 opencv
        约定（类型不是 opencv / 宽高不为正数）时抛出。
    """
    data = json.loads(text)  # 第 1 步：把 JSON 字符串解析成 Python 字典
    for name in ("front", "wrist"):  # 第 2 步：逐个检查两个必备相机
        assert name in data, f"missing camera: {name}"  # 2a. 相机名必须存在
        cam = data[name]
        assert cam.get("type") == "opencv", f"{name}: type must be opencv"  # 2b. 类型必须是 opencv
        assert cam.get("width", 0) > 0 and cam.get("height", 0) > 0  # 2c. 宽高必须为正数
    return data  # 第 3 步：校验通过，返回配置字典供调用方使用


def validate_repo_id(repo_id):
    """校验 Hugging Face 数据集 ID 是否为合法的“用户名/数据集名”格式。

    参数：
        repo_id (str)：待校验的 ID，例如 "alice/so101_sort"。
    返回：
        bool：格式合法返回 True，否则返回 False。
    """
    # 正则匹配规则：斜杠前后各为一组字符，允许字母、数字、点、下划线、短横线
    return bool(re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", repo_id))
