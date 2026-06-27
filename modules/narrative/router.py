"""叙事层 API：故事蓝图(S1) + 自主导演(S6) + 结局判定(S7)。

挂在 WORLD 之上：先有世界(/world)，再用 /narrative 给它一个「故事」与「结局目标」，
然后让导演规划下一幕、判定是否收束。
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.security.deps import get_request_user_id
from modules.narrative.service import StoryService

router = APIRouter(prefix="/narrative", tags=["narrative"])


class Directive(BaseModel):
    directive: str | None = ""


class AutoRequest(BaseModel):
    directive: str | None = ""
    # 本次自动驾驶最多推进几幕(安全上限，避免无限跑)
    max_scenes: int | None = 4
    # 每幕最多几轮对话
    max_rounds: int | None = None


class BlueprintUpdate(BaseModel):
    premise: str | None = None
    central_conflict: str | None = None
    theme: str | None = None
    intended_endings: list | None = None
    dramatic_phase: str | None = None
    tension_target: int | None = None
    status: str | None = None


# ---- S1 故事蓝图 ----
@router.get("/{world_id}/blueprint")
async def get_blueprint(world_id: int, svc: StoryService = Depends()):
    """取这个世界的故事蓝图(没有则返回 null，前端可提示去生成)。"""
    return await svc.get_blueprint(world_id)


@router.post("/{world_id}/blueprint/generate")
async def generate_blueprint(world_id: int, req: Directive, svc: StoryService = Depends(),
                             user_id: str = Depends(get_request_user_id)):
    """让导演读世界、草拟故事蓝图(中心冲突/主题/可接受结局集)并落库。"""
    return await svc.generate_blueprint(world_id, (req.directive or "").strip())


@router.patch("/{world_id}/blueprint")
async def update_blueprint(world_id: int, req: BlueprintUpdate, svc: StoryService = Depends()):
    """手工编辑蓝图(改中心冲突/结局条件/弧线位置等)。"""
    out = await svc.update_blueprint(world_id, req.model_dump(exclude_unset=True))
    if out is None:
        raise HTTPException(404, "该世界尚无故事蓝图，请先生成")
    return out


# ---- S6 自主导演：下一个戏剧动作 ----
@router.post("/{world_id}/plan")
async def plan_next(world_id: int, req: Directive, svc: StoryService = Depends(),
                    user_id: str = Depends(get_request_user_id)):
    """评估故事状态→决定下一个戏剧动作，并产出交给模拟层的 directive。"""
    out = await svc.plan_next(world_id, (req.directive or "").strip())
    if out is None:
        raise HTTPException(404, "该世界尚无故事蓝图，请先生成蓝图再规划")
    return out


# ---- S7 结局判定 ----
@router.post("/{world_id}/judge")
async def judge_ending(world_id: int, svc: StoryService = Depends(),
                       user_id: str = Depends(get_request_user_id)):
    """对照结局条件核查世界态，判断故事是否已抵达结局。"""
    out = await svc.judge_ending(world_id)
    if out is None:
        raise HTTPException(404, "该世界尚无故事蓝图，无法判定结局")
    return out


# ---- 自动驾驶：S6→WORLD→S7 闭环，自主跑向结局 ----
@router.post("/{world_id}/auto")
async def auto_advance(world_id: int, req: AutoRequest, svc: StoryService = Depends(),
                       user_id: str = Depends(get_request_user_id)):
    """非流式自动推进若干幕(规划→演出→判定)，命中结局或达上限即停。返回轨迹。"""
    kw = {"max_scenes": req.max_scenes or 4, "directive": (req.directive or "").strip()}
    if req.max_rounds:
        kw["max_rounds"] = req.max_rounds
    out = await svc.auto_advance(world_id, **kw)
    if out is None:
        raise HTTPException(404, "该世界尚无故事蓝图，请先生成蓝图")
    return out


@router.post("/{world_id}/auto/stream")
async def auto_advance_stream(world_id: int, req: AutoRequest, svc: StoryService = Depends(),
                              user_id: str = Depends(get_request_user_id)):
    """流式「自动驾驶」：导演决策 + 逐 token 演出 + 结局判定，交织直播直到收束。"""
    kw = {"max_scenes": req.max_scenes or 4, "directive": (req.directive or "").strip()}
    if req.max_rounds:
        kw["max_rounds"] = req.max_rounds

    async def gen():
        async for ev in svc.auto_advance_stream(world_id, **kw):
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\r\n\r\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
