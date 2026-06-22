"""Agent 可调用的工具集合。

新增工具步骤:
1. 在本目录下新建 xxx_tool.py,用 @tool 装饰一个带 docstring 的函数
   (docstring 就是给模型看的"什么时候该调用"说明,务必写清楚)。
2. 在下面 import 并加入 ALL_TOOLS 列表即可。
"""

from core.agent.tools.time_tool import get_beijing_time

ALL_TOOLS = [
    get_beijing_time,
]
