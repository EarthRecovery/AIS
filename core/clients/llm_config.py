import os

# 全站对话 / 推演统一使用的大模型。可用环境变量 AIS_CHAT_MODEL 覆盖。
CHAT_MODEL = os.getenv("AIS_CHAT_MODEL", "gpt-5.5")

# 成稿（写作层）单独可配；默认与对话同。可用 AIS_WRITING_MODEL 单独换更强/不同的模型。
WRITING_MODEL = os.getenv("AIS_WRITING_MODEL", CHAT_MODEL)
