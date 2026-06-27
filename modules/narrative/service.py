"""StoryService：STORY（叙事）层的编排服务。

把导演 agent(core/agent/director) 的决策落库，并在 STORY 与 WORLD 之间搭桥：
- S1 蓝图：generate_blueprint / get_blueprint / update_blueprint
- S6 规划：plan_next —— 产出「下一个戏剧动作」与交模拟层的 directive
- S7 判定：judge_ending —— 对照结局条件判断是否收束，命中则把蓝图标记 completed

世界态(角色/关系/事件/大纲)复用 WorldService._director_context，避免重复造数据通路；
导演决策同时写一条 WorldEvent，纳入既有的追加式时间线，便于回溯。
"""

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.clients.llm_client import LLMClient
from modules.deps import get_llm_client
from modules.communication.world_service import WorldService
from modules.communication.simulation import MAX_ROUNDS_PER_SCENE, SimulationService
from storage.db import get_db
from storage.models.story_blueprint import StoryBlueprint


# 蓝图里允许用户手工编辑的字段
_EDITABLE = {"premise", "central_conflict", "theme", "intended_endings",
             "dramatic_phase", "tension_target", "status"}


class StoryService:
    def __init__(self, llm: LLMClient = Depends(get_llm_client), db: AsyncSession = Depends(get_db)):
        self.llm = llm
        self.db = db
        # 复用世界层的上下文拼装(角色/关系/事件/大纲/时间)
        self.ws = WorldService(llm, db)
        # STORY→WORLD：把导演 directive 交给模拟层演出
        self.sim = SimulationService(llm, db)

    # ---------------- 内部 ----------------
    async def _get_blueprint(self, world_id) -> StoryBlueprint | None:
        return (await self.db.execute(
            select(StoryBlueprint).where(StoryBlueprint.world_id == world_id)
        )).scalar_one_or_none()

    @staticmethod
    def _bp_dict(bp: StoryBlueprint | None) -> dict:
        if bp is None:
            return {}
        return {
            "premise": bp.premise, "central_conflict": bp.central_conflict,
            "theme": bp.theme, "intended_endings": bp.intended_endings or [],
            "dramatic_phase": bp.dramatic_phase, "tension_target": bp.tension_target,
            "status": bp.status,
        }

    async def _story_state(self, world_id) -> tuple[dict, StoryBlueprint | None]:
        """导演规划/判定的输入：故事蓝图 + 世界态(含大纲)。"""
        world_ctx, world, _, _ = await self.ws._director_context(world_id)
        # _director_context 不含 outline，补上(S6/S7 要看节拍进度)
        world_ctx["outline"] = (world.outline or []) if world else []
        bp = await self._get_blueprint(world_id)
        return {"blueprint": self._bp_dict(bp), "world": world_ctx}, bp

    # ---------------- S1 故事蓝图 ----------------
    async def get_blueprint(self, world_id) -> dict | None:
        bp = await self._get_blueprint(world_id)
        return self.serialize(bp) if bp else None

    async def generate_blueprint(self, world_id, directive: str = "") -> dict:
        """导演读世界 → 草拟故事蓝图(中心冲突/主题/结局集) → upsert 落库。"""
        ctx, world, _, _ = await self.ws._director_context(world_id)
        ctx["outline"] = (world.outline or []) if world else []
        draft = await self.llm.director_draft_blueprint(ctx, directive)

        bp = await self._get_blueprint(world_id)
        if bp is None:
            bp = StoryBlueprint(world_id=world_id)
            self.db.add(bp)
        bp.premise = draft.get("premise") or ""
        bp.central_conflict = draft.get("central_conflict") or ""
        bp.theme = draft.get("theme") or ""
        bp.intended_endings = draft.get("intended_endings") or []
        bp.dramatic_phase = draft.get("dramatic_phase") or "setup"
        bp.tension_target = draft.get("tension_target")
        bp.status = "active"
        await self.db.commit()
        await self.db.refresh(bp)
        await self.ws.log_event(
            world_id, "story_blueprint_set",
            f"制定故事蓝图：{bp.central_conflict[:40] if bp.central_conflict else ''}",
            {"endings": [e.get("title") for e in (bp.intended_endings or [])]},
            in_world_time=(world.in_world_time if world else None),
        )
        return self.serialize(bp)

    async def update_blueprint(self, world_id, data: dict) -> dict | None:
        """用户手工编辑蓝图(中心冲突/主题/结局条件/弧线位置…)。"""
        bp = await self._get_blueprint(world_id)
        if bp is None:
            return None
        for k, v in (data or {}).items():
            if k in _EDITABLE and v is not None:
                setattr(bp, k, v)
        await self.db.commit()
        await self.db.refresh(bp)
        return self.serialize(bp)

    # ---------------- S6 自主导演 ----------------
    async def plan_next(self, world_id, directive: str = "") -> dict | None:
        """评估故事状态 → 决定下一个戏剧动作 + 给模拟层的 directive。"""
        state, bp = await self._story_state(world_id)
        if bp is None:
            return None
        plan = await self.llm.director_plan_next(state, directive)
        bp.last_plan = plan
        # 导演若判断要推进弧线位置/调整目标张力，落到蓝图上
        if plan.get("new_phase"):
            bp.dramatic_phase = plan["new_phase"]
        if plan.get("tension_target") is not None:
            bp.tension_target = plan["tension_target"]
        if plan.get("action_type") == "converge":
            bp.status = "converging"
        await self.db.commit()
        await self.ws.log_event(
            world_id, "story_plan",
            f"导演决策[{plan.get('action_type')}]：{plan.get('scene_function') or ''}",
            {"directive": plan.get("directive"), "pov": plan.get("pov")},
        )
        return plan

    # ---------------- S7 结局判定 ----------------
    async def judge_ending(self, world_id) -> dict | None:
        """对照结局条件核查世界态；命中则把蓝图标记 completed。"""
        state, bp = await self._story_state(world_id)
        if bp is None:
            return None
        verdict = await self.llm.director_judge_ending(state)
        bp.ending_verdict = verdict
        if verdict.get("completed"):
            bp.status = "completed"
        await self.db.commit()
        await self.ws.log_event(
            world_id, "story_ending_judged",
            ("故事抵达结局：" + (verdict.get("which_ending") or "")) if verdict.get("completed")
            else "结局判定：尚未收束",
            {"completed": verdict.get("completed"), "unmet": verdict.get("unmet")},
        )
        return verdict

    # ---------------- 自动驾驶：S6→WORLD→S7 闭环 ----------------
    # 这是「自主跑向结局」的主循环：每一幕，导演(S6)决定下一个戏剧动作并产出 directive，
    # 交模拟层(WORLD)实际演出一场戏改变世界真值，再由判定器(S7)核对是否抵达结局；
    # 命中结局或达到幕数上限即停。directive 是 STORY→WORLD 的唯一接口。

    async def auto_advance(self, world_id, max_scenes: int = 4, directive: str = "",
                           max_rounds: int = MAX_ROUNDS_PER_SCENE) -> dict | None:
        """非流式自动推进若干幕，返回每一幕的 (规划→演出→判定) 轨迹。"""
        bp = await self._get_blueprint(world_id)
        if bp is None:
            return None
        iterations = []
        completed = False
        for i in range(max(1, max_scenes)):
            plan = await self.plan_next(world_id, directive)          # S6
            pdir = (plan.get("directive") or directive or "").strip()
            await self.sim.open_scene(world_id, directive=pdir)       # STORY→WORLD：开一场导演指定的戏
            scene_res = await self.sim.run_scene(world_id, directive=pdir, max_rounds=max_rounds)
            verdict = await self.judge_ending(world_id)               # S7
            iterations.append({"iteration": i + 1, "plan": plan,
                               "scene": scene_res, "verdict": verdict})
            if verdict.get("completed"):
                completed = True
                break
        return {"iterations": iterations, "completed": completed,
                "blueprint": self.serialize(await self._get_blueprint(world_id))}

    async def auto_advance_stream(self, world_id, max_scenes: int = 4, directive: str = "",
                                  max_rounds: int = MAX_ROUNDS_PER_SCENE):
        """流式自动推进：把导演决策(director_plan)、逐 token 的演出、结局判定(ending_verdict)
        交织成一条事件流，直到抵达结局或达幕数上限。供前端「自动驾驶」直播。"""
        bp = await self._get_blueprint(world_id)
        if bp is None:
            yield {"type": "error", "message": "该世界尚无故事蓝图，请先生成蓝图"}
            return
        for i in range(max(1, max_scenes)):
            # S6：导演规划下一个戏剧动作
            plan = await self.plan_next(world_id, directive)
            pdir = (plan.get("directive") or directive or "").strip()
            yield {"type": "director_plan", "iteration": i + 1,
                   "action_type": plan.get("action_type"), "assessment": plan.get("assessment"),
                   "rationale": plan.get("rationale"), "scene_function": plan.get("scene_function"),
                   "pov": plan.get("pov"), "directive": pdir}

            # STORY→WORLD：开一场导演指定的戏，并把它播给前端
            opened = await self.sim.open_scene(world_id, directive=pdir)
            if opened.get("error"):
                yield {"type": "error", "message": opened["error"]}
                return
            sev = await self.sim._emit_scene_event(world_id)
            if sev:
                yield sev

            # 跑若干轮对话(流式)，到本幕被裁判判结束或达上限
            rounds = 0
            err = False
            while rounds < max_rounds:
                ended = False
                async for ev in self.sim.step_round_stream(world_id, pdir):
                    t = ev.get("type")
                    if t == "done":
                        continue                 # 吞掉每轮 done，末尾统一收尾
                    if t == "error":
                        err = True
                    if t == "judge":
                        ended = bool(ev.get("scene_ended"))
                    yield ev
                rounds += 1
                if err or ended:
                    break
            if err:
                return

            # S7：核对结局条件
            verdict = await self.judge_ending(world_id)
            yield {"type": "ending_verdict", "iteration": i + 1,
                   "completed": verdict.get("completed"), "which_ending": verdict.get("which_ending"),
                   "satisfied": verdict.get("satisfied"), "unmet": verdict.get("unmet"),
                   "needs_epilogue": verdict.get("needs_epilogue"), "reason": verdict.get("reason")}
            if verdict.get("completed"):
                yield {"type": "done", "mode": "auto", "iterations": i + 1, "completed": True,
                       "which_ending": verdict.get("which_ending")}
                return
        yield {"type": "done", "mode": "auto", "iterations": max_scenes, "completed": False}

    # ---------------- 序列化 ----------------
    @staticmethod
    def serialize(bp: StoryBlueprint) -> dict:
        return {
            "id": bp.id, "world_id": bp.world_id,
            "premise": bp.premise, "central_conflict": bp.central_conflict,
            "theme": bp.theme, "intended_endings": bp.intended_endings or [],
            "dramatic_phase": bp.dramatic_phase, "tension_target": bp.tension_target,
            "status": bp.status, "last_plan": bp.last_plan or {},
            "ending_verdict": bp.ending_verdict or {},
        }
