from storage.db import Base  # re-export Base for Alembic/migrations
# Import models so Alembic autogenerate can see their metadata
from storage.models import user, message, history, role, profile, summary  # noqa: F401
# communication 模块：场景化多人格交流（Room 已演进为 Scene）
from storage.models import worldview, scene, scene_participant, scene_message, scene_knowledge  # noqa: F401
# communication 持久世界：长期可演化的多智能体仿真建模
from storage.models import (  # noqa: F401
    world,
    character,
    location,
    item,
    ability,
    relationship,
    mental_state,
    agent_memory,
    common_knowledge,
    world_event,
)
