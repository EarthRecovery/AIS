from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class StoryBlueprint(Base):
    """故事蓝图 (STORY 层 S1)：一个世界「在讲什么故事、要走向哪个结局」的北极星。

    WORLD 层(角色/场景/事件)回答「发生了什么」；STORY 层在其之上回答「这是什么故事、
    讲到哪、离结局差什么」。本表是叙事智能的根：中心前提 + 中心冲突 + 主题 + 意图结局集。

    自主导演(S6)读它来规划下一个戏剧动作，结局判定器(S7)拿它的「结局条件」对照当前
    世界状态判断是否收束。一个世界一份蓝图(world_id 唯一)。
    """

    __tablename__ = "ais_story_blueprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 一个世界一份蓝图
    world_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)

    # ---- S1 北极星：故事的「是什么」 ----
    # 中心前提：一句话概括这个故事的核心情境/钩子
    premise: Mapped[str] = mapped_column(Text, nullable=True)
    # 中心冲突：贯穿全篇、推动一切的根本对抗(谁 vs 谁/什么，争什么)
    central_conflict: Mapped[str] = mapped_column(Text, nullable=True)
    # 主题：故事想探讨/表达的东西
    theme: Mapped[str] = mapped_column(Text, nullable=True)
    # 意图结局 / 可接受结局集：达成任一即可收束。
    #   [{"title":..,"summary":..,"conditions":["可被验证的收束条件", ...]}]
    intended_endings: Mapped[list] = mapped_column(JSON, nullable=True, default=list)

    # ---- S2 戏剧结构(钩子，本期最小化)：故事的「在哪」 ----
    # 弧线位置：setup(铺垫) / rising(升级) / climax(高潮) / resolution(收束)
    dramatic_phase: Mapped[str] = mapped_column(String(20), nullable=False, default="setup")
    # 目标张力形状里「此刻该有多紧」的目标值 0-100(供 S6 调度节奏)
    tension_target: Mapped[int] = mapped_column(Integer, nullable=True)

    # ---- 运行态 ----
    # planning(蓝图草拟中) / active(推进中) / converging(收束中) / completed(已抵达结局)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # S6 最近一次规划结果(交给模拟层演出的「下一个戏剧动作」)：
    #   {"action_type":..,"rationale":..,"pov":..,"scene_function":..,"directive":..}
    last_plan: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    # S7 最近一次结局判定：
    #   {"completed":bool,"which_ending":..,"satisfied":[..],"unmet":[..],"needs_epilogue":bool,"reason":..}
    ending_verdict: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
