from datetime import datetime, timezone, timedelta

from langchain_core.tools import tool

# 北京时区 (UTC+8),不依赖系统本地时区,保证结果稳定
BEIJING_TZ = timezone(timedelta(hours=8))


@tool
def get_beijing_time() -> str:
    """获取当前的北京时间(UTC+8)。

    当用户询问“现在几点”“今天的日期”或任何需要当前时间的场景时调用本工具。
    返回格式为 'YYYY-MM-DD HH:MM:SS' 的字符串。
    """
    now = datetime.now(BEIJING_TZ)
    return now.strftime("%Y-%m-%d %H:%M:%S")
